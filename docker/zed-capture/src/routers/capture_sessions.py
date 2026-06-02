import pathlib
from asyncio import to_thread
from datetime import UTC, datetime
from os import environ
from shutil import rmtree
from typing import Annotated, List, cast
from uuid import UUID

from common.stream_tar import compute_tar_size, compute_tar_size_cached, stream_tar
from litestar import Router, delete, get, patch, post
from litestar.exceptions import ClientException, NotFoundException
from litestar.response import Stream
from litestar.status_codes import HTTP_409_CONFLICT, HTTP_422_UNPROCESSABLE_ENTITY
from pydantic import AwareDatetime, BaseModel, Field

CAPTURES_DIRECTORY = pathlib.Path.home() / "captures"
NAME_FILE = "name.txt"

if environ.get("CODEGEN"):
    from ..zed.zed_stub import InvalidStateException, Zed

    zed = Zed(CAPTURES_DIRECTORY)
else:
    from ..zed.zed import InvalidStateException, Zed

    zed = Zed(CAPTURES_DIRECTORY)
    zed.start()


DEFAULT_CAPTURE_INTERVAL = 0.5


class StopCaptureRequest(BaseModel):
    name: str


class UpdateCaptureSessionRequest(BaseModel):
    name: str


@post("/start")
async def start_capture(capture_interval: float | None = None) -> UUID:
    # Camera open is ~4s of synchronous work waiting on the actor-thread Future.
    # Off-loading to a worker thread keeps the event loop free so concurrent
    # /status polls don't queue up and time out, which would otherwise flip the
    # phone-side health monitor to Unreachable on every StartCapture.
    try:
        capture_id = await to_thread(zed.start_capture, capture_interval or DEFAULT_CAPTURE_INTERVAL)
    except InvalidStateException as e:
        raise ClientException(detail=str(e), status_code=HTTP_409_CONFLICT)
    # Placeholder so the non-null name invariant holds during the recording window
    # and survives a crash mid-recording. Overwritten by /stop with the operator's
    # chosen name on the normal path.
    _write_name(capture_id, _placeholder_name())
    return capture_id


@post("/stop")
async def stop_capture(data: StopCaptureRequest) -> None:
    name = _validate_name(data.name)
    active_id = zed.state().capture_id
    if active_id is None:
        raise ClientException(detail="No active capture", status_code=HTTP_409_CONFLICT)
    # Write sidecar before stopping so a sidecar-write failure leaves the
    # recording running rather than producing a finalized-but-nameless directory.
    _write_name(active_id, name)
    try:
        await to_thread(zed.stop_capture)
    except InvalidStateException as e:
        raise ClientException(detail=str(e), status_code=HTTP_409_CONFLICT)


class ZedCapture(BaseModel):
    id: UUID
    name: str
    recorded_at: AwareDatetime
    size_bytes: Annotated[int, Field(json_schema_extra={"format": "int64"})]


# Matches the default exclude_suffixes for download_capture_session_tar so size_bytes
# is the byte count the phone will actually upload.
_DEFAULT_UPLOAD_EXCLUDES: tuple[str, ...] = (".svo2",)


@get("")
async def get_capture_sessions() -> List[ZedCapture]:
    active_capture_id = zed.state().capture_id
    captures = [
        ZedCapture(
            id=cast(UUID, capture.name),
            name=_read_name(capture),
            # st_ctime is the directory's inode-change time. The directory is
            # created at recording-start and its child rig0/cameraN subdirs are
            # created within the same start_capture() call (see zed.py _start),
            # so st_ctime settles within ~ms of recording-start and is stable
            # for the rest of the session — close enough to "when recording
            # began" to display in the UI without writing a sidecar timestamp.
            recorded_at=datetime.fromtimestamp(capture.stat().st_ctime, tz=UTC),
            size_bytes=await to_thread(_capture_upload_size, capture, _DEFAULT_UPLOAD_EXCLUDES, active_capture_id),
        )
        for capture in CAPTURES_DIRECTORY.glob("*")
        if capture.is_dir() and (capture / NAME_FILE).exists()
    ]
    return sorted(captures, key=lambda c: c.id)


# Active recording grows mid-session, so its size cannot be cached.
def _capture_upload_size(
    capture_directory: pathlib.Path,
    exclude_suffixes: tuple[str, ...],
    active_capture_id: UUID | None,
) -> int:
    if active_capture_id is not None and capture_directory.name == str(active_capture_id):
        return compute_tar_size(capture_directory, exclude_suffixes)
    return compute_tar_size_cached(capture_directory, exclude_suffixes)


@patch("/{id:uuid}")
async def update_capture_session(id: UUID, data: UpdateCaptureSessionRequest) -> None:
    capture_directory = CAPTURES_DIRECTORY / str(id)
    if not capture_directory.exists():
        raise NotFoundException(f"Capture with id {id} not found")
    name = _validate_name(data.name)
    _write_name(id, name)


@get(
    "/{id:uuid}/tar",
    media_type="application/x-tar",
    content_encoding="binary",
    content_media_type="application/x-tar",
)
async def download_capture_session_tar(id: UUID, include_svo: bool = False) -> Stream:
    capture_directory = CAPTURES_DIRECTORY / str(id)
    if not capture_directory.exists():
        raise NotFoundException(f"Capture with id {id} not found")

    exclude_suffixes = () if include_svo else (".svo2",)
    total_bytes = await to_thread(_capture_upload_size, capture_directory, exclude_suffixes, zed.state().capture_id)
    return Stream(
        stream_tar(capture_directory, exclude_suffixes=exclude_suffixes),
        media_type="application/x-tar",
        headers={
            "Content-Disposition": f'attachment; filename="{id}.tar"',
            "Content-Length": str(total_bytes),
        },
    )


@delete("/{id:uuid}")
async def delete_capture_session(id: UUID) -> None:
    capture_directory = CAPTURES_DIRECTORY / str(id)
    if not capture_directory.exists():
        raise NotFoundException(f"Capture with id {id} not found")
    rmtree(capture_directory)


@delete("")
async def delete_all_capture_sessions() -> None:
    for capture in CAPTURES_DIRECTORY.glob("*"):
        if capture.is_dir():
            rmtree(capture)


def _validate_name(name: str) -> str:
    stripped = name.strip()
    if not stripped:
        raise ClientException(detail="name must be non-empty", status_code=HTTP_422_UNPROCESSABLE_ENTITY)
    return stripped


def _write_name(capture_id: UUID, name: str) -> None:
    (CAPTURES_DIRECTORY / str(capture_id) / NAME_FILE).write_text(name, encoding="utf-8")


def _read_name(capture_directory: pathlib.Path) -> str:
    return (capture_directory / NAME_FILE).read_text(encoding="utf-8").strip()


def _placeholder_name() -> str:
    return f"Capture {datetime.now(tz=UTC).strftime('%Y-%m-%d %H:%M:%S')}"


router = Router(
    path="/capture_sessions",
    tags=["Capture Sessions"],
    route_handlers=[
        start_capture,
        stop_capture,
        get_capture_sessions,
        update_capture_session,
        download_capture_session_tar,
        delete_capture_session,
        delete_all_capture_sessions,
    ],
)
