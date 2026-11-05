"""Run a fusion algorithm over a stretch of a run, the way the device would have run it."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from . import se3
from .algorithms import Decision, Fusion
from .data import Run
from .schedule import Request

Matrix = np.ndarray


@dataclass
class Result:
    name: str
    frames: np.ndarray  # video frame indices replayed
    t: np.ndarray
    alignment: np.ndarray  # (N, 4, 4) Unity from ECEF, NaN before the first fix
    map_from_camera: np.ndarray  # (N, 4, 4) the camera in the map, as the fused pose has it; NaN before
    diagnostics: dict[str, np.ndarray]
    requests: list[Request]
    decisions: list[Decision | None]  # None: its answer landed after the stretch ended
    apply_frame: list[int | None]  # video frame index each request was applied at
    correction_m: np.ndarray  # how far each frame's change of alignment moved the camera in the map
    correction_deg: np.ndarray
    seed: int | None = None
    notes: dict[str, str] = field(default_factory=dict)

    def at(self, frame: int) -> int | None:
        """Row of this result for a video frame index, if it was replayed."""
        row = int(frame - self.frames[0])
        return row if 0 <= row < len(self.frames) else None

    def has_fix(self, frame: int) -> bool:
        row = self.at(frame)
        return row is not None and not np.isnan(self.alignment[row, 0, 0])


def ecef_from_map(run: Run) -> Matrix:
    for fix in run.fixes:
        if fix.ok and fix.ecef_from_map is not None:
            return fix.ecef_from_map
    return np.eye(4)


def replay(
    run: Run,
    algorithm: Fusion,
    requests: list[Request],
    start_t: float = 0.0,
    end_t: float | None = None,
    seed_still: int | None = None,
) -> Result:
    """Replay video frames from `start_t` to `end_t`. `seed_still` hands that still's fix to the
    algorithm before the first frame, to start a stretch already localized."""
    end = run.video[-1].t if end_t is None else end_t
    frames = np.array([f.index for f in run.video if start_t <= f.t <= end])
    if not len(frames):
        raise ValueError(f"No video frames between {start_t} and {end}")
    pending = sorted(range(len(requests)), key=lambda i: requests[i].apply_t)
    decisions: list[Decision | None] = [None] * len(requests)
    apply_frame: list[int | None] = [None] * len(requests)
    nan = np.full((4, 4), np.nan)
    alignments, diagnostics_rows = [], []

    if seed_still is not None:
        still = run.stills[seed_still]
        algorithm.on_vps(still.t, run.fixes[seed_still], still.unity_from_camera)

    cursor = 0
    for index in frames:
        frame = run.video[index]
        while cursor < len(pending) and requests[pending[cursor]].apply_t <= frame.t:
            i = pending[cursor]
            cursor += 1
            request = requests[i]
            still = run.stills[request.still]
            decisions[i] = algorithm.on_vps(request.apply_t, request.fix, still.unity_from_camera)
            apply_frame[i] = int(index)
        algorithm.on_frame(frame.t, frame.unity_from_camera)
        alignment = algorithm.alignment()
        alignments.append(nan if alignment is None else alignment)
        diagnostics_rows.append(algorithm.diagnostics())

    alignment_array = np.stack(alignments)
    poses = np.stack([run.video[i].unity_from_camera for i in frames])
    map_from_ecef = np.linalg.inv(ecef_from_map(run))
    map_from_camera = np.full_like(alignment_array, np.nan)
    has = ~np.isnan(alignment_array[:, 0, 0])
    if has.any():
        map_from_camera[has] = map_from_ecef @ np.linalg.inv(alignment_array[has]) @ poses[has]

    # The correction: the camera's pose in the map under this frame's alignment against the last
    # frame's, with the same VIO pose, so the camera's own motion is taken out.
    correction_m = np.full(len(frames), np.nan)
    correction_deg = np.full(len(frames), np.nan)
    for row in range(1, len(frames)):
        if has[row] and has[row - 1]:
            before = map_from_ecef @ np.linalg.inv(alignment_array[row - 1]) @ poses[row]
            change = np.linalg.inv(before) @ map_from_camera[row]
            correction_m[row] = float(np.linalg.norm(map_from_camera[row][:3, 3] - before[:3, 3]))
            correction_deg[row] = se3.rotation_deg(_orthonormal(change))

    keys = sorted({k for row in diagnostics_rows for k in row})
    diagnostics = {k: np.array([row.get(k, np.nan) for row in diagnostics_rows]) for k in keys}
    return Result(
        name=algorithm.name,
        frames=frames,
        t=np.array([run.video[i].t for i in frames]),
        alignment=alignment_array,
        map_from_camera=map_from_camera,
        diagnostics=diagnostics,
        requests=requests,
        decisions=decisions,
        apply_frame=apply_frame,
        correction_m=correction_m,
        correction_deg=correction_deg,
        seed=seed_still,
    )


def _orthonormal(matrix: Matrix) -> Matrix:
    """The rotation part of a pose that may carry a scale."""
    u, _, vt = np.linalg.svd(matrix[:3, :3])
    out = np.eye(4)
    out[:3, :3] = u @ vt
    return out
