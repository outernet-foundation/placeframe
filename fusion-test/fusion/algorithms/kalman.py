"""RelocalizationFilter.cs: an SE(3) Kalman filter over the Unity-from-ECEF alignment.

State: the alignment's mean and a 6x6 covariance in its tangent space ([rotation, translation]).
A fix is gated on its Mahalanobis distance (chi-square, 6 DOF); an accepted fix updates the mean and
the published alignment either snaps to it (the first fix, or a shift too big to slew) or slews over
`slew_s` with a smoothstep.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from .. import se3
from ..data import Fix
from .base import Decision, Matrix, measurement_alignment


@dataclass(frozen=True)
class KalmanParams:
    gate_chi2: float = 16.81  # 99% for 6 DOF
    bypass_gate: bool = False
    bypass_kalman: bool = False  # take each accepted fix as it is, with its covariance (still gated)
    snap_sigmas_sq: float = 36.0
    slew_s: float = 0.5
    drift_per_m: float = 0.01  # alignment uncertainty growth per metre walked since the last fix
    base_translation_variance: float = 1e-4
    base_rotation_variance: float = 1e-6
    bootstrap_sigma_translation_m: float = 100.0
    bootstrap_sigma_rotation_rad: float = math.pi


class Kalman:
    def __init__(self, params: KalmanParams | None = None, name: str = "kalman") -> None:
        self.params = params or KalmanParams()
        self.name = name
        self.mean = np.eye(4)
        self.covariance = self._bootstrap()
        self.current = np.eye(4)
        self.slew_start = np.eye(4)
        self.slew_progress = 1.0
        self.last_accepted_vio_position: np.ndarray | None = None
        self.has_accepted = False
        self.consecutive_rejections = 0
        self._last_t: float | None = None

    def _bootstrap(self) -> Matrix:
        p = self.params
        return np.diag([p.bootstrap_sigma_rotation_rad**2] * 3 + [p.bootstrap_sigma_translation_m**2] * 3)

    def _process_noise(self, vio_position: np.ndarray) -> Matrix:
        p = self.params
        noise = np.diag([p.base_rotation_variance] * 3 + [p.base_translation_variance] * 3)
        if self.last_accepted_vio_position is None:
            return noise
        sigma = p.drift_per_m * float(np.linalg.norm(vio_position - self.last_accepted_vio_position))
        return noise + np.eye(6) * sigma * sigma

    def on_vps(self, t: float, fix: Fix, unity_from_camera: Matrix) -> Decision:
        p = self.params
        if not fix.ok or fix.covariance is None:
            return Decision(False, note=fix.error or "failed")
        measurement = measurement_alignment(fix, unity_from_camera)
        vio_position = unity_from_camera[:3, 3]
        predicted = self.covariance + self._process_noise(vio_position)
        residual = se3.log(np.linalg.inv(self.mean) @ measurement)
        innovation = predicted + fix.covariance
        m2 = float(residual @ np.linalg.solve(innovation, residual))

        if not p.bypass_gate and m2 > p.gate_chi2:
            # Process noise accumulates across rejections so the gate can reopen, capped at bootstrap.
            predicted[np.diag_indices(6)] = np.minimum(np.diag(predicted), np.diag(self._bootstrap()))
            self.covariance = predicted
            self.consecutive_rejections += 1
            return Decision(False, m2, note="gated")

        if p.bypass_kalman:
            new_mean, new_covariance = measurement, fix.covariance
        else:
            gain = predicted @ np.linalg.inv(innovation)
            new_mean = self.mean @ se3.exp(gain @ residual)
            new_covariance = (np.eye(6) - gain) @ predicted

        snap = not self.has_accepted or p.bypass_kalman
        if not snap:
            shift = se3.log(np.linalg.inv(self.current) @ new_mean)
            snap = float(shift @ np.linalg.solve(new_covariance, shift)) > p.snap_sigmas_sq

        self.mean, self.covariance = new_mean, new_covariance
        if snap:
            self.slew_start = self.current = new_mean
            self.slew_progress = 1.0
        else:
            self.slew_start = self.current
            self.slew_progress = 0.0
        self.has_accepted = True
        self.last_accepted_vio_position = vio_position
        self.consecutive_rejections = 0
        return Decision(True, m2, snap)

    def on_frame(self, t: float, unity_from_camera: Matrix) -> None:
        delta = 0.0 if self._last_t is None else t - self._last_t
        self._last_t = t
        if self.slew_progress >= 1.0:
            return
        self.slew_progress = min(1.0, self.slew_progress + delta / self.params.slew_s)
        self.current = (
            self.mean
            if self.slew_progress >= 1.0
            else se3.interpolate(self.slew_start, self.mean, se3.smooth_step(self.slew_progress))
        )

    def alignment(self) -> Matrix | None:
        return self.current.copy() if self.has_accepted else None

    def diagnostics(self) -> dict[str, float]:
        diagonal = np.diag(self.covariance)
        return {
            "sigma_translation_m": math.sqrt(float(diagonal[3:].sum())),
            "sigma_rotation_deg": math.degrees(math.sqrt(float(diagonal[:3].sum()))),
            "slewing": float(self.slew_progress < 1.0),
            "consecutive_rejections": float(self.consecutive_rejections),
        }
