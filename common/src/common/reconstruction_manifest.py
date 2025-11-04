from typing import Optional

from pydantic import BaseModel, Field


class ReconstructionOptions(BaseModel):
    neightbors_count: Optional[int] = Field(
        default=None,
        description=(
            "How many pose-nearest neighbors to consider when generating image pairs. "
            "Use -1 for exhaustive matching (all pairs). If None, a sensible default is used (currently 12). "
            "Smaller values reduce weak overlaps and speed up matching at the cost of some coverage."
        ),
    )
    max_keypoints_per_image: Optional[int] = Field(
        default=None,
        description=(
            "Upper bound on detected local features per image (SuperPoint). "
            "Reduces descriptor/match volume and downstream 3D points; too small can hurt registration."
        ),
    )
    ransac_max_error: Optional[float] = Field(
        default=None,
        description=(
            "Two-view RANSAC inlier threshold (pixels) used by verify_matches(). "
            "Lower = stricter inlier test; removes borderline correspondences before SfM."
        ),
    )
    ransac_min_inlier_ratio: Optional[float] = Field(
        default=None,
        description=(
            "Two-view RANSAC minimum inlier ratio to accept the model. "
            "Higher = reject more weak pairs; typically 0.10–0.20 for stricter matching."
        ),
    )
    use_prior_position: Optional[bool] = Field(
        default=None,
        description=(
            "If true, use position priors during registration. "
            "This leverages PosePrior(position=...) written into the database to guide image registration."
        ),
    )
    triangulation_minimum_angle: Optional[float] = Field(
        default=None,
        description=(
            "Minimum triangulation angle (degrees). Applied at creation time (triangulation.min_angle) and "
            "again during mapper filtering (mapper.filter_min_tri_angle). Raising it removes low-parallax points."
        ),
    )
    triangulation_complete_max_reprojection_error: Optional[float] = Field(
        default=None,
        description=(
            "Triangulation-time gate (pixels) for COMPLETING tracks into new 3D points "
            "(triangulation.complete_max_reproj_error). Lower → fewer borderline new points."
        ),
    )
    triangulation_merge_max_reprojection_error: Optional[float] = Field(
        default=None,
        description=(
            "Triangulation-time gate (pixels) for MERGING near-duplicate 3D points "
            "(triangulation.merge_max_reproj_error). Lower → fewer merges; higher → more aggressive deduplication."
        ),
    )
    mapper_filter_max_reprojection_error: Optional[float] = Field(
        default=None,
        description=(
            "Mapper-level **post-BA outlier** threshold (pixels) (mapper.filter_max_reproj_error). "
            "Points exceeding this after local/global BA are culled. "
            "This is NOT a triangulation accept threshold."
        ),
    )
    bundle_adjustment_refine_sensor_from_rig: Optional[bool] = Field(
        default=None,
        description=(
            "If true, refine per-camera extrinsics within the rig during BA "
            "(ba_refine_sensor_from_rig). Useful when rig calibration is approximate."
        ),
    )
    bundle_adjustment_refine_focal_length: Optional[bool] = Field(
        default=None, description="If true, refine the camera focal length during BA (ba_refine_focal_length)."
    )
    bundle_adjustment_refine_principal_point: Optional[bool] = Field(
        default=None, description="If true, refine the camera principal point during BA (ba_refine_principal_point)."
    )
    bundle_adjustment_refine_additional_params: Optional[bool] = Field(
        default=None,
        description=(
            "If true, refine model-specific additional parameters during BA (ba_refine_extra_params), "
            "e.g., radial/tangential distortion where applicable."
        ),
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


class ReconstructionManifest(BaseModel):
    capture_id: str
    status: str
    error: Optional[str] = Field(default=None)
    options: ReconstructionOptions
    metrics: ReconstructionMetrics
