"""
COLMAP plugin
"""
from __future__ import annotations
import collections.abc
import numpy
import numpy.typing
import typing
from . import cost_functions
from . import pyceres
__all__: list[str] = ['AbsolutePoseEstimationOptions', 'AbsolutePoseRefinementOptions', 'AlignedBox3d', 'BACovariance', 'BACovarianceOptions', 'BACovarianceOptionsParams', 'Bitmap', 'BundleAdjuster', 'BundleAdjustmentConfig', 'BundleAdjustmentGauge', 'BundleAdjustmentOptions', 'COLMAP_build', 'COLMAP_version', 'CalculateTriangulationAngle', 'Camera', 'CameraMap', 'CameraMode', 'CameraModelId', 'CopyType', 'Correspondence', 'CorrespondenceGraph', 'Database', 'DatabaseCache', 'DatabaseTransaction', 'DelaunayMeshingOptions', 'Device', 'EstimateTriangulationOptions', 'ExhaustivePairGenerator', 'ExhaustivePairingOptions', 'ExperimentalPoseParam', 'FeatureExtractionOptions', 'FeatureKeypoint', 'FeatureKeypoints', 'FeatureMatch', 'FeatureMatches', 'FeatureMatchingOptions', 'Frame', 'FrameMap', 'GPSTransform', 'GPSTransfromEllipsoid', 'INVALID_CAMERA_ID', 'INVALID_IMAGE_ID', 'INVALID_IMAGE_PAIR_ID', 'INVALID_POINT2D_IDX', 'INVALID_POINT3D_ID', 'Image', 'ImageAlignmentError', 'ImageMap', 'ImagePairStat', 'ImageReaderOptions', 'ImageScore', 'ImageSelectionMethod', 'ImportedPairGenerator', 'ImportedPairingOptions', 'IncrementalMapper', 'IncrementalMapperCallback', 'IncrementalMapperOptions', 'IncrementalMapperStatus', 'IncrementalPipeline', 'IncrementalPipelineOptions', 'IncrementalTriangulator', 'IncrementalTriangulatorOptions', 'LocalBundleAdjustmentReport', 'LossFunctionType', 'MVSModel', 'Normalization', 'ObservationManager', 'PairGenerator', 'PatchMatchOptions', 'Point2D', 'Point2DList', 'Point3D', 'Point3DMap', 'PoissonMeshingOptions', 'PosePrior', 'PosePriorBundleAdjustmentOptions', 'PosePriorCoordinateSystem', 'RANSACOptions', 'Reconstruction', 'ReconstructionManager', 'Rig', 'RigConfig', 'RigConfigCamera', 'RigMap', 'Rigid3d', 'Rotation3d', 'SensorType', 'SequentialPairGenerator', 'SequentialPairingOptions', 'Sift', 'SiftExtractionOptions', 'SiftMatchingOptions', 'Sim3d', 'SpatialPairGenerator', 'SpatialPairingOptions', 'StereoFusionOptions', 'SyntheticDatasetMatchConfig', 'SyntheticDatasetOptions', 'SyntheticImageOptions', 'SyntheticNoiseOptions', 'Timer', 'Track', 'TrackElement', 'TriangulatePoint', 'TriangulationResidualType', 'TwoViewGeometry', 'TwoViewGeometryConfiguration', 'TwoViewGeometryOptions', 'UndistortCameraOptions', 'VisualIndex', 'VocabTreePairGenerator', 'VocabTreePairingOptions', 'absolute_pose_estimation', 'align_reconstruction_to_locations', 'align_reconstruction_to_orig_rig_scales', 'align_reconstructions_via_points', 'align_reconstructions_via_proj_centers', 'align_reconstructions_via_reprojections', 'apply_rig_config', 'average_quaternions', 'bundle_adjustment', 'calculate_triangulation_angle', 'compare_reconstructions', 'compute_squared_sampson_error', 'cost_functions', 'create_default_bundle_adjuster', 'create_pose_prior_bundle_adjuster', 'data_t', 'essential_matrix_estimation', 'essential_matrix_from_pose', 'estimate_absolute_pose', 'estimate_affine2d', 'estimate_affine2d_robust', 'estimate_and_refine_absolute_pose', 'estimate_and_refine_generalized_absolute_pose', 'estimate_ba_covariance', 'estimate_ba_covariance_from_problem', 'estimate_calibrated_two_view_geometry', 'estimate_essential_matrix', 'estimate_fundamental_matrix', 'estimate_generalized_absolute_pose', 'estimate_generalized_relative_pose', 'estimate_homography_matrix', 'estimate_relative_pose', 'estimate_rigid3d', 'estimate_rigid3d_robust', 'estimate_sim3d', 'estimate_sim3d_robust', 'estimate_triangulation', 'estimate_two_view_geometry', 'estimate_two_view_geometry_pose', 'extract_features', 'fundamental_matrix_estimation', 'get_covariance_for_composed_rigid3d', 'get_covariance_for_inverse', 'get_covariance_for_relative_rigid3d', 'has_cuda', 'homography_decomposition', 'homography_matrix_estimation', 'image_pair_to_pair_id', 'import_images', 'incremental_mapping', 'infer_camera_from_image', 'interpolate_camera_poses', 'logging', 'match_exhaustive', 'match_sequential', 'match_spatial', 'match_vocabtree', 'ostream', 'pair_id_to_image_pair', 'patch_match_stereo', 'poisson_meshing', 'pose_from_homography_matrix', 'pyceres', 'read_rig_config', 'refine_absolute_pose', 'refine_generalized_absolute_pose', 'refine_relative_pose', 'rig_absolute_pose_estimation', 'sensor_t', 'set_random_seed', 'squared_sampson_error', 'stereo_fusion', 'swap_image_pair', 'synthesize_dataset', 'synthesize_images', 'synthesize_noise', 'triangulate_mid_point', 'triangulate_point', 'triangulate_points', 'undistort_camera', 'undistort_image', 'undistort_images', 'verify_matches']
class AbsolutePoseEstimationOptions:
    __hash__: typing.ClassVar[None] = None
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __copy__(self) -> AbsolutePoseEstimationOptions:
        ...
    def __deepcopy__(self, arg0: dict) -> AbsolutePoseEstimationOptions:
        ...
    def __eq__(self, arg0: typing.Any) -> bool:
        ...
    def __getstate__(self) -> dict:
        ...
    @typing.overload
    def __init__(self) -> None:
        ...
    @typing.overload
    def __init__(self, arg0: dict) -> None:
        ...
    @typing.overload
    def __init__(self, **kwargs) -> None:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, arg0: dict) -> None:
        ...
    def mergedict(self, kwargs: dict) -> None:
        ...
    def summary(self, write_type: bool = False) -> str:
        ...
    def todict(self, recursive: bool = True) -> dict:
        ...
    @property
    def estimate_focal_length(self) -> bool:
        """
         (bool, default: False)
        """
    @estimate_focal_length.setter
    def estimate_focal_length(self, arg0: bool) -> None:
        ...
    @property
    def ransac(self) -> RANSACOptions:
        """
         (RANSACOptions, default: RANSACOptions(max_error=12.0, min_inlier_ratio=0.1, confidence=0.99999, dyn_num_trials_multiplier=3.0, min_num_trials=100, max_num_trials=10000, random_seed=-1))
        """
    @ransac.setter
    def ransac(self, arg0: RANSACOptions) -> None:
        ...
class AbsolutePoseRefinementOptions:
    __hash__: typing.ClassVar[None] = None
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __copy__(self) -> AbsolutePoseRefinementOptions:
        ...
    def __deepcopy__(self, arg0: dict) -> AbsolutePoseRefinementOptions:
        ...
    def __eq__(self, arg0: typing.Any) -> bool:
        ...
    def __getstate__(self) -> dict:
        ...
    @typing.overload
    def __init__(self) -> None:
        ...
    @typing.overload
    def __init__(self, arg0: dict) -> None:
        ...
    @typing.overload
    def __init__(self, **kwargs) -> None:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, arg0: dict) -> None:
        ...
    def mergedict(self, kwargs: dict) -> None:
        ...
    def summary(self, write_type: bool = False) -> str:
        ...
    def todict(self, recursive: bool = True) -> dict:
        ...
    @property
    def gradient_tolerance(self) -> float:
        """
         (float, default: 1.0)
        """
    @gradient_tolerance.setter
    def gradient_tolerance(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def loss_function_scale(self) -> float:
        """
         (float, default: 1.0)
        """
    @loss_function_scale.setter
    def loss_function_scale(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def max_num_iterations(self) -> int:
        """
         (int, default: 100)
        """
    @max_num_iterations.setter
    def max_num_iterations(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def print_summary(self) -> bool:
        """
         (bool, default: False)
        """
    @print_summary.setter
    def print_summary(self, arg0: bool) -> None:
        ...
    @property
    def refine_extra_params(self) -> bool:
        """
         (bool, default: False)
        """
    @refine_extra_params.setter
    def refine_extra_params(self, arg0: bool) -> None:
        ...
    @property
    def refine_focal_length(self) -> bool:
        """
         (bool, default: False)
        """
    @refine_focal_length.setter
    def refine_focal_length(self, arg0: bool) -> None:
        ...
class AlignedBox3d:
    __hash__: typing.ClassVar[None] = None
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __copy__(self) -> AlignedBox3d:
        ...
    def __deepcopy__(self, arg0: dict) -> AlignedBox3d:
        ...
    def __eq__(self, arg0: typing.Any) -> bool:
        ...
    def __getstate__(self) -> dict:
        ...
    @typing.overload
    def __init__(self) -> None:
        ...
    @typing.overload
    def __init__(self, min: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[3, 1]"], max: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[3, 1]"]) -> None:
        ...
    @typing.overload
    def __init__(self, arg0: dict) -> None:
        ...
    @typing.overload
    def __init__(self, **kwargs) -> None:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, arg0: dict) -> None:
        ...
    def contains_bbox(self, other: AlignedBox3d) -> bool:
        ...
    def contains_point(self, point: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[3, 1]"]) -> bool:
        ...
    def diagonal(self) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[3, 1]"]:
        ...
    def mergedict(self, kwargs: dict) -> None:
        ...
    def summary(self, write_type: bool = False) -> str:
        ...
    def todict(self, recursive: bool = True) -> dict:
        ...
    @property
    def max(self) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[3, 1]"]:
        """
         (ndarray, default: [-1.79769313e+308 -1.79769313e+308 -1.79769313e+308])
        """
    @max.setter
    def max(self, arg1: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[3, 1]"]) -> None:
        ...
    @property
    def min(self) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[3, 1]"]:
        """
         (ndarray, default: [1.79769313e+308 1.79769313e+308 1.79769313e+308])
        """
    @min.setter
    def min(self, arg1: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[3, 1]"]) -> None:
        ...
class BACovariance:
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def get_cam2_cov_from_cam1(self, image_id1: typing.SupportsInt, cam1_from_world: Rigid3d, image_id2: typing.SupportsInt, cam2_from_world: Rigid3d) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[m, n]"] | None:
        """
        Get relative pose covariance in the order [rotation, translation]. This function returns null if some dimensions are kept constant for either of the two poses. This does not mean that one cannot get relative pose covariance for such case, but requires custom logic to fill in zero block in the covariance matrix.
        """
    def get_cam_cov_from_world(self, image_id: typing.SupportsInt) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[m, n]"] | None:
        """
        Tangent space covariance in the order [rotation, translation]. If some dimensions are kept constant, the respective rows/columns are omitted. Returns null if image is not a variable in the problem.
        """
    def get_cam_cross_cov_from_world(self, image_id1: typing.SupportsInt, image_id2: typing.SupportsInt) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[m, n]"] | None:
        """
        Tangent space covariance in the order [rotation, translation]. If some dimensions are kept constant, the respective rows/columns are omitted. Returns null if image is not a variable in the problem.
        """
    def get_other_params_cov(self, param: typing.Annotated[numpy.typing.ArrayLike, numpy.float64]) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[m, n]"] | None:
        """
        Tangent space covariance for any variable parameter block in the problem. If some dimensions are kept constant, the respective rows/columns are omitted. Returns null if parameter block not a variable in the problem.
        """
    def get_point_cov(self, point3D_id: typing.SupportsInt) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[m, n]"] | None:
        """
        Covariance for 3D points, conditioned on all other variables set constant. If some dimensions are kept constant, the respective rows/columns are omitted. Returns null if 3D point not a variable in the problem.
        """
class BACovarianceOptions:
    __hash__: typing.ClassVar[None] = None
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __copy__(self) -> BACovarianceOptions:
        ...
    def __deepcopy__(self, arg0: dict) -> BACovarianceOptions:
        ...
    def __eq__(self, arg0: typing.Any) -> bool:
        ...
    def __getstate__(self) -> dict:
        ...
    @typing.overload
    def __init__(self) -> None:
        ...
    @typing.overload
    def __init__(self, arg0: dict) -> None:
        ...
    @typing.overload
    def __init__(self, **kwargs) -> None:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, arg0: dict) -> None:
        ...
    def mergedict(self, kwargs: dict) -> None:
        ...
    def summary(self, write_type: bool = False) -> str:
        ...
    def todict(self, recursive: bool = True) -> dict:
        ...
    @property
    def damping(self) -> float:
        """
        Damping factor for the Hessian in the Schur complement solver. Enables to robustly deal with poorly conditioned parameters. (float, default: 1e-08)
        """
    @damping.setter
    def damping(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def experimental_custom_poses(self) -> list[ExperimentalPoseParam]:
        """
        WARNING: This option will be removed in a future release, use at your own risk. For custom bundle adjustment problems, this enables to specify a custom set of pose parameter blocks to consider. Note that these pose blocks must not necessarily be part of the reconstruction but they must follow the standard requirement for applying the Schur complement trick. (list, default: [])
        """
    @experimental_custom_poses.setter
    def experimental_custom_poses(self, arg0: collections.abc.Sequence[ExperimentalPoseParam]) -> None:
        ...
    @property
    def params(self) -> BACovarianceOptionsParams:
        """
        For which parameters to compute the covariance. (BACovarianceOptionsParams, default: BACovarianceOptionsParams.ALL)
        """
    @params.setter
    def params(self, arg0: BACovarianceOptionsParams) -> None:
        ...
class BACovarianceOptionsParams:
    """
    Members:
    
      POSES
    
      POINTS
    
      POSES_AND_POINTS
    
      ALL
    """
    ALL: typing.ClassVar[BACovarianceOptionsParams]  # value = BACovarianceOptionsParams.ALL
    POINTS: typing.ClassVar[BACovarianceOptionsParams]  # value = BACovarianceOptionsParams.POINTS
    POSES: typing.ClassVar[BACovarianceOptionsParams]  # value = BACovarianceOptionsParams.POSES
    POSES_AND_POINTS: typing.ClassVar[BACovarianceOptionsParams]  # value = BACovarianceOptionsParams.POSES_AND_POINTS
    __members__: typing.ClassVar[dict[str, BACovarianceOptionsParams]]  # value = {'POSES': BACovarianceOptionsParams.POSES, 'POINTS': BACovarianceOptionsParams.POINTS, 'POSES_AND_POINTS': BACovarianceOptionsParams.POSES_AND_POINTS, 'ALL': BACovarianceOptionsParams.ALL}
    @staticmethod
    def __repr__(*args, **kwargs):
        """
        __str__(self: object, /) -> str
        """
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __eq__(self, other: typing.Any) -> bool:
        ...
    def __getstate__(self) -> int:
        ...
    def __hash__(self) -> int:
        ...
    def __index__(self) -> int:
        ...
    @typing.overload
    def __init__(self, value: typing.SupportsInt) -> None:
        ...
    @typing.overload
    def __init__(self, name: str) -> None:
        ...
    def __int__(self) -> int:
        ...
    def __ne__(self, other: typing.Any) -> bool:
        ...
    def __setstate__(self, state: typing.SupportsInt) -> None:
        ...
    def __str__(self) -> str:
        ...
    @property
    def name(self) -> str:
        ...
    @property
    def value(self) -> int:
        ...
class Bitmap:
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    @staticmethod
    def from_array(array: typing.Annotated[numpy.typing.ArrayLike, numpy.uint8]) -> Bitmap:
        """
        Create bitmap as a copy of array. Returns RGB bitmap, if array has shape (H, W, 3), or grayscale bitmap, if array has shape (H, W[, 1]).
        """
    @staticmethod
    def read(path: str, as_rgb: bool) -> pycolmap._core.Bitmap | None:
        """
        Read bitmap from file.
        """
    def __init__(self) -> None:
        ...
    def __repr__(self) -> str:
        ...
    def to_array(self) -> numpy.typing.NDArray[numpy.uint8]:
        ...
    def write(self, path: str, flags: typing.SupportsInt = 0) -> bool:
        """
        Write bitmap to file.
        """
class BundleAdjuster:
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __init__(self, options: BundleAdjustmentOptions, config: BundleAdjustmentConfig) -> None:
        ...
    def solve(self) -> pyceres.SolverSummary:
        ...
    @property
    def config(self) -> BundleAdjustmentConfig:
        ...
    @property
    def options(self) -> BundleAdjustmentOptions:
        ...
    @property
    def problem(self) -> ...:
        ...
class BundleAdjustmentConfig:
    __hash__: typing.ClassVar[None] = None
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __copy__(self) -> BundleAdjustmentConfig:
        ...
    def __deepcopy__(self, arg0: dict) -> BundleAdjustmentConfig:
        ...
    def __eq__(self, arg0: typing.Any) -> bool:
        ...
    def __getstate__(self) -> dict:
        ...
    @typing.overload
    def __init__(self) -> None:
        ...
    @typing.overload
    def __init__(self, arg0: dict) -> None:
        ...
    @typing.overload
    def __init__(self, **kwargs) -> None:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, arg0: dict) -> None:
        ...
    def add_constant_point(self, point3D_id: typing.SupportsInt) -> None:
        ...
    def add_image(self, image_id: typing.SupportsInt) -> None:
        ...
    def add_variable_point(self, point3D_id: typing.SupportsInt) -> None:
        ...
    def fix_gauge(self, arg0: BundleAdjustmentGauge) -> None:
        ...
    def has_constant_cam_intrinsics(self, camera_id: typing.SupportsInt) -> bool:
        ...
    def has_constant_point(self, point3D_id: typing.SupportsInt) -> bool:
        ...
    def has_constant_rig_from_world_pose(self, frame_id: typing.SupportsInt) -> bool:
        ...
    def has_constant_sensor_from_rig_pose(self, sensor_id: sensor_t) -> bool:
        ...
    def has_image(self, image_id: typing.SupportsInt) -> bool:
        ...
    def has_point(self, point3D_id: typing.SupportsInt) -> bool:
        ...
    def has_variable_point(self, point3D_id: typing.SupportsInt) -> bool:
        ...
    def mergedict(self, kwargs: dict) -> None:
        ...
    def num_constant_cam_intrinsics(self) -> int:
        ...
    def num_constant_points(self) -> int:
        ...
    def num_constant_rig_from_world_poses(self) -> int:
        ...
    def num_constant_sensor_from_rig_poses(self) -> int:
        ...
    def num_points(self) -> int:
        ...
    def num_residuals(self, reconstruction: Reconstruction) -> int:
        ...
    def num_variable_points(self) -> int:
        ...
    def remove_constant_point(self, point3D_id: typing.SupportsInt) -> None:
        ...
    def remove_image(self, image_id: typing.SupportsInt) -> None:
        ...
    def remove_variable_point(self, point3D_id: typing.SupportsInt) -> None:
        ...
    def set_constant_cam_intrinsics(self, camera_id: typing.SupportsInt) -> None:
        ...
    def set_constant_rig_from_world_pose(self, frame_id: typing.SupportsInt) -> None:
        ...
    def set_constant_sensor_from_rig_pose(self, sensor_id: sensor_t) -> None:
        ...
    def set_variable_cam_intrinsics(self, camera_id: typing.SupportsInt) -> None:
        ...
    def set_variable_rig_from_world_pose(self, frame_id: typing.SupportsInt) -> None:
        ...
    def set_variable_sensor_from_rig_pose(self, sensor_id: sensor_t) -> None:
        ...
    def summary(self, write_type: bool = False) -> str:
        ...
    def todict(self, recursive: bool = True) -> dict:
        ...
    @property
    def constant_cam_intrinsics(self) -> set[int]:
        """
         (set, default: set())
        """
    @property
    def constant_points(self) -> set[int]:
        """
         (set, default: set())
        """
    @property
    def constant_rig_from_world_poses(self) -> set[int]:
        """
         (set, default: set())
        """
    @property
    def constant_sensor_from_rig_poses(self) -> set[sensor_t]:
        """
         (set, default: set())
        """
    @property
    def fixed_gauge(self) -> BundleAdjustmentGauge:
        """
         (BundleAdjustmentGauge, default: BundleAdjustmentGauge.UNSPECIFIED)
        """
    @property
    def images(self) -> set[int]:
        """
         (set, default: set())
        """
    @property
    def variable_points(self) -> set[int]:
        """
         (set, default: set())
        """
class BundleAdjustmentGauge:
    """
    Members:
    
      UNSPECIFIED
    
      TWO_CAMS_FROM_WORLD
    
      THREE_POINTS
    """
    THREE_POINTS: typing.ClassVar[BundleAdjustmentGauge]  # value = BundleAdjustmentGauge.THREE_POINTS
    TWO_CAMS_FROM_WORLD: typing.ClassVar[BundleAdjustmentGauge]  # value = BundleAdjustmentGauge.TWO_CAMS_FROM_WORLD
    UNSPECIFIED: typing.ClassVar[BundleAdjustmentGauge]  # value = BundleAdjustmentGauge.UNSPECIFIED
    __members__: typing.ClassVar[dict[str, BundleAdjustmentGauge]]  # value = {'UNSPECIFIED': BundleAdjustmentGauge.UNSPECIFIED, 'TWO_CAMS_FROM_WORLD': BundleAdjustmentGauge.TWO_CAMS_FROM_WORLD, 'THREE_POINTS': BundleAdjustmentGauge.THREE_POINTS}
    @staticmethod
    def __repr__(*args, **kwargs):
        """
        __str__(self: object, /) -> str
        """
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __eq__(self, other: typing.Any) -> bool:
        ...
    def __getstate__(self) -> int:
        ...
    def __hash__(self) -> int:
        ...
    def __index__(self) -> int:
        ...
    @typing.overload
    def __init__(self, value: typing.SupportsInt) -> None:
        ...
    @typing.overload
    def __init__(self, name: str) -> None:
        ...
    def __int__(self) -> int:
        ...
    def __ne__(self, other: typing.Any) -> bool:
        ...
    def __setstate__(self, state: typing.SupportsInt) -> None:
        ...
    def __str__(self) -> str:
        ...
    @property
    def name(self) -> str:
        ...
    @property
    def value(self) -> int:
        ...
class BundleAdjustmentOptions:
    __hash__: typing.ClassVar[None] = None
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __copy__(self) -> BundleAdjustmentOptions:
        ...
    def __deepcopy__(self, arg0: dict) -> BundleAdjustmentOptions:
        ...
    def __eq__(self, arg0: typing.Any) -> bool:
        ...
    def __getstate__(self) -> dict:
        ...
    @typing.overload
    def __init__(self) -> None:
        ...
    @typing.overload
    def __init__(self, arg0: dict) -> None:
        ...
    @typing.overload
    def __init__(self, **kwargs) -> None:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, arg0: dict) -> None:
        ...
    def create_loss_function(self) -> ...:
        ...
    def create_solver_options(self, config: BundleAdjustmentConfig, problem: ...) -> pyceres.SolverOptions:
        ...
    def mergedict(self, kwargs: dict) -> None:
        ...
    def summary(self, write_type: bool = False) -> str:
        ...
    def todict(self, recursive: bool = True) -> dict:
        ...
    @property
    def gpu_index(self) -> str:
        """
        Which GPU to use for solving the problem. (str, default: -1)
        """
    @gpu_index.setter
    def gpu_index(self, arg0: str) -> None:
        ...
    @property
    def loss_function_scale(self) -> float:
        """
        Scaling factor determines residual at which robustification takes place. (float, default: 1.0)
        """
    @loss_function_scale.setter
    def loss_function_scale(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def loss_function_type(self) -> LossFunctionType:
        """
        Loss function types: Trivial (non-robust) and Cauchy (robust) loss. (LossFunctionType, default: LossFunctionType.TRIVIAL)
        """
    @loss_function_type.setter
    def loss_function_type(self, arg0: LossFunctionType) -> None:
        ...
    @property
    def max_num_images_direct_dense_cpu_solver(self) -> int:
        """
        Threshold to switch between direct, sparse, and iterative solvers. (int, default: 50)
        """
    @max_num_images_direct_dense_cpu_solver.setter
    def max_num_images_direct_dense_cpu_solver(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def max_num_images_direct_dense_gpu_solver(self) -> int:
        """
        Threshold to switch between direct, sparse, and iterative solvers. (int, default: 200)
        """
    @max_num_images_direct_dense_gpu_solver.setter
    def max_num_images_direct_dense_gpu_solver(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def max_num_images_direct_sparse_cpu_solver(self) -> int:
        """
        Threshold to switch between direct, sparse, and iterative solvers. (int, default: 1000)
        """
    @max_num_images_direct_sparse_cpu_solver.setter
    def max_num_images_direct_sparse_cpu_solver(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def max_num_images_direct_sparse_gpu_solver(self) -> int:
        """
        Threshold to switch between direct, sparse, and iterative solvers. (int, default: 4000)
        """
    @max_num_images_direct_sparse_gpu_solver.setter
    def max_num_images_direct_sparse_gpu_solver(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def min_num_images_gpu_solver(self) -> int:
        """
        Minimum number of images to use the GPU solver. (int, default: 50)
        """
    @min_num_images_gpu_solver.setter
    def min_num_images_gpu_solver(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def min_num_residuals_for_cpu_multi_threading(self) -> int:
        """
        Minimum number of residuals to enable multi-threading. Note that single-threaded is typically better for small bundle adjustment problems due to the overhead of threading. (int, default: 50000)
        """
    @min_num_residuals_for_cpu_multi_threading.setter
    def min_num_residuals_for_cpu_multi_threading(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def print_summary(self) -> bool:
        """
        Whether to print a final summary. (bool, default: True)
        """
    @print_summary.setter
    def print_summary(self, arg0: bool) -> None:
        ...
    @property
    def refine_extra_params(self) -> bool:
        """
        Whether to refine the extra parameter group. (bool, default: True)
        """
    @refine_extra_params.setter
    def refine_extra_params(self, arg0: bool) -> None:
        ...
    @property
    def refine_focal_length(self) -> bool:
        """
        Whether to refine the focal length parameter group. (bool, default: True)
        """
    @refine_focal_length.setter
    def refine_focal_length(self, arg0: bool) -> None:
        ...
    @property
    def refine_principal_point(self) -> bool:
        """
        Whether to refine the principal point parameter group. (bool, default: False)
        """
    @refine_principal_point.setter
    def refine_principal_point(self, arg0: bool) -> None:
        ...
    @property
    def refine_rig_from_world(self) -> bool:
        """
        Whether to refine the frame from world extrinsic parameter group. (bool, default: True)
        """
    @refine_rig_from_world.setter
    def refine_rig_from_world(self, arg0: bool) -> None:
        ...
    @property
    def refine_sensor_from_rig(self) -> bool:
        """
        Whether to refine the sensor from rig extrinsic parameter group. (bool, default: True)
        """
    @refine_sensor_from_rig.setter
    def refine_sensor_from_rig(self, arg0: bool) -> None:
        ...
    @property
    def solver_options(self) -> pyceres.SolverOptions:
        """
        Options for the Ceres solver. Using this member requires having PyCeres installed. (SolverOptions, default: SolverOptions(minimizer_type=MinimizerType.TRUST_REGION, line_search_direction_type=LineSearchDirectionType.LBFGS, line_search_type=LineSearchType.WOLFE, nonlinear_conjugate_gradient_type=NonlinearConjugateGradientType.FLETCHER_REEVES, max_lbfgs_rank=20, use_approximate_eigenvalue_bfgs_scaling=False, line_search_interpolation_type=LineSearchInterpolationType.CUBIC, min_line_search_step_size=1e-09, line_search_sufficient_function_decrease=0.0001, max_line_search_step_contraction=0.001, min_line_search_step_contraction=0.6, max_num_line_search_step_size_iterations=20, max_num_line_search_direction_restarts=5, line_search_sufficient_curvature_decrease=0.9, max_line_search_step_expansion=10.0, trust_region_strategy_type=TrustRegionStrategyType.LEVENBERG_MARQUARDT, dogleg_type=DoglegType.TRADITIONAL_DOGLEG, use_nonmonotonic_steps=False, max_consecutive_nonmonotonic_steps=10, max_num_iterations=100, max_solver_time_in_seconds=1000000000.0, num_threads=-1, initial_trust_region_radius=10000.0, max_trust_region_radius=1e+16, min_trust_region_radius=1e-32, min_relative_decrease=0.001, min_lm_diagonal=1e-06, max_lm_diagonal=1e+32, max_num_consecutive_invalid_steps=10, function_tolerance=0.0, gradient_tolerance=0.0001, parameter_tolerance=0.0, linear_solver_type=LinearSolverType.SPARSE_NORMAL_CHOLESKY, preconditioner_type=PreconditionerType.JACOBI, visibility_clustering_type=VisibilityClusteringType.CANONICAL_VIEWS, dense_linear_algebra_library_type=DenseLinearAlgebraLibraryType.EIGEN, sparse_linear_algebra_library_type=SparseLinearAlgebraLibraryType.SUITE_SPARSE, use_explicit_schur_complement=False, dynamic_sparsity=False, use_inner_iterations=False, inner_iteration_tolerance=0.001, min_linear_solver_iterations=0, max_linear_solver_iterations=200, eta=0.1, jacobi_scaling=True, logging_type=LoggingType.SILENT, minimizer_progress_to_stdout=False, trust_region_problem_dump_directory='/tmp', trust_region_problem_dump_format_type=DumpFormatType.TEXTFILE, check_gradients=False, gradient_check_relative_precision=1e-08, gradient_check_numeric_derivative_relative_step_size=1e-06, update_state_every_iteration=False))
        """
    @solver_options.setter
    def solver_options(self, arg0: pyceres.SolverOptions) -> None:
        ...
    @property
    def use_gpu(self) -> bool:
        """
        Whether to use Ceres' CUDA linear algebra library, if available. (bool, default: False)
        """
    @use_gpu.setter
    def use_gpu(self, arg0: bool) -> None:
        ...
class Camera:
    __hash__: typing.ClassVar[None] = None
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    @staticmethod
    def create(camera_id: typing.SupportsInt, model: CameraModelId, focal_length: typing.SupportsFloat, width: typing.SupportsInt, height: typing.SupportsInt) -> Camera:
        ...
    def __copy__(self) -> Camera:
        ...
    def __deepcopy__(self, arg0: dict) -> Camera:
        ...
    def __eq__(self, arg0: Camera) -> bool:
        ...
    def __getstate__(self) -> dict:
        ...
    @typing.overload
    def __init__(self) -> None:
        ...
    @typing.overload
    def __init__(self, arg0: dict) -> None:
        ...
    @typing.overload
    def __init__(self, **kwargs) -> None:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, arg0: dict) -> None:
        ...
    def calibration_matrix(self) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[3, 3]"]:
        """
        Compute calibration matrix from params.
        """
    @typing.overload
    def cam_from_img(self, image_point: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[2, 1]"]) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[2, 1]"] | None:
        """
        Unproject point in image plane to camera frame.
        """
    @typing.overload
    def cam_from_img(self, image_points: typing.Annotated[numpy.typing.NDArray[numpy.float64], "[m, 2]"]) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[m, 2]"]:
        """
        Unproject list of points in image plane to camera frame.
        """
    @typing.overload
    def cam_from_img(self, image_points: Point2DList) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[m, 2]"]:
        """
        Unproject list of points in image plane to camera frame.
        """
    def cam_from_img_threshold(self, threshold: typing.SupportsFloat) -> float:
        """
        Convert pixel threshold in image plane to world space.
        """
    def extra_params_idxs(self) -> list[int]:
        """
        Indices of extra parameters in params property.
        """
    def focal_length_idxs(self) -> list[int]:
        """
        Indices of focal length parameters in params property.
        """
    def has_bogus_params(self, min_focal_length_ratio: typing.SupportsFloat, max_focal_length_ratio: typing.SupportsFloat, max_extra_param: typing.SupportsFloat) -> bool:
        """
        Check whether camera has bogus parameters.
        """
    @typing.overload
    def img_from_cam(self, cam_point: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[3, 1]"]) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[2, 1]"] | None:
        """
        Project point from camera frame to image plane.
        """
    @typing.overload
    def img_from_cam(self, cam_point: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[2, 1]"]) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[2, 1]"] | None:
        """
        (Deprecated) Project point from camera frame to image plane.
        """
    @typing.overload
    def img_from_cam(self, cam_points: typing.Annotated[numpy.typing.NDArray[numpy.float64], "[m, 3]"]) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[m, 2]"]:
        """
        Project list of points from camera frame to image plane.
        """
    @typing.overload
    def img_from_cam(self, cam_points: typing.Annotated[numpy.typing.NDArray[numpy.float64], "[m, 2]"]) -> typing.Any:
        """
        (Deprecated) Project list of points from camera frame to image plane.
        """
    @typing.overload
    def img_from_cam(self, cam_points: Point2DList) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[m, 2]"]:
        """
        Project list of points from camera frame to image plane.
        """
    def mean_focal_length(self) -> float:
        ...
    def mergedict(self, kwargs: dict) -> None:
        ...
    def params_to_string(self) -> str:
        """
        Concatenate parameters as comma-separated list.
        """
    def principal_point_idxs(self) -> list[int]:
        """
        Indices of principal point parameters in params property.
        """
    @typing.overload
    def rescale(self, new_width: typing.SupportsInt, new_height: typing.SupportsInt) -> None:
        """
        Rescale the camera dimensions and accordingly the focal length and the principal point.
        """
    @typing.overload
    def rescale(self, scale: typing.SupportsFloat) -> None:
        """
        Rescale the camera dimensions and accordingly the focal length and the principal point.
        """
    def set_params_from_string(self, params: str) -> bool:
        """
        Set camera parameters from comma-separated list.
        """
    def summary(self, write_type: bool = False) -> str:
        ...
    def todict(self, recursive: bool = True) -> dict:
        ...
    def verify_params(self) -> bool:
        """
        Check whether parameters are valid, i.e. the parameter vector has the correct dimensions that match the specified camera model.
        """
    @property
    def camera_id(self) -> int:
        """
        Unique identifier of the camera. (int, default: 4294967295)
        """
    @camera_id.setter
    def camera_id(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def focal_length(self) -> float:
        ...
    @focal_length.setter
    def focal_length(self, arg1: typing.SupportsFloat) -> None:
        ...
    @property
    def focal_length_x(self) -> float:
        ...
    @focal_length_x.setter
    def focal_length_x(self, arg1: typing.SupportsFloat) -> None:
        ...
    @property
    def focal_length_y(self) -> float:
        ...
    @focal_length_y.setter
    def focal_length_y(self, arg1: typing.SupportsFloat) -> None:
        ...
    @property
    def has_prior_focal_length(self) -> bool:
        """
         (bool, default: False)
        """
    @has_prior_focal_length.setter
    def has_prior_focal_length(self, arg0: bool) -> None:
        ...
    @property
    def height(self) -> int:
        """
        Height of camera sensor. (int, default: 0)
        """
    @height.setter
    def height(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def model(self) -> CameraModelId:
        """
        Camera model. (CameraModelId, default: CameraModelId.INVALID)
        """
    @model.setter
    def model(self, arg0: CameraModelId) -> None:
        ...
    @property
    def params(self) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[m, 1]", "flags.writeable"]:
        """
        Camera parameters. (ndarray, default: [])
        """
    @params.setter
    def params(self, arg1: collections.abc.Sequence[typing.SupportsFloat]) -> None:
        ...
    @property
    def params_info(self) -> str:
        """
        Get human-readable information about the parameter vector ordering.
        """
    @property
    def principal_point_x(self) -> float:
        ...
    @principal_point_x.setter
    def principal_point_x(self, arg1: typing.SupportsFloat) -> None:
        ...
    @property
    def principal_point_y(self) -> float:
        ...
    @principal_point_y.setter
    def principal_point_y(self, arg1: typing.SupportsFloat) -> None:
        ...
    @property
    def sensor_id(self) -> sensor_t:
        """
        Unique identifier of the sensor. (sensor_t, default: sensor_t(type=SensorType.CAMERA, id=4294967295))
        """
    @property
    def width(self) -> int:
        """
        Width of camera sensor. (int, default: 0)
        """
    @width.setter
    def width(self, arg0: typing.SupportsInt) -> None:
        ...
class CameraMap:
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __bool__(self) -> bool:
        """
        Check whether the map is nonempty
        """
    @typing.overload
    def __contains__(self, arg0: typing.SupportsInt) -> bool:
        ...
    @typing.overload
    def __contains__(self, arg0: typing.Any) -> bool:
        ...
    def __delitem__(self, arg0: typing.SupportsInt) -> None:
        ...
    def __getitem__(self, arg0: typing.SupportsInt) -> Camera:
        ...
    def __init__(self) -> None:
        ...
    def __iter__(self) -> collections.abc.Iterator[int]:
        ...
    def __len__(self) -> int:
        ...
    def __repr__(self) -> str:
        """
        Return the canonical string representation of this map.
        """
    def __setitem__(self, arg0: typing.SupportsInt, arg1: Camera) -> None:
        ...
    def items(self) -> typing.ItemsView:
        ...
    def keys(self) -> typing.KeysView:
        ...
    def values(self) -> typing.ValuesView:
        ...
class CameraMode:
    """
    Members:
    
      AUTO
    
      SINGLE
    
      PER_FOLDER
    
      PER_IMAGE
    """
    AUTO: typing.ClassVar[CameraMode]  # value = CameraMode.AUTO
    PER_FOLDER: typing.ClassVar[CameraMode]  # value = CameraMode.PER_FOLDER
    PER_IMAGE: typing.ClassVar[CameraMode]  # value = CameraMode.PER_IMAGE
    SINGLE: typing.ClassVar[CameraMode]  # value = CameraMode.SINGLE
    __members__: typing.ClassVar[dict[str, CameraMode]]  # value = {'AUTO': CameraMode.AUTO, 'SINGLE': CameraMode.SINGLE, 'PER_FOLDER': CameraMode.PER_FOLDER, 'PER_IMAGE': CameraMode.PER_IMAGE}
    @staticmethod
    def __repr__(*args, **kwargs):
        """
        __str__(self: object, /) -> str
        """
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __eq__(self, other: typing.Any) -> bool:
        ...
    def __getstate__(self) -> int:
        ...
    def __hash__(self) -> int:
        ...
    def __index__(self) -> int:
        ...
    @typing.overload
    def __init__(self, value: typing.SupportsInt) -> None:
        ...
    @typing.overload
    def __init__(self, name: str) -> None:
        ...
    def __int__(self) -> int:
        ...
    def __ne__(self, other: typing.Any) -> bool:
        ...
    def __setstate__(self, state: typing.SupportsInt) -> None:
        ...
    def __str__(self) -> str:
        ...
    @property
    def name(self) -> str:
        ...
    @property
    def value(self) -> int:
        ...
class CameraModelId:
    """
    Members:
    
      INVALID
    
      SIMPLE_PINHOLE
    
      PINHOLE
    
      SIMPLE_RADIAL
    
      SIMPLE_RADIAL_FISHEYE
    
      RADIAL
    
      RADIAL_FISHEYE
    
      OPENCV
    
      OPENCV_FISHEYE
    
      FULL_OPENCV
    
      FOV
    
      THIN_PRISM_FISHEYE
    
      RAD_TAN_THIN_PRISM_FISHEYE
    """
    FOV: typing.ClassVar[CameraModelId]  # value = CameraModelId.FOV
    FULL_OPENCV: typing.ClassVar[CameraModelId]  # value = CameraModelId.FULL_OPENCV
    INVALID: typing.ClassVar[CameraModelId]  # value = CameraModelId.INVALID
    OPENCV: typing.ClassVar[CameraModelId]  # value = CameraModelId.OPENCV
    OPENCV_FISHEYE: typing.ClassVar[CameraModelId]  # value = CameraModelId.OPENCV_FISHEYE
    PINHOLE: typing.ClassVar[CameraModelId]  # value = CameraModelId.PINHOLE
    RADIAL: typing.ClassVar[CameraModelId]  # value = CameraModelId.RADIAL
    RADIAL_FISHEYE: typing.ClassVar[CameraModelId]  # value = CameraModelId.RADIAL_FISHEYE
    RAD_TAN_THIN_PRISM_FISHEYE: typing.ClassVar[CameraModelId]  # value = CameraModelId.RAD_TAN_THIN_PRISM_FISHEYE
    SIMPLE_PINHOLE: typing.ClassVar[CameraModelId]  # value = CameraModelId.SIMPLE_PINHOLE
    SIMPLE_RADIAL: typing.ClassVar[CameraModelId]  # value = CameraModelId.SIMPLE_RADIAL
    SIMPLE_RADIAL_FISHEYE: typing.ClassVar[CameraModelId]  # value = CameraModelId.SIMPLE_RADIAL_FISHEYE
    THIN_PRISM_FISHEYE: typing.ClassVar[CameraModelId]  # value = CameraModelId.THIN_PRISM_FISHEYE
    __members__: typing.ClassVar[dict[str, CameraModelId]]  # value = {'INVALID': CameraModelId.INVALID, 'SIMPLE_PINHOLE': CameraModelId.SIMPLE_PINHOLE, 'PINHOLE': CameraModelId.PINHOLE, 'SIMPLE_RADIAL': CameraModelId.SIMPLE_RADIAL, 'SIMPLE_RADIAL_FISHEYE': CameraModelId.SIMPLE_RADIAL_FISHEYE, 'RADIAL': CameraModelId.RADIAL, 'RADIAL_FISHEYE': CameraModelId.RADIAL_FISHEYE, 'OPENCV': CameraModelId.OPENCV, 'OPENCV_FISHEYE': CameraModelId.OPENCV_FISHEYE, 'FULL_OPENCV': CameraModelId.FULL_OPENCV, 'FOV': CameraModelId.FOV, 'THIN_PRISM_FISHEYE': CameraModelId.THIN_PRISM_FISHEYE, 'RAD_TAN_THIN_PRISM_FISHEYE': CameraModelId.RAD_TAN_THIN_PRISM_FISHEYE}
    @staticmethod
    def __repr__(*args, **kwargs):
        """
        __str__(self: object, /) -> str
        """
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __eq__(self, other: typing.Any) -> bool:
        ...
    def __getstate__(self) -> int:
        ...
    def __hash__(self) -> int:
        ...
    def __index__(self) -> int:
        ...
    @typing.overload
    def __init__(self, value: typing.SupportsInt) -> None:
        ...
    @typing.overload
    def __init__(self, name: str) -> None:
        ...
    def __int__(self) -> int:
        ...
    def __ne__(self, other: typing.Any) -> bool:
        ...
    def __setstate__(self, state: typing.SupportsInt) -> None:
        ...
    def __str__(self) -> str:
        ...
    @property
    def name(self) -> str:
        ...
    @property
    def value(self) -> int:
        ...
class CopyType:
    """
    Members:
    
      copy
    
      softlink
    
      hardlink
    """
    __members__: typing.ClassVar[dict[str, CopyType]]  # value = {'copy': CopyType.copy, 'softlink': CopyType.softlink, 'hardlink': CopyType.hardlink}
    copy: typing.ClassVar[CopyType]  # value = CopyType.copy
    hardlink: typing.ClassVar[CopyType]  # value = CopyType.hardlink
    softlink: typing.ClassVar[CopyType]  # value = CopyType.softlink
    @staticmethod
    def __repr__(*args, **kwargs):
        """
        __str__(self: object, /) -> str
        """
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __eq__(self, other: typing.Any) -> bool:
        ...
    def __getstate__(self) -> int:
        ...
    def __hash__(self) -> int:
        ...
    def __index__(self) -> int:
        ...
    @typing.overload
    def __init__(self, value: typing.SupportsInt) -> None:
        ...
    @typing.overload
    def __init__(self, name: str) -> None:
        ...
    def __int__(self) -> int:
        ...
    def __ne__(self, other: typing.Any) -> bool:
        ...
    def __setstate__(self, state: typing.SupportsInt) -> None:
        ...
    def __str__(self) -> str:
        ...
    @property
    def name(self) -> str:
        ...
    @property
    def value(self) -> int:
        ...
class Correspondence:
    __hash__: typing.ClassVar[None] = None
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __copy__(self) -> Correspondence:
        ...
    def __deepcopy__(self, arg0: dict) -> Correspondence:
        ...
    def __eq__(self, arg0: typing.Any) -> bool:
        ...
    def __getstate__(self) -> dict:
        ...
    @typing.overload
    def __init__(self) -> None:
        ...
    @typing.overload
    def __init__(self, image_id: typing.SupportsInt, point2D_idx: typing.SupportsInt) -> None:
        ...
    @typing.overload
    def __init__(self, arg0: dict) -> None:
        ...
    @typing.overload
    def __init__(self, **kwargs) -> None:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, arg0: dict) -> None:
        ...
    def mergedict(self, kwargs: dict) -> None:
        ...
    def summary(self, write_type: bool = False) -> str:
        ...
    def todict(self, recursive: bool = True) -> dict:
        ...
    @property
    def image_id(self) -> int:
        """
         (int, default: 4294967295)
        """
    @image_id.setter
    def image_id(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def point2D_idx(self) -> int:
        """
         (int, default: 4294967295)
        """
    @point2D_idx.setter
    def point2D_idx(self, arg0: typing.SupportsInt) -> None:
        ...
class CorrespondenceGraph:
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __copy__(self) -> CorrespondenceGraph:
        ...
    def __deepcopy__(self, arg0: dict) -> CorrespondenceGraph:
        ...
    def __init__(self) -> None:
        ...
    def __repr__(self) -> str:
        ...
    def add_correspondences(self, image_id1: typing.SupportsInt, image_id2: typing.SupportsInt, correspondences: typing.Annotated[numpy.typing.ArrayLike, numpy.uint32, "[m, 2]"]) -> None:
        ...
    def add_image(self, image_id: typing.SupportsInt, num_points2D: typing.SupportsInt) -> None:
        ...
    def exists_image(self, image_id: typing.SupportsInt) -> bool:
        ...
    def extract_correspondences(self, image_id: typing.SupportsInt, point2D_idx: typing.SupportsInt) -> list[Correspondence]:
        ...
    def extract_transitive_correspondences(self, image_id: typing.SupportsInt, point2D_idx: typing.SupportsInt, transitivity: typing.SupportsInt) -> list[Correspondence]:
        ...
    def finalize(self) -> None:
        ...
    def find_correspondences_between_images(self, image_id1: typing.SupportsInt, image_id2: typing.SupportsInt) -> typing.Annotated[numpy.typing.NDArray[numpy.uint32], "[m, 2]"]:
        ...
    def has_correspondences(self, image_id: typing.SupportsInt, point2D_idx: typing.SupportsInt) -> bool:
        ...
    def is_two_view_observation(self, image_id: typing.SupportsInt, point2D_idx: typing.SupportsInt) -> bool:
        ...
    def num_correspondences_between_all_images(self) -> dict[int, int]:
        ...
    def num_correspondences_between_images(self, image_id1: typing.SupportsInt, image_id2: typing.SupportsInt) -> int:
        ...
    def num_correspondences_for_image(self, image_id: typing.SupportsInt) -> int:
        ...
    def num_image_pairs(self) -> int:
        ...
    def num_images(self) -> int:
        ...
    def num_observations_for_image(self, image_id: typing.SupportsInt) -> int:
        ...
class Database:
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    @staticmethod
    def merge(database1: Database, database2: Database, merged_database: Database) -> None:
        ...
    @staticmethod
    def open(path: str) -> Database:
        ...
    def __enter__(self) -> Database:
        ...
    def __exit__(self, *args) -> None:
        ...
    def __init__(self) -> None:
        ...
    def clear_all_tables(self) -> None:
        ...
    def clear_cameras(self) -> None:
        ...
    def clear_descriptors(self) -> None:
        ...
    def clear_frames(self) -> None:
        ...
    def clear_images(self) -> None:
        ...
    def clear_keypoints(self) -> None:
        ...
    def clear_matches(self) -> None:
        ...
    def clear_pose_priors(self) -> None:
        ...
    def clear_rigs(self) -> None:
        ...
    def clear_two_view_geometries(self) -> None:
        ...
    def close(self) -> None:
        ...
    def delete_inlier_matches(self, image_id1: typing.SupportsInt, image_id2: typing.SupportsInt) -> None:
        ...
    def delete_matches(self, image_id1: typing.SupportsInt, image_id2: typing.SupportsInt) -> None:
        ...
    def exists_camera(self, camera_id: typing.SupportsInt) -> bool:
        ...
    def exists_descriptors(self, image_id: typing.SupportsInt) -> bool:
        ...
    def exists_frame(self, frame_id: typing.SupportsInt) -> bool:
        ...
    @typing.overload
    def exists_image(self, image_id: typing.SupportsInt) -> bool:
        ...
    @typing.overload
    def exists_image(self, name: str) -> bool:
        ...
    def exists_inlier_matches(self, image_id1: typing.SupportsInt, image_id2: typing.SupportsInt) -> bool:
        ...
    def exists_keypoints(self, image_id: typing.SupportsInt) -> bool:
        ...
    def exists_matches(self, image_id1: typing.SupportsInt, image_id2: typing.SupportsInt) -> bool:
        ...
    def exists_pose_prior(self, image_id: typing.SupportsInt) -> bool:
        ...
    def exists_rig(self, rig_id: typing.SupportsInt) -> bool:
        ...
    def num_cameras(self) -> int:
        ...
    def num_descriptors(self) -> int:
        ...
    def num_descriptors_for_image(self, image_id: typing.SupportsInt) -> int:
        ...
    def num_frames(self) -> int:
        ...
    def num_images(self) -> int:
        ...
    def num_inlier_matches(self) -> int:
        ...
    def num_keypoints(self) -> int:
        ...
    def num_keypoints_for_image(self, image_id: typing.SupportsInt) -> int:
        ...
    def num_matched_image_pairs(self) -> int:
        ...
    def num_matches(self) -> int:
        ...
    def num_pose_priors(self) -> int:
        ...
    def num_rigs(self) -> int:
        ...
    def num_verified_image_pairs(self) -> int:
        ...
    def read_all_cameras(self) -> list[Camera]:
        ...
    def read_all_frames(self) -> list[Frame]:
        ...
    def read_all_images(self) -> list[Image]:
        ...
    def read_all_matches(self) -> tuple[list[int], list[typing.Annotated[numpy.typing.NDArray[numpy.uint32], "[m, 2]"]]]:
        ...
    def read_all_rigs(self) -> list[Rig]:
        ...
    def read_camera(self, camera_id: typing.SupportsInt) -> Camera:
        ...
    def read_descriptors(self, image_id: typing.SupportsInt) -> typing.Annotated[numpy.typing.NDArray[numpy.uint8], "[m, n]"]:
        ...
    def read_frame(self, frame_id: typing.SupportsInt) -> Frame:
        ...
    def read_image(self, image_id: typing.SupportsInt) -> Image:
        ...
    def read_image_with_name(self, name: str) -> pycolmap._core.Image | None:
        ...
    def read_keypoints(self, image_id: typing.SupportsInt) -> typing.Annotated[numpy.typing.NDArray[numpy.float32], "[m, n]"]:
        ...
    def read_matches(self, image_id1: typing.SupportsInt, image_id2: typing.SupportsInt) -> typing.Annotated[numpy.typing.NDArray[numpy.uint32], "[m, 2]"]:
        ...
    def read_num_matches(self) -> tuple[list[int], list[int]]:
        ...
    def read_pose_prior(self, image_id: typing.SupportsInt) -> PosePrior:
        ...
    def read_rig(self, rig_id: typing.SupportsInt) -> Rig:
        ...
    def read_rig_with_sensor(self, sensor_id: sensor_t) -> pycolmap._core.Rig | None:
        ...
    def read_two_view_geometries(self) -> tuple[list[int], list[TwoViewGeometry]]:
        ...
    def read_two_view_geometry(self, image_id1: typing.SupportsInt, image_id2: typing.SupportsInt) -> TwoViewGeometry:
        ...
    def read_two_view_geometry_num_inliers(self) -> tuple[list[int], list[int]]:
        ...
    def update_camera(self, camera: Camera) -> None:
        ...
    def update_frame(self, frame: Frame) -> None:
        ...
    def update_image(self, image: Image) -> None:
        ...
    def update_keypoints(self, image_id: typing.SupportsInt, keypoints: typing.Annotated[numpy.typing.ArrayLike, numpy.float32, "[m, n]"]) -> None:
        ...
    def update_pose_prior(self, image_id: typing.SupportsInt, pose_prior: PosePrior) -> None:
        ...
    def update_rig(self, rig: Rig) -> None:
        ...
    def write_camera(self, camera: Camera, use_camera_id: bool = False) -> int:
        ...
    def write_descriptors(self, image_id: typing.SupportsInt, descriptors: typing.Annotated[numpy.typing.ArrayLike, numpy.uint8, "[m, n]"]) -> None:
        ...
    def write_frame(self, frame: Frame, use_frame_id: bool = False) -> int:
        ...
    def write_image(self, image: Image, use_image_id: bool = False) -> int:
        ...
    def write_keypoints(self, image_id: typing.SupportsInt, keypoints: typing.Annotated[numpy.typing.ArrayLike, numpy.float32, "[m, n]"]) -> None:
        ...
    def write_matches(self, image_id1: typing.SupportsInt, image_id2: typing.SupportsInt, matches: typing.Annotated[numpy.typing.ArrayLike, numpy.uint32, "[m, 2]"]) -> None:
        ...
    def write_pose_prior(self, image_id: typing.SupportsInt, pose_prior: PosePrior) -> None:
        ...
    def write_rig(self, rig: Rig, use_rig_id: bool = False) -> int:
        ...
    def write_two_view_geometry(self, image_id1: typing.SupportsInt, image_id2: typing.SupportsInt, two_view_geometry: TwoViewGeometry) -> None:
        ...
class DatabaseCache:
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    @staticmethod
    def create(database: Database, min_num_matches: typing.SupportsInt, ignore_watermarks: bool, image_names: collections.abc.Set[str]) -> DatabaseCache:
        ...
    def __init__(self) -> None:
        ...
    def add_camera(self, arg0: Camera) -> None:
        ...
    def add_frame(self, arg0: Frame) -> None:
        ...
    def add_image(self, arg0: Image) -> None:
        ...
    def add_rig(self, arg0: Rig) -> None:
        ...
    def exists_camera(self, camera_id: typing.SupportsInt) -> bool:
        ...
    def exists_frame(self, frame_id: typing.SupportsInt) -> bool:
        ...
    def exists_image(self, image_id: typing.SupportsInt) -> bool:
        ...
    def exists_rig(self, rig_id: typing.SupportsInt) -> bool:
        ...
    def find_image_with_name(self, name: str) -> Image:
        ...
    def num_cameras(self) -> int:
        ...
    def num_frames(self) -> int:
        ...
    def num_images(self) -> int:
        ...
    def num_rigs(self) -> int:
        ...
    @property
    def cameras(self) -> dict[int, Camera]:
        ...
    @property
    def correspondence_graph(self) -> CorrespondenceGraph:
        ...
    @property
    def frames(self) -> dict[int, Frame]:
        ...
    @property
    def images(self) -> dict[int, Image]:
        ...
    @property
    def rigs(self) -> dict[int, Rig]:
        ...
class DatabaseTransaction:
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __enter__(self) -> None:
        ...
    def __exit__(self, *args) -> None:
        ...
    def __init__(self, database: Database) -> None:
        ...
class DelaunayMeshingOptions:
    __hash__: typing.ClassVar[None] = None
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __copy__(self) -> DelaunayMeshingOptions:
        ...
    def __deepcopy__(self, arg0: dict) -> DelaunayMeshingOptions:
        ...
    def __eq__(self, arg0: typing.Any) -> bool:
        ...
    def __getstate__(self) -> dict:
        ...
    @typing.overload
    def __init__(self) -> None:
        ...
    @typing.overload
    def __init__(self, arg0: dict) -> None:
        ...
    @typing.overload
    def __init__(self, **kwargs) -> None:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, arg0: dict) -> None:
        ...
    def check(self) -> bool:
        ...
    def mergedict(self, kwargs: dict) -> None:
        ...
    def summary(self, write_type: bool = False) -> str:
        ...
    def todict(self, recursive: bool = True) -> dict:
        ...
    @property
    def distance_sigma_factor(self) -> float:
        """
        The factor that is applied to the computed distance sigma, which isautomatically computed as the 25th percentile of edge lengths. A highervalue will increase the smoothness of the surface. (float, default: 1.0)
        """
    @distance_sigma_factor.setter
    def distance_sigma_factor(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def max_depth_dist(self) -> float:
        """
        Maximum relative depth difference between input point and a vertex of anexisting cell in the Delaunay triangulation, otherwise a new vertex iscreated in the triangulation. (float, default: 0.05)
        """
    @max_depth_dist.setter
    def max_depth_dist(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def max_proj_dist(self) -> float:
        """
        Unify input points into one cell in the Delaunay triangulation that fallwithin a reprojected radius of the given pixels. (float, default: 20.0)
        """
    @max_proj_dist.setter
    def max_proj_dist(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def max_side_length_factor(self) -> float:
        """
        Filtering thresholds for outlier surface mesh faces. If the longest side ofa mesh face (longest out of 3) exceeds the side lengths of all faces at acertain percentile by the given factor, then it is considered an outliermesh face and discarded. (float, default: 25.0)
        """
    @max_side_length_factor.setter
    def max_side_length_factor(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def max_side_length_percentile(self) -> float:
        """
        Filtering thresholds for outlier surface mesh faces. If the longest side ofa mesh face (longest out of 3) exceeds the side lengths of all faces at acertain percentile by the given factor, then it is considered an outliermesh face and discarded. (float, default: 95.0)
        """
    @max_side_length_percentile.setter
    def max_side_length_percentile(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def num_threads(self) -> int:
        """
        The number of threads to use for reconstruction. Default is all threads. (int, default: -1)
        """
    @num_threads.setter
    def num_threads(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def quality_regularization(self) -> float:
        """
        A higher quality regularization leads to a smoother surface. (float, default: 1.0)
        """
    @quality_regularization.setter
    def quality_regularization(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def visibility_sigma(self) -> float:
        """
        The standard deviation of wrt. the number of images seen by each point.Increasing this value decreases the influence of points seen in few images. (float, default: 3.0)
        """
    @visibility_sigma.setter
    def visibility_sigma(self, arg0: typing.SupportsFloat) -> None:
        ...
class Device:
    """
    Members:
    
      auto
    
      cpu
    
      cuda
    """
    __members__: typing.ClassVar[dict[str, Device]]  # value = {'auto': Device.auto, 'cpu': Device.cpu, 'cuda': Device.cuda}
    auto: typing.ClassVar[Device]  # value = Device.auto
    cpu: typing.ClassVar[Device]  # value = Device.cpu
    cuda: typing.ClassVar[Device]  # value = Device.cuda
    @staticmethod
    def __repr__(*args, **kwargs):
        """
        __str__(self: object, /) -> str
        """
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __eq__(self, other: typing.Any) -> bool:
        ...
    def __getstate__(self) -> int:
        ...
    def __hash__(self) -> int:
        ...
    def __index__(self) -> int:
        ...
    @typing.overload
    def __init__(self, value: typing.SupportsInt) -> None:
        ...
    @typing.overload
    def __init__(self, name: str) -> None:
        ...
    def __int__(self) -> int:
        ...
    def __ne__(self, other: typing.Any) -> bool:
        ...
    def __setstate__(self, state: typing.SupportsInt) -> None:
        ...
    def __str__(self) -> str:
        ...
    @property
    def name(self) -> str:
        ...
    @property
    def value(self) -> int:
        ...
class EstimateTriangulationOptions:
    __hash__: typing.ClassVar[None] = None
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __copy__(self) -> EstimateTriangulationOptions:
        ...
    def __deepcopy__(self, arg0: dict) -> EstimateTriangulationOptions:
        ...
    def __eq__(self, arg0: typing.Any) -> bool:
        ...
    def __getstate__(self) -> dict:
        ...
    @typing.overload
    def __init__(self) -> None:
        ...
    @typing.overload
    def __init__(self, arg0: dict) -> None:
        ...
    @typing.overload
    def __init__(self, **kwargs) -> None:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, arg0: dict) -> None:
        ...
    def mergedict(self, kwargs: dict) -> None:
        ...
    def summary(self, write_type: bool = False) -> str:
        ...
    def todict(self, recursive: bool = True) -> dict:
        ...
    @property
    def min_tri_angle(self) -> float:
        """
        Minimum triangulation angle in radians. (float, default: 0.0)
        """
    @min_tri_angle.setter
    def min_tri_angle(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def ransac(self) -> RANSACOptions:
        """
        RANSAC options. (RANSACOptions, default: RANSACOptions(max_error=0.03490658503988659, min_inlier_ratio=0.02, confidence=0.9999, dyn_num_trials_multiplier=3.0, min_num_trials=0, max_num_trials=10000, random_seed=-1))
        """
    @ransac.setter
    def ransac(self, arg0: RANSACOptions) -> None:
        ...
    @property
    def residual_type(self) -> TriangulationResidualType:
        """
        Employed residual type. (TriangulationResidualType, default: TriangulationResidualType.ANGULAR_ERROR)
        """
    @residual_type.setter
    def residual_type(self, arg0: TriangulationResidualType) -> None:
        ...
class ExhaustivePairGenerator(PairGenerator):
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __init__(self, options: ExhaustivePairingOptions, database: Database) -> None:
        ...
class ExhaustivePairingOptions:
    __hash__: typing.ClassVar[None] = None
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __copy__(self) -> ExhaustivePairingOptions:
        ...
    def __deepcopy__(self, arg0: dict) -> ExhaustivePairingOptions:
        ...
    def __eq__(self, arg0: typing.Any) -> bool:
        ...
    def __getstate__(self) -> dict:
        ...
    @typing.overload
    def __init__(self) -> None:
        ...
    @typing.overload
    def __init__(self, arg0: dict) -> None:
        ...
    @typing.overload
    def __init__(self, **kwargs) -> None:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, arg0: dict) -> None:
        ...
    def check(self) -> bool:
        ...
    def mergedict(self, kwargs: dict) -> None:
        ...
    def summary(self, write_type: bool = False) -> str:
        ...
    def todict(self, recursive: bool = True) -> dict:
        ...
    @property
    def block_size(self) -> int:
        """
         (int, default: 50)
        """
    @block_size.setter
    def block_size(self, arg0: typing.SupportsInt) -> None:
        ...
class ExperimentalPoseParam:
    __hash__: typing.ClassVar[None] = None
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __copy__(self) -> ExperimentalPoseParam:
        ...
    def __deepcopy__(self, arg0: dict) -> ExperimentalPoseParam:
        ...
    def __eq__(self, arg0: typing.Any) -> bool:
        ...
    def __getstate__(self) -> dict:
        ...
    @typing.overload
    def __init__(self) -> None:
        ...
    @typing.overload
    def __init__(self, arg0: dict) -> None:
        ...
    @typing.overload
    def __init__(self, **kwargs) -> None:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, arg0: dict) -> None:
        ...
    def mergedict(self, kwargs: dict) -> None:
        ...
    def summary(self, write_type: bool = False) -> str:
        ...
    def todict(self, recursive: bool = True) -> dict:
        ...
    @property
    def image_id(self) -> int:
        """
         (int, default: 4294967295)
        """
    @image_id.setter
    def image_id(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def qvec(self) -> numpy.typing.NDArray[numpy.float64] | None:
        """
         (NoneType, default: None)
        """
    @qvec.setter
    def qvec(self, arg1: typing.Annotated[numpy.typing.ArrayLike, numpy.float64]) -> None:
        ...
    @property
    def tvec(self) -> numpy.typing.NDArray[numpy.float64] | None:
        """
         (NoneType, default: None)
        """
    @tvec.setter
    def tvec(self, arg1: typing.Annotated[numpy.typing.ArrayLike, numpy.float64]) -> None:
        ...
class FeatureExtractionOptions:
    __hash__: typing.ClassVar[None] = None
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __copy__(self) -> FeatureExtractionOptions:
        ...
    def __deepcopy__(self, arg0: dict) -> FeatureExtractionOptions:
        ...
    def __eq__(self, arg0: typing.Any) -> bool:
        ...
    def __getstate__(self) -> dict:
        ...
    @typing.overload
    def __init__(self) -> None:
        ...
    @typing.overload
    def __init__(self, arg0: dict) -> None:
        ...
    @typing.overload
    def __init__(self, **kwargs) -> None:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, arg0: dict) -> None:
        ...
    def check(self) -> bool:
        ...
    def mergedict(self, kwargs: dict) -> None:
        ...
    def summary(self, write_type: bool = False) -> str:
        ...
    def todict(self, recursive: bool = True) -> dict:
        ...
    @property
    def gpu_index(self) -> str:
        """
        Index of the GPU used for feature matching. For multi-GPU matching, you should separate multiple GPU indices by comma, e.g., '0,1,2,3'. (str, default: -1)
        """
    @gpu_index.setter
    def gpu_index(self, arg0: str) -> None:
        ...
    @property
    def max_image_size(self) -> int:
        """
        Maximum image size, otherwise image will be down-scaled. (int, default: 3200)
        """
    @max_image_size.setter
    def max_image_size(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def num_threads(self) -> int:
        """
        Number of threads for feature matching and geometric verification. (int, default: -1)
        """
    @num_threads.setter
    def num_threads(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def sift(self) -> SiftExtractionOptions:
        """
         (SiftExtractionOptions, default: SiftExtractionOptions(max_num_features=8192, first_octave=-1, num_octaves=4, octave_resolution=3, peak_threshold=0.006666666666666667, edge_threshold=10.0, estimate_affine_shape=False, max_num_orientations=2, upright=False, darkness_adaptivity=False, domain_size_pooling=False, dsp_min_scale=0.16666666666666666, dsp_max_scale=3.0, dsp_num_scales=10, normalization=Normalization.L1_ROOT))
        """
    @sift.setter
    def sift(self, arg0: SiftExtractionOptions) -> None:
        ...
    @property
    def use_gpu(self) -> bool:
        """
         (bool, default: False)
        """
    @use_gpu.setter
    def use_gpu(self, arg0: bool) -> None:
        ...
class FeatureKeypoint:
    __hash__: typing.ClassVar[None] = None
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    @staticmethod
    def from_shape_parameters(arg0: typing.SupportsFloat, arg1: typing.SupportsFloat, arg2: typing.SupportsFloat, arg3: typing.SupportsFloat, arg4: typing.SupportsFloat, arg5: typing.SupportsFloat) -> FeatureKeypoint:
        ...
    def __copy__(self) -> FeatureKeypoint:
        ...
    def __deepcopy__(self, arg0: dict) -> FeatureKeypoint:
        ...
    def __eq__(self, arg0: FeatureKeypoint) -> bool:
        ...
    def __getstate__(self) -> dict:
        ...
    @typing.overload
    def __init__(self) -> None:
        ...
    @typing.overload
    def __init__(self, arg0: dict) -> None:
        ...
    @typing.overload
    def __init__(self, **kwargs) -> None:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, arg0: dict) -> None:
        ...
    def compute_orientation(self) -> float:
        ...
    def compute_scale(self) -> float:
        ...
    def compute_scale_x(self) -> float:
        ...
    def compute_scale_y(self) -> float:
        ...
    def compute_shear(self) -> float:
        ...
    def mergedict(self, kwargs: dict) -> None:
        ...
    @typing.overload
    def rescale(self, arg0: typing.SupportsFloat) -> None:
        ...
    @typing.overload
    def rescale(self, arg0: typing.SupportsFloat, arg1: typing.SupportsFloat) -> None:
        ...
    def summary(self, write_type: bool = False) -> str:
        ...
    def todict(self, recursive: bool = True) -> dict:
        ...
    @property
    def a11(self) -> float:
        """
         (float, default: 1.0)
        """
    @a11.setter
    def a11(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def a12(self) -> float:
        """
         (float, default: 0.0)
        """
    @a12.setter
    def a12(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def a21(self) -> float:
        """
         (float, default: 0.0)
        """
    @a21.setter
    def a21(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def a22(self) -> float:
        """
         (float, default: 1.0)
        """
    @a22.setter
    def a22(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def x(self) -> float:
        """
         (float, default: 0.0)
        """
    @x.setter
    def x(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def y(self) -> float:
        """
         (float, default: 0.0)
        """
    @y.setter
    def y(self, arg0: typing.SupportsFloat) -> None:
        ...
class FeatureKeypoints:
    __hash__: typing.ClassVar[None] = None
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __bool__(self) -> bool:
        """
        Check whether the list is nonempty
        """
    def __contains__(self, x: FeatureKeypoint) -> bool:
        """
        Return true the container contains ``x``
        """
    @typing.overload
    def __delitem__(self, arg0: typing.SupportsInt) -> None:
        """
        Delete the list elements at index ``i``
        """
    @typing.overload
    def __delitem__(self, arg0: slice) -> None:
        """
        Delete list elements using a slice object
        """
    def __eq__(self, arg0: FeatureKeypoints) -> bool:
        ...
    @typing.overload
    def __getitem__(self, s: slice) -> FeatureKeypoints:
        """
        Retrieve list elements using a slice object
        """
    @typing.overload
    def __getitem__(self, arg0: typing.SupportsInt) -> FeatureKeypoint:
        ...
    @typing.overload
    def __init__(self) -> None:
        ...
    @typing.overload
    def __init__(self, arg0: FeatureKeypoints) -> None:
        """
        Copy constructor
        """
    @typing.overload
    def __init__(self, arg0: collections.abc.Iterable) -> None:
        ...
    def __iter__(self) -> collections.abc.Iterator[FeatureKeypoint]:
        ...
    def __len__(self) -> int:
        ...
    def __ne__(self, arg0: FeatureKeypoints) -> bool:
        ...
    @typing.overload
    def __setitem__(self, arg0: typing.SupportsInt, arg1: FeatureKeypoint) -> None:
        ...
    @typing.overload
    def __setitem__(self, arg0: slice, arg1: FeatureKeypoints) -> None:
        """
        Assign list elements using a slice object
        """
    def append(self, x: FeatureKeypoint) -> None:
        """
        Add an item to the end of the list
        """
    def clear(self) -> None:
        """
        Clear the contents
        """
    def count(self, x: FeatureKeypoint) -> int:
        """
        Return the number of times ``x`` appears in the list
        """
    @typing.overload
    def extend(self, L: FeatureKeypoints) -> None:
        """
        Extend the list by appending all the items in the given list
        """
    @typing.overload
    def extend(self, L: collections.abc.Iterable) -> None:
        """
        Extend the list by appending all the items in the given list
        """
    def insert(self, i: typing.SupportsInt, x: FeatureKeypoint) -> None:
        """
        Insert an item at a given position.
        """
    @typing.overload
    def pop(self) -> FeatureKeypoint:
        """
        Remove and return the last item
        """
    @typing.overload
    def pop(self, i: typing.SupportsInt) -> FeatureKeypoint:
        """
        Remove and return the item at index ``i``
        """
    def remove(self, x: FeatureKeypoint) -> None:
        """
        Remove the first item from the list whose value is x. It is an error if there is no such item.
        """
class FeatureMatch:
    __hash__: typing.ClassVar[None] = None
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __copy__(self) -> FeatureMatch:
        ...
    def __deepcopy__(self, arg0: dict) -> FeatureMatch:
        ...
    def __eq__(self, arg0: FeatureMatch) -> bool:
        ...
    def __getstate__(self) -> dict:
        ...
    @typing.overload
    def __init__(self) -> None:
        ...
    @typing.overload
    def __init__(self, arg0: typing.SupportsInt, arg1: typing.SupportsInt) -> None:
        ...
    @typing.overload
    def __init__(self, arg0: dict) -> None:
        ...
    @typing.overload
    def __init__(self, **kwargs) -> None:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, arg0: dict) -> None:
        ...
    def mergedict(self, kwargs: dict) -> None:
        ...
    def summary(self, write_type: bool = False) -> str:
        ...
    def todict(self, recursive: bool = True) -> dict:
        ...
    @property
    def point2D_idx1(self) -> int:
        """
         (int, default: 4294967295)
        """
    @point2D_idx1.setter
    def point2D_idx1(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def point2D_idx2(self) -> int:
        """
         (int, default: 4294967295)
        """
    @point2D_idx2.setter
    def point2D_idx2(self, arg0: typing.SupportsInt) -> None:
        ...
class FeatureMatches:
    __hash__: typing.ClassVar[None] = None
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __bool__(self) -> bool:
        """
        Check whether the list is nonempty
        """
    def __contains__(self, x: FeatureMatch) -> bool:
        """
        Return true the container contains ``x``
        """
    @typing.overload
    def __delitem__(self, arg0: typing.SupportsInt) -> None:
        """
        Delete the list elements at index ``i``
        """
    @typing.overload
    def __delitem__(self, arg0: slice) -> None:
        """
        Delete list elements using a slice object
        """
    def __eq__(self, arg0: FeatureMatches) -> bool:
        ...
    @typing.overload
    def __getitem__(self, s: slice) -> FeatureMatches:
        """
        Retrieve list elements using a slice object
        """
    @typing.overload
    def __getitem__(self, arg0: typing.SupportsInt) -> FeatureMatch:
        ...
    @typing.overload
    def __init__(self) -> None:
        ...
    @typing.overload
    def __init__(self, arg0: FeatureMatches) -> None:
        """
        Copy constructor
        """
    @typing.overload
    def __init__(self, arg0: collections.abc.Iterable) -> None:
        ...
    def __iter__(self) -> collections.abc.Iterator[FeatureMatch]:
        ...
    def __len__(self) -> int:
        ...
    def __ne__(self, arg0: FeatureMatches) -> bool:
        ...
    @typing.overload
    def __setitem__(self, arg0: typing.SupportsInt, arg1: FeatureMatch) -> None:
        ...
    @typing.overload
    def __setitem__(self, arg0: slice, arg1: FeatureMatches) -> None:
        """
        Assign list elements using a slice object
        """
    def append(self, x: FeatureMatch) -> None:
        """
        Add an item to the end of the list
        """
    def clear(self) -> None:
        """
        Clear the contents
        """
    def count(self, x: FeatureMatch) -> int:
        """
        Return the number of times ``x`` appears in the list
        """
    @typing.overload
    def extend(self, L: FeatureMatches) -> None:
        """
        Extend the list by appending all the items in the given list
        """
    @typing.overload
    def extend(self, L: collections.abc.Iterable) -> None:
        """
        Extend the list by appending all the items in the given list
        """
    def insert(self, i: typing.SupportsInt, x: FeatureMatch) -> None:
        """
        Insert an item at a given position.
        """
    @typing.overload
    def pop(self) -> FeatureMatch:
        """
        Remove and return the last item
        """
    @typing.overload
    def pop(self, i: typing.SupportsInt) -> FeatureMatch:
        """
        Remove and return the item at index ``i``
        """
    def remove(self, x: FeatureMatch) -> None:
        """
        Remove the first item from the list whose value is x. It is an error if there is no such item.
        """
class FeatureMatchingOptions:
    __hash__: typing.ClassVar[None] = None
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __copy__(self) -> FeatureMatchingOptions:
        ...
    def __deepcopy__(self, arg0: dict) -> FeatureMatchingOptions:
        ...
    def __eq__(self, arg0: typing.Any) -> bool:
        ...
    def __getstate__(self) -> dict:
        ...
    @typing.overload
    def __init__(self) -> None:
        ...
    @typing.overload
    def __init__(self, arg0: dict) -> None:
        ...
    @typing.overload
    def __init__(self, **kwargs) -> None:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, arg0: dict) -> None:
        ...
    def check(self) -> bool:
        ...
    def mergedict(self, kwargs: dict) -> None:
        ...
    def summary(self, write_type: bool = False) -> str:
        ...
    def todict(self, recursive: bool = True) -> dict:
        ...
    @property
    def gpu_index(self) -> str:
        """
        Index of the GPU used for feature matching. For multi-GPU matching, you should separate multiple GPU indices by comma, e.g., "0,1,2,3". (str, default: -1)
        """
    @gpu_index.setter
    def gpu_index(self, arg0: str) -> None:
        ...
    @property
    def guided_matching(self) -> bool:
        """
        Whether to perform guided matching, if geometric verification succeeds. (bool, default: False)
        """
    @guided_matching.setter
    def guided_matching(self, arg0: bool) -> None:
        ...
    @property
    def max_num_matches(self) -> int:
        """
        Maximum number of matches. (int, default: 32768)
        """
    @max_num_matches.setter
    def max_num_matches(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def num_threads(self) -> int:
        """
         (int, default: -1)
        """
    @num_threads.setter
    def num_threads(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def rig_verification(self) -> bool:
        """
        Whether to perform geometric verification using rig constraints between pairs of non-trivial frames. If disabled, performs geometric two-view verification for non-trivial frames without rig constraints. (bool, default: False)
        """
    @rig_verification.setter
    def rig_verification(self, arg0: bool) -> None:
        ...
    @property
    def sift(self) -> SiftMatchingOptions:
        """
         (SiftMatchingOptions, default: SiftMatchingOptions(max_ratio=0.8, max_distance=0.7, cross_check=True, cpu_brute_force_matcher=False))
        """
    @sift.setter
    def sift(self, arg0: SiftMatchingOptions) -> None:
        ...
    @property
    def skip_image_pairs_in_same_frame(self) -> bool:
        """
        Whether to skip matching images within the same frame. This is useful for the case of non-overlapping cameras in a rig. (bool, default: False)
        """
    @skip_image_pairs_in_same_frame.setter
    def skip_image_pairs_in_same_frame(self, arg0: bool) -> None:
        ...
    @property
    def use_gpu(self) -> bool:
        """
         (bool, default: False)
        """
    @use_gpu.setter
    def use_gpu(self, arg0: bool) -> None:
        ...
class Frame:
    __hash__: typing.ClassVar[None] = None
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __copy__(self) -> Frame:
        ...
    def __deepcopy__(self, arg0: dict) -> Frame:
        ...
    def __eq__(self, arg0: Frame) -> bool:
        ...
    def __getstate__(self) -> dict:
        ...
    @typing.overload
    def __init__(self) -> None:
        ...
    @typing.overload
    def __init__(self, arg0: dict) -> None:
        ...
    @typing.overload
    def __init__(self, **kwargs) -> None:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, arg0: dict) -> None:
        ...
    def add_data_id(self, arg0: data_t) -> None:
        """
        Associate data with frame.
        """
    def has_data(self, arg0: data_t) -> bool:
        """
        Check whether frame has associated data.
        """
    def has_pose(self) -> bool:
        """
        Whether the frame has a valid pose.
        """
    def mergedict(self, kwargs: dict) -> None:
        ...
    def num_data_ids(self) -> int:
        """
        Number of associated data items in frame.
        """
    def reset_pose(self) -> None:
        """
        Invalidate the pose of the frame.
        """
    def reset_rig_ptr(self) -> None:
        """
        Make the rig pointer a nullptr.
        """
    def sensor_from_world(self, sensor_id: sensor_t) -> Rigid3d:
        """
        The transformation from the world to a specific sensor.
        """
    def set_cam_from_world(self, camera_id: typing.SupportsInt, cam_from_world: Rigid3d) -> None:
        """
        Set the world to frame from the given camera from world transformation.
        """
    def summary(self, write_type: bool = False) -> str:
        ...
    def todict(self, recursive: bool = True) -> dict:
        ...
    @property
    def data_ids(self) -> set[data_t]:
        """
        The associated data. (set, default: set())
        """
    @property
    def frame_id(self) -> int:
        """
        Unique identifier of the frame. (int, default: 4294967295)
        """
    @frame_id.setter
    def frame_id(self, arg1: typing.SupportsInt) -> None:
        ...
    @property
    def image_ids(self) -> list[data_t]:
        """
        The associated image data. (list, default: [])
        """
    @property
    def rig(self) -> pycolmap._core.Rig | None:
        """
        The associated rig object. (NoneType, default: None)
        """
    @rig.setter
    def rig(self, arg1: Rig) -> None:
        ...
    @property
    def rig_from_world(self) -> pycolmap._core.Rigid3d | None:
        """
        The pose of the frame, defined as the transformation from world to rig space. (NoneType, default: None)
        """
    @rig_from_world.setter
    def rig_from_world(self, arg1: pycolmap._core.Rigid3d | None) -> None:
        ...
    @property
    def rig_id(self) -> int:
        """
        Unique identifier of the rig. (int, default: 4294967295)
        """
    @rig_id.setter
    def rig_id(self, arg1: typing.SupportsInt) -> None:
        ...
class FrameMap:
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __bool__(self) -> bool:
        """
        Check whether the map is nonempty
        """
    @typing.overload
    def __contains__(self, arg0: typing.SupportsInt) -> bool:
        ...
    @typing.overload
    def __contains__(self, arg0: typing.Any) -> bool:
        ...
    def __delitem__(self, arg0: typing.SupportsInt) -> None:
        ...
    def __getitem__(self, arg0: typing.SupportsInt) -> Frame:
        ...
    def __init__(self) -> None:
        ...
    def __iter__(self) -> collections.abc.Iterator[int]:
        ...
    def __len__(self) -> int:
        ...
    def __repr__(self) -> str:
        """
        Return the canonical string representation of this map.
        """
    def __setitem__(self, arg0: typing.SupportsInt, arg1: Frame) -> None:
        ...
    def items(self) -> typing.ItemsView:
        ...
    def keys(self) -> typing.KeysView:
        ...
    def values(self) -> typing.ValuesView:
        ...
class GPSTransform:
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __init__(self, ellipsoid: GPSTransfromEllipsoid = ...) -> None:
        ...
    def ecef_to_ellipsoid(self, xyz_in_ecef: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[m, 3]"]) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[m, 3]"]:
        ...
    def ecef_to_enu(self, xyz_in_ecef: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[m, 3]"], ref_lat: typing.SupportsFloat, ref_lon: typing.SupportsFloat) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[m, 3]"]:
        ...
    def ellipsoid_to_ecef(self, lat_lon_alt: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[m, 3]"]) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[m, 3]"]:
        ...
    def ellipsoid_to_enu(self, lat_lon_alt: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[m, 3]"], ref_lat: typing.SupportsFloat, ref_lon: typing.SupportsFloat) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[m, 3]"]:
        ...
    def ellipsoid_to_utm(self, lat_lon_alt: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[m, 3]"]) -> tuple[typing.Annotated[numpy.typing.NDArray[numpy.float64], "[m, 3]"], int]:
        ...
    def enu_to_ecef(self, xyz_in_enu: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[m, 3]"], ref_lat: typing.SupportsFloat, ref_lon: typing.SupportsFloat, ref_alt: typing.SupportsFloat) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[m, 3]"]:
        ...
    def enu_to_ellipsoid(self, xyz_in_enu: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[m, 3]"], ref_lat: typing.SupportsFloat, ref_lon: typing.SupportsFloat, ref_alt: typing.SupportsFloat) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[m, 3]"]:
        ...
    def utm_to_ellipsoid(self, xyz_in_utm: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[m, 3]"], zone: typing.SupportsInt, is_north: bool) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[m, 3]"]:
        ...
class GPSTransfromEllipsoid:
    """
    Members:
    
      GRS80
    
      WGS84
    """
    GRS80: typing.ClassVar[GPSTransfromEllipsoid]  # value = GPSTransfromEllipsoid.GRS80
    WGS84: typing.ClassVar[GPSTransfromEllipsoid]  # value = GPSTransfromEllipsoid.WGS84
    __members__: typing.ClassVar[dict[str, GPSTransfromEllipsoid]]  # value = {'GRS80': GPSTransfromEllipsoid.GRS80, 'WGS84': GPSTransfromEllipsoid.WGS84}
    @staticmethod
    def __repr__(*args, **kwargs):
        """
        __str__(self: object, /) -> str
        """
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __eq__(self, other: typing.Any) -> bool:
        ...
    def __getstate__(self) -> int:
        ...
    def __hash__(self) -> int:
        ...
    def __index__(self) -> int:
        ...
    @typing.overload
    def __init__(self, value: typing.SupportsInt) -> None:
        ...
    @typing.overload
    def __init__(self, name: str) -> None:
        ...
    def __int__(self) -> int:
        ...
    def __ne__(self, other: typing.Any) -> bool:
        ...
    def __setstate__(self, state: typing.SupportsInt) -> None:
        ...
    def __str__(self) -> str:
        ...
    @property
    def name(self) -> str:
        ...
    @property
    def value(self) -> int:
        ...
class Image:
    __hash__: typing.ClassVar[None] = None
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __copy__(self) -> Image:
        ...
    def __deepcopy__(self, arg0: dict) -> Image:
        ...
    def __eq__(self, arg0: Image) -> bool:
        ...
    def __getstate__(self) -> dict:
        ...
    @typing.overload
    def __init__(self) -> None:
        ...
    @typing.overload
    def __init__(self, name: str = '', points2D: Point2DList = ..., camera_id: typing.SupportsInt = ..., image_id: typing.SupportsInt = ...) -> None:
        ...
    @typing.overload
    def __init__(self, name: str = '', keypoints: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[m, 2]"] = ..., camera_id: typing.SupportsInt = ..., image_id: typing.SupportsInt = ...) -> None:
        ...
    @typing.overload
    def __init__(self, arg0: dict) -> None:
        ...
    @typing.overload
    def __init__(self, **kwargs) -> None:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, arg0: dict) -> None:
        ...
    def cam_from_world(self) -> Rigid3d:
        """
        The pose of the image, defined as the transformation from world to camera space. This method is read-only and support non-trivial frame (rig).
        """
    def get_observation_point2D_idxs(self) -> list[int]:
        """
        Get the indices of 2D points that observe a 3D point.
        """
    def get_observation_points2D(self) -> Point2DList:
        """
        Get the 2D points that observe a 3D point.
        """
    def has_camera_id(self) -> bool:
        """
        Check whether identifier of camera has been set.
        """
    def has_camera_ptr(self) -> bool:
        """
        Check whether the camera pointer has been set.
        """
    def has_frame_id(self) -> bool:
        """
        Check whether identifier of frame has been set.
        """
    def has_frame_ptr(self) -> bool:
        """
        Check whether the frame pointer has been set.
        """
    def has_point3D(self, point3D_id: typing.SupportsInt) -> bool:
        """
        Check whether one of the image points is part of a 3D point track.
        """
    def mergedict(self, kwargs: dict) -> None:
        ...
    def num_points2D(self) -> int:
        """
        Get the number of image points (keypoints).
        """
    def point2D(self, point2D_idx: typing.SupportsInt) -> Point2D:
        """
        Direct accessor for a point2D.
        """
    def project_point(self, point3D: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[3, 1]"]) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[2, 1]"] | None:
        """
        Project 3D point onto the image
        """
    def projection_center(self) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[3, 1]"]:
        """
        Extract the projection center in world space.
        """
    def reset_camera_ptr(self) -> None:
        """
        Make the camera pointer a nullptr.
        """
    def reset_frame_ptr(self) -> None:
        """
        Make the frame pointer a nullptr.
        """
    def reset_point3D_for_point2D(self, point2D_idx: typing.SupportsInt) -> None:
        """
        Set the point as not triangulated, i.e. it is not part of a 3D point track
        """
    def set_point3D_for_point2D(self, point2D_Idx: typing.SupportsInt, point3D_id: typing.SupportsInt) -> None:
        """
        Set the point as triangulated, i.e. it is part of a 3D point track.
        """
    def summary(self, write_type: bool = False) -> str:
        ...
    def todict(self, recursive: bool = True) -> dict:
        ...
    def viewing_direction(self) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[3, 1]"]:
        """
        Extract the viewing direction of the image.
        """
    @property
    def camera(self) -> pycolmap._core.Camera | None:
        """
        The associated camera object. (NoneType, default: None)
        """
    @camera.setter
    def camera(self, arg1: Camera) -> None:
        ...
    @property
    def camera_id(self) -> int:
        """
        Unique identifier of the camera. (int, default: 4294967295)
        """
    @camera_id.setter
    def camera_id(self, arg1: typing.SupportsInt) -> None:
        ...
    @property
    def data_id(self) -> data_t:
        """
        Unique identifier of the data. (data_t, default: data_t(sensor_id=sensor_t(type=SensorType.CAMERA, id=4294967295), id=4294967295))
        """
    @property
    def frame(self) -> pycolmap._core.Frame | None:
        """
        The associated frame object. (NoneType, default: None)
        """
    @frame.setter
    def frame(self, arg1: Frame) -> None:
        ...
    @property
    def frame_id(self) -> int:
        """
        Unique identifier of the frame. (int, default: 4294967295)
        """
    @frame_id.setter
    def frame_id(self, arg1: typing.SupportsInt) -> None:
        ...
    @property
    def has_pose(self) -> bool:
        """
        Whether the image has a valid pose. (bool, default: False)
        """
    @property
    def image_id(self) -> int:
        """
        Unique identifier of the image. (int, default: 4294967295)
        """
    @image_id.setter
    def image_id(self, arg1: typing.SupportsInt) -> None:
        ...
    @property
    def name(self) -> str:
        """
        Name of the image. (str, default: )
        """
    @name.setter
    def name(self, arg1: str) -> None:
        ...
    @property
    def num_points3D(self) -> int:
        """
        Get the number of triangulations, i.e. the number of points that
        are part of a 3D point track. (int, default: 0)
        """
    @property
    def points2D(self) -> Point2DList:
        """
        Array of Points2D (=keypoints). (Point2DList, default: Point2DList[])
        """
    @points2D.setter
    def points2D(self, arg1: Point2DList) -> None:
        ...
class ImageAlignmentError:
    image_name: str
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __init__(self) -> None:
        ...
    @property
    def proj_center_error(self) -> float:
        ...
    @proj_center_error.setter
    def proj_center_error(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def rotation_error_deg(self) -> float:
        ...
    @rotation_error_deg.setter
    def rotation_error_deg(self, arg0: typing.SupportsFloat) -> None:
        ...
class ImageMap:
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __bool__(self) -> bool:
        """
        Check whether the map is nonempty
        """
    @typing.overload
    def __contains__(self, arg0: typing.SupportsInt) -> bool:
        ...
    @typing.overload
    def __contains__(self, arg0: typing.Any) -> bool:
        ...
    def __delitem__(self, arg0: typing.SupportsInt) -> None:
        ...
    def __getitem__(self, arg0: typing.SupportsInt) -> Image:
        ...
    def __init__(self) -> None:
        ...
    def __iter__(self) -> collections.abc.Iterator[int]:
        ...
    def __len__(self) -> int:
        ...
    def __repr__(self) -> str:
        """
        Return the canonical string representation of this map.
        """
    def __setitem__(self, arg0: typing.SupportsInt, arg1: Image) -> None:
        ...
    def items(self) -> typing.ItemsView:
        ...
    def keys(self) -> typing.KeysView:
        ...
    def values(self) -> typing.ValuesView:
        ...
class ImagePairStat:
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __init__(self) -> None:
        ...
    @property
    def num_total_corrs(self) -> int:
        ...
    @num_total_corrs.setter
    def num_total_corrs(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def num_tri_corrs(self) -> int:
        ...
    @num_tri_corrs.setter
    def num_tri_corrs(self, arg0: typing.SupportsInt) -> None:
        ...
class ImageReaderOptions:
    __hash__: typing.ClassVar[None] = None
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __copy__(self) -> ImageReaderOptions:
        ...
    def __deepcopy__(self, arg0: dict) -> ImageReaderOptions:
        ...
    def __eq__(self, arg0: typing.Any) -> bool:
        ...
    def __getstate__(self) -> dict:
        ...
    @typing.overload
    def __init__(self) -> None:
        ...
    @typing.overload
    def __init__(self, arg0: dict) -> None:
        ...
    @typing.overload
    def __init__(self, **kwargs) -> None:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, arg0: dict) -> None:
        ...
    def check(self) -> bool:
        ...
    def mergedict(self, kwargs: dict) -> None:
        ...
    def summary(self, write_type: bool = False) -> str:
        ...
    def todict(self, recursive: bool = True) -> dict:
        ...
    @property
    def camera_mask_path(self) -> str:
        """
        Optional path to an image file specifying a mask for all images. No features will be extracted in regions where the mask is black (pixel intensity value 0 in grayscale) (str, default: )
        """
    @camera_mask_path.setter
    def camera_mask_path(self, arg0: str) -> None:
        ...
    @property
    def camera_model(self) -> str:
        """
        Name of the camera model. (str, default: SIMPLE_RADIAL)
        """
    @camera_model.setter
    def camera_model(self, arg0: str) -> None:
        ...
    @property
    def camera_params(self) -> str:
        """
        Manual specification of camera parameters. If empty, camera parameters will be extracted from EXIF, i.e. principal point and focal length. (str, default: )
        """
    @camera_params.setter
    def camera_params(self, arg0: str) -> None:
        ...
    @property
    def default_focal_length_factor(self) -> float:
        """
        If camera parameters are not specified manually and the image does not have focal length EXIF information, the focal length is set to the value `default_focal_length_factor * max(width, height)`. (float, default: 1.2)
        """
    @default_focal_length_factor.setter
    def default_focal_length_factor(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def existing_camera_id(self) -> int:
        """
        Whether to explicitly use an existing camera for all images. Note that in this case the specified camera model and parameters are ignored. (int, default: -1)
        """
    @existing_camera_id.setter
    def existing_camera_id(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def mask_path(self) -> str:
        """
        Optional root path to folder which contains imagemasks. For a given image, the corresponding maskmust have the same sub-path below this root as theimage has below image_path. The filename must beequal, aside from the added extension .png. For example, for an image image_path/abc/012.jpg,the mask would be mask_path/abc/012.jpg.png. Nofeatures will be extracted in regions where themask image is black (pixel intensity value 0 ingrayscale). (str, default: )
        """
    @mask_path.setter
    def mask_path(self, arg0: str) -> None:
        ...
class ImageScore:
    __hash__: typing.ClassVar[None] = None
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __copy__(self) -> ImageScore:
        ...
    def __deepcopy__(self, arg0: dict) -> ImageScore:
        ...
    def __eq__(self, arg0: typing.Any) -> bool:
        ...
    def __getstate__(self) -> dict:
        ...
    @typing.overload
    def __init__(self) -> None:
        ...
    @typing.overload
    def __init__(self, arg0: dict) -> None:
        ...
    @typing.overload
    def __init__(self, **kwargs) -> None:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, arg0: dict) -> None:
        ...
    def mergedict(self, kwargs: dict) -> None:
        ...
    def summary(self, write_type: bool = False) -> str:
        ...
    def todict(self, recursive: bool = True) -> dict:
        ...
    @property
    def image_id(self) -> int:
        """
         (int, default: -1)
        """
    @property
    def score(self) -> float:
        """
         (float, default: 0.0)
        """
class ImageSelectionMethod:
    """
    Members:
    
      MAX_VISIBLE_POINTS_NUM
    
      MAX_VISIBLE_POINTS_RATIO
    
      MIN_UNCERTAINTY
    """
    MAX_VISIBLE_POINTS_NUM: typing.ClassVar[ImageSelectionMethod]  # value = ImageSelectionMethod.MAX_VISIBLE_POINTS_NUM
    MAX_VISIBLE_POINTS_RATIO: typing.ClassVar[ImageSelectionMethod]  # value = ImageSelectionMethod.MAX_VISIBLE_POINTS_RATIO
    MIN_UNCERTAINTY: typing.ClassVar[ImageSelectionMethod]  # value = ImageSelectionMethod.MIN_UNCERTAINTY
    __members__: typing.ClassVar[dict[str, ImageSelectionMethod]]  # value = {'MAX_VISIBLE_POINTS_NUM': ImageSelectionMethod.MAX_VISIBLE_POINTS_NUM, 'MAX_VISIBLE_POINTS_RATIO': ImageSelectionMethod.MAX_VISIBLE_POINTS_RATIO, 'MIN_UNCERTAINTY': ImageSelectionMethod.MIN_UNCERTAINTY}
    @staticmethod
    def __repr__(*args, **kwargs):
        """
        __str__(self: object, /) -> str
        """
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __eq__(self, other: typing.Any) -> bool:
        ...
    def __getstate__(self) -> int:
        ...
    def __hash__(self) -> int:
        ...
    def __index__(self) -> int:
        ...
    @typing.overload
    def __init__(self, value: typing.SupportsInt) -> None:
        ...
    @typing.overload
    def __init__(self, name: str) -> None:
        ...
    def __int__(self) -> int:
        ...
    def __ne__(self, other: typing.Any) -> bool:
        ...
    def __setstate__(self, state: typing.SupportsInt) -> None:
        ...
    def __str__(self) -> str:
        ...
    @property
    def name(self) -> str:
        ...
    @property
    def value(self) -> int:
        ...
class ImportedPairGenerator(PairGenerator):
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __init__(self, options: ImportedPairingOptions, database: Database) -> None:
        ...
class ImportedPairingOptions:
    __hash__: typing.ClassVar[None] = None
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __copy__(self) -> ImportedPairingOptions:
        ...
    def __deepcopy__(self, arg0: dict) -> ImportedPairingOptions:
        ...
    def __eq__(self, arg0: typing.Any) -> bool:
        ...
    def __getstate__(self) -> dict:
        ...
    @typing.overload
    def __init__(self) -> None:
        ...
    @typing.overload
    def __init__(self, arg0: dict) -> None:
        ...
    @typing.overload
    def __init__(self, **kwargs) -> None:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, arg0: dict) -> None:
        ...
    def check(self) -> bool:
        ...
    def mergedict(self, kwargs: dict) -> None:
        ...
    def summary(self, write_type: bool = False) -> str:
        ...
    def todict(self, recursive: bool = True) -> dict:
        ...
    @property
    def block_size(self) -> int:
        """
        Number of image pairs to match in one batch. (int, default: 1225)
        """
    @block_size.setter
    def block_size(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def match_list_path(self) -> str:
        """
        Path to the file with the matches. (str, default: )
        """
    @match_list_path.setter
    def match_list_path(self, arg0: str) -> None:
        ...
class IncrementalMapper:
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __init__(self, database_cache: DatabaseCache) -> None:
        ...
    def adjust_global_bundle(self, options: IncrementalMapperOptions, ba_options: BundleAdjustmentOptions) -> bool:
        ...
    def adjust_local_bundle(self, options: IncrementalMapperOptions, ba_options: BundleAdjustmentOptions, tri_options: IncrementalTriangulatorOptions, image_id: typing.SupportsInt, point3D_ids: collections.abc.Set[typing.SupportsInt]) -> LocalBundleAdjustmentReport:
        ...
    def begin_reconstruction(self, reconstruction: Reconstruction) -> None:
        ...
    def clear_modified_points3D(self) -> None:
        ...
    def complete_and_merge_tracks(self, tri_options: IncrementalTriangulatorOptions) -> int:
        ...
    def complete_tracks(self, tri_options: IncrementalTriangulatorOptions) -> int:
        ...
    def end_reconstruction(self, discard: bool) -> None:
        ...
    def estimate_initial_two_view_geometry(self, options: IncrementalMapperOptions, image_id1: typing.SupportsInt, image_id2: typing.SupportsInt) -> pycolmap._core.Rigid3d | None:
        ...
    def filter_frames(self, options: IncrementalMapperOptions) -> int:
        ...
    def filter_points(self, options: IncrementalMapperOptions) -> int:
        ...
    def find_initial_image_pair(self, options: IncrementalMapperOptions, image_id1: typing.SupportsInt, image_id2: typing.SupportsInt) -> tuple[tuple[int, int], Rigid3d] | None:
        ...
    def find_local_bundle(self, options: IncrementalMapperOptions, image_id: typing.SupportsInt) -> list[int]:
        ...
    def find_next_images(self, options: IncrementalMapperOptions) -> list[int]:
        ...
    def get_modified_points3D(self) -> set[int]:
        ...
    def iterative_global_refinement(self, max_num_refinements: typing.SupportsInt, max_refinement_change: typing.SupportsFloat, options: IncrementalMapperOptions, ba_options: BundleAdjustmentOptions, tri_options: IncrementalTriangulatorOptions, normalize_reconstruction: bool = True) -> None:
        ...
    def iterative_local_refinement(self, max_num_refinements: typing.SupportsInt, max_refinement_change: typing.SupportsFloat, options: IncrementalMapperOptions, ba_options: BundleAdjustmentOptions, tri_options: IncrementalTriangulatorOptions, image_id: typing.SupportsInt) -> None:
        ...
    def merge_tracks(self, tri_options: IncrementalTriangulatorOptions) -> int:
        ...
    def num_shared_reg_images(self) -> int:
        ...
    def num_total_reg_images(self) -> int:
        ...
    def register_initial_image_pair(self, options: IncrementalMapperOptions, two_view_geometry: typing.SupportsInt, image_id1: typing.SupportsInt, image_id2: Rigid3d) -> None:
        ...
    def register_next_image(self, options: IncrementalMapperOptions, image_id: typing.SupportsInt) -> bool:
        ...
    def reset_initialization_stats(self) -> None:
        ...
    def retriangulate(self, tri_options: IncrementalTriangulatorOptions) -> int:
        ...
    def triangulate_image(self, tri_options: IncrementalTriangulatorOptions, image_id: typing.SupportsInt) -> int:
        ...
    @property
    def existing_frame_ids(self) -> set[int]:
        ...
    @property
    def filtered_frames(self) -> set[int]:
        ...
    @property
    def num_reg_frames_per_rig(self) -> dict[int, int]:
        ...
    @property
    def num_reg_images_per_camera(self) -> dict[int, int]:
        ...
    @property
    def observation_manager(self) -> ObservationManager:
        ...
    @property
    def reconstruction(self) -> Reconstruction:
        ...
    @property
    def triangulator(self) -> IncrementalTriangulator:
        ...
class IncrementalMapperCallback:
    """
    Members:
    
      INITIAL_IMAGE_PAIR_REG_CALLBACK
    
      NEXT_IMAGE_REG_CALLBACK
    
      LAST_IMAGE_REG_CALLBACK
    """
    INITIAL_IMAGE_PAIR_REG_CALLBACK: typing.ClassVar[IncrementalMapperCallback]  # value = IncrementalMapperCallback.INITIAL_IMAGE_PAIR_REG_CALLBACK
    LAST_IMAGE_REG_CALLBACK: typing.ClassVar[IncrementalMapperCallback]  # value = IncrementalMapperCallback.LAST_IMAGE_REG_CALLBACK
    NEXT_IMAGE_REG_CALLBACK: typing.ClassVar[IncrementalMapperCallback]  # value = IncrementalMapperCallback.NEXT_IMAGE_REG_CALLBACK
    __members__: typing.ClassVar[dict[str, IncrementalMapperCallback]]  # value = {'INITIAL_IMAGE_PAIR_REG_CALLBACK': IncrementalMapperCallback.INITIAL_IMAGE_PAIR_REG_CALLBACK, 'NEXT_IMAGE_REG_CALLBACK': IncrementalMapperCallback.NEXT_IMAGE_REG_CALLBACK, 'LAST_IMAGE_REG_CALLBACK': IncrementalMapperCallback.LAST_IMAGE_REG_CALLBACK}
    @staticmethod
    def __repr__(*args, **kwargs):
        """
        __str__(self: object, /) -> str
        """
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __eq__(self, other: typing.Any) -> bool:
        ...
    def __getstate__(self) -> int:
        ...
    def __hash__(self) -> int:
        ...
    def __index__(self) -> int:
        ...
    @typing.overload
    def __init__(self, value: typing.SupportsInt) -> None:
        ...
    @typing.overload
    def __init__(self, name: str) -> None:
        ...
    def __int__(self) -> int:
        ...
    def __ne__(self, other: typing.Any) -> bool:
        ...
    def __setstate__(self, state: typing.SupportsInt) -> None:
        ...
    def __str__(self) -> str:
        ...
    @property
    def name(self) -> str:
        ...
    @property
    def value(self) -> int:
        ...
class IncrementalMapperOptions:
    __hash__: typing.ClassVar[None] = None
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __copy__(self) -> IncrementalMapperOptions:
        ...
    def __deepcopy__(self, arg0: dict) -> IncrementalMapperOptions:
        ...
    def __eq__(self, arg0: typing.Any) -> bool:
        ...
    def __getstate__(self) -> dict:
        ...
    @typing.overload
    def __init__(self) -> None:
        ...
    @typing.overload
    def __init__(self, arg0: dict) -> None:
        ...
    @typing.overload
    def __init__(self, **kwargs) -> None:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, arg0: dict) -> None:
        ...
    def check(self) -> bool:
        ...
    def mergedict(self, kwargs: dict) -> None:
        ...
    def summary(self, write_type: bool = False) -> str:
        ...
    def todict(self, recursive: bool = True) -> dict:
        ...
    @property
    def abs_pose_max_error(self) -> float:
        """
        Maximum reprojection error in absolute pose estimation. (float, default: 12.0)
        """
    @abs_pose_max_error.setter
    def abs_pose_max_error(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def abs_pose_min_inlier_ratio(self) -> float:
        """
        Minimum inlier ratio in absolute pose estimation. (float, default: 0.25)
        """
    @abs_pose_min_inlier_ratio.setter
    def abs_pose_min_inlier_ratio(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def abs_pose_min_num_inliers(self) -> int:
        """
        Minimum number of inliers in absolute pose estimation. (int, default: 30)
        """
    @abs_pose_min_num_inliers.setter
    def abs_pose_min_num_inliers(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def abs_pose_refine_extra_params(self) -> bool:
        """
        Whether to estimate the extra parameters in absolute pose estimation. (bool, default: True)
        """
    @abs_pose_refine_extra_params.setter
    def abs_pose_refine_extra_params(self, arg0: bool) -> None:
        ...
    @property
    def abs_pose_refine_focal_length(self) -> bool:
        """
        Whether to estimate the focal length in absolute pose estimation. (bool, default: True)
        """
    @abs_pose_refine_focal_length.setter
    def abs_pose_refine_focal_length(self, arg0: bool) -> None:
        ...
    @property
    def ba_global_ignore_redundant_points3D(self) -> bool:
        """
        Whether to ignore redundant 3D points in bundle adjustment when jointly optimizing all parameters. If this is enabled, then the bundle adjustment problem is first solved with a reduced set of 3D points and then the remaining 3D points are optimized in a second step with all other parameters fixed. Points excplicitly configured as constant or variable are not ignored. This is only activated when the reconstruction has reached sufficient size with at least 10 registered frames. (bool, default: False)
        """
    @ba_global_ignore_redundant_points3D.setter
    def ba_global_ignore_redundant_points3D(self, arg0: bool) -> None:
        ...
    @property
    def ba_global_prune_points_min_coverage_gain(self) -> float:
        """
        The minimum coverage gain for any 3D point to be included in the optimization. A larger value means more 3D points are ignored. (float, default: 0.05)
        """
    @ba_global_prune_points_min_coverage_gain.setter
    def ba_global_prune_points_min_coverage_gain(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def ba_local_min_tri_angle(self) -> float:
        """
        Minimum triangulation for images to be chosen in local bundle adjustment. (float, default: 6.0)
        """
    @ba_local_min_tri_angle.setter
    def ba_local_min_tri_angle(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def ba_local_num_images(self) -> int:
        """
        Number of images to optimize in local bundle adjustment. (int, default: 6)
        """
    @ba_local_num_images.setter
    def ba_local_num_images(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def constant_cameras(self) -> set[int]:
        """
        List of cameras for which to fix the camera parameters independent of refine_focal_length, refine_principal_point, and refine_extra_params. (set, default: set())
        """
    @constant_cameras.setter
    def constant_cameras(self, arg0: collections.abc.Set[typing.SupportsInt]) -> None:
        ...
    @property
    def constant_rigs(self) -> set[int]:
        """
        List of rigs for which to fix the sensor_from_rig transformation, independent of ba_refine_sensor_from_rig. (set, default: set())
        """
    @constant_rigs.setter
    def constant_rigs(self, arg0: collections.abc.Set[typing.SupportsInt]) -> None:
        ...
    @property
    def filter_max_reproj_error(self) -> float:
        """
        Maximum reprojection error in pixels for observations. (float, default: 4.0)
        """
    @filter_max_reproj_error.setter
    def filter_max_reproj_error(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def filter_min_tri_angle(self) -> float:
        """
        Minimum triangulation angle in degrees for stable 3D points. (float, default: 1.5)
        """
    @filter_min_tri_angle.setter
    def filter_min_tri_angle(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def fix_existing_frames(self) -> bool:
        """
        If reconstruction is provided as input, fix the existing frame poses. (bool, default: False)
        """
    @fix_existing_frames.setter
    def fix_existing_frames(self, arg0: bool) -> None:
        ...
    @property
    def image_selection_method(self) -> ImageSelectionMethod:
        """
        Method to find and select next best image to register. (ImageSelectionMethod, default: ImageSelectionMethod.MIN_UNCERTAINTY)
        """
    @image_selection_method.setter
    def image_selection_method(self, arg0: ImageSelectionMethod) -> None:
        ...
    @property
    def init_max_error(self) -> float:
        """
        Maximum error in pixels for two-view geometry estimation for initial image pair. (float, default: 4.0)
        """
    @init_max_error.setter
    def init_max_error(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def init_max_forward_motion(self) -> float:
        """
        Maximum forward motion for initial image pair. (float, default: 0.95)
        """
    @init_max_forward_motion.setter
    def init_max_forward_motion(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def init_max_reg_trials(self) -> int:
        """
        Maximum number of trials to use an image for initialization. (int, default: 2)
        """
    @init_max_reg_trials.setter
    def init_max_reg_trials(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def init_min_num_inliers(self) -> int:
        """
        Minimum number of inliers for initial image pair. (int, default: 100)
        """
    @init_min_num_inliers.setter
    def init_min_num_inliers(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def init_min_tri_angle(self) -> float:
        """
        Minimum triangulation angle for initial image pair. (float, default: 16.0)
        """
    @init_min_tri_angle.setter
    def init_min_tri_angle(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def max_extra_param(self) -> float:
        """
        The threshold used to filter and ignore images with degenerate intrinsics. (float, default: 1.0)
        """
    @max_extra_param.setter
    def max_extra_param(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def max_focal_length_ratio(self) -> float:
        """
        The threshold used to filter and ignore images with degenerate intrinsics. (float, default: 10.0)
        """
    @max_focal_length_ratio.setter
    def max_focal_length_ratio(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def max_reg_trials(self) -> int:
        """
        Maximum number of trials to register an image. (int, default: 3)
        """
    @max_reg_trials.setter
    def max_reg_trials(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def min_focal_length_ratio(self) -> float:
        """
        The threshold used to filter and ignore images with degenerate intrinsics. (float, default: 0.1)
        """
    @min_focal_length_ratio.setter
    def min_focal_length_ratio(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def num_threads(self) -> int:
        """
        Number of threads. (int, default: -1)
        """
    @num_threads.setter
    def num_threads(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def random_seed(self) -> int:
        """
        PRNG seed for all stochastic methods during reconstruction. (int, default: -1)
        """
    @random_seed.setter
    def random_seed(self, arg0: typing.SupportsInt) -> None:
        ...
class IncrementalMapperStatus:
    """
    Members:
    
      NO_INITIAL_PAIR
    
      BAD_INITIAL_PAIR
    
      SUCCESS
    
      INTERRUPTED
    """
    BAD_INITIAL_PAIR: typing.ClassVar[IncrementalMapperStatus]  # value = IncrementalMapperStatus.BAD_INITIAL_PAIR
    INTERRUPTED: typing.ClassVar[IncrementalMapperStatus]  # value = IncrementalMapperStatus.INTERRUPTED
    NO_INITIAL_PAIR: typing.ClassVar[IncrementalMapperStatus]  # value = IncrementalMapperStatus.NO_INITIAL_PAIR
    SUCCESS: typing.ClassVar[IncrementalMapperStatus]  # value = IncrementalMapperStatus.SUCCESS
    __members__: typing.ClassVar[dict[str, IncrementalMapperStatus]]  # value = {'NO_INITIAL_PAIR': IncrementalMapperStatus.NO_INITIAL_PAIR, 'BAD_INITIAL_PAIR': IncrementalMapperStatus.BAD_INITIAL_PAIR, 'SUCCESS': IncrementalMapperStatus.SUCCESS, 'INTERRUPTED': IncrementalMapperStatus.INTERRUPTED}
    @staticmethod
    def __repr__(*args, **kwargs):
        """
        __str__(self: object, /) -> str
        """
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __eq__(self, other: typing.Any) -> bool:
        ...
    def __getstate__(self) -> int:
        ...
    def __hash__(self) -> int:
        ...
    def __index__(self) -> int:
        ...
    @typing.overload
    def __init__(self, value: typing.SupportsInt) -> None:
        ...
    @typing.overload
    def __init__(self, name: str) -> None:
        ...
    def __int__(self) -> int:
        ...
    def __ne__(self, other: typing.Any) -> bool:
        ...
    def __setstate__(self, state: typing.SupportsInt) -> None:
        ...
    def __str__(self) -> str:
        ...
    @property
    def name(self) -> str:
        ...
    @property
    def value(self) -> int:
        ...
class IncrementalPipeline:
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __init__(self, options: IncrementalPipelineOptions, image_path: str, database_path: str, reconstruction_manager: ReconstructionManager) -> None:
        ...
    def add_callback(self, id: typing.SupportsInt, func: collections.abc.Callable[[], None]) -> None:
        ...
    def callback(self, id: typing.SupportsInt) -> None:
        ...
    def check_run_global_refinement(self, reconstruction: Reconstruction, ba_prev_num_reg_images: typing.SupportsInt, ba_prev_num_points: typing.SupportsInt) -> bool:
        ...
    def initialize_reconstruction(self, mapper: IncrementalMapper, mapper_options: IncrementalMapperOptions, reconstruction: Reconstruction) -> IncrementalMapperStatus:
        ...
    def load_database(self) -> bool:
        ...
    def reconstruct(self, mapper: IncrementalMapper, mapper_options: IncrementalMapperOptions, continue_reconstruction: bool) -> None:
        ...
    def reconstruct_sub_model(self, mapper: IncrementalMapper, mapper_options: IncrementalMapperOptions, reconstruction: Reconstruction) -> IncrementalMapperStatus:
        ...
    def run(self) -> None:
        ...
    @property
    def database_cache(self) -> DatabaseCache:
        ...
    @property
    def database_path(self) -> str:
        ...
    @property
    def image_path(self) -> str:
        ...
    @property
    def options(self) -> IncrementalPipelineOptions:
        ...
    @property
    def reconstruction_manager(self) -> ReconstructionManager:
        ...
class IncrementalPipelineOptions:
    __hash__: typing.ClassVar[None] = None
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __copy__(self) -> IncrementalPipelineOptions:
        ...
    def __deepcopy__(self, arg0: dict) -> IncrementalPipelineOptions:
        ...
    def __eq__(self, arg0: typing.Any) -> bool:
        ...
    def __getstate__(self) -> dict:
        ...
    @typing.overload
    def __init__(self) -> None:
        ...
    @typing.overload
    def __init__(self, arg0: dict) -> None:
        ...
    @typing.overload
    def __init__(self, **kwargs) -> None:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, arg0: dict) -> None:
        ...
    def check(self) -> bool:
        ...
    def get_global_bundle_adjustment(self) -> BundleAdjustmentOptions:
        ...
    def get_local_bundle_adjustment(self) -> BundleAdjustmentOptions:
        ...
    def get_mapper(self) -> IncrementalMapperOptions:
        ...
    def get_triangulation(self) -> IncrementalTriangulatorOptions:
        ...
    def is_initial_pair_provided(self) -> bool:
        ...
    def mergedict(self, kwargs: dict) -> None:
        ...
    def summary(self, write_type: bool = False) -> str:
        ...
    def todict(self, recursive: bool = True) -> dict:
        ...
    @property
    def ba_global_frames_freq(self) -> int:
        """
        The growth rates after which to perform global bundle adjustment. (int, default: 500)
        """
    @ba_global_frames_freq.setter
    def ba_global_frames_freq(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def ba_global_frames_ratio(self) -> float:
        """
        The growth rates after which to perform global bundle adjustment. (float, default: 1.1)
        """
    @ba_global_frames_ratio.setter
    def ba_global_frames_ratio(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def ba_global_function_tolerance(self) -> float:
        """
        Ceres solver function tolerance for global bundle adjustment. (float, default: 0.0)
        """
    @ba_global_function_tolerance.setter
    def ba_global_function_tolerance(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def ba_global_max_num_iterations(self) -> int:
        """
        The maximum number of global bundle adjustment iterations. (int, default: 50)
        """
    @ba_global_max_num_iterations.setter
    def ba_global_max_num_iterations(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def ba_global_max_refinement_change(self) -> float:
        """
        The thresholds for iterative bundle adjustment refinements. (float, default: 0.0005)
        """
    @ba_global_max_refinement_change.setter
    def ba_global_max_refinement_change(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def ba_global_max_refinements(self) -> int:
        """
        The thresholds for iterative bundle adjustment refinements. (int, default: 5)
        """
    @ba_global_max_refinements.setter
    def ba_global_max_refinements(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def ba_global_points_freq(self) -> int:
        """
        The growth rates after which to perform global bundle adjustment. (int, default: 250000)
        """
    @ba_global_points_freq.setter
    def ba_global_points_freq(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def ba_global_points_ratio(self) -> float:
        """
        The growth rates after which to perform global bundle adjustment. (float, default: 1.1)
        """
    @ba_global_points_ratio.setter
    def ba_global_points_ratio(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def ba_gpu_index(self) -> str:
        """
        Index of CUDA GPU to use for BA, if available. (str, default: -1)
        """
    @ba_gpu_index.setter
    def ba_gpu_index(self, arg0: str) -> None:
        ...
    @property
    def ba_local_function_tolerance(self) -> float:
        """
        Ceres solver function tolerance for local bundle adjustment. (float, default: 0.0)
        """
    @ba_local_function_tolerance.setter
    def ba_local_function_tolerance(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def ba_local_max_num_iterations(self) -> int:
        """
        The maximum number of local bundle adjustment iterations. (int, default: 25)
        """
    @ba_local_max_num_iterations.setter
    def ba_local_max_num_iterations(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def ba_local_max_refinement_change(self) -> float:
        """
        The thresholds for iterative bundle adjustment refinements. (float, default: 0.001)
        """
    @ba_local_max_refinement_change.setter
    def ba_local_max_refinement_change(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def ba_local_max_refinements(self) -> int:
        """
        The thresholds for iterative bundle adjustment refinements. (int, default: 2)
        """
    @ba_local_max_refinements.setter
    def ba_local_max_refinements(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def ba_min_num_residuals_for_cpu_multi_threading(self) -> int:
        """
        The minimum number of residuals per bundle adjustment problem to enable multi-threading solving of the problems. (int, default: 50000)
        """
    @ba_min_num_residuals_for_cpu_multi_threading.setter
    def ba_min_num_residuals_for_cpu_multi_threading(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def ba_refine_extra_params(self) -> bool:
        """
        Whether to refine extra parameters during the reconstruction. (bool, default: True)
        """
    @ba_refine_extra_params.setter
    def ba_refine_extra_params(self, arg0: bool) -> None:
        ...
    @property
    def ba_refine_focal_length(self) -> bool:
        """
        Whether to refine the focal length during the reconstruction. (bool, default: True)
        """
    @ba_refine_focal_length.setter
    def ba_refine_focal_length(self, arg0: bool) -> None:
        ...
    @property
    def ba_refine_principal_point(self) -> bool:
        """
        Whether to refine the principal point during the reconstruction. (bool, default: False)
        """
    @ba_refine_principal_point.setter
    def ba_refine_principal_point(self, arg0: bool) -> None:
        ...
    @property
    def ba_refine_sensor_from_rig(self) -> bool:
        """
        Whether to refine rig poses during the reconstruction. (bool, default: True)
        """
    @ba_refine_sensor_from_rig.setter
    def ba_refine_sensor_from_rig(self, arg0: bool) -> None:
        ...
    @property
    def ba_use_gpu(self) -> bool:
        """
        Whether to use Ceres' CUDA sparse linear algebra library, if available. (bool, default: False)
        """
    @ba_use_gpu.setter
    def ba_use_gpu(self, arg0: bool) -> None:
        ...
    @property
    def constant_cameras(self) -> set[int]:
        """
        List of cameras for which to fix the camera parameters independent of refine_focal_length, refine_principal_point, and refine_extra_params. (set, default: set())
        """
    @constant_cameras.setter
    def constant_cameras(self, arg0: collections.abc.Set[typing.SupportsInt]) -> None:
        ...
    @property
    def constant_rigs(self) -> set[int]:
        """
        List of rigs for which to fix the sensor_from_rig transformation, independent of ba_refine_sensor_from_rig. (set, default: set())
        """
    @constant_rigs.setter
    def constant_rigs(self, arg0: collections.abc.Set[typing.SupportsInt]) -> None:
        ...
    @property
    def extract_colors(self) -> bool:
        """
        Whether to extract colors for reconstructed points. (bool, default: True)
        """
    @extract_colors.setter
    def extract_colors(self, arg0: bool) -> None:
        ...
    @property
    def fix_existing_frames(self) -> bool:
        """
        If reconstruction is provided as input, fix the existing frame poses. (bool, default: False)
        """
    @fix_existing_frames.setter
    def fix_existing_frames(self, arg0: bool) -> None:
        ...
    @property
    def ignore_watermarks(self) -> bool:
        """
        Whether to ignore the inlier matches of watermark image pairs. (bool, default: False)
        """
    @ignore_watermarks.setter
    def ignore_watermarks(self, arg0: bool) -> None:
        ...
    @property
    def image_names(self) -> list[str]:
        """
        Optional list of image names to reconstruct. If no images are specified, all images will be reconstructed by default. (list, default: [])
        """
    @image_names.setter
    def image_names(self, arg0: collections.abc.Sequence[str]) -> None:
        ...
    @property
    def init_image_id1(self) -> int:
        """
        The image identifier of the first image used to initialize the reconstruction. (int, default: -1)
        """
    @init_image_id1.setter
    def init_image_id1(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def init_image_id2(self) -> int:
        """
        The image identifier of the second image used to initialize the reconstruction. Determined automatically if left unspecified. (int, default: -1)
        """
    @init_image_id2.setter
    def init_image_id2(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def init_num_trials(self) -> int:
        """
        The number of trials to initialize the reconstruction. (int, default: 200)
        """
    @init_num_trials.setter
    def init_num_trials(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def mapper(self) -> IncrementalMapperOptions:
        """
        Options of the IncrementalMapper. (IncrementalMapperOptions, default: IncrementalMapperOptions(init_min_num_inliers=100, init_max_error=4.0, init_max_forward_motion=0.95, init_min_tri_angle=16.0, init_max_reg_trials=2, abs_pose_max_error=12.0, abs_pose_min_num_inliers=30, abs_pose_min_inlier_ratio=0.25, abs_pose_refine_focal_length=True, abs_pose_refine_extra_params=True, ba_local_num_images=6, ba_local_min_tri_angle=6.0, ba_global_ignore_redundant_points3D=False, ba_global_prune_points_min_coverage_gain=0.05, min_focal_length_ratio=0.1, max_focal_length_ratio=10.0, max_extra_param=1.0, filter_max_reproj_error=4.0, filter_min_tri_angle=1.5, max_reg_trials=3, fix_existing_frames=False, constant_rigs=set(), constant_cameras=set(), num_threads=-1, random_seed=-1, image_selection_method=ImageSelectionMethod.MIN_UNCERTAINTY))
        """
    @mapper.setter
    def mapper(self, arg0: IncrementalMapperOptions) -> None:
        ...
    @property
    def max_extra_param(self) -> float:
        """
        The threshold used to filter and ignore images with degenerate intrinsics. (float, default: 1.0)
        """
    @max_extra_param.setter
    def max_extra_param(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def max_focal_length_ratio(self) -> float:
        """
        The threshold used to filter and ignore images with degenerate intrinsics. (float, default: 10.0)
        """
    @max_focal_length_ratio.setter
    def max_focal_length_ratio(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def max_model_overlap(self) -> int:
        """
        The maximum number of overlapping images between sub-models. If the current sub-models shares more than this number of images with another model, then the reconstruction is stopped. (int, default: 20)
        """
    @max_model_overlap.setter
    def max_model_overlap(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def max_num_models(self) -> int:
        """
        The number of sub-models to reconstruct. (int, default: 50)
        """
    @max_num_models.setter
    def max_num_models(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def max_runtime_seconds(self) -> int:
        """
        Maximum runtime in seconds for the reconstruction process. If set to a non-positive value, the process will run until completion. (int, default: -1)
        """
    @max_runtime_seconds.setter
    def max_runtime_seconds(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def min_focal_length_ratio(self) -> float:
        """
        The threshold used to filter and ignore images with degenerate intrinsics. (float, default: 0.1)
        """
    @min_focal_length_ratio.setter
    def min_focal_length_ratio(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def min_model_size(self) -> int:
        """
        The minimum number of registered images of a sub-model, otherwise the sub-model is discarded. Note that the first sub-model is always kept independent of size. (int, default: 10)
        """
    @min_model_size.setter
    def min_model_size(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def min_num_matches(self) -> int:
        """
        The minimum number of matches for inlier matches to be considered. (int, default: 15)
        """
    @min_num_matches.setter
    def min_num_matches(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def multiple_models(self) -> bool:
        """
        Whether to reconstruct multiple sub-models. (bool, default: True)
        """
    @multiple_models.setter
    def multiple_models(self, arg0: bool) -> None:
        ...
    @property
    def num_threads(self) -> int:
        """
        The number of threads to use during reconstruction. (int, default: -1)
        """
    @num_threads.setter
    def num_threads(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def prior_position_loss_scale(self) -> float:
        """
        Threshold on the residual for the robust position prior loss (chi2 for 3DOF at 95% = 7.815). (float, default: 7.815)
        """
    @prior_position_loss_scale.setter
    def prior_position_loss_scale(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def random_seed(self) -> int:
        """
        PRNG seed for all stochastic methods during reconstruction. (int, default: -1)
        """
    @random_seed.setter
    def random_seed(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def snapshot_frames_freq(self) -> int:
        """
        Frequency of registered images according to which reconstruction snapshots will be saved. (int, default: 0)
        """
    @snapshot_frames_freq.setter
    def snapshot_frames_freq(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def snapshot_path(self) -> str:
        """
        Path to a folder in which reconstruction snapshots will be saved during incremental reconstruction. (str, default: )
        """
    @snapshot_path.setter
    def snapshot_path(self, arg0: str) -> None:
        ...
    @property
    def triangulation(self) -> IncrementalTriangulatorOptions:
        """
        Options of the IncrementalTriangulator. (IncrementalTriangulatorOptions, default: IncrementalTriangulatorOptions(max_transitivity=1, create_max_angle_error=2.0, continue_max_angle_error=2.0, merge_max_reproj_error=4.0, complete_max_reproj_error=4.0, complete_max_transitivity=5, re_max_angle_error=5.0, re_min_ratio=0.2, re_max_trials=1, min_angle=1.5, ignore_two_view_tracks=True, min_focal_length_ratio=0.1, max_focal_length_ratio=10.0, max_extra_param=1.0, random_seed=-1))
        """
    @triangulation.setter
    def triangulation(self, arg0: IncrementalTriangulatorOptions) -> None:
        ...
    @property
    def use_prior_position(self) -> bool:
        """
        Whether to use priors on the camera positions. (bool, default: False)
        """
    @use_prior_position.setter
    def use_prior_position(self, arg0: bool) -> None:
        ...
    @property
    def use_robust_loss_on_prior_position(self) -> bool:
        """
        Whether to use a robust loss on prior camera positions. (bool, default: False)
        """
    @use_robust_loss_on_prior_position.setter
    def use_robust_loss_on_prior_position(self, arg0: bool) -> None:
        ...
class IncrementalTriangulator:
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __copy__(self) -> IncrementalTriangulator:
        ...
    def __deepcopy__(self, arg0: dict) -> IncrementalTriangulator:
        ...
    def __init__(self, correspondence_graph: CorrespondenceGraph, reconstruction: Reconstruction, observation_manager: ObservationManager = None) -> None:
        ...
    def __repr__(self) -> str:
        ...
    def add_modified_point3D(self, point3D_id: typing.SupportsInt) -> None:
        ...
    def clear_modified_points3D(self) -> None:
        ...
    def complete_all_tracks(self, options: IncrementalTriangulatorOptions) -> int:
        ...
    def complete_image(self, options: IncrementalTriangulatorOptions, image_id: typing.SupportsInt) -> int:
        ...
    def complete_tracks(self, options: IncrementalTriangulatorOptions, point3D_ids: collections.abc.Set[typing.SupportsInt]) -> int:
        ...
    def merge_all_tracks(self, options: IncrementalTriangulatorOptions) -> int:
        ...
    def merge_tracks(self, options: IncrementalTriangulatorOptions, point3D_ids: collections.abc.Set[typing.SupportsInt]) -> int:
        ...
    def retriangulate(self, options: IncrementalTriangulatorOptions) -> int:
        ...
    def triangulate_image(self, options: IncrementalTriangulatorOptions, image_id: typing.SupportsInt) -> int:
        ...
class IncrementalTriangulatorOptions:
    __hash__: typing.ClassVar[None] = None
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __copy__(self) -> IncrementalTriangulatorOptions:
        ...
    def __deepcopy__(self, arg0: dict) -> IncrementalTriangulatorOptions:
        ...
    def __eq__(self, arg0: typing.Any) -> bool:
        ...
    def __getstate__(self) -> dict:
        ...
    @typing.overload
    def __init__(self) -> None:
        ...
    @typing.overload
    def __init__(self, arg0: dict) -> None:
        ...
    @typing.overload
    def __init__(self, **kwargs) -> None:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, arg0: dict) -> None:
        ...
    def check(self) -> bool:
        ...
    def mergedict(self, kwargs: dict) -> None:
        ...
    def summary(self, write_type: bool = False) -> str:
        ...
    def todict(self, recursive: bool = True) -> dict:
        ...
    @property
    def complete_max_reproj_error(self) -> float:
        """
        Maximum reprojection error to complete an existing triangulation. (float, default: 4.0)
        """
    @complete_max_reproj_error.setter
    def complete_max_reproj_error(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def complete_max_transitivity(self) -> int:
        """
        Maximum transitivity for track completion. (int, default: 5)
        """
    @complete_max_transitivity.setter
    def complete_max_transitivity(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def continue_max_angle_error(self) -> float:
        """
        Maximum angular error to continue existing triangulations. (float, default: 2.0)
        """
    @continue_max_angle_error.setter
    def continue_max_angle_error(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def create_max_angle_error(self) -> float:
        """
        Maximum angular error to create new triangulations. (float, default: 2.0)
        """
    @create_max_angle_error.setter
    def create_max_angle_error(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def ignore_two_view_tracks(self) -> bool:
        """
        Whether to ignore two-view tracks. (bool, default: True)
        """
    @ignore_two_view_tracks.setter
    def ignore_two_view_tracks(self, arg0: bool) -> None:
        ...
    @property
    def max_extra_param(self) -> float:
        """
        The threshold used to filter and ignore images with degenerate intrinsics. (float, default: 1.0)
        """
    @max_extra_param.setter
    def max_extra_param(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def max_focal_length_ratio(self) -> float:
        """
        The threshold used to filter and ignore images with degenerate intrinsics. (float, default: 10.0)
        """
    @max_focal_length_ratio.setter
    def max_focal_length_ratio(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def max_transitivity(self) -> int:
        """
        Maximum transitivity to search for correspondences. (int, default: 1)
        """
    @max_transitivity.setter
    def max_transitivity(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def merge_max_reproj_error(self) -> float:
        """
        Maximum reprojection error in pixels to merge triangulations. (float, default: 4.0)
        """
    @merge_max_reproj_error.setter
    def merge_max_reproj_error(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def min_angle(self) -> float:
        """
        Minimum pairwise triangulation angle for a stable triangulation. (float, default: 1.5)
        """
    @min_angle.setter
    def min_angle(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def min_focal_length_ratio(self) -> float:
        """
        The threshold used to filter and ignore images with degenerate intrinsics. (float, default: 0.1)
        """
    @min_focal_length_ratio.setter
    def min_focal_length_ratio(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def random_seed(self) -> int:
        """
        PRNG seed for all stochastic methods during triangulation. (int, default: -1)
        """
    @random_seed.setter
    def random_seed(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def re_max_angle_error(self) -> float:
        """
        Maximum angular error to re-triangulate under-reconstructed image pairs. (float, default: 5.0)
        """
    @re_max_angle_error.setter
    def re_max_angle_error(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def re_max_trials(self) -> int:
        """
        Maximum number of trials to re-triangulate an image pair. (int, default: 1)
        """
    @re_max_trials.setter
    def re_max_trials(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def re_min_ratio(self) -> float:
        """
        Minimum ratio of common triangulations between an image pair over the number of correspondences between that image pair to be considered as under-reconstructed. (float, default: 0.2)
        """
    @re_min_ratio.setter
    def re_min_ratio(self, arg0: typing.SupportsFloat) -> None:
        ...
class LocalBundleAdjustmentReport:
    __hash__: typing.ClassVar[None] = None
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __copy__(self) -> LocalBundleAdjustmentReport:
        ...
    def __deepcopy__(self, arg0: dict) -> LocalBundleAdjustmentReport:
        ...
    def __eq__(self, arg0: typing.Any) -> bool:
        ...
    def __getstate__(self) -> dict:
        ...
    @typing.overload
    def __init__(self) -> None:
        ...
    @typing.overload
    def __init__(self, arg0: dict) -> None:
        ...
    @typing.overload
    def __init__(self, **kwargs) -> None:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, arg0: dict) -> None:
        ...
    def mergedict(self, kwargs: dict) -> None:
        ...
    def summary(self, write_type: bool = False) -> str:
        ...
    def todict(self, recursive: bool = True) -> dict:
        ...
    @property
    def num_adjusted_observations(self) -> int:
        """
         (int, default: 0)
        """
    @num_adjusted_observations.setter
    def num_adjusted_observations(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def num_completed_observations(self) -> int:
        """
         (int, default: 0)
        """
    @num_completed_observations.setter
    def num_completed_observations(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def num_filtered_observations(self) -> int:
        """
         (int, default: 0)
        """
    @num_filtered_observations.setter
    def num_filtered_observations(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def num_merged_observations(self) -> int:
        """
         (int, default: 0)
        """
    @num_merged_observations.setter
    def num_merged_observations(self, arg0: typing.SupportsInt) -> None:
        ...
class LossFunctionType:
    """
    Members:
    
      TRIVIAL
    
      SOFT_L1
    
      CAUCHY
    """
    CAUCHY: typing.ClassVar[LossFunctionType]  # value = LossFunctionType.CAUCHY
    SOFT_L1: typing.ClassVar[LossFunctionType]  # value = LossFunctionType.SOFT_L1
    TRIVIAL: typing.ClassVar[LossFunctionType]  # value = LossFunctionType.TRIVIAL
    __members__: typing.ClassVar[dict[str, LossFunctionType]]  # value = {'TRIVIAL': LossFunctionType.TRIVIAL, 'SOFT_L1': LossFunctionType.SOFT_L1, 'CAUCHY': LossFunctionType.CAUCHY}
    @staticmethod
    def __repr__(*args, **kwargs):
        """
        __str__(self: object, /) -> str
        """
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __eq__(self, other: typing.Any) -> bool:
        ...
    def __getstate__(self) -> int:
        ...
    def __hash__(self) -> int:
        ...
    def __index__(self) -> int:
        ...
    @typing.overload
    def __init__(self, value: typing.SupportsInt) -> None:
        ...
    @typing.overload
    def __init__(self, name: str) -> None:
        ...
    def __int__(self) -> int:
        ...
    def __ne__(self, other: typing.Any) -> bool:
        ...
    def __setstate__(self, state: typing.SupportsInt) -> None:
        ...
    def __str__(self) -> str:
        ...
    @property
    def name(self) -> str:
        ...
    @property
    def value(self) -> int:
        ...
class MVSModel:
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __init__(self) -> None:
        ...
    def __repr__(self) -> str:
        ...
    def compute_depth_ranges(self) -> list[tuple[float, float]]:
        """
        Compute robust minimum and maximum depths from the sparse point cloud.
        """
    def compute_shared_points(self) -> list[dict[int, int]]:
        """
        Compute the number of shared points between all overlapping images.
        """
    def compute_triangulation_angles(self, percentile: typing.SupportsFloat = 50.0) -> list[dict[int, float]]:
        """
        Compute the median triangulation angles between all overlapping images.
        """
    def get_image_idx(self, name: str) -> int:
        """
        Get the image index for the given image name.
        """
    def get_image_name(self, image_idx: typing.SupportsInt) -> str:
        """
        Get the image name for the given image index.
        """
    def get_max_overlapping_images(self, num_images: typing.SupportsInt, min_triangulation_angle: typing.SupportsFloat) -> list[list[int]]:
        """
        Determine maximally overlapping images for each image, sorted by number of shared points subject to a minimum triangulation angle.
        """
    def get_max_overlapping_images_from_pmvs(self) -> list[list[int]]:
        """
        Get overlapping images defined in the PMVS vis.dat file.
        """
    def read(self, path: str, format: str) -> None:
        """
        Read the model from the given path in the specified format.
        """
    def read_from_colmap(self, path: str, sparse_path: str = 'sparse', images_path: str = 'images') -> None:
        """
        Read the model from a COLMAP reconstruction.
        """
    def read_from_pmvs(self, path: str) -> None:
        """
        Read the model from PMVS output.
        """
class Normalization:
    """
    Members:
    
      L1_ROOT : L1-normalizes each descriptor followed by element-wise square rooting. This normalization is usually better than standard L2-normalization. See 'Three things everyone should know to improve object retrieval', Relja Arandjelovic and Andrew Zisserman, CVPR 2012.
    
      L2 : Each vector is L2-normalized.
    """
    L1_ROOT: typing.ClassVar[Normalization]  # value = Normalization.L1_ROOT
    L2: typing.ClassVar[Normalization]  # value = Normalization.L2
    __members__: typing.ClassVar[dict[str, Normalization]]  # value = {'L1_ROOT': Normalization.L1_ROOT, 'L2': Normalization.L2}
    @staticmethod
    def __repr__(*args, **kwargs):
        """
        __str__(self: object, /) -> str
        """
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __eq__(self, other: typing.Any) -> bool:
        ...
    def __getstate__(self) -> int:
        ...
    def __hash__(self) -> int:
        ...
    def __index__(self) -> int:
        ...
    @typing.overload
    def __init__(self, value: typing.SupportsInt) -> None:
        ...
    @typing.overload
    def __init__(self, name: str) -> None:
        ...
    def __int__(self) -> int:
        ...
    def __ne__(self, other: typing.Any) -> bool:
        ...
    def __setstate__(self, state: typing.SupportsInt) -> None:
        ...
    def __str__(self) -> str:
        ...
    @property
    def name(self) -> str:
        ...
    @property
    def value(self) -> int:
        ...
class ObservationManager:
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __init__(self, reconstruction: Reconstruction, correspondence_graph: CorrespondenceGraph = None) -> None:
        ...
    def __repr__(self) -> str:
        ...
    def add_observation(self, point3D_id: typing.SupportsInt, track_element: TrackElement) -> None:
        """
        Add observation to existing 3D point.
        """
    def add_point3D(self, xyz: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[3, 1]"], track: Track, color: typing.Annotated[numpy.typing.ArrayLike, numpy.uint8, "[3, 1]"] = ...) -> int:
        """
        Add new 3D object, and return its unique ID.
        """
    def decrement_correspondence_has_point3D(self, image_id: typing.SupportsInt, point2D_idx: typing.SupportsInt) -> None:
        """
        Indicate that another image has a point that is not triangulated any more and has a correspondence to this image point. This assumesthat `IncrementCorrespondenceHasPoint3D` was called for the sameimage point and correspondence before.
        """
    def delete_observation(self, image_id: typing.SupportsInt, point2D_idx: typing.SupportsInt) -> None:
        """
        Delete one observation from an image and the corresponding 3D point. Note that this deletes the entire 3D point, if the track has two elements prior to calling this method.
        """
    def delete_point3D(self, point3D_id: typing.SupportsInt) -> None:
        """
        Delete a 3D point, and all its references in the observed images.
        """
    def deregister_frame(self, frame_id: typing.SupportsInt) -> None:
        """
        De-register an existing frame, and all its references.
        """
    def filter_all_points3D(self, max_reproj_error: typing.SupportsFloat, min_tri_angle: typing.SupportsFloat) -> int:
        """
        Filter 3D points with large reprojection error, negative depth, orinsufficient triangulation angle. Return the number of filtered observations.
        """
    def filter_frames(self, min_focal_length_ratio: typing.SupportsFloat, max_focal_length_ratio: typing.SupportsFloat, max_extra_param: typing.SupportsFloat) -> list[int]:
        """
        Filter frames without observations or bogus camera parameters.Return the identifiers of the filtered frames.
        """
    def filter_observations_with_negative_depth(self) -> int:
        """
        Filter observations that have negative depth. Return the number of filtered observations.
        """
    def filter_points3D(self, max_reproj_error: typing.SupportsFloat, min_tri_angle: typing.SupportsFloat, point3D_ids: collections.abc.Set[typing.SupportsInt]) -> int:
        """
        Filter 3D points with large reprojection error, negative depth, orinsufficient triangulation angle. Return the number of filtered observations.
        """
    def filter_points3D_in_images(self, max_reproj_error: typing.SupportsFloat, min_tri_angle: typing.SupportsFloat, image_ids: collections.abc.Set[typing.SupportsInt]) -> int:
        """
        Filter 3D points with large reprojection error, negative depth, orinsufficient triangulation angle. Return the number of filtered observations.
        """
    def increment_correspondence_has_point3D(self, image_id: typing.SupportsInt, point2D_idx: typing.SupportsInt) -> None:
        """
        Indicate that another image has a point that is triangulated and has a correspondence to this image point.
        """
    def merge_points3D(self, point3D_id1: typing.SupportsInt, point3D_id2: typing.SupportsInt) -> int:
        """
        Merge two 3D points and return new identifier of new 3D point.The location of the merged 3D point is a weighted average of the two original 3D point's locations according to their track lengths.
        """
    def num_correspondences(self, image_id: typing.SupportsInt) -> int:
        """
        Number of correspondences for all image points.
        """
    def num_observations(self, image_id: typing.SupportsInt) -> int:
        """
        Number of observations, i.e. the number of image points thathave at least one correspondence to another image.
        """
    def num_visible_points3D(self, image_id: typing.SupportsInt) -> int:
        """
        Get the number of observations that see a triangulated point, i.e. the number of image points that have at least one correspondence toa triangulated point in another image.
        """
    def point3D_visibility_score(self, image_id: typing.SupportsInt) -> int:
        """
        Get the score of triangulated observations. In contrast to`NumVisiblePoints3D`, this score also captures the distributionof triangulated observations in the image. This is useful to select the next best image in incremental reconstruction, because amore uniform distribution of observations results in more robust registration.
        """
    def register_frame(self, frame_id: typing.SupportsInt) -> None:
        """
        Register an existing frame, and all its references.
        """
    @property
    def image_pairs(self) -> dict[int, ImagePairStat]:
        ...
class PairGenerator:
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def all_pairs(self) -> list[tuple[int, int]]:
        ...
    def has_finished(self) -> bool:
        ...
    def next(self) -> list[tuple[int, int]]:
        ...
    def reset(self) -> None:
        ...
class PatchMatchOptions:
    __hash__: typing.ClassVar[None] = None
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __copy__(self) -> PatchMatchOptions:
        ...
    def __deepcopy__(self, arg0: dict) -> PatchMatchOptions:
        ...
    def __eq__(self, arg0: typing.Any) -> bool:
        ...
    def __getstate__(self) -> dict:
        ...
    @typing.overload
    def __init__(self) -> None:
        ...
    @typing.overload
    def __init__(self, arg0: dict) -> None:
        ...
    @typing.overload
    def __init__(self, **kwargs) -> None:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, arg0: dict) -> None:
        ...
    def check(self) -> bool:
        ...
    def mergedict(self, kwargs: dict) -> None:
        ...
    def summary(self, write_type: bool = False) -> str:
        ...
    def todict(self, recursive: bool = True) -> dict:
        ...
    @property
    def allow_missing_files(self) -> bool:
        """
        Whether to tolerate missing images/maps in the problem setup (bool, default: False)
        """
    @allow_missing_files.setter
    def allow_missing_files(self, arg0: bool) -> None:
        ...
    @property
    def cache_size(self) -> float:
        """
        Cache size in gigabytes for patch match. (float, default: 32.0)
        """
    @cache_size.setter
    def cache_size(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def depth_max(self) -> float:
        """
         (float, default: -1.0)
        """
    @depth_max.setter
    def depth_max(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def depth_min(self) -> float:
        """
         (float, default: -1.0)
        """
    @depth_min.setter
    def depth_min(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def filter(self) -> bool:
        """
        Whether to enable filtering. (bool, default: True)
        """
    @filter.setter
    def filter(self, arg0: bool) -> None:
        ...
    @property
    def filter_geom_consistency_max_cost(self) -> float:
        """
        Maximum forward-backward reprojection error for pixel to be geometrically consistent. (float, default: 1.0)
        """
    @filter_geom_consistency_max_cost.setter
    def filter_geom_consistency_max_cost(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def filter_min_ncc(self) -> float:
        """
        Minimum NCC coefficient for pixel to be photo-consistent. (float, default: 0.10000000149011612)
        """
    @filter_min_ncc.setter
    def filter_min_ncc(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def filter_min_num_consistent(self) -> int:
        """
        Minimum number of source images have to be consistent for pixel not to be filtered. (int, default: 2)
        """
    @filter_min_num_consistent.setter
    def filter_min_num_consistent(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def filter_min_triangulation_angle(self) -> float:
        """
        Minimum triangulation angle to be stable. (float, default: 3.0)
        """
    @filter_min_triangulation_angle.setter
    def filter_min_triangulation_angle(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def geom_consistency(self) -> bool:
        """
        Whether to add a regularized geometric consistency term to the cost function. If true, the `depth_maps` and `normal_maps` must not be null. (bool, default: True)
        """
    @geom_consistency.setter
    def geom_consistency(self, arg0: bool) -> None:
        ...
    @property
    def geom_consistency_max_cost(self) -> float:
        """
        Maximum geometric consistency cost in terms of the forward-backward reprojection error in pixels. (float, default: 3.0)
        """
    @geom_consistency_max_cost.setter
    def geom_consistency_max_cost(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def geom_consistency_regularizer(self) -> float:
        """
        The relative weight of the geometric consistency term w.r.t. to the photo-consistency term. (float, default: 0.30000001192092896)
        """
    @geom_consistency_regularizer.setter
    def geom_consistency_regularizer(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def gpu_index(self) -> str:
        """
        Index of the GPU used for patch match. For multi-GPU usage, you should separate multiple GPU indices by comma, e.g., "0,1,2,3". (str, default: -1)
        """
    @gpu_index.setter
    def gpu_index(self, arg0: str) -> None:
        ...
    @property
    def incident_angle_sigma(self) -> float:
        """
        Spread of the incident angle likelihood function. (float, default: 0.8999999761581421)
        """
    @incident_angle_sigma.setter
    def incident_angle_sigma(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def max_image_size(self) -> int:
        """
        Maximum image size in either dimension. (int, default: -1)
        """
    @max_image_size.setter
    def max_image_size(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def min_triangulation_angle(self) -> float:
        """
        Minimum triangulation angle in degrees. (float, default: 1.0)
        """
    @min_triangulation_angle.setter
    def min_triangulation_angle(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def ncc_sigma(self) -> float:
        """
        Spread of the NCC likelihood function. (float, default: 0.6000000238418579)
        """
    @ncc_sigma.setter
    def ncc_sigma(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def num_iterations(self) -> int:
        """
        Number of coordinate descent iterations. (int, default: 5)
        """
    @num_iterations.setter
    def num_iterations(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def num_samples(self) -> int:
        """
        Number of random samples to draw in Monte Carlo sampling. (int, default: 15)
        """
    @num_samples.setter
    def num_samples(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def sigma_color(self) -> float:
        """
        Color sigma for bilaterally weighted NCC. (float, default: 0.20000000298023224)
        """
    @sigma_color.setter
    def sigma_color(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def sigma_spatial(self) -> float:
        """
        Spatial sigma for bilaterally weighted NCC. (float, default: -1.0)
        """
    @sigma_spatial.setter
    def sigma_spatial(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def window_radius(self) -> int:
        """
        Half window size to compute NCC photo-consistency cost. (int, default: 5)
        """
    @window_radius.setter
    def window_radius(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def window_step(self) -> int:
        """
        Number of pixels to skip when computing NCC. (int, default: 1)
        """
    @window_step.setter
    def window_step(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def write_consistency_graph(self) -> bool:
        """
        Whether to write the consistency graph. (bool, default: False)
        """
    @write_consistency_graph.setter
    def write_consistency_graph(self, arg0: bool) -> None:
        ...
class Point2D:
    __hash__: typing.ClassVar[None] = None
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __copy__(self) -> Point2D:
        ...
    def __deepcopy__(self, arg0: dict) -> Point2D:
        ...
    def __eq__(self, arg0: Point2D) -> bool:
        ...
    def __getstate__(self) -> dict:
        ...
    @typing.overload
    def __init__(self) -> None:
        ...
    @typing.overload
    def __init__(self, xy: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[2, 1]"], point3D_id: typing.SupportsInt = ...) -> None:
        ...
    @typing.overload
    def __init__(self, arg0: dict) -> None:
        ...
    @typing.overload
    def __init__(self, **kwargs) -> None:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, arg0: dict) -> None:
        ...
    def has_point3D(self) -> bool:
        ...
    def mergedict(self, kwargs: dict) -> None:
        ...
    def summary(self, write_type: bool = False) -> str:
        ...
    def todict(self, recursive: bool = True) -> dict:
        ...
    def x(self) -> float:
        ...
    def y(self) -> float:
        ...
    @property
    def point3D_id(self) -> int:
        """
         (int, default: 18446744073709551615)
        """
    @point3D_id.setter
    def point3D_id(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def xy(self) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[2, 1]"]:
        """
         (ndarray, default: [0. 0.])
        """
    @xy.setter
    def xy(self, arg0: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[2, 1]"]) -> None:
        ...
class Point2DList:
    __hash__: typing.ClassVar[None] = None
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __bool__(self) -> bool:
        """
        Check whether the list is nonempty
        """
    def __contains__(self, x: Point2D) -> bool:
        """
        Return true the container contains ``x``
        """
    @typing.overload
    def __delitem__(self, arg0: typing.SupportsInt) -> None:
        """
        Delete the list elements at index ``i``
        """
    @typing.overload
    def __delitem__(self, arg0: slice) -> None:
        """
        Delete list elements using a slice object
        """
    def __eq__(self, arg0: Point2DList) -> bool:
        ...
    @typing.overload
    def __getitem__(self, s: slice) -> Point2DList:
        """
        Retrieve list elements using a slice object
        """
    @typing.overload
    def __getitem__(self, arg0: typing.SupportsInt) -> Point2D:
        ...
    @typing.overload
    def __init__(self) -> None:
        ...
    @typing.overload
    def __init__(self, arg0: Point2DList) -> None:
        """
        Copy constructor
        """
    @typing.overload
    def __init__(self, arg0: collections.abc.Iterable) -> None:
        ...
    def __iter__(self) -> collections.abc.Iterator[Point2D]:
        ...
    def __len__(self) -> int:
        ...
    def __ne__(self, arg0: Point2DList) -> bool:
        ...
    def __repr__(self) -> str:
        """
        Return the canonical string representation of this list.
        """
    @typing.overload
    def __setitem__(self, arg0: typing.SupportsInt, arg1: Point2D) -> None:
        ...
    @typing.overload
    def __setitem__(self, arg0: slice, arg1: Point2DList) -> None:
        """
        Assign list elements using a slice object
        """
    def append(self, x: Point2D) -> None:
        """
        Add an item to the end of the list
        """
    def clear(self) -> None:
        """
        Clear the contents
        """
    def count(self, x: Point2D) -> int:
        """
        Return the number of times ``x`` appears in the list
        """
    @typing.overload
    def extend(self, L: Point2DList) -> None:
        """
        Extend the list by appending all the items in the given list
        """
    @typing.overload
    def extend(self, L: collections.abc.Iterable) -> None:
        """
        Extend the list by appending all the items in the given list
        """
    def insert(self, i: typing.SupportsInt, x: Point2D) -> None:
        """
        Insert an item at a given position.
        """
    @typing.overload
    def pop(self) -> Point2D:
        """
        Remove and return the last item
        """
    @typing.overload
    def pop(self, i: typing.SupportsInt) -> Point2D:
        """
        Remove and return the item at index ``i``
        """
    def remove(self, x: Point2D) -> None:
        """
        Remove the first item from the list whose value is x. It is an error if there is no such item.
        """
class Point3D:
    __hash__: typing.ClassVar[None] = None
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __copy__(self) -> Point3D:
        ...
    def __deepcopy__(self, arg0: dict) -> Point3D:
        ...
    def __eq__(self, arg0: Point3D) -> bool:
        ...
    def __getstate__(self) -> dict:
        ...
    @typing.overload
    def __init__(self) -> None:
        ...
    @typing.overload
    def __init__(self, arg0: dict) -> None:
        ...
    @typing.overload
    def __init__(self, **kwargs) -> None:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, arg0: dict) -> None:
        ...
    def mergedict(self, kwargs: dict) -> None:
        ...
    def summary(self, write_type: bool = False) -> str:
        ...
    def todict(self, recursive: bool = True) -> dict:
        ...
    @property
    def color(self) -> typing.Annotated[numpy.typing.NDArray[numpy.uint8], "[3, 1]"]:
        """
         (ndarray, default: [0 0 0])
        """
    @color.setter
    def color(self, arg0: typing.Annotated[numpy.typing.ArrayLike, numpy.uint8, "[3, 1]"]) -> None:
        ...
    @property
    def error(self) -> float:
        """
         (float, default: -1.0)
        """
    @error.setter
    def error(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def track(self) -> Track:
        """
         (Track, default: Track(elements=[]))
        """
    @track.setter
    def track(self, arg0: Track) -> None:
        ...
    @property
    def xyz(self) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[3, 1]"]:
        """
         (ndarray, default: [0. 0. 0.])
        """
    @xyz.setter
    def xyz(self, arg0: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[3, 1]"]) -> None:
        ...
class Point3DMap:
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __bool__(self) -> bool:
        """
        Check whether the map is nonempty
        """
    @typing.overload
    def __contains__(self, arg0: typing.SupportsInt) -> bool:
        ...
    @typing.overload
    def __contains__(self, arg0: typing.Any) -> bool:
        ...
    def __delitem__(self, arg0: typing.SupportsInt) -> None:
        ...
    def __getitem__(self, arg0: typing.SupportsInt) -> Point3D:
        ...
    def __init__(self) -> None:
        ...
    def __iter__(self) -> collections.abc.Iterator[int]:
        ...
    def __len__(self) -> int:
        ...
    def __repr__(self) -> str:
        """
        Return the canonical string representation of this map.
        """
    def __setitem__(self, arg0: typing.SupportsInt, arg1: Point3D) -> None:
        ...
    def items(self) -> typing.ItemsView:
        ...
    def keys(self) -> typing.KeysView:
        ...
    def values(self) -> typing.ValuesView:
        ...
class PoissonMeshingOptions:
    __hash__: typing.ClassVar[None] = None
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __copy__(self) -> PoissonMeshingOptions:
        ...
    def __deepcopy__(self, arg0: dict) -> PoissonMeshingOptions:
        ...
    def __eq__(self, arg0: typing.Any) -> bool:
        ...
    def __getstate__(self) -> dict:
        ...
    @typing.overload
    def __init__(self) -> None:
        ...
    @typing.overload
    def __init__(self, arg0: dict) -> None:
        ...
    @typing.overload
    def __init__(self, **kwargs) -> None:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, arg0: dict) -> None:
        ...
    def check(self) -> bool:
        ...
    def mergedict(self, kwargs: dict) -> None:
        ...
    def summary(self, write_type: bool = False) -> str:
        ...
    def todict(self, recursive: bool = True) -> dict:
        ...
    @property
    def color(self) -> float:
        """
        If specified, the reconstruction code assumes that the input is equippedwith colors and will extrapolate the color values to the vertices of thereconstructed mesh. The floating point value specifies the relativeimportance of finer color estimates over lower ones. (float, default: 32.0)
        """
    @color.setter
    def color(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def depth(self) -> int:
        """
        This integer is the maximum depth of the tree that will be used for surfacereconstruction. Running at depth d corresponds to solving on a voxel gridwhose resolution is no larger than 2^d x 2^d x 2^d. Note that since thereconstructor adapts the octree to the sampling density, the specifiedreconstruction depth is only an upper bound. (int, default: 13)
        """
    @depth.setter
    def depth(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def num_threads(self) -> int:
        """
        The number of threads used for the Poisson reconstruction. (int, default: -1)
        """
    @num_threads.setter
    def num_threads(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def point_weight(self) -> float:
        """
        This floating point value specifies the importance that interpolation ofthe point samples is given in the formulation of the screened Poissonequation. The results of the original (unscreened) Poisson Reconstructioncan be obtained by setting this value to 0. (float, default: 1.0)
        """
    @point_weight.setter
    def point_weight(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def trim(self) -> float:
        """
        This floating point values specifies the value for mesh trimming. Thesubset of the mesh with signal value less than the trim value is discarded. (float, default: 10.0)
        """
    @trim.setter
    def trim(self, arg0: typing.SupportsFloat) -> None:
        ...
class PosePrior:
    __hash__: typing.ClassVar[None] = None
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __copy__(self) -> PosePrior:
        ...
    def __deepcopy__(self, arg0: dict) -> PosePrior:
        ...
    def __eq__(self, arg0: PosePrior) -> bool:
        ...
    def __getstate__(self) -> dict:
        ...
    @typing.overload
    def __init__(self) -> None:
        ...
    @typing.overload
    def __init__(self, position: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[3, 1]"]) -> None:
        ...
    @typing.overload
    def __init__(self, position: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[3, 1]"], coordinate_system: PosePriorCoordinateSystem) -> None:
        ...
    @typing.overload
    def __init__(self, position: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[3, 1]"], position_covariance: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[3, 3]"]) -> None:
        ...
    @typing.overload
    def __init__(self, position: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[3, 1]"], position_covariance: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[3, 3]"], coordinate_system: PosePriorCoordinateSystem) -> None:
        ...
    @typing.overload
    def __init__(self, arg0: dict) -> None:
        ...
    @typing.overload
    def __init__(self, **kwargs) -> None:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, arg0: dict) -> None:
        ...
    def is_covariance_valid(self) -> bool:
        ...
    def is_valid(self) -> bool:
        ...
    def mergedict(self, kwargs: dict) -> None:
        ...
    def summary(self, write_type: bool = False) -> str:
        ...
    def todict(self, recursive: bool = True) -> dict:
        ...
    @property
    def coordinate_system(self) -> PosePriorCoordinateSystem:
        """
         (PosePriorCoordinateSystem, default: PosePriorCoordinateSystem.UNDEFINED)
        """
    @coordinate_system.setter
    def coordinate_system(self, arg0: PosePriorCoordinateSystem) -> None:
        ...
    @property
    def position(self) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[3, 1]"]:
        """
         (ndarray, default: [nan nan nan])
        """
    @position.setter
    def position(self, arg0: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[3, 1]"]) -> None:
        ...
    @property
    def position_covariance(self) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[3, 3]"]:
        """
         (ndarray, default: [[nan nan nan]
         [nan nan nan]
         [nan nan nan]])
        """
    @position_covariance.setter
    def position_covariance(self, arg0: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[3, 3]"]) -> None:
        ...
class PosePriorBundleAdjustmentOptions:
    __hash__: typing.ClassVar[None] = None
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __copy__(self) -> PosePriorBundleAdjustmentOptions:
        ...
    def __deepcopy__(self, arg0: dict) -> PosePriorBundleAdjustmentOptions:
        ...
    def __eq__(self, arg0: typing.Any) -> bool:
        ...
    def __getstate__(self) -> dict:
        ...
    @typing.overload
    def __init__(self) -> None:
        ...
    @typing.overload
    def __init__(self, arg0: dict) -> None:
        ...
    @typing.overload
    def __init__(self, **kwargs) -> None:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, arg0: dict) -> None:
        ...
    def mergedict(self, kwargs: dict) -> None:
        ...
    def summary(self, write_type: bool = False) -> str:
        ...
    def todict(self, recursive: bool = True) -> dict:
        ...
    @property
    def alignment_ransac(self) -> RANSACOptions:
        """
        RANSAC options for Sim3 alignment. (RANSACOptions, default: RANSACOptions(max_error=0.0, min_inlier_ratio=0.1, confidence=0.99, dyn_num_trials_multiplier=3.0, min_num_trials=0, max_num_trials=2147483647, random_seed=-1))
        """
    @alignment_ransac.setter
    def alignment_ransac(self, arg0: RANSACOptions) -> None:
        ...
    @property
    def prior_position_loss_scale(self) -> float:
        """
        Threshold on the residual for the robust loss (chi2 for 3DOF at 95% = 7.815). (float, default: 2.7954834829151074)
        """
    @prior_position_loss_scale.setter
    def prior_position_loss_scale(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def use_robust_loss_on_prior_position(self) -> bool:
        """
        Whether to use a robust loss on prior locations. (bool, default: False)
        """
    @use_robust_loss_on_prior_position.setter
    def use_robust_loss_on_prior_position(self, arg0: bool) -> None:
        ...
class PosePriorCoordinateSystem:
    """
    Members:
    
      UNDEFINED
    
      WGS84
    
      CARTESIAN
    """
    CARTESIAN: typing.ClassVar[PosePriorCoordinateSystem]  # value = PosePriorCoordinateSystem.CARTESIAN
    UNDEFINED: typing.ClassVar[PosePriorCoordinateSystem]  # value = PosePriorCoordinateSystem.UNDEFINED
    WGS84: typing.ClassVar[PosePriorCoordinateSystem]  # value = PosePriorCoordinateSystem.WGS84
    __members__: typing.ClassVar[dict[str, PosePriorCoordinateSystem]]  # value = {'UNDEFINED': PosePriorCoordinateSystem.UNDEFINED, 'WGS84': PosePriorCoordinateSystem.WGS84, 'CARTESIAN': PosePriorCoordinateSystem.CARTESIAN}
    @staticmethod
    def __repr__(*args, **kwargs):
        """
        __str__(self: object, /) -> str
        """
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __eq__(self, other: typing.Any) -> bool:
        ...
    def __getstate__(self) -> int:
        ...
    def __hash__(self) -> int:
        ...
    def __index__(self) -> int:
        ...
    @typing.overload
    def __init__(self, value: typing.SupportsInt) -> None:
        ...
    @typing.overload
    def __init__(self, name: str) -> None:
        ...
    def __int__(self) -> int:
        ...
    def __ne__(self, other: typing.Any) -> bool:
        ...
    def __setstate__(self, state: typing.SupportsInt) -> None:
        ...
    def __str__(self) -> str:
        ...
    @property
    def name(self) -> str:
        ...
    @property
    def value(self) -> int:
        ...
class RANSACOptions:
    __hash__: typing.ClassVar[None] = None
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __copy__(self) -> RANSACOptions:
        ...
    def __deepcopy__(self, arg0: dict) -> RANSACOptions:
        ...
    def __eq__(self, arg0: typing.Any) -> bool:
        ...
    def __getstate__(self) -> dict:
        ...
    @typing.overload
    def __init__(self) -> None:
        ...
    @typing.overload
    def __init__(self, arg0: dict) -> None:
        ...
    @typing.overload
    def __init__(self, **kwargs) -> None:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, arg0: dict) -> None:
        ...
    def check(self) -> None:
        ...
    def mergedict(self, kwargs: dict) -> None:
        ...
    def summary(self, write_type: bool = False) -> str:
        ...
    def todict(self, recursive: bool = True) -> dict:
        ...
    @property
    def confidence(self) -> float:
        """
         (float, default: 0.9999)
        """
    @confidence.setter
    def confidence(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def dyn_num_trials_multiplier(self) -> float:
        """
         (float, default: 3.0)
        """
    @dyn_num_trials_multiplier.setter
    def dyn_num_trials_multiplier(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def max_error(self) -> float:
        """
         (float, default: 4.0)
        """
    @max_error.setter
    def max_error(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def max_num_trials(self) -> int:
        """
         (int, default: 100000)
        """
    @max_num_trials.setter
    def max_num_trials(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def min_inlier_ratio(self) -> float:
        """
         (float, default: 0.01)
        """
    @min_inlier_ratio.setter
    def min_inlier_ratio(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def min_num_trials(self) -> int:
        """
         (int, default: 1000)
        """
    @min_num_trials.setter
    def min_num_trials(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def random_seed(self) -> int:
        """
         (int, default: -1)
        """
    @random_seed.setter
    def random_seed(self, arg0: typing.SupportsInt) -> None:
        ...
class Reconstruction:
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __copy__(self) -> Reconstruction:
        ...
    def __deepcopy__(self, arg0: dict) -> Reconstruction:
        ...
    @typing.overload
    def __init__(self) -> None:
        ...
    @typing.overload
    def __init__(self, reconstruction: Reconstruction) -> None:
        ...
    @typing.overload
    def __init__(self, path: str) -> None:
        ...
    def __repr__(self) -> str:
        ...
    def add_camera(self, camera: Camera) -> None:
        """
        Add new camera. There is only one camera per image, while multiple images might be taken by the same camera.
        """
    def add_frame(self, frame: Frame) -> None:
        """
        Add new frame.
        """
    def add_image(self, image: Image) -> None:
        """
        Add new image. Its camera must have been added before. If its camera object is unset, it will be automatically populated from the added cameras.
        """
    def add_observation(self, point3D_id: typing.SupportsInt, track_element: TrackElement) -> None:
        """
        Add observation to existing 3D point.
        """
    def add_point3D(self, xyz: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[3, 1]"], track: Track, color: typing.Annotated[numpy.typing.ArrayLike, numpy.uint8, "[3, 1]"] = ...) -> int:
        """
        Add new 3D object, and return its unique ID.
        """
    def add_rig(self, rig: Rig) -> None:
        """
        Add new rig.
        """
    def camera(self, camera_id: typing.SupportsInt) -> Camera:
        """
        Direct accessor for a camera.
        """
    def compute_bounding_box(self, min_percentile: typing.SupportsFloat = 0.0, max_percentile: typing.SupportsFloat = 1.0, use_images: bool = False) -> AlignedBox3d:
        ...
    def compute_centroid(self, min_percentile: typing.SupportsFloat = 0.0, max_percentile: typing.SupportsFloat = 1.0, use_images: bool = False) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[3, 1]"]:
        ...
    def compute_mean_observations_per_reg_image(self) -> float:
        ...
    def compute_mean_reprojection_error(self) -> float:
        ...
    def compute_mean_track_length(self) -> float:
        ...
    def compute_num_observations(self) -> int:
        ...
    def create_image_dirs(self, path: str) -> None:
        """
        Create all image sub-directories in the given path.
        """
    def crop(self, bbox: AlignedBox3d) -> Reconstruction:
        ...
    def delete_all_points2D_and_points3D(self) -> None:
        """
        Delete all 2D points of all images and all 3D points.
        """
    def delete_observation(self, image_id: typing.SupportsInt, point2D_idx: typing.SupportsInt) -> None:
        """
        Delete one observation from an image and the corresponding 3D point. Note that this deletes the entire 3D point, if the track has two elements prior to calling this method.
        """
    def delete_point3D(self, point3D_id: typing.SupportsInt) -> None:
        """
        Delete a 3D point, and all its references in the observed images.
        """
    def deregister_frame(self, frame_id: typing.SupportsInt) -> None:
        """
        De-register an existing frame, and all its references.
        """
    def exists_camera(self, camera_id: typing.SupportsInt) -> bool:
        ...
    def exists_frame(self, frame_id: typing.SupportsInt) -> bool:
        ...
    def exists_image(self, image_id: typing.SupportsInt) -> bool:
        ...
    def exists_point3D(self, point3D_id: typing.SupportsInt) -> bool:
        ...
    def exists_rig(self, rig_id: typing.SupportsInt) -> bool:
        ...
    def export_PLY(self, output_path: str) -> None:
        """
        Export 3D points to PLY format (.ply).
        """
    def extract_colors_for_all_images(self, path: str) -> None:
        """
        Extract colors for all 3D points by computing the mean color of all images.
        """
    def extract_colors_for_image(self, image_id: typing.SupportsInt, path: str) -> bool:
        """
        Extract colors for 3D points of given image. Colors will be extracted only for 3D points which are completely black. Return True if the image could be read at the given path.
        """
    def find_common_reg_image_ids(self, other: Reconstruction) -> list[tuple[int, int]]:
        """
        Find images that are both present in this and the given reconstruction.
        """
    def find_image_with_name(self, name: str) -> Image:
        """
        Find image with matching name. Returns None if no match is found.
        """
    def frame(self, frame_id: typing.SupportsInt) -> Frame:
        """
        Direct accessor for a frame.
        """
    def image(self, image_id: typing.SupportsInt) -> Image:
        """
        Direct accessor for an image.
        """
    def import_PLY(self, path: str) -> None:
        """
        Import from PLY format. Note that these import functions areonly intended for visualization of data and usable for reconstruction.
        """
    def load(self, database_cache: DatabaseCache) -> None:
        ...
    def merge_points3D(self, point3D_id1: typing.SupportsInt, point3D_id2: typing.SupportsInt) -> int:
        """
        Merge two 3D points and return new identifier of new 3D point.The location of the merged 3D point is a weighted average of the two original 3D point's locations according to their track lengths.
        """
    def normalize(self, fixed_scale: bool = False, extent: typing.SupportsFloat = 10.0, min_percentile: typing.SupportsFloat = 0.1, max_percentile: typing.SupportsFloat = 0.9, use_images: bool = True) -> Sim3d:
        """
        Normalize scene by scaling and translation to avoid degeneratevisualization after bundle adjustment and to improve numericalstability of algorithms.
        
        Translates scene such that the mean of the camera centers or pointlocations are at the origin of the coordinate system.
        
         Scales scene such that the minimum and maximum camera centers (or points) are  at the given `extent`, whereas `min_percentile` and  `max_percentile` determine the minimum  and maximum percentiles of the camera centers (or points) considered.
        """
    def num_cameras(self) -> int:
        ...
    def num_frames(self) -> int:
        ...
    def num_images(self) -> int:
        ...
    def num_points3D(self) -> int:
        ...
    def num_reg_frames(self) -> int:
        ...
    def num_reg_images(self) -> int:
        ...
    def num_rigs(self) -> int:
        ...
    def point3D(self, point3D_id: typing.SupportsInt) -> Point3D:
        """
        Direct accessor for a Point3D.
        """
    def point3D_ids(self) -> set[int]:
        ...
    def read(self, path: str) -> None:
        """
        Read reconstruction in COLMAP format. Prefer binary.
        """
    def read_binary(self, path: str) -> None:
        ...
    def read_text(self, path: str) -> None:
        ...
    def reg_frame_ids(self) -> list[int]:
        ...
    def reg_image_ids(self) -> list[int]:
        ...
    def register_frame(self, frame_id: typing.SupportsInt) -> None:
        """
        Register an existing frame.
        """
    def rig(self, rig_id: typing.SupportsInt) -> Rig:
        """
        Direct accessor for a rig.
        """
    def summary(self) -> str:
        ...
    def tear_down(self) -> None:
        ...
    def transform(self, new_from_old_world: Sim3d) -> None:
        """
        Apply the 3D similarity transformation to all images and points.
        """
    def update_point_3d_errors(self) -> None:
        ...
    def write(self, output_dir: str) -> None:
        """
        Write reconstruction in COLMAP binary format.
        """
    def write_binary(self, path: str) -> None:
        ...
    def write_text(self, path: str) -> None:
        ...
    @property
    def cameras(self) -> CameraMap:
        ...
    @property
    def frames(self) -> FrameMap:
        ...
    @property
    def images(self) -> ImageMap:
        ...
    @property
    def points3D(self) -> Point3DMap:
        ...
    @property
    def rigs(self) -> RigMap:
        ...
class ReconstructionManager:
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __init__(self) -> None:
        ...
    def add(self) -> int:
        ...
    def clear(self) -> None:
        ...
    def delete(self, idx: typing.SupportsInt) -> None:
        ...
    def get(self, idx: typing.SupportsInt) -> Reconstruction:
        ...
    def read(self, path: str) -> int:
        ...
    def size(self) -> int:
        ...
    def write(self, path: str) -> None:
        ...
class Rig:
    __hash__: typing.ClassVar[None] = None
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __copy__(self) -> Rig:
        ...
    def __deepcopy__(self, arg0: dict) -> Rig:
        ...
    def __eq__(self, arg0: Rig) -> bool:
        ...
    def __getstate__(self) -> dict:
        ...
    @typing.overload
    def __init__(self) -> None:
        ...
    @typing.overload
    def __init__(self, arg0: dict) -> None:
        ...
    @typing.overload
    def __init__(self, **kwargs) -> None:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, arg0: dict) -> None:
        ...
    def add_ref_sensor(self, arg0: sensor_t) -> None:
        """
        sensor_idAdd reference sensor.
        """
    def add_sensor(self, arg0: sensor_t, arg1: pycolmap._core.Rigid3d | None) -> None:
        """
        sensor_idAdd non-reference sensor.
        """
    def has_sensor(self, arg0: sensor_t) -> bool:
        """
        Whether the rig has a specific sensor.
        """
    def is_ref_sensor(self, arg0: sensor_t) -> bool:
        """
        Check whether the given sensor is the reference sensor.
        """
    def mergedict(self, kwargs: dict) -> None:
        ...
    def num_sensors(self) -> int:
        """
        The number of sensors in the rig.
        """
    def sensor_from_rig(self, sensor_id: sensor_t) -> pycolmap._core.Rigid3d | None:
        """
        The the transformation from rig to the sensor.
        """
    def sensor_ids(self) -> set[sensor_t]:
        """
        Get all sensor ids (including the reference sensor) in the rig.
        """
    def set_sensor_from_rig(self, sensor_id: sensor_t, sensor_from_rig: pycolmap._core.Rigid3d | None) -> None:
        """
        Set the sensor_from_rig transformation.
        """
    def summary(self, write_type: bool = False) -> str:
        ...
    def todict(self, recursive: bool = True) -> dict:
        ...
    @property
    def non_ref_sensors(self) -> dict[sensor_t, pycolmap._core.Rigid3d | None]:
        """
        Access all sensors in the rig except for reference sensor (dict, default: {})
        """
    @property
    def ref_sensor_id(self) -> sensor_t:
        """
        The reference sensor's identifier. (sensor_t, default: sensor_t(type=SensorType.INVALID, id=4294967295))
        """
    @property
    def rig_id(self) -> int:
        """
        Unique identifier of the rig. (int, default: 4294967295)
        """
    @rig_id.setter
    def rig_id(self, arg1: typing.SupportsInt) -> None:
        ...
class RigConfig:
    __hash__: typing.ClassVar[None] = None
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __copy__(self) -> RigConfig:
        ...
    def __deepcopy__(self, arg0: dict) -> RigConfig:
        ...
    def __eq__(self, arg0: typing.Any) -> bool:
        ...
    def __getstate__(self) -> dict:
        ...
    @typing.overload
    def __init__(self) -> None:
        ...
    @typing.overload
    def __init__(self, arg0: dict) -> None:
        ...
    @typing.overload
    def __init__(self, **kwargs) -> None:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, arg0: dict) -> None:
        ...
    def mergedict(self, kwargs: dict) -> None:
        ...
    def summary(self, write_type: bool = False) -> str:
        ...
    def todict(self, recursive: bool = True) -> dict:
        ...
    @property
    def cameras(self) -> list[RigConfigCamera]:
        """
         (list, default: [])
        """
    @cameras.setter
    def cameras(self, arg0: collections.abc.Sequence[RigConfigCamera]) -> None:
        ...
class RigConfigCamera:
    __hash__: typing.ClassVar[None] = None
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __copy__(self) -> RigConfigCamera:
        ...
    def __deepcopy__(self, arg0: dict) -> RigConfigCamera:
        ...
    def __eq__(self, arg0: typing.Any) -> bool:
        ...
    def __getstate__(self) -> dict:
        ...
    @typing.overload
    def __init__(self) -> None:
        ...
    @typing.overload
    def __init__(self, arg0: dict) -> None:
        ...
    @typing.overload
    def __init__(self, **kwargs) -> None:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, arg0: dict) -> None:
        ...
    def mergedict(self, kwargs: dict) -> None:
        ...
    def summary(self, write_type: bool = False) -> str:
        ...
    def todict(self, recursive: bool = True) -> dict:
        ...
    @property
    def cam_from_rig(self) -> pycolmap._core.Rigid3d | None:
        """
         (NoneType, default: None)
        """
    @cam_from_rig.setter
    def cam_from_rig(self, arg0: pycolmap._core.Rigid3d | None) -> None:
        ...
    @property
    def camera(self) -> pycolmap._core.Camera | None:
        """
         (NoneType, default: None)
        """
    @camera.setter
    def camera(self, arg0: pycolmap._core.Camera | None) -> None:
        ...
    @property
    def image_prefix(self) -> str:
        """
         (str, default: )
        """
    @image_prefix.setter
    def image_prefix(self, arg0: str) -> None:
        ...
    @property
    def ref_sensor(self) -> bool:
        """
         (bool, default: False)
        """
    @ref_sensor.setter
    def ref_sensor(self, arg0: bool) -> None:
        ...
class RigMap:
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __bool__(self) -> bool:
        """
        Check whether the map is nonempty
        """
    @typing.overload
    def __contains__(self, arg0: typing.SupportsInt) -> bool:
        ...
    @typing.overload
    def __contains__(self, arg0: typing.Any) -> bool:
        ...
    def __delitem__(self, arg0: typing.SupportsInt) -> None:
        ...
    def __getitem__(self, arg0: typing.SupportsInt) -> Rig:
        ...
    def __init__(self) -> None:
        ...
    def __iter__(self) -> collections.abc.Iterator[int]:
        ...
    def __len__(self) -> int:
        ...
    def __repr__(self) -> str:
        """
        Return the canonical string representation of this map.
        """
    def __setitem__(self, arg0: typing.SupportsInt, arg1: Rig) -> None:
        ...
    def items(self) -> typing.ItemsView:
        ...
    def keys(self) -> typing.KeysView:
        ...
    def values(self) -> typing.ValuesView:
        ...
class Rigid3d:
    __hash__: typing.ClassVar[None] = None
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    @staticmethod
    def interpolate(cam_from_world1: Rigid3d, cam_from_world2: Rigid3d, t: typing.SupportsFloat) -> Rigid3d:
        ...
    def __copy__(self) -> Rigid3d:
        ...
    def __deepcopy__(self, arg0: dict) -> Rigid3d:
        ...
    def __eq__(self, arg0: Rigid3d) -> bool:
        ...
    def __getstate__(self) -> dict:
        ...
    @typing.overload
    def __init__(self) -> None:
        ...
    @typing.overload
    def __init__(self, rotation: Rotation3d, translation: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[3, 1]"]) -> None:
        ...
    @typing.overload
    def __init__(self, matrix: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[3, 4]"]) -> None:
        """
        3x4 transformation matrix.
        """
    @typing.overload
    def __init__(self, arg0: dict) -> None:
        ...
    @typing.overload
    def __init__(self, **kwargs) -> None:
        ...
    @typing.overload
    def __mul__(self, arg0: Rigid3d) -> Rigid3d:
        ...
    @typing.overload
    def __mul__(self, arg0: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[3, 1]"]) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[3, 1]"]:
        ...
    @typing.overload
    def __mul__(self, arg0: typing.Annotated[numpy.typing.NDArray[numpy.float64], "[m, 3]"]) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[m, 3]"]:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, arg0: dict) -> None:
        ...
    def adjoint(self) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[6, 6]"]:
        ...
    def adjoint_inverse(self) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[6, 6]"]:
        ...
    def inverse(self) -> Rigid3d:
        ...
    def matrix(self) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[3, 4]"]:
        ...
    def mergedict(self, kwargs: dict) -> None:
        ...
    def summary(self, write_type: bool = False) -> str:
        ...
    def todict(self, recursive: bool = True) -> dict:
        ...
    @property
    def rotation(self) -> Rotation3d:
        """
         (Rotation3d, default: Rotation3d(xyzw=[0, 0, 0, 1]))
        """
    @rotation.setter
    def rotation(self, arg0: Rotation3d) -> None:
        ...
    @property
    def translation(self) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[3, 1]"]:
        """
         (ndarray, default: [0. 0. 0.])
        """
    @translation.setter
    def translation(self, arg0: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[3, 1]"]) -> None:
        ...
class Rotation3d:
    __hash__: typing.ClassVar[None] = None
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __copy__(self) -> Rotation3d:
        ...
    def __deepcopy__(self, arg0: dict) -> Rotation3d:
        ...
    def __eq__(self, arg0: Rotation3d) -> bool:
        ...
    def __getstate__(self) -> dict:
        ...
    @typing.overload
    def __init__(self) -> None:
        ...
    @typing.overload
    def __init__(self, xyzw: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[4, 1]"]) -> None:
        """
        Quaternion in [x,y,z,w] format.
        """
    @typing.overload
    def __init__(self, matrix: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[3, 3]"]) -> None:
        """
        3x3 rotation matrix.
        """
    @typing.overload
    def __init__(self, axis_angle: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[3, 1]"]) -> None:
        """
        Axis-angle 3D vector.
        """
    @typing.overload
    def __init__(self, arg0: dict) -> None:
        ...
    @typing.overload
    def __init__(self, **kwargs) -> None:
        ...
    @typing.overload
    def __mul__(self, arg0: Rotation3d) -> Rotation3d:
        ...
    @typing.overload
    def __mul__(self, arg0: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[3, 1]"]) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[3, 1]"]:
        ...
    @typing.overload
    def __mul__(self, arg0: typing.Annotated[numpy.typing.NDArray[numpy.float64], "[m, 3]"]) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[m, 3]"]:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, arg0: dict) -> None:
        ...
    def angle(self) -> float:
        ...
    def angle_to(self, other: Rotation3d) -> float:
        ...
    def inverse(self) -> Rotation3d:
        ...
    def matrix(self) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[3, 3]"]:
        ...
    def mergedict(self, kwargs: dict) -> None:
        ...
    def norm(self) -> float:
        ...
    def normalize(self) -> None:
        ...
    def summary(self, write_type: bool = False) -> str:
        ...
    def todict(self, recursive: bool = True) -> dict:
        ...
    @property
    def quat(self) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[4, 1]"]:
        """
        Quaternion in [x,y,z,w] format. (ndarray, default: [0. 0. 0. 1.])
        """
    @quat.setter
    def quat(self, arg1: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[4, 1]"]) -> None:
        ...
class SensorType:
    """
    Members:
    
      INVALID
    
      CAMERA
    
      IMU
    """
    CAMERA: typing.ClassVar[SensorType]  # value = SensorType.CAMERA
    IMU: typing.ClassVar[SensorType]  # value = SensorType.IMU
    INVALID: typing.ClassVar[SensorType]  # value = SensorType.INVALID
    __members__: typing.ClassVar[dict[str, SensorType]]  # value = {'INVALID': SensorType.INVALID, 'CAMERA': SensorType.CAMERA, 'IMU': SensorType.IMU}
    @staticmethod
    def __repr__(*args, **kwargs):
        """
        __str__(self: object, /) -> str
        """
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __eq__(self, other: typing.Any) -> bool:
        ...
    def __getstate__(self) -> int:
        ...
    def __hash__(self) -> int:
        ...
    def __index__(self) -> int:
        ...
    @typing.overload
    def __init__(self, value: typing.SupportsInt) -> None:
        ...
    @typing.overload
    def __init__(self, name: str) -> None:
        ...
    def __int__(self) -> int:
        ...
    def __ne__(self, other: typing.Any) -> bool:
        ...
    def __setstate__(self, state: typing.SupportsInt) -> None:
        ...
    def __str__(self) -> str:
        ...
    @property
    def name(self) -> str:
        ...
    @property
    def value(self) -> int:
        ...
class SequentialPairGenerator(PairGenerator):
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __init__(self, options: SequentialPairingOptions, database: Database) -> None:
        ...
class SequentialPairingOptions:
    __hash__: typing.ClassVar[None] = None
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __copy__(self) -> SequentialPairingOptions:
        ...
    def __deepcopy__(self, arg0: dict) -> SequentialPairingOptions:
        ...
    def __eq__(self, arg0: typing.Any) -> bool:
        ...
    def __getstate__(self) -> dict:
        ...
    @typing.overload
    def __init__(self) -> None:
        ...
    @typing.overload
    def __init__(self, arg0: dict) -> None:
        ...
    @typing.overload
    def __init__(self, **kwargs) -> None:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, arg0: dict) -> None:
        ...
    def check(self) -> bool:
        ...
    def mergedict(self, kwargs: dict) -> None:
        ...
    def summary(self, write_type: bool = False) -> str:
        ...
    def todict(self, recursive: bool = True) -> dict:
        ...
    def vocab_tree_options(self) -> VocabTreePairingOptions:
        ...
    @property
    def expand_rig_images(self) -> bool:
        """
        Whether to match an image against all images in neighboring rig frames. If no rigs/frames are configured in the database, this option is ignored. (bool, default: True)
        """
    @expand_rig_images.setter
    def expand_rig_images(self, arg0: bool) -> None:
        ...
    @property
    def loop_detection(self) -> bool:
        """
        Loop detection is invoked every `loop_detection_period` images. (bool, default: False)
        """
    @loop_detection.setter
    def loop_detection(self, arg0: bool) -> None:
        ...
    @property
    def loop_detection_max_num_features(self) -> int:
        """
        The maximum number of features to use for indexing an image. If an image has more features, only the largest-scale features will be indexed. (int, default: -1)
        """
    @loop_detection_max_num_features.setter
    def loop_detection_max_num_features(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def loop_detection_num_checks(self) -> int:
        """
        Number of nearest-neighbor checks to use in retrieval. (int, default: 64)
        """
    @loop_detection_num_checks.setter
    def loop_detection_num_checks(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def loop_detection_num_images(self) -> int:
        """
        The number of images to retrieve in loop detection. This number should be significantly larger than the sequential matching overlap. (int, default: 50)
        """
    @loop_detection_num_images.setter
    def loop_detection_num_images(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def loop_detection_num_images_after_verification(self) -> int:
        """
        How many images to return after spatial verification. Set to 0 to turn off spatial verification. (int, default: 0)
        """
    @loop_detection_num_images_after_verification.setter
    def loop_detection_num_images_after_verification(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def loop_detection_num_nearest_neighbors(self) -> int:
        """
        Number of nearest neighbors to retrieve per query feature. (int, default: 1)
        """
    @loop_detection_num_nearest_neighbors.setter
    def loop_detection_num_nearest_neighbors(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def loop_detection_period(self) -> int:
        """
        The frequency at which loop detection is triggered, in number of images. (int, default: 10)
        """
    @loop_detection_period.setter
    def loop_detection_period(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def num_threads(self) -> int:
        """
        Number of threads for loop detection indexing and retrieval. (int, default: -1)
        """
    @num_threads.setter
    def num_threads(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def overlap(self) -> int:
        """
        Number of overlapping image pairs. (int, default: 10)
        """
    @overlap.setter
    def overlap(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def quadratic_overlap(self) -> bool:
        """
        Whether to match images against their quadratic neighbors. (bool, default: True)
        """
    @quadratic_overlap.setter
    def quadratic_overlap(self, arg0: bool) -> None:
        ...
    @property
    def vocab_tree_path(self) -> str:
        """
        Path to the vocabulary tree. (str, default: https://github.com/colmap/colmap/releases/download/3.11.1/vocab_tree_faiss_flickr100K_words256K.bin;vocab_tree_faiss_flickr100K_words256K.bin;96ca8ec8ea60b1f73465aaf2c401fd3b3ca75cdba2d3c50d6a2f6f760f275ddc)
        """
    @vocab_tree_path.setter
    def vocab_tree_path(self, arg0: str) -> None:
        ...
class Sift:
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __init__(self, options: pycolmap._core.FeatureExtractionOptions | None = None, device: Device = ...) -> None:
        ...
    @typing.overload
    def extract(self, image: typing.Annotated[numpy.typing.NDArray[numpy.uint8], "[m, n]", "flags.c_contiguous"]) -> tuple[typing.Annotated[numpy.typing.NDArray[numpy.float32], "[m, 4]"], typing.Annotated[numpy.typing.NDArray[numpy.float32], "[m, n]"]]:
        ...
    @typing.overload
    def extract(self, image: typing.Annotated[numpy.typing.NDArray[numpy.float32], "[m, n]", "flags.c_contiguous"]) -> tuple[typing.Annotated[numpy.typing.NDArray[numpy.float32], "[m, 4]"], typing.Annotated[numpy.typing.NDArray[numpy.float32], "[m, n]"]]:
        ...
    @property
    def device(self) -> Device:
        ...
    @property
    def options(self) -> FeatureExtractionOptions:
        ...
class SiftExtractionOptions:
    __hash__: typing.ClassVar[None] = None
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __copy__(self) -> SiftExtractionOptions:
        ...
    def __deepcopy__(self, arg0: dict) -> SiftExtractionOptions:
        ...
    def __eq__(self, arg0: typing.Any) -> bool:
        ...
    def __getstate__(self) -> dict:
        ...
    @typing.overload
    def __init__(self) -> None:
        ...
    @typing.overload
    def __init__(self, arg0: dict) -> None:
        ...
    @typing.overload
    def __init__(self, **kwargs) -> None:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, arg0: dict) -> None:
        ...
    def check(self) -> bool:
        ...
    def mergedict(self, kwargs: dict) -> None:
        ...
    def summary(self, write_type: bool = False) -> str:
        ...
    def todict(self, recursive: bool = True) -> dict:
        ...
    @property
    def darkness_adaptivity(self) -> bool:
        """
        Whether to adapt the feature detection depending on the image darkness. only available on GPU. (bool, default: False)
        """
    @darkness_adaptivity.setter
    def darkness_adaptivity(self, arg0: bool) -> None:
        ...
    @property
    def domain_size_pooling(self) -> bool:
        """
        "Domain-Size Pooling in Local Descriptors and NetworkArchitectures", J. Dong and S. Soatto, CVPR 2015 (bool, default: False)
        """
    @domain_size_pooling.setter
    def domain_size_pooling(self, arg0: bool) -> None:
        ...
    @property
    def dsp_max_scale(self) -> float:
        """
         (float, default: 3.0)
        """
    @dsp_max_scale.setter
    def dsp_max_scale(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def dsp_min_scale(self) -> float:
        """
         (float, default: 0.16666666666666666)
        """
    @dsp_min_scale.setter
    def dsp_min_scale(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def dsp_num_scales(self) -> int:
        """
         (int, default: 10)
        """
    @dsp_num_scales.setter
    def dsp_num_scales(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def edge_threshold(self) -> float:
        """
        Edge threshold for detection. (float, default: 10.0)
        """
    @edge_threshold.setter
    def edge_threshold(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def estimate_affine_shape(self) -> bool:
        """
        Estimate affine shape of SIFT features in the form of oriented ellipses as opposed to original SIFT which estimates oriented disks. (bool, default: False)
        """
    @estimate_affine_shape.setter
    def estimate_affine_shape(self, arg0: bool) -> None:
        ...
    @property
    def first_octave(self) -> int:
        """
        First octave in the pyramid, i.e. -1 upsamples the image by one level. (int, default: -1)
        """
    @first_octave.setter
    def first_octave(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def max_num_features(self) -> int:
        """
        Maximum number of features to detect, keeping larger-scale features. (int, default: 8192)
        """
    @max_num_features.setter
    def max_num_features(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def max_num_orientations(self) -> int:
        """
        Maximum number of orientations per keypoint if not estimate_affine_shape. (int, default: 2)
        """
    @max_num_orientations.setter
    def max_num_orientations(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def normalization(self) -> Normalization:
        """
        L1_ROOT or L2 descriptor normalization (Normalization, default: Normalization.L1_ROOT)
        """
    @normalization.setter
    def normalization(self, arg0: Normalization) -> None:
        ...
    @property
    def num_octaves(self) -> int:
        """
         (int, default: 4)
        """
    @num_octaves.setter
    def num_octaves(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def octave_resolution(self) -> int:
        """
        Number of levels per octave. (int, default: 3)
        """
    @octave_resolution.setter
    def octave_resolution(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def peak_threshold(self) -> float:
        """
        Peak threshold for detection. (float, default: 0.006666666666666667)
        """
    @peak_threshold.setter
    def peak_threshold(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def upright(self) -> bool:
        """
        Fix the orientation to 0 for upright features (bool, default: False)
        """
    @upright.setter
    def upright(self, arg0: bool) -> None:
        ...
class SiftMatchingOptions:
    __hash__: typing.ClassVar[None] = None
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __copy__(self) -> SiftMatchingOptions:
        ...
    def __deepcopy__(self, arg0: dict) -> SiftMatchingOptions:
        ...
    def __eq__(self, arg0: typing.Any) -> bool:
        ...
    def __getstate__(self) -> dict:
        ...
    @typing.overload
    def __init__(self) -> None:
        ...
    @typing.overload
    def __init__(self, arg0: dict) -> None:
        ...
    @typing.overload
    def __init__(self, **kwargs) -> None:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, arg0: dict) -> None:
        ...
    def check(self) -> bool:
        ...
    def mergedict(self, kwargs: dict) -> None:
        ...
    def summary(self, write_type: bool = False) -> str:
        ...
    def todict(self, recursive: bool = True) -> dict:
        ...
    @property
    def cpu_brute_force_matcher(self) -> bool:
        """
        Whether to use brute-force instead of faiss based CPU matching. (bool, default: False)
        """
    @cpu_brute_force_matcher.setter
    def cpu_brute_force_matcher(self, arg0: bool) -> None:
        ...
    @property
    def cross_check(self) -> bool:
        """
        Whether to enable cross checking in matching. (bool, default: True)
        """
    @cross_check.setter
    def cross_check(self, arg0: bool) -> None:
        ...
    @property
    def max_distance(self) -> float:
        """
        Maximum distance to best match. (float, default: 0.7)
        """
    @max_distance.setter
    def max_distance(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def max_ratio(self) -> float:
        """
        Maximum distance ratio between first and second best match. (float, default: 0.8)
        """
    @max_ratio.setter
    def max_ratio(self, arg0: typing.SupportsFloat) -> None:
        ...
class Sim3d:
    __hash__: typing.ClassVar[None] = None
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __copy__(self) -> Sim3d:
        ...
    def __deepcopy__(self, arg0: dict) -> Sim3d:
        ...
    def __eq__(self, arg0: Sim3d) -> bool:
        ...
    def __getstate__(self) -> dict:
        ...
    @typing.overload
    def __init__(self) -> None:
        ...
    @typing.overload
    def __init__(self, scale: typing.SupportsFloat, rotation: Rotation3d, translation: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[3, 1]"]) -> None:
        ...
    @typing.overload
    def __init__(self, matrix: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[3, 4]"]) -> None:
        """
        3x4 transformation matrix.
        """
    @typing.overload
    def __init__(self, arg0: dict) -> None:
        ...
    @typing.overload
    def __init__(self, **kwargs) -> None:
        ...
    @typing.overload
    def __mul__(self, arg0: Sim3d) -> Sim3d:
        ...
    @typing.overload
    def __mul__(self, arg0: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[3, 1]"]) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[3, 1]"]:
        ...
    @typing.overload
    def __mul__(self, arg0: typing.Annotated[numpy.typing.NDArray[numpy.float64], "[m, 3]"]) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[m, 3]"]:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, arg0: dict) -> None:
        ...
    def inverse(self) -> Sim3d:
        ...
    def matrix(self) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[3, 4]"]:
        ...
    def mergedict(self, kwargs: dict) -> None:
        ...
    def summary(self, write_type: bool = False) -> str:
        ...
    def todict(self, recursive: bool = True) -> dict:
        ...
    def transform_camera_world(self, cam_from_world: Rigid3d) -> Rigid3d:
        ...
    @property
    def rotation(self) -> Rotation3d:
        """
         (Rotation3d, default: Rotation3d(xyzw=[0, 0, 0, 1]))
        """
    @rotation.setter
    def rotation(self, arg0: Rotation3d) -> None:
        ...
    @property
    def scale(self) -> numpy.ndarray:
        """
         (ndarray, default: 1.0)
        """
    @scale.setter
    def scale(self, arg1: typing.SupportsFloat) -> None:
        ...
    @property
    def translation(self) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[3, 1]"]:
        """
         (ndarray, default: [0. 0. 0.])
        """
    @translation.setter
    def translation(self, arg0: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[3, 1]"]) -> None:
        ...
class SpatialPairGenerator(PairGenerator):
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __init__(self, options: SpatialPairingOptions, database: Database) -> None:
        ...
class SpatialPairingOptions:
    __hash__: typing.ClassVar[None] = None
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __copy__(self) -> SpatialPairingOptions:
        ...
    def __deepcopy__(self, arg0: dict) -> SpatialPairingOptions:
        ...
    def __eq__(self, arg0: typing.Any) -> bool:
        ...
    def __getstate__(self) -> dict:
        ...
    @typing.overload
    def __init__(self) -> None:
        ...
    @typing.overload
    def __init__(self, arg0: dict) -> None:
        ...
    @typing.overload
    def __init__(self, **kwargs) -> None:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, arg0: dict) -> None:
        ...
    def check(self) -> bool:
        ...
    def mergedict(self, kwargs: dict) -> None:
        ...
    def summary(self, write_type: bool = False) -> str:
        ...
    def todict(self, recursive: bool = True) -> dict:
        ...
    @property
    def ignore_z(self) -> bool:
        """
        Whether to ignore the Z-component of the location prior. (bool, default: True)
        """
    @ignore_z.setter
    def ignore_z(self, arg0: bool) -> None:
        ...
    @property
    def max_distance(self) -> float:
        """
        The maximum distance between the query and nearest neighbor [meters]. (float, default: 100.0)
        """
    @max_distance.setter
    def max_distance(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def max_num_neighbors(self) -> int:
        """
        The maximum number of nearest neighbors to match. (int, default: 50)
        """
    @max_num_neighbors.setter
    def max_num_neighbors(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def min_num_neighbors(self) -> int:
        """
        The minimum number of nearest neighbors to match. Neighbors include those within max_distance or to satisfy min_num_neighbors. (int, default: 0)
        """
    @min_num_neighbors.setter
    def min_num_neighbors(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def num_threads(self) -> int:
        """
         (int, default: -1)
        """
    @num_threads.setter
    def num_threads(self, arg0: typing.SupportsInt) -> None:
        ...
class StereoFusionOptions:
    __hash__: typing.ClassVar[None] = None
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __copy__(self) -> StereoFusionOptions:
        ...
    def __deepcopy__(self, arg0: dict) -> StereoFusionOptions:
        ...
    def __eq__(self, arg0: typing.Any) -> bool:
        ...
    def __getstate__(self) -> dict:
        ...
    @typing.overload
    def __init__(self) -> None:
        ...
    @typing.overload
    def __init__(self, arg0: dict) -> None:
        ...
    @typing.overload
    def __init__(self, **kwargs) -> None:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, arg0: dict) -> None:
        ...
    def check(self) -> bool:
        ...
    def mergedict(self, kwargs: dict) -> None:
        ...
    def summary(self, write_type: bool = False) -> str:
        ...
    def todict(self, recursive: bool = True) -> dict:
        ...
    @property
    def bounding_box(self) -> tuple[typing.Annotated[numpy.typing.NDArray[numpy.float32], "[3, 1]"], typing.Annotated[numpy.typing.NDArray[numpy.float32], "[3, 1]"]]:
        """
        Bounding box Tuple[min, max] (tuple, default: (array([-3.4028235e+38, -3.4028235e+38, -3.4028235e+38], dtype=float32), array([3.4028235e+38, 3.4028235e+38, 3.4028235e+38], dtype=float32)))
        """
    @bounding_box.setter
    def bounding_box(self, arg0: tuple[typing.Annotated[numpy.typing.ArrayLike, numpy.float32, "[3, 1]"], typing.Annotated[numpy.typing.ArrayLike, numpy.float32, "[3, 1]"]]) -> None:
        ...
    @property
    def cache_size(self) -> float:
        """
        Cache size in gigabytes for fusion. (float, default: 32.0)
        """
    @cache_size.setter
    def cache_size(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def check_num_images(self) -> int:
        """
        Number of overlapping images to transitively check for fusing points. (int, default: 50)
        """
    @check_num_images.setter
    def check_num_images(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def mask_path(self) -> str:
        """
        Path for PNG masks. Same format expected as ImageReaderOptions. (str, default: )
        """
    @mask_path.setter
    def mask_path(self, arg0: str) -> None:
        ...
    @property
    def max_depth_error(self) -> float:
        """
        Maximum relative difference between measured and projected depth. (float, default: 0.009999999776482582)
        """
    @max_depth_error.setter
    def max_depth_error(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def max_image_size(self) -> int:
        """
        Maximum image size in either dimension. (int, default: -1)
        """
    @max_image_size.setter
    def max_image_size(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def max_normal_error(self) -> float:
        """
        Maximum angular difference in degrees of normals of pixels to be fused. (float, default: 10.0)
        """
    @max_normal_error.setter
    def max_normal_error(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def max_num_pixels(self) -> int:
        """
        Maximum number of pixels to fuse into a single point. (int, default: 10000)
        """
    @max_num_pixels.setter
    def max_num_pixels(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def max_reproj_error(self) -> float:
        """
        Maximum relative difference between measured and projected pixel. (float, default: 2.0)
        """
    @max_reproj_error.setter
    def max_reproj_error(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def max_traversal_depth(self) -> int:
        """
        Maximum depth in consistency graph traversal. (int, default: 100)
        """
    @max_traversal_depth.setter
    def max_traversal_depth(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def min_num_pixels(self) -> int:
        """
        Minimum number of fused pixels to produce a point. (int, default: 5)
        """
    @min_num_pixels.setter
    def min_num_pixels(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def num_threads(self) -> int:
        """
        The number of threads to use during fusion. (int, default: -1)
        """
    @num_threads.setter
    def num_threads(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def use_cache(self) -> bool:
        """
        Flag indicating whether to use LRU cache or pre-load all data (bool, default: False)
        """
    @use_cache.setter
    def use_cache(self, arg0: bool) -> None:
        ...
class SyntheticDatasetMatchConfig:
    """
    Members:
    
      EXHAUSTIVE
    
      CHAINED
    """
    CHAINED: typing.ClassVar[SyntheticDatasetMatchConfig]  # value = SyntheticDatasetMatchConfig.CHAINED
    EXHAUSTIVE: typing.ClassVar[SyntheticDatasetMatchConfig]  # value = SyntheticDatasetMatchConfig.EXHAUSTIVE
    __members__: typing.ClassVar[dict[str, SyntheticDatasetMatchConfig]]  # value = {'EXHAUSTIVE': SyntheticDatasetMatchConfig.EXHAUSTIVE, 'CHAINED': SyntheticDatasetMatchConfig.CHAINED}
    @staticmethod
    def __repr__(*args, **kwargs):
        """
        __str__(self: object, /) -> str
        """
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __eq__(self, other: typing.Any) -> bool:
        ...
    def __getstate__(self) -> int:
        ...
    def __hash__(self) -> int:
        ...
    def __index__(self) -> int:
        ...
    @typing.overload
    def __init__(self, value: typing.SupportsInt) -> None:
        ...
    @typing.overload
    def __init__(self, name: str) -> None:
        ...
    def __int__(self) -> int:
        ...
    def __ne__(self, other: typing.Any) -> bool:
        ...
    def __setstate__(self, state: typing.SupportsInt) -> None:
        ...
    def __str__(self) -> str:
        ...
    @property
    def name(self) -> str:
        ...
    @property
    def value(self) -> int:
        ...
class SyntheticDatasetOptions:
    __hash__: typing.ClassVar[None] = None
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __copy__(self) -> SyntheticDatasetOptions:
        ...
    def __deepcopy__(self, arg0: dict) -> SyntheticDatasetOptions:
        ...
    def __eq__(self, arg0: typing.Any) -> bool:
        ...
    def __getstate__(self) -> dict:
        ...
    @typing.overload
    def __init__(self) -> None:
        ...
    @typing.overload
    def __init__(self, arg0: dict) -> None:
        ...
    @typing.overload
    def __init__(self, **kwargs) -> None:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, arg0: dict) -> None:
        ...
    def mergedict(self, kwargs: dict) -> None:
        ...
    def summary(self, write_type: bool = False) -> str:
        ...
    def todict(self, recursive: bool = True) -> dict:
        ...
    @property
    def camera_height(self) -> int:
        """
         (int, default: 768)
        """
    @camera_height.setter
    def camera_height(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def camera_model_id(self) -> CameraModelId:
        """
         (CameraModelId, default: CameraModelId.SIMPLE_RADIAL)
        """
    @camera_model_id.setter
    def camera_model_id(self, arg0: CameraModelId) -> None:
        ...
    @property
    def camera_params(self) -> list[float]:
        """
         (list, default: [1280.0, 512.0, 384.0, 0.05])
        """
    @camera_params.setter
    def camera_params(self, arg0: collections.abc.Sequence[typing.SupportsFloat]) -> None:
        ...
    @property
    def camera_width(self) -> int:
        """
         (int, default: 1024)
        """
    @camera_width.setter
    def camera_width(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def match_config(self) -> SyntheticDatasetMatchConfig:
        """
         (SyntheticDatasetMatchConfig, default: SyntheticDatasetMatchConfig.EXHAUSTIVE)
        """
    @match_config.setter
    def match_config(self, arg0: SyntheticDatasetMatchConfig) -> None:
        ...
    @property
    def num_cameras_per_rig(self) -> int:
        """
         (int, default: 1)
        """
    @num_cameras_per_rig.setter
    def num_cameras_per_rig(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def num_frames_per_rig(self) -> int:
        """
         (int, default: 5)
        """
    @num_frames_per_rig.setter
    def num_frames_per_rig(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def num_points2D_without_point3D(self) -> int:
        """
         (int, default: 10)
        """
    @num_points2D_without_point3D.setter
    def num_points2D_without_point3D(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def num_points3D(self) -> int:
        """
         (int, default: 100)
        """
    @num_points3D.setter
    def num_points3D(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def num_rigs(self) -> int:
        """
         (int, default: 2)
        """
    @num_rigs.setter
    def num_rigs(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def prior_position_stddev(self) -> float:
        """
         (float, default: 1.5)
        """
    @prior_position_stddev.setter
    def prior_position_stddev(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def sensor_from_rig_rotation_stddev(self) -> float:
        """
        Random rotation in degrees around the z-axis of the sensor. (float, default: 5.0)
        """
    @sensor_from_rig_rotation_stddev.setter
    def sensor_from_rig_rotation_stddev(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def sensor_from_rig_translation_stddev(self) -> float:
        """
         (float, default: 0.05)
        """
    @sensor_from_rig_translation_stddev.setter
    def sensor_from_rig_translation_stddev(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def use_geographic_coords_prior(self) -> bool:
        """
         (bool, default: False)
        """
    @use_geographic_coords_prior.setter
    def use_geographic_coords_prior(self, arg0: bool) -> None:
        ...
    @property
    def use_prior_position(self) -> bool:
        """
         (bool, default: False)
        """
    @use_prior_position.setter
    def use_prior_position(self, arg0: bool) -> None:
        ...
class SyntheticImageOptions:
    __hash__: typing.ClassVar[None] = None
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __copy__(self) -> SyntheticImageOptions:
        ...
    def __deepcopy__(self, arg0: dict) -> SyntheticImageOptions:
        ...
    def __eq__(self, arg0: typing.Any) -> bool:
        ...
    def __getstate__(self) -> dict:
        ...
    @typing.overload
    def __init__(self) -> None:
        ...
    @typing.overload
    def __init__(self, arg0: dict) -> None:
        ...
    @typing.overload
    def __init__(self, **kwargs) -> None:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, arg0: dict) -> None:
        ...
    def mergedict(self, kwargs: dict) -> None:
        ...
    def summary(self, write_type: bool = False) -> str:
        ...
    def todict(self, recursive: bool = True) -> dict:
        ...
    @property
    def feature_patch_max_brightness(self) -> int:
        """
         (int, default: 128)
        """
    @feature_patch_max_brightness.setter
    def feature_patch_max_brightness(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def feature_patch_radius(self) -> int:
        """
        Random rotation in degrees around the z-axis of the rig. (int, default: 15)
        """
    @feature_patch_radius.setter
    def feature_patch_radius(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def feature_peak_radius(self) -> int:
        """
         (int, default: 2)
        """
    @feature_peak_radius.setter
    def feature_peak_radius(self, arg0: typing.SupportsInt) -> None:
        ...
class SyntheticNoiseOptions:
    __hash__: typing.ClassVar[None] = None
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __copy__(self) -> SyntheticNoiseOptions:
        ...
    def __deepcopy__(self, arg0: dict) -> SyntheticNoiseOptions:
        ...
    def __eq__(self, arg0: typing.Any) -> bool:
        ...
    def __getstate__(self) -> dict:
        ...
    @typing.overload
    def __init__(self) -> None:
        ...
    @typing.overload
    def __init__(self, arg0: dict) -> None:
        ...
    @typing.overload
    def __init__(self, **kwargs) -> None:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, arg0: dict) -> None:
        ...
    def mergedict(self, kwargs: dict) -> None:
        ...
    def summary(self, write_type: bool = False) -> str:
        ...
    def todict(self, recursive: bool = True) -> dict:
        ...
    @property
    def point2D_stddev(self) -> float:
        """
         (float, default: 0.0)
        """
    @point2D_stddev.setter
    def point2D_stddev(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def point3D_stddev(self) -> float:
        """
         (float, default: 0.0)
        """
    @point3D_stddev.setter
    def point3D_stddev(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def rig_from_world_rotation_stddev(self) -> float:
        """
        Random rotation in degrees around the z-axis of the rig. (float, default: 0.0)
        """
    @rig_from_world_rotation_stddev.setter
    def rig_from_world_rotation_stddev(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def rig_from_world_translation_stddev(self) -> float:
        """
         (float, default: 0.0)
        """
    @rig_from_world_translation_stddev.setter
    def rig_from_world_translation_stddev(self, arg0: typing.SupportsFloat) -> None:
        ...
class Timer:
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __init__(self) -> None:
        ...
    def elapsed_hours(self) -> float:
        ...
    def elapsed_micro_seconds(self) -> float:
        ...
    def elapsed_minutes(self) -> float:
        ...
    def elapsed_seconds(self) -> float:
        ...
    def pause(self) -> None:
        ...
    def print_hours(self) -> None:
        ...
    def print_minutes(self) -> None:
        ...
    def print_seconds(self) -> None:
        ...
    def reset(self) -> None:
        ...
    def restart(self) -> None:
        ...
    def resume(self) -> None:
        ...
    def start(self) -> None:
        ...
class Track:
    __hash__: typing.ClassVar[None] = None
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __copy__(self) -> Track:
        ...
    def __deepcopy__(self, arg0: dict) -> Track:
        ...
    def __eq__(self, arg0: Track) -> bool:
        ...
    def __getstate__(self) -> dict:
        ...
    @typing.overload
    def __init__(self) -> None:
        ...
    @typing.overload
    def __init__(self, elements: collections.abc.Sequence[TrackElement]) -> None:
        ...
    @typing.overload
    def __init__(self, arg0: dict) -> None:
        ...
    @typing.overload
    def __init__(self, **kwargs) -> None:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, arg0: dict) -> None:
        ...
    @typing.overload
    def add_element(self, image_id: typing.SupportsInt, point2D_idx: typing.SupportsInt) -> None:
        """
        Add an observation to the track.
        """
    @typing.overload
    def add_element(self, element: TrackElement) -> None:
        ...
    def add_elements(self, elements: collections.abc.Sequence[TrackElement]) -> None:
        """
        Add multiple elements.
        """
    @typing.overload
    def delete_element(self, image_id: typing.SupportsInt, point2D_idx: typing.SupportsInt) -> None:
        """
        Delete observation from track.
        """
    @typing.overload
    def delete_element(self, index: typing.SupportsInt) -> None:
        """
        Remove TrackElement at index.
        """
    def length(self) -> int:
        """
        Track Length.
        """
    def mergedict(self, kwargs: dict) -> None:
        ...
    def summary(self, write_type: bool = False) -> str:
        ...
    def todict(self, recursive: bool = True) -> dict:
        ...
    @property
    def elements(self) -> list[TrackElement]:
        """
         (list, default: [])
        """
    @elements.setter
    def elements(self, arg1: collections.abc.Sequence[TrackElement]) -> None:
        ...
class TrackElement:
    __hash__: typing.ClassVar[None] = None
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __copy__(self) -> TrackElement:
        ...
    def __deepcopy__(self, arg0: dict) -> TrackElement:
        ...
    def __eq__(self, arg0: TrackElement) -> bool:
        ...
    def __getstate__(self) -> dict:
        ...
    @typing.overload
    def __init__(self) -> None:
        ...
    @typing.overload
    def __init__(self, image_id: typing.SupportsInt, point2D_idx: typing.SupportsInt) -> None:
        ...
    @typing.overload
    def __init__(self, arg0: dict) -> None:
        ...
    @typing.overload
    def __init__(self, **kwargs) -> None:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, arg0: dict) -> None:
        ...
    def mergedict(self, kwargs: dict) -> None:
        ...
    def summary(self, write_type: bool = False) -> str:
        ...
    def todict(self, recursive: bool = True) -> dict:
        ...
    @property
    def image_id(self) -> int:
        """
         (int, default: 4294967295)
        """
    @image_id.setter
    def image_id(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def point2D_idx(self) -> int:
        """
         (int, default: 4294967295)
        """
    @point2D_idx.setter
    def point2D_idx(self, arg0: typing.SupportsInt) -> None:
        ...
class TriangulationResidualType:
    """
    Members:
    
      ANGULAR_ERROR
    
      REPROJECTION_ERROR
    """
    ANGULAR_ERROR: typing.ClassVar[TriangulationResidualType]  # value = TriangulationResidualType.ANGULAR_ERROR
    REPROJECTION_ERROR: typing.ClassVar[TriangulationResidualType]  # value = TriangulationResidualType.REPROJECTION_ERROR
    __members__: typing.ClassVar[dict[str, TriangulationResidualType]]  # value = {'ANGULAR_ERROR': TriangulationResidualType.ANGULAR_ERROR, 'REPROJECTION_ERROR': TriangulationResidualType.REPROJECTION_ERROR}
    @staticmethod
    def __repr__(*args, **kwargs):
        """
        __str__(self: object, /) -> str
        """
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __eq__(self, other: typing.Any) -> bool:
        ...
    def __getstate__(self) -> int:
        ...
    def __hash__(self) -> int:
        ...
    def __index__(self) -> int:
        ...
    @typing.overload
    def __init__(self, value: typing.SupportsInt) -> None:
        ...
    @typing.overload
    def __init__(self, name: str) -> None:
        ...
    def __int__(self) -> int:
        ...
    def __ne__(self, other: typing.Any) -> bool:
        ...
    def __setstate__(self, state: typing.SupportsInt) -> None:
        ...
    def __str__(self) -> str:
        ...
    @property
    def name(self) -> str:
        ...
    @property
    def value(self) -> int:
        ...
class TwoViewGeometry:
    __hash__: typing.ClassVar[None] = None
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __copy__(self) -> TwoViewGeometry:
        ...
    def __deepcopy__(self, arg0: dict) -> TwoViewGeometry:
        ...
    def __eq__(self, arg0: typing.Any) -> bool:
        ...
    def __getstate__(self) -> dict:
        ...
    @typing.overload
    def __init__(self) -> None:
        ...
    @typing.overload
    def __init__(self, arg0: dict) -> None:
        ...
    @typing.overload
    def __init__(self, **kwargs) -> None:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, arg0: dict) -> None:
        ...
    def invert(self) -> None:
        ...
    def mergedict(self, kwargs: dict) -> None:
        ...
    def summary(self, write_type: bool = False) -> str:
        ...
    def todict(self, recursive: bool = True) -> dict:
        ...
    @property
    def E(self) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[3, 3]"]:
        """
         (ndarray, default: [[0. 0. 0.]
         [0. 0. 0.]
         [0. 0. 0.]])
        """
    @E.setter
    def E(self, arg0: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[3, 3]"]) -> None:
        ...
    @property
    def F(self) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[3, 3]"]:
        """
         (ndarray, default: [[0. 0. 0.]
         [0. 0. 0.]
         [0. 0. 0.]])
        """
    @F.setter
    def F(self, arg0: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[3, 3]"]) -> None:
        ...
    @property
    def H(self) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[3, 3]"]:
        """
         (ndarray, default: [[0. 0. 0.]
         [0. 0. 0.]
         [0. 0. 0.]])
        """
    @H.setter
    def H(self, arg0: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[3, 3]"]) -> None:
        ...
    @property
    def cam2_from_cam1(self) -> Rigid3d:
        """
         (Rigid3d, default: Rigid3d(rotation_xyzw=[0, 0, 0, 1], translation=[0, 0, 0]))
        """
    @cam2_from_cam1.setter
    def cam2_from_cam1(self, arg0: Rigid3d) -> None:
        ...
    @property
    def config(self) -> int:
        """
         (int, default: 0)
        """
    @config.setter
    def config(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def inlier_matches(self) -> typing.Annotated[numpy.typing.NDArray[numpy.uint32], "[m, 2]"]:
        """
         (ndarray, default: [])
        """
    @inlier_matches.setter
    def inlier_matches(self, arg1: typing.Annotated[numpy.typing.ArrayLike, numpy.uint32, "[m, 2]"]) -> None:
        ...
    @property
    def tri_angle(self) -> float:
        """
         (float, default: -1.0)
        """
    @tri_angle.setter
    def tri_angle(self, arg0: typing.SupportsFloat) -> None:
        ...
class TwoViewGeometryConfiguration:
    """
    Members:
    
      UNDEFINED
    
      DEGENERATE
    
      CALIBRATED
    
      CALIBRATED_RIG
    
      UNCALIBRATED
    
      PLANAR
    
      PANORAMIC
    
      PLANAR_OR_PANORAMIC
    
      WATERMARK
    
      MULTIPLE
    """
    CALIBRATED: typing.ClassVar[TwoViewGeometryConfiguration]  # value = TwoViewGeometryConfiguration.CALIBRATED
    CALIBRATED_RIG: typing.ClassVar[TwoViewGeometryConfiguration]  # value = TwoViewGeometryConfiguration.CALIBRATED_RIG
    DEGENERATE: typing.ClassVar[TwoViewGeometryConfiguration]  # value = TwoViewGeometryConfiguration.DEGENERATE
    MULTIPLE: typing.ClassVar[TwoViewGeometryConfiguration]  # value = TwoViewGeometryConfiguration.MULTIPLE
    PANORAMIC: typing.ClassVar[TwoViewGeometryConfiguration]  # value = TwoViewGeometryConfiguration.PANORAMIC
    PLANAR: typing.ClassVar[TwoViewGeometryConfiguration]  # value = TwoViewGeometryConfiguration.PLANAR
    PLANAR_OR_PANORAMIC: typing.ClassVar[TwoViewGeometryConfiguration]  # value = TwoViewGeometryConfiguration.PLANAR_OR_PANORAMIC
    UNCALIBRATED: typing.ClassVar[TwoViewGeometryConfiguration]  # value = TwoViewGeometryConfiguration.UNCALIBRATED
    UNDEFINED: typing.ClassVar[TwoViewGeometryConfiguration]  # value = TwoViewGeometryConfiguration.UNDEFINED
    WATERMARK: typing.ClassVar[TwoViewGeometryConfiguration]  # value = TwoViewGeometryConfiguration.WATERMARK
    __members__: typing.ClassVar[dict[str, TwoViewGeometryConfiguration]]  # value = {'UNDEFINED': TwoViewGeometryConfiguration.UNDEFINED, 'DEGENERATE': TwoViewGeometryConfiguration.DEGENERATE, 'CALIBRATED': TwoViewGeometryConfiguration.CALIBRATED, 'CALIBRATED_RIG': TwoViewGeometryConfiguration.CALIBRATED_RIG, 'UNCALIBRATED': TwoViewGeometryConfiguration.UNCALIBRATED, 'PLANAR': TwoViewGeometryConfiguration.PLANAR, 'PANORAMIC': TwoViewGeometryConfiguration.PANORAMIC, 'PLANAR_OR_PANORAMIC': TwoViewGeometryConfiguration.PLANAR_OR_PANORAMIC, 'WATERMARK': TwoViewGeometryConfiguration.WATERMARK, 'MULTIPLE': TwoViewGeometryConfiguration.MULTIPLE}
    @staticmethod
    def __repr__(*args, **kwargs):
        """
        __str__(self: object, /) -> str
        """
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __eq__(self, other: typing.Any) -> bool:
        ...
    def __getstate__(self) -> int:
        ...
    def __hash__(self) -> int:
        ...
    def __index__(self) -> int:
        ...
    @typing.overload
    def __init__(self, value: typing.SupportsInt) -> None:
        ...
    @typing.overload
    def __init__(self, name: str) -> None:
        ...
    def __int__(self) -> int:
        ...
    def __ne__(self, other: typing.Any) -> bool:
        ...
    def __setstate__(self, state: typing.SupportsInt) -> None:
        ...
    def __str__(self) -> str:
        ...
    @property
    def name(self) -> str:
        ...
    @property
    def value(self) -> int:
        ...
class TwoViewGeometryOptions:
    __hash__: typing.ClassVar[None] = None
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __copy__(self) -> TwoViewGeometryOptions:
        ...
    def __deepcopy__(self, arg0: dict) -> TwoViewGeometryOptions:
        ...
    def __eq__(self, arg0: typing.Any) -> bool:
        ...
    def __getstate__(self) -> dict:
        ...
    @typing.overload
    def __init__(self) -> None:
        ...
    @typing.overload
    def __init__(self, arg0: dict) -> None:
        ...
    @typing.overload
    def __init__(self, **kwargs) -> None:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, arg0: dict) -> None:
        ...
    def mergedict(self, kwargs: dict) -> None:
        ...
    def summary(self, write_type: bool = False) -> str:
        ...
    def todict(self, recursive: bool = True) -> dict:
        ...
    @property
    def compute_relative_pose(self) -> bool:
        """
         (bool, default: False)
        """
    @compute_relative_pose.setter
    def compute_relative_pose(self, arg0: bool) -> None:
        ...
    @property
    def detect_watermark(self) -> bool:
        """
         (bool, default: True)
        """
    @detect_watermark.setter
    def detect_watermark(self, arg0: bool) -> None:
        ...
    @property
    def filter_stationary_matches(self) -> bool:
        """
         (bool, default: False)
        """
    @filter_stationary_matches.setter
    def filter_stationary_matches(self, arg0: bool) -> None:
        ...
    @property
    def force_H_use(self) -> bool:
        """
         (bool, default: False)
        """
    @force_H_use.setter
    def force_H_use(self, arg0: bool) -> None:
        ...
    @property
    def max_H_inlier_ratio(self) -> float:
        """
         (float, default: 0.8)
        """
    @max_H_inlier_ratio.setter
    def max_H_inlier_ratio(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def min_E_F_inlier_ratio(self) -> float:
        """
         (float, default: 0.95)
        """
    @min_E_F_inlier_ratio.setter
    def min_E_F_inlier_ratio(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def min_num_inliers(self) -> int:
        """
         (int, default: 15)
        """
    @min_num_inliers.setter
    def min_num_inliers(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def multiple_ignore_watermark(self) -> bool:
        """
         (bool, default: True)
        """
    @multiple_ignore_watermark.setter
    def multiple_ignore_watermark(self, arg0: bool) -> None:
        ...
    @property
    def multiple_models(self) -> bool:
        """
         (bool, default: False)
        """
    @multiple_models.setter
    def multiple_models(self, arg0: bool) -> None:
        ...
    @property
    def ransac(self) -> RANSACOptions:
        """
         (RANSACOptions, default: RANSACOptions(max_error=4.0, min_inlier_ratio=0.25, confidence=0.999, dyn_num_trials_multiplier=3.0, min_num_trials=100, max_num_trials=10000, random_seed=-1))
        """
    @ransac.setter
    def ransac(self, arg0: RANSACOptions) -> None:
        ...
    @property
    def stationary_matches_max_error(self) -> float:
        """
         (float, default: 4.0)
        """
    @stationary_matches_max_error.setter
    def stationary_matches_max_error(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def watermark_border_size(self) -> float:
        """
         (float, default: 0.1)
        """
    @watermark_border_size.setter
    def watermark_border_size(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def watermark_detection_max_error(self) -> float:
        """
         (float, default: 4.0)
        """
    @watermark_detection_max_error.setter
    def watermark_detection_max_error(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def watermark_min_inlier_ratio(self) -> float:
        """
         (float, default: 0.7)
        """
    @watermark_min_inlier_ratio.setter
    def watermark_min_inlier_ratio(self, arg0: typing.SupportsFloat) -> None:
        ...
class UndistortCameraOptions:
    __hash__: typing.ClassVar[None] = None
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __copy__(self) -> UndistortCameraOptions:
        ...
    def __deepcopy__(self, arg0: dict) -> UndistortCameraOptions:
        ...
    def __eq__(self, arg0: typing.Any) -> bool:
        ...
    def __getstate__(self) -> dict:
        ...
    @typing.overload
    def __init__(self) -> None:
        ...
    @typing.overload
    def __init__(self, arg0: dict) -> None:
        ...
    @typing.overload
    def __init__(self, **kwargs) -> None:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, arg0: dict) -> None:
        ...
    def mergedict(self, kwargs: dict) -> None:
        ...
    def summary(self, write_type: bool = False) -> str:
        ...
    def todict(self, recursive: bool = True) -> dict:
        ...
    @property
    def blank_pixels(self) -> float:
        """
         (float, default: 0.0)
        """
    @blank_pixels.setter
    def blank_pixels(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def max_image_size(self) -> int:
        """
         (int, default: -1)
        """
    @max_image_size.setter
    def max_image_size(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def max_scale(self) -> float:
        """
         (float, default: 2.0)
        """
    @max_scale.setter
    def max_scale(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def min_scale(self) -> float:
        """
         (float, default: 0.2)
        """
    @min_scale.setter
    def min_scale(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def roi_max_x(self) -> float:
        """
         (float, default: 1.0)
        """
    @roi_max_x.setter
    def roi_max_x(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def roi_max_y(self) -> float:
        """
         (float, default: 1.0)
        """
    @roi_max_y.setter
    def roi_max_y(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def roi_min_x(self) -> float:
        """
         (float, default: 0.0)
        """
    @roi_min_x.setter
    def roi_min_x(self, arg0: typing.SupportsFloat) -> None:
        ...
    @property
    def roi_min_y(self) -> float:
        """
         (float, default: 0.0)
        """
    @roi_min_y.setter
    def roi_min_y(self, arg0: typing.SupportsFloat) -> None:
        ...
class VisualIndex:
    class BuildOptions:
        __hash__: typing.ClassVar[None] = None
        @staticmethod
        def _pybind11_conduit_v1_(*args, **kwargs):
            ...
        def __copy__(self) -> VisualIndex.BuildOptions:
            ...
        def __deepcopy__(self, arg0: dict) -> VisualIndex.BuildOptions:
            ...
        def __eq__(self, arg0: typing.Any) -> bool:
            ...
        def __getstate__(self) -> dict:
            ...
        @typing.overload
        def __init__(self) -> None:
            ...
        @typing.overload
        def __init__(self, arg0: dict) -> None:
            ...
        @typing.overload
        def __init__(self, **kwargs) -> None:
            ...
        def __repr__(self) -> str:
            ...
        def __setstate__(self, arg0: dict) -> None:
            ...
        def mergedict(self, kwargs: dict) -> None:
            ...
        def summary(self, write_type: bool = False) -> str:
            ...
        def todict(self, recursive: bool = True) -> dict:
            ...
        @property
        def num_checks(self) -> int:
            """
             (int, default: 256)
            """
        @num_checks.setter
        def num_checks(self, arg0: typing.SupportsInt) -> None:
            ...
        @property
        def num_iterations(self) -> int:
            """
             (int, default: 100)
            """
        @num_iterations.setter
        def num_iterations(self, arg0: typing.SupportsInt) -> None:
            ...
        @property
        def num_rounds(self) -> int:
            """
             (int, default: 3)
            """
        @num_rounds.setter
        def num_rounds(self, arg0: typing.SupportsInt) -> None:
            ...
        @property
        def num_threads(self) -> int:
            """
             (int, default: -1)
            """
        @num_threads.setter
        def num_threads(self, arg0: typing.SupportsInt) -> None:
            ...
        @property
        def num_visual_words(self) -> int:
            """
             (int, default: 65536)
            """
        @num_visual_words.setter
        def num_visual_words(self, arg0: typing.SupportsInt) -> None:
            ...
    class IndexOptions:
        __hash__: typing.ClassVar[None] = None
        @staticmethod
        def _pybind11_conduit_v1_(*args, **kwargs):
            ...
        def __copy__(self) -> VisualIndex.IndexOptions:
            ...
        def __deepcopy__(self, arg0: dict) -> VisualIndex.IndexOptions:
            ...
        def __eq__(self, arg0: typing.Any) -> bool:
            ...
        def __getstate__(self) -> dict:
            ...
        @typing.overload
        def __init__(self) -> None:
            ...
        @typing.overload
        def __init__(self, arg0: dict) -> None:
            ...
        @typing.overload
        def __init__(self, **kwargs) -> None:
            ...
        def __repr__(self) -> str:
            ...
        def __setstate__(self, arg0: dict) -> None:
            ...
        def mergedict(self, kwargs: dict) -> None:
            ...
        def summary(self, write_type: bool = False) -> str:
            ...
        def todict(self, recursive: bool = True) -> dict:
            ...
        @property
        def num_checks(self) -> int:
            """
             (int, default: 64)
            """
        @num_checks.setter
        def num_checks(self, arg0: typing.SupportsInt) -> None:
            ...
        @property
        def num_neighbors(self) -> int:
            """
             (int, default: 1)
            """
        @num_neighbors.setter
        def num_neighbors(self, arg0: typing.SupportsInt) -> None:
            ...
        @property
        def num_threads(self) -> int:
            """
             (int, default: -1)
            """
        @num_threads.setter
        def num_threads(self, arg0: typing.SupportsInt) -> None:
            ...
    class QueryOptions:
        __hash__: typing.ClassVar[None] = None
        @staticmethod
        def _pybind11_conduit_v1_(*args, **kwargs):
            ...
        def __copy__(self) -> VisualIndex.QueryOptions:
            ...
        def __deepcopy__(self, arg0: dict) -> VisualIndex.QueryOptions:
            ...
        def __eq__(self, arg0: typing.Any) -> bool:
            ...
        def __getstate__(self) -> dict:
            ...
        @typing.overload
        def __init__(self) -> None:
            ...
        @typing.overload
        def __init__(self, arg0: dict) -> None:
            ...
        @typing.overload
        def __init__(self, **kwargs) -> None:
            ...
        def __repr__(self) -> str:
            ...
        def __setstate__(self, arg0: dict) -> None:
            ...
        def mergedict(self, kwargs: dict) -> None:
            ...
        def summary(self, write_type: bool = False) -> str:
            ...
        def todict(self, recursive: bool = True) -> dict:
            ...
        @property
        def max_num_images(self) -> int:
            """
             (int, default: -1)
            """
        @max_num_images.setter
        def max_num_images(self, arg0: typing.SupportsInt) -> None:
            ...
        @property
        def num_checks(self) -> int:
            """
             (int, default: 64)
            """
        @num_checks.setter
        def num_checks(self, arg0: typing.SupportsInt) -> None:
            ...
        @property
        def num_images_after_verification(self) -> int:
            """
             (int, default: 0)
            """
        @num_images_after_verification.setter
        def num_images_after_verification(self, arg0: typing.SupportsInt) -> None:
            ...
        @property
        def num_neighbors(self) -> int:
            """
             (int, default: 5)
            """
        @num_neighbors.setter
        def num_neighbors(self, arg0: typing.SupportsInt) -> None:
            ...
        @property
        def num_threads(self) -> int:
            """
             (int, default: -1)
            """
        @num_threads.setter
        def num_threads(self, arg0: typing.SupportsInt) -> None:
            ...
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    @staticmethod
    def create(arg0: typing.SupportsInt, arg1: typing.SupportsInt) -> VisualIndex:
        ...
    @staticmethod
    def read(arg0: str) -> VisualIndex:
        ...
    def __init__(self) -> None:
        ...
    def __repr__(self) -> str:
        ...
    def add(self, arg0: VisualIndex.IndexOptions, arg1: typing.SupportsInt, arg2: collections.abc.Sequence[FeatureKeypoint], arg3: typing.Annotated[numpy.typing.ArrayLike, numpy.float32, "[m, n]"]) -> None:
        ...
    def build(self, arg0: VisualIndex.BuildOptions, arg1: typing.Annotated[numpy.typing.ArrayLike, numpy.float32, "[m, n]"]) -> None:
        ...
    def desc_dim(self) -> int:
        ...
    def embedding_dim(self) -> int:
        ...
    def is_image_indexed(self, arg0: typing.SupportsInt) -> bool:
        ...
    def num_images(self) -> int:
        ...
    def num_visual_words(self) -> int:
        ...
    def prepare(self) -> None:
        ...
    @typing.overload
    def query(self, arg0: VisualIndex.QueryOptions, arg1: typing.Annotated[numpy.typing.ArrayLike, numpy.float32, "[m, n]"], arg2: collections.abc.Sequence[ImageScore]) -> None:
        ...
    @typing.overload
    def query(self, arg0: VisualIndex.QueryOptions, arg1: collections.abc.Sequence[FeatureKeypoint], arg2: typing.Annotated[numpy.typing.ArrayLike, numpy.float32, "[m, n]"], arg3: collections.abc.Sequence[ImageScore]) -> None:
        ...
    def write(self, arg0: str) -> None:
        ...
class VocabTreePairGenerator(PairGenerator):
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __init__(self, options: VocabTreePairingOptions, database: Database, query_image_ids: collections.abc.Sequence[typing.SupportsInt] = []) -> None:
        ...
class VocabTreePairingOptions:
    __hash__: typing.ClassVar[None] = None
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __copy__(self) -> VocabTreePairingOptions:
        ...
    def __deepcopy__(self, arg0: dict) -> VocabTreePairingOptions:
        ...
    def __eq__(self, arg0: typing.Any) -> bool:
        ...
    def __getstate__(self) -> dict:
        ...
    @typing.overload
    def __init__(self) -> None:
        ...
    @typing.overload
    def __init__(self, arg0: dict) -> None:
        ...
    @typing.overload
    def __init__(self, **kwargs) -> None:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, arg0: dict) -> None:
        ...
    def check(self) -> bool:
        ...
    def mergedict(self, kwargs: dict) -> None:
        ...
    def summary(self, write_type: bool = False) -> str:
        ...
    def todict(self, recursive: bool = True) -> dict:
        ...
    @property
    def match_list_path(self) -> str:
        """
        Optional path to file with specific image names to match. (str, default: )
        """
    @match_list_path.setter
    def match_list_path(self, arg0: str) -> None:
        ...
    @property
    def max_num_features(self) -> int:
        """
        The maximum number of features to use for indexing an image. (int, default: -1)
        """
    @max_num_features.setter
    def max_num_features(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def num_checks(self) -> int:
        """
        Number of nearest-neighbor checks to use in retrieval. (int, default: 64)
        """
    @num_checks.setter
    def num_checks(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def num_images(self) -> int:
        """
        Number of images to retrieve for each query image. (int, default: 100)
        """
    @num_images.setter
    def num_images(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def num_images_after_verification(self) -> int:
        """
        How many images to return after spatial verification. Set to 0 to turn off spatial verification. (int, default: 0)
        """
    @num_images_after_verification.setter
    def num_images_after_verification(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def num_nearest_neighbors(self) -> int:
        """
        Number of nearest neighbors to retrieve per query feature. (int, default: 5)
        """
    @num_nearest_neighbors.setter
    def num_nearest_neighbors(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def num_threads(self) -> int:
        """
         (int, default: -1)
        """
    @num_threads.setter
    def num_threads(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def vocab_tree_path(self) -> str:
        """
        Path to the vocabulary tree. (str, default: https://github.com/colmap/colmap/releases/download/3.11.1/vocab_tree_faiss_flickr100K_words256K.bin;vocab_tree_faiss_flickr100K_words256K.bin;96ca8ec8ea60b1f73465aaf2c401fd3b3ca75cdba2d3c50d6a2f6f760f275ddc)
        """
    @vocab_tree_path.setter
    def vocab_tree_path(self, arg0: str) -> None:
        ...
class data_t:
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __copy__(self) -> data_t:
        ...
    def __deepcopy__(self, arg0: dict) -> data_t:
        ...
    def __eq__(self, arg0: data_t) -> bool:
        ...
    def __getstate__(self) -> dict:
        ...
    def __hash__(self) -> int:
        ...
    @typing.overload
    def __init__(self) -> None:
        ...
    @typing.overload
    def __init__(self, arg0: dict) -> None:
        ...
    @typing.overload
    def __init__(self, **kwargs) -> None:
        ...
    def __lt__(self, arg0: data_t) -> bool:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, arg0: dict) -> None:
        ...
    def mergedict(self, kwargs: dict) -> None:
        ...
    def summary(self, write_type: bool = False) -> str:
        ...
    def todict(self, recursive: bool = True) -> dict:
        ...
    @property
    def id(self) -> int:
        """
         (int, default: 4294967295)
        """
    @id.setter
    def id(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def sensor_id(self) -> sensor_t:
        """
         (sensor_t, default: sensor_t(type=SensorType.INVALID, id=4294967295))
        """
    @sensor_id.setter
    def sensor_id(self, arg0: sensor_t) -> None:
        ...
class logging:
    class Level:
        """
        Members:
        
          INFO
        
          WARNING
        
          ERROR
        
          FATAL
        """
        ERROR: typing.ClassVar[logging.Level]  # value = <Level.ERROR: 2>
        FATAL: typing.ClassVar[logging.Level]  # value = <Level.FATAL: 3>
        INFO: typing.ClassVar[logging.Level]  # value = <Level.INFO: 0>
        WARNING: typing.ClassVar[logging.Level]  # value = <Level.WARNING: 1>
        __members__: typing.ClassVar[dict[str, logging.Level]]  # value = {'INFO': <Level.INFO: 0>, 'WARNING': <Level.WARNING: 1>, 'ERROR': <Level.ERROR: 2>, 'FATAL': <Level.FATAL: 3>}
        @staticmethod
        def _pybind11_conduit_v1_(*args, **kwargs):
            ...
        def __eq__(self, other: typing.Any) -> bool:
            ...
        def __getstate__(self) -> int:
            ...
        def __hash__(self) -> int:
            ...
        def __index__(self) -> int:
            ...
        def __init__(self, value: typing.SupportsInt) -> None:
            ...
        def __int__(self) -> int:
            ...
        def __ne__(self, other: typing.Any) -> bool:
            ...
        def __repr__(self) -> str:
            ...
        def __setstate__(self, state: typing.SupportsInt) -> None:
            ...
        def __str__(self) -> str:
            ...
        @property
        def name(self) -> str:
            ...
        @property
        def value(self) -> int:
            ...
    ERROR: typing.ClassVar[logging.Level]  # value = <Level.ERROR: 2>
    FATAL: typing.ClassVar[logging.Level]  # value = <Level.FATAL: 3>
    INFO: typing.ClassVar[logging.Level]  # value = <Level.INFO: 0>
    WARNING: typing.ClassVar[logging.Level]  # value = <Level.WARNING: 1>
    alsologtostderr: typing.ClassVar[bool] = True
    log_dir: typing.ClassVar[str] = ''
    logtostderr: typing.ClassVar[bool] = False
    minloglevel: typing.ClassVar[int] = 0
    stderrthreshold: typing.ClassVar[int] = 2
    verbose_level: typing.ClassVar[int] = 0
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    @staticmethod
    def error(message: str) -> None:
        ...
    @staticmethod
    def fatal(message: str) -> None:
        ...
    @staticmethod
    def info(message: str) -> None:
        ...
    @staticmethod
    def set_log_destination(level: logging.Level, path: str) -> None:
        ...
    @staticmethod
    def verbose(level: typing.SupportsInt, message: str) -> None:
        ...
    @staticmethod
    def warning(message: str) -> None:
        ...
class ostream:
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __enter__(self) -> None:
        ...
    def __exit__(self, *args) -> None:
        ...
    def __init__(self, stdout: bool = True, stderr: bool = True) -> None:
        ...
class sensor_t:
    @staticmethod
    def _pybind11_conduit_v1_(*args, **kwargs):
        ...
    def __copy__(self) -> sensor_t:
        ...
    def __deepcopy__(self, arg0: dict) -> sensor_t:
        ...
    def __eq__(self, arg0: sensor_t) -> bool:
        ...
    def __getstate__(self) -> dict:
        ...
    def __hash__(self) -> int:
        ...
    @typing.overload
    def __init__(self) -> None:
        ...
    @typing.overload
    def __init__(self, arg0: dict) -> None:
        ...
    @typing.overload
    def __init__(self, **kwargs) -> None:
        ...
    def __lt__(self, arg0: sensor_t) -> bool:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, arg0: dict) -> None:
        ...
    def mergedict(self, kwargs: dict) -> None:
        ...
    def summary(self, write_type: bool = False) -> str:
        ...
    def todict(self, recursive: bool = True) -> dict:
        ...
    @property
    def id(self) -> int:
        """
         (int, default: 4294967295)
        """
    @id.setter
    def id(self, arg0: typing.SupportsInt) -> None:
        ...
    @property
    def type(self) -> SensorType:
        """
         (SensorType, default: SensorType.INVALID)
        """
    @type.setter
    def type(self, arg0: SensorType) -> None:
        ...
def CalculateTriangulationAngle(*args, **kwargs) -> typing.Any:
    """
    Deprecated, use ``calculate_triangulation_angle`` instead.
    """
def TriangulatePoint(*args, **kwargs) -> typing.Any:
    """
    Deprecated, use ``triangulate_point`` instead.
    """
def absolute_pose_estimation(*args, **kwargs) -> typing.Any:
    """
    Deprecated, use ``estimate_and_refine_absolute_pose`` instead.
    """
def align_reconstruction_to_locations(src: Reconstruction, tgt_image_names: collections.abc.Sequence[str], tgt_locations: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[m, 3]"], min_common_images: typing.SupportsInt, ransac_options: RANSACOptions) -> pycolmap._core.Sim3d | None:
    ...
def align_reconstruction_to_orig_rig_scales(orig_rigs: collections.abc.Mapping[typing.SupportsInt, Rig], reconstruction: Reconstruction) -> bool:
    ...
def align_reconstructions_via_points(src_reconstruction: Reconstruction, tgt_reconstruction: Reconstruction, min_common_observations: typing.SupportsInt = 3, max_error: typing.SupportsFloat = 0.005, min_inlier_ratio: typing.SupportsFloat = 0.9) -> pycolmap._core.Sim3d | None:
    ...
def align_reconstructions_via_proj_centers(src_reconstruction: Reconstruction, tgt_reconstruction: Reconstruction, max_proj_center_error: typing.SupportsFloat) -> pycolmap._core.Sim3d | None:
    ...
def align_reconstructions_via_reprojections(src_reconstruction: Reconstruction, tgt_reconstruction: Reconstruction, min_inlier_observations: typing.SupportsFloat = 0.3, max_reproj_error: typing.SupportsFloat = 8.0) -> pycolmap._core.Sim3d | None:
    ...
def apply_rig_config(configs: collections.abc.Sequence[RigConfig], database: Database, reconstruction: Reconstruction = None) -> None:
    """
    Applies the given rig configuration to the database and optionally derives camera rig extrinsics and intrinsics from the reconstruction, if not defined in the config. If the reconstruction is provided, it is also updated with the provided config and any previous rigs/frames are cleared and overwritten.
    """
def average_quaternions(quats: collections.abc.Sequence[Rotation3d], weights: collections.abc.Sequence[typing.SupportsFloat]) -> Rotation3d:
    ...
def bundle_adjustment(reconstruction: Reconstruction, options: BundleAdjustmentOptions = ...) -> None:
    """
    Jointly refine 3D points and camera poses
    """
def calculate_triangulation_angle(proj_center1: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[3, 1]"], proj_center2: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[3, 1]"], point3D: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[3, 1]"]) -> float:
    """
    Calculate triangulation angle in radians.
    """
def compare_reconstructions(reconstruction1: Reconstruction, reconstruction2: Reconstruction, alignment_error: str = 'reprojection', min_inlier_observations: typing.SupportsFloat = 0.3, max_reproj_error: typing.SupportsFloat = 8.0, max_proj_center_error: typing.SupportsFloat = 0.1) -> dict | None:
    ...
def compute_squared_sampson_error(points2D1: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[m, 2]"], points2D2: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[m, 2]"], E: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[3, 3]"]) -> list[float]:
    """
    Calculate the squared Sampson error for a given essential or fundamental matrix.
    """
def create_default_bundle_adjuster(options: BundleAdjustmentOptions, config: BundleAdjustmentConfig, reconstruction: Reconstruction) -> BundleAdjuster:
    ...
def create_pose_prior_bundle_adjuster(options: BundleAdjustmentOptions, prior_options: PosePriorBundleAdjustmentOptions, config: BundleAdjustmentConfig, pose_priors: collections.abc.Mapping[typing.SupportsInt, PosePrior], reconstruction: Reconstruction) -> BundleAdjuster:
    ...
def essential_matrix_estimation(*args, **kwargs) -> typing.Any:
    """
    Deprecated, use ``estimate_essential_matrix`` instead.
    """
def essential_matrix_from_pose(cam2_from_cam1: Rigid3d) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[3, 3]"]:
    """
    Construct essential matrix from relative pose.
    """
def estimate_absolute_pose(points2D: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[m, 2]"], points3D: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[m, 3]"], camera: Camera, estimation_options: AbsolutePoseEstimationOptions = ...) -> dict | None:
    """
    Robustly estimate absolute pose using LO-RANSAC without non-linear refinement.
    """
def estimate_affine2d(src: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[m, 2]"], tgt: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[m, 2]"]) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[2, 3]"] | None:
    """
    Estimate the 2D affine transform tgt_from_src.
    """
def estimate_affine2d_robust(src: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[m, 2]"], tgt: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[m, 2]"], estimation_options: RANSACOptions = ...) -> dict | None:
    """
    Robustly estimate the 2D affine transform tgt_from_src using LO-RANSAC.
    """
def estimate_and_refine_absolute_pose(points2D: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[m, 2]"], points3D: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[m, 3]"], camera: Camera, estimation_options: AbsolutePoseEstimationOptions = ..., refinement_options: AbsolutePoseRefinementOptions = ..., return_covariance: bool = False) -> dict | None:
    """
    Robust absolute pose estimation with LO-RANSAC followed by non-linear refinement.
    """
def estimate_and_refine_generalized_absolute_pose(points2D: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[m, 2]"], points3D: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[m, 3]"], camera_idxs: collections.abc.Sequence[typing.SupportsInt], cams_from_rig: collections.abc.Sequence[Rigid3d], cameras: collections.abc.Sequence[Camera], estimation_options: RANSACOptions = ..., refinement_options: AbsolutePoseRefinementOptions = ..., return_covariance: bool = False) -> dict | None:
    """
    Robustly estimate generalized absolute pose using LO-RANSACfollowed by non-linear refinement.
    """
def estimate_ba_covariance(options: BACovarianceOptions, reconstruction: Reconstruction, bundle_adjuster: BundleAdjuster) -> pycolmap._core.BACovariance | None:
    """
    Computes covariances for the parameters in a bundle adjustment problem. It is important that the problem has a structure suitable for solving using the Schur complement trick. This is the case for the standard configuration of bundle adjustment problems, but be careful if you modify the underlying problem with custom residuals. Returns null if the estimation was not successful.
    """
def estimate_ba_covariance_from_problem(options: BACovarianceOptions, reconstruction: Reconstruction, problem: ...) -> pycolmap._core.BACovariance | None:
    """
    Computes covariances for the parameters in a bundle adjustment problem. It is important that the problem has a structure suitable for solving using the Schur complement trick. This is the case for the standard configuration of bundle adjustment problems, but be careful if you modify the underlying problem with custom residuals. Returns null if the estimation was not successful.
    """
def estimate_calibrated_two_view_geometry(camera1: Camera, points1: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[m, 2]"], camera2: Camera, points2: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[m, 2]"], matches: typing.Annotated[numpy.typing.ArrayLike, numpy.uint32, "[m, 2]"] = None, options: TwoViewGeometryOptions = ...) -> TwoViewGeometry:
    ...
def estimate_essential_matrix(points2D1: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[m, 2]"], points2D2: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[m, 2]"], camera1: Camera, camera2: Camera, estimation_options: RANSACOptions = ...) -> dict | None:
    """
    Robustly estimate essential matrix with LO-RANSAC and decompose it using the cheirality check.
    """
def estimate_fundamental_matrix(points2D1: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[m, 2]"], points2D2: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[m, 2]"], estimation_options: RANSACOptions = ...) -> dict | None:
    """
    Robustly estimate fundamental matrix with LO-RANSAC.
    """
def estimate_generalized_absolute_pose(points2D: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[m, 2]"], points3D: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[m, 3]"], camera_idxs: collections.abc.Sequence[typing.SupportsInt], cams_from_rig: collections.abc.Sequence[Rigid3d], cameras: collections.abc.Sequence[Camera], estimation_options: RANSACOptions = ...) -> dict | None:
    ...
def estimate_generalized_relative_pose(points2D1: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[m, 2]"], points2D2: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[m, 2]"], camera_idxs1: collections.abc.Sequence[typing.SupportsInt], camera_idxs2: collections.abc.Sequence[typing.SupportsInt], cams_from_rig: collections.abc.Sequence[Rigid3d], cameras: collections.abc.Sequence[Camera], estimation_options: RANSACOptions = ...) -> dict | None:
    ...
def estimate_homography_matrix(points2D1: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[m, 2]"], points2D2: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[m, 2]"], estimation_options: RANSACOptions = ...) -> dict | None:
    """
    Robustly estimate homography matrix using LO-RANSAC.
    """
def estimate_relative_pose(cam_rays1: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[m, 3]"], cam_rays2: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[m, 3]"], options: RANSACOptions = ...) -> dict | None:
    """
    Robustly estimate relative pose using LO-RANSAC without non-linear refinement.
    """
def estimate_rigid3d(src: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[m, 3]"], tgt: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[m, 3]"]) -> pycolmap._core.Rigid3d | None:
    """
    Estimate the 3D rigid transform tgt_from_src.
    """
def estimate_rigid3d_robust(src: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[m, 3]"], tgt: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[m, 3]"], estimation_options: RANSACOptions = ...) -> pycolmap._core.Rigid3d | None:
    """
    Robustly estimate the 3D rigid transform tgt_from_src using LO-RANSAC.
    """
def estimate_sim3d(src: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[m, 3]"], tgt: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[m, 3]"]) -> pycolmap._core.Sim3d | None:
    """
    Estimate the 3D similarity transform tgt_from_src.
    """
def estimate_sim3d_robust(src: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[m, 3]"], tgt: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[m, 3]"], estimation_options: RANSACOptions = ...) -> pycolmap._core.Sim3d | None:
    """
    Robustly estimate the 3D similarity transform tgt_from_src using LO-RANSAC.
    """
def estimate_triangulation(points: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[m, 2]"], cams_from_world: collections.abc.Sequence[Rigid3d], cameras: collections.abc.Sequence[Camera], options: EstimateTriangulationOptions = ...) -> dict | None:
    """
    Robustly estimate 3D point from observations in multiple views using LO-RANSAC
    """
def estimate_two_view_geometry(camera1: Camera, points1: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[m, 2]"], camera2: Camera, points2: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[m, 2]"], matches: typing.Annotated[numpy.typing.ArrayLike, numpy.uint32, "[m, 2]"] = None, options: TwoViewGeometryOptions = ...) -> TwoViewGeometry:
    ...
def estimate_two_view_geometry_pose(camera1: Camera, points1: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[m, 2]"], camera2: Camera, points2: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[m, 2]"], geometry: TwoViewGeometry) -> bool:
    ...
def extract_features(database_path: str, image_path: str, image_names: collections.abc.Sequence[str] = [], camera_mode: CameraMode = ..., camera_model: str = 'SIMPLE_RADIAL', reader_options: ImageReaderOptions = ..., extraction_options: FeatureExtractionOptions = ..., device: Device = ...) -> None:
    """
    Extract SIFT Features and write them to database
    """
def fundamental_matrix_estimation(*args, **kwargs) -> typing.Any:
    """
    Deprecated, use ``estimate_fundamental_matrix`` instead.
    """
def get_covariance_for_composed_rigid3d(left_rigid3d: Rigid3d, joint_covar: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[12, 12]"]) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[6, 6]"]:
    ...
def get_covariance_for_inverse(rigid3d: Rigid3d, covar: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[6, 6]"]) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[6, 6]"]:
    ...
def get_covariance_for_relative_rigid3d(base_rigid3d: Rigid3d, target_rigid3d: Rigid3d, joint_covar: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[12, 12]"]) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[6, 6]"]:
    ...
def homography_decomposition(*args, **kwargs) -> typing.Any:
    """
    Deprecated, use ``pose_from_homography_matrix`` instead.
    """
def homography_matrix_estimation(*args, **kwargs) -> typing.Any:
    """
    Deprecated, use ``estimate_homography_matrix`` instead.
    """
def image_pair_to_pair_id(image_id1: typing.SupportsInt, image_id2: typing.SupportsInt) -> int:
    ...
def import_images(database_path: str, image_path: str, camera_mode: CameraMode = ..., image_names: collections.abc.Sequence[str] = [], options: ImageReaderOptions = ...) -> None:
    """
    Import images into a database
    """
def incremental_mapping(database_path: str, image_path: str, output_path: str, options: IncrementalPipelineOptions = ..., input_path: str = '', initial_image_pair_callback: collections.abc.Callable[[], None] = None, next_image_callback: collections.abc.Callable[[], None] = None) -> dict[int, Reconstruction]:
    """
    Recover 3D points and unknown camera poses
    """
def infer_camera_from_image(image_path: str, options: ImageReaderOptions = ...) -> Camera:
    """
    Guess the camera parameters from the EXIF metadata
    """
def interpolate_camera_poses(cam1_from_world: Rigid3d, cam2_from_world: Rigid3d, t: typing.SupportsFloat) -> Rigid3d:
    ...
def match_exhaustive(database_path: str, matching_options: FeatureMatchingOptions = ..., pairing_options: ExhaustivePairingOptions = ..., verification_options: TwoViewGeometryOptions = ..., device: Device = ...) -> None:
    """
    Exhaustive feature matching
    """
def match_sequential(database_path: str, matching_options: FeatureMatchingOptions = ..., pairing_options: SequentialPairingOptions = ..., verification_options: TwoViewGeometryOptions = ..., device: Device = ...) -> None:
    """
    Sequential feature matching
    """
def match_spatial(database_path: str, matching_options: FeatureMatchingOptions = ..., pairing_options: SpatialPairingOptions = ..., verification_options: TwoViewGeometryOptions = ..., device: Device = ...) -> None:
    """
    Spatial feature matching
    """
def match_vocabtree(database_path: str, matching_options: FeatureMatchingOptions = ..., pairing_options: VocabTreePairingOptions = ..., verification_options: TwoViewGeometryOptions = ..., device: Device = ...) -> None:
    """
    Vocab tree feature matching
    """
def pair_id_to_image_pair(pair_id: typing.SupportsInt) -> tuple[int, int]:
    ...
def patch_match_stereo(workspace_path: str, workspace_format: str = 'COLMAP', pmvs_option_name: str = 'option-all', options: PatchMatchOptions = ..., config_path: str = '') -> None:
    """
    Runs Patch-Match-Stereo (requires CUDA)
    """
def poisson_meshing(input_path: str, output_path: str, options: PoissonMeshingOptions = ...) -> None:
    """
    Perform Poisson surface reconstruction and return true if successful.
    """
def pose_from_homography_matrix(H: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[3, 3]"], K1: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[3, 3]"], K2: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[3, 3]"], cam_rays1: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[m, 3]"], cam_rays2: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[m, 3]"]) -> dict:
    """
    Recover the most probable pose from the given homography matrix using the cheirality check.
    """
def read_rig_config(path: str) -> list[RigConfig]:
    """
    Read the rig configuration from a .json file.
    """
def refine_absolute_pose(cam_from_world: Rigid3d, points2D: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[m, 2]"], points3D: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[m, 3]"], inlier_mask: typing.Annotated[numpy.typing.ArrayLike, numpy.bool, "[m, 1]"], camera: Camera, refinement_options: AbsolutePoseRefinementOptions = ..., return_covariance: bool = False) -> dict | None:
    """
    Non-linear refinement of absolute pose.
    """
def refine_generalized_absolute_pose(rig_from_world: Rigid3d, points2D: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[m, 2]"], points3D: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[m, 3]"], inlier_mask: typing.Annotated[numpy.typing.ArrayLike, numpy.bool, "[m, 1]"], camera_idxs: collections.abc.Sequence[typing.SupportsInt], cams_from_rig: collections.abc.Sequence[Rigid3d], cameras: collections.abc.Sequence[Camera], refinement_options: AbsolutePoseRefinementOptions = ..., return_covariance: bool = False) -> dict | None:
    """
    Robustly estimate generalized absolute pose using LO-RANSACfollowed by non-linear refinement.
    """
def refine_relative_pose(cam2_from_cam1: Rigid3d, cam_rays1: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[m, 3]"], cam_rays2: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[m, 3]"], inlier_mask: typing.Annotated[numpy.typing.ArrayLike, numpy.bool, "[m, 1]"], options: pyceres.SolverOptions = ...) -> dict | None:
    """
    Non-linear refinement of relative pose.
    """
def rig_absolute_pose_estimation(*args, **kwargs) -> typing.Any:
    """
    Deprecated, use ``estimate_and_refine_generalized_absolute_pose`` instead.
    """
def set_random_seed(seed: typing.SupportsInt) -> None:
    """
    Initialize the PRNG with the given seed.
    """
def squared_sampson_error(*args, **kwargs) -> typing.Any:
    """
    Deprecated, use ``compute_squared_sampson_error`` instead.
    """
def stereo_fusion(output_path: str, workspace_path: str, workspace_format: str = 'COLMAP', pmvs_option_name: str = 'option-all', input_type: str = 'geometric', options: StereoFusionOptions = ...) -> Reconstruction:
    """
    Stereo Fusion
    """
def swap_image_pair(image_id1: typing.SupportsInt, image_id2: typing.SupportsInt) -> bool:
    ...
def synthesize_dataset(options: SyntheticDatasetOptions, database: Database = None) -> Reconstruction:
    ...
def synthesize_images(options: SyntheticImageOptions, reconstruction: Reconstruction, image_path: str) -> None:
    ...
def synthesize_noise(options: SyntheticNoiseOptions, reconstruction: Reconstruction, database: Database = None) -> None:
    ...
def triangulate_mid_point(cam2_from_cam1: Rigid3d, cam_ray1: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[3, 1]"], cam_ray2: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[3, 1]"]) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[3, 1]"] | None:
    """
    Triangulate mid-point in first camera from two-view observation.
    """
def triangulate_point(cam1_from_world: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[3, 4]"], cam2_from_world: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[3, 4]"], cam_point1: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[2, 1]"], cam_point2: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[2, 1]"]) -> typing.Annotated[numpy.typing.NDArray[numpy.float64], "[3, 1]"] | None:
    """
    Triangulate point in world from two-view observation.
    """
def triangulate_points(reconstruction: Reconstruction, database_path: str, image_path: str, output_path: str, clear_points: bool = True, options: IncrementalPipelineOptions = ..., refine_intrinsics: bool = False) -> Reconstruction:
    """
    Triangulate 3D points from known camera poses
    """
def undistort_camera(options: UndistortCameraOptions, camera: Camera) -> Camera:
    """
    Undistort camera.
    """
def undistort_image(options: UndistortCameraOptions, distorted_image: Bitmap, distorted_camera: Camera) -> tuple[Bitmap, Camera]:
    """
    Undistort image and corresponding camera.
    """
def undistort_images(output_path: str, input_path: str, image_path: str, image_names: collections.abc.Sequence[str] = [], output_type: str = 'COLMAP', copy_policy: CopyType = ..., num_patch_match_src_images: typing.SupportsInt = 20, undistort_options: UndistortCameraOptions = ...) -> None:
    """
    Undistort images
    """
def verify_matches(database_path: str, pairs_path: str, options: TwoViewGeometryOptions = ...) -> None:
    """
    Run geometric verification of the matches
    """
COLMAP_build: str = 'Commit 0b31f98 on 2025-11-07 without CUDA'
COLMAP_version: str = 'COLMAP 3.13.0'
INVALID_CAMERA_ID: int = 4294967295
INVALID_IMAGE_ID: int = 4294967295
INVALID_IMAGE_PAIR_ID: int = 18446744073709551615
INVALID_POINT2D_IDX: int = 4294967295
INVALID_POINT3D_ID: int = 18446744073709551615
__ceres_version__: str = '2.2.0'
__version__: str = '3.13.0'
has_cuda: bool = False
