from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Any, cast

from core.calibration import FEATURE_NAMES, SCHEMA_VERSION, CalibrationArtifact, Features, ToleranceModel
from numpy import (
    asarray,
    eye,
    float64,
    inf,
    log1p,
    ndarray,
    unique,
)
from numpy.linalg import LinAlgError
from numpy.typing import NDArray  # noqa: TID251 — Phase T piece 3 follow-up migration
from scipy.optimize import minimize
from scipy.stats import multivariate_normal
from sklearn.isotonic import IsotonicRegression  # type: ignore[import-untyped]
from sklearn.linear_model import LogisticRegression  # type: ignore[import-untyped]
from typer import Exit, Option, Typer, echo

from .e2e_results import E2EResults

app = Typer()

REPO_ROOT = Path(__file__).resolve().parents[3]

# Success thresholds (intent doc Algorithm 1 step 4).
TIGHT_T_M = 0.05
TIGHT_R_DEG = 1.0
LOOSE_T_M = 0.30
LOOSE_R_DEG = 5.0

# scipy.optimize bounds and seed for the (alpha, beta) fit.
_SIGMA_MEAS_INITIAL = (1.0, 1.0e-4)
_SIGMA_MEAS_BOUNDS = ((1.0e-6, 1.0e6), (0.0, 1.0e3))
_IDENTITY_6 = eye(6, dtype=float64)


@app.command()
def main(
    inputs: Annotated[list[Path], Option("--input", help="Path to e2e-results.json (repeat to pool corpora).")],
    output: Annotated[Path, Option("--output", help="Path to write the calibration artifact.")] = (
        REPO_ROOT / "config" / "calibration" / "global.json"
    ),
    pipeline_version: Annotated[
        str,
        Option(
            "--pipeline-version",
            help="Localizer git SHA the calibration is fit against. Used as the artifact's pipeline_version.",
        ),
    ] = ...,  # type: ignore[assignment] — typer treats this as required when ... is the default
) -> None:
    if not inputs:
        echo("At least one --input is required.")
        raise Exit(1)
    for path in inputs:
        if not path.exists():
            echo(f"Input not found: {path}")
            raise Exit(1)

    artifact = fit_calibration_from_results(
        [E2EResults.model_validate_json(path.read_text(encoding="utf-8")) for path in inputs],
        pipeline_version=pipeline_version,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    artifact.write(output)

    echo(f"Pipeline version:   {artifact.pipeline_version}")
    echo(f"Sample count:       {artifact.sample_count}")
    echo(f"sigma_meas alpha:   {artifact.sigma_meas_alpha:.6g}")
    echo(f"sigma_meas beta:    {artifact.sigma_meas_beta:.6g}")
    echo(f"\nArtifact written to {output}")


def fit_calibration_from_results(results: list[E2EResults], pipeline_version: str) -> CalibrationArtifact:
    reconstructions_by_id = {
        reconstruction.reconstruction_id: reconstruction
        for result in results
        for reconstruction in result.reconstructions
        if reconstruction.reconstruction_id is not None
    }

    feature_rows: list[NDArray[float64]] = []
    tight_labels_list: list[int] = []
    loose_labels_list: list[int] = []
    pnp_covariance_list: list[NDArray[float64]] = []
    residual_list: list[NDArray[float64]] = []

    skipped_unsuccessful = 0
    skipped_missing_features = 0

    for localization in (loc for result in results for loc in result.localizations):
        if not localization.succeeded or localization.err_t_m is None or localization.err_r_deg is None:
            skipped_unsuccessful += 1
            continue
        reconstruction = reconstructions_by_id.get(localization.reconstruction_id)
        if reconstruction is None:
            skipped_missing_features += 1
            continue
        metrics = reconstruction.metrics
        if metrics is None or reconstruction.is_indoor is None:
            skipped_missing_features += 1
            continue
        if (
            localization.num_inliers is None
            or localization.inlier_ratio is None
            or localization.reproj_error_median is None
        ):
            skipped_missing_features += 1
            continue
        if localization.inlier_coverage is None or localization.num_matches is None:
            skipped_missing_features += 1
            continue
        if metrics.map_image_count is None or metrics.map_point_count is None or metrics.map_avg_track_length is None:
            skipped_missing_features += 1
            continue
        if metrics.map_bounding_volume_m3 is None or metrics.map_viewpoint_diversity is None:
            skipped_missing_features += 1
            continue

        features = Features(
            log_inliers=float(log1p(localization.num_inliers)),
            inlier_ratio=localization.inlier_ratio,
            reproj_err_norm=localization.reproj_error_median / localization.query_image_diagonal_px,
            inlier_coverage=localization.inlier_coverage,
            log_num_matches=float(log1p(localization.num_matches)),
            log_map_image_count=float(log1p(metrics.map_image_count)),
            log_map_point_count=float(log1p(metrics.map_point_count)),
            map_avg_track_length=metrics.map_avg_track_length,
            log_map_bounding_volume_m3=float(log1p(metrics.map_bounding_volume_m3)),
            map_viewpoint_diversity=metrics.map_viewpoint_diversity,
            is_indoor=1.0 if reconstruction.is_indoor else 0.0,
        )
        feature_rows.append(_features_to_row(features))
        tight_labels_list.append(_success_label(localization.err_t_m, localization.err_r_deg, TIGHT_T_M, TIGHT_R_DEG))
        loose_labels_list.append(_success_label(localization.err_t_m, localization.err_r_deg, LOOSE_T_M, LOOSE_R_DEG))

        if localization.pnp_covariance is not None and localization.se3_residual is not None:
            pnp_covariance_list.append(asarray(localization.pnp_covariance, dtype=float64))
            residual_list.append(asarray(localization.se3_residual, dtype=float64))

    if not feature_rows:
        raise RuntimeError(
            f"No usable rows after pooling. Skipped {skipped_unsuccessful} unsuccessful localizations and "
            f"{skipped_missing_features} rows missing features. Confirm the harness was run against a stack with "
            "the chunk-2 map-quality fields and the chunk-4 pnp_covariance/se3_residual fields populated."
        )

    features = asarray(feature_rows, dtype=float64)
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
        tight=fit_logistic_with_isotonic(features, tight_labels),
        loose=fit_logistic_with_isotonic(features, loose_labels),
        sigma_meas_alpha=sigma_meas_alpha,
        sigma_meas_beta=sigma_meas_beta,
    )


def _features_to_row(features: Features) -> NDArray[float64]:
    dump = features.model_dump()
    return asarray([dump[name] for name in FEATURE_NAMES], dtype=float64)


def _success_label(
    error_translation_meters: float,
    error_rotation_degrees: float,
    max_translation_meters: float,
    max_rotation_degrees: float,
) -> int:
    if error_translation_meters < max_translation_meters and error_rotation_degrees < max_rotation_degrees:
        return 1
    return 0


def _nll(parameters: ndarray, pnp_covariances: NDArray[float64], se3_residuals: NDArray[float64]) -> float:
    alpha, beta = float(parameters[0]), float(parameters[1])
    # Loop+logpdf is ~50x slower than batched slogdet+solve; swap if fits become slow.
    try:
        return -sum(
            float(multivariate_normal.logpdf(residual, cov=alpha * covariance + beta * _IDENTITY_6))
            for residual, covariance in zip(se3_residuals, pnp_covariances)
        )
    except (ValueError, LinAlgError):
        return float(inf)


def fit_logistic_with_isotonic(features: NDArray[float64], labels: NDArray[float64]) -> ToleranceModel:
    if unique(labels).size < 2:
        # Degenerate: only one observed class. Synthesize a constant-output logistic.
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
