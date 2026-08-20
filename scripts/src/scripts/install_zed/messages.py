BOX_INTERFACE_UNPARSEABLE = "Could not parse box-facing interface from `ip route get {host_ip}`: {route_out}"

NO_ACTIVE_NM_CONNECTION = (
    "No active NetworkManager connection on box interface {interface}. Active list: {connections_raw}"
)

NO_UNUSED_WIRED_INTERFACE = """\
Could not auto-detect an unused wired interface for the {connection_name!r} NM connection.
Candidates: {candidates}.
Configure manually: sudo nmcli con add type ethernet con-name {connection_name} \
ethernet.mac-address <mac> ipv4.method manual ipv4.addresses {cidr}"""

FIREWALLD_REQUIRED = """\
firewalld is required on the host for the box→internet path (NAT + trusted-zone
forwarding). On Ubuntu: sudo apt install firewalld."""

ARM64_EMULATION_MISSING = """\
Cross-building the box's linux/arm64 images on this x86 host needs QEMU
binfmt_misc emulation, but no enabled qemu-aarch64 handler is registered.
Without it the build dies on the first arm64 RUN step with `exec format error`.

Register the emulators on the host (persists until reboot), then retry:
  docker run --privileged --rm tonistiigi/binfmt --install arm64

Or skip local cross-compilation and pull prebuilt images from ghcr.io instead:
  uv run install-zed"""

BOX_ID_UNRESOLVABLE = "Could not resolve box id: /proc/device-tree/serial-number is empty or missing"

IMAGE_PULL_FAILED = """\
Image pull failed for {image}. Either the tag has not been pushed to ghcr.io
yet, or the ZED Box is offline. Push via CI (merge/push to trigger the build
workflow) or build locally with: uv run install-zed --build"""

SSH_KEY_COPY_PROMPT = "will prompt for the SSH login one last time to copy the install-zed key"

NO_DHCP_LEASE_RECEIVED = """\
Box did not request a DHCP lease within {timeout_seconds}s during bootstrap.
Check that the ethernet cable is connected to the box and the box's wired
NetworkManager connection is set to ipv4.method=auto (the L4T factory
default). If the box already has a static IP, install-zed expects it to be
{box_ip} — anything else won't be reached without bootstrap."""

NO_BOX_WIRED_CONNECTION = """\
Could not find a wired (802-3-ethernet) NetworkManager device on the box
during bootstrap. nmcli device list:
{raw}"""
