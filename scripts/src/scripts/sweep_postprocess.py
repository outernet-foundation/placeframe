from __future__ import annotations

import csv
import json
from itertools import pairwise
from pathlib import Path
from typing import Annotated, NamedTuple, NotRequired, TypedDict
from uuid import UUID

import numpy as np
import typer
from common.bash import bash, bash_output

from .displacement_check import (
    DEFAULT_SEQUENTIAL_WINDOW,
    TELEPORT_SPEED_THRESHOLD_M_PER_S,
    parse_image_id_to_rig_temporal_index,
    parse_image_id_to_timestamp,
    parse_prior_centers,
    parse_rig_centers,
    summarize_track_extents,
)


RESULT_FIELD_NAMES = [
    "reconstruction_id",
    "retrieval_label",
    "vio_em_label",
    "replicate",
    "retrieval_neighbors",
    "vio_em_rotation_deg",
    "status",
    "created_at",
    "pair_count",
    "max_speed",
    "max_distance",
    "p95_speed",
    "median_speed",
    "bad_pair_count",
    "total_classified_tracks",
    "long_range_track_count",
    "cross_rig_track_count",
    "p95_track_extent",
    "median_track_extent",
    "max_track_extent",
]


class ReconstructionRecord(NamedTuple):
    reconstruction_id: UUID
    status: str
    created_at: str
    retrieval_neighbors: int
    vio_em_rotation_deg: float


class ClassifiedReconstruction(NamedTuple):
    record: ReconstructionRecord
    retrieval_label: str
    vio_em_label: str
    replicate: int


class DisplacementSummary(NamedTuple):
    pair_count: int
    max_speed: float
    max_distance: float
    p95_speed: float
    median_speed: float
    bad_pair_count: int
    worst_pair: dict[str, float | int] | None


class EnrichedRow(TypedDict):
    reconstruction_id: str
    retrieval_label: str
    vio_em_label: str
    replicate: int
    retrieval_neighbors: int
    vio_em_rotation_deg: float
    status: str
    created_at: str
    pair_count: NotRequired[int]
    max_speed: NotRequired[float]
    max_distance: NotRequired[float]
    p95_speed: NotRequired[float]
    median_speed: NotRequired[float]
    bad_pair_count: NotRequired[int]
    worst_pair: NotRequired[dict[str, float | int] | None]
    total_classified_tracks: NotRequired[int]
    long_range_track_count: NotRequired[int]
    cross_rig_track_count: NotRequired[int]
    p95_track_extent: NotRequired[float]
    median_track_extent: NotRequired[float]
    max_track_extent: NotRequired[float]


app = typer.Typer(add_completion=False, no_args_is_help=True)


@app.command()
def sweep_postprocess(
    capture_id: Annotated[
        UUID, typer.Argument(help="Capture session whose reconstructions form the sweep to analyze.")
    ],
    output_dir: Annotated[
        Path,
        typer.Option(help="Output root. Per-capture results land under <output_dir>/<capture_id>/."),
    ] = Path("sweep-output"),
    sequential_window: Annotated[
        int,
        typer.Option(
            help="Frame-count window passed to the track-extent metric; long-range threshold is 2× this. Independent of reconstruction sequential_window_m (which is a metric path distance, not a frame count)."
        ),
    ] = DEFAULT_SEQUENTIAL_WINDOW,
) -> None:
    capture_output_dir = output_dir / str(capture_id)
    capture_output_dir.mkdir(parents=True, exist_ok=True)

    records = fetch_reconstructions(capture_id)
    print(f"found {len(records)} reconstructions for capture {capture_id}")

    classified = classify_into_cells(records)
    print(f"classified {len(classified)} reconstructions into sweep cells")

    persist_mapping(classified, capture_output_dir / "mapping.json")

    capture_dir = ensure_capture_extracted(capture_id, capture_output_dir)
    frames_csv = capture_dir / "rig0" / "frames.csv"

    enriched = analyze_all(classified, capture_output_dir, frames_csv, sequential_window)
    write_results(enriched, capture_output_dir)
    print_summary(enriched, capture_output_dir / "summary.txt")


def fetch_reconstructions(capture_id: UUID) -> list[ReconstructionRecord]:
    sql = (
        "SELECT id, status, created_at::text, "
        "manifest->'options'->>'retrieval_neighbors', "
        "manifest->'options'->>'pair_vio_em_max_rotation_disagreement_deg' "
        "FROM reconstructions WHERE capture_session_id=:'capture_id' "
        "ORDER BY created_at;"
    )
    raw = bash_output(
        f"docker exec placeframe-postgres-1 psql -U postgres -d placeframe -t -A -F'|' "
        f'-v capture_id={capture_id} -c "{sql}"'
    )
    records: list[ReconstructionRecord] = []
    for line in raw.strip().split("\n"):
        if not line:
            continue
        fields = line.split("|")
        if len(fields) != 5:
            continue
        if not fields[3] or not fields[4]:
            continue
        records.append(
            ReconstructionRecord(
                reconstruction_id=UUID(fields[0]),
                status=fields[1],
                created_at=fields[2],
                retrieval_neighbors=int(fields[3]),
                vio_em_rotation_deg=float(fields[4]),
            )
        )
    return records


def classify_into_cells(records: list[ReconstructionRecord]) -> list[ClassifiedReconstruction]:
    cell_counters: dict[tuple[str, str], int] = {}
    classified: list[ClassifiedReconstruction] = []
    for record in records:
        retrieval_label = f"R{record.retrieval_neighbors}"
        vio_em_label = "EMon" if record.vio_em_rotation_deg > 0 else "EMoff"
        cell_key = (retrieval_label, vio_em_label)
        replicate = cell_counters.get(cell_key, 0)
        cell_counters[cell_key] = replicate + 1
        classified.append(
            ClassifiedReconstruction(
                record=record,
                retrieval_label=retrieval_label,
                vio_em_label=vio_em_label,
                replicate=replicate,
            )
        )
    return classified


def persist_mapping(classified: list[ClassifiedReconstruction], mapping_path: Path) -> None:
    payload = [
        {
            "reconstruction_id": str(c.record.reconstruction_id),
            "status": c.record.status,
            "created_at": c.record.created_at,
            "retrieval_label": c.retrieval_label,
            "vio_em_label": c.vio_em_label,
            "replicate": c.replicate,
            "retrieval_neighbors": c.record.retrieval_neighbors,
            "vio_em_rotation_deg": c.record.vio_em_rotation_deg,
        }
        for c in classified
    ]
    mapping_path.write_text(json.dumps(payload, indent=2))
    print(f"wrote {mapping_path}")


def ensure_capture_extracted(capture_id: UUID, output_dir: Path) -> Path:
    capture_dir = output_dir / "capture_extracted"
    if (capture_dir / "rig0" / "frames.csv").exists():
        return capture_dir
    capture_tar = output_dir / "capture.tar"
    if not capture_tar.exists():
        print(f"downloading capture {capture_id} from MinIO")
        bash(f"docker exec placeframe-minio-1 mc cp local/dev-captures/{capture_id}.tar /tmp/sweep_capture.tar")
        bash(f"docker cp placeframe-minio-1:/tmp/sweep_capture.tar {capture_tar}")
        bash("docker exec placeframe-minio-1 rm -f /tmp/sweep_capture.tar")
    capture_dir.mkdir(parents=True, exist_ok=True)
    bash(f"tar -xf {capture_tar} -C {capture_dir}")
    return capture_dir


def pull_sfm_artifacts(reconstruction_id: UUID, output_dir: Path) -> Path | None:
    sfm_dir = output_dir / "recons" / str(reconstruction_id) / "sfm"
    if (sfm_dir / "frames.txt").exists() and (sfm_dir / "points3D.txt").exists():
        return sfm_dir
    sfm_dir.mkdir(parents=True, exist_ok=True)
    container_tmp = f"/tmp/sweep_pull_{reconstruction_id}"
    bash(f"docker exec placeframe-minio-1 rm -rf {container_tmp}")
    bash(
        f"docker exec placeframe-minio-1 mc cp --recursive "
        f"local/dev-reconstructions/{reconstruction_id}/sfm_model/ {container_tmp}/"
    )
    bash(f"docker cp placeframe-minio-1:{container_tmp}/. {sfm_dir}")
    bash(f"docker exec placeframe-minio-1 rm -rf {container_tmp}")
    if not (sfm_dir / "frames.txt").exists():
        return None
    return sfm_dir


def analyze_all(
    classified: list[ClassifiedReconstruction],
    output_dir: Path,
    frames_csv: Path,
    sequential_window: int,
) -> list[EnrichedRow]:
    enriched: list[EnrichedRow] = []
    for index, item in enumerate(classified, start=1):
        recon_id = item.record.reconstruction_id
        label = f"{item.retrieval_label} {item.vio_em_label} rep{item.replicate}"
        print(f"[{index}/{len(classified)}] {recon_id} ({label}) status={item.record.status}")
        row = base_row(item)
        if item.record.status != "succeeded":
            enriched.append(row)
            continue
        sfm_dir = pull_sfm_artifacts(recon_id, output_dir)
        if sfm_dir is None:
            row["status"] = f"{item.record.status}/pull_failed"
            enriched.append(row)
            continue
        displacement = summarize_displacement(sfm_dir, frames_csv)
        tracks = summarize_tracks(sfm_dir, sequential_window)
        row.update({
            "pair_count": displacement.pair_count,
            "max_speed": displacement.max_speed,
            "max_distance": displacement.max_distance,
            "p95_speed": displacement.p95_speed,
            "median_speed": displacement.median_speed,
            "bad_pair_count": displacement.bad_pair_count,
            "worst_pair": displacement.worst_pair,
            "total_classified_tracks": tracks.total_classified_tracks,
            "long_range_track_count": tracks.long_range_track_count,
            "cross_rig_track_count": tracks.cross_rig_track_count,
            "p95_track_extent": tracks.p95_track_extent,
            "median_track_extent": tracks.median_track_extent,
            "max_track_extent": tracks.max_track_extent,
        })
        worst = displacement.worst_pair
        worst_repr = (
            f"  worst={worst['previous_ts']}→{worst['current_ts']} recon={worst['recon_distance']:.2f}m"
            if worst is not None
            else ""
        )
        print(
            f"  max_speed={displacement.max_speed:.2f} m/s  "
            f"bad_pairs={displacement.bad_pair_count}/{displacement.pair_count}  "
            f"long_range={tracks.long_range_track_count}  "
            f"p95_extent={tracks.p95_track_extent:.1f}"
            f"{worst_repr}"
        )
        enriched.append(row)
    return enriched


def base_row(item: ClassifiedReconstruction) -> EnrichedRow:
    return {
        "reconstruction_id": str(item.record.reconstruction_id),
        "retrieval_label": item.retrieval_label,
        "vio_em_label": item.vio_em_label,
        "replicate": item.replicate,
        "retrieval_neighbors": item.record.retrieval_neighbors,
        "vio_em_rotation_deg": item.record.vio_em_rotation_deg,
        "status": item.record.status,
        "created_at": item.record.created_at,
    }


def summarize_displacement(sfm_dir: Path, frames_csv: Path) -> DisplacementSummary:
    image_id_to_timestamp = parse_image_id_to_timestamp(sfm_dir / "images.txt")
    rig_centers = parse_rig_centers(sfm_dir / "frames.txt", image_id_to_timestamp)
    prior_centers = parse_prior_centers(frames_csv)

    rigs = sorted({rig_id for rig_id, _ in rig_centers})
    speeds: list[float] = []
    distances: list[float] = []
    worst_pair: dict[str, float | int] | None = None
    bad_pair_count = 0
    pair_count = 0

    for rig_id in rigs:
        rig_timestamps = sorted(timestamp for (other_rig_id, timestamp) in rig_centers if other_rig_id == rig_id)
        for previous_ts, current_ts in pairwise(rig_timestamps):
            recon_distance = float(
                np.linalg.norm(rig_centers[(rig_id, current_ts)] - rig_centers[(rig_id, previous_ts)])
            )
            delta_seconds = (current_ts - previous_ts) / 1000.0
            speed = recon_distance / delta_seconds if delta_seconds > 0 else float("inf")
            speeds.append(speed)
            distances.append(recon_distance)
            pair_count += 1
            if speed > TELEPORT_SPEED_THRESHOLD_M_PER_S:
                bad_pair_count += 1
            if worst_pair is None or speed > worst_pair["speed"]:
                prior_distance = (
                    float(np.linalg.norm(prior_centers[current_ts] - prior_centers[previous_ts]))
                    if previous_ts in prior_centers and current_ts in prior_centers
                    else float("nan")
                )
                worst_pair = {
                    "previous_ts": previous_ts,
                    "current_ts": current_ts,
                    "delta_seconds": delta_seconds,
                    "recon_distance": recon_distance,
                    "prior_distance": prior_distance,
                    "speed": speed,
                }

    return DisplacementSummary(
        pair_count=pair_count,
        max_speed=float(np.max(speeds)) if speeds else float("nan"),
        max_distance=float(np.max(distances)) if distances else float("nan"),
        p95_speed=float(np.percentile(speeds, 95)) if speeds else float("nan"),
        median_speed=float(np.median(speeds)) if speeds else float("nan"),
        bad_pair_count=bad_pair_count,
        worst_pair=worst_pair,
    )


def summarize_tracks(sfm_dir: Path, sequential_window: int):
    image_id_to_timestamp = parse_image_id_to_timestamp(sfm_dir / "images.txt")
    image_id_to_rig_temporal_index = parse_image_id_to_rig_temporal_index(sfm_dir / "frames.txt", image_id_to_timestamp)
    return summarize_track_extents(sfm_dir / "points3D.txt", image_id_to_rig_temporal_index, sequential_window)


def write_results(enriched: list[EnrichedRow], output_dir: Path) -> None:
    json_path = output_dir / "results.json"
    json_path.write_text(json.dumps(enriched, indent=2, default=str))
    csv_path = output_dir / "results.csv"
    with csv_path.open("w") as fh:
        writer = csv.DictWriter(fh, fieldnames=RESULT_FIELD_NAMES, extrasaction="ignore")
        writer.writeheader()
        for entry in enriched:
            writer.writerow(entry)
    print(f"\nwrote {csv_path}")
    print(f"wrote {json_path}")


def print_summary(enriched: list[EnrichedRow], summary_path: Path) -> None:
    cells: dict[tuple[str, str], list[EnrichedRow]] = {}
    for entry in enriched:
        if entry.get("max_speed") is None:
            continue
        cell_key = (entry["retrieval_label"], entry["vio_em_label"])
        cells.setdefault(cell_key, []).append(entry)
    lines = ["=== per-cell summary (median across replicates) ==="]
    for (retrieval_label, vio_em_label), entries in sorted(cells.items()):
        speeds = [e["max_speed"] for e in entries if "max_speed" in e]
        bad_counts = [e["bad_pair_count"] for e in entries if "bad_pair_count" in e]
        long_range = [e["long_range_track_count"] for e in entries if "long_range_track_count" in e]
        p95_extents = [e["p95_track_extent"] for e in entries if "p95_track_extent" in e]
        if not speeds:
            continue
        lines.append(
            f"  {retrieval_label} {vio_em_label}: n={len(speeds)}  "
            f"median_max_speed={np.median(speeds):.2f} m/s  "
            f"speed_spread={max(speeds) - min(speeds):.2f}  "
            f"median_bad_pairs={int(np.median(bad_counts))}  "
            f"median_long_range={int(np.median(long_range))}  "
            f"median_p95_extent={np.median(p95_extents):.1f}"
        )
    summary_text = "\n".join(lines) + "\n"
    summary_path.write_text(summary_text)
    print()
    print(summary_text)


if __name__ == "__main__":
    app()
