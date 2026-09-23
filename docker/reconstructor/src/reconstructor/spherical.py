"""Rendering a spherical capture's frames into the views COLMAP can model.

A spherical capture holds one whole-sphere (equirectangular) frame per instant,
which no COLMAP camera model represents: its fisheye models only cover rays
under 90 degrees off axis. `Rig` expands such a camera into several narrower
views (see rig.SphericalExpansion and the panorama package); this module writes
those views to disk, beside the sphere they came from, under the derived camera
ids the rest of the pipeline uses as image folders:

    rig0/camera0/<frame>.jpg          the sphere, as captured
    rig0/camera0_A/<frame>.jpg        the views rendered from it
    rig0/camera0_B/<frame>.jpg        ...

Only the kept keyframes are rendered, so this runs after keyframe selection.
"""

from __future__ import annotations

from pathlib import Path

from numpy import asarray, uint8
from numpy.typing import NDArray  # noqa: TID251 — tracked in PLE-233
from panorama.projection import ViewMap, render, view_map
from PIL import Image as PILImage
from torch import Tensor

from .rig import Rig

# Keypoints nearer the rim than this (in pixels of the rendered view) are
# dropped: the image circle's edge against black is a strong, frame-invariant
# feature that would otherwise match like a pattern stuck to the lens.
IMAGE_CIRCLE_MARGIN_PX = 12


def inside_image_circle(keypoints: Tensor, width: int) -> Tensor:
    """Mask of the keypoints far enough inside a rendered view's image circle."""
    centre = (width - 1) / 2
    radius = ((keypoints[:, 0] - centre) ** 2 + (keypoints[:, 1] - centre) ** 2).sqrt()
    return radius <= width / 2 - IMAGE_CIRCLE_MARGIN_PX


def render_spherical_views(rig: Rig, capture_session_directory: Path) -> int:
    """Write every view of every kept frame of this rig's spherical camera.

    Returns the number of view images written; zero for a rig that has no
    spherical camera, which is every capture from a phone or a ZED.
    """
    expansion = rig.spherical_expansion
    if expansion is None:
        return 0

    source_directory = capture_session_directory / rig.id / expansion.source_camera_id
    maps: dict[str, ViewMap] = {}
    written = 0
    for frame_id in rig.frame_poses:
        frame_path = source_directory / f"{frame_id}.jpg"
        with PILImage.open(frame_path) as opened:
            frame = asarray(opened.convert("RGB"), dtype=uint8)
        if not maps:
            height, width = frame.shape[:2]
            if width != 2 * height:
                raise ValueError(
                    f"{frame_path} is {width}x{height}; an equirectangular frame is twice as wide as it is high"
                )
            maps = {
                view.name: view_map(width, height, view, expansion.size, expansion.fov_deg) for view in expansion.views
            }
            print(
                f"Rig {rig.id}: rendering {len(expansion.views)} views of {len(rig.frame_poses)} spherical frames "
                f"({width}x{height} -> {expansion.size}px at {expansion.fov_deg} degrees)"
            )

        for view in expansion.views:
            view_directory = capture_session_directory / rig.id / expansion.camera_id(view)
            view_directory.mkdir(parents=True, exist_ok=True)
            rendered: NDArray[uint8] = render(frame, maps[view.name])
            PILImage.fromarray(rendered).save(view_directory / f"{frame_id}.jpg", quality=95)
            written += 1
    return written


__all__ = ["IMAGE_CIRCLE_MARGIN_PX", "inside_image_circle", "render_spherical_views"]
