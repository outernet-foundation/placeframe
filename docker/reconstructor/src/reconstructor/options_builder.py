from __future__ import annotations

from dataclasses import dataclass

from core.reconstruction_options import ReconstructionOptions
from pycolmap import BundleAdjustmentOptions, IncrementalPipelineOptions, TwoViewGeometryOptions


@dataclass(frozen=True)
class PairVioEssentialMatrixOptions:
    max_rotation_disagreement_deg: float
    max_translation_direction_deg: float
    min_baseline_m: float


class OptionsBuilder:
    def __init__(self, options: ReconstructionOptions, is_multi_camera_capture: bool):
        self.options = options
        self.is_multi_camera_capture = is_multi_camera_capture

    def two_view_geometry_options(self):
        two_view_geometry_options = TwoViewGeometryOptions()
        two_view_geometry_options.compute_relative_pose = True
        if self.options.deterministic_seed is not None:
            two_view_geometry_options.ransac.random_seed = self.options.deterministic_seed
        two_view_geometry_options.ransac.max_error = self.options.ransac_max_error
        two_view_geometry_options.ransac.min_inlier_ratio = self.options.ransac_min_inlier_ratio
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

    def retrieval_min_score(self):
        return self.options.retrieval_min_score

    def pose_prior_position_sigma_m(self):
        return self.options.pose_prior_position_sigma_m

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
        incremental_pipeline_options.ba_refine_sensor_from_rig = False
        incremental_pipeline_options.ba_refine_focal_length = True
        incremental_pipeline_options.ba_refine_principal_point = False
        incremental_pipeline_options.ba_refine_extra_params = True
        incremental_pipeline_options.ba_global_frames_ratio = self.options.bundle_adjustment_global_frames_ratio
        incremental_pipeline_options.ba_global_max_refinements = 3
        incremental_pipeline_options.ba_global_function_tolerance = (
            self.options.bundle_adjustment_global_function_tolerance
        )
        incremental_pipeline_options.mapper.ba_global_ignore_redundant_points3D = True
        if constant_rigs:
            incremental_pipeline_options.constant_rigs = constant_rigs

        incremental_pipeline_options.triangulation.min_angle = self.options.triangulation_minimum_angle
        incremental_pipeline_options.mapper.filter_min_tri_angle = self.options.triangulation_minimum_angle
        incremental_pipeline_options.mapper.filter_max_reproj_error = self.options.mapper_filter_max_reprojection_error

        return incremental_pipeline_options

    def final_bundle_adjustment_options(self):
        bundle_adjustment_options = BundleAdjustmentOptions()
        bundle_adjustment_options.refine_sensor_from_rig = not self.is_multi_camera_capture
        bundle_adjustment_options.refine_focal_length = True
        bundle_adjustment_options.refine_principal_point = False
        bundle_adjustment_options.refine_extra_params = True
        if self.options.deterministic_seed is not None:
            bundle_adjustment_options.ceres.solver_options.num_threads = 1
        return bundle_adjustment_options
