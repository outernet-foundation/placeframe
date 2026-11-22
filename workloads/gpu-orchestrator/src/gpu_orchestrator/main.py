from __future__ import annotations

from asyncio import create_task, to_thread

from docker import DockerClient, from_env
from httpx import AsyncClient
from litestar import Litestar, get, patch
from litestar.exceptions import HTTPException
from litestar.openapi.config import OpenAPIConfig
from litestar.openapi.spec import Server
from placeframe_common.litestar import create_litestar_app
from placeframe_common.logging_config import configure_logging
from pydantic import BaseModel

from .orchestrator import (
    COMPOSE_PROJECT_LABEL,
    COMPOSE_SERVICE_LABEL,
    MANAGED_SERVICES,
    QUEUE_POLL_TIMEOUT_S,
    BootState,
    Orchestrator,
)
from .settings import IDLE_WINDOW_FLOOR_S, POLL_INTERVAL_FLOOR_S, Settings

configure_logging("gpu-orchestrator")

openapi_config = OpenAPIConfig(
    "Placeframe GPU Orchestrator",
    "0.1.0",
    servers=[Server(url="http://gpu-orchestrator:8000")],
)


class StateReport(BaseModel):
    running: list[str]
    managed: list[str]
    localization_demand_active: bool
    reconstruction_demand_active: bool
    queued: int
    in_flight: int
    gpu_contended: bool
    idle_window_seconds: int
    poll_interval_seconds: int
    last_pass_at: str | None


class LocalizerAddressResponse(BaseModel):
    address: str | None
    retry_after_seconds: int


class PolicyUpdate(BaseModel):
    idle_window_seconds: int | None = None
    poll_interval_seconds: int | None = None


class PolicyResponse(BaseModel):
    idle_window_seconds: int
    poll_interval_seconds: int


_orchestrator: Orchestrator | None = None


@get("/localizer-address")
async def get_localizer_address() -> LocalizerAddressResponse:
    orchestrator = _orchestrator_or_raise()
    orchestrator.record_heartbeat()
    address = await to_thread(orchestrator.localizer_address)
    return LocalizerAddressResponse(
        address=address,
        retry_after_seconds=0 if address is not None else orchestrator.state.retry_after_s,
    )


@get("/state")
async def get_state() -> StateReport:
    orchestrator = _orchestrator_or_raise()
    running = await to_thread(orchestrator.running_services)
    return StateReport(
        running=sorted(running),
        managed=sorted(MANAGED_SERVICES),
        localization_demand_active=orchestrator.localization_demand_active(),
        reconstruction_demand_active=orchestrator.reconstruction_demand_active(),
        queued=orchestrator.queue_sample.queued,
        in_flight=orchestrator.queue_sample.in_flight,
        gpu_contended=orchestrator.state.gpu_contended,
        idle_window_seconds=orchestrator.state.idle_window_s,
        poll_interval_seconds=orchestrator.state.poll_interval_s,
        last_pass_at=orchestrator.last_pass_at,
    )


@patch("/policy", sync_to_thread=False)
def patch_policy(data: PolicyUpdate) -> PolicyResponse:
    orchestrator = _orchestrator_or_raise()
    if data.idle_window_seconds is not None and data.idle_window_seconds < IDLE_WINDOW_FLOOR_S:
        raise HTTPException(status_code=400, detail=f"idle_window_seconds must be at least {IDLE_WINDOW_FLOOR_S}")
    if data.poll_interval_seconds is not None and data.poll_interval_seconds < POLL_INTERVAL_FLOOR_S:
        raise HTTPException(status_code=400, detail=f"poll_interval_seconds must be at least {POLL_INTERVAL_FLOOR_S}")
    idle_window_s = (
        data.idle_window_seconds if data.idle_window_seconds is not None else orchestrator.state.idle_window_s
    )
    poll_interval_s = (
        data.poll_interval_seconds if data.poll_interval_seconds is not None else orchestrator.state.poll_interval_s
    )
    orchestrator.set_timer_values(idle_window_s, poll_interval_s)
    return PolicyResponse(
        idle_window_seconds=orchestrator.state.idle_window_s,
        poll_interval_seconds=orchestrator.state.poll_interval_s,
    )


def _orchestrator_or_raise() -> Orchestrator:
    if _orchestrator is None:
        raise RuntimeError("gpu orchestrator is unconfigured, bootstrap must run first")
    return _orchestrator


async def bootstrap(app: Litestar) -> None:
    global _orchestrator
    settings = Settings.model_validate({})
    docker_client = await to_thread(from_env)
    await to_thread(require_managed_pair, docker_client, settings.compose_project)

    _orchestrator = Orchestrator(
        BootState(
            docker=docker_client,
            compose_project=settings.compose_project,
            http=AsyncClient(timeout=QUEUE_POLL_TIMEOUT_S),
            localizer_url=settings.localizer_url,
            lease_server_url=settings.lease_server_url,
            gpu_contended=settings.gpu_contended,
            retry_after_s=settings.retry_after_s,
            idle_window_s=settings.idle_window_s,
            poll_interval_s=settings.poll_interval_s,
        )
    )
    app.state.reconcile_loop = create_task(_orchestrator.run_forever())


def require_managed_pair(client: DockerClient, project: str) -> None:
    # Validate the platform-injected project against the actuation targets, because a scope
    # nobody verifies is a scope the reconcile loop silently misses
    for service_name in sorted(MANAGED_SERVICES):
        matches = client.containers.list(
            all=True,
            filters={
                "label": [
                    f"{COMPOSE_SERVICE_LABEL}={service_name}",
                    f"{COMPOSE_PROJECT_LABEL}={project}",
                ]
            },
        )
        if not matches:
            raise ValueError(f"no {service_name} container in compose project {project}, run boatyard up")


app = create_litestar_app([get_localizer_address, get_state, patch_policy], openapi_config, logging_config=None)
app.on_startup.append(bootstrap)
