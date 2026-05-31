from __future__ import annotations

from enum import Enum
from itertools import combinations
from pathlib import Path

import torch
from numpy import arange, argsort, float32, float64, stack, where
from numpy.linalg import norm
from numpy.typing import NDArray  # noqa: TID251 — Phase T piece 3 follow-up migration
from torch import from_numpy, topk  # type: ignore

from .rig import Rig

PAIRS_FILE = "pairs.txt"


class PairSource(str, Enum):
    INTRA_FRAME_STEREO = "intra_frame_stereo"
    SEQUENTIAL = "sequential"
    SPATIAL = "spatial"
    RETRIEVAL = "retrieval"


# Precedence: the most-trusted source wins when a pair would be claimed by several. Intra-frame
# stereo (same-frame, different sensor) is the strongest geometric constraint we have; sequential
# is next-strongest (small VIO step between adjacent keyframes); spatial third; retrieval last
# because visual similarity is the weakest spatial cue. A pair landing under a stronger source
# inherits its (more permissive) verification threshold profile downstream.
SOURCE_PRECEDENCE: tuple[PairSource, ...] = (
    PairSource.INTRA_FRAME_STEREO,
    PairSource.SEQUENTIAL,
    PairSource.SPATIAL,
    PairSource.RETRIEVAL,
)


def generate_image_pairs(
    rigs: dict[str, Rig],
    global_descriptors: dict[str, NDArray[float32]],
    sequential_window: int,
    spatial_neighbors: int,
    spatial_max_distance_m: float,
    retrieval_neighbors: int,
    retrieval_min_distance_m: float,
    retrieval_min_score: float,
) -> dict[PairSource, list[tuple[str, str]]]:
    sequential_frame_pairs: list[tuple[tuple[str, str], tuple[str, str]]] = []
    for rig_id, rig in rigs.items():
        frame_ids = sorted(rig.frame_poses.keys(), key=int)
        for i in range(len(frame_ids)):
            for j in range(i + 1, min(i + 1 + sequential_window, len(frame_ids))):
                sequential_frame_pairs.append(((rig_id, frame_ids[i]), (rig_id, frame_ids[j])))

    spatial_frame_pairs: list[tuple[tuple[str, str], tuple[str, str]]] = []
    if spatial_neighbors > 0:
        for rig_id, rig in rigs.items():
            frame_ids_with_translation: list[str] = []
            translations: list[NDArray[float64]] = []
            for frame_id in sorted(rig.frame_poses.keys(), key=int):
                translation = rig.frame_poses[frame_id].translation
                if translation is None:
                    continue
                frame_ids_with_translation.append(frame_id)
                translations.append(translation)
            if not frame_ids_with_translation:
                continue
            positions = stack(translations).astype(float64, copy=False)
            distances = norm(positions[:, None, :] - positions[None, :, :], axis=-1)
            for i, frame_id_a in enumerate(frame_ids_with_translation):
                in_range = where(
                    (distances[i] <= spatial_max_distance_m) & (arange(len(frame_ids_with_translation)) != i)
                )[0]
                if len(in_range) > spatial_neighbors:
                    in_range = in_range[argsort(distances[i, in_range])[:spatial_neighbors]]
                for j in in_range:
                    spatial_frame_pairs.append(((rig_id, frame_id_a), (rig_id, frame_ids_with_translation[int(j)])))

    sequential_image_pairs = [
        (
            f"{rig_id_a}/{camera_a[0].id}/{frame_id_a}.jpg",
            f"{rig_id_b}/{camera_b[0].id}/{frame_id_b}.jpg",
        )
        for (rig_id_a, frame_id_a), (rig_id_b, frame_id_b) in sequential_frame_pairs
        for camera_a in rigs[rig_id_a].cameras.values()
        for camera_b in rigs[rig_id_b].cameras.values()
    ]

    spatial_image_pairs = [
        (
            f"{rig_id_a}/{camera_a[0].id}/{frame_id_a}.jpg",
            f"{rig_id_b}/{camera_b[0].id}/{frame_id_b}.jpg",
        )
        for (rig_id_a, frame_id_a), (rig_id_b, frame_id_b) in spatial_frame_pairs
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

        # Drop retrieval matches the VIO prior places closer than retrieval_min_distance_m — the
        # spatial and sequential sources already cover those. Skipped when positions are absent.
        image_positions_list: list[NDArray[float64]] = []
        for name in image_names:
            translation = rigs[name.split("/", 2)[0]].frame_poses[name.split("/", 2)[2].rsplit(".", 1)[0]].translation
            if translation is None:
                image_positions_list = []
                break
            image_positions_list.append(translation)
        if image_positions_list:
            image_positions = stack(image_positions_list).astype(float64, copy=False)
            image_distances = norm(image_positions[:, None, :] - image_positions[None, :, :], axis=-1)
            too_close = from_numpy(image_distances < retrieval_min_distance_m).to(similarity.device)
            scores = similarity.masked_fill(too_close, float("-inf"))
        else:
            scores = similarity
        scores = scores.masked_fill(scores < retrieval_min_score, float("-inf"))
        scores = scores.masked_fill(torch.eye(len(image_names), dtype=torch.bool, device=scores.device), float("-inf"))

        top_k = topk(scores, min(retrieval_neighbors, len(image_names)), dim=1)
        retrieval_indices = top_k.indices.cpu().numpy()
        retrieval_valid = top_k.values.isfinite().cpu().numpy()
        retrieval_image_pairs = [
            (image_names[int(i)], image_names[int(retrieval_indices[i, j])]) for i, j in zip(*where(retrieval_valid))
        ]

    pairs_by_source: dict[PairSource, list[tuple[str, str]]] = {source: [] for source in PairSource}
    seen: dict[tuple[str, str], PairSource] = {}
    for source, candidate_pairs in [
        (PairSource.INTRA_FRAME_STEREO, intra_frame_image_pairs),
        (PairSource.SEQUENTIAL, sequential_image_pairs),
        (PairSource.SPATIAL, spatial_image_pairs),
        (PairSource.RETRIEVAL, retrieval_image_pairs),
    ]:
        for a, b in candidate_pairs:
            if a == b:
                continue
            normalized = (a, b) if a <= b else (b, a)
            if normalized in seen:
                continue
            seen[normalized] = source
            pairs_by_source[source].append(normalized)

    for source_pairs in pairs_by_source.values():
        source_pairs.sort()

    return pairs_by_source


def flatten_pairs(pairs_by_source: dict[PairSource, list[tuple[str, str]]]) -> list[tuple[str, str]]:
    return sorted(pair for pairs in pairs_by_source.values() for pair in pairs)


def write_pairs(pairs: list[tuple[str, ...]], root_path: Path):
    path = root_path / PAIRS_FILE
    path.write_text("\n".join([" ".join(pair) for pair in pairs]))
    return PAIRS_FILE, path.read_bytes()
