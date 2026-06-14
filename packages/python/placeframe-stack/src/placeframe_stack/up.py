import os
from pathlib import Path

import typer
from placeframe_bash import bash_handoff
from .detect_gpu import Gpu, detect_gpu

from .build_docker import run_build
from .context_sha import compute_service_shas
from .modes import resolve_auth_mode

ENV_FILE = Path(".env")
LOCK_FILE = Path(".env.lock")
BAKE_FILE = Path("compose.bake.yml")


def _resolve_service_shas() -> None:
    os.environ.update(compute_service_shas(Path.cwd(), BAKE_FILE))


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
    no_dev: bool = typer.Option(False, "--no-dev", help="Skip layering compose.dev.yml (production-shape bring-up)"),
    compose_file: Path = typer.Option(
        Path("compose.yml"),
        "--compose-file",
        help=(
            "Base compose file. In the placeframe repo (where compose.bake.yml lives) the default compose.yml "
            "triggers the native multi-file assembly. A consumer stack — e.g. make-it-sing's compose.yml, which "
            "OCI-pulls the published placeframe artifact and adds LiveKit on top — is run as the complete graph "
            "with only --env-file .env."
        ),
    ),
) -> None:
    # The placeframe repo carries compose.bake.yml and builds its own images, so the
    # default compose.yml means the native multi-file stack (postgres + gpu + dev layers,
    # per-service SHA injection, .env.lock). A consumer repo has no bake file: its
    # --compose-file is the whole graph (placeframe arrives baked via OCI include or a
    # sibling-checkout include), so SHA resolution and .env.lock don't apply.
    native = compose_file == Path("compose.yml") and BAKE_FILE.exists()

    if not ENV_FILE.exists():
        raise RuntimeError("No .env file found; create one first (e.g., copy .env.example)")

    if native and not LOCK_FILE.exists():
        raise RuntimeError("No lock file found; run 'uv run build --lock-only' first")

    if build and not native:
        raise typer.BadParameter(
            "--build is only supported for the native placeframe stack; a consumer stack consumes images "
            "from the OCI-included placeframe artifact and has no local build graph."
        )

    if gpu == "auto":
        gpu = detect_gpu()

    auth_mode = resolve_auth_mode(ENV_FILE)

    if build:
        run_build(gpu=gpu)

    if BAKE_FILE.exists():
        _resolve_service_shas()

    profile_flag = "--profile keycloak " if auth_mode == "keycloak" else ""
    if native:
        gpu_file = f"-f compose.{gpu}.yml " if gpu != "none" else ""
        dev_file = "" if no_dev else "-f compose.dev.yml "
        compose_args = (
            f"-f compose.yml -f compose.postgres.yml {gpu_file}{dev_file}{profile_flag}"
            f"--env-file .env --env-file {LOCK_FILE}"
        )
    else:
        lock_flag = f"--env-file {LOCK_FILE} " if LOCK_FILE.exists() else ""
        compose_args = f"-f {compose_file} {profile_flag}--env-file .env {lock_flag}".rstrip()

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
