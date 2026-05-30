from __future__ import annotations

from core.reconstruction_options import ReconstructionOptions
from pycolmap import BundleAdjustmentOptions, FeatureMatchingOptions, IncrementalPipelineOptions, TwoViewGeometryOptions


class OptionsBuilder:
    def __init__(self, options: ReconstructionOptions):
        self.options = options

    def two_view_geometry_options(self):
        two_view_geometry_options = TwoViewGeometryOptions()
        two_view_geometry_options.compute_relative_pose = True
        if self.options.deterministic_seed is not None:
            two_view_geometry_options.ransac.random_seed = self.options.deterministic_seed
        two_view_geometry_options.ransac.max_error = self.options.ransac_max_error
        two_view_geometry_options.ransac.min_inlier_ratio = self.options.ransac_min_inlier_ratio
        two_view_geometry_options.filter_stationary_matches = True
        two_view_geometry_options.stationary_matches_max_error = 4.0
        return two_view_geometry_options

    def feature_matching_options(self):
        feature_matching_options = FeatureMatchingOptions()
        feature_matching_options.rig_verification = self.options.rig_verification
        feature_matching_options.skip_image_pairs_in_same_frame = False
        return feature_matching_options

    def sequential_window(self):
        return self.options.sequential_window

    def retrieval_neighbors(self):
        return self.options.retrieval_neighbors

    def retrieval_min_distance_m(self):
        return self.options.retrieval_min_distance_m

    def retrieval_min_score(self):
        return self.options.retrieval_min_score

    def compression_opq_number_of_subvectors(self):
        return self.options.compression_opq_number_of_subvectors

    def compression_opq_number_of_bits_per_subvector(self):
        return self.options.compression_opq_number_of_bits_per_subvector

    def compression_opq_number_of_training_iterations(self):
        return self.options.compression_opq_number_of_training_iterations

    def pose_prior_position_sigma_m(self):
        return self.options.pose_prior_position_sigma_m

    def lightglue_batch_size(self):
        return self.options.lightglue_batch_size

    def max_keypoints_per_image(self):
        return self.options.max_keypoints_per_image

    def incremental_pipeline_options(self, constant_rigs: set[int]):
        incremental_pipeline_options = IncrementalPipelineOptions()

        if self.options.deterministic_seed is not None:
            incremental_pipeline_options.random_seed = self.options.deterministic_seed
            incremental_pipeline_options.triangulation.random_seed = self.options.deterministic_seed
            incremental_pipeline_options.num_threads = 1
            incremental_pipeline_options.mapper.num_threads = 1

        incremental_pipeline_options.use_prior_position = self.options.use_prior_position
        incremental_pipeline_options.ba_refine_sensor_from_rig = self.options.bundle_adjustment_refine_sensor_from_rig
        incremental_pipeline_options.ba_refine_focal_length = self.options.bundle_adjustment_refine_focal_length
        incremental_pipeline_options.ba_refine_principal_point = self.options.bundle_adjustment_refine_principal_point
        incremental_pipeline_options.ba_refine_extra_params = self.options.bundle_adjustment_refine_additional_params
        incremental_pipeline_options.ba_global_frames_ratio = self.options.bundle_adjustment_global_frames_ratio
        incremental_pipeline_options.ba_global_max_refinements = self.options.bundle_adjustment_global_max_refinements
        incremental_pipeline_options.ba_global_function_tolerance = (
            self.options.bundle_adjustment_global_function_tolerance
        )
        incremental_pipeline_options.mapper.ba_global_ignore_redundant_points3D = (
            self.options.bundle_adjustment_ignore_redundant_points3D
        )
        if constant_rigs:
            incremental_pipeline_options.constant_rigs = constant_rigs

        incremental_pipeline_options.triangulation.min_angle = self.options.triangulation_minimum_angle
        incremental_pipeline_options.triangulation.complete_max_reproj_error = (
            self.options.triangulation_complete_max_reprojection_error
        )
        incremental_pipeline_options.triangulation.merge_max_reproj_error = (
            self.options.triangulation_merge_max_reprojection_error
        )
        incremental_pipeline_options.mapper.filter_min_tri_angle = self.options.triangulation_minimum_angle
        incremental_pipeline_options.mapper.filter_max_reproj_error = self.options.mapper_filter_max_reprojection_error

        return incremental_pipeline_options

    def final_bundle_adjustment_options(self):
        bundle_adjustment_options = BundleAdjustmentOptions()
        bundle_adjustment_options.refine_sensor_from_rig = True
        bundle_adjustment_options.refine_focal_length = self.options.bundle_adjustment_refine_focal_length
        bundle_adjustment_options.refine_principal_point = self.options.bundle_adjustment_refine_principal_point
        bundle_adjustment_options.refine_extra_params = self.options.bundle_adjustment_refine_additional_params
        if self.options.deterministic_seed is not None:
            bundle_adjustment_options.ceres.solver_options.num_threads = 1
        return bundle_adjustment_options
