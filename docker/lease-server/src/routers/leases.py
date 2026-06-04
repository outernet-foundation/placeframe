from __future__ import annotations

from datetime import timedelta
from typing import Optional
from uuid import UUID

from core.reconstruction_manifest import MANIFEST_VERSION, Manifest
from core.reconstruction_metrics import ReconstructionMetrics
from core.reconstruction_options import ReconstructionOptions
from datamodels.public_tables import Reconstruction, ReconstructionStatus
from litestar import Router, post, put
from litestar.di import Provide
from litestar.exceptions import NotFoundException
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from ..database import get_session

LEASE_TIMEOUT = timedelta(minutes=30)


class LeaseResponse(BaseModel):
    reconstruction_id: UUID
    capture_session_id: UUID
    options: ReconstructionOptions


class ProgressUpdate(BaseModel):
    status: ReconstructionStatus
    progress_current: Optional[int] = None
    progress_total: Optional[int] = None
    progress_attempt: Optional[int] = None
    error: Optional[str] = None


class FailLeaseRequest(BaseModel):
    error: str
    metrics: Optional[ReconstructionMetrics] = None


@post("/request")
async def request_lease(session: AsyncSession) -> LeaseResponse:
    # Reap stale leases — a worker crash skips complete_lease and would otherwise stall the queue.
    # A lease is "stale" when it has been off the queued list for longer than LEASE_TIMEOUT
    # without any updated_at refresh (every progress write touches updated_at via the trigger).
    await session.execute(
        update(Reconstruction)
        .where(
            ~Reconstruction.status.in_((
                ReconstructionStatus.SUCCEEDED,
                ReconstructionStatus.FAILED,
                ReconstructionStatus.CANCELLED,
                ReconstructionStatus.QUEUED,
            )),
            Reconstruction.updated_at < func.now() - LEASE_TIMEOUT,
        )
        .values(status=ReconstructionStatus.FAILED, error="Lease timed out")
    )

    result = await session.execute(
        select(Reconstruction)
        .where(Reconstruction.status == ReconstructionStatus.QUEUED)
        .order_by(Reconstruction.created_at)
        .with_for_update(skip_locked=True)
        .limit(1)
    )
    row = result.scalar_one_or_none()

    if not row:
        raise NotFoundException("No pending jobs")

    # Validate the manifest BEFORE flipping status. If validation throws after the commit,
    # the row is already out of QUEUED but no worker has it, leaving it stuck in
    # EXTRACTING_FEATURES until LEASE_TIMEOUT reaps it 30 minutes later.
    manifest = Manifest.model_validate(row.manifest)

    # Flip out of QUEUED so subsequent request_lease polls skip this row. The reconstructor's
    # pre-extraction setup (tar download, manifest parse, rig build, pair gen) runs under
    # EXTRACTING_FEATURES with no progress until the per-image loop sets the real total.
    row.status = ReconstructionStatus.EXTRACTING_FEATURES

    await session.flush()
    await session.commit()

    return LeaseResponse(
        reconstruction_id=row.id,
        capture_session_id=row.capture_session_id,
        options=manifest.options,
    )


@put("/{id:uuid}/progress")
async def update_progress(session: AsyncSession, id: UUID, data: ProgressUpdate) -> None:
    row = await session.get(Reconstruction, id)

    if not row:
        raise NotFoundException("Reconstruction not found")

    row.status = data.status
    row.progress_current = data.progress_current
    row.progress_total = data.progress_total
    row.progress_attempt = data.progress_attempt
    row.error = data.error

    await session.flush()
    await session.commit()


@put("/{id:uuid}/succeed")
async def succeed_lease(session: AsyncSession, id: UUID, data: ReconstructionMetrics) -> None:
    row = await _finalize_lease(session, id, ReconstructionStatus.SUCCEEDED)
    row.error = None

    existing = Manifest.model_validate(row.manifest)
    merged = Manifest(options=existing.options, metrics=data)
    row.manifest = merged.model_dump(mode="json")
    row.manifest_version = MANIFEST_VERSION

    await session.flush()
    await session.commit()


@put("/{id:uuid}/fail")
async def fail_lease(session: AsyncSession, id: UUID, data: FailLeaseRequest) -> None:
    row = await _finalize_lease(session, id, ReconstructionStatus.FAILED)
    row.error = data.error

    if data.metrics is not None:
        existing = Manifest.model_validate(row.manifest)
        merged = Manifest(options=existing.options, metrics=data.metrics)
        row.manifest = merged.model_dump(mode="json")
        row.manifest_version = MANIFEST_VERSION

    await session.flush()
    await session.commit()


async def _finalize_lease(session: AsyncSession, id: UUID, status: ReconstructionStatus) -> Reconstruction:
    row = await session.get(Reconstruction, id)

    if not row:
        raise NotFoundException("Reconstruction not found")

    row.status = status
    # Clear progress fields on terminal transition so callers don't see stale phase numbers.
    row.progress_current = None
    row.progress_total = None
    row.progress_attempt = None

    return row


router = Router(
    path="/leases",
    tags=["Leases"],
    dependencies={"session": Provide(get_session)},
    route_handlers=[request_lease, update_progress, succeed_lease, fail_lease],
)
