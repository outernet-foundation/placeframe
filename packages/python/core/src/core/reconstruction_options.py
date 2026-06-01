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
    sequential_window: int = Field(
        default=20,
        description="Per-frame count of temporally-adjacent neighbours (each side) paired within a rig for the temporal match-graph backbone.",
    )
    spatial_neighbors: int = Field(
        default=25,
        description="Top-K closest in-range neighbours by VIO-position paired with each frame; 0 disables spatial pairing. Adjacent frames already covered by sequential pairing are deduped at union time.",
    )
    spatial_max_distance_m: float = Field(
        default=6.0,
        description="Maximum VIO-position distance (meters) for spatial pairs; in-range neighbours are then capped at spatial_neighbors closest. No-op when positions are absent.",
    )
    retrieval_neighbors: int = Field(
        default=20,
        description="Top-K most-similar images (DIR cosine) paired with each image for loop closures; 0 disables retrieval.",
    )
    retrieval_min_distance_m: float = Field(
        default=1.0,
        description="Minimum VIO-position distance for retrieval pairs; drops candidates already covered by sequential pairing. No-op when positions are absent.",
    )
    pair_max_displacement_scene_m: float = Field(
        default=10.0,
        description="Max plausible scene-radius component of the displacement bound used to reject any candidate pair (a,b) whose VIO straight-line displacement exceeds the bound. Combined with pair_max_displacement_drift_rate_m_per_s: a pair is rejected when |vio_pos(b)−vio_pos(a)| > pair_max_displacement_scene_m + pair_max_displacement_drift_rate_m_per_s · |t_b−t_a|. Applied uniformly across all pair sources; stereo and short-temporal pairs trivially satisfy any reasonable bound. No-op when positions are absent.",
    )
    pair_max_displacement_drift_rate_m_per_s: float = Field(
        default=0.1,
        description="VIO drift-rate slack added to the displacement bound per second of time gap between the two frames of a candidate pair. Lets long-temporal-gap true loop closures survive accumulated drift while still rejecting short-temporal-gap aliased pairs (e.g. retrieval matches between physically distant frames seconds apart). Calibrate per device class against post-hoc VIO↔recon residuals.",
    )
    retrieval_min_score: float = Field(
        default=0.35,
        description="Minimum cosine similarity for retrieval candidates; drops visually-weak matches before BA.",
    )
    retrieval_covisibility_window: int = Field(
        default=3,
        description="Half-width (in temporal keyframe indices) of the neighborhood used to validate retrieval pairs against perceptual aliasing. A pair (A,B) is supported by another retrieval pair (A',B') iff both endpoints fall within this window of the original pair on their respective trajectories.",
    )
    retrieval_covisibility_min_support: int = Field(
        default=2,
        description="Minimum count of supporting retrieval pairs within retrieval_covisibility_window required for a retrieval candidate to be kept; aliased pairs (e.g. two similar paintings in different rooms) appear as singletons and get dropped, while true loop closures appear as bands and survive. 0 disables the filter.",
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
    retrieval_min_inlier_ratio: float = Field(
        default=0.40,
        description="Two-view RANSAC minimum inlier ratio for retrieval-sourced pairs only; stricter than the sequential/spatial/intra-frame floor because visually-similar-but-spatially-distant indoor regions can fabricate plausible-looking essential matrices.",
    )
    retrieval_min_num_inliers: int = Field(
        default=50,
        description="Absolute minimum inlier count for retrieval-sourced pair geometries; stricter than the global two_view_min_num_inliers because retrieval is the lone pair source where visual similarity does not imply spatial proximity.",
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
    vio_check_max_disagreement_m: float = Field(
        default=1.0,
        description="Reject a registration when the disagreement (meters) between the local-Umeyama-predicted recon position and the recon position COLMAP just assigned exceeds this. Also used as the LO-RANSAC inlier threshold when fitting the local Sim3 from VIO neighbors.",
    )
    max_keypoints_per_image: int = Field(
        default=2500,
        description="Maximum ALIKED keypoints retained per image.",
    )
    held_out_frame_timestamps: Optional[list[int]] = Field(
        default=None,
        description="Frame timestamps (ms) to exclude from this reconstruction so they can later be localized as held-out queries.",
    )
