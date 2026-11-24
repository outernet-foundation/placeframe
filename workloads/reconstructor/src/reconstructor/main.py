import asyncio
import os
from asyncio import CancelledError, run, sleep
from dataclasses import dataclass
from logging import getLogger
from signal import SIGTERM
from typing import NoReturn
from uuid import UUID

from httpx import HTTPError
from placeframe_common.boto_clients import create_s3_client
from placeframe_common.logging_config import configure_logging
from placeframe_core.reconstruction_options import ReconstructionOptions as CoreReconstructionOptions
from placeframe_core.reconstruction_metrics import ReconstructionMetrics as CoreReconstructionMetrics
from placeframe_lease_server_client import (
    ApiClient,
    ApiException,
    Configuration,
    DefaultApi,
    ErrorRequest,
    FailLeaseRequest,
    Lease,
    PreemptRequest,
)

from placeframe_lease_server_client.models.reconstruction_metrics import ReconstructionMetrics
from .progress_publisher import AsyncProgressFlusher, LeaseLostError, ReconstructionPublisher
from .run_reconstruction import load_models, run_reconstruction
from .settings import get_settings
from .uploader import ArtifactUploader, compute_options_hash, delete_shard_prefix

configure_logging("reconstructor")

logger = getLogger(__name__)

POLL_INTERVAL_SECONDS = 5.0
SIGTERM_DRAIN_TIMEOUT_SECONDS = 55.0

settings = get_settings()


@dataclass
class WorkerState:
    active_lease_id: UUID | None = None
    active_lease_attempt: int | None = None
    active_uploader: ArtifactUploader | None = None
    eviction_task: asyncio.Task[None] | None = None


async def _run_worker() -> None:
    logger.info("Reconstructor worker started")

    configuration = Configuration(host=str(settings.lease_server_url))

    async with ApiClient(configuration) as api_client:
        api = DefaultApi(api_client)
        loop = asyncio.get_running_loop()
        state = WorkerState()

        # Preempt the in-flight lease and exit because a spot eviction SIGTERM lands ~2 minutes before node reclamation
        loop.add_signal_handler(SIGTERM, _on_sigterm, api, state, loop)

        await worker_loop(api, loop, state)


def _on_sigterm(api: DefaultApi, state: WorkerState, loop: asyncio.AbstractEventLoop) -> None:
    if state.eviction_task is not None:
        return
    state.eviction_task = loop.create_task(
        _preempt_and_exit(api, state.active_lease_id, state.active_lease_attempt, state.active_uploader)
    )


async def _preempt_and_exit(
    api: DefaultApi,
    reconstruction_id: UUID | None,
    lease_attempt: int | None,
    uploader: ArtifactUploader | None,
) -> NoReturn:
    if reconstruction_id is None or lease_attempt is None or uploader is None:
        logger.info("Eviction (SIGTERM) received while idle, exiting")
        os._exit(0)

    logger.info("Eviction (SIGTERM) received, preempting lease reconstruction_id=%s", reconstruction_id)
    loop = asyncio.get_running_loop()
    drain_completed = await loop.run_in_executor(None, uploader.drain, SIGTERM_DRAIN_TIMEOUT_SECONDS)
    if not drain_completed:
        logger.info("Uploader drain timed out, exiting with unwritten shard markers")

    try:
        await api.preempt_lease(reconstruction_id, PreemptRequest(lease_attempt=lease_attempt))
    except Exception as e:
        logger.info("Preempt on eviction did not complete reconstruction_id=%s: %s", reconstruction_id, e)

    os._exit(0)


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

        # Run the reconstruction in a thread pool so the event loop keeps the lease alive through the heartbeat task
        reconstruction_options = CoreReconstructionOptions.model_validate(lease.options.model_dump())
        uploader = ArtifactUploader(
            create_s3_client(
                s3_endpoint_url=settings.s3_endpoint_url,
                s3_access_key=settings.s3_access_key,
                s3_secret_key=settings.s3_secret_key,
            ),
            bucket=settings.reconstructions_bucket,
            reconstruction_id=lease.reconstruction_id,
            pipeline_version=os.environ["RECONSTRUCTOR_SHA"],
            options_hash=compute_options_hash(reconstruction_options),
        )
        publisher = ReconstructionPublisher(
            AsyncProgressFlusher(api, loop), lease.reconstruction_id, lease.lease_attempt
        )
        heartbeat_task = loop.create_task(_lease_heartbeat(publisher))
        metrics: CoreReconstructionMetrics | None = None
        error_text: str | None = None
        try:
            state.active_uploader = uploader
            state.active_lease_id = lease.reconstruction_id
            state.active_lease_attempt = lease.lease_attempt
            metrics = await loop.run_in_executor(
                None,
                run_reconstruction,
                lease.capture_session_id,
                reconstruction_options,
                publisher,
                uploader,
            )
        except LeaseLostError as e:
            logger.info("Lease lost, abandoning job reconstruction_id=%s: %s", lease.reconstruction_id, e)
            continue
        except Exception as e:
            error_text = str(e)
        finally:
            state.active_uploader = None
            state.active_lease_id = None
            state.active_lease_attempt = None
            heartbeat_task.cancel()

        # Report the result of the reconstruction to the lease server
        try:
            publisher.raise_if_lease_lost()

            if error_text is not None:
                logger.info("Reconstruction raised reconstruction_id=%s: %s", lease.reconstruction_id, error_text)
                await api.error_lease(lease.reconstruction_id, lease.lease_attempt, ErrorRequest(error=error_text))
                continue

            assert metrics is not None
            client_metrics = ReconstructionMetrics.model_validate(metrics.model_dump())

            if not metrics.successful:
                error = "Reconstruction produced no model"
                logger.info("Reconstruction failed reconstruction_id=%s: %s", lease.reconstruction_id, error)
                await api.fail_lease(
                    lease.reconstruction_id,
                    lease.lease_attempt,
                    FailLeaseRequest(error=error, metrics=client_metrics),
                )
                continue

            logger.info("Reconstruction succeeded reconstruction_id=%s", lease.reconstruction_id)
            await api.succeed_lease(lease.reconstruction_id, lease.lease_attempt, client_metrics)
            await _delete_shards_after_success(loop, lease.reconstruction_id)
        except LeaseLostError as e:
            logger.info("Lease lost, abandoning job reconstruction_id=%s: %s", lease.reconstruction_id, e)
        except (ApiException, HTTPError) as e:
            logger.info("Failed to report reconstruction result reconstruction_id=%s: %s", lease.reconstruction_id, e)


async def _delete_shards_after_success(loop: asyncio.AbstractEventLoop, reconstruction_id: UUID) -> None:
    logger.info("Deleting shard artifacts reconstruction_id=%s", reconstruction_id)
    s3_client = create_s3_client(
        s3_endpoint_url=settings.s3_endpoint_url,
        s3_access_key=settings.s3_access_key,
        s3_secret_key=settings.s3_secret_key,
    )
    try:
        await loop.run_in_executor(
            None, delete_shard_prefix, s3_client, settings.reconstructions_bucket, reconstruction_id
        )
    except Exception as e:
        logger.info("Shard cleanup failed reconstruction_id=%s: %s", reconstruction_id, e)


async def _lease_heartbeat(publisher: ReconstructionPublisher) -> None:
    while True:
        await sleep(settings.lease_heartbeat_cadence_s)
        publisher.heartbeat()


def main() -> None:
    load_models()

    try:
        # This is the single place where the event loop is started
        run(_run_worker())
    except (KeyboardInterrupt, CancelledError):
        # Silence the stack trace on exit
        pass

    logger.info("Worker stopped")
