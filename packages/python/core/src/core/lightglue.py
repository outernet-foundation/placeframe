from lightglue import LightGlue  # type: ignore
from numpy import float32, int32, intp, nonzero
from numpy.typing import NDArray
from torch import Tensor, from_numpy, inference_mode, tensor  # type: ignore
from torch.nn.utils.rnn import pad_sequence


def lightglue_match(
    lightglue: LightGlue,
    pairs: list[tuple[str, str]],
    keypoints: dict[str, NDArray[float32]],
    descriptors: dict[str, NDArray[float32]],
    sizes: dict[str, tuple[int, int]],
    batch_size: int,
    device: str,
):
    keypoints_tensors = {name: from_numpy(kp).to(device) for name, kp in keypoints.items()}
    descriptors_tensors = {name: from_numpy(desc).to(device) for name, desc in descriptors.items()}

    return lightglue_match_tensors(lightglue, pairs, keypoints_tensors, descriptors_tensors, sizes, batch_size, device)


def lightglue_match_tensors(
    lightglue: LightGlue,
    pairs: list[tuple[str, str]],
    keypoints: dict[str, Tensor],
    descriptors: dict[str, Tensor],
    sizes: dict[str, tuple[int, int]],
    batch_size: int,
    device: str,
):
    num_batches = (len(pairs) + batch_size - 1) // batch_size
    match_indices: dict[tuple[str, str], tuple[NDArray[intp], NDArray[intp]]] = {}
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
            batch_matches = matches[i, :image_a_num_keypoints].cpu().numpy().astype(int32)

            # Mask out non-matches (-1)
            mask = batch_matches >= 0
            image_a_keypoint_indices = nonzero(mask)[0]
            image_b_keypoint_indices = batch_matches[mask]
            match_indices[(image_a, image_b)] = (image_a_keypoint_indices, image_b_keypoint_indices)

    return match_indices
