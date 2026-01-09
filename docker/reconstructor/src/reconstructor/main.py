from asyncio import CancelledError, run, sleep
from pathlib import Path
from signal import SIGTERM, signal
from typing import Any, NoReturn, cast

from common.token_manager import TokenManager
from plerion_api_client import ApiClient, ApiException, Configuration, DefaultApi, OrchestrationStatus

from .run_reconstruction import run_reconstruction
from .settings import get_settings

POLL_INTERVAL_SECONDS = 5.0

settings = get_settings()


async def worker_loop() -> None:
    print("Reconstructor Worker Started")

    auth = TokenManager(str(settings.auth_token_url), settings.auth_client_id, Path(settings.private_key_path))
    configuration = Configuration(host=str(settings.api_internal_url))

    async with ApiClient(configuration) as api_client:
        api = DefaultApi(api_client)
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

                lease_id = lease.reconstruction_id
                reconstruction_id = lease.reconstruction_id
                capture_id = lease.capture_session_id
                print(f"[{lease_id}] Acquired lease")

                try:
                    run_reconstruction(reconstruction_id, capture_id)
                    print(f"[{lease_id}] Reconstruction succeeded")

                    await api.complete_lease(lease_id, OrchestrationStatus.SUCCEEDED)

                except Exception as e:
                    print(f"[{lease_id}] Reconstruction failed: {e}")

                    await api.complete_lease(lease_id, OrchestrationStatus.FAILED)

            except CancelledError:
                print("Worker loop cancelled. Shutting down...")
                break
            except Exception as e:
                print(f"[Critical Worker Error] {e}")
                await sleep(POLL_INTERVAL_SECONDS)


def handle_sigterm(signum: int, frame: Any) -> NoReturn:
    raise CancelledError()


def main() -> None:
    # Register the signal handler for graceful Docker shutdowns
    signal(SIGTERM, handle_sigterm)

    try:
        # This is the single place where the event loop is started
        run(worker_loop())
    except (KeyboardInterrupt, CancelledError):
        # Silence the stack trace on exit
        pass

    print("Worker stopped.")
