from __future__ import annotations

import json
import os
import subprocess
from asyncio import run, sleep
from collections.abc import Callable
from csv import DictReader
from dataclasses import dataclass
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
from typing import Annotated, Any, cast
from uuid import UUID

from core.calibration import FEATURE_NAMES, SCHEMA_VERSION, CalibrationArtifact, Features, ToleranceModel
from httpx import AsyncClient
from numpy import asarray, degrees, eye, float64, inf, log1p, ndarray, unique
from numpy.linalg import LinAlgError, norm
from numpy.typing import NDArray  # noqa: TID251 — Phase T piece 3 follow-up migration
from pydantic import BaseModel
from pytransform3d.transformations import (
    concat,
    exponential_coordinates_from_transform,
    invert_transform,
    transform_from,
)
from scipy.optimize import minimize
from scipy.spatial.transform import Rotation
from scipy.stats import multivariate_normal
from sklearn.isotonic import IsotonicRegression  # type: ignore[import-untyped]
from sklearn.linear_model import LogisticRegression  # type: ignore[import-untyped]
from typer import Exit, Option, Typer, echo

from placeframe_api_client import (
    ApiClient,
    ApiException,
    AxisConvention,
    Configuration,
    DefaultApi,
    LocalizationEvaluationCreate,
    LocalizationMapCreate,
    OrchestrationStatus,
    PinholeCameraConfig,
    ReconstructionCreate,
    ReconstructionCreateWithOptions,
    ReconstructionOptions,
)
from placeframe_localizer_client import (
    ApiClient as LocalizerApiClient,
    Configuration as LocalizerConfiguration,
    DefaultApi as LocalizerDefaultApi,
)

from .held_out_selection import HeldOutSelectionOptions, get_selector

app = Typer()

REPO_ROOT = Path(__file__).resolve().parents[3]

# Algorithm 1 success thresholds (intent doc Algorithm 1 step 4).
TIGHT_T_M = 0.05
TIGHT_R_DEG = 1.0
LOOSE_T_M = 0.30
LOOSE_R_DEG = 5.0

# scipy.optimize bounds and seed for the (alpha, beta) Σ_meas fit.
_SIGMA_MEAS_INITIAL = (1.0, 1.0e-4)
_SIGMA_MEAS_BOUNDS = ((1.0e-6, 1.0e6), (0.0, 1.0e3))
_IDENTITY_6 = eye(6, dtype=float64)

# Hand-set gate thresholds written into the artifact. The starter's tight model is degenerate
# (no positive class to fit on), so tight_min=0.0 no-ops the tight gate; loose_min=0.25 sits
# in the empirical gap between the starter fit's loose=0 and loose=0.5 clusters. The corpus
# run is expected to derive both from the success-cluster distribution; that wiring is a
# deferred Phase 3 follow-up.
STARTER_LOOSE_MIN = 0.25
STARTER_TIGHT_MIN = 0.0

# Reconstruction polling.
RECONSTRUCTION_POLL_S = 5
RECONSTRUCTION_TIMEOUT_S = 1800


class CorpusRow(BaseModel):
    succeeded: bool
    inlier_ratio: float
    reproj_error_median: float
    num_inliers: int
    num_correspondences: int
    num_matches: int
    inlier_coverage: float
    pnp_covariance: list[list[float]] | None
    se3_residual: list[float] | None
    err_t_m: float | None
    err_r_deg: float | None
    query_image_diagonal_px: float
    map_image_count: int
    map_point_count: int
    map_avg_track_length: float
    map_bounding_volume_m3: float
    map_viewpoint_diversity: float
    is_indoor: bool


@dataclass
class _TruthPose:
    translation: NDArray[float64]
    rotation_quat_xyzw: NDArray[float64]


@app.command()
def main(
    captures: Annotated[
        list[UUID] | None,
        Option(
            "--captures", help="Capture session ids. Selects held-out frames and builds reconstructions per capture."
        ),
    ] = None,
    reconstructions: Annotated[
        list[UUID] | None,
        Option(
            "--reconstructions",
            help="Reconstruction ids. Skips reconstruction; uses pre-built reconstructions whose held_out_frame_timestamps are already set.",
        ),
    ] = None,
    pipeline_version: Annotated[
        str | None,
        Option(
            "--pipeline-version",
            help="Override the localizer's git SHA. Default is auto-detected from the localizer's /version endpoint.",
        ),
    ] = None,
    no_fit: Annotated[
        bool,
        Option("--no-fit", help="Populate localization_evaluations cache without writing the calibration artifact."),
    ] = False,
    held_out_count: Annotated[int, Option("--held-out-count", help="Target held-out frame count per capture.")] = 100,
    held_out_selector_name: Annotated[
        str, Option("--held-out-selector", help="Selector name. See scripts/held_out_selection.py registry.")
    ] = "stride",
    output: Annotated[Path, Option("--output", help="Path to write the calibration artifact.")] = (
        REPO_ROOT / "config" / "calibration" / "global.json"
    ),
) -> None:
    if not captures and not reconstructions:
        echo("Pass --captures <id>... or --reconstructions <id>...")
        raise Exit(1)
    if captures and reconstructions:
        echo("--captures and --reconstructions are mutually exclusive")
        raise Exit(1)

    run(
        _run(
            capture_ids=captures or [],
            reconstruction_ids=reconstructions or [],
            pipeline_version_override=pipeline_version,
            no_fit=no_fit,
            held_out_count=held_out_count,
            held_out_selector_name=held_out_selector_name,
            output=output,
        )
    )


async def _run(
    *,
    capture_ids: list[UUID],
    reconstruction_ids: list[UUID],
    pipeline_version_override: str | None,
    no_fit: bool,
    held_out_count: int,
    held_out_selector_name: str,
    output: Path,
) -> None:
    api_config = await _build_api_config()

    if pipeline_version_override is not None:
        pipeline_version = pipeline_version_override
        echo(f"Using --pipeline-version override: {pipeline_version}")
    else:
        pipeline_version = await _fetch_localizer_version()
        echo(f"Auto-detected pipeline_version from localizer /version: {pipeline_version}")

    selector = get_selector(held_out_selector_name)
    selector_options = HeldOutSelectionOptions(target_count=held_out_count)

    async with ApiClient(api_config) as api_client:
        # The generated openapi-generator client emits empty `_auth_settings` on every method,
        # so `Configuration(access_token=...)` is never consumed and requests go out without
        # an Authorization header. Until the codegen is fixed, inject the token as a default
        # header so all calls authenticate. The cast wraps an untyped generated-client method.
        cast(Callable[[str, str], None], api_client.set_default_header)(
            "Authorization", f"Bearer {api_config.access_token}"
        )
        api = DefaultApi(api_client)

        if capture_ids:
            resolved: list[UUID] = []
            for capture_id in capture_ids:
                frames_csv_bytes = await api.get_capture_session_frames_csv(id=capture_id)
                held_out_ts = selector(frames_csv_bytes.decode("utf-8"), selector_options)
                requested = ReconstructionOptions(held_out_frame_timestamps=held_out_ts)
                recon_id = await match_or_create_reconstruction(api, capture_id, requested)
                resolved.append(recon_id)
                echo(f"Capture {capture_id}: held-out {len(held_out_ts)} frames, reconstruction {recon_id}")
            reconstruction_ids = resolved

        for recon_id in reconstruction_ids:
            await _populate_evaluations(api, recon_id, pipeline_version)

        if no_fit:
            echo("--no-fit: cache populated, skipping fit")
            return

        corpus = await _read_corpus(api, reconstruction_ids, pipeline_version)

    artifact = fit_calibration_from_corpus(corpus, pipeline_version=pipeline_version)
    output.parent.mkdir(parents=True, exist_ok=True)
    artifact.write(output)

    echo(f"\nPipeline version:   {artifact.pipeline_version}")
    echo(f"Sample count:       {artifact.sample_count}")
    echo(f"sigma_meas alpha:   {artifact.sigma_meas_alpha:.6g}")
    echo(f"sigma_meas beta:    {artifact.sigma_meas_beta:.6g}")
    echo(f"\nArtifact written to {output}")


async def match_or_create_reconstruction(
    api: DefaultApi, capture_id: UUID, requested_options: ReconstructionOptions
) -> UUID:
    # Match on the FULL ReconstructionOptions blob so calibrations are fit against one
    # pipeline configuration only — mixing reconstructions built with different options
    # into one corpus contaminates the fit. Pydantic equality compares every field
    # including held_out_frame_timestamps, so a row built with a different held-out set
    # is correctly treated as a different reconstruction.
    #
    # Ideas for later:
    #   - Options-hash column on reconstructions to avoid the per-candidate manifest fetch.
    #   - Opt-in --match-options-on=held_out_only flag for development workflows where
    #     the operator knows other options are immaterial (e.g. iterating on selector
    #     logic against a fixed parameter set).
    candidate_ids = await api.get_capture_session_reconstructions(id=capture_id)
    for candidate_id in candidate_ids:
        manifest = await api.get_reconstruction_manifest(id=candidate_id)
        if manifest.status != "succeeded":
            continue
        if manifest.options == requested_options:
            return candidate_id

    created = await api.create_reconstruction(
        ReconstructionCreateWithOptions(
            create=ReconstructionCreate(capture_session_id=capture_id),
            options=requested_options,
        )
    )
    await _wait_for_reconstruction(api, created.id)
    return created.id


async def _wait_for_reconstruction(api: DefaultApi, reconstruction_id: UUID) -> None:
    deadline = RECONSTRUCTION_TIMEOUT_S
    elapsed = 0
    while True:
        await sleep(RECONSTRUCTION_POLL_S)
        elapsed += RECONSTRUCTION_POLL_S
        status = await api.get_reconstruction_status(id=reconstruction_id)
        if status == OrchestrationStatus.SUCCEEDED:
            return
        if status in (OrchestrationStatus.FAILED, OrchestrationStatus.CANCELLED):
            raise RuntimeError(f"Reconstruction {reconstruction_id} ended in {status.value}")
        if elapsed >= deadline:
            raise RuntimeError(f"Reconstruction {reconstruction_id} did not succeed within {deadline}s")


async def _populate_evaluations(api: DefaultApi, reconstruction_id: UUID, pipeline_version: str) -> None:
    manifest = await api.get_reconstruction_manifest(id=reconstruction_id)
    held_out_ts = manifest.options.held_out_frame_timestamps or []
    if not held_out_ts:
        echo(f"  Reconstruction {reconstruction_id} has no held-out frames; skipping localization step")
        return

    capture_id = UUID(manifest.capture_id)
    cached = await api.list_localization_evaluations(
        reconstruction_id=reconstruction_id, pipeline_version=pipeline_version
    )
    cached_timestamps = {row.frame_timestamp for row in cached}

    pending = [ts for ts in held_out_ts if ts not in cached_timestamps]
    if not pending:
        echo(f"  Reconstruction {reconstruction_id}: all {len(held_out_ts)} held-out frames already cached")
        return

    echo(
        f"  Reconstruction {reconstruction_id}: localizing {len(pending)} held-out frames ({len(cached_timestamps)} cached)"
    )

    capture_manifest_bytes = await api.get_capture_session_manifest_file(id=capture_id)
    capture_manifest = json.loads(capture_manifest_bytes.decode("utf-8"))
    camera_config, axis_convention = _camera_config_from_manifest(capture_manifest)

    frames_csv_bytes = await api.get_capture_session_frames_csv(id=capture_id)
    truth_by_ts = _parse_truth_poses(frames_csv_bytes.decode("utf-8"))

    map_id = await _ensure_localization_map(api, reconstruction_id)

    for ts in pending:
        if ts not in truth_by_ts:
            echo(f"    Skipping ts={ts}: not present in frames.csv")
            continue
        image_bytes = await api.get_capture_session_image(id=capture_id, frame_timestamp=ts)
        await _localize_and_persist(
            api=api,
            reconstruction_id=reconstruction_id,
            map_id=map_id,
            camera_config=camera_config,
            axis_convention=axis_convention,
            frame_timestamp=ts,
            image_bytes=image_bytes,
            truth=truth_by_ts[ts],
            pipeline_version=pipeline_version,
        )


async def _ensure_localization_map(api: DefaultApi, reconstruction_id: UUID) -> UUID:
    try:
        return await api.get_reconstruction_localization_map(id=reconstruction_id)
    except ApiException as e:
        if cast(int | None, e.status) != 404:
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


async def _localize_and_persist(
    *,
    api: DefaultApi,
    reconstruction_id: UUID,
    map_id: UUID,
    camera_config: PinholeCameraConfig,
    axis_convention: AxisConvention,
    frame_timestamp: int,
    image_bytes: bytes,
    truth: _TruthPose,
    pipeline_version: str,
) -> None:
    diagonal_px = float((camera_config.width**2 + camera_config.height**2) ** 0.5)
    succeeded = False
    inlier_ratio = 0.0
    reproj_error_median = 0.0
    num_inliers = 0
    num_correspondences = 0
    num_matches = 0
    inlier_coverage = 0.0
    pnp_covariance: list[list[float]] | None = None
    se3_residual: list[float] | None = None
    err_t_m: float | None = None
    err_r_deg: float | None = None

    try:
        loc_resp = await api.localize_image(
            map_ids=[map_id],
            camera_config=camera_config,
            axis_convention=axis_convention,
            image=("query.jpg", image_bytes),
        )
    except ApiException as e:
        echo(f"    ts={frame_timestamp}: localization failed ({cast(int | None, e.status)})")
        loc_resp = []

    if loc_resp:
        best = loc_resp[0]
        succeeded = True
        inlier_ratio = float(best.metrics.inlier_ratio)
        reproj_error_median = float(best.metrics.reprojection_error_median)
        num_inliers = int(best.metrics.num_inliers)
        num_correspondences = int(best.metrics.num_correspondences)
        num_matches = int(best.metrics.num_matches)
        inlier_coverage = float(best.metrics.inlier_coverage)
        pnp_covariance = [[float(v) for v in row] for row in best.metrics.pnp_covariance]

        cam_from_map_translation = asarray(
            [
                best.camera_from_map_transform.translation.x,
                best.camera_from_map_transform.translation.y,
                best.camera_from_map_transform.translation.z,
            ],
            dtype=float64,
        )
        cam_from_map_rotation = Rotation.from_quat([
            best.camera_from_map_transform.rotation.x,
            best.camera_from_map_transform.rotation.y,
            best.camera_from_map_transform.rotation.z,
            best.camera_from_map_transform.rotation.w,
        ]).as_matrix()
        estimated_camera_position = -cam_from_map_rotation.T @ cam_from_map_translation
        estimated_world_from_camera = cam_from_map_rotation.T
        truth_world_from_camera = Rotation.from_quat(truth.rotation_quat_xyzw).as_matrix()
        relative_rotation = Rotation.from_matrix(truth_world_from_camera @ estimated_world_from_camera.T)

        err_t_m = float(norm(truth.translation - estimated_camera_position))
        err_r_deg = float(degrees(relative_rotation.magnitude()))

        truth_4x4 = transform_from(truth_world_from_camera, truth.translation)
        estimated_4x4 = transform_from(estimated_world_from_camera, estimated_camera_position)
        residual_transform = concat(truth_4x4, invert_transform(estimated_4x4, check=False))
        se3_residual = exponential_coordinates_from_transform(residual_transform).tolist()

    await api.upsert_localization_evaluation(
        reconstruction_id=reconstruction_id,
        localization_evaluation_create=LocalizationEvaluationCreate(
            reconstruction_id=reconstruction_id,
            frame_timestamp=frame_timestamp,
            retrieval_top_k=0,
            ransac_threshold=0.0,
            pipeline_version=pipeline_version,
            succeeded=succeeded,
            inlier_ratio=inlier_ratio,
            reproj_error_median=reproj_error_median,
            num_inliers=num_inliers,
            num_correspondences=num_correspondences,
            num_matches=num_matches,
            inlier_coverage=inlier_coverage,
            pnp_covariance=cast(list[Any] | None, pnp_covariance),
            se3_residual=cast(list[Any] | None, se3_residual),
            err_t_m=err_t_m,
            err_r_deg=err_r_deg,
            query_image_diagonal_px=diagonal_px,
        ),
    )


async def _read_corpus(api: DefaultApi, reconstruction_ids: list[UUID], pipeline_version: str) -> list[CorpusRow]:
    corpus: list[CorpusRow] = []
    for reconstruction_id in reconstruction_ids:
        manifest = await api.get_reconstruction_manifest(id=reconstruction_id)
        recon = await api.get_reconstruction(id=reconstruction_id)
        metrics = manifest.metrics
        if (
            metrics.map_image_count is None
            or metrics.map_point_count is None
            or metrics.map_avg_track_length is None
            or metrics.map_bounding_volume_m3 is None
            or metrics.map_viewpoint_diversity is None
        ):
            echo(f"  Reconstruction {reconstruction_id} missing map-quality metrics; skipping its rows")
            continue
        evals = await api.list_localization_evaluations(
            reconstruction_id=reconstruction_id, pipeline_version=pipeline_version
        )
        for row in evals:
            corpus.append(
                CorpusRow(
                    succeeded=row.succeeded,
                    inlier_ratio=float(row.inlier_ratio),
                    reproj_error_median=float(row.reproj_error_median),
                    num_inliers=int(row.num_inliers),
                    num_correspondences=int(row.num_correspondences),
                    num_matches=int(row.num_matches),
                    inlier_coverage=float(row.inlier_coverage),
                    pnp_covariance=[[float(v) for v in r] for r in row.pnp_covariance] if row.pnp_covariance else None,
                    se3_residual=[float(v) for v in row.se3_residual] if row.se3_residual else None,
                    err_t_m=float(row.err_t_m) if row.err_t_m is not None else None,
                    err_r_deg=float(row.err_r_deg) if row.err_r_deg is not None else None,
                    query_image_diagonal_px=float(row.query_image_diagonal_px),
                    map_image_count=int(metrics.map_image_count),
                    map_point_count=int(metrics.map_point_count),
                    map_avg_track_length=float(metrics.map_avg_track_length),
                    map_bounding_volume_m3=float(metrics.map_bounding_volume_m3),
                    map_viewpoint_diversity=float(metrics.map_viewpoint_diversity),
                    is_indoor=bool(recon.is_indoor),
                )
            )
    return corpus


def fit_calibration_from_corpus(corpus: list[CorpusRow], *, pipeline_version: str) -> CalibrationArtifact:
    feature_rows: list[NDArray[float64]] = []
    tight_labels_list: list[int] = []
    loose_labels_list: list[int] = []
    pnp_covariance_list: list[NDArray[float64]] = []
    residual_list: list[NDArray[float64]] = []

    skipped_unsuccessful = 0

    for row in corpus:
        if not row.succeeded or row.err_t_m is None or row.err_r_deg is None:
            skipped_unsuccessful += 1
            continue
        features = Features(
            log_inliers=float(log1p(row.num_inliers)),
            inlier_ratio=row.inlier_ratio,
            reproj_err_norm=row.reproj_error_median / row.query_image_diagonal_px,
            inlier_coverage=row.inlier_coverage,
            log_num_matches=float(log1p(row.num_matches)),
            log_map_image_count=float(log1p(row.map_image_count)),
            log_map_point_count=float(log1p(row.map_point_count)),
            map_avg_track_length=row.map_avg_track_length,
            log_map_bounding_volume_m3=float(log1p(row.map_bounding_volume_m3)),
            map_viewpoint_diversity=row.map_viewpoint_diversity,
            is_indoor=1.0 if row.is_indoor else 0.0,
        )
        feature_rows.append(_features_to_row(features))
        tight_labels_list.append(_success_label(row.err_t_m, row.err_r_deg, TIGHT_T_M, TIGHT_R_DEG))
        loose_labels_list.append(_success_label(row.err_t_m, row.err_r_deg, LOOSE_T_M, LOOSE_R_DEG))

        if row.pnp_covariance is not None and row.se3_residual is not None:
            pnp_covariance_list.append(asarray(row.pnp_covariance, dtype=float64))
            residual_list.append(asarray(row.se3_residual, dtype=float64))

    if not feature_rows:
        raise RuntimeError(
            f"No usable rows after pooling. Skipped {skipped_unsuccessful} unsuccessful localizations. "
            "Confirm the localization_evaluations cache is populated and that the supplied --pipeline-version "
            "matches the rows you intend to fit against."
        )

    features_matrix = asarray(feature_rows, dtype=float64)
    tight_labels = asarray(tight_labels_list, dtype=float64)
    loose_labels = asarray(loose_labels_list, dtype=float64)

    if pnp_covariance_list:
        sigma_meas_result = minimize(
            _nll,
            x0=asarray(_SIGMA_MEAS_INITIAL, dtype=float64),
            args=(asarray(pnp_covariance_list, dtype=float64), asarray(residual_list, dtype=float64)),
            bounds=_SIGMA_MEAS_BOUNDS,
            method="L-BFGS-B",
        )
        sigma_meas_alpha = float(sigma_meas_result.x[0])
        sigma_meas_beta = float(sigma_meas_result.x[1])
    else:
        sigma_meas_alpha, sigma_meas_beta = 1.0, 0.0

    return CalibrationArtifact(
        schema_version=SCHEMA_VERSION,
        pipeline_version=pipeline_version,
        fit_at=datetime.now(timezone.utc).isoformat(),
        fit_by="scripts/fit_calibration.py",
        sample_count=int(tight_labels.size),
        tight=fit_logistic_with_isotonic(features_matrix, tight_labels),
        loose=fit_logistic_with_isotonic(features_matrix, loose_labels),
        sigma_meas_alpha=sigma_meas_alpha,
        sigma_meas_beta=sigma_meas_beta,
        loose_min=STARTER_LOOSE_MIN,
        tight_min=STARTER_TIGHT_MIN,
    )


def fit_logistic_with_isotonic(features: NDArray[float64], labels: NDArray[float64]) -> ToleranceModel:
    if unique(labels).size < 2:
        constant_label = float(labels[0])
        return ToleranceModel(
            logistic_weights=[0.0] * features.shape[1],
            logistic_intercept=30.0 if constant_label > 0.5 else -30.0,
            logistic_feature_names=list(FEATURE_NAMES),
            isotonic_x_breakpoints=[0.0, 1.0],
            isotonic_y_breakpoints=[0.0, 1.0],
        )

    model = cast(Any, LogisticRegression(class_weight="balanced", max_iter=1000))
    model.fit(features, labels)
    raw_predictions = cast(NDArray[float64], model.predict_proba(features))[:, 1]

    isotonic = cast(Any, IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0))
    isotonic.fit(raw_predictions, labels)

    x_breakpoints: list[float] = cast(NDArray[float64], isotonic.X_thresholds_).tolist()
    y_breakpoints: list[float] = cast(NDArray[float64], isotonic.y_thresholds_).tolist()
    if len(x_breakpoints) < 2:
        x_breakpoints = [0.0, 1.0]
        y_breakpoints = [float(labels.mean())] * 2

    return ToleranceModel(
        logistic_weights=cast(NDArray[float64], model.coef_[0]).tolist(),
        logistic_intercept=float(cast(NDArray[float64], model.intercept_)[0]),
        logistic_feature_names=list(FEATURE_NAMES),
        isotonic_x_breakpoints=x_breakpoints,
        isotonic_y_breakpoints=y_breakpoints,
    )


def _features_to_row(features: Features) -> NDArray[float64]:
    dump = features.model_dump()
    return asarray([dump[name] for name in FEATURE_NAMES], dtype=float64)


def _success_label(err_t_m: float, err_r_deg: float, max_t_m: float, max_r_deg: float) -> int:
    return 1 if err_t_m < max_t_m and err_r_deg < max_r_deg else 0


def _nll(parameters: ndarray, pnp_covariances: NDArray[float64], se3_residuals: NDArray[float64]) -> float:
    alpha, beta = float(parameters[0]), float(parameters[1])
    try:
        return -sum(
            float(multivariate_normal.logpdf(residual, cov=alpha * covariance + beta * _IDENTITY_6))
            for residual, covariance in zip(se3_residuals, pnp_covariances)
        )
    except (ValueError, LinAlgError):
        return float(inf)


def _camera_config_from_manifest(manifest: dict[str, Any]) -> tuple[PinholeCameraConfig, AxisConvention]:
    rigs = manifest.get("rigs", [])
    if not rigs or not rigs[0].get("cameras"):
        raise RuntimeError("Capture manifest is missing rigs[0].cameras[0]")
    raw = rigs[0]["cameras"][0]["camera_config"]
    return (
        PinholeCameraConfig(
            width=int(raw["width"]),
            height=int(raw["height"]),
            orientation=str(raw["orientation"]),
            fx=float(raw["fx"]),
            fy=float(raw["fy"]),
            cx=float(raw["cx"]),
            cy=float(raw["cy"]),
        ),
        AxisConvention(manifest["axis_convention"]),
    )


def _parse_truth_poses(frames_csv: str) -> dict[int, _TruthPose]:
    truth: dict[int, _TruthPose] = {}
    for row in DictReader(StringIO(frames_csv)):
        timestamp = int(row["timestamp"])
        truth[timestamp] = _TruthPose(
            translation=asarray([float(row["tx"]), float(row["ty"]), float(row["tz"])], dtype=float64),
            rotation_quat_xyzw=asarray(
                [float(row["qx"]), float(row["qy"]), float(row["qz"]), float(row["qw"])], dtype=float64
            ),
        )
    return truth


async def _build_api_config() -> Configuration:
    public_domain: str | None = None
    for line in (REPO_ROOT / ".env").read_text().splitlines():
        stripped = line.strip()
        if stripped.startswith("PUBLIC_DOMAIN=") and not stripped.startswith("#"):
            public_domain = stripped.split("=", 1)[1].strip()
            break
    if public_domain is None:
        raise RuntimeError("PUBLIC_DOMAIN not found in .env")

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

    return Configuration(
        host=f"https://{public_domain}",
        access_token=resp.json()["access_token"],
        ssl_ca_cert=False,  # type: ignore[arg-type]
    )


async def _fetch_localizer_version() -> str:
    base_url = _resolve_localizer_url()
    async with LocalizerApiClient(LocalizerConfiguration(host=base_url)) as client:
        version = await LocalizerDefaultApi(client).get_localizer_version()
    return version.git_sha


def _resolve_localizer_url() -> str:
    env_url = os.environ.get("LOCALIZER_BASE_URL")
    if env_url:
        return env_url
    container = os.environ.get("LOCALIZER_CONTAINER", "placeframe-localizer-cuda-1")
    ip = subprocess.check_output(
        [
            "docker",
            "inspect",
            container,
            "-f",
            '{{ (index .NetworkSettings.Networks "placeframe_default").IPAddress }}',
        ],
        text=True,
        stderr=subprocess.DEVNULL,
    ).strip()
    if not ip:
        raise RuntimeError(
            f"Could not resolve localizer ip via 'docker inspect {container}'. "
            "Set LOCALIZER_BASE_URL or LOCALIZER_CONTAINER to override."
        )
    return f"http://{ip}:8000"
