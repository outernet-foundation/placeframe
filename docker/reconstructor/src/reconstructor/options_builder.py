from __future__ import annotations

from dataclasses import dataclass

from core.reconstruction_options import ReconstructionOptions
from pycolmap import BundleAdjustmentOptions, IncrementalPipelineOptions, TwoViewGeometryOptions


@dataclass(frozen=True)
class PairPoseGraphOptions:
    max_rotation_disagreement_deg: float
    max_translation_direction_deg: float
    min_baseline_m: float
    min_registered_frames: int


@dataclass(frozen=True)
class PairVioEssentialMatrixOptions:
    max_rotation_disagreement_deg: float
    max_translation_direction_deg: float
    min_baseline_m: float


# Hardcoded pipeline knobs. Kept out of ReconstructionOptions because either there is one
# correct answer or the option was never exercised by any caller.
BUNDLE_ADJUSTMENT_INCREMENTAL_REFINE_SENSOR_FROM_RIG = False
BUNDLE_ADJUSTMENT_REFINE_FOCAL_LENGTH = True
BUNDLE_ADJUSTMENT_REFINE_PRINCIPAL_POINT = False
BUNDLE_ADJUSTMENT_REFINE_ADDITIONAL_PARAMS = True
BUNDLE_ADJUSTMENT_GLOBAL_MAX_REFINEMENTS = 3
BUNDLE_ADJUSTMENT_IGNORE_REDUNDANT_POINTS_3D = True


class OptionsBuilder:
    def __init__(self, options: ReconstructionOptions, is_multi_camera_capture: bool):
        self.options = options
        # Multi-camera captures run priors-off in BA (PosePrior loss disabled, sensor_from_rig pinned
        # so the stereo baseline survives the final standalone BA's 7-DOF gauge freedom) but
        # priors-on in pair generation and keyframe selection. See SPEC.md "Priors-on in pair gen,
        # priors-off in BA for multi-camera rigs".
        self.is_multi_camera_capture = is_multi_camera_capture

    def two_view_geometry_options(self):
        two_view_geometry_options = TwoViewGeometryOptions()
        two_view_geometry_options.compute_relative_pose = True
        if self.options.deterministic_seed is not None:
            two_view_geometry_options.ransac.random_seed = self.options.deterministic_seed
        two_view_geometry_options.ransac.max_error = self.options.ransac_max_error
        two_view_geometry_options.ransac.min_inlier_ratio = self.options.ransac_min_inlier_ratio
        # max_num_trials=500 (from 10000) and confidence=0.95 (from 0.999) collapse the
        # low-inlier-ratio tail of RANSAC iterations to a fraction of stock. At min_inlier_ratio=0.25
        # with confidence=0.95, the adaptive trial count terminates around ~189 trials; the 500-trial
        # ceiling only bites below the cutoff (which fails on inlier-ratio anyway). False-rejection
        # probability for true-positive pairs sitting exactly at the cutoff is ~5%.
        two_view_geometry_options.ransac.max_num_trials = 500
        two_view_geometry_options.ransac.confidence = 0.95
        two_view_geometry_options.min_num_inliers = self.options.two_view_min_num_inliers
        two_view_geometry_options.filter_stationary_matches = True
        two_view_geometry_options.stationary_matches_max_error = 4.0
        return two_view_geometry_options

    def keyframe_min_distance_m(self):
        return self.options.keyframe_min_distance_m

    def sequential_window_m(self):
        return self.options.sequential_window_m

    def retrieval_neighbors(self):
        return self.options.retrieval_neighbors

    def retrieval_min_distance_m(self):
        return self.options.retrieval_min_distance_m

    def retrieval_min_score(self):
        return self.options.retrieval_min_score

    def pose_prior_position_sigma_m(self):
        return self.options.pose_prior_position_sigma_m

    def vio_check_max_disagreement_m(self):
        return self.options.vio_check_max_disagreement_m

    def pair_pose_graph_options(self):
        return PairPoseGraphOptions(
            max_rotation_disagreement_deg=self.options.pair_pose_graph_max_rotation_disagreement_deg,
            max_translation_direction_deg=self.options.pair_pose_graph_max_translation_direction_deg,
            min_baseline_m=self.options.pair_pose_graph_min_baseline_m,
            min_registered_frames=self.options.pair_pose_graph_min_registered_frames,
        )

    def pair_vio_essential_matrix_options(self):
        return PairVioEssentialMatrixOptions(
            max_rotation_disagreement_deg=self.options.pair_vio_em_max_rotation_disagreement_deg,
            max_translation_direction_deg=self.options.pair_vio_em_max_translation_direction_deg,
            min_baseline_m=self.options.pair_vio_em_min_baseline_m,
        )

    def max_keypoints_per_image(self):
        return self.options.max_keypoints_per_image

    def incremental_pipeline_options(self, constant_rigs: set[int]):
        incremental_pipeline_options = IncrementalPipelineOptions()

        if self.options.deterministic_seed is not None:
            incremental_pipeline_options.random_seed = self.options.deterministic_seed
            incremental_pipeline_options.triangulation.random_seed = self.options.deterministic_seed
            incremental_pipeline_options.num_threads = 1
            incremental_pipeline_options.mapper.num_threads = 1

        incremental_pipeline_options.use_prior_position = not self.is_multi_camera_capture
        incremental_pipeline_options.ba_refine_sensor_from_rig = BUNDLE_ADJUSTMENT_INCREMENTAL_REFINE_SENSOR_FROM_RIG
        incremental_pipeline_options.ba_refine_focal_length = BUNDLE_ADJUSTMENT_REFINE_FOCAL_LENGTH
        incremental_pipeline_options.ba_refine_principal_point = BUNDLE_ADJUSTMENT_REFINE_PRINCIPAL_POINT
        incremental_pipeline_options.ba_refine_extra_params = BUNDLE_ADJUSTMENT_REFINE_ADDITIONAL_PARAMS
        incremental_pipeline_options.ba_global_frames_ratio = self.options.bundle_adjustment_global_frames_ratio
        incremental_pipeline_options.ba_global_max_refinements = BUNDLE_ADJUSTMENT_GLOBAL_MAX_REFINEMENTS
        incremental_pipeline_options.ba_global_function_tolerance = (
            self.options.bundle_adjustment_global_function_tolerance
        )
        incremental_pipeline_options.mapper.ba_global_ignore_redundant_points3D = (
            BUNDLE_ADJUSTMENT_IGNORE_REDUNDANT_POINTS_3D
        )
        if constant_rigs:
            incremental_pipeline_options.constant_rigs = constant_rigs

        incremental_pipeline_options.triangulation.min_angle = self.options.triangulation_minimum_angle
        incremental_pipeline_options.mapper.filter_min_tri_angle = self.options.triangulation_minimum_angle
        incremental_pipeline_options.mapper.filter_max_reproj_error = self.options.mapper_filter_max_reprojection_error

        return incremental_pipeline_options

    def final_bundle_adjustment_options(self):
        bundle_adjustment_options = BundleAdjustmentOptions()
        bundle_adjustment_options.refine_sensor_from_rig = not self.is_multi_camera_capture
        bundle_adjustment_options.refine_focal_length = BUNDLE_ADJUSTMENT_REFINE_FOCAL_LENGTH
        bundle_adjustment_options.refine_principal_point = BUNDLE_ADJUSTMENT_REFINE_PRINCIPAL_POINT
        bundle_adjustment_options.refine_extra_params = BUNDLE_ADJUSTMENT_REFINE_ADDITIONAL_PARAMS
        if self.options.deterministic_seed is not None:
            bundle_adjustment_options.ceres.solver_options.num_threads = 1
        return bundle_adjustment_options
