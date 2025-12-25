from typing import Annotated
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
from litestar import Router, delete, get, patch, post
from litestar.di import Provide
from litestar.exceptions import NotFoundException
from litestar.params import Parameter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session


@post("")
async def create_layer(session: AsyncSession, layer: LayerCreate) -> LayerRead:
    row = layer_from_dto(layer)

    session.add(row)
    await session.flush()
    await session.refresh(row)
    return layer_to_dto(row)


@delete("")
async def delete_layers(
    session: AsyncSession, ids: Annotated[list[UUID], Parameter(description="List of Ids to delete")]
) -> None:
    for id in ids:
        row = await session.get(Layer, id)
        if row:
            await session.delete(row)

    await session.flush()


@get("")
async def get_layers(
    session: AsyncSession,
    ids: Annotated[list[UUID] | None, Parameter(description="Optional list of Ids to filter by")] = None,
) -> list[LayerRead]:
    query = select(Layer)
    if ids:
        query = query.where(Layer.id.in_(ids))

    result = await session.execute(query)

    results = [layer_to_dto(row) for row in result.scalars().all()]
    return results


@patch("")
async def update_layers(
    session: AsyncSession, layers: list[LayerBatchUpdate], allow_missing: bool = False
) -> list[LayerRead]:
    rows: list[Layer] = []
    for layer in layers:
        row = await session.get(Layer, layer.id)
        if not row:
            if not allow_missing:
                raise NotFoundException(f"Layer with id {layer.id} not found")
            continue

        layer_apply_batch_update_dto(row, layer)
        rows.append(row)

    await session.flush()
    for row in rows:
        await session.refresh(row)
    return [layer_to_dto(r) for r in rows]


router = Router(
    "/layers",
    tags=["Layers"],
    dependencies={"session": Provide(get_session)},
    route_handlers=[create_layer, delete_layers, get_layers, update_layers],
)
