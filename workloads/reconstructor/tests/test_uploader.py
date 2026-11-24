from __future__ import annotations

from hashlib import sha256
from json import dumps, loads
from threading import Event, Thread
from time import sleep
from uuid import uuid4

import pytest
from placeframe_core.reconstruction_options import ReconstructionOptions

from reconstructor import uploader as uploader_module
from reconstructor.uploader import ArtifactUploader, compute_options_hash


class StubS3Client:
    def __init__(self) -> None:
        self.uploads: list[tuple[str, bytes]] = []
        self.attempts: list[str] = []
        self.fail_uploads = False
        self.hold_first_put = False
        self.first_put_started = Event()
        self.put_gate = Event()

    def put_object(self, **kwargs: str | bytes) -> None:
        key = kwargs["Key"]
        body = kwargs["Body"]
        if not isinstance(key, str) or not isinstance(body, bytes):
            raise TypeError("put_object stub expects a str Key and bytes Body")
        self.attempts.append(key)
        if self.hold_first_put and not self.first_put_started.is_set():
            self.first_put_started.set()
            self.put_gate.wait()
        if self.fail_uploads:
            raise RuntimeError("s3 unavailable")
        self.uploads.append((key, body))


def test_put_blocks_when_queue_is_full(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(uploader_module, "QUEUE_MAX_SIZE", 1)
    stub = StubS3Client()
    stub.hold_first_put = True
    reconstruction_id = uuid4()
    uploader = ArtifactUploader(stub, "reconstructions", reconstruction_id, "pipeline-sha", "options-sha")

    uploader.put_artifact("first", b"first-body")
    assert stub.first_put_started.wait(timeout=2.0)
    uploader.put_artifact("second", b"second-body")

    blocked_put = Thread(target=uploader.put_artifact, args=("third", b"third-body"))
    blocked_put.start()
    sleep(0.3)
    assert blocked_put.is_alive()

    stub.put_gate.set()
    blocked_put.join(timeout=2.0)
    assert not blocked_put.is_alive()
    assert uploader.drain(timeout_seconds=2.0)
    assert [key for key, _body in stub.uploads] == [
        f"{reconstruction_id}/first",
        f"{reconstruction_id}/second",
        f"{reconstruction_id}/third",
    ]


def test_marker_written_only_after_shard_puts_succeed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(uploader_module, "RETRY_BACKOFF_INITIAL_SECONDS", 0.001)
    monkeypatch.setattr(uploader_module, "RETRY_BACKOFF_MAX_SECONDS", 0.002)
    stub = StubS3Client()
    stub.fail_uploads = True
    reconstruction_id = uuid4()
    uploader = ArtifactUploader(stub, "reconstructions", reconstruction_id, "pipeline-sha", "options-sha")

    uploader.put_shard(
        "shards/features/00001",
        {"keypoints.h5": b"keypoints", "descriptors.h5": b"descriptors"},
        {"shard_index": 1, "shard_count": 4},
    )
    sleep(0.3)
    assert not any(key.endswith("marker.json") for key in stub.attempts)

    stub.fail_uploads = False
    assert uploader.drain(timeout_seconds=2.0)

    prefix = f"{reconstruction_id}/shards/features/00001"
    assert [key for key, _body in stub.uploads] == [
        f"{prefix}/keypoints.h5",
        f"{prefix}/descriptors.h5",
        f"{prefix}/marker.json",
    ]


def test_drain_completes_when_queue_empties() -> None:
    stub = StubS3Client()
    reconstruction_id = uuid4()
    uploader = ArtifactUploader(stub, "reconstructions", reconstruction_id, "pipeline-sha", "options-sha")
    for index in range(8):
        uploader.put_artifact(f"artifact-{index}", f"body-{index}".encode())

    assert uploader.drain(timeout_seconds=5.0)

    assert len(stub.uploads) == 8


def test_drain_quits_on_timeout() -> None:
    stub = StubS3Client()
    stub.hold_first_put = True
    reconstruction_id = uuid4()
    uploader = ArtifactUploader(stub, "reconstructions", reconstruction_id, "pipeline-sha", "options-sha")

    uploader.put_artifact("held", b"held-body")
    assert stub.first_put_started.wait(timeout=2.0)

    assert uploader.drain(timeout_seconds=0.2) is False

    stub.put_gate.set()
    assert uploader.drain(timeout_seconds=2.0) is True


def test_marker_schema_round_trip() -> None:
    options = ReconstructionOptions()
    stub = StubS3Client()
    reconstruction_id = uuid4()
    uploader = ArtifactUploader(
        stub, "reconstructions", reconstruction_id, "pipeline-sha", compute_options_hash(options)
    )

    uploader.put_shard(
        "shards/matches/00003",
        {"pairs.json": b"[]", "matches.npz": b"matches"},
        {"shard_index": 3, "shard_count": 9},
    )
    assert uploader.drain(timeout_seconds=5.0)

    marker_key = f"{reconstruction_id}/shards/matches/00003/marker.json"
    marker_bodies = [body for key, body in stub.uploads if key == marker_key]
    assert len(marker_bodies) == 1
    marker = loads(marker_bodies[0])
    assert (
        marker["options_hash"]
        == sha256(dumps(options.model_dump(mode="json"), sort_keys=True).encode("utf-8")).hexdigest()
    )
    assert marker["pipeline_version"] == "pipeline-sha"
    assert marker["files"] == {
        "pairs.json": sha256(b"[]").hexdigest(),
        "matches.npz": sha256(b"matches").hexdigest(),
    }
    assert marker["shard_index"] == 3
    assert marker["shard_count"] == 9
