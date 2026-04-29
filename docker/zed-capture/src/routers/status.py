from importlib.metadata import PackageNotFoundError, version
from shutil import disk_usage
from time import monotonic
from typing import Annotated
from uuid import UUID

from litestar import Router, get
from pydantic import BaseModel, Field

from ..cursor_store import cursor_store
from .captures import CAPTURES_DIRECTORY, zed

_START_MONOTONIC = monotonic()


def _read_version() -> str:
    try:
        return version("zed")
    except PackageNotFoundError:
        return "unknown"


_VERSION = _read_version()


# Disk free bytes exceeds int32 on modern storage; force int64 in the OpenAPI
# schema so generated clients (notably openapi-generator's C#) emit `long`.
# Must go through Pydantic `Field(json_schema_extra=...)` — Litestar's OpenAPI
# generator reads that path but ignores `pydantic.WithJsonSchema` markers.
Int64 = Annotated[int, Field(json_schema_extra={"format": "int64"})]


class ZedStatus(BaseModel):
    current_capture_id: UUID | None
    last_exception: str | None
    disk_free_bytes: Int64
    uptime_s: float
    version: str
    log_cursor: str


def compute_status() -> ZedStatus:
    state = zed.state()
    disk_path = CAPTURES_DIRECTORY if CAPTURES_DIRECTORY.exists() else CAPTURES_DIRECTORY.parent
    return ZedStatus(
        current_capture_id=state.capture_id,
        last_exception=state.last_exception,
        disk_free_bytes=disk_usage(disk_path).free,
        uptime_s=monotonic() - _START_MONOTONIC,
        version=_VERSION,
        log_cursor=cursor_store.committed,
    )


@get("/status")
async def get_status() -> ZedStatus:
    return compute_status()


router = Router(path="/", tags=["status"], route_handlers=[get_status])
