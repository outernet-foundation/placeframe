# noqa-wrapper: boto3.client() has a giant stub overload that resolves to Unknown under basedpyright
# strict, and its operation parameters are PascalCase (Bucket); this module is the single suppression
# boundary for S3 client construction and the boto API shape.
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

import boto3
from botocore.config import Config

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client
else:
    S3Client = Any


class BucketClient(Protocol):
    def head_bucket(self, *, Bucket: str) -> object: ...  # noqa: N803

    def create_bucket(self, *, Bucket: str) -> object: ...  # noqa: N803


def create_s3_client(endpoint_url: str, access_key: str, secret_key: str) -> S3Client:
    return boto3.client(  # pyright: ignore[reportUnknownMemberType]
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=Config(
            signature_version="s3v4",
            region_name="us-east-1",
            s3={"addressing_style": "path"},
        ),
    )
