from __future__ import annotations

from core.reconstruction_options import ReconstructionOptions
from pycolmap import FeatureMatchingOptions, IncrementalPipelineOptions, TwoViewGeometryOptions

DEFAULT_NEIGHBORS_COUNT = 12
DEFAULT_MAX_KEYPOINTS_PER_IMAGE = 2500
DEFAULT_NEIGHBOR_ROTATION_THRESHOLD = 30.0
DEFAULT_RANSAC_MAX_ERROR = 2.0
DEFAULT_RANSAC_MIN_INLIER_RATIO = 0.15
DEFAULT_TRIANGULATION_MINIMUM_ANGLE = 3.0
DEFAULT_TRIANGULATION_COMPLETE_MAX_REPROJECTION_ERROR = 2.0
DEFAULT_TRIANGULATION_MERGE_MAX_REPROJECTION_ERROR = 4.0
DEFAULT_MAPPER_FILTER_MAX_REPROJECTION_ERROR = 2.0
DEFAULT_POSE_PRIOR_POS_SIGMA_M = 0.25
DEFAULT_OPQ_NUMBER_OF_SUBVECTORS = 16
DEFAULT_OPQ_NUMBER_OF_BITS_PER_SUBVECTOR = 8
DEFAULT_OPQ_NUMBER_OF_TRAINING_ITERATIONS = 20


class OptionsBuilder:
    def __init__(self, options: ReconstructionOptions):
        self.options = options

    def two_view_geometry_options(self):
        two_view_geometry_options = TwoViewGeometryOptions()
        two_view_geometry_options.compute_relative_pose = True
        if self.options.random_seed is not None:
            two_view_geometry_options.ransac.random_seed = self.options.random_seed
        two_view_geometry_options.ransac.max_error = self.options.ransac_max_error or DEFAULT_RANSAC_MAX_ERROR
        two_view_geometry_options.ransac.min_inlier_ratio = (
            self.options.ransac_min_inlier_ratio or DEFAULT_RANSAC_MIN_INLIER_RATIO
        )
        two_view_geometry_options.filter_stationary_matches = True
        two_view_geometry_options.stationary_matches_max_error = 4.0
        return two_view_geometry_options

    def feature_matching_options(self):
        feature_matching_options = FeatureMatchingOptions()
        if self.options.rig_verification is not None:
            feature_matching_options.rig_verification = self.options.rig_verification
        feature_matching_options.skip_image_pairs_in_same_frame = False
        return feature_matching_options

    def neighbors_count(self):
        return self.options.neighbors_count or DEFAULT_NEIGHBORS_COUNT

    def rotation_threshold_deg(self):
        return self.options.rotation_threshold or DEFAULT_NEIGHBOR_ROTATION_THRESHOLD

    def max_keypoints_per_image(self):
        return self.options.max_keypoints_per_image or DEFAULT_MAX_KEYPOINTS_PER_IMAGE

    def compression_opq_number_of_subvectors(self):
        return self.options.compression_opq_number_of_subvectors or DEFAULT_OPQ_NUMBER_OF_SUBVECTORS

    def compression_opq_number_of_bits_per_subvector(self):
        return self.options.compression_opq_number_of_bits_per_subvector or DEFAULT_OPQ_NUMBER_OF_BITS_PER_SUBVECTOR

    def compression_opq_number_of_training_iterations(self):
        return self.options.compression_opq_number_of_training_iterations or DEFAULT_OPQ_NUMBER_OF_TRAINING_ITERATIONS

    def pose_prior_position_sigma_m(self):
        return self.options.pose_prior_position_sigma_m or DEFAULT_POSE_PRIOR_POS_SIGMA_M

    def incremental_pipeline_options(self):
        incremental_pipeline_options = IncrementalPipelineOptions()
        # incremental_pipeline_options.num_threads = 1
        # incremental_pipeline_options.mapper.num_threads = 1

        if self.options.random_seed is not None:
            incremental_pipeline_options.random_seed = self.options.random_seed
            incremental_pipeline_options.triangulation.random_seed = self.options.random_seed

        if self.options.use_prior_position is not None:
            incremental_pipeline_options.use_prior_position = self.options.use_prior_position
        if self.options.bundle_adjustment_refine_sensor_from_rig is not None:
            incremental_pipeline_options.ba_refine_sensor_from_rig = (
                self.options.bundle_adjustment_refine_sensor_from_rig
            )
        if self.options.bundle_adjustment_refine_focal_length is not None:
            incremental_pipeline_options.ba_refine_focal_length = self.options.bundle_adjustment_refine_focal_length
        if self.options.bundle_adjustment_refine_principal_point is not None:
            incremental_pipeline_options.ba_refine_principal_point = (
                self.options.bundle_adjustment_refine_principal_point
            )

        triangulation_min_angle = self.options.triangulation_minimum_angle or DEFAULT_TRIANGULATION_MINIMUM_ANGLE

        incremental_pipeline_options.triangulation.min_angle = triangulation_min_angle
        incremental_pipeline_options.triangulation.complete_max_reproj_error = (
            self.options.triangulation_complete_max_reprojection_error
            or DEFAULT_TRIANGULATION_COMPLETE_MAX_REPROJECTION_ERROR
        )
        incremental_pipeline_options.triangulation.merge_max_reproj_error = (
            self.options.triangulation_merge_max_reprojection_error
            or DEFAULT_TRIANGULATION_MERGE_MAX_REPROJECTION_ERROR
        )
        incremental_pipeline_options.mapper.filter_min_tri_angle = triangulation_min_angle
        incremental_pipeline_options.mapper.filter_max_reproj_error = (
            self.options.mapper_filter_max_reprojection_error or DEFAULT_MAPPER_FILTER_MAX_REPROJECTION_ERROR
        )

        return incremental_pipeline_options
