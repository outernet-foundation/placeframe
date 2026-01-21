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
from datamodels.public_tables import Group, Node
from litestar import Router, delete, get, patch, post
from litestar.di import Provide
from litestar.exceptions import HTTPException
from litestar.params import Parameter
from litestar.status_codes import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND, HTTP_409_CONFLICT
from sqlalchemy import delete as sql_delete
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session


async def _delete_group_recursive(session: AsyncSession, group: Group) -> None:
    # Delete child nodes
    await session.execute(sql_delete(Node).where(Node.parent_id == group.id))

    # Recursively delete child groups
    result = await session.execute(select(Group).where(Group.parent_id == group.id))
    for child in result.scalars().all():
        await _delete_group_recursive(session, child)

    # Delete the group itself
    await session.delete(group)


@post("")
async def create_group(session: AsyncSession, data: GroupCreate) -> GroupRead:
    if data.parent_id is not None:
        result = await session.execute(select(1).where(Group.id == data.parent_id))
        if not result.scalar():
            raise HTTPException(HTTP_400_BAD_REQUEST, f"Parent group with id {data.parent_id} does not exist.")

    row = group_from_dto(data)
    session.add(row)
    await session.flush()
    await session.refresh(row)
    return group_to_dto(row)


@post("/batch")
async def create_groups_batch(session: AsyncSession, data: list[GroupCreate]) -> list[GroupRead]:
    # Collect all parent IDs referenced in this batch
    parent_ids = {g.parent_id for g in data if g.parent_id is not None}

    # Verify those parents exist
    if parent_ids:
        stmt = select(Group.id).where(Group.id.in_(parent_ids))
        result = await session.execute(stmt)
        found_ids = set(result.scalars().all())

        missing = parent_ids - found_ids
        if missing:
            raise HTTPException(HTTP_400_BAD_REQUEST, f"The following parent group IDs do not exist: {missing}")

    # Insert
    rows = [group_from_dto(group_data) for group_data in data]
    for row in rows:
        session.add(row)

    await session.flush()

    for row in rows:
        await session.refresh(row)

    return [group_to_dto(r) for r in rows]


@delete("")
async def delete_groups(
    session: AsyncSession,
    ids: Annotated[list[UUID], Parameter(description="List of Ids to delete")],
    cascade: Annotated[bool, Parameter(query="cascade", description="If true, recursively delete children.")] = False,
) -> None:
    for id in ids:
        row = await session.get(Group, id)
        if not row:
            continue

        if cascade:
            await _delete_group_recursive(session, row)
            continue

        child_group_exists = await session.execute(select(1).where(Group.parent_id == id))
        child_node_exists = await session.execute(select(1).where(Node.parent_id == id))

        if child_group_exists.scalar() or child_node_exists.scalar():
            raise HTTPException(HTTP_409_CONFLICT, f"Group {id} has children. Set cascade=true to delete them.")

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
    session: AsyncSession, data: list[GroupBatchUpdate], allow_missing: bool = False
) -> list[GroupRead]:
    rows: list[Group] = []
    for group in data:
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
    route_handlers=[create_group, create_groups_batch, delete_groups, get_groups, update_groups],
)
