from __future__ import annotations

from datetime import timedelta
from logging import getLogger
from typing import Literal, Optional
from uuid import UUID

from placeframe_core.reconstruction_manifest import MANIFEST_VERSION, Manifest
from placeframe_core.reconstruction_metrics import ReconstructionMetrics
from placeframe_core.reconstruction_options import ReconstructionOptions
from datamodels.public_tables import Reconstruction, ReconstructionStatus
from litestar import Request, Response, Router, post
from litestar.datastructures import State
from litestar.di import Provide
from litestar.exceptions import HTTPException, NotFoundException
from litestar.openapi.datastructures import ResponseSpec
from litestar.status_codes import HTTP_409_CONFLICT, HTTP_422_UNPROCESSABLE_ENTITY
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from ..database import SessionLocal, get_session
from ..settings import get_settings

logger = getLogger("lease-server")

MAX_ERROR_ATTEMPTS = 5
TERMINAL_STATUSES = (ReconstructionStatus.SUCCEEDED, ReconstructionStatus.FAILED)
# QUEUED, PAUSED, and terminal rows hold no lease a worker may write
NON_WORKING_STATUSES = (ReconstructionStatus.QUEUED, ReconstructionStatus.PAUSED, *TERMINAL_STATUSES)

RefusalReason = Literal["superseded", "paused"]


class LeaseRefusal(BaseModel):
    reason: RefusalReason


class LeaseRefusalException(HTTPException):
    status_code = HTTP_409_CONFLICT

    def __init__(self, reason: RefusalReason) -> None:
        super().__init__(detail=f"Lease refused: the row is {reason}")
        self.reason = reason


class Lease(BaseModel):
    reconstruction_id: UUID
    capture_session_id: UUID
    options: ReconstructionOptions
    lease_attempt: int


class LeaseResponse(BaseModel):
    lease: Lease | None


class ProgressUpdate(BaseModel):
    status: ReconstructionStatus
    progress_current: Optional[int] = None
    progress_total: Optional[int] = None
    progress_attempt: Optional[int] = None
    error: Optional[str] = None
    lease_attempt: int


class FailLeaseRequest(BaseModel):
    error: str
    metrics: Optional[ReconstructionMetrics] = None


class ErrorRequest(BaseModel):
    error: str


class PreemptRequest(BaseModel):
    lease_attempt: int


REFUSAL_RESPONSE = ResponseSpec(
    data_container=LeaseRefusal,
    # The example generator embeds a LeaseRefusal instance the codegen spec dump cannot serialize
    generate_examples=False,
    description=(
        "The write was refused and changed nothing: reason `paused` means an operator paused the job, "
        "reason `superseded` means the row is terminal or owned by a different lease attempt. "
        "The worker abandons the job and leaves all artifacts untouched."
    ),
)


def render_lease_refusal(
    request: Request[None, None, State], exception: LeaseRefusalException
) -> Response[dict[str, str]]:
    logger.info("Lease refusal on %s %s: reason=%s", request.method, request.url.path, exception.reason)
    return Response(content={"reason": exception.reason}, status_code=HTTP_409_CONFLICT)


@post("/request")
async def request_lease(session: AsyncSession) -> LeaseResponse:
    settings = get_settings()

    # Stale means a working row whose lease_heartbeat_at is older than the lease timeout
    stale_filter = (
        ~Reconstruction.status.in_(NON_WORKING_STATUSES),
        Reconstruction.lease_heartbeat_at < func.now() - timedelta(seconds=settings.lease_timeout_s),
    )

    # Reap a dead worker's lease in its own transaction so it persists even when no row is granted
    async with SessionLocal() as reaper_session, reaper_session.begin():
        await reaper_session.execute(
            update(Reconstruction)
            .where(*stale_filter, Reconstruction.error_count >= MAX_ERROR_ATTEMPTS)
            .values(
                status=ReconstructionStatus.FAILED,
                error=func.coalesce(Reconstruction.error, "lease timed out"),
                progress_current=None,
                progress_total=None,
                progress_attempt=None,
            )
        )
        await reaper_session.execute(
            update(Reconstruction)
            .where(*stale_filter, Reconstruction.error_count < MAX_ERROR_ATTEMPTS)
            .values(
                status=ReconstructionStatus.QUEUED,
                error_count=Reconstruction.error_count + 1,
                error="lease timed out",
                progress_current=None,
                progress_total=None,
                progress_attempt=None,
            )
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
        return LeaseResponse(lease=None)

    # Validate the manifest before flipping status, because a failure after the commit strands the row
    manifest = Manifest.model_validate(row.manifest)

    # Claim the row and stamp its first heartbeat, because pre-extraction setup reports no progress
    await session.execute(
        update(Reconstruction)
        .where(Reconstruction.id == row.id)
        .values(
            status=ReconstructionStatus.EXTRACTING_FEATURES,
            lease_attempt=Reconstruction.lease_attempt + 1,
            lease_heartbeat_at=func.now(),
        )
    )

    await session.commit()

    assert row.capture_session_id is not None

    return LeaseResponse(
        lease=Lease(
            reconstruction_id=row.id,
            capture_session_id=row.capture_session_id,
            options=manifest.options,
            lease_attempt=row.lease_attempt + 1,
        ),
    )


@post("/{id:uuid}/progress", raises=[LeaseRefusalException, NotFoundException], responses={409: REFUSAL_RESPONSE})
async def update_progress(session: AsyncSession, id: UUID, data: ProgressUpdate) -> None:
    await _fenced_row(session, id, data.lease_attempt)

    if data.status in NON_WORKING_STATUSES:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Status {data.status.value} is outside the working family a lease may report",
        )

    # A core UPDATE, because SQLAlchemy skips ORM updates with no changed column and a
    # repeat write must still refresh the heartbeat
    await session.execute(
        update(Reconstruction)
        .where(
            Reconstruction.id == id,
            Reconstruction.lease_attempt == data.lease_attempt,
            ~Reconstruction.status.in_(NON_WORKING_STATUSES),
        )
        .values(
            status=data.status,
            progress_current=data.progress_current,
            progress_total=data.progress_total,
            progress_attempt=data.progress_attempt,
            error=data.error,
            lease_heartbeat_at=func.now(),
        )
    )

    await session.commit()


@post("/{id:uuid}/succeed", raises=[LeaseRefusalException, NotFoundException], responses={409: REFUSAL_RESPONSE})
async def succeed_lease(session: AsyncSession, id: UUID, data: ReconstructionMetrics, lease_attempt: int) -> None:
    row = await _fenced_row(session, id, lease_attempt)

    row.status = ReconstructionStatus.SUCCEEDED
    row.error = None
    row.progress_current = None
    row.progress_total = None
    row.progress_attempt = None

    existing = Manifest.model_validate(row.manifest)
    merged = Manifest(options=existing.options, metrics=data)
    row.manifest = merged.model_dump(mode="json")
    row.manifest_version = MANIFEST_VERSION

    await session.flush()
    await session.commit()


@post("/{id:uuid}/fail", raises=[LeaseRefusalException, NotFoundException], responses={409: REFUSAL_RESPONSE})
async def fail_lease(session: AsyncSession, id: UUID, data: FailLeaseRequest, lease_attempt: int) -> None:
    row = await _fenced_row(session, id, lease_attempt)

    row.status = ReconstructionStatus.FAILED
    row.error = data.error
    row.progress_current = None
    row.progress_total = None
    row.progress_attempt = None

    if data.metrics is not None:
        existing = Manifest.model_validate(row.manifest)
        merged = Manifest(options=existing.options, metrics=data.metrics)
        row.manifest = merged.model_dump(mode="json")
        row.manifest_version = MANIFEST_VERSION

    await session.flush()
    await session.commit()


@post("/{id:uuid}/error", raises=[LeaseRefusalException, NotFoundException], responses={409: REFUSAL_RESPONSE})
async def error_lease(session: AsyncSession, id: UUID, data: ErrorRequest, lease_attempt: int) -> None:
    row = await _fenced_row(session, id, lease_attempt)

    row.error = data.error
    if row.error_count >= MAX_ERROR_ATTEMPTS:
        row.status = ReconstructionStatus.FAILED
    if row.error_count < MAX_ERROR_ATTEMPTS:
        row.status = ReconstructionStatus.QUEUED
        row.error_count = row.error_count + 1

    row.progress_current = None
    row.progress_total = None
    row.progress_attempt = None

    await session.flush()
    await session.commit()


@post("/{id:uuid}/preempt", raises=[LeaseRefusalException, NotFoundException], responses={409: REFUSAL_RESPONSE})
async def preempt_lease(session: AsyncSession, id: UUID, data: PreemptRequest) -> None:
    row = await _fenced_row(session, id, data.lease_attempt)

    # Return the row to QUEUED without counting an error and without failing the job
    row.status = ReconstructionStatus.QUEUED
    row.error = None
    row.progress_current = None
    row.progress_total = None
    row.progress_attempt = None

    await session.flush()
    await session.commit()


async def _fenced_row(session: AsyncSession, id: UUID, echoed_attempt: int) -> Reconstruction:
    row = await session.get(Reconstruction, id)

    if row is None:
        raise NotFoundException("Reconstruction not found")

    # Refuse the write when the lease is gone: the row is paused or terminal, the echoed
    # attempt is stale, or a QUEUED row's matching attempt is owned by nobody until the next grant
    if row.status == ReconstructionStatus.PAUSED:
        raise LeaseRefusalException("paused")
    if row.status in TERMINAL_STATUSES:
        raise LeaseRefusalException("superseded")
    if echoed_attempt != row.lease_attempt:
        raise LeaseRefusalException("superseded")
    if row.status == ReconstructionStatus.QUEUED:
        raise LeaseRefusalException("superseded")

    return row


router = Router(
    path="/leases",
    tags=["Leases"],
    dependencies={"session": Provide(get_session)},
    route_handlers=[request_lease, update_progress, succeed_lease, fail_lease, error_lease, preempt_lease],
    exception_handlers={LeaseRefusalException: render_lease_refusal},
)
