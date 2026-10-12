from __future__ import annotations

from numpy import float64
from numpy.linalg import norm
from numpy.typing import NDArray  # noqa: TID251 — tracked in PLE-233


def select_keyframes_by_distance(
    frame_ids_in_order: list[str],
    translations_by_frame_id: dict[str, NDArray[float64]],
    min_distance_m: float,
) -> list[str]:
    if not frame_ids_in_order:
        return []
    kept: list[str] = [frame_ids_in_order[0]]
    last_kept_translation = translations_by_frame_id[frame_ids_in_order[0]]
    for frame_id in frame_ids_in_order[1:]:
        translation = translations_by_frame_id[frame_id]
        if float(norm(translation - last_kept_translation)) >= min_distance_m:
            kept.append(frame_id)
            last_kept_translation = translation
    return kept
