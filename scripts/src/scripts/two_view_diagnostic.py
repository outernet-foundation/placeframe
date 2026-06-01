from __future__ import annotations

import csv
import json
import re
import sqlite3
import struct
from itertools import pairwise
from math import acos, degrees
from pathlib import Path
from typing import Annotated, NamedTuple

import numpy as np
import typer
from numpy.typing import NDArray  # noqa: TID251 — Phase T piece 3 follow-up migration
from scipy.spatial.transform import Rotation


PAIR_ID_MULTIPLIER = 2147483647
IMAGE_LINE_PATTERN = re.compile(r"^(\d+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+\d+\s+(\S+)$")
NAME_PATTERN = re.compile(r"^([^/]+)/([^/]+)/(\d+)\.jpg$")
MIN_BASELINE_FOR_DIRECTION = 1e-3
TVG_CONFIG_LABEL = {
    0: "UNDEFINED",
    1: "DEGENERATE",
    2: "CALIBRATED",
    3: "UNCALIBRATED",
    4: "PLANAR",
    5: "PANORAMIC",
    6: "PLANAR_OR_PANORAMIC",
    7: "WATERMARK",
    8: "MULTIPLE",
    9: "CALIBRATED_RIG",
}


app = typer.Typer(add_completion=False, no_args_is_help=True)


class Rigid3(NamedTuple):
    rotation: NDArray[np.float64]
    translation: NDArray[np.float64]


class FrameKey(NamedTuple):
    rig_id: str
    camera_id: str
    timestamp_ms: int


class PairRow(NamedTuple):
    rig_id: str
    camera_id: str
    timestamp_a: int
    timestamp_b: int
    delta_seconds: float
    vio_baseline_m: float | None
    tvg_config: int | None
    tvg_config_label: str
    recon_registered: bool
    vio_vs_verif_rotation_deg: float | None
    vio_vs_verif_translation_deg: float | None
    vio_vs_recon_rotation_deg: float | None
    vio_vs_recon_translation_deg: float | None
    verif_vs_recon_rotation_deg: float | None
    verif_vs_recon_translation_deg: float | None


def quaternion_wxyz_to_matrix(qw: float, qx: float, qy: float, qz: float) -> NDArray[np.float64]:
    return Rotation.from_quat([qx, qy, qz, qw]).as_matrix()


def identity_rigid3() -> Rigid3:
    return Rigid3(rotation=np.eye(3), translation=np.zeros(3))


def invert(transform: Rigid3) -> Rigid3:
    rotation_t = transform.rotation.T
    return Rigid3(rotation=rotation_t, translation=-rotation_t @ transform.translation)


def compose(left: Rigid3, right: Rigid3) -> Rigid3:
    return Rigid3(
        rotation=left.rotation @ right.rotation,
        translation=left.rotation @ right.translation + left.translation,
    )


def angle_between_rotations_rad(rotation_a: NDArray[np.float64], rotation_b: NDArray[np.float64]) -> float:
    cos_theta = (np.trace(rotation_a.T @ rotation_b) - 1.0) / 2.0
    return acos(max(-1.0, min(1.0, float(cos_theta))))


def angle_between_directions_rad(
    translation_a: NDArray[np.float64], translation_b: NDArray[np.float64]
) -> float | None:
    norm_a = float(np.linalg.norm(translation_a))
    norm_b = float(np.linalg.norm(translation_b))
    if norm_a < MIN_BASELINE_FOR_DIRECTION or norm_b < MIN_BASELINE_FOR_DIRECTION:
        return None
    cosine = float(np.dot(translation_a, translation_b) / (norm_a * norm_b))
    return acos(max(-1.0, min(1.0, cosine)))


def load_recon_images(images_txt: Path) -> dict[FrameKey, tuple[int, Rigid3]]:
    result: dict[FrameKey, tuple[int, Rigid3]] = {}
    with images_txt.open() as fh:
        for raw_line in fh:
            line = raw_line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            match = IMAGE_LINE_PATTERN.match(line)
            if not match:
                continue
            image_id = int(match.group(1))
            qw, qx, qy, qz = (float(match.group(index)) for index in (2, 3, 4, 5))
            tx, ty, tz = (float(match.group(index)) for index in (6, 7, 8))
            name = match.group(9)
            name_match = NAME_PATTERN.match(name)
            if not name_match:
                continue
            key = FrameKey(name_match.group(1), name_match.group(2), int(name_match.group(3)))
            cam_from_world = Rigid3(
                rotation=quaternion_wxyz_to_matrix(qw, qx, qy, qz),
                translation=np.array([tx, ty, tz], dtype=np.float64),
            )
            result[key] = (image_id, cam_from_world)
    return result


def load_vio_world_from_rig(frames_csv: Path) -> dict[int, Rigid3]:
    result: dict[int, Rigid3] = {}
    with frames_csv.open() as fh:
        reader = csv.reader(fh)
        next(reader)
        for row in reader:
            if len(row) < 8:
                continue
            timestamp = int(row[0])
            tx, ty, tz = (float(row[index]) for index in (1, 2, 3))
            qx, qy, qz, qw = (float(row[index]) for index in (4, 5, 6, 7))
            result[timestamp] = Rigid3(
                rotation=Rotation.from_quat([qx, qy, qz, qw]).as_matrix(),
                translation=np.array([tx, ty, tz], dtype=np.float64),
            )
    return result


def load_cam_from_rig(manifest_json: Path) -> dict[tuple[str, str], Rigid3]:
    with manifest_json.open() as fh:
        manifest = json.load(fh)
    result: dict[tuple[str, str], Rigid3] = {}
    for rig in manifest["rigs"]:
        for camera in rig["cameras"]:
            rotation = camera["rotation"]
            translation = camera["translation"]
            result[(rig["id"], camera["id"])] = Rigid3(
                rotation=Rotation.from_quat([rotation["x"], rotation["y"], rotation["z"], rotation["w"]]).as_matrix(),
                translation=np.array([translation["x"], translation["y"], translation["z"]], dtype=np.float64),
            )
    return result


def load_database_image_ids(database_path: Path) -> dict[FrameKey, int]:
    connection = sqlite3.connect(str(database_path))
    try:
        result: dict[FrameKey, int] = {}
        for image_id, name in connection.execute("SELECT image_id, name FROM images"):
            name_match = NAME_PATTERN.match(name)
            if not name_match:
                continue
            key = FrameKey(name_match.group(1), name_match.group(2), int(name_match.group(3)))
            result[key] = image_id
        return result
    finally:
        connection.close()


def load_database_tvg(database_path: Path) -> dict[int, tuple[int, Rigid3 | None]]:
    connection = sqlite3.connect(str(database_path))
    try:
        result: dict[int, tuple[int, Rigid3 | None]] = {}
        for pair_id, config, qvec, tvec in connection.execute(
            "SELECT pair_id, config, qvec, tvec FROM two_view_geometries"
        ):
            if config == 0 or qvec is None or tvec is None or len(qvec) != 32 or len(tvec) != 24:
                result[pair_id] = (int(config), None)
                continue
            qw, qx, qy, qz = struct.unpack("<4d", qvec)
            tx, ty, tz = struct.unpack("<3d", tvec)
            result[pair_id] = (
                int(config),
                Rigid3(
                    rotation=quaternion_wxyz_to_matrix(qw, qx, qy, qz),
                    translation=np.array([tx, ty, tz], dtype=np.float64),
                ),
            )
        return result
    finally:
        connection.close()


def vio_cam_b_from_cam_a(
    cam_from_rig: Rigid3,
    world_from_rig_a: Rigid3,
    world_from_rig_b: Rigid3,
) -> Rigid3:
    return compose(
        compose(compose(cam_from_rig, invert(world_from_rig_b)), world_from_rig_a),
        invert(cam_from_rig),
    )


def recon_cam_b_from_cam_a(
    cam_a_from_world: Rigid3,
    cam_b_from_world: Rigid3,
) -> Rigid3:
    return compose(cam_b_from_world, invert(cam_a_from_world))


def lookup_tvg(
    database_tvg: dict[int, tuple[int, Rigid3 | None]],
    image_id_a: int,
    image_id_b: int,
) -> tuple[int | None, Rigid3 | None]:
    small_id, big_id = sorted([image_id_a, image_id_b])
    pair_id = small_id * PAIR_ID_MULTIPLIER + big_id
    entry = database_tvg.get(pair_id)
    if entry is None:
        return None, None
    config, transform = entry
    if transform is None:
        return config, None
    if image_id_a != small_id:
        return config, invert(transform)
    return config, transform


@app.command()
def two_view_diagnostic(
    sfm_directory: Annotated[
        Path,
        typer.Argument(
            help="Directory containing COLMAP images.txt (the directory MinIO stores as <reconstruction_id>/sfm_model/)."
        ),
    ],
    frames_csv: Annotated[
        Path,
        typer.Argument(help="Per-rig frames.csv with VIO position priors and orientation."),
    ],
    database_path: Annotated[
        Path,
        typer.Argument(help="COLMAP database.db produced by the reconstructor."),
    ],
    manifest_json: Annotated[
        Path,
        typer.Argument(help="Capture manifest.json with per-camera cam_from_rig calibrations."),
    ],
    output_csv: Annotated[
        Path,
        typer.Argument(help="Path to write the per-pair CSV report."),
    ],
) -> None:
    recon_images = load_recon_images(sfm_directory / "images.txt")
    vio_world_from_rig = load_vio_world_from_rig(frames_csv)
    cam_from_rig_table = load_cam_from_rig(manifest_json)
    database_image_ids = load_database_image_ids(database_path)
    database_tvg = load_database_tvg(database_path)

    grouped: dict[tuple[str, str], list[int]] = {}
    for key in database_image_ids:
        grouped.setdefault((key.rig_id, key.camera_id), []).append(key.timestamp_ms)
    for timestamps in grouped.values():
        timestamps.sort()

    rows: list[PairRow] = []
    with output_csv.open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(list(PairRow._fields))
        for (rig_id, camera_id), timestamps in sorted(grouped.items()):
            cam_from_rig = cam_from_rig_table.get((rig_id, camera_id), identity_rigid3())
            for timestamp_a, timestamp_b in pairwise(timestamps):
                row = build_row(
                    rig_id,
                    camera_id,
                    timestamp_a,
                    timestamp_b,
                    cam_from_rig,
                    recon_images,
                    vio_world_from_rig,
                    database_image_ids,
                    database_tvg,
                )
                rows.append(row)
                writer.writerow([format_field(value) for value in row])

    print_summary(rows)


def build_row(
    rig_id: str,
    camera_id: str,
    timestamp_a: int,
    timestamp_b: int,
    cam_from_rig: Rigid3,
    recon_images: dict[FrameKey, tuple[int, Rigid3]],
    vio_world_from_rig: dict[int, Rigid3],
    database_image_ids: dict[FrameKey, int],
    database_tvg: dict[int, tuple[int, Rigid3 | None]],
) -> PairRow:
    key_a = FrameKey(rig_id, camera_id, timestamp_a)
    key_b = FrameKey(rig_id, camera_id, timestamp_b)
    image_id_a = database_image_ids.get(key_a)
    image_id_b = database_image_ids.get(key_b)

    delta_seconds = (timestamp_b - timestamp_a) / 1000.0
    vio_a = vio_world_from_rig.get(timestamp_a)
    vio_b = vio_world_from_rig.get(timestamp_b)
    vio_transform = (
        vio_cam_b_from_cam_a(cam_from_rig, vio_a, vio_b) if vio_a is not None and vio_b is not None else None
    )
    vio_baseline = float(np.linalg.norm(vio_transform.translation)) if vio_transform is not None else None

    verif_config: int | None = None
    verif_label = ""
    verif_transform: Rigid3 | None = None
    if image_id_a is not None and image_id_b is not None:
        verif_config, verif_transform = lookup_tvg(database_tvg, image_id_a, image_id_b)
        verif_label = TVG_CONFIG_LABEL.get(verif_config, "") if verif_config is not None else ""

    recon_a = recon_images.get(key_a)
    recon_b = recon_images.get(key_b)
    recon_registered = recon_a is not None and recon_b is not None
    recon_transform = (
        recon_cam_b_from_cam_a(recon_a[1], recon_b[1]) if recon_a is not None and recon_b is not None else None
    )

    return PairRow(
        rig_id=rig_id,
        camera_id=camera_id,
        timestamp_a=timestamp_a,
        timestamp_b=timestamp_b,
        delta_seconds=delta_seconds,
        vio_baseline_m=vio_baseline,
        tvg_config=verif_config,
        tvg_config_label=verif_label,
        recon_registered=recon_registered,
        vio_vs_verif_rotation_deg=pair_rotation_deg(vio_transform, verif_transform),
        vio_vs_verif_translation_deg=pair_translation_deg(vio_transform, verif_transform),
        vio_vs_recon_rotation_deg=pair_rotation_deg(vio_transform, recon_transform),
        vio_vs_recon_translation_deg=pair_translation_deg(vio_transform, recon_transform),
        verif_vs_recon_rotation_deg=pair_rotation_deg(verif_transform, recon_transform),
        verif_vs_recon_translation_deg=pair_translation_deg(verif_transform, recon_transform),
    )


def pair_rotation_deg(left: Rigid3 | None, right: Rigid3 | None) -> float | None:
    if left is None or right is None:
        return None
    return degrees(angle_between_rotations_rad(left.rotation, right.rotation))


def pair_translation_deg(left: Rigid3 | None, right: Rigid3 | None) -> float | None:
    if left is None or right is None:
        return None
    angle = angle_between_directions_rad(left.translation, right.translation)
    return None if angle is None else degrees(angle)


def format_field(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def format_optional_deg(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.2f}°"


def print_summary(rows: list[PairRow]) -> None:
    print(f"\ntotal pairs: {len(rows)}")
    columns: tuple[tuple[str, str], ...] = (
        ("vio_vs_verif_rotation_deg", "1↔2 rotation (VIO vs verification)"),
        ("vio_vs_verif_translation_deg", "1↔2 translation-dir (VIO vs verification)"),
        ("vio_vs_recon_rotation_deg", "1↔3 rotation (VIO vs final recon)"),
        ("vio_vs_recon_translation_deg", "1↔3 translation-dir (VIO vs final recon)"),
        ("verif_vs_recon_rotation_deg", "2↔3 rotation (verification vs final recon)"),
        ("verif_vs_recon_translation_deg", "2↔3 translation-dir (verification vs final recon)"),
    )
    for column, label in columns:
        values = [value for row in rows if (value := getattr(row, column)) is not None]
        if not values:
            print(f"  {label}: no samples")
            continue
        array = np.array(values, dtype=np.float64)
        print(
            f"  {label}: n={len(values)} "
            f"median={np.median(array):.2f}° p95={np.percentile(array, 95):.2f}° "
            f"p99={np.percentile(array, 99):.2f}° max={array.max():.2f}°"
        )

    def vio_verif_translation(row: PairRow) -> float | None:
        return row.vio_vs_verif_translation_deg

    def vio_recon_translation(row: PairRow) -> float | None:
        return row.vio_vs_recon_translation_deg

    for header, getter in (
        ("\ntop 10 by 1↔2 translation-dir (VIO vs verification):", vio_verif_translation),
        ("\ntop 10 by 1↔3 translation-dir (VIO vs final recon):", vio_recon_translation),
    ):
        print(header)
        sortable = [row for row in rows if getter(row) is not None]
        for row in sorted(sortable, key=lambda row: -(getter(row) or 0.0))[:10]:
            print(
                f"  {row.rig_id}/{row.camera_id} {row.timestamp_a} → {row.timestamp_b} "
                f"tvg={row.tvg_config_label or 'n/a'} "
                f"vio↔verif rot/trans={format_optional_deg(row.vio_vs_verif_rotation_deg)}/{format_optional_deg(row.vio_vs_verif_translation_deg)} "
                f"vio↔recon rot/trans={format_optional_deg(row.vio_vs_recon_rotation_deg)}/{format_optional_deg(row.vio_vs_recon_translation_deg)} "
                f"verif↔recon rot/trans={format_optional_deg(row.verif_vs_recon_rotation_deg)}/{format_optional_deg(row.verif_vs_recon_translation_deg)}"
            )


if __name__ == "__main__":
    app()
