from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from json import dumps
from queue import Queue
from threading import Thread
from time import monotonic, sleep
from typing import Any
from uuid import UUID

from placeframe_core.reconstruction_options import ReconstructionOptions

QUEUE_MAX_SIZE = 64
RETRY_BACKOFF_INITIAL_SECONDS = 1.0
RETRY_BACKOFF_MAX_SECONDS = 60.0
DRAIN_POLL_INTERVAL_SECONDS = 0.05
MARKER_FILE_NAME = "marker.json"
SHARD_KEY_PREFIX = "shards/"


class ArtifactUploader:
    def __init__(
        self,
        s3_client: Any,
        bucket: str,
        reconstruction_id: UUID,
        pipeline_version: str,
        options_hash: str,
    ) -> None:
        self._s3_client = s3_client
        self._bucket = bucket
        self._reconstruction_id = reconstruction_id
        self._pipeline_version = pipeline_version
        self._options_hash = options_hash
        self._queue: Queue[_Upload | _ShardUpload] = Queue(maxsize=QUEUE_MAX_SIZE)
        self._thread = Thread(target=self._drain_loop, name=f"artifact-uploader-{reconstruction_id}", daemon=True)
        self._thread.start()

    def put_artifact(self, key: str, body: bytes) -> None:
        self._queue.put(_Upload(key=key, body=body))

    def put_shard(self, prefix: str, files: dict[str, bytes], marker_extra: dict[str, int]) -> None:
        marker_body = _build_marker_body(self._options_hash, self._pipeline_version, files, marker_extra)
        self._queue.put(_ShardUpload(prefix=prefix, files=dict(files), marker_body=marker_body))

    def put_stage_marker(self, marker_key: str, files: dict[str, bytes]) -> None:
        # Put a standalone marker at an arbitrary key, checksumming artifacts that went out through put_artifact
        marker_body = _build_marker_body(self._options_hash, self._pipeline_version, files, {})
        self._queue.put(_Upload(key=marker_key, body=marker_body))

    def drain(self, timeout_seconds: float | None = None) -> bool:
        if timeout_seconds is None:
            self._queue.join()
            return True
        deadline = monotonic() + timeout_seconds
        while self._queue.unfinished_tasks > 0:
            if monotonic() >= deadline:
                return False
            sleep(DRAIN_POLL_INTERVAL_SECONDS)
        return True

    def _drain_loop(self) -> None:
        while True:
            item = self._queue.get()
            if isinstance(item, _Upload):
                self._put_object_with_retry(item.key, item.body)
                self._queue.task_done()
                continue
            for name, body in item.files.items():
                self._put_object_with_retry(f"{item.prefix}/{name}", body)

            # Write the marker last so its presence certifies the shard's data objects are durable
            self._put_object_with_retry(f"{item.prefix}/{MARKER_FILE_NAME}", item.marker_body)
            self._queue.task_done()

    def _put_object_with_retry(self, key: str, body: bytes) -> None:
        backoff_seconds = RETRY_BACKOFF_INITIAL_SECONDS
        while True:
            try:
                self._s3_client.put_object(Bucket=self._bucket, Key=f"{self._reconstruction_id}/{key}", Body=body)
                print(f"[uploader] put {self._reconstruction_id}/{key}")
                return
            except Exception as e:
                print(f"[uploader] put failed {self._reconstruction_id}/{key}, retrying in {backoff_seconds}s: {e}")
                sleep(backoff_seconds)
                backoff_seconds = min(backoff_seconds * 2, RETRY_BACKOFF_MAX_SECONDS)


@dataclass(frozen=True)
class _Upload:
    key: str
    body: bytes


@dataclass(frozen=True)
class _ShardUpload:
    prefix: str
    files: dict[str, bytes]
    marker_body: bytes


def compute_options_hash(reconstruction_options: ReconstructionOptions) -> str:
    canonical_options = dumps(reconstruction_options.model_dump(mode="json"), sort_keys=True)
    return sha256(canonical_options.encode("utf-8")).hexdigest()


def _build_marker_body(
    options_hash: str, pipeline_version: str, files: dict[str, bytes], marker_extra: dict[str, int]
) -> bytes:
    marker = {
        "options_hash": options_hash,
        "pipeline_version": pipeline_version,
        "files": {name: sha256(body).hexdigest() for name, body in files.items()},
        **marker_extra,
    }
    return dumps(marker, sort_keys=True).encode("utf-8")


def delete_shard_prefix(s3_client: Any, bucket: str, reconstruction_id: UUID) -> None:
    prefix = f"{reconstruction_id}/{SHARD_KEY_PREFIX}"
    paginator = s3_client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        objects = [{"Key": key} for entry in page.get("Contents", []) if (key := entry.get("Key")) is not None]
        if not objects:
            continue
        response = s3_client.delete_objects(Bucket=bucket, Delete={"Objects": objects})
        errors = response.get("Errors", [])
        if errors:
            raise RuntimeError(f"S3 delete failed for {len(errors)} objects under {prefix}")
