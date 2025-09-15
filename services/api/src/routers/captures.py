from typing import List, Optional
from uuid import UUID

from common.schemas import tar_schema
from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from pydantic import ConfigDict

from ..db.piccolo_shims import create_pydantic_model
from ..db.tables.captures import Capture
from ..storage import Storage, get_storage

BUCKET = "dev-captures"

router = APIRouter(prefix="/captures")


class CaptureModel(create_pydantic_model(Capture)):
    model_config = ConfigDict(from_attributes=True)


@router.get("")
async def get_captures(
    ids: Optional[List[UUID]] = Query(None, description="Optional list of Ids to filter by"),
) -> List[CaptureModel]:
    if ids:
        rows = await Capture.objects().where(Capture.id.is_in(ids))
    else:
        rows = await Capture.objects()
    return [CaptureModel.model_validate(r) for r in rows]


@router.get("/{id}")
async def get_capture(id: UUID) -> CaptureModel:
    row = await Capture.objects().get(Capture.id == id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Capture with id {id} not found")

    return CaptureModel.model_validate(row)


@router.post("")
async def create_capture(id: UUID = Body(..., embed=True), filename: str = Body(..., embed=True)) -> CaptureModel:
    exists = await Capture.objects().get(Capture.id == id)

    if exists:
        raise HTTPException(409, f"Capture with id {id} already exists")

    row = await Capture.objects().create(id=id, filename=filename)

    return CaptureModel.model_validate(row)


@router.put(
    "/{id}/tar",
    status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    openapi_extra={"requestBody": {"required": True, "content": tar_schema}},
)
async def upload_capture_tar(id: UUID) -> RedirectResponse:
    if not await Capture.exists().where(Capture.id == id):
        raise HTTPException(404, f"Capture {id} not found")

    try:
        url = get_storage().presign_put(BUCKET, f"{id}.tar", "application/x-tar")
    except Exception as exc:
        raise HTTPException(502, f"Presign failed: {exc}") from exc

    return RedirectResponse(url)


@router.get("/{id}/tar", status_code=status.HTTP_307_TEMPORARY_REDIRECT, responses={200: {"content": tar_schema}})
async def download_capture_tar(id: UUID, storage: Storage = Depends(get_storage)) -> RedirectResponse:
    if not await Capture.exists().where(Capture.id == id):
        raise HTTPException(404, f"Capture {id} not found")

    try:
        url = storage.presign_get(BUCKET, f"{id}.tar", "application/x-tar")
    except Exception as exc:
        raise HTTPException(502, f"Presign failed: {exc}") from exc

    return RedirectResponse(url)
