"""A sliding-window fit: the alignment that best explains the last few fixes together, optionally
with a scale (a similarity), so a map whose scale is off does not drift away as the camera walks.

Each accepted fix k gives the camera's position in Unity world (VIO) u_k and in ECEF e_k, and the
rotation R_k its own alignment implies. The fit takes R as the chordal mean of the R_k, then the
scale and translation that best map the e_k onto the u_k under R, and drops the worst fix while its
residual is over `outlier_m`. The published alignment slews to each new fit.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from scipy.spatial.transform import Rotation

from .. import se3
from ..data import Fix
from .base import Decision, Matrix, measurement_alignment


@dataclass(frozen=True)
class WindowParams:
    window_fixes: int = 12
    window_s: float = 30.0
    fit_scale: bool = False
    min_spread_m: float = 3.0  # below this spread of positions (rms, m), the scale is not fitted
    min_scale_fixes: int = 5
    max_scale_error: float = 0.25  # the scale is held within 1 +- this
    outlier_m: float = 0.5
    min_inliers: int = 0
    slew_s: float = 0.5


@dataclass
class _Sample:
    t: float
    unity: np.ndarray
    ecef: np.ndarray
    rotation: Matrix  # of the fix's own alignment


class Window:
    def __init__(self, params: WindowParams | None = None, name: str | None = None) -> None:
        self.params = params or WindowParams()
        self.name = name or ("window-sim3" if self.params.fit_scale else "window")
        self.samples: list[_Sample] = []
        self.fit: Matrix | None = None
        self.current: Matrix | None = None
        self.slew_start: Matrix | None = None
        self.slew_progress = 1.0
        self.residual_m = math.nan
        self.scale = 1.0
        self.used = 0
        self._last_t: float | None = None

    def on_vps(self, t: float, fix: Fix, unity_from_camera: Matrix) -> Decision:
        p = self.params
        if not fix.ok or fix.camera_from_map is None or fix.ecef_from_map is None:
            return Decision(False, note=fix.error or "failed")
        if fix.num_inliers < p.min_inliers:
            return Decision(False, note=f"{fix.num_inliers} inliers")
        single = measurement_alignment(fix, unity_from_camera)
        ecef_position = (fix.ecef_from_map @ fix.map_from_camera)[:3, 3]
        self.samples.append(_Sample(t, unity_from_camera[:3, 3].copy(), ecef_position, single[:3, :3]))
        self.samples = [s for s in self.samples if t - s.t <= p.window_s][-p.window_fixes :]

        fit, kept, residual = self._fit()
        accepted = any(s is self.samples[-1] for s in kept)
        self.fit, self.used, self.residual_m = fit, len(kept), residual
        if self.current is None:
            self.current = self.slew_start = fit
            self.slew_progress = 1.0
        else:
            self.slew_start = self.current
            self.slew_progress = 0.0
        return Decision(
            accepted,
            snapped=self.slew_progress >= 1.0,
            note="" if accepted else "outlier",
            extra={"window_residual_m": residual, "scale": self.scale},
        )

    def _fit(self) -> tuple[Matrix, list[_Sample], float]:
        p = self.params
        kept = list(self.samples)
        while True:
            matrix, residuals = self._solve(kept)
            worst = int(np.argmax(residuals))
            if len(kept) <= 2 or residuals[worst] <= p.outlier_m:
                return matrix, kept, float(np.sqrt(np.mean(residuals**2)))
            kept.pop(worst)

    def _solve(self, samples: list[_Sample]) -> tuple[Matrix, np.ndarray]:
        rotation = Rotation.from_matrix(np.stack([s.rotation for s in samples])).mean().as_matrix()
        u = np.stack([s.unity for s in samples])
        e = np.stack([s.ecef for s in samples])
        u_mean, e_mean = u.mean(axis=0), e.mean(axis=0)
        rotated = (e - e_mean) @ rotation.T
        spread = float(np.sqrt(((e - e_mean) ** 2).sum(axis=1).mean()))
        scale = 1.0
        p = self.params
        if p.fit_scale and spread >= p.min_spread_m and len(samples) >= p.min_scale_fixes:
            scale = float(((u - u_mean) * rotated).sum() / (rotated**2).sum())
            scale = min(1 + p.max_scale_error, max(1 - p.max_scale_error, scale))
        self.scale = scale
        translation = u_mean - scale * rotation @ e_mean
        matrix = se3.transform(scale * rotation, translation)
        residuals = np.linalg.norm(u - (scale * e @ rotation.T + translation), axis=1)
        return matrix, residuals

    def on_frame(self, t: float, unity_from_camera: Matrix) -> None:
        delta = 0.0 if self._last_t is None else t - self._last_t
        self._last_t = t
        if self.fit is None or self.slew_start is None or self.slew_progress >= 1.0:
            return
        self.slew_progress = min(1.0, self.slew_progress + delta / self.params.slew_s)
        self.current = (
            self.fit
            if self.slew_progress >= 1.0
            else _interpolate_similarity(self.slew_start, self.fit, se3.smooth_step(self.slew_progress))
        )

    def alignment(self) -> Matrix | None:
        return None if self.current is None else self.current.copy()

    def diagnostics(self) -> dict[str, float]:
        return {
            "window_fixes": float(self.used),
            "window_residual_m": self.residual_m,
            "scale": self.scale,
            "slewing": float(self.slew_progress < 1.0),
        }


def _interpolate_similarity(a: Matrix, b: Matrix, t: float) -> Matrix:
    scale_a = float(np.cbrt(np.linalg.det(a[:3, :3])))
    scale_b = float(np.cbrt(np.linalg.det(b[:3, :3])))
    unit_a = se3.transform(a[:3, :3] / scale_a, a[:3, 3])
    unit_b = se3.transform(b[:3, :3] / scale_b, b[:3, 3])
    blended = se3.interpolate(unit_a, unit_b, t)
    blended[:3, :3] *= scale_a + (scale_b - scale_a) * t
    return blended
