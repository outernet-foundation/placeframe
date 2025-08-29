from typing import Literal

from .batch_client_api import BatchClient
from .batch_client_aws import BatchClient as AwsBatchClient
from .batch_client_compose import BatchClient as ComposeBatchClient


def create_batch_client(backend: Literal["aws", "compose"]) -> BatchClient:
    if backend == "aws":
        return AwsBatchClient()
    elif backend == "compose":
        return ComposeBatchClient()
