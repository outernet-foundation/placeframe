from typing import Annotated
from uuid import UUID

from datamodels.public_dtos import (
    LocalizationMapBatchUpdate,
    LocalizationMapCreate,
    LocalizationMapRead,
    LocalizationMapUpdate,
    localization_map_apply_batch_update_dto,
    localization_map_apply_dto,
    localization_map_from_dto,
    localization_map_to_dto,
)
from datamodels.public_tables import LocalizationMap
from litestar import Router, delete, get, patch, post
from litestar.di import Provide
from litestar.exceptions import HTTPException, NotFoundException
from litestar.params import Parameter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..settings import get_settings
from .reconstructions import fetch_reconstruction_status

settings = get_settings()


@post("")
async def create_localization_map(session: AsyncSession, data: LocalizationMapCreate) -> LocalizationMapRead:
    reconstruction_status = await fetch_reconstruction_status(data.reconstruction_id, session)

    if reconstruction_status != "succeeded":
        raise HTTPException(
            status_code=400, detail=f"Reconstruction with id {data.reconstruction_id} is not in 'succeeded' state"
        )

    row = localization_map_from_dto(data)

    session.add(row)

    await session.flush()
    await session.refresh(row)
    return localization_map_to_dto(row)


@delete("/{id:uuid}")
async def delete_localization_map(session: AsyncSession, id: UUID) -> None:
    row = await session.get(LocalizationMap, id)

    if not row:
        raise NotFoundException(f"LocalizationMap with id {id} not found")

    await session.delete(row)

    await session.flush()
    return None


@delete("")
async def delete_localization_maps(
    session: AsyncSession, ids: Annotated[list[UUID], Parameter(description="List of Ids to delete")]
) -> None:
    for id in ids:
        row = await session.get(LocalizationMap, id)

        if not row:
            raise NotFoundException(f"LocalizationMap with id {id} not found")

        await session.delete(row)

    await session.flush()
    return None


async def fetch_localization_maps(
    session: AsyncSession, ids: list[UUID] | None = None, reconstruction_ids: list[UUID] | None = None
) -> list[LocalizationMapRead]:
    if ids and reconstruction_ids:
        raise HTTPException(status_code=400, detail="Cannot filter by both ids and reconstruction_ids")

    query = select(LocalizationMap)

    if ids:
        query = query.where(LocalizationMap.id.in_(ids))

    if reconstruction_ids:
        query = query.where(LocalizationMap.reconstruction_id.in_(reconstruction_ids))

    result = await session.execute(query)

    return [localization_map_to_dto(row) for row in result.scalars().all()]


@get("")
async def get_localization_maps(
    session: AsyncSession,
    ids: Annotated[list[UUID] | None, Parameter(description="Optional list of Ids to filter by")] = None,
    reconstruction_ids: Annotated[
        list[UUID] | None, Parameter(description="Optional list of Reconstruction Ids to filter by")
    ] = None,
) -> list[LocalizationMapRead]:
    return await fetch_localization_maps(session, ids, reconstruction_ids)


@get("/{id:uuid}")
async def get_localization_map(session: AsyncSession, id: UUID) -> LocalizationMapRead:
    row = await session.get(LocalizationMap, id)

    if not row:
        raise HTTPException(status_code=404, detail=f"LocalizationMap with id {id} not found")

    return localization_map_to_dto(row)


@patch("/{id:uuid}")
async def update_localization_map(session: AsyncSession, id: UUID, data: LocalizationMapUpdate) -> LocalizationMapRead:
    row = await session.get(LocalizationMap, id)

    if not row:
        raise NotFoundException(f"LocalizationMap with id {id} not found")

    localization_map_apply_dto(row, data)

    await session.flush()
    await session.refresh(row)
    return localization_map_to_dto(row)


@patch("")
async def update_localization_maps(
    session: AsyncSession, data: list[LocalizationMapBatchUpdate], allow_missing: bool = False
) -> list[LocalizationMapRead]:
    rows: list[LocalizationMap] = []
    for localization_map in data:
        row = await session.get(LocalizationMap, localization_map.id)
        if not row:
            if not allow_missing:
                raise NotFoundException(f"LocalizationMap with id {localization_map.id} not found")
            continue

        localization_map_apply_batch_update_dto(row, localization_map)
        rows.append(row)

    await session.flush()
    for row in rows:
        await session.refresh(row)
    return [localization_map_to_dto(r) for r in rows]


router = Router(
    "/localization-maps",
    tags=["Localization Maps"],
    dependencies={"session": Provide(get_session)},
    route_handlers=[
        create_localization_map,
        delete_localization_map,
        delete_localization_maps,
        get_localization_maps,
        get_localization_map,
        update_localization_map,
        update_localization_maps,
    ],
)
