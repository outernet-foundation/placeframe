from typing import Literal, Protocol

from .batch_client_aws import AwsBatchClient
from .batch_client_docker import DockerBatchClient


class BatchClient(Protocol):
    def submit_job(
        self,
        name: str,
        queue_name: str,
        job_definition_name: str,
        *,
        array_size: int | None = None,
        environment: dict[str, str] | None = None,
    ) -> str: ...

    def get_job_status(self, job_id: str) -> str: ...


def create_batch_client(backend: Literal["aws", "docker"]) -> BatchClient:
    if backend == "aws":
        return AwsBatchClient()
    elif backend == "docker":
        return DockerBatchClient()
