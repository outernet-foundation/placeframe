from __future__ import annotations

import os
import tarfile
from os import PathLike
from pathlib import Path


def build_tar(
    src_directory: str | PathLike[str],
    dst_path: str | PathLike[str],
    exclude_suffixes: tuple[str, ...] = (),
) -> None:
    src_path = Path(src_directory).resolve()
    if not src_path.is_dir():
        raise FileNotFoundError(f"{src_path} is not a directory")
    dst = Path(dst_path)
    # Atomic publish: build into a sibling .tmp, fsync, rename, fsync the parent
    # directory so a power loss between rename-journal-commit and data-flush
    # cannot leave the published name pointing at an empty inode.
    temp_path = dst.with_name(dst.name + ".tmp")
    if temp_path.exists():
        temp_path.unlink()
    with tarfile.open(temp_path, mode="w") as tar_file:
        for path in sorted(src_path.rglob("*")):
            if not path.is_file():
                continue
            if exclude_suffixes and path.suffix in exclude_suffixes:
                continue
            arcname = str(path.relative_to(src_path))
            tar_file.add(str(path), arcname=arcname, recursive=False)
    file_descriptor = os.open(temp_path, os.O_RDONLY)
    try:
        os.fsync(file_descriptor)
    finally:
        os.close(file_descriptor)
    temp_path.rename(dst)
    dir_fd = os.open(dst.parent, os.O_RDONLY)
    try:
        os.fsync(dir_fd)
    finally:
        os.close(dir_fd)
