from functools import lru_cache
from typing import TYPE_CHECKING, Any

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

    return Storage(
        s3=create_s3_client(
            s3_endpoint_url=settings.s3_endpoint_url,
            s3_access_key=settings.s3_access_key,
            s3_secret_key=settings.s3_secret_key,
        )
    )


def get_storage() -> Storage:
    return _build_storage()
