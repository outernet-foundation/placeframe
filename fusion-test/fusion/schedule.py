"""Which fixes reach the algorithm, and when.

The device asks for a fix every `interval_s` (ThrottleLast), localizing the latest still, and drops
a tick while a request is in flight (AwaitOperation.Drop); the fix lands `latency_s` after the
request. Here every still already has its fix, so a schedule only picks which ones and when they
land; edits then remove fixes or tamper with them.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np

from . import se3
from .data import Fix, Run


@dataclass(frozen=True)
class Request:
    fix: Fix
    request_t: float  # when it was asked for
    apply_t: float  # when its answer reaches the algorithm
    note: str = ""  # what an edit did to it

    @property
    def still(self) -> int:
        return self.fix.still


def device(
    run: Run, interval_s: float = 1.0, latency_s: float = 2.0, start_t: float = 0.0, end_t: float | None = None
) -> list[Request]:
    """The requests the device would have made between `start_t` and `end_t`."""
    end = run.video[-1].t if end_t is None else end_t
    still_times = np.array([s.t for s in run.stills])
    requests: list[Request] = []
    busy_until = start_t
    used: set[int] = set()
    tick = start_t + interval_s
    while tick <= end + 1e-9:
        latest = int(np.searchsorted(still_times, tick, side="right")) - 1
        if latest >= 0 and tick >= busy_until and latest not in used and still_times[latest] >= start_t:
            used.add(latest)
            requests.append(Request(run.fixes[latest], tick, tick + latency_s))
            busy_until = tick + latency_s
        tick += interval_s
    return requests


def every_still(run: Run, latency_s: float = 0.0, start_t: float = 0.0, end_t: float | None = None) -> list[Request]:
    """Every still's fix, as if VPS kept up with the stills (4 Hz)."""
    end = run.video[-1].t if end_t is None else end_t
    return [Request(run.fixes[s.index], s.t, s.t + latency_s) for s in run.stills if start_t <= s.t <= end]


def at_stills(run: Run, stills: list[int], latency_s: float = 2.0) -> list[Request]:
    """Exactly these stills' fixes, each asked for when its still was taken."""
    return [Request(run.fixes[i], run.stills[i].t, run.stills[i].t + latency_s) for i in sorted(stills)]


# --- edits ---------------------------------------------------------------------------------------


def drop(requests: list[Request], stills: set[int]) -> list[Request]:
    return [r for r in requests if r.still not in stills]


def min_inliers(requests: list[Request], count: int) -> list[Request]:
    """Drop fixes with fewer inliers, as a stricter server-side gate would."""
    return [r for r in requests if not r.fix.ok or r.fix.num_inliers >= count]


def perturb(
    requests: list[Request], still: int, rotation_deg: float, translation_m: float, seed: int = 0
) -> list[Request]:
    """Corrupt one fix: its camera pose moved by a random rotation and shift of these sizes, in the map."""
    rng = np.random.default_rng(seed)
    out = []
    for r in requests:
        if r.still == still and r.fix.ok and r.fix.camera_from_map is not None:
            map_from_camera = se3.perturb(r.fix.map_from_camera, rotation_deg, translation_m, rng)
            fix = replace(r.fix, camera_from_map=np.linalg.inv(map_from_camera))
            r = replace(r, fix=fix, note=f"perturbed {rotation_deg:g} deg, {translation_m:g} m")
        out.append(r)
    return out


def delay(requests: list[Request], still: int, extra_s: float) -> list[Request]:
    return [
        replace(r, apply_t=r.apply_t + extra_s, note=f"+{extra_s:g} s") if r.still == still else r for r in requests
    ]
