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
def down(
    volumes: bool = typer.Option(False, "--volumes", "-v", help="Remove named volumes."),
    gpu: Gpu = typer.Option("auto", "--gpu", help="auto|cuda|rocm|none"),
) -> None:
    if not ENV_FILE.exists():
        raise RuntimeError("No .env file found")

    if not LOCK_FILE.exists():
        raise RuntimeError("No lock file found; run 'uv run build --lock-only' first")

    if gpu == "auto":
        gpu = detect_gpu()

    _resolve_service_shas()

    command = (
        "docker compose "
        "-f compose.yml "
        f"{f'-f compose.{gpu}.yml ' if gpu != 'none' else ''}"
        "--env-file .env "
        f"--env-file {LOCK_FILE} "  # Needed so compose won't error on missing variables, even though they are irrelevant for 'down'
        "down --remove-orphans"
    )

    if volumes:
        command += " -v"

    bash_handoff(command)


def main():
    app()


if __name__ == "__main__":
    main()
