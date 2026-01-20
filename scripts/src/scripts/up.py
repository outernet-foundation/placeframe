import subprocess
import sys
from pathlib import Path

import typer

# The "Contract" (Duplicated from lock.py is fine here)
SHARED_LOCK = Path(".env.lock")
LOCAL_LOCK = Path(".env.local.lock")

app = typer.Typer(add_completion=False)


@app.command()
def up(
    official: bool = typer.Option(
        False, "--official", help="Force use of official .env.lock even if local build exists."
    ),
    detach: bool = typer.Option(False, "--detach", "-d", help="Run containers in background."),
    profile: str = typer.Option(None, "--profile", help="Docker compose profile (e.g. cuda, rocm)."),
) -> None:
    """Wrapper for docker compose up that selects the correct lock file."""
    lock_to_use = SHARED_LOCK

    # Logic: Prefer local lock if it exists, unless --official is passed
    if not official and LOCAL_LOCK.exists():
        lock_to_use = LOCAL_LOCK
        print(f"    [INFO] Using LOCAL lock file: {LOCAL_LOCK}")
    else:
        print(f"    [INFO] Using SHARED lock file: {SHARED_LOCK}")

    cmd = ["docker", "compose"]

    # 1. Load the standard configuration variables (if .env exists)
    # We load this FIRST so that the lock file (loaded second) can override image tags
    if Path(".env").exists():
        cmd.extend(["--env-file", ".env"])

    # 2. Load the locked image digests
    cmd.extend(["--env-file", str(lock_to_use)])

    if profile:
        cmd.extend(["--profile", profile])

    cmd.extend(["up"])
    if detach:
        cmd.append("-d")

    # Pass control to docker compose
    try:
        if sys.platform != "win32":
            import os

            # Use execvp to replace the process (cleaner signal handling)
            os.execvp("docker", cmd)
        else:
            subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        raise typer.Exit(code=e.returncode)


def main():
    app()


if __name__ == "__main__":
    main()
