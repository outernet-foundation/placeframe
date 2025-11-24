from __future__ import annotations
import numpy
import numpy.typing
import pycolmap._core
import typing
__all__: list[str] = ['AbsolutePosePositionPriorCost', 'AbsolutePosePriorCost', 'Point3DAlignmentCost', 'RelativePosePriorCost', 'ReprojErrorCost', 'RigReprojErrorCost', 'SampsonErrorCost']
@typing.overload
def AbsolutePosePositionPriorCost(position_in_world_prior: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[3, 1]"]) -> ...:
    """
    3-DoF error on the absolute camera pose's position.
    """
@typing.overload
def AbsolutePosePositionPriorCost(position_cov_in_world_prior: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[3, 3]"], position_in_world_prior: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[3, 1]"]) -> ...:
    """
    3-DoF error on the absolute camera pose's position with prior covariance.
    """
@typing.overload
def AbsolutePosePriorCost(cam_from_world_prior: pycolmap._core.Rigid3d) -> ...:
    """
    6-DoF error on the absolute camera pose.
    """
@typing.overload
def AbsolutePosePriorCost(cam_cov_from_world_prior: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[6, 6]"], cam_from_world_prior: pycolmap._core.Rigid3d) -> ...:
    """
    6-DoF error on the absolute camera pose with prior covariance.
    """
@typing.overload
def Point3DAlignmentCost(point_in_b_prior: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[3, 1]"], use_log_scale: bool = True) -> ...:
    """
    Error between 3D points transformed by a 3D similarity transform.
    """
@typing.overload
def Point3DAlignmentCost(point_cov_in_b_prior: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[3, 3]"], point_in_b_prior: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[3, 1]"], use_log_scale: bool = True) -> ...:
    """
    Error between 3D points transformed by a 3D similarity transform. with prior covariance
    """
@typing.overload
def RelativePosePriorCost(i_from_j_prior: pycolmap._core.Rigid3d) -> ...:
    """
    6-DoF error between two absolute camera poses based on a prior relative pose.
    """
@typing.overload
def RelativePosePriorCost(i_cov_from_j_prior: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[6, 6]"], i_from_j_prior: pycolmap._core.Rigid3d) -> ...:
    """
    6-DoF error between two absolute camera poses based on a prior relative pose with prior covariance.
    """
@typing.overload
def ReprojErrorCost(camera_model_id: pycolmap._core.CameraModelId, point2D: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[2, 1]"]) -> ...:
    """
    Reprojection error.
    """
@typing.overload
def ReprojErrorCost(camera_model_id: pycolmap._core.CameraModelId, point2D_cov: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[2, 2]"], point2D: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[2, 1]"]) -> ...:
    """
    Reprojection error with 2D detection noise.
    """
@typing.overload
def ReprojErrorCost(camera_model_id: pycolmap._core.CameraModelId, point2D: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[2, 1]"], cam_from_world: pycolmap._core.Rigid3d) -> ...:
    """
    Reprojection error with constant camera pose.
    """
@typing.overload
def ReprojErrorCost(camera_model_id: pycolmap._core.CameraModelId, point2D_cov: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[2, 2]"], point2D: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[2, 1]"], cam_from_world: pycolmap._core.Rigid3d) -> ...:
    """
    Reprojection error with constant camera pose and 2D detection noise.
    """
@typing.overload
def ReprojErrorCost(camera_model_id: pycolmap._core.CameraModelId, point2D: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[2, 1]"], point3D: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[3, 1]"]) -> ...:
    """
    Reprojection error with constant 3D point.
    """
@typing.overload
def ReprojErrorCost(camera_model_id: pycolmap._core.CameraModelId, point2D_cov: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[2, 2]"], point2D: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[2, 1]"], point3D: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[3, 1]"]) -> ...:
    """
    Reprojection error with constant 3D point and 2D detection noise.
    """
@typing.overload
def RigReprojErrorCost(camera_model_id: pycolmap._core.CameraModelId, point2D: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[2, 1]"]) -> ...:
    """
    Reprojection error for camera rig.
    """
@typing.overload
def RigReprojErrorCost(camera_model_id: pycolmap._core.CameraModelId, point2D_cov: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[2, 2]"], point2D: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[2, 1]"]) -> ...:
    """
    Reprojection error for camera rig with 2D detection noise.
    """
@typing.overload
def RigReprojErrorCost(camera_model_id: pycolmap._core.CameraModelId, point2D: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[2, 1]"], cam_from_rig: pycolmap._core.Rigid3d) -> ...:
    """
    Reprojection error for camera rig with constant cam-from-rig pose.
    """
@typing.overload
def RigReprojErrorCost(camera_model_id: pycolmap._core.CameraModelId, point2D_cov: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[2, 2]"], point2D: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[2, 1]"], cam_from_rig: pycolmap._core.Rigid3d) -> ...:
    """
    Reprojection error for camera rig with constant cam-from-rig pose and 2D detection noise.
    """
def SampsonErrorCost(cam_ray1: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[3, 1]"], cam_ray2: typing.Annotated[numpy.typing.ArrayLike, numpy.float64, "[3, 1]"]) -> ...:
    """
    Sampson error for two-view geometry.
    """
