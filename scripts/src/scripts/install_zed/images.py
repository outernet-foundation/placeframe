from logging import getLogger
from subprocess import CalledProcessError

from common.bash import bash, bash_check, bash_output
from common.ui import bail

from .constants import BAKE_FILE, GHCR_BASE, REGISTRY_IMAGE, REGISTRY_PORT
from .docker_setup import ensure_box_insecure_registry
from .messages import IMAGE_PULL_FAILED
from .ssh import ssh_run

logger = getLogger(__name__)


def acquire_images(host_ip: str, build: bool, docker: str, service_shas: dict[str, str]) -> dict[str, str]:
    if not build:
        zed_image = f"{GHCR_BASE}/zed-capture:{service_shas['ZED_CAPTURE_SHA']}"
        bridge_image = f"{GHCR_BASE}/aoa-bridge:{service_shas['AOA_BRIDGE_SHA']}"
        gateway_image = f"{GHCR_BASE}/aoa-gateway:{service_shas['AOA_GATEWAY_SHA']}"
        pull_image_on_box(docker, zed_image)
        pull_image_on_box(docker, bridge_image)
        pull_image_on_box(docker, gateway_image)
        return {"zed_capture": zed_image, "aoa_bridge": bridge_image, "aoa_gateway": gateway_image}

    # Local registry instead of `docker save | ssh docker load`: pulls are
    # layer-aware, so iterative dev only ships changed layers across the
    # cable.

    # Docker treats `localhost` as insecure-by-default for push; the box's
    # daemon needs the box-facing host IP in its insecure-registries.
    ensure_local_registry_running()

    local_zed = f"localhost:{REGISTRY_PORT}/zed-capture:{service_shas['ZED_CAPTURE_SHA']}"
    local_bridge = f"localhost:{REGISTRY_PORT}/aoa-bridge:{service_shas['AOA_BRIDGE_SHA']}"
    local_gateway = f"localhost:{REGISTRY_PORT}/aoa-gateway:{service_shas['AOA_GATEWAY_SHA']}"
    remote_zed = f"{host_ip}:{REGISTRY_PORT}/zed-capture:{service_shas['ZED_CAPTURE_SHA']}"
    remote_bridge = f"{host_ip}:{REGISTRY_PORT}/aoa-bridge:{service_shas['AOA_BRIDGE_SHA']}"
    remote_gateway = f"{host_ip}:{REGISTRY_PORT}/aoa-gateway:{service_shas['AOA_GATEWAY_SHA']}"

    logger.info("cross_compiling_images", extra={"bake_file": str(BAKE_FILE)})
    env_prefix = " ".join(f"{k}={v}" for k, v in service_shas.items())
    bash(
        f"env {env_prefix} docker buildx bake -f {BAKE_FILE}"
        f" --set zed-capture.tags={local_zed}"
        f" --set aoa-bridge.tags={local_bridge}"
        f" --set aoa-gateway.tags={local_gateway}"
        " --push --provenance=false --sbom=false zed-capture aoa-bridge aoa-gateway",
    )

    ensure_box_insecure_registry(host_ip)

    pull_image_on_box(docker, remote_zed)
    pull_image_on_box(docker, remote_bridge)
    pull_image_on_box(docker, remote_gateway)
    return {"zed_capture": remote_zed, "aoa_bridge": remote_bridge, "aoa_gateway": remote_gateway}


def ensure_local_registry_running() -> None:
    if not bash_check("docker container inspect registry"):
        logger.info("starting_local_registry", extra={"port": REGISTRY_PORT})
        bash(
            f"docker run -d -p {REGISTRY_PORT}:{REGISTRY_PORT} --name registry --restart unless-stopped"
            f" {REGISTRY_IMAGE}"
        )
        return
    if bash_output('docker inspect -f "{{.State.Running}}" registry').strip() == "true":
        logger.info("local_registry_already_running")
        return
    logger.info("restarting_local_registry")
    bash("docker start registry")


def pull_image_on_box(docker: str, image: str) -> None:
    logger.info("pulling_image_on_box", extra={"image": image})
    try:
        ssh_run(f'"{docker} pull {image}"')
    except CalledProcessError:
        bail(IMAGE_PULL_FAILED, image=image)
