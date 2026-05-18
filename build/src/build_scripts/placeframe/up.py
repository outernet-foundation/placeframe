import os
from datetime import UTC, datetime
from pathlib import Path

import typer
from common.bash import bash, bash_handoff
from common.detect_gpu import Gpu, detect_gpu

from .context_sha import compute_service_shas

ENV_FILE = Path(".env")
LOCK_FILE = Path(".env.lock")
LOG_DIRECTORY = Path(".placeframe") / "logs"


def _resolve_service_shas() -> None:
    os.environ.update(compute_service_shas(Path.cwd(), Path("compose.bake.yml")))


app = typer.Typer(add_completion=False)


@app.command()
def up(
    attached: bool = typer.Option(False, "--attached", "-a", help="Run in foreground (not detached)"),
    quiet_pull: bool = typer.Option(
        False, "--quiet-pull", "-q", help="Pull verbosely to a log file under .placeframe/logs/ instead of the console"
    ),
    gpu: Gpu = typer.Option("auto", "--gpu", help="auto|cuda|rocm|none"),
) -> None:
    if not LOCK_FILE.exists():
        raise RuntimeError("No lock file found; run 'uv run build --lock-only' first")

    if not ENV_FILE.exists():
        raise RuntimeError("No .env file found; create one first (e.g., copy .env.example)")

    if gpu == "auto":
        gpu = detect_gpu()

    _resolve_service_shas()

    gpu_file = f"-f compose.{gpu}.yml " if gpu != "none" else ""
    compose_args = f"-f compose.yml {gpu_file}--env-file .env --env-file {LOCK_FILE}"

    if quiet_pull:
        timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
        log_path = LOG_DIRECTORY / f"up-pull-{timestamp}.log"
        print(f"Pulling images → {log_path}")
        bash(f"docker compose --progress plain {compose_args} pull", log_path=log_path)

    up_command = f"docker compose {compose_args} up"
    if not attached:
        up_command += " -d"

    bash_handoff(up_command)


def main():
    app()


if __name__ == "__main__":
    main()
