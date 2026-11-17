import asyncio
import os
from asyncio import CancelledError, run, sleep
from dataclasses import dataclass
from logging import getLogger
from signal import SIGTERM
from typing import NoReturn
from uuid import UUID

from httpx import HTTPError
from placeframe_common.logging_config import configure_logging
from placeframe_core.reconstruction_options import ReconstructionOptions as CoreReconstructionOptions
from placeframe_core.reconstruction_metrics import ReconstructionMetrics as CoreReconstructionMetrics
from placeframe_lease_server_client import (
    ApiClient,
    ApiException,
    Configuration,
    DefaultApi,
    FailLeaseRequest,
    Lease,
)

from placeframe_lease_server_client.models.reconstruction_metrics import ReconstructionMetrics
from .progress_publisher import AsyncProgressFlusher, ReconstructionPublisher
from .run_reconstruction import load_models, run_reconstruction
from .settings import get_settings

configure_logging("reconstructor")

logger = getLogger(__name__)

POLL_INTERVAL_SECONDS = 5.0

settings = get_settings()


@dataclass
class WorkerState:
    active_lease_id: UUID | None = None
    eviction_task: asyncio.Task[None] | None = None


async def _run_worker() -> None:
    logger.info("Reconstructor worker started")

    configuration = Configuration(host=str(settings.lease_server_url))

    async with ApiClient(configuration) as api_client:
        api = DefaultApi(api_client)
        loop = asyncio.get_running_loop()
        state = WorkerState()

        # A spot eviction arrives as SIGTERM ~2 minutes before the node is reclaimed. Requeue the
        # in-flight lease so a fresh worker re-runs it, then exit; without this the job is orphaned
        # until the 30-minute reaper marks it failed. The task reference is held on state so it is
        # not garbage-collected before it runs.
        loop.add_signal_handler(SIGTERM, _on_sigterm, api, state, loop)

        await worker_loop(api, loop, state)


async def worker_loop(api: DefaultApi, loop: asyncio.AbstractEventLoop, state: WorkerState) -> None:
    while True:
        # Request a lease from the server. If none is available, sleep for a while and try again.
        lease: Lease | None = None
        try:
            response = await api.request_lease()
            lease = response.lease
        except (ApiException, HTTPError) as e:
            logger.info("request_lease failed: %s", e)

        if lease is None:
            await sleep(POLL_INTERVAL_SECONDS)
            continue

        # Run the reconstruction in a thread pool so it does not block the event loop. The lease is
        # marked active so that if a SIGTERM arrives, the lease can be requeued.
        metrics_or_error: CoreReconstructionMetrics | str = ""
        try:
            state.active_lease_id = lease.reconstruction_id
            metrics_or_error = await loop.run_in_executor(
                None,
                run_reconstruction,
                lease.reconstruction_id,
                lease.capture_session_id,
                CoreReconstructionOptions.model_validate(lease.options.model_dump()),
                ReconstructionPublisher(AsyncProgressFlusher(api, loop), lease.reconstruction_id),
            )
        except Exception as e:
            metrics_or_error = str(e)
        finally:
            state.active_lease_id = None

        # Report the result of the reconstruction to the lease serve
        try:
            if isinstance(metrics_or_error, str):
                logger.info("Reconstruction failed reconstruction_id=%s: %s", lease.reconstruction_id, metrics_or_error)
                await api.fail_lease(
                    lease.reconstruction_id,
                    FailLeaseRequest(error=metrics_or_error),
                )
                continue

            metrics = ReconstructionMetrics.model_validate(metrics_or_error.model_dump())

            if not metrics_or_error.successful:
                error = "Reconstruction produced no model"
                logger.info("Reconstruction failed reconstruction_id=%s: %s", lease.reconstruction_id, error)
                await api.fail_lease(
                    lease.reconstruction_id,
                    FailLeaseRequest(error="Reconstruction produced no model", metrics=metrics),
                )
                continue

            logger.info("Reconstruction succeeded reconstruction_id=%s", lease.reconstruction_id)
            await api.succeed_lease(
                lease.reconstruction_id,
                metrics,
            )
        except (ApiException, HTTPError) as e:
            logger.info("Failed to report reconstruction result reconstruction_id=%s: %s", lease.reconstruction_id, e)


def _on_sigterm(api: DefaultApi, state: WorkerState, loop: asyncio.AbstractEventLoop) -> None:
    if state.eviction_task is not None:
        return
    state.eviction_task = loop.create_task(_requeue_and_exit(api, state.active_lease_id))


async def _requeue_and_exit(api: DefaultApi, reconstruction_id: UUID | None) -> NoReturn:
    if reconstruction_id is not None:
        logger.info("Eviction (SIGTERM) received, requeuing lease reconstruction_id=%s", reconstruction_id)
        try:
            await api.requeue_lease(reconstruction_id)
        except Exception as e:
            logger.info("Requeue on eviction failed reconstruction_id=%s: %s", reconstruction_id, e)
    else:
        logger.info("Eviction (SIGTERM) received while idle, exiting")

    os._exit(0)


def main() -> None:
    load_models()

    try:
        # This is the single place where the event loop is started
        run(_run_worker())
    except (KeyboardInterrupt, CancelledError):
        # Silence the stack trace on exit
        pass

    logger.info("Worker stopped")
