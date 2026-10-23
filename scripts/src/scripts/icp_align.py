"""Refine a coarse placement of one map onto another by ICP on their point clouds.

The use: a single-walk Insta360 map has no metric scale, and the align page's placement of it on a
Zed map is a by-eye starting point. ICP turns that into a Sim(3) good to centimetres near the
cameras, which transform-reconstruction then applies to every pose and point.

Only points within NEAR_PATH_M of both camera paths take part: far points are the least accurate
(stereo depth error grows with range squared) and the least likely to be seen by both walks. Both
clouds are thinned to one voxel size in the reference's units, so the dense map does not outvote
the sparse one. The fit runs trimmed point-to-point with a tightening match radius, then
point-to-plane against the reference's local planes, Huber-weighted. Rotation is free about all
three axes. Two restarts from deliberately perturbed placements, on other subsamples, report how
well the answer is pinned down: where they land on the candidate's camera path, against the main
answer.

On the Fosun site (Insta360 onto a Zed merge) this moved a by-eye placement by 0.15% in scale,
0.6 degrees in yaw and 1.3 m, and eight perturbed restarts agreed to 0.04% in scale and 0.15
degrees; within 8 m of the Zed cameras the clouds then sat a median 0.14 m apart.
"""

from __future__ import annotations

import tarfile
from collections.abc import Callable
from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path
from typing import Any, cast

import numpy as np
from numpy.typing import NDArray  # noqa: TID251 -- point clouds of varying length, not worth shape-branding
from scipy.spatial import cKDTree

Floats = NDArray[np.float64]
Sim3 = tuple[float, Floats, Floats]  # X' = scale * R @ X + translation

POINT_CLOUD_MEMBER = "sfm_model/points3D.npz"
FRAME_POSES_MEMBER = "sfm_model/frame_poses.npz"
NEAR_PATH_M = 30.0
VOXEL_M = 0.15
CANDIDATE_POINTS = 60_000
REFERENCE_POINTS = 150_000
POINT_TO_POINT_RADII_M = (3.0, 1.5, 0.75, 0.5)
POINT_TO_PLANE_RADII_M = (0.5, 0.25)
HUBER_M = 0.05
MIN_PLANARITY = 0.3  # point-to-plane only where the reference surface is locally a plane
RESTARTS = 2
RESTART_YAW_DEG = 3.0
RESTART_SCALE = 0.04
RESTART_SHIFT_M = 1.5
MIN_MATCHES = 200

Progress = Callable[[int, int], None]


@dataclass(frozen=True)
class Cloud:
    points: Floats
    cameras: Floats  # one position per registered frame


@dataclass(frozen=True)
class IcpResult:
    transform: Sim3
    fit: dict[str, float]
    restarts: list[dict[str, float]] = field(default_factory=list[dict[str, float]])

    def record(self) -> dict[str, Any]:
        """The transform-reconstruction --sim3 shape, with how it was found."""
        s, rotation, t = self.transform
        return {
            "scale": s,
            "R": rotation.tolist(),
            "translation": t.tolist(),
            "yaw_deg": yaw_deg(rotation),
            "tilt_deg": tilt_deg(rotation),
            "fit": self.fit,
            "restarts": self.restarts,
        }


def read_cloud(tar_path: Path) -> Cloud:
    """The point cloud and camera positions of a reconstruction tar, without unpacking the rest."""
    wanted = {POINT_CLOUD_MEMBER: b"", FRAME_POSES_MEMBER: b""}
    with tarfile.open(tar_path, mode="r:*") as tar:
        for member in tar:
            if member.name in wanted:
                handle = tar.extractfile(member)
                if handle is not None:
                    wanted[member.name] = handle.read()
            if all(wanted.values()):
                break
    missing = [name for name, data in wanted.items() if not data]
    if missing:
        raise ValueError(f"{tar_path.name} has no {', '.join(missing)}")
    points = np.load(BytesIO(wanted[POINT_CLOUD_MEMBER]))["positions"].astype(np.float64)
    cameras = np.load(BytesIO(wanted[FRAME_POSES_MEMBER]))["positions"].astype(np.float64)
    return Cloud(points, cameras)


def yaw_matrix(deg: float) -> Floats:
    """Rotation about the vertical (y) axis, in the align page's convention."""
    c, s = np.cos(np.radians(deg)), np.sin(np.radians(deg))
    return np.array([[c, 0.0, s], [0.0, 1.0, 0.0], [-s, 0.0, c]])


def yaw_deg(rotation: Floats) -> float:
    return float(np.degrees(np.arctan2(rotation[0, 2], rotation[0, 0])))


def tilt_deg(rotation: Floats) -> float:
    """Angle between the two maps' vertical axes."""
    return float(np.degrees(np.arccos(np.clip(rotation[1, 1], -1.0, 1.0))))


def apply(transform: Sim3, points: Floats) -> Floats:
    s, rotation, t = transform
    return s * (points @ rotation.T) + t


def compose(outer: Sim3, inner: Sim3) -> Sim3:
    """`outer` after `inner`."""
    sa, ra, ta = outer
    sb, rb, tb = inner
    return sa * sb, ra @ rb, sa * (ra @ tb) + ta


def _rotvec(w: Floats) -> Floats:
    theta = float(np.linalg.norm(w))
    if theta < 1e-12:
        return np.eye(3)
    k = w / theta
    K = np.array([[0.0, -k[2], k[1]], [k[2], 0.0, -k[0]], [-k[1], k[0], 0.0]])
    return np.eye(3) + np.sin(theta) * K + (1 - np.cos(theta)) * (K @ K)


def _voxel(points: Floats, size: float, cap: int, rng: np.random.Generator) -> Floats:
    _, first = np.unique(np.floor(points / size).astype(np.int64), axis=0, return_index=True)
    kept = points[np.sort(first)]
    return kept[rng.choice(len(kept), cap, replace=False)] if len(kept) > cap else kept


def _nearest(tree: cKDTree, points: Floats) -> tuple[Floats, NDArray[np.intp]]:
    d, j = cast("tuple[Floats, NDArray[np.intp]]", tree.query(points))
    return d, j


def _umeyama(src: Floats, dst: Floats, with_scale: bool) -> Sim3:
    mu_s, mu_d = src.mean(0), dst.mean(0)
    S, D = src - mu_s, dst - mu_d
    U, sig, Vt = np.linalg.svd(S.T @ D / len(src))
    E = np.diag([1.0, 1.0, float(np.sign(np.linalg.det(U @ Vt)))])
    R = Vt.T @ E @ U.T
    s = float(np.trace(np.diag(sig) @ E) / (S**2).sum() * len(src)) if with_scale else 1.0
    return s, R, mu_d - s * (R @ mu_s)


def _normals(points: Floats, tree: cKDTree, k: int = 20) -> tuple[Floats, Floats]:
    _, j = cast("tuple[Floats, NDArray[np.intp]]", tree.query(points, k))
    neighbours = points[j] - points[j].mean(1, keepdims=True)
    w, v = np.linalg.eigh(np.einsum("nki,nkj->nij", neighbours, neighbours))
    planarity = (w[:, 1] - w[:, 0]) / np.maximum(w[:, 2], 1e-12)
    return v[:, :, 0], planarity


@dataclass(frozen=True)
class _Reference:
    points: Floats
    tree: cKDTree
    normals: Floats
    planar: NDArray[np.bool_]


def _point_to_point(src: Floats, ref: _Reference, current: Sim3, radius: float, with_scale: bool) -> Sim3:
    for _ in range(40):
        S = apply(current, src)
        d, j = _nearest(ref.tree, S)
        m = np.argsort(d)[: int(len(d) * 0.7)]
        m = m[d[m] < radius]
        if len(m) < MIN_MATCHES:
            raise ValueError(
                f"only {len(m)} points of the candidate lie within {radius} m of the reference; "
                "the placement is too far off for ICP to start from"
            )
        step = _umeyama(S[m], ref.points[j[m]], with_scale)
        current = compose(step, current)
        if abs(step[0] - 1) < 1e-6 and float(np.linalg.norm(step[2])) < 1e-4:
            break
    return current


def _point_to_plane(src: Floats, ref: _Reference, current: Sim3, radius: float, with_scale: bool) -> Sim3:
    """Gauss-Newton on n . (s R p + t - q): a small rotation, translation and log-scale per step."""
    for _ in range(30):
        S = apply(current, src)
        d, j = _nearest(ref.tree, S)
        m = (d < radius) & ref.planar[j]
        if int(m.sum()) < MIN_MATCHES:
            break
        p, q, n = S[m], ref.points[j[m]], ref.normals[j[m]]
        c = p.mean(0)  # linearised about the matched centroid, so rotation and translation decouple
        pc = p - c
        r = np.einsum("ij,ij->i", n, p - q)
        columns: list[Floats] = [cast("Floats", np.cross(pc, n)), n]
        if with_scale:
            columns.append(np.einsum("ij,ij->i", n, pc)[:, None])
        J: Floats = np.hstack(columns)
        w: Floats = np.where(np.abs(r) < HUBER_M, 1.0, HUBER_M / np.maximum(np.abs(r), 1e-12))
        x = cast("Floats", np.linalg.solve(J.T @ (J * w[:, None]) + 1e-9 * np.eye(J.shape[1]), -J.T @ (w * r)))
        dR, dt = _rotvec(x[:3]), x[3:6]
        ds = float(np.exp(x[6])) if with_scale else 1.0
        current = compose((ds, dR, c + dt - ds * (dR @ c)), current)
        if float(np.linalg.norm(x)) < 1e-6:
            break
    return current


def _refine(src: Floats, ref: _Reference, current: Sim3, with_scale: bool, step: Callable[[], None]) -> Sim3:
    for radius in POINT_TO_POINT_RADII_M:
        current = _point_to_point(src, ref, current, radius, with_scale)
        step()
    for radius in POINT_TO_PLANE_RADII_M:
        current = _point_to_plane(src, ref, current, radius, with_scale)
        step()
    return current


def _fit_stats(transform: Sim3, src: Floats, ref: _Reference, reference_cameras: Floats) -> dict[str, float]:
    d, _ = _nearest(ref.tree, apply(transform, src))
    # near the reference's cameras is where its geometry is most accurate, and where a device will be
    near = cast("Floats", cKDTree(reference_cameras).query(ref.points)[0]) < 8.0
    back, _ = _nearest(cKDTree(apply(transform, src)), ref.points[near]) if near.any() else (np.zeros(1), None)
    return {
        "candidate_to_reference_median_m": float(np.median(d)),
        "candidate_within_0.25m": float((d < 0.25).mean()),
        "reference_near_cameras_to_candidate_median_m": float(np.median(back)),
        "reference_near_cameras_within_0.25m": float((back < 0.25).mean()),
    }


def steps_total() -> int:
    return (1 + RESTARTS) * (len(POINT_TO_POINT_RADII_M) + len(POINT_TO_PLANE_RADII_M))


def icp_align(
    candidate: Cloud, reference: Cloud, initial: Sim3, fit_scale: bool, progress: Progress | None = None
) -> IcpResult:
    """The Sim(3) taking the candidate onto the reference, refined from `initial`.

    With fit_scale false the scale stays at the initial one: right when the candidate is metric
    already (a stereo map), where a free scale could only move it away from correct.
    """
    total = steps_total()
    done = 0

    def step() -> None:
        nonlocal done
        done += 1
        if progress is not None:
            progress(done, total)

    rng = np.random.default_rng(0)
    placed_points, placed_cameras = apply(initial, candidate.points), apply(initial, candidate.cameras)
    reference_path, candidate_path = cKDTree(reference.cameras), cKDTree(placed_cameras)

    def overlap(points: Floats) -> NDArray[np.bool_]:
        near_reference = cast("Floats", reference_path.query(points)[0]) < NEAR_PATH_M
        near_candidate = cast("Floats", candidate_path.query(points)[0]) < NEAR_PATH_M
        return near_reference & near_candidate

    ref_points = _voxel(reference.points[overlap(reference.points)], VOXEL_M, REFERENCE_POINTS, rng)
    in_overlap = placed_points[overlap(placed_points)]
    if len(ref_points) < MIN_MATCHES or len(in_overlap) < MIN_MATCHES:
        raise ValueError(
            f"the placement leaves too little overlap ({len(in_overlap)} candidate and {len(ref_points)} reference "
            f"points within {NEAR_PATH_M:.0f} m of both camera paths); place the maps over each other first"
        )
    tree = cKDTree(ref_points)
    normals, planarity = _normals(ref_points, tree)
    ref = _Reference(ref_points, tree, normals, planarity > MIN_PLANARITY)
    s0, R0, t0 = initial

    def sample(seed: int) -> Floats:
        # thinned in the reference's units, then taken back into the candidate's frame
        placed = _voxel(in_overlap, VOXEL_M, CANDIDATE_POINTS, np.random.default_rng(seed))
        return ((placed - t0) @ R0) / s0

    src = sample(1)
    found = _refine(src, ref, initial, fit_scale, step)
    restarts: list[dict[str, float]] = []
    for k in range(RESTARTS):
        r = np.random.default_rng(100 + k)
        dyaw = float(r.uniform(-RESTART_YAW_DEG, RESTART_YAW_DEG))
        dscale = float(r.uniform(-RESTART_SCALE, RESTART_SCALE)) if fit_scale else 0.0
        shift = np.array([
            r.uniform(-RESTART_SHIFT_M, RESTART_SHIFT_M),
            0.0,
            r.uniform(-RESTART_SHIFT_M, RESTART_SHIFT_M),
        ])
        start: Sim3 = (s0 * (1 + dscale), yaw_matrix(dyaw) @ R0, t0 + shift)
        restarted = _refine(sample(10 + k), ref, start, fit_scale, step)
        gap = np.linalg.norm(apply(restarted, candidate.cameras) - apply(found, candidate.cameras), axis=1)
        restarts.append({
            "start_yaw_offset_deg": dyaw,
            "start_scale_offset_pct": 100 * dscale,
            "scale": restarted[0],
            "yaw_deg": yaw_deg(restarted[1]),
            "camera_path_gap_median_m": float(np.median(gap)),
            "camera_path_gap_max_m": float(gap.max()),
        })
    fit = _fit_stats(found, src, ref, reference.cameras)
    fit["initial_candidate_to_reference_median_m"] = _fit_stats(initial, src, ref, reference.cameras)[
        "candidate_to_reference_median_m"
    ]
    return IcpResult(found, fit, restarts)


__all__ = ["Cloud", "IcpResult", "Sim3", "apply", "icp_align", "read_cloud", "steps_total", "yaw_matrix"]
