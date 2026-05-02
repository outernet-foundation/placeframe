from pydantic import BaseModel


class Confidence(BaseModel):
    tight: float
    loose: float
    is_calibrated: bool


class LocalizationMetrics(BaseModel):
    inlier_ratio: float
    reprojection_error_median: float
    num_inliers: int
    num_correspondences: int
    num_matches: int
    inlier_coverage: float
    confidence: Confidence
    # 6x6 measurement covariance in se(3) tangent coordinates that the frontend filter
    # consumes directly as Σ_meas. Derived from the inverse PnP Hessian and scaled by
    # confidence; the precise scaling is a calibration concern owned by the localizer.
    measurement_covariance: list[list[float]]
    # Raw 6x6 inverse PnP Hessian (se(3) tangent), pre-Σ_meas-scaling. Surfaced so
    # `scripts/fit_calibration.py` can fit the Σ_meas α/β scalars against held-out residuals.
    pnp_covariance: list[list[float]]
    pipeline_version: str
