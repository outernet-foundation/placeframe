from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from enum import Enum
from pathlib import Path
from shutil import rmtree
from threading import Lock
from uuid import UUID

from common.boto_clients import create_s3_client
from common.classes import CameraIntrinsics, LocalizationMetrics, Transform
from fastapi import FastAPI, File, HTTPException, UploadFile
from pycolmap import Camera, CameraModelId
from torch import cuda  # type: ignore

from .localize import localize_image_against_reconstruction
from .map import Map, load_map_data
from .settings import get_settings

DEVICE = "cuda" if cuda.is_available() else "cpu"
print(f"Using device: {DEVICE}")

RECONSTRUCTIONS_DIR = Path("/tmp/reconstructions")


maps: dict[UUID, Map] = {}
settings = get_settings()
s3_client = create_s3_client(
    s3_endpoint_url=settings.s3_endpoint_url, s3_access_key=settings.s3_access_key, s3_secret_key=settings.s3_secret_key
)


app = FastAPI(title="FastAPI App")


class LoadState(str, Enum):
    PENDING = "pending"
    LOADING = "loading"
    READY = "ready"
    FAILED = "failed"


_executor = ThreadPoolExecutor(max_workers=2)
_load_lock = Lock()
_load_state: dict[UUID, LoadState] = {}
_load_error: dict[UUID, str] = {}

_camera = Camera()


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


def _start_load_reconstruction(id: UUID):
    with _load_lock:
        state = _load_state.get(id)
        if state is not None:
            return state
        _load_state[id] = LoadState.LOADING

        def _on_done(future: Future[None]) -> None:
            try:
                future.result()
            except Exception as e:
                print(f"Failed to load reconstruction {id}: {e}")
                with _load_lock:
                    _load_state[id] = LoadState.FAILED
                    _load_error[id] = str(e)
            else:
                with _load_lock:
                    _load_state[id] = LoadState.READY

        future = _executor.submit(_load_reconstruction, id)
        future.add_done_callback(_on_done)
        return LoadState.LOADING


def _load_reconstruction(id: UUID):
    for page in s3_client.get_paginator("list_objects_v2").paginate(
        Bucket=settings.reconstructions_bucket, Prefix=str(id)
    ):
        for obj in page.get("Contents", []):
            key = obj["Key"]  # type: ignore
            local_path = RECONSTRUCTIONS_DIR / str(id) / key[len(str(id)) :].lstrip("/")
            local_path.parent.mkdir(parents=True, exist_ok=True)  # Ensure parent dirs exist
            print(f"Downloading s3://{settings.reconstructions_bucket}/{key} to {local_path}")
            s3_client.download_file(settings.reconstructions_bucket, key, str(local_path))

    maps[id] = load_map_data(reconstruction_path=RECONSTRUCTIONS_DIR / str(id), device=DEVICE)


@app.post("/reconstructions/{id}")
async def load_reconstruction(id: UUID):
    status = _start_load_reconstruction(id)
    if status == LoadState.FAILED:
        raise HTTPException(
            status_code=500, detail=f"Failed to load reconstruction: {_load_error.get(id, 'Unknown error')}"
        )

    return {"status": status.value}


@app.delete("/reconstructions/{id}")
async def unload_reconstruction(id: UUID):
    with _load_lock:
        _load_state.pop(id, None)
        _load_error.pop(id, None)
    maps.pop(id, None)
    rmtree(RECONSTRUCTIONS_DIR / str(id))
    return {"ok": True}


@app.get("/reconstructions/{id}/status")
async def get_reconstruction_load_status(id: UUID) -> dict[str, str]:
    with _load_lock:
        if id not in _load_state:
            return {"status": LoadState.PENDING.value}

        if _load_state[id] == LoadState.FAILED:
            return {"status": _load_state[id].value, "error": _load_error[id]}

        return {"status": _load_state[id].value}


@app.put("/camera")
async def set_camera_intrinsics(camera: CameraIntrinsics):
    # only pinhole supported for now
    if camera["model"] != "PINHOLE":
        raise HTTPException(status_code=422, detail="Only PINHOLE camera model is supported")

    _camera.model = CameraModelId.PINHOLE
    _camera.params = [camera["fx"], camera["fy"], camera["cx"], camera["cy"]]
    _camera.width = camera["width"]
    _camera.height = camera["height"]

    return {"ok": True}


@app.post("/localization")
async def localize_image(image: UploadFile = File(...)) -> dict[UUID, tuple[Transform, LocalizationMetrics]]:
    return {
        id: await localize_image_against_reconstruction(map=maps[id], camera=_camera, image=await image.read())
        for id in maps.keys()
    }
