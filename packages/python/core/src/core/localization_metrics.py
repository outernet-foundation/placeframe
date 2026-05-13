from pydantic import BaseModel


# Localizer hyperparameters. The localizer falls back to these when callers omit the values, and
# fit_calibration passes them explicitly to api.localize_image and persists them on each
# localization_evaluations row. The (reconstruction_id, frame_timestamp, retrieval_top_k,
# ransac_threshold, pipeline_version) cache key in localization_evaluations relies on caller and
# fallback agreeing, so both sides must read these constants from one source.
RETRIEVAL_TOP_K_DEFAULT = 12
RANSAC_THRESHOLD_DEFAULT = 8.0


class LocalizationMetrics(BaseModel):
    inlier_ratio: float
    reprojection_error_median: float
    num_inliers: int
    num_correspondences: int
    num_matches: int
    inlier_coverage: float
    confidence_tight: float
    confidence_loose: float
    confidence_is_calibrated: bool
    measurement_covariance: list[list[float]]
    pnp_covariance: list[list[float]]
    pipeline_version: str
