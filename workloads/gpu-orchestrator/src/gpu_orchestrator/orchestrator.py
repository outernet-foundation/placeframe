from __future__ import annotations

from asyncio import Event, to_thread, wait_for
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from logging import getLogger
from math import inf
from time import monotonic, sleep

from docker import DockerClient
from docker.models.containers import Container
from httpx import AsyncClient, HTTPError
from pydantic import BaseModel

LOCALIZER = "localizer"
RECONSTRUCTOR = "reconstructor"
MANAGED_SERVICES = frozenset({LOCALIZER, RECONSTRUCTOR})

COMPOSE_PROJECT_LABEL = "com.docker.compose.project"
COMPOSE_SERVICE_LABEL = "com.docker.compose.service"
# Drain real-time localization before the stop, because an interrupted localization is a failed client request
LOCALIZATION_DRAIN_SECONDS = 0.7
# Leave room for a future checkpoint-on-SIGTERM, because docker's 10 s default SIGKILLs mid-checkpoint
RECONSTRUCTOR_STOP_TIMEOUT_S = 60

QUEUE_POLL_TIMEOUT_S = 10.0

logger = getLogger(__name__)


class QueueSample(BaseModel):
    queued: int
    in_flight: int


@dataclass
class BootState:
    docker: DockerClient
    compose_project: str
    http: AsyncClient
    localizer_url: str
    lease_server_url: str
    gpu_contended: bool
    retry_after_s: int
    idle_window_s: int
    poll_interval_s: int


class Orchestrator:
    def __init__(self, state: BootState, clock: Callable[[], float] = monotonic) -> None:
        self.state = state
        self.clock = clock

        # Start with an empty queue so batch demand is inactive until the first poll
        self.queue_sample = QueueSample(queued=0, in_flight=0)

        # Read never as -inf, so an unseen heartbeat ages out and the first pass polls immediately
        self.heartbeat_at = -inf
        self.last_poll_at = -inf

        self.last_pass_at: str | None = None
        self.hint_edge = False
        self.poke = Event()

    async def run_forever(self) -> None:
        # Poll the queue on the interval, converge to the desired set, and stamp each pass
        while True:
            try:
                now = self.clock()

                if now - self.last_poll_at >= self.state.poll_interval_s:
                    self.last_poll_at = now
                    await self._poll_queue_sample()

                localization_demand = self.localization_demand_active()
                reconstruction_demand = self.reconstruction_demand_active()

                # Prioritize localization over batch demand and default to the localizer
                contended_winner = (
                    frozenset({RECONSTRUCTOR})
                    if reconstruction_demand and not localization_demand
                    else frozenset({LOCALIZER})
                )
                desired = contended_winner if self.state.gpu_contended else MANAGED_SERVICES

                held_out = frozenset(
                    service
                    for service, demand in ((LOCALIZER, localization_demand), (RECONSTRUCTOR, reconstruction_demand))
                    if demand and service not in desired
                )

                # If held-out demand is new since the last pass
                if held_out and not self.hint_edge:
                    logger.info(
                        "held-out GPU demand for %s under GPU_CONTENDED arbitration, "
                        "set GPU_CONTENDED false in boatyard.values.yaml if this hardware fits both workloads",
                        sorted(held_out),
                    )
                self.hint_edge = bool(held_out)

                # Run converge in a thread, because the Docker SDK is synchronous
                await to_thread(self.converge, desired)
                self.last_pass_at = datetime.now(UTC).isoformat()
            except Exception:
                logger.exception("reconcile pass failed")

            # Wait for a poke or the poll interval, whichever comes first
            try:
                await wait_for(self.poke.wait(), timeout=self.state.poll_interval_s)
            except TimeoutError:
                pass

            self.poke.clear()

    def record_heartbeat(self) -> None:
        self.heartbeat_at = self.clock()
        self.poke.set()

    def set_timer_values(self, idle_window_s: int, poll_interval_s: int) -> None:
        if idle_window_s != self.state.idle_window_s:
            logger.info("idle window old=%ds new=%ds", self.state.idle_window_s, idle_window_s)
            self.state.idle_window_s = idle_window_s
        if poll_interval_s != self.state.poll_interval_s:
            logger.info("poll interval old=%ds new=%ds", self.state.poll_interval_s, poll_interval_s)
            self.state.poll_interval_s = poll_interval_s

    def localization_demand_active(self) -> bool:
        return self.clock() - self.heartbeat_at <= self.state.idle_window_s

    def reconstruction_demand_active(self) -> bool:
        return self.queue_sample.queued > 0 or self.queue_sample.in_flight > 0

    def localizer_address(self) -> str | None:
        return self.state.localizer_url if LOCALIZER in self.running_services() else None

    def running_services(self) -> set[str]:
        containers = self._containers_by_service()
        return {service for service, container in containers.items() if container.status == "running"}

    def converge(self, desired: frozenset[str]) -> None:
        # Stop before starting so the GPU slot is free, and finish the whole transition inside this pass
        containers = self._containers_by_service()

        # Stop the running services that lost the slot
        for service in sorted(MANAGED_SERVICES):
            container = containers.get(service)
            if container is None or service in desired or container.status != "running":
                continue

            # Exactly one arm fires, because the loop ranges over the managed pair
            if service == LOCALIZER:
                sleep(LOCALIZATION_DRAIN_SECONDS)
                container.stop()
            if service == RECONSTRUCTOR:
                container.stop(timeout=RECONSTRUCTOR_STOP_TIMEOUT_S)
            container.wait()

        # Start the desired services that are not running yet
        for service in sorted(MANAGED_SERVICES):
            if service not in desired:
                continue
            container = containers.get(service)
            if container is None:
                raise ValueError(
                    f"no {service} container in compose project {self.state.compose_project}, run boatyard up"
                )
            if container.status != "running":
                container.start()

    async def _poll_queue_sample(self) -> None:
        # Hold the last sample when the poll fails, because reading an unreachable lease-server
        # as no-demand would preempt a running reconstruction during every lease-server restart
        url = f"{self.state.lease_server_url.rstrip('/')}/queue-state"

        # Plain httpx rather than the generated client, because this is a one-endpoint attribute read
        try:
            response = await self.state.http.get(url)
            response.raise_for_status()
            self.queue_sample = QueueSample.model_validate(response.json())
        except HTTPError:
            logger.info("queue-state poll failed, holding the last sample sample=%s", self.queue_sample)

    def _containers_by_service(self) -> dict[str, Container]:
        containers: dict[str, Container] = {}
        for service_name in sorted(MANAGED_SERVICES):
            # List stopped containers too, because boatyard up creates both GPU workloads stopped
            matches = self.state.docker.containers.list(
                all=True,
                filters={
                    "label": [
                        f"{COMPOSE_SERVICE_LABEL}={service_name}",
                        f"{COMPOSE_PROJECT_LABEL}={self.state.compose_project}",
                    ]
                },
            )
            if not matches:
                continue
            containers[service_name] = matches[0]
        return containers
