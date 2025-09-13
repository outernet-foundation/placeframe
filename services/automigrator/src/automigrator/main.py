import hashlib
import os
import time
from pathlib import Path

from common.run_command import run_command as run_command_

from .settings import get_settings


def main():
    print("Creating initial migration if needed")
    create_and_rename_migration()

    print("Applying initial migrations")
    apply_migrations()

    print("Watching for changes")
    last_checksum: str = ""
    while True:
        current_checksum = hashlib.md5(
            "\n".join([
                f"{hashlib.md5(file.read_bytes()).hexdigest()}  {file}"
                for file in sorted((get_settings().api_dir / "src/db/tables").rglob("*.py"))
                if file.exists() and file.is_file()
            ]).encode("utf-8")
        ).hexdigest()

        if current_checksum != last_checksum and last_checksum:
            print("Changes detected, applying new migration")
            create_and_rename_migration()
            apply_migrations()

        last_checksum = current_checksum
        time.sleep(1)


def create_and_rename_migration() -> None:
    settings = get_settings()

    output = run_command("uv run --no-sync piccolo migrations new all --auto --auto_input=y")

    if "No changes detected" in output:
        return

    newest_file_path = max(
        list(Path(settings.api_dir).glob("**/migrations/*.py")), key=lambda candidate: candidate.stat().st_mtime
    )
    renamed = newest_file_path.with_name(f"{newest_file_path.stem}_auto-dev.py")
    newest_file_path.rename(renamed)
    print(f"Created new migration: {renamed}")


def apply_migrations():
    run_command("uv run --no-sync piccolo migrations forwards all")


def run_command(command: str):
    return run_command_(command, cwd=get_settings().api_dir, env=dict(os.environ))
