from pydantic import BaseModel


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
