from __future__ import annotations

from os import environ
from pathlib import Path
from uuid import UUID

from common.fastapi import create_fastapi_app
from core.rig import CameraConfig, PinholeCameraConfig
from fastapi import File, HTTPException, UploadFile

from .localize import load_models
from .map_manager import LoadStateResponse, Localization, get_load_state, localize, start_load, unload

RECONSTRUCTIONS_DIR = Path("/tmp/reconstructions")
MAX_KEYPOINTS = 2500

if not environ.get("CODEGEN"):
    load_models(MAX_KEYPOINTS)


app = create_fastapi_app(title="Localize")

_camera: PinholeCameraConfig | None = None


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/reconstructions/{id}")
async def load_reconstruction(id: UUID):
    status = start_load(id)

    return {"status": status.value}


@app.delete("/reconstructions/{id}")
async def unload_reconstruction(id: UUID):
    unload(id)
    return {"ok": True}


@app.get("/reconstructions/{id}/status")
async def get_reconstruction_load_status(id: UUID) -> LoadStateResponse:
    return get_load_state(id)


@app.put("/camera")
async def set_camera_intrinsics(camera: CameraConfig):
    # only pinhole supported for now
    if camera.model != "PINHOLE":
        raise HTTPException(status_code=422, detail="Only PINHOLE camera model is supported")

    global _camera
    _camera = camera

    return {"ok": True}


@app.post("/localization")
async def localize_image(image: UploadFile = File(...)) -> list[Localization]:
    if _camera is None:
        raise HTTPException(status_code=400, detail="Camera intrinsics not set")

    return localize(camera=_camera, image=await image.read())
