from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ReconstructionOptions(BaseModel):
    deterministic_seed: Optional[int] = Field(
        default=None,
        description=(
            "If set, run the reconstruction deterministically: this value is the PRNG seed AND the "
            "pipeline runs single-threaded so thread-scheduling does not introduce non-determinism "
            "between reruns. If None, the reconstruction is non-deterministic (seed unpinned, "
            "threading enabled)."
        ),
    )
    keyframe_parallax_threshold_px: float = Field(
        default=50.0,
        description=(
            "Accumulated median Lucas-Kanade pixel displacement (at 320×240 working resolution) between "
            "successive kept keyframes."
        ),
    )
    sequential_window: int = Field(
        default=10,
        description=(
            "Number of temporally-adjacent frames each side of every frame to pair within a rig. "
            "Generates the temporal backbone of the match graph. Window 10 means each frame pairs "
            "with the next 10 frames in its rig's timestamp order."
        ),
    )
    retrieval_neighbors: int = Field(
        default=20,
        description=(
            "Number of most-similar images (by global descriptor cosine similarity) to pair with "
            "each image after pose-distance and similarity gating. Generates loop-closure pairs "
            "between visually-similar but pose-distant frames. Set to 0 to disable retrieval."
        ),
    )
    retrieval_min_distance_m: float = Field(
        default=1.0,
        description=(
            "Minimum pose-center distance (meters) for retrieval pair candidates. Drops retrieval "
            "matches between frames the VIO prior already places close together — those are covered "
            "by sequential or spatial pairing. Scopes retrieval to genuine loop closures."
        ),
    )
    retrieval_min_score: float = Field(
        default=0.5,
        description=(
            "Minimum cosine similarity (in the L2-normalized DIR descriptor space) for retrieval "
            "pair candidates. Drops the long tail of visually-weak matches that would otherwise "
            "feed BA descriptor-similar-but-non-overlapping correspondences."
        ),
    )
    lightglue_batch_size: int = Field(
        default=16,
        description=(
            "Batch size to use when running LightGlue for feature matching. "
            "Larger batch sizes can improve GPU utilization but require more memory."
        ),
    )
    ransac_max_error: float = Field(
        default=2.0,
        description=(
            "Two-view RANSAC inlier threshold (pixels) used by verify_matches(). "
            "Lower = stricter inlier test; removes borderline correspondences before SfM."
        ),
    )
    ransac_min_inlier_ratio: float = Field(
        default=0.15,
        description=(
            "Two-view RANSAC minimum inlier ratio to accept the model. "
            "Higher = reject more weak pairs; typically 0.10–0.20 for stricter matching."
        ),
    )
    use_prior_position: bool = Field(
        default=True,
        description=(
            "If true, use position priors during registration. "
            "This leverages PosePrior(position=...) written into the database to guide image registration."
        ),
    )
    rig_verification: bool = Field(
        default=True,
        description=(
            "If true, perform rig-based verification during feature matching and two-view geometry verification. "
            "Requires images to be tagged with rig/camera IDs."
        ),
    )
    triangulation_minimum_angle: float = Field(
        default=3.0,
        description=(
            "Minimum triangulation angle (degrees). Applied at creation time (triangulation.min_angle) and "
            "again during mapper filtering (mapper.filter_min_tri_angle). Raising it removes low-parallax points."
        ),
    )
    triangulation_complete_max_reprojection_error: float = Field(
        default=2.0,
        description=(
            "Triangulation-time gate (pixels) for COMPLETING tracks into new 3D points "
            "(triangulation.complete_max_reproj_error). Lower → fewer borderline new points."
        ),
    )
    triangulation_merge_max_reprojection_error: float = Field(
        default=4.0,
        description=(
            "Triangulation-time gate (pixels) for MERGING near-duplicate 3D points "
            "(triangulation.merge_max_reproj_error). Lower → fewer merges; higher → more aggressive deduplication."
        ),
    )
    mapper_filter_max_reprojection_error: float = Field(
        default=2.0,
        description=(
            "Mapper-level **post-BA outlier** threshold (pixels) (mapper.filter_max_reproj_error). "
            "Points exceeding this after local/global BA are culled. "
            "This is NOT a triangulation accept threshold."
        ),
    )
    bundle_adjustment_refine_sensor_from_rig: bool = Field(
        default=False,
        description=(
            "If true, refine per-camera extrinsics within the rig during the incremental "
            "BA loop (ba_refine_sensor_from_rig). The shipped pattern leaves this False, "
            "pins rigs via constant_rigs, and re-enables rig refinement only on the final "
            "standalone BA pass. See docker/reconstructor/SPEC.md for rationale."
        ),
    )
    bundle_adjustment_refine_focal_length: bool = Field(
        default=True,
        description="If true, refine the camera focal length during BA (ba_refine_focal_length).",
    )
    bundle_adjustment_refine_principal_point: bool = Field(
        default=False,
        description="If true, refine the camera principal point during BA (ba_refine_principal_point).",
    )
    bundle_adjustment_refine_additional_params: bool = Field(
        default=True,
        description=(
            "If true, refine model-specific additional parameters during BA (ba_refine_extra_params), "
            "e.g., radial/tangential distortion where applicable."
        ),
    )
    bundle_adjustment_global_frames_ratio: float = Field(
        default=1.5,
        description=(
            "Growth ratio of registered frames after which to trigger a global bundle adjustment "
            "(ba_global_frames_ratio). Larger = fewer global BA events, less wall time, "
            "longer between cleanup passes."
        ),
    )
    bundle_adjustment_global_max_refinements: int = Field(
        default=1,
        description=(
            "Maximum BA refinement passes per global-BA event (ba_global_max_refinements). "
            "Dev default 1; production-quality maps should override to 3 (or higher). See "
            "docker/reconstructor/SPEC.md."
        ),
    )
    bundle_adjustment_global_function_tolerance: float = Field(
        default=1e-3,
        description=(
            "Ceres solver function tolerance for global bundle adjustment "
            "(ba_global_function_tolerance). Larger = earlier exit when residual delta becomes "
            "insignificant."
        ),
    )
    bundle_adjustment_ignore_redundant_points3D: bool = Field(
        default=True,
        description=(
            "If true, solve global BA without redundant 3D points first, then refine pruned points "
            "in a second pass with everything else fixed (mapper.ba_global_ignore_redundant_points3D). "
            "Same final geometry, smaller main problem. Activates only when ≥10 frames are registered."
        ),
    )
    compression_opq_number_of_subvectors: int = Field(
        default=16, description="Number of subvectors for OPQ compression."
    )
    compression_opq_number_of_bits_per_subvector: int = Field(
        default=8, description="Number of bits per subvector for OPQ compression."
    )
    compression_opq_number_of_training_iterations: int = Field(
        default=20, description="Number of training iterations for OPQ compression."
    )
    pose_prior_position_sigma_m: float = Field(
        default=0.05,
        description=(
            "Standard deviation (meters) for position priors when writing PosePrior to the database. "
            "Smaller values = stronger priors."
        ),
    )
    max_keypoints_per_image: int = Field(
        default=2500,
        description=(
            "Maximum number of ALIKED keypoints to retain per image (acts as a safety cap in threshold mode)."
        ),
    )
    held_out_frame_timestamps: Optional[list[int]] = Field(
        default=None,
        description=(
            "Frame timestamps (Unix milliseconds, matching the first column of each rig's frames.csv) "
            "to exclude from this reconstruction. Held-out frames never enter the rig's frame_poses, so "
            "their images are skipped during feature extraction, pair generation, and SfM. Used by "
            "calibration to build a map without specific frames so those frames can later be localized "
            "as held-out queries."
        ),
    )
