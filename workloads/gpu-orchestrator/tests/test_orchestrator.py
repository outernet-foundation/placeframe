from __future__ import annotations

import asyncio
import logging
from asyncio import CancelledError
from contextlib import suppress
from threading import Event
from time import monotonic

import pytest
from gpu_orchestrator import orchestrator as orchestrator_module
from gpu_orchestrator.orchestrator import (
    LOCALIZATION_DRAIN_SECONDS,
    RECONSTRUCTOR_STOP_TIMEOUT_S,
    Orchestrator,
    QueueSample,
)
from httpx import ConnectError

from fakes import BlockingStopContainer, FakeContainer, SleepRecorder, boot_the_loop

LOOP_LOGGER = "gpu_orchestrator.orchestrator"


async def a_pass_completes(orchestrator: Orchestrator) -> None:
    # The loop stamps last_pass_at at the end of each pass
    deadline = monotonic() + 5.0
    while orchestrator.last_pass_at is None:
        assert monotonic() < deadline, "a reconcile pass did not complete"
        await asyncio.sleep(0.01)


async def start_the_loop(orchestrator: Orchestrator) -> asyncio.Task[None]:
    task = asyncio.create_task(orchestrator.run_forever())
    await a_pass_completes(orchestrator)
    return task


async def poke_for_a_pass(orchestrator: Orchestrator) -> None:
    orchestrator.last_pass_at = None
    orchestrator.poke.set()
    await a_pass_completes(orchestrator)


async def stop_the_loop(task: asyncio.Task[None]) -> None:
    task.cancel()
    with suppress(CancelledError):
        await task


def simulate_heartbeat(orchestrator: Orchestrator) -> None:
    # Loop tests simulate the demand signal without the HTTP surface
    orchestrator.record_heartbeat()


async def await_a_failed_pass(caplog: pytest.LogCaptureFixture) -> None:
    deadline = monotonic() + 5.0
    while not any("reconcile pass failed" in record.message for record in caplog.records):
        assert monotonic() < deadline, "a reconcile pass did not fail"
        await asyncio.sleep(0.01)


@pytest.mark.asyncio
async def test_the_first_pass_polls_and_converges_the_resting_state() -> None:
    events: list[str] = []
    orchestrator, http, _ = boot_the_loop(events)

    task = await start_the_loop(orchestrator)
    try:
        assert http.calls == 1
        assert http.urls == ["http://lease-server:8000/queue-state"]
        assert events == ["localizer:start"]
        assert orchestrator.last_pass_at is not None
    finally:
        await stop_the_loop(task)


@pytest.mark.asyncio
async def test_a_poke_pass_reuses_the_cached_queue_sample() -> None:
    events: list[str] = []
    orchestrator, http, _ = boot_the_loop(events)

    task = await start_the_loop(orchestrator)
    try:
        await poke_for_a_pass(orchestrator)
        assert http.calls == 1
        assert events == ["localizer:start"]
    finally:
        await stop_the_loop(task)


@pytest.mark.asyncio
async def test_the_poll_cadence_refetches_the_sample() -> None:
    events: list[str] = []
    orchestrator, http, clock = boot_the_loop(events)

    task = await start_the_loop(orchestrator)
    try:
        clock.advance(15)
        await poke_for_a_pass(orchestrator)
        assert http.calls == 2
    finally:
        await stop_the_loop(task)


@pytest.mark.asyncio
async def test_a_failed_poll_holds_the_last_sample(caplog: pytest.LogCaptureFixture) -> None:
    events: list[str] = []
    orchestrator, _, clock = boot_the_loop(
        events, script=[QueueSample(queued=2, in_flight=1), ConnectError("unreachable")]
    )

    with caplog.at_level(logging.INFO, logger=LOOP_LOGGER):
        task = await start_the_loop(orchestrator)
        try:
            clock.advance(15)
            await poke_for_a_pass(orchestrator)
        finally:
            await stop_the_loop(task)

    assert orchestrator.queue_sample == QueueSample(queued=2, in_flight=1)
    assert "queue-state poll failed" in caplog.text


@pytest.mark.asyncio
async def test_localization_demand_beats_queue_demand() -> None:
    events: list[str] = []
    orchestrator, _, _ = boot_the_loop(
        events,
        script=[QueueSample(queued=3, in_flight=0)],
        containers={
            "localizer": FakeContainer("localizer", "exited", events),
            "reconstructor": FakeContainer("reconstructor", "running", events),
        },
    )

    simulate_heartbeat(orchestrator)
    task = await start_the_loop(orchestrator)
    try:
        assert events == [
            f"reconstructor:stop(timeout={RECONSTRUCTOR_STOP_TIMEOUT_S})",
            "reconstructor:wait",
            "localizer:start",
        ]
    finally:
        await stop_the_loop(task)


@pytest.mark.asyncio
async def test_heartbeat_expiry_hands_the_slot_back_to_reconstruction(monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[str] = []
    monkeypatch.setattr(orchestrator_module, "sleep", SleepRecorder(events))
    busy = QueueSample(queued=3, in_flight=0)
    orchestrator, _, clock = boot_the_loop(events, script=[busy, busy])

    simulate_heartbeat(orchestrator)
    task = await start_the_loop(orchestrator)
    try:
        clock.advance(601)
        await poke_for_a_pass(orchestrator)
        assert events == [
            "localizer:start",
            f"sleep:{LOCALIZATION_DRAIN_SECONDS}",
            "localizer:stop",
            "localizer:wait",
            "reconstructor:start",
        ]
    finally:
        await stop_the_loop(task)


@pytest.mark.asyncio
async def test_in_flight_work_keeps_reconstruction_running() -> None:
    events: list[str] = []
    orchestrator, _, _ = boot_the_loop(events, script=[QueueSample(queued=0, in_flight=1)])

    task = await start_the_loop(orchestrator)
    try:
        assert events == ["reconstructor:start"]
    finally:
        await stop_the_loop(task)


@pytest.mark.asyncio
async def test_uncontended_passes_desire_both() -> None:
    events: list[str] = []
    orchestrator, _, _ = boot_the_loop(events, gpu_contended=False)

    task = await start_the_loop(orchestrator)
    try:
        assert events == ["localizer:start", "reconstructor:start"]
    finally:
        await stop_the_loop(task)


@pytest.mark.asyncio
async def test_held_out_demand_hint_logs_once_per_rising_edge(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    events: list[str] = []
    monkeypatch.setattr(orchestrator_module, "sleep", SleepRecorder(events))
    busy = QueueSample(queued=2, in_flight=0)
    orchestrator, _, clock = boot_the_loop(events, script=[busy, busy])

    with caplog.at_level(logging.INFO, logger=LOOP_LOGGER):
        simulate_heartbeat(orchestrator)
        task = await start_the_loop(orchestrator)
        try:
            clock.advance(601)
            await poke_for_a_pass(orchestrator)
            simulate_heartbeat(orchestrator)
            await poke_for_a_pass(orchestrator)
        finally:
            await stop_the_loop(task)

    hints = [record for record in caplog.records if "held-out GPU demand" in record.message]
    assert len(hints) == 2
    assert all("GPU_CONTENDED" in record.message for record in hints)
    assert "'reconstructor'" in hints[0].message


@pytest.mark.asyncio
async def test_a_pass_awaits_the_full_transition_before_returning(monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[str] = []
    monkeypatch.setattr(orchestrator_module, "sleep", SleepRecorder(events))
    entered = Event()
    release = Event()
    localizer = BlockingStopContainer("localizer", "running", events, entered, release)
    reconstructor = FakeContainer("reconstructor", "exited", events)
    orchestrator, _, _ = boot_the_loop(
        events,
        script=[QueueSample(queued=1, in_flight=0)],
        containers={"localizer": localizer, "reconstructor": reconstructor},
    )

    task = asyncio.create_task(orchestrator.run_forever())
    try:
        # Offload the blocking wait: waiting on the loop thread would starve the very
        # task this test is observing
        assert await asyncio.to_thread(entered.wait, 5)
        assert not task.done()

        release.set()
        await a_pass_completes(orchestrator)
        assert events == [
            f"sleep:{LOCALIZATION_DRAIN_SECONDS}",
            "localizer:stop",
            "localizer:wait",
            "reconstructor:start",
        ]
    finally:
        await stop_the_loop(task)


@pytest.mark.asyncio
async def test_run_forever_wakes_on_a_poke_before_the_poll_interval() -> None:
    events: list[str] = []
    orchestrator, _, _ = boot_the_loop(events, poll_interval_s=3600)

    task = await start_the_loop(orchestrator)
    try:
        orchestrator.last_pass_at = None
        simulate_heartbeat(orchestrator)
        await a_pass_completes(orchestrator)
    finally:
        await stop_the_loop(task)


@pytest.mark.asyncio
async def test_run_forever_logs_a_failed_pass_and_keeps_going(caplog: pytest.LogCaptureFixture) -> None:
    events: list[str] = []
    orchestrator, _, _ = boot_the_loop(events, script=[ValueError("boom")])

    with caplog.at_level(logging.INFO, logger=LOOP_LOGGER):
        task = asyncio.create_task(orchestrator.run_forever())
        try:
            await await_a_failed_pass(caplog)
            assert events == []

            await poke_for_a_pass(orchestrator)
            assert events == ["localizer:start"]
        finally:
            await stop_the_loop(task)

    failures = [record for record in caplog.records if "reconcile pass failed" in record.message]
    assert len(failures) == 1
