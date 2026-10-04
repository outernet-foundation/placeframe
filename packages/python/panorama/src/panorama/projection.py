"""Turning an equirectangular frame into the views a reconstructor can use.

COLMAP's fisheye camera models normalise by z before taking the ray angle, so
they only represent rays under 90 degrees off axis -- just under 180 degrees of
field of view, and numerically poor near that limit. A spherical frame therefore
has to be cut into several narrower views, one camera each, rigidly related.

Each view is rendered as an EQUIDISTANT fisheye (r = f * theta) whose image
circle spans the requested field of view, so its parameters are exact rather
than estimated:

    f = (size / 2) / (fov / 2)   [pixels per radian]

which is COLMAP's OPENCV_FISHEYE with all four distortion coefficients zero.

Layouts:
  TETRAHEDRON  four views, axes 109.5 degrees apart. The worst-covered direction
               on the sphere is 70.5 degrees from its nearest axis, so a field of
               view of 141 degrees or more covers the whole sphere; at the
               default 150 there are 4.5 degrees to spare. Two views are tilted
               up and two down, so neither the zenith nor the nadir (where the
               operator is) sits at a view centre.
  CUBE         the six cube faces, for comparison; needs 141 degrees as well to
               cover the sphere as fisheye views (a 90-degree face only covers
               the sphere when rendered as a rectilinear face).
  HEXRING      six views around one ring, 60 degrees apart in yaw, tilted
               alternately 15 degrees up and down. Axes are 66.5 degrees apart,
               so 150 degrees covers the whole sphere as the tetrahedron does --
               but the point of it is the narrower end: every view stays near
               horizontal, so a view matches a query taken looking level far
               better than a 150-degree view does, and a narrower view is closer
               to rectilinear where a query is rectilinear. Coverage falls off
               gently rather than suddenly, which outdoors costs little: 120
               degrees leaves 99% of everything between 45 up and 70 down, and
               what it drops is mostly sky. The alternating tilt is what makes
               that possible -- six coplanar views could not reach a pole at any
               field of view a fisheye model can represent, since every axis
               would be 90 degrees from it.

All views of a frame share one optical centre, so the rig that relates them is
pure rotation: translations are exactly zero, not merely small.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np


from numpy.typing import NDArray  # noqa: TID251 — tracked in PLE-233

# How a view samples the sphere.
#
# "fisheye" is equidistant (r = f * theta): angular resolution is uniform across the field, and
# any field of view under 180 degrees is representable. It is the only option that can cover a
# sphere in few views.
#
# "rectilinear" is a pinhole view (r = f * tan(theta)): straight lines stay straight and local
# patches stay near-isotropic, which is what a phone camera produces. It cannot approach 180
# degrees -- magnification goes as 1/cos^2(theta) off axis -- so it is for narrow views only,
# and covering a sphere with it takes many more of them.
#
# Which to prefer is set by what the query images look like, not by the sphere: a map image that
# matches the query's projection and angular resolution gives a feature matcher a far easier job.
Projection = Literal["fisheye", "rectilinear"]

# Half the tetrahedral tilt angle: asin(1/sqrt(3)) in degrees.
TETRA_TILT_DEG = 35.264389682754654
MIN_TETRA_FOV_DEG = 141.06


@dataclass(frozen=True)
class View:
    """One rendered view: a name, and where it points in panorama axes."""

    name: str
    yaw_deg: float
    pitch_deg: float


TETRAHEDRON: tuple[View, ...] = (
    View("A", 45.0, TETRA_TILT_DEG),
    View("B", 135.0, -TETRA_TILT_DEG),
    View("C", 225.0, TETRA_TILT_DEG),
    View("D", 315.0, -TETRA_TILT_DEG),
)

CUBE: tuple[View, ...] = (
    View("front", 0.0, 0.0),
    View("right", 90.0, 0.0),
    View("back", 180.0, 0.0),
    View("left", 270.0, 0.0),
    View("up", 0.0, 90.0),
    View("down", 0.0, -90.0),
)

# Six views on one ring, alternately tilted up and down. The tilt is small enough that every view
# still looks roughly level -- which is the point, for a map whose queries are taken level -- but
# large enough to lift the axes out of a single plane, so the poles are reachable at all.
HEXRING_TILT_DEG = 15.0

# Yaws are written 0..300 rather than signed: a view's name becomes an image folder and a COLMAP
# image prefix, and a '+' in either is a character that some consumer eventually reads as a space.
HEXRING: tuple[View, ...] = tuple(
    View(f"h{yaw:03d}", float(yaw), HEXRING_TILT_DEG if index % 2 == 0 else -HEXRING_TILT_DEG)
    for index, yaw in enumerate((0, 60, 120, 180, 240, 300))
)

LAYOUTS: dict[str, tuple[View, ...]] = {"tetrahedron": TETRAHEDRON, "cube": CUBE, "hexring": HEXRING}


def layout(name: str) -> tuple[View, ...]:
    try:
        return LAYOUTS[name]
    except KeyError:
        raise ValueError(f"unknown layout {name!r}; known layouts: {', '.join(sorted(LAYOUTS))}") from None


def focal_length(size: int, fov_deg: float, projection: Projection = "fisheye") -> float:
    """Focal length in pixels for a view spanning `fov_deg` across `size` pixels.

    Equidistant gives pixels per radian directly; rectilinear is the pinhole focal length, for
    which the same field of view needs a longer focal length and so resolves the centre of the
    field more finely at the cost of reaching nowhere near 180 degrees.
    """
    half = np.radians(fov_deg / 2)
    if projection == "rectilinear":
        return (size / 2) / np.tan(half)
    return (size / 2) / half


def camera_model(projection: Projection) -> str:
    """The COLMAP camera model a view of this projection is exactly described by."""
    return "PINHOLE" if projection == "rectilinear" else "OPENCV_FISHEYE"


def camera_params(size: int, fov_deg: float, projection: Projection = "fisheye") -> list[float]:
    """COLMAP camera parameters for a view.

    OPENCV_FISHEYE (fx, fy, cx, cy, k1..k4) for an equidistant view, PINHOLE (fx, fy, cx, cy)
    for a rectilinear one. Both are exact for a rendered view rather than estimated, because
    the projection that produced the pixels is the one being described.
    """
    focal = focal_length(size, fov_deg, projection)
    centre = (size - 1) / 2
    if projection == "rectilinear":
        return [focal, focal, centre, centre]
    return [focal, focal, centre, centre, 0.0, 0.0, 0.0, 0.0]


def pano_from_cam(view: View) -> NDArray[np.float64]:
    """Rotation taking a ray in the view's camera frame into panorama axes.

    The camera frame is OpenCV's (x right, y down, z forward); the panorama has
    y up with its centre column at yaw 0. Positive pitch tilts the view up.
    """
    yaw, pitch = np.radians(view.yaw_deg), np.radians(-view.pitch_deg)
    rot_yaw = np.array([[np.cos(yaw), 0, np.sin(yaw)], [0, 1, 0], [-np.sin(yaw), 0, np.cos(yaw)]])
    rot_pitch = np.array([[1, 0, 0], [0, np.cos(pitch), -np.sin(pitch)], [0, np.sin(pitch), np.cos(pitch)]])
    return rot_yaw @ rot_pitch @ np.diag([1.0, -1.0, 1.0])


# Panorama axes are y-up, which with z forward makes them left-handed; camera and
# capture frames are OpenCV's right-handed y-down. This flip relates the two, and
# is why pano_from_cam alone is not a rotation (its determinant is -1).
Y_FLIP = np.diag([1.0, -1.0, 1.0])


def opencv_from_cam(view: View) -> NDArray[np.float64]:
    """Rotation from a view's camera frame into the capture's (OpenCV) frame.

    Unlike pano_from_cam this is a proper rotation, so it is what to use for
    anything physical -- restating gravity or a device pose in a view's frame.
    """
    return Y_FLIP @ pano_from_cam(view)


def cam_from_rig(view: View, reference: View) -> NDArray[np.float64]:
    """Rotation from the rig frame (the reference view's camera frame) into `view`.

    The panorama-axes flip cancels between the two views, so this is a proper
    rotation whichever of pano_from_cam or opencv_from_cam it is built from.
    """
    return pano_from_cam(view).T @ pano_from_cam(reference)


@dataclass(frozen=True)
class ViewMap:
    """Where each pixel of a rendered view samples the equirectangular frame."""

    view: View
    size: int
    fov_deg: float
    map_x: NDArray[np.float32]
    map_y: NDArray[np.float32]
    inside: NDArray[np.bool_]
    projection: Projection = "fisheye"

    @property
    def camera_params(self) -> list[float]:
        return camera_params(self.size, self.fov_deg, self.projection)

    @property
    def camera_model(self) -> str:
        return camera_model(self.projection)


def view_map(
    pano_width: int,
    pano_height: int,
    view: View,
    size: int,
    fov_deg: float,
    projection: Projection = "fisheye",
) -> ViewMap:
    """Sampling tables for one view of an equirectangular frame of this size."""
    focal = focal_length(size, fov_deg, projection)
    centre = (size - 1) / 2

    px, py = np.meshgrid(np.arange(size, dtype=np.float32), np.arange(size, dtype=np.float32))
    dx, dy = px - centre, py - centre

    if projection == "rectilinear":
        # A pinhole view fills its frame, so every pixel carries image -- there is no circle to
        # mask off and no corner to discard.
        cam = np.stack([dx, dy, np.full_like(dx, focal)], axis=-1)
        cam /= np.linalg.norm(cam, axis=-1, keepdims=True)
        inside = np.ones(dx.shape, dtype=bool)
    else:
        radius = np.hypot(dx, dy)
        theta = radius / focal
        phi = np.arctan2(dy, dx)
        cam = np.stack([np.sin(theta) * np.cos(phi), np.sin(theta) * np.sin(phi), np.cos(theta)], axis=-1)
        inside = radius <= size / 2

    rays = cam @ pano_from_cam(view).T

    lon = np.arctan2(rays[..., 0], rays[..., 2])
    lat = np.arcsin(np.clip(rays[..., 1], -1.0, 1.0))
    map_x = (((lon / (2 * np.pi) + 0.5) * pano_width) % pano_width).astype(np.float32)
    map_y = ((0.5 - lat / np.pi) * pano_height).astype(np.float32)
    return ViewMap(view, size, fov_deg, map_x, map_y, inside, projection)


def render(frame: NDArray[np.uint8], tables: ViewMap) -> NDArray[np.uint8]:
    """Sample `frame` (H x W x C, equirectangular) into one view, bilinearly.

    Done in numpy rather than with OpenCV so that services which only need the
    projection maths do not have to carry an image library. Longitude wraps
    around the seam; latitude clamps at the poles. Pixels outside the image
    circle are black, and a mask keeps feature detectors off that hard edge.
    """
    height, width = frame.shape[:2]
    x0 = np.floor(tables.map_x).astype(np.int64)
    y0 = np.floor(tables.map_y).astype(np.int64)
    fx = (tables.map_x - x0)[..., None]
    fy = (tables.map_y - y0)[..., None]
    x1, y1 = (x0 + 1) % width, np.clip(y0 + 1, 0, height - 1)
    x0, y0 = x0 % width, np.clip(y0, 0, height - 1)

    source = frame.astype(np.float32)
    top = source[y0, x0] * (1 - fx) + source[y0, x1] * fx
    bottom = source[y1, x0] * (1 - fx) + source[y1, x1] * fx
    view = (top * (1 - fy) + bottom * fy).astype(np.uint8)
    view[~tables.inside] = 0
    return view


def circle_mask(size: int, margin: int = 12) -> NDArray[np.uint8]:
    """White inside the image circle (shrunk by `margin`), for COLMAP's mask.

    Everything outside the circle is black and sits at identical pixels in every
    frame, so features there would match like a pattern stuck to the lens.
    """
    centre = (size - 1) / 2
    px, py = np.meshgrid(np.arange(size), np.arange(size))
    inside = np.hypot(px - centre, py - centre) <= size / 2 - margin
    mask = np.zeros((size, size), dtype=np.uint8)
    mask[inside] = 255
    return mask
