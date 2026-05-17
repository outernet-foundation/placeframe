NETWORKMANAGER_NOT_ACTIVE = """\
NetworkManager is not active on the box. install-zed assumes NM manages the
box's RJ-45 (the L4T default) so the persistent gateway + DNS land in
/etc/NetworkManager/system-connections/. If the box is on systemd-networkd
or another stack, persistence needs a different approach."""

BOX_INTERFACE_UNPARSEABLE = "Could not parse box-facing interface from `ip route get {host_ip}`: {route_out}"

NO_ACTIVE_NM_CONNECTION = (
    "No active NetworkManager connection on box interface {interface}. Active list: {connections_raw}"
)

NO_UNUSED_WIRED_INTERFACE = """\
Could not auto-detect an unused wired interface for the {connection_name!r} NM connection.
Candidates: {candidates}.
Configure manually: sudo nmcli con add type ethernet ifname <iface> con-name {connection_name} \
ipv4.method manual ipv4.addresses {cidr}"""

FIREWALLD_REQUIRED = """\
firewalld is required on the host for the box→internet path (NAT + trusted-zone
forwarding). On Ubuntu: sudo apt install firewalld."""

BOX_ID_UNRESOLVABLE = "Could not resolve box id: both /proc/device-tree/serial-number and /etc/machine-id are empty"

IMAGE_PULL_FAILED = """\
Image pull failed. Either the tags have not been pushed to ghcr.io yet, or the
ZED Box is offline. Push via CI (merge/push to trigger the build workflow) or
build locally with: uv run install-zed --build"""

SSH_KEY_COPY_PROMPT = "will prompt for the SSH login one last time to copy the install-zed key"

SUDOERS_INSTALL_PROMPT = "will prompt for sudo once to install the passwordless-sudo rule"

NO_DHCP_LEASE_RECEIVED = """\
Box did not request a DHCP lease within {timeout_seconds}s during bootstrap.
Check that the ethernet cable is connected to the box and the box's wired
NetworkManager connection is set to ipv4.method=auto (the L4T factory
default). If the box already has a static IP, install-zed expects it to be
{box_ip} — anything else won't be reached without bootstrap."""

NO_BOX_WIRED_CONNECTION = """\
Could not find a wired (802-3-ethernet) NetworkManager connection on the box
during bootstrap. Active-connection output from the box:
{raw}"""
