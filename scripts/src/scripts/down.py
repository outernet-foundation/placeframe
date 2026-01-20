import subprocess
import sys
from pathlib import Path

import typer

# The "Contract"
SHARED_LOCK = Path(".env.lock")
LOCAL_LOCK = Path(".env.local.lock")


def main(volumes: bool = typer.Option(False, "--volumes", "-v", help="Remove named volumes.")) -> None:
    """Wrapper for docker compose down."""

    # We need to provide the env files so Compose can resolve variables in compose.yml
    # Otherwise it crashes with "required variable ... is missing"
    cmd = ["docker", "compose"]

    # 1. Load standard config .env
    if Path(".env").exists():
        cmd.extend(["--env-file", ".env"])

    # 2. Load a lockfile (Local takes precedence if exists)
    # It doesn't strictly matter WHICH lockfile we use for 'down',
    # as long as the variables are defined so parsing succeeds.
    if LOCAL_LOCK.exists():
        cmd.extend(["--env-file", str(LOCAL_LOCK)])
    else:
        cmd.extend(["--env-file", str(SHARED_LOCK)])

    cmd.extend(["down", "--remove-orphans"])

    if volumes:
        cmd.append("-v")

    try:
        if sys.platform != "win32":
            import os

            os.execvp("docker", cmd)
        else:
            subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        raise typer.Exit(code=e.returncode)


if __name__ == "__main__":
    typer.run(main)
