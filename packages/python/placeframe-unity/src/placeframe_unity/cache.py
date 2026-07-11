from __future__ import annotations

import platform
import shutil
import sys
import tempfile
from pathlib import Path
from subprocess import CalledProcessError

from bashrun import bash, bash_check, bash_pipe


def _posix(path: Path) -> str:
    return path.as_posix() if platform.system() == "Windows" else str(path)


def restore(
    registry: str,
    name: str,
    tag: str,
    target_directory: Path,
    *,
    required: bool = False,
    fallback_tags: list[str] | None = None,
) -> bool:
    # OCI repository names must be lowercase; GitHub repository names preserve case
    registry = registry.lower()
    staging = Path(tempfile.gettempdir()) / "cache"

    for candidate_tag in [tag, *(fallback_tags or [])]:
        if candidate_tag != tag:
            print(f"Falling back to {name}:{candidate_tag}")

        reference = f"{registry}/{name}:{candidate_tag}"
        staging.mkdir(parents=True, exist_ok=True)

        if not bash_check(f"oras pull {reference} -o {staging}"):
            shutil.rmtree(staging, ignore_errors=True)
            continue

        archive = staging / f"{name}.tar.zst"
        try:
            if platform.system() == "Windows":
                bash_pipe(f"zstd -d {_posix(archive)} --stdout", f"tar -xf - -C {_posix(target_directory)}")
            else:
                bash(f"tar -xf {archive} -C {target_directory}")
        except CalledProcessError:
            print(f"WARNING: Cache extraction failed for {name}:{candidate_tag}, trying next")
            shutil.rmtree(staging, ignore_errors=True)
            continue

        shutil.rmtree(staging, ignore_errors=True)
        print(f"Cache hit: {name}:{candidate_tag}")
        return True

    if required:
        print(f"FATAL: Required cache missing: {registry}/{name}:{tag}")
        sys.exit(1)

    print(f"Cache miss: {name}")
    return False


def save(registry: str, name: str, tag: str, source_directory: Path, paths: list[str]) -> None:
    # OCI repository names must be lowercase; GitHub repository names preserve case
    registry = registry.lower()
    resolved: list[str] = []
    for pattern in paths:
        if any(character in pattern for character in "*?["):
            matches = sorted(source_directory.glob(pattern))
            resolved.extend(str(match.relative_to(source_directory)) for match in matches)
        else:
            resolved.append(pattern)

    staging = Path(tempfile.gettempdir()) / "cache"
    staging.mkdir(parents=True, exist_ok=True)
    archive_name = f"{name}.tar.zst"
    archive_path = staging / archive_name

    joined = " ".join(resolved)
    if platform.system() == "Windows":
        bash_pipe(f"tar -cf - {joined}", f"zstd -o {_posix(archive_path)}", cwd=source_directory)
    else:
        bash(f"tar --zstd -cf {archive_path} {joined}", cwd=source_directory)

    reference = f"{registry}/{name}:{tag}"
    bash(f"oras push {reference} {archive_name}:application/vnd.placeframe.cache.v1+zstd", cwd=staging)
    archive_path.unlink()
    print(f"Saved cache: {reference}")
