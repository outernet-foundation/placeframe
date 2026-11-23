from __future__ import annotations

import pytest
from gpu_orchestrator import orchestrator as orchestrator_module
from gpu_orchestrator.orchestrator import (
    LOCALIZATION_DRAIN_SECONDS,
    MANAGED_SERVICES,
    RECONSTRUCTOR_STOP_TIMEOUT_S,
    Orchestrator,
)

from fakes import FakeContainer, SleepRecorder, boot_the_loop


def boot_actuation(
    events: list[str], localizer_status: str, reconstructor_status: str
) -> tuple[Orchestrator, FakeContainer, FakeContainer]:
    localizer = FakeContainer("localizer", localizer_status, events)
    reconstructor = FakeContainer("reconstructor", reconstructor_status, events)
    orchestrator, _, _ = boot_the_loop(events, containers={"localizer": localizer, "reconstructor": reconstructor})
    return orchestrator, localizer, reconstructor


def test_converge_to_reconstructor_drains_before_the_interactive_stop(monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[str] = []
    monkeypatch.setattr(orchestrator_module, "sleep", SleepRecorder(events))
    orchestrator, _, _ = boot_actuation(events, localizer_status="running", reconstructor_status="exited")

    orchestrator.converge(frozenset({"reconstructor"}))

    assert events == [
        f"sleep:{LOCALIZATION_DRAIN_SECONDS}",
        "localizer:stop",
        "localizer:wait",
        "reconstructor:start",
    ]


def test_converge_to_localizer_stops_the_batch_class_with_an_explicit_timeout() -> None:
    events: list[str] = []
    orchestrator, _, _ = boot_actuation(events, localizer_status="exited", reconstructor_status="running")

    orchestrator.converge(frozenset({"localizer"}))

    assert events == [
        f"reconstructor:stop(timeout={RECONSTRUCTOR_STOP_TIMEOUT_S})",
        "reconstructor:wait",
        "localizer:start",
    ]


def test_converge_on_the_desired_state_is_a_no_op() -> None:
    events: list[str] = []
    orchestrator, _, _ = boot_actuation(events, localizer_status="running", reconstructor_status="exited")

    orchestrator.converge(frozenset({"localizer"}))

    assert events == []


def test_converge_stops_the_extra_when_drift_started_both() -> None:
    events: list[str] = []
    orchestrator, _, reconstructor = boot_actuation(events, localizer_status="running", reconstructor_status="exited")
    reconstructor.start()

    orchestrator.converge(frozenset({"localizer"}))

    assert events == [
        "reconstructor:start",
        f"reconstructor:stop(timeout={RECONSTRUCTOR_STOP_TIMEOUT_S})",
        "reconstructor:wait",
    ]


def test_converge_repairs_an_externally_stopped_container() -> None:
    events: list[str] = []
    orchestrator, localizer, _ = boot_actuation(events, localizer_status="running", reconstructor_status="exited")
    localizer.stop()

    orchestrator.converge(frozenset({"localizer"}))

    assert events == ["localizer:stop", "localizer:start"]


def test_converge_uncontended_starts_both() -> None:
    events: list[str] = []
    orchestrator, _, _ = boot_actuation(events, localizer_status="created", reconstructor_status="created")

    orchestrator.converge(MANAGED_SERVICES)

    assert events == ["localizer:start", "reconstructor:start"]


def test_converge_with_a_missing_desired_container_raises() -> None:
    events: list[str] = []
    localizer = FakeContainer("localizer", "running", events)
    orchestrator, _, _ = boot_the_loop(events, containers={"localizer": localizer})

    with pytest.raises(ValueError, match="no reconstructor container"):
        orchestrator.converge(frozenset({"reconstructor"}))


def test_running_services_reports_the_running_subset() -> None:
    events: list[str] = []
    orchestrator, _, _ = boot_actuation(events, localizer_status="running", reconstructor_status="exited")

    assert orchestrator.running_services() == {"localizer"}
