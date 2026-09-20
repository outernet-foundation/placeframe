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
    phase_timings: Optional[list[PhaseTiming]] = Field(
        default=None,
        description="Per-phase wall-clock durations in execution order, captured at each set_phase boundary.",
    )
    pipeline_version: Optional[str] = Field(
        default=None,
        description="RECONSTRUCTOR_SHA of the image that produced this reconstruction.",
    )
