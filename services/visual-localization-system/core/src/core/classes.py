from __future__ import annotations

from pydantic import BaseModel

from .transform import Vector3


class Point3D(BaseModel):
    x: float
    y: float
    z: float


class Color(BaseModel):
    r: int
    g: int
    b: int


class PointCloudPoint(BaseModel):
    position: Vector3  # uses transform.position (rotation ignored for points)
    color: Color


# @dataclass
# class LocalizationRequest:
#     camera: Annotated[Json[Camera], Form()]  # This parses JSON automatically!
#     image: UploadFile = File(...)


class LocalizationMetrics(BaseModel):
    inlier_ratio: float
    reprojection_error_median: float
    image_coverage: float
    depth_z_90th_percentile: float
    depth_z_10th_percentile: float
