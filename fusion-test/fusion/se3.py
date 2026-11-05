"""SE(3) helpers (Se3.cs, MathUtil.cs). Tangent vectors are [rotation (3), translation (3)]."""

from __future__ import annotations

import math
from typing import Any

import numpy as np
from scipy.spatial.transform import Rotation, Slerp

Matrix = np.ndarray


def skew(v: np.ndarray) -> Matrix:
    return np.array([[0.0, -v[2], v[1]], [v[2], 0.0, -v[0]], [-v[1], v[0], 0.0]])


def _skew_inverse(m: Matrix) -> np.ndarray:
    return np.array([(m[2, 1] - m[1, 2]) * 0.5, (m[0, 2] - m[2, 0]) * 0.5, (m[1, 0] - m[0, 1]) * 0.5])


def transform(rotation: Matrix, translation: np.ndarray) -> Matrix:
    matrix = np.eye(4)
    matrix[:3, :3] = rotation
    matrix[:3, 3] = translation
    return matrix


def pose(position: Any, quaternion_xyzw: Any) -> Matrix:
    return transform(Rotation.from_quat(quaternion_xyzw).as_matrix(), np.asarray(position, dtype=np.float64))


def from_dict(d: dict[str, Any]) -> Matrix:
    """A pose as the run files store it: {"position": [x, y, z], "rotation_xyzw": [x, y, z, w]}."""
    return pose(d["position"], d["rotation_xyzw"])


def exp(xi: np.ndarray) -> Matrix:
    omega, rho = xi[:3], xi[3:]
    theta = float(np.linalg.norm(omega))
    k = skew(omega)
    if theta < 1e-6:
        rotation = np.eye(3) + k
        v = np.eye(3) + 0.5 * k
    else:
        k2 = k @ k
        s = math.sin(theta) / theta
        c = (1.0 - math.cos(theta)) / theta**2
        d = (theta - math.sin(theta)) / theta**3
        rotation = np.eye(3) + s * k + c * k2
        v = np.eye(3) + c * k + d * k2
    return transform(rotation, v @ rho)


def log(matrix: Matrix) -> np.ndarray:
    rotation, translation = matrix[:3, :3], matrix[:3, 3]
    theta = math.acos(min(1.0, max(-1.0, (np.trace(rotation) - 1.0) / 2.0)))
    if theta < 1e-6:
        omega = _skew_inverse(rotation - np.eye(3))
        v_inverse = np.eye(3) - 0.5 * skew(omega)
    else:
        omega = (theta / (2.0 * math.sin(theta))) * _skew_inverse(rotation - rotation.T)
        k = skew(omega)
        b = 1.0 / theta**2 - (1.0 + math.cos(theta)) / (2.0 * theta * math.sin(theta))
        v_inverse = np.eye(3) - 0.5 * k + b * k @ k
    return np.concatenate([omega, v_inverse @ translation])


def interpolate(a: Matrix, b: Matrix, t: float) -> Matrix:
    rotation = Slerp([0.0, 1.0], Rotation.from_matrix(np.stack([a[:3, :3], b[:3, :3]])))([t]).as_matrix()[0]
    return transform(rotation, a[:3, 3] + (b[:3, 3] - a[:3, 3]) * t)


def smooth_step(t: float) -> float:
    return t * t * (3.0 - 2.0 * t)


def rotation_deg(matrix: Matrix) -> float:
    """The angle of a pose's (or a difference of poses') rotation."""
    return math.degrees(math.acos(min(1.0, max(-1.0, (np.trace(matrix[:3, :3]) - 1.0) / 2.0))))


def perturb(matrix: Matrix, rotation_deg: float, translation_m: float, rng: np.random.Generator) -> Matrix:
    """`matrix` moved by a random rotation of `rotation_deg` and a random shift of `translation_m`,
    each in a uniformly random direction, applied on the left (in the outer frame)."""
    axis = rng.normal(size=3)
    shift = rng.normal(size=3)
    axis /= np.linalg.norm(axis)
    shift /= np.linalg.norm(shift)
    delta = transform(Rotation.from_rotvec(axis * math.radians(rotation_deg)).as_matrix(), shift * translation_m)
    return delta @ matrix
