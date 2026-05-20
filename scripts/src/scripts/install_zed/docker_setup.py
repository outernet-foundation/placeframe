import json
import tempfile
from logging import getLogger

from common.bash import bash

from .constants import (
    BOX_SSH_TARGET,
    DOCKER_DEB_BASE,
    DOCKER_DEBS,
    L4T_USB_DEVICE_MODE_UNIT,
    REGISTRY_PORT,
    SSH_MUX,
)
from .ssh import ssh_check, ssh_output, ssh_run

logger = getLogger(__name__)


def ensure_docker_on_box() -> bool:
    if ssh_check("which docker"):
        logger.info("docker_already_installed")
        return False
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
    ssh_run(f'"sudo dpkg -i {deb_paths}"')
    ssh_run(f'"sudo usermod -aG docker {box_user}"')
    ssh_run(f'"rm {deb_paths}"')
    logger.info("docker_installed", extra={"user": box_user})
    return True


def ensure_nvidia_runtime_on_box() -> None:
    if ssh_check('"test -f /etc/docker/daemon.json"') and ssh_check('"grep -q nvidia /etc/docker/daemon.json"'):
        logger.info("nvidia_runtime_already_configured")
        return
    logger.info("configuring_nvidia_runtime")
    ssh_run('"sudo nvidia-ctk runtime configure --runtime=docker"')
    ssh_run('"sudo systemctl restart docker"')


def ensure_usb_device_mode_disabled() -> None:
    logger.info("disabling_usb_device_mode_service", extra={"unit": L4T_USB_DEVICE_MODE_UNIT})
    ssh_check(f'"sudo systemctl disable --now {L4T_USB_DEVICE_MODE_UNIT}"')


def ensure_box_insecure_registry(host_ip: str) -> None:
    if ssh_check(f'"grep -q {host_ip}:{REGISTRY_PORT} /etc/docker/daemon.json"'):
        logger.info("box_insecure_registry_present", extra={"registry": f"{host_ip}:{REGISTRY_PORT}"})
        return
    logger.info("configuring_box_insecure_registry", extra={"registry": f"{host_ip}:{REGISTRY_PORT}"})
    config = json.loads(ssh_output('"cat /etc/docker/daemon.json"').strip())
    registries: list[str] = config.get("insecure-registries", [])
    registries.append(f"{host_ip}:{REGISTRY_PORT}")
    config["insecure-registries"] = registries
    ssh_run("sudo tee /etc/docker/daemon.json", stdin_text=json.dumps(config, indent=2))
    ssh_run('"sudo systemctl restart docker"')
