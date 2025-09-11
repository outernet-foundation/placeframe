from typing import List, Optional, cast
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import ConfigDict

from ..db.piccolo_shims import create_pydantic_model
from ..db.tables.groups import Group


class GroupModel(create_pydantic_model(Group)):
    model_config = ConfigDict(from_attributes=True)


# ----------- Router -----------

router = APIRouter(prefix="/groups", tags=["groups"])


# CREATE
@router.post("")
async def create_group(group: GroupModel):
    exists = await Group.exists().where(Group.id == group.id)  # type: ignore

    if exists:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Group with id {id} already exists",
        )

    row = await Group.objects().create(**group.model_dump())

    return GroupModel.model_validate(row)


# READ ALL
@router.get("")
async def get_groups(
    ids: Optional[List[UUID]] = Query(
        None, description="Optional list of Ids to filter by"
    ),
) -> List[GroupModel]:
    if ids:
        rows = await Group.objects().where(Group.id.is_in(ids))
    else:
        rows = await Group.objects()
    return [GroupModel.model_validate(r) for r in rows]


# UPDATE
@router.put("/{id}")
async def update_group(id: UUID, group: GroupModel):
    exists = await Group.exists().where(Group.id == id)
    if not exists:
        raise HTTPException(status_code=404, detail="Group not found")

    await Group.update(group.model_dump()).where(Group.id == id)  # type: ignore
    return await Group.objects().where(Group.id == id).first()


@router.put("/upsert")
async def upsert_groups(groups: List[GroupModel]):
    """
    Bulk upsert groups.
    - If a group has an id and exists → update it.
    - If a group has an id but doesn't exist → insert it.
    - If a group has no id → generate a new UUID and insert it.
    """

    for group in groups:
        data = group.model_dump()

        # Generate an id if missing
        group_id = data.get("id")
        if not group_id:
            group_id = UUID()
            data["id"] = group_id

        # Update or insert
        exists = await Group.exists().where(Group.id == group_id)  # type: ignore

        if exists:
            await Group.update(data).where(Group.id == group_id)  # type: ignore
        else:
            new_group = Group(**data)
            await new_group.save()  # type: ignore

        # Fetch the final row
        row = cast(dict, await Group.objects().where(Group.id == group_id).first())  # type: ignore
        if not row:
            raise HTTPException(
                status_code=500,
                detail=f"Upsert failed unexpectedly for group id {group_id}",
            )

    return groups


# DELETE
@router.delete("/", response_model=List[UUID])
async def delete_groups(
    ids: List[UUID],
):
    if len(ids) == 0:
        return ids

    # First fetch which ids actually exist
    existing = await Group.select(Group.id).where(Group.id.is_in(ids))  # type: ignore
    existing_ids = [str(row["id"]) for row in existing]

    if not existing_ids:
        raise HTTPException(status_code=404, detail="No matching groups found")

    # Delete only those existing ids
    await Group.delete().where(Group.id.is_in(existing_ids))

    return existing_ids
