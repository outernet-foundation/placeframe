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

All views of a frame share one optical centre, so the rig that relates them is
pure rotation: translations are exactly zero, not merely small.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray  # noqa: TID251 — tracked in PLE-233

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

LAYOUTS: dict[str, tuple[View, ...]] = {"tetrahedron": TETRAHEDRON, "cube": CUBE}


def layout(name: str) -> tuple[View, ...]:
    try:
        return LAYOUTS[name]
    except KeyError:
        raise ValueError(f"unknown layout {name!r}; known layouts: {', '.join(sorted(LAYOUTS))}") from None


def focal_length(size: int, fov_deg: float) -> float:
    """Pixels per radian for an equidistant view whose circle spans `fov_deg`."""
    return (size / 2) / np.radians(fov_deg / 2)


def camera_params(size: int, fov_deg: float) -> list[float]:
    """COLMAP OPENCV_FISHEYE parameters (fx, fy, cx, cy, k1..k4) for a view."""
    focal = focal_length(size, fov_deg)
    centre = (size - 1) / 2
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


def cam_from_rig(view: View, reference: View) -> NDArray[np.float64]:
    """Rotation from the rig frame (the reference view's camera frame) into `view`."""
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

    @property
    def camera_params(self) -> list[float]:
        return camera_params(self.size, self.fov_deg)


def view_map(pano_width: int, pano_height: int, view: View, size: int, fov_deg: float) -> ViewMap:
    """Sampling tables for one view of an equirectangular frame of this size."""
    focal = focal_length(size, fov_deg)
    centre = (size - 1) / 2

    px, py = np.meshgrid(np.arange(size, dtype=np.float32), np.arange(size, dtype=np.float32))
    dx, dy = px - centre, py - centre
    radius = np.hypot(dx, dy)
    theta = radius / focal
    phi = np.arctan2(dy, dx)

    cam = np.stack([np.sin(theta) * np.cos(phi), np.sin(theta) * np.sin(phi), np.cos(theta)], axis=-1)
    rays = cam @ pano_from_cam(view).T

    lon = np.arctan2(rays[..., 0], rays[..., 2])
    lat = np.arcsin(np.clip(rays[..., 1], -1.0, 1.0))
    map_x = (((lon / (2 * np.pi) + 0.5) * pano_width) % pano_width).astype(np.float32)
    map_y = ((0.5 - lat / np.pi) * pano_height).astype(np.float32)
    return ViewMap(view, size, fov_deg, map_x, map_y, radius <= size / 2)


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
