from __future__ import annotations

import asyncio
from asyncio import AbstractEventLoop
from collections.abc import Callable
from concurrent.futures import Future
from functools import partial
from json import loads
from time import perf_counter
from typing import Any, Protocol
from uuid import UUID

import httpx
from placeframe_core.reconstruction_metrics import PhaseTiming
from placeframe_lease_server_client import ApiException, DefaultApi, ProgressUpdate, ReconstructionStatus

from .lease_client_types import api_exception_body, api_exception_status

RefusalCallback = Callable[[str], None]
REFUSAL_STATUSES = (404, 409)


class LeaseLostError(Exception):
    pass


class ProgressFlusher(Protocol):
    def flush(self, reconstruction_id: UUID, update: ProgressUpdate, on_refusal: RefusalCallback) -> None: ...


class AsyncProgressFlusher:
    def __init__(self, api: DefaultApi, loop: AbstractEventLoop) -> None:
        self._api = api
        self._loop = loop

    def flush(self, reconstruction_id: UUID, update: ProgressUpdate, on_refusal: RefusalCallback) -> None:
        future = asyncio.run_coroutine_threadsafe(
            self._api.update_progress(reconstruction_id, update),
            self._loop,
        )
        future.add_done_callback(partial(_handle_flush_result, on_refusal))


class SyncProgressFlusher:
    def __init__(self, client: httpx.Client, base_url: str) -> None:
        self._client = client
        self._base_url = base_url

    def flush(self, reconstruction_id: UUID, update: ProgressUpdate, on_refusal: RefusalCallback) -> None:
        response = self._client.put(
            f"{self._base_url}/leases/{reconstruction_id}/progress",
            json=update.model_dump(mode="json", exclude_none=False),
        )
        if response.status_code in REFUSAL_STATUSES:
            on_refusal(_reason_from_body(response.status_code, response.text))
            return
        if response.status_code >= 400:
            print(f"[progress write failed] HTTP {response.status_code} {response.text}")


class ReconstructionPublisher:
    def __init__(self, flusher: ProgressFlusher, reconstruction_id: UUID, lease_attempt: int) -> None:
        self._flusher = flusher
        self._reconstruction_id = reconstruction_id
        self._lease_attempt = lease_attempt
        self._status: ReconstructionStatus | None = None
        self._progress_total: int | None = None
        self._progress_current: int | None = None
        self._progress_attempt: int | None = None
        self._last_emit = 0.0
        self._phase_start: float | None = None
        self._phase_timings: list[PhaseTiming] = []
        self._lease_lost_reason: str | None = None

    @property
    def reconstruction_id(self) -> UUID:
        return self._reconstruction_id

    @property
    def lease_attempt(self) -> int:
        return self._lease_attempt

    @property
    def phase_timings(self) -> list[PhaseTiming]:
        return self._phase_timings

    def set_phase(self, status: ReconstructionStatus, total: int | None = None) -> None:
        self.raise_if_lease_lost()
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

    def heartbeat(self) -> None:
        self._flush()

    def _flush(self) -> None:
        if self._status is None:
            return
        update = ProgressUpdate(
            status=self._status,
            progress_current=self._progress_current,
            progress_total=self._progress_total,
            progress_attempt=self._progress_attempt,
            lease_attempt=self._lease_attempt,
        )
        self._flusher.flush(self._reconstruction_id, update, self._mark_lease_lost)

    def raise_if_lease_lost(self) -> None:
        if self._lease_lost_reason is not None:
            raise LeaseLostError(self._lease_lost_reason)

    def _mark_lease_lost(self, reason: str) -> None:
        if self._lease_lost_reason is None:
            self._lease_lost_reason = reason
            print(f"[lease lost] reason={reason}")


def _handle_flush_result(on_refusal: RefusalCallback, future: Future[Any]) -> None:
    exception = future.exception()
    if exception is None:
        return
    if not isinstance(exception, ApiException):
        _log_flush_failure(exception)
        return
    status = api_exception_status(exception)
    if status not in REFUSAL_STATUSES:
        _log_flush_failure(exception)
        return
    on_refusal(_reason_from_body(status, api_exception_body(exception)))


def _log_flush_failure(exception: BaseException) -> None:
    print(f"[progress write failed] {exception}")


def _reason_from_body(status_code: int, body: str | None) -> str:
    if status_code == 404:
        return "not-found"
    if body is None:
        return "refused"
    try:
        return str(loads(body)["reason"])
    except (ValueError, KeyError):
        return "refused"
