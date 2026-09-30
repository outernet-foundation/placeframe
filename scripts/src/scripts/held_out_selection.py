# Held-out frame selection for fit-calibration.
#
# A `HeldOutFrameSelector` picks a subset of capture-session frames to withhold
# from map building so the localizer can be evaluated on them as ground truth.
# Selectors are invoked by name through `get_selector` so a future strategy
# (e.g. spatial-bin) lands without surgery to fit_calibration.py's orchestration
# loop or the localization-evaluations contract.
#
# `StrideHeldOutSelector` is the chosen starter:
#   - Deterministic. Same frames.csv + target_count → same selection.
#   - Scales to capture length. Stride adapts to total frame count.
#   - Roughly even spatial coverage on smooth capture paths (operator typically
#     walks a continuous trajectory, so even temporal stride ≈ even spatial stride).
#
# Known limitations of stride selection:
#   - Connectivity loss. A held-out frame may be one the SfM needed to bridge
#     two view clusters; pulling it could fragment the reconstruction. No
#     post-build filter is applied, so the held-out set is not validated against
#     what the SfM ultimately registered.
#   - Non-smooth captures. Operators who pause, backtrack, or revisit areas get
#     uneven spatial coverage from temporal stride.
#   - Fixed count. `target_count = 100` regardless of capture length means
#     short captures lose proportionally more frames than long ones.
#
# Ideas for later (each a candidate new selector):
#   - Post-build filter: drop held-outs the SfM unregistered, augment from the
#     registered pool to maintain target_count.
#   - Spatial-bin: voxelize positions from frames.csv and pick one frame per
#     occupied voxel for true spatial uniformity.
#   - Hybrid stride+voxel: stride pre-filter, voxel-bin tie-break.
#   - Fraction-of-registered count: target = max(20, registered_frames // 10).
#
# Adding a new strategy means: new class implementing HeldOutFrameSelector,
# register it in `_REGISTRY`, expose via `get_selector(name)`. Nothing in
# fit_calibration.py changes.
from __future__ import annotations

from csv import DictReader
from dataclasses import dataclass
from io import StringIO
from typing import Protocol


@dataclass
class HeldOutSelectionOptions:
    target_count: int = 100


class HeldOutFrameSelector(Protocol):
    def __call__(self, frames_csv: str, options: HeldOutSelectionOptions) -> list[int]: ...


class StrideHeldOutSelector:
    def __call__(self, frames_csv: str, options: HeldOutSelectionOptions) -> list[int]:
        timestamps = [int(row["timestamp_ms"]) for row in DictReader(StringIO(frames_csv))]
        if not timestamps:
            return []
        if options.target_count <= 0:
            return []
        stride = max(1, len(timestamps) // options.target_count)
        return timestamps[stride // 2 :: stride]


_REGISTRY: dict[str, HeldOutFrameSelector] = {
    "stride": StrideHeldOutSelector(),
}


def get_selector(name: str) -> HeldOutFrameSelector:
    if name not in _REGISTRY:
        raise ValueError(f"Unknown held-out selector: {name!r}. Known: {sorted(_REGISTRY)}")
    return _REGISTRY[name]
