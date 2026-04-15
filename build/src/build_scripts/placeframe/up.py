import os
from pathlib import Path

import typer
from common.bash import bash_handoff
from common.detect_gpu import Gpu, detect_gpu

from .context_sha import compute_service_shas

ENV_FILE = Path(".env")
LOCK_FILE = Path(".env.lock")


def _resolve_service_shas() -> None:
    os.environ.update(compute_service_shas(Path.cwd(), Path("compose.bake.yml")))


app = typer.Typer(add_completion=False)


@app.command()
def up(
    attached: bool = typer.Option(False, "--attached", "-a", help="Run in foreground (not detached)"),
    quiet_pull: bool = typer.Option(False, "--quiet-pull", "-q", help="Suppress docker compose pull progress output"),
    gpu: Gpu = typer.Option("auto", "--gpu", help="auto|cuda|rocm|none"),
) -> None:
    if not LOCK_FILE.exists():
        raise RuntimeError("No lock file found; run 'uv run build --lock-only' first")

    if not ENV_FILE.exists():
        raise RuntimeError("No .env file found; create one first (e.g., copy .env.example)")

    if gpu == "auto":
        gpu = detect_gpu()

    _resolve_service_shas()

    command = (
        "docker compose "
        "-f compose.yml "
        f"{f'-f compose.{gpu}.yml ' if gpu != 'none' else ''}"
        "--env-file .env "
        f"--env-file {LOCK_FILE} "
        "up"
    )

    if quiet_pull:
        command += " --quiet-pull"
    if not attached:
        command += " -d"

    bash_handoff(command)


def main():
    app()


if __name__ == "__main__":
    main()
