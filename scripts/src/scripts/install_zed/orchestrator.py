from contextlib import ExitStack
from logging import getLogger
from typing import Annotated

import typer
from build_scripts.placeframe.context_sha import compute_service_shas
from common.bash import bash, bash_check
from common.logging_config import configure_logging

from .box_network import (
    ensure_box_default_route_via,
    ensure_box_reachable_via_ssh,
    ensure_box_ssh_key_authorized,
    ensure_etc_hosts_entry,
    lookup_host_ip_from_box,
)
from .constants import BAKE_FILE, BOX_SSH_TARGET, REPO_ROOT, SSH_MUX, SSH_SOCKET
from .deploy import (
    detect_box_id,
    ensure_box_env_file,
    ensure_camera_daemons_enabled,
    ensure_compose_on_box,
    ensure_systemd_unit_on_box,
    redeploy_compose_stack,
    warm_zed_sdk,
)
from .docker_setup import (
    ensure_docker_on_box,
    ensure_nvidia_runtime_on_box,
    ensure_usb_device_mode_disabled,
)
from .host_network import (
    ensure_firewalld_configured,
    ensure_host_cable_set_to,
    ensure_ip_forward_on_host,
)
from .images import acquire_images
from .ssh import ensure_ssh_key, ensure_sudoers_on_box

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
        install(stack, build)


# Separate helper so ExitStack callbacks fire when this returns, not at the
# typer command-function boundary.
def install(stack: ExitStack, build: bool) -> None:
    service_shas = compute_service_shas(REPO_ROOT, BAKE_FILE)

    ensure_ssh_key()
    ensure_host_cable_set_to("manual")
    ensure_box_reachable_via_ssh()
    ensure_box_ssh_key_authorized()

    logger.info("connecting_to_box", extra={"target": BOX_SSH_TARGET})
    bash(f"ssh {SSH_MUX} -fN {BOX_SSH_TARGET}")
    stack.callback(lambda: bash_check(f"ssh -o ControlPath={SSH_SOCKET} -O exit {BOX_SSH_TARGET}"))

    ensure_sudoers_on_box()
    fresh_install = ensure_docker_on_box()
    # The just-added docker group membership isn't picked up on this SSH
    # session, so the fresh-install path needs sudo.
    docker = "sudo docker" if fresh_install else "docker"
    ensure_nvidia_runtime_on_box()
    ensure_usb_device_mode_disabled()
    ensure_etc_hosts_entry()

    host_ip = lookup_host_ip_from_box()
    ensure_box_default_route_via(host_ip)

    ensure_ip_forward_on_host()
    ensure_firewalld_configured()

    images = acquire_images(host_ip, build, docker, service_shas)

    ensure_compose_on_box()
    box_id = detect_box_id()
    ensure_box_env_file(images, box_id)
    ensure_systemd_unit_on_box()
    ensure_camera_daemons_enabled()
    redeploy_compose_stack(docker)

    if not build:
        warm_zed_sdk(docker)

    logger.info("install_done")
