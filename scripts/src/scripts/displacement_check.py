from __future__ import annotations

import csv
import re
from itertools import pairwise
from pathlib import Path
from typing import Annotated

import numpy as np
import typer
from numpy.typing import NDArray  # noqa: TID251 — Phase T piece 3 follow-up migration
from scipy.spatial.transform import Rotation


IMAGE_LINE_PATTERN = re.compile(r"^(\d+)\s+\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+(\S+)$")
IMAGE_NAME_PATTERN = re.compile(r"^[^/]+/[^/]+/(\d+)\.jpg$")
TELEPORT_SPEED_THRESHOLD_M_PER_S = 2.5

app = typer.Typer(add_completion=False, no_args_is_help=True)


@app.command()
def displacement_check(
    sfm_directory: Annotated[
        Path,
        typer.Argument(
            help="Directory containing COLMAP images.txt and frames.txt (the directory MinIO stores as <reconstruction_id>/sfm_model/)."
        ),
    ],
    frames_csv: Annotated[
        Path,
        typer.Argument(
            help="Per-rig frames.csv with VIO position priors (timestamp_ms, x, y, z, qw, qx, qy, qz, ...). Used as the ground-truth-ish comparison for flagged pairs."
        ),
    ],
) -> None:
    image_id_to_timestamp = parse_image_id_to_timestamp(sfm_directory / "images.txt")
    rig_centers = parse_rig_centers(sfm_directory / "frames.txt", image_id_to_timestamp)
    prior_centers = parse_prior_centers(frames_csv)
    report_displacement(rig_centers, prior_centers)


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
    centers: dict[tuple[str, int], NDArray[np.float64]] = {}
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
            centers[(rig_id, timestamp)] = world_from_rig_translation
    return centers


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


if __name__ == "__main__":
    app()
