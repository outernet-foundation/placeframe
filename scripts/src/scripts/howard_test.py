from __future__ import annotations

import base64
import csv
import re
import sys
import tarfile
import zipfile
from asyncio import run, sleep, to_thread
from collections.abc import Callable
from datetime import datetime, timezone
from io import BytesIO
from json import dumps, loads
from shutil import rmtree
from pathlib import Path
from struct import pack
from typing import Annotated, Any, NoReturn, cast
from uuid import UUID, uuid4

import matplotlib as mpl
import numpy as np
import typer
from core.capture_session_manifest import CaptureSessionManifest
from core.localization_metrics import RANSAC_THRESHOLD_DEFAULT, RETRIEVAL_TOP_K_DEFAULT
from panorama.video import frames as video_frames
from panorama.video import inspect as inspect_video
from core.reconstruction_options import ReconstructionOptions as CoreReconstructionOptions
from numpy.typing import NDArray  # noqa: TID251 -- one-off visualizer, not worth shape-branding
from PIL import Image, ImageDraw, ImageFont
from scipy.spatial.transform import Rotation

mpl.use("Agg")
from matplotlib import pyplot as plt  # noqa: E402 -- backend must be selected before pyplot import

from placeframe_api_client import (
    ApiException,
    AxisConvention,
    CaptureSessionRead,
    CaptureSessionUpdate,
    DefaultApi,
    DeviceType,
    LocalizationMapCreate,
    PinholeCameraConfig,
    ReconstructionCreate,
    ReconstructionCreateWithOptions,
    ReconstructionOptions,
    ReconstructionReadWithQueue,
    ReconstructionStatus,
)

from .api_auth import authenticated_api_client

app = typer.Typer(add_completion=False, no_args_is_help=True)

# Capture tars can run into the hundreds of MB; the upload is a single request.
REQUEST_TIMEOUT = 600.0
RECONSTRUCTION_POLL_S = 5.0
RECONSTRUCTION_TIMEOUT_S = 1800.0

# The reconstructor writes the sparse point cloud as a flattened NPZ (positions + colors, no point
# IDs/tracks) at this path inside the tar, separate from the full COLMAP text model — see
# docker/reconstructor/src/reconstructor/colmap.py.
POINT_CLOUD_TAR_MEMBER = "sfm_model/points3D.npz"

# Sibling NPZ, same directory: one world_from_rig pose per registered *rig frame* (not per camera
# image — a multi-camera rig like the stereo ZED contributes one pose per synchronized frame, not
# one per image). `orientations` is xyzw (scipy Rotation.as_quat() default), matching core's
# "quaternion order is xyzw everywhere" convention — see colmap.py's write_reconstruction.
FRAME_POSES_TAR_MEMBER = "sfm_model/frame_poses.npz"

# Local cache for reconstruction exports and their rendered point clouds, keyed by reconstruction
# id. Populated once a reconstruction succeeds (see _ensure_cached_tar) so the dashboard's
# Visualize tab doesn't re-download a multi-hundred-MB tar on every "Create PNG" click.
REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = REPO_ROOT / "data"
RECONSTRUCTIONS_DIR = DATA_DIR / "reconstructions"
LOCALIZATIONS_DIR = DATA_DIR / "localizations"

LOCALIZATION_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
LOCALIZATION_THUMBNAIL_SIZE = (200, 150)

# docker/api/src/routers/reconstructions.py's METADATA_MEMBER: the tar entry naming the
# reconstruction (and so its id, which the API refuses to import twice).
TAR_METADATA_MEMBER = "metadata.json"

# "Poseless" captures: a plain sequentially-ordered folder of images with no known camera pose
# (e.g. frames extracted from a video), packaged into a monocular capture with a synthetic
# straight-line trajectory. Rig.__init__ (docker/reconstructor/src/reconstructor/rig.py) parses
# frames.csv as a fixed 7-column `timestamp_ms,tx,ty,tz,qx,qy,qz,qw` layout — there is no 3/6-column
# dispatch despite docker/reconstructor/AGENTS.md's "frames.csv schema is column-count-dispatched"
# claim, which describes an aspirational/stale schema, not the code as it stands. An identity
# quaternion keeps rotation a no-op (rig.py only uses it to derive gravity_in_rig_local, which comes
# out as OPENCV down [0, 1, 0] regardless — exactly what a stationary-gravity assumption wants).
POSELESS_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
POSELESS_TARGET_KEYFRAMES = 30

# Mirrors ReconstructionOptions.keyframe_min_distance_m's default (core/reconstruction_options.py —
# verified directly, since docker/reconstructor/AGENTS.md's stated default of 0.3m does not match
# the code). Used only to size the synthetic trajectory's step so it yields roughly
# POSELESS_TARGET_KEYFRAMES keyframes regardless of how many images were supplied.
POSELESS_KEYFRAME_MIN_DISTANCE_M = 1.0
# Default milliseconds between synthetic frame timestamps; arbitrary since no real capture rate
# exists, but must be nonzero and monotonically increasing per frame for frame_id uniqueness.
POSELESS_FRAME_INTERVAL_MS = 200
# Bundle adjustment treats position priors as a quadratic PosePrior loss (docker/reconstructor's
# "priors-on vs priors-off" constraint) — with a synthetic trajectory this would inject fabricated
# geometry into BA. Inflating the prior's assumed uncertainty this far makes that loss term
# negligible, so COLMAP's own feature-matched geometry dominates instead, approximating the
# multi-camera priors-off path without touching the reconstructor itself.
POSELESS_POSE_PRIOR_SIGMA_M = 1000.0

# A spherical video is dense in time (30 fps); every fifth frame at walking pace
# leaves enough baseline between frames without uploading the whole video.
SPHERICAL_FRAME_STRIDE = 5

_NATURAL_SORT_SPLIT_RE = re.compile(r"(\d+)")


def _natural_sort_key(name: str) -> list[int | str]:
    return [int(part) if part.isdigit() else part.lower() for part in _NATURAL_SORT_SPLIT_RE.split(name)]


_TERMINAL_STATUSES = (ReconstructionStatus.SUCCEEDED, ReconstructionStatus.FAILED, ReconstructionStatus.CANCELLED)


def _cached_tar_path(reconstruction_id: UUID) -> Path:
    return RECONSTRUCTIONS_DIR / f"{reconstruction_id}.tar"


def _cached_png_path(reconstruction_id: UUID) -> Path:
    return RECONSTRUCTIONS_DIR / f"{reconstruction_id}.png"


async def _ensure_cached_tar(api: DefaultApi, reconstruction_id: UUID) -> Path:
    path = _cached_tar_path(reconstruction_id)
    if not path.exists():
        tar_bytes = await api.export_reconstruction_tar(id=reconstruction_id, _request_timeout=REQUEST_TIMEOUT)
        RECONSTRUCTIONS_DIR.mkdir(parents=True, exist_ok=True)
        path.write_bytes(tar_bytes)
    return path


async def upload_capture_session(
    api: DefaultApi,
    tar_name: str,
    tar_bytes: bytes,
    device_type: DeviceType,
    name: str,
    id: UUID | None = None,
) -> CaptureSessionRead:
    return await api.create_capture_session(
        device_type=device_type,
        data=(tar_name, tar_bytes),
        name=name,
        id=id,
        _request_timeout=REQUEST_TIMEOUT,
    )


def build_spherical_capture_tar(
    video_path: Path,
    stride: int,
    max_width: int,
) -> tuple[bytes, int, str]:
    """Package a spherical video as a capture: one equirectangular frame per instant.

    The frames are uploaded as the camera recorded them; the views a
    reconstructor can model are rendered from them at reconstruction time, so
    the layout stays a per-reconstruction choice (ReconstructionOptions'
    spherical_* fields) rather than something baked into the capture.
    """
    info = inspect_video(video_path)
    if not info.is_spherical:
        raise ValueError(
            f"{video_path.name} declares no spherical projection (no sv3d box), so it is an ordinary video; "
            "only spherical captures are supported here"
        )
    if not info.is_equirectangular:
        raise ValueError(f"{video_path.name} is {info.projection}; only EQUIRECTANGULAR frames are supported")

    frame_interval_ms = 1000.0 * stride / info.fps
    width = min(max_width, info.width) if max_width else info.width
    height = width // 2

    manifest = {
        "axis_convention": "OPENCV",
        "rigs": [
            {
                "id": "rig0",
                "cameras": [
                    {
                        "id": "camera0",
                        "ref_sensor": True,
                        "rotation": {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0},
                        "translation": {"x": 0.0, "y": 0.0, "z": 0.0},
                        # No focal length: a sphere is not a perspective image.
                        "camera_config": {
                            "orientation": "TOP_LEFT",
                            "width": width,
                            "height": height,
                            "projection": "EQUIRECTANGULAR",
                        },
                    }
                ],
            }
        ],
        "capture_interval_seconds": frame_interval_ms / 1000.0,
    }

    buffer = BytesIO()
    timestamps: list[int] = []
    with tarfile.open(fileobj=buffer, mode="w") as tar:

        def add_bytes(name: str, data: bytes) -> None:
            info_member = tarfile.TarInfo(name=name)
            info_member.size = len(data)
            tar.addfile(info_member, BytesIO(data))

        for index, frame in video_frames(video_path, stride):
            timestamp_ms = round(index * 1000 / info.fps)
            timestamps.append(timestamp_ms)
            image = Image.fromarray(frame[:, :, ::-1])  # decoded BGR; PIL wants RGB
            if width != info.width:
                image = image.resize((width, height), Image.Resampling.LANCZOS)
            encoded = BytesIO()
            image.save(encoded, format="JPEG", quality=95)
            add_bytes(f"rig0/camera0/{timestamp_ms}.jpg", encoded.getvalue())

        if not timestamps:
            raise ValueError(f"No frames decoded from {video_path}")

        # Same synthetic straight-line trajectory as an image folder, for the same
        # reason: a video carries no poses, and keyframe selection needs translations.
        step_m = (POSELESS_TARGET_KEYFRAMES * POSELESS_KEYFRAME_MIN_DISTANCE_M) / max(1, len(timestamps) - 1)
        frame_lines = ["timestamp_ms,tx,ty,tz,qx,qy,qz,qw"]
        frame_lines += [f"{timestamp},{index * step_m:.6f},0,0,0,0,0,1" for index, timestamp in enumerate(timestamps)]
        add_bytes("rig0/frames.csv", ("\n".join(frame_lines) + "\n").encode())
        add_bytes("manifest.json", dumps(manifest).encode())

    summary = f"{len(timestamps)} frames at {width}x{height} (every {stride} of {info.frame_count}, {info.fps:g} fps)"
    return buffer.getvalue(), len(timestamps), summary


def build_poseless_capture_tar(
    image_dir: Path,
    focal_length: float,
    frame_interval_ms: int = POSELESS_FRAME_INTERVAL_MS,
) -> tuple[bytes, int]:
    images = sorted(
        (p for p in image_dir.iterdir() if p.is_file() and p.suffix.lower() in POSELESS_IMAGE_EXTENSIONS),
        key=lambda p: _natural_sort_key(p.name),
    )
    if not images:
        raise ValueError(f"No images (.jpg/.jpeg/.png) found in {image_dir}")

    with Image.open(images[0]) as first_image:
        width, height = first_image.size

    manifest = {
        "axis_convention": "OPENCV",
        "rigs": [
            {
                "id": "rig0",
                "cameras": [
                    {
                        "id": "camera0",
                        "ref_sensor": True,
                        "rotation": {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0},
                        "translation": {"x": 0.0, "y": 0.0, "z": 0.0},
                        "camera_config": {
                            "orientation": "TOP_LEFT",
                            "width": width,
                            "height": height,
                            # No calibration exists for an arbitrary image folder, so the caller
                            # supplies a real (or best-estimated, e.g. from a known FOV) focal
                            # length in pixels rather than the tool guessing one — a wrong fx/fy
                            # distorts scale/geometry, and unit-aspect-ratio guesses (fx=fy=width)
                            # are frequently far off for wide/fisheye-ish lenses.
                            "fx": focal_length,
                            "fy": focal_length,
                            "cx": width / 2.0,
                            "cy": height / 2.0,
                        },
                    }
                ],
            }
        ],
        "capture_interval_seconds": frame_interval_ms / 1000.0,
    }

    # Straight-line synthetic trajectory sized so keyframe selection (which keeps a frame every
    # POSELESS_KEYFRAME_MIN_DISTANCE_M of translation) yields roughly POSELESS_TARGET_KEYFRAMES
    # keyframes regardless of how many images were supplied.
    step_m = (POSELESS_TARGET_KEYFRAMES * POSELESS_KEYFRAME_MIN_DISTANCE_M) / max(1, len(images) - 1)

    frame_lines = ["timestamp_ms,tx,ty,tz,qx,qy,qz,qw"]
    for index in range(len(images)):
        timestamp_ms = index * frame_interval_ms
        frame_lines.append(f"{timestamp_ms},{index * step_m:.6f},0,0,0,0,0,1")
    frames_csv = "\n".join(frame_lines) + "\n"

    buffer = BytesIO()
    with tarfile.open(fileobj=buffer, mode="w") as tar:

        def add_bytes(name: str, data: bytes) -> None:
            info = tarfile.TarInfo(name=name)
            info.size = len(data)
            tar.addfile(info, BytesIO(data))

        add_bytes("manifest.json", dumps(manifest).encode())
        add_bytes("rig0/frames.csv", frames_csv.encode())
        for index, image_path in enumerate(images):
            timestamp_ms = index * frame_interval_ms
            tar.add(image_path, arcname=f"rig0/camera0/{timestamp_ms}.jpg")

    return buffer.getvalue(), len(images)


async def create_reconstruction(
    api: DefaultApi,
    capture_session_id: UUID,
    options: ReconstructionOptions,
    wait: bool,
    timeout_s: float = RECONSTRUCTION_TIMEOUT_S,
) -> ReconstructionReadWithQueue:
    # create_reconstruction both creates the row and queues it for the reconstructor to pick up
    # over the lease-server poll (worker-pull architecture — see docker/AGENTS.md); there is no
    # separate "start" call.
    reconstruction = await api.create_reconstruction(
        ReconstructionCreateWithOptions(
            create=ReconstructionCreate(capture_session_id=capture_session_id),
            options=options,
        )
    )
    if not wait:
        return reconstruction

    elapsed = 0.0
    while reconstruction.status not in _TERMINAL_STATUSES:
        if elapsed >= timeout_s:
            raise TimeoutError(f"Reconstruction {reconstruction.id} did not finish within {timeout_s}s")
        await sleep(RECONSTRUCTION_POLL_S)
        elapsed += RECONSTRUCTION_POLL_S
        reconstruction = await api.get_reconstruction(id=reconstruction.id)
    if reconstruction.status == ReconstructionStatus.SUCCEEDED:
        await _ensure_cached_tar(api, reconstruction.id)
    return reconstruction


def _parse_options(options_json: str | None) -> ReconstructionOptions:
    return ReconstructionOptions.model_validate(loads(options_json)) if options_json else ReconstructionOptions()


def _parse_poseless_options(options_json: str | None, use_all_images: bool) -> ReconstructionOptions:
    overrides = loads(options_json) if options_json else {}
    overrides.setdefault("pose_prior_position_sigma_m", POSELESS_POSE_PRIOR_SIGMA_M)
    if use_all_images:
        # select_keyframes_by_distance (docker/reconstructor/src/reconstructor/keyframes.py) keeps
        # a frame iff its distance from the last kept keyframe is >= this threshold. The synthetic
        # trajectory's per-frame step is always well above 1e-6 (even at very high image counts),
        # so this guarantees every supplied image is kept as a keyframe rather than thinned down to
        # ~POSELESS_TARGET_KEYFRAMES — unless the caller's own options_json already sets this.
        overrides.setdefault("keyframe_min_distance_m", 1e-6)
    return ReconstructionOptions.model_validate(overrides)


def _metrics(reconstruction: ReconstructionReadWithQueue) -> dict[str, Any]:
    metrics: dict[str, Any] = reconstruction.manifest.get("metrics") or {}
    return metrics


def _capture_to_dict(session: CaptureSessionRead) -> dict[str, Any]:
    return {
        "id": str(session.id),
        "name": session.name,
        "device_type": session.device_type.value,
        "size_bytes": session.size_bytes,
        "recorded_at": session.recorded_at.isoformat(),
    }


# Server defaults for every ReconstructionOptions field (core's model: the generated client's omits
# fields whose default is None). Reconstructions of one capture differ only by their options, so
# the dashboard shows each one's departures from these.
_DEFAULT_OPTIONS: dict[str, Any] = CoreReconstructionOptions().model_dump(mode="json")


def _options_diff(options: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in options.items() if k not in _DEFAULT_OPTIONS or _DEFAULT_OPTIONS[k] != v}


def _reconstruction_to_dict(reconstruction: ReconstructionReadWithQueue) -> dict[str, Any]:
    metrics = _metrics(reconstruction)
    options: dict[str, Any] = reconstruction.manifest.get("options") or {}
    tar_path = _cached_tar_path(reconstruction.id)
    png_path = _cached_png_path(reconstruction.id)
    return {
        "id": str(reconstruction.id),
        "capture_session_id": (str(reconstruction.capture_session_id) if reconstruction.capture_session_id else None),
        "status": reconstruction.status.value,
        "created_at": reconstruction.created_at.isoformat(),
        "error": reconstruction.error,
        "progress_current": reconstruction.progress_current,
        "progress_total": reconstruction.progress_total,
        "queue_position": reconstruction.queue_position,
        "queue_depth": reconstruction.queue_depth,
        "map_point_count": metrics.get("map_point_count"),
        "map_image_count": metrics.get("map_image_count"),
        "options": options,
        "options_diff": _options_diff(options),
        "cached_tar_path": str(tar_path) if tar_path.exists() else None,
        "cached_png_path": str(png_path) if png_path.exists() else None,
    }


# Best-effort: a failure fetching either the manifest or frames.csv for a capture shouldn't abort
# listing every reconstruction, so both halves degrade to None independently rather than raising.
async def _fetch_capture_frame_stats(api: DefaultApi, capture_session_id: UUID) -> tuple[bool | None, int | None]:
    is_stereo: bool | None = None
    total_frame_count: int | None = None
    try:
        manifest_bytes = await api.get_capture_session_manifest_file(id=capture_session_id)
        manifest = CaptureSessionManifest.model_validate_json(manifest_bytes)
        if manifest.rigs:
            is_stereo = len(manifest.rigs[0].cameras) > 1
    except ApiException:
        pass
    try:
        # One row per captured *rig* frame (not per camera image) — see docker/AGENTS.md's
        # frames.csv schema note. This is the total-captured-frames denominator; map_image_count
        # (already on every row) is registered *images*, so dividing the two would double-count
        # for a stereo rig. registered_frame_count (below) is the matching rig-frame numerator.
        csv_bytes = await api.get_capture_session_frames_csv(id=capture_session_id)
        lines = csv_bytes.decode().strip().splitlines()
        total_frame_count = max(0, len(lines) - 1)
    except ApiException:
        pass
    return is_stereo, total_frame_count


# Only populated when the reconstruction's tar is already cached locally — reading frame_poses.npz
# out of a not-yet-downloaded multi-hundred-MB reconstruction tar just to report a count would be a
# surprise download triggered by a dashboard page load. Reconstructions created via the dashboard's
# Reconstruct tab already get their tar cached automatically once they succeed (see
# dashboard/backend's _run_reconstruct_job), so this is populated for those without extra action.
def _registered_frame_count(reconstruction_id: UUID) -> int | None:
    cached = _cached_tar_path(reconstruction_id)
    if not cached.exists():
        return None
    try:
        with tarfile.open(cached, "r") as tar:
            pose_member = tar.extractfile(FRAME_POSES_TAR_MEMBER)
            if pose_member is None:
                return None
            pose_data = np.load(BytesIO(pose_member.read()))
            return int(pose_data["positions"].shape[0])
    except (tarfile.TarError, OSError):
        return None


async def _enrich_reconstruction_rows(
    rows: list[ReconstructionReadWithQueue], frame_stats: bool = True
) -> list[dict[str, Any]]:
    capture_ids = {r.capture_session_id for r in rows if r.capture_session_id is not None}
    stats: dict[UUID, tuple[bool | None, int | None]] = {}
    capture_names: dict[UUID, str] = {}
    async with authenticated_api_client() as api:
        for capture_id in capture_ids if frame_stats else ():
            stats[capture_id] = await _fetch_capture_frame_stats(api, capture_id)
        # Names label reconstructions in the dashboard's pickers — an imported reconstruction's
        # stand-in capture session is named after its tar. One call; best-effort like the stats.
        try:
            capture_names = {s.id: s.name for s in await api.get_capture_sessions(_request_timeout=REQUEST_TIMEOUT)}
        except ApiException:
            pass

    entries: list[dict[str, Any]] = []
    for r in rows:
        entry = _reconstruction_to_dict(r)
        entry["capture_name"] = capture_names.get(r.capture_session_id) if r.capture_session_id else None
        is_stereo, total_frame_count = (
            stats.get(r.capture_session_id, (None, None))
            if r.capture_session_id
            else (
                None,
                None,
            )
        )
        entry["is_stereo"] = is_stereo
        entry["total_frame_count"] = total_frame_count
        entry["registered_frame_count"] = _registered_frame_count(r.id)
        entries.append(entry)
    return entries


@app.command()
def captures(json_output: Annotated[bool, typer.Option("--json", help="Emit JSON instead of a table")] = False) -> None:
    sessions = sorted(run(_list_captures()), key=lambda s: s.recorded_at, reverse=True)
    if json_output:
        typer.echo(dumps([_capture_to_dict(s) for s in sessions]))
        return
    _print_table(
        ["ID", "Name", "Device", "Size", "Recorded"],
        [
            [str(s.id), s.name, s.device_type.value, _format_size(s.size_bytes), s.recorded_at.date().isoformat()]
            for s in sessions
        ],
    )


@app.command()
def reconstructions(
    json_output: Annotated[bool, typer.Option("--json", help="Emit JSON instead of a table")] = False,
    frame_stats: Annotated[
        bool,
        typer.Option(
            "--frame-stats/--no-frame-stats",
            help="With --json, also fetch each capture's mono/stereo and frame count (slow: the API streams "
            "through each capture tar to find them)",
        ),
    ] = True,
) -> None:
    rows = sorted(run(_list_reconstructions()), key=lambda r: r.created_at, reverse=True)
    if json_output:
        # Stereo/mono + frame-usage stats are only fetched for --json (the dashboard's consumption
        # path) — they cost extra API round trips (capture manifest, frames.csv) per unique capture
        # that the plain-text table below has no use for.
        typer.echo(dumps(run(_enrich_reconstruction_rows(rows, frame_stats))))
        return
    _print_table(
        ["ID", "Capture ID", "Status", "Created", "Map points"],
        [
            [
                str(r.id),
                str(r.capture_session_id) if r.capture_session_id else "—",
                r.status.value,
                r.created_at.date().isoformat(),
                str(_metrics(r).get("map_point_count") or "—"),
            ]
            for r in rows
        ],
    )


@app.command(name="delete-reconstruction")
def delete_reconstruction(
    reconstruction_id: Annotated[UUID, typer.Argument(help="Reconstruction to permanently delete")],
    cascade: Annotated[
        bool,
        typer.Option(
            "--cascade",
            help="Also delete what depends on it: its localization map (the API refuses the delete while one "
            "exists), this machine's cached tar/PNG, and its local localization runs",
        ),
    ] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Emit JSON instead of text")] = False,
) -> None:
    # The API refuses to delete a reconstruction with an associated LocalizationMap (a 404-shaped
    # error, oddly — see docker/api/src/routers/reconstructions.py's delete_reconstruction), which
    # in practice only ever exists once someone has run `localize` against this reconstruction.
    removed = run(_delete_reconstruction(reconstruction_id, cascade))
    if json_output:
        typer.echo(dumps({"id": str(reconstruction_id), "deleted": True, **removed}))
        return
    typer.echo(f"Deleted reconstruction {reconstruction_id} and its stored map data")
    if cascade:
        typer.echo(f"  localization map: {'deleted' if removed['localization_map'] else 'none'}")
        typer.echo(f"  local runs deleted: {len(removed['localization_runs'])}")
        typer.echo(f"  local cache files deleted: {removed['cached_files']}")


@app.command(name="rename-capture")
def rename_capture(
    capture_id: Annotated[UUID, typer.Argument(help="Capture session to rename")],
    name: Annotated[str, typer.Argument(help="New name")],
    json_output: Annotated[bool, typer.Option("--json", help="Emit JSON instead of text")] = False,
) -> None:
    session = run(_rename_capture(capture_id, name))
    if json_output:
        typer.echo(dumps(_capture_to_dict(session)))
        return
    typer.echo(f"Renamed capture session {capture_id} to {session.name}")


@app.command(name="delete-capture")
def delete_capture(
    capture_id: Annotated[UUID, typer.Argument(help="Capture session to permanently delete, with its tar")],
    cascade: Annotated[
        bool,
        typer.Option(
            "--cascade",
            help="Also delete the capture's reconstructions first (each with its localization map, stored map "
            "data and local runs); without this the API refuses while any exist",
        ),
    ] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Emit JSON instead of text")] = False,
) -> None:
    removed = run(_delete_capture(capture_id, cascade))
    if json_output:
        typer.echo(dumps({"id": str(capture_id), "deleted": True, **removed}))
        return
    typer.echo(f"Deleted capture session {capture_id} and its tar")
    typer.echo(f"  reconstructions deleted: {len(removed['reconstructions'])}")


@app.command()
def upload(
    tar_path: Annotated[Path, typer.Argument(help="Path to the capture session .tar")],
    device_type: Annotated[DeviceType, typer.Option(help="Device that produced the capture")] = DeviceType.ZED,
    name: Annotated[str | None, typer.Option(help="Capture session name; defaults to the tar's filename stem")] = None,
    id: Annotated[UUID | None, typer.Option(help="Capture session id; server assigns one if omitted")] = None,
) -> None:
    session = run(_upload(tar_path.name, tar_path.read_bytes(), device_type, name or tar_path.stem, id))
    typer.echo(f"Uploaded capture session {session.id} ({session.name}, {session.size_bytes} bytes)")


@app.command(name="import-reconstruction")
def import_reconstruction(
    tar_path: Annotated[
        Path, typer.Argument(help="Reconstruction tar (metadata.json + artifacts); its stem names the map")
    ],
    new_id: Annotated[
        bool,
        typer.Option(
            "--new-id",
            help="Import as a separate copy: give the reconstruction a fresh id instead of the one in the tar "
            "(which can only be imported once)",
        ),
    ] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Emit JSON instead of text")] = False,
) -> None:
    reconstruction = run(_import_reconstruction(tar_path.name, tar_path.read_bytes(), new_id))
    if json_output:
        typer.echo(dumps(_reconstruction_to_dict(reconstruction)))
        return
    typer.echo(f"Imported reconstruction {reconstruction.id} (capture session {reconstruction.capture_session_id})")


@app.command()
def reconstruct(
    capture_id: Annotated[UUID, typer.Argument(help="Capture session to reconstruct")],
    options_json: Annotated[
        str | None, typer.Option(help="JSON overrides for ReconstructionOptions; server defaults for the rest")
    ] = None,
    wait: Annotated[bool, typer.Option(help="Poll until the reconstruction reaches a terminal status")] = False,
    timeout_s: Annotated[float, typer.Option(help="Seconds to wait for --wait before giving up")] = (
        RECONSTRUCTION_TIMEOUT_S
    ),
    json_output: Annotated[bool, typer.Option("--json", help="Emit JSON instead of text")] = False,
) -> None:
    reconstruction = run(_reconstruct(capture_id, _parse_options(options_json), wait, timeout_s))
    _report_reconstruction(reconstruction, json_output)


@app.command(name="reconstruct-poseless")
def reconstruct_poseless(
    image_dir: Annotated[
        Path, typer.Argument(help="Directory of sequentially-ordered, poseless images (.jpg/.jpeg/.png)")
    ],
    name: Annotated[str, typer.Option(help="Capture session name")],
    focal_length: Annotated[
        float,
        typer.Option(
            help="Focal length in pixels, used for both fx and fy (no calibration exists for an arbitrary "
            "image folder, so this must be supplied rather than guessed)"
        ),
    ],
    use_all_images: Annotated[
        bool,
        typer.Option(
            "--use-all-images/--auto-select-images",
            help="Force every supplied image to be kept as a keyframe, instead of letting the reconstructor's "
            f"distance-based keyframe selection thin them down to roughly {POSELESS_TARGET_KEYFRAMES}",
        ),
    ] = False,
    frame_interval_ms: Annotated[
        int, typer.Option(help="Synthetic milliseconds between frames; arbitrary, just needs to be nonzero")
    ] = POSELESS_FRAME_INTERVAL_MS,
    options_json: Annotated[
        str | None,
        typer.Option(
            help="JSON overrides for ReconstructionOptions; pose_prior_position_sigma_m defaults to "
            f"{POSELESS_POSE_PRIOR_SIGMA_M} unless overridden here, to neutralize the synthetic trajectory's "
            "influence on bundle adjustment"
        ),
    ] = None,
    capture_id: Annotated[
        UUID | None,
        typer.Option(
            help="Reconstruct this already-uploaded capture of the folder instead of packaging and uploading a "
            "new one (its focal length is fixed at upload, so --focal-length is not re-applied)"
        ),
    ] = None,
    wait: Annotated[bool, typer.Option(help="Poll until the reconstruction reaches a terminal status")] = False,
    timeout_s: Annotated[float, typer.Option(help="Seconds to wait for --wait before giving up")] = (
        RECONSTRUCTION_TIMEOUT_S
    ),
    json_output: Annotated[bool, typer.Option("--json", help="Emit JSON instead of text")] = False,
) -> None:
    reconstruction = run(
        _reconstruct_poseless(
            image_dir,
            name,
            focal_length,
            _parse_poseless_options(options_json, use_all_images),
            frame_interval_ms,
            wait,
            timeout_s,
            capture_id,
        )
    )
    _report_reconstruction(reconstruction, json_output)


@app.command(name="reconstruct-spherical")
def reconstruct_spherical(
    video: Annotated[Path, typer.Argument(help="Spherical (360) mp4; its own metadata must declare the projection")],
    name: Annotated[str, typer.Option(help="Capture session name")],
    stride: Annotated[int, typer.Option(help="Keep every Nth video frame")] = SPHERICAL_FRAME_STRIDE,
    max_width: Annotated[
        int,
        typer.Option(
            help="Downscale frames to at most this width before upload; 0 keeps the camera's own resolution. "
            "A view rendered at --view-size over --view-fov-deg reads about (view-size / fov) pixels per degree, "
            "so a width below 360 times that throws away detail the reconstruction would have used"
        ),
    ] = 0,
    layout: Annotated[
        str, typer.Option(help="Which views to reconstruct through: tetrahedron (covers the sphere) or cube")
    ] = "tetrahedron",
    view_fov_deg: Annotated[
        float, typer.Option(help="Field of view of each rendered view; must stay under 180")
    ] = 150.0,
    view_size: Annotated[int, typer.Option(help="Pixel size of each rendered view")] = 1600,
    use_all_images: Annotated[
        bool,
        typer.Option(
            "--use-all-images/--auto-select-images",
            help="Reconstruct every extracted frame instead of letting keyframe selection thin them to roughly "
            f"{POSELESS_TARGET_KEYFRAMES}",
        ),
    ] = False,
    options_json: Annotated[
        str | None, typer.Option(help="JSON overrides for ReconstructionOptions; applied over the flags above")
    ] = None,
    wait: Annotated[bool, typer.Option(help="Poll until the reconstruction reaches a terminal status")] = False,
    timeout_s: Annotated[float, typer.Option(help="Seconds to wait for --wait before giving up")] = (
        RECONSTRUCTION_TIMEOUT_S
    ),
    json_output: Annotated[bool, typer.Option("--json", help="Emit JSON instead of text")] = False,
) -> None:
    overrides: dict[str, Any] = loads(options_json) if options_json else {}
    overrides.setdefault("spherical_layout", layout)
    overrides.setdefault("spherical_view_fov_deg", view_fov_deg)
    overrides.setdefault("spherical_view_size", view_size)
    reconstruction = run(
        _reconstruct_spherical(
            video,
            name,
            stride,
            max_width,
            _parse_poseless_options(dumps(overrides), use_all_images),
            wait,
            timeout_s,
        )
    )
    _report_reconstruction(reconstruction, json_output)


@app.command()
def visualize(
    reconstruction_id: Annotated[UUID, typer.Argument(help="Reconstruction whose point cloud to render")],
    output: Annotated[
        Path | None, typer.Option(help="Image path; defaults to data/reconstructions/<reconstruction_id>.png")
    ] = None,
    max_points: Annotated[
        int | None, typer.Option(help="Randomly subsample to at most this many points; omit to render all")
    ] = None,
    point_size: Annotated[float, typer.Option(help="Marker size in points^2")] = 0.5,
    elev: Annotated[float, typer.Option(help="Camera elevation angle in degrees")] = 20.0,
    azim: Annotated[float, typer.Option(help="Camera azimuth angle in degrees")] = -60.0,
    radius_percentile: Annotated[
        float,
        typer.Option(
            help="Percentile of distance-from-median used to frame the view; SfM point clouds tend to have "
            "a sparse noise halo far outside the mapped scene, so 100 usually frames mostly empty space"
        ),
    ] = 90.0,
    json_output: Annotated[bool, typer.Option("--json", help="Emit JSON instead of text")] = False,
) -> None:
    output = output or _cached_png_path(reconstruction_id)
    positions, colors = run(_fetch_point_cloud(reconstruction_id))
    rendered = _render_point_cloud(positions, colors, output, max_points, point_size, elev, azim, radius_percentile)
    if json_output:
        typer.echo(
            dumps({
                "reconstruction_id": str(reconstruction_id),
                "output": str(output),
                "point_count": len(positions),
                "rendered_point_count": rendered,
            })
        )
        return
    typer.echo(f"Rendered {rendered}/{len(positions)} points from reconstruction {reconstruction_id} to {output}")


@app.command()
def points(
    reconstruction_id: Annotated[
        UUID, typer.Argument(help="Reconstruction whose point cloud and camera poses to dump")
    ],
) -> None:
    # Raw binary on stdout, not --json: this feeds the dashboard's interactive (three.js) viewer,
    # where a compact fixed layout is cheaper to transfer and parse than JSON-encoding ~10^5-10^6
    # numbers. Layout: point_count:u32, positions:f32[point_count*3], colors:u8[point_count*3],
    # pose_count:u32, pose_positions:f32[pose_count*3], pose_orientations(xyzw):f32[pose_count*4].
    positions, colors, pose_positions, pose_orientations = run(_fetch_reconstruction_geometry(reconstruction_id))
    stdout = sys.stdout.buffer
    stdout.write(pack("<I", len(positions)))
    stdout.write(np.ascontiguousarray(positions, dtype="<f4").tobytes())
    stdout.write(np.ascontiguousarray(colors, dtype="u1").tobytes())
    stdout.write(pack("<I", len(pose_positions)))
    stdout.write(np.ascontiguousarray(pose_positions, dtype="<f4").tobytes())
    stdout.write(np.ascontiguousarray(pose_orientations, dtype="<f4").tobytes())
    stdout.flush()


@app.command(name="export-poses")
def export_poses(
    reconstruction_id: Annotated[UUID, typer.Argument(help="Reconstruction whose frame_poses.npz to convert")],
    output_path: Annotated[Path, typer.Argument(help="Output JSON file path")],
    json_output: Annotated[bool, typer.Option("--json", help="Emit JSON instead of text")] = False,
) -> None:
    # Reuses the same tar-caching fetch as `points`/`visualize` — no new download path.
    _positions, _colors, pose_positions, pose_orientations = run(_fetch_reconstruction_geometry(reconstruction_id))
    if len(pose_positions) == 0:
        typer.echo(f"No camera poses found for reconstruction {reconstruction_id}", err=True)
        raise typer.Exit(1)

    images = [
        _pose_to_localization_image(i, pose_positions[i], pose_orientations[i]) for i in range(len(pose_positions))
    ]
    result: dict[str, Any] = {
        "reconstruction_id": str(reconstruction_id),
        "source": "frame_poses.npz",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "images": images,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(dumps(result))

    if json_output:
        typer.echo(dumps({"output_path": str(output_path), "count": len(images)}))
        return
    typer.echo(f"Exported {len(images)} poses from reconstruction {reconstruction_id} to {output_path}")


def _write_zip_from_tar(tar_path: Path, output_path: Path) -> int:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    # Nest every entry under a top-level folder named after the output file (stem, so a `.zip`
    # extension doesn't leak into the folder name) rather than writing the tar's members flat —
    # unzipping otherwise dumps 14+ loose files straight into whatever directory it's extracted
    # into. Naming the folder after the chosen output filename (not e.g. the reconstruction id)
    # means renaming the .zip before saving also renames the folder it expands into.
    root = output_path.stem
    file_count = 0
    with tarfile.open(tar_path) as tar, zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for member in tar.getmembers():
            if not member.isfile():
                continue
            extracted = tar.extractfile(member)
            if extracted is None:
                continue
            zf.writestr(f"{root}/{member.name}", extracted.read())
            file_count += 1
    return file_count


async def _export_zip(reconstruction_id: UUID, output_path: Path) -> dict[str, Any]:
    # Reuses the same tar-caching fetch as `points`/`visualize`/`export-poses` — no new download path.
    cached = _cached_tar_path(reconstruction_id)
    if not cached.exists():
        async with authenticated_api_client() as api:
            try:
                await _ensure_cached_tar(api, reconstruction_id)
            except ApiException as exception:
                _fail(exception)
    file_count = await to_thread(_write_zip_from_tar, cached, output_path)
    return {"output_path": str(output_path), "file_count": file_count, "size_bytes": output_path.stat().st_size}


@app.command(name="export-zip")
def export_zip(
    reconstruction_id: Annotated[UUID, typer.Argument(help="Reconstruction to export")],
    output_path: Annotated[Path, typer.Argument(help="Output .zip file path")],
    json_output: Annotated[bool, typer.Option("--json", help="Emit JSON instead of text")] = False,
) -> None:
    result = run(_export_zip(reconstruction_id, output_path))
    if json_output:
        typer.echo(dumps(result))
        return
    typer.echo(f"Exported {result['file_count']} file(s) ({result['size_bytes']} bytes) to {result['output_path']}")


@app.command()
def show(
    reconstruction_id: Annotated[UUID, typer.Argument(help="Reconstruction to inspect")],
    cache: Annotated[
        bool, typer.Option(help="Download and cache the tar locally once the reconstruction has succeeded")
    ] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Emit JSON instead of text")] = False,
) -> None:
    reconstruction = run(_show(reconstruction_id, cache))
    _report_reconstruction(reconstruction, json_output)


@app.command(name="run")
def run_pipeline(
    tar_path: Annotated[Path, typer.Argument(help="Path to the capture session .tar")],
    device_type: Annotated[DeviceType, typer.Option(help="Device that produced the capture")] = DeviceType.ZED,
    name: Annotated[str | None, typer.Option(help="Capture session name; defaults to the tar's filename stem")] = None,
    options_json: Annotated[
        str | None, typer.Option(help="JSON overrides for ReconstructionOptions; server defaults for the rest")
    ] = None,
    wait: Annotated[bool, typer.Option(help="Poll until the reconstruction reaches a terminal status")] = False,
    timeout_s: Annotated[float, typer.Option(help="Seconds to wait for --wait before giving up")] = (
        RECONSTRUCTION_TIMEOUT_S
    ),
) -> None:
    session, reconstruction = run(
        _run_pipeline(
            tar_path.name, tar_path.read_bytes(), device_type, name or tar_path.stem, options_json, wait, timeout_s
        )
    )
    typer.echo(f"Uploaded capture session {session.id} ({session.name}, {session.size_bytes} bytes)")
    _report_reconstruction(reconstruction, json_output=False)


@app.command()
def localize(
    reconstruction_id: Annotated[UUID, typer.Argument(help="Reconstruction to localize query images against")],
    image_dir: Annotated[Path, typer.Argument(help="Directory of query images (.jpg/.jpeg/.png)")],
    retrieval_top_k: Annotated[int, typer.Option(help="Top-K retrieval candidates per query")] = (
        RETRIEVAL_TOP_K_DEFAULT
    ),
    ransac_threshold: Annotated[float, typer.Option(help="RANSAC inlier threshold in pixels")] = (
        RANSAC_THRESHOLD_DEFAULT
    ),
    use_chunking: Annotated[
        bool,
        typer.Option(
            "--use-chunking/--no-chunking",
            help="Batch the localizer's feature-matching step in small chunks instead of one large "
            "batch, capping peak GPU memory per query (see docker/localizer/src/localize.py's "
            "MATCH_BATCH_SIZE). Disable to reproduce the pre-fix behavior for comparison.",
        ),
    ] = True,
    json_output: Annotated[bool, typer.Option("--json", help="Emit JSON instead of a table")] = False,
    run_id: Annotated[
        str | None, typer.Option("--run-id", help="Use this run id instead of generating a fresh one")
    ] = None,
) -> None:
    if not image_dir.is_dir():
        typer.echo(f"Not a directory: {image_dir}", err=True)
        raise typer.Exit(1)
    image_paths = sorted(p for p in image_dir.iterdir() if p.suffix.lower() in LOCALIZATION_IMAGE_EXTENSIONS)
    if not image_paths:
        typer.echo(f"No images found in {image_dir}", err=True)
        raise typer.Exit(1)
    images = [(path.resolve(), path.name, path.read_bytes()) for path in image_paths]

    resolved_run_id = run_id or str(uuid4())
    run_dir = LOCALIZATIONS_DIR / resolved_run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    progress_path = run_dir / "progress.json"
    total = len(images)
    progress_path.write_text(dumps({"completed": 0, "total": total}))

    def report_progress(completed: int) -> None:
        progress_path.write_text(dumps({"completed": completed, "total": total}))

    capture_id, entries = run(
        _localize(reconstruction_id, images, retrieval_top_k, ransac_threshold, use_chunking, report_progress)
    )
    result: dict[str, Any] = {
        "run_id": resolved_run_id,
        "reconstruction_id": str(reconstruction_id),
        "capture_session_id": str(capture_id),
        "image_dir": str(image_dir.resolve()),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "use_chunking": use_chunking,
        "images": entries,
    }
    (run_dir / "results.json").write_text(dumps(result))

    if json_output:
        typer.echo(dumps(result))
        return
    typer.echo(f"Run {result['run_id']}: localized {len(result['images'])} images from {image_dir}")
    _print_table(
        ["#", "Filename", "Status", "X", "Y", "Z", "Roll", "Pitch", "Yaw"],
        [_localization_row(image) for image in result["images"]],
    )


@app.command(name="localize-save-table")
def localize_save_table(
    run_id: Annotated[str, typer.Argument(help="Localization run id")],
    output_path: Annotated[Path, typer.Argument(help="CSV file to write")],
    json_output: Annotated[bool, typer.Option("--json", help="Emit JSON instead of text")] = False,
) -> None:
    result = _load_localization_run(run_id)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["index", "filename", "status", "x", "y", "z", "roll_deg", "pitch_deg", "yaw_deg", "error"])
        for image in result["images"]:
            position: dict[str, Any] = image["position"] or {}
            rpy: dict[str, Any] = image["rpy_deg"] or {}
            writer.writerow([
                image["index"],
                image["filename"],
                image["status"],
                position.get("x"),
                position.get("y"),
                position.get("z"),
                rpy.get("roll"),
                rpy.get("pitch"),
                rpy.get("yaw"),
                image["error"] or "",
            ])
    if json_output:
        typer.echo(dumps({"output_path": str(output_path), "count": len(result["images"])}))
        return
    typer.echo(f"Saved table for run {run_id} to {output_path}")


@app.command(name="localize-save-images")
def localize_save_images(
    run_id: Annotated[str, typer.Argument(help="Localization run id")],
    output_dir: Annotated[Path, typer.Argument(help="Directory to write pose-annotated images to")],
    json_output: Annotated[bool, typer.Option("--json", help="Emit JSON instead of text")] = False,
) -> None:
    result = _load_localization_run(run_id)
    output_dir.mkdir(parents=True, exist_ok=True)
    saved = 0
    # The pose is drawn onto the original image, so a run whose query folder has since been moved or
    # deleted saves nothing; report that rather than a silent zero.
    missing = 0
    for image in result["images"]:
        source_path = Path(image["path"])
        if not source_path.exists():
            missing += 1
            continue
        annotated = _annotate_pose_image(source_path, image)
        annotated.save(output_dir / source_path.name)
        saved += 1
    if json_output:
        typer.echo(dumps({"output_dir": str(output_dir), "count": saved, "missing": missing}))
        return
    typer.echo(f"Saved {saved} annotated images for run {run_id} to {output_dir}")
    if missing:
        typer.echo(f"  {missing} source image(s) no longer exist and were skipped", err=True)


def _localization_row(image: dict[str, Any]) -> list[str]:
    if image["status"] != "ok":
        return [str(image["index"]), image["filename"], image["status"], "—", "—", "—", "—", "—", "—"]
    position, rpy = image["position"], image["rpy_deg"]
    return [
        str(image["index"]),
        image["filename"],
        image["status"],
        f"{position['x']:.3f}",
        f"{position['y']:.3f}",
        f"{position['z']:.3f}",
        f"{rpy['roll']:.1f}",
        f"{rpy['pitch']:.1f}",
        f"{rpy['yaw']:.1f}",
    ]


def _report_reconstruction(reconstruction: ReconstructionReadWithQueue, json_output: bool) -> None:
    if json_output:
        typer.echo(dumps(_reconstruction_to_dict(reconstruction)))
    else:
        typer.echo(f"Reconstruction {reconstruction.id} is {reconstruction.status.value}")
        typer.echo(f"  Capture session: {reconstruction.capture_session_id}")
        if reconstruction.status == ReconstructionStatus.QUEUED and reconstruction.queue_position is not None:
            typer.echo(f"  Queue position: {reconstruction.queue_position} of {reconstruction.queue_depth}")
        if reconstruction.progress_total is not None:
            typer.echo(f"  Progress: {reconstruction.progress_current}/{reconstruction.progress_total}")
        if reconstruction.status in (ReconstructionStatus.FAILED, ReconstructionStatus.CANCELLED):
            typer.echo(f"  Error: {reconstruction.error or '(no error message recorded)'}", err=True)
        elif reconstruction.status == ReconstructionStatus.SUCCEEDED:
            metrics = _metrics(reconstruction)
            typer.echo(f"  Map points: {metrics.get('map_point_count')}, images: {metrics.get('map_image_count')}")
    if reconstruction.status in (ReconstructionStatus.FAILED, ReconstructionStatus.CANCELLED):
        raise typer.Exit(1)


async def _upload(
    tar_name: str, tar_bytes: bytes, device_type: DeviceType, name: str, id: UUID | None
) -> CaptureSessionRead:
    async with authenticated_api_client() as api:
        try:
            return await upload_capture_session(api, tar_name, tar_bytes, device_type, name, id)
        except ApiException as exception:
            _fail(exception)


def _tar_metadata_id(tar_bytes: bytes) -> UUID | None:
    with tarfile.open(fileobj=BytesIO(tar_bytes), mode="r:*") as tar:
        for member in tar:
            if member.name == TAR_METADATA_MEMBER:
                handle = tar.extractfile(member)
                if handle is None:
                    return None
                return UUID(loads(handle.read())["reconstruction"]["id"])
    return None


def _retag_tar(tar_bytes: bytes, reconstruction_id: UUID) -> bytes:
    """The same tar with metadata.json's reconstruction id replaced, for a separate copy."""
    out = BytesIO()
    with (
        tarfile.open(fileobj=BytesIO(tar_bytes), mode="r:*") as source,
        tarfile.open(fileobj=out, mode="w", format=tarfile.GNU_FORMAT) as target,
    ):
        for member in source:
            handle = source.extractfile(member)
            if member.name != TAR_METADATA_MEMBER:
                target.addfile(member, handle)
                continue
            if handle is None:
                raise ValueError(f"{TAR_METADATA_MEMBER} is not a regular file")
            metadata = loads(handle.read())
            metadata["reconstruction"]["id"] = str(reconstruction_id)
            payload = dumps(metadata).encode()
            member.size = len(payload)
            target.addfile(member, BytesIO(payload))
    return out.getvalue()


async def _import_reconstruction(tar_name: str, tar_bytes: bytes, new_id: bool = False) -> ReconstructionReadWithQueue:
    existing_id = _tar_metadata_id(tar_bytes)
    if new_id:
        tar_bytes = await to_thread(_retag_tar, tar_bytes, uuid4())
    async with authenticated_api_client() as api:
        # Checked before the upload: a tar carries one fixed id, so re-importing it would otherwise
        # push the whole (often hundreds of MB) archive only to be refused with a 409.
        if existing_id is not None and not new_id:
            try:
                await api.get_reconstruction(id=existing_id)
            except ApiException as exception:
                if cast("int | None", exception.status) != 404:
                    _fail(exception)
            else:
                typer.echo(
                    f"This tar's reconstruction ({existing_id}) is already imported. Export it again for a new id, "
                    "or pass --new-id to import it as a separate copy.",
                    err=True,
                )
                raise typer.Exit(1)
        try:
            return await api.import_reconstruction_tar(data=(tar_name, tar_bytes), _request_timeout=REQUEST_TIMEOUT)
        except ApiException as exception:
            _fail(exception)


async def _reconstruct(
    capture_id: UUID, options: ReconstructionOptions, wait: bool, timeout_s: float
) -> ReconstructionReadWithQueue:
    async with authenticated_api_client() as api:
        try:
            return await create_reconstruction(api, capture_id, options, wait, timeout_s)
        except ApiException as exception:
            _fail(exception)


async def _reconstruct_spherical(
    video_path: Path,
    name: str,
    stride: int,
    max_width: int,
    options: ReconstructionOptions,
    wait: bool,
    timeout_s: float,
) -> ReconstructionReadWithQueue:
    tar_bytes, frame_count, summary = await to_thread(build_spherical_capture_tar, video_path, stride, max_width)
    typer.echo(f"{video_path.name}: {summary}; capture is {_format_size(len(tar_bytes))}", err=True)
    async with authenticated_api_client() as api:
        try:
            capture = await upload_capture_session(api, f"{name}.tar", tar_bytes, DeviceType.ARFOUNDATION, name)
            typer.echo(f"Uploaded spherical capture {capture.id} ({frame_count} frames)", err=True)
            return await create_reconstruction(api, capture.id, options, wait, timeout_s)
        except ApiException as exception:
            _fail(exception)


async def _reconstruct_poseless(
    image_dir: Path,
    name: str,
    focal_length: float,
    options: ReconstructionOptions,
    frame_interval_ms: int,
    wait: bool,
    timeout_s: float,
    capture_id: UUID | None = None,
) -> ReconstructionReadWithQueue:
    if capture_id is not None:
        async with authenticated_api_client() as api:
            try:
                return await create_reconstruction(api, capture_id, options, wait, timeout_s)
            except ApiException as exception:
                _fail(exception)
    tar_bytes, image_count = await to_thread(build_poseless_capture_tar, image_dir, focal_length, frame_interval_ms)
    async with authenticated_api_client() as api:
        try:
            capture = await upload_capture_session(api, f"{name}.tar", tar_bytes, DeviceType.ARFOUNDATION, name)
            typer.echo(f"Uploaded poseless capture {capture.id} ({image_count} images)", err=True)
            return await create_reconstruction(api, capture.id, options, wait, timeout_s)
        except ApiException as exception:
            _fail(exception)


async def _list_captures() -> list[CaptureSessionRead]:
    async with authenticated_api_client() as api:
        try:
            return await api.get_capture_sessions(_request_timeout=REQUEST_TIMEOUT)
        except ApiException as exception:
            _fail(exception)


async def _list_reconstructions() -> list[ReconstructionReadWithQueue]:
    async with authenticated_api_client() as api:
        try:
            return await api.get_reconstructions(_request_timeout=REQUEST_TIMEOUT)
        except ApiException as exception:
            _fail(exception)


def _delete_local_reconstruction_files(reconstruction_id: UUID) -> int:
    """This machine's cached export/render for a reconstruction; both are re-fetchable."""
    deleted = 0
    for path in (_cached_tar_path(reconstruction_id), _cached_png_path(reconstruction_id)):
        if path.exists():
            path.unlink()
            deleted += 1
    return deleted


def _localization_runs_of(reconstruction_id: UUID) -> list[str]:
    if not LOCALIZATIONS_DIR.exists():
        return []
    runs: list[str] = []
    for run_dir in LOCALIZATIONS_DIR.iterdir():
        for name in ("results.json", "request.json"):
            try:
                data = loads((run_dir / name).read_text())
            except (OSError, ValueError):
                continue
            if data.get("reconstruction_id") == str(reconstruction_id):
                runs.append(run_dir.name)
            break
    return runs


def _delete_local_runs(reconstruction_id: UUID) -> list[str]:
    runs = _localization_runs_of(reconstruction_id)
    for run_id in runs:
        rmtree(LOCALIZATIONS_DIR / run_id, ignore_errors=True)
    return runs


async def _delete_reconstruction_with(api: DefaultApi, reconstruction_id: UUID, cascade: bool) -> dict[str, Any]:
    removed: dict[str, Any] = {"localization_map": None, "localization_runs": [], "cached_files": 0}
    try:
        if cascade:
            # A localization map exists for anything that has been localized against (and for every
            # imported reconstruction); the API refuses the delete while one does.
            try:
                map_id = await api.get_reconstruction_localization_map(id=reconstruction_id)
            except ApiException as exception:
                if cast("int | None", exception.status) != 404:
                    raise
            else:
                await api.delete_localization_map(id=map_id)
                removed["localization_map"] = str(map_id)
        # Deletes the reconstruction's objects in the reconstructions bucket, then the row.
        await api.delete_reconstruction(id=reconstruction_id)
    except ApiException as exception:
        _fail(exception)
    if cascade:
        removed["localization_runs"] = await to_thread(_delete_local_runs, reconstruction_id)
        removed["cached_files"] = await to_thread(_delete_local_reconstruction_files, reconstruction_id)
    return removed


async def _delete_reconstruction(reconstruction_id: UUID, cascade: bool = False) -> dict[str, Any]:
    async with authenticated_api_client() as api:
        return await _delete_reconstruction_with(api, reconstruction_id, cascade)


async def _rename_capture(capture_id: UUID, name: str) -> CaptureSessionRead:
    async with authenticated_api_client() as api:
        try:
            return await api.update_capture_session(
                id=capture_id, capture_session_update=CaptureSessionUpdate(name=name)
            )
        except ApiException as exception:
            _fail(exception)


async def _delete_capture(capture_id: UUID, cascade: bool) -> dict[str, Any]:
    async with authenticated_api_client() as api:
        reconstructions: list[dict[str, Any]] = []
        try:
            if cascade:
                # Returns the capture's reconstruction ids.
                for reconstruction_id in await api.get_capture_session_reconstructions(id=capture_id):
                    removed = await _delete_reconstruction_with(api, reconstruction_id, cascade=True)
                    reconstructions.append({"id": str(reconstruction_id), **removed})
            # Deletes the capture's tar, then the row; refused while any reconstruction remains.
            await api.delete_capture_session(id=capture_id)
        except ApiException as exception:
            _fail(exception)
    return {"reconstructions": reconstructions}


def _format_size(num_bytes: int) -> str:
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def _print_table(headers: list[str], rows: list[list[str]]) -> None:
    if not rows:
        typer.echo("(none)")
        return
    widths = [max(len(cell) for cell in column) for column in zip(headers, *rows)]
    for row in (headers, ["-" * width for width in widths], *rows):
        typer.echo("  ".join(cell.ljust(width) for cell, width in zip(row, widths)))


async def _show(reconstruction_id: UUID, cache: bool = False) -> ReconstructionReadWithQueue:
    async with authenticated_api_client() as api:
        try:
            reconstruction = await api.get_reconstruction(id=reconstruction_id)
            if cache and reconstruction.status == ReconstructionStatus.SUCCEEDED:
                await _ensure_cached_tar(api, reconstruction_id)
            return reconstruction
        except ApiException as exception:
            _fail(exception)


ReconstructionGeometry = tuple[NDArray[np.float32], NDArray[np.uint8], NDArray[np.float32], NDArray[np.float32]]


async def _fetch_point_cloud(reconstruction_id: UUID) -> tuple[NDArray[np.float32], NDArray[np.uint8]]:
    positions, colors, _pose_positions, _pose_orientations = await _fetch_reconstruction_geometry(reconstruction_id)
    return positions, colors


async def _fetch_reconstruction_geometry(reconstruction_id: UUID) -> ReconstructionGeometry:
    cached = _cached_tar_path(reconstruction_id)
    if not cached.exists():
        async with authenticated_api_client() as api:
            try:
                await _ensure_cached_tar(api, reconstruction_id)
            except ApiException as exception:
                _fail(exception)
    return _load_reconstruction_geometry(cached.read_bytes())


def _load_reconstruction_geometry(tar_bytes: bytes) -> ReconstructionGeometry:
    with tarfile.open(fileobj=BytesIO(tar_bytes)) as tar:
        point_member = tar.extractfile(POINT_CLOUD_TAR_MEMBER)
        if point_member is None:
            raise RuntimeError(
                f"No {POINT_CLOUD_TAR_MEMBER} in the reconstruction tar — the reconstruction may not have succeeded"
            )
        point_data = np.load(BytesIO(point_member.read()))
        positions, colors = point_data["positions"], point_data["colors"]

        # Older reconstructions (or a reconstructor version predating pose export) may lack this
        # file; camera poses are a visualization extra, not required for the point cloud itself.
        pose_member = tar.extractfile(FRAME_POSES_TAR_MEMBER)
        if pose_member is not None:
            pose_data = np.load(BytesIO(pose_member.read()))
            pose_positions, pose_orientations = pose_data["positions"], pose_data["orientations"]
        else:
            pose_positions = np.empty((0, 3), dtype=np.float32)
            pose_orientations = np.empty((0, 4), dtype=np.float32)

    return positions, colors, pose_positions, pose_orientations


# Mirrors the `images[]` entry shape `_localize_one_image` produces (see LocalizationImage in the
# dashboard's types.ts) so a reconstruction's own poses and a localization run's estimated poses
# can be viewed/consumed with the same tooling. `path`/`thumbnail_base64` are always null here —
# frame_poses.npz carries no image bytes or filenames, only one pose per registered rig frame.
def _pose_to_localization_image(
    index: int, position: NDArray[np.float32], quaternion_xyzw: NDArray[np.float32]
) -> dict[str, Any]:
    roll, pitch, yaw = Rotation.from_quat(quaternion_xyzw).as_euler("xyz", degrees=True)
    return {
        "index": index,
        "filename": f"frame_{index:04d}",
        "path": None,
        "status": "ok",
        "error": None,
        "position": {"x": float(position[0]), "y": float(position[1]), "z": float(position[2])},
        "quaternion_xyzw": [float(v) for v in quaternion_xyzw],
        "rpy_deg": {"roll": float(roll), "pitch": float(pitch), "yaw": float(yaw)},
        "thumbnail_base64": None,
    }


def _render_point_cloud(
    positions: NDArray[np.float32],
    colors: NDArray[np.uint8],
    output: Path,
    max_points: int | None,
    point_size: float,
    elev: float,
    azim: float,
    radius_percentile: float,
) -> int:
    if max_points is not None and len(positions) > max_points:
        indices = np.random.default_rng(0).choice(len(positions), size=max_points, replace=False)
        positions = positions[indices]
        colors = colors[indices]

    # mplot3d's Axes3D is not fully typed upstream (methods below infer parameter types from
    # untyped defaults, e.g. scatter's `zs: int = 0`), hence the blanket ignores through this block.
    fig = plt.figure(figsize=(10, 10))  # pyright: ignore[reportUnknownMemberType]
    ax = fig.add_subplot(projection="3d")
    ax.scatter(  # pyright: ignore[reportUnknownMemberType]
        positions[:, 0],
        positions[:, 1],
        positions[:, 2],  # pyright: ignore[reportArgumentType]
        c=colors / 255.0,
        s=point_size,  # pyright: ignore[reportArgumentType]
        linewidths=0,
    )
    ax.view_init(elev=elev, azim=azim)  # pyright: ignore[reportUnknownMemberType]
    ax.set_axis_off()  # pyright: ignore[reportUnknownMemberType]
    ax.set_box_aspect((1, 1, 1))  # pyright: ignore[reportUnknownMemberType]

    # Median + percentile radius rather than mean/max: a handful of stray SfM points far from
    # the map body would otherwise blow out the bounding box and shrink everything else to a
    # speck.
    center = np.median(positions, axis=0)
    radius = float(np.percentile(np.linalg.norm(positions - center, axis=1), radius_percentile)) or 1.0
    ax.set_xlim(center[0] - radius, center[0] + radius)  # pyright: ignore[reportUnknownMemberType]
    ax.set_ylim(center[1] - radius, center[1] + radius)  # pyright: ignore[reportUnknownMemberType]
    ax.set_zlim(center[2] - radius, center[2] + radius)  # pyright: ignore[reportUnknownMemberType]

    output.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(pad=0)
    fig.savefig(output, dpi=200)  # pyright: ignore[reportUnknownMemberType]
    plt.close(fig)
    return len(positions)


async def _localize(
    reconstruction_id: UUID,
    images: list[tuple[Path, str, bytes]],
    retrieval_top_k: int,
    ransac_threshold: float,
    use_chunking: bool,
    report_progress: Callable[[int], None] | None = None,
) -> tuple[UUID, list[dict[str, Any]]]:
    async with authenticated_api_client() as api:
        try:
            reconstruction = await api.get_reconstruction(id=reconstruction_id)
            capture_id = reconstruction.capture_session_id
            if capture_id is None:
                raise RuntimeError(f"Reconstruction {reconstruction_id} has no capture session")

            camera_config, axis_convention = await _query_camera(api, reconstruction_id, capture_id)

            map_id = await _get_or_create_localization_map(api, reconstruction_id)

            entries: list[dict[str, Any]] = []
            for index, (path, name, image_bytes) in enumerate(images):
                entry = await _localize_one_image(
                    api,
                    map_id,
                    camera_config,
                    axis_convention,
                    index,
                    path,
                    name,
                    image_bytes,
                    retrieval_top_k,
                    ransac_threshold,
                    use_chunking,
                )
                entries.append(entry)
                if report_progress is not None:
                    report_progress(index + 1)
        except ApiException as exception:
            _fail(exception)
    return capture_id, entries


async def _query_camera(
    api: DefaultApi, reconstruction_id: UUID, capture_id: UUID
) -> tuple[PinholeCameraConfig, AxisConvention]:
    # Query images are assumed to come from the capture's camera. An imported reconstruction
    # (POST /reconstructions/tar) hangs off a stand-in capture session with no tar, so the manifest
    # fetch fails (500 "Download failed", or 404 if the tar lacks manifest.json); fall back to the
    # map's own camera, in the OpenCV convention every sfm_model is written in.
    try:
        manifest_bytes = await api.get_capture_session_manifest_file(id=capture_id)
    except ApiException as exception:
        if cast("int | None", exception.status) not in (404, 500):
            raise
        typer.echo(
            f"Capture {capture_id} has no manifest (imported reconstruction?); using the reconstruction's own camera",
            err=True,
        )
        return _camera_config_from_tar(await _ensure_cached_tar(api, reconstruction_id)), AxisConvention.OPENCV
    manifest = CaptureSessionManifest.model_validate_json(manifest_bytes)
    camera_config = PinholeCameraConfig(**manifest.rigs[0].cameras[0].camera_config.model_dump())
    return camera_config, AxisConvention(manifest.axis_convention.value)


def _camera_config_from_tar(tar_path: Path) -> PinholeCameraConfig:
    with tarfile.open(tar_path) as tar:
        member = tar.extractfile("sfm_model/cameras.txt")
        if member is None:
            raise RuntimeError(f"{tar_path} has no sfm_model/cameras.txt")
        lines = [line.split() for line in member.read().decode().splitlines() if line and not line.startswith("#")]
    if len(lines) != 1 or lines[0][1] != "PINHOLE":
        raise RuntimeError(f"Expected exactly one PINHOLE camera in {tar_path}, got {[line[:2] for line in lines]}")
    _camera_id, _model, width, height, fx, fy, cx, cy = lines[0]
    return PinholeCameraConfig(
        width=int(width),
        height=int(height),
        orientation="TOP_LEFT",
        fx=float(fx),
        fy=float(fy),
        cx=float(cx),
        cy=float(cy),
    )


async def _get_or_create_localization_map(api: DefaultApi, reconstruction_id: UUID) -> UUID:
    try:
        return await api.get_reconstruction_localization_map(id=reconstruction_id)
    except ApiException as exception:
        if cast("int | None", exception.status) != 404:
            raise
        created = await api.create_localization_map(
            LocalizationMapCreate(
                reconstruction_id=reconstruction_id,
                position_x=0.0,
                position_y=0.0,
                position_z=0.0,
                rotation_x=0.0,
                rotation_y=0.0,
                rotation_z=0.0,
                rotation_w=1.0,
                color=0,
            )
        )
        return created.id


async def _localize_one_image(
    api: DefaultApi,
    map_id: UUID,
    camera_config: PinholeCameraConfig,
    axis_convention: AxisConvention,
    index: int,
    image_path: Path,
    image_name: str,
    image_bytes: bytes,
    retrieval_top_k: int,
    ransac_threshold: float,
    use_chunking: bool,
) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "index": index,
        "filename": image_name,
        "path": str(image_path),
        "status": "failed",
        "error": None,
        "position": None,
        "quaternion_xyzw": None,
        "rpy_deg": None,
        "thumbnail_base64": _build_thumbnail_data_uri(image_bytes),
    }

    try:
        # A per-image failure (bad frame, no match) shouldn't abort the whole directory — same
        # rationale as fit_calibration.py's per-timestamp try/except around this same call.
        responses = await api.localize_image(
            map_ids=[map_id],
            camera_config=camera_config,
            axis_convention=axis_convention,
            image=(image_name, image_bytes),
            retrieval_top_k=retrieval_top_k,
            ransac_threshold=ransac_threshold,
            use_chunking=use_chunking,
        )
    except ApiException as exception:
        entry["error"] = str(exception)
        return entry

    if not responses:
        entry["error"] = "No localization match"
        return entry

    # camera_from_map_transform is world-to-camera (extrinsic); invert to get the camera's own
    # position/orientation in map/world coordinates — same convention frame_poses.npz uses, and
    # the same inversion fit_calibration.py does for the calibration corpus.
    best = responses[0]
    translation = best.camera_from_map_transform.translation
    rotation = best.camera_from_map_transform.rotation
    camera_from_map_rotation = Rotation.from_quat([rotation.x, rotation.y, rotation.z, rotation.w]).as_matrix()
    camera_from_map_translation = np.array([translation.x, translation.y, translation.z])
    position = -camera_from_map_rotation.T @ camera_from_map_translation
    world_from_camera = Rotation.from_matrix(camera_from_map_rotation.T)
    quat_xyzw = world_from_camera.as_quat()
    roll, pitch, yaw = world_from_camera.as_euler("xyz", degrees=True)

    entry["status"] = "ok"
    entry["position"] = {"x": float(position[0]), "y": float(position[1]), "z": float(position[2])}
    entry["quaternion_xyzw"] = [float(v) for v in quat_xyzw]
    entry["rpy_deg"] = {"roll": float(roll), "pitch": float(pitch), "yaw": float(yaw)}
    return entry


def _build_thumbnail_data_uri(image_bytes: bytes) -> str:
    image = Image.open(BytesIO(image_bytes)).convert("RGB")
    image.thumbnail(LOCALIZATION_THUMBNAIL_SIZE)
    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=80)
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/jpeg;base64,{encoded}"


def _load_localization_run(run_id: str) -> dict[str, Any]:
    results_path = LOCALIZATIONS_DIR / run_id / "results.json"
    if not results_path.exists():
        typer.echo(f"No localization run found: {run_id}", err=True)
        raise typer.Exit(1)
    result: dict[str, Any] = loads(results_path.read_text())
    return result


def _annotation_font() -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    try:
        return ImageFont.truetype("DejaVuSans-Bold.ttf", 22)
    except OSError:
        return ImageFont.load_default()


def _annotate_pose_image(source_path: Path, image_entry: dict[str, Any]) -> Image.Image:
    image = Image.open(source_path).convert("RGB")
    draw = ImageDraw.Draw(image)
    if image_entry["status"] == "ok":
        position, rpy = image_entry["position"], image_entry["rpy_deg"]
        text = (
            f"XYZ: {position['x']:.3f}, {position['y']:.3f}, {position['z']:.3f}\n"
            f"RPY: {rpy['roll']:.1f}, {rpy['pitch']:.1f}, {rpy['yaw']:.1f}"
        )
    else:
        text = "Localization failed"
    draw.multiline_text((12, 12), text, font=_annotation_font(), fill="white", stroke_width=2, stroke_fill="black")
    return image


async def _run_pipeline(
    tar_name: str,
    tar_bytes: bytes,
    device_type: DeviceType,
    name: str,
    options_json: str | None,
    wait: bool,
    timeout_s: float,
) -> tuple[CaptureSessionRead, ReconstructionReadWithQueue]:
    async with authenticated_api_client() as api:
        try:
            session = await upload_capture_session(api, tar_name, tar_bytes, device_type, name, None)
            reconstruction = await create_reconstruction(api, session.id, _parse_options(options_json), wait, timeout_s)
            return session, reconstruction
        except ApiException as exception:
            _fail(exception)


def _fail(exception: ApiException) -> NoReturn:
    # str(ApiException) is a multi-line dump (status line, every response header, then the body);
    # the useful part is the body's "detail", so surface that and keep the status for context.
    detail: str | None = None
    body = cast("bytes | str | None", getattr(exception, "body", None) or getattr(exception, "data", None))
    if body is not None:
        try:
            parsed = loads(body)
            value = cast("dict[str, object]", parsed).get("detail") if isinstance(parsed, dict) else None
            detail = str(value) if value is not None else None
        except ValueError:
            detail = body.decode(errors="replace") if isinstance(body, bytes) else body
    status = getattr(exception, "status", None)
    typer.echo(f"Request failed ({status}): {detail or exception}".strip(), err=True)
    raise typer.Exit(1)


if __name__ == "__main__":
    app()
