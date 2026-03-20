import os
from pathlib import Path
from subprocess import CalledProcessError

import typer
from common.bash import bash_handoff, bash_output
from common.detect_gpu import Gpu, detect_gpu

ENV_FILE = Path(".env")
LOCK_FILE = Path(".env.lock")
LOCAL_LOCK_FILE = Path(".env.local.lock")


def _load_lock_value(path: Path, key: str) -> str | None:
    if not path.exists():
        return None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith(f"{key}="):
            return line.split("=", 1)[1].strip()
    return None


def _resolve_git_sha(local_lock: Path, *, use_local: bool = True) -> str:
    if use_local:
        local_sha = _load_lock_value(local_lock, "GIT_SHA")
        if local_sha:
            return local_sha
    try:
        tag = bash_output("git describe --tags --match built-* --abbrev=0 HEAD").strip()
        return tag.removeprefix("built-")
    except CalledProcessError:
        return bash_output("git rev-parse HEAD").strip()


app = typer.Typer(add_completion=False)


@app.command()
def up(
    use_lock: bool = typer.Option(False, "--locked", "-l", help="Use .env.lock even if .env.local.lock exists."),
    attached: bool = typer.Option(False, "--attached", "-a", help="Run in foreground (not detached)"),
    gpu: Gpu = typer.Option("auto", "--gpu", help="auto|cuda|rocm|none"),
) -> None:
    if not LOCK_FILE.exists() and not LOCAL_LOCK_FILE.exists():
        raise RuntimeError("No lock file found; run 'lock.py' first")

    if not ENV_FILE.exists():
        raise RuntimeError("No .env file found; create one first (e.g., copy .env.example)")

    if gpu == "auto":
        gpu = detect_gpu()

    os.environ["GIT_SHA"] = _resolve_git_sha(LOCAL_LOCK_FILE, use_local=not use_lock)

    command = (
        "docker compose "
        "-f compose.yml "
        f"{f'-f compose.{gpu}.yml ' if gpu != 'none' else ''}"
        "--env-file .env "
        f"--env-file {LOCAL_LOCK_FILE if not use_lock and LOCAL_LOCK_FILE.exists() else LOCK_FILE} "
        "up"
    )

    if not attached:
        command += " -d"

    bash_handoff(command)


def main():
    app()


if __name__ == "__main__":
    main()
