from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import ClassVar, NamedTuple
from uuid import UUID, uuid4

import pytest
from typer.testing import CliRunner

from scripts import reconstruction
from scripts.reconstruction import app

TAR_BYTES = b"not-a-real-tar"
TAR_NAME = "reconstruction-office.tar"


class FakeApi:
    import_calls: ClassVar[list[ImportCall]] = []

    async def import_reconstruction_tar(
        self,
        *,
        data: tuple[str, bytes],
        allow_missing_capture_session: bool | None = None,
        _request_timeout: float | None = None,
    ) -> ImportedReconstruction:
        FakeApi.import_calls.append(
            ImportCall(
                data=data,
                allow_missing_capture_session=allow_missing_capture_session,
                request_timeout=_request_timeout,
            )
        )
        return ImportedReconstruction()


class ImportCall(NamedTuple):
    data: tuple[str, bytes]
    allow_missing_capture_session: bool | None
    request_timeout: float | None


class ImportedReconstruction:
    def __init__(self) -> None:
        self.id: UUID = uuid4()


@pytest.fixture(autouse=True)
def fake_api(monkeypatch: pytest.MonkeyPatch) -> None:
    FakeApi.import_calls.clear()
    monkeypatch.setattr(reconstruction, "authenticated_api_client", fake_authenticated_api_client)


def test_import_uploads_the_tar_as_a_standalone_map(tmp_path: Path) -> None:
    tar_path = tmp_path / TAR_NAME
    tar_path.write_bytes(TAR_BYTES)

    result = CliRunner().invoke(app, ["import", str(tar_path)])

    assert result.exit_code == 0, result.output
    assert "Imported reconstruction" in result.output
    assert FakeApi.import_calls == [
        ImportCall(
            data=(TAR_NAME, TAR_BYTES),
            allow_missing_capture_session=True,
            request_timeout=reconstruction.REQUEST_TIMEOUT,
        )
    ]


@asynccontextmanager
async def fake_authenticated_api_client() -> AsyncIterator[FakeApi]:
    yield FakeApi()
