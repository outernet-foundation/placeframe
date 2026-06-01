from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ReconstructionOptions(BaseModel):
    deterministic_seed: Optional[int] = Field(
        default=None,
        description="PRNG seed and single-threaded gate for reproducible reconstructions; None means non-deterministic.",
    )
    keyframe_min_distance_m: float = Field(
        default=0.2,
        description="Minimum VIO-translation distance (meters) between successive kept keyframes; frames closer to the last kept frame than this are dropped before feature extraction.",
    )
    sequential_window_m: float = Field(
        default=3.0,
        description="VIO-path-distance window (meters) used to enumerate same-rig sequential pairs. For each keyframe, every later keyframe whose cumulative segment-by-segment path length along the VIO trajectory is within this many metres is paired with it. Path distance — not straight-line distance — so doubling back along the trajectory (e.g. corridor return pass) walks away from earlier frames rather than landing on them. Scales the temporal match-graph backbone to actual device motion: stationary stretches shrink to almost no extra pairs, fast-motion stretches grow to cover the swept arc.",
    )
    retrieval_neighbors: int = Field(
        default=0,
        description="Top-K most-similar images (DIR cosine) paired with each image for loop closures; 0 disables retrieval.",
    )
    retrieval_min_score: float = Field(
        default=0.35,
        description="Minimum cosine similarity for retrieval candidates; drops visually-weak matches before BA.",
    )
    ransac_max_error: float = Field(
        default=2.0,
        description="Two-view RANSAC inlier threshold in pixels; lower is stricter.",
    )
    ransac_min_inlier_ratio: float = Field(
        default=0.25,
        description="Two-view RANSAC minimum inlier ratio to accept a pair's geometry.",
    )
    two_view_min_num_inliers: int = Field(
        default=30,
        description="Absolute minimum inlier count for a verified two-view geometry, applied alongside ransac_min_inlier_ratio. Raised above pycolmap's SIFT-era default of 15 to reject small false-positive clusters on repetitive structure.",
    )
    triangulation_minimum_angle: float = Field(
        default=3.0,
        description="Minimum triangulation angle in degrees; applied at creation time and again in mapper filtering.",
    )
    mapper_filter_max_reprojection_error: float = Field(
        default=2.0,
        description="Post-BA outlier reprojection threshold in pixels; points exceeding it are culled.",
    )
    bundle_adjustment_global_frames_ratio: float = Field(
        default=1.5,
        description="Frame-count growth ratio that triggers a global BA event; larger = fewer events.",
    )
    bundle_adjustment_global_function_tolerance: float = Field(
        default=1e-3,
        description="Ceres function tolerance for global BA exit; larger = earlier exit on residual plateaus.",
    )
    pose_prior_position_sigma_m: float = Field(
        default=0.05,
        description="Standard deviation in meters for the position prior covariance; consumed only by monocular captures (multi-camera captures run priors-off).",
    )
    pair_vio_em_max_rotation_disagreement_deg: float = Field(
        default=25.0,
        description="At two-view verification time, every sequential pair whose VIO poses carry rotation has its essential-matrix relative pose compared against the VIO-implied relative pose. The pair is rejected (its two-view geometry deleted from the database) when the angle between the two rotations exceeds this threshold. Sequential-only because retrieval pairs span genuine loop closures where VIO drift can disagree with the essential matrix legitimately, and intra-frame stereo is already validated by the rig constraint. 0 disables. Applied only to pairs with 7-column VIO rows (quaternion present).",
    )
    pair_vio_em_max_translation_direction_deg: float = Field(
        default=60.0,
        description="Companion to pair_vio_em_max_rotation_disagreement_deg: bounds the angle between the essential-matrix translation direction (camera-1 origin direction in camera-2) and the VIO-implied translation direction for the same camera pair. Skipped when the essential-matrix baseline is below pair_vio_em_min_baseline_m, where translation direction is ill-conditioned. 0 disables.",
    )
    pair_vio_em_min_baseline_m: float = Field(
        default=0.3,
        description="Essential-matrix-baseline floor below which the VIO-vs-essential-matrix translation-direction component is skipped. Near-co-located camera pairs (intra-rig stereo timing jitter, hover frames in slow motion) have ill-defined essential-matrix translation direction; the rotation component still applies.",
    )
    max_keypoints_per_image: int = Field(
        default=2500,
        description="Maximum ALIKED keypoints retained per image.",
    )
    held_out_frame_timestamps: Optional[list[int]] = Field(
        default=None,
        description="Frame timestamps (ms) to exclude from this reconstruction so they can later be localized as held-out queries.",
    )
