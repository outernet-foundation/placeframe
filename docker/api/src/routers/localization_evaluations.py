from __future__ import annotations

from typing import Annotated, Optional
from uuid import UUID

from datamodels.public_dtos import (
    LocalizationEvaluationCreate,
    LocalizationEvaluationRead,
    localization_evaluation_to_dto,
)
from datamodels.public_tables import LocalizationEvaluation, Reconstruction
from litestar import Router, get, post
from litestar.di import Provide
from litestar.exceptions import ClientException, NotFoundException
from litestar.params import Parameter
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session

UPSERT_CONFLICT_KEYS = [
    "reconstruction_id",
    "frame_timestamp",
    "retrieval_top_k",
    "ransac_threshold",
    "pipeline_version",
]


@post("")
async def upsert_localization_evaluation(
    session: AsyncSession,
    reconstruction_id: UUID,
    data: LocalizationEvaluationCreate,
) -> LocalizationEvaluationRead:
    if data.reconstruction_id != reconstruction_id:
        raise ClientException("reconstruction_id in path and body must match")

    if not await session.get(Reconstruction, reconstruction_id):
        raise NotFoundException(f"Reconstruction with id {reconstruction_id} not found")

    values = data.model_dump(exclude_unset=True, mode="json")
    update_columns = {k: v for k, v in values.items() if k not in (*UPSERT_CONFLICT_KEYS, "id")}

    stmt = pg_insert(LocalizationEvaluation).values(**values)
    stmt = stmt.on_conflict_do_update(index_elements=UPSERT_CONFLICT_KEYS, set_=update_columns).returning(
        LocalizationEvaluation
    )

    result = await session.execute(stmt)
    row = result.scalar_one()
    return localization_evaluation_to_dto(row)


@get("")
async def list_localization_evaluations(
    session: AsyncSession,
    reconstruction_id: UUID,
    pipeline_version: Annotated[Optional[str], Parameter(description="Optional pipeline_version to filter by")] = None,
) -> list[LocalizationEvaluationRead]:
    if not await session.get(Reconstruction, reconstruction_id):
        raise NotFoundException(f"Reconstruction with id {reconstruction_id} not found")

    query = select(LocalizationEvaluation).where(LocalizationEvaluation.reconstruction_id == reconstruction_id)
    if pipeline_version is not None:
        query = query.where(LocalizationEvaluation.pipeline_version == pipeline_version)

    result = await session.execute(query)
    return [localization_evaluation_to_dto(row) for row in result.scalars().all()]


router = Router(
    "/reconstructions/{reconstruction_id:uuid}/localization-evaluations",
    tags=["Localization Evaluations"],
    dependencies={"session": Provide(get_session)},
    route_handlers=[
        upsert_localization_evaluation,
        list_localization_evaluations,
    ],
)
