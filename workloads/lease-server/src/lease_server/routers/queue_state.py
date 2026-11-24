from __future__ import annotations

from datamodels.public_tables import Reconstruction, ReconstructionStatus
from litestar import Router, get
from litestar.di import Provide
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from ..database import get_session
from .leases import TERMINAL_STATUSES

# The statuses in_flight excludes, the same set the stale-lease reaper filters on
NON_ACTIVE_STATUSES = (*TERMINAL_STATUSES, ReconstructionStatus.QUEUED, ReconstructionStatus.PAUSED)


class QueueState(BaseModel):
    queued: int
    in_flight: int


@get("")
async def get_queue_state(session: AsyncSession) -> QueueState:
    queued = (
        await session.execute(
            select(func.count()).select_from(Reconstruction).where(Reconstruction.status == ReconstructionStatus.QUEUED)
        )
    ).scalar_one()
    in_flight = (
        await session.execute(
            select(func.count()).select_from(Reconstruction).where(~Reconstruction.status.in_(NON_ACTIVE_STATUSES))
        )
    ).scalar_one()
    return QueueState(queued=queued, in_flight=in_flight)


router = Router(
    path="/queue-state",
    tags=["QueueState"],
    dependencies={"session": Provide(get_session)},
    route_handlers=[get_queue_state],
)
