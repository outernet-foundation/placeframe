from __future__ import annotations

from collections.abc import Mapping
from threading import Event

import pytest
from gpu_orchestrator import main
from gpu_orchestrator.orchestrator import (
    COMPOSE_PROJECT_LABEL,
    COMPOSE_SERVICE_LABEL,
    BootState,
    Orchestrator,
    QueueSample,
)
from gpu_orchestrator.settings import Settings

SERVICE_LABEL_PREFIX = "com.docker.compose.service="
PROJECT_LABEL_PREFIX = "com.docker.compose.project="
COMPOSE_PROJECT = "placeframe-core-cuda"

BASE_VALUES = {
    "gpu_contended": True,
    "idle_window_s": 600,
    "poll_interval_s": 15,
    "retry_after_s": 60,
    "compose_project": COMPOSE_PROJECT,
    "lease_server_url": "http://lease-server:8000",
    "localizer_url": "http://localizer:8000",
}


class FakeContainer:
    def __init__(self, service_name: str, status: str, events: list[str], project: str = COMPOSE_PROJECT) -> None:
        self.service_name = service_name
        self.status = status
        self.events = events
        self.project = project
        self.name = f"{project}-{service_name}-1"
        self.attrs: dict[str, object] = {
            "Config": {
                "Labels": {
                    COMPOSE_SERVICE_LABEL: service_name,
                    COMPOSE_PROJECT_LABEL: project,
                }
            }
        }

    def start(self) -> None:
        self.events.append(f"{self.service_name}:start")
        self.status = "running"

    def stop(self, timeout: int | None = None) -> None:
        spelling = f"{self.service_name}:stop" if timeout is None else f"{self.service_name}:stop(timeout={timeout})"
        self.events.append(spelling)
        self.status = "exited"

    def wait(self) -> int:
        self.events.append(f"{self.service_name}:wait")
        return 0


class FakeContainerCollection:
    def __init__(self, containers: Mapping[str, FakeContainer]) -> None:
        self._containers = list(containers.values())

    def list(self, *, filters: dict[str, list[str]], **_options: object) -> list[FakeContainer]:
        service = None
        project = None
        for label in filters["label"]:
            if label.startswith(SERVICE_LABEL_PREFIX):
                service = label.removeprefix(SERVICE_LABEL_PREFIX)
            elif label.startswith(PROJECT_LABEL_PREFIX):
                project = label.removeprefix(PROJECT_LABEL_PREFIX)
            else:
                raise AssertionError(f"list() filtered on unexpected label {label!r}")
        matches = [container for container in self._containers if container.service_name == service]
        if project is not None:
            matches = [container for container in matches if container.project == project]
        return matches


class FakeDockerClient:
    def __init__(self, containers: Mapping[str, FakeContainer]) -> None:
        self.containers = FakeContainerCollection(containers)


class BlockingStopContainer(FakeContainer):
    def __init__(self, service_name: str, status: str, events: list[str], entered: Event, release: Event) -> None:
        super().__init__(service_name, status, events)
        self._entered = entered
        self._release = release

    def stop(self, timeout: int | None = None) -> None:
        self._entered.set()
        self._release.wait()
        super().stop(timeout)


class FakeQueueResponse:
    def __init__(self, payload: Mapping[str, int]) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> Mapping[str, int]:
        return self._payload


class FakeAsyncClient:
    def __init__(self, script: list[QueueSample | Exception] | None = None) -> None:
        self.calls = 0
        self.urls: list[str] = []
        self._script = list(script) if script is not None else []

    async def get(self, url: str) -> FakeQueueResponse:
        self.calls += 1
        self.urls.append(url)
        if self._script:
            outcome = self._script.pop(0)
            if isinstance(outcome, Exception):
                raise outcome
            return FakeQueueResponse({"queued": outcome.queued, "in_flight": outcome.in_flight})
        return FakeQueueResponse({"queued": 0, "in_flight": 0})


class SleepRecorder:
    def __init__(self, events: list[str]) -> None:
        self.events = events

    def __call__(self, seconds: float) -> None:
        self.events.append(f"sleep:{seconds}")


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def boot_the_loop(
    events: list[str],
    script: list[QueueSample | Exception] | None = None,
    containers: Mapping[str, FakeContainer] | None = None,
    **overrides: object,
) -> tuple[Orchestrator, FakeAsyncClient, FakeClock]:
    values: dict[str, object] = {**BASE_VALUES, **overrides}
    settings = Settings.model_validate(values)
    if containers is None:
        containers = {
            "localizer": FakeContainer("localizer", "exited", events),
            "reconstructor": FakeContainer("reconstructor", "exited", events),
        }
    http = FakeAsyncClient(script)
    clock = FakeClock()
    orchestrator = Orchestrator(
        BootState(
            docker=FakeDockerClient(containers),
            compose_project=COMPOSE_PROJECT,
            http=http,
            localizer_url=settings.localizer_url,
            lease_server_url=settings.lease_server_url,
            gpu_contended=settings.gpu_contended,
            retry_after_s=settings.retry_after_s,
            idle_window_s=settings.idle_window_s,
            poll_interval_s=settings.poll_interval_s,
        ),
        clock=clock,
    )
    return orchestrator, http, clock


def install_orchestrator(monkeypatch: pytest.MonkeyPatch, orchestrator: Orchestrator) -> None:
    monkeypatch.setattr(main, "_orchestrator", orchestrator)
