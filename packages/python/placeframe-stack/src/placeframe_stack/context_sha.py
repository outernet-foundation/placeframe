from __future__ import annotations

import os
import subprocess
from pathlib import Path, PurePosixPath
from tempfile import TemporaryDirectory

from typing import Any

import pathspec
import yaml


def _env_var_name(dockerfile_dir: str) -> str:
    return PurePosixPath(dockerfile_dir).name.upper().replace("-", "_") + "_SHA"


def _extract_service_dirs(bake_data: dict[str, Any]) -> set[str]:
    service_dirs: set[str] = set()
    services: dict[str, Any] = bake_data["services"]
    for config in services.values():
        build: dict[str, Any] = config.get("build", {})
        if not build.get("tags"):
            continue
        dockerfile: str = build.get("dockerfile", "")
        service_dirs.add(str(PurePosixPath(dockerfile).parent))
    return service_dirs


def compute_service_shas(repo_root: Path, bake_file: Path) -> dict[str, str]:
    repo_root = repo_root.resolve()

    bake_data: dict[str, Any] = yaml.safe_load(bake_file.read_text(encoding="utf-8"))
    service_dirs = _extract_service_dirs(bake_data)

    tree_entries = subprocess.run(
        ["git", "ls-tree", "-r", "HEAD"], cwd=str(repo_root), capture_output=True, text=True, check=True
    ).stdout.splitlines()

    dockerignore = repo_root / ".dockerignore"
    spec = pathspec.PathSpec.from_lines("gitignore", dockerignore.read_text().splitlines())

    allowed_entries: list[tuple[str, str, str]] = []
    for entry in tree_entries:
        meta, path = entry.split("\t", 1)
        if spec.match_file(path):
            continue
        mode, _type, obj_hash = meta.split()
        allowed_entries.append((mode, obj_hash, path))

    docker_prefix = "docker/"
    shared_entries: list[tuple[str, str, str]] = []
    per_service: dict[str, list[tuple[str, str, str]]] = {d: [] for d in service_dirs}

    for mode, obj_hash, path in allowed_entries:
        if path.startswith(docker_prefix):
            for service_dir in service_dirs:
                if path.startswith(service_dir + "/"):
                    per_service[service_dir].append((mode, obj_hash, path))
                    break
        else:
            shared_entries.append((mode, obj_hash, path))

    result: dict[str, str] = {}
    for service_dir in sorted(service_dirs):
        entries = shared_entries + per_service[service_dir]
        index_input = "\n".join(f"{mode} {obj_hash}\t{path}" for mode, obj_hash, path in entries) + "\n"

        with TemporaryDirectory() as tmpdir:
            env = {**os.environ, "GIT_INDEX_FILE": str(Path(tmpdir) / "index")}
            subprocess.run(
                ["git", "update-index", "--index-info"],
                cwd=str(repo_root),
                env=env,
                input=index_input.encode(),
                capture_output=True,
                check=True,
            )
            tree_hash = subprocess.run(
                ["git", "write-tree"], cwd=str(repo_root), env=env, capture_output=True, text=True, check=True
            ).stdout.strip()

        var_name = _env_var_name(service_dir)
        result[var_name] = f"tree-{tree_hash}"

    return result
