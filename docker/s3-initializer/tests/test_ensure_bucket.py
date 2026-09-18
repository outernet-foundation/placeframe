from __future__ import annotations

import pytest
from botocore.exceptions import ClientError, EndpointConnectionError

from s3_initializer.main import ensure_bucket


def client_error(status_code: str) -> ClientError:
    return ClientError({"Error": {"Code": status_code, "Message": "irrelevant"}}, "HeadBucket")


class FakeS3Client:
    def __init__(self, existing_buckets: set[str], failures: dict[str, Exception] | None = None):
        self.existing_buckets = existing_buckets
        self.failures = failures if failures is not None else {}
        self.created_buckets: list[str] = []

    def head_bucket(self, **operation: str) -> dict[str, str]:
        bucket = operation["Bucket"]
        if bucket in self.failures:
            raise self.failures[bucket]
        if bucket not in self.existing_buckets:
            raise client_error("404")
        return {}

    def create_bucket(self, **operation: str) -> dict[str, str]:
        self.created_buckets.append(operation["Bucket"])
        return {}


class TestEnsureBucket:
    def test_should_verify_existing_bucket_without_creating(self):
        client = FakeS3Client(existing_buckets={"dev-captures"})
        assert ensure_bucket(client, "dev-captures") == "verified"
        assert client.created_buckets == []

    def test_should_create_missing_bucket(self):
        client = FakeS3Client(existing_buckets=set())
        assert ensure_bucket(client, "dev-captures") == "created"
        assert client.created_buckets == ["dev-captures"]

    def test_should_raise_when_bucket_belongs_to_someone_else(self):
        client = FakeS3Client(existing_buckets={"dev-captures"}, failures={"dev-captures": client_error("403")})
        with pytest.raises(ClientError):
            ensure_bucket(client, "dev-captures")

    def test_should_raise_on_unexpected_endpoint_error(self):
        client = FakeS3Client(
            existing_buckets={"dev-captures"}, failures={"dev-captures": EndpointConnectionError(endpoint_url="x")}
        )
        with pytest.raises(EndpointConnectionError):
            ensure_bucket(client, "dev-captures")
