from __future__ import annotations

from logging import getLogger
from threading import Lock
from time import sleep

from docker import DockerClient
from docker.models.containers import Container

from .settings import Mode

logger = getLogger(__name__)

COMPOSE_PROJECT = "placeframe"
COMPOSE_PROJECT_LABEL = "com.docker.compose.project"
COMPOSE_SERVICE_LABEL = "com.docker.compose.service"
LOCALIZER_ADDRESS = "http://localizer:8000"
LOCALIZATION_DRAIN_SECONDS = 0.7

SERVICE_FOR_MODE: dict[Mode, str] = {"localization": "localizer", "reconstruction": "reconstructor"}
MODE_FOR_SERVICE: dict[str, Mode] = {"localizer": "localization", "reconstructor": "reconstruction"}


class ModeSwitcher:
    def __init__(self, client: DockerClient, default_mode: Mode = "localization") -> None:
        self._client = client
        self._default_mode: Mode = default_mode
        self._mode: Mode = default_mode
        self._lock = Lock()

    @property
    def mode(self) -> Mode:
        return self._mode

    def reconcile(self) -> Mode:
        with self._lock:
            containers = self._gpu_containers()
            running = {service for service, container in containers.items() if container.status == "running"}
            if len(running) > 1:
                self._mode = self._default_mode
                keep_service = SERVICE_FOR_MODE[self._default_mode]
                for service in sorted(running):
                    if service != keep_service:
                        containers[service].stop()
                logger.info("boot reconcile stopped extras running=%s mode=%s", sorted(running), self._mode)
            elif running:
                adopted_service = next(iter(running))
                self._mode = MODE_FOR_SERVICE[adopted_service]
                logger.info("boot reconcile adopted service=%s mode=%s", adopted_service, self._mode)
            else:
                self._mode = self._default_mode
                default_container = containers.get(SERVICE_FOR_MODE[self._default_mode])
                if default_container is not None:
                    default_container.start()
                logger.info("boot reconcile started default mode=%s", self._mode)
            return self._mode

    def switch(self, target_mode: Mode) -> Mode:
        with self._lock:
            if target_mode == self._mode:
                return self._mode
            logger.info("switching mode from=%s to=%s", self._mode, target_mode)
            containers = self._gpu_containers()
            source_container = containers.get(SERVICE_FOR_MODE[self._mode])
            if source_container is not None and source_container.status == "running":
                if self._mode == "localization":
                    sleep(LOCALIZATION_DRAIN_SECONDS)
                source_container.stop()
                source_container.wait()
            target_container = containers.get(SERVICE_FOR_MODE[target_mode])
            if target_container is None:
                raise ValueError(
                    f"no {SERVICE_FOR_MODE[target_mode]} container in compose project {COMPOSE_PROJECT}; run boatyard up"
                )
            target_container.start()
            self._mode = target_mode
            return self._mode

    def localizer_address(self) -> str | None:
        container = self._gpu_containers().get("localizer")
        if container is not None and container.status == "running":
            return LOCALIZER_ADDRESS
        return None

    def _gpu_containers(self) -> dict[str, Container]:
        containers: dict[str, Container] = {}
        for service_name in SERVICE_FOR_MODE.values():
            matches = self._client.containers.list(
                all=True,
                filters={
                    "label": [
                        f"{COMPOSE_SERVICE_LABEL}={service_name}",
                        f"{COMPOSE_PROJECT_LABEL}={COMPOSE_PROJECT}",
                    ]
                },
            )
            if matches:
                containers[service_name] = matches[0]
        return containers
