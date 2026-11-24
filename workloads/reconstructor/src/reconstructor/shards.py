from __future__ import annotations

from hashlib import sha256
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, ValidationError

from .uploader import MARKER_FILE_NAME

FEATURE_SHARD_SIZE = 64
MATCH_SHARD_SIZE = 512
FEATURE_SHARD_PREFIX = "shards/features"
MATCH_SHARD_PREFIX = "shards/matches"
VERIFICATION_SHARD_PREFIX = "shards/verification"
OPQ_MARKER_KEY = "shards/training/opq.marker.json"
PQ_MARKER_KEY = "shards/training/pq.marker.json"
SHARD_SIZES_FILE = "sizes.json"
SHARD_PAIRS_FILE = "pairs.json"
MATCHES_FILE = "matches.npz"
TWO_VIEW_GEOMETRIES_FILE = "two_view_geometries.npz"


class ShardMarker(BaseModel):
    model_config = ConfigDict(extra="ignore")

    options_hash: str
    pipeline_version: str
    files: dict[str, str]


def fetch_valid_shard_indexes(
    s3_client: Any,
    bucket: str,
    reconstruction_id: UUID,
    shard_prefix: str,
    options_hash: str,
    pipeline_version: str,
) -> set[int]:
    # Ignore markers whose hash or version disagrees with this lease, so their shards are recomputed and overwritten
    valid_indexes: set[int] = set()
    paginator = s3_client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=f"{reconstruction_id}/{shard_prefix}/"):
        for entry in page.get("Contents", []):
            key = entry.get("Key")
            if key is None or not key.endswith(MARKER_FILE_NAME):
                continue
            marker = _parse_marker(get_object_bytes(s3_client, bucket, key))
            if marker is None or marker.options_hash != options_hash or marker.pipeline_version != pipeline_version:
                continue
            valid_indexes.add(int(key.removesuffix(f"/{MARKER_FILE_NAME}").rsplit("/", 1)[1]))

    return valid_indexes


def load_stage_artifact(
    s3_client: Any,
    bucket: str,
    reconstruction_id: UUID,
    marker_key: str,
    artifact_name: str,
    options_hash: str,
    pipeline_version: str,
) -> bytes | None:
    # Return the stored artifact bytes only when its stage marker matches this lease and checksums those bytes
    listing = s3_client.list_objects_v2(Bucket=bucket, Prefix=f"{reconstruction_id}/{marker_key}", MaxKeys=1)
    if not listing.get("Contents"):
        return None

    marker = _parse_marker(get_object_bytes(s3_client, bucket, f"{reconstruction_id}/{marker_key}"))
    if marker is None or marker.options_hash != options_hash or marker.pipeline_version != pipeline_version:
        return None

    artifact_body = get_object_bytes(s3_client, bucket, f"{reconstruction_id}/{artifact_name}")
    if sha256(artifact_body).hexdigest() != marker.files.get(artifact_name):
        return None

    return artifact_body


def get_object_bytes(s3_client: Any, bucket: str, key: str) -> bytes:
    return s3_client.get_object(Bucket=bucket, Key=key)["Body"].read()


def _parse_marker(marker_body: bytes) -> ShardMarker | None:
    try:
        return ShardMarker.model_validate_json(marker_body)
    except ValidationError:
        return None


def shard_count(item_count: int, shard_size: int) -> int:
    return (item_count + shard_size - 1) // shard_size


def first_unmarked_index(count: int, marked_indexes: set[int]) -> int:
    return next((index for index in range(count) if index not in marked_indexes), count)
