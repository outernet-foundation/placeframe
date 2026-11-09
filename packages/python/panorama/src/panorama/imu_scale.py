"""Metric scale for a spherical reconstruction from the .insv's own IMU.

A reconstruction of an imported video is up to scale: its trajectory prior is a made-up straight
line. The camera's accelerometer measures the real thing, so integrating it between keyframes and
comparing with the keyframes' reconstructed displacements gives the scale -- the inertial
initialisation of ORB-SLAM3 / VINS-Mono, run once over a finished map. Three steps:

1. Sync. The gyro, integrated between consecutive keyframes, must turn the camera as the map
   does. Fitting that gives the time offset between record 4's frame stamps and the IMU, the
   rotation between the IMU and the map's camera, and the gyro bias. The map's rotations must
   follow the camera body, so the reconstruction must come from the .insv itself: an Insta360
   Studio export is stabilised (rotated per frame to hold the view still) and fails here.
2. Scale. Between keyframes i and j the accelerometer, rotated into the map by the synced
   orientation, gives the change in velocity and position up to gravity and the accelerometer
   bias. With every keyframe's velocity unknown, s * (p_j - p_i) = v_i dt + g dt^2 / 2 + R_i alpha_ij
   and v_j = v_i + g dt + R_i beta_ij are linear in the scale, the velocities and the bias (solved
   for the inverse scale; see _scale_system); gravity is fixed at 9.80665 m/s^2 and only its direction searched. The free fit's |g| is reported as a
   check: a sound sync and map give ~9.8.
3. Drift. The scale refitted per window of the walk (gravity and bias held at the global fit), with
   a chi-square test of whether one scale explains them all.

The result is a Sim(3) about the map's origin: the scale to metres and the turn that puts gravity
on +y (the reconstructor's down). The reconstructor applies it to a map of a capture that carries
its motion (panorama.motion) when the fit passes `rejection`'s checks; `howard-test imu-scale`
applies it to an older map as a metric copy. The IMU is taken to sit at the sphere's centre; the
X4's is a few centimetres off, which only matters for fast rotation and is ignored.

Scipy is needed here, and only here: the package's `imu` extra.
"""

from __future__ import annotations

import math
from itertools import pairwise
from dataclasses import dataclass
from typing import Any

import numpy as np
from numpy.typing import NDArray  # noqa: TID251 — tracked in PLE-233
from scipy.optimize import minimize
from scipy.spatial.transform import Rotation
from scipy.stats import chi2

from .motion import STANDARD_GRAVITY, Imu, Motion

Floats = NDArray[np.float64]
GRAVITY = STANDARD_GRAVITY
DRIFT_WINDOW_S = 30.0  # long enough that each window's scale is a few percent
OFFSET_SEARCH_S = 0.5  # record 4 has been seen ~0.2 s off the IMU; search well beyond that


# --- inputs --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Keyframes:
    t_s: Floats  # (n,) record-4 time of each keyframe, before the sync offset
    position: Floats  # (n, 3) camera centre in the map
    world_from_cam: Rotation  # (n,)


def keyframes(
    motion: Motion, frame_ids_ms: NDArray[np.int64], positions: Floats, world_from_cam: Rotation
) -> Keyframes:
    """A map's registered frames, in capture order, timed on the IMU's clock: frame ids are the
    frames.csv timestamps the capture names its frames by."""
    order = np.argsort(frame_ids_ms)
    return Keyframes(motion.frame_times(frame_ids_ms[order]), positions[order], world_from_cam[order])


# --- gyro integration ----------------------------------------------------------------------------


def _quat_mul(a: Floats, b: Floats) -> Floats:
    """Hamilton product of (..., 4) scalar-last quaternions."""
    ax, ay, az, aw = np.moveaxis(a, -1, 0)
    bx, by, bz, bw = np.moveaxis(b, -1, 0)
    return np.stack(
        [
            aw * bx + ax * bw + ay * bz - az * by,
            aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw,
            aw * bw - ax * bx - ay * by - az * bz,
        ],
        -1,
    )


def integrate_gyro(imu: Imu, bias: Floats) -> Rotation:
    """Orientation at every IMU sample relative to the first (start_from_body), by a parallel prefix
    product of the per-sample increments: log2(n) vectorised steps instead of an n-step loop."""
    dt = np.diff(imu.t_s, append=imu.t_s[-1])
    q = Rotation.from_rotvec((imu.gyro - bias) * dt[:, None]).as_quat()
    q = np.vstack([[0.0, 0.0, 0.0, 1.0], q[:-1]])  # sample k holds the turn up to its own time
    step = 1
    while step < len(q):
        q[step:] = _quat_mul(q[:-step], q[step:])
        q /= np.linalg.norm(q, axis=1, keepdims=True)
        step *= 2
    return Rotation.from_quat(q)


def sample_at(imu: Imu, t_s: Floats) -> NDArray[np.intp]:
    return np.clip(np.searchsorted(imu.t_s, t_s), 0, len(imu.t_s) - 1)


# --- 1. sync -------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Sync:
    offset_s: float  # IMU time = record-4 time + offset
    cam_from_imu: Rotation
    gyro_bias: Floats
    residual_deg: Floats  # per keyframe interval


def _sync_residuals(keys: Keyframes, imu: Imu, orientation: Rotation, offset: float, cam_from_imu: Rotation) -> Floats:
    k = sample_at(imu, keys.t_s + offset)
    gyro_turn = orientation[k[:-1]].inv() * orientation[k[1:]]
    map_turn = keys.world_from_cam[:-1].inv() * keys.world_from_cam[1:]
    return (map_turn.inv() * cam_from_imu * gyro_turn * cam_from_imu.inv()).as_rotvec()


def _kabsch(source: Floats, target: Floats) -> Rotation:
    rotation, _ = Rotation.align_vectors(target, source)
    return rotation


def fit_sync(keys: Keyframes, imu: Imu) -> Sync:
    map_turn = (keys.world_from_cam[:-1].inv() * keys.world_from_cam[1:]).as_rotvec()
    bias: Floats = np.zeros(3)
    orientation = integrate_gyro(imu, bias)

    def best_rotation(offset: float) -> tuple[float, Rotation]:
        k = sample_at(imu, keys.t_s + offset)
        gyro_turn = (orientation[k[:-1]].inv() * orientation[k[1:]]).as_rotvec()
        rotation = _kabsch(gyro_turn, map_turn)
        cost = float(
            np.mean(np.sum(_sync_residuals(keys, imu, orientation, offset, rotation) ** 2, axis=1), dtype=np.float64)
        )
        return cost, rotation

    offsets = np.arange(-OFFSET_SEARCH_S, OFFSET_SEARCH_S + 1e-9, 0.005)
    offset = float(offsets[np.argmin([best_rotation(o)[0] for o in offsets])])
    cam_from_imu = best_rotation(offset)[1]
    for _round in range(3):
        # rotation and bias by Gauss-Newton at this offset, then the offset again at 1 ms
        for _iteration in range(8):
            params: Floats = np.concatenate([np.zeros(3), bias])

            def residual(p: Floats, base: Rotation = cam_from_imu, at: float = offset) -> Floats:
                o = integrate_gyro(imu, p[3:])
                return _sync_residuals(keys, imu, o, at, Rotation.from_rotvec(p[:3]) * base).ravel()

            r0 = residual(params)
            jac = np.empty((len(r0), 6))
            for j in range(6):
                d = np.zeros(6)
                d[j] = 1e-6
                jac[:, j] = (residual(params + d) - r0) / 1e-6
            delta: Floats = np.linalg.lstsq(jac, -r0, rcond=None)[0].astype(np.float64)
            cam_from_imu = Rotation.from_rotvec(delta[:3]) * cam_from_imu
            bias = bias + delta[3:]
            if np.abs(delta).max() < 1e-8:
                break
        orientation = integrate_gyro(imu, bias)
        fine = offset + np.arange(-0.01, 0.0105, 0.001)
        costs = [
            float(
                np.mean(np.sum(_sync_residuals(keys, imu, orientation, o, cam_from_imu) ** 2, axis=1), dtype=np.float64)
            )
            for o in fine.tolist()
        ]
        offset = float(fine[int(np.argmin(np.asarray(costs)))])
    residual_deg = np.degrees(np.linalg.norm(_sync_residuals(keys, imu, orientation, offset, cam_from_imu), axis=1))
    return Sync(offset, cam_from_imu, bias, residual_deg)


# --- 2. scale ------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Interval:
    """Accelerometer integrated from keyframe i to i + 1, in the body frame at i."""

    dt: float
    alpha: Floats  # double integral (position)
    beta: Floats  # single integral (velocity)
    d_alpha_d_bias: Floats  # 3x3
    d_beta_d_bias: Floats  # 3x3


def preintegrate(keys: Keyframes, imu: Imu, sync: Sync) -> list[Interval]:
    orientation = integrate_gyro(imu, sync.gyro_bias)
    k = sample_at(imu, keys.t_s + sync.offset_s)
    intervals: list[Interval] = []
    for a, b in pairwise(k):
        dt = np.diff(imu.t_s[a : b + 1])
        turn = (orientation[a].inv() * orientation[a:b]).as_matrix()  # body at i <- body at sample
        accel = np.einsum("nij,nj->ni", turn, imu.accel[a:b])
        velocity = np.cumsum(accel * dt[:, None], axis=0)
        before = np.vstack([np.zeros((1, 3)), velocity[:-1]])
        alpha = np.sum(before * dt[:, None] + 0.5 * accel * dt[:, None] ** 2, axis=0)
        rotated_dt = np.cumsum(turn * dt[:, None, None], axis=0)
        rotated_before = np.concatenate([np.zeros((1, 3, 3)), rotated_dt[:-1]])
        d_alpha = -np.sum(rotated_before * dt[:, None, None] + 0.5 * turn * dt[:, None, None] ** 2, axis=0)
        intervals.append(Interval(float(dt.sum()), alpha, velocity[-1], d_alpha, -rotated_dt[-1]))
    return intervals


@dataclass(frozen=True)
class ScaleFit:
    scale: float  # metres per map unit
    scale_sigma: float
    gravity: Floats  # in the map, m/s^2 (points down)
    accel_bias: Floats
    rms: float  # residual, map units / s^2


def _scale_system(
    keys: Keyframes,
    intervals: list[Interval],
    world_from_body: Rotation,
    gravity: Floats | None,
    accel_bias: Floats | None,
) -> tuple[Floats, Floats, int]:
    """Rows of A x = y in map units, over x = [lambda, (lambda g), (lambda b), u_0 .. u_n-1]: lambda
    is the inverse scale (map units per metre) and u = lambda v. Solving for the inverse keeps the
    map's displacements, the noisy measurement, alone on the right; with the scale multiplying them
    instead, their noise biases the scale low (errors in variables: 3% from 3 mm on a synthetic
    walk). Each row is weighted to map units / s^2 so position and velocity rows compare. A given
    gravity or bias folds into lambda's column."""
    n = len(keys.t_s)
    free = 1 + (3 if gravity is None else 0) + (3 if accel_bias is None else 0)
    rows: list[Floats] = []
    rhs: list[Floats] = []
    for i, item in enumerate(intervals):
        rot = world_from_body[i].as_matrix()
        dt = item.dt
        # position: lambda (R alpha(b) + g dt^2/2) + u_i dt = dp, alpha(b) = alpha(0) + (dA/db) b
        row = np.zeros((3, free + 3 * n))
        row[:, 0] = rot @ item.alpha
        col = 1
        if gravity is None:
            row[:, col : col + 3] = 0.5 * dt**2 * np.eye(3)
            col += 3
        else:
            row[:, 0] += 0.5 * dt**2 * gravity
        if accel_bias is None:
            row[:, col : col + 3] = rot @ item.d_alpha_d_bias
        else:
            row[:, 0] += rot @ item.d_alpha_d_bias @ accel_bias
        row[:, free + 3 * i : free + 3 * i + 3] = dt * np.eye(3)
        rows.append(row / (0.5 * dt**2))
        rhs.append((keys.position[i + 1] - keys.position[i]) / (0.5 * dt**2))
        # velocity: lambda (R beta(b) + g dt) + u_i - u_j = 0
        row = np.zeros((3, free + 3 * n))
        row[:, 0] = rot @ item.beta
        col = 1
        if gravity is None:
            row[:, col : col + 3] = dt * np.eye(3)
            col += 3
        else:
            row[:, 0] += dt * gravity
        if accel_bias is None:
            row[:, col : col + 3] = rot @ item.d_beta_d_bias
        else:
            row[:, 0] += rot @ item.d_beta_d_bias @ accel_bias
        row[:, free + 3 * i : free + 3 * i + 3] = np.eye(3)
        row[:, free + 3 * (i + 1) : free + 3 * (i + 1) + 3] = -np.eye(3)
        rows.append(row / dt)
        rhs.append(np.zeros(3))
    return np.vstack(rows), np.concatenate(rhs), free


def _solve(a: Floats, y: Floats) -> tuple[Floats, Floats, float]:
    x: Floats = np.linalg.lstsq(a, y, rcond=None)[0].astype(np.float64)
    residual = y - a @ x
    dof = max(1, len(y) - a.shape[1])
    covariance = np.linalg.pinv(a.T @ a) * float(residual @ residual) / dof
    return x, covariance, float(np.sqrt(np.mean(residual**2)))


def _scale_of(x: Floats, covariance: Floats) -> tuple[float, float]:
    """Scale and its sigma from the inverse scale's."""
    inverse = float(x[0])
    return 1 / inverse, float(np.sqrt(covariance[0, 0])) / inverse**2


def fit_scale_free_gravity(keys: Keyframes, intervals: list[Interval], world_from_body: Rotation) -> Floats:
    a, y, _free = _scale_system(keys, intervals, world_from_body, None, None)
    x = _solve(a, y)[0]
    return x[1:4] / x[0]


def fit_scale(keys: Keyframes, intervals: list[Interval], world_from_body: Rotation, direction: Floats) -> ScaleFit:
    """Gravity's size fixed at 9.80665 and its direction searched; the rest is linear for each."""
    axis_a = np.cross(direction, [1.0, 0.0, 0.0])
    if np.linalg.norm(axis_a) < 0.1:
        axis_a = np.cross(direction, [0.0, 1.0, 0.0])
    axis_a /= np.linalg.norm(axis_a)
    axis_b = np.cross(direction, axis_a)

    def gravity_of(angles: Floats) -> Floats:
        return GRAVITY * Rotation.from_rotvec(angles[0] * axis_a + angles[1] * axis_b).apply(direction)

    def cost(angles: Floats) -> float:
        a, y, _free = _scale_system(keys, intervals, world_from_body, gravity_of(angles), None)
        return _solve(a, y)[2]

    angles = minimize(cost, np.zeros(2), method="Nelder-Mead", options={"xatol": 1e-6, "fatol": 1e-12}).x
    gravity = gravity_of(angles)
    a, y, _free = _scale_system(keys, intervals, world_from_body, gravity, None)
    x, covariance, rms = _solve(a, y)
    scale, sigma = _scale_of(x, covariance)
    return ScaleFit(scale, sigma, gravity, x[1:4] / x[0], rms)


# --- 3. drift ------------------------------------------------------------------------------------


def window_scales(
    keys: Keyframes, intervals: list[Interval], world_from_body: Rotation, fit: ScaleFit, window_s: float
) -> list[dict[str, float]]:
    """The scale refitted over each window of keyframe intervals, gravity and bias held."""
    start = keys.t_s[0]
    group = np.floor((keys.t_s[:-1] - start) / window_s).astype(int)
    out: list[dict[str, float]] = []
    for g in np.unique(group):
        chosen = np.flatnonzero(group == g)
        if len(chosen) < 3:
            continue
        first, last = int(chosen[0]), int(chosen[-1]) + 1
        sub = Keyframes(
            keys.t_s[first : last + 1], keys.position[first : last + 1], keys.world_from_cam[first : last + 1]
        )
        a, y, _free = _scale_system(
            sub, intervals[first:last], world_from_body[first : last + 1], fit.gravity, fit.accel_bias
        )
        x, covariance, rms = _solve(a, y)
        scale, sigma = _scale_of(x, covariance)
        out.append({
            "t_start_s": float(keys.t_s[first] - start),
            "t_end_s": float(keys.t_s[last] - start),
            "intervals": len(chosen),
            "scale": scale,
            "scale_sigma": sigma,
            "rms": rms,
        })
    return out


def fit(keys: Keyframes, imu: Imu, window_s: float = DRIFT_WINDOW_S) -> tuple[dict[str, Any], dict[str, Any]]:
    """The fit's report and its Sim(3) (scale, R, translation: X' = scale * R @ X + translation)."""
    sync = fit_sync(keys, imu)
    world_from_body = keys.world_from_cam * sync.cam_from_imu
    intervals = preintegrate(keys, imu, sync)
    free_gravity = fit_scale_free_gravity(keys, intervals, world_from_body)
    direction = free_gravity / np.linalg.norm(free_gravity)
    fit = fit_scale(keys, intervals, world_from_body, direction)
    windows = window_scales(keys, intervals, world_from_body, fit, window_s)
    scales = np.array([w["scale"] for w in windows])
    sigmas = np.array([w["scale_sigma"] for w in windows])
    chi_square = float(np.sum(((scales - fit.scale) / sigmas) ** 2)) if len(windows) > 1 else float("nan")

    down = fit.gravity / np.linalg.norm(fit.gravity)
    level, _ = Rotation.align_vectors([[0.0, 1.0, 0.0]], [down])
    sim3 = {
        "scale": fit.scale,
        "R": level.as_matrix().tolist(),
        "translation": [0.0, 0.0, 0.0],
        "source": "imu_scale",
        "scale_sigma": fit.scale_sigma,
    }
    report = {
        "keyframes": len(keys.t_s),
        "span_s": float(keys.t_s[-1] - keys.t_s[0]),
        "sync": {
            "offset_s": sync.offset_s,
            "cam_from_imu": sync.cam_from_imu.as_matrix().tolist(),
            "gyro_bias_deg_s": np.degrees(sync.gyro_bias).tolist(),
            "residual_deg_median": float(np.median(sync.residual_deg)),
            "residual_deg_rms": float(np.sqrt(np.mean(sync.residual_deg**2))),
            "map_turn_deg_median": float(
                np.median(np.degrees((keys.world_from_cam[:-1].inv() * keys.world_from_cam[1:]).magnitude()))
            ),
        },
        "free_gravity_norm_mps2": float(np.linalg.norm(free_gravity)),
        "scale": fit.scale,
        "scale_sigma": fit.scale_sigma,
        "accel_bias_mps2": fit.accel_bias.tolist(),
        "rms_map_units_s2": fit.rms,
        "path_length_m": float(fit.scale * np.sum(np.linalg.norm(np.diff(keys.position, axis=0), axis=1))),
        "window_s": window_s,
        "windows": windows,
        "drift_chi_square": chi_square,
        "drift_p_value": float(chi2.sf(chi_square, len(windows) - 1)) if len(windows) > 1 else float("nan"),
    }
    return report, sim3


# --- 4. whether to believe it --------------------------------------------------------------------

# Each check is one way a fit has been seen to go wrong. A map of a stabilised export syncs to ~9
# degrees (a native .insv to ~0.1) and drags the free gravity far from 9.81 (49.7 on one); the
# Fosun walk's windows disagreed far beyond their errors (p ~ 3e-10) and its scale came out 6.7%
# short of a stereo map's. Thresholds sit well clear of every good native fit seen so far.
MAX_SYNC_RESIDUAL_DEG = 0.5
MAX_GRAVITY_ERROR = 0.03  # of 9.80665, for the free fit
MAX_RELATIVE_SIGMA = 0.03
MIN_DRIFT_P_VALUE = 0.01
MIN_KEYFRAMES = 20


def rejection(report: dict[str, Any]) -> str | None:
    """Why the fit's scale should not be trusted, or None when every check passes."""
    if report["keyframes"] < MIN_KEYFRAMES:
        return f"only {report['keyframes']} keyframes (at least {MIN_KEYFRAMES} wanted)"
    residual = report["sync"]["residual_deg_median"]
    if residual > MAX_SYNC_RESIDUAL_DEG:
        return (
            f"the gyro syncs to the map's rotations only to {residual:.2f} deg (at most {MAX_SYNC_RESIDUAL_DEG} "
            "wanted): the map does not follow the camera body, as with a stabilised export"
        )
    gravity = report["free_gravity_norm_mps2"]
    if abs(gravity / GRAVITY - 1) > MAX_GRAVITY_ERROR:
        return f"unconstrained gravity fits to {gravity:.2f} m/s^2, not ~{GRAVITY:.2f}"
    scale, sigma = report["scale"], report["scale_sigma"]
    if scale <= 0 or sigma / scale > MAX_RELATIVE_SIGMA:
        return f"scale {scale:.4g} +- {sigma:.2g} is not determined to {100 * MAX_RELATIVE_SIGMA:.0f}%"
    p_value = report["drift_p_value"]
    if not math.isnan(p_value) and p_value < MIN_DRIFT_P_VALUE:  # one window: nothing to compare
        return f"the scale drifts along the walk (p = {p_value:.2g} that one scale explains every window)"
    return None
