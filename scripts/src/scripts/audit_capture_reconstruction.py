from __future__ import annotations

import csv
import json
from itertools import pairwise
from pathlib import Path
from typing import Annotated, NamedTuple

import numpy as np
import typer
from numpy import dtype, float64, int64, ndarray
from scipy.spatial.transform import Rotation

from .displacement_check import FrameRecord, parse_frames, parse_image_id_to_timestamp


Vector3 = ndarray[tuple[int], dtype[float64]]
Quat = ndarray[tuple[int], dtype[float64]]
Matrix3 = ndarray[tuple[int, int], dtype[float64]]
ResidualVector = ndarray[tuple[int], dtype[float64]]
TimestampVector = ndarray[tuple[int], dtype[int64]]

TELEPORT_TRANSLATION_SPEED_M_PER_S = 3.0
TELEPORT_ROTATION_SPEED_DEG_PER_S = 360.0

app = typer.Typer(add_completion=False, no_args_is_help=True)


class CapturePose(NamedTuple):
    timestamp_ms: int
    position: Vector3
    rotation_quat_xyzw: Quat


class LoopClosureReport(NamedTuple):
    first_timestamp_ms: int
    last_timestamp_ms: int
    duration_seconds: float
    translation_distance_m: float
    translation_delta_m: Vector3
    rotation_angle_deg: float
    path_length_m: float


class TeleportEvent(NamedTuple):
    previous_timestamp_ms: int
    current_timestamp_ms: int
    delta_seconds: float
    translation_m: float
    translation_speed_m_per_s: float
    rotation_deg: float
    rotation_speed_deg_per_s: float
    trigger: str


class ShapeReport(NamedTuple):
    matched_frame_count: int
    scale: float
    rotation_matrix: Matrix3
    translation_m: Vector3
    residual_rmse_m: float
    residual_max_m: float
    residual_p95_m: float
    residual_p50_m: float
    per_frame_residuals_m: ResidualVector
    per_frame_timestamps_ms: TimestampVector


@app.command()
def audit(
    sfm_directory: Annotated[
        Path,
        typer.Argument(
            help="COLMAP sfm_model directory (containing images.txt, frames.txt). Pulled from MinIO `<reconstruction_id>/sfm_model/`."
        ),
    ],
    frames_csv: Annotated[
        Path,
        typer.Argument(help="Capture session per-rig frames.csv (timestamp_ms, tx, ty, tz, qx, qy, qz, qw)."),
    ],
    output_directory: Annotated[
        Path,
        typer.Option(
            help="Directory to write the JSON summary + residual time-series CSV. Defaults to the SfM directory."
        ),
    ] = Path(),
) -> None:
    output_directory = output_directory if output_directory != Path() else sfm_directory

    capture_priors = parse_capture_priors(frames_csv)
    image_id_to_timestamp = parse_image_id_to_timestamp(sfm_directory / "images.txt")
    recon_records = parse_frames(sfm_directory / "frames.txt", image_id_to_timestamp)

    print(f"capture frames: {len(capture_priors)}")
    print(f"reconstruction registered rig frames: {len(recon_records)}")
    print()

    loop = compute_loop_closure_drift(capture_priors)
    print_loop_closure(loop)
    print()

    teleports = detect_capture_teleports(capture_priors)
    print_teleports(teleports, len(capture_priors))
    print()

    shape = compute_trajectory_shape(capture_priors, recon_records)
    print_shape(shape)

    summary_path = output_directory / "audit_summary.json"
    residuals_path = output_directory / "audit_residuals.csv"
    write_summary(summary_path, loop, teleports, shape)
    write_residuals(residuals_path, shape)
    print()
    print(f"summary: {summary_path}")
    print(f"residual time-series: {residuals_path}")


def parse_capture_priors(frames_csv: Path) -> list[CapturePose]:
    priors: list[CapturePose] = []
    with frames_csv.open() as fh:
        reader = csv.reader(fh)
        next(reader)
        for row in reader:
            timestamp_ms = int(row[0])
            position = np.array([float(row[1]), float(row[2]), float(row[3])])
            rotation_quat_xyzw = np.array([float(row[4]), float(row[5]), float(row[6]), float(row[7])])
            priors.append(CapturePose(timestamp_ms, position, rotation_quat_xyzw))
    priors.sort(key=lambda pose: pose.timestamp_ms)
    return priors


def compute_loop_closure_drift(priors: list[CapturePose]) -> LoopClosureReport:
    first, last = priors[0], priors[-1]
    translation_delta = last.position - first.position
    translation_distance = float(np.linalg.norm(translation_delta))
    relative_rotation = Rotation.from_quat(first.rotation_quat_xyzw).inv() * Rotation.from_quat(last.rotation_quat_xyzw)
    rotation_angle_deg = float(np.degrees(np.linalg.norm(relative_rotation.as_rotvec())))
    duration_seconds = (last.timestamp_ms - first.timestamp_ms) / 1000.0
    path_length = sum(float(np.linalg.norm(curr.position - prev.position)) for prev, curr in pairwise(priors))
    return LoopClosureReport(
        first_timestamp_ms=first.timestamp_ms,
        last_timestamp_ms=last.timestamp_ms,
        duration_seconds=duration_seconds,
        translation_distance_m=translation_distance,
        translation_delta_m=translation_delta,
        rotation_angle_deg=rotation_angle_deg,
        path_length_m=path_length,
    )


def print_loop_closure(report: LoopClosureReport) -> None:
    print("=== Task 1: loop-closure drift (first vs last capture pose) ===")
    print(f"  duration:                {report.duration_seconds:.1f} s")
    print(f"  total path length:       {report.path_length_m:.2f} m")
    print(f"  endpoint translation:    {report.translation_distance_m:.3f} m")
    print(
        f"  endpoint delta (x,y,z):  ({report.translation_delta_m[0]:+.3f}, {report.translation_delta_m[1]:+.3f}, {report.translation_delta_m[2]:+.3f}) m"
    )
    print(f"  endpoint rotation:       {report.rotation_angle_deg:.2f} deg")
    drift_fraction = report.translation_distance_m / report.path_length_m if report.path_length_m > 0 else float("nan")
    print(f"  drift / path-length:     {drift_fraction:.2%}")


def detect_capture_teleports(priors: list[CapturePose]) -> list[TeleportEvent]:
    events: list[TeleportEvent] = []
    for prev, curr in pairwise(priors):
        delta_seconds = (curr.timestamp_ms - prev.timestamp_ms) / 1000.0
        if delta_seconds <= 0:
            continue
        translation = float(np.linalg.norm(curr.position - prev.position))
        translation_speed = translation / delta_seconds
        relative_rotation = Rotation.from_quat(prev.rotation_quat_xyzw).inv() * Rotation.from_quat(
            curr.rotation_quat_xyzw
        )
        rotation_deg = float(np.degrees(np.linalg.norm(relative_rotation.as_rotvec())))
        rotation_speed = rotation_deg / delta_seconds
        triggers: list[str] = []
        if translation_speed > TELEPORT_TRANSLATION_SPEED_M_PER_S:
            triggers.append(f"translation_speed>{TELEPORT_TRANSLATION_SPEED_M_PER_S}m/s")
        if rotation_speed > TELEPORT_ROTATION_SPEED_DEG_PER_S:
            triggers.append(f"rotation_speed>{TELEPORT_ROTATION_SPEED_DEG_PER_S}deg/s")
        if not triggers:
            continue
        events.append(
            TeleportEvent(
                previous_timestamp_ms=prev.timestamp_ms,
                current_timestamp_ms=curr.timestamp_ms,
                delta_seconds=delta_seconds,
                translation_m=translation,
                translation_speed_m_per_s=translation_speed,
                rotation_deg=rotation_deg,
                rotation_speed_deg_per_s=rotation_speed,
                trigger=", ".join(triggers),
            )
        )
    return events


def print_teleports(events: list[TeleportEvent], frame_count: int) -> None:
    print("=== Task 2: capture-session teleport scan ===")
    print(
        f"  thresholds: translation_speed > {TELEPORT_TRANSLATION_SPEED_M_PER_S} m/s "
        f"OR rotation_speed > {TELEPORT_ROTATION_SPEED_DEG_PER_S} deg/s"
    )
    print(
        "  rationale: peak walking speed ~1.5 m/s; peak hand-held rotation ~360 deg/s. "
        "Anything above these is a discontinuity, not motion."
    )
    print(f"  pairs flagged: {len(events)} of {frame_count - 1}")
    if not events:
        return
    print("  top 10 by translation speed:")
    for event in sorted(events, key=lambda candidate: -candidate.translation_speed_m_per_s)[:10]:
        print(
            f"    {event.previous_timestamp_ms} → {event.current_timestamp_ms}  "
            f"Δt={event.delta_seconds:.3f}s  Δt_pos={event.translation_m:.3f}m  "
            f"speed={event.translation_speed_m_per_s:.2f}m/s  Δrot={event.rotation_deg:.2f}deg  "
            f"ω={event.rotation_speed_deg_per_s:.1f}deg/s  ({event.trigger})"
        )


def compute_trajectory_shape(priors: list[CapturePose], recon_records: list[FrameRecord]) -> ShapeReport:
    prior_by_ts: dict[int, Vector3] = {pose.timestamp_ms: pose.position for pose in priors}
    matched: list[tuple[Vector3, Vector3, int]] = []
    for record in recon_records:
        if record.timestamp in prior_by_ts:
            matched.append((record.world_from_rig_center, prior_by_ts[record.timestamp], record.timestamp))
    if len(matched) < 3:
        raise RuntimeError(f"Insufficient matched frames for Umeyama alignment: {len(matched)}")
    source = np.array([entry[0] for entry in matched])
    target = np.array([entry[1] for entry in matched])
    timestamps = np.array([entry[2] for entry in matched], dtype=np.int64)
    order = timestamps.argsort()
    source, target, timestamps = source[order], target[order], timestamps[order]

    scale, rotation_matrix, translation = umeyama_sim3(source, target)
    aligned = (scale * (rotation_matrix @ source.T)).T + translation
    residuals: ResidualVector = np.asarray(np.linalg.norm(target - aligned, axis=1), dtype=float64)
    sum_of_squares = float(residuals @ residuals)
    return ShapeReport(
        matched_frame_count=len(matched),
        scale=scale,
        rotation_matrix=rotation_matrix,
        translation_m=translation,
        residual_rmse_m=float(np.sqrt(sum_of_squares / len(residuals))),
        residual_max_m=float(residuals.max()),
        residual_p95_m=float(np.percentile(residuals, 95)),
        residual_p50_m=float(np.percentile(residuals, 50)),
        per_frame_residuals_m=residuals,
        per_frame_timestamps_ms=timestamps,
    )


def umeyama_sim3(
    source: ndarray[tuple[int, int], dtype[float64]],
    target: ndarray[tuple[int, int], dtype[float64]],
) -> tuple[float, Matrix3, Vector3]:
    source_mean = source.mean(axis=0)
    target_mean = target.mean(axis=0)
    source_centered = source - source_mean
    target_centered = target - target_mean
    correlation = source_centered.T @ target_centered / source.shape[0]
    u, singular_values, vt = np.linalg.svd(correlation)
    sign_correction = np.eye(3)
    if np.linalg.det(u) * np.linalg.det(vt) < 0:
        sign_correction[2, 2] = -1.0
    rotation_matrix = vt.T @ sign_correction @ u.T
    source_variance = (source_centered**2).sum() / source.shape[0]
    scale = float((singular_values * np.diag(sign_correction)).sum() / source_variance)
    translation = target_mean - scale * rotation_matrix @ source_mean
    return scale, rotation_matrix, translation


def print_shape(report: ShapeReport) -> None:
    print("=== Task 3: trajectory shape (Umeyama Sim(3): recon → capture) ===")
    print(f"  matched frames:         {report.matched_frame_count}")
    print(f"  fitted scale:           {report.scale:.6f}  (1.0 == perfect metric match)")
    print(f"  residual RMSE:          {report.residual_rmse_m:.3f} m")
    print(f"  residual max:           {report.residual_max_m:.3f} m")
    print(f"  residual p95:           {report.residual_p95_m:.3f} m")
    print(f"  residual median:        {report.residual_p50_m:.3f} m")
    print("  worst 10 frames (by residual):")
    indices = np.argsort(report.per_frame_residuals_m)[::-1][:10]
    for index in indices:
        print(f"    ts={report.per_frame_timestamps_ms[index]}  residual={report.per_frame_residuals_m[index]:.3f} m")


def write_summary(
    output_path: Path,
    loop: LoopClosureReport,
    teleports: list[TeleportEvent],
    shape: ShapeReport,
) -> None:
    payload = {
        "loop_closure": {
            "first_timestamp_ms": loop.first_timestamp_ms,
            "last_timestamp_ms": loop.last_timestamp_ms,
            "duration_seconds": loop.duration_seconds,
            "path_length_m": loop.path_length_m,
            "endpoint_translation_m": loop.translation_distance_m,
            "endpoint_delta_xyz_m": loop.translation_delta_m.tolist(),
            "endpoint_rotation_deg": loop.rotation_angle_deg,
        },
        "teleports": {
            "translation_speed_threshold_m_per_s": TELEPORT_TRANSLATION_SPEED_M_PER_S,
            "rotation_speed_threshold_deg_per_s": TELEPORT_ROTATION_SPEED_DEG_PER_S,
            "events": [
                {
                    "previous_timestamp_ms": event.previous_timestamp_ms,
                    "current_timestamp_ms": event.current_timestamp_ms,
                    "delta_seconds": event.delta_seconds,
                    "translation_m": event.translation_m,
                    "translation_speed_m_per_s": event.translation_speed_m_per_s,
                    "rotation_deg": event.rotation_deg,
                    "rotation_speed_deg_per_s": event.rotation_speed_deg_per_s,
                    "trigger": event.trigger,
                }
                for event in teleports
            ],
        },
        "trajectory_shape": {
            "matched_frame_count": shape.matched_frame_count,
            "scale": shape.scale,
            "rotation_matrix": shape.rotation_matrix.tolist(),
            "translation_m": shape.translation_m.tolist(),
            "residual_rmse_m": shape.residual_rmse_m,
            "residual_max_m": shape.residual_max_m,
            "residual_p95_m": shape.residual_p95_m,
            "residual_p50_m": shape.residual_p50_m,
        },
    }
    output_path.write_text(json.dumps(payload, indent=2))


def write_residuals(output_path: Path, shape: ShapeReport) -> None:
    with output_path.open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["timestamp_ms", "residual_m"])
        for timestamp, residual in zip(shape.per_frame_timestamps_ms, shape.per_frame_residuals_m):
            writer.writerow([int(timestamp), float(residual)])


if __name__ == "__main__":
    app()
