from __future__ import annotations

from itertools import combinations
from pathlib import Path
from typing import Dict, Optional

import torch
from core.rig import Transform
from numpy import arccos, clip, degrees, fill_diagonal, stack, where
from numpy.linalg import norm
from torch import from_numpy, topk  # type: ignore

from .rig import Rig

PAIRS_FILE = "pairs.txt"


def generate_image_pairs(rigs: Dict[str, Rig], neighbors_count: int, rotation_thresh_deg: float):
    proximal_frame_pairs = pairs_from_poses(
        {
            (rig_id, frame_id): transform
            for rig_id, rig in rigs.items()
            for frame_id, transform in rig.frame_poses.items()
        },
        neighbors_count,
        rotation_thresh_deg,
    )

    cross_frame_image_pairs_by_frame_proximity = [
        (f"{rig_id_a}/{camera_a[0].id}/{frame_id_a}.jpg", f"{rig_id_b}/{camera_b[0].id}/{frame_id_b}.jpg")
        for (rig_id_a, frame_id_a), (rig_id_b, frame_id_b) in proximal_frame_pairs
        for camera_a in rigs[rig_id_a].cameras.values()
        for camera_b in rigs[rig_id_b].cameras.values()
    ]

    intra_frame_image_pairs = [
        (f"{rig_id}/{camera_a[0].id}/{frame_id}.jpg", f"{rig_id}/{camera_b[0].id}/{frame_id}.jpg")
        for rig_id, rig in rigs.items()
        for frame_id in rig.frame_poses.keys()
        for camera_a, camera_b in combinations(list(rig.cameras.values()), 2)
    ]

    # Canonicalize and deduplicate
    return sorted({
        (a, b) if a <= b else (b, a)
        for a, b in cross_frame_image_pairs_by_frame_proximity + intra_frame_image_pairs
        if a != b
    })


def write_pairs(pairs: list[tuple[str, ...]], root_path: Path):
    path = root_path / PAIRS_FILE
    path.write_text("\n".join([" ".join(pair) for pair in pairs]))
    return PAIRS_FILE, path.read_bytes()


def pairs_from_poses(images: dict[tuple[str, str], Transform], num_neighbors: int, rotation_thresh_deg: float):
    names = list(images.keys())
    R_w_c = stack([images[name].rotation for name in names], axis=0)  # (N, 3, 3)
    centers = stack([images[name].translation for name in names], axis=0)  # (N, 3)

    # Euclidean distances of camera centres
    diff = centers[:, None, :] - centers[None, :, :]
    dists = norm(diff, axis=-1)

    # Principal optical axis (Z direction) in world frame
    optical_axes = R_w_c[:, :, 2]
    cosines = clip(optical_axes @ optical_axes.T, -1.0, 1.0)
    ang_deg = degrees(arccos(cosines))

    scores = -from_numpy(dists)
    invalid = ang_deg >= rotation_thresh_deg
    fill_diagonal(invalid, True)
    invalid = from_numpy(invalid).to(scores.device)  # NEW: convert mask to torch bool tensor
    selected = pairs_from_score_matrix(scores, invalid, num_neighbors)

    return [(names[i], names[j]) for i, j in selected]


def pairs_from_retrieval(descriptors: Dict[str, torch.Tensor], num_neighbors: int, min_score: Optional[float] = None):
    names = list(descriptors.keys())
    tensor = torch.stack([descriptors[n] for n in names], dim=0)
    similarity = tensor @ tensor.t()

    invalid = torch.eye(len(names), dtype=torch.bool)
    if min_score is not None:
        invalid |= similarity < min_score

    selected = pairs_from_score_matrix(similarity, invalid, num_neighbors)
    return [(names[i], names[j]) for i, j in selected]


def pairs_from_score_matrix(scores: torch.Tensor, invalid: torch.Tensor, num_select: int):
    scores.masked_fill_(invalid, float("-inf"))
    top_k = topk(scores, min(num_select, scores.size(1)), dim=1)
    indices = top_k.indices.cpu().numpy()
    valid = top_k.values.isfinite().cpu().numpy()

    return [(int(i), int(indices[i, j])) for i, j in zip(*where(valid))]
