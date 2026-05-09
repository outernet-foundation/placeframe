from __future__ import annotations

import pytest
from core.axis_convention import AxisConvention
from core.camera_config import PinholeCameraConfig
from core.capture_session_manifest import CaptureSessionManifest, RigCameraConfig, RigConfig
from core.transform import Float3, Float4
from reconstructor.rig import Rig


@pytest.fixture
def manifest() -> CaptureSessionManifest:
    return CaptureSessionManifest(
        axis_convention=AxisConvention.OPENCV,
        rigs=[
            RigConfig(
                id="rig0",
                cameras=[
                    RigCameraConfig(
                        id="camera0",
                        ref_sensor=True,
                        rotation=Float4(w=1.0, x=0.0, y=0.0, z=0.0),
                        translation=Float3(x=0.0, y=0.0, z=0.0),
                        camera_config=PinholeCameraConfig(
                            width=640,
                            height=480,
                            orientation="TOP_LEFT",
                            fx=500.0,
                            fy=500.0,
                            cx=320.0,
                            cy=240.0,
                        ),
                    )
                ],
            )
        ],
    )


@pytest.fixture
def frames_csv() -> str:
    header = "timestamp,tx,ty,tz,qx,qy,qz,qw"
    rows = [
        "1700000000001,0.0,0.0,0.0,0.0,0.0,0.0,1.0",
        "1700000000002,1.0,0.0,0.0,0.0,0.0,0.0,1.0",
        "1700000000003,2.0,0.0,0.0,0.0,0.0,0.0,1.0",
    ]
    return "\n".join([header, *rows])


def test_held_out_timestamp_excluded_from_frame_poses(manifest: CaptureSessionManifest, frames_csv: str):
    rig_config = manifest.rigs[0]
    timestamps = [int(line.split(",")[0]) for line in frames_csv.splitlines()[1:]]
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


def test_no_held_out_argument_preserves_all_frames(manifest: CaptureSessionManifest, frames_csv: str):
    rig_config = manifest.rigs[0]
    rig = Rig(rig_config, manifest.axis_convention, frames_csv)
    expected_count = len(frames_csv.splitlines()) - 1
    assert len(rig.frame_poses) == expected_count
