import time
from logging import getLogger

from common.bash import bash, bash_check, bash_output
from common.ui import bail, note

from .constants import (
    BOX_IP,
    BOX_SSH_TARGET,
    DHCP_LEASE_WAIT_SECONDS,
    SSH_KEY,
)
from .host_network import ensure_host_cable_set_to
from .messages import (
    BOX_INTERFACE_UNPARSEABLE,
    NETWORKMANAGER_NOT_ACTIVE,
    NO_ACTIVE_NM_CONNECTION,
    NO_BOX_WIRED_CONNECTION,
    NO_DHCP_LEASE_RECEIVED,
    SSH_KEY_COPY_PROMPT,
)
from .ssh import ssh_check, ssh_output, ssh_run

logger = getLogger(__name__)


def ensure_box_reachable_via_ssh() -> None:
    if bash_check(f"ssh -o BatchMode=yes -o ConnectTimeout=5 {BOX_SSH_TARGET} true"):
        return
    _bootstrap_box_via_dhcp()


def ensure_box_ssh_key_authorized() -> None:
    if bash_check(f"ssh -o BatchMode=yes -o ConnectTimeout=5 {BOX_SSH_TARGET} true"):
        return
    note(SSH_KEY_COPY_PROMPT)
    bash(f"ssh-copy-id -i {SSH_KEY} {BOX_SSH_TARGET}")


def ensure_etc_hosts_entry() -> None:
    box_hostname = ssh_output('"hostname"').strip()
    if ssh_check(f'"grep -q {box_hostname} /etc/hosts"'):
        logger.info("etc_hosts_entry_present", extra={"hostname": box_hostname})
        return
    logger.info("adding_etc_hosts_entry", extra={"hostname": box_hostname})
    ssh_run('"sudo tee -a /etc/hosts > /dev/null"', stdin_text=f"127.0.0.1 {box_hostname}\n")


def lookup_host_ip_from_box() -> str:
    if not ssh_check('"systemctl is-active --quiet NetworkManager"'):
        bail(NETWORKMANAGER_NOT_ACTIVE)
    # $SSH_CLIENT is the host IP the box can already reach us on — by
    # construction the 100.64.0.0/24 address the host cable connection holds.
    return ssh_output('"echo $SSH_CLIENT"').split()[0]


def ensure_box_default_route_via(host_ip: str) -> None:
    route_out = ssh_output(f'"ip route get {host_ip}"').strip().split()
    if "dev" not in route_out:
        bail(BOX_INTERFACE_UNPARSEABLE, host_ip=host_ip, route_out=repr(route_out))
    box_interface = route_out[route_out.index("dev") + 1]

    connections_raw = ssh_output('"nmcli -t -f NAME,DEVICE con show --active"').strip()
    box_connection = next(
        (
            parts[0].replace("\\:", ":").replace("\\\\", "\\")
            for line in connections_raw.splitlines()
            if (parts := line.partition(":"))[2] == box_interface
        ),
        "",
    )
    if not box_connection:
        bail(NO_ACTIVE_NM_CONNECTION, interface=box_interface, connections_raw=repr(connections_raw))

    nmcli_modify = (
        f'sudo nmcli con mod \\"{box_connection}\\" ipv4.gateway {host_ip} ipv4.dns 8.8.8.8 ipv4.ignore-auto-dns yes'
    )
    ssh_run(f'"{nmcli_modify}"')
    ssh_run(f'"sudo nmcli con up \\"{box_connection}\\""')


def _bootstrap_box_via_dhcp() -> None:
    logger.info("bootstrapping_box_via_dhcp")
    # NM's dnsmasq re-reads the lease file on startup, so a prior bootstrap's
    # entry survives a manual-shared-manual cycle and gets re-served, pointing
    # at an IP the box no longer holds. Delete the file so dnsmasq starts
    # empty.
    bash_check("sudo find /var/lib/NetworkManager -maxdepth 1 -name 'dnsmasq-*.leases' -delete")
    ensure_host_cable_set_to("shared")

    leased_ip = _wait_for_box_lease()
    logger.info("box_dhcp_lease_acquired", extra={"leased_ip": leased_ip})
    bootstrap_target = f"user@{leased_ip}"

    if not bash_check(f"ssh -o BatchMode=yes -o ConnectTimeout=5 {bootstrap_target} true"):
        note(SSH_KEY_COPY_PROMPT)
        bash(f"ssh-copy-id -i {SSH_KEY} {bootstrap_target}")

    box_connection = _find_box_wired_connection_name(bootstrap_target)
    logger.info("renumbering_box_to_static", extra={"connection": box_connection, "from": leased_ip, "to": BOX_IP})
    # `nmcli con up` flips the box's IP, silently killing this TCP session
    # (no FIN, no RST). ServerAlive* bounds the local SSH wait to ~10s
    # instead of the kernel's multi-minute TCP retransmit timeout.
    bash_check(
        f"ssh -t -o ServerAliveInterval=5 -o ServerAliveCountMax=2 {bootstrap_target} "
        f'"sudo nmcli con mod \\"{box_connection}\\" ipv4.method manual'
        f" ipv4.addresses {BOX_IP}/24 ipv4.gateway '' ipv4.dns ''"
        f' && sudo nmcli con up \\"{box_connection}\\""'
    )

    ensure_host_cable_set_to("manual")


def _wait_for_box_lease() -> str:
    logger.info("waiting_for_box_dhcp_lease", extra={"timeout_seconds": DHCP_LEASE_WAIT_SECONDS})
    deadline = time.monotonic() + DHCP_LEASE_WAIT_SECONDS
    while True:
        # /var/lib/NetworkManager is root-only-readable. `find -name` (not
        # the shell glob) handles a no-match gracefully.
        raw = bash_output(
            'sudo find /var/lib/NetworkManager -maxdepth 1 -name "dnsmasq-*.leases" -exec cat {} +'
        ).strip()
        now = time.time()
        # Lease format: `<expiry-unix-ts> <mac> <ip> <hostname> <client-id>`.
        for line in raw.splitlines():
            parts = line.split()
            if len(parts) >= 3 and parts[0].isdigit() and int(parts[0]) > now:
                return parts[2]
        if time.monotonic() >= deadline:
            bail(NO_DHCP_LEASE_RECEIVED, timeout_seconds=DHCP_LEASE_WAIT_SECONDS, box_ip=BOX_IP)
        time.sleep(1)


def _find_box_wired_connection_name(bootstrap_target: str) -> str:
    raw = bash_output(f'ssh {bootstrap_target} "nmcli -t -f NAME,TYPE con show --active"').strip()
    # nmcli's terse output escapes colons in field values as `\:` and
    # backslashes as `\\`. rpartition splits on the LAST colon so escaped
    # colons in the connection name stay intact; we then unescape.
    candidates = [
        line.rpartition(":")[0].replace("\\:", ":").replace("\\\\", "\\")
        for line in raw.splitlines()
        if line.rpartition(":")[2] == "802-3-ethernet"
    ]
    if not candidates:
        bail(NO_BOX_WIRED_CONNECTION, raw=repr(raw))
    return candidates[0]
