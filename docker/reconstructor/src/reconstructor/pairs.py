from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from itertools import combinations
from pathlib import Path

import torch
from numpy import float32, where
from numpy.linalg import norm
from numpy.typing import NDArray  # noqa: TID251 — Phase T piece 3 follow-up migration
from torch import from_numpy, topk  # type: ignore

from .rig import Rig

PAIRS_FILE = "pairs.txt"
PAIRS_WITH_SOURCE_FILE = "pairs_with_source.csv"


class PairSource(str, Enum):
    INTRA_FRAME_STEREO = "intra_frame_stereo"
    SEQUENTIAL = "sequential"
    RETRIEVAL = "retrieval"


@dataclass(frozen=True)
class Pair:
    image_a: str
    image_b: str
    source: PairSource


SOURCE_PRECEDENCE: tuple[PairSource, ...] = (
    PairSource.INTRA_FRAME_STEREO,
    PairSource.SEQUENTIAL,
    PairSource.RETRIEVAL,
)


def generate_image_pairs(
    rigs: dict[str, Rig],
    global_descriptors: dict[str, NDArray[float32]],
    sequential_window_m: float,
    retrieval_neighbors: int,
    retrieval_min_score: float,
) -> list[Pair]:

    intra_frame_image_pairs = [
        (
            f"{rig_id}/{camera_a[0].id}/{frame_id}.jpg",
            f"{rig_id}/{camera_b[0].id}/{frame_id}.jpg",
        )
        for rig_id, rig in rigs.items()
        for frame_id in rig.frame_poses.keys()
        for camera_a, camera_b in combinations(rig.cameras.values(), 2)
    ]

    sequential_frame_pairs: list[tuple[tuple[str, str], tuple[str, str]]] = []
    for rig_id, rig in rigs.items():
        frame_ids = sorted(rig.frame_poses.keys(), key=int)
        translations = [rig.frame_poses[frame_id].translation for frame_id in frame_ids]
        for i in range(len(frame_ids)):
            cumulative_distance = 0.0
            for j in range(i + 1, len(frame_ids)):
                cumulative_distance += float(norm(translations[j] - translations[j - 1]))
                if cumulative_distance > sequential_window_m:
                    break
                sequential_frame_pairs.append(((rig_id, frame_ids[i]), (rig_id, frame_ids[j])))

    sequential_image_pairs = [
        (
            f"{rig_id_a}/{camera_a[0].id}/{frame_id_a}.jpg",
            f"{rig_id_b}/{camera_b[0].id}/{frame_id_b}.jpg",
        )
        for (rig_id_a, frame_id_a), (rig_id_b, frame_id_b) in sequential_frame_pairs
        for camera_a in rigs[rig_id_a].cameras.values()
        for camera_b in rigs[rig_id_b].cameras.values()
    ]

    retrieval_image_pairs: list[tuple[str, str]] = []
    if retrieval_neighbors > 0 and global_descriptors:
        image_names = list(global_descriptors.keys())
        pooled = torch.stack([from_numpy(global_descriptors[name].max(axis=0)) for name in image_names])
        image_descriptors = torch.nn.functional.normalize(pooled, dim=1)
        similarity = image_descriptors @ image_descriptors.t()

        scores = similarity.masked_fill(similarity < retrieval_min_score, float("-inf"))
        scores = scores.masked_fill(torch.eye(len(image_names), dtype=torch.bool, device=scores.device), float("-inf"))

        top_k = topk(scores, min(retrieval_neighbors, len(image_names)), dim=1)
        retrieval_indices = top_k.indices.cpu().numpy()
        retrieval_valid = top_k.values.isfinite().cpu().numpy()
        retrieval_image_pairs = [
            (image_names[int(i)], image_names[int(retrieval_indices[i, j])]) for i, j in zip(*where(retrieval_valid))
        ]

    # Canonicalize pair ordering, and deduplicate across sources
    seen: dict[tuple[str, str], PairSource] = {}
    for source, candidate_pairs in [
        (PairSource.INTRA_FRAME_STEREO, intra_frame_image_pairs),
        (PairSource.SEQUENTIAL, sequential_image_pairs),
        (PairSource.RETRIEVAL, retrieval_image_pairs),
    ]:
        for a, b in candidate_pairs:
            if a == b:
                continue
            normalized = (a, b) if a <= b else (b, a)
            if normalized in seen:
                continue
            seen[normalized] = source

    return [Pair(image_a=a, image_b=b, source=source) for (a, b), source in sorted(seen.items())]


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
