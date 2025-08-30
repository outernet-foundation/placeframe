from __future__ import annotations

import threading
import uuid
from pathlib import Path
from typing import Dict, Literal

import docker
from docker.types import DeviceRequest

Status = Literal["SUBMITTED", "RUNNING", "SUCCEEDED", "FAILED", "UNKNOWN"]


class ComposeBatchClient:
    def __init__(self, compose_file: Path) -> None:
        self.compose_file = compose_file
        self.jobs: Dict[str, Dict[str, Status]] = {}
        self._docker = docker.from_env()

    def submit_job(
        self,
        name: str,
        queue_name: str,
        job_definition_name: str,
        *,
        environment_variables: Dict[str, str] | None = None,
        array_size: int | None = None,
    ) -> str:
        if array_size is None:
            array_size = 1
        if array_size <= 0:
            raise ValueError("array_size must be greater than 0")

        job_id = f"{name}-{uuid.uuid4().hex[:12]}"
        self.jobs[job_id] = {}

        for index in range(array_size):
            env = dict(environment_variables or {})
            env["DOCKER_HOST"] = "unix:///var/run/docker.sock"
            env["BATCH_JOB_ARRAY_INDEX"] = str(index)

            container = self._docker.containers.run(
                image=job_definition_name,
                command=None,
                environment=env,
                volumes={
                    "/var/run/docker.sock": {
                        "bind": "/var/run/docker.sock",
                        "mode": "rw",
                    }
                },
                detach=True,
                remove=True,
                tty=False,
                device_requests=[DeviceRequest(count=-1, capabilities=[["gpu"]])],
            )

            container_id = container.id
            assert container_id is not None
            self.jobs[job_id][container_id] = "SUBMITTED"
            threading.Thread(
                target=self._wait_for_exit, args=(job_id, container_id), daemon=True
            ).start()

        return job_id

    def get_job_status(self, job_id: str) -> str:
        if job_id not in self.jobs:
            raise ValueError(f"Unknown job ID: {job_id}")

        for container_id, status in list(self.jobs[job_id].items()):
            if status == "SUBMITTED":
                try:
                    container = self._docker.containers.get(container_id)
                    container.reload()

                    if container.status == "running":
                        self.jobs[job_id][container_id] = "RUNNING"
                except Exception:
                    pass

        statuses = set(self.jobs[job_id].values())

        if "FAILED" in statuses:
            return "FAILED"
        if statuses == {"SUCCEEDED"}:
            return "SUCCEEDED"
        if "RUNNING" in statuses:
            return "RUNNING"
        if "SUBMITTED" in statuses:
            return "SUBMITTED"
        return "UNKNOWN"

    def _wait_for_exit(self, job_id: str, container_id: str) -> None:
        try:
            result = self._docker.api.wait(container_id)
            code = int(result.get("StatusCode", 1))
        except Exception:
            code = 1

        self.jobs[job_id][container_id] = "SUCCEEDED" if code == 0 else "FAILED"
