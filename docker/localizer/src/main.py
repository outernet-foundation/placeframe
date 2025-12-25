from __future__ import annotations

from os import environ
from pathlib import Path
from uuid import UUID

from common.fastapi import create_fastapi_app
from core.axis_convention import AxisConvention
from core.camera_config import PinholeCameraConfig
from fastapi import File, HTTPException, UploadFile

# from .localize import load_models
# from .map_manager import get_load_state, localize, start_load, unload
from .schemas import LoadStateResponse, Localization

RECONSTRUCTIONS_DIR = Path("/tmp/reconstructions")
MAX_KEYPOINTS = 2500

if not environ.get("CODEGEN"):
    from .localize import load_models

    load_models(MAX_KEYPOINTS)


app = create_fastapi_app(title="Localize")

_camera: PinholeCameraConfig | None = None


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/reconstructions/{id}")
async def load_reconstruction(id: UUID):
    if environ.get("CODEGEN"):
        raise

    from .map_manager import start_load

    status = start_load(id)
    return {"status": status.value}


@app.delete("/reconstructions/{id}")
async def unload_reconstruction(id: UUID):
    if environ.get("CODEGEN"):
        raise

    from .map_manager import unload

    unload(id)
    return {"ok": True}


@app.get("/reconstructions/{id}/status")
async def get_reconstruction_load_status(id: UUID) -> LoadStateResponse:
    if environ.get("CODEGEN"):
        raise

    from .map_manager import get_load_state

    return get_load_state(id)


@app.put("/camera")
async def set_camera_intrinsics(camera: PinholeCameraConfig):
    global _camera
    _camera = camera

    return {"ok": True}


@app.post("/localization")
async def localize_image(axis_convention: AxisConvention, image: UploadFile = File(...)) -> list[Localization]:
    if environ.get("CODEGEN"):
        raise
    from .map_manager import localize

    if _camera is None:
        raise HTTPException(status_code=400, detail="Camera intrinsics not set")

    return localize(camera=_camera, axis_convention=axis_convention, image=await image.read())
