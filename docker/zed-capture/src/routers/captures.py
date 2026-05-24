import pathlib
from asyncio import to_thread
from datetime import UTC, datetime
from os import environ
from shutil import rmtree
from typing import Annotated, List, cast
from uuid import UUID

from common.stream_tar import compute_tar_size, stream_tar
from litestar import Router, delete, get, post
from litestar.exceptions import ClientException, NotFoundException
from litestar.response import Stream
from litestar.status_codes import HTTP_409_CONFLICT
from pydantic import AwareDatetime, BaseModel, Field

CAPTURES_DIRECTORY = pathlib.Path.home() / "captures"

if environ.get("CODEGEN"):
    from ..zed.zed_stub import InvalidStateException, Zed

    zed = Zed(CAPTURES_DIRECTORY)
else:
    from ..zed.zed import InvalidStateException, Zed

    zed = Zed(CAPTURES_DIRECTORY)
    zed.start()


DEFAULT_CAPTURE_INTERVAL = 0.5


@post("/start")
async def start_capture(capture_interval: float | None = None) -> UUID:
    # Camera open is ~4s of synchronous work waiting on the actor-thread Future.
    # Off-loading to a worker thread keeps the event loop free so concurrent
    # /status polls don't queue up and time out, which would otherwise flip the
    # phone-side health monitor to Unreachable on every StartCapture.
    try:
        return await to_thread(zed.start_capture, capture_interval or DEFAULT_CAPTURE_INTERVAL)
    except InvalidStateException as e:
        raise ClientException(detail=str(e), status_code=HTTP_409_CONFLICT)


@post("/stop")
async def stop_capture() -> None:
    try:
        await to_thread(zed.stop_capture)
    except InvalidStateException as e:
        raise ClientException(detail=str(e), status_code=HTTP_409_CONFLICT)


class ZedCapture(BaseModel):
    id: UUID
    recorded_at: AwareDatetime
    size_bytes: Annotated[int, Field(json_schema_extra={"format": "int64"})]


# Matches the default exclude_suffixes for download_capture_tar so size_bytes
# is the byte count the phone will actually upload.
_DEFAULT_UPLOAD_EXCLUDES: tuple[str, ...] = (".svo2",)


@get("")
async def get_captures() -> List[ZedCapture]:
    captures = [
        ZedCapture(
            id=cast(UUID, capture.name),
            # st_ctime is the directory's inode-change time. The directory is
            # created at recording-start and its child rig0/cameraN subdirs are
            # created within the same start_capture() call (see zed.py _start),
            # so st_ctime settles within ~ms of recording-start and is stable
            # for the rest of the session — close enough to "when recording
            # began" to display in the UI without writing a sidecar timestamp.
            recorded_at=datetime.fromtimestamp(capture.stat().st_ctime, tz=UTC),
            size_bytes=await to_thread(compute_tar_size, capture, _DEFAULT_UPLOAD_EXCLUDES),
        )
        for capture in CAPTURES_DIRECTORY.glob("*")
        if capture.is_dir()
    ]
    return sorted(captures, key=lambda c: c.id)


@get(
    "/{id:uuid}",
    media_type="application/x-tar",
    content_encoding="binary",
    content_media_type="application/x-tar",
)
async def download_capture_tar(id: UUID, include_svo: bool = False) -> Stream:
    capture_directory = CAPTURES_DIRECTORY / str(id)
    if not capture_directory.exists():
        raise NotFoundException(f"Capture with id {id} not found")

    exclude_suffixes = () if include_svo else (".svo2",)
    total_bytes = await to_thread(compute_tar_size, capture_directory, exclude_suffixes)
    return Stream(
        stream_tar(capture_directory, exclude_suffixes=exclude_suffixes),
        media_type="application/x-tar",
        headers={
            "Content-Disposition": f'attachment; filename="{id}.tar"',
            "Content-Length": str(total_bytes),
        },
    )


@delete("/{id:uuid}")
async def delete_capture(id: UUID) -> None:
    capture_directory = CAPTURES_DIRECTORY / str(id)
    if not capture_directory.exists():
        raise NotFoundException(f"Capture with id {id} not found")
    rmtree(capture_directory)


@delete("")
async def delete_all_captures() -> None:
    for capture in CAPTURES_DIRECTORY.glob("*"):
        if capture.is_dir():
            rmtree(capture)


router = Router(
    path="/captures",
    tags=["captures"],
    route_handlers=[
        start_capture,
        stop_capture,
        get_captures,
        download_capture_tar,
        delete_capture,
        delete_all_captures,
    ],
)
