import os
from pathlib import Path

import typer
from placeframe_bash import bash_handoff
from .detect_gpu import Gpu, detect_gpu

from .context_sha import compute_service_shas
from .modes import resolve_auth_mode

ENV_FILE = Path(".env")
LOCK_FILE = Path(".env.lock")


def _resolve_service_shas() -> None:
    os.environ.update(compute_service_shas(Path.cwd(), Path("compose.bake.yml")))


app = typer.Typer(add_completion=False)


@app.command()
def down(
    volumes: bool = typer.Option(False, "--volumes", "-v", help="Remove named volumes."),
    gpu: Gpu = typer.Option("auto", "--gpu", help="auto|cuda|rocm|none"),
    compose_file: Path = typer.Option(
        Path("compose.yml"),
        "--compose-file",
        help=("Base compose file. Default compose.yml. Use compose.makeitsing.yml to tear down the makeitsing stack."),
    ),
) -> None:
    if not ENV_FILE.exists():
        raise RuntimeError("No .env file found")

    if not LOCK_FILE.exists():
        raise RuntimeError("No lock file found; run 'uv run build --lock-only' first")

    if gpu == "auto":
        gpu = detect_gpu()

    resolve_auth_mode(ENV_FILE)

    _resolve_service_shas()

    if compose_file == Path("compose.yml"):
        compose_files = (
            "-f compose.yml "
            "-f compose.postgres.yml "
            f"{f'-f compose.{gpu}.yml ' if gpu != 'none' else ''}"
            "-f compose.dev.yml "  # Include so containers from a prior dev bring-up get torn down even with --no-dev later
        )
    else:
        compose_files = f"-f {compose_file} "

    command = (
        "docker compose "
        f"{compose_files}"
        "--profile keycloak "  # Always include so any keycloak containers from a previous AUTH_MODE=keycloak run get torn down
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
