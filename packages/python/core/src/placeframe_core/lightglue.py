from __future__ import annotations

import logging
from collections import UserDict
from collections.abc import Callable, Mapping, MutableMapping
from typing import NewType

from lightglue import LightGlue  # type: ignore
from numpy import bool_, dtype, float16, float32, intp, ndarray
from torch import Tensor, from_numpy, inference_mode, tensor  # type: ignore
from torch.nn.utils.rnn import pad_sequence

from .numpy_ops import compress, nonzero

logger = logging.getLogger(__name__)

NumMatches = NewType("NumMatches", int)

MatchIndices = dict[
    tuple[str, str],
    tuple[ndarray[tuple[NumMatches], dtype[intp]], ndarray[tuple[NumMatches], dtype[intp]]],
]

# Per-image-name dicts for the matcher's two distinct positional arguments. Branded at the dict
# level so pyright catches positional swaps at the call site — passing Keypoints where Descriptors
# is expected (or vice versa) is a type error, even though both wrap MutableMapping[str, Tensor] at runtime.
# Mappings, not dicts: lightglue_match passes caches that move each image to the device when a batch needs it.
Keypoints = NewType("Keypoints", MutableMapping[str, Tensor])
Descriptors = NewType("Descriptors", MutableMapping[str, Tensor])
KeypointsArrays = NewType("KeypointsArrays", dict[str, ndarray[tuple[int, int], dtype[float32]]])
# Local descriptors are kept in half precision: matching is insensitive to it, and it halves the reconstructor's
# largest memory use. LightGlue receives them as float32 on the device.
DescriptorsArrays = NewType("DescriptorsArrays", dict[str, ndarray[tuple[int, int], dtype[float16]]])


def lightglue_match(
    lightglue: LightGlue,
    pairs: list[tuple[str, str]],
    keypoints: KeypointsArrays,
    descriptors: DescriptorsArrays,
    sizes: dict[str, tuple[int, int]],
    batch_size: int,
    device: str,
    on_progress: Callable[[int], None] | None = None,
) -> MatchIndices:
    # Images move to the device when a batch needs them (the most recent few hundred are kept), not all at once:
    # a 9,000-image map's descriptors alone are 6-12 GB.
    keypoints_tensors = Keypoints(_OnDevice(keypoints, device))
    descriptors_tensors = Descriptors(_OnDevice(descriptors, device))

    return lightglue_match_tensors(
        lightglue, pairs, keypoints_tensors, descriptors_tensors, sizes, batch_size, device, on_progress
    )


def lightglue_match_tensors(
    lightglue: LightGlue,
    pairs: list[tuple[str, str]],
    keypoints: Keypoints,
    descriptors: Descriptors,
    sizes: dict[str, tuple[int, int]],
    batch_size: int,
    device: str,
    on_progress: Callable[[int], None] | None = None,
) -> MatchIndices:
    num_batches = (len(pairs) + batch_size - 1) // batch_size
    match_indices: MatchIndices = {}
    for batch_start in range(0, len(pairs), batch_size):
        logger.info("Matching features: batch %d of %d", batch_start // batch_size + 1, num_batches)
        batch_pairs = pairs[batch_start : batch_start + batch_size]

        with inference_mode():
            matches = lightglue({
                "image0": {
                    "keypoints": pad_sequence([keypoints[a] for a, _ in batch_pairs], batch_first=True),
                    "descriptors": pad_sequence([descriptors[a] for a, _ in batch_pairs], batch_first=True),
                    "image_size": tensor([sizes[a] for a, _ in batch_pairs], device=device),
                },
                "image1": {
                    "keypoints": pad_sequence([keypoints[b] for _, b in batch_pairs], batch_first=True),
                    "descriptors": pad_sequence([descriptors[b] for _, b in batch_pairs], batch_first=True),
                    "image_size": tensor([sizes[b] for _, b in batch_pairs], device=device),
                },
            })["matches0"]

        for i, (image_a, image_b) in enumerate(batch_pairs):
            image_a_num_keypoints = keypoints[image_a].shape[0]

            # Get actual batch matches (without padding), move to CPU, and convert to numpy
            batch_matches = matches[i, :image_a_num_keypoints].cpu().numpy().astype(intp)

            # Mask out non-matches (-1)
            mask: ndarray[tuple[int], dtype[bool_]] = batch_matches >= 0
            match_indices[(image_a, image_b)] = (nonzero(mask)[0], compress(mask, batch_matches))

        if on_progress is not None:
            on_progress(batch_start + len(batch_pairs))

    return match_indices


# Arrays by image name, moved to the device (as float32) on first use; the oldest are dropped beyond `keep`.
class _OnDevice(UserDict[str, Tensor]):
    def __init__(
        self, arrays: Mapping[str, ndarray[tuple[int, int], dtype[float16 | float32]]], device: str, keep: int = 512
    ) -> None:
        super().__init__()
        self._arrays, self._device, self._keep = arrays, device, keep

    def __missing__(self, name: str) -> Tensor:
        if len(self) >= self._keep:
            del self[next(iter(self))]  # insertion order: the oldest
        value = from_numpy(self._arrays[name]).to(self._device).float()
        self[name] = value
        return value
