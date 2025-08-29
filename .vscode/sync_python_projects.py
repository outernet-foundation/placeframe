#!/usr/bin/env python3
import os, subprocess, sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
MAX_DEPTH = 3
dirs = set()

for dirpath, _, files in os.walk(ROOT):
    # compute depth relative to ROOT
    rel = os.path.relpath(dirpath, ROOT)
    depth = 0 if rel == "." else rel.count(os.sep) + 1
    if depth <= MAX_DEPTH and "pyproject.toml" in files:
        dirs.add(dirpath)

for d in sorted(dirs):
    print(f"🔧 syncing {d}")
    subprocess.run(["uv", "sync"], cwd=d, check=True)
