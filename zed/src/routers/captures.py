import pathlib
from os import environ
from shutil import rmtree
from typing import List, cast
from uuid import UUID

from common.schemas import TarStreamResponse, tar_schema
from common.stream_tar import stream_tar
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from litestar.exceptions import NotFoundException

CAPTURES_DIRECTORY = pathlib.Path.home() / "captures"

if environ.get("CODEGEN"):
    from ..zed.zed_stub import InvalidStateException, Zed

    zed = Zed(CAPTURES_DIRECTORY)
else:
    from ..zed.zed import InvalidStateException, Zed

    zed = Zed(CAPTURES_DIRECTORY)
    zed.start()

router = APIRouter(prefix="/captures", tags=["captures"])


DEFAULT_CAPTURE_INTERVAL = 0.5


@router.post("/start")
async def start_capture(capture_interval: float | None = None):
    try:
        return zed.start_capture(capture_interval or DEFAULT_CAPTURE_INTERVAL)
    except InvalidStateException as e:
        raise HTTPException(detail=str(e), status_code=status.HTTP_409_CONFLICT)


@router.post("/stop")
async def stop_capture():
    try:
        zed.stop_capture()
    except InvalidStateException as e:
        raise HTTPException(detail=str(e), status_code=status.HTTP_409_CONFLICT)


@router.get("")
async def get_captures() -> List[UUID]:
    return sorted([cast(UUID, capture.name) for capture in CAPTURES_DIRECTORY.glob("*") if capture.is_dir()])


@router.get(
    "/{id}",
    # https://github.com/fastapi/fastapi/discussions/6964
    response_class=TarStreamResponse,
    responses={200: {"content": tar_schema}},
)
async def download_capture_tar(id: UUID):
    capture_directory = CAPTURES_DIRECTORY / str(id)
    if not capture_directory.exists():
        raise NotFoundException(f"Capture with id {id} not found")

    return StreamingResponse(
        stream_tar(capture_directory),
        media_type="application/x-tar",
        headers={"Content-Disposition": f'attachment; filename="{id}.tar"'},
    )


@router.delete("/{id}")
async def delete_capture(id: UUID):
    capture_directory = CAPTURES_DIRECTORY / str(id)
    if not capture_directory.exists():
        raise NotFoundException(f"Capture with id {id} not found")
    rmtree(capture_directory)
