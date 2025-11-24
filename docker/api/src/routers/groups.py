from typing import Optional
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
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session

router = APIRouter(prefix="/groups", tags=["groups"])


@router.post("")
async def create_group(group: GroupCreate, session: AsyncSession = Depends(get_session)) -> GroupRead:
    row = group_from_dto(group)

    session.add(row)
    await session.flush()
    await session.refresh(row)
    return group_to_dto(row)


@router.delete("")
async def delete_groups(
    ids: list[UUID] = Query(..., description="List of Ids to delete"), session: AsyncSession = Depends(get_session)
) -> None:
    for id in ids:
        row = await session.get(Group, id)
        if row:
            await session.delete(row)

    await session.flush()


@router.get("")
async def get_groups(
    ids: Optional[list[UUID]] = Query(None, description="Optional list of Ids to filter by"),
    session: AsyncSession = Depends(get_session),
) -> list[GroupRead]:
    query = select(Group)
    if ids:
        query = query.where(Group.id.in_(ids))

    result = await session.execute(query)

    results = [group_to_dto(row) for row in result.scalars().all()]
    return results


@router.patch("")
async def update_groups(
    groups: list[GroupBatchUpdate], allow_missing: bool = False, session: AsyncSession = Depends(get_session)
) -> list[GroupRead]:
    rows: list[Group] = []
    for group in groups:
        row = await session.get(Group, group.id)
        if not row:
            if not allow_missing:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Group with id {group.id} not found")
            continue

        group_apply_batch_update_dto(row, group)
        rows.append(row)

    await session.flush()
    for row in rows:
        await session.refresh(row)
    return [group_to_dto(r) for r in rows]
