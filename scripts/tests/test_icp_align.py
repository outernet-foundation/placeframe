"""ICP recovers a known similarity transform from a by-eye starting placement.

The scene is what ICP has to work with on a street: a ground plane, building walls and a few
boxes, sampled more densely in the candidate than in the reference (a dense Insta360 map onto a
sparser Zed one), with noise on both.
"""

from __future__ import annotations

import numpy as np
import pytest
from scripts.icp_align import Cloud, apply, icp_align, tilt_deg, yaw_deg, yaw_matrix


def _scene(rng: np.random.Generator, n: int) -> np.ndarray:
    def box(lo: list[float], hi: list[float], k: int) -> np.ndarray:
        return rng.uniform(lo, hi, (k, 3))

    parts = [
        box([-30, 1.5, -30], [30, 1.5, 30], n // 2),  # ground, y down: 1.5 m below the cameras
        box([-30, -6, 20], [30, 1.5, 20], n // 8),  # walls
        box([-30, -6, -20], [10, 1.5, -20], n // 8),
        box([25, -6, -30], [25, 1.5, 15], n // 8),
        box([-5, -1, 3], [-3, 1.5, 6], n // 16),  # boxes, which pin the slide along the walls
        box([8, -2, -8], [11, 1.5, -6], n // 16),
    ]
    return np.vstack(parts)


@pytest.mark.parametrize("fit_scale", [True, False])
def test_recovers_a_known_transform_from_a_rough_placement(fit_scale: bool) -> None:
    rng = np.random.default_rng(3)
    path = np.column_stack([np.linspace(-25, 20, 60), np.zeros(60), np.linspace(-10, 10, 60)])
    reference = Cloud(_scene(rng, 20_000) + rng.normal(0, 0.02, (20_000, 3)), path)
    # the candidate's own frame: the reference, taken out by the inverse of the truth
    truth_scale = 2.9 if fit_scale else 1.0
    truth = (truth_scale, yaw_matrix(25.0), np.array([4.0, 0.3, -7.0]))
    s, R, t = truth

    def to_candidate(points: np.ndarray) -> np.ndarray:
        return ((points - t) @ R) / s

    candidate = Cloud(to_candidate(_scene(rng, 60_000) + rng.normal(0, 0.03, (60_000, 3))), to_candidate(path))

    # off the way a by-eye placement is: 2 degrees, 3% in scale (if free), a metre
    start = (truth_scale * (1.03 if fit_scale else 1.0), yaw_matrix(27.0), t + np.array([1.0, 0.0, -0.8]))
    steps: list[tuple[int, int]] = []
    result = icp_align(candidate, reference, start, fit_scale, lambda done, total: steps.append((done, total)))

    found = result.transform
    assert abs(found[0] / truth_scale - 1) < 2e-3
    assert abs(yaw_deg(found[1]) - 25.0) < 0.2
    assert tilt_deg(found[1]) < 0.2
    gap = np.linalg.norm(apply(found, candidate.cameras) - path, axis=1)
    assert gap.max() < 0.05
    assert steps[-1][0] == steps[-1][1]  # progress reaches its total
    assert all(r["camera_path_gap_max_m"] < 0.1 for r in result.restarts)


def test_a_placement_with_no_overlap_is_refused() -> None:
    rng = np.random.default_rng(0)
    path = np.zeros((10, 3))
    cloud = Cloud(_scene(rng, 5_000), path)
    far = (1.0, np.eye(3), np.array([500.0, 0.0, 0.0]))
    with pytest.raises(ValueError, match="overlap"):
        icp_align(cloud, cloud, far, fit_scale=True)
