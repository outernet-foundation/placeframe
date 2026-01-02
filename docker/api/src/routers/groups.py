from typing import Annotated
from uuid import UUID

from datamodels.public_dtos import (
    GroupBatchUpdate,
    GroupCreate,
    GroupRead,
    group_apply_batch_update_dto,
    group_from_dto,
    group_to_dto,
)
from datamodels.public_tables import Group
from litestar import Router, delete, get, patch, post
from litestar.di import Provide
from litestar.exceptions import HTTPException
from litestar.params import Parameter
from litestar.status_codes import HTTP_404_NOT_FOUND
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session


@post("")
async def create_group(session: AsyncSession, group: GroupCreate) -> GroupRead:
    row = group_from_dto(group)

    session.add(row)
    await session.flush()
    await session.refresh(row)
    return group_to_dto(row)


@delete("")
async def delete_groups(
    session: AsyncSession, ids: Annotated[list[UUID], Parameter(description="List of Ids to delete")]
) -> None:
    for id in ids:
        row = await session.get(Group, id)
        if row:
            await session.delete(row)

    await session.flush()


@get("")
async def get_groups(
    session: AsyncSession,
    ids: Annotated[list[UUID] | None, Parameter(description="Optional list of Ids to filter by")] = None,
) -> list[GroupRead]:
    query = select(Group)
    if ids:
        query = query.where(Group.id.in_(ids))

    result = await session.execute(query)

    results = [group_to_dto(row) for row in result.scalars().all()]
    return results


@patch("")
async def update_groups(
    session: AsyncSession, groups: list[GroupBatchUpdate], allow_missing: bool = False
) -> list[GroupRead]:
    rows: list[Group] = []
    for group in groups:
        row = await session.get(Group, group.id)
        if not row:
            if not allow_missing:
                raise HTTPException(HTTP_404_NOT_FOUND, f"Group with id {group.id} not found")
            continue

        group_apply_batch_update_dto(row, group)
        rows.append(row)

    await session.flush()
    for row in rows:
        await session.refresh(row)
    return [group_to_dto(r) for r in rows]


router = Router(
    "/groups",
    tags=["Groups"],
    dependencies={"session": Provide(get_session)},
    route_handlers=[create_group, delete_groups, get_groups, update_groups],
)
