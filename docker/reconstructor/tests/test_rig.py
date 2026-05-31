from __future__ import annotations

import pytest
from core.axis_convention import AxisConvention
from core.camera_config import PinholeCameraConfig
from core.capture_session_manifest import CaptureSessionManifest, RigCameraConfig, RigConfig
from core.transform import Float3, Float4
from reconstructor.rig import Rig


def _camera(camera_id: str, ref_sensor: bool, translation: Float3) -> RigCameraConfig:
    return RigCameraConfig(
        id=camera_id,
        ref_sensor=ref_sensor,
        rotation=Float4(w=1.0, x=0.0, y=0.0, z=0.0),
        translation=translation,
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


@pytest.fixture
def manifest() -> CaptureSessionManifest:
    return CaptureSessionManifest(
        axis_convention=AxisConvention.OPENCV,
        rigs=[
            RigConfig(id="rig0", cameras=[_camera("camera0", ref_sensor=True, translation=Float3(x=0.0, y=0.0, z=0.0))])
        ],
    )


@pytest.fixture
def multi_camera_manifest() -> CaptureSessionManifest:
    return CaptureSessionManifest(
        axis_convention=AxisConvention.OPENCV,
        rigs=[
            RigConfig(
                id="rig0",
                cameras=[
                    _camera("camera0", ref_sensor=True, translation=Float3(x=0.0, y=0.0, z=0.0)),
                    _camera("camera1", ref_sensor=False, translation=Float3(x=0.12, y=0.0, z=0.0)),
                ],
            )
        ],
    )


@pytest.fixture
def legacy_priors_frames_csv() -> str:
    header = "timestamp,tx,ty,tz,qx,qy,qz,qw"
    rows = [
        "1700000000001,0.0,0.0,0.0,0.0,0.0,0.0,1.0",
        "1700000000002,1.0,0.0,0.0,0.0,0.0,0.0,1.0",
        "1700000000003,2.0,0.0,0.0,0.0,0.0,0.0,1.0",
    ]
    return "\n".join([header, *rows])


@pytest.fixture
def gravity_only_frames_csv() -> str:
    header = "timestamp_ms,gx,gy,gz"
    rows = [
        "1700000000001,0.0,1.0,0.0",
        "1700000000002,0.0,1.0,0.0",
        "1700000000003,0.0,1.0,0.0",
    ]
    return "\n".join([header, *rows])


@pytest.fixture
def position_and_gravity_frames_csv() -> str:
    header = "timestamp_ms,tx,ty,tz,gx,gy,gz"
    rows = [
        "1700000000001,0.0,0.0,0.0,0.0,1.0,0.0",
        "1700000000002,1.0,0.0,0.0,0.0,1.0,0.0",
        "1700000000003,2.0,0.0,0.0,0.0,1.0,0.0",
    ]
    return "\n".join([header, *rows])


def test_held_out_timestamp_excluded_from_frame_poses(manifest: CaptureSessionManifest, legacy_priors_frames_csv: str):
    rig_config = manifest.rigs[0]
    timestamps = [int(line.split(",")[0]) for line in legacy_priors_frames_csv.splitlines()[1:]]
    held_out_timestamp = timestamps[0]

    rig_with_filter = Rig(
        rig_config,
        manifest.axis_convention,
        legacy_priors_frames_csv,
        held_out_frame_timestamps={held_out_timestamp},
    )
    rig_without_filter = Rig(rig_config, manifest.axis_convention, legacy_priors_frames_csv)

    assert str(held_out_timestamp) not in rig_with_filter.frame_poses
    assert str(held_out_timestamp) in rig_without_filter.frame_poses
    assert len(rig_with_filter.frame_poses) == len(rig_without_filter.frame_poses) - 1
    for ts in timestamps[1:]:
        assert str(ts) in rig_with_filter.frame_poses


def test_no_held_out_argument_preserves_all_frames(manifest: CaptureSessionManifest, legacy_priors_frames_csv: str):
    rig_config = manifest.rigs[0]
    rig = Rig(rig_config, manifest.axis_convention, legacy_priors_frames_csv)
    expected_count = len(legacy_priors_frames_csv.splitlines()) - 1
    assert len(rig.frame_poses) == expected_count


def test_multi_camera_gravity_only_parses_without_translation(
    multi_camera_manifest: CaptureSessionManifest, gravity_only_frames_csv: str
):
    rig_config = multi_camera_manifest.rigs[0]
    rig = Rig(rig_config, multi_camera_manifest.axis_convention, gravity_only_frames_csv)

    assert rig.is_multi_camera
    assert len(rig.frame_poses) == 3
    for pose in rig.frame_poses.values():
        assert pose.translation is None
        assert pose.gravity_in_rig_local is not None
        assert pose.gravity_in_rig_local.tolist() == [0.0, 1.0, 0.0]


def test_multi_camera_keeps_translation_from_legacy_priors_csv(
    multi_camera_manifest: CaptureSessionManifest, legacy_priors_frames_csv: str
):
    rig_config = multi_camera_manifest.rigs[0]
    rig = Rig(rig_config, multi_camera_manifest.axis_convention, legacy_priors_frames_csv)

    assert rig.is_multi_camera
    for pose in rig.frame_poses.values():
        assert pose.translation is not None


def test_monocular_legacy_priors_schema_populates_translation(
    manifest: CaptureSessionManifest, legacy_priors_frames_csv: str
):
    rig_config = manifest.rigs[0]
    rig = Rig(rig_config, manifest.axis_convention, legacy_priors_frames_csv)

    assert not rig.is_multi_camera
    for pose in rig.frame_poses.values():
        assert pose.translation is not None
        assert pose.gravity_in_rig_local is None


def test_monocular_gravity_only_csv_is_rejected(manifest: CaptureSessionManifest, gravity_only_frames_csv: str):
    rig_config = manifest.rigs[0]
    with pytest.raises(ValueError, match="requires per-frame position priors"):
        Rig(rig_config, manifest.axis_convention, gravity_only_frames_csv)


def test_multi_camera_position_and_gravity_csv_populates_both(
    multi_camera_manifest: CaptureSessionManifest, position_and_gravity_frames_csv: str
):
    rig_config = multi_camera_manifest.rigs[0]
    rig = Rig(rig_config, multi_camera_manifest.axis_convention, position_and_gravity_frames_csv)

    assert rig.is_multi_camera
    assert len(rig.frame_poses) == 3
    for pose in rig.frame_poses.values():
        assert pose.translation is not None
        assert pose.gravity_in_rig_local is not None
        assert pose.gravity_in_rig_local.tolist() == [0.0, 1.0, 0.0]
