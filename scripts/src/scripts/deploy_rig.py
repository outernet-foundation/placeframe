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

L4T_RUNTIME_START_SH = "/opt/nvidia/l4t-usb-device-mode/nv-l4t-usb-device-mode-runtime-start.sh"
L4T_USB_RUNTIME_UNIT = "nv-l4t-usb-device-mode-runtime.service"
PLACEFRAME_CAPTIVE_PORTAL_MARKER = "placeframe-captive-portal-fix"
DHCP_LEASE_SECONDS = 3600


def _ssh(host: str, command: str, stdin_text: str | None = None) -> None:
    bash(f"ssh {SSH_MUX} {host} {command}", stdin_text=stdin_text)


def _ssh_check(host: str, command: str) -> bool:
    return bash_check(f"ssh {SSH_MUX} {host} {command}")


def _ssh_output(host: str, command: str) -> str:
    return bash_output(f"ssh {SSH_MUX} {host} {command}")


def _resolve_box_id(host: str) -> str:
    # Jetson hardware-burned serial survives OS reflashes; fall back to
    # /etc/machine-id on non-Jetson devices. ZED_BOX_ID becomes the Loki
    # stream label for relayed logs from this box.
    serial = _ssh_output(
        host,
        '"tr -d \'\\0\\n\' < /proc/device-tree/serial-number 2>/dev/null || cat /etc/machine-id"',
    ).strip()
    if not serial:
        raise SystemExit(f"Could not resolve box id on {host}: both /proc/device-tree/serial-number and /etc/machine-id are empty")
    return serial


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
    remote_rule = _ssh_output(host, '"cat /etc/sudoers.d/deploy-rig 2>/dev/null || true"').strip()
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
    _ssh(host, f'"sudo dpkg -i {debs_str} && sudo usermod -aG docker {user} && rm /tmp/*.deb"')


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
    _ssh_check(host, f'"sudo ip route del default via {USB_HOST_IP} 2>/dev/null || true"')
    bash_check(f"sudo iptables -t nat -D POSTROUTING -s {USB_SUBNET} -j MASQUERADE")


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


def _patch_or_exit(content: str, already_applied: bool, anchor: str, replacement: str, label: str) -> str:
    if already_applied:
        return content
    if anchor not in content:
        raise SystemExit(
            f"\nCould not locate {label} in {L4T_RUNTIME_START_SH}.\n"
            "NVIDIA may have changed the heredoc shape in this L4T release.\n"
            "Update the anchor in _setup_captive_portal_dhcp."
        )
    return content.replace(anchor, replacement)


def _setup_captive_portal_dhcp(host: str) -> None:
    # Two patches into NVIDIA's runtime-start.sh, both targeting the inline
    # heredoc that regenerates /opt/nvidia/l4t-usb-device-mode/dhcpd.conf on
    # every cable connect. Editing the generated conf directly is silently
    # overwritten on the next plug; editing the heredoc itself sticks.
    #
    # Patch 1 — captive-portal DNS option. Android's NetworkMonitor probes
    # connectivitycheck.gstatic.com/generate_204 over every new network. The
    # USB-ethernet link has no internet, so probes fail and the network is
    # marked unvalidated. We advertise the Jetson as DNS server via DHCP
    # option 6 here; the captive-portal-responder service in compose.rig.yml
    # answers the DNS+HTTP probes so validation passes.
    #
    # Patch 2 — DHCP lease times. NVIDIA's stock heredoc references
    # ${net_dhcp_lease_time} which resolves to 15 seconds (either via L4T's
    # config XML or because the variable is unset and dhcpd falls back to its
    # 15s compile-time minimum). Android's DhcpClient schedules renewal at
    # ~29s (its internal minimum), so the lease expires before renewal: kernel
    # removes 192.168.55.100 from usb0, EthernetNetworkFactory restarts
    # IpClient, kernel destroys live TCP sockets, in-flight HTTP calls die
    # with `java.net.SocketException: Software caused connection abort`. We
    # hardcode both lease-time directives in the heredoc to a sane value.
    #
    # Idempotency: each patch's anchor is the original NVIDIA text, so once a
    # patch is applied its anchor no longer matches and re-running is a no-op.
    # ISC dhcpd doesn't reread on SIGHUP; we restart the L4T runtime unit to
    # force regeneration (cable must be plugged in for l4tbr0 to exist).
    if not _ssh_check(host, f'"test -f {L4T_RUNTIME_START_SH}"'):
        raise SystemExit(
            f"\n{L4T_RUNTIME_START_SH} not found on {host}.\n"
            "This deploy step assumes NVIDIA's stock L4T USB device mode setup.\n"
            "If your Jetson uses a non-standard DHCP setup, the captive-portal\n"
            "fix needs to be retargeted at whatever serves DHCP for l4tbr0.\n"
            "See docker/zed-capture/CLAUDE.md for the design rationale."
        )
    current = _ssh_output(host, f"cat {L4T_RUNTIME_START_SH}")
    new_content = current

    # Anchors below match the heredoc shape in NVIDIA's stock script (verified
    # on L4T R36). If a future L4T release tweaks the heredoc, neither anchor
    # will match — _patch_or_exit raises SystemExit with a pointer to update.
    captive_portal_anchor = "    range ${net_dhcp_start} ${net_dhcp_end};\n}"
    captive_portal_injected = (
        "    range ${net_dhcp_start} ${net_dhcp_end};\n"
        f"    # {PLACEFRAME_CAPTIVE_PORTAL_MARKER}: spoof DNS so Android's\n"
        "    # NetworkMonitor probe resolves to captive-portal-responder and\n"
        "    # the link validates instead of restart-looping IpClient.\n"
        "    option domain-name-servers 192.168.55.1;\n}"
    )
    new_content = _patch_or_exit(
        new_content,
        PLACEFRAME_CAPTIVE_PORTAL_MARKER in current,
        captive_portal_anchor,
        captive_portal_injected,
        "dhcpd heredoc subnet block",
    )

    lease_anchor = "max-lease-time ${net_dhcp_lease_time};\ndefault-lease-time ${net_dhcp_lease_time};"
    lease_replacement = f"max-lease-time {DHCP_LEASE_SECONDS};\ndefault-lease-time {DHCP_LEASE_SECONDS};"
    new_content = _patch_or_exit(
        new_content,
        lease_replacement in current,
        lease_anchor,
        lease_replacement,
        "lease-time directives",
    )

    if new_content != current:
        print(f"  Patching {L4T_RUNTIME_START_SH}...")
        # `sudo tee` preserves the existing file mode, so no chmod needed
        # (and chmod isn't in the NOPASSWD allowlist anyway).
        _ssh(host, f"sudo tee {L4T_RUNTIME_START_SH} > /dev/null", stdin_text=new_content)

    # Verify the regenerated dhcpd.conf actually picked up both patches, and
    # restart the runtime unit only if it didn't. This makes the function
    # self-healing across partial-failure re-runs and a no-op once the
    # generated conf is correct. The conf file only exists once the cable has
    # been up at least once (regenerated on plug).
    dhcpd_conf = "/opt/nvidia/l4t-usb-device-mode/dhcpd.conf"
    if _ssh_check(host, f'"test -f {dhcpd_conf}"'):
        regenerated = _ssh_output(host, f"cat {dhcpd_conf}")
        if (
            "option domain-name-servers 192.168.55.1" in regenerated
            and f"max-lease-time {DHCP_LEASE_SECONDS}" in regenerated
        ):
            return
    print(f"  Restarting {L4T_USB_RUNTIME_UNIT} (cable must be plugged in)...")
    _ssh(host, f'"sudo systemctl restart {L4T_USB_RUNTIME_UNIT}"')


def _allow_http_registry_on_jetson(host: str) -> None:
    # Docker defaults to HTTPS for all registries. The local registry is plain HTTP, but that's
    # fine here — traffic goes over a direct USB-ethernet cable with no network in between.
    # This adds the host's USB IP to the Jetson's "insecure-registries" (Docker's name for "use HTTP").
    if _ssh_check(host, f'"grep -q {REGISTRY_JETSON_ADDR} /etc/docker/daemon.json 2>/dev/null"'):
        return
    print(f"  Configuring Jetson Docker to use HTTP for {REGISTRY_JETSON_ADDR}...")
    existing = _ssh_output(host, '"cat /etc/docker/daemon.json"').strip()
    config = json.loads(existing)
    registries: list[str] = config.get("insecure-registries", [])
    if REGISTRY_JETSON_ADDR not in registries:
        registries.append(REGISTRY_JETSON_ADDR)
    config["insecure-registries"] = registries
    _ssh(host, "sudo tee /etc/docker/daemon.json", stdin_text=json.dumps(config, indent=2))
    _ssh(host, '"sudo systemctl restart docker"')


@app.command()
def main(
    host: str = typer.Option("user@192.168.55.1", help="SSH target for the ZED Box"),
    local: bool = typer.Option(
        False, help="Build ARM64 locally and push via local registry instead of pulling from ghcr"
    ),
) -> None:
    shas = compute_service_shas(REPO_ROOT, BAKE_FILE)

    if local:
        print("Build ARM64 image locally and push to local registry...")
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

    fresh_install = not _ssh_check(host, "which docker")
    if fresh_install:
        print("Install Docker on ZED Box")
        _install_docker_remote(host)
    else:
        print("Docker already installed, skipping")

    docker = "sudo docker" if fresh_install else "docker"

    if not _ssh_check(host, '"grep -q nvidia /etc/docker/daemon.json 2>/dev/null"'):
        print("  Configuring NVIDIA container runtime...")
        _ssh(host, '"sudo nvidia-ctk runtime configure --runtime=docker && sudo systemctl restart docker"')

    if local:
        _allow_http_registry_on_jetson(host)
        print("Pull local image on ZED Box...")
        _ssh(host, f'"{docker} pull {LOCAL_IMAGE}"')
    else:
        print("Enable internet sharing over USB...")
        _enable_internet_sharing(host)
        atexit.register(lambda: _disable_internet_sharing(host))

        print("Pull image on ZED Box (layer-aware, only changed layers download)...")
        image = f"ghcr.io/outernet-foundation/placeframe/zed-capture:{shas['ZED_CAPTURE_SHA']}"
        try:
            _ssh(host, f'"{docker} pull {image}"')
        except Exception:
            tag = shas["ZED_CAPTURE_SHA"]
            raise SystemExit(
                f"\nImage not found: zed-capture:{tag}\n"
                "This tag has not been pushed to ghcr.io yet.\n"
                "Either push via CI (merge/push to trigger the build workflow)\n"
                "or build locally with: uv run deploy-rig --local"
            ) from None

    print("Transfer compose file to ZED Box")
    _ssh(host, f'"mkdir -p {REMOTE_DIR}"')
    bash(f"scp {SSH_MUX} {COMPOSE_SOURCE!s} {host}:{REMOTE_COMPOSE}")

    image_env = f"ZED_IMAGE={LOCAL_IMAGE}" if local else f"ZED_CAPTURE_SHA={shas['ZED_CAPTURE_SHA']}"
    box_id = _resolve_box_id(host)
    env_text = f"{image_env}\nZED_BOX_ID={box_id}\n"
    _ssh(host, f"tee {REMOTE_DIR}/.env", stdin_text=env_text)

    print("Install systemd unit for boot-time container recreation")
    remote_home = _ssh_output(host, '"echo $HOME"').strip()
    remote_compose_abs = f"{remote_home}/.placeframe/compose.rig.yml"
    unit_content = SYSTEMD_UNIT_SOURCE.read_text().replace("COMPOSE_PATH", remote_compose_abs)
    _ssh(host, '"sudo tee /etc/systemd/system/placeframe-zed.service > /dev/null"', stdin_text=unit_content)
    _ssh(host, '"sudo systemctl daemon-reload && sudo systemctl enable placeframe-zed.service"')

    print("Ensure ZED camera daemons are running")
    _ssh(host, '"sudo systemctl enable --now nvargus-daemon zed_x_daemon"')

    print("Configure captive-portal DHCP option")
    _setup_captive_portal_dhcp(host)

    print("Start container on ZED Box")
    _ssh(host, f'"{docker} compose -f {REMOTE_COMPOSE} up -d --force-recreate"')

    if not local:
        container = f"{docker} compose -f {REMOTE_COMPOSE} exec zed-capture"
        print("Warm up ZED SDK (downloads calibration + AI models while internet is available)...")
        bash(
            f'ssh {SSH_MUX} {host} "{container} python -c \\"'
            f"import pyzed.sl as sl; c = sl.Camera(); p = sl.InitParameters(); c.open(p); c.close()"
            f'\\""'
        )

    print("Done.")
