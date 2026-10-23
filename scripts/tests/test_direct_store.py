"""A capture that goes around the API still has to pass the API's checks.

The direct-store path validates a capture tar locally with a copy of the API's
rules, and decides from size alone whether a capture needs that path. These
tests pin both against hand-built tars.
"""

from __future__ import annotations

import tarfile
from io import BytesIO
from json import dumps

import pytest
from common.limits import REQUEST_MAX_BODY_SIZE
from scripts.howard_test import direct_store_wanted, validate_capture_tar


def _tar(members: dict[str, bytes]) -> bytes:
    buffer = BytesIO()
    with tarfile.open(fileobj=buffer, mode="w") as tar:
        for name, data in members.items():
            info = tarfile.TarInfo(name=name)
            info.size = len(data)
            tar.addfile(info, BytesIO(data))
    return buffer.getvalue()


def _manifest(capture_interval_seconds: float | None) -> bytes:
    manifest = {
        "axis_convention": "OPENCV",
        "rigs": [
            {
                "id": "rig0",
                "cameras": [
                    {
                        "id": "camera0",
                        "ref_sensor": True,
                        "rotation": {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0},
                        "translation": {"x": 0.0, "y": 0.0, "z": 0.0},
                        "camera_config": {
                            "orientation": "TOP_LEFT",
                            "width": 3840,
                            "height": 1920,
                            "projection": "EQUIRECTANGULAR",
                        },
                    }
                ],
            }
        ],
    }
    if capture_interval_seconds is not None:
        manifest["capture_interval_seconds"] = capture_interval_seconds
    return dumps(manifest).encode()


def _frames_csv(timestamps_ms: list[int]) -> bytes:
    lines = ["timestamp_ms,tx,ty,tz,qx,qy,qz,qw"] + [f"{t},{i:.6f},0,0,0,0,0,1" for i, t in enumerate(timestamps_ms)]
    return ("\n".join(lines) + "\n").encode()


def test_a_well_formed_capture_passes() -> None:
    tar = _tar({"manifest.json": _manifest(1.0), "rig0/frames.csv": _frames_csv([0, 1000, 2000, 3000])})
    validate_capture_tar(tar)


def test_missing_manifest_is_rejected() -> None:
    with pytest.raises(ValueError, match=r"missing manifest\.json"):
        validate_capture_tar(_tar({"rig0/frames.csv": _frames_csv([0, 1000])}))


def test_invalid_manifest_is_rejected() -> None:
    with pytest.raises(ValueError, match=r"manifest\.json is invalid"):
        validate_capture_tar(_tar({"manifest.json": b"{}"}))


def test_not_a_tar_is_rejected() -> None:
    with pytest.raises(ValueError, match="invalid tar"):
        validate_capture_tar(b"this is not a tar")


def test_sparse_frames_fail_temporal_coverage() -> None:
    # Four frames over 30 s at a declared 1 s interval is 13% coverage, under the API's 50% floor.
    tar = _tar({"manifest.json": _manifest(1.0), "rig0/frames.csv": _frames_csv([0, 10000, 20000, 30000])})
    with pytest.raises(ValueError, match="temporal coverage"):
        validate_capture_tar(tar)


def test_no_interval_means_no_coverage_check() -> None:
    tar = _tar({"manifest.json": _manifest(None), "rig0/frames.csv": _frames_csv([0, 10000, 20000, 30000])})
    validate_capture_tar(tar)


def test_direct_is_automatic_only_past_the_limit() -> None:
    assert direct_store_wanted(None, REQUEST_MAX_BODY_SIZE) is False
    assert direct_store_wanted(None, REQUEST_MAX_BODY_SIZE + 1) is True


def test_an_explicit_choice_wins() -> None:
    assert direct_store_wanted(True, 1) is True
    assert direct_store_wanted(False, REQUEST_MAX_BODY_SIZE + 1) is False


def test_a_metadata_only_tar_keeps_just_the_metadata() -> None:
    """A reconstruction too large for the API goes in as its artifacts, stored directly, plus this:
    the import inserts the rows from metadata.json and has nothing else to upload."""
    from scripts.howard_test import metadata_only_tar

    metadata = dumps({"reconstruction": {"id": "0b1f6c1e-0000-4000-8000-000000000000"}}).encode()
    source = _tar({"metadata.json": metadata, "features.h5": b"x" * 4096, "sfm_model/images.txt": b"1 0 0 0\n"})
    with tarfile.open(fileobj=BytesIO(metadata_only_tar(source))) as tar:
        assert tar.getnames() == ["metadata.json"]
        handle = tar.extractfile("metadata.json")
        assert handle is not None and handle.read() == metadata
