"""How good a replay was, without ground truth.

registration  At each localized still in the stretch, VPS's own inlier map points projected with the
              fused pose of that moment, against the features they matched: the pixel error of "do
              the points line up". Every still counts, not only the ones the algorithm was given.
reference     A stand-in for ground truth: at each frame, the alignment that the strong fixes within
              +-window_s agree on (outliers against their consensus dropped, the rest averaged). The
              fused camera pose's distance from where that alignment puts the camera is the error.
              It is built from 4 Hz fixes, so it is much denser than the ~1 Hz an algorithm is given,
              but an algorithm fed every still can come close to it by construction.
smoothness    How much the fused pose jumps per frame (Result.correction_m / _deg): the number of
              frames it moves more than 5 cm, the largest jump, and the total it moved.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from . import se3
from .algorithms import measurement_alignment
from .data import Run
from .replay import Result, ecef_from_map

Matrix = np.ndarray


@dataclass
class Registration:
    still: np.ndarray  # still indices
    t: np.ndarray
    median_px: np.ndarray
    p90_px: np.ndarray
    count: np.ndarray


def project_map_points(
    run: Run, camera_from_map: Matrix, points: np.ndarray, intrinsics: str = "stills"
) -> tuple[np.ndarray, np.ndarray]:
    camera = run.still_intrinsics if intrinsics == "stills" else run.video_intrinsics
    xyz = run.map.points[points]
    in_camera = xyz @ camera_from_map[:3, :3].T + camera_from_map[:3, 3]
    return camera.project(in_camera)


def registration(run: Run, result: Result, min_inliers: int = 30) -> Registration:
    rows = []
    for still_index, fix in enumerate(run.fixes):
        frame = run.still_video_index[still_index]
        row = result.at(frame) if frame is not None else None
        if row is None or not fix.ok or len(fix.inlier_points) < min_inliers or np.isnan(result.alignment[row, 0, 0]):
            continue
        # The still's own VIO pose, which is the video frame's.
        camera_from_map = np.linalg.inv(result.map_from_camera[row])
        uv, z = project_map_points(run, camera_from_map, fix.inlier_points)
        error = np.linalg.norm(uv - fix.inlier_uv, axis=1)
        error = error[z > 0]
        if not len(error):
            continue
        rows.append((still_index, fix.t, float(np.median(error)), float(np.percentile(error, 90)), len(error)))
    data = np.array(rows, dtype=np.float64).reshape(-1, 5)
    return Registration(data[:, 0].astype(int), data[:, 1], data[:, 2], data[:, 3], data[:, 4].astype(int))


@dataclass
class Reference:
    t: np.ndarray  # per video frame
    alignment: np.ndarray  # (N, 4, 4), NaN where no strong fix is near
    map_from_camera: np.ndarray
    support: np.ndarray  # fixes averaged at each frame


def reference(
    run: Run, min_inliers: int = 150, window_s: float = 1.5, outlier_m: float = 0.3, outlier_deg: float = 2.0
) -> Reference:
    """The robust local consensus of the strong fixes, at every video frame."""
    strong = [
        (fix.t, measurement_alignment(fix, run.stills[i].unity_from_camera), run.stills[i].unity_from_camera)
        for i, fix in enumerate(run.fixes)
        if fix.ok and fix.num_inliers >= min_inliers and fix.gate_passed is not False
    ]
    times = np.array([s[0] for s in strong])
    poses = run.video_poses()
    map_from_ecef = np.linalg.inv(ecef_from_map(run))
    out = np.full((len(run.video), 4, 4), np.nan)
    support = np.zeros(len(run.video), dtype=int)
    for i, frame in enumerate(run.video):
        near = np.flatnonzero(np.abs(times - frame.t) <= window_s)
        if not len(near):
            continue
        candidates = [strong[k][1] for k in near]
        # Compare alignments by where they put this frame's camera, which is what a viewer sees.
        cameras = [map_from_ecef @ np.linalg.inv(a) @ poses[i] for a in candidates]
        positions = np.array([c[:3, 3] for c in cameras])
        centre = np.median(positions, axis=0)
        medoid = int(np.argmin(np.linalg.norm(positions - centre, axis=1)))
        keep = [
            k
            for k, c in enumerate(cameras)
            if np.linalg.norm(c[:3, 3] - cameras[medoid][:3, 3]) <= outlier_m
            and se3.rotation_deg(np.linalg.inv(cameras[medoid]) @ c) <= outlier_deg
        ]
        base = candidates[medoid]
        mean_tangent = np.mean([se3.log(np.linalg.inv(base) @ candidates[k]) for k in keep], axis=0)
        out[i] = base @ se3.exp(mean_tangent)
        support[i] = len(keep)
    has = ~np.isnan(out[:, 0, 0])
    map_from_camera = np.full_like(out, np.nan)
    map_from_camera[has] = map_from_ecef @ np.linalg.inv(out[has]) @ poses[has]
    return Reference(np.array([f.t for f in run.video]), out, map_from_camera, support)


def reference_error(result: Result, ref: Reference) -> tuple[np.ndarray, np.ndarray]:
    """Per replayed frame: the fused camera's distance (m) and angle (deg) from the reference's."""
    position = np.full(len(result.frames), np.nan)
    angle = np.full(len(result.frames), np.nan)
    for row, frame in enumerate(result.frames):
        fused, truth = result.map_from_camera[row], ref.map_from_camera[frame]
        if np.isnan(fused[0, 0]) or np.isnan(truth[0, 0]):
            continue
        position[row] = float(np.linalg.norm(fused[:3, 3] - truth[:3, 3]))
        relative = np.linalg.inv(truth) @ fused
        u, _, vt = np.linalg.svd(relative[:3, :3])
        angle[row] = se3.rotation_deg(se3.transform(u @ vt, np.zeros(3)))
    return position, angle


def _stat(values: np.ndarray, q: float | None = None) -> float:
    values = values[~np.isnan(values)]
    if not len(values):
        return float("nan")
    return float(np.max(values) if q == 100 else np.percentile(values, q) if q is not None else np.median(values))


def summarize(run: Run, result: Result, ref: Reference | None = None) -> dict[str, float | str]:
    decided = [d for d in result.decisions if d is not None]
    reg = registration(run, result)
    has = ~np.isnan(result.alignment[:, 0, 0])
    first = float(result.t[np.argmax(has)] - result.t[0]) if has.any() else float("nan")
    summary: dict[str, float | str] = {
        "algorithm": result.name,
        "requests": len(result.requests),
        "accepted": sum(d.accepted for d in decided),
        "rejected": sum(not d.accepted for d in decided),
        "first_fix_s": first,
        "registration_median_px": _stat(reg.median_px),
        "registration_p90_px": _stat(reg.median_px, 90),
        "jumps_over_5cm": int(np.sum(result.correction_m > 0.05)),
        "correction_max_cm": _stat(result.correction_m * 100, 100),
        "correction_max_deg": _stat(result.correction_deg, 100),
        "correction_total_m": float(np.nansum(result.correction_m)),
    }
    if ref is not None:
        position, angle = reference_error(result, ref)
        summary.update({
            "ref_error_median_cm": _stat(position * 100),
            "ref_error_p90_cm": _stat(position * 100, 90),
            "ref_error_median_deg": _stat(angle),
            "ref_error_p90_deg": _stat(angle, 90),
        })
    return summary
