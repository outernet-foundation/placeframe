import json
import platform
import shlex
import socket
import tempfile
import time
from logging import getLogger
from pathlib import Path
from subprocess import CalledProcessError

from bashrun import bash, bash_check, bash_output
from common.ui import bail, note

from .constants import (
    APPLIANCE_BANNER_PATHS,
    APPLIANCE_BANNER_TEXT,
    APPLIANCE_DEFAULT_TARGET,
    APPLIANCE_SYSTEM_UNITS_TO_MASK,
    APPLIANCE_USER_UNITS_TO_MASK,
    BAKE_FILE,
    BOX_IP,
    BOX_REACHABLE_PROBE_SECONDS,
    BOX_SSH_TARGET,
    COMPOSE_SOURCE,
    DHCP_LEASE_WAIT_SECONDS,
    DOCKER_DEB_BASE,
    DOCKER_DEBS,
    GHCR_BASE,
    L4T_USB_DEVICE_MODE_UNIT,
    REGISTRY_IMAGE,
    REGISTRY_PORT,
    REMOTE_COMPOSE,
    REMOTE_DIR,
    REMOTE_WAIT_FOR_ZED_CAMERA,
    SSH_KEY,
    SSH_MUX,
    SSH_SOCKET,
    SUDOERS_RULE,
    SYSTEMD_UNIT_SOURCE,
    WAIT_FOR_ZED_CAMERA_SOURCE,
    ZED_SERVICES,
)
from .host_setup import set_host_link_method
from .messages import (
    ARM64_EMULATION_MISSING,
    BOX_ID_UNRESOLVABLE,
    BOX_INTERFACE_UNPARSEABLE,
    IMAGE_PULL_FAILED,
    NO_ACTIVE_NM_CONNECTION,
    NO_BOX_WIRED_CONNECTION,
    NO_DHCP_LEASE_RECEIVED,
    SSH_KEY_COPY_PROMPT,
)
from .ssh import ssh_check, ssh_output, ssh_run

logger = getLogger(__name__)


def install_box(build: bool, service_shas: dict[str, str]) -> None:
    # Fail before touching the box if the host can't actually cross-build the
    # arm64 images — otherwise the missing prerequisite only surfaces as an
    # opaque `exec format error` mid-build, after the box has been reconfigured.
    if build:
        _ensure_arm64_emulation()

    # On a re-run the box already holds its static IP, so try it directly. A
    # bare TCP liveness probe separates two cases an auth-gated probe conflates:
    # the box is present but our key isn't installed (just needs ssh-copy-id),
    # versus the box is absent and needs first-contact DHCP bootstrap. Gating on
    # key auth would drop a reachable-but-unkeyed box into the DHCP path, where a
    # statically-addressed box never requests a lease and the wait times out.
    if _box_reachable_at_static_ip():
        _ensure_key_access(BOX_SSH_TARGET)
    else:
        _claim_box_via_dhcp()

    # Open one SSH connection and reuse it for every command below.
    logger.info("connecting_to_box", extra={"target": BOX_SSH_TARGET})
    bash(f"ssh {SSH_MUX} -fN {BOX_SSH_TARGET}")
    try:
        # Refresh the passwordless-sudo rule. `sudo -n install` overwrites the
        # file with identical content on subsequent runs, so this is naturally
        # idempotent; no content-comparison check is needed. The `-n` flag
        # fails loudly instead of prompting if NOPASSWD isn't in effect,
        # which surfaces a stale or missing rule as a script-fatal error
        # rather than silently degrading to interactive.
        logger.info("refreshing_sudoers_rule")
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sudoers") as sudoers_file:
            sudoers_file.write(SUDOERS_RULE + "\n")
            sudoers_file.flush()
            bash(f"scp {SSH_MUX} {sudoers_file.name} {BOX_SSH_TARGET}:/tmp/install-zed.sudoers")
            ssh_run("sudo -n install -m 0440 -o root -g root /tmp/install-zed.sudoers /etc/sudoers.d/install-zed")
            ssh_run("rm /tmp/install-zed.sudoers")

        # Install Docker from pinned .deb URLs (Ubuntu's repo is a moving target).
        if ssh_check("which docker"):
            logger.info("docker_already_installed")
        else:
            logger.info("installing_docker")
            with tempfile.TemporaryDirectory() as temp_directory:
                logger.info("downloading_docker_packages", extra={"count": len(DOCKER_DEBS)})
                for deb_file in DOCKER_DEBS:
                    bash(f"curl -fsSL -o {temp_directory}/{deb_file} {DOCKER_DEB_BASE}/{deb_file}")
                logger.info("transferring_docker_packages", extra={"target": BOX_SSH_TARGET})
                for deb_file in DOCKER_DEBS:
                    bash(f"scp {SSH_MUX} {temp_directory}/{deb_file} {BOX_SSH_TARGET}:/tmp/{deb_file}")
            deb_paths = " ".join(f"/tmp/{deb_file}" for deb_file in DOCKER_DEBS)
            box_user = BOX_SSH_TARGET.split("@")[0]
            ssh_run(f"sudo dpkg -i {deb_paths}")
            ssh_run(f"sudo usermod -aG docker {box_user}")
            ssh_run(f"rm {deb_paths}")
            logger.info("docker_installed", extra={"user": box_user})

        # Wire NVIDIA Container Toolkit into dockerd so compose's `runtime: nvidia` works.
        if ssh_check("grep -q nvidia /etc/docker/daemon.json"):
            logger.info("nvidia_runtime_already_configured")
        else:
            logger.info("configuring_nvidia_runtime")
            ssh_run("sudo nvidia-ctk runtime configure --runtime=docker")
            ssh_run("sudo systemctl restart docker")

        # Pins the Jetson's USB-C port as a USB gadget, which is incompatible
        # with the box acting as USB host for the phone-as-accessory link.
        # Disabling frees the port for host duty.
        logger.info("disabling_usb_device_mode_service", extra={"unit": L4T_USB_DEVICE_MODE_UNIT})
        ssh_check(f"sudo systemctl disable --now {L4T_USB_DEVICE_MODE_UNIT}")

        # Strip the JetPack desktop to a headless appliance; see _strip_to_appliance.
        _strip_to_appliance()

        # Add the box's hostname to /etc/hosts so sudo doesn't reverse-DNS each call.
        box_hostname = ssh_output("hostname").strip()
        if ssh_check(f"grep -q {box_hostname} /etc/hosts"):
            logger.info("etc_hosts_entry_present", extra={"hostname": box_hostname})
        else:
            logger.info("adding_etc_hosts_entry", extra={"hostname": box_hostname})
            ssh_run("sudo tee -a /etc/hosts > /dev/null", stdin_text=f"127.0.0.1 {box_hostname}\n")

        # Point the box's default gateway and DNS at the host so it can reach the internet.
        # $SSH_CLIENT is the host IP the box can already reach us on — by
        # construction the 100.64.0.0/24 address the host cable connection holds.
        host_ip = ssh_output("echo $SSH_CLIENT").split()[0]

        route_out = ssh_output(f"ip route get {host_ip}").strip().split()
        if "dev" not in route_out:
            bail(BOX_INTERFACE_UNPARSEABLE, host_ip=host_ip, route_out=repr(route_out))
        box_interface = route_out[route_out.index("dev") + 1]
        active_connections_raw = ssh_output("nmcli -t -f NAME,DEVICE con show --active").strip()
        box_connection = next(
            (
                parts[0].replace("\\:", ":").replace("\\\\", "\\")
                for line in active_connections_raw.splitlines()
                if (parts := line.partition(":"))[2] == box_interface
            ),
            "",
        )
        if not box_connection:
            bail(NO_ACTIVE_NM_CONNECTION, interface=box_interface, connections_raw=repr(active_connections_raw))
        ssh_run(
            f'sudo nmcli con mod "{box_connection}" ipv4.gateway {host_ip} ipv4.dns 8.8.8.8 ipv4.ignore-auto-dns yes'
        )
        ssh_run(f'sudo nmcli con up "{box_connection}"')

        # Acquire container images (pull from ghcr.io, or cross-compile via local registry).
        images = _acquire_images(host_ip, build, service_shas)

        # Ship the compose file and supporting scripts. The aoa-alloy /
        # aoa-loki configs ride inside the placeframe-owned wrapper images
        # acquired above; no bind-mounted configs.
        logger.info("transferring_compose_file", extra={"source": str(COMPOSE_SOURCE)})
        ssh_run(f"mkdir -p {REMOTE_DIR}")
        bash(f"scp {SSH_MUX} {COMPOSE_SOURCE!s} {BOX_SSH_TARGET}:{REMOTE_COMPOSE}")
        bash(f"scp {SSH_MUX} {WAIT_FOR_ZED_CAMERA_SOURCE!s} {BOX_SSH_TARGET}:{REMOTE_WAIT_FOR_ZED_CAMERA}")

        # Jetson hardware-burned serial survives OS reflashes.
        box_id = ssh_output("tr -d '\\0\\n' < /proc/device-tree/serial-number").strip()
        if not box_id:
            bail(BOX_ID_UNRESOLVABLE)

        # Write the .env that compose reads: built-image refs + every SHA-keyed
        # variable compose.rig.yml references (one per box image; ZED_CAPTURE_SHA
        # also feeds SERVICE_VERSION) + box hardware id for log tagging.
        box_shas = {service.sha_key: service_shas[service.sha_key] for service in ZED_SERVICES}
        env_lines = "".join(f"{key}={value}\n" for key, value in {**images, **box_shas}.items())
        ssh_run(f"tee {REMOTE_DIR}/.env", stdin_text=env_lines + f"ZED_BOX_ID={box_id}\n")

        # Install the systemd unit so the stack auto-starts on boot.
        logger.info("installing_systemd_unit", extra={"unit": "placeframe-zed.service"})
        remote_home = ssh_output("echo $HOME").strip()
        remote_compose_abs = f"{remote_home}/.placeframe/compose.rig.yml"
        remote_wait_for_zed_camera_abs = f"{remote_home}/.placeframe/wait_for_zed_camera.py"
        unit_content = (
            SYSTEMD_UNIT_SOURCE
            .read_text()
            .replace("COMPOSE_PATH", remote_compose_abs)
            .replace("WAIT_FOR_ZED_CAMERA_PATH", remote_wait_for_zed_camera_abs)
        )
        ssh_run("sudo tee /etc/systemd/system/placeframe-zed.service > /dev/null", stdin_text=unit_content)
        ssh_run("sudo systemctl daemon-reload")
        ssh_run("sudo systemctl enable placeframe-zed.service")

        # Start the host-side camera daemons; the container bind-mounts their IPC sockets.
        logger.info("enabling_camera_daemons")
        ssh_run("sudo systemctl enable --now nvargus-daemon zed_x_daemon")

        # Direct compose (not `systemctl restart placeframe-zed.service`) so the
        # install can succeed on a box without the camera attached — the unit's
        # wait_for_zed_camera ExecStartPre would otherwise time out.
        logger.info("redeploying_compose_stack", extra={"compose": REMOTE_COMPOSE})
        ssh_run(f"sudo docker compose -f {REMOTE_COMPOSE} down --remove-orphans")
        ssh_run(f"sudo docker compose -f {REMOTE_COMPOSE} up -d")

        # Trigger the ZED SDK's first-open firmware download so a real capture doesn't stall on it.
        if not build:
            logger.info("warming_zed_sdk")
            ssh_run(
                f"sudo docker compose -f {REMOTE_COMPOSE} exec zed-capture python -c "
                '"import pyzed.sl as sl; c = sl.Camera(); p = sl.InitParameters(); c.open(p); c.close()"'
            )

        logger.info("install_done")
    finally:
        # Close the SSH multiplexer (otherwise it lingers until ControlPersist expires).
        bash_check(f"ssh -o ControlPath={SSH_SOCKET} -O exit {BOX_SSH_TARGET}")


def _strip_to_appliance() -> None:
    # The stock JetPack image boots to a GNOME desktop, but the product flow is
    # cable-to-laptop then install-zed; nobody sits at the box with HDMI and a
    # keyboard. The desktop session is not just dead weight: its volume-monitor
    # probers (gvfs-mtp / gvfs-afc / gvfs-gphoto2 / gvfs-udisks2) call
    # libusb_open and read descriptors against every newly-enumerated USB
    # device. Against an AOA-mode phone those reads stall the kernel's 5s
    # USB_CTRL_GET_TIMEOUT and trip usb_reset_and_verify_device(), which
    # invalidates the accessory FD the user already granted and forces Android
    # to fire a second UsbConfirmActivity dialog inside the app.
    #
    # Four actions strip the premise: (a) set the default target to
    # multi-user.target, dropping gdm and the entire graphical session; (b) mask
    # the consumer-USB / desktop / auto-update system units
    # (APPLIANCE_SYSTEM_UNITS_TO_MASK); (c) --global mask the gvfs + evolution
    # user units (APPLIANCE_USER_UNITS_TO_MASK) so they stay off even if a
    # maintenance user shells in interactively; (d) overwrite the login banners
    # so plugging in HDMI shows a signal, not a black screen. nvargus-daemon and
    # zed_x_daemon are left running — the compose stack binds their IPC sockets.
    #
    # Strip-the-premise was chosen over symptomatic udev VID filtering. A VID
    # filter would silence this one dialog-respawn but leave the whole
    # consumer-USB-monitoring stack running on hardware that has no business
    # running it; the next latent conflict (fwupd auto-upgrading, snapd
    # refreshing, PackageKit holding the apt lock) would land in the same place.
    current_target = ssh_output("systemctl get-default").strip()
    if current_target == APPLIANCE_DEFAULT_TARGET:
        logger.info("appliance_default_target_already_set", extra={"target": current_target})
    else:
        logger.info(
            "setting_appliance_default_target",
            extra={"from": current_target, "to": APPLIANCE_DEFAULT_TARGET},
        )
        ssh_run(f"sudo systemctl set-default {APPLIANCE_DEFAULT_TARGET}")

    logger.info("masking_appliance_system_units", extra={"count": len(APPLIANCE_SYSTEM_UNITS_TO_MASK)})
    ssh_run(f"sudo systemctl mask --now {' '.join(APPLIANCE_SYSTEM_UNITS_TO_MASK)}")

    logger.info("masking_appliance_user_units", extra={"count": len(APPLIANCE_USER_UNITS_TO_MASK)})
    ssh_run(f"sudo systemctl --global mask {' '.join(APPLIANCE_USER_UNITS_TO_MASK)}")

    for banner_path in APPLIANCE_BANNER_PATHS:
        current = ssh_output(f"cat {banner_path}") if ssh_check(f"test -f {banner_path}") else ""
        if current == APPLIANCE_BANNER_TEXT:
            logger.info("appliance_banner_present", extra={"path": banner_path})
        else:
            logger.info("installing_appliance_banner", extra={"path": banner_path})
            ssh_run(f"sudo tee {banner_path} > /dev/null", stdin_text=APPLIANCE_BANNER_TEXT)


def _box_reachable_at_static_ip() -> bool:
    logger.info("probing_box_reachability", extra={"box_ip": BOX_IP, "timeout_seconds": BOX_REACHABLE_PROBE_SECONDS})
    deadline = time.monotonic() + BOX_REACHABLE_PROBE_SECONDS
    while True:
        try:
            with socket.create_connection((BOX_IP, 22), timeout=2):
                return True
        except OSError:
            if time.monotonic() >= deadline:
                return False

            time.sleep(1)


def _ensure_key_access(target: str) -> None:
    if bash_check(f"ssh -o BatchMode=yes -o ConnectTimeout=5 {target} true"):
        return

    note(SSH_KEY_COPY_PROMPT)
    bash(f"ssh-copy-id -i {SSH_KEY} {target}")


def _claim_box_via_dhcp() -> None:
    logger.info("claiming_box_via_dhcp")
    # NM's dnsmasq re-reads the lease file on startup, so a prior bootstrap's
    # entry survives a manual-shared-manual cycle and gets re-served, pointing
    # at an IP the box no longer holds. Delete the file so dnsmasq starts
    # empty.
    bash_check("sudo find /var/lib/NetworkManager -maxdepth 1 -name 'dnsmasq-*.leases' -delete")
    set_host_link_method("shared")

    logger.info("waiting_for_box_dhcp_lease", extra={"timeout_seconds": DHCP_LEASE_WAIT_SECONDS})
    deadline = time.monotonic() + DHCP_LEASE_WAIT_SECONDS
    leased_ip = ""
    while not leased_ip:
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
                leased_ip = parts[2]
                break
        if not leased_ip:
            if time.monotonic() >= deadline:
                bail(NO_DHCP_LEASE_RECEIVED, timeout_seconds=DHCP_LEASE_WAIT_SECONDS, box_ip=BOX_IP)
            time.sleep(1)

    logger.info("box_dhcp_lease_acquired", extra={"leased_ip": leased_ip})
    bootstrap_target = f"user@{leased_ip}"

    _ensure_key_access(bootstrap_target)

    # Find the wired ethernet device on the box, then ask which NM connection
    # currently holds it. `-g <single-field>` returns the value alone (no
    # field-separator escaping to undo) and field values queried this way
    # ride through verbatim regardless of what colons or backslashes the
    # name contains.
    devices_raw = bash_output(f'ssh {bootstrap_target} "nmcli -t -e no -f DEVICE,TYPE,STATE device"').strip()
    wired_devices = [
        line.split(":", 2)[0]
        for line in devices_raw.splitlines()
        if line.split(":", 2)[1:3] == ["ethernet", "connected"]
    ]
    if not wired_devices:
        bail(NO_BOX_WIRED_CONNECTION, raw=repr(devices_raw))
    bootstrap_connection = bash_output(
        f'ssh {bootstrap_target} "nmcli -g GENERAL.CONNECTION device show {wired_devices[0]}"'
    ).strip()

    logger.info(
        "renumbering_box_to_static",
        extra={"connection": bootstrap_connection, "from": leased_ip, "to": BOX_IP},
    )
    # Schedule the IP change as a systemd transient unit firing a few seconds
    # after our SSH disconnects. The box's TCP socket gets silently torn down
    # the instant nmcli activates the new address; running the renumber off
    # any live SSH session means the local client returns cleanly instead of
    # hanging on a half-dead connection. The renumber script is written via
    # a quoted heredoc so the connection name carries through verbatim, which
    # collapses both layers of the previous ssh-shell-escape gymnastics.
    remote_conn = shlex.quote(bootstrap_connection)
    bash(
        f"ssh {bootstrap_target} bash",
        stdin_text=(
            "cat > /tmp/zedbox-renumber.sh <<'SHELL_EOF'\n"
            f"nmcli con mod {remote_conn} ipv4.method manual "
            f"ipv4.addresses {BOX_IP}/24 ipv4.gateway '' ipv4.dns ''\n"
            f"nmcli con up {remote_conn}\n"
            "SHELL_EOF\n"
            "sudo systemd-run --on-active=3 /bin/sh /tmp/zedbox-renumber.sh\n"
        ),
    )

    set_host_link_method("manual")


def _ensure_arm64_emulation() -> None:
    if platform.machine() in ("aarch64", "arm64"):
        return

    handler = Path("/proc/sys/fs/binfmt_misc/qemu-aarch64")
    if handler.exists() and handler.read_text().startswith("enabled"):
        return

    bail(ARM64_EMULATION_MISSING)


def _acquire_images(host_ip: str, build: bool, service_shas: dict[str, str]) -> dict[str, str]:
    if not build:
        images = {
            service.image_env: f"{GHCR_BASE}/{service.name}:{service_shas[service.sha_key]}" for service in ZED_SERVICES
        }
        for image in images.values():
            _pull_image_on_box(image)
        return images

    # Local registry instead of `docker save | ssh docker load`: pulls are
    # layer-aware, so iterative dev only ships changed layers across the
    # cable.
    if not bash_check("docker container inspect registry"):
        logger.info("starting_local_registry", extra={"port": REGISTRY_PORT})
        bash(
            f"docker run -d -p {REGISTRY_PORT}:{REGISTRY_PORT} --name registry --restart unless-stopped"
            f" {REGISTRY_IMAGE}"
        )
    elif bash_output('docker inspect -f "{{.State.Running}}" registry').strip() == "true":
        logger.info("local_registry_already_running")
    else:
        logger.info("restarting_local_registry")
        bash("docker start registry")

    local_images = {
        service.name: f"localhost:{REGISTRY_PORT}/{service.name}:{service_shas[service.sha_key]}"
        for service in ZED_SERVICES
    }
    remote_images = {
        service.image_env: f"{host_ip}:{REGISTRY_PORT}/{service.name}:{service_shas[service.sha_key]}"
        for service in ZED_SERVICES
    }

    logger.info("cross_compiling_images", extra={"bake_file": str(BAKE_FILE)})
    env_prefix = " ".join(f"{k}={v}" for k, v in service_shas.items())
    set_flags = " ".join(f"--set {service.name}.tags={local_images[service.name]}" for service in ZED_SERVICES)
    bake_targets = " ".join(service.name for service in ZED_SERVICES)
    bash(
        f"env {env_prefix} docker buildx bake -f {BAKE_FILE} {set_flags}"
        f" --push --provenance=false --sbom=false {bake_targets}",
    )

    # Docker treats `localhost` as insecure-by-default for push; the box's
    # daemon needs the box-facing host IP in its insecure-registries.
    if ssh_check(f"grep -q {host_ip}:{REGISTRY_PORT} /etc/docker/daemon.json"):
        logger.info("box_insecure_registry_present", extra={"registry": f"{host_ip}:{REGISTRY_PORT}"})
    else:
        logger.info("configuring_box_insecure_registry", extra={"registry": f"{host_ip}:{REGISTRY_PORT}"})
        daemon_config = json.loads(ssh_output("cat /etc/docker/daemon.json").strip())
        registries: list[str] = daemon_config.get("insecure-registries", [])
        registries.append(f"{host_ip}:{REGISTRY_PORT}")
        daemon_config["insecure-registries"] = registries
        ssh_run("sudo tee /etc/docker/daemon.json", stdin_text=json.dumps(daemon_config, indent=2))
        ssh_run("sudo systemctl restart docker")

    for image in remote_images.values():
        _pull_image_on_box(image)
    return remote_images


def _pull_image_on_box(image: str) -> None:
    logger.info("pulling_image_on_box", extra={"image": image})
    try:
        ssh_run(f"sudo docker pull {image}")
    except CalledProcessError:
        bail(IMAGE_PULL_FAILED, image=image)
