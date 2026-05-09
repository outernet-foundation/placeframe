from __future__ import annotations

import asyncio
from asyncio import AbstractEventLoop
from concurrent.futures import Future
from time import perf_counter
from typing import Any
from uuid import UUID

from placeframe_api_client import DefaultApi, ProgressUpdate, ReconstructionStatus


class ReconstructionPublisher:
    def __init__(self, api: DefaultApi, loop: AbstractEventLoop, reconstruction_id: UUID) -> None:
        self._api = api
        self._loop = loop
        self._reconstruction_id = reconstruction_id
        self._status: ReconstructionStatus | None = None
        self._progress_total: int | None = None
        self._progress_current: int | None = None
        self._progress_attempt: int | None = None
        self._last_emit = 0.0

    def set_phase(self, status: ReconstructionStatus, total: int | None = None) -> None:
        self._status = status
        self._progress_total = total
        self._progress_current = 0 if total is not None else None
        self._progress_attempt = 1 if total is not None else None
        self._flush()
        self._last_emit = perf_counter()
        print(f"[{status.value}]" + (f" 0/{total}" if total is not None else ""))

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
        future = asyncio.run_coroutine_threadsafe(
            self._api.update_progress(self._reconstruction_id, update),
            self._loop,
        )
        future.add_done_callback(_log_progress_failure)


def _log_progress_failure(future: Future[Any]) -> None:
    exc = future.exception()
    if exc is not None:
        print(f"[progress write failed] {exc}")
