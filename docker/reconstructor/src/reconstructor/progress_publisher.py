from __future__ import annotations

import asyncio
from asyncio import AbstractEventLoop
from concurrent.futures import Future
from time import perf_counter
from typing import Any, Protocol
from uuid import UUID

import httpx
from core.reconstruction_metrics import PhaseTiming
from placeframe_api_client import DefaultApi, ProgressUpdate, ReconstructionStatus


class ProgressFlusher(Protocol):
    def flush(self, reconstruction_id: UUID, update: ProgressUpdate) -> None: ...


class AsyncProgressFlusher:
    def __init__(self, api: DefaultApi, loop: AbstractEventLoop) -> None:
        self._api = api
        self._loop = loop

    def flush(self, reconstruction_id: UUID, update: ProgressUpdate) -> None:
        future = asyncio.run_coroutine_threadsafe(
            self._api.update_progress(reconstruction_id, update),
            self._loop,
        )
        future.add_done_callback(_log_progress_failure)


class SyncProgressFlusher:
    def __init__(self, client: httpx.Client, base_url: str) -> None:
        self._client = client
        self._base_url = base_url

    def flush(self, reconstruction_id: UUID, update: ProgressUpdate) -> None:
        response = self._client.put(
            f"{self._base_url}/internal/leases/{reconstruction_id}/progress",
            json=update.model_dump(mode="json", exclude_none=False),
        )
        if response.status_code >= 400:
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

    @property
    def reconstruction_id(self) -> UUID:
        return self._reconstruction_id

    @property
    def phase_timings(self) -> list[PhaseTiming]:
        return self._phase_timings

    def set_phase(self, status: ReconstructionStatus, total: int | None = None) -> None:
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

    def on_progress(self, current: int, attempt: int = 1) -> None:
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

    def _flush(self) -> None:
        if self._status is None:
            return
        update = ProgressUpdate(
            status=self._status,
            progress_current=self._progress_current,
            progress_total=self._progress_total,
            progress_attempt=self._progress_attempt,
        )
        self._flusher.flush(self._reconstruction_id, update)


def _log_progress_failure(future: Future[Any]) -> None:
    exc = future.exception()
    if exc is not None:
        print(f"[progress write failed] {exc}")
