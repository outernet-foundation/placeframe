from __future__ import annotations

import platform
import shutil
import sys
import tempfile
from pathlib import Path
from subprocess import CalledProcessError

from common.bash import bash, bash_check, bash_pipe


def _posix(path: Path) -> str:
    return path.as_posix() if platform.system() == "Windows" else str(path)


def restore(registry: str, name: str, tag: str, target_directory: Path, *, required: bool = False) -> bool:
    reference = f"{registry}/{name}:{tag}"
    staging = Path(tempfile.gettempdir()) / "cache"
    staging.mkdir(parents=True, exist_ok=True)

    hit = bash_check(f"oras pull {reference} -o {staging}")

    if hit:
        archive = staging / f"{name}.tar.zst"
        try:
            if platform.system() == "Windows":
                bash_pipe(f"zstd -d {_posix(archive)} --stdout", f"tar -xf - -C {_posix(target_directory)}")
            else:
                bash(f"tar -xf {archive} -C {target_directory}")
        except CalledProcessError:
            print(f"WARNING: Cache extraction failed for {name}, treating as cache miss")
            hit = False
        shutil.rmtree(staging)

    if hit:
        print(f"Cache hit: {name}")
    elif required:
        print(f"FATAL: Required cache missing: {reference}")
        sys.exit(1)
    else:
        print(f"Cache miss: {name}")

    return hit


def save(registry: str, name: str, tag: str, source_directory: Path, paths: list[str]) -> None:
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
