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
WAIT_FOR_ZED_CAMERA_SOURCE = REPO_ROOT / "docker" / "zed-capture" / "wait_for_zed_camera.py"
REMOTE_DIR = "~/.placeframe"
REMOTE_COMPOSE = f"{REMOTE_DIR}/compose.rig.yml"
REMOTE_WAIT_FOR_ZED_CAMERA = f"{REMOTE_DIR}/wait_for_zed_camera.py"
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
    "user ALL=(ALL) NOPASSWD: /usr/bin/dpkg, /usr/sbin/usermod, /usr/bin/nvidia-ctk,"
    " /usr/bin/systemctl, /usr/bin/docker, /usr/bin/tee, /usr/bin/nmcli, /usr/bin/install"
)

# Pins the Jetson's USB-C port as a USB gadget, which is incompatible with
# the box acting as USB host for the phone-as-accessory link. Disabling
# frees the port for host duty.
L4T_USB_DEVICE_MODE_UNIT = "nv-l4t-usb-device-mode.service"

APPLIANCE_DEFAULT_TARGET = "multi-user.target"

# System-level units installed by the stock JetPack desktop image that have
# no role on a placeframe appliance. gdm pulls in the entire GNOME session;
# fwupd / packagekit / snapd run unsolicited update + probe traffic;
# geoclue / accounts-daemon / ModemManager / upower are desktop-session
# auxiliaries; cups / bluetooth / whoopsie / apport / unattended-upgrades are
# generic Ubuntu defaults a headless box has no business running.
APPLIANCE_SYSTEM_UNITS_TO_MASK: tuple[str, ...] = (
    "gdm.service",
    "fwupd.service",
    "packagekit.service",
    "snapd.service",
    "geoclue.service",
    "accounts-daemon.service",
    "ModemManager.service",
    "upower.service",
    "cups.service",
    "cups-browsed.service",
    "bluetooth.service",
    "whoopsie.service",
    "apport.service",
    "unattended-upgrades.service",
)

# User-scope units that gnome-session spawns when a desktop user logs in.
# Masking at --global level keeps them off even if a maintenance user shells
# in interactively. The gvfs-*-volume-monitor probers were the proximate
# cause of the AOA dialog-respawn bug — libusb_open + descriptor probes
# against the AOA-mode phone stalled the kernel into a SuperSpeed reset.
APPLIANCE_USER_UNITS_TO_MASK: tuple[str, ...] = (
    "gvfs-udisks2-volume-monitor.service",
    "gvfs-mtp-volume-monitor.service",
    "gvfs-afc-volume-monitor.service",
    "gvfs-gphoto2-volume-monitor.service",
    "evolution-source-registry.service",
    "evolution-calendar-factory.service",
    "evolution-addressbook-factory.service",
    "gnome-software.service",
)

APPLIANCE_BANNER_TEXT = "Placeframe ZED Box - managed remotely, see install-zed.\n"
APPLIANCE_BANNER_PATHS: tuple[str, ...] = ("/etc/issue", "/etc/issue.net", "/etc/motd")
