from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


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
            "Average number of detected keypoints per image (after SuperPoint extraction), computed across all images."
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
