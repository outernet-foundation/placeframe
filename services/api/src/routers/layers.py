from typing import List, Optional, cast
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import ConfigDict

from ..db.piccolo_shims import create_pydantic_model
from ..db.tables.layers import Layer


class LayerModel(create_pydantic_model(Layer)):
    model_config = ConfigDict(from_attributes=True)


# ----------- Router -----------

router = APIRouter(prefix="/layers", tags=["layers"])


# CREATE
@router.post("")
async def create_layer(layer: LayerModel):
    exists = await Layer.exists().where(Layer.id == layer.id)  # type: ignore

    if exists:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Layer with id {id} already exists",
        )

    row = await Layer.objects().create(**layer.model_dump())

    return LayerModel.model_validate(row)


# READ ALL
@router.get("")
async def get_layers(
    ids: Optional[List[UUID]] = Query(
        None, description="Optional list of Ids to filter by"
    ),
) -> List[LayerModel]:
    if ids:
        rows = await Layer.objects().where(Layer.id.is_in(ids))
    else:
        rows = await Layer.objects()
    return [LayerModel.model_validate(r) for r in rows]


# UPDATE
@router.put("/{id}")
async def update_layer(id: UUID, layer: LayerModel):
    exists = await Layer.exists().where(Layer.id == id)
    if not exists:
        raise HTTPException(status_code=404, detail="Layer not found")

    await Layer.update(layer.model_dump()).where(Layer.id == id)  # type: ignore
    return await Layer.objects().where(Layer.id == id).first()


# UPSERT
@router.put("/upsert")
async def upsert_layers(layers: List[LayerModel]):
    """
    Bulk upsert layers.
    - If a layer has an id and exists → update it.
    - If a layer has an id but doesn't exist → insert it.
    - If a layer has no id → generate a new UUID and insert it.
    """
    if len(layers) == 0:
        return

    for layer in layers:
        data = layer.model_dump()

        # Generate an id if missing
        layer_id = data.get("id")
        if not layer_id:
            layer_id = UUID()
            data["id"] = layer_id

        # Update or insert
        exists = await Layer.exists().where(Layer.id == layer_id)  # type: ignore

        if exists:
            await Layer.update(data).where(Layer.id == layer_id)  # type: ignore
        else:
            new_layer = Layer(**data)
            await new_layer.save()  # type: ignore

        # Fetch the final row
        row = cast(dict, await Layer.objects().where(Layer.id == layer_id).first())  # type: ignore
        if not row:
            raise HTTPException(
                status_code=500,
                detail=f"Upsert failed unexpectedly for layer id {layer_id}",
            )

    return layers


# DELETE
@router.delete("/", response_model=List[UUID])
async def delete_layers(
    ids: List[UUID],
):
    if len(ids) == 0:
        return ids

    # First fetch which ids actually exist
    existing = await Layer.select(Layer.id).where(Layer.id.is_in(ids))  # type: ignore
    existing_ids = [str(row["id"]) for row in existing]

    if not existing_ids:
        raise HTTPException(status_code=404, detail="No matching layers found")

    # Delete only those existing ids
    await Layer.delete().where(Layer.id.is_in(existing_ids))

    return existing_ids
