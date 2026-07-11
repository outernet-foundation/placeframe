from logging import getLogger
from typing import Annotated

import typer
from placeframe_stack.context_sha import compute_service_shas
from bashrun import bash
from common.logging_config import configure_logging

from .box_install import install_box
from .constants import BAKE_FILE, BOX_SSH_TARGET, REPO_ROOT, SSH_KEY
from .host_setup import share_host_internet

logger = getLogger(__name__)
app = typer.Typer()


@app.command()
def main(
    build: Annotated[
        bool,
        typer.Option("--build", help="Cross-compile box images locally instead of pulling from ghcr"),
    ] = False,
) -> None:
    configure_logging("install-zed", log_file_path=REPO_ROOT / ".placeframe" / "logs" / "install-zed.jsonl")
    logger.info("starting_install", extra={"target": BOX_SSH_TARGET, "build": build})
    service_shas = compute_service_shas(REPO_ROOT, BAKE_FILE)

    if SSH_KEY.exists():
        logger.info("ssh_key_exists", extra={"path": str(SSH_KEY)})
    else:
        logger.info("generating_ssh_key", extra={"path": str(SSH_KEY)})
        SSH_KEY.parent.mkdir(parents=True, exist_ok=True)
        bash(f'ssh-keygen -t ed25519 -N "" -f {SSH_KEY}')

    share_host_internet()
    install_box(build, service_shas)
