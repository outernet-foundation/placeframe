from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ZedService:
    # compose.rig.yml service key, image base name, and compose.zed.bake.yml target.
    # These three are the same string by construction.
    name: str
    # Env var compose.rig.yml uses to override the image (`${X:-default}`). Asymmetric
    # with name (`zed-capture` → `ZED_IMAGE`, not `ZED_CAPTURE_IMAGE`), so listed explicitly.
    image_env: str
    # Key into the dict returned by `compute_service_shas`.
    sha_key: str


ZED_SERVICES: tuple[ZedService, ...] = (
    ZedService("zed-capture", "ZED_IMAGE", "ZED_CAPTURE_SHA"),
    ZedService("aoa-bridge", "AOA_BRIDGE_IMAGE", "AOA_BRIDGE_SHA"),
    ZedService("aoa-gateway", "AOA_GATEWAY_IMAGE", "AOA_GATEWAY_SHA"),
)

# Pure-upstream images (no build target) that compose.rig.yml references via
# `${KEY:?err}`. install_zed reads these entries from the host's .env.lock and
# forwards them to the box's .env so the box pulls the same digest-pinned
# versions the host uses.
ZED_UPSTREAM_IMAGE_KEYS: tuple[str, ...] = ("LOKI_IMAGE", "ALLOY_IMAGE")

REPO_ROOT = Path(__file__).resolve().parents[4]
BAKE_FILE = REPO_ROOT / "compose.zed.bake.yml"
ENV_LOCK_FILE = REPO_ROOT / ".env.lock"
COMPOSE_SOURCE = REPO_ROOT / "docker" / "zed-capture" / "compose.rig.yml"
AOA_LOKI_CONFIG_SOURCE = REPO_ROOT / "docker" / "aoa-loki" / "config.yaml"
AOA_ALLOY_CONFIG_SOURCE = REPO_ROOT / "docker" / "aoa-alloy" / "config.alloy"
SYSTEMD_UNIT_SOURCE = REPO_ROOT / "docker" / "zed-capture" / "placeframe-zed.service"
REMOTE_DIR = "~/.placeframe"
REMOTE_COMPOSE = f"{REMOTE_DIR}/compose.rig.yml"
REMOTE_AOA_LOKI_DIR = f"{REMOTE_DIR}/aoa-loki"
REMOTE_AOA_ALLOY_DIR = f"{REMOTE_DIR}/aoa-alloy"
SSH_SOCKET = "/tmp/install-zed-ssh-%C"
SSH_MUX = f"-o ControlMaster=auto -o ControlPath={SSH_SOCKET} -o ControlPersist=120"
SSH_KEY = Path.home() / ".ssh" / "id_ed25519"
GHCR_BASE = "ghcr.io/outernet-foundation/placeframe"

# Inside RFC 6598 Shared Address Space (100.64.0.0/10), not RFC1918, so
# sandbox containers with RFC1918-block firewall rules can still reach the
# box.
BOX_SUBNET = "100.64.0.0/24"
BOX_IP = "100.64.0.1"
HOST_CABLE_CIDR = "100.64.0.2/24"
HOST_NM_CONNECTION = "zedbox"
HOST_NO_AUTO_DEFAULT_CONF = "/etc/NetworkManager/conf.d/zedbox-no-auto-default.conf"
HOST_SYSCTL_FILE = "/etc/sysctl.d/99-zedbox.conf"
HOST_SYSCTL_CONTENT = "net.ipv4.ip_forward = 1\n"
BOX_SSH_TARGET = f"user@{BOX_IP}"

DOCKER_DEB_BASE = "https://download.docker.com/linux/ubuntu/dists/jammy/pool/stable/arm64"
DOCKER_DEBS = [
    "containerd.io_2.2.2-1~ubuntu.22.04~jammy_arm64.deb",
    "docker-ce-cli_29.3.1-1~ubuntu.22.04~jammy_arm64.deb",
    "docker-ce_29.3.1-1~ubuntu.22.04~jammy_arm64.deb",
    "docker-buildx-plugin_0.33.0-1~ubuntu.22.04~jammy_arm64.deb",
    "docker-compose-plugin_5.1.1-1~ubuntu.22.04~jammy_arm64.deb",
]

REGISTRY_IMAGE = "registry@sha256:a3d8aaa63ed8681a604f1dea0aa03f100d5895b6a58ace528858a7b332415373"
REGISTRY_PORT = 5000

DHCP_LEASE_WAIT_SECONDS = 60

SUDOERS_RULE = (
    "user ALL=(ALL) NOPASSWD: /usr/bin/dpkg, /usr/bin/apt-get, /usr/sbin/usermod, /usr/bin/nvidia-ctk,"
    " /usr/bin/systemctl, /usr/bin/docker, /usr/bin/tee, /usr/bin/nmcli, /usr/bin/mkdir"
)

# Pins the Jetson's USB-C port as a USB gadget, which is incompatible with
# the box acting as USB host for the phone-as-accessory link. Disabling
# frees the port for host duty.
L4T_USB_DEVICE_MODE_UNIT = "nv-l4t-usb-device-mode.service"

# Forces journald to write to /var/log/journal/ (persistent) and fsync every
# second (default is 5 minutes). The box wedges in a way that requires a
# power-cycle to recover; without aggressive sync, the seconds-before-cycle
# events that diagnose the wedge are lost. RateLimitBurst=0 disables per-unit
# log rate limiting so the failure-moment flood isn't dropped.
JOURNALD_DROPIN_DIR = "/etc/systemd/journald.conf.d"
JOURNALD_DROPIN_PATH = f"{JOURNALD_DROPIN_DIR}/placeframe.conf"
JOURNALD_DROPIN_CONTENT = "[Journal]\nStorage=persistent\nSyncIntervalSec=1s\nRateLimitBurst=0\n"

# Always-on tcpdump on lo:9000 capturing the aoa-bridge <-> aoa-gateway HTTP/2
# wire to a rolling ring of pcap files on persistent disk. Caddy's Go net/http2
# framer rejects frames at the 9-byte header read with ErrCode=FRAME_SIZE_ERROR
# and never logs the offending bytes; without an on-the-wire capture there is
# no way to identify the bad frame after the wedge that follows. -C 10 -W 20
# gives a 200 MB ring (20 files of 10 MB), cycling oldest-first. -U flushes
# each packet so a power-cycle keeps the last seconds. -Z root pins the user
# so tcpdump can write to /var/log/postmortem (which is root-owned) rather
# than auto-dropping to the `tcpdump` system user.
H2_FRAME_CAPTURE_LOG_DIR = "/var/log/postmortem/h2-frame"
H2_FRAME_CAPTURE_UNIT_NAME = "h2-frame-capture.service"
H2_FRAME_CAPTURE_UNIT_PATH = f"/etc/systemd/system/{H2_FRAME_CAPTURE_UNIT_NAME}"
H2_FRAME_CAPTURE_UNIT_CONTENT = (
    "[Unit]\n"
    "Description=Persistent HTTP/2 frame capture on lo:9000 (aoa-bridge <-> aoa-gateway)\n"
    "\n"
    "[Service]\n"
    "Type=exec\n"
    "ExecStart=/usr/bin/tcpdump -i lo -s 0 -U -C 10 -W 20 -Z root"
    f" -w {H2_FRAME_CAPTURE_LOG_DIR}/lo-9000.pcap tcp port 9000\n"
    "Restart=always\n"
    "RestartSec=2\n"
    "\n"
    "[Install]\n"
    "WantedBy=multi-user.target\n"
)
