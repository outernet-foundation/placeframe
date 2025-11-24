from typing import Optional
from uuid import UUID

from datamodels.public_dtos import (
    LayerBatchUpdate,
    LayerCreate,
    LayerRead,
    layer_apply_batch_update_dto,
    layer_from_dto,
    layer_to_dto,
)
from datamodels.public_tables import Layer
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session

router = APIRouter(prefix="/layers", tags=["layers"])


@router.post("")
async def create_layer(layer: LayerCreate, session: AsyncSession = Depends(get_session)) -> LayerRead:
    row = layer_from_dto(layer)

    session.add(row)
    await session.flush()
    await session.refresh(row)
    return layer_to_dto(row)


@router.delete("")
async def delete_layers(
    ids: list[UUID] = Query(..., description="List of Ids to delete"), session: AsyncSession = Depends(get_session)
) -> None:
    for id in ids:
        row = await session.get(Layer, id)
        if row:
            await session.delete(row)

    await session.flush()


@router.get("")
async def get_layers(
    ids: Optional[list[UUID]] = Query(None, description="Optional list of Ids to filter by"),
    session: AsyncSession = Depends(get_session),
) -> list[LayerRead]:
    query = select(Layer)
    if ids:
        query = query.where(Layer.id.in_(ids))

    result = await session.execute(query)

    results = [layer_to_dto(row) for row in result.scalars().all()]
    return results


@router.patch("")
async def update_layers(
    layers: list[LayerBatchUpdate], allow_missing: bool = False, session: AsyncSession = Depends(get_session)
) -> list[LayerRead]:
    rows: list[Layer] = []
    for layer in layers:
        row = await session.get(Layer, layer.id)
        if not row:
            if not allow_missing:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Layer with id {layer.id} not found")
            continue

        layer_apply_batch_update_dto(row, layer)
        rows.append(row)

    await session.flush()
    for row in rows:
        await session.refresh(row)
    return [layer_to_dto(r) for r in rows]
