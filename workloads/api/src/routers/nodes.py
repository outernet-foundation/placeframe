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
from datamodels.public_tables import Group, Layer, Node
from litestar import Router, delete, get, patch, post
from litestar.di import Provide
from litestar.exceptions import ClientException, NotFoundException
from litestar.params import Parameter
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session


@post("")
async def create_node(session: AsyncSession, data: NodeCreate) -> NodeRead:
    if data.parent_id is not None:
        result = await session.execute(select(1).where(Group.id == data.parent_id))
        if not result.scalar():
            raise ClientException(f"Parent group with id {data.parent_id} does not exist.")

    if data.layer_id is not None:
        result = await session.execute(select(1).where(Layer.id == data.layer_id))
        if not result.scalar():
            raise ClientException(f"Layer with id {data.layer_id} does not exist.")

    row = node_from_dto(data)
    session.add(row)
    await session.flush()
    await session.refresh(row)
    return node_to_dto(row)


@post("/batch")
async def create_nodes_batch(session: AsyncSession, data: list[NodeCreate]) -> list[NodeRead]:
    # 1. Collect unique parent IDs and layer IDs
    parent_ids = {n.parent_id for n in data if n.parent_id is not None}
    layer_ids = {n.layer_id for n in data if n.layer_id is not None}

    # 2. Verify existence
    if layer_ids:
        result = await session.execute(select(Layer.id).where(Layer.id.in_(layer_ids)))
        missing = layer_ids - set(result.scalars().all())
        if missing:
            raise ClientException(f"The following layer IDs do not exist: {missing}")

    if parent_ids:
        stmt = select(Group.id).where(Group.id.in_(parent_ids))
        result = await session.execute(stmt)
        found_ids = set(result.scalars().all())

        missing = parent_ids - found_ids
        if missing:
            raise ClientException(f"The following parent group IDs do not exist: {missing}")

    # 3. Create
    rows: list[Node] = []
    for node_data in data:
        row = node_from_dto(node_data)
        session.add(row)
        rows.append(row)

    await session.flush()

    for row in rows:
        await session.refresh(row)

    return [node_to_dto(r) for r in rows]


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
    position_x: float | None = None,
    position_y: float | None = None,
    position_z: float | None = None,
    radius: float | None = None,
) -> list[NodeRead]:
    spatial_params = [position_x, position_y, position_z, radius]
    has_spatial = any(p is not None for p in spatial_params)
    if has_spatial and not all(p is not None for p in spatial_params):
        raise ClientException(
            "Cannot provide partial spatial parameters; position_x, position_y, position_z, and radius must all be provided together"
        )

    if has_spatial and ids:
        raise ClientException("Cannot combine spatial filter with ids")

    query = select(Node)
    if ids:
        query = query.where(Node.id.in_(ids))

    if has_spatial:
        query = query.where(
            func.ST_3DDWithin(
                func.ST_MakePoint(Node.position_x, Node.position_y, Node.position_z),
                func.ST_MakePoint(position_x, position_y, position_z),
                radius,
            )
        )

    result = await session.execute(query)

    results = [node_to_dto(row) for row in result.scalars().all()]
    return results


@patch("")
async def update_nodes(
    session: AsyncSession, data: list[NodeBatchUpdate], allow_missing: bool = False
) -> list[NodeRead]:
    layer_ids = {n.layer_id for n in data if n.layer_id is not None}
    if layer_ids:
        result = await session.execute(select(Layer.id).where(Layer.id.in_(layer_ids)))
        missing = layer_ids - set(result.scalars().all())
        if missing:
            raise ClientException(f"The following layer IDs do not exist: {missing}")

    rows: list[Node] = []
    for node in data:
        row = await session.get(Node, node.id)
        if not row:
            if not allow_missing:
                raise NotFoundException(f"Node with id {node.id} not found")
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
    route_handlers=[create_node, create_nodes_batch, delete_nodes, get_nodes, update_nodes],
)
