from __future__ import annotations

import csv
import re
from itertools import pairwise
from pathlib import Path
from typing import Annotated, NamedTuple

import numpy as np
import typer
from numpy.typing import NDArray  # noqa: TID251 — Phase T piece 3 follow-up migration
from scipy.spatial.transform import Rotation


IMAGE_LINE_PATTERN = re.compile(r"^(\d+)\s+\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+(\S+)$")
IMAGE_NAME_PATTERN = re.compile(r"^[^/]+/[^/]+/(\d+)\.jpg$")
TELEPORT_SPEED_THRESHOLD_M_PER_S = 2.5
DEFAULT_SEQUENTIAL_WINDOW = 20

app = typer.Typer(add_completion=False, no_args_is_help=True)


class FrameRecord(NamedTuple):
    rig_id: str
    timestamp: int
    world_from_rig_center: NDArray[np.float64]
    image_ids: list[int]


class TrackExtentSummary(NamedTuple):
    total_classified_tracks: int
    long_range_track_count: int
    single_rig_long_range_count: int
    cross_rig_track_count: int
    p95_track_extent: float
    median_track_extent: float
    max_track_extent: float


@app.command()
def displacement_check(
    sfm_directory: Annotated[
        Path,
        typer.Argument(
            help="Directory containing COLMAP images.txt, frames.txt, and optionally points3D.txt (the directory MinIO stores as <reconstruction_id>/sfm_model/)."
        ),
    ],
    frames_csv: Annotated[
        Path,
        typer.Argument(
            help="Per-rig frames.csv with VIO position priors (timestamp_ms, x, y, z, qw, qx, qy, qz, ...). Used as the ground-truth-ish comparison for flagged pairs."
        ),
    ],
    sequential_window: Annotated[
        int,
        typer.Option(
            help="The reconstruction's sequential_window option. Single-rig tracks with temporal extent above 2× this threshold cannot exist from sequential matching alone and are counted as loop-closure evidence."
        ),
    ] = DEFAULT_SEQUENTIAL_WINDOW,
) -> None:
    image_id_to_timestamp = parse_image_id_to_timestamp(sfm_directory / "images.txt")
    rig_centers = parse_rig_centers(sfm_directory / "frames.txt", image_id_to_timestamp)
    prior_centers = parse_prior_centers(frames_csv)
    report_displacement(rig_centers, prior_centers)

    points3d_txt = sfm_directory / "points3D.txt"
    if not points3d_txt.exists():
        print(f"\npoints3D.txt not found at {points3d_txt}; skipping track-extent report")
        return
    image_id_to_rig_temporal_index = parse_image_id_to_rig_temporal_index(
        sfm_directory / "frames.txt", image_id_to_timestamp
    )
    track_summary = summarize_track_extents(points3d_txt, image_id_to_rig_temporal_index, sequential_window)
    report_track_extents(track_summary, sequential_window)


def parse_image_id_to_timestamp(images_txt: Path) -> dict[int, int]:
    mapping: dict[int, int] = {}
    with images_txt.open() as fh:
        for raw_line in fh:
            line = raw_line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            line_match = IMAGE_LINE_PATTERN.match(line)
            if not line_match:
                continue
            name_match = IMAGE_NAME_PATTERN.match(line_match.group(2))
            if not name_match:
                continue
            mapping[int(line_match.group(1))] = int(name_match.group(1))
    return mapping


def parse_rig_centers(
    frames_txt: Path,
    image_id_to_timestamp: dict[int, int],
) -> dict[tuple[str, int], NDArray[np.float64]]:
    return {
        (record.rig_id, record.timestamp): record.world_from_rig_center
        for record in parse_frames(frames_txt, image_id_to_timestamp)
    }


def parse_prior_centers(frames_csv: Path) -> dict[int, NDArray[np.float64]]:
    priors: dict[int, NDArray[np.float64]] = {}
    with frames_csv.open() as fh:
        reader = csv.reader(fh)
        next(reader)
        for row in reader:
            priors[int(row[0])] = np.array([float(row[1]), float(row[2]), float(row[3])])
    return priors


def report_displacement(
    rig_centers: dict[tuple[str, int], NDArray[np.float64]],
    prior_centers: dict[int, NDArray[np.float64]],
) -> None:
    rigs = sorted({rig_id for rig_id, _ in rig_centers})
    for rig_id in rigs:
        rig_timestamps = sorted(timestamp for (other_rig_id, timestamp) in rig_centers if other_rig_id == rig_id)
        pairs = list(pairwise(rig_timestamps))

        if not pairs:
            print(f"rig {rig_id}: no consecutive frames registered, nothing to check")
            continue

        rows: list[tuple[int, int, float, float, float]] = []
        for previous_ts, current_ts in pairs:
            recon_distance = float(
                np.linalg.norm(rig_centers[(rig_id, current_ts)] - rig_centers[(rig_id, previous_ts)])
            )
            delta_seconds = (current_ts - previous_ts) / 1000.0
            speed = recon_distance / delta_seconds if delta_seconds > 0 else float("inf")
            rows.append((previous_ts, current_ts, delta_seconds, recon_distance, speed))

        speeds = np.array([row[4] for row in rows])
        distances = np.array([row[3] for row in rows])
        deltas = np.array([row[2] for row in rows])

        prefix = f"rig {rig_id}: " if len(rigs) > 1 else ""
        print(f"{prefix}keyframe pairs:              {len(rows)}")
        print(f"{prefix}median Δt between keyframes: {np.median(deltas):.2f} s")
        print(f"{prefix}max distance / pair:         {distances.max():.2f} m")
        print(f"{prefix}p99 distance / pair:         {np.percentile(distances, 99):.2f} m")
        print(f"{prefix}p95 distance / pair:         {np.percentile(distances, 95):.2f} m")
        print(f"{prefix}median distance / pair:      {np.median(distances):.2f} m")
        print(f"{prefix}max speed:                   {speeds.max():.2f} m/s")
        print(f"{prefix}p99 speed:                   {np.percentile(speeds, 99):.2f} m/s")
        print(f"{prefix}p95 speed:                   {np.percentile(speeds, 95):.2f} m/s")
        print(f"{prefix}median speed:                {np.median(speeds):.2f} m/s")

        teleports = [row for row in rows if row[4] > TELEPORT_SPEED_THRESHOLD_M_PER_S]
        print(f"{prefix}keyframe pairs > {TELEPORT_SPEED_THRESHOLD_M_PER_S} m/s:    {len(teleports)} of {len(rows)}")
        if teleports:
            print(f"{prefix}  top 5 by speed:")
            for previous_ts, current_ts, delta_seconds, distance, speed in sorted(teleports, key=lambda row: -row[4])[
                :5
            ]:
                prior_distance = (
                    float(np.linalg.norm(prior_centers[current_ts] - prior_centers[previous_ts]))
                    if previous_ts in prior_centers and current_ts in prior_centers
                    else float("nan")
                )
                print(
                    f"{prefix}    {previous_ts} → {current_ts}  Δt={delta_seconds:.2f}s  "
                    f"recon={distance:.2f}m  prior={prior_distance:.2f}m  speed={speed:.2f} m/s"
                )


def parse_image_id_to_rig_temporal_index(
    frames_txt: Path,
    image_id_to_timestamp: dict[int, int],
) -> dict[int, tuple[str, int]]:
    records = parse_frames(frames_txt, image_id_to_timestamp)
    rig_to_timestamps: dict[str, set[int]] = {}
    for record in records:
        rig_to_timestamps.setdefault(record.rig_id, set()).add(record.timestamp)
    rig_timestamp_to_index = {
        rig_id: {timestamp: index for index, timestamp in enumerate(sorted(timestamps))}
        for rig_id, timestamps in rig_to_timestamps.items()
    }
    result: dict[int, tuple[str, int]] = {}
    for record in records:
        index = rig_timestamp_to_index[record.rig_id][record.timestamp]
        for image_id in record.image_ids:
            result[image_id] = (record.rig_id, index)
    return result


def summarize_track_extents(
    points3d_txt: Path,
    image_id_to_rig_temporal_index: dict[int, tuple[str, int]],
    sequential_window: int,
) -> TrackExtentSummary:
    long_range_threshold = 2 * sequential_window
    extents: list[int] = []
    cross_rig_count = 0
    single_rig_long_range = 0
    with points3d_txt.open() as fh:
        for raw_line in fh:
            line = raw_line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            fields = line.split()
            track_fields = fields[8:]
            if len(track_fields) % 2 != 0:
                continue
            per_rig_indices: dict[str, list[int]] = {}
            for offset in range(0, len(track_fields), 2):
                image_id = int(track_fields[offset])
                position = image_id_to_rig_temporal_index.get(image_id)
                if position is None:
                    continue
                rig_id, index = position
                per_rig_indices.setdefault(rig_id, []).append(index)
            if not per_rig_indices:
                continue
            if len(per_rig_indices) > 1:
                cross_rig_count += 1
                continue
            indices = next(iter(per_rig_indices.values()))
            extent = max(indices) - min(indices)
            extents.append(extent)
            if extent > long_range_threshold:
                single_rig_long_range += 1
    return TrackExtentSummary(
        total_classified_tracks=len(extents) + cross_rig_count,
        long_range_track_count=single_rig_long_range + cross_rig_count,
        single_rig_long_range_count=single_rig_long_range,
        cross_rig_track_count=cross_rig_count,
        p95_track_extent=float(np.percentile(extents, 95)) if extents else float("nan"),
        median_track_extent=float(np.median(extents)) if extents else float("nan"),
        max_track_extent=float(max(extents)) if extents else float("nan"),
    )


def report_track_extents(summary: TrackExtentSummary, sequential_window: int) -> None:
    long_range_threshold = 2 * sequential_window
    print()
    print(f"track extents (long-range threshold = 2 × sequential_window = {long_range_threshold}):")
    print(f"  total classified tracks:    {summary.total_classified_tracks}")
    print(f"  long-range tracks:          {summary.long_range_track_count}")
    print(f"    single-rig (> threshold):   {summary.single_rig_long_range_count}")
    print(f"    cross-rig:                  {summary.cross_rig_track_count}")
    print(f"  p95 single-rig extent:      {summary.p95_track_extent:.1f}")
    print(f"  median single-rig extent:   {summary.median_track_extent:.1f}")
    print(f"  max single-rig extent:      {summary.max_track_extent:.1f}")


def parse_frames(
    frames_txt: Path,
    image_id_to_timestamp: dict[int, int],
) -> list[FrameRecord]:
    records: list[FrameRecord] = []
    with frames_txt.open() as fh:
        for raw_line in fh:
            line = raw_line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            fields = line.split()
            rig_id = fields[1]
            qw, qx, qy, qz = (float(field) for field in fields[2:6])
            tx, ty, tz = (float(field) for field in fields[6:9])
            num_data = int(fields[9])
            data_section = fields[10 : 10 + num_data * 3]
            image_ids = [int(data_section[index * 3 + 2]) for index in range(num_data)]
            timestamps = {
                image_id_to_timestamp[image_id] for image_id in image_ids if image_id in image_id_to_timestamp
            }
            if len(timestamps) != 1:
                continue
            timestamp = next(iter(timestamps))
            rotation_matrix = Rotation.from_quat([qx, qy, qz, qw]).as_matrix()
            world_from_rig_translation = -rotation_matrix.T @ np.array([tx, ty, tz])
            records.append(FrameRecord(rig_id, timestamp, world_from_rig_translation, image_ids))
    return records


if __name__ == "__main__":
    app()
