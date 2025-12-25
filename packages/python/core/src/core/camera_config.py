from __future__ import annotations

from io import BytesIO
from typing import Literal

from PIL import Image as PILImage
from PIL.Image import Transpose
from pydantic import BaseModel

# See "Orientation" property here: https://exiv2.org/tags-xmp-tiff.html
ImageOrientation = Literal[
    "TOP_LEFT", "TOP_RIGHT", "BOTTOM_RIGHT", "BOTTOM_LEFT", "LEFT_TOP", "RIGHT_TOP", "RIGHT_BOTTOM", "LEFT_BOTTOM"
]


class PinholeCameraConfig(BaseModel):
    width: int
    height: int
    orientation: ImageOrientation
    fx: float
    fy: float
    cx: float
    cy: float


def transform_image(image_buffer: bytes, orientation: ImageOrientation) -> PILImage.Image:
    image = PILImage.open(BytesIO(image_buffer))

    match orientation:
        case "TOP_LEFT":
            ...
        case "TOP_RIGHT":
            image = image.transpose(Transpose.FLIP_LEFT_RIGHT)
        case "BOTTOM_RIGHT":
            image = image.transpose(Transpose.ROTATE_180)
        case "BOTTOM_LEFT":
            image = image.transpose(Transpose.FLIP_TOP_BOTTOM)
        case "LEFT_TOP":
            image = image.transpose(Transpose.TRANSPOSE)
        case "RIGHT_TOP":
            image = image.transpose(Transpose.ROTATE_270)
        case "RIGHT_BOTTOM":
            image = image.transpose(Transpose.TRANSVERSE)
        case "LEFT_BOTTOM":
            image = image.transpose(Transpose.ROTATE_90)

    return image.convert("RGB")


def transform_intrinsics(camera: PinholeCameraConfig):
    w = camera.width
    h = camera.height

    if camera.orientation == "TOP_LEFT":
        return camera.width, camera.height, camera.fx, camera.fy, camera.cx, camera.cy

    if camera.orientation == "TOP_RIGHT":
        return camera.width, camera.height, camera.fx, camera.fy, (w - camera.cx), camera.cy

    if camera.orientation == "BOTTOM_RIGHT":
        return camera.width, camera.height, camera.fx, camera.fy, (w - camera.cx), (h - camera.cy)

    if camera.orientation == "BOTTOM_LEFT":
        return camera.width, camera.height, camera.fx, camera.fy, camera.cx, (h - camera.cy)

    new_width = camera.height
    new_height = camera.width

    if camera.orientation == "LEFT_TOP":
        return new_width, new_height, camera.fy, camera.fx, camera.cy, camera.cx

    if camera.orientation == "RIGHT_TOP":
        return new_width, new_height, camera.fy, camera.fx, (h - camera.cy), camera.cx

    if camera.orientation == "RIGHT_BOTTOM":
        return new_width, new_height, camera.fy, camera.fx, (h - camera.cy), (w - camera.cx)

    if camera.orientation == "LEFT_BOTTOM":
        return new_width, new_height, camera.fy, camera.fx, camera.cy, (w - camera.cx)

    raise ValueError(f"Unknown orientation: {camera.orientation!r}")
