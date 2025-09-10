#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Iterable, Set

MAX_DEPTH: int = 3


def discover_projects(root: Path, max_depth: int = MAX_DEPTH) -> Set[Path]:
    """
    Walk `root` to a limited depth and return directories that contain a pyproject.toml.
    """
    dirs: Set[Path] = set()
    for dirpath, _dirnames, files in os.walk(str(root)):
        # compute depth relative to root
        rel = os.path.relpath(dirpath, str(root))
        depth = 0 if rel == "." else rel.count(os.sep) + 1
        if depth <= max_depth and "pyproject.toml" in files:
            dirs.add(Path(dirpath))
    return dirs


def sync_dirs(dirs: Iterable[Path]) -> None:
    """Run `uv sync` in each directory."""
    for d in sorted(dirs):
        print(f"🔧 syncing {d}")
        subprocess.run(["uv", "sync"], cwd=str(d), check=True)


def main(argv: list[str]) -> None:
    root_arg = argv[1] if len(argv) > 1 else "."
    root = Path(root_arg)
    sync_dirs(discover_projects(root))


if __name__ == "__main__":
    main(sys.argv)
