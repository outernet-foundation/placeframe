from __future__ import annotations

from threading import Event, Thread

import pytest
from litestar import Litestar
from litestar.openapi.config import OpenAPIConfig
from litestar.testing import TestClient
from mode_switcher import main
from mode_switcher.main import (
    LOCALIZATION_DRAIN_SECONDS,
    LOCALIZER_URL_ENV,
    compose_project_of,
    current_mode,
    get_localizer_address,
    get_mode,
    initialize,
    localizer_address,
    set_mode,
    switch,
)
from placeframe_common.litestar import create_litestar_app

SERVICE_LABEL_PREFIX = "com.docker.compose.service="
PROJECT_LABEL_PREFIX = "com.docker.compose.project="
COMPOSE_PROJECT = "placeframe-core-cuda"


@pytest.fixture(autouse=True)
def localizer_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(LOCALIZER_URL_ENV, "http://localizer:8000")


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


class FakeOwnContainer:
    def __init__(self, labels: dict[str, str]) -> None:
        self.name = "own"
        self.status = "running"
        self.attrs: dict[str, object] = {"Config": {"Labels": labels}}


class FakeContainerCollection:
    def __init__(self, containers: dict[str, FakeContainer], project: str, own_container: FakeOwnContainer) -> None:
        self._containers = containers
        self._project = project
        self._own_container = own_container

    def get(self, _name: str) -> FakeOwnContainer:
        return self._own_container

    def list(self, *, filters: dict[str, list[str]], **_options: object) -> list[FakeContainer]:
        service = None
        for label in filters["label"]:
            if label.startswith(SERVICE_LABEL_PREFIX):
                service = label.removeprefix(SERVICE_LABEL_PREFIX)
            else:
                assert label == f"{PROJECT_LABEL_PREFIX}{self._project}", (
                    f"list() filtered on unexpected project label {label!r}"
                )
        container = self._containers.get(service or "")
        return [container] if container is not None else []


class FakeDockerClient:
    def __init__(
        self,
        containers: dict[str, FakeContainer],
        project: str = COMPOSE_PROJECT,
        own_labels: dict[str, str] | None = None,
    ) -> None:
        labels = own_labels if own_labels is not None else {"com.docker.compose.project": project}
        self.containers = FakeContainerCollection(containers, project, FakeOwnContainer(labels))


class SleepRecorder:
    def __init__(self, events: list[str]) -> None:
        self.events = events

    def __call__(self, seconds: float) -> None:
        self.events.append(f"sleep:{seconds}")


class BlockingStopContainer(FakeContainer):
    def __init__(self, service_name: str, status: str, events: list[str], entered: Event, release: Event) -> None:
        super().__init__(service_name, status, events)
        self._entered = entered
        self._release = release

    def stop(self) -> None:
        self._entered.set()
        self._release.wait()
        super().stop()


def initialize_switcher(
    events: list[str], localizer_status: str, reconstructor_status: str
) -> tuple[FakeContainer, FakeContainer]:
    localizer = FakeContainer("localizer", localizer_status, events)
    reconstructor = FakeContainer("reconstructor", reconstructor_status, events)
    initialize(FakeDockerClient({"localizer": localizer, "reconstructor": reconstructor}))
    return localizer, reconstructor


def make_test_client() -> TestClient[Litestar]:
    application = create_litestar_app(
        [get_mode, set_mode, get_localizer_address],
        OpenAPIConfig("Placeframe Mode Switcher", "0.1.0"),
        logging_config=None,
    )
    return TestClient(app=application)


def test_initialize_stops_the_non_default_when_both_running() -> None:
    events: list[str] = []
    initialize_switcher(events, localizer_status="running", reconstructor_status="running")

    assert events == ["reconstructor:stop"]


def test_initialize_honors_the_default(monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[str] = []
    monkeypatch.setattr(main, "DEFAULT_MODE", "reconstructor")
    initialize_switcher(events, localizer_status="running", reconstructor_status="running")

    assert events == ["localizer:stop"]


def test_initialize_starts_the_default_when_none_running() -> None:
    events: list[str] = []
    initialize_switcher(events, localizer_status="created", reconstructor_status="created")

    assert events == ["localizer:start"]


def test_initialize_adopts_the_single_running_container() -> None:
    events: list[str] = []
    initialize_switcher(events, localizer_status="exited", reconstructor_status="running")

    assert events == []


def test_initialize_without_containers_does_nothing() -> None:
    events: list[str] = []
    initialize(FakeDockerClient({}))

    assert events == []


def test_switch_from_localizer_drains_before_stop(monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[str] = []
    monkeypatch.setattr(main, "sleep", SleepRecorder(events))
    initialize_switcher(events, localizer_status="running", reconstructor_status="exited")

    assert switch("reconstructor") == "reconstructor"

    assert events == [
        f"sleep:{LOCALIZATION_DRAIN_SECONDS}",
        "localizer:stop",
        "localizer:wait",
        "reconstructor:start",
    ]


def test_switch_from_reconstructor_interrupts_immediately() -> None:
    events: list[str] = []
    initialize_switcher(events, localizer_status="exited", reconstructor_status="running")

    assert switch("localizer") == "localizer"

    assert events == ["reconstructor:stop", "reconstructor:wait", "localizer:start"]


def test_switch_to_running_target_is_a_no_op() -> None:
    events: list[str] = []
    initialize_switcher(events, localizer_status="running", reconstructor_status="exited")

    assert switch("localizer") == "localizer"
    assert events == []


def test_switch_stops_the_extra_when_both_running() -> None:
    events: list[str] = []
    _, reconstructor = initialize_switcher(events, localizer_status="running", reconstructor_status="exited")
    # External drift: the stopped GPU container is started outside the switcher
    reconstructor.start()

    assert switch("localizer") == "localizer"

    assert events == ["reconstructor:start", "reconstructor:stop", "reconstructor:wait"]


def test_switch_skips_stop_when_the_source_was_stopped_externally() -> None:
    events: list[str] = []
    localizer, _ = initialize_switcher(events, localizer_status="running", reconstructor_status="exited")
    # External drift: the running GPU container is stopped outside the switcher
    localizer.stop()

    assert switch("reconstructor") == "reconstructor"

    assert events == ["localizer:stop", "reconstructor:start"]


def test_switch_with_missing_target_container_raises() -> None:
    events: list[str] = []
    localizer = FakeContainer("localizer", "running", events)
    initialize(FakeDockerClient({"localizer": localizer}))

    with pytest.raises(ValueError, match="no reconstructor container"):
        switch("reconstructor")


def test_switch_clears_the_transition_marker_when_it_fails() -> None:
    events: list[str] = []
    localizer = FakeContainer("localizer", "running", events)
    initialize(FakeDockerClient({"localizer": localizer}))

    with pytest.raises(ValueError, match="no reconstructor container"):
        switch("reconstructor")

    assert current_mode() == "localizer"


def test_current_mode_adopts_the_single_running_container() -> None:
    events: list[str] = []
    initialize_switcher(events, localizer_status="exited", reconstructor_status="running")

    assert current_mode() == "reconstructor"
    assert events == []


def test_current_mode_reports_default_when_nothing_runs() -> None:
    events: list[str] = []
    localizer, _ = initialize_switcher(events, localizer_status="running", reconstructor_status="exited")
    # External drift: the running GPU container is stopped outside the switcher
    localizer.stop()

    assert current_mode() == "localizer"


def test_current_mode_reports_default_when_drift_starts_both() -> None:
    events: list[str] = []
    _, reconstructor = initialize_switcher(events, localizer_status="running", reconstructor_status="exited")
    # External drift: the stopped GPU container is started outside the switcher
    reconstructor.start()

    assert current_mode() == "localizer"


def test_current_mode_during_a_switch_reports_the_target_without_blocking(monkeypatch: pytest.MonkeyPatch) -> None:
    entered = Event()
    release = Event()
    events: list[str] = []
    monkeypatch.setattr(main, "sleep", SleepRecorder(events))
    localizer = BlockingStopContainer("localizer", "running", events, entered, release)
    reconstructor = FakeContainer("reconstructor", "exited", events)
    initialize(FakeDockerClient({"localizer": localizer, "reconstructor": reconstructor}))

    switching = Thread(target=switch, args=("reconstructor",))
    switching.start()
    assert entered.wait(timeout=5)

    # The switch holds _switch_lock for the whole stop/wait/start sequence; a mode
    # read during that window must answer the transition target, not block.
    readings: list[str] = []
    reading = Thread(target=lambda: readings.append(current_mode()))
    reading.start()
    reading.join(timeout=5)
    assert not reading.is_alive()
    assert readings == ["reconstructor"]

    release.set()
    switching.join(timeout=5)
    assert not switching.is_alive()


def test_compose_project_of_reads_the_own_container_label(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("mode_switcher.main.gethostname", lambda: "abc123")
    client = FakeDockerClient({}, own_labels={"com.docker.compose.project": "placeframe-core-rocm"})

    assert compose_project_of(client) == "placeframe-core-rocm"


def test_compose_project_of_without_the_label_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("mode_switcher.main.gethostname", lambda: "abc123")
    client = FakeDockerClient({}, own_labels={})

    with pytest.raises(ValueError, match=r"carries no com\.docker\.compose\.project label"):
        compose_project_of(client)


def test_localizer_address_when_running() -> None:
    events: list[str] = []
    initialize_switcher(events, localizer_status="running", reconstructor_status="exited")

    assert localizer_address() == "http://localizer:8000"


def test_localizer_address_when_stopped() -> None:
    events: list[str] = []
    initialize_switcher(events, localizer_status="exited", reconstructor_status="running")

    assert localizer_address() is None


def test_get_mode_endpoint() -> None:
    events: list[str] = []
    initialize_switcher(events, localizer_status="running", reconstructor_status="exited")
    with make_test_client() as client:
        response = client.get("/mode")

    assert response.status_code == 200
    assert response.json() == {"mode": "localizer"}


def test_post_mode_endpoint_switches(monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[str] = []
    monkeypatch.setattr(main, "sleep", SleepRecorder(events))
    initialize_switcher(events, localizer_status="running", reconstructor_status="exited")
    with make_test_client() as client:
        response = client.post("/mode", json={"mode": "reconstructor"})

    assert response.status_code == 201
    assert response.json() == {"mode": "reconstructor"}
    assert events == [
        f"sleep:{LOCALIZATION_DRAIN_SECONDS}",
        "localizer:stop",
        "localizer:wait",
        "reconstructor:start",
    ]


def test_post_mode_endpoint_rejects_unknown_mode() -> None:
    events: list[str] = []
    initialize_switcher(events, localizer_status="running", reconstructor_status="exited")
    with make_test_client() as client:
        response = client.post("/mode", json={"mode": "hibernation"})

    assert response.status_code == 400


def test_localizer_address_endpoint_non_null() -> None:
    events: list[str] = []
    initialize_switcher(events, localizer_status="running", reconstructor_status="exited")
    with make_test_client() as client:
        response = client.get("/localizer-address")

    assert response.status_code == 200
    assert response.json() == {"address": "http://localizer:8000"}


def test_localizer_address_endpoint_null() -> None:
    events: list[str] = []
    initialize_switcher(events, localizer_status="exited", reconstructor_status="running")
    with make_test_client() as client:
        response = client.get("/localizer-address")

    assert response.status_code == 200
    assert response.json() == {"address": None}
