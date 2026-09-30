from __future__ import annotations

import time

from botocore.exceptions import ClientError, EndpointConnectionError
from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

from .boto_client import BucketClient, create_s3_client

ENDPOINT_READY_TIMEOUT_SECONDS = 120.0
ENDPOINT_RETRY_INTERVAL_SECONDS = 2.0


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    s3_endpoint_url: AnyHttpUrl
    s3_access_key: str
    s3_secret_key: str
    s3_buckets: str


def main() -> None:
    settings = Settings.model_validate({})
    client = create_s3_client(str(settings.s3_endpoint_url), settings.s3_access_key, settings.s3_secret_key)
    buckets = settings.s3_buckets.split()
    deadline = time.monotonic() + ENDPOINT_READY_TIMEOUT_SECONDS
    while True:
        try:
            results = {bucket: ensure_bucket(client, bucket) for bucket in buckets}
            break
        except EndpointConnectionError:
            if time.monotonic() >= deadline:
                raise
            print(f"Waiting for S3 endpoint {settings.s3_endpoint_url} ...", flush=True)
            time.sleep(ENDPOINT_RETRY_INTERVAL_SECONDS)
    for bucket, action in results.items():
        print(f"{bucket}: {action}", flush=True)


def ensure_bucket(client: BucketClient, bucket: str) -> str:
    try:
        client.head_bucket(Bucket=bucket)
        return "verified"
    except ClientError as error:
        if str(error.response.get("Error", {}).get("Code", "")) != "404":
            raise
    client.create_bucket(Bucket=bucket)
    return "created"
