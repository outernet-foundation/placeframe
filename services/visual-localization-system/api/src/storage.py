from functools import lru_cache
from typing import TYPE_CHECKING, Any, cast

import boto3
from botocore.config import Config

from .settings import get_settings

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client
else:
    S3Client = Any

UPLOAD_EXPIRES = 15 * 60
DOWNLOAD_EXPIRES = 60


class Storage:
    def __init__(self, s3: S3Client) -> None:
        self._s3 = s3

    def presign_put(self, bucket: str, key: str, content_type: str, expires: int = UPLOAD_EXPIRES) -> str:
        return self._s3.generate_presigned_url(
            "put_object",
            Params={"Bucket": bucket, "Key": key, "ContentType": content_type},
            ExpiresIn=expires,
            HttpMethod="PUT",
        )

    def presign_get(self, bucket: str, key: str, content_type: str, expires: int = DOWNLOAD_EXPIRES) -> str:
        return self._s3.generate_presigned_url(
            "get_object", Params={"Bucket": bucket, "Key": key, "ContentType": content_type}, ExpiresIn=expires
        )

    def delete(self, bucket: str, key: str) -> None:
        self._s3.delete_object(Bucket=bucket, Key=key)


@lru_cache(maxsize=1)
def _build_storage() -> Storage:
    settings = get_settings()

    kwargs: dict[str, Any] = {}
    if settings.s3_endpoint_url:
        kwargs.update(
            endpoint_url=str(settings.s3_endpoint_url),
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            config=Config(
                signature_version="s3v4",
                region_name="us-east-1",  # required by SigV4
                s3={"addressing_style": "path"},  # ← force path-style (/{bucket}/{key})
            ),
        )

    # See https://github.com/microsoft/pylance-release/issues/2809
    client = cast(S3Client, boto3.client("s3", **kwargs))  # type: ignore[call-arg]
    return Storage(s3=client)


def get_storage() -> Storage:
    return _build_storage()
