from typing import Any, cast

import pytest
import torch
from numpy import arange, float16, float32, ones
from placeframe_core.lightglue import DescriptorsArrays, KeypointsArrays, lightglue_match
from placeframe_core.reconstruction_options import ReconstructionOptions
from reconstructor.options_builder import OptionsBuilder


# Stands in for LightGlue: records what it receives and matches keypoint i to keypoint i.
class _RecordingMatcher:
    def __init__(self) -> None:
        self.descriptor_dtypes: set[torch.dtype] = set()

    def __call__(self, data: dict[str, Any]) -> dict[str, torch.Tensor]:
        self.descriptor_dtypes.update({data["image0"]["descriptors"].dtype, data["image1"]["descriptors"].dtype})
        batch, length = data["image0"]["keypoints"].shape[:2]
        return {"matches0": torch.arange(length).repeat(batch, 1)}


@pytest.mark.parametrize(("half_precision", "stored_dtype"), [(True, float16), (False, float32)])
def test_descriptors_are_stored_at_the_chosen_precision_and_matched_as_float32(
    half_precision: bool, stored_dtype: type[float16] | type[float32]
) -> None:
    options = OptionsBuilder(
        ReconstructionOptions(half_precision_descriptors=half_precision), is_multi_camera_capture=False
    )
    assert options.local_descriptor_dtype() is stored_dtype

    names = [f"rig/cam/{i}.jpg" for i in range(5)]
    keypoints = KeypointsArrays({name: arange(8, dtype=float32).reshape(4, 2) for name in names})
    descriptors = DescriptorsArrays({name: ones((4, 128), dtype=options.local_descriptor_dtype()) for name in names})
    pairs = [(names[i], names[i + 1]) for i in range(4)]
    matcher = _RecordingMatcher()

    sizes: dict[str, tuple[int, int]] = dict.fromkeys(names, (480, 640))
    matches = lightglue_match(cast(Any, matcher), pairs, keypoints, descriptors, sizes, 2, "cpu")

    assert matcher.descriptor_dtypes == {torch.float32}
    assert set(matches) == set(pairs)
    assert all(len(a) == 4 for a, _ in matches.values())
