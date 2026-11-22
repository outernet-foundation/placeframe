from __future__ import annotations

import logging

import pytest
from gpu_orchestrator.main import get_localizer_address, get_state, patch_policy, require_managed_pair
from gpu_orchestrator.orchestrator import Orchestrator, QueueSample
from litestar import Litestar
from litestar.openapi.config import OpenAPIConfig
from litestar.testing import TestClient
from placeframe_common.litestar import create_litestar_app

from fakes import COMPOSE_PROJECT, FakeDockerClient, FakeContainer, boot_the_loop, install_orchestrator

COMPLETED_AT_STAMP = "2026-11-21T00:00:00+00:00"


@pytest.fixture
def booted(monkeypatch: pytest.MonkeyPatch) -> Orchestrator:
    events: list[str] = []
    orchestrator, _, _ = boot_the_loop(
        events,
        containers={
            "localizer": FakeContainer("localizer", "running", events),
            "reconstructor": FakeContainer("reconstructor", "exited", events),
        },
    )
    install_orchestrator(monkeypatch, orchestrator)
    return orchestrator


def make_test_client() -> TestClient[Litestar]:
    application = create_litestar_app(
        [get_localizer_address, get_state, patch_policy],
        OpenAPIConfig("Placeframe GPU Orchestrator", "0.1.0"),
        logging_config=None,
    )
    return TestClient(app=application)


def test_endpoints_before_bootstrap_raise_the_unconfigured_guard() -> None:
    # The app converts the unhandled guard RuntimeError into a bare 500 response,
    # so assert on the status the TestClient actually surfaces
    with make_test_client() as client:
        assert client.get("/localizer-address").status_code == 500
        assert client.get("/state").status_code == 500
        assert client.patch("/policy", json={}).status_code == 500


def test_localizer_address_non_null_answers_zero_retry(booted: Orchestrator) -> None:
    with make_test_client() as client:
        response = client.get("/localizer-address")

    assert response.status_code == 200
    assert response.json() == {"address": "http://localizer:8000", "retry_after_seconds": 0}
    assert booted.poke.is_set()


def test_localizer_address_null_answers_the_retry_hint(monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[str] = []
    orchestrator, _, _ = boot_the_loop(
        events,
        containers={
            "localizer": FakeContainer("localizer", "exited", events),
            "reconstructor": FakeContainer("reconstructor", "running", events),
        },
    )
    install_orchestrator(monkeypatch, orchestrator)
    with make_test_client() as client:
        response = client.get("/localizer-address")

    assert response.status_code == 200
    assert response.json() == {"address": None, "retry_after_seconds": 60}
    assert orchestrator.poke.is_set()


def test_state_reports_both_demand_signals_and_the_cached_sample(booted: Orchestrator) -> None:
    booted.queue_sample = QueueSample(queued=4, in_flight=1)
    booted.last_pass_at = COMPLETED_AT_STAMP
    with make_test_client() as client:
        # The address query is the heartbeat that activates localization demand
        assert client.get("/localizer-address").status_code == 200
        response = client.get("/state")

    assert response.status_code == 200
    body = response.json()
    assert body["running"] == ["localizer"]
    assert body["managed"] == ["localizer", "reconstructor"]
    assert body["localization_demand_active"] is True
    assert body["reconstruction_demand_active"] is True
    assert body["queued"] == 4
    assert body["in_flight"] == 1
    assert body["gpu_contended"] is True
    assert body["idle_window_seconds"] == 600
    assert body["poll_interval_seconds"] == 15
    assert body["last_pass_at"] == COMPLETED_AT_STAMP


def test_patch_policy_applies_valid_values_and_logs_old_to_new(
    booted: Orchestrator, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.INFO, logger="gpu_orchestrator.orchestrator"):
        with make_test_client() as client:
            response = client.patch("/policy", json={"idle_window_seconds": 120, "poll_interval_seconds": 30})

    assert response.status_code == 200
    assert response.json() == {"idle_window_seconds": 120, "poll_interval_seconds": 30}
    assert booted.state.idle_window_s == 120
    assert booted.state.poll_interval_s == 30
    assert "idle window old=600s new=120s" in caplog.text
    assert "poll interval old=15s new=30s" in caplog.text


def test_patch_policy_rejects_values_below_the_floors(booted: Orchestrator) -> None:
    with make_test_client() as client:
        idle = client.patch("/policy", json={"idle_window_seconds": 30})
        poll = client.patch("/policy", json={"poll_interval_seconds": 1})

    assert idle.status_code == 400
    assert poll.status_code == 400
    assert booted.state.idle_window_s == 600
    assert booted.state.poll_interval_s == 15


def test_require_managed_pair_accepts_the_pair_in_the_project() -> None:
    containers = {
        "localizer": FakeContainer("localizer", "created", []),
        "reconstructor": FakeContainer("reconstructor", "created", []),
    }

    require_managed_pair(FakeDockerClient(containers), COMPOSE_PROJECT)


def test_require_managed_pair_without_a_managed_container_raises() -> None:
    containers = {"localizer": FakeContainer("localizer", "created", [])}

    with pytest.raises(ValueError, match=r"no reconstructor container in compose project"):
        require_managed_pair(FakeDockerClient(containers), COMPOSE_PROJECT)


def test_require_managed_pair_ignores_foreign_project_containers() -> None:
    containers = {
        "localizer": FakeContainer("localizer", "created", [], project="placeframe-core-rocm"),
        "reconstructor": FakeContainer("reconstructor", "created", [], project="placeframe-core-rocm"),
    }

    with pytest.raises(ValueError, match=r"no localizer container in compose project placeframe-core-cuda"):
        require_managed_pair(FakeDockerClient(containers), COMPOSE_PROJECT)


def test_patch_policy_without_fields_changes_nothing(booted: Orchestrator) -> None:
    with make_test_client() as client:
        response = client.patch("/policy", json={})

    assert response.status_code == 200
    assert response.json() == {"idle_window_seconds": 600, "poll_interval_seconds": 15}
