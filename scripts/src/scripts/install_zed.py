import json
import tempfile
from contextlib import ExitStack
from pathlib import Path

import typer
from build_scripts.placeframe.context_sha import compute_service_shas
from common.bash import bash, bash_check, bash_output

app = typer.Typer()

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

DOCKER_DEB_BASE = "https://download.docker.com/linux/ubuntu/dists/jammy/pool/stable/arm64"
DOCKER_DEBS = [
    "containerd.io_2.2.2-1~ubuntu.22.04~jammy_arm64.deb",
    "docker-ce-cli_29.3.1-1~ubuntu.22.04~jammy_arm64.deb",
    "docker-ce_29.3.1-1~ubuntu.22.04~jammy_arm64.deb",
    "docker-buildx-plugin_0.33.0-1~ubuntu.22.04~jammy_arm64.deb",
    "docker-compose-plugin_5.1.1-1~ubuntu.22.04~jammy_arm64.deb",
]

SUDOERS_RULE = (
    "user ALL=(ALL) NOPASSWD: /usr/bin/dpkg, /usr/sbin/usermod, /usr/bin/nvidia-ctk,"
    " /usr/bin/systemctl, /usr/bin/docker, /usr/bin/tee, /usr/bin/nmcli"
)

# Disabling NVIDIA's stock USB device-mode service is the cornerstone of the
# AOA migration: it pins the Jetson's USB-C port as a USB gadget (Ethernet +
# mass-storage), which is incompatible with the ZED being a USB host for the
# phone-as-accessory link. Once disabled, udev's stock OTG role-switch makes
# the port available for host duty.
L4T_USB_DEVICE_MODE_UNIT = "nv-l4t-usb-device-mode.service"


@app.command()
def main(
    host: str = typer.Option(
        "user@10.0.0.1",
        help="SSH target for the ZED Box. Default assumes direct ethernet cable host-to-box; override with --host user@<ip> for shared-LAN setups.",
    ),
    build: bool = typer.Option(False, "--build", help="Cross-compile zed-capture locally instead of pulling from ghcr"),
) -> None:
    with ExitStack() as stack:
        _install(stack, host, build)


def _install(stack: ExitStack, host: str, build: bool) -> None:
    shas = compute_service_shas(REPO_ROOT, BAKE_FILE)

    # SSH bootstrap: key + control master + passwordless sudo. One-time setup
    # the first time you target a given box.
    if not SSH_KEY.exists():
        print("  Generating SSH key...")
        SSH_KEY.parent.mkdir(parents=True, exist_ok=True)
        bash(f'ssh-keygen -t ed25519 -N "" -f {SSH_KEY}')
    if not bash_check(f"ssh -o BatchMode=yes -o ConnectTimeout=5 {host} true"):
        print("  Copying SSH key to ZED Box (you will be prompted for the password one last time)...")
        bash(f"ssh-copy-id -i {SSH_KEY} {host}")
    print("Connecting to ZED Box...")
    bash(f"ssh {SSH_MUX} -fN {host}")
    # Best-effort: tear down the SSH control master at exit; ignore if it's already gone.
    stack.callback(lambda: bash_check(f"ssh -o ControlPath={SSH_SOCKET} -O exit {host}"))

    if _ssh_output(host, '"cat /etc/sudoers.d/install-zed 2>/dev/null || true"').strip() != SUDOERS_RULE:
        print("  Configuring passwordless sudo (will prompt for sudo password one last time)...")
        bash(f"ssh -t {SSH_MUX} {host} \"echo '{SUDOERS_RULE}' | sudo tee /etc/sudoers.d/install-zed > /dev/null\"")

    fresh_install = not _ssh_check(host, "which docker")
    if fresh_install:
        with tempfile.TemporaryDirectory() as tmpdir:
            print("Downloading Docker packages...")
            for deb in DOCKER_DEBS:
                bash(f"curl -fsSL -o {tmpdir}/{deb} {DOCKER_DEB_BASE}/{deb}")
            print("Transferring packages to ZED Box...")
            for deb in DOCKER_DEBS:
                bash(f"scp {SSH_MUX} {tmpdir}/{deb} {host}:/tmp/{deb}")
        debs_str = " ".join(f"/tmp/{deb}" for deb in DOCKER_DEBS)
        print("Installing Docker on ZED Box...")
        _ssh(host, f'"sudo dpkg -i {debs_str} && sudo usermod -aG docker {host.split("@")[0]} && rm {debs_str}"')
    else:
        print("Docker already installed, skipping")
    # Right after install, the user isn't yet picked up in the docker group on
    # the existing SSH master, so we need sudo. Subsequent runs see docker
    # already installed and use the user's group membership directly.
    docker = "sudo docker" if fresh_install else "docker"

    if not _ssh_check(host, '"grep -q nvidia /etc/docker/daemon.json 2>/dev/null"'):
        print("  Configuring NVIDIA container runtime...")
        _ssh(host, '"sudo nvidia-ctk runtime configure --runtime=docker && sudo systemctl restart docker"')

    print("Disabling NVIDIA USB device-mode service (frees USB-C port for AOA host mode)...")
    _ssh(host, f'"sudo systemctl disable --now {L4T_USB_DEVICE_MODE_UNIT} 2>/dev/null || true"')

    # $SSH_CLIENT on the box reports the host's source IP on the established
    # SSH session — by construction the address the box can already reach the
    # host on. Used below for box-side default route, and as the local-registry
    # address inside _acquire_images' --build branch.
    host_ip = _ssh_output(host, '"echo $SSH_CLIENT"').split()[0]

    # Persistent box networking: write the default gateway and DNS into the
    # NetworkManager connection profile so they survive reboots and NM
    # resolv.conf regeneration. Pulsar's setup-agent-sandbox masquerades box
    # traffic out the host's uplink (see configure_firewalld_for_zed_box).
    # /etc/hosts self-pin suppresses sudo's "unable to resolve host" warnings.
    _configure_box_networking(host, host_ip)

    images = _acquire_images(host, host_ip, build, docker, shas)

    print("Transfer compose file to ZED Box")
    _ssh(host, f'"mkdir -p {REMOTE_DIR}"')
    bash(f"scp {SSH_MUX} {COMPOSE_SOURCE!s} {host}:{REMOTE_COMPOSE}")

    # Jetson hardware-burned serial survives OS reflashes; fall back to
    # /etc/machine-id on non-Jetson devices. ZED_BOX_ID becomes the Loki
    # stream label for relayed logs from this box.
    box_id = _ssh_output(
        host,
        "\"tr -d '\\0\\n' < /proc/device-tree/serial-number 2>/dev/null || cat /etc/machine-id\"",
    ).strip()
    if not box_id:
        raise SystemExit(
            f"Could not resolve box id on {host}: both /proc/device-tree/serial-number and /etc/machine-id are empty"
        )
    _ssh(
        host,
        f"tee {REMOTE_DIR}/.env",
        stdin_text=(
            f"ZED_IMAGE={images['zed_capture']}\nAOA_BRIDGE_IMAGE={images['aoa_bridge']}\nZED_BOX_ID={box_id}\n"
        ),
    )

    print("Install systemd unit for boot-time container recreation")
    remote_home = _ssh_output(host, '"echo $HOME"').strip()
    remote_compose_abs = f"{remote_home}/.placeframe/compose.rig.yml"
    unit_content = SYSTEMD_UNIT_SOURCE.read_text().replace("COMPOSE_PATH", remote_compose_abs)
    _ssh(host, '"sudo tee /etc/systemd/system/placeframe-zed.service > /dev/null"', stdin_text=unit_content)
    _ssh(host, '"sudo systemctl daemon-reload && sudo systemctl enable placeframe-zed.service"')

    print("Ensure ZED camera daemons are running")
    _ssh(host, '"sudo systemctl enable --now nvargus-daemon zed_x_daemon"')

    # `down` first so deploys are idempotent against any prior partially-failed
    # `up --force-recreate` (which can leave containers stuck under their
    # ID-prefixed rename, blocking the next recreate with a name conflict).
    _ssh(host, f'"{docker} compose -f {REMOTE_COMPOSE} down --remove-orphans"')
    _ssh(host, f'"{docker} compose -f {REMOTE_COMPOSE} up -d"')

    # ZED SDK warmup downloads calibration + AI models. The Jetson reaches the
    # internet over its own wired-ethernet link now (no host-side internet
    # sharing involved); the warmup just needs the box to be online.
    if not build:
        print("Warm up ZED SDK (downloads calibration + AI models)...")
        bash(
            f'ssh {SSH_MUX} {host} "{docker} compose -f {REMOTE_COMPOSE} exec zed-capture python -c \\"'
            f"import pyzed.sl as sl; c = sl.Camera(); p = sl.InitParameters(); c.open(p); c.close()"
            f'\\""'
        )

    print("Done.")


def _configure_box_networking(host: str, host_ip: str) -> None:
    print(f"Configuring persistent box networking (default via {host_ip}, DNS 8.8.8.8)...")
    _ssh(
        host,
        '"grep -q $(hostname) /etc/hosts || echo 127.0.0.1 $(hostname) | sudo tee -a /etc/hosts > /dev/null"',
    )

    if not _ssh_check(host, '"systemctl is-active --quiet NetworkManager"'):
        raise SystemExit(
            "NetworkManager is not active on the box. install-zed assumes NM\n"
            "manages the box's RJ-45 (the L4T default) so the persistent\n"
            "gateway + DNS land in /etc/NetworkManager/system-connections/.\n"
            "If the box is on systemd-networkd or another stack, persistence\n"
            "needs a different approach — adapt _configure_box_networking."
        )

    route_out = _ssh_output(host, f'"ip route get {host_ip}"').strip().split()
    if "dev" not in route_out:
        raise SystemExit(f"Could not parse box-facing interface from `ip route get {host_ip}`: {route_out!r}")
    iface = route_out[route_out.index("dev") + 1]

    conns_raw = _ssh_output(host, '"nmcli -t -f NAME,DEVICE con show --active"').strip()
    conn = ""
    for line in conns_raw.splitlines():
        name, _sep, device = line.partition(":")
        if device == iface:
            conn = name.replace("\\:", ":").replace("\\\\", "\\")
            break
    if not conn:
        raise SystemExit(f"No active NetworkManager connection on box interface {iface}. Active list: {conns_raw!r}")

    _ssh(
        host,
        f'"sudo nmcli con mod \\"{conn}\\" ipv4.gateway {host_ip} ipv4.dns 8.8.8.8 ipv4.ignore-auto-dns yes"',
    )
    _ssh(host, f'"sudo nmcli con up \\"{conn}\\""')


def _acquire_images(host: str, host_ip: str, build: bool, docker: str, shas: dict[str, str]) -> dict[str, str]:
    if build:
        # Cross-compile and serve via a local Docker registry on the host (port
        # 5000), which the box pulls from over the wired ethernet link. Pulls
        # are layer-aware — only changed layers transfer. `docker save | ssh
        # docker load` is the obvious alternative but ships the entire image
        # every run.
        #
        # Docker treats `localhost` as insecure-by-default for push; the box-
        # side daemon needs the box-facing host IP added to its
        # insecure-registries.
        if not bash_check("docker container inspect registry"):
            print("Starting local Docker registry on :5000...")
            bash("docker run -d -p 5000:5000 --name registry --restart unless-stopped registry:2")
        elif bash_output('docker inspect -f "{{.State.Running}}" registry').strip() != "true":
            print("Restarting local Docker registry...")
            bash("docker start registry")

        local_zed = f"localhost:5000/zed-capture:{shas['ZED_CAPTURE_SHA']}"
        local_bridge = f"localhost:5000/aoa-bridge:{shas['AOA_BRIDGE_SHA']}"
        remote_zed = f"{host_ip}:5000/zed-capture:{shas['ZED_CAPTURE_SHA']}"
        remote_bridge = f"{host_ip}:5000/aoa-bridge:{shas['AOA_BRIDGE_SHA']}"

        print("Cross-compiling zed-capture + aoa-bridge for ARM64 and pushing to local registry...")
        env_prefix = " ".join(f"{k}={v}" for k, v in shas.items())
        bash(
            f"env {env_prefix} docker buildx bake -f {BAKE_FILE}"
            f" --set zed-capture.tags={local_zed}"
            f" --set aoa-bridge.tags={local_bridge}"
            " --push --provenance=false --sbom=false zed-capture aoa-bridge",
        )

        if not _ssh_check(host, f'"grep -q {host_ip}:5000 /etc/docker/daemon.json 2>/dev/null"'):
            print(f"Configuring box Docker to use HTTP for {host_ip}:5000...")
            config = json.loads(_ssh_output(host, '"cat /etc/docker/daemon.json"').strip())
            registries: list[str] = config.get("insecure-registries", [])
            registries.append(f"{host_ip}:5000")
            config["insecure-registries"] = registries
            _ssh(host, "sudo tee /etc/docker/daemon.json", stdin_text=json.dumps(config, indent=2))
            _ssh(host, '"sudo systemctl restart docker"')

        print(f"Pull images on ZED Box from {host_ip}:5000...")
        _ssh(host, f'"{docker} pull {remote_zed}"')
        _ssh(host, f'"{docker} pull {remote_bridge}"')
        return {"zed_capture": remote_zed, "aoa_bridge": remote_bridge}

    zed_image = f"{GHCR_BASE}/zed-capture:{shas['ZED_CAPTURE_SHA']}"
    bridge_image = f"{GHCR_BASE}/aoa-bridge:{shas['AOA_BRIDGE_SHA']}"
    print("Pull images on ZED Box (requires box to have internet)...")
    try:
        _ssh(host, f'"{docker} pull {zed_image}"')
        _ssh(host, f'"{docker} pull {bridge_image}"')
    except Exception:
        raise SystemExit(
            "\nImage pull failed. Either the tags have not been pushed to ghcr.io yet,\n"
            "or the ZED Box is offline.\n"
            "Push via CI (merge/push to trigger the build workflow) or build\n"
            "locally with: uv run install-zed --build"
        ) from None
    return {"zed_capture": zed_image, "aoa_bridge": bridge_image}


def _ssh(host: str, command: str, stdin_text: str | None = None) -> None:
    bash(f"ssh {SSH_MUX} {host} {command}", stdin_text=stdin_text)


def _ssh_check(host: str, command: str) -> bool:
    return bash_check(f"ssh {SSH_MUX} {host} {command}")


def _ssh_output(host: str, command: str) -> str:
    return bash_output(f"ssh {SSH_MUX} {host} {command}")
