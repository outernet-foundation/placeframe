import asyncio
import os
from asyncio import CancelledError, run, sleep
from signal import SIGTERM
from typing import NoReturn, cast
from uuid import UUID

from common.logging_config import configure_logging
from core.reconstruction_options import ReconstructionOptions as CoreReconstructionOptions
from placeframe_lease_server_client import (
    ApiClient,
    ApiException,
    Configuration,
    DefaultApi,
    FailLeaseRequest,
    LeaseResponse,
)
from placeframe_lease_server_client import ReconstructionMetrics as ClientReconstructionMetrics

from .metrics_builder import MetricsBuilder
from .progress_publisher import AsyncProgressFlusher, ReconstructionPublisher
from .run_reconstruction import load_models, run_reconstruction
from .settings import get_settings

configure_logging("reconstructor")

POLL_INTERVAL_SECONDS = 5.0

settings = get_settings()


async def worker_loop() -> None:
    print("Reconstructor Worker Started")

    configuration = Configuration(host=str(settings.lease_server_url))

    async with ApiClient(configuration) as api_client:
        api = DefaultApi(api_client)
        loop = asyncio.get_running_loop()
        active_lease_id: UUID | None = None
        eviction_task: asyncio.Task[None] | None = None

        # A spot eviction arrives as SIGTERM ~2 minutes before the node is reclaimed. Requeue the
        # in-flight lease so a fresh worker re-runs it, then exit; without this the job is orphaned
        # until the 30-minute reaper marks it failed. The task reference is held so it is not
        # garbage-collected before it runs.
        def on_sigterm() -> None:
            nonlocal eviction_task
            eviction_task = loop.create_task(_requeue_and_exit(api, active_lease_id))

        loop.add_signal_handler(SIGTERM, on_sigterm)

        while True:
            try:
                try:
                    lease = await api.request_lease()
                except ApiException as e:
                    status = cast(int | None, e.status)
                    if status == 404:
                        await sleep(POLL_INTERVAL_SECONDS)
                        continue
                    else:
                        print(f"[Critical Worker Error] Could not reach API: {e}")
                        await sleep(POLL_INTERVAL_SECONDS)
                        continue

                print(f"[{lease.reconstruction_id}] Acquired lease")
                active_lease_id = lease.reconstruction_id
                await _run_and_report(api, loop, lease)
                active_lease_id = None

            except CancelledError:
                print("Worker loop cancelled. Shutting down...")
                break
            except Exception as e:
                print(f"[Critical Worker Error] {e}")
                await sleep(POLL_INTERVAL_SECONDS)


async def _run_and_report(api: DefaultApi, loop: asyncio.AbstractEventLoop, lease: LeaseResponse) -> None:
    reconstruction_id = lease.reconstruction_id
    capture_id = lease.capture_session_id
    options = CoreReconstructionOptions.model_validate(lease.options.model_dump())

    publisher = ReconstructionPublisher(AsyncProgressFlusher(api, loop), reconstruction_id)
    metrics_builder = MetricsBuilder()

    try:
        # run_reconstruction is sync and CPU/GPU-bound; push it to a thread so the
        # event loop stays live for progress writes the publisher dispatches back.
        metrics = await loop.run_in_executor(
            None,
            run_reconstruction,
            reconstruction_id,
            capture_id,
            options,
            publisher,
            metrics_builder,
        )
        print(f"[{reconstruction_id}] Reconstruction succeeded")
        await api.succeed_lease(
            reconstruction_id,
            ClientReconstructionMetrics.model_validate(metrics.model_dump()),
        )
    except Exception as e:
        print(f"[{reconstruction_id}] Reconstruction failed: {e}")
        partial_metrics = ClientReconstructionMetrics.model_validate(metrics_builder.metrics.model_dump())
        await api.fail_lease(
            reconstruction_id,
            FailLeaseRequest(error=str(e), metrics=partial_metrics),
        )


async def _requeue_and_exit(api: DefaultApi, reconstruction_id: UUID | None) -> NoReturn:
    if reconstruction_id is not None:
        print(f"[{reconstruction_id}] Eviction (SIGTERM) received — requeuing lease")
        try:
            await api.requeue_lease(reconstruction_id)
        except ApiException as e:
            print(f"[{reconstruction_id}] Requeue on eviction failed: {e}")
    else:
        print("Eviction (SIGTERM) received while idle — exiting")

    os._exit(0)


def main() -> None:
    load_models()

    try:
        # This is the single place where the event loop is started
        run(worker_loop())
    except (KeyboardInterrupt, CancelledError):
        # Silence the stack trace on exit
        pass

    print("Worker stopped.")
