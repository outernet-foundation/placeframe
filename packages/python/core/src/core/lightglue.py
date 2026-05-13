from __future__ import annotations

from collections.abc import Callable
from typing import NewType

from lightglue import LightGlue  # type: ignore
from numpy import bool_, dtype, float32, intp, ndarray
from torch import Tensor, from_numpy, inference_mode, tensor  # type: ignore
from torch.nn.utils.rnn import pad_sequence

from .numpy_ops import compress, nonzero

NumMatches = NewType("NumMatches", int)

MatchIndices = dict[
    tuple[str, str],
    tuple[ndarray[tuple[NumMatches], dtype[intp]], ndarray[tuple[NumMatches], dtype[intp]]],
]

# Per-image-name dicts for the matcher's two distinct positional arguments. Branded at the dict
# level so pyright catches positional swaps at the call site — passing Keypoints where Descriptors
# is expected (or vice versa) is a type error, even though both wrap dict[str, Tensor] at runtime.
Keypoints = NewType("Keypoints", dict[str, Tensor])
Descriptors = NewType("Descriptors", dict[str, Tensor])
KeypointsArrays = NewType("KeypointsArrays", dict[str, ndarray[tuple[int, int], dtype[float32]]])
DescriptorsArrays = NewType("DescriptorsArrays", dict[str, ndarray[tuple[int, int], dtype[float32]]])


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
    keypoints_tensors = Keypoints({name: from_numpy(kp).to(device) for name, kp in keypoints.items()})
    descriptors_tensors = Descriptors({name: from_numpy(desc).to(device) for name, desc in descriptors.items()})

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
        print(f"Matching features: batch {batch_start // batch_size + 1} of {num_batches}")
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
