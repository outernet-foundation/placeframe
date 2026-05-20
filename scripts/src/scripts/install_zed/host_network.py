from logging import getLogger
from pathlib import Path

from common.bash import bash, bash_check, bash_output
from common.ui import bail

from .constants import (
    BOX_SUBNET,
    HOST_CABLE_CIDR,
    HOST_NM_CONNECTION,
    HOST_SYSCTL_CONTENT,
    HOST_SYSCTL_FILE,
)
from .messages import FIREWALLD_REQUIRED, NO_UNUSED_WIRED_INTERFACE

logger = getLogger(__name__)


def ensure_host_cable_set_to(method: str) -> None:
    # `nmcli con show <name>` outputs property:value pairs, not a tabular
    # view with a NAME column, so `-f NAME` matches no field and exits
    # non-zero. List-view + membership check works.
    existing_connections = bash_output("nmcli -t -f NAME con show").strip().splitlines()
    if HOST_NM_CONNECTION not in existing_connections:
        host_interface = _detect_box_interface()
        logger.info(
            "creating_host_cable_connection",
            extra={"connection": HOST_NM_CONNECTION, "interface": host_interface, "method": method},
        )
        bash(
            f"sudo nmcli con add type ethernet ifname {host_interface} con-name {HOST_NM_CONNECTION}"
            f' ipv4.method {method} ipv4.addresses {HOST_CABLE_CIDR} ipv4.gateway "" ipv4.dns ""'
        )
        _evict_competing_connections(host_interface)
        bash(f"sudo nmcli con up {HOST_NM_CONNECTION}")
        return

    # NIC names track PCIe enumeration — adding, removing, or reseating
    # hardware can shift enp6s0 to enp5s0 and leave the saved
    # connection.interface-name pointing at a device that no longer exists.
    # `nmcli con up` then fails with no clear diagnostic. Rebind to whatever
    # box-facing interface is present now.
    saved_interface = bash_output(f"nmcli -t -g connection.interface-name con show {HOST_NM_CONNECTION}").strip()
    if not saved_interface or not Path(f"/sys/class/net/{saved_interface}").exists():
        new_interface = _detect_box_interface()
        logger.info(
            "rebinding_host_cable_interface",
            extra={
                "connection": HOST_NM_CONNECTION,
                "from": saved_interface or "<unset>",
                "to": new_interface,
            },
        )
        bash(f"sudo nmcli con mod {HOST_NM_CONNECTION} connection.interface-name {new_interface}")
        bound_interface = new_interface
    else:
        bound_interface = saved_interface

    current_method = bash_output(f"nmcli -t -g ipv4.method con show {HOST_NM_CONNECTION}").strip()
    current_addresses = bash_output(f"nmcli -t -g ipv4.addresses con show {HOST_NM_CONNECTION}").strip()
    if current_method != method or current_addresses != HOST_CABLE_CIDR:
        logger.info(
            "reconfiguring_host_cable",
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

    _evict_competing_connections(bound_interface)

    active_connections = bash_output("nmcli -t -f NAME con show --active").strip().splitlines()
    if HOST_NM_CONNECTION in active_connections:
        logger.info("host_cable_already_active", extra={"interface": bound_interface, "method": method})
        return
    bash(f"sudo nmcli con up {HOST_NM_CONNECTION}")


def ensure_ip_forward_on_host() -> None:
    sysctl_path = Path(HOST_SYSCTL_FILE)
    if sysctl_path.exists() and sysctl_path.read_text() == HOST_SYSCTL_CONTENT:
        logger.info("ip_forward_already_enabled", extra={"path": HOST_SYSCTL_FILE})
        return
    logger.info("enabling_ip_forward", extra={"path": HOST_SYSCTL_FILE})
    bash(f"sudo tee {HOST_SYSCTL_FILE}", stdin_text=HOST_SYSCTL_CONTENT)
    bash("sudo sysctl --system")


def ensure_firewalld_configured() -> None:
    if not bash_check("which firewall-cmd"):
        bail(FIREWALLD_REQUIRED)
    dirty = False
    if bash_check(f"sudo firewall-cmd --permanent --zone=trusted --query-source={BOX_SUBNET}"):
        logger.info("firewalld_trusted_source_present", extra={"source": BOX_SUBNET})
    else:
        logger.info("adding_firewalld_trusted_source", extra={"source": BOX_SUBNET})
        bash(f"sudo firewall-cmd --permanent --zone=trusted --add-source={BOX_SUBNET}")
        dirty = True

    if bash_check("sudo firewall-cmd --permanent --zone=public --query-masquerade"):
        logger.info("firewalld_masquerade_already_enabled")
    else:
        logger.info("enabling_firewalld_masquerade")
        bash("sudo firewall-cmd --permanent --zone=public --add-masquerade")
        dirty = True

    if dirty:
        bash("sudo firewall-cmd --reload")


def _detect_box_interface() -> str:
    # Ethernet device with link carrier whose current NM connection is
    # either unbound or NM's auto-named "Wired connection N" fallback.
    # User-named profiles are excluded as those mark the host's internet
    # path; unmanaged devices (Docker veths, libvirt bridges) are excluded
    # by state.
    devices_raw = bash_output("nmcli -t -f DEVICE,TYPE,STATE,CONNECTION device").strip()
    candidates: list[str] = []
    for line in devices_raw.splitlines():
        # CONNECTION (the final field) can contain colons, so cap split at 3
        # so escaped colons in the name stay attached.
        parts = line.split(":", 3)
        if len(parts) < 4 or parts[1] != "ethernet" or parts[2] == "unmanaged":
            continue
        device, connection = parts[0], parts[3]
        if not _has_carrier(device):
            continue
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
    return candidates[0]


def _has_carrier(device: str) -> bool:
    carrier_path = Path(f"/sys/class/net/{device}/carrier")
    if not carrier_path.exists():
        return False
    # /sys/class/net/<device>/carrier raises EINVAL when the interface is
    # administratively down. Treat that as "carrier unknown".
    try:
        return carrier_path.read_text().strip() == "1"
    except OSError:
        return False


def _evict_competing_connections(device: str) -> None:
    # When NM auto-binds a "Wired connection N" fallback profile to the
    # box-facing NIC (typical on cable plug before zedbox is brought up),
    # `nmcli con up zedbox` races against it. Bring competitors down and
    # turn off their autoconnect so they don't grab the port again on the
    # next replug.
    raw = bash_output("nmcli -t -f NAME,DEVICE con show --active").strip()
    for line in raw.splitlines():
        # NAME may contain escaped colons; DEVICE is bare and last.
        name_raw, _, active_device = line.rpartition(":")
        if active_device != device:
            continue
        name = name_raw.replace("\\:", ":").replace("\\\\", "\\")
        if name == HOST_NM_CONNECTION:
            continue
        logger.info("evicting_competing_connection", extra={"connection": name, "device": device})
        bash(f'sudo nmcli con down "{name}"')
        if name.startswith("Wired connection"):
            bash(f'sudo nmcli con mod "{name}" connection.autoconnect no')
