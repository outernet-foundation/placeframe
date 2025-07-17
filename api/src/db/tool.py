"""
db tool wrapper for Piccolo.

Default: use REMOTE_CONF (production / real DB).

Automatically switch to LOCAL_CONF for commands that *don't* need a live DB:
    - migrations new ...
    - project new ...
    - app new ...
    - asgi new ...
    - meta version

Everything else runs with REMOTE_CONF.
"""

import os
import subprocess
import sys
from typing import List

LOCAL_CONF = "src.db.local_conf"
REMOTE_CONF = "src.db.conf"


# ----- command classification -------------------------------------------------

_NO_DB_CMDS_TOP = {
    # top-level command -> always local
    "project": "new",  # we'll confirm subcmd is 'new' below
    "app": "new",
    "asgi": "new",
    "meta": "version",
}
# Note: we'll match only when the expected subcommand token is present
# so `piccolo meta somethingelse` falls through to remote.


def _needs_local(argv: List[str]) -> bool:
    """
    Return True if this argv sequence corresponds to a Piccolo command that
    *does not* require a live DB connection (so we use LOCAL_CONF).

    argv excludes the wrapper name (`db`).
    """
    if not argv:
        return False  # just `uv run db` -> fall through (remote default)

    cmd = argv[0]

    # migrations new
    if cmd == "migrations" and len(argv) >= 2 and argv[1] == "new":
        return True

    # project/app/asgi new
    expected = _NO_DB_CMDS_TOP.get(cmd)
    if expected and len(argv) >= 2 and argv[1] == expected:
        return True

    # meta version
    if cmd == "meta" and len(argv) >= 2 and argv[1] == "version":
        return True

    return False


def main() -> int:
    args = sys.argv[1:]

    if _needs_local(args):
        os.environ["PICCOLO_CONF"] = LOCAL_CONF
    else:
        # Don’t clobber an explicit override the user already set; only set if missing.
        os.environ.setdefault("PICCOLO_CONF", REMOTE_CONF)

    # Locate the piccolo console script in the current environment.
    python_bin = sys.executable
    bin_dir = os.path.dirname(python_bin)
    piccolo_path = os.path.join(bin_dir, "piccolo")

    if os.path.isfile(piccolo_path) and os.access(piccolo_path, os.X_OK):
        cmd = [piccolo_path] + args
    else:
        # Fallback – rely on PATH resolution.
        cmd = ["piccolo"] + args

    return subprocess.call(cmd)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
