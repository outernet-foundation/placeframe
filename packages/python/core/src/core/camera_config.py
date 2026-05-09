from __future__ import annotations

from typing import Literal

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
