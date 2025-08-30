from pathlib import Path
from typing import Literal

from .batch_client_api import BatchClient
from .batch_client_aws import AwsBatchClient
from .batch_client_compose import ComposeBatchClient


def create_batch_client(
    backend: Literal["aws", "compose"], compose_file: Path | None = None
) -> BatchClient:
    if backend == "aws":
        return AwsBatchClient()
    elif backend == "compose":
        if compose_file is None:
            raise ValueError("compose_file must be provided for compose backend")
        return ComposeBatchClient(compose_file)
