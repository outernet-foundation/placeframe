from pathlib import Path

import typer
from common.detect_gpu import Gpu, detect_gpu
from common.run_command import exec_command

ENV_FILE = Path(".env")
LOCK_FILE = Path(".env.lock")
LOCAL_LOCK_FILE = Path(".env.local.lock")

app = typer.Typer(add_completion=False)


@app.command()
def down(
    volumes: bool = typer.Option(False, "--volumes", "-v", help="Remove named volumes."),
    gpu: Gpu = typer.Option("auto", "--gpu", help="auto|cuda|rocm"),
) -> None:
    """Wrapper for docker compose down."""
    if not ENV_FILE.exists():
        raise RuntimeError("No .env file found")

    if not LOCK_FILE.exists() and not LOCAL_LOCK_FILE.exists():
        raise RuntimeError("No lock file found; run 'lock.py' first")

    if gpu == "auto":
        gpu = detect_gpu()

    lock_file = LOCAL_LOCK_FILE if LOCAL_LOCK_FILE.exists() else LOCK_FILE

    command = (
        "docker compose "
        "-f compose.yml "
        f"-f compose.{gpu}.yml "
        "--env-file .env "
        f"--env-file {lock_file} "  # Needed so compose won't error on missing variables, even though they are irrelevant for 'down'
        "down --remove-orphans"
    )

    if volumes:
        command += " -v"

    exec_command(command)


def main():
    app()


if __name__ == "__main__":
    main()
