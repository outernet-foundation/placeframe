from graphlib import CycleError, TopologicalSorter
from uuid import UUID

from datamodels.public_dtos import (
    GroupBatchCreate,
    GroupRead,
    NodeBatchCreate,
    NodeRead,
    group_from_batch_create_dto,
    group_to_dto,
    node_from_batch_create_dto,
    node_to_dto,
)
from datamodels.public_tables import Group
from litestar import Router, post
from litestar.di import Provide
from litestar.exceptions import HTTPException
from litestar.status_codes import HTTP_400_BAD_REQUEST
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session


class CreateGraphRequest(BaseModel):
    groups: list[GroupBatchCreate] = Field(default_factory=list)
    nodes: list[NodeBatchCreate] = Field(default_factory=list)


class CreateGraphResponse(BaseModel):
    groups: list[GroupRead]
    nodes: list[NodeRead]


@post("/")
async def create_graph(session: AsyncSession, data: CreateGraphRequest) -> CreateGraphResponse:
    groups = {group.id: group for group in data.groups}

    # Collect all external parent IDs (parent IDs referenced by objects in this batch that are not in the batch)
    external_parent_ids = (
        set(group.parent_id for group in data.groups if group.parent_id is not None)
        | set(node.parent_id for node in data.nodes if node.parent_id is not None)
    ) - set(groups.keys())

    # Verify that all external parent IDs exist in the database
    if external_parent_ids:
        stmt = select(Group.id).where(Group.id.in_(external_parent_ids))
        result = await session.execute(stmt)
        existing_ids = set(result.scalars().all())

        missing_ids = external_parent_ids - existing_ids
        if missing_ids:
            raise HTTPException(
                HTTP_400_BAD_REQUEST,
                f"Missing parent dependencies. The following Group IDs were referenced but do not exist in the batch or database: {missing_ids}",
            )

    # Topologically sort groups to ensure parents are created before children
    sorter: TopologicalSorter[UUID] = TopologicalSorter()
    for group in data.groups:
        if group.parent_id:
            sorter.add(group.id, group.parent_id)
        else:
            sorter.add(group.id)

    try:
        sorted_group_ids = list(sorter.static_order())
    except CycleError as e:
        raise HTTPException(HTTP_400_BAD_REQUEST, f"Circular dependency detected in Group hierarchy: {e.args}")

    # Create groups first, in topological order
    group_rows = [group_from_batch_create_dto(groups[group_id]) for group_id in sorted_group_ids if group_id in groups]
    for group in group_rows:
        session.add(group)

    # Create nodes
    node_rows = [node_from_batch_create_dto(node_dto) for node_dto in data.nodes]
    for row_n in node_rows:
        session.add(row_n)

    await session.flush()

    return CreateGraphResponse(
        groups=[group_to_dto(group) for group in group_rows], nodes=[node_to_dto(node) for node in node_rows]
    )


router = Router("/graph", tags=["graph"], dependencies={"session": Provide(get_session)}, route_handlers=[create_graph])
