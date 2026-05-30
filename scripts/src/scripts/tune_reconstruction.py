# Plackett-Burman sweep over ReconstructionOptions across one or more captures.
# Compares PB cells by *map-quality metrics* read from each reconstruction's manifest
# (registered images, point count, average track length, bounding volume, viewpoint
# diversity, plus the truth-alignment Procrustes residual).
#
# DEFERRED — localization-quality eval per cell. The genuine figure of merit for
# parameter tuning is *localization* quality (held-out localizations per cell),
# not just map quality. Comparing cells by held-out localization aggregates would
# require running effectively the fit-calibration loop per cell — its own
# multi-hour effort, downstream of getting calibration logic itself correct.
# Map-quality metrics are a cheap proxy that surfaces gross differences between
# cells. Once the calibration work in plan.md Phase 3 is done, extend this
# script (or a sibling) to evaluate held-out-localization aggregates per cell.
from __future__ import annotations

from asyncio import run, sleep
from json import dumps
from pathlib import Path
from typing import Annotated
from uuid import UUID

from core.reconstruction_metrics import ReconstructionMetrics
from typer import Exit, Option, Typer, echo

from placeframe_api_client import (
    DefaultApi,
    ReconstructionCreate,
    ReconstructionCreateWithOptions,
    ReconstructionOptions,
    ReconstructionStatus,
)

from .api_auth import authenticated_api_client

app = Typer()

POLL_INTERVAL_S = 10

PB_LOW = ReconstructionOptions(
    retrieval_neighbors=8,
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
    retrieval_neighbors=20,
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


@app.command()
def main(
    captures: Annotated[list[UUID], Option("--captures", help="Capture session ids to sweep over")],
    output: Annotated[Path | None, Option("--output", help="Optional path to write the tuning report as JSON")] = None,
) -> None:
    if not captures:
        echo("--captures requires at least one capture session id")
        raise Exit(1)
    report = run(_run(captures))
    rendered = dumps(report, indent=2)
    echo(rendered)
    if output is not None:
        output.write_text(rendered)
        echo(f"Report written to {output}")


async def _run(capture_ids: list[UUID]) -> list[dict[str, object]]:
    configs = _pb_configs()
    echo(f"=== {len(configs)} configs (1 baseline + {len(configs) - 1} Plackett-Burman) ===")

    rows: list[dict[str, object]] = []
    async with authenticated_api_client() as api:
        for capture_id in capture_ids:
            for config_idx, options in enumerate(configs):
                rows.append(await _run_cell(api, capture_id, options, config_idx))

    succeeded = sum(1 for row in rows if row["succeeded"])
    echo(f"\n{succeeded}/{len(rows)} reconstructions succeeded")
    return rows


async def _run_cell(
    api: DefaultApi, capture_id: UUID, options: ReconstructionOptions | None, config_idx: int
) -> dict[str, object]:
    recon = await api.create_reconstruction(
        ReconstructionCreateWithOptions(
            create=ReconstructionCreate(capture_session_id=capture_id),
            options=options,
        )
    )
    echo(f"  [{config_idx:02d}] capture {capture_id} → {recon.id}")

    while True:
        await sleep(POLL_INTERVAL_S)
        current = await api.get_reconstruction(id=recon.id)
        if current.status == ReconstructionStatus.SUCCEEDED:
            break
        if current.status in (ReconstructionStatus.FAILED, ReconstructionStatus.CANCELLED):
            echo(f"    {current.status.value}")
            return {
                "capture_id": str(capture_id),
                "config_idx": config_idx,
                "options": options.to_dict() if options else None,
                "reconstruction_id": str(recon.id),
                "succeeded": False,
            }

    metrics = ReconstructionMetrics.model_validate(current.manifest["metrics"])
    echo(f"    Succeeded, {metrics.registered_images}/{metrics.total_images} images")
    return {
        "capture_id": str(capture_id),
        "config_idx": config_idx,
        "options": options.to_dict() if options else None,
        "reconstruction_id": str(recon.id),
        "succeeded": True,
        "registered_images": metrics.registered_images,
        "total_images": metrics.total_images,
        "registration_rate": metrics.registration_rate,
        "num_3d_points": metrics.num_3d_points,
        "reproj_error_50th": metrics.reprojection_pixel_error_50th_percentile,
        "reproj_error_90th": metrics.reprojection_pixel_error_90th_percentile,
        "map_image_count": metrics.map_image_count,
        "map_point_count": metrics.map_point_count,
        "map_avg_track_length": metrics.map_avg_track_length,
        "map_bounding_volume_m3": metrics.map_bounding_volume_m3,
        "map_viewpoint_diversity": metrics.map_viewpoint_diversity,
        "truth_alignment_rms_residual_m": metrics.truth_alignment_rms_residual_m,
        "truth_alignment_max_residual_m": metrics.truth_alignment_max_residual_m,
    }


def _pb_configs() -> list[ReconstructionOptions | None]:
    # Plackett-Burman screening — rotate seed row to generate 15 configs + all-low + baseline.
    configs: list[ReconstructionOptions | None] = [None]
    row = list(PB_SEED)
    for _ in range(len(PB_SEED) + 5):
        configs.append(
            ReconstructionOptions(**{f: getattr(PB_HIGH if s == 1 else PB_LOW, f) for f, s in zip(PB_FACTORS, row)})
        )
        row = [row[-1], *row[:-1]]
    configs.append(ReconstructionOptions(**{f: getattr(PB_LOW, f) for f in PB_FACTORS}))
    return configs
