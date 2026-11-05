"""The simplest baseline: publish each fix's own alignment the moment it lands, no gate, no filter.
Every VPS error shows up as a jump; anything smoother has to beat it on accuracy."""

from __future__ import annotations

from ..data import Fix
from .base import Decision, Matrix, measurement_alignment


class Snap:
    def __init__(self, min_inliers: int = 0, name: str = "snap") -> None:
        self.min_inliers = min_inliers
        self.name = name
        self._alignment: Matrix | None = None

    def on_vps(self, t: float, fix: Fix, unity_from_camera: Matrix) -> Decision:
        if not fix.ok:
            return Decision(False, note=fix.error or "failed")
        if fix.num_inliers < self.min_inliers:
            return Decision(False, note=f"{fix.num_inliers} inliers")
        self._alignment = measurement_alignment(fix, unity_from_camera)
        return Decision(True, snapped=True)

    def on_frame(self, t: float, unity_from_camera: Matrix) -> None:
        pass

    def alignment(self) -> Matrix | None:
        return None if self._alignment is None else self._alignment.copy()

    def diagnostics(self) -> dict[str, float]:
        return {}
