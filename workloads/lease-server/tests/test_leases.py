from __future__ import annotations

from collections.abc import Awaitable, Callable
from types import TracebackType
from typing import Self
from uuid import UUID, uuid4

import pytest
from datamodels.public_tables import Reconstruction, ReconstructionStatus
from lease_server.routers import leases
from lease_server.routers.leases import (
    ErrorRequest,
    FailLeaseRequest,
    LeaseRefusalException,
    PreemptRequest,
    ProgressUpdate,
    error_lease,
    fail_lease,
    preempt_lease,
    request_lease,
    succeed_lease,
    update_progress,
)
from litestar.exceptions import HTTPException, NotFoundException
from placeframe_core.reconstruction_manifest import MANIFEST_VERSION
from placeframe_core.reconstruction_metrics import ReconstructionMetrics
from sqlalchemy import Update
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import Select

RECONSTRUCTION_ID = uuid4()
WORKING_STATUS = ReconstructionStatus.EXTRACTING_FEATURES
GRANTED_ATTEMPT = 4
NON_WORKING_PAYLOAD_STATUSES = (
    ReconstructionStatus.QUEUED,
    ReconstructionStatus.PAUSED,
    ReconstructionStatus.SUCCEEDED,
    ReconstructionStatus.FAILED,
)


JsonValue = str | int | float | bool | list["JsonValue"] | dict[str, "JsonValue"] | None


class StubRow:
    def __init__(
        self,
        status: ReconstructionStatus,
        lease_attempt: int = GRANTED_ATTEMPT,
        error_count: int = 0,
        error: str | None = None,
    ) -> None:
        self.id = RECONSTRUCTION_ID
        self.capture_session_id = uuid4()
        self.status = status
        self.lease_attempt = lease_attempt
        self.error_count = error_count
        self.error = error
        self.progress_current = 11
        self.progress_total = 22
        self.progress_attempt = 33
        self.manifest: dict[str, dict[str, JsonValue]] = {"options": {}, "metrics": {}}
        self.manifest_version = 0


class StubResult:
    def __init__(self, row: StubRow | None) -> None:
        self._row = row

    def scalar_one_or_none(self) -> StubRow | None:
        return self._row


class StubSession:
    def __init__(self, row: StubRow | None = None) -> None:
        self._row = row
        self.statements: list[Select[tuple[Reconstruction]] | Update] = []

    async def execute(self, statement: Select[tuple[Reconstruction]] | Update) -> StubResult:
        self.statements.append(statement)
        return StubResult(self._row)

    async def get(self, _model: type[Reconstruction], _id: UUID) -> StubRow | None:
        return self._row

    async def flush(self) -> None:
        return None

    async def commit(self) -> None:
        return None


class StubReaperSession:
    def __init__(self) -> None:
        self.statements: list[Update] = []

    async def execute(self, statement: Update) -> None:
        self.statements.append(statement)

    def begin(self) -> StubReaperSession:
        return self

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        return None


class StubSessionLocal:
    def __init__(self) -> None:
        self.session = StubReaperSession()

    def __call__(self) -> StubReaperSession:
        return self.session


WriteCallable = Callable[[StubSession, int], Awaitable[None]]


async def _progress_write(session: StubSession, echoed_attempt: int) -> None:
    await update_progress.fn(
        session=session,
        id=RECONSTRUCTION_ID,
        data=ProgressUpdate(status=WORKING_STATUS, progress_current=1, progress_total=2, lease_attempt=echoed_attempt),
    )


async def _succeed_write(session: StubSession, echoed_attempt: int) -> None:
    await succeed_lease.fn(
        session=session, id=RECONSTRUCTION_ID, data=ReconstructionMetrics(), lease_attempt=echoed_attempt
    )


async def _fail_write(session: StubSession, echoed_attempt: int) -> None:
    await fail_lease.fn(
        session=session, id=RECONSTRUCTION_ID, data=FailLeaseRequest(error="boom"), lease_attempt=echoed_attempt
    )


async def _error_write(session: StubSession, echoed_attempt: int) -> None:
    await error_lease.fn(
        session=session, id=RECONSTRUCTION_ID, data=ErrorRequest(error="boom"), lease_attempt=echoed_attempt
    )


async def _preempt_write(session: StubSession, echoed_attempt: int) -> None:
    await preempt_lease.fn(session=session, id=RECONSTRUCTION_ID, data=PreemptRequest(lease_attempt=echoed_attempt))


FENCED_WRITES: list[tuple[str, WriteCallable]] = [
    ("progress", _progress_write),
    ("succeed", _succeed_write),
    ("fail", _fail_write),
    ("error", _error_write),
    ("preempt", _preempt_write),
]


def _rendered(statement: Select[tuple[Reconstruction]] | Update) -> str:
    return str(statement.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}))


@pytest.fixture
def reaper(monkeypatch: pytest.MonkeyPatch) -> StubReaperSession:
    stub = StubSessionLocal()
    monkeypatch.setattr(leases, "SessionLocal", stub)
    return stub.session


@pytest.mark.asyncio
@pytest.mark.parametrize(("name", "write"), FENCED_WRITES)
async def test_missing_row_is_not_found(name: str, write: WriteCallable) -> None:
    session = StubSession(row=None)

    with pytest.raises(NotFoundException):
        await write(session, GRANTED_ATTEMPT)


@pytest.mark.asyncio
@pytest.mark.parametrize(("name", "write"), FENCED_WRITES)
async def test_paused_row_is_refused_as_paused(name: str, write: WriteCallable) -> None:
    session = StubSession(row=StubRow(ReconstructionStatus.PAUSED))

    with pytest.raises(LeaseRefusalException) as refusal:
        await write(session, GRANTED_ATTEMPT)

    assert refusal.value.reason == "paused"


@pytest.mark.asyncio
@pytest.mark.parametrize(("name", "write"), FENCED_WRITES)
async def test_failed_row_is_refused_as_superseded(name: str, write: WriteCallable) -> None:
    session = StubSession(row=StubRow(ReconstructionStatus.FAILED))

    with pytest.raises(LeaseRefusalException) as refusal:
        await write(session, GRANTED_ATTEMPT)

    assert refusal.value.reason == "superseded"


@pytest.mark.asyncio
async def test_late_succeed_on_succeeded_is_refused_as_superseded() -> None:
    session = StubSession(row=StubRow(ReconstructionStatus.SUCCEEDED))

    with pytest.raises(LeaseRefusalException) as refusal:
        await _succeed_write(session, GRANTED_ATTEMPT)

    assert refusal.value.reason == "superseded"


@pytest.mark.asyncio
@pytest.mark.parametrize(("name", "write"), FENCED_WRITES)
async def test_stale_attempt_is_refused_as_superseded(name: str, write: WriteCallable) -> None:
    session = StubSession(row=StubRow(WORKING_STATUS, lease_attempt=GRANTED_ATTEMPT + 1))

    with pytest.raises(LeaseRefusalException) as refusal:
        await write(session, GRANTED_ATTEMPT)

    assert refusal.value.reason == "superseded"


@pytest.mark.asyncio
@pytest.mark.parametrize(("name", "write"), FENCED_WRITES)
async def test_matching_attempt_on_queued_row_is_refused_as_superseded(name: str, write: WriteCallable) -> None:
    session = StubSession(row=StubRow(ReconstructionStatus.QUEUED))

    with pytest.raises(LeaseRefusalException) as refusal:
        await write(session, GRANTED_ATTEMPT)

    assert refusal.value.reason == "superseded"


@pytest.mark.asyncio
@pytest.mark.parametrize("status", NON_WORKING_PAYLOAD_STATUSES)
async def test_progress_rejects_non_working_statuses_with_422(status: ReconstructionStatus) -> None:
    session = StubSession(row=StubRow(WORKING_STATUS))

    with pytest.raises(HTTPException) as raised:
        await update_progress.fn(
            session=session,
            id=RECONSTRUCTION_ID,
            data=ProgressUpdate(status=status, lease_attempt=GRANTED_ATTEMPT),
        )

    assert raised.value.status_code == 422


@pytest.mark.asyncio
async def test_progress_write_persists_the_heartbeat_on_every_write() -> None:
    session = StubSession(row=StubRow(WORKING_STATUS))

    await _progress_write(session, GRANTED_ATTEMPT)
    await _progress_write(session, GRANTED_ATTEMPT)

    assert len(session.statements) == 2
    for statement in session.statements:
        rendered = _rendered(statement)
        assert "lease_heartbeat_at=now()" in rendered, f"no-op writes must still stamp the heartbeat: {rendered}"
        assert "lease_attempt = 4" in rendered
        assert "NOT IN" in rendered


@pytest.mark.asyncio
async def test_succeed_flips_terminal_merges_metrics_and_clears_error(reaper: StubReaperSession) -> None:
    row = StubRow(WORKING_STATUS, error="left over from an error report")
    session = StubSession(row=row)

    await succeed_lease.fn(
        session=session,
        id=RECONSTRUCTION_ID,
        data=ReconstructionMetrics(successful=True),
        lease_attempt=GRANTED_ATTEMPT,
    )

    assert row.status == ReconstructionStatus.SUCCEEDED
    assert row.error is None
    assert row.progress_current is None
    assert row.progress_total is None
    assert row.progress_attempt is None
    assert row.manifest["metrics"]["successful"] is True
    assert row.manifest_version == MANIFEST_VERSION


@pytest.mark.asyncio
async def test_fail_flips_terminal_with_error_and_optional_metrics() -> None:
    row = StubRow(WORKING_STATUS, error_count=2)
    session = StubSession(row=row)

    await fail_lease.fn(
        session=session,
        id=RECONSTRUCTION_ID,
        data=FailLeaseRequest(error="no model", metrics=ReconstructionMetrics(successful=False)),
        lease_attempt=GRANTED_ATTEMPT,
    )

    assert row.status == ReconstructionStatus.FAILED
    assert row.error == "no model"
    assert row.error_count == 2
    assert row.progress_current is None
    assert row.manifest["metrics"]["successful"] is False


@pytest.mark.asyncio
async def test_error_below_cap_requeues_and_counts() -> None:
    row = StubRow(WORKING_STATUS, error_count=2)
    session = StubSession(row=row)

    await _error_write(session, GRANTED_ATTEMPT)

    assert row.status == ReconstructionStatus.QUEUED
    assert row.error_count == 3
    assert row.error == "boom"
    assert row.progress_current is None
    assert row.progress_total is None
    assert row.progress_attempt is None


@pytest.mark.asyncio
async def test_error_at_cap_fails_without_counting() -> None:
    row = StubRow(WORKING_STATUS, error_count=5)
    session = StubSession(row=row)

    await _error_write(session, GRANTED_ATTEMPT)

    assert row.status == ReconstructionStatus.FAILED
    assert row.error_count == 5
    assert row.error == "boom"


@pytest.mark.asyncio
async def test_preempt_requeues_without_counting_or_failing() -> None:
    row = StubRow(WORKING_STATUS, error_count=5, error="left over from an error report")
    session = StubSession(row=row)

    await _preempt_write(session, GRANTED_ATTEMPT)

    assert row.status == ReconstructionStatus.QUEUED
    assert row.error_count == 5
    assert row.error is None
    assert row.progress_current is None
    assert row.progress_total is None
    assert row.progress_attempt is None


@pytest.mark.asyncio
async def test_grant_increments_the_attempt_and_stamps_the_first_heartbeat(reaper: StubReaperSession) -> None:
    row = StubRow(ReconstructionStatus.QUEUED, lease_attempt=3)
    session = StubSession(row=row)

    response = await request_lease.fn(session=session)

    assert response.lease is not None
    assert response.lease.lease_attempt == 4
    assert response.lease.reconstruction_id == row.id
    rendered = _rendered(session.statements[1])
    assert "lease_attempt + 1" in rendered
    assert "lease_heartbeat_at=now()" in rendered
    assert "'extracting_features'" in rendered


@pytest.mark.asyncio
async def test_grant_with_no_queued_row_returns_a_null_lease(reaper: StubReaperSession) -> None:
    session = StubSession(row=None)

    response = await request_lease.fn(session=session)

    assert response.lease is None


@pytest.mark.asyncio
async def test_reaper_excludes_queued_paused_and_terminal_rows(reaper: StubReaperSession) -> None:
    session = StubSession(row=None)

    await request_lease.fn(session=session)

    stale_clause = _rendered(reaper.statements[0])
    for value in ("'queued'", "'paused'", "'succeeded'", "'failed'"):
        assert value in stale_clause, f"the stale filter must exclude {value}: {stale_clause}"
    assert "lease_heartbeat_at" in stale_clause
    assert "now()" in stale_clause


@pytest.mark.asyncio
async def test_reaper_below_cap_counts_one_error_and_requeues(reaper: StubReaperSession) -> None:
    session = StubSession(row=None)

    await request_lease.fn(session=session)

    rendered = _rendered(reaper.statements[1])
    assert "'queued'" in rendered
    assert "error_count + 1" in rendered
    assert "'lease timed out'" in rendered


@pytest.mark.asyncio
async def test_reaper_at_cap_fails_preserving_the_last_error(reaper: StubReaperSession) -> None:
    session = StubSession(row=None)

    await request_lease.fn(session=session)

    rendered = _rendered(reaper.statements[0])
    assert "'failed'" in rendered
    assert "coalesce(public.reconstructions.error, 'lease timed out')" in rendered
    assert "error_count + 1" not in rendered
