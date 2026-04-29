import pathlib
from asyncio import to_thread
from os import environ
from shutil import rmtree
from typing import List, cast
from uuid import UUID

from common.stream_tar import stream_tar
from litestar import Router, delete, get, post
from litestar.exceptions import ClientException, NotFoundException
from litestar.response import Stream
from litestar.status_codes import HTTP_409_CONFLICT

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


@get("")
async def get_captures() -> List[UUID]:
    return sorted([cast(UUID, capture.name) for capture in CAPTURES_DIRECTORY.glob("*") if capture.is_dir()])


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
    return Stream(
        stream_tar(capture_directory, exclude_suffixes=exclude_suffixes),
        media_type="application/x-tar",
        headers={"Content-Disposition": f'attachment; filename="{id}.tar"'},
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
