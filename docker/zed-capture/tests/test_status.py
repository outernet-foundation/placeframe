from dataclasses import dataclass
from uuid import UUID

import pytest

from src.main import app
from src.routers import status as status_module


@dataclass(frozen=True)
class _FakeState:
    capture_id: UUID | None
    last_exception: str | None


def test_status_default_shape():
    result = status_module.compute_status()
    assert result.current_capture_id is None
    assert result.last_exception is None
    assert isinstance(result.disk_free_bytes, int)
    assert result.disk_free_bytes > 0
    assert result.uptime_s >= 0.0
    assert isinstance(result.version, str)


def test_status_reflects_actor_state(monkeypatch: pytest.MonkeyPatch):
    test_id = UUID("12345678-1234-5678-1234-567812345678")
    monkeypatch.setattr(
        status_module.zed,
        "state",
        lambda: _FakeState(capture_id=test_id, last_exception="boom"),
    )

    result = status_module.compute_status()
    assert result.current_capture_id == test_id
    assert result.last_exception == "boom"


# Regression: Litestar's OpenAPI generator ignored `pydantic.WithJsonSchema`
# markers, so `disk_free_bytes` silently emitted as int32 in generated clients.
# Fixed by routing through `Field(json_schema_extra=...)`. This test fails if
# the emitted schema loses `format: int64`.
def test_disk_free_bytes_emits_int64_format():
    schema = app.openapi_schema.to_schema()
    assert schema["components"]["schemas"]["ZedStatus"]["properties"]["disk_free_bytes"] == {
        "type": "integer",
        "format": "int64",
    }
