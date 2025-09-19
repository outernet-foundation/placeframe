from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from models.public_dtos import ReconstructionCreate, ReconstructionRead, reconstruction_from_dto, reconstruction_to_dto
from models.public_tables import Reconstruction
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session

BUCKET = "dev-reconstructions"

router = APIRouter(prefix="/reconstructions")


@router.get("")
async def get_reconstructions(
    ids: Optional[List[UUID]] = Query(None, description="Optional list of Ids to filter by"),
    session: AsyncSession = Depends(get_session),
) -> List[ReconstructionRead]:
    query = select(Reconstruction)

    if ids:
        query = query.where(Reconstruction.id.in_(ids))

    result = await session.execute(query)

    return [reconstruction_to_dto(row) for row in result.scalars().all()]


@router.get("/{id:uuid}")
async def get_reconstruction(id: UUID, session: AsyncSession = Depends(get_session)) -> ReconstructionRead:
    row = await session.get(Reconstruction, id)

    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Reconstruction with id {id} not found")

    return reconstruction_to_dto(row)


@router.post("")
async def create_reconstruction(
    reconstruction: ReconstructionCreate, session: AsyncSession = Depends(get_session)
) -> ReconstructionRead:
    # If we were provided an ID, ensure it doesn't already exist
    if reconstruction.id is not None:
        result = await session.execute(select(Reconstruction).where(Reconstruction.id == reconstruction.id))
        existing_row = result.scalar_one_or_none()

        if existing_row is not None:
            raise HTTPException(409, f"Reconstruction with id {reconstruction.id} already exists")

    row = reconstruction_from_dto(reconstruction)

    session.add(row)

    await session.flush()
    await session.refresh(row)
    return reconstruction_to_dto(row)


@router.delete("/{id:uuid}")
async def delete_reconstruction(id: UUID, session: AsyncSession = Depends(get_session)) -> None:
    row = await session.get(Reconstruction, id)

    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Reconstruction with id {id} not found")

    await session.delete(row)

    await session.flush()
    return None
