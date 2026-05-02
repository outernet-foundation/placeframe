from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ReconMetrics(BaseModel):
    total_images: int | None
    registered_images: int | None
    registration_rate: float | None
    num_3d_points: int | None
    reproj_error_50th: float | None
    reproj_error_90th: float | None
    map_image_count: int | None
    map_point_count: int | None
    map_avg_track_length: float | None
    map_bounding_volume_m3: float | None
    map_viewpoint_diversity: float | None


class ReconstructionResult(BaseModel):
    location: str
    device_type: str
    capture_name: str
    config_idx: int
    options: dict[str, Any] | None
    reconstruction_id: str | None
    succeeded: bool
    metrics: ReconMetrics | None = None
    loc_map_id: str | None = None
    is_indoor: bool | None = None
    truth_alignment_rms_residual_m: float | None = None
    truth_alignment_max_residual_m: float | None = None


class LocalizationResult(BaseModel):
    location: str
    recon_device_type: str
    recon_capture_name: str
    recon_config_idx: int
    reconstruction_id: str
    query_device_type: str
    query_capture_name: str
    query_frame_timestamp: str
    query_image_diagonal_px: float
    is_cross_device: bool
    retrieval_top_k: int | None
    ransac_threshold: float | None
    succeeded: bool
    inlier_ratio: float | None = None
    reproj_error_median: float | None = None
    num_inliers: int | None = None
    num_correspondences: int | None = None
    num_matches: int | None = None
    inlier_coverage: float | None = None
    pnp_covariance: list[list[float]] | None = None
    err_t_m: float | None = None
    err_r_deg: float | None = None
    # 6-D SE(3) twist: log(P_truth · P_estimated⁻¹) in (translation, rotation) tangent
    # coordinates. Feeds the Σ_meas α/β fit in scripts/fit_calibration.py.
    se3_residual: list[float] | None = None


class E2EResults(BaseModel):
    run_timestamp: str
    reconstructions: list[ReconstructionResult]
    localizations: list[LocalizationResult]
