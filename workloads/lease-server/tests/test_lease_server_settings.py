from __future__ import annotations

import pytest
from lease_server.settings import Settings
from pydantic import ValidationError

BASE_ENV = {
    "POSTGRES_HOST": "pf-postgres",
    "DATABASE_NAME": "placeframe",
    "DATABASE_ORCHESTRATION_USER": "placeframe_orchestration_user",
    "DATABASE_ORCHESTRATION_USER_PASSWORD": "password",
}


@pytest.fixture(autouse=True)
def isolated_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name, value in BASE_ENV.items():
        monkeypatch.setenv(name, value)
    for name in ("LEASE_TIMEOUT_S", "LEASE_HEARTBEAT_CADENCE_S"):
        monkeypatch.delenv(name, raising=False)


def test_defaults_satisfy_the_boot_invariant() -> None:
    settings = Settings.model_validate({})

    assert settings.lease_timeout_s == 1800
    assert settings.lease_heartbeat_cadence_s == 60


def test_timeout_below_three_heartbeats_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Settings.model_validate({"lease_timeout_s": 179, "lease_heartbeat_cadence_s": 60})


def test_timeout_at_exactly_three_heartbeats_is_accepted() -> None:
    settings = Settings.model_validate({"lease_timeout_s": 180, "lease_heartbeat_cadence_s": 60})

    assert settings.lease_timeout_s == 180
