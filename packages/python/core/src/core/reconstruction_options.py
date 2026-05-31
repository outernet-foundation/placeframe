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
    retrieval_min_score: float = Field(
        default=0.35,
        description="Minimum cosine similarity for retrieval candidates; drops visually-weak matches before BA.",
    )
    ransac_max_error: float = Field(
        default=2.0,
        description="Two-view RANSAC inlier threshold in pixels; lower is stricter.",
    )
    ransac_min_inlier_ratio: float = Field(
        default=0.15,
        description="Two-view RANSAC minimum inlier ratio to accept a pair's geometry.",
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
    max_keypoints_per_image: int = Field(
        default=2500,
        description="Maximum ALIKED keypoints retained per image.",
    )
    held_out_frame_timestamps: Optional[list[int]] = Field(
        default=None,
        description="Frame timestamps (ms) to exclude from this reconstruction so they can later be localized as held-out queries.",
    )
