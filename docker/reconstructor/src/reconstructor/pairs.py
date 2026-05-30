from __future__ import annotations

from itertools import combinations
from pathlib import Path

import torch
from numpy import float32, float64, stack, where
from numpy.linalg import norm
from numpy.typing import NDArray  # noqa: TID251 — Phase T piece 3 follow-up migration
from torch import from_numpy, topk  # type: ignore

from .rig import Rig

PAIRS_FILE = "pairs.txt"


def generate_image_pairs(
    rigs: dict[str, Rig],
    global_descriptors: dict[str, NDArray[float32]],
    sequential_window: int,
    retrieval_neighbors: int,
    retrieval_min_distance_m: float,
    retrieval_min_score: float,
) -> list[tuple[str, str]]:
    sequential_frame_pairs: list[tuple[tuple[str, str], tuple[str, str]]] = []
    for rig_id, rig in rigs.items():
        frame_ids = sorted(rig.frame_poses.keys(), key=int)
        for i in range(len(frame_ids)):
            for j in range(i + 1, min(i + 1 + sequential_window, len(frame_ids))):
                sequential_frame_pairs.append(((rig_id, frame_ids[i]), (rig_id, frame_ids[j])))

    cross_frame_image_pairs = [
        (
            f"{rig_id_a}/{camera_a[0].id}/{frame_id_a}.jpg",
            f"{rig_id_b}/{camera_b[0].id}/{frame_id_b}.jpg",
        )
        for (rig_id_a, frame_id_a), (rig_id_b, frame_id_b) in sequential_frame_pairs
        for camera_a in rigs[rig_id_a].cameras.values()
        for camera_b in rigs[rig_id_b].cameras.values()
    ]

    intra_frame_image_pairs = [
        (
            f"{rig_id}/{camera_a[0].id}/{frame_id}.jpg",
            f"{rig_id}/{camera_b[0].id}/{frame_id}.jpg",
        )
        for rig_id, rig in rigs.items()
        for frame_id in rig.frame_poses.keys()
        for camera_a, camera_b in combinations(rig.cameras.values(), 2)
    ]

    retrieval_image_pairs: list[tuple[str, str]] = []
    if retrieval_neighbors > 0 and global_descriptors:
        image_names = list(global_descriptors.keys())
        pooled = torch.stack([from_numpy(global_descriptors[name].max(axis=0)) for name in image_names])
        image_descriptors = torch.nn.functional.normalize(pooled, dim=1)
        similarity = image_descriptors @ image_descriptors.t()

        image_positions = stack([
            rigs[name.split("/", 2)[0]].frame_poses[name.split("/", 2)[2].rsplit(".", 1)[0]].translation
            for name in image_names
        ]).astype(float64, copy=False)
        image_distances = norm(image_positions[:, None, :] - image_positions[None, :, :], axis=-1)
        too_close = from_numpy(image_distances < retrieval_min_distance_m).to(similarity.device)

        # Drop retrieval matches the VIO prior places closer than retrieval_min_distance_m —
        # sequential and spatial pairing already cover those.
        scores = similarity.masked_fill(too_close, float("-inf"))
        scores = scores.masked_fill(scores < retrieval_min_score, float("-inf"))
        scores = scores.masked_fill(torch.eye(len(image_names), dtype=torch.bool, device=scores.device), float("-inf"))

        top_k = topk(scores, min(retrieval_neighbors, len(image_names)), dim=1)
        retrieval_indices = top_k.indices.cpu().numpy()
        retrieval_valid = top_k.values.isfinite().cpu().numpy()
        retrieval_image_pairs = [
            (image_names[int(i)], image_names[int(retrieval_indices[i, j])]) for i, j in zip(*where(retrieval_valid))
        ]

    return sorted({
        (a, b) if a <= b else (b, a)
        for a, b in cross_frame_image_pairs + intra_frame_image_pairs + retrieval_image_pairs
        if a != b
    })


def write_pairs(pairs: list[tuple[str, ...]], root_path: Path):
    path = root_path / PAIRS_FILE
    path.write_text("\n".join([" ".join(pair) for pair in pairs]))
    return PAIRS_FILE, path.read_bytes()
