import asyncio
from asyncio import CancelledError, run, sleep
from pathlib import Path
from signal import SIGTERM, signal
from typing import Any, NoReturn, cast

from common.token_manager import TokenManager
from core.reconstruction_options import ReconstructionOptions as CoreReconstructionOptions
from placeframe_api_client import (
    ApiClient,
    ApiException,
    Configuration,
    DefaultApi,
    FailLeaseRequest,
    LeaseResponse,
)
from placeframe_api_client import ReconstructionMetrics as ClientReconstructionMetrics

from .metrics_builder import MetricsBuilder
from .progress_publisher import ReconstructionPublisher
from .run_reconstruction import load_models, run_reconstruction
from .settings import get_settings

POLL_INTERVAL_SECONDS = 5.0

settings = get_settings()


async def worker_loop() -> None:
    print("Reconstructor Worker Started")

    auth = TokenManager(str(settings.auth_token_url), settings.auth_client_id, Path(settings.private_key_path))
    configuration = Configuration(host=str(settings.api_internal_url))

    async with ApiClient(configuration) as api_client:
        api = DefaultApi(api_client)
        loop = asyncio.get_running_loop()

        while True:
            try:
                token = await auth.get_token()
                configuration.access_token = token
                cast(dict[Any, Any], api_client.default_headers)["Authorization"] = f"Bearer {token}"

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
                await _run_and_report(api, loop, lease)

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

    publisher = ReconstructionPublisher(api, loop, reconstruction_id)
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


def handle_sigterm(signum: int, frame: Any) -> NoReturn:
    raise CancelledError()


def main() -> None:
    load_models()

    # Register the signal handler for graceful Docker shutdowns
    signal(SIGTERM, handle_sigterm)

    try:
        # This is the single place where the event loop is started
        run(worker_loop())
    except (KeyboardInterrupt, CancelledError):
        # Silence the stack trace on exit
        pass

    print("Worker stopped.")
