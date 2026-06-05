from __future__ import annotations

from asyncio import run, sleep
from csv import DictReader
from dataclasses import dataclass
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
from typing import Annotated, Any, cast
from uuid import UUID

from core.calibration import (
    SCHEMA_VERSION,
    CalibrationArtifact,
    Features,
    RawLocalizationMetrics,
    RawMapMetrics,
    ToleranceModel,
)
from core.capture_session_manifest import CaptureSessionManifest
from core.localization_metrics import RANSAC_THRESHOLD_DEFAULT, RETRIEVAL_TOP_K_DEFAULT
from numpy import asarray, degrees, eye, float64, inf, unique
from numpy.linalg import LinAlgError, norm
from numpy.typing import NDArray  # noqa: TID251 — Phase T piece 3 follow-up migration
from pydantic import BaseModel, ValidationError
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
    ApiException,
    AxisConvention,
    DefaultApi,
    LocalizationEvaluationCreate,
    LocalizationEvaluationRead,
    LocalizationMapCreate,
    PinholeCameraConfig,
    ReconstructionCreate,
    ReconstructionCreateWithOptions,
    ReconstructionOptions,
    ReconstructionStatus,
)

from .api_auth import authenticated_api_client
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
    evaluation: LocalizationEvaluationRead
    map_metrics: RawMapMetrics


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
        REPO_ROOT / "docker" / "localizer" / "calibration" / "global.json"
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
    selector = get_selector(held_out_selector_name)
    selector_options = HeldOutSelectionOptions(target_count=held_out_count)

    async with authenticated_api_client() as api:
        if pipeline_version_override is not None:
            pipeline_version = pipeline_version_override
            echo(f"Using --pipeline-version override: {pipeline_version}")
        else:
            pipeline_version = await api.get_localizer_version()
            echo(f"Auto-detected pipeline_version from localizer /version: {pipeline_version}")

        if capture_ids:
            resolved: list[UUID] = []
            for capture_id in capture_ids:
                frames_csv_bytes = await api.get_capture_session_frames_csv(id=capture_id)
                held_out_timestamps = selector(frames_csv_bytes.decode("utf-8"), selector_options)
                requested = ReconstructionOptions(held_out_frame_timestamps=held_out_timestamps)
                reconstruction_id = await match_or_create_reconstruction(api, capture_id, requested)
                resolved.append(reconstruction_id)
                echo(
                    f"Capture {capture_id}: held-out {len(held_out_timestamps)} frames, "
                    f"reconstruction {reconstruction_id}"
                )
            reconstruction_ids = resolved

        for reconstruction_id in reconstruction_ids:
            await _populate_evaluations(api, reconstruction_id, pipeline_version)

        if no_fit:
            echo("--no-fit: cache populated, skipping fit")
            return

        corpus: list[CorpusRow] = []
        for reconstruction_id in reconstruction_ids:
            reconstruction = await api.get_reconstruction(id=reconstruction_id)
            try:
                map_metrics = RawMapMetrics.model_validate(reconstruction.manifest["metrics"])
            except ValidationError:
                echo(f"  Reconstruction {reconstruction_id} missing map-quality metrics; skipping its rows")
                continue
            evaluations = await api.list_localization_evaluations(
                reconstruction_id=reconstruction_id, pipeline_version=pipeline_version
            )
            for evaluation in evaluations:
                corpus.append(CorpusRow(evaluation=evaluation, map_metrics=map_metrics))

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
        reconstruction = await api.get_reconstruction(id=candidate_id)
        if reconstruction.status != ReconstructionStatus.SUCCEEDED:
            continue
        if ReconstructionOptions.model_validate(reconstruction.manifest["options"]) == requested_options:
            return candidate_id

    created = await api.create_reconstruction(
        ReconstructionCreateWithOptions(
            create=ReconstructionCreate(capture_session_id=capture_id),
            options=requested_options,
        )
    )
    elapsed = 0
    while True:
        await sleep(RECONSTRUCTION_POLL_S)
        elapsed += RECONSTRUCTION_POLL_S
        current = await api.get_reconstruction(id=created.id)
        if current.status == ReconstructionStatus.SUCCEEDED:
            break
        if current.status in (ReconstructionStatus.FAILED, ReconstructionStatus.CANCELLED):
            raise RuntimeError(f"Reconstruction {created.id} ended in {current.status.value}")
        if elapsed >= RECONSTRUCTION_TIMEOUT_S:
            raise RuntimeError(f"Reconstruction {created.id} did not succeed within {RECONSTRUCTION_TIMEOUT_S}s")
    return created.id


async def _populate_evaluations(api: DefaultApi, reconstruction_id: UUID, pipeline_version: str) -> None:
    reconstruction = await api.get_reconstruction(id=reconstruction_id)
    options = ReconstructionOptions.model_validate(reconstruction.manifest["options"])
    held_out_timestamps = options.held_out_frame_timestamps or []
    if not held_out_timestamps:
        echo(f"  Reconstruction {reconstruction_id} has no held-out frames; skipping localization step")
        return

    capture_id = reconstruction.capture_session_id
    cached = await api.list_localization_evaluations(
        reconstruction_id=reconstruction_id, pipeline_version=pipeline_version
    )
    cached_timestamps = {row.frame_timestamp for row in cached}

    pending = [timestamp for timestamp in held_out_timestamps if timestamp not in cached_timestamps]
    if not pending:
        echo(f"  Reconstruction {reconstruction_id}: all {len(held_out_timestamps)} held-out frames already cached")
        return

    echo(
        f"  Reconstruction {reconstruction_id}: localizing {len(pending)} held-out frames "
        f"({len(cached_timestamps)} cached)"
    )

    capture_manifest_bytes = await api.get_capture_session_manifest_file(id=capture_id)
    capture_manifest = CaptureSessionManifest.model_validate_json(capture_manifest_bytes)
    camera_config_dump = capture_manifest.rigs[0].cameras[0].camera_config.model_dump()
    camera_config = PinholeCameraConfig(**camera_config_dump)
    axis_convention = AxisConvention(capture_manifest.axis_convention.value)

    frames_csv_bytes = await api.get_capture_session_frames_csv(id=capture_id)
    truth_by_timestamp: dict[int, _TruthPose] = {}
    for row in DictReader(StringIO(frames_csv_bytes.decode("utf-8"))):
        truth_by_timestamp[int(row["timestamp_ms"])] = _TruthPose(
            translation=asarray([float(row["tx"]), float(row["ty"]), float(row["tz"])], dtype=float64),
            rotation_quat_xyzw=asarray(
                [float(row["qx"]), float(row["qy"]), float(row["qz"]), float(row["qw"])], dtype=float64
            ),
        )

    try:
        map_id = await api.get_reconstruction_localization_map(id=reconstruction_id)
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
        map_id = created.id

    for timestamp in pending:
        if timestamp not in truth_by_timestamp:
            echo(f"    Skipping timestamp={timestamp}: not present in frames.csv")
            continue
        image_bytes = await api.get_capture_session_image(id=capture_id, frame_timestamp=timestamp)
        await _localize_and_persist(
            api=api,
            reconstruction_id=reconstruction_id,
            map_id=map_id,
            camera_config=camera_config,
            axis_convention=axis_convention,
            frame_timestamp=timestamp,
            image_bytes=image_bytes,
            truth=truth_by_timestamp[timestamp],
            pipeline_version=pipeline_version,
        )


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

    try:
        localization_response = await api.localize_image(
            map_ids=[map_id],
            camera_config=camera_config,
            axis_convention=axis_convention,
            image=("query.jpg", image_bytes),
            retrieval_top_k=RETRIEVAL_TOP_K_DEFAULT,
            ransac_threshold=RANSAC_THRESHOLD_DEFAULT,
        )
    except ApiException as e:
        echo(f"    timestamp={frame_timestamp}: localization failed ({cast(int | None, e.status)})")
        localization_response = []

    if localization_response:
        best = localization_response[0]
        camera_from_map_translation = asarray(
            [
                best.camera_from_map_transform.translation.x,
                best.camera_from_map_transform.translation.y,
                best.camera_from_map_transform.translation.z,
            ],
            dtype=float64,
        )
        camera_from_map_rotation = Rotation.from_quat([
            best.camera_from_map_transform.rotation.x,
            best.camera_from_map_transform.rotation.y,
            best.camera_from_map_transform.rotation.z,
            best.camera_from_map_transform.rotation.w,
        ]).as_matrix()
        estimated_camera_position = -camera_from_map_rotation.T @ camera_from_map_translation
        estimated_world_from_camera = camera_from_map_rotation.T
        truth_world_from_camera = Rotation.from_quat(truth.rotation_quat_xyzw).as_matrix()
        relative_rotation = Rotation.from_matrix(truth_world_from_camera @ estimated_world_from_camera.T)
        residual_transform = concat(
            transform_from(truth_world_from_camera, truth.translation),
            invert_transform(transform_from(estimated_world_from_camera, estimated_camera_position), check=False),
        )
        evaluation = LocalizationEvaluationCreate(
            reconstruction_id=reconstruction_id,
            frame_timestamp=frame_timestamp,
            retrieval_top_k=RETRIEVAL_TOP_K_DEFAULT,
            ransac_threshold=RANSAC_THRESHOLD_DEFAULT,
            pipeline_version=pipeline_version,
            query_image_diagonal_px=diagonal_px,
            succeeded=True,
            num_inliers=int(best.metrics.num_inliers),
            inlier_ratio=float(best.metrics.inlier_ratio),
            reproj_error_median=float(best.metrics.reprojection_error_median),
            inlier_coverage=float(best.metrics.inlier_coverage),
            num_matches=int(best.metrics.num_matches),
            num_correspondences=int(best.metrics.num_correspondences),
            pnp_covariance=cast(list[Any], [[float(v) for v in row] for row in best.metrics.pnp_covariance]),
            se3_residual=cast(list[Any], exponential_coordinates_from_transform(residual_transform).tolist()),
            err_t_m=float(norm(truth.translation - estimated_camera_position)),
            err_r_deg=float(degrees(relative_rotation.magnitude())),
        )
    else:
        evaluation = LocalizationEvaluationCreate(
            reconstruction_id=reconstruction_id,
            frame_timestamp=frame_timestamp,
            retrieval_top_k=RETRIEVAL_TOP_K_DEFAULT,
            ransac_threshold=RANSAC_THRESHOLD_DEFAULT,
            pipeline_version=pipeline_version,
            query_image_diagonal_px=diagonal_px,
            succeeded=False,
            num_inliers=0,
            inlier_ratio=0.0,
            reproj_error_median=0.0,
            inlier_coverage=0.0,
            num_matches=0,
            num_correspondences=0,
            pnp_covariance=None,
            se3_residual=None,
            err_t_m=None,
            err_r_deg=None,
        )

    await api.upsert_localization_evaluation(
        reconstruction_id=reconstruction_id,
        localization_evaluation_create=evaluation,
    )


def fit_calibration_from_corpus(corpus: list[CorpusRow], *, pipeline_version: str) -> CalibrationArtifact:
    feature_rows: list[NDArray[float64]] = []
    tight_labels_list: list[int] = []
    loose_labels_list: list[int] = []
    pnp_covariance_list: list[NDArray[float64]] = []
    residual_list: list[NDArray[float64]] = []

    skipped_unsuccessful = 0

    for row in corpus:
        evaluation = row.evaluation
        if not evaluation.succeeded or evaluation.err_t_m is None or evaluation.err_r_deg is None:
            skipped_unsuccessful += 1
            continue

        features = Features.compute(
            localization=RawLocalizationMetrics.model_validate(evaluation, from_attributes=True),
            map_metrics=row.map_metrics,
        )
        feature_rows.append(asarray(list(features.model_dump().values()), dtype=float64))
        tight_labels_list.append(_success_label(evaluation.err_t_m, evaluation.err_r_deg, TIGHT_T_M, TIGHT_R_DEG))
        loose_labels_list.append(_success_label(evaluation.err_t_m, evaluation.err_r_deg, LOOSE_T_M, LOOSE_R_DEG))

        if evaluation.pnp_covariance is not None and evaluation.se3_residual is not None:
            pnp_covariance_list.append(asarray(evaluation.pnp_covariance, dtype=float64))
            residual_list.append(asarray(evaluation.se3_residual, dtype=float64))

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
            _negative_log_likelihood,
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
        fit_by=str(Path(__file__).resolve().relative_to(REPO_ROOT)),
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
        return ToleranceModel(
            logistic_weights=Features.zeros(),
            logistic_intercept=30.0 if float(labels[0]) > 0.5 else -30.0,
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
        logistic_weights=Features(
            **dict(zip(Features.model_fields, cast(NDArray[float64], model.coef_[0]).tolist(), strict=True))
        ),
        logistic_intercept=float(cast(NDArray[float64], model.intercept_)[0]),
        isotonic_x_breakpoints=x_breakpoints,
        isotonic_y_breakpoints=y_breakpoints,
    )


def _success_label(err_t_m: float, err_r_deg: float, max_t_m: float, max_r_deg: float) -> int:
    return 1 if err_t_m < max_t_m and err_r_deg < max_r_deg else 0


def _negative_log_likelihood(
    parameters: NDArray[float64], pnp_covariances: NDArray[float64], se3_residuals: NDArray[float64]
) -> float:
    alpha, beta = float(parameters[0]), float(parameters[1])
    try:
        return -sum(
            float(multivariate_normal.logpdf(residual, cov=alpha * covariance + beta * _IDENTITY_6))
            for residual, covariance in zip(se3_residuals, pnp_covariances)
        )
    except (ValueError, LinAlgError):
        return float(inf)
