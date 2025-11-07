from typing import Annotated, Literal, Union

from pydantic import BaseModel, Discriminator

from .transform import Quaternion, Vector3


class CameraBase(BaseModel):
    width: int
    height: int
    mirroring: Literal["None", "X", "Y"]
    rotation: Literal["None", "90_CW", "180", "90_CCW"]


class PinholeCamera(CameraBase):
    model: Literal["PINHOLE"]
    fx: float
    fy: float
    cx: float
    cy: float


class OpenCVCamera(CameraBase):
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


class FullOpenCVCamera(CameraBase):
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


class GenericParamsIntrinsics(CameraBase):
    model: Literal["GENERIC"]
    width: int
    height: int
    params: list[float]


Camera = Annotated[
    Union[PinholeCamera, OpenCVCamera, FullOpenCVCamera, GenericParamsIntrinsics], Discriminator("model")
]


class RigCamera(BaseModel):
    id: str
    ref_sensor: bool | None
    rotation: Quaternion
    translation: Vector3
    intrinsics: Camera


class Rig(BaseModel):
    id: str
    cameras: list[RigCamera]


class RigConfig(BaseModel):
    rigs: list[Rig]
