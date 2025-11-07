from typing import TypedDict


class LocalizationResult(TypedDict):
    position: list[float]
    orientation: list[float]


class Point3D(TypedDict):
    position: list[float]
    color: list[int]
