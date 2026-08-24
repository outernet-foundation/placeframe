from __future__ import annotations

import tarfile
from asyncio import run, sleep
from io import BytesIO
from json import dumps, loads
from pathlib import Path
from typing import Annotated, Any, NoReturn
from uuid import UUID

import matplotlib as mpl
import numpy as np
import typer
from numpy.typing import NDArray  # noqa: TID251 -- one-off visualizer, not worth shape-branding

mpl.use("Agg")
from matplotlib import pyplot as plt  # noqa: E402 -- backend must be selected before pyplot import

from placeframe_api_client import (
    ApiException,
    CaptureSessionRead,
    DefaultApi,
    DeviceType,
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

# Local cache for reconstruction exports and their rendered point clouds, keyed by reconstruction
# id. Populated once a reconstruction succeeds (see _ensure_cached_tar) so the dashboard's
# Visualize tab doesn't re-download a multi-hundred-MB tar on every "Create PNG" click.
REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = REPO_ROOT / "data"
RECONSTRUCTIONS_DIR = DATA_DIR / "reconstructions"

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


async def _fetch_point_cloud(
    reconstruction_id: UUID,
) -> tuple[NDArray[np.float32], NDArray[np.uint8]]:
    cached = _cached_tar_path(reconstruction_id)
    if not cached.exists():
        async with authenticated_api_client() as api:
            try:
                await _ensure_cached_tar(api, reconstruction_id)
            except ApiException as exception:
                _fail(exception)
    return _load_point_cloud(cached.read_bytes())


def _load_point_cloud(tar_bytes: bytes) -> tuple[NDArray[np.float32], NDArray[np.uint8]]:
    with tarfile.open(fileobj=BytesIO(tar_bytes)) as tar:
        member = tar.extractfile(POINT_CLOUD_TAR_MEMBER)
        if member is None:
            raise RuntimeError(
                f"No {POINT_CLOUD_TAR_MEMBER} in the reconstruction tar — the reconstruction may not have succeeded"
            )
        data = np.load(BytesIO(member.read()))
    return data["positions"], data["colors"]


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
