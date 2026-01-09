from __future__ import annotations

from uuid import UUID

from datamodels.public_tables import OrchestrationStatus, Reconstruction
from litestar import Router, post, put
from litestar.di import Provide
from litestar.exceptions import HTTPException
from litestar.status_codes import HTTP_404_NOT_FOUND
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_worker_session


class LeaseResponse(BaseModel):
    reconstruction_id: UUID
    capture_session_id: UUID


@post("/request")
async def request_lease(session: AsyncSession) -> LeaseResponse:
    # Find the oldest queued reconstruction and lock the row
    result = await session.execute(
        select(Reconstruction)
        .where(Reconstruction.orchestration_status == OrchestrationStatus.QUEUED)
        .order_by(Reconstruction.created_at)
        .with_for_update(skip_locked=True)
        .limit(1)
    )
    row = result.scalar_one_or_none()

    if not row:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="No pending jobs")

    row.orchestration_status = OrchestrationStatus.PENDING

    await session.flush()
    await session.commit()

    return LeaseResponse(reconstruction_id=row.id, capture_session_id=row.capture_session_id)


@put("/{id:uuid}/complete")
async def complete_lease(session: AsyncSession, id: UUID, data: OrchestrationStatus) -> None:
    row = await session.get(Reconstruction, id)

    if not row:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Reconstruction not found")

    row.orchestration_status = data

    await session.flush()
    await session.commit()

    return None


router = Router(
    path="/internal/leases",
    tags=["Leases", "Internal"],
    dependencies={"session": Provide(get_worker_session)},
    route_handlers=[request_lease, complete_lease],
)
