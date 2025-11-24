from typing import Optional
from uuid import UUID

from datamodels.public_dtos import (
    NodeBatchUpdate,
    NodeCreate,
    NodeRead,
    node_apply_batch_update_dto,
    node_from_dto,
    node_to_dto,
)
from datamodels.public_tables import Node
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session

router = APIRouter(prefix="/nodes", tags=["nodes"])


@router.post("")
async def create_node(node: NodeCreate, session: AsyncSession = Depends(get_session)) -> NodeRead:
    row = node_from_dto(node)

    session.add(row)
    await session.flush()
    await session.refresh(row)
    return node_to_dto(row)


@router.delete("")
async def delete_nodes(
    ids: list[UUID] = Query(..., description="List of Ids to delete"), session: AsyncSession = Depends(get_session)
) -> None:
    for id in ids:
        row = await session.get(Node, id)
        if row:
            await session.delete(row)

    await session.flush()


@router.get("")
async def get_nodes(
    ids: Optional[list[UUID]] = Query(None, description="Optional list of Ids to filter by"),
    session: AsyncSession = Depends(get_session),
) -> list[NodeRead]:
    query = select(Node)
    if ids:
        query = query.where(Node.id.in_(ids))

    result = await session.execute(query)

    results = [node_to_dto(row) for row in result.scalars().all()]
    return results


@router.patch("")
async def update_nodes(
    nodes: list[NodeBatchUpdate], allow_missing: bool = False, session: AsyncSession = Depends(get_session)
) -> list[NodeRead]:
    rows: list[Node] = []
    for node in nodes:
        row = await session.get(Node, node.id)
        if not row:
            if not allow_missing:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Node with id {node.id} not found")
            continue

        node_apply_batch_update_dto(row, node)
        rows.append(row)

    await session.flush()
    for row in rows:
        await session.refresh(row)
    return [node_to_dto(r) for r in rows]
