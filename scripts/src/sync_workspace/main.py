#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import threading
import time
from pathlib import Path
from socket import gethostname
from typing import Any, List, Optional, cast

from typer import Option, run
from watchdog.events import FileSystemEvent, RegexMatchingEventHandler
from watchdog.observers import Observer

from ..run_command import run_command
from .sync_client import sync_client
from .sync_schema import sync_schema

repo_root = Path.cwd().resolve().parent

IGNORE_DIRNAMES = {".git", ".venv", "__pycache__", "bin", "obj", "clients"}


def make_watch_ignore_regexes() -> list[str]:
    # Ignore any path that contains /<name>/... or ends with /<name>
    # Works on Windows and POSIX thanks to [\\/]
    return [rf".*[\\/]{re.escape(name)}(?:[\\/].*|$)" for name in IGNORE_DIRNAMES]


WATCH_IGNORE_REGEXES = make_watch_ignore_regexes()


def cli(
    watch: bool = Option(False, "--watch", "-w", help="Watch for changes and re-sync as needed"),
    no_cache: bool = Option(False, "--no-cache", "-n", help="Do not use caching when syncing"),
    log: bool = Option(False, "--log", "-l", help="Log commands being run"),
):
    workspace_config = json.loads((repo_root / "workspace.json").read_text(encoding="utf-8"))

    env_path = repo_root / ".env"
    if not env_path.exists():
        print("WARNING: .env file does not exist, creating from .env.sample")
        env = (repo_root / ".env.sample").read_text()
        env = env.replace("<YOUR_DEVICE_NAME>", gethostname().lower())
        env = env.replace("<YOUR_HOME_DIRECTORY>", str(Path.home()).replace("\\", "/"))
        env_path.write_text(env)

    print("Syncing python projects")

    pyproject_paths = list(repo_root.rglob("pyproject.toml"))
    for path in pyproject_paths:
        # if path has "third_party" or "third-party" in any parent directory, skip it
        if any(part.lower() in {"third_party", "third-party"} for part in path.parts):
            continue

        if _ignored(path):
            continue
        _sync_uv(path.parent, log=log)

    print("Starting backend")

    run_command("docker compose up -d", cwd=repo_root, stream_log=log)

    print("Syncing schemas")

    databases: dict[Path, str] = {repo_root / k: v for k, v in workspace_config.get("databases", {}).items()}
    for path, database_name in databases.items():
        if _ignored(path):
            continue
        sync_schema(path, database_name, no_cache, log)

    print("Syncing OpenAPI clients")

    openapi_projects: dict[Path, List[Path]] = {
        repo_root / k: [repo_root / p for p in v] for k, v in workspace_config.get("openapi_projects", {}).items()
    }
    for path in openapi_projects.keys():
        sync_client(path, no_cache, log)

    if not watch:
        return

    print("Workspace synchronized, watching for changes...")

    observer = Observer()
    for path in pyproject_paths:
        observer.schedule(PyprojectHandler(log), str(path.parent), recursive=False)
    for path, database_name in databases.items():
        observer.schedule(DatabaseHandler(database_name, no_cache, log), str(path), recursive=True)
    for project_path, additional_paths in openapi_projects.items():
        observer.schedule(OpenApiHandler(project_path, project_path, no_cache, log), str(project_path), recursive=True)
        for additional_path in additional_paths:
            observer.schedule(
                OpenApiHandler(project_path, repo_root / additional_path, no_cache, log),
                str(repo_root / additional_path),
                recursive=True,
            )
    observer.daemon = True
    observer.start()

    # Keep the main thread alive
    try:
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


def _sync_uv(path: Path, log: bool):
    print(f"Syncing uv project: {path}")
    run_command("uv sync --all-groups --all-extras", cwd=path, log=log)


def _ignored(path: Path):
    parts = {p.lower() for p in path.parts}
    return any(name.lower() in parts for name in IGNORE_DIRNAMES)


class DebounceHandler(RegexMatchingEventHandler):
    def __init__(
        self, watch_path: Path, regexes: List[str], ignore_regexes: List[str], debounce_seconds: float = 0.4
    ) -> None:
        super().__init__(regexes=regexes, ignore_regexes=ignore_regexes, ignore_directories=True, case_sensitive=False)
        self.watch_path = watch_path
        self.debounce_seconds = debounce_seconds
        self.lock = threading.Lock()
        self._timer: Optional[threading.Timer] = None

    def _on_created(self, event: FileSystemEvent):
        print(f"Detected change: Created {event.src_path}")
        self._schedule(f"Created: {event.src_path}", cast(str, event.src_path))

    def _on_modified(self, event: FileSystemEvent):
        print(f"Detected change: Modified {event.src_path}")
        self._schedule(f"Modified: {event.src_path}", cast(str, event.src_path))

    def _on_deleted(self, event: FileSystemEvent):
        print(f"Detected change: Deleted {event.src_path}")
        self._schedule(f"Deleted: {event.src_path}", cast(str, event.src_path))

    def _on_moved(self, event: FileSystemEvent):
        print(f"Detected change: Moved {event.src_path} -> {cast(Any, event).dest_path}")
        self._schedule(f"Moved: {event.src_path} -> {cast(Any, event).dest_path}", cast(Any, event).dest_path)

    def _schedule(self, message: str, path: str):
        if self._timer is not None:
            self._timer.cancel()
        self._timer = threading.Timer(self.debounce_seconds, self._run_internal, args=(message, path))
        self._timer.daemon = True
        self._timer.start()

    def _run_internal(self, message: str, path: str):
        # If a git operation is in progress, skip syncing
        git_dir = repo_root / ".git"
        if any(
            (git_dir / sentinel).exists()
            for sentinel in [
                "rebase-merge",
                "rebase-apply",
                "MERGE_HEAD",
                "CHERRY_PICK_HEAD",
                "REVERT_HEAD",
                "BISECT_LOG",
            ]
        ):
            print("Git operation in progress, skipping sync")
            return

        with self.lock:
            self._run(message, path)
            print("Workspace synchronized, watching for changes...")

    def _run(self, message: str, path: str):
        pass  # To be implemented by subclasses


class PyprojectHandler(DebounceHandler):
    def __init__(self, log: bool) -> None:
        super().__init__(
            watch_path=repo_root, regexes=[r".*[\\/]pyproject\.toml$"], ignore_regexes=WATCH_IGNORE_REGEXES
        )
        self.log = log

    def _run(self, message: str, path: str):
        _sync_uv(Path(path).parent, log=self.log)

    def on_created(self, event: FileSystemEvent):
        self._on_created(event)

    def on_modified(self, event: FileSystemEvent):
        self._on_modified(event)


class DatabaseHandler(DebounceHandler):
    def __init__(self, database_name: str, no_cache: bool, log: bool) -> None:
        super().__init__(
            watch_path=repo_root, regexes=[r".*[\\/]database[\\/].*\.sql$"], ignore_regexes=WATCH_IGNORE_REGEXES
        )
        self.database_name = database_name
        self.no_cache = no_cache
        self.log = log

    def _run(self, message: str, path: str):
        sync_schema(Path(path).parent.parent, self.database_name, self.no_cache, self.log)

    def on_created(self, event: FileSystemEvent):
        self._on_created(event)

    def on_modified(self, event: FileSystemEvent):
        self._on_modified(event)

    def on_deleted(self, event: FileSystemEvent):
        self._on_deleted(event)

    def on_moved(self, event: FileSystemEvent):
        self._on_moved(event)


class OpenApiHandler(DebounceHandler):
    def __init__(self, project_root: Path, watch_path: Path, no_cache: bool, log: bool) -> None:
        super().__init__(watch_path=watch_path, regexes=[r".*\.py$"], ignore_regexes=WATCH_IGNORE_REGEXES)
        self.project_root = project_root
        self.no_cache = no_cache
        self.log = log

    def _run(self, message: str, path: str):
        sync_client(self.project_root, self.no_cache, self.log)

    def on_created(self, event: FileSystemEvent):
        self._on_created(event)

    def on_modified(self, event: FileSystemEvent):
        self._on_modified(event)

    def on_deleted(self, event: FileSystemEvent):
        self._on_deleted(event)

    def on_moved(self, event: FileSystemEvent):
        self._on_moved(event)


if __name__ == "__main__":
    run(cli)
