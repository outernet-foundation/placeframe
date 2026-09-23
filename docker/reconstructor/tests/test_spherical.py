from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from core.axis_convention import AxisConvention
from core.camera_config import PinholeCameraConfig, SphericalCameraConfig
from core.capture_session_manifest import RigCameraConfig, RigConfig
from core.image_preprocess import LOCAL_FEATURE_RESIZE_SHORTER_SIDE
from core.reconstruction_options import ReconstructionOptions
from core.transform import Float3, Float4
from panorama import projection
from PIL import Image as PILImage
from reconstructor.rig import Rig
from reconstructor.spherical import inside_image_circle, render_spherical_views
from torch import tensor

FRAMES_CSV = (
    "timestamp,tx,ty,tz,qx,qy,qz,qw\n"
    "1700000000001,0.0,0.0,0.0,0.0,0.0,0.0,1.0\n"
    "1700000000002,1.0,0.0,0.0,0.0,0.0,0.0,1.0"
)


def spherical_rig(camera_id: str = "camera0") -> RigConfig:
    return RigConfig(
        id="rig0",
        cameras=[
            RigCameraConfig(
                id=camera_id,
                ref_sensor=True,
                rotation=Float4(w=1.0, x=0.0, y=0.0, z=0.0),
                translation=Float3(x=0.0, y=0.0, z=0.0),
                camera_config=SphericalCameraConfig(width=1024, height=512, orientation="TOP_LEFT"),
            )
        ],
    )


def build(rig_config: RigConfig, **option_overrides: object) -> Rig:
    return Rig(
        rig_config,
        AxisConvention.OPENCV,
        FRAMES_CSV,
        options=ReconstructionOptions(**option_overrides),  # pyright: ignore[reportArgumentType]
    )


def test_a_spherical_camera_becomes_one_camera_per_view() -> None:
    rig = build(spherical_rig())

    assert sorted(rig.cameras) == ["camera0_A", "camera0_B", "camera0_C", "camera0_D"]
    for _, camera in rig.cameras.values():
        assert camera.model.name == "OPENCV_FISHEYE"
        # Views are square and the pipeline canonicalises every image to this size.
        assert (camera.width, camera.height) == (LOCAL_FEATURE_RESIZE_SHORTER_SIDE, LOCAL_FEATURE_RESIZE_SHORTER_SIDE)
        assert list(camera.params) == pytest.approx(projection.camera_params(LOCAL_FEATURE_RESIZE_SHORTER_SIDE, 150.0))
    # Not a multi-camera rig in the sense that matters: that flag means a
    # baseline anchors scale, and views of one sphere share a centre.
    assert not rig.is_multi_camera
    assert rig.ref_colmap_camera_id == "camera0_A"


def test_the_views_are_a_rig_of_rotations_about_one_centre() -> None:
    rig = build(spherical_rig())
    cameras = {camera.image_prefix: camera for camera in rig.colmap_rig_config.cameras}

    assert sorted(cameras) == [f"rig0/camera0_{name}/" for name in "ABCD"]
    assert sum(camera.ref_sensor for camera in cameras.values()) == 1
    reference = projection.TETRAHEDRON[0]
    for view in projection.TETRAHEDRON:
        camera = cameras[f"rig0/camera0_{view.name}/"]
        assert camera.cam_from_rig is not None
        assert np.allclose(camera.cam_from_rig.translation, 0.0)
        assert np.allclose(camera.cam_from_rig.rotation.matrix(), projection.cam_from_rig(view, reference), atol=1e-9)
    assert cameras[f"rig0/camera0_{reference.name}/"].ref_sensor


def test_frame_poses_move_into_the_reference_view_frame() -> None:
    """The reference view becomes COLMAP's rig frame, so rig-local quantities
    from the capture have to be restated in it; positions are untouched because
    every view shares the sphere's centre."""
    spherical = build(spherical_rig())
    pinhole = Rig(
        RigConfig(
            id="rig0",
            cameras=[
                RigCameraConfig(
                    id="camera0",
                    ref_sensor=True,
                    rotation=Float4(w=1.0, x=0.0, y=0.0, z=0.0),
                    translation=Float3(x=0.0, y=0.0, z=0.0),
                    camera_config=PinholeCameraConfig(
                        width=640, height=480, orientation="TOP_LEFT", fx=500.0, fy=500.0, cx=320.0, cy=240.0
                    ),
                )
            ],
        ),
        AxisConvention.OPENCV,
        FRAMES_CSV,
    )

    rotation = projection.opencv_from_cam(projection.TETRAHEDRON[0]).T
    assert np.allclose(spherical.rig_from_manifest_rig, rotation)
    # a rotation, not a reflection: panorama axes are y-up, capture axes y-down
    assert np.linalg.det(rotation) == pytest.approx(1.0)
    assert np.allclose(pinhole.rig_from_manifest_rig, np.eye(3))

    for frame_id, pose in spherical.frame_poses.items():
        reference_pose = pinhole.frame_poses[frame_id]
        assert np.allclose(pose.translation, reference_pose.translation)
        assert np.allclose(pose.gravity_in_rig_local, rotation @ reference_pose.gravity_in_rig_local)
        assert np.allclose(pose.rotation.matrix(), reference_pose.rotation.matrix() @ rotation.T)


def test_the_layout_and_field_of_view_are_options() -> None:
    rig = build(spherical_rig(), spherical_layout="cube", spherical_view_fov_deg=160.0)
    assert sorted(rig.cameras) == sorted(f"camera0_{view.name}" for view in projection.CUBE)
    _, camera = next(iter(rig.cameras.values()))
    assert list(camera.params) == pytest.approx(projection.camera_params(LOCAL_FEATURE_RESIZE_SHORTER_SIDE, 160.0))


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"spherical_view_fov_deg": 200.0}, "under 180 degrees"),
        ({"spherical_view_fov_deg": 0.0}, "under 180 degrees"),
    ],
)
def test_a_view_wider_than_a_camera_model_can_represent_is_rejected(overrides: dict[str, float], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        build(spherical_rig(), **overrides)


def test_a_sphere_mixed_with_other_cameras_is_rejected() -> None:
    rig_config = spherical_rig()
    rig_config.cameras.append(
        RigCameraConfig(
            id="camera1",
            ref_sensor=False,
            rotation=Float4(w=1.0, x=0.0, y=0.0, z=0.0),
            translation=Float3(x=0.1, y=0.0, z=0.0),
            camera_config=PinholeCameraConfig(
                width=640, height=480, orientation="TOP_LEFT", fx=500.0, fy=500.0, cx=320.0, cy=240.0
            ),
        )
    )
    with pytest.raises(ValueError, match="mixes a spherical camera"):
        build(rig_config)


def test_a_sideways_sphere_is_rejected() -> None:
    rig_config = spherical_rig()
    rig_config.cameras[0].camera_config = SphericalCameraConfig(width=1024, height=512, orientation="RIGHT_TOP")
    with pytest.raises(ValueError, match="must be upright"):
        build(rig_config)


def test_rendering_writes_one_view_per_frame(tmp_path: Path) -> None:
    rig = build(spherical_rig(), spherical_view_size=64)
    source = tmp_path / "rig0" / "camera0"
    source.mkdir(parents=True)
    # A smooth image: JPEG mangles random noise, which would swamp the comparison.
    ys, xs = np.mgrid[0:256, 0:512]
    frame = np.stack([xs % 256, ys, (xs + ys) % 256], axis=-1).astype(np.uint8)
    for frame_id in rig.frame_poses:
        PILImage.fromarray(frame).save(source / f"{frame_id}.jpg", quality=95)

    written = render_spherical_views(rig, tmp_path)

    assert written == len(rig.frame_poses) * len(projection.TETRAHEDRON)
    for frame_id in rig.frame_poses:
        for view in projection.TETRAHEDRON:
            path = tmp_path / "rig0" / f"camera0_{view.name}" / f"{frame_id}.jpg"
            with PILImage.open(path) as rendered:
                assert rendered.size == (64, 64)
    # and the rendering is the package's, not a reimplementation
    with PILImage.open(tmp_path / "rig0" / "camera0_A" / f"{next(iter(rig.frame_poses))}.jpg") as rendered:
        written_view = np.asarray(rendered.convert("RGB"), dtype=np.int16)
    expected = projection.render(frame, projection.view_map(512, 256, projection.TETRAHEDRON[0], 64, 150.0))
    assert np.abs(written_view - expected.astype(np.int16)).mean() < 6  # jpeg round-trip


def test_rendering_a_capture_that_is_not_spherical_does_nothing(tmp_path: Path) -> None:
    rig = Rig(
        RigConfig(
            id="rig0",
            cameras=[
                RigCameraConfig(
                    id="camera0",
                    ref_sensor=True,
                    rotation=Float4(w=1.0, x=0.0, y=0.0, z=0.0),
                    translation=Float3(x=0.0, y=0.0, z=0.0),
                    camera_config=PinholeCameraConfig(
                        width=640, height=480, orientation="TOP_LEFT", fx=500.0, fy=500.0, cx=320.0, cy=240.0
                    ),
                )
            ],
        ),
        AxisConvention.OPENCV,
        FRAMES_CSV,
    )
    assert render_spherical_views(rig, tmp_path) == 0
    assert not list(tmp_path.iterdir())


def test_keypoints_on_the_image_circle_edge_are_dropped() -> None:
    width = 100
    keypoints = tensor([
        [50.0, 50.0],  # centre
        [30.0, 50.0],  # inside
        [1.0, 50.0],  # on the rim, against the black surround
        [50.0, 99.0],  # on the rim
    ])
    assert inside_image_circle(keypoints, width).tolist() == [True, True, False, False]
