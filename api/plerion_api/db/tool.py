"""
db tool wrapper for Piccolo.

Usage (from project root):
    uv run db migrations new <app> [--auto ...]
    uv run db migrations forwards <app> [<migration_id>? ...]
"""

from __future__ import annotations

import os
import subprocess
import sys

LOCAL_CONF = "api.db.conf.local"
REMOTE_CONF = "api.db.conf.remote"


def _pick_conf(argv: list[str]) -> str | None:
    """
    Decide which PICCOLO_CONF to set based on the subcommand sequence.

    We only care about:
        migrations new      -> LOCAL_CONF
        migrations forwards -> REMOTE_CONF

    Anything else returns None (leave env as-is).
    """
    if len(argv) >= 2 and argv[0] == "migrations":
        if argv[1] == "new":
            return LOCAL_CONF
        if argv[1] == "forwards":
            return REMOTE_CONF
    return None


def main() -> int:
    args = sys.argv[1:]  # drop the 'db' wrapper name
    conf = _pick_conf(args)
    if conf is not None:
        os.environ["PICCOLO_CONF"] = conf

    # Exec Piccolo CLI under the current interpreter so we inherit the uv-managed env.
    cmd = [sys.executable, "-m", "piccolo"] + args
    return subprocess.call(cmd)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
