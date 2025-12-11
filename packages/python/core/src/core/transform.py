from __future__ import annotations

from pydantic import BaseModel


class Float3(BaseModel):
    x: float
    y: float
    z: float


class Float4(BaseModel):
    x: float
    y: float
    z: float
    w: float


class Transform(BaseModel):
    translation: Float3
    rotation: Float4
