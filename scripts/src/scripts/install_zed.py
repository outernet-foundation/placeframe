import json
import tempfile
import time
from contextlib import ExitStack
from logging import getLogger
from pathlib import Path
from subprocess import CalledProcessError
from typing import Annotated

import typer
from build_scripts.placeframe.context_sha import compute_service_shas
from common.bash import bash, bash_check, bash_output
from common.logging_config import configure_logging
from common.ui import bail, note

from . import messages

REPO_ROOT = Path(__file__).resolve().parents[3]
BAKE_FILE = REPO_ROOT / "compose.zed.bake.yml"
COMPOSE_SOURCE = REPO_ROOT / "docker" / "zed-capture" / "compose.rig.yml"
SYSTEMD_UNIT_SOURCE = REPO_ROOT / "docker" / "zed-capture" / "placeframe-zed.service"
REMOTE_DIR = "~/.placeframe"
REMOTE_COMPOSE = f"{REMOTE_DIR}/compose.rig.yml"
SSH_SOCKET = "/tmp/install-zed-ssh-%C"
SSH_MUX = f"-o ControlMaster=auto -o ControlPath={SSH_SOCKET} -o ControlPersist=120"
SSH_KEY = Path.home() / ".ssh" / "id_ed25519"
GHCR_BASE = "ghcr.io/outernet-foundation/placeframe"

# Inside RFC 6598 Shared Address Space (100.64.0.0/10), not RFC1918, so
# sandbox containers with RFC1918-block firewall rules can still reach the
# box.
BOX_SUBNET = "100.64.0.0/24"
BOX_IP = "100.64.0.1"
HOST_CABLE_IP = "100.64.0.2"
HOST_CABLE_CIDR = f"{HOST_CABLE_IP}/24"
HOST_NM_CONNECTION = "zedbox"
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
    " /usr/bin/systemctl, /usr/bin/docker, /usr/bin/tee, /usr/bin/nmcli"
)

# Pins the Jetson's USB-C port as a USB gadget, which is incompatible with
# the box acting as USB host for the phone-as-accessory link. Disabling
# frees the port for host duty.
L4T_USB_DEVICE_MODE_UNIT = "nv-l4t-usb-device-mode.service"

logger = getLogger(__name__)
app = typer.Typer()


@app.command()
def main(
    build: Annotated[
        bool,
        typer.Option("--build", help="Cross-compile zed-capture locally instead of pulling from ghcr"),
    ] = False,
) -> None:
    configure_logging("install-zed")
    logger.info("starting_install", extra={"target": BOX_SSH_TARGET, "build": build})
    with ExitStack() as stack:
        _install(stack, build)


# Separate helper so ExitStack callbacks fire when this returns, not at the
# typer command-function boundary.
def _install(stack: ExitStack, build: bool) -> None:
    service_shas = compute_service_shas(REPO_ROOT, BAKE_FILE)

    if need_ssh_key_generate():
        SSH_KEY.parent.mkdir(parents=True, exist_ok=True)
        bash(f'ssh-keygen -t ed25519 -N "" -f {SSH_KEY}')

    _set_host_cable_to("manual")

    if not bash_check(f"ssh -o BatchMode=yes -o ConnectTimeout=5 {BOX_SSH_TARGET} true"):
        _bootstrap_box_via_dhcp()

    if not bash_check(f"ssh -o BatchMode=yes -o ConnectTimeout=5 {BOX_SSH_TARGET} true"):
        note(messages.SSH_KEY_COPY_PROMPT)
        bash(f"ssh-copy-id -i {SSH_KEY} {BOX_SSH_TARGET}")

    logger.info("connecting_to_box", extra={"target": BOX_SSH_TARGET})
    bash(f"ssh {SSH_MUX} -fN {BOX_SSH_TARGET}")
    stack.callback(lambda: bash_check(f"ssh -o ControlPath={SSH_SOCKET} -O exit {BOX_SSH_TARGET}"))

    if need_sudoers_write():
        note(messages.SUDOERS_INSTALL_PROMPT)
        # `sudo install` (not pipe-into-tee) avoids a remote pipeline and
        # works before passwordless sudo exists.
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sudoers") as sudoers_file:
            sudoers_file.write(SUDOERS_RULE + "\n")
            sudoers_file.flush()
            bash(f"scp {SSH_MUX} {sudoers_file.name} {BOX_SSH_TARGET}:/tmp/install-zed.sudoers")
            bash(
                f"ssh -t {SSH_MUX} {BOX_SSH_TARGET}"
                ' "sudo install -m 0440 -o root -g root /tmp/install-zed.sudoers /etc/sudoers.d/install-zed"'
            )
            _ssh('"rm /tmp/install-zed.sudoers"')

    fresh_install = need_docker_install()
    if fresh_install:
        with tempfile.TemporaryDirectory() as temp_directory:
            logger.info("downloading_docker_packages", extra={"count": len(DOCKER_DEBS)})
            for deb_file in DOCKER_DEBS:
                bash(f"curl -fsSL -o {temp_directory}/{deb_file} {DOCKER_DEB_BASE}/{deb_file}")
            logger.info("transferring_docker_packages", extra={"target": BOX_SSH_TARGET})
            for deb_file in DOCKER_DEBS:
                bash(f"scp {SSH_MUX} {temp_directory}/{deb_file} {BOX_SSH_TARGET}:/tmp/{deb_file}")
        deb_paths = " ".join(f"/tmp/{deb_file}" for deb_file in DOCKER_DEBS)
        box_user = BOX_SSH_TARGET.split("@")[0]
        _ssh(f'"sudo dpkg -i {deb_paths}"')
        _ssh(f'"sudo usermod -aG docker {box_user}"')
        _ssh(f'"rm {deb_paths}"')
        logger.info("docker_installed", extra={"user": box_user})
    # The just-added docker group membership isn't picked up on this SSH
    # session, so the fresh-install path needs sudo.
    docker = "sudo docker" if fresh_install else "docker"

    if need_nvidia_runtime_configure():
        _ssh('"sudo nvidia-ctk runtime configure --runtime=docker"')
        _ssh('"sudo systemctl restart docker"')

    logger.info("disabling_usb_device_mode_service", extra={"unit": L4T_USB_DEVICE_MODE_UNIT})
    _ssh_check(f'"sudo systemctl disable --now {L4T_USB_DEVICE_MODE_UNIT}"')

    logger.info("configuring_box_networking")
    box_hostname = _ssh_output('"hostname"').strip()
    if need_etc_hosts_entry(box_hostname):
        _ssh('"sudo tee -a /etc/hosts > /dev/null"', stdin_text=f"127.0.0.1 {box_hostname}\n")

    if not _ssh_check('"systemctl is-active --quiet NetworkManager"'):
        bail(messages.NETWORKMANAGER_NOT_ACTIVE)

    # $SSH_CLIENT is the host IP the box can already reach us on — by
    # construction the 100.64.0.0/24 address the host cable connection holds.
    host_ip = _ssh_output('"echo $SSH_CLIENT"').split()[0]
    route_out = _ssh_output(f'"ip route get {host_ip}"').strip().split()
    if "dev" not in route_out:
        bail(messages.BOX_INTERFACE_UNPARSEABLE, host_ip=host_ip, route_out=repr(route_out))
    box_interface = route_out[route_out.index("dev") + 1]

    connections_raw = _ssh_output('"nmcli -t -f NAME,DEVICE con show --active"').strip()
    box_connection = next(
        (
            parts[0].replace("\\:", ":").replace("\\\\", "\\")
            for line in connections_raw.splitlines()
            if (parts := line.partition(":"))[2] == box_interface
        ),
        "",
    )
    if not box_connection:
        bail(messages.NO_ACTIVE_NM_CONNECTION, interface=box_interface, connections_raw=repr(connections_raw))

    nmcli_modify = (
        f'sudo nmcli con mod \\"{box_connection}\\" ipv4.gateway {host_ip} ipv4.dns 8.8.8.8 ipv4.ignore-auto-dns yes'
    )
    _ssh(f'"{nmcli_modify}"')
    _ssh(f'"sudo nmcli con up \\"{box_connection}\\""')

    if need_ip_forward_enable():
        bash(f"sudo tee {HOST_SYSCTL_FILE}", stdin_text=HOST_SYSCTL_CONTENT)
        bash("sudo sysctl --system")

    if not bash_check("which firewall-cmd"):
        bail(messages.FIREWALLD_REQUIRED)
    firewalld_changed = False
    if need_firewalld_trusted_source_add():
        bash(f"sudo firewall-cmd --permanent --zone=trusted --add-source={BOX_SUBNET}")
        firewalld_changed = True
    if need_firewalld_masquerade_enable():
        bash("sudo firewall-cmd --permanent --zone=public --add-masquerade")
        firewalld_changed = True
    if firewalld_changed:
        bash("sudo firewall-cmd --reload")

    images = _acquire_images(host_ip, build, docker, service_shas)

    logger.info("transferring_compose_file", extra={"source": str(COMPOSE_SOURCE)})
    _ssh(f'"mkdir -p {REMOTE_DIR}"')
    bash(f"scp {SSH_MUX} {COMPOSE_SOURCE!s} {BOX_SSH_TARGET}:{REMOTE_COMPOSE}")

    # Jetson hardware-burned serial survives OS reflashes; /etc/machine-id is
    # the non-Jetson fallback.
    if _ssh_check('"test -e /proc/device-tree/serial-number"'):
        box_id = _ssh_output("\"tr -d '\\0\\n' < /proc/device-tree/serial-number\"").strip()
    else:
        box_id = ""
    if not box_id:
        box_id = _ssh_output('"cat /etc/machine-id"').strip()
    if not box_id:
        bail(messages.BOX_ID_UNRESOLVABLE)
    _ssh(
        f"tee {REMOTE_DIR}/.env",
        stdin_text=(
            f"ZED_IMAGE={images['zed_capture']}\nAOA_BRIDGE_IMAGE={images['aoa_bridge']}\nZED_BOX_ID={box_id}\n"
        ),
    )

    logger.info("installing_systemd_unit", extra={"unit": "placeframe-zed.service"})
    remote_home = _ssh_output('"echo $HOME"').strip()
    remote_compose_abs = f"{remote_home}/.placeframe/compose.rig.yml"
    unit_content = SYSTEMD_UNIT_SOURCE.read_text().replace("COMPOSE_PATH", remote_compose_abs)
    _ssh('"sudo tee /etc/systemd/system/placeframe-zed.service > /dev/null"', stdin_text=unit_content)
    _ssh('"sudo systemctl daemon-reload"')
    _ssh('"sudo systemctl enable placeframe-zed.service"')

    logger.info("enabling_camera_daemons")
    _ssh('"sudo systemctl enable --now nvargus-daemon zed_x_daemon"')

    # `down` first so deploys are idempotent against any prior partially-failed
    # `up --force-recreate` (which can leave containers stuck under their
    # ID-prefixed rename, blocking the next recreate with a name conflict).
    logger.info("redeploying_compose_stack", extra={"compose": REMOTE_COMPOSE})
    _ssh(f'"{docker} compose -f {REMOTE_COMPOSE} down --remove-orphans"')
    _ssh(f'"{docker} compose -f {REMOTE_COMPOSE} up -d"')

    if not build:
        logger.info("warming_zed_sdk")
        bash(
            f'ssh {SSH_MUX} {BOX_SSH_TARGET} "{docker} compose -f {REMOTE_COMPOSE} exec zed-capture python -c \\"'
            f"import pyzed.sl as sl; c = sl.Camera(); p = sl.InitParameters(); c.open(p); c.close()"
            f'\\""'
        )

    logger.info("install_done")


def _bootstrap_box_via_dhcp() -> None:
    logger.info("bootstrapping_box_via_dhcp")
    # NM's dnsmasq re-reads the lease file on startup, so a prior bootstrap's
    # entry survives a manual-shared-manual cycle and gets re-served, pointing
    # at an IP the box no longer holds. Delete the file so dnsmasq starts
    # empty.
    bash_check("sudo find /var/lib/NetworkManager -maxdepth 1 -name 'dnsmasq-*.leases' -delete")
    _set_host_cable_to("shared")

    leased_ip = _wait_for_box_lease()
    logger.info("box_dhcp_lease_acquired", extra={"leased_ip": leased_ip})
    bootstrap_target = f"user@{leased_ip}"

    if not bash_check(f"ssh -o BatchMode=yes -o ConnectTimeout=5 {bootstrap_target} true"):
        note(messages.SSH_KEY_COPY_PROMPT)
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

    _set_host_cable_to("manual")


def _set_host_cable_to(method: str) -> None:
    # `nmcli con show <name>` outputs property:value pairs, not a tabular
    # view with a NAME column, so `-f NAME` matches no field and exits
    # non-zero. List-view + membership check works.
    existing_connections = bash_output("nmcli -t -f NAME con show").strip().splitlines()
    if HOST_NM_CONNECTION not in existing_connections:
        # Detect-by-name is more robust than detect-by-device because the
        # device name varies per host (enp6s0, eno1, etc.).
        devices_raw = bash_output("nmcli -t -f DEVICE,TYPE,STATE device").strip()
        # `disconnected` is NM's state for "real NIC, no connection assigned".
        # `unmanaged` (Docker veths, libvirt bridges) and `connected` (NIC
        # owned by another NM connection) would both be wrong matches.
        candidates = [
            parts[0]
            for line in devices_raw.splitlines()
            if (parts := line.split(":")) and len(parts) >= 3 and parts[1] == "ethernet" and parts[2] == "disconnected"
        ]
        if len(candidates) != 1:
            bail(
                messages.NO_UNUSED_WIRED_INTERFACE,
                connection_name=HOST_NM_CONNECTION,
                candidates=candidates or "<none>",
                cidr=HOST_CABLE_CIDR,
            )
        host_interface = candidates[0]
        logger.info(
            "creating_host_cable_connection",
            extra={"connection": HOST_NM_CONNECTION, "interface": host_interface, "method": method},
        )
        bash(
            f"sudo nmcli con add type ethernet ifname {host_interface} con-name {HOST_NM_CONNECTION}"
            f' ipv4.method {method} ipv4.addresses {HOST_CABLE_CIDR} ipv4.gateway "" ipv4.dns ""'
        )
        bash(f"sudo nmcli con up {HOST_NM_CONNECTION}")
        return

    current_method = bash_output(f"nmcli -t -g ipv4.method con show {HOST_NM_CONNECTION}").strip()
    current_addresses = bash_output(f"nmcli -t -g ipv4.addresses con show {HOST_NM_CONNECTION}").strip()
    if current_method == method and current_addresses == HOST_CABLE_CIDR:
        logger.info("host_cable_already_configured", extra={"method": method, "cidr": current_addresses})
        return

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
    bash(f"sudo nmcli con up {HOST_NM_CONNECTION}")


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
            bail(messages.NO_DHCP_LEASE_RECEIVED, timeout_seconds=DHCP_LEASE_WAIT_SECONDS, box_ip=BOX_IP)
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
        bail(messages.NO_BOX_WIRED_CONNECTION, raw=repr(raw))
    return candidates[0]


def _acquire_images(host_ip: str, build: bool, docker: str, service_shas: dict[str, str]) -> dict[str, str]:
    if not build:
        zed_image = f"{GHCR_BASE}/zed-capture:{service_shas['ZED_CAPTURE_SHA']}"
        bridge_image = f"{GHCR_BASE}/aoa-bridge:{service_shas['AOA_BRIDGE_SHA']}"
        logger.info("pulling_images_from_ghcr", extra={"zed": zed_image, "bridge": bridge_image})
        try:
            _ssh(f'"{docker} pull {zed_image}"')
            _ssh(f'"{docker} pull {bridge_image}"')
        except CalledProcessError:
            bail(messages.IMAGE_PULL_FAILED)
        return {"zed_capture": zed_image, "aoa_bridge": bridge_image}

    # Local registry instead of `docker save | ssh docker load`: pulls are
    # layer-aware, so iterative dev only ships changed layers across the
    # cable.

    # Docker treats `localhost` as insecure-by-default for push; the box's
    # daemon needs the box-facing host IP in its insecure-registries.
    if need_registry_start():
        bash(
            f"docker run -d -p {REGISTRY_PORT}:{REGISTRY_PORT} --name registry --restart unless-stopped"
            f" {REGISTRY_IMAGE}"
        )
    elif need_registry_restart():
        bash("docker start registry")

    local_zed = f"localhost:{REGISTRY_PORT}/zed-capture:{service_shas['ZED_CAPTURE_SHA']}"
    local_bridge = f"localhost:{REGISTRY_PORT}/aoa-bridge:{service_shas['AOA_BRIDGE_SHA']}"
    remote_zed = f"{host_ip}:{REGISTRY_PORT}/zed-capture:{service_shas['ZED_CAPTURE_SHA']}"
    remote_bridge = f"{host_ip}:{REGISTRY_PORT}/aoa-bridge:{service_shas['AOA_BRIDGE_SHA']}"

    logger.info("cross_compiling_images", extra={"bake_file": str(BAKE_FILE)})
    env_prefix = " ".join(f"{k}={v}" for k, v in service_shas.items())
    bash(
        f"env {env_prefix} docker buildx bake -f {BAKE_FILE}"
        f" --set zed-capture.tags={local_zed}"
        f" --set aoa-bridge.tags={local_bridge}"
        " --push --provenance=false --sbom=false zed-capture aoa-bridge",
    )

    if need_box_insecure_registry_config(host_ip):
        config = json.loads(_ssh_output('"cat /etc/docker/daemon.json"').strip())
        registries: list[str] = config.get("insecure-registries", [])
        registries.append(f"{host_ip}:{REGISTRY_PORT}")
        config["insecure-registries"] = registries
        _ssh("sudo tee /etc/docker/daemon.json", stdin_text=json.dumps(config, indent=2))
        _ssh('"sudo systemctl restart docker"')

    logger.info("pulling_images_from_local_registry", extra={"registry": f"{host_ip}:{REGISTRY_PORT}"})
    _ssh(f'"{docker} pull {remote_zed}"')
    _ssh(f'"{docker} pull {remote_bridge}"')
    return {"zed_capture": remote_zed, "aoa_bridge": remote_bridge}


def need_ssh_key_generate() -> bool:
    if SSH_KEY.exists():
        logger.info("ssh_key_exists", extra={"path": str(SSH_KEY)})
        return False
    logger.info("generating_ssh_key", extra={"path": str(SSH_KEY)})
    return True


def need_sudoers_write() -> bool:
    if _ssh_check('"test -f /etc/sudoers.d/install-zed"'):
        current = _ssh_output('"cat /etc/sudoers.d/install-zed"').strip()
        if current == SUDOERS_RULE:
            logger.info("sudoers_rule_present")
            return False
    logger.info("installing_sudoers_rule")
    return True


def need_docker_install() -> bool:
    if _ssh_check("which docker"):
        logger.info("docker_already_installed")
        return False
    logger.info("installing_docker")
    return True


def need_nvidia_runtime_configure() -> bool:
    if _ssh_check('"test -f /etc/docker/daemon.json"') and _ssh_check('"grep -q nvidia /etc/docker/daemon.json"'):
        logger.info("nvidia_runtime_already_configured")
        return False
    logger.info("configuring_nvidia_runtime")
    return True


def need_etc_hosts_entry(box_hostname: str) -> bool:
    if _ssh_check(f'"grep -q {box_hostname} /etc/hosts"'):
        logger.info("etc_hosts_entry_present", extra={"hostname": box_hostname})
        return False
    logger.info("adding_etc_hosts_entry", extra={"hostname": box_hostname})
    return True


def need_ip_forward_enable() -> bool:
    sysctl_path = Path(HOST_SYSCTL_FILE)
    if sysctl_path.exists() and sysctl_path.read_text() == HOST_SYSCTL_CONTENT:
        logger.info("ip_forward_already_enabled", extra={"path": HOST_SYSCTL_FILE})
        return False
    logger.info("enabling_ip_forward", extra={"path": HOST_SYSCTL_FILE})
    return True


def need_firewalld_trusted_source_add() -> bool:
    if bash_check(f"sudo firewall-cmd --permanent --zone=trusted --query-source={BOX_SUBNET}"):
        logger.info("firewalld_trusted_source_present", extra={"source": BOX_SUBNET})
        return False
    logger.info("adding_firewalld_trusted_source", extra={"source": BOX_SUBNET})
    return True


def need_firewalld_masquerade_enable() -> bool:
    if bash_check("sudo firewall-cmd --permanent --zone=public --query-masquerade"):
        logger.info("firewalld_masquerade_already_enabled")
        return False
    logger.info("enabling_firewalld_masquerade")
    return True


def need_registry_start() -> bool:
    if bash_check("docker container inspect registry"):
        return False
    logger.info("starting_local_registry", extra={"port": REGISTRY_PORT})
    return True


def need_registry_restart() -> bool:
    if bash_output('docker inspect -f "{{.State.Running}}" registry').strip() == "true":
        logger.info("local_registry_already_running")
        return False
    logger.info("restarting_local_registry")
    return True


def need_box_insecure_registry_config(host_ip: str) -> bool:
    if _ssh_check(f'"grep -q {host_ip}:{REGISTRY_PORT} /etc/docker/daemon.json"'):
        logger.info("box_insecure_registry_present", extra={"registry": f"{host_ip}:{REGISTRY_PORT}"})
        return False
    logger.info("configuring_box_insecure_registry", extra={"registry": f"{host_ip}:{REGISTRY_PORT}"})
    return True


def _ssh(command: str, stdin_text: str | None = None) -> None:
    bash(f"ssh {SSH_MUX} {BOX_SSH_TARGET} {command}", stdin_text=stdin_text)


def _ssh_check(command: str) -> bool:
    return bash_check(f"ssh {SSH_MUX} {BOX_SSH_TARGET} {command}")


def _ssh_output(command: str) -> str:
    return bash_output(f"ssh {SSH_MUX} {BOX_SSH_TARGET} {command}")
