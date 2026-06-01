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
    retrieval_min_distance_m: float = Field(
        default=1.0,
        description="Minimum VIO-position distance for retrieval pairs; drops candidates already covered by sequential pairing.",
    )
    pair_min_match_spread: float = Field(
        default=0.08,
        description="Minimum spread of inlier-match keypoint positions, expressed as geometric mean of per-axis standard deviations normalized by image dimensions, taken as the min across the two images. Pairs below the threshold are rejected at the two-view verification stage. Catches the repeated-decor aliasing pattern where matches concentrate on a small set of similar features (e.g. multiple identical artworks in an office) — both images show matches clustered in a tiny region, producing a low spread, while true wide-baseline matches spread across the image. Independent of VIO drift; works monocular. 0 disables the filter.",
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
    retrieval_min_inlier_ratio: float = Field(
        default=0.40,
        description="Two-view RANSAC minimum inlier ratio for retrieval-sourced pairs only; stricter than the sequential/intra-frame-stereo floor because visually-similar-but-spatially-distant indoor regions can fabricate plausible-looking essential matrices.",
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
        default=1e9,
        description="Reject a registration when the disagreement (meters) between the local-Umeyama-predicted recon position and the recon position COLMAP just assigned exceeds this. Also used as the LO-RANSAC inlier threshold when fitting the local Sim3 from VIO neighbors. Disabled by default (1e9 m is effectively infinity for any real capture); the pair-level pose-graph consistency check and the two-phase retrieval ingest are the primary aliasing defenses. Set to a finite value (e.g. 1.0) to gate registrations against VIO drift bounds on captures where the device-reported trajectory is trusted to within a metre.",
    )
    pair_pose_graph_max_rotation_disagreement_deg: float = Field(
        default=15.0,
        description="At per-frame registration time, compare the relative rotation each already-registered partner's two-view geometry implies against the relative rotation the partial reconstruction estimates between the same frames. Partners exceeding this angular threshold are flagged poisoned and their contributing matches are excised from the new frame's observations before the next BA pass. Independent of VIO; uses the pose graph itself as the consistency oracle. 0 disables.",
    )
    pair_pose_graph_max_translation_direction_deg: float = Field(
        default=30.0,
        description="Companion to pair_pose_graph_max_rotation_disagreement_deg: bounds the angle between the unit translation direction the two-view geometry implies and the unit translation direction implied by the partial reconstruction's pose estimates of the two frames. Two-view geometry is scale-free in the monocular case so only direction is compared. Skipped when the estimated baseline is below pair_pose_graph_min_baseline_m. 0 disables.",
    )
    pair_pose_graph_min_baseline_m: float = Field(
        default=0.3,
        description="Estimated-baseline floor below which the translation-direction component of the pose-graph consistency check is skipped. Near-co-located frames have ill-defined translation direction; the rotation component still applies.",
    )
    pair_pose_graph_min_registered_frames: int = Field(
        default=15,
        description="Minimum number of registered frames in the partial reconstruction before pair_pose_graph_* consistency checks fire. Early in the reconstruction the pose graph is too soft to be a reliable oracle; the front-door filters (covisibility, drift budget, vio_check) carry the load until the graph stiffens.",
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
