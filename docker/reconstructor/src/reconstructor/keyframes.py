from __future__ import annotations

from pathlib import Path

import cv2
from numpy import asarray, empty_like, float32, linalg, median, uint8
from numpy.typing import NDArray  # noqa: TID251 — Phase T piece 3 follow-up migration


def select_keyframes_by_parallax(
    image_paths_in_order: list[Path],
    accumulated_parallax_threshold_px: float,
    working_resolution: tuple[int, int] = (320, 240),
    minimum_tracked_corners: int = 10,
    maximum_corners_per_frame: int = 200,
) -> list[int]:
    if not image_paths_in_order:
        return []

    kept_indices: list[int] = [0]
    previous_small = _load_grayscale_resized(image_paths_in_order[0], working_resolution)
    previous_corners = _detect_corners(previous_small, maximum_corners_per_frame)
    accumulated_displacement = 0.0

    for index in range(1, len(image_paths_in_order)):
        current_small = _load_grayscale_resized(image_paths_in_order[index], working_resolution)

        if previous_corners.shape[0] < minimum_tracked_corners:
            kept_indices.append(index)
            accumulated_displacement = 0.0
            previous_small = current_small
            previous_corners = _detect_corners(current_small, maximum_corners_per_frame)
            continue

        tracked_raw, status, _ = cv2.calcOpticalFlowPyrLK(
            previous_small, current_small, previous_corners, empty_like(previous_corners)
        )
        tracked = asarray(tracked_raw, dtype=float32)
        valid_mask = asarray(status, dtype=uint8).ravel() == 1
        if int(valid_mask.sum()) < minimum_tracked_corners:
            kept_indices.append(index)
            accumulated_displacement = 0.0
        else:
            displacements = linalg.norm(tracked[valid_mask] - previous_corners[valid_mask], axis=2).reshape(-1)
            accumulated_displacement += float(median(displacements))
            if accumulated_displacement >= accumulated_parallax_threshold_px:
                kept_indices.append(index)
                accumulated_displacement = 0.0

        previous_small = current_small
        previous_corners = _detect_corners(current_small, maximum_corners_per_frame)

    return kept_indices


def _load_grayscale_resized(image_path: Path, working_resolution: tuple[int, int]) -> NDArray[uint8]:
    image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise ValueError(f"Could not load image at {image_path}")
    return asarray(cv2.resize(image, working_resolution), dtype=uint8)


def _detect_corners(image: NDArray[uint8], maximum_corners: int) -> NDArray[float32]:
    corners = cv2.goodFeaturesToTrack(image, maxCorners=maximum_corners, qualityLevel=0.01, minDistance=8)
    return asarray(corners, dtype=float32).reshape(-1, 1, 2)
