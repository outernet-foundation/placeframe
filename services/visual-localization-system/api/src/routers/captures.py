from typing import Optional
from uuid import UUID

from common.schemas import PlainTextResponse, tar_schema
from core.rig import RigConfig
from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from models.public_dtos import (
    CaptureSessionBatchUpdate,
    CaptureSessionCreate,
    CaptureSessionRead,
    CaptureSessionUpdate,
    capture_session_apply_batch_update_dto,
    capture_session_apply_dto,
    capture_session_from_dto,
    capture_session_from_dto_overwrite,
    capture_session_to_dto,
)
from models.public_tables import CaptureSession, Reconstruction
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..storage import get_storage

BUCKET = "dev-captures"

router = APIRouter(prefix="/capture_sessions", tags=["capture_sessions"])


@router.post("")
async def create_capture_session(
    capture: CaptureSessionCreate, session: AsyncSession = Depends(get_session)
) -> CaptureSessionRead:
    row = await _create_capture(capture, False, session)

    session.add(row)

    await session.flush()
    await session.refresh(row)
    return capture_session_to_dto(row)


@router.post("/bulk")
async def create_capture_sessions(
    captures: list[CaptureSessionCreate] = Body(...),
    overwrite: bool = False,
    session: AsyncSession = Depends(get_session),
) -> list[CaptureSessionRead]:
    rows: list[CaptureSession] = []
    for capture in captures:
        row = await _create_capture(capture, overwrite, session)
        rows.append(row)

    session.add_all(rows)

    await session.flush()
    for row in rows:
        await session.refresh(row)
    return [capture_session_to_dto(r) for r in rows]


@router.get("")
async def get_capture_sessions(
    ids: Optional[list[UUID]] = Query(None, description="Optional list of Ids to filter by"),
    session: AsyncSession = Depends(get_session),
) -> list[CaptureSessionRead]:
    query = select(CaptureSession)

    if ids:
        query = query.where(CaptureSession.id.in_(ids))

    result = await session.execute(query)

    results = [capture_session_to_dto(row) for row in result.scalars().all()]
    return results


@router.get("/{id}")
async def get_capture_session(id: UUID, session: AsyncSession = Depends(get_session)) -> CaptureSessionRead:
    row = await session.get(CaptureSession, id)

    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Capture session with id {id} not found")

    return capture_session_to_dto(row)


@router.get("/{id}/reconstructions")
async def get_capture_session_reconstructions(id: UUID, session: AsyncSession = Depends(get_session)) -> list[UUID]:
    row = await session.get(CaptureSession, id)

    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Capture session with id {id} not found")
    result = await session.execute(select(Reconstruction.id).where(Reconstruction.capture_session_id == id))

    return [r[0] for r in result.all()]


@router.delete("/{id}")
async def delete_capture_session(id: UUID, session: AsyncSession = Depends(get_session)) -> None:
    row = await session.get(CaptureSession, id)

    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Capture session with id {id} not found")

    await session.delete(row)

    await session.flush()
    return None


@router.patch("/{id}")
async def update_capture_session(
    id: UUID, capture: CaptureSessionUpdate, session: AsyncSession = Depends(get_session)
) -> CaptureSessionRead:
    row = await session.get(CaptureSession, id)

    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Capture session with id {id} not found")

    capture_session_apply_dto(row, capture)

    await session.flush()
    await session.refresh(row)
    return capture_session_to_dto(row)


@router.patch("")
async def update_capture_sessions(
    captures: list[CaptureSessionBatchUpdate], allow_missing: bool = False, session: AsyncSession = Depends(get_session)
) -> list[CaptureSessionRead]:
    rows: list[CaptureSession] = []
    for capture in captures:
        row = await session.get(CaptureSession, capture.id)

        if not row:
            if not allow_missing:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail=f"Capture session with id {capture.id} not found"
                )
            continue

        capture_session_apply_batch_update_dto(row, capture)
        rows.append(row)

    await session.flush()
    for row in rows:
        await session.refresh(row)
    return [capture_session_to_dto(r) for r in rows]


@router.put("/{id}/tar", response_class=PlainTextResponse)
async def get_upload_capture_session_tar_presigned_url(
    id: UUID, session: AsyncSession = Depends(get_session)
) -> PlainTextResponse:
    row = await session.get(CaptureSession, id)

    if row is None:
        raise HTTPException(404, f"Capture session {id} not found")

    try:
        url = get_storage().presign_put(BUCKET, f"{id}.tar", "application/x-tar", expires=60 * 60)
    except Exception as exc:
        raise HTTPException(502, f"Presign failed: {exc}") from exc

    return PlainTextResponse(content=url)


@router.get("/{id}/tar", status_code=status.HTTP_307_TEMPORARY_REDIRECT, responses={200: {"content": tar_schema}})
async def download_capture_session_tar(id: UUID, session: AsyncSession = Depends(get_session)) -> RedirectResponse:
    row = await session.get(CaptureSession, id)

    if row is None:
        raise HTTPException(404, f"Capture session {id} not found")

    try:
        url = get_storage().presign_get(BUCKET, f"{id}.tar", "application/x-tar")
    except Exception as exc:
        raise HTTPException(502, f"Presign failed: {exc}") from exc

    return RedirectResponse(url)


# dummy method, just to get RigConfig into the OpenAPI schema
@router.get("/{id}/rig_config")
async def get_capture_session_rig_config(id: UUID, session: AsyncSession = Depends(get_session)) -> RigConfig:
    rig_config = RigConfig(rigs=[])

    return rig_config


async def _create_capture(capture: CaptureSessionCreate, overwrite: bool, session: AsyncSession) -> CaptureSession:
    if capture.id is not None:
        result = await session.execute(select(CaptureSession).where(CaptureSession.id == capture.id))
        existing_row = result.scalar_one_or_none()

        if existing_row is not None:
            if not overwrite:
                raise HTTPException(409, f"Capture with id {capture.id} already exists")

            capture_session_from_dto_overwrite(existing_row, capture)
            return existing_row

    return capture_session_from_dto(capture)
