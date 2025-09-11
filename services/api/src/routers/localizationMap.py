from typing import List, Optional, cast
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import ConfigDict

from ..db.piccolo_shims import create_pydantic_model
from ..db.tables.localizationMaps import LocalizationMap


class LocalizationMapModel(create_pydantic_model(LocalizationMap)):
    model_config = ConfigDict(from_attributes=True)


# ----------- Router -----------

router = APIRouter(prefix="/localizationMaps", tags=["localizationMaps"])


# CREATE
@router.post("")
async def create_localizationMap(localizationMap: LocalizationMapModel):
    exists = await LocalizationMap.exists().where(
        LocalizationMap.id == localizationMap.id  # type: ignore
    )

    if exists:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"LocalizationMap with id {id} already exists",
        )

    row = await LocalizationMap.objects().create(**localizationMap.model_dump())

    return LocalizationMapModel.model_validate(row)


# READ ALL
@router.get("")
async def get_localizationMaps(
    ids: Optional[List[UUID]] = Query(
        None, description="Optional list of Ids to filter by"
    ),
) -> List[LocalizationMapModel]:
    if ids:
        rows = await LocalizationMap.objects().where(LocalizationMap.id.is_in(ids))
    else:
        rows = await LocalizationMap.objects()
    return [LocalizationMapModel.model_validate(r) for r in rows]


# UPDATE
@router.put("/{id}")
async def update_localizationMap(id: UUID, localizationMap: LocalizationMapModel):
    exists = await LocalizationMap.exists().where(LocalizationMap.id == id)
    if not exists:
        raise HTTPException(status_code=404, detail="LocalizationMap not found")

    await LocalizationMap.update(localizationMap.model_dump()).where(  # type: ignore
        LocalizationMap.id == id
    )
    return await LocalizationMap.objects().where(LocalizationMap.id == id).first()


@router.put("/upsert")
async def upsert_localizationMaps(localizationMaps: List[LocalizationMapModel]):
    """
    Bulk upsert localizationMaps.
    - If a localizationMap has an id and exists → update it.
    - If a localizationMap has an id but doesn't exist → insert it.
    - If a localizationMap has no id → generate a new UUID and insert it.
    """

    for localizationMap in localizationMaps:
        data = localizationMap.model_dump()

        # Generate an id if missing
        localizationMap_id = data.get("id")
        if not localizationMap_id:
            localizationMap_id = UUID()
            data["id"] = localizationMap_id

        # Update or insert
        exists = await LocalizationMap.exists().where(
            LocalizationMap.id == localizationMap_id
        )  # type: ignore

        if exists:
            await LocalizationMap.update(data).where(  # type: ignore
                LocalizationMap.id == localizationMap_id
            )
        else:
            new_localizationMap = LocalizationMap(**data)
            await new_localizationMap.save()  # type: ignore

        # Fetch the final row
        row = cast(  # type: ignore
            dict,  # type: ignore
            await LocalizationMap.objects()
            .where(LocalizationMap.id == localizationMap_id)
            .first(),
        )
        if not row:
            raise HTTPException(
                status_code=500,
                detail=f"Upsert failed unexpectedly for localizationMap id {localizationMap_id}",
            )

    return localizationMaps


# DELETE
@router.delete("/", response_model=List[UUID])
async def delete_localizationMaps(ids: List[UUID]):
    if len(ids) == 0:
        return ids

    # First fetch which ids actually exist
    existing = await LocalizationMap.select(LocalizationMap.id).where(  # type: ignore
        LocalizationMap.id.is_in(ids)
    )
    existing_ids = [str(row["id"]) for row in existing]

    if not existing_ids:
        raise HTTPException(
            status_code=404, detail="No matching Localization Maps found"
        )

    # Delete only those existing ids
    await LocalizationMap.delete().where(LocalizationMap.id.is_in(existing_ids))

    return existing_ids
