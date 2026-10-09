from __future__ import annotations

import asyncio
from asyncio import AbstractEventLoop
from collections.abc import Callable
from concurrent.futures import Future
from threading import Event
from time import perf_counter
from typing import cast, Any, Protocol
from uuid import UUID

import httpx
from core.reconstruction_metrics import PhaseTiming
from placeframe_lease_server_client import ApiException, DefaultApi, ProgressUpdate, ReconstructionStatus

# The lease server answers a progress write for a cancelled reconstruction with this status. It is
# the only way the worker hears of a cancellation: it never reads the row, it only writes to it.
CANCELLED_STATUS_CODE = 409


def is_cancelled_refusal(e: ApiException) -> bool:
    """True when a lease-server write was refused because the row is CANCELLED."""
    return cast(int | None, e.status) == CANCELLED_STATUS_CODE


class ReconstructionCancelled(Exception):
    """Raised on the worker thread, at a progress tick, once the job has been cancelled."""


class ProgressFlusher(Protocol):
    def flush(self, reconstruction_id: UUID, update: ProgressUpdate, on_cancelled: Callable[[], None]) -> None: ...


class AsyncProgressFlusher:
    def __init__(self, api: DefaultApi, loop: AbstractEventLoop) -> None:
        self._api = api
        self._loop = loop

    def flush(self, reconstruction_id: UUID, update: ProgressUpdate, on_cancelled: Callable[[], None]) -> None:
        future = asyncio.run_coroutine_threadsafe(
            self._api.update_progress(reconstruction_id, update),
            self._loop,
        )

        def done(completed: Future[Any]) -> None:
            exc = completed.exception()
            if isinstance(exc, ApiException) and is_cancelled_refusal(exc):
                on_cancelled()
            elif exc is not None:
                print(f"[progress write failed] {exc}")

        future.add_done_callback(done)


class SyncProgressFlusher:
    def __init__(self, client: httpx.Client, base_url: str) -> None:
        self._client = client
        self._base_url = base_url

    def flush(self, reconstruction_id: UUID, update: ProgressUpdate, on_cancelled: Callable[[], None]) -> None:
        response = self._client.put(
            f"{self._base_url}/leases/{reconstruction_id}/progress",
            json=update.model_dump(mode="json", exclude_none=False),
        )
        if response.status_code == CANCELLED_STATUS_CODE:
            on_cancelled()
        elif response.status_code >= 400:
            print(f"[progress write failed] HTTP {response.status_code} {response.text}")


class ReconstructionPublisher:
    def __init__(self, flusher: ProgressFlusher, reconstruction_id: UUID) -> None:
        self._flusher = flusher
        self._reconstruction_id = reconstruction_id
        self._status: ReconstructionStatus | None = None
        self._progress_total: int | None = None
        self._progress_current: int | None = None
        self._progress_attempt: int | None = None
        self._last_emit = 0.0
        self._phase_start: float | None = None
        self._phase_timings: list[PhaseTiming] = []
        # Set from whichever thread sees the lease server refuse a write; read on the worker thread.
        self._cancelled = Event()

    @property
    def reconstruction_id(self) -> UUID:
        return self._reconstruction_id

    @property
    def cancelled(self) -> bool:
        return self._cancelled.is_set()

    def cancel(self) -> None:
        self._cancelled.set()

    def raise_if_cancelled(self) -> None:
        """Abandon the job if it was cancelled: called at progress ticks, and after phases whose
        progress is reported from somewhere the exception could not propagate."""
        if self._cancelled.is_set():
            raise ReconstructionCancelled(f"reconstruction {self._reconstruction_id} was cancelled")

    @property
    def phase_timings(self) -> list[PhaseTiming]:
        return self._phase_timings

    def set_phase(self, status: ReconstructionStatus, total: int | None = None) -> None:
        self.raise_if_cancelled()
        now = perf_counter()
        self._close_active_phase(now)
        self._phase_start = now
        self._status = status
        self._progress_total = total
        self._progress_current = 0 if total is not None else None
        self._progress_attempt = 1 if total is not None else None
        self._flush()
        self._last_emit = now
        print(f"[{status.value}]" + (f" 0/{total}" if total is not None else ""))

    def finalize_timings(self) -> None:
        self._close_active_phase(perf_counter())
        self._phase_start = None

    def _close_active_phase(self, now: float) -> None:
        if self._status is None or self._phase_start is None:
            return
        self._phase_timings.append(PhaseTiming(phase=self._status.value, duration_seconds=now - self._phase_start))

    def on_progress(self, current: int, attempt: int = 1, *, raise_if_cancelled: bool = True) -> None:
        """Report a tick. `raise_if_cancelled=False` is for ticks delivered from inside native code
        (pycolmap's mapping callbacks), where a Python exception cannot propagate; the caller checks
        raise_if_cancelled() itself once the native call returns."""
        if self._progress_total is None or self._status is None:
            return
        self._progress_current = current
        self._progress_attempt = attempt
        print(f"[{self._status.value}] {current}/{self._progress_total}")
        now = perf_counter()
        # Throttle API flushes to ~2 Hz; the per-tick stdout above is unthrottled.
        if now - self._last_emit >= 0.5:
            self._flush()
            self._last_emit = now
        if raise_if_cancelled:
            self.raise_if_cancelled()

    def _flush(self) -> None:
        if self._status is None:
            return
        update = ProgressUpdate(
            status=self._status,
            progress_current=self._progress_current,
            progress_total=self._progress_total,
            progress_attempt=self._progress_attempt,
        )
        self._flusher.flush(self._reconstruction_id, update, self.cancel)
