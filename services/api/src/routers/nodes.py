from typing import List, Optional, cast
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import ConfigDict

from ..db.piccolo_shims import create_pydantic_model
from ..db.tables.nodes import Node


class NodeModel(create_pydantic_model(Node)):
    model_config = ConfigDict(from_attributes=True)


# ----------- Router -----------

router = APIRouter(prefix="/nodes", tags=["nodes"])


# CREATE
@router.post("")
async def create_node(node: NodeModel):
    exists = await Node.exists().where(Node.id == node.id)  # type: ignore

    if exists:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Node with id {id} already exists",
        )

    row = await Node.objects().create(**node.model_dump())

    return NodeModel.model_validate(row)


# READ ALL
@router.get("")
async def get_nodes(
    ids: Optional[List[UUID]] = Query(
        None, description="Optional list of Ids to filter by"
    ),
) -> List[NodeModel]:
    if ids:
        rows = await Node.objects().where(Node.id.is_in(ids))
    else:
        rows = await Node.objects()
    return [NodeModel.model_validate(r) for r in rows]


# UPDATE
@router.put("/{id}")
async def update_node(id: UUID, node: NodeModel):
    exists = await Node.exists().where(Node.id == id)
    if not exists:
        raise HTTPException(status_code=404, detail="Node not found")

    await Node.update(node.model_dump()).where(Node.id == id)  # type: ignore
    return await Node.objects().where(Node.id == id).first()


@router.put("/upsert")
async def upsert_nodes(nodes: List[NodeModel]):
    """
    Bulk upsert nodes.
    - If a node has an id and exists → update it.
    - If a node has an id but doesn't exist → insert it.
    - If a node has no id → generate a new UUID and insert it.
    """

    for node in nodes:
        data = node.model_dump()

        # Generate an id if missing
        node_id = data.get("id")
        if not node_id:
            node_id = uuid4()
            data["id"] = node_id

        # Update or insert
        exists = await Node.exists().where(Node.id == node_id)  # type: ignore

        if exists:
            await Node.update(data).where(Node.id == node_id)  # type: ignore
        else:
            new_node = Node(**data)
            await new_node.save()  # type: ignore

        # Fetch the final row
        row = cast(dict, await Node.objects().where(Node.id == node_id).first())  # type: ignore
        if not row:
            raise HTTPException(
                status_code=500,
                detail=f"Upsert failed unexpectedly for node id {node_id}",
            )

    return nodes


@router.delete("/", response_model=List[UUID])
async def delete_nodes(ids: List[UUID]):
    if len(ids) == 0:
        return ids

    # First fetch which ids actually exist
    existing = await Node.select(Node.id).where(Node.id.is_in(ids))  # type: ignore
    existing_ids = [str(row["id"]) for row in existing]

    if not existing_ids:
        raise HTTPException(status_code=404, detail="No matching nodes found")

    # Delete only those existing ids
    await Node.delete().where(Node.id.is_in(existing_ids))

    return existing_ids
