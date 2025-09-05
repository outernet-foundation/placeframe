from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Body, HTTPException, Query, status
from pydantic import ConfigDict

from ..db.piccolo_shims import create_pydantic_model
from ..db.tables.nodes import Node

router = APIRouter(prefix="/nodes", tags=["nodes"])


class NodeModel(create_pydantic_model(Node)):
    model_config = ConfigDict(from_attributes=True)


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


@router.get("/{id}")
async def get_node(
    id: UUID,
) -> NodeModel:
    row = await Node.objects().get(Node.id == id)
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Node with id {id} not found",
        )

    return NodeModel.model_validate(row)


@router.post("")
async def create_node(
    id: UUID = Body(..., embed=True),
    filename: str = Body(..., embed=True),
) -> NodeModel:
    exists = await Node.objects().get(Node.id == id)

    if exists:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Node with id {id} already exists",
        )

    row = await Node.objects().create(id=id, filename=filename)

    return NodeModel.model_validate(row)
