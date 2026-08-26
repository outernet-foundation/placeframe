from __future__ import annotations

import base64
import csv
import sys
import tarfile
from asyncio import run, sleep
from collections.abc import Callable
from datetime import datetime, timezone
from io import BytesIO
from json import dumps, loads
from pathlib import Path
from struct import pack
from typing import Annotated, Any, NoReturn, cast
from uuid import UUID, uuid4

import matplotlib as mpl
import numpy as np
import typer
from core.capture_session_manifest import CaptureSessionManifest
from core.localization_metrics import RANSAC_THRESHOLD_DEFAULT, RETRIEVAL_TOP_K_DEFAULT
from numpy.typing import NDArray  # noqa: TID251 -- one-off visualizer, not worth shape-branding
from PIL import Image, ImageDraw, ImageFont
from scipy.spatial.transform import Rotation

mpl.use("Agg")
from matplotlib import pyplot as plt  # noqa: E402 -- backend must be selected before pyplot import

from placeframe_api_client import (
    ApiException,
    AxisConvention,
    CaptureSessionRead,
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


def _reconstruction_to_dict(reconstruction: ReconstructionReadWithQueue) -> dict[str, Any]:
    metrics = _metrics(reconstruction)
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
        "cached_tar_path": str(tar_path) if tar_path.exists() else None,
        "cached_png_path": str(png_path) if png_path.exists() else None,
    }


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
) -> None:
    rows = sorted(run(_list_reconstructions()), key=lambda r: r.created_at, reverse=True)
    if json_output:
        typer.echo(dumps([_reconstruction_to_dict(r) for r in rows]))
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


@app.command()
def upload(
    tar_path: Annotated[Path, typer.Argument(help="Path to the capture session .tar")],
    device_type: Annotated[DeviceType, typer.Option(help="Device that produced the capture")] = DeviceType.ZED,
    name: Annotated[str | None, typer.Option(help="Capture session name; defaults to the tar's filename stem")] = None,
    id: Annotated[UUID | None, typer.Option(help="Capture session id; server assigns one if omitted")] = None,
) -> None:
    session = run(_upload(tar_path.name, tar_path.read_bytes(), device_type, name or tar_path.stem, id))
    typer.echo(f"Uploaded capture session {session.id} ({session.name}, {session.size_bytes} bytes)")


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

    capture_id, entries = run(_localize(reconstruction_id, images, retrieval_top_k, ransac_threshold, report_progress))
    result: dict[str, Any] = {
        "run_id": resolved_run_id,
        "reconstruction_id": str(reconstruction_id),
        "capture_session_id": str(capture_id),
        "image_dir": str(image_dir.resolve()),
        "created_at": datetime.now(timezone.utc).isoformat(),
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
    for image in result["images"]:
        source_path = Path(image["path"])
        if not source_path.exists():
            continue
        annotated = _annotate_pose_image(source_path, image)
        annotated.save(output_dir / source_path.name)
        saved += 1
    if json_output:
        typer.echo(dumps({"output_dir": str(output_dir), "count": saved}))
        return
    typer.echo(f"Saved {saved} annotated images for run {run_id} to {output_dir}")


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


async def _reconstruct(
    capture_id: UUID, options: ReconstructionOptions, wait: bool, timeout_s: float
) -> ReconstructionReadWithQueue:
    async with authenticated_api_client() as api:
        try:
            return await create_reconstruction(api, capture_id, options, wait, timeout_s)
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
    report_progress: Callable[[int], None] | None = None,
) -> tuple[UUID, list[dict[str, Any]]]:
    async with authenticated_api_client() as api:
        try:
            reconstruction = await api.get_reconstruction(id=reconstruction_id)
            capture_id = reconstruction.capture_session_id
            if capture_id is None:
                raise RuntimeError(f"Reconstruction {reconstruction_id} has no capture session")

            manifest_bytes = await api.get_capture_session_manifest_file(id=capture_id)
            manifest = CaptureSessionManifest.model_validate_json(manifest_bytes)
            camera_config = PinholeCameraConfig(**manifest.rigs[0].cameras[0].camera_config.model_dump())
            axis_convention = AxisConvention(manifest.axis_convention.value)

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
                )
                entries.append(entry)
                if report_progress is not None:
                    report_progress(index + 1)
        except ApiException as exception:
            _fail(exception)
    return capture_id, entries


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
    typer.echo(f"Request failed: {exception}", err=True)
    raise typer.Exit(1)


if __name__ == "__main__":
    app()
