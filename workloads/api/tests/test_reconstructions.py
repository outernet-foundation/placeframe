from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime
from functools import partial
from io import BytesIO
from typing import Optional
from uuid import UUID, uuid4

import pytest
import tarfile
from datamodels.public_tables import LocalizationMap, Reconstruction, ReconstructionStatus
from litestar.exceptions import HTTPException, NotFoundException
from litestar.handlers import HTTPRouteHandler
from sqlalchemy.sql import Select
from src.routers import reconstructions
from src.routers.reconstructions import (
    TERMINAL_STATUSES,
    delete_reconstruction,
    iter_reconstruction_tar,
    pause_reconstruction,
    resume_reconstruction,
)

RECONSTRUCTION_ID = uuid4()
WORKING_STATUS = ReconstructionStatus.EXTRACTING_FEATURES
QUEUE_POSITION = 3
QUEUE_DEPTH = 7


class StubSession:
    def __init__(self, row: StubRow | None, localization_map_id: UUID | None = None) -> None:
        self._row = row
        self._localization_map_id = localization_map_id
        self.deleted_rows: list[StubRow] = []

    async def execute(self, statement: ExecutionStatement) -> StubResult:
        return StubResult(self._row, self._localization_map_id)

    async def get(self, _model: type[Reconstruction], _id: UUID) -> StubRow | None:
        return self._row

    async def delete(self, row: StubRow) -> None:
        self.deleted_rows.append(row)

    async def flush(self) -> None:
        return None


ExecutionStatement = Select[tuple[Reconstruction, Optional[int], Optional[int]]] | Select[tuple[LocalizationMap]]


class StubResult:
    def __init__(self, row: StubRow | None, localization_map_id: UUID | None) -> None:
        self._row = row
        self._localization_map_id = localization_map_id

    def one(self) -> tuple[StubRow, int, int]:
        assert self._row is not None
        return self._row, QUEUE_POSITION, QUEUE_DEPTH

    def scalar_one_or_none(self) -> UUID | None:
        return self._localization_map_id


class StubRow:
    def __init__(
        self,
        status: ReconstructionStatus,
        error_count: int = 0,
        error: str | None = None,
        lease_attempt: int = 4,
    ) -> None:
        self.tenant_id = uuid4()
        self.id = RECONSTRUCTION_ID
        self.capture_session_id = uuid4()
        self.created_at = datetime(2026, 11, 24, 12, 0, tzinfo=UTC)
        self.updated_at = datetime(2026, 11, 24, 12, 0, tzinfo=UTC)
        self.status = status
        self.error_count = error_count
        self.error = error
        self.lease_attempt = lease_attempt
        self.lease_heartbeat_at = datetime(2026, 11, 24, 12, 0, tzinfo=UTC)
        self.progress_current = 11
        self.progress_total = 22
        self.progress_attempt = 33
        self.manifest: dict[str, dict[str, JsonValue]] = {"options": {}, "metrics": {}}
        self.manifest_version = 0


class StubS3Client:
    def __init__(self, keys: list[str]) -> None:
        self._keys = keys
        self.deleted_batches: list[list[str]] = []

    def get_paginator(self, _operation: str) -> StubPaginator:
        return StubPaginator([{"Contents": [{"Key": key} for key in self._keys]}])

    def delete_objects(self, **_kwargs: JsonValue) -> S3Page:
        delete_request = _kwargs["Delete"]
        self.deleted_batches.append([obj["Key"] for obj in delete_request["Objects"]])
        return {"Errors": []}


class StubPaginator:
    def __init__(self, pages: list[S3Page]) -> None:
        self._pages = pages

    def paginate(self, **_kwargs: JsonValue) -> Iterator[S3Page]:
        return iter(self._pages)


S3Page = dict[str, list[dict[str, str]]]

JsonValue = str | int | float | bool | list["JsonValue"] | dict[str, "JsonValue"] | None


class StubStorage:
    def __init__(self, keys: list[tuple[str, int]]) -> None:
        self._keys = keys

    def list_objects(self, bucket: str, prefix: str) -> Iterator[tuple[str, int]]:
        for key, size in self._keys:
            if not key.startswith(prefix):
                continue
            yield key, size

    def get_object(self, bucket: str, key: str) -> dict[str, StubBody]:
        return {"Body": StubBody(b"payload")}


class StubBody:
    def __init__(self, payload: bytes) -> None:
        self._payload = payload

    def iter_chunks(self, chunk_size: int) -> Iterator[bytes]:
        yield self._payload


@pytest.mark.asyncio
@pytest.mark.parametrize("handler", [pause_reconstruction, resume_reconstruction])
async def test_missing_row_is_not_found(handler: HTTPRouteHandler) -> None:
    session = StubSession(row=None)

    with pytest.raises(NotFoundException):
        await handler.fn(session=session, id=RECONSTRUCTION_ID)


@pytest.mark.asyncio
async def test_pause_on_queued_moves_only_the_status() -> None:
    row = StubRow(ReconstructionStatus.QUEUED, error_count=2, error="earlier failure")
    session = StubSession(row=row)

    response = await pause_reconstruction.fn(session=session, id=RECONSTRUCTION_ID)

    assert row.status == ReconstructionStatus.PAUSED
    assert row.error_count == 2
    assert row.error == "earlier failure"
    assert row.progress_current == 11
    assert row.progress_total == 22
    assert row.progress_attempt == 33
    assert row.lease_attempt == 4
    assert response.status == ReconstructionStatus.PAUSED


@pytest.mark.asyncio
async def test_pause_on_a_working_status_pauses_the_job() -> None:
    row = StubRow(WORKING_STATUS)
    session = StubSession(row=row)

    response = await pause_reconstruction.fn(session=session, id=RECONSTRUCTION_ID)

    assert row.status == ReconstructionStatus.PAUSED
    assert response.status == ReconstructionStatus.PAUSED


@pytest.mark.asyncio
async def test_pause_on_paused_is_an_idempotent_no_op() -> None:
    row = StubRow(ReconstructionStatus.PAUSED, error_count=2, error="earlier failure")
    session = StubSession(row=row)

    response = await pause_reconstruction.fn(session=session, id=RECONSTRUCTION_ID)

    assert row.status == ReconstructionStatus.PAUSED
    assert row.error_count == 2
    assert row.error == "earlier failure"
    assert response.status == ReconstructionStatus.PAUSED


@pytest.mark.asyncio
@pytest.mark.parametrize("status", list(TERMINAL_STATUSES))
async def test_pause_on_a_terminal_status_is_refused(status: ReconstructionStatus) -> None:
    session = StubSession(row=StubRow(status))

    with pytest.raises(HTTPException) as raised:
        await pause_reconstruction.fn(session=session, id=RECONSTRUCTION_ID)

    assert raised.value.status_code == 409


@pytest.mark.asyncio
async def test_resume_on_paused_requeues_resets_the_budget_and_keeps_the_attempt() -> None:
    row = StubRow(ReconstructionStatus.PAUSED, error_count=5, error="boom", lease_attempt=9)
    session = StubSession(row=row)

    response = await resume_reconstruction.fn(session=session, id=RECONSTRUCTION_ID)

    assert row.status == ReconstructionStatus.QUEUED
    assert row.error_count == 0
    assert row.error is None
    assert row.progress_current is None
    assert row.progress_total is None
    assert row.progress_attempt is None
    assert row.lease_attempt == 9
    assert response.status == ReconstructionStatus.QUEUED


@pytest.mark.asyncio
async def test_resume_on_failed_requeues_resets_the_budget_and_keeps_the_attempt() -> None:
    row = StubRow(ReconstructionStatus.FAILED, error_count=5, error="exhausted", lease_attempt=9)
    session = StubSession(row=row)

    response = await resume_reconstruction.fn(session=session, id=RECONSTRUCTION_ID)

    assert row.status == ReconstructionStatus.QUEUED
    assert row.error_count == 0
    assert row.error is None
    assert row.lease_attempt == 9
    assert response.status == ReconstructionStatus.QUEUED


@pytest.mark.asyncio
async def test_resume_on_queued_is_an_idempotent_no_op() -> None:
    row = StubRow(ReconstructionStatus.QUEUED, error_count=1, error="stale")
    session = StubSession(row=row)

    response = await resume_reconstruction.fn(session=session, id=RECONSTRUCTION_ID)

    assert row.status == ReconstructionStatus.QUEUED
    assert row.error_count == 1
    assert row.error == "stale"
    assert row.progress_current == 11
    assert response.status == ReconstructionStatus.QUEUED


@pytest.mark.asyncio
async def test_resume_on_succeeded_is_refused_with_the_finished_job_reason() -> None:
    session = StubSession(row=StubRow(ReconstructionStatus.SUCCEEDED))

    with pytest.raises(HTTPException) as raised:
        await resume_reconstruction.fn(session=session, id=RECONSTRUCTION_ID)

    assert raised.value.status_code == 409
    assert "A finished job is not resumed" in raised.value.detail


@pytest.mark.asyncio
async def test_resume_on_a_working_status_is_refused() -> None:
    session = StubSession(row=StubRow(WORKING_STATUS))

    with pytest.raises(HTTPException) as raised:
        await resume_reconstruction.fn(session=session, id=RECONSTRUCTION_ID)

    assert raised.value.status_code == 409


def test_router_carries_pause_and_resume_and_no_retry() -> None:
    paths = {route.path for route in reconstructions.router.routes}

    assert "/reconstructions/{id:uuid}/pause" in paths
    assert "/reconstructions/{id:uuid}/resume" in paths
    assert "/reconstructions/{id:uuid}/retry" not in paths


@pytest.mark.asyncio
async def test_delete_on_a_missing_row_is_not_found() -> None:
    session = StubSession(row=None)

    with pytest.raises(NotFoundException):
        await delete_reconstruction.fn(session=session, id=RECONSTRUCTION_ID)


@pytest.mark.asyncio
async def test_delete_with_a_localization_map_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    row = StubRow(WORKING_STATUS)
    session = StubSession(row=row, localization_map_id=uuid4())
    stub_client = StubS3Client([])
    monkeypatch.setattr(reconstructions, "s3_client", stub_client)

    with pytest.raises(NotFoundException):
        await delete_reconstruction.fn(session=session, id=RECONSTRUCTION_ID)

    assert session.deleted_rows == []
    assert stub_client.deleted_batches == []


@pytest.mark.asyncio
async def test_delete_removes_the_artifact_prefix_and_the_row(monkeypatch: pytest.MonkeyPatch) -> None:
    row = StubRow(WORKING_STATUS)
    session = StubSession(row=row)
    keys = [f"{RECONSTRUCTION_ID}/features.h5", f"{RECONSTRUCTION_ID}/shards/features/00000/keypoints.h5"]
    stub_client = StubS3Client(keys)
    monkeypatch.setattr(reconstructions, "s3_client", stub_client)

    await delete_reconstruction.fn(session=session, id=RECONSTRUCTION_ID)

    assert stub_client.deleted_batches == [keys]
    assert session.deleted_rows == [row]


def test_tar_export_skips_shards_and_the_database_artifact(monkeypatch: pytest.MonkeyPatch) -> None:
    prefix = f"{RECONSTRUCTION_ID}/"
    keys = [
        (f"{prefix}global_descriptors.h5", 7),
        (f"{prefix}features.h5", 7),
        (f"{prefix}database.db", 7),
        (f"{prefix}pairs.txt", 7),
        (f"{prefix}shards/features/00000/marker.json", 7),
        (f"{prefix}shards/training/opq.marker.json", 7),
    ]
    monkeypatch.setattr(reconstructions, "get_storage", partial(StubStorage, keys))

    stream = BytesIO(b"".join(iter_reconstruction_tar(RECONSTRUCTION_ID, b"{}")))
    with tarfile.open(fileobj=stream) as tar:
        names = tar.getnames()

    assert names == ["metadata.json", "global_descriptors.h5", "features.h5", "pairs.txt"]
