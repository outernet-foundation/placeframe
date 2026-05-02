from __future__ import annotations

from pathlib import Path

import pytest
from core.calibration import CalibrationArtifact
from numpy import asarray, eye, exp, float64
from numpy.random import default_rng

from scripts.fit_calibration import (
    fit_calibration_from_results,
    fit_logistic_with_isotonic,
)
from scripts.e2e_results import (
    E2EResults,
    LocalizationResult,
    ReconMetrics,
    ReconstructionResult,
)


def _make_recon(reconstruction_id: str = "recon-1") -> ReconstructionResult:
    return ReconstructionResult(
        location="loc",
        device_type="zed",
        capture_name="zed",
        config_idx=0,
        options=None,
        reconstruction_id=reconstruction_id,
        succeeded=True,
        metrics=ReconMetrics(
            total_images=100,
            registered_images=95,
            registration_rate=0.95,
            num_3d_points=20000,
            reproj_error_50th=1.0,
            reproj_error_90th=2.0,
            map_image_count=95,
            map_point_count=20000,
            map_avg_track_length=4.5,
            map_bounding_volume_m3=12.3,
            map_viewpoint_diversity=0.6,
        ),
        loc_map_id="map-1",
        is_indoor=True,
        truth_alignment_rms_residual_m=0.01,
        truth_alignment_max_residual_m=0.03,
    )


def _make_loc(
    *,
    reconstruction_id: str = "recon-1",
    succeeded: bool = True,
    err_t_m: float = 0.02,
    err_r_deg: float = 0.5,
    inlier_ratio: float = 0.6,
    num_inliers: int = 200,
    pnp_covariance: list[list[float]] | None = None,
    se3_residual: list[float] | None = None,
) -> LocalizationResult:
    return LocalizationResult(
        location="loc",
        recon_device_type="zed",
        recon_capture_name="zed",
        recon_config_idx=0,
        reconstruction_id=reconstruction_id,
        query_device_type="zed",
        query_capture_name="zed",
        query_frame_timestamp="0",
        query_image_diagonal_px=1500.0,
        is_cross_device=False,
        retrieval_top_k=5,
        ransac_threshold=12.0,
        succeeded=succeeded,
        inlier_ratio=inlier_ratio,
        reproj_error_median=1.2,
        num_inliers=num_inliers,
        num_correspondences=400,
        num_matches=350,
        inlier_coverage=0.4,
        pnp_covariance=pnp_covariance,
        err_t_m=err_t_m,
        err_r_deg=err_r_deg,
        se3_residual=se3_residual,
    )


class TestFitLogisticWithIsotonic:
    def test_separable_features_recover_perfect_accuracy(self):
        rng = default_rng(0)
        n = 200
        successes = rng.normal(loc=2.0, size=(n // 2, 11))
        failures = rng.normal(loc=-2.0, size=(n // 2, 11))
        features = asarray([*successes, *failures], dtype=float64)
        labels = asarray([1.0] * (n // 2) + [0.0] * (n // 2), dtype=float64)

        tolerance = fit_logistic_with_isotonic(features, labels)

        assert len(tolerance.logistic_weights) == 11
        assert len(tolerance.isotonic_x_breakpoints) >= 2
        # Linearly separable → very high accuracy at 0.5 threshold.
        logits = features @ asarray(tolerance.logistic_weights, dtype=float64) + tolerance.logistic_intercept
        predictions = 1.0 / (1.0 + exp(-logits))
        accuracy = float(((predictions >= 0.5) == labels).mean())
        assert accuracy >= 0.95

    def test_single_class_collapses_to_constant(self):
        features = default_rng(0).normal(size=(20, 11))
        labels_all_success = asarray([1.0] * 20, dtype=float64)

        tolerance = fit_logistic_with_isotonic(features, labels_all_success)

        assert all(w == 0.0 for w in tolerance.logistic_weights)
        assert tolerance.logistic_intercept > 10.0


class TestFitCalibrationFromResults:
    def _make_results(self, n_success: int = 8, n_failure: int = 4) -> E2EResults:
        recon = _make_recon()
        rng = default_rng(0)
        identity_6 = eye(6, dtype=float64)
        locs: list[LocalizationResult] = []
        for _ in range(n_success):
            cov = (rng.normal(size=(6, 6)) @ rng.normal(size=(6, 6)).T + 1e-3 * identity_6).tolist()
            res = (rng.normal(size=6) * 0.01).tolist()
            locs.append(
                _make_loc(
                    err_t_m=0.02, err_r_deg=0.3, inlier_ratio=0.7, num_inliers=300, pnp_covariance=cov, se3_residual=res
                )
            )
        for _ in range(n_failure):
            cov = (rng.normal(size=(6, 6)) @ rng.normal(size=(6, 6)).T + 1e-3 * identity_6).tolist()
            res = (rng.normal(size=6) * 0.5).tolist()
            locs.append(
                _make_loc(
                    err_t_m=0.5,
                    err_r_deg=10.0,
                    inlier_ratio=0.1,
                    num_inliers=50,
                    pnp_covariance=cov,
                    se3_residual=res,
                )
            )
        return E2EResults(run_timestamp="2026-05-02T00:00:00+00:00", reconstructions=[recon], localizations=locs)

    def test_produces_artifact_with_all_required_blocks(self):
        artifact = fit_calibration_from_results([self._make_results()], pipeline_version="abc123")

        assert artifact.schema_version == 1
        assert artifact.pipeline_version == "abc123"
        assert artifact.tight.logistic_feature_names
        assert artifact.loose.logistic_feature_names
        assert artifact.sigma_meas_alpha > 0
        assert artifact.sample_count == 12

    def test_round_trip_through_disk(self, tmp_path: Path):
        artifact = fit_calibration_from_results([self._make_results()], pipeline_version="def456")
        out = tmp_path / "global.json"
        artifact.write(out)

        loaded = CalibrationArtifact.read(out)

        assert loaded.pipeline_version == artifact.pipeline_version
        assert loaded.sigma_meas_alpha == pytest.approx(artifact.sigma_meas_alpha)
        assert loaded.tight.logistic_weights == artifact.tight.logistic_weights
        assert loaded.sample_count == 12

    def test_no_usable_rows_raises(self):
        empty = E2EResults(run_timestamp="t", reconstructions=[], localizations=[])
        with pytest.raises(RuntimeError, match="No usable rows"):
            fit_calibration_from_results([empty], pipeline_version="x")
