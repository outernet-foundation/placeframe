"""A cancellation reaches the worker as a refused progress write, and stops it at the next tick."""

from __future__ import annotations

from collections.abc import Callable
from uuid import uuid4

import pytest
from placeframe_lease_server_client import ProgressUpdate, ReconstructionStatus
from reconstructor.progress_publisher import ReconstructionCancelled, ReconstructionPublisher


class RefusingFlusher:
    """Accepts writes until told the job is cancelled, then refuses them the way the lease server does."""

    def __init__(self) -> None:
        self.cancelled = False
        self.writes = 0

    def flush(self, reconstruction_id: object, update: ProgressUpdate, on_cancelled: Callable[[], None]) -> None:
        self.writes += 1
        if self.cancelled:
            on_cancelled()


def test_ticks_pass_until_a_write_is_refused() -> None:
    flusher = RefusingFlusher()
    publisher = ReconstructionPublisher(flusher, uuid4())
    publisher.set_phase(ReconstructionStatus.EXTRACTING_FEATURES, total=10)
    publisher.on_progress(1)
    assert not publisher.cancelled

    flusher.cancelled = True
    publisher._last_emit = 0.0  # noqa: SLF001  # pyright: ignore[reportPrivateUsage] -- defeat the 2 Hz throttle
    with pytest.raises(ReconstructionCancelled):
        publisher.on_progress(2)
    assert publisher.cancelled


def test_a_native_callback_tick_only_notes_the_cancellation() -> None:
    """Inside pycolmap's callbacks nothing may raise; the caller asks afterwards."""
    flusher = RefusingFlusher()
    flusher.cancelled = True
    publisher = ReconstructionPublisher(flusher, uuid4())
    publisher._status = ReconstructionStatus.RECONSTRUCTING  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
    publisher._progress_total = 5  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
    publisher._last_emit = 0.0  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
    publisher.on_progress(3, raise_if_cancelled=False)
    assert publisher.cancelled
    with pytest.raises(ReconstructionCancelled):
        publisher.raise_if_cancelled()


def test_set_phase_refuses_to_start_a_phase_once_cancelled() -> None:
    publisher = ReconstructionPublisher(RefusingFlusher(), uuid4())
    publisher.cancel()
    with pytest.raises(ReconstructionCancelled):
        publisher.set_phase(ReconstructionStatus.MATCHING_FEATURES, total=1)
