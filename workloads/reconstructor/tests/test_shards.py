from __future__ import annotations

from collections.abc import Iterator
from hashlib import sha256
from json import dumps
from pathlib import Path
from uuid import UUID, uuid4

from numpy import allclose, array_equal, float32
from numpy.random import default_rng

from placeframe_core.h5 import read_descriptors, read_keypoints, write_descriptors, write_keypoints

from reconstructor.shards import (
    fetch_valid_shard_indexes,
    first_unmarked_index,
    load_stage_artifact,
)


class StubBody:
    def __init__(self, body: bytes) -> None:
        self._body = body

    def read(self) -> bytes:
        return self._body


class StubPaginator:
    def __init__(self, objects: dict[str, bytes]) -> None:
        self._objects = objects

    def paginate(self, **kwargs: str) -> Iterator[dict[str, list[dict[str, str]]]]:
        prefix = kwargs["Prefix"]
        keys = [key for key in sorted(self._objects) if key.startswith(prefix)]
        yield {"Contents": [{"Key": key} for key in keys]}


class StubS3Client:
    def __init__(self, objects: dict[str, bytes]) -> None:
        self.objects = objects

    def get_paginator(self, operation_name: str) -> StubPaginator:
        return StubPaginator(self.objects)

    def get_object(self, **kwargs: str) -> dict[str, StubBody]:
        return {"Body": StubBody(self.objects[kwargs["Key"]])}

    def list_objects_v2(self, **kwargs: str) -> dict[str, list[dict[str, str]]]:
        prefix = kwargs["Prefix"]
        keys = [key for key in sorted(self.objects) if key.startswith(prefix)]
        return {"Contents": [{"Key": key} for key in keys]}


def _marker(options_hash: str, pipeline_version: str, files: dict[str, str]) -> bytes:
    return dumps(
        {"options_hash": options_hash, "pipeline_version": pipeline_version, "files": files}, sort_keys=True
    ).encode("utf-8")


def _feature_marker_key(reconstruction_id: UUID, index: int) -> str:
    return f"{reconstruction_id}/shards/features/{index:05d}/marker.json"


def test_marker_hash_and_version_mismatch_means_overwrite() -> None:
    reconstruction_id = uuid4()
    objects = {
        _feature_marker_key(reconstruction_id, 0): _marker("matching-hash", "matching-sha", {}),
        _feature_marker_key(reconstruction_id, 1): _marker("other-hash", "matching-sha", {}),
        _feature_marker_key(reconstruction_id, 2): _marker("matching-hash", "other-sha", {}),
    }

    valid = fetch_valid_shard_indexes(
        StubS3Client(objects), "reconstructions", reconstruction_id, "shards/features", "matching-hash", "matching-sha"
    )

    assert valid == {0}


def test_marker_files_and_non_marker_keys_are_ignored() -> None:
    reconstruction_id = uuid4()
    prefix = f"{reconstruction_id}/shards/features"
    objects = {
        f"{prefix}/00000/marker.json": _marker("hash", "sha", {"keypoints.h5": "0" * 64}),
        f"{prefix}/00000/keypoints.h5": b"keypoints",
        f"{prefix}/stray.txt": b"stray",
    }

    valid = fetch_valid_shard_indexes(
        StubS3Client(objects), "reconstructions", reconstruction_id, "shards/features", "hash", "sha"
    )

    assert valid == {0}


def test_first_unmarked_index_selection() -> None:
    assert first_unmarked_index(5, {0, 1, 2}) == 3
    assert first_unmarked_index(5, {0, 1, 2, 3, 4}) == 5
    assert first_unmarked_index(5, set()) == 0
    assert first_unmarked_index(5, {0, 2, 4}) == 1


def test_stage_marker_match_reuses_artifact() -> None:
    reconstruction_id = uuid4()
    artifact = b"opq-matrix-bytes"
    objects = {
        f"{reconstruction_id}/shards/training/opq.marker.json": _marker(
            "hash", "sha", {"opq_matrix.tf": sha256(artifact).hexdigest()}
        ),
        f"{reconstruction_id}/opq_matrix.tf": artifact,
    }

    loaded = load_stage_artifact(
        StubS3Client(objects),
        "reconstructions",
        reconstruction_id,
        "shards/training/opq.marker.json",
        "opq_matrix.tf",
        "hash",
        "sha",
    )

    assert loaded == artifact


def test_stage_marker_mismatch_returns_none() -> None:
    reconstruction_id = uuid4()
    artifact = b"opq-matrix-bytes"
    objects = {
        f"{reconstruction_id}/shards/training/opq.marker.json": _marker(
            "other-hash", "sha", {"opq_matrix.tf": sha256(artifact).hexdigest()}
        ),
        f"{reconstruction_id}/opq_matrix.tf": artifact,
    }

    loaded = load_stage_artifact(
        StubS3Client(objects),
        "reconstructions",
        reconstruction_id,
        "shards/training/opq.marker.json",
        "opq_matrix.tf",
        "hash",
        "sha",
    )

    assert loaded is None


def test_stage_artifact_checksum_mismatch_returns_none() -> None:
    reconstruction_id = uuid4()
    objects = {
        f"{reconstruction_id}/shards/training/opq.marker.json": _marker(
            "hash", "sha", {"opq_matrix.tf": sha256(b"other-bytes").hexdigest()}
        ),
        f"{reconstruction_id}/opq_matrix.tf": b"opq-matrix-bytes",
    }

    loaded = load_stage_artifact(
        StubS3Client(objects),
        "reconstructions",
        reconstruction_id,
        "shards/training/opq.marker.json",
        "opq_matrix.tf",
        "hash",
        "sha",
    )

    assert loaded is None


def test_stage_marker_absent_returns_none() -> None:
    reconstruction_id = uuid4()

    loaded = load_stage_artifact(
        StubS3Client({}),
        "reconstructions",
        reconstruction_id,
        "shards/training/opq.marker.json",
        "opq_matrix.tf",
        "hash",
        "sha",
    )

    assert loaded is None


def test_descriptor_float16_round_trip(tmp_path: Path) -> None:
    generator = default_rng(7)
    descriptors = {
        "rig0/camera0/1000.jpg": generator.normal(size=(64, 128)).astype(float32),
        "rig0/camera0/1001.jpg": generator.normal(size=(32, 128)).astype(float32),
    }

    write_descriptors(tmp_path, descriptors)
    restored = read_descriptors(tmp_path, descriptors.keys())

    for name, descriptor in descriptors.items():
        assert restored[name].dtype == float32
        assert allclose(restored[name], descriptor, rtol=2e-3, atol=1e-3)


def test_keypoints_round_trip(tmp_path: Path) -> None:
    generator = default_rng(11)
    keypoints = {"rig0/camera0/1000.jpg": generator.normal(size=(48, 2)).astype(float32)}

    write_keypoints(tmp_path, keypoints)
    restored = read_keypoints(tmp_path, keypoints.keys())

    for name, image_keypoints in keypoints.items():
        assert array_equal(restored[name], image_keypoints)
