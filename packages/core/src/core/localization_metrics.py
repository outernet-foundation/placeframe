from pydantic import BaseModel


class LocalizationMetrics(BaseModel):
    inlier_ratio: float
    reprojection_error_median: float
