from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ReconstructionOptions(BaseModel):
    random_seed: Optional[int] = Field(default=None, description="Random seed to use (for deterministic behavior).")
    single_threaded: Optional[bool] = Field(
        default=None, description="If true, run reconstruction in single-threaded mode (for deterministic behavior)."
    )
    neighbors_count: Optional[int] = Field(
        default=None,
        description=(
            "How many pose-nearest neighbors to consider when generating image pairs. "
            "Use -1 for exhaustive matching (all pairs). If None, a sensible default is used (currently 12). "
            "Smaller values reduce weak overlaps and speed up matching at the cost of some coverage."
        ),
    )
    rotation_threshold: Optional[float] = Field(
        default=None,
        description=(
            "Rotation angle threshold (degrees) for considering two images as neighbors when generating image pairs. "
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
    rig_verification: Optional[bool] = Field(
        default=None,
        description=(
            "If true, perform rig-based verification during feature matching and two-view geometry verification. "
            "Requires images to be tagged with rig/camera IDs."
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
    compression_opq_number_of_subvectors: Optional[int] = Field(
        default=None, description="Number of subvectors for OPQ compression."
    )
    compression_opq_number_of_bits_per_subvector: Optional[int] = Field(
        default=None, description="Number of bits per subvector for OPQ compression."
    )
    compression_opq_number_of_training_iterations: Optional[int] = Field(
        default=None, description="Number of training iterations for OPQ compression."
    )
    pose_prior_position_sigma_m: Optional[float] = Field(
        default=None,
        description=(
            "Standard deviation (meters) for position priors when writing PosePrior to the database. "
            "Smaller values = stronger priors."
        ),
    )
