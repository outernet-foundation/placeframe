import os
from pathlib import Path

import typer
from common.bash import bash_handoff
from common.detect_gpu import Gpu, detect_gpu

from .build_docker import run_build
from .context_sha import compute_service_shas

ENV_FILE = Path(".env")
LOCK_FILE = Path(".env.lock")


def _resolve_service_shas() -> None:
    os.environ.update(compute_service_shas(Path.cwd(), Path("compose.bake.yml")))


app = typer.Typer(add_completion=False)


@app.command()
def up(
    attached: bool = typer.Option(False, "--attached", "-a", help="Run in foreground (not detached)"),
    quiet_pull: bool = typer.Option(
        False,
        "--quiet-pull",
        "-q",
        help="Suppress per-layer pull progress (still shows pull/push totals).",
    ),
    build: bool = typer.Option(
        False, "--build", help="Build all images locally before bringing the stack up; skips pulling"
    ),
    gpu: Gpu = typer.Option("auto", "--gpu", help="auto|cuda|rocm|none"),
) -> None:
    if not LOCK_FILE.exists():
        raise RuntimeError("No lock file found; run 'uv run build --lock-only' first")

    if not ENV_FILE.exists():
        raise RuntimeError("No .env file found; create one first (e.g., copy .env.example)")

    if gpu == "auto":
        gpu = detect_gpu()

    if build:
        run_build(gpu=gpu)

    _resolve_service_shas()

    gpu_file = f"-f compose.{gpu}.yml " if gpu != "none" else ""
    compose_args = f"-f compose.yml {gpu_file}--env-file .env --env-file {LOCK_FILE}"

    up_command = f"docker compose {compose_args} up"
    if not build:
        # tree-<sha> tags are immutable (derived from dockerignore-allowlisted
        # context), so a local hit is byte-identical to what the registry would
        # serve. --pull missing skips locally-present tags, avoiding hard errors
        # on images built locally but not yet pushed.
        up_command += " --pull missing"
        if quiet_pull:
            up_command += " --quiet-pull"
    if not attached:
        up_command += " -d"

    bash_handoff(up_command)


def main():
    app()


if __name__ == "__main__":
    main()
