from typing import List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse
from pydantic import ConfigDict

from ..db.piccolo_shims import create_pydantic_model
from ..db.tables.captures import Capture
from ..storage import Storage, get_storage

BUCKET = "dev-captures"

router = APIRouter(prefix="/captures", tags=["captures"])

binary_schema = {
    "application/octet-stream": {"schema": {"type": "string", "format": "binary"}}
}


class CaptureModel(create_pydantic_model(Capture)):
    model_config = ConfigDict(from_attributes=True)


@router.get("")
async def get_captures(
    filenames: Optional[List[str]] = Query(
        None, description="Optional list of filenames to filter by"
    ),
) -> List[CaptureModel]:
    if filenames:
        rows = await Capture.objects().where(Capture.filename.is_in(filenames))
    else:
        rows = await Capture.objects()
    return [CaptureModel.model_validate(r) for r in rows]


@router.get("/{id}")
async def get_capture(
    id: str,
) -> CaptureModel:
    row = await Capture.objects().get(Capture.id == id)
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Capture with id {id} not found",
        )

    return CaptureModel.model_validate(row)


@router.post("")
async def create_captue(
    filename: str = Body(..., embed=True),
) -> CaptureModel:
    exists = await Capture.objects().get(Capture.filename == filename)

    if exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Capture with filename '{filename}' already exists",
        )

    row = await Capture.objects().create(filename=filename)

    return CaptureModel.model_validate(row)


@router.put(
    "/{id}/file",
    status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    openapi_extra={"requestBody": {"required": True, "content": binary_schema}},
)
async def upload_capture_file(
    request: Request,
    id: str,
    storage: Storage = Depends(get_storage),
) -> RedirectResponse:
    if not await Capture.exists().where(Capture.id == id):
        raise HTTPException(404, f"Capture {id} not found")

    try:
        url = storage.presign_put(BUCKET, id)
        print(url)
    except Exception as exc:
        raise HTTPException(502, f"Presign failed: {exc}") from exc

    return RedirectResponse(url)


@router.get(
    "/{id}/file",
    status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    responses={200: {"content": binary_schema}},
)
async def download_capture_file(
    id: str,
    storage: Storage = Depends(get_storage),
) -> RedirectResponse:
    if not await Capture.exists().where(Capture.id == id):
        raise HTTPException(404, f"Capture {id} not found")

    try:
        url = storage.presign_get(BUCKET, id)
    except Exception as exc:
        raise HTTPException(502, f"Presign failed: {exc}") from exc

    return RedirectResponse(url)
