import atexit
import json
import os
import tempfile
from pathlib import Path

import typer
from build_scripts.placeframe.context_sha import compute_service_shas
from common.bash import bash, bash_check, bash_output

app = typer.Typer()

REPO_ROOT = Path(__file__).resolve().parents[3]
BAKE_FILE = REPO_ROOT / "compose.bake.yml"
COMPOSE_SOURCE = REPO_ROOT / "docker" / "zed-capture" / "compose.rig.yml"
SYSTEMD_UNIT_SOURCE = REPO_ROOT / "docker" / "zed-capture" / "placeframe-zed.service"
REMOTE_DIR = "~/.placeframe"
REMOTE_COMPOSE = f"{REMOTE_DIR}/compose.rig.yml"
SSH_SOCKET = "/tmp/deploy-rig-ssh-%C"
SSH_MUX = f"-o ControlMaster=auto -o ControlPath={SSH_SOCKET} -o ControlPersist=120"
SSH_KEY = Path.home() / ".ssh" / "id_ed25519"

USB_SUBNET = "192.168.55.0/24"
USB_HOST_IP = "192.168.55.100"
USB_INTERFACE = "usb0"

# The local registry runs on the host at :5000 and is reachable from two addresses:
#   - localhost:5000      — used by buildx to push (Docker allows HTTP to localhost by default)
#   - 192.168.55.100:5000 — used by the Jetson to pull over the direct USB-ethernet link
REGISTRY_HOST_ADDR = "localhost:5000"
REGISTRY_JETSON_ADDR = f"{USB_HOST_IP}:5000"
LOCAL_IMAGE = f"{REGISTRY_JETSON_ADDR}/zed-capture:latest"

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
    " /usr/bin/systemctl, /usr/bin/docker, /sbin/ip, /usr/bin/tee"
)


def _ensure_ssh_key() -> None:
    if SSH_KEY.exists():
        return
    print("  Generating SSH key...")
    SSH_KEY.parent.mkdir(parents=True, exist_ok=True)
    bash(f'ssh-keygen -t ed25519 -N "" -f {SSH_KEY}')


def _ensure_ssh_key_copied(host: str) -> None:
    if bash_check(f"ssh -o BatchMode=yes -o ConnectTimeout=5 {host} true"):
        return
    print("  Copying SSH key to ZED Box (you will be prompted for the password one last time)...")
    bash(f"ssh-copy-id -i {SSH_KEY} {host}")


def _setup_nopasswd_sudo(host: str) -> None:
    remote_rule = bash_output(f'ssh {SSH_MUX} {host} "cat /etc/sudoers.d/deploy-rig 2>/dev/null || true"').strip()
    if remote_rule == SUDOERS_RULE:
        return
    print("  Configuring passwordless sudo (will prompt for sudo password one last time)...")
    bash(f"ssh -t {SSH_MUX} {host} \"echo '{SUDOERS_RULE}' | sudo tee /etc/sudoers.d/deploy-rig > /dev/null\"")


def _install_docker_remote(host: str) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        print("  Downloading Docker packages...")
        for deb in DOCKER_DEBS:
            bash(f"curl -fsSL -o {tmpdir}/{deb} {DOCKER_DEB_BASE}/{deb}")
        print("  Transferring packages to ZED Box...")
        for deb in DOCKER_DEBS:
            bash(f"scp {SSH_MUX} {tmpdir}/{deb} {host}:/tmp/{deb}")

    debs_str = " ".join(f"/tmp/{deb}" for deb in DOCKER_DEBS)
    user = host.split("@")[0]
    print("  Installing Docker on ZED Box...")
    bash(f'ssh {SSH_MUX} {host} "sudo dpkg -i {debs_str} && sudo usermod -aG docker {user} && rm /tmp/*.deb"')


def _enable_internet_sharing(host: str) -> None:
    # Enable IP forwarding + NAT on host in a single sudo call.
    # sysctl is idempotent; iptables -C checks if rule exists, adds only if missing.
    print("  Configuring host networking (may require sudo)...")
    bash(
        f"sudo sh -c '"
        f"sysctl -w net.ipv4.ip_forward=1"
        f" && (iptables -t nat -C POSTROUTING -s {USB_SUBNET} -j MASQUERADE 2>/dev/null"
        f" || iptables -t nat -A POSTROUTING -s {USB_SUBNET} -j MASQUERADE)'"
    )

    # Set up routing and DNS on the Jetson
    # Ensure the Jetson's hostname is in /etc/hosts (suppresses sudo warnings)
    bash(
        f'ssh {SSH_MUX} {host} "'
        f"grep -q $(hostname) /etc/hosts || echo 127.0.0.1 $(hostname) | sudo tee -a /etc/hosts > /dev/null"
        f" && sudo ip route replace default via {USB_HOST_IP}"
        f" && (grep -q 'nameserver 8.8.8.8' /etc/resolv.conf"
        f" || echo 'nameserver 8.8.8.8' | sudo tee -a /etc/resolv.conf > /dev/null)\""
    )


def _disable_internet_sharing(host: str) -> None:
    bash_check(f'ssh {SSH_MUX} {host} "sudo ip route del default via {USB_HOST_IP} 2>/dev/null || true"')
    bash_check(f"sudo iptables -t nat -D POSTROUTING -s {USB_SUBNET} -j MASQUERADE")


def _compute_shas() -> dict[str, str]:
    return compute_service_shas(REPO_ROOT, BAKE_FILE)


def _ensure_local_registry() -> None:
    if bash_check("docker container inspect registry"):
        state = bash_output('docker inspect -f "{{.State.Running}}" registry').strip()
        if state == "true":
            print("  Local registry already running")
            return
        print("  Removing stopped registry container...")
        bash("docker rm -f registry")
    print("  Starting local Docker registry on :5000...")
    bash("docker run -d -p 5000:5000 --name registry --restart unless-stopped registry:2")


def _build_and_push(shas: dict[str, str]) -> None:
    os.environ.update(shas)
    print("  Cross-compiling zed-capture for ARM64...")
    bash(
        f"docker buildx bake -f {BAKE_FILE}"
        f" --set zed-capture.tags={REGISTRY_HOST_ADDR}/zed-capture:latest"
        " --push --provenance=false --sbom=false zed-capture",
    )


def _allow_http_registry_on_jetson(host: str) -> None:
    # Docker defaults to HTTPS for all registries. The local registry is plain HTTP, but that's
    # fine here — traffic goes over a direct USB-ethernet cable with no network in between.
    # This adds the host's USB IP to the Jetson's "insecure-registries" (Docker's name for "use HTTP").
    if bash_check(f'ssh {SSH_MUX} {host} "grep -q {REGISTRY_JETSON_ADDR} /etc/docker/daemon.json 2>/dev/null"'):
        return
    print(f"  Configuring Jetson Docker to use HTTP for {REGISTRY_JETSON_ADDR}...")
    existing = bash_output(f'ssh {SSH_MUX} {host} "cat /etc/docker/daemon.json"').strip()
    config = json.loads(existing)
    registries: list[str] = config.get("insecure-registries", [])
    if REGISTRY_JETSON_ADDR not in registries:
        registries.append(REGISTRY_JETSON_ADDR)
    config["insecure-registries"] = registries
    bash(
        f"ssh {SSH_MUX} {host} sudo tee /etc/docker/daemon.json",
        stdin_text=json.dumps(config, indent=2),
    )
    bash(f'ssh {SSH_MUX} {host} "sudo systemctl restart docker"')


@app.command()
def main(
    host: str = typer.Option("user@192.168.55.1", help="SSH target for the ZED Box"),
    local: bool = typer.Option(
        False, help="Build ARM64 locally and push via local registry instead of pulling from ghcr"
    ),
) -> None:
    shas = _compute_shas()

    if local:
        print("Step 0: Build ARM64 image locally and push to local registry...")
        _ensure_local_registry()
        _build_and_push(shas)

    # One-time setup: SSH key + copy to ZED Box (single password prompt, never again)
    _ensure_ssh_key()
    _ensure_ssh_key_copied(host)

    print("Connecting to ZED Box...")
    bash(f"ssh {SSH_MUX} -fN {host}")
    atexit.register(lambda: bash_check(f"ssh -o ControlPath={SSH_SOCKET} -O exit {host}"))

    # One-time setup: passwordless sudo for deploy commands
    _setup_nopasswd_sudo(host)

    fresh_install = not bash_check(f"ssh {SSH_MUX} {host} which docker")
    if fresh_install:
        print("Step 1: Install Docker on ZED Box")
        _install_docker_remote(host)
    else:
        print("Step 1: Docker already installed, skipping")

    docker = "sudo docker" if fresh_install else "docker"

    if not bash_check(f'ssh {SSH_MUX} {host} "grep -q nvidia /etc/docker/daemon.json 2>/dev/null"'):
        print("  Configuring NVIDIA container runtime...")
        bash(
            f'ssh {SSH_MUX} {host} "sudo nvidia-ctk runtime configure --runtime=docker && sudo systemctl restart docker"'
        )

    if local:
        _allow_http_registry_on_jetson(host)
        print("Step 2: Pull local image on ZED Box...")
        bash(f'ssh {SSH_MUX} {host} "{docker} pull {LOCAL_IMAGE}"')
    else:
        print("Step 2: Enable internet sharing over USB...")
        _enable_internet_sharing(host)
        atexit.register(lambda: _disable_internet_sharing(host))

        print("Step 3: Pull image on ZED Box (layer-aware, only changed layers download)...")
        image = f"ghcr.io/outernet-foundation/placeframe/zed-capture:{shas['ZED_CAPTURE_SHA']}"
        try:
            bash(f'ssh {SSH_MUX} {host} "{docker} pull {image}"')
        except Exception:
            tag = shas["ZED_CAPTURE_SHA"]
            raise SystemExit(
                f"\nImage not found: zed-capture:{tag}\n"
                "This tag has not been pushed to ghcr.io yet.\n"
                "Either push via CI (merge/push to trigger the build workflow)\n"
                "or build locally with: uv run deploy-rig --local"
            ) from None

    print("Step 4: Transfer compose file to ZED Box")
    bash(f'ssh {SSH_MUX} {host} "mkdir -p {REMOTE_DIR}"')
    bash(f"scp {SSH_MUX} {COMPOSE_SOURCE!s} {host}:{REMOTE_COMPOSE}")

    env_line = f"ZED_IMAGE={LOCAL_IMAGE}" if local else f"ZED_CAPTURE_SHA={shas['ZED_CAPTURE_SHA']}"
    bash(f"ssh {SSH_MUX} {host} tee {REMOTE_DIR}/.env", stdin_text=env_line)

    print("Step 5: Install systemd unit for boot-time container recreation")
    remote_home = bash_output(f'ssh {SSH_MUX} {host} "echo $HOME"').strip()
    remote_compose_abs = f"{remote_home}/.placeframe/compose.rig.yml"
    unit_content = SYSTEMD_UNIT_SOURCE.read_text().replace("COMPOSE_PATH", remote_compose_abs)
    bash(
        f'ssh {SSH_MUX} {host} "sudo tee /etc/systemd/system/placeframe-zed.service > /dev/null"',
        stdin_text=unit_content,
    )
    bash(f'ssh {SSH_MUX} {host} "sudo systemctl daemon-reload && sudo systemctl enable placeframe-zed.service"')

    print("Step 6: Ensure ZED camera daemons are running")
    bash(f'ssh {SSH_MUX} {host} "sudo systemctl enable --now nvargus-daemon zed_x_daemon"')

    print("Step 7: Start container on ZED Box")
    bash(f'ssh {SSH_MUX} {host} "{docker} compose -f {REMOTE_COMPOSE} up -d --force-recreate"')

    if not local:
        container = f"{docker} compose -f {REMOTE_COMPOSE} exec zed-capture"
        print("Step 8: Warm up ZED SDK (downloads calibration + AI models while internet is available)...")
        bash(
            f'ssh {SSH_MUX} {host} "{container} python -c \\"'
            f"import pyzed.sl as sl; c = sl.Camera(); p = sl.InitParameters(); c.open(p); c.close()"
            f'\\""'
        )

    print("Done.")
