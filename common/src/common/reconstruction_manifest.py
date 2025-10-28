from typing import Optional

from pydantic import BaseModel, Field


class ReconstructionOptions(BaseModel):
    neightbors_count: Optional[int] = Field(
        default=None,
        description="Number of neighboring images to consider during reconstruction. If not set, exhaustive matching is used.",
    )
    max_keypoints_per_image: Optional[int] = Field(
        default=None, description="Maximum number of keypoints to detect and use per image during reconstruction."
    )
    use_prior_position: Optional[bool] = Field(
        default=None, description="Whether to use prior position during reconstruction."
    )
    ba_refine_sensor_from_rig: Optional[bool] = Field(
        default=None, description="Whether to refine sensor from rig during bundle adjustment."
    )
    ba_refine_focal_length: Optional[bool] = Field(
        default=None, description="Whether to refine focal length during bundle adjustment."
    )
    ba_refine_principal_point: Optional[bool] = Field(
        default=None, description="Whether to refine principal point during bundle adjustment."
    )
    ba_refine_extra_params: Optional[bool] = Field(
        default=None, description="Whether to refine extra parameters during bundle adjustment."
    )


class ReconstructionMetrics(BaseModel):
    total_images: Optional[int] = Field(default=None, description="Total number of images in the capture.")
    registered_images: Optional[int] = Field(
        default=None, description="Number of images successfully registered in the reconstruction."
    )
    registration_rate: Optional[float] = Field(
        default=None, description="Percentage of images registered in the reconstruction."
    )
    num_3d_points: Optional[int] = Field(
        default=None, description="Total number of 3D points reconstructed in the reconstruction."
    )
    average_keypoints_per_image: Optional[float] = Field(
        default=None, description="Average number of keypoints detected per image in the reconstruction."
    )
    reprojection_pixel_error_50th_percentile: Optional[float] = Field(
        default=None, description="50th percentile of reprojection pixel error across all 3D points."
    )
    reprojection_pixel_error_90th_percentile: Optional[float] = Field(
        default=None, description="90th percentile of reprojection pixel error across all 3D points."
    )
    track_length_50th_percentile: Optional[float] = Field(default=None, description="50th percentile of track length.")
    percent_tracks_with_length_greater_than_or_equal_to_3: Optional[float] = Field(
        default=None, description="Percentage of tracks with length greater than or equal to 3."
    )


class ReconstructionManifest(BaseModel):
    capture_id: str
    status: str
    error: Optional[str] = Field(default=None)
    options: ReconstructionOptions
    metrics: ReconstructionMetrics
