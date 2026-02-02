from pathlib import Path

import typer
from common.detect_gpu import Gpu, detect_gpu
from common.run_command import exec_command

ENV_FILE = Path(".env")
LOCK_FILE = Path(".env.lock")
LOCAL_LOCK_FILE = Path(".env.local.lock")

app = typer.Typer(add_completion=False)


@app.command()
def up(
    use_lock: bool = typer.Option(False, "--locked", "-l", help="Use .env.lock even if .env.local.lock exists."),
    attached: bool = typer.Option(False, "--attached", "-a", help="Run in foreground (not detached)"),
    gpu: Gpu = typer.Option("auto", "--gpu", help="auto|cuda|rocm"),
) -> None:
    if not LOCK_FILE.exists() and not LOCAL_LOCK_FILE.exists():
        raise RuntimeError("No lock file found; run 'lock.py' first")

    if not ENV_FILE.exists():
        raise RuntimeError("No .env file found; create one first (e.g., copy .env.example)")

    if gpu == "auto":
        gpu = detect_gpu()

    command = (
        "docker compose "
        "-f compose.yml "
        f"-f compose.{gpu}.yml "
        "--env-file .env "
        f"--env-file {LOCAL_LOCK_FILE if not use_lock and LOCAL_LOCK_FILE.exists() else LOCK_FILE} "
        "up"
    )

    if not attached:
        command += " -d"

    exec_command(command)


def main():
    app()


if __name__ == "__main__":
    main()
