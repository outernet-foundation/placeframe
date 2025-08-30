from __future__ import annotations

import json
import subprocess
import threading
import uuid
from pathlib import Path
from typing import Dict, Literal

Status = Literal["SUBMITTED", "RUNNING", "SUCCEEDED", "FAILED", "UNKNOWN"]


class ComposeBatchClient:
    def __init__(self, compose_file: Path) -> None:
        self.compose_file = compose_file
        self.jobs: Dict[str, Dict[str, Status]] = {}

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
            command = [
                "docker",
                "compose",
                "-f",
                str(self.compose_file),  # Specify the compose file
                "--profile",
                "tasks",  # All tasks are in the "tasks" profile
                "run",
                "-d",  # Run containers in detached mode
                "--rm",  # Remove containers after they exit
                "--no-deps",  # Don't start linked services (I don't think this switch is actually necessary)
                "-T",  # Disable pseudo-TTY allocation
                "-e",  # Environment variables
                f"BATCH_JOB_ARRAY_INDEX={index}",
            ]

            for k, v in dict(environment_variables or {}).items():
                command += ["-e", f"{k}={v}"]
            command += [job_definition_name]

            process = subprocess.run(
                command, capture_output=True, text=True, check=False
            )

            if process.returncode != 0:
                raise RuntimeError(process.stderr.strip())

            container_id = process.stdout.strip()

            threading.Thread(
                target=self._wait_for_exit, args=(job_id, container_id), daemon=True
            ).start()

            self.jobs[job_id][container_id] = "SUBMITTED"

        return job_id

    def get_job_status(self, job_id: str) -> str:
        if job_id not in self.jobs:
            raise ValueError(f"Unknown job ID: {job_id}")

        for container_id, status in list(self.jobs[job_id].items()):
            if status == "SUBMITTED":
                process = subprocess.run(
                    ["docker", "inspect", container_id],
                    capture_output=True,
                    text=True,
                    check=False,
                )

                if process.returncode != 0:
                    continue

                try:
                    state = json.loads(process.stdout)[0].get("State", {})
                    if str(state.get("Status", "")) == "running":
                        self.jobs[job_id][container_id] = "RUNNING"
                except Exception:
                    continue

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
        process = subprocess.run(
            ["docker", "wait", container_id], capture_output=True, text=True
        )

        try:
            return_code = int((process.stdout or "").strip())
        except (ValueError, TypeError):
            return_code = 1

        self.jobs[job_id][container_id] = return_code == 0 and "SUCCEEDED" or "FAILED"
