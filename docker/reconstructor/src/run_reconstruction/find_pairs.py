# type: ignore
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import numpy as np
import torch

ROTATION_THRESHOLD_DEG = 30.0


class ImageTransform:
    def __init__(self, name: str, rotation: np.ndarray, translation: np.ndarray):
        self.name = name
        self.rotation = rotation
        self.translation = translation


def pairs_from_poses(
    images: List[ImageTransform], num_neighbors: int, rotation_thresh_deg: float = ROTATION_THRESHOLD_DEG
) -> List[Tuple[str, str]]:
    """Pose‑space k‑NN with orientation gating (à la HLoc)."""

    ids = [img.name for img in images]
    R_w_c = np.stack([img.rotation for img in images], axis=0)  # (N,3,3)
    centers = np.stack([img.translation for img in images], axis=0)  # (N,3)

    # Euclidean distances of camera centres
    diff = centers[:, None, :] - centers[None, :, :]
    dists = np.linalg.norm(diff, axis=-1)

    # Principal optical axis (Z direction) in world frame
    optical_axes = R_w_c[:, :, 2]
    cosines = np.clip(optical_axes @ optical_axes.T, -1.0, 1.0)
    ang_deg = np.degrees(np.arccos(cosines))

    scores = -torch.from_numpy(dists)
    invalid = ang_deg >= rotation_thresh_deg
    np.fill_diagonal(invalid, True)

    selected = pairs_from_score_matrix(scores, invalid, num_neighbors)
    return [(ids[i], ids[j]) for i, j in selected]


def pairs_from_retrieval(
    descriptors: Dict[str, torch.Tensor], num_neighbors: int, min_score: Optional[float] = None
) -> List[Tuple[str, str]]:
    """Dot‑product similarity k‑NN for loop‑closure discovery."""

    names = list(descriptors.keys())
    tensor = torch.stack([descriptors[n] for n in names], dim=0)
    similarity = tensor @ tensor.t()  # cosine if descriptors normalised

    invalid = torch.eye(len(names), dtype=torch.bool)
    selected = pairs_from_score_matrix(similarity, invalid.numpy(), num_neighbors, min_score)
    return [(names[i], names[j]) for i, j in selected]


def pairs_from_score_matrix(
    scores: torch.Tensor, invalid: np.array, num_select: int, min_score: Optional[float] = None
):
    assert scores.shape == invalid.shape
    if isinstance(scores, np.ndarray):
        scores = torch.from_numpy(scores)
    invalid = torch.from_numpy(invalid).to(scores.device)
    if min_score is not None:
        invalid |= scores < min_score
    scores.masked_fill_(invalid, float("-inf"))

    topk = torch.topk(scores, num_select, dim=1)
    indices = topk.indices.cpu().numpy()
    valid = topk.values.isfinite().cpu().numpy()

    pairs = []
    for i, j in zip(*np.where(valid)):
        pairs.append((i, indices[i, j]))
    return pairs
