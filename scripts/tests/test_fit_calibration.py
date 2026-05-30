from __future__ import annotations

from datetime import datetime, timezone
from itertools import pairwise
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest
from core.calibration import CalibrationArtifact, Features, RawMapMetrics
from numpy import asarray, eye, exp, float64
from numpy.random import default_rng

from placeframe_api_client import LocalizationEvaluationRead

from scripts.fit_calibration import (
    CorpusRow,
    fit_calibration_from_corpus,
    fit_logistic_with_isotonic,
)
from scripts.held_out_selection import HeldOutSelectionOptions, StrideHeldOutSelector


_FIXED_MAP_METRICS = RawMapMetrics(
    map_image_count=95,
    map_point_count=20000,
    map_avg_track_length=4.5,
    map_viewpoint_diversity=0.6,
)


def _make_row(
    *,
    succeeded: bool = True,
    err_t_m: float | None = 0.02,
    err_r_deg: float | None = 0.5,
    inlier_ratio: float = 0.6,
    num_inliers: int = 200,
    pnp_covariance: list[Any] | None = None,
    se3_residual: list[Any] | None = None,
) -> CorpusRow:
    now = datetime.now(timezone.utc)
    evaluation = LocalizationEvaluationRead(
        reconstruction_id=uuid4(),
        id=uuid4(),
        ransac_threshold=0.0,
        frame_timestamp=0,
        updated_at=now,
        created_at=now,
        retrieval_top_k=0,
        pipeline_version="test",
        succeeded=succeeded,
        inlier_ratio=inlier_ratio,
        reproj_error_median=1.2,
        num_inliers=num_inliers,
        num_correspondences=400,
        num_matches=350,
        inlier_coverage=0.4,
        query_image_diagonal_px=1500.0,
        err_t_m=err_t_m,
        err_r_deg=err_r_deg,
        pnp_covariance=pnp_covariance,
        se3_residual=se3_residual,
    )
    return CorpusRow(evaluation=evaluation, map_metrics=_FIXED_MAP_METRICS)


class TestFitLogisticWithIsotonic:
    def test_separable_features_recover_perfect_accuracy(self):
        rng = default_rng(0)
        n = 200
        feature_count = len(Features.model_fields)
        successes = rng.normal(loc=2.0, size=(n // 2, feature_count))
        failures = rng.normal(loc=-2.0, size=(n // 2, feature_count))
        features = asarray([*successes, *failures], dtype=float64)
        labels = asarray([1.0] * (n // 2) + [0.0] * (n // 2), dtype=float64)

        tolerance = fit_logistic_with_isotonic(features, labels)

        weight_vector = asarray(list(tolerance.logistic_weights.model_dump().values()), dtype=float64)
        assert weight_vector.size == feature_count
        assert len(tolerance.isotonic_x_breakpoints) >= 2
        logits = features @ weight_vector + tolerance.logistic_intercept
        predictions = 1.0 / (1.0 + exp(-logits))
        accuracy = float(((predictions >= 0.5) == labels).mean())
        assert accuracy >= 0.95

    def test_single_class_collapses_to_constant(self):
        feature_count = len(Features.model_fields)
        features = default_rng(0).normal(size=(20, feature_count))
        labels_all_success = asarray([1.0] * 20, dtype=float64)

        tolerance = fit_logistic_with_isotonic(features, labels_all_success)

        assert all(w == 0.0 for w in tolerance.logistic_weights.model_dump().values())
        assert tolerance.logistic_intercept > 10.0


class TestFitCalibrationFromCorpus:
    def _make_corpus(self, n_success: int = 8, n_failure: int = 4) -> list[CorpusRow]:
        rng = default_rng(0)
        identity_6 = eye(6, dtype=float64)
        rows: list[CorpusRow] = []
        for _ in range(n_success):
            cov = (rng.normal(size=(6, 6)) @ rng.normal(size=(6, 6)).T + 1e-3 * identity_6).tolist()
            res = (rng.normal(size=6) * 0.01).tolist()
            rows.append(
                _make_row(
                    err_t_m=0.02,
                    err_r_deg=0.3,
                    inlier_ratio=0.7,
                    num_inliers=300,
                    pnp_covariance=cov,
                    se3_residual=res,
                )
            )
        for _ in range(n_failure):
            cov = (rng.normal(size=(6, 6)) @ rng.normal(size=(6, 6)).T + 1e-3 * identity_6).tolist()
            res = (rng.normal(size=6) * 0.5).tolist()
            rows.append(
                _make_row(
                    err_t_m=0.5,
                    err_r_deg=10.0,
                    inlier_ratio=0.1,
                    num_inliers=50,
                    pnp_covariance=cov,
                    se3_residual=res,
                )
            )
        return rows

    def test_produces_artifact_with_all_required_blocks(self):
        artifact = fit_calibration_from_corpus(self._make_corpus(), pipeline_version="abc123")

        assert artifact.schema_version == 2
        assert artifact.pipeline_version == "abc123"
        assert artifact.sigma_meas_alpha > 0
        assert artifact.sample_count == 12

    def test_round_trip_through_disk(self, tmp_path: Path):
        artifact = fit_calibration_from_corpus(self._make_corpus(), pipeline_version="def456")
        out = tmp_path / "global.json"
        artifact.write(out)

        loaded = CalibrationArtifact.read(out)

        assert loaded.pipeline_version == artifact.pipeline_version
        assert loaded.sigma_meas_alpha == pytest.approx(artifact.sigma_meas_alpha)
        assert loaded.tight.logistic_weights == artifact.tight.logistic_weights
        assert loaded.sample_count == 12

    def test_no_usable_rows_raises(self):
        with pytest.raises(RuntimeError, match="No usable rows"):
            fit_calibration_from_corpus([], pipeline_version="x")


class TestStrideHeldOutSelector:
    def test_picks_evenly_spaced_timestamps(self):
        timestamps = list(range(1_700_000_000_000, 1_700_000_000_500))
        frames_csv = "timestamp,tx,ty,tz,qx,qy,qz,qw\n" + "".join(f"{ts},0,0,0,0,0,0,1\n" for ts in timestamps)

        selected = StrideHeldOutSelector()(frames_csv, HeldOutSelectionOptions(target_count=10))

        assert len(selected) == 10
        assert selected[0] == 1_700_000_000_025
        for prev, curr in pairwise(selected):
            assert curr - prev == 50

    def test_empty_input_returns_empty(self):
        frames_csv = "timestamp,tx,ty,tz,qx,qy,qz,qw\n"
        assert StrideHeldOutSelector()(frames_csv, HeldOutSelectionOptions(target_count=100)) == []

    def test_target_count_exceeds_available_falls_back_to_stride_one(self):
        timestamps = [1, 2, 3, 4, 5]
        frames_csv = "timestamp,tx,ty,tz,qx,qy,qz,qw\n" + "".join(f"{ts},0,0,0,0,0,0,1\n" for ts in timestamps)

        selected = StrideHeldOutSelector()(frames_csv, HeldOutSelectionOptions(target_count=100))

        assert selected == timestamps
