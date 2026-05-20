from logging import getLogger

from common.bash import bash
from common.ui import bail

from .constants import (
    BOX_SSH_TARGET,
    COMPOSE_SOURCE,
    REMOTE_COMPOSE,
    REMOTE_DIR,
    SSH_MUX,
    SYSTEMD_UNIT_SOURCE,
)
from .messages import BOX_ID_UNRESOLVABLE
from .ssh import ssh_check, ssh_output, ssh_run

logger = getLogger(__name__)


def ensure_compose_on_box() -> None:
    logger.info("transferring_compose_file", extra={"source": str(COMPOSE_SOURCE)})
    ssh_run(f'"mkdir -p {REMOTE_DIR}"')
    bash(f"scp {SSH_MUX} {COMPOSE_SOURCE!s} {BOX_SSH_TARGET}:{REMOTE_COMPOSE}")


def detect_box_id() -> str:
    # Jetson hardware-burned serial survives OS reflashes; /etc/machine-id is
    # the non-Jetson fallback.
    if ssh_check('"test -e /proc/device-tree/serial-number"'):
        box_id = ssh_output("\"tr -d '\\0\\n' < /proc/device-tree/serial-number\"").strip()
    else:
        box_id = ""
    if not box_id:
        box_id = ssh_output('"cat /etc/machine-id"').strip()
    if not box_id:
        bail(BOX_ID_UNRESOLVABLE)
    return box_id


def ensure_box_env_file(images: dict[str, str], box_id: str) -> None:
    ssh_run(
        f"tee {REMOTE_DIR}/.env",
        stdin_text=(
            f"ZED_IMAGE={images['zed_capture']}\n"
            f"AOA_BRIDGE_IMAGE={images['aoa_bridge']}\n"
            f"AOA_GATEWAY_IMAGE={images['aoa_gateway']}\n"
            f"ZED_BOX_ID={box_id}\n"
        ),
    )


def ensure_systemd_unit_on_box() -> None:
    logger.info("installing_systemd_unit", extra={"unit": "placeframe-zed.service"})
    remote_home = ssh_output('"echo $HOME"').strip()
    remote_compose_abs = f"{remote_home}/.placeframe/compose.rig.yml"
    unit_content = SYSTEMD_UNIT_SOURCE.read_text().replace("COMPOSE_PATH", remote_compose_abs)
    ssh_run('"sudo tee /etc/systemd/system/placeframe-zed.service > /dev/null"', stdin_text=unit_content)
    ssh_run('"sudo systemctl daemon-reload"')
    ssh_run('"sudo systemctl enable placeframe-zed.service"')


def ensure_camera_daemons_enabled() -> None:
    logger.info("enabling_camera_daemons")
    ssh_run('"sudo systemctl enable --now nvargus-daemon zed_x_daemon"')


def redeploy_compose_stack(docker: str) -> None:
    # `down` first so deploys are idempotent against any prior partially-failed
    # `up --force-recreate` (which can leave containers stuck under their
    # ID-prefixed rename, blocking the next recreate with a name conflict).
    logger.info("redeploying_compose_stack", extra={"compose": REMOTE_COMPOSE})
    ssh_run(f'"{docker} compose -f {REMOTE_COMPOSE} down --remove-orphans"')
    ssh_run(f'"{docker} compose -f {REMOTE_COMPOSE} up -d"')


def warm_zed_sdk(docker: str) -> None:
    logger.info("warming_zed_sdk")
    bash(
        f'ssh {SSH_MUX} {BOX_SSH_TARGET} "{docker} compose -f {REMOTE_COMPOSE} exec zed-capture python -c \\"'
        f"import pyzed.sl as sl; c = sl.Camera(); p = sl.InitParameters(); c.open(p); c.close()"
        f'\\""'
    )
