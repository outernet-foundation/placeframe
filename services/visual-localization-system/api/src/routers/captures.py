from typing import List, Optional
from uuid import UUID

from common.schemas import tar_schema
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from models.public_dtos import (
    CaptureBatchUpdate,
    CaptureCreate,
    CaptureRead,
    CaptureUpdate,
    capture_apply_batch_update_dto,
    capture_apply_dto,
    capture_from_dto,
    capture_from_dto_overwrite,
    capture_to_dto,
)
from models.public_tables import Capture
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..storage import get_storage

BUCKET = "dev-captures"

router = APIRouter(prefix="/captures")


@router.get("")
async def get_captures(
    ids: Optional[List[UUID]] = Query(None, description="Optional list of Ids to filter by"),
    session: AsyncSession = Depends(get_session),
) -> List[CaptureRead]:
    query = select(Capture)

    if ids:
        query = query.where(Capture.id.in_(ids))

    result = await session.execute(query)

    results = [capture_to_dto(row) for row in result.scalars().all()]
    return results


@router.get("/{id:uuid}")
async def get_capture(id: UUID, session: AsyncSession = Depends(get_session)) -> CaptureRead:
    row = await session.get(Capture, id)

    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Capture with id {id} not found")

    return capture_to_dto(row)


@router.post("")
async def create_capture(capture: CaptureCreate, session: AsyncSession = Depends(get_session)) -> CaptureRead:
    row = await _create_capture(capture, False, session)

    session.add(row)

    await session.flush()
    await session.refresh(row)
    return capture_to_dto(row)


@router.post("/bulk")
async def create_captures(
    captures: List[CaptureCreate], overwrite: bool = False, session: AsyncSession = Depends(get_session)
) -> List[CaptureRead]:
    rows: List[Capture] = []
    for capture in captures:
        row = await _create_capture(capture, overwrite, session)
        rows.append(row)

    session.add_all(rows)

    await session.flush()
    for row in rows:
        await session.refresh(row)
    return [capture_to_dto(r) for r in rows]


@router.patch("/{id:uuid}")
async def update_capture(id: UUID, capture: CaptureUpdate, session: AsyncSession = Depends(get_session)) -> CaptureRead:
    row = await session.get(Capture, id)

    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Capture with id {id} not found")

    capture_apply_dto(row, capture)

    await session.flush()
    await session.refresh(row)
    return capture_to_dto(row)


@router.patch("")
async def update_captures(
    captures: list[CaptureBatchUpdate], allow_missing: bool = False, session: AsyncSession = Depends(get_session)
) -> List[CaptureRead]:
    rows: List[Capture] = []
    for capture in captures:
        row = await session.get(Capture, capture.id)

        if not row:
            if not allow_missing:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail=f"Capture with id {capture.id} not found"
                )
            continue

        capture_apply_batch_update_dto(row, capture)
        rows.append(row)

    await session.flush()
    for row in rows:
        await session.refresh(row)
    return [capture_to_dto(r) for r in rows]


@router.delete("/{id:uuid}")
async def delete_capture(id: UUID, session: AsyncSession = Depends(get_session)) -> None:
    row = await session.get(Capture, id)

    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Capture with id {id} not found")

    await session.delete(row)

    await session.flush()
    return None


@router.put(
    "/{id:uuid}/tar",
    status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    openapi_extra={"requestBody": {"required": True, "content": tar_schema}},
)
async def upload_capture_tar(id: UUID, session: AsyncSession = Depends(get_session)) -> RedirectResponse:
    row = await session.get(Capture, id)

    if row is None:
        raise HTTPException(404, f"Capture {id} not found")

    try:
        url = get_storage().presign_put(BUCKET, f"{id}.tar", "application/x-tar")
    except Exception as exc:
        raise HTTPException(502, f"Presign failed: {exc}") from exc

    return RedirectResponse(url)


@router.get("/{id:uuid}/tar", status_code=status.HTTP_307_TEMPORARY_REDIRECT, responses={200: {"content": tar_schema}})
async def download_capture_tar(id: UUID, session: AsyncSession = Depends(get_session)) -> RedirectResponse:
    row = await session.get(Capture, id)

    if row is None:
        raise HTTPException(404, f"Capture {id} not found")

    try:
        url = get_storage().presign_get(BUCKET, f"{id}.tar", "application/x-tar")
    except Exception as exc:
        raise HTTPException(502, f"Presign failed: {exc}") from exc

    return RedirectResponse(url)


async def _create_capture(capture: CaptureCreate, overwrite: bool, session: AsyncSession) -> Capture:
    if capture.id is not None:
        result = await session.execute(select(Capture).where(Capture.id == capture.id))
        existing_row = result.scalar_one_or_none()

        if existing_row is not None:
            if not overwrite:
                raise HTTPException(409, f"Capture with id {capture.id} already exists")

            capture_from_dto_overwrite(existing_row, capture)
            return existing_row

    return capture_from_dto(capture)
