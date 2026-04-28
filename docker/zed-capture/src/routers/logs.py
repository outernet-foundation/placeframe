from pathlib import Path
from typing import Annotated

from litestar import Router, get
from litestar.exceptions import ClientException
from litestar.params import Parameter
from litestar.status_codes import HTTP_400_BAD_REQUEST
from pydantic import BaseModel, Field

from ..logging_config import LOG_DIR, LOG_FILE_NAME
from ..state import cursor_store

# Response caps. Hit either and we set `has_more=True` so the client drains again.
DEFAULT_MAX_LINES = 1000
DEFAULT_MAX_BYTES = 4 * 1024 * 1024
LIMIT_UPPER_BOUND = 10000

# Force int64 in the OpenAPI schema — bytes-returned can exceed int32.
Int64 = Annotated[int, Field(json_schema_extra={"format": "int64"})]


class LogBatch(BaseModel):
    entries: list[str]
    next_cursor: str
    has_more: bool
    # True when the client's prior cursor pointed at logs that have since been
    # rotated off the end — caller missed some lines.
    dropped_before: bool
    bytes_returned: Int64


def _parse_cursor(cursor: str) -> tuple[int, int] | None:
    if not cursor:
        return None
    inode_str, _, offset_str = cursor.partition(":")
    if not inode_str or not offset_str:
        raise ClientException(detail=f"Invalid cursor format: {cursor!r}", status_code=HTTP_400_BAD_REQUEST)
    try:
        return (int(inode_str), int(offset_str))
    except ValueError:
        raise ClientException(detail=f"Invalid cursor format: {cursor!r}", status_code=HTTP_400_BAD_REQUEST)


def _ordered_log_files(log_dir: Path) -> list[Path]:
    # Backups sort oldest-first: app.jsonl.5, .4, ..., .1. Current file last.
    current = log_dir / LOG_FILE_NAME
    backups = sorted(
        (p for p in log_dir.glob(f"{LOG_FILE_NAME}.*") if p.suffix[1:].isdigit()),
        key=lambda p: int(p.suffix[1:]),
        reverse=True,
    )
    return [*backups, *([current] if current.exists() else [])]


def _read_lines_from_file(
    path: Path,
    start_offset: int,
    entries: list[str],
    line_limit: int,
    bytes_so_far: int,
    max_bytes: int,
) -> tuple[int, int, bool]:
    offset = start_offset
    bytes_returned = bytes_so_far
    with path.open("rb") as f:
        f.seek(offset)
        while True:
            line = f.readline()
            if not line:
                return offset, bytes_returned, False
            # Partial line (writer mid-line) — don't advance cursor past it.
            if not line.endswith(b"\n"):
                return offset, bytes_returned, False
            entries.append(line.decode("utf-8", errors="replace").rstrip("\n"))
            bytes_returned += len(line)
            offset += len(line)
            if len(entries) >= line_limit or bytes_returned >= max_bytes:
                return offset, bytes_returned, True


def read_logs(log_dir: Path, cursor: str, limit: int, max_bytes: int) -> LogBatch:
    files = _ordered_log_files(log_dir)
    if not files:
        return LogBatch(entries=[], next_cursor=cursor, has_more=False, dropped_before=False, bytes_returned=0)

    files_with_inode = [(p, p.stat().st_ino) for p in files]
    parsed = _parse_cursor(cursor)

    start_index = 0
    start_offset = 0
    dropped_before = False
    if parsed is not None:
        cursor_inode, cursor_offset = parsed
        match = next((i for i, (_, ino) in enumerate(files_with_inode) if ino == cursor_inode), None)
        if match is None:
            dropped_before = True
        else:
            start_index = match
            start_offset = cursor_offset

    entries: list[str] = []
    bytes_returned = 0
    last_inode = files_with_inode[start_index][1]
    last_offset = start_offset
    has_more = False

    for index in range(start_index, len(files_with_inode)):
        path, inode = files_with_inode[index]
        offset = start_offset if index == start_index else 0
        last_inode = inode
        last_offset, bytes_returned, hit_limit = _read_lines_from_file(
            path, offset, entries, limit, bytes_returned, max_bytes
        )
        if hit_limit:
            has_more = True
            break

    return LogBatch(
        entries=entries,
        next_cursor=f"{last_inode}:{last_offset}",
        has_more=has_more,
        dropped_before=dropped_before,
        bytes_returned=bytes_returned,
    )


@get("/logs")
async def get_logs(
    ack: Annotated[
        str,
        Parameter(description="Token from previous response; ack-on-next-fetch advances the box's persistent cursor"),
    ] = "",
    limit: Annotated[int, Parameter(ge=1, le=LIMIT_UPPER_BOUND)] = DEFAULT_MAX_LINES,
) -> LogBatch:
    # The box owns the cursor. The client's ack is best-effort: if it matches
    # what we last handed out, we advance and persist; otherwise we re-read
    # from the committed cursor (at-least-once delivery on forward failure).
    start = cursor_store.ack_and_get_committed(ack)
    batch = read_logs(LOG_DIR, start, limit, DEFAULT_MAX_BYTES)
    cursor_store.set_pending(batch.next_cursor)
    return batch


router = Router(path="/", tags=["logs"], route_handlers=[get_logs])
