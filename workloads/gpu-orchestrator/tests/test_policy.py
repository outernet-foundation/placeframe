from __future__ import annotations

from gpu_orchestrator.orchestrator import QueueSample

from fakes import boot_the_loop

IDLE_WINDOW = 600


def test_localization_demand_expires_with_the_idle_window() -> None:
    orchestrator, _, clock = boot_the_loop([])
    assert orchestrator.localization_demand_active() is False
    orchestrator.record_heartbeat()
    assert orchestrator.localization_demand_active() is True
    clock.advance(IDLE_WINDOW)
    assert orchestrator.localization_demand_active() is True
    clock.advance(0.001)
    assert orchestrator.localization_demand_active() is False


def test_reconstruction_demand_counts_queued_and_in_flight() -> None:
    orchestrator, _, _ = boot_the_loop([])
    orchestrator.queue_sample = QueueSample(queued=1, in_flight=0)
    assert orchestrator.reconstruction_demand_active() is True
    orchestrator.queue_sample = QueueSample(queued=0, in_flight=1)
    assert orchestrator.reconstruction_demand_active() is True
    orchestrator.queue_sample = QueueSample(queued=0, in_flight=0)
    assert orchestrator.reconstruction_demand_active() is False
