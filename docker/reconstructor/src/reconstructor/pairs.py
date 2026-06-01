from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from itertools import combinations
from pathlib import Path

import torch
from numpy import arange, argsort, asarray, float32, float64, stack, where
from numpy.linalg import norm
from numpy.typing import NDArray  # noqa: TID251 — Phase T piece 3 follow-up migration
from torch import from_numpy, topk  # type: ignore

from .rig import Rig

PAIRS_FILE = "pairs.txt"
PAIRS_WITH_SOURCE_FILE = "pairs_with_source.csv"


class PairSource(str, Enum):
    INTRA_FRAME_STEREO = "intra_frame_stereo"
    SEQUENTIAL = "sequential"
    SPATIAL = "spatial"
    RETRIEVAL = "retrieval"


@dataclass(frozen=True)
class Pair:
    image_a: str
    image_b: str
    source: PairSource


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
    retrieval_covisibility_window: int,
    retrieval_covisibility_min_support: int,
    pair_max_displacement_scene_m: float,
    pair_max_displacement_drift_rate_m_per_s: float,
) -> list[Pair]:
    sequential_frame_pairs: list[tuple[tuple[str, str], tuple[str, str]]] = []
    for rig_id, rig in rigs.items():
        frame_ids = sorted(rig.frame_poses.keys(), key=int)
        for i in range(len(frame_ids)):
            for j in range(i + 1, min(i + 1 + sequential_window, len(frame_ids))):
                sequential_frame_pairs.append(((rig_id, frame_ids[i]), (rig_id, frame_ids[j])))

    spatial_frame_pairs: list[tuple[tuple[str, str], tuple[str, str]]] = []
    if spatial_neighbors > 0:
        for rig_id, rig in rigs.items():
            ordered_frame_ids = sorted(rig.frame_poses.keys(), key=int)
            frame_id_to_temporal_index = {frame_id: index for index, frame_id in enumerate(ordered_frame_ids)}
            frame_ids_with_translation: list[str] = []
            translations: list[NDArray[float64]] = []
            for frame_id in ordered_frame_ids:
                translation = rig.frame_poses[frame_id].translation
                if translation is None:
                    continue
                frame_ids_with_translation.append(frame_id)
                translations.append(translation)
            if not frame_ids_with_translation:
                continue
            positions = stack(translations).astype(float64, copy=False)
            distances = norm(positions[:, None, :] - positions[None, :, :], axis=-1)
            temporal_indices = asarray([
                frame_id_to_temporal_index[frame_id] for frame_id in frame_ids_with_translation
            ])
            for i, frame_id_a in enumerate(frame_ids_with_translation):
                # Spatial source is the loop-closure-by-VIO-position complement to sequential. Pairs
                # already proposed by sequential (temporal-index distance <= sequential_window) are
                # excluded here so spatial_neighbors counts loop-closure candidates, not redundancy
                # with sequential's coverage.
                in_range = where(
                    (distances[i] <= spatial_max_distance_m)
                    & (arange(len(frame_ids_with_translation)) != i)
                    & (abs(temporal_indices - temporal_indices[i]) > sequential_window)
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

    # Covisibility filter: an aliased retrieval pair (e.g. two paintings with similar composition in
    # different rooms) appears as a singleton — frame A retrieval-matches frame B but A's temporal
    # neighbours do not retrieval-match B's temporal neighbours. A true loop closure produces a band
    # because the whole stretch of trajectory re-matches when you genuinely revisit a place. For each
    # candidate frame-pair (A, B) we count supporting frame-pairs (A', B') where each endpoint is
    # within retrieval_covisibility_window keyframe steps of the corresponding original and the rigs
    # match; pairs with fewer than retrieval_covisibility_min_support supporters are dropped. Both
    # forward (A'≈A, B'≈B) and backward (A'≈B, B'≈A) orderings count, since a real revisit can
    # traverse the loop in either direction.
    # STRIPPED-TO-STUDS: retrieval covisibility filter disabled.
    # if retrieval_image_pairs and retrieval_covisibility_min_support > 0:
    #     cross_rig_temporal_index: dict[tuple[str, str], int] = {}
    #     for rig_id, rig in rigs.items():
    #         for index, frame_id in enumerate(sorted(rig.frame_poses.keys(), key=int)):
    #             cross_rig_temporal_index[(rig_id, frame_id)] = index
    #
    #     candidate_frame_pairs: set[tuple[tuple[str, str], tuple[str, str]]] = set()
    #     for image_a, image_b in retrieval_image_pairs:
    #         rig_a, _, rest_a = image_a.split("/", 2)
    #         frame_a = (rig_a, rest_a.rsplit(".", 1)[0])
    #         rig_b, _, rest_b = image_b.split("/", 2)
    #         frame_b = (rig_b, rest_b.rsplit(".", 1)[0])
    #         if frame_a == frame_b:
    #             continue
    #         canonical = (frame_a, frame_b) if frame_a <= frame_b else (frame_b, frame_a)
    #         candidate_frame_pairs.add(canonical)
    #
    #     candidate_list = list(candidate_frame_pairs)
    #     accepted_frame_pairs: set[tuple[tuple[str, str], tuple[str, str]]] = set()
    #     for i, (target_a, target_b) in enumerate(candidate_list):
    #         support = 0
    #         target_a_index = cross_rig_temporal_index[target_a]
    #         target_b_index = cross_rig_temporal_index[target_b]
    #         for j, (other_a, other_b) in enumerate(candidate_list):
    #             if i == j:
    #                 continue
    #             forward_match = (
    #                 other_a[0] == target_a[0]
    #                 and other_b[0] == target_b[0]
    #                 and abs(cross_rig_temporal_index[other_a] - target_a_index) <= retrieval_covisibility_window
    #                 and abs(cross_rig_temporal_index[other_b] - target_b_index) <= retrieval_covisibility_window
    #             )
    #             backward_match = (
    #                 other_a[0] == target_b[0]
    #                 and other_b[0] == target_a[0]
    #                 and abs(cross_rig_temporal_index[other_a] - target_b_index) <= retrieval_covisibility_window
    #                 and abs(cross_rig_temporal_index[other_b] - target_a_index) <= retrieval_covisibility_window
    #             )
    #             if forward_match or backward_match:
    #                 support += 1
    #                 if support >= retrieval_covisibility_min_support:
    #                     break
    #         if support >= retrieval_covisibility_min_support:
    #             accepted_frame_pairs.add((target_a, target_b))
    #
    #     filtered_retrieval_image_pairs: list[tuple[str, str]] = []
    #     for image_a, image_b in retrieval_image_pairs:
    #         rig_a, _, rest_a = image_a.split("/", 2)
    #         frame_a = (rig_a, rest_a.rsplit(".", 1)[0])
    #         rig_b, _, rest_b = image_b.split("/", 2)
    #         frame_b = (rig_b, rest_b.rsplit(".", 1)[0])
    #         canonical = (frame_a, frame_b) if frame_a <= frame_b else (frame_b, frame_a)
    #         if canonical in accepted_frame_pairs:
    #             filtered_retrieval_image_pairs.append((image_a, image_b))
    #     retrieval_image_pairs = filtered_retrieval_image_pairs

    image_translations: dict[str, NDArray[float64] | None] = {}
    image_timestamps_ms: dict[str, int] = {}
    for rig_id, rig in rigs.items():
        for frame_id, frame_pose in rig.frame_poses.items():
            timestamp_ms = int(frame_id)
            for camera_a, _ in rig.cameras.values():
                name = f"{rig_id}/{camera_a.id}/{frame_id}.jpg"
                image_translations[name] = frame_pose.translation
                image_timestamps_ms[name] = timestamp_ms

    rejected_by_source: dict[PairSource, int] = dict.fromkeys(SOURCE_PRECEDENCE, 0)
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
            if not _pair_passes_drift_budget(
                normalized[0],
                normalized[1],
                image_translations,
                image_timestamps_ms,
                pair_max_displacement_scene_m,
                pair_max_displacement_drift_rate_m_per_s,
            ):
                rejected_by_source[source] += 1
                continue
            seen[normalized] = source

    print(
        "Drift-budget filter rejections: "
        + ", ".join(f"{source.value}={count}" for source, count in rejected_by_source.items())
    )

    return [Pair(image_a=a, image_b=b, source=source) for (a, b), source in sorted(seen.items())]


def _pair_passes_drift_budget(
    image_a: str,
    image_b: str,
    image_translations: dict[str, NDArray[float64] | None],
    image_timestamps_ms: dict[str, int],
    pair_max_displacement_scene_m: float,
    pair_max_displacement_drift_rate_m_per_s: float,
) -> bool:
    # Bound = room-scale floor + per-second VIO drift budget. The drift budget lets
    # long-temporal-gap true loop closures survive accumulated drift in absolute VIO positions;
    # the floor still rejects short-temporal-gap visually-similar pairs across physically distant
    # parts of the scene. Skips silently when either frame lacks a VIO position, mirroring
    # retrieval_min_distance_m.
    translation_a = image_translations[image_a]
    translation_b = image_translations[image_b]
    if translation_a is None or translation_b is None:
        return True
    delta_seconds = abs(image_timestamps_ms[image_a] - image_timestamps_ms[image_b]) / 1000.0
    max_displacement = pair_max_displacement_scene_m + pair_max_displacement_drift_rate_m_per_s * delta_seconds
    return bool(norm(translation_b - translation_a) <= max_displacement)


def write_pairs(pairs: list[Pair], root_path: Path) -> tuple[str, bytes]:
    path = root_path / PAIRS_FILE
    path.write_text("\n".join(f"{pair.image_a} {pair.image_b}" for pair in pairs))
    return PAIRS_FILE, path.read_bytes()


def write_pairs_with_source(pairs: list[Pair], root_path: Path) -> tuple[str, bytes]:
    pairs_by_source: dict[PairSource, list[Pair]] = {source: [] for source in SOURCE_PRECEDENCE}
    for pair in pairs:
        pairs_by_source[pair.source].append(pair)
    lines = ["image_a,image_b,source"]
    for source in SOURCE_PRECEDENCE:
        for pair in pairs_by_source[source]:
            lines.append(f"{pair.image_a},{pair.image_b},{source.value}")
    path = root_path / PAIRS_WITH_SOURCE_FILE
    path.write_text("\n".join(lines) + "\n")
    return PAIRS_WITH_SOURCE_FILE, path.read_bytes()
