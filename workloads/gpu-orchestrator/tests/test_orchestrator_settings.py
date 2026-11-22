from __future__ import annotations

import logging

import pytest
from gpu_orchestrator.settings import IDLE_WINDOW_FLOOR_S, POLL_INTERVAL_FLOOR_S, Settings

BASE_VALUES = {
    "compose_project": "placeframe-core-cuda",
    "lease_server_url": "http://lease-server:8000",
    "localizer_url": "http://localizer:8000",
}
ENV_NAMES = ("GPU_CONTENDED", "GPU_IDLE_WINDOW_S", "GPU_POLL_INTERVAL_S", "GPU_RETRY_AFTER_SECONDS")


@pytest.fixture(autouse=True)
def clean_gpu_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (*ENV_NAMES, "LEASE_SERVER_URL", "LOCALIZER_URL"):
        monkeypatch.delenv(name, raising=False)


def build(**overrides: object) -> Settings:
    values: dict[str, object] = {**BASE_VALUES, **overrides}
    return Settings.model_validate(values)


def test_defaults_match_the_values_grammar() -> None:
    settings = build()

    assert settings.gpu_contended is True
    assert settings.idle_window_s == 600
    assert settings.poll_interval_s == 15
    assert settings.retry_after_s == 60


def test_env_names_map_to_the_values_grammar(monkeypatch: pytest.MonkeyPatch) -> None:
    for name, value in (
        ("GPU_CONTENDED", "false"),
        ("GPU_IDLE_WINDOW_S", "120"),
        ("GPU_POLL_INTERVAL_S", "30"),
        ("GPU_RETRY_AFTER_SECONDS", "90"),
        ("COMPOSE_PROJECT_NAME", "placeframe-core-rocm"),
        ("LEASE_SERVER_URL", "http://lease-server:9000"),
        ("LOCALIZER_URL", "http://localizer:9000"),
    ):
        monkeypatch.setenv(name, value)

    settings = Settings.model_validate({})

    assert settings.gpu_contended is False
    assert settings.idle_window_s == 120
    assert settings.poll_interval_s == 30
    assert settings.retry_after_s == 90
    assert settings.compose_project == "placeframe-core-rocm"
    assert settings.lease_server_url == "http://lease-server:9000"
    assert settings.localizer_url == "http://localizer:9000"


def test_idle_window_below_the_floor_clamps_with_an_error_log(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.ERROR, logger="gpu_orchestrator.settings"):
        settings = build(idle_window_s=10)

    assert settings.idle_window_s == IDLE_WINDOW_FLOOR_S
    assert "GPU_IDLE_WINDOW_S=10" in caplog.text


def test_poll_interval_below_the_floor_clamps_with_an_error_log(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.ERROR, logger="gpu_orchestrator.settings"):
        settings = build(poll_interval_s=1)

    assert settings.poll_interval_s == POLL_INTERVAL_FLOOR_S
    assert "GPU_POLL_INTERVAL_S=1" in caplog.text


def test_values_at_the_floors_are_kept() -> None:
    settings = build(idle_window_s=IDLE_WINDOW_FLOOR_S, poll_interval_s=POLL_INTERVAL_FLOOR_S)

    assert settings.idle_window_s == IDLE_WINDOW_FLOOR_S
    assert settings.poll_interval_s == POLL_INTERVAL_FLOOR_S
