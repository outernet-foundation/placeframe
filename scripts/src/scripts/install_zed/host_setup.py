from logging import getLogger
from pathlib import Path
from typing import Literal

from placeframe_bash import bash, bash_check, bash_output
from common.ui import bail

from .constants import (
    BOX_SUBNET,
    HOST_CABLE_CIDR,
    HOST_NM_CONNECTION,
    HOST_NO_AUTO_DEFAULT_CONF,
    HOST_SYSCTL_CONTENT,
    HOST_SYSCTL_FILE,
)
from .messages import FIREWALLD_REQUIRED, NO_UNUSED_WIRED_INTERFACE

logger = getLogger(__name__)


def share_host_internet() -> None:
    set_host_link_method("manual")

    sysctl_path = Path(HOST_SYSCTL_FILE)
    if sysctl_path.exists() and sysctl_path.read_text() == HOST_SYSCTL_CONTENT:
        logger.info("ip_forward_already_enabled", extra={"path": HOST_SYSCTL_FILE})
    else:
        logger.info("enabling_ip_forward", extra={"path": HOST_SYSCTL_FILE})
        bash(f"sudo tee {HOST_SYSCTL_FILE}", stdin_text=HOST_SYSCTL_CONTENT)
        bash("sudo sysctl --system")

    if not bash_check("which firewall-cmd"):
        bail(FIREWALLD_REQUIRED)
    firewalld_dirty = False
    if bash_check(f"sudo firewall-cmd --permanent --zone=trusted --query-source={BOX_SUBNET}"):
        logger.info("firewalld_trusted_source_present", extra={"source": BOX_SUBNET})
    else:
        logger.info("adding_firewalld_trusted_source", extra={"source": BOX_SUBNET})
        bash(f"sudo firewall-cmd --permanent --zone=trusted --add-source={BOX_SUBNET}")
        firewalld_dirty = True
    if bash_check("sudo firewall-cmd --permanent --zone=public --query-masquerade"):
        logger.info("firewalld_masquerade_already_enabled")
    else:
        logger.info("enabling_firewalld_masquerade")
        bash("sudo firewall-cmd --permanent --zone=public --add-masquerade")
        firewalld_dirty = True
    if firewalld_dirty:
        bash("sudo firewall-cmd --reload")

    # firewalld's masquerade never fires for the box if Docker's FORWARD chain
    # drops the packet first: Docker sets the FORWARD policy to DROP and only
    # accepts traffic to/from its own bridges, so box->internet forwarding falls
    # through to that drop. DOCKER-USER is the chain Docker consults before its
    # own rules and leaves to operators; accept the box subnet in both directions
    # so forwarded traffic and its return path survive. Skipped when Docker isn't
    # installed (no DOCKER-USER chain), where forwarding works without it.
    if not bash_check("sudo iptables -S DOCKER-USER"):
        return

    for flag in ("-s", "-d"):
        rule = f"DOCKER-USER {flag} {BOX_SUBNET} -j ACCEPT"
        if bash_check(f"sudo iptables -C {rule}"):
            logger.info("docker_forward_rule_present", extra={"flag": flag, "subnet": BOX_SUBNET})
        else:
            logger.info("allowing_box_through_docker_forward", extra={"flag": flag, "subnet": BOX_SUBNET})
            bash(f"sudo iptables -I {rule}")


def set_host_link_method(method: Literal["shared", "manual"]) -> None:
    existing_profiles = bash_output("nmcli -t -e no -f NAME con show").strip().splitlines()
    config_changed = False

    if HOST_NM_CONNECTION not in existing_profiles:
        # First-run detection: an ethernet device with a live cable whose
        # current NM connection is either unbound or NM's auto-named "Wired
        # connection N" fallback. User-named profiles flag a NIC the user
        # explicitly manages (office wired, etc.) and are left alone.
        devices_raw = bash_output("nmcli -t -e no -f DEVICE,TYPE,STATE device").strip()
        candidates: list[str] = []
        for line in devices_raw.splitlines():
            device, device_type, state = line.split(":", 2)
            if device_type != "ethernet" or state == "unmanaged":
                continue
            carrier = Path(f"/sys/class/net/{device}/carrier").read_text().strip()
            if carrier != "1":
                continue
            connection = bash_output(f"nmcli -t -g GENERAL.CONNECTION device show {device}").strip()
            if connection not in ("", "--") and not connection.startswith("Wired connection"):
                continue
            candidates.append(device)

        if len(candidates) != 1:
            bail(
                NO_UNUSED_WIRED_INTERFACE,
                connection_name=HOST_NM_CONNECTION,
                candidates=candidates or "<none>",
                cidr=HOST_CABLE_CIDR,
            )
        device = candidates[0]
        mac = bash_output(f"nmcli -t -g GENERAL.HWADDR device show {device}").strip()

        # MAC-binding (ethernet.mac-address) makes the saved profile follow the
        # NIC across PCIe renumbering — the connection auto-binds to whatever
        # interface currently exposes this hardware address. no-auto-default
        # tells NM not to invent a competing "Wired connection N" for the same
        # MAC during cable replug events. autoconnect-priority=100 (default 0)
        # is belt-and-braces in case a competing profile is created or already
        # exists.
        logger.info("installing_no_auto_default_fragment", extra={"path": HOST_NO_AUTO_DEFAULT_CONF, "mac": mac})
        bash(f"sudo tee {HOST_NO_AUTO_DEFAULT_CONF}", stdin_text=f"[main]\nno-auto-default={mac}\n")
        bash("sudo nmcli general reload")

        logger.info(
            "creating_host_link",
            extra={"connection": HOST_NM_CONNECTION, "device": device, "mac": mac, "method": method},
        )
        bash(
            f"sudo nmcli con add type ethernet con-name {HOST_NM_CONNECTION}"
            f" ethernet.mac-address {mac}"
            f" connection.autoconnect-priority 100"
            f" ipv4.method {method} ipv4.addresses {HOST_CABLE_CIDR}"
            f' ipv4.gateway "" ipv4.dns ""'
        )
        config_changed = True
    else:
        current_method = bash_output(f"nmcli -t -g ipv4.method con show {HOST_NM_CONNECTION}").strip()
        current_addresses = bash_output(f"nmcli -t -g ipv4.addresses con show {HOST_NM_CONNECTION}").strip()
        if current_method != method or current_addresses != HOST_CABLE_CIDR:
            logger.info(
                "reconfiguring_host_link",
                extra={
                    "method": method,
                    "cidr": HOST_CABLE_CIDR,
                    "current_method": current_method,
                    "current_addresses": current_addresses,
                },
            )
            bash(
                f"sudo nmcli con mod {HOST_NM_CONNECTION} ipv4.method {method}"
                f' ipv4.addresses {HOST_CABLE_CIDR} ipv4.gateway "" ipv4.dns ""'
            )
            config_changed = True

    active_connections = bash_output("nmcli -t -e no -f NAME con show --active").strip().splitlines()
    currently_active = HOST_NM_CONNECTION in active_connections

    # `nmcli con mod` updates the on-disk profile but does not change the
    # running activation. Bounce the connection so pending changes take effect.
    if config_changed and currently_active:
        bash(f"sudo nmcli con down {HOST_NM_CONNECTION}")
        currently_active = False

    if currently_active:
        logger.info("host_link_already_active", extra={"method": method})
        return

    bash(f"sudo nmcli con up {HOST_NM_CONNECTION}")
