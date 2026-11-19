from __future__ import annotations

import pytest
from litestar import Litestar
from litestar.openapi.config import OpenAPIConfig
from litestar.testing import TestClient
from mode_switcher import docker_lifecycle
from mode_switcher.docker_lifecycle import LOCALIZATION_DRAIN_SECONDS, ModeSwitcher
from mode_switcher.routers.mode import router as mode_router
from mode_switcher.settings import Mode
from placeframe_common.litestar import create_litestar_app

SERVICE_LABEL_PREFIX = "com.docker.compose.service="


class FakeContainer:
    def __init__(self, service_name: str, status: str, events: list[str]) -> None:
        self.service_name = service_name
        self.status = status
        self.events = events

    def start(self) -> None:
        self.events.append(f"{self.service_name}:start")
        self.status = "running"

    def stop(self) -> None:
        self.events.append(f"{self.service_name}:stop")
        self.status = "exited"

    def wait(self) -> int:
        self.events.append(f"{self.service_name}:wait")
        return 0


class FakeContainerCollection:
    def __init__(self, containers: dict[str, FakeContainer]) -> None:
        self._containers = containers

    def list(self, *, filters: dict[str, list[str]], **_options: object) -> list[FakeContainer]:
        for label in filters["label"]:
            if label.startswith(SERVICE_LABEL_PREFIX):
                service = label.removeprefix(SERVICE_LABEL_PREFIX)
                container = self._containers.get(service)
                return [container] if container is not None else []
        return []


class FakeDockerClient:
    def __init__(self, containers: dict[str, FakeContainer]) -> None:
        self.containers = FakeContainerCollection(containers)


class SleepRecorder:
    def __init__(self, events: list[str]) -> None:
        self.events = events

    def __call__(self, seconds: float) -> None:
        self.events.append(f"sleep:{seconds}")


def make_switcher(
    events: list[str], localizer_status: str, reconstructor_status: str, default_mode: Mode = "localization"
) -> ModeSwitcher:
    localizer = FakeContainer("localizer", localizer_status, events)
    reconstructor = FakeContainer("reconstructor", reconstructor_status, events)
    return ModeSwitcher(FakeDockerClient({"localizer": localizer, "reconstructor": reconstructor}), default_mode)


def make_test_client(events: list[str], localizer_status: str, reconstructor_status: str) -> TestClient[Litestar]:
    openapi_config = OpenAPIConfig("Placeframe Mode Switcher", "0.1.0")
    app = create_litestar_app([mode_router], openapi_config, logging_config=None)
    app.state.mode_switcher = make_switcher(events, localizer_status, reconstructor_status)
    return TestClient(app=app)


def test_switch_from_localization_drains_before_stop(monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[str] = []
    monkeypatch.setattr(docker_lifecycle, "sleep", SleepRecorder(events))
    switcher = make_switcher(events, localizer_status="running", reconstructor_status="exited")

    assert switcher.reconcile() == "localization"
    assert switcher.switch("reconstruction") == "reconstruction"

    assert events == [
        f"sleep:{LOCALIZATION_DRAIN_SECONDS}",
        "localizer:stop",
        "localizer:wait",
        "reconstructor:start",
    ]


def test_switch_from_reconstruction_interrupts_immediately() -> None:
    events: list[str] = []
    switcher = make_switcher(events, localizer_status="exited", reconstructor_status="running")

    assert switcher.reconcile() == "reconstruction"
    assert switcher.switch("localization") == "localization"

    assert events == ["reconstructor:stop", "reconstructor:wait", "localizer:start"]


def test_switch_to_current_mode_is_a_no_op() -> None:
    events: list[str] = []
    switcher = make_switcher(events, localizer_status="running", reconstructor_status="exited")

    assert switcher.reconcile() == "localization"
    assert switcher.switch("localization") == "localization"
    assert events == []


def test_switch_without_running_source_container_skips_stop(monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[str] = []
    monkeypatch.setattr(docker_lifecycle, "sleep", SleepRecorder(events))
    switcher = make_switcher(
        events, localizer_status="created", reconstructor_status="created", default_mode="reconstruction"
    )

    assert switcher.switch("localization") == "localization"
    assert events == ["localizer:start"]


def test_switch_with_missing_target_container_raises() -> None:
    events: list[str] = []
    localizer = FakeContainer("localizer", "running", events)
    switcher = ModeSwitcher(FakeDockerClient({"localizer": localizer}), "localization")

    with pytest.raises(ValueError, match="no reconstructor container"):
        switcher.switch("reconstruction")


def test_reconcile_adopts_the_single_running_container() -> None:
    events: list[str] = []
    switcher = make_switcher(events, localizer_status="exited", reconstructor_status="running")

    assert switcher.reconcile() == "reconstruction"
    assert switcher.mode == "reconstruction"
    assert events == []


def test_reconcile_with_both_running_stops_the_non_default() -> None:
    events: list[str] = []
    switcher = make_switcher(events, localizer_status="running", reconstructor_status="running")

    assert switcher.reconcile() == "localization"
    assert events == ["reconstructor:stop"]


def test_reconcile_with_both_running_honors_default_mode() -> None:
    events: list[str] = []
    switcher = make_switcher(
        events, localizer_status="running", reconstructor_status="running", default_mode="reconstruction"
    )

    assert switcher.reconcile() == "reconstruction"
    assert events == ["localizer:stop"]


def test_reconcile_with_none_running_starts_the_default() -> None:
    events: list[str] = []
    switcher = make_switcher(events, localizer_status="created", reconstructor_status="created")

    assert switcher.reconcile() == "localization"
    assert events == ["localizer:start"]


def test_reconcile_without_containers_reports_default() -> None:
    events: list[str] = []
    switcher = ModeSwitcher(FakeDockerClient({}), "localization")

    assert switcher.reconcile() == "localization"
    assert events == []


def test_localizer_address_when_running() -> None:
    events: list[str] = []
    switcher = make_switcher(events, localizer_status="running", reconstructor_status="exited")

    assert switcher.localizer_address() == "http://localizer:8000"


def test_localizer_address_when_stopped() -> None:
    events: list[str] = []
    switcher = make_switcher(events, localizer_status="exited", reconstructor_status="running")

    assert switcher.localizer_address() is None


def test_get_mode_endpoint() -> None:
    events: list[str] = []
    with make_test_client(events, localizer_status="running", reconstructor_status="exited") as client:
        response = client.get("/mode")

    assert response.status_code == 200
    assert response.json() == {"mode": "localization"}


def test_post_mode_endpoint_switches(monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[str] = []
    monkeypatch.setattr(docker_lifecycle, "sleep", SleepRecorder(events))
    with make_test_client(events, localizer_status="running", reconstructor_status="exited") as client:
        response = client.post("/mode", json={"mode": "reconstruction"})

    assert response.status_code == 201
    assert response.json() == {"mode": "reconstruction"}
    assert events == [
        f"sleep:{LOCALIZATION_DRAIN_SECONDS}",
        "localizer:stop",
        "localizer:wait",
        "reconstructor:start",
    ]


def test_post_mode_endpoint_rejects_unknown_mode() -> None:
    events: list[str] = []
    with make_test_client(events, localizer_status="running", reconstructor_status="exited") as client:
        response = client.post("/mode", json={"mode": "hibernation"})

    assert response.status_code == 400


def test_localizer_address_endpoint_non_null() -> None:
    events: list[str] = []
    with make_test_client(events, localizer_status="running", reconstructor_status="exited") as client:
        response = client.get("/localizer-address")

    assert response.status_code == 200
    assert response.json() == {"address": "http://localizer:8000"}


def test_localizer_address_endpoint_null() -> None:
    events: list[str] = []
    with make_test_client(events, localizer_status="exited", reconstructor_status="running") as client:
        response = client.get("/localizer-address")

    assert response.status_code == 200
    assert response.json() == {"address": None}
