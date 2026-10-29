"""Tests for the per-query diagnostic payload.

The behaviour worth pinning down is attribution: the correspondence list PnP sees is flat
across every retrieved image, and these tests check that each inlier, outlier and
no-3D-point match lands back on the database image that produced it.
"""

from __future__ import annotations

from typing import Any, cast
from unittest.mock import MagicMock

import numpy as np
import pytest
from core.axis_convention import AxisConvention, change_basis_unity_from_opencv_pose
from core.calibration import CalibrationArtifact
from core.camera_config import PinholeCameraConfig
from core.lightglue import Keypoints
from core.localization_detail import MATCH_INLIER, MATCH_NO_POINT3D, MATCH_OUTLIER
from numpy.testing import assert_allclose
from pycolmap import AbsolutePoseEstimationOptions
from pycolmap import Camera as ColmapCamera
from pycolmap._core import Rigid3d, Rotation3d  # type: ignore  # noqa: PLC2701 — no public API
from scipy.spatial.transform import Rotation
from torch import tensor

from src.build_detail import PAIR_POSE_MIN_INLIERS, build_localization_detail, camera_from_map_transform
from src.build_detail import _pair_pose  # noqa: PLC2701  # pyright: ignore[reportPrivateUsage] — testing private helper

# Only reached by a pair with enough correspondences for its own PnP; the attribution tests
# below have a handful, so for them it is never used.
PNP_CAMERA = ColmapCamera(width=1024, height=768, model="PINHOLE", params=[800.0, 800.0, 512.0, 384.0])


def _identity_pose() -> Rigid3d:
    return Rigid3d(Rotation3d(np.array([0.0, 0.0, 0.0, 1.0])), np.array([0.0, 0.0, 0.0]))


def _pose_at(x: float) -> Rigid3d:
    # cam_from_world for a camera whose centre sits at (x, 0, 0) with identity rotation
    # is a pure translation of -x, since centre = -R.T @ t.
    return Rigid3d(Rotation3d(np.array([0.0, 0.0, 0.0, 1.0])), np.array([-x, 0.0, 0.0]))


def _fake_map(poses: dict[int, Rigid3d]) -> Any:
    map_stub = MagicMock()
    map_stub.image_sizes = {str(image_id): (480, 640) for image_id in poses}
    images: dict[int, Any] = {}
    for image_id, pose in poses.items():
        image = MagicMock()
        image.name = f"yaw000_up15/{image_id:06d}.jpg"
        image.cam_from_world.return_value = pose
        images[image_id] = image
    map_stub.images = images
    return map_stub


def _calibration() -> CalibrationArtifact:
    calibration = MagicMock(spec=CalibrationArtifact)
    calibration.loose_min = 0.25
    calibration.tight_min = 0.0
    return cast(CalibrationArtifact, calibration)


@pytest.fixture
def camera() -> PinholeCameraConfig:
    return PinholeCameraConfig(
        width=2048, height=1536, orientation="TOP_LEFT", fx=1600.0, fy=1600.0, cx=1024.0, cy=768.0
    )


class TestMatchAttribution:
    def _build(self, camera: PinholeCameraConfig) -> Any:
        # Two database images, two raw matches each. Image 1's first match has no 3D point;
        # every other match became a correspondence. Correspondence order follows the loop in
        # localize.py: image 1 slot 1, then image 2 slot 0, then image 2 slot 1.
        keypoints = Keypoints({
            "1": tensor([[10.0, 20.0], [30.0, 40.0]]),
            "2": tensor([[50.0, 60.0], [70.0, 80.0]]),
            "query": tensor([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]]),
        })
        match_indices = {
            ("1", "query"): (np.array([0, 1]), np.array([0, 1])),
            ("2", "query"): (np.array([0, 1]), np.array([1, 2])),
        }
        return build_localization_detail(
            map=_fake_map({1: _pose_at(3.0), 2: _pose_at(-4.0)}),
            camera=camera,
            matched_image_ids=[1, 2],
            retrieval_scores=[0.82, 0.71],
            match_indices=cast(Any, match_indices),
            keypoints=keypoints,
            correspondence_sources=[(1, 1), (2, 0), (2, 1)],
            inlier_mask=np.array([True, False, True]),
            reprojection_errors=np.array([1.5, 42.0, 2.5]),
            cam_from_world=_identity_pose(),
            pycolmap_camera=PNP_CAMERA,
            estimation_options=AbsolutePoseEstimationOptions(),
            axis_convention=AxisConvention.OPENCV,
            top_k=2,
            ransac_threshold=8.0,
            num_query_keypoints=3,
            timings={"pnp": 0.012},
            metrics=None,
            calibration=_calibration(),
            failure_reason=None,
        )

    def test_no_point3d_match_is_distinguished_from_an_outlier(self, camera: PinholeCameraConfig) -> None:
        detail = self._build(camera)
        first = detail.pairs[0]

        assert first.status == [MATCH_NO_POINT3D, MATCH_INLIER]
        # A match PnP never saw carries no residual, rather than a misleading 0.0.
        assert first.reprojection_error_px[0] == -1.0
        assert first.reprojection_error_px[1] == pytest.approx(1.5)

    def test_inliers_are_attributed_to_the_image_that_produced_them(self, camera: PinholeCameraConfig) -> None:
        detail = self._build(camera)

        assert [pair.num_inliers for pair in detail.pairs] == [1, 1]
        assert [pair.num_correspondences for pair in detail.pairs] == [1, 2]
        # The second image matched twice but only one survived RANSAC.
        assert detail.pairs[1].status == [MATCH_OUTLIER, MATCH_INLIER]
        assert detail.pairs[1].inlier_ratio == pytest.approx(0.5)

    def test_keypoint_coordinates_pair_query_to_database(self, camera: PinholeCameraConfig) -> None:
        detail = self._build(camera)

        # Image 2 slot 0 matched database keypoint 0 against query keypoint 1.
        assert detail.pairs[1].database_xy[0] == [50.0, 60.0]
        assert detail.pairs[1].query_xy[0] == [3.0, 4.0]

    def test_median_reprojection_error_uses_only_that_pair_inliers(self, camera: PinholeCameraConfig) -> None:
        detail = self._build(camera)

        assert detail.pairs[0].reprojection_error_median == pytest.approx(1.5)
        assert detail.pairs[1].reprojection_error_median == pytest.approx(2.5)

    def test_distance_to_each_database_camera(self, camera: PinholeCameraConfig) -> None:
        detail = self._build(camera)

        # Query camera is at the origin; the two database cameras sit 3m and 4m away.
        assert detail.pairs[0].distance_m == pytest.approx(3.0)
        assert detail.pairs[1].distance_m == pytest.approx(4.0)
        # Identical rotations, so the optical axes agree.
        assert detail.pairs[0].view_angle_deg == pytest.approx(0.0, abs=1e-6)

    def test_reports_the_canonicalized_intrinsics_not_the_caller_supplied_ones(
        self, camera: PinholeCameraConfig
    ) -> None:
        detail = self._build(camera)

        # canonicalize_intrinsics resizes so the short side is 1024, so a 2048x1536 query is
        # reported at 1365x1024 with intrinsics scaled to match -- the frame the keypoint
        # coordinates above actually live in.
        assert detail.camera.height == 1024
        assert detail.camera.width == 1365
        assert detail.camera.fx == pytest.approx(1600.0 * 1365 / 2048, rel=1e-3)

    def test_timings_are_reported_in_milliseconds(self, camera: PinholeCameraConfig) -> None:
        detail = self._build(camera)

        assert detail.timings_ms["pnp"] == pytest.approx(12.0)

    def test_pooled_pose_is_reported_and_thin_pairs_get_none_of_their_own(self, camera: PinholeCameraConfig) -> None:
        detail = self._build(camera)

        assert detail.camera_from_map_transform is not None
        assert detail.camera_from_map_transform.rotation.w == pytest.approx(1.0)
        # One or two correspondences each: far too few for a pose a pair could stand behind.
        assert [pair.camera_from_map_transform for pair in detail.pairs] == [None, None]
        assert [pair.pose_num_inliers for pair in detail.pairs] == [0, 0]


class TestFailedAttempt:
    def test_pairs_survive_with_no_pose_and_no_metrics(self, camera: PinholeCameraConfig) -> None:
        keypoints = Keypoints({"1": tensor([[10.0, 20.0]]), "query": tensor([[1.0, 2.0]])})
        detail = build_localization_detail(
            map=_fake_map({1: _pose_at(1.0)}),
            camera=camera,
            matched_image_ids=[1],
            retrieval_scores=[0.4],
            match_indices=cast(Any, {("1", "query"): (np.array([0]), np.array([0]))}),
            keypoints=keypoints,
            correspondence_sources=[],
            inlier_mask=None,
            reprojection_errors=None,
            cam_from_world=None,
            pycolmap_camera=PNP_CAMERA,
            estimation_options=AbsolutePoseEstimationOptions(),
            axis_convention=AxisConvention.OPENCV,
            top_k=1,
            ransac_threshold=8.0,
            num_query_keypoints=1,
            timings={"aliked": 0.03},
            metrics=None,
            calibration=_calibration(),
            failure_reason="No matching keypoints found",
        )

        assert detail.failure_reason == "No matching keypoints found"
        assert detail.gate is None
        # Retrieval still chose a candidate, and that is the diagnostic: the query matched
        # something, it just never produced a usable 2D-3D correspondence.
        assert detail.pairs[0].retrieval_score == pytest.approx(0.4)
        assert detail.pairs[0].status == [MATCH_NO_POINT3D]
        # Without a pose there is nothing to measure a distance against.
        assert detail.pairs[0].distance_m is None
        assert detail.camera_from_map_transform is None


def _pnp_pose() -> Rigid3d:
    rotation = Rotation.from_euler("xyz", [5.0, -20.0, 3.0], degrees=True)
    return Rigid3d(Rotation3d(np.asarray(rotation.as_quat(), dtype=np.float64)), np.array([0.3, -0.1, 2.0]))


def _observations(count: int, seed: int = 0) -> tuple[list[Any], list[Any]]:
    """Map points in front of `_pnp_pose()` and their exact projections."""
    pose = _pnp_pose()
    rng = np.random.default_rng(seed)
    in_camera = np.column_stack([rng.uniform(-2, 2, count), rng.uniform(-1.5, 1.5, count), rng.uniform(4, 9, count)])
    world = (in_camera - pose.translation) @ pose.rotation.matrix()
    pixels = PNP_CAMERA.img_from_cam(cam_points=in_camera)
    return list(pixels), list(world)


class TestPairPose:
    def test_recovers_the_pose_its_correspondences_imply(self) -> None:
        pixels, world = _observations(60)
        result = _pair_pose(pixels, world, PNP_CAMERA, AbsolutePoseEstimationOptions())

        assert result is not None
        estimate, inliers = result
        assert inliers == 60
        assert_allclose(estimate.rotation.matrix(), _pnp_pose().rotation.matrix(), atol=1e-6)
        assert_allclose(estimate.translation, _pnp_pose().translation, atol=1e-6)

    def test_too_few_correspondences_give_no_pose(self) -> None:
        pixels, world = _observations(PAIR_POSE_MIN_INLIERS - 1)

        assert _pair_pose(pixels, world, PNP_CAMERA, AbsolutePoseEstimationOptions()) is None

    def test_too_few_inliers_give_no_pose(self) -> None:
        # Enough correspondences, but nearly all of them nonsense: the handful that agree must
        # not be passed off as this pair's pose.
        pixels, world = _observations(40)
        rng = np.random.default_rng(1)
        for i in range(PAIR_POSE_MIN_INLIERS - 4, 40):
            pixels[i] = rng.uniform([0, 0], [1024, 768])

        assert _pair_pose(pixels, world, PNP_CAMERA, AbsolutePoseEstimationOptions()) is None


class TestCameraFromMapTransform:
    def test_opencv_passes_the_pose_through(self) -> None:
        transform = camera_from_map_transform(_pnp_pose(), AxisConvention.OPENCV)
        t, q = transform.translation, transform.rotation

        assert_allclose([t.x, t.y, t.z], _pnp_pose().translation)
        assert_allclose(Rotation.from_quat([q.x, q.y, q.z, q.w]).as_matrix(), _pnp_pose().rotation.matrix(), atol=1e-12)

    def test_unity_changes_basis_as_the_response_does(self) -> None:
        transform = camera_from_map_transform(_pnp_pose(), AxisConvention.UNITY)
        translation, rotation = change_basis_unity_from_opencv_pose(
            _pnp_pose().translation, _pnp_pose().rotation.matrix()
        )
        t, q = transform.translation, transform.rotation

        assert_allclose([t.x, t.y, t.z], translation)
        assert_allclose(Rotation.from_quat([q.x, q.y, q.z, q.w]).as_matrix(), rotation, atol=1e-12)
