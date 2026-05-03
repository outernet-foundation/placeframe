from __future__ import annotations

import os
import subprocess
import tarfile
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from common.boto_clients import create_s3_client
from core.capture_session_manifest import CaptureSessionManifest
from pydantic import AnyHttpUrl, TypeAdapter
from reconstructor.rig import Rig

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client

CAPTURES_BUCKET = os.environ.get("CAPTURES_BUCKET", "dev-captures")


def _resolve_minio_endpoint() -> str | None:
    env_url = os.environ.get("MINIO_ENDPOINT_URL")
    if env_url:
        return env_url
    try:
        ip = subprocess.check_output(
            [
                "docker",
                "inspect",
                "placeframe-minio-1",
                "-f",
                '{{ (index .NetworkSettings.Networks "placeframe_default").IPAddress }}',
            ],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    if not ip:
        return None
    return f"http://{ip}:9000"


@pytest.fixture(scope="module")
def s3() -> S3Client:
    endpoint = _resolve_minio_endpoint()
    if endpoint is None:
        pytest.skip("MinIO not reachable; set MINIO_ENDPOINT_URL or run inside the placeframe stack")
    access_key = os.environ.get("MINIO_ACCESS_KEY", "admin")
    secret_key = os.environ.get("MINIO_SECRET_KEY", "password")
    return create_s3_client(TypeAdapter(AnyHttpUrl).validate_python(endpoint), access_key, secret_key)


@pytest.fixture(scope="module")
def capture_tar(s3: S3Client, tmp_path_factory: pytest.TempPathFactory) -> Path:
    listing = s3.list_objects_v2(Bucket=CAPTURES_BUCKET)
    tar_keys = [obj["Key"] for obj in listing.get("Contents", []) if obj.get("Key", "").endswith(".tar")]
    if not tar_keys:
        pytest.skip(f"No capture tars in '{CAPTURES_BUCKET}' bucket")
    tar_bytes = s3.get_object(Bucket=CAPTURES_BUCKET, Key=tar_keys[0])["Body"].read()
    tmp = tmp_path_factory.mktemp("capture")
    with tarfile.open(fileobj=BytesIO(tar_bytes), mode="r:*") as tf:
        tf.extractall(path=tmp)
    return tmp


def test_held_out_timestamp_excluded_from_frame_poses(capture_tar: Path):
    manifest = CaptureSessionManifest.model_validate_json((capture_tar / "manifest.json").read_text())
    rig_config = manifest.rigs[0]
    frames_csv = (capture_tar / f"{rig_config.id}/frames.csv").read_text()

    timestamps = [int(line.split(",")[0]) for line in frames_csv.splitlines()[1:]]
    assert len(timestamps) >= 2, "Need at least 2 frames to exercise held-out filtering"
    held_out_timestamp = timestamps[0]

    rig_with_filter = Rig(
        rig_config,
        manifest.axis_convention,
        frames_csv,
        held_out_frame_timestamps={held_out_timestamp},
    )
    rig_without_filter = Rig(rig_config, manifest.axis_convention, frames_csv)

    assert str(held_out_timestamp) not in rig_with_filter.frame_poses
    assert str(held_out_timestamp) in rig_without_filter.frame_poses
    assert len(rig_with_filter.frame_poses) == len(rig_without_filter.frame_poses) - 1
    for ts in timestamps[1:]:
        assert str(ts) in rig_with_filter.frame_poses


def test_no_held_out_argument_preserves_all_frames(capture_tar: Path):
    manifest = CaptureSessionManifest.model_validate_json((capture_tar / "manifest.json").read_text())
    rig_config = manifest.rigs[0]
    frames_csv = (capture_tar / f"{rig_config.id}/frames.csv").read_text()

    rig = Rig(rig_config, manifest.axis_convention, frames_csv)
    expected_count = len(frames_csv.splitlines()) - 1
    assert len(rig.frame_poses) == expected_count
