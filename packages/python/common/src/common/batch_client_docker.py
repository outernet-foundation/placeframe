# from __future__ import annotations

# import threading
# import uuid
# from typing import Any, Literal

# from docker.types import DeviceRequest

# import docker

# Status = Literal["SUBMITTED", "RUNNING", "SUCCEEDED", "FAILED", "UNKNOWN"]


# class DockerBatchClient:
#     def __init__(self) -> None:
#         self.jobs: dict[str, dict[str, Status]] = {}
#         self._docker = docker.from_env()

#     def submit_job(
#         self,
#         name: str,
#         queue_name: str,
#         job_definition_name: str,
#         *,
#         array_size: int | None = None,
#         torch_device: Literal["cpu", "cuda", "rocm"] = "cpu",
#         environment: dict[str, str] | None = None,
#     ) -> str:
#         if array_size is None:
#             array_size = 1
#         if array_size <= 0:
#             raise ValueError("array_size must be greater than 0")

#         job_id = f"{name}-{uuid.uuid4().hex[:12]}"
#         self.jobs[job_id] = {}

#         for index in range(array_size):
#             environment = dict(environment or {})
#             environment["DOCKER_HOST"] = "unix:///var/run/docker.sock"
#             environment["BATCH_JOB_ARRAY_INDEX"] = str(index)

#             run_kwargs: dict[str, Any] = {}
#             if torch_device == "cuda":
#                 run_kwargs["device_requests"] = [DeviceRequest(count=-1, capabilities=[["gpu"]])]
#             elif torch_device == "rocm":
#                 run_kwargs["devices"] = ["/dev/kfd:/dev/kfd", "/dev/dri:/dev/dri"]

#             container = self._docker.containers.run(
#                 image=f"{job_definition_name}:latest",
#                 environment=environment,
#                 network="plerion_default",
#                 volumes={
#                     "/var/run/docker.sock": {"bind": "/var/run/docker.sock", "mode": "rw"}
#                 },  # So task can submit subtasks
#                 ports={"5678/tcp": ("127.0.0.1", 0)},  # Forward the debugging port to a random host port
#                 labels={"service": job_definition_name, "job": job_id, "task": str(index)},
#                 detach=True,
#                 remove=False,
#                 **run_kwargs,
#             )

#             container_id = container.id
#             assert container_id is not None
#             self.jobs[job_id][container_id] = "SUBMITTED"
#             threading.Thread(target=self._wait_for_exit, args=(job_id, container_id), daemon=True).start()

#         return job_id

#     def get_job_status(self, job_id: str) -> str:
#         if job_id not in self.jobs:
#             raise ValueError(f"Unknown job ID: {job_id}")

#         for container_id, status in list(self.jobs[job_id].items()):
#             if status == "SUBMITTED":
#                 try:
#                     container = self._docker.containers.get(container_id)
#                     container.reload()

#                     if container.status == "running":
#                         self.jobs[job_id][container_id] = "RUNNING"
#                 except Exception:
#                     pass

#         statuses = set(self.jobs[job_id].values())

#         if "FAILED" in statuses:
#             return "FAILED"
#         if statuses == {"SUCCEEDED"}:
#             return "SUCCEEDED"
#         if "RUNNING" in statuses:
#             return "RUNNING"
#         if "SUBMITTED" in statuses:
#             return "SUBMITTED"
#         return "UNKNOWN"

#     def _wait_for_exit(self, job_id: str, container_id: str) -> None:
#         try:
#             result = self._docker.api.wait(container_id)
#             code = int(result.get("StatusCode", 1))
#         except Exception:
#             code = 1

#         self.jobs[job_id][container_id] = "SUCCEEDED" if code == 0 else "FAILED"
