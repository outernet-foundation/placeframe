from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated, Literal, TypedDict, Union

from fastapi import File, Form, UploadFile
from pydantic import Discriminator, Json


class Point3D(TypedDict):
    x: float
    y: float
    z: float


class Color(TypedDict):
    r: int
    g: int
    b: int


class PinholeIntrinsics(TypedDict):
    model: Literal["PINHOLE"]
    width: int
    height: int
    fx: float
    fy: float
    cx: float
    cy: float


class OpenCVRadTanIntrinsics(TypedDict):
    model: Literal["OPENCV"]
    width: int
    height: int
    fx: float
    fy: float
    cx: float
    cy: float
    k1: float
    k2: float
    p1: float
    p2: float


class GenericParamsIntrinsics(TypedDict):
    model: Literal["GENERIC"]
    width: int
    height: int
    params: list[float]


CameraIntrinsics = Annotated[
    Union[PinholeIntrinsics, OpenCVRadTanIntrinsics, GenericParamsIntrinsics], Discriminator("model")
]


def get_camera_intrinsics_type(intrinsics: CameraIntrinsics) -> list[float]:
    if intrinsics["model"] == "PINHOLE":
        return [intrinsics["fx"], intrinsics["fy"], intrinsics["cx"], intrinsics["cy"]]
    elif intrinsics["model"] == "OPENCV":
        return [
            intrinsics["fx"],
            intrinsics["fy"],
            intrinsics["cx"],
            intrinsics["cy"],
            intrinsics["k1"],
            intrinsics["k2"],
            intrinsics["p1"],
            intrinsics["p2"],
        ]
    elif intrinsics["model"] == "GENERIC":
        return intrinsics["params"]
    else:
        raise ValueError(f"Unknown intrinsics model: {intrinsics['model']}")


class RigCamera(TypedDict):
    id: str
    ref_sensor: bool | None
    rotation: Quaternion
    translation: Vector3
    intrinsics: CameraIntrinsics


class Rig(TypedDict):
    id: str
    cameras: list[RigCamera]


class RigConfig(TypedDict):
    rigs: list[Rig]


class Vector3(TypedDict):
    x: float
    y: float
    z: float


class Quaternion(TypedDict):
    x: float
    y: float
    z: float
    w: float


class Transform(TypedDict):
    position: Vector3
    rotation: Quaternion


class PointCloudPoint(TypedDict):
    position: Vector3  # uses transform.position (rotation ignored for points)
    color: Color


@dataclass
class LocalizationRequest:
    camera: Annotated[Json[CameraIntrinsics], Form()]  # This parses JSON automatically!
    image: UploadFile = File(...)
