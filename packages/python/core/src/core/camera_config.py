from __future__ import annotations

from typing import Annotated, Literal, Union

from core.image_orientation import ImageOrientation
from pydantic import BaseModel, Discriminator


class CameraConfigBase(BaseModel):
    width: int
    height: int
    orientation: ImageOrientation


class PinholeCameraConfig(CameraConfigBase):
    model: Literal["PINHOLE"]
    fx: float
    fy: float
    cx: float
    cy: float


class OpenCVCameraConfig(CameraConfigBase):
    model: Literal["OPENCV"]
    fx: float
    fy: float
    cx: float
    cy: float
    k1: float
    k2: float
    p1: float
    p2: float
    k3: float


class FullOpenCVCameraConfig(CameraConfigBase):
    model: Literal["FULL_OPENCV"]
    fx: float
    fy: float
    cx: float
    cy: float
    k1: float
    k2: float
    p1: float
    p2: float
    k3: float
    k4: float
    k5: float
    k6: float


CameraConfig = Annotated[Union[PinholeCameraConfig, OpenCVCameraConfig, FullOpenCVCameraConfig], Discriminator("model")]
