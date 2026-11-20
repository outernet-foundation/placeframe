from __future__ import annotations

from asyncio import to_thread
from logging import getLogger
from os import environ
from socket import gethostname
from threading import Lock
from time import sleep
from typing import Literal

from docker import DockerClient, from_env
from docker.models.containers import Container
from litestar import Litestar, get, post
from litestar.openapi.config import OpenAPIConfig
from litestar.openapi.spec import Server
from placeframe_common.litestar import create_litestar_app
from placeframe_common.logging_config import configure_logging
from pydantic import BaseModel

configure_logging("mode-switcher")

logger = getLogger(__name__)

Mode = Literal["localizer", "reconstructor"]

DEFAULT_MODE: Mode = "localizer"
GPU_SERVICES: tuple[Mode, ...] = ("localizer", "reconstructor")
COMPOSE_PROJECT_LABEL = "com.docker.compose.project"
COMPOSE_SERVICE_LABEL = "com.docker.compose.service"
# The localizer's compose-network URL arrives from the provisioner, templated from
# the localizer workload's own service.ports declaration — no copied port here.
LOCALIZER_URL_ENV = "LOCALIZER_URL"
LOCALIZATION_DRAIN_SECONDS = 0.7

openapi_config = OpenAPIConfig(
    "Placeframe Mode Switcher",
    "0.1.0",
    servers=[Server(url="http://mode-switcher:8000")],
)

_client: DockerClient | None = None
_project: str | None = None
# The transition marker publishes an in-flight switch so mode reads never block
# behind the 10-30s container sequence and never misreport the gap between the
# two containers as the default mode. Set under _flag_lock when a switch begins,
# cleared in the switch's finally.
_transition: Mode | None = None
_switch_lock = Lock()
_flag_lock = Lock()


class ModeResponse(BaseModel):
    mode: Mode


class ModeRequest(BaseModel):
    mode: Mode


class LocalizerAddressResponse(BaseModel):
    address: str | None


@get("/mode")
async def get_mode() -> ModeResponse:
    return ModeResponse(mode=await to_thread(current_mode))


@post("/mode")
async def set_mode(data: ModeRequest) -> ModeResponse:
    return ModeResponse(mode=await to_thread(switch, data.mode))


@get("/localizer-address")
async def get_localizer_address() -> LocalizerAddressResponse:
    return LocalizerAddressResponse(address=await to_thread(localizer_address))


async def bootstrap(app: Litestar) -> None:
    await to_thread(initialize, from_env())


def initialize(client: DockerClient) -> None:
    global _client, _project
    _client = client
    _project = compose_project_of(client)
    with _switch_lock:
        containers = _containers_by_service()
        running: set[Mode] = {service for service, container in containers.items() if container.status == "running"}
        if len(running) > 1:
            for service, container in sorted(containers.items()):
                if service != DEFAULT_MODE and container.status == "running":
                    container.stop()
            logger.info("boot repair stopped extras running=%s", sorted(running))
            return

        # A single running container is adopted, whichever it is
        if running:
            return
        default_container = containers.get(DEFAULT_MODE)
        if default_container is not None:
            default_container.start()
            logger.info("boot repair started default service=%s", DEFAULT_MODE)


def current_mode() -> Mode:
    with _flag_lock:
        transition = _transition
    if transition is not None:
        return transition

    containers = _containers_by_service()
    running: set[Mode] = {service for service, container in containers.items() if container.status == "running"}
    if len(running) == 1:
        return next(iter(running))
    # Zero running (external docker stops, a switch another process did not
    # survive) and two running (raw docker compose up) encode no mode; the
    # default answers both.
    return DEFAULT_MODE


def switch(target_mode: Mode) -> Mode:
    global _transition
    with _switch_lock:
        with _flag_lock:
            _transition = target_mode
        try:
            containers = _containers_by_service()
            for service, container in sorted(containers.items()):
                if service == target_mode or container.status != "running":
                    continue
                # Drain real-time localization before the stop, because an interrupted
                # reconstruction requeues its job
                if service == "localizer":
                    sleep(LOCALIZATION_DRAIN_SECONDS)
                container.stop()
                container.wait()
            target_container = containers.get(target_mode)
            if target_container is None:
                raise ValueError(
                    f"no {target_mode} container in compose project {_configured_project()}; run boatyard up"
                )
            if target_container.status != "running":
                target_container.start()
            return target_mode
        finally:
            with _flag_lock:
                _transition = None


def localizer_address() -> str | None:
    container = _containers_by_service().get("localizer")
    if container is not None and container.status == "running":
        return environ[LOCALIZER_URL_ENV]
    return None


def _containers_by_service() -> dict[Mode, Container]:
    if _client is None:
        raise RuntimeError("mode switcher is unconfigured; bootstrap must run first")
    client = _client
    containers: dict[Mode, Container] = {}
    for service_name in GPU_SERVICES:
        # List stopped containers too, because boatyard up creates both GPU workloads stopped
        matches = client.containers.list(
            all=True,
            filters={
                "label": [
                    f"{COMPOSE_SERVICE_LABEL}={service_name}",
                    f"{COMPOSE_PROJECT_LABEL}={_configured_project()}",
                ]
            },
        )
        if matches:
            containers[service_name] = matches[0]
    return containers


def _configured_project() -> str:
    if _project is None:
        raise RuntimeError("mode switcher is unconfigured; bootstrap must run first")
    return _project


def compose_project_of(client: DockerClient) -> str:
    # Discover the project from this container's own labels, because the compose project name is entry-prefixed
    own = client.containers.get(gethostname())

    # Read the project from attrs because typeshed leaves Container.labels unannotated
    labels: dict[str, str] = own.attrs["Config"].get("Labels", {})
    project = labels.get(COMPOSE_PROJECT_LABEL)
    if project is None:
        raise ValueError(f"container {own.name} carries no {COMPOSE_PROJECT_LABEL} label")
    return project


app = create_litestar_app([get_mode, set_mode, get_localizer_address], openapi_config, logging_config=None)
app.on_startup.append(bootstrap)
