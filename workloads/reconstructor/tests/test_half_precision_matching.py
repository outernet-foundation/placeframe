from typing import Any, cast

import torch
from numpy import arange, float16, float32, ones
from placeframe_core.lightglue import DescriptorsArrays, KeypointsArrays, lightglue_match


# Stands in for LightGlue: records what it receives and matches keypoint i to keypoint i.
class _RecordingMatcher:
    def __init__(self) -> None:
        self.descriptor_dtypes: set[torch.dtype] = set()

    def __call__(self, data: dict[str, Any]) -> dict[str, torch.Tensor]:
        self.descriptor_dtypes.update({data["image0"]["descriptors"].dtype, data["image1"]["descriptors"].dtype})
        batch, length = data["image0"]["keypoints"].shape[:2]
        return {"matches0": torch.arange(length).repeat(batch, 1)}


def test_half_precision_descriptors_are_matched_as_float32() -> None:
    names = [f"rig/cam/{i}.jpg" for i in range(5)]
    keypoints = KeypointsArrays({name: arange(8, dtype=float32).reshape(4, 2) for name in names})
    descriptors = DescriptorsArrays({name: ones((4, 128), dtype=float16) for name in names})
    pairs = [(names[i], names[i + 1]) for i in range(4)]
    matcher = _RecordingMatcher()

    sizes: dict[str, tuple[int, int]] = dict.fromkeys(names, (480, 640))
    matches = lightglue_match(cast(Any, matcher), pairs, keypoints, descriptors, sizes, 2, "cpu")

    assert matcher.descriptor_dtypes == {torch.float32}
    assert set(matches) == set(pairs)
    assert all(len(a) == 4 for a, _ in matches.values())
