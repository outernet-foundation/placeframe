"""What a fusion algorithm is to the replay.

The replay walks the video in time order. At each frame it first hands over every fix whose answer
has arrived (`on_vps`), then advances the algorithm to the frame (`on_frame`), then reads the
alignment it would publish (`alignment`). An alignment is Unity-from-ECEF as a 4x4 matrix; it may
carry a scale (a similarity), since the replay only ever inverts and composes it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

import numpy as np

from .. import se3
from ..data import Fix

Matrix = np.ndarray


@dataclass
class Decision:
    accepted: bool
    mahalanobis_sq: float | None = None
    snapped: bool = False
    note: str = ""
    extra: dict[str, float] = field(default_factory=dict)


class Fusion(Protocol):
    name: str

    def on_vps(self, t: float, fix: Fix, unity_from_camera: Matrix) -> Decision:
        """A fix arrives. `unity_from_camera` is the tracker's pose of the still it localized."""
        ...

    def on_frame(self, t: float, unity_from_camera: Matrix) -> None:
        """Time moves on to a video frame (slews progress, uncertainty grows)."""
        ...

    def alignment(self) -> Matrix | None:
        """The published Unity-from-ECEF alignment, or None before the first fix."""
        ...

    def diagnostics(self) -> dict[str, float]:
        """Per-frame numbers worth plotting (sigma, slew progress, ...)."""
        ...


def measurement_alignment(fix: Fix, unity_from_camera: Matrix) -> Matrix:
    """The Unity-from-ECEF alignment one fix implies on its own (ComputeAlignmentFromResult),
    anchored on the camera so rotation noise cannot lever-arm the camera off its VIO position."""
    assert fix.camera_from_map is not None and fix.ecef_from_map is not None
    rotation_camera_from_map = fix.camera_from_map[:3, :3]
    map_from_camera_translation = -rotation_camera_from_map.T @ fix.camera_from_map[:3, 3]
    ecef_from_camera_translation = fix.ecef_from_map[:3, :3] @ map_from_camera_translation + fix.ecef_from_map[:3, 3]
    rotation = unity_from_camera[:3, :3] @ rotation_camera_from_map @ fix.ecef_from_map[:3, :3].T
    translation = unity_from_camera[:3, 3] - rotation @ ecef_from_camera_translation
    return se3.transform(rotation, translation)
