import sys
from typing import NoReturn


def bail(message: str, **fields: object) -> NoReturn:
    sys.stderr.write(f"ERROR: {message.format(**fields)}\n")
    sys.exit(1)


def warn(message: str, **fields: object) -> None:
    sys.stderr.write(f"WARNING: {message.format(**fields)}\n")


def note(message: str, **fields: object) -> None:
    sys.stderr.write(f"NOTE: {message.format(**fields)}\n")
