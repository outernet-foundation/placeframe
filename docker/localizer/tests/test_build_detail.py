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
from core.calibration import CalibrationArtifact
from core.camera_config import PinholeCameraConfig
from core.lightglue import Keypoints
from core.localization_detail import MATCH_INLIER, MATCH_NO_POINT3D, MATCH_OUTLIER
from pycolmap._core import Rigid3d, Rotation3d  # type: ignore  # noqa: PLC2701 — no public API
from torch import tensor

from src.build_detail import build_localization_detail


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
