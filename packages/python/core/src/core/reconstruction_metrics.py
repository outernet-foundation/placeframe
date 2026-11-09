from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class PhaseTiming(BaseModel):
    phase: str = Field(description="ReconstructionStatus value of the phase, e.g. 'extracting_features'.")
    duration_seconds: float = Field(description="Wall-clock seconds the phase spent in-flight.")


class ReconstructionMetrics(BaseModel):
    reprojection_pixel_error_50th_percentile: Optional[float] = Field(
        default=None,
        description="Median reprojection error in pixels across all valid 2D observations in registered images.",
    )
    reprojection_pixel_error_90th_percentile: Optional[float] = Field(
        default=None,
        description="90th percentile reprojection error in pixels across all valid 2D observations.",
    )
    track_length_50th_percentile: Optional[float] = Field(
        default=None,
        description="Median number of distinct images observing each 3D point.",
    )
    all_verified_matches: Optional[int] = Field(
        default=None, description="Total number of verified matches across all image pairs."
    )
    all_verified_match_rate: Optional[float] = Field(
        default=None, description="Percentage of image pairs that passed two-view geometry verification."
    )
    all_verified_match_inliers_mean: Optional[float] = Field(
        default=None, description="Mean inlier count among verified image pairs."
    )
    all_verified_match_inliers_median: Optional[float] = Field(
        default=None, description="Median inlier count among verified image pairs."
    )
    stereo_verified_matches: Optional[int] = Field(
        default=None, description="Number of verified stereo pairs (same frame, different sensors)."
    )
    stereo_verified_match_rate: Optional[float] = Field(
        default=None, description="Percentage of stereo pairs that passed verification."
    )
    stereo_verified_match_inliers_mean: Optional[float] = Field(
        default=None, description="Mean inlier count among verified stereo pairs."
    )
    stereo_verified_match_inliers_median: Optional[float] = Field(
        default=None, description="Median inlier count among verified stereo pairs."
    )
    map_image_count: Optional[int] = Field(
        default=None, description="Number of registered images in the reconstruction."
    )
    map_point_count: Optional[int] = Field(
        default=None, description="Number of triangulated 3D points in the reconstruction."
    )
    map_avg_track_length: Optional[float] = Field(
        default=None, description="Mean number of image observations per 3D point."
    )
    map_viewpoint_diversity: Optional[float] = Field(
        default=None,
        description="1 minus the magnitude of the mean unit viewing direction across registered cameras; 0 means uniform direction, approaches 1 as viewpoints spread.",
    )
    gravity_aligned_in_map_frame: Optional[bool] = Field(
        default=None,
        description="True when per-frame gravity samples aligned the map's vertical axis; False when no samples were available and only origin-shift was applied.",
    )
    gravity_sample_count: Optional[int] = Field(
        default=None,
        description="Number of registered frames that contributed gravity samples to the map-frame alignment.",
    )
    prior_drift_residual_rms_m: Optional[float] = Field(
        default=None,
        description="RMS residual in meters of a rigid Umeyama fit from map camera centers to VIO position priors; None for multi-camera captures, which run priors-off and carry no per-frame positions.",
    )
    prior_drift_residual_max_m: Optional[float] = Field(
        default=None,
        description="Maximum residual in meters of the same Umeyama fit; surfaces single-frame outliers the RMS smooths over.",
    )
    imu_scale_applied: Optional[bool] = Field(
        default=None,
        description="True when the capture's own IMU (an Insta360 .insv import) scaled the map to metres and levelled it to true gravity; False when the fit ran but failed its checks, leaving the map in arbitrary units; None when the capture carries no IMU.",
    )
    imu_scale_rejected_because: Optional[str] = Field(
        default=None,
        description="Why the IMU fit was not applied (which check failed, or why it could not run); None when it was applied or never ran.",
    )
    imu_scale_m_per_unit: Optional[float] = Field(
        default=None,
        description="Metres per map unit the IMU fit found for the map as SfM built it, applied or not.",
    )
    imu_scale_sigma_m_per_unit: Optional[float] = Field(
        default=None, description="Standard error of imu_scale_m_per_unit from the least-squares fit."
    )
    imu_sync_residual_deg: Optional[float] = Field(
        default=None,
        description="Median angle between the gyro's turn and the map's turn over each keyframe interval after syncing; ~0.1 deg when the map follows the camera body.",
    )
    imu_free_gravity_mps2: Optional[float] = Field(
        default=None,
        description="Gravity's magnitude when the IMU fit leaves it free, in m/s^2; near 9.81 when the sync and the map are sound.",
    )
    imu_scale_drift_p_value: Optional[float] = Field(
        default=None,
        description="Chi-square p-value that one scale explains every 30 s window of the walk; small means the scale drifts along it. None with fewer than two windows.",
    )
    phase_timings: Optional[list[PhaseTiming]] = Field(
        default=None,
        description="Per-phase wall-clock durations in execution order, captured at each set_phase boundary.",
    )
    pipeline_version: Optional[str] = Field(
        default=None,
        description="RECONSTRUCTOR_SHA of the image that produced this reconstruction.",
    )
