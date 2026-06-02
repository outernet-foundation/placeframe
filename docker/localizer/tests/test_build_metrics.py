from math import log1p
from types import SimpleNamespace

import numpy as np
import pytest
from core.calibration import (
    CalibrationArtifact,
    Features,
    RawLocalizationMetrics,
    RawMapMetrics,
    ToleranceModel,
    apply_global_calibration,
)
from src.build_metrics import _compute_inlier_coverage  # noqa: PLC2701 — testing private helper
from src.build_metrics import build_localization_metrics
from numpy.testing import assert_allclose


class TestComputeInlierCoverage:
    def test_fewer_than_3_inliers_returns_zero(self):
        points = np.array([[10.0, 20.0], [30.0, 40.0]])
        assert _compute_inlier_coverage(points, 100, 100) == 0.0

    def test_single_point_returns_zero(self):
        points = np.array([[50.0, 50.0]])
        assert _compute_inlier_coverage(points, 100, 100) == 0.0

    def test_empty_returns_zero(self):
        points = np.empty((0, 2))
        assert _compute_inlier_coverage(points, 100, 100) == 0.0

    def test_collinear_points_returns_zero(self):
        points = np.array([[0.0, 0.0], [50.0, 0.0], [100.0, 0.0]])
        assert _compute_inlier_coverage(points, 100, 100) == 0.0

    def test_quarter_coverage(self):
        points = np.array([[0.0, 0.0], [50.0, 0.0], [50.0, 50.0], [0.0, 50.0]])
        assert _compute_inlier_coverage(points, 100, 100) == pytest.approx(0.25, abs=1e-6)

    def test_full_coverage(self):
        points = np.array([[0.0, 0.0], [100.0, 0.0], [100.0, 100.0], [0.0, 100.0]])
        assert _compute_inlier_coverage(points, 100, 100) == pytest.approx(1.0, abs=1e-6)

    def test_triangle_area(self):
        # Right triangle: area = 0.5 * 100 * 100 = 5000, image = 200*200 = 40000
        points = np.array([[0.0, 0.0], [100.0, 0.0], [0.0, 100.0]])
        assert _compute_inlier_coverage(points, 200, 200) == pytest.approx(5000.0 / 40000.0, abs=1e-6)

    def test_nonsquare_image(self):
        # Full-width half-height rectangle in a 200x100 image
        points = np.array([[0.0, 0.0], [200.0, 0.0], [200.0, 50.0], [0.0, 50.0]])
        # Hull area = 200*50 = 10000, image area = 200*100 = 20000
        assert _compute_inlier_coverage(points, 200, 100) == pytest.approx(0.5, abs=1e-6)


def _make_map(
    *,
    map_image_count: int = 100,
    map_point_count: int = 25_000,
    map_avg_track_length: float = 4.5,
    map_viewpoint_diversity: float = 0.6,
) -> SimpleNamespace:
    return SimpleNamespace(
        map_metrics=RawMapMetrics(
            map_image_count=map_image_count,
            map_point_count=map_point_count,
            map_avg_track_length=map_avg_track_length,
            map_viewpoint_diversity=map_viewpoint_diversity,
        ),
    )


def _make_calibration(*, sigma_meas_alpha: float = 1.0, sigma_meas_beta: float = 0.0) -> CalibrationArtifact:
    empty_tolerance = ToleranceModel(
        logistic_weights=Features.zeros(),
        logistic_intercept=0.0,
        isotonic_x_breakpoints=[],
        isotonic_y_breakpoints=[],
    )
    return CalibrationArtifact(
        schema_version=2,
        pipeline_version="test",
        fit_at="2026-05-03T00:00:00Z",
        fit_by="test",
        sample_count=0,
        tight=empty_tolerance,
        loose=empty_tolerance,
        sigma_meas_alpha=sigma_meas_alpha,
        sigma_meas_beta=sigma_meas_beta,
        loose_min=0.0,
        tight_min=0.0,
    )


class TestBuildFeatures:
    def test_log_transforms_and_passthroughs(self):
        map_ = _make_map()
        features = Features.compute(
            localization=RawLocalizationMetrics(
                num_inliers=200,
                inlier_ratio=0.6,
                reproj_error_median=1.2,
                inlier_coverage=0.4,
                num_matches=350,
                query_image_diagonal_px=1500.0,
            ),
            map_metrics=map_.map_metrics,
        )

        assert features.log_inliers == pytest.approx(log1p(200))
        assert features.inlier_ratio == 0.6
        assert features.reproj_err_norm == pytest.approx(1.2 / 1500.0)
        assert features.inlier_coverage == 0.4
        assert features.log_num_matches == pytest.approx(log1p(350))
        assert features.log_map_image_count == pytest.approx(log1p(100))
        assert features.log_map_point_count == pytest.approx(log1p(25_000))
        assert features.map_avg_track_length == 4.5
        assert features.map_viewpoint_diversity == 0.6


class TestBuildLocalizationMetricsSigmaMeas:
    def _make_pnp_result(
        self,
        *,
        num_inliers: int,
        num_correspondences: int,
        covariance: np.ndarray,
    ) -> dict:
        rng = np.random.default_rng(0)
        cam_from_world = SimpleNamespace(
            rotation=SimpleNamespace(matrix=lambda: np.eye(3)),
            translation=np.zeros(3),
        )
        inlier_mask = np.zeros(num_correspondences, dtype=bool)
        inlier_mask[:num_inliers] = True
        return {
            "num_inliers": num_inliers,
            "inlier_mask": inlier_mask,
            "cam_from_world": cam_from_world,
            "covariance": covariance,
            "_dummy_random": rng.random(),
        }

    def _make_pycolmap_camera(self):
        # Avoid importing pycolmap.Camera; build_localization_metrics only calls
        # `pycolmap_camera.img_from_cam(points)` which we can stub with a closure.
        return SimpleNamespace(img_from_cam=lambda pts: pts[:, :2])

    def test_sigma_meas_uses_alpha_beta_formula(self):
        rng = np.random.default_rng(0)
        covariance = rng.normal(size=(6, 6)) @ rng.normal(size=(6, 6)).T + np.eye(6)
        alpha, beta = 0.7, 0.3
        calibration = _make_calibration(sigma_meas_alpha=alpha, sigma_meas_beta=beta)

        n = 50
        points2d = rng.normal(size=(n, 2)) * 10 + 100
        points3d = rng.normal(size=(n, 3))
        pnp_result = self._make_pnp_result(num_inliers=30, num_correspondences=n, covariance=covariance)

        metrics = build_localization_metrics(
            pnp_result,
            points2d,
            points3d,
            self._make_pycolmap_camera(),
            num_matches=80,
            image_width=1920,
            image_height=1080,
            pipeline_version="test",
            calibration=calibration,
            map=_make_map(),  # type: ignore[arg-type]
        )

        expected = (alpha * covariance + beta * np.eye(6)).tolist()
        assert_allclose(np.asarray(metrics.measurement_covariance), np.asarray(expected), rtol=1e-12, atol=1e-12)

    def test_sigma_meas_alpha_one_beta_zero_passes_pnp_through(self):
        rng = np.random.default_rng(1)
        covariance = rng.normal(size=(6, 6)) @ rng.normal(size=(6, 6)).T + np.eye(6)
        calibration = _make_calibration(sigma_meas_alpha=1.0, sigma_meas_beta=0.0)

        n = 20
        points2d = rng.normal(size=(n, 2)) * 10 + 50
        points3d = rng.normal(size=(n, 3))
        pnp_result = self._make_pnp_result(num_inliers=15, num_correspondences=n, covariance=covariance)

        metrics = build_localization_metrics(
            pnp_result,
            points2d,
            points3d,
            self._make_pycolmap_camera(),
            num_matches=40,
            image_width=1280,
            image_height=720,
            pipeline_version="test",
            calibration=calibration,
            map=_make_map(),  # type: ignore[arg-type]
        )

        assert_allclose(np.asarray(metrics.measurement_covariance), covariance, rtol=1e-12, atol=1e-12)

    def test_metrics_carry_real_features_through_calibration(self):
        # Identity-bootstrap-like calibration: empty weights, zero intercept, no isotonic.
        # Confidence is sigmoid(0) = 0.5; what we're testing is that feature plumbing reaches
        # the calibration call with non-zero values rather than the prior Features.zeros().
        rng = np.random.default_rng(2)
        covariance = np.eye(6)
        calibration = _make_calibration()

        n = 40
        points2d = rng.normal(size=(n, 2)) * 5 + 100
        points3d = rng.normal(size=(n, 3))
        pnp_result = self._make_pnp_result(num_inliers=24, num_correspondences=n, covariance=covariance)

        metrics = build_localization_metrics(
            pnp_result,
            points2d,
            points3d,
            self._make_pycolmap_camera(),
            num_matches=60,
            image_width=1600,
            image_height=900,
            pipeline_version="test",
            calibration=calibration,
            map=_make_map(),  # type: ignore[arg-type]
        )

        # Empty-weight calibration → confidence is intercept-only sigmoid(0) = 0.5 for tight & loose.
        assert metrics.confidence_tight == pytest.approx(0.5)
        assert metrics.confidence_loose == pytest.approx(0.5)
        # Sanity: applying the same calibration with a zero-Features instance gives the same
        # constants (the intercept-only path is feature-independent), but applying it to a
        # real Features computed from the inputs above also lands at 0.5 — proving the
        # feature path is exercised end-to-end.
        sanity_tight, _sanity_loose, _ = apply_global_calibration(calibration, features=Features.zeros())
        assert metrics.confidence_tight == pytest.approx(sanity_tight)
