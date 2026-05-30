from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class PhaseTiming(BaseModel):
    phase: str = Field(description="ReconstructionStatus value of the phase, e.g. 'extracting_features'.")
    duration_seconds: float = Field(
        description="Wall-clock seconds the phase spent in-flight, measured between the publisher's set_phase boundaries."
    )


class ReconstructionMetrics(BaseModel):
    total_images: Optional[int] = Field(
        default=None, description="Total number of input images considered for this reconstruction run."
    )
    registered_images: Optional[int] = Field(
        default=None, description="Number of images successfully registered into the final model."
    )
    registration_rate: Optional[float] = Field(
        default=None,
        description=(
            "Registration rate in percent: 100 × (registered_images / total_images). "
            "Computed after selecting the best reconstruction (max registered images)."
        ),
    )
    num_3d_points: Optional[int] = Field(
        default=None, description="Count of 3D points in the selected 'best' reconstruction."
    )
    average_keypoints_per_image: Optional[float] = Field(
        default=None,
        description=(
            "Average number of detected keypoints per image (after ALIKED extraction), computed across all images."
        ),
    )
    reprojection_pixel_error_50th_percentile: Optional[float] = Field(
        default=None,
        description=(
            "Median (50th percentile) reprojection error in pixels across all valid 2D observations "
            "in registered images, measured using image.project_point(point3D.xyz) vs. observed 2D keypoint."
        ),
    )
    reprojection_pixel_error_90th_percentile: Optional[float] = Field(
        default=None,
        description=(
            "90th percentile reprojection error in pixels across all valid 2D observations, "
            "computed the same way as the median."
        ),
    )
    track_length_50th_percentile: Optional[float] = Field(
        default=None,
        description=(
            "Median (50th percentile) track length across 3D points in the selected model. "
            "Track length = number of distinct images observing the point."
        ),
    )
    percent_tracks_with_length_greater_than_or_equal_to_3: Optional[float] = Field(
        default=None,
        description=(
            "Percentage of 3D points whose track length is ≥ 3 (a common robustness threshold). "
            "Computed as 100 × (#points with length≥3 / #points)."
        ),
    )
    all_verified_matches: Optional[int] = Field(
        default=None, description="Total number of verified matches across all image pairs."
    )
    all_verified_match_rate: Optional[float] = Field(
        default=None, description="Percentage of verified matches across all image pairs."
    )
    all_verified_match_inliers_mean: Optional[float] = Field(
        default=None, description="Mean number of inliers for all verified matches."
    )
    all_verified_match_inliers_median: Optional[float] = Field(
        default=None, description="Median number of inliers for all verified matches."
    )
    stereo_verified_matches: Optional[int] = Field(
        default=None, description="Number of verified matches for stereo pairs (same frame, different sensors)."
    )
    stereo_verified_match_rate: Optional[float] = Field(
        default=None, description="Percentage of verified matches for stereo pairs."
    )
    stereo_verified_match_inliers_mean: Optional[float] = Field(
        default=None, description="Mean number of inliers for verified matches for stereo pairs."
    )
    stereo_verified_match_inliers_median: Optional[float] = Field(
        default=None, description="Median number of inliers for verified matches for stereo pairs."
    )
    same_sensor_verified_matches: Optional[int] = Field(
        default=None, description="Number of verified matches for same-sensor pairs (across frames)."
    )
    same_sensor_verified_match_rate: Optional[float] = Field(
        default=None, description="Percentage of verified matches for same-sensor pairs."
    )
    same_sensor_verified_match_inliers_mean: Optional[float] = Field(
        default=None, description="Mean number of inliers for verified matches for same-sensor pairs."
    )
    same_sensor_verified_match_inliers_median: Optional[float] = Field(
        default=None, description="Median number of inliers for verified matches for same-sensor pairs."
    )
    cross_sensor_verified_matches: Optional[int] = Field(
        default=None, description="Number of verified matches for cross-sensor pairs (across frames)."
    )
    cross_sensor_verified_match_rate: Optional[float] = Field(
        default=None, description="Percentage of verified matches for cross-sensor pairs."
    )
    cross_sensor_verified_match_inliers_mean: Optional[float] = Field(
        default=None, description="Mean number of inliers for verified matches for cross-sensor pairs."
    )
    cross_sensor_verified_match_inliers_median: Optional[float] = Field(
        default=None, description="Median number of inliers for verified matches for cross-sensor pairs."
    )
    map_image_count: Optional[int] = Field(
        default=None, description="Number of registered images in the reconstruction."
    )
    map_point_count: Optional[int] = Field(
        default=None, description="Number of triangulated 3D points in the reconstruction."
    )
    map_avg_track_length: Optional[float] = Field(
        default=None, description="Mean number of image observations per 3D point. Coarse density-of-evidence proxy."
    )
    map_viewpoint_diversity: Optional[float] = Field(
        default=None,
        description=(
            "1 - |mean(unit viewing direction)| across registered cameras. Zero when all cameras face the "
            "same way; approaches one as viewing directions spread uniformly. Discriminates panoramic sweeps "
            "from single-viewpoint maps even when the rest of the metrics agree."
        ),
    )
    gravity_aligned_in_map_frame: Optional[bool] = Field(
        default=None,
        description=(
            "True when the map frame's vertical axis was aligned to gravity using per-frame gravity "
            "samples; False when no samples were available and only origin-shift was applied."
        ),
    )
    gravity_sample_count: Optional[int] = Field(
        default=None,
        description="Number of registered frames that contributed gravity samples to the map-frame alignment.",
    )
    truth_alignment_rms_residual_m: Optional[float] = Field(
        default=None,
        description=(
            "RMS over registered cameras of ||T·c_map - c_truth|| in meters, where T is the rigid Umeyama "
            "alignment from map to truth applied during reconstruction. Diagnostic for VIO-truth quality: "
            "small (~cm) means the truth poses are internally consistent with the COLMAP geometry; large "
            "values indicate VIO drift, scale errors, or other capture-time pose noise that disqualifies "
            "the capture from calibration."
        ),
    )
    truth_alignment_max_residual_m: Optional[float] = Field(
        default=None,
        description=(
            "Maximum over registered cameras of ||T·c_map - c_truth|| in meters. Companion to the RMS "
            "field; surfaces single-frame outliers that the RMS would smooth over."
        ),
    )
    phase_timings: Optional[list[PhaseTiming]] = Field(
        default=None,
        description=(
            "Per-phase wall-clock durations in execution order, captured at each ReconstructionPublisher "
            "set_phase boundary. Useful for after-the-fact attribution of total reconstruction time across "
            "feature extraction, OPQ/PQ training, matching, geometric verification, and incremental mapping."
        ),
    )
    pipeline_version: Optional[str] = Field(
        default=None,
        description=(
            "Content-addressed hash of the reconstructor image's build context (RECONSTRUCTOR_SHA, computed by "
            "build_scripts.placeframe.context_sha.compute_service_shas) that produced this reconstruction. "
            "None on rows whose manifest was created before the lease succeeded. Mirrors the localizer's "
            "LocalizationMetrics.pipeline_version contract."
        ),
    )
