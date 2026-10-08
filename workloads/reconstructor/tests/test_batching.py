from __future__ import annotations

import pytest
from reconstructor.batching import (
    LIGHTGLUE_BATCH_KEYPOINT_BUDGET,
    REFERENCE_BATCH_SIZE,
    REFERENCE_MAX_KEYPOINTS,
    lightglue_batch_size,
)


def test_default_cap_keeps_the_historical_batch_size() -> None:
    assert lightglue_batch_size(REFERENCE_MAX_KEYPOINTS) == REFERENCE_BATCH_SIZE


@pytest.mark.parametrize("max_keypoints", [2500, 3500, 5000, 8000, 20000])
def test_batch_times_cap_squared_stays_within_budget(max_keypoints: int) -> None:
    batch = lightglue_batch_size(max_keypoints)
    assert batch >= 1
    # Within budget, unless a single pair already exceeds it -- then one pair is the floor.
    assert batch * max_keypoints**2 <= LIGHTGLUE_BATCH_KEYPOINT_BUDGET or batch == 1


def test_large_caps_match_one_pair_at_a_time() -> None:
    assert lightglue_batch_size(5000) == 1
    assert lightglue_batch_size(8000) == 1


def test_small_caps_match_more_pairs_at_once() -> None:
    assert lightglue_batch_size(1000) == 25


def test_override_wins_over_the_rule() -> None:
    assert lightglue_batch_size(8000, "4") == 4
    assert lightglue_batch_size(2500, " 2 ") == 2


@pytest.mark.parametrize("override", [None, "", "   "])
def test_empty_override_defers_to_the_rule(override: str | None) -> None:
    assert lightglue_batch_size(8000, override) == 1


@pytest.mark.parametrize("override", ["0", "-1", "four"])
def test_bad_override_is_rejected(override: str) -> None:
    with pytest.raises(ValueError, match=r"positive integer|invalid literal"):
        lightglue_batch_size(2500, override)
