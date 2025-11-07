from typing import TYPE_CHECKING, Any, cast

import boto3
from botocore.config import Config
from pydantic import AnyHttpUrl

if TYPE_CHECKING:
    from mypy_boto3_batch import BatchClient
    from mypy_boto3_ecs import ECSClient
    from mypy_boto3_lambda import LambdaClient
    from mypy_boto3_s3 import S3Client
    from mypy_boto3_secretsmanager import SecretsManagerClient
else:
    BatchClient = Any
    ECSClient = Any
    S3Client = Any
    SecretsManagerClient = Any
    LambdaClient = Any


def create_batch_client() -> BatchClient:
    return cast(BatchClient, boto3.client("batch", region_name="us-east-1"))  # type: ignore[call-arg]


def create_ecs_client() -> ECSClient:
    return cast(
        ECSClient,
        boto3.client(  # pyright: ignore[reportUnknownMemberType]
            "ecs",
            region_name="us-east-1",
            config=Config(
                connect_timeout=10,
                read_timeout=910,
                tcp_keepalive=True,
                retries={"max_attempts": 3, "mode": "standard"},
            ),
        ),
    )  # type: ignore[call-arg]


def create_lambda_client() -> LambdaClient:
    return cast(
        LambdaClient,
        boto3.client(  # pyright: ignore[reportUnknownMemberType]
            "lambda",
            region_name="us-east-1",
            config=Config(
                connect_timeout=10,
                read_timeout=910,
                tcp_keepalive=True,
                retries={"max_attempts": 3, "mode": "standard"},
            ),
        ),
    )  # type: ignore[call-arg]


def create_s3_client(
    s3_endpoint_url: AnyHttpUrl | None, s3_access_key: str | None, s3_secret_key: str | None
) -> S3Client:
    kwargs: dict[str, Any] = {}
    if s3_endpoint_url:
        kwargs.update(
            endpoint_url=str(s3_endpoint_url),
            aws_access_key_id=s3_access_key,
            aws_secret_access_key=s3_secret_key,
            config=Config(
                signature_version="s3v4",
                region_name="us-east-1",  # required by SigV4
                s3={"addressing_style": "path"},  # ← force path-style (/{bucket}/{key})
            ),
        )

    return cast(S3Client, boto3.client("s3", **kwargs))  # type: ignore[call-arg]


def create_secretsmanager_client() -> SecretsManagerClient:
    return cast(SecretsManagerClient, boto3.client("secretsmanager", region_name="us-east-1"))  # type: ignore[call-arg]
