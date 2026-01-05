from __future__ import annotations

from core.axis_convention import AxisConvention
from core.camera_config import PinholeCameraConfig
from core.transform import Float3, Float4
from pydantic import BaseModel


class RigCameraConfig(BaseModel):
    id: str
    ref_sensor: bool
    rotation: Float4
    translation: Float3
    camera_config: PinholeCameraConfig


class RigConfig(BaseModel):
    id: str
    cameras: list[RigCameraConfig]


class CaptureSessionManifest(BaseModel):
    axis_convention: AxisConvention
    rigs: list[RigConfig]
