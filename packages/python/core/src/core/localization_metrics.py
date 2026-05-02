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
    # 6x6 pose covariance in se(3) tangent coordinates from the inverse PnP Hessian.
    covariance: list[list[float]]
    pipeline_version: str
