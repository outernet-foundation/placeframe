from __future__ import annotations

from asyncio import run, sleep
from csv import DictReader, DictWriter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from io import BytesIO, StringIO
from itertools import product
from json import load as json_load
from pathlib import Path
from tarfile import TarInfo, open as tar_open
from typing import Annotated
from uuid import UUID

from httpx import AsyncClient
from numpy import array, degrees, float64
from numpy.linalg import norm
from numpy.typing import NDArray  # noqa: TID251 — Phase T piece 3 follow-up migration
from pytransform3d.transformations import (
    concat,
    exponential_coordinates_from_transform,
    invert_transform,
    transform_from,
)
from scipy.spatial.transform import Rotation
from typer import Exit, Option, Typer, echo

from placeframe_api_client import (
    ApiClient,
    AxisConvention,
    CaptureSessionCreate,
    Configuration,
    DefaultApi,
    DeviceType,
    LocalizationMapCreate,
    OrchestrationStatus,
    PinholeCameraConfig,
    ReconstructionCreate,
    ReconstructionCreateWithOptions,
    ReconstructionOptions,
)

from .e2e_results import E2EResults, LocalizationResult, ReconMetrics, ReconstructionResult

app = Typer()

REPO_ROOT = Path(__file__).resolve().parents[3]
CAPTURES_DIR = REPO_ROOT.parent / "placeframe-test-captures"

DEVICE_DIR_MAP: dict[str, DeviceType] = {
    "zed": DeviceType.ZED,
    "arfoundation": DeviceType.ARFOUNDATION,
}

WITHHOLD_INTERVAL = 9
POLL_INTERVAL_S = 10

PB_LOW = ReconstructionOptions(
    neighbors_count=8,
    ransac_max_error=1.0,
    ransac_min_inlier_ratio=0.08,
    triangulation_minimum_angle=1.5,
    use_prior_position=False,
    bundle_adjustment_refine_focal_length=False,
    bundle_adjustment_refine_principal_point=False,
    bundle_adjustment_refine_additional_params=False,
    mapper_filter_max_reprojection_error=1.0,
    triangulation_complete_max_reprojection_error=2.0,
)
PB_HIGH = ReconstructionOptions(
    neighbors_count=20,
    ransac_max_error=4.0,
    ransac_min_inlier_ratio=0.25,
    triangulation_minimum_angle=5.0,
    use_prior_position=True,
    bundle_adjustment_refine_focal_length=True,
    bundle_adjustment_refine_principal_point=True,
    bundle_adjustment_refine_additional_params=True,
    mapper_filter_max_reprojection_error=4.0,
    triangulation_complete_max_reprojection_error=6.0,
)
PB_FACTORS = [
    f for f in ReconstructionOptions.model_fields if f != "additional_properties" and getattr(PB_LOW, f) is not None
]
PB_SEED = [+1, +1, +1, +1, -1, +1, -1, +1, +1, -1]

LOC_RETRIEVAL_TOP_K = [3, 5, 10]
LOC_RANSAC_THRESHOLD = [6.0, 12.0, 24.0]


# --- Internal dataclasses ---


@dataclass
class CaptureInfo:
    location: str
    device_dir: str
    device_type: DeviceType
    tar_path: Path
    axis_convention: AxisConvention
    camera_configs: dict[str, PinholeCameraConfig]
    modified_tar_bytes: bytes = b""
    withheld_frames: list[WithheldFrame] = field(default_factory=list)


@dataclass
class WithheldFrame:
    timestamp: str
    image_bytes: bytes
    camera_config: PinholeCameraConfig
    # world_from_rig pose from frames.csv, in the capture's native axis convention.
    # The localizer returns its estimate in that same convention (it converts back from OpenCV at
    # the API boundary), so direct comparison is correct without a basis change.
    truth_translation: NDArray[float64]
    truth_rotation_quat_xyzw: NDArray[float64]


# --- Helpers (called from multiple sites or to reduce nesting) ---


def _prepare_capture(capture: CaptureInfo) -> None:
    with tar_open(capture.tar_path, "r") as tf:
        frames_f = tf.extractfile("rig0/frames.csv")
        assert frames_f is not None
        all_rows = list(DictReader(StringIO(frames_f.read().decode("utf-8"))))

    withheld_indices = {i for i in range(len(all_rows)) if (i + 1) % WITHHOLD_INTERVAL == 0}

    withheld_truth_by_timestamp: dict[str, tuple[NDArray[float64], NDArray[float64]]] = {}
    for i in sorted(withheld_indices):
        row = all_rows[i]
        withheld_truth_by_timestamp[row["timestamp"]] = (
            array([float(row["tx"]), float(row["ty"]), float(row["tz"])], dtype=float64),
            array([float(row["qx"]), float(row["qy"]), float(row["qz"]), float(row["qw"])], dtype=float64),
        )

    withheld_image_paths: set[str] = set()
    for i in sorted(withheld_indices):
        ts = all_rows[i]["timestamp"]
        withheld_image_paths.add(f"rig0/camera0/{ts}.jpg")
        if capture.device_type == DeviceType.ZED:
            withheld_image_paths.add(f"rig0/camera1/{ts}.jpg")

    csv_out = StringIO()
    writer = DictWriter(csv_out, fieldnames=list(all_rows[0].keys()) if all_rows else [])
    writer.writeheader()
    writer.writerows(row for i, row in enumerate(all_rows) if i not in withheld_indices)
    modified_csv_bytes = csv_out.getvalue().encode("utf-8")

    withheld_frames: list[WithheldFrame] = []

    tar_buffer = BytesIO()
    with tar_open(capture.tar_path, "r") as src, tar_open(fileobj=tar_buffer, mode="w") as dst:
        for member in src.getmembers():
            if member.name == "rig0/frames.csv":
                info = TarInfo(name="rig0/frames.csv")
                info.size = len(modified_csv_bytes)
                dst.addfile(info, BytesIO(modified_csv_bytes))
                continue
            if member.name in withheld_image_paths and member.name.startswith("rig0/camera0/"):
                f = src.extractfile(member)
                assert f is not None
                timestamp = Path(member.name).stem
                truth_translation, truth_rotation = withheld_truth_by_timestamp[timestamp]
                withheld_frames.append(
                    WithheldFrame(
                        timestamp=timestamp,
                        image_bytes=f.read(),
                        camera_config=capture.camera_configs["camera0"],
                        truth_translation=truth_translation,
                        truth_rotation_quat_xyzw=truth_rotation,
                    )
                )
            if member.name in withheld_image_paths:
                continue
            if member.isfile():
                f = src.extractfile(member)
                assert f is not None
                dst.addfile(member, f)
                continue
            dst.addfile(member)

    capture.modified_tar_bytes = tar_buffer.getvalue()
    capture.withheld_frames = withheld_frames
    echo(
        f"  {capture.location}/{capture.device_dir}: "
        f"{len(all_rows)} frames, withheld {len(withheld_indices)}, "
        f"{len(withheld_frames)} query images"
    )


async def _localize_and_label(
    api: DefaultApi,
    recon: ReconstructionResult,
    loc_map_id: str,
    reconstruction_id: str,
    qcap: CaptureInfo,
    qframe: WithheldFrame,
    top_k: int | None,
    thresh: float | None,
) -> LocalizationResult:
    loc_result = LocalizationResult(
        location=recon.location,
        recon_device_type=recon.device_type,
        recon_capture_name=recon.capture_name,
        recon_config_idx=recon.config_idx,
        reconstruction_id=reconstruction_id,
        query_device_type=qcap.device_type.value,
        query_capture_name=qcap.device_dir,
        query_frame_timestamp=qframe.timestamp,
        query_image_diagonal_px=float((qframe.camera_config.width**2 + qframe.camera_config.height**2) ** 0.5),
        is_cross_device=qcap.device_type.value != recon.device_type,
        retrieval_top_k=top_k,
        ransac_threshold=thresh,
        succeeded=False,
    )

    try:
        loc_resp = await api.localize_image(
            map_ids=[UUID(loc_map_id)],
            camera_config=qframe.camera_config,
            axis_convention=qcap.axis_convention,
            retrieval_top_k=top_k,
            ransac_threshold=thresh,
            image=("query.jpg", qframe.image_bytes),
        )
    except Exception as e:
        echo(f"    Localization error: {e}")
        return loc_result

    if not loc_resp:
        return loc_result

    best = loc_resp[0].metrics
    loc_result.succeeded = True
    loc_result.inlier_ratio = best.inlier_ratio
    loc_result.reproj_error_median = best.reprojection_error_median
    loc_result.num_inliers = best.num_inliers
    loc_result.num_correspondences = best.num_correspondences
    loc_result.num_matches = best.num_matches
    loc_result.inlier_coverage = best.inlier_coverage
    loc_result.pnp_covariance = [[float(v) for v in row] for row in best.pnp_covariance]

    # camera_from_map is the localizer's camera-from-world pose (the reconstructor's
    # Umeyama alignment puts the map in truth-world frame). Truth from frames.csv is
    # world_from_rig with the ref sensor at identity offset, so it doubles as
    # world_from_camera. Both are in the capture's native axis convention — the API
    # converts back from OpenCV at the boundary based on the query's `axis_convention`.
    cam_from_map = loc_resp[0].camera_from_map_transform
    cam_from_map_translation = array(
        [cam_from_map.translation.x, cam_from_map.translation.y, cam_from_map.translation.z],
        dtype=float64,
    )
    cam_from_map_rotation = Rotation.from_quat([
        cam_from_map.rotation.x,
        cam_from_map.rotation.y,
        cam_from_map.rotation.z,
        cam_from_map.rotation.w,
    ]).as_matrix()
    estimated_camera_position = -cam_from_map_rotation.T @ cam_from_map_translation
    estimated_world_from_camera = cam_from_map_rotation.T
    truth_world_from_camera = Rotation.from_quat(qframe.truth_rotation_quat_xyzw).as_matrix()
    relative_rotation = Rotation.from_matrix(truth_world_from_camera @ estimated_world_from_camera.T)

    loc_result.err_t_m = float(norm(qframe.truth_translation - estimated_camera_position))
    loc_result.err_r_deg = float(degrees(relative_rotation.magnitude()))

    # SE(3) residual log(P_truth · P_estimated⁻¹) as a 6-vector for the Σ_meas α/β fit.
    truth_world_from_camera_4x4 = transform_from(truth_world_from_camera, qframe.truth_translation)
    estimated_world_from_camera_4x4 = transform_from(estimated_world_from_camera, estimated_camera_position)
    residual_transform = concat(
        truth_world_from_camera_4x4, invert_transform(estimated_world_from_camera_4x4, check=False)
    )
    loc_result.se3_residual = exponential_coordinates_from_transform(residual_transform).tolist()

    return loc_result


async def _run_reconstruction(
    api: DefaultApi,
    capture: CaptureInfo,
    capture_session_id: UUID,
    options: ReconstructionOptions | None,
    config_idx: int,
) -> ReconstructionResult:
    recon = await api.create_reconstruction(
        ReconstructionCreateWithOptions(
            create=ReconstructionCreate(capture_session_id=capture_session_id),
            options=options,
        )
    )
    echo(f"  [{config_idx:02d}] {capture.location}/{capture.device_dir} → {recon.id}")

    while True:
        await sleep(POLL_INTERVAL_S)
        status = await api.get_reconstruction_status(id=recon.id)
        if status == OrchestrationStatus.SUCCEEDED:
            break
        if status in (OrchestrationStatus.FAILED, OrchestrationStatus.CANCELLED):
            echo(f"    {status.value}")
            return ReconstructionResult(
                location=capture.location,
                device_type=capture.device_type.value,
                capture_name=capture.device_dir,
                config_idx=config_idx,
                options=options.to_dict() if options else None,
                reconstruction_id=str(recon.id),
                succeeded=False,
            )

    m = (await api.get_reconstruction_manifest(id=recon.id)).metrics
    recon_read = await api.get_reconstruction(id=recon.id)

    loc_map = await api.create_localization_map(
        LocalizationMapCreate(
            reconstruction_id=recon.id,
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
    echo(f"    Succeeded, map {loc_map.id}, {m.registered_images}/{m.total_images} images")
    return ReconstructionResult(
        location=capture.location,
        device_type=capture.device_type.value,
        capture_name=capture.device_dir,
        config_idx=config_idx,
        options=options.to_dict() if options else None,
        reconstruction_id=str(recon.id),
        succeeded=True,
        metrics=ReconMetrics(
            total_images=m.total_images,
            registered_images=m.registered_images,
            registration_rate=m.registration_rate,
            num_3d_points=m.num_3d_points,
            reproj_error_50th=m.reprojection_pixel_error_50th_percentile,
            reproj_error_90th=m.reprojection_pixel_error_90th_percentile,
            map_image_count=m.map_image_count,
            map_point_count=m.map_point_count,
            map_avg_track_length=m.map_avg_track_length,
            map_bounding_volume_m3=m.map_bounding_volume_m3,
            map_viewpoint_diversity=m.map_viewpoint_diversity,
        ),
        loc_map_id=str(loc_map.id),
        is_indoor=recon_read.is_indoor,
        truth_alignment_rms_residual_m=m.truth_alignment_rms_residual_m,
        truth_alignment_max_residual_m=m.truth_alignment_max_residual_m,
    )


# --- Main orchestration ---


async def _run(tar_paths: list[Path], single_config: bool) -> E2EResults:
    results = E2EResults(
        run_timestamp=datetime.now(timezone.utc).isoformat(),
        reconstructions=[],
        localizations=[],
    )

    public_domain: str | None = None
    for line in (REPO_ROOT / ".env").read_text().splitlines():
        stripped = line.strip()
        if stripped.startswith("PUBLIC_DOMAIN=") and not stripped.startswith("#"):
            public_domain = stripped.split("=", 1)[1].strip()
            break
    if public_domain is None:
        raise RuntimeError("PUBLIC_DOMAIN not found in .env")

    echo(f"Using API at https://{public_domain}")
    echo("Authenticating...")

    async with AsyncClient(verify=False) as http:  # noqa: S501
        resp = await http.post(
            f"https://{public_domain}/auth/realms/placeframe-dev/protocol/openid-connect/token",
            data={
                "grant_type": "password",
                "client_id": "placeframe-api",
                "username": "user",
                "password": "password",
            },
        )
        resp.raise_for_status()

    api_config = Configuration(
        host=f"https://{public_domain}",
        access_token=resp.json()["access_token"],
        ssl_ca_cert=False,  # type: ignore[arg-type]
    )

    # Phase 1: Discover captures
    echo("\n=== Phase 1: Discovering captures ===")
    captures: list[CaptureInfo] = []
    for tar_path in tar_paths:
        device_dir = tar_path.parent
        location_dir = device_dir.parent
        device_type = DEVICE_DIR_MAP.get(device_dir.name.lower())
        if device_type is None:
            echo(f"  Skipping unknown device dir: {device_dir.name}")
            continue

        with tar_open(tar_path, "r") as tf:
            manifest_f = tf.extractfile("manifest.json")
            assert manifest_f is not None
            manifest_data = json_load(manifest_f)

        camera_configs: dict[str, PinholeCameraConfig] = {}
        for cam in (c for rig in manifest_data["rigs"] for c in rig["cameras"]):
            cc = cam["camera_config"]
            camera_configs[cam["id"]] = PinholeCameraConfig(
                width=cc["width"],
                height=cc["height"],
                orientation=cc["orientation"],
                fx=cc["fx"],
                fy=cc["fy"],
                cx=cc["cx"],
                cy=cc["cy"],
            )

        captures.append(
            CaptureInfo(
                location=location_dir.name,
                device_dir=device_dir.name,
                device_type=device_type,
                tar_path=tar_path,
                axis_convention=AxisConvention(manifest_data["axis_convention"]),
                camera_configs=camera_configs,
            )
        )
        echo(f"  Found: {location_dir.name}/{device_dir.name} ({device_type.value})")

    if not captures:
        echo("No captures found!")
        raise Exit(1)
    echo(f"Found {len(captures)} captures")

    # Phase 2: Prepare captures (withhold frames)
    echo("\n=== Phase 2: Preparing captures ===")
    for capture in captures:
        _prepare_capture(capture)

    # Phase 3: Upload captures
    echo("\n=== Phase 3: Uploading captures ===")
    session_ids: dict[int, UUID] = {}
    async with ApiClient(api_config) as api_client:
        api = DefaultApi(api_client)
        for ci, capture in enumerate(captures):
            session = await api.create_capture_session(
                CaptureSessionCreate(
                    device_type=capture.device_type,
                    name=f"e2e-{capture.location}-{capture.device_dir}",
                )
            )
            session_ids[ci] = session.id
            await api.upload_capture_session_tar(id=session.id, file=("capture.tar", capture.modified_tar_bytes))
            echo(f"  Uploaded {capture.location}/{capture.device_dir} → {session.id}")

    # Phase 4: Plackett-Burman screening — rotate seed row to generate 15 configs + all-low + baseline.
    # In single-config mode, short-circuit to the server-default baseline only (one cell per capture).
    configs: list[ReconstructionOptions | None] = [None]
    if not single_config:
        row = list(PB_SEED)
        for _ in range(len(PB_SEED) + 5):
            configs.append(
                ReconstructionOptions(**{f: getattr(PB_HIGH if s == 1 else PB_LOW, f) for f, s in zip(PB_FACTORS, row)})
            )
            row = [row[-1], *row[:-1]]
        configs.append(ReconstructionOptions(**{f: getattr(PB_LOW, f) for f in PB_FACTORS}))
    echo(f"=== Phase 4: {len(configs)} experiment configs (1 baseline + {len(configs) - 1} Plackett-Burman) ===")

    # Phase 5: Run reconstructions
    recon_tasks = [(ci, opt, cap_i, cap) for ci, opt in enumerate(configs) for cap_i, cap in enumerate(captures)]
    echo(f"\n=== Phase 5: Running {len(recon_tasks)} reconstructions ===")

    async with ApiClient(api_config) as api_client:
        api = DefaultApi(api_client)
        for config_idx, recon_options, cap_idx, capture in recon_tasks:
            results.reconstructions.append(
                await _run_reconstruction(api, capture, session_ids[cap_idx], recon_options, config_idx)
            )

    succeeded = [r for r in results.reconstructions if r.succeeded]
    echo(f"\n{len(succeeded)}/{len(results.reconstructions)} reconstructions succeeded")

    # Phase 6: Cross-device localization
    captures_by_location: dict[str, list[CaptureInfo]] = {}
    for cap in captures:
        captures_by_location.setdefault(cap.location, []).append(cap)

    loc_param_grid: list[tuple[int | None, float | None]] = (
        [(None, None)] if single_config else list(product(LOC_RETRIEVAL_TOP_K, LOC_RANSAC_THRESHOLD))
    )
    loc_tasks = [
        (recon, recon.loc_map_id, recon.reconstruction_id, qcap, qframe, top_k, thresh)
        for recon in succeeded
        if recon.loc_map_id is not None and recon.reconstruction_id is not None
        for qcap in captures_by_location.get(recon.location, [])
        for qframe in qcap.withheld_frames
        for top_k, thresh in loc_param_grid
    ]
    echo(f"\n=== Phase 6: Running {len(loc_tasks)} localizations ===")

    async with ApiClient(api_config) as api_client:
        api = DefaultApi(api_client)
        for i, (recon, loc_map_id, reconstruction_id, qcap, qframe, top_k, thresh) in enumerate(loc_tasks):
            if (i + 1) % 100 == 0:
                echo(f"  Localization {i + 1}/{len(loc_tasks)}...")
            results.localizations.append(
                await _localize_and_label(api, recon, loc_map_id, reconstruction_id, qcap, qframe, top_k, thresh)
            )

    echo(f"\nReconstructions: {len(succeeded)}/{len(results.reconstructions)} succeeded")
    echo(
        f"Localizations: {sum(1 for loc in results.localizations if loc.succeeded)}/{len(results.localizations)} succeeded"
    )
    return results


@app.command()
def main(
    captures_dir: Annotated[Path, Option(help="Directory containing test captures")] = CAPTURES_DIR,
    output: Annotated[Path, Option(help="Path for JSON results file")] = REPO_ROOT / "e2e-results.json",
    single_config: Annotated[
        bool,
        Option(
            "--single-config",
            help="Run a single server-default reconstruction and localization cell per capture (skips the parameter cross-product). Use to produce starter calibration rows from a small corpus.",
        ),
    ] = False,
) -> None:
    results = run(_run(sorted(captures_dir.glob("*/*/capture.tar")), single_config=single_config))
    output.write_text(results.model_dump_json(indent=2))
    echo(f"Results written to {output}")
