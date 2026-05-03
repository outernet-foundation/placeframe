from __future__ import annotations

import math
from pathlib import Path

from numpy import interp
from pydantic import BaseModel

from .localization_metrics import Confidence

SCHEMA_VERSION = 1


class CalibrationLoadError(RuntimeError):
    pass


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
    is_indoor: float

    @classmethod
    def zeros(cls) -> Features:
        return cls(
            log_inliers=0.0,
            inlier_ratio=0.0,
            reproj_err_norm=0.0,
            inlier_coverage=0.0,
            log_num_matches=0.0,
            log_map_image_count=0.0,
            log_map_point_count=0.0,
            map_avg_track_length=0.0,
            log_map_bounding_volume_m3=0.0,
            map_viewpoint_diversity=0.0,
            is_indoor=0.0,
        )


FEATURE_NAMES: tuple[str, ...] = tuple(Features.model_fields.keys())


class ToleranceModel(BaseModel):
    logistic_weights: list[float]
    logistic_intercept: float
    logistic_feature_names: list[str]
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

    _validate_feature_names(calibration, path)
    return calibration


def _validate_feature_names(calibration: CalibrationArtifact, path: Path) -> None:
    expected = list(FEATURE_NAMES)
    for label, model in (("tight", calibration.tight), ("loose", calibration.loose)):
        names = model.logistic_feature_names
        if names != expected:
            raise CalibrationLoadError(
                f"Calibration {label} feature-name mismatch in {path}.\n"
                f"  File:     {names}\n"
                f"  Expected: {expected}\n"
                "The artifact was fit against a different feature set than this build "
                "of core.calibration.Features defines. Refit and redeploy."
            )


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def _apply_tolerance(model: ToleranceModel, features: Features) -> float:
    feature_dict = features.model_dump()
    logit = model.logistic_intercept
    for name, weight in zip(model.logistic_feature_names, model.logistic_weights, strict=True):
        logit += weight * feature_dict[name]
    raw = _sigmoid(logit)
    if not model.isotonic_x_breakpoints:
        return raw
    return float(interp(raw, model.isotonic_x_breakpoints, model.isotonic_y_breakpoints))


def apply_global_calibration(calibration: CalibrationArtifact, features: Features) -> Confidence:
    return Confidence(
        tight=_apply_tolerance(calibration.tight, features),
        loose=_apply_tolerance(calibration.loose, features),
        is_calibrated=True,
    )
