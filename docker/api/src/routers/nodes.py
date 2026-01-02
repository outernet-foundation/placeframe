from typing import Annotated
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
from litestar import Router, delete, get, patch, post
from litestar.di import Provide
from litestar.exceptions import HTTPException
from litestar.params import Parameter
from litestar.status_codes import HTTP_404_NOT_FOUND
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session


@post("")
async def create_node(session: AsyncSession, node: NodeCreate) -> NodeRead:
    row = node_from_dto(node)

    session.add(row)
    await session.flush()
    await session.refresh(row)
    return node_to_dto(row)


@delete("")
async def delete_nodes(
    session: AsyncSession, ids: Annotated[list[UUID], Parameter(description="List of Ids to delete")]
) -> None:
    for id in ids:
        row = await session.get(Node, id)
        if row:
            await session.delete(row)

    await session.flush()


@get("")
async def get_nodes(
    session: AsyncSession,
    ids: Annotated[list[UUID] | None, Parameter(description="Optional list of Ids to filter by")] = None,
) -> list[NodeRead]:
    query = select(Node)
    if ids:
        query = query.where(Node.id.in_(ids))

    result = await session.execute(query)

    results = [node_to_dto(row) for row in result.scalars().all()]
    return results


@patch("")
async def update_nodes(
    session: AsyncSession, nodes: list[NodeBatchUpdate], allow_missing: bool = False
) -> list[NodeRead]:
    rows: list[Node] = []
    for node in nodes:
        row = await session.get(Node, node.id)
        if not row:
            if not allow_missing:
                raise HTTPException(HTTP_404_NOT_FOUND, f"Node with id {node.id} not found")
            continue

        node_apply_batch_update_dto(row, node)
        rows.append(row)

    await session.flush()
    for row in rows:
        await session.refresh(row)
    return [node_to_dto(r) for r in rows]


router = Router(
    "/nodes",
    tags=["Nodes"],
    dependencies={"session": Provide(get_session)},
    route_handlers=[create_node, delete_nodes, get_nodes, update_nodes],
)
