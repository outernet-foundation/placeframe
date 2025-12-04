from __future__ import annotations

from pydantic import BaseModel


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


class Vector3(BaseModel):
    x: float
    y: float
    z: float


class Quaternion(BaseModel):
    x: float
    y: float
    z: float
    w: float


class Transform(BaseModel):
    position: Vector3
    rotation: Quaternion
