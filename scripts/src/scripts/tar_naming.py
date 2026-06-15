import re
from pathlib import Path
from uuid import UUID

# Collapse any run of filesystem-unfriendly characters (spaces, slashes, etc.) into a single dash so a
# human-readable capture/session name becomes a safe tar filename.
_UNSAFE = re.compile(r"[^A-Za-z0-9._-]+")


# Default export path under `directory`: the row's name as the filename, sanitized. Falls back to the id
# when the name is empty or sanitizes to nothing, and appends the id when the name-based file already
# exists (reconstructions of the same capture share a name) so an export never silently clobbers another.
def export_destination(name: str, identifier: UUID, directory: Path) -> Path:
    stem = _UNSAFE.sub("-", name).strip("-._") or str(identifier)

    candidate = directory / f"{stem}.tar"
    if not candidate.exists():
        return candidate

    return directory / f"{stem}-{identifier}.tar"
