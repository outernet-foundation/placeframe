from __future__ import annotations

from typing import Literal, Union

from pydantic import BaseModel, ConfigDict

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


# A camera that records the whole sphere in one frame (a 360 camera). The frame
# is stored in the projection named here -- equirectangular for every current
# source -- and has no focal length: a sphere is not a perspective image. Views a
# reconstructor can actually model are rendered from it (see the `panorama`
# package), which is why the projection is all this needs to describe.
class SphericalCameraConfig(BaseModel):
    # Rejecting unexpected fields keeps a pinhole config, which carries fx/fy/cx/cy,
    # from validating as a spherical one: existing manifests have no discriminator.
    model_config = ConfigDict(extra="forbid")

    width: int
    height: int
    orientation: ImageOrientation
    projection: Literal["EQUIRECTANGULAR"] = "EQUIRECTANGULAR"


CameraConfig = Union[PinholeCameraConfig, SphericalCameraConfig]
