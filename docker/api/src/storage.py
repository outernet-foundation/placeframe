from functools import lru_cache
from typing import TYPE_CHECKING, Any, BinaryIO

from common.boto_clients import create_s3_client

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

    def upload_fileobj(self, bucket: str, key: str, fileobj: BinaryIO, content_type: str):
        self._s3.upload_fileobj(Fileobj=fileobj, Bucket=bucket, Key=key, ExtraArgs={"ContentType": content_type})

    def get_object(self, bucket: str, key: str):
        return self._s3.get_object(Bucket=bucket, Key=key)


@lru_cache(maxsize=1)
def _build_storage() -> Storage:
    settings = get_settings()

    return Storage(
        s3=create_s3_client(
            minio_endpoint_url=settings.minio_endpoint_url,
            minio_access_key=settings.minio_access_key,
            minio_secret_key=settings.minio_secret_key,
        )
    )


def get_storage() -> Storage:
    return _build_storage()
