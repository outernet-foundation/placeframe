from __future__ import annotations

import io
import json
import tarfile
from asyncio import run
from datetime import UTC, datetime
from typing import BinaryIO, ClassVar
from uuid import UUID, uuid4

import pytest
from litestar.exceptions import HTTPException
from litestar.status_codes import HTTP_409_CONFLICT, HTTP_422_UNPROCESSABLE_ENTITY
from placeframe_core.reconstruction_manifest import MANIFEST_VERSION, Manifest
from placeframe_core.reconstruction_metrics import ReconstructionMetrics
from placeframe_core.reconstruction_options import ReconstructionOptions
from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession
from src.routers import reconstructions
from src.routers.reconstructions import (
    QueuedReconstructionRow,
    ReconstructionReadWithQueue,
    import_reconstruction_tar,
)

from datamodels.public_dtos import ReconstructionRead
from datamodels.public_tables import (
    CaptureSession,
    DeviceType,
    LocalizationMap,
    Reconstruction,
    ReconstructionStatus,
)

NOW = datetime(2026, 11, 13, tzinfo=UTC)
ARTIFACTS = {"features.h5": b"features", "sfm_model/frame_poses.npz": b"poses"}
SYNCED_MAPS: list[UUID] = []


class FakeStorage:
    uploaded: ClassVar[list[str]] = []
    deleted_prefixes: ClassVar[list[str]] = []

    def upload_fileobj(self, bucket: str, key: str, fileobj: BinaryIO, content_type: str) -> None:
        fileobj.read()
        FakeStorage.uploaded.append(key)

    def delete_prefix(self, bucket: str, prefix: str) -> None:
        FakeStorage.deleted_prefixes.append(prefix)


class FakeSession:
    def __init__(
        self,
        *,
        reconstruction_rows: dict[UUID, Reconstruction] | None = None,
        capture_session_rows: dict[UUID, CaptureSession] | None = None,
    ) -> None:
        self.reconstruction_rows = reconstruction_rows or {}
        self.capture_session_rows = capture_session_rows or {}
        self.added: list[Row] = []

    async def get(
        self, model: type[CaptureSession | Reconstruction], identity: UUID
    ) -> CaptureSession | Reconstruction | None:
        rows = self.reconstruction_rows if model is Reconstruction else self.capture_session_rows
        return rows.get(identity)

    def add(self, instance: Row) -> None:
        self.added.append(instance)

    async def flush(self) -> None:
        # Fill in the server defaults a real flush would set on new rows
        for row in self.added:
            if row.id is None:
                row.id = uuid4()
            if row.created_at is None:
                row.created_at = NOW
                row.updated_at = NOW
            if isinstance(row, Reconstruction) and row.requeue_count is None:
                row.requeue_count = 0

    async def execute(self, statement: Select[QueuedReconstructionRow]) -> FakeResult:
        row = next(instance for instance in self.added if isinstance(instance, Reconstruction))
        return FakeResult(row)


Row = CaptureSession | Reconstruction | LocalizationMap


class FakeResult:
    def __init__(self, row: Reconstruction) -> None:
        self.row = row

    def one(self) -> QueuedReconstructionRow:
        return self.row, None, None


class UploadRequest:
    def __init__(self, data: UploadedTar) -> None:
        self.data = data


class UploadedTar:
    def __init__(self, content: bytes, filename: str) -> None:
        self.file = io.BytesIO(content)
        self.filename = filename


@pytest.fixture(autouse=True)
def recording_fakes(monkeypatch: pytest.MonkeyPatch) -> None:
    FakeStorage.uploaded.clear()
    FakeStorage.deleted_prefixes.clear()
    SYNCED_MAPS.clear()
    monkeypatch.setattr(reconstructions, "get_storage", fake_get_storage)
    monkeypatch.setattr(reconstructions, "sync_camera_positions", fake_sync_camera_positions)


def test_capture_on_this_backend_takes_the_reconstruction() -> None:
    capture = existing_capture()
    session = FakeSession(capture_session_rows={capture.id: capture})
    reconstruction = build_reconstruction(capture_session_id=capture.id)

    result = import_tar(session, reconstruction)

    assert result.id == reconstruction.id
    assert result.status == ReconstructionStatus.SUCCEEDED
    assert result.capture_session_id == capture.id
    assert {type(row) for row in session.added} == {Reconstruction}
    assert sorted(FakeStorage.uploaded) == sorted(f"{reconstruction.id}/{name}" for name in ARTIFACTS)
    assert SYNCED_MAPS == []


def test_allowed_missing_capture_still_prefers_the_capture_on_this_backend() -> None:
    capture = existing_capture()
    session = FakeSession(capture_session_rows={capture.id: capture})
    reconstruction = build_reconstruction(capture_session_id=capture.id)

    result = import_tar(session, reconstruction, allow_missing_capture_session=True)

    assert result.capture_session_id == capture.id
    assert {type(row) for row in session.added} == {Reconstruction}
    assert SYNCED_MAPS == []


@pytest.mark.parametrize(
    ("named", "phrase"),
    [(uuid4(), "names capture session"), (None, "names no capture session")],
    ids=["absent", "unnamed"],
)
def test_missing_capture_is_refused_before_anything_is_written(named: UUID | None, phrase: str) -> None:
    session = FakeSession()
    reconstruction = build_reconstruction(capture_session_id=named)

    with pytest.raises(HTTPException) as excinfo:
        import_tar(session, reconstruction)

    detail = str(excinfo.value.detail)
    assert excinfo.value.status_code == HTTP_422_UNPROCESSABLE_ENTITY
    assert phrase in detail
    assert "allow_missing_capture_session=true" in detail
    if named is not None:
        assert str(named) in detail
    assert session.added == []
    assert FakeStorage.uploaded == []
    assert FakeStorage.deleted_prefixes == []


@pytest.mark.parametrize("named", [uuid4(), None], ids=["absent", "unnamed"])
def test_allowed_missing_capture_imports_standalone(named: UUID | None) -> None:
    session = FakeSession()
    reconstruction = build_reconstruction(capture_session_id=named)

    result = import_tar(session, reconstruction, allow_missing_capture_session=True)

    stand_in, row, map_row = session.added
    assert isinstance(stand_in, CaptureSession)
    assert isinstance(row, Reconstruction)
    assert isinstance(map_row, LocalizationMap)

    # Compare with the JSON-form values, because the generated *_from_dto constructors dump in JSON mode
    assert stand_in.device_type == DeviceType.ZED.value
    assert map_row.reconstruction_id == str(reconstruction.id)

    assert stand_in.name == "reconstruction-office"
    assert result.capture_session_id == stand_in.id
    assert row.capture_session_id == stand_in.id
    assert (map_row.position_x, map_row.position_y, map_row.position_z) == (0.0, 0.0, 0.0)
    assert (map_row.rotation_x, map_row.rotation_y, map_row.rotation_z, map_row.rotation_w) == (
        0.0,
        0.0,
        0.0,
        1.0,
    )
    assert [map_row.id] == SYNCED_MAPS
    assert sorted(FakeStorage.uploaded) == sorted(f"{reconstruction.id}/{name}" for name in ARTIFACTS)


def test_existing_reconstruction_conflicts() -> None:
    capture = existing_capture()
    reconstruction = build_reconstruction(capture_session_id=capture.id)
    session = FakeSession(
        capture_session_rows={capture.id: capture},
        reconstruction_rows={reconstruction.id: Reconstruction(id=reconstruction.id)},
    )

    with pytest.raises(HTTPException) as excinfo:
        import_tar(session, reconstruction)

    assert excinfo.value.status_code == HTTP_409_CONFLICT
    assert FakeStorage.uploaded == []


def existing_capture() -> CaptureSession:
    return CaptureSession(
        id=uuid4(),
        created_at=NOW,
        updated_at=NOW,
        recorded_at=NOW,
        name="office",
        device_type=DeviceType.ZED,
        size_bytes=1,
    )


def build_reconstruction(*, capture_session_id: UUID | None) -> ReconstructionRead:
    manifest = Manifest(options=ReconstructionOptions(), metrics=ReconstructionMetrics())
    return ReconstructionRead(
        created_at=NOW,
        updated_at=NOW,
        status=ReconstructionStatus.SUCCEEDED,
        requeue_count=0,
        manifest=manifest.model_dump(mode="json"),
        manifest_version=MANIFEST_VERSION,
        id=uuid4(),
        capture_session_id=capture_session_id,
    )


def import_tar(
    session: FakeSession, reconstruction: ReconstructionRead, *, allow_missing_capture_session: bool = False
) -> ReconstructionReadWithQueue:
    tar_manifest = {
        "tar_version": reconstructions.TAR_VERSION,
        "reconstruction": reconstruction.model_dump(mode="json"),
    }
    members = {"metadata.json": json.dumps(tar_manifest).encode(), **ARTIFACTS}
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w") as tar:
        for name, content in members.items():
            info = tarfile.TarInfo(name)
            info.size = len(content)
            tar.addfile(info, io.BytesIO(content))

    upload = UploadRequest(UploadedTar(buffer.getvalue(), "reconstruction-office.tar"))
    return run(
        import_reconstruction_tar.fn(session, upload, allow_missing_capture_session=allow_missing_capture_session)
    )


def fake_get_storage() -> FakeStorage:
    return FakeStorage()


async def fake_sync_camera_positions(session: AsyncSession, row: LocalizationMap) -> None:
    SYNCED_MAPS.append(row.id)
