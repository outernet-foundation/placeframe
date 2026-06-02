import json
import pathlib
from asyncio import to_thread
from datetime import UTC, datetime
from os import environ
from shutil import rmtree
from typing import Annotated, List
from uuid import UUID

from common.stream_tar import build_tar
from litestar import Router, delete, get, patch, post
from litestar.exceptions import ClientException, NotFoundException
from litestar.response import File
from litestar.status_codes import HTTP_409_CONFLICT, HTTP_422_UNPROCESSABLE_ENTITY
from pydantic import AwareDatetime, BaseModel, Field

if environ.get("CODEGEN"):
    from ..zed.zed_stub import InvalidStateException, Zed
else:
    from ..zed.zed import InvalidStateException, Zed

CAPTURES_DIRECTORY = pathlib.Path.home() / "captures"

# Recording artifacts (rig0/, frames.csv, manifest.json, *.svo2) live in
# CAPTURES_DIRECTORY / <id>/ and are write-once after stop_capture finishes.
# Mutable metadata (operator-chosen name) lives outside that directory in
# CAPTURES_DIRECTORY / <id>.meta.json, so the tar payload remains immutable and
# its on-disk size matches the Content-Length declared by the static-file
# response for every byte.
META_SUFFIX = ".meta.json"
TAR_SUFFIX = ".tar"

# The phone never uploads svo2 (large binary recordings used for offline
# replay), so the pre-built tar excludes them by construction.
_TAR_EXCLUDE_SUFFIXES: tuple[str, ...] = (".svo2",)

# Legacy on-disk shape from before metadata-outside-dir and from the cached
# Content-Length scheme. The startup migration converts these forward so no
# future tar-build sees them.
_LEGACY_CACHE_PREFIX = ".placeframe_tar_size_cache."
_LEGACY_NAME_FILE = "name.txt"

DEFAULT_CAPTURE_INTERVAL = 0.5


class ZedCapture(BaseModel):
    id: UUID
    name: str
    recorded_at: AwareDatetime
    size_bytes: Annotated[int, Field(json_schema_extra={"format": "int64"})]


class StopCaptureRequest(BaseModel):
    name: str


class UpdateCaptureSessionRequest(BaseModel):
    name: str


zed = Zed(CAPTURES_DIRECTORY)


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
    # Placeholder so the non-null name invariant holds during the recording
    # window and survives a crash mid-recording. Overwritten by /stop with the
    # operator's chosen name on the normal path.
    _write_meta(capture_id, _placeholder_name())
    return capture_id


@post("/stop")
async def stop_capture(data: StopCaptureRequest) -> None:
    name = _validate_name(data.name)
    active_id = zed.state().capture_id
    if active_id is None:
        raise ClientException(detail="No active capture", status_code=HTTP_409_CONFLICT)
    try:
        await to_thread(zed.stop_capture)
    except InvalidStateException as e:
        raise ClientException(detail=str(e), status_code=HTTP_409_CONFLICT)
    # Commit the operator's chosen name before building the tar so a build
    # failure leaves the meta intact for the startup migration to rebuild the
    # tar on the next container restart.
    _write_meta(active_id, name)
    await to_thread(
        build_tar,
        _recording_directory(active_id),
        _tar_path(active_id),
        _TAR_EXCLUDE_SUFFIXES,
    )


@get("")
async def get_capture_sessions() -> List[ZedCapture]:
    return sorted(
        [
            ZedCapture(
                id=capture_id,
                name=_read_meta(capture_id)["name"],
                # st_ctime is the recording directory's inode-change time. The
                # directory is created at recording-start and its child
                # rig0/cameraN subdirs are created within the same start_capture()
                # call (see zed.py _start), so st_ctime settles within ~ms of
                # recording-start and is stable for the rest of the session.
                recorded_at=datetime.fromtimestamp(_recording_directory(capture_id).stat().st_ctime, tz=UTC),
                size_bytes=_tar_path(capture_id).stat().st_size,
            )
            for capture_id in _finalized_capture_ids()
        ],
        key=lambda c: c.id,
    )


@patch("/{id:uuid}")
async def update_capture_session(id: UUID, data: UpdateCaptureSessionRequest) -> None:
    if not _meta_path(id).exists():
        raise NotFoundException(f"Capture with id {id} not found")
    _write_meta(id, _validate_name(data.name))


@get(
    "/{id:uuid}/tar",
    media_type="application/x-tar",
    content_encoding="binary",
    content_media_type="application/x-tar",
)
async def download_capture_session_tar(id: UUID) -> File:
    tar_path = _tar_path(id)
    if not tar_path.exists():
        raise NotFoundException(f"Capture with id {id} not found")
    return File(
        path=tar_path,
        filename=f"{id}.tar",
        media_type="application/x-tar",
    )


@delete("/{id:uuid}")
async def delete_capture_session(id: UUID) -> None:
    if not (_meta_path(id).exists() or _recording_directory(id).exists() or _tar_path(id).exists()):
        raise NotFoundException(f"Capture with id {id} not found")
    _delete_capture(id)


@delete("")
async def delete_all_capture_sessions() -> None:
    for capture_id in _all_capture_ids():
        _delete_capture(capture_id)


def _validate_name(name: str) -> str:
    stripped = name.strip()
    if not stripped:
        raise ClientException(detail="name must be non-empty", status_code=HTTP_422_UNPROCESSABLE_ENTITY)
    return stripped


def _write_meta(capture_id: UUID, name: str) -> None:
    meta_path = _meta_path(capture_id)
    temp_path = meta_path.with_name(meta_path.name + ".tmp")
    temp_path.write_text(json.dumps({"name": name}), encoding="utf-8")
    temp_path.rename(meta_path)


def _read_meta(capture_id: UUID) -> dict[str, str]:
    return json.loads(_meta_path(capture_id).read_text(encoding="utf-8"))


def _recording_directory(capture_id: UUID) -> pathlib.Path:
    return CAPTURES_DIRECTORY / str(capture_id)


def _meta_path(capture_id: UUID) -> pathlib.Path:
    return CAPTURES_DIRECTORY / f"{capture_id}{META_SUFFIX}"


def _tar_path(capture_id: UUID) -> pathlib.Path:
    return CAPTURES_DIRECTORY / f"{capture_id}{TAR_SUFFIX}"


def _finalized_capture_ids() -> list[UUID]:
    return [UUID(path.name.removesuffix(TAR_SUFFIX)) for path in CAPTURES_DIRECTORY.glob(f"*{TAR_SUFFIX}")]


def _all_capture_ids() -> list[UUID]:
    ids: list[UUID] = []
    for entry in CAPTURES_DIRECTORY.glob("*"):
        if not entry.is_dir():
            continue
        try:
            ids.append(UUID(entry.name))
        except ValueError:
            continue
    return ids


def _placeholder_name() -> str:
    return f"Capture {datetime.now(tz=UTC).strftime('%Y-%m-%d %H:%M:%S')}"


def _delete_capture(capture_id: UUID) -> None:
    recording = _recording_directory(capture_id)
    if recording.exists():
        rmtree(recording)
    _tar_path(capture_id).unlink(missing_ok=True)
    _meta_path(capture_id).unlink(missing_ok=True)


def _migrate_legacy_captures() -> None:
    CAPTURES_DIRECTORY.mkdir(parents=True, exist_ok=True)
    for recording in CAPTURES_DIRECTORY.glob("*"):
        if not recording.is_dir():
            continue
        try:
            capture_id = UUID(recording.name)
        except ValueError:
            continue
        # Forward-migrate the legacy on-disk shape: name.txt-inside-dir → sibling
        # meta.json; delete stale Content-Length cache sidecars.
        legacy_name_file = recording / _LEGACY_NAME_FILE
        meta_path = _meta_path(capture_id)
        if legacy_name_file.exists() and not meta_path.exists():
            legacy_name = legacy_name_file.read_text(encoding="utf-8").strip()
            _write_meta(capture_id, legacy_name or _placeholder_name())
        legacy_name_file.unlink(missing_ok=True)
        for cache_file in recording.glob(f"{_LEGACY_CACHE_PREFIX}*"):
            cache_file.unlink(missing_ok=True)
        # Rebuild the immutable tar for any recording whose meta exists but
        # whose tar is missing (legacy captures pre-migration, or a previous
        # stop_capture that crashed between recording-stop and tar-build).
        tar_path = _tar_path(capture_id)
        if meta_path.exists() and not tar_path.exists():
            build_tar(recording, tar_path, _TAR_EXCLUDE_SUFFIXES)


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


if not environ.get("CODEGEN"):
    _migrate_legacy_captures()
    zed.start()
