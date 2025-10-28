import pathlib
import threading
from os import environ
from shutil import rmtree
from typing import List, Optional, cast
from uuid import UUID, uuid4

from anyio.to_thread import run_sync
from common.schemas import TarStreamResponse, tar_schema
from common.stream_tar import stream_tar
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse

if environ.get("CODEGEN"):
    from ..zed.zed_stub import CaptureThread
else:
    from ..zed.zed import CaptureThread


router = APIRouter(prefix="/captures", tags=["captures"])


CAPTURES_DIRECTORY = pathlib.Path.home() / "captures"
CAPTURES_DIRECTORY.mkdir(parents=True, exist_ok=True)
DEFAULT_CAPTURE_INTERVAL = 0.5

stop_event = threading.Event()
capture_thread: Optional[CaptureThread] = None


@router.post("/start")
async def start_capture(capture_interval: float | None = None):
    global capture_thread, stop_event

    if capture_thread and capture_thread.is_alive():
        raise HTTPException(detail="Capture already running", status_code=status.HTTP_409_CONFLICT)

    id = uuid4()
    stop_event = threading.Event()
    capture_thread = CaptureThread(
        stop_event, CAPTURES_DIRECTORY / str(id), capture_interval or DEFAULT_CAPTURE_INTERVAL
    )
    capture_thread.start()

    return id


@router.post("/stop")
async def stop_capture():
    global capture_thread, stop_event

    if not (capture_thread and capture_thread.is_alive()):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No capture running")

    stop_event.set()
    await run_sync(capture_thread.join)

    if capture_thread.exception():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Capture error: {capture_thread.exception()}"
        )

    capture_thread = None


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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Capture with id {id} not found")

    return StreamingResponse(
        stream_tar(capture_directory),
        media_type="application/x-tar",
        headers={"Content-Disposition": f'attachment; filename="{id}.tar"'},
    )


@router.delete("/{id}")
async def delete_capture(id: UUID):
    capture_directory = CAPTURES_DIRECTORY / str(id)
    if not capture_directory.exists():
        raise HTTPException(status_code=404, detail=f"Capture with id {id} not found")
    rmtree(capture_directory)
