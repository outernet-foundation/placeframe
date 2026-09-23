"""How many of a poseless capture's frames survive keyframe selection.

A poseless capture carries a synthetic straight-line trajectory, so the
reconstructor's distance-based keyframe selector degenerates to "keep every k-th
frame". These tests pin what k the CLI asks for, by reimplementing the selector's
one-line rule rather than trusting the arithmetic in isolation.
"""

from __future__ import annotations

import pytest
from scripts.howard_test import POSELESS_STEP_M, keyframe_min_distance_m


def kept(frame_count: int, target_keyframes: int | None) -> int:
    """Frames surviving select_keyframes_by_distance on the synthetic trajectory."""
    threshold = keyframe_min_distance_m(frame_count, target_keyframes)
    keep_count, last_kept = 1, 0
    for index in range(1, frame_count):
        if (index - last_kept) * POSELESS_STEP_M >= threshold:
            keep_count += 1
            last_kept = index
    return keep_count


@pytest.mark.parametrize("frame_count", [1, 2, 30, 73, 372, 5000])
def test_no_target_keeps_every_frame(frame_count: int) -> None:
    """The default: the caller already chose the density, by stride or by folder."""
    assert kept(frame_count, None) == frame_count


def test_a_target_thins_towards_it() -> None:
    assert kept(372, 30) == 29
    assert kept(5000, 100) == 100


def test_a_target_above_the_frame_count_keeps_everything() -> None:
    assert kept(20, 30) == 20


def test_the_reachable_counts_are_the_every_k_th_ones() -> None:
    """Only whole k is reachable, so a target is approached, not hit — 73 frames
    towards 30 keeps every 2nd. The point is that the caller asked for thinning;
    what the old code did was thin by default and quantise silently."""
    assert kept(73, 30) == 37
    assert [kept(73, target) for target in (73, 37, 25, 19)] == [73, 37, 25, 19]
