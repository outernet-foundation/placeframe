from __future__ import annotations

import math
import sys
from pathlib import Path

from numpy import interp, log1p
from pydantic import BaseModel


SCHEMA_VERSION = 2

# Sentinel `pipeline_version` value that bypasses the pipeline-version check in
# `load_global_calibration`. Use only with placeholder calibrations whose values
# don't depend on the inference pipeline (zeroed weights, fixed sigma_meas
# constants). A real calibration fit against a real corpus must pin to the
# localizer image's CONTEXT_SHA so any pipeline change forces a paired refit.
PLACEHOLDER_PIPELINE_VERSION = "placeholder"


class CalibrationLoadError(RuntimeError):
    pass


class RawLocalizationMetrics(BaseModel):
    num_inliers: int
    inlier_ratio: float
    reproj_error_median: float
    inlier_coverage: float
    num_matches: int
    query_image_diagonal_px: float


class RawMapMetrics(BaseModel):
    map_image_count: int
    map_point_count: int
    map_avg_track_length: float
    map_bounding_volume_m3: float
    map_viewpoint_diversity: float


class Features(BaseModel):
    log_inliers: float
    inlier_ratio: float
    reproj_err_norm: float
    inlier_coverage: float
    log_num_matches: float
    log_map_image_count: float
    log_map_point_count: float
    map_avg_track_length: float
    log_map_bounding_volume_m3: float
    map_viewpoint_diversity: float

    @classmethod
    def zeros(cls) -> Features:
        return cls(**dict.fromkeys(cls.model_fields, 0.0))

    @classmethod
    def compute(cls, *, localization: RawLocalizationMetrics, map_metrics: RawMapMetrics) -> Features:
        return cls(
            log_inliers=float(log1p(localization.num_inliers)),
            inlier_ratio=localization.inlier_ratio,
            reproj_err_norm=localization.reproj_error_median / localization.query_image_diagonal_px,
            inlier_coverage=localization.inlier_coverage,
            log_num_matches=float(log1p(localization.num_matches)),
            log_map_image_count=float(log1p(map_metrics.map_image_count)),
            log_map_point_count=float(log1p(map_metrics.map_point_count)),
            map_avg_track_length=map_metrics.map_avg_track_length,
            log_map_bounding_volume_m3=float(log1p(map_metrics.map_bounding_volume_m3)),
            map_viewpoint_diversity=map_metrics.map_viewpoint_diversity,
        )


class ToleranceModel(BaseModel):
    logistic_weights: Features
    logistic_intercept: float
    isotonic_x_breakpoints: list[float]
    isotonic_y_breakpoints: list[float]


class CalibrationArtifact(BaseModel):
    schema_version: int
    pipeline_version: str
    fit_at: str
    fit_by: str
    sample_count: int
    tight: ToleranceModel
    loose: ToleranceModel
    sigma_meas_alpha: float
    sigma_meas_beta: float
    loose_min: float
    tight_min: float

    def write(self, path: Path) -> None:
        path.write_text(self.model_dump_json(indent=2) + "\n", encoding="utf-8")

    @classmethod
    def read(cls, path: Path) -> CalibrationArtifact:
        return cls.model_validate_json(path.read_text(encoding="utf-8"))


def load_global_calibration(path: Path, expected_pipeline_version: str) -> CalibrationArtifact:
    if not path.exists():
        raise CalibrationLoadError(
            f"Global calibration not found at {path}. "
            f"Expected pipeline version: {expected_pipeline_version}. "
            f"Run scripts/fit_calibration.py against this pipeline and commit "
            f"the resulting config/calibration/global.json."
        )

    calibration = CalibrationArtifact.read(path)

    if calibration.schema_version != SCHEMA_VERSION:
        raise CalibrationLoadError(
            f"Unsupported calibration schema_version {calibration.schema_version} "
            f"in {path}. Localizer expects schema_version {SCHEMA_VERSION}."
        )

    if calibration.pipeline_version == PLACEHOLDER_PIPELINE_VERSION:
        print(
            f"WARNING: loading placeholder calibration from {path}. "
            f"Pipeline-version check bypassed (expected {expected_pipeline_version}). "
            "Tight/loose confidence gates are no-ops; outputs are not trustworthy. "
            "Refit via scripts/fit_calibration.py before relying on calibrated confidences.",
            file=sys.stderr,
            flush=True,
        )
        return calibration

    if calibration.pipeline_version != expected_pipeline_version:
        raise CalibrationLoadError(
            "Global calibration pipeline-version mismatch.\n"
            f"  Calibration file: {path}\n"
            f"  File version:     {calibration.pipeline_version}\n"
            f"  Expected version: {expected_pipeline_version}\n"
            "Refit calibration against the new pipeline "
            "(scripts/fit_calibration.py), commit the updated artifact, "
            "and redeploy."
        )

    return calibration


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def _apply_tolerance(model: ToleranceModel, features: Features) -> float:
    weights = model.logistic_weights.model_dump()
    feature_values = features.model_dump()
    logit = model.logistic_intercept + sum(weights[name] * feature_values[name] for name in feature_values)
    raw = _sigmoid(logit)
    if not model.isotonic_x_breakpoints:
        return raw
    return float(interp(raw, model.isotonic_x_breakpoints, model.isotonic_y_breakpoints))


def apply_global_calibration(calibration: CalibrationArtifact, features: Features) -> tuple[float, float, bool]:
    tight = _apply_tolerance(calibration.tight, features)
    loose = _apply_tolerance(calibration.loose, features)
    return tight, loose, True
