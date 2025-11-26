from typing import Any

from core.localization_metrics import LocalizationMetrics
from numpy import asarray, float64, median, ndarray
from numpy.linalg import norm
from numpy.typing import NDArray
from pycolmap import Camera as ColmapCamera


def build_localization_metrics(
    pnp_result: dict[str, Any], points2d: ndarray, points3d: ndarray, pycolmap_camera: ColmapCamera
):
    # Compute inlier ratio
    inlier_ratio = float(int(pnp_result["num_inliers"])) / float(int(points2d.shape[0]))

    # Get inliers for this PnP result
    points3d_inliers = points3d[pnp_result["inlier_mask"]]
    points2d_inliers = points2d[pnp_result["inlier_mask"]]

    # Transform 3d inliers from world frame into camera frame
    rotation_camera_from_world = pnp_result["cam_from_world"].rotation.matrix()
    translation_camera_from_world = asarray(pnp_result["cam_from_world"].translation, dtype=float64)
    camera_frame_points = (rotation_camera_from_world @ points3d_inliers.T).T + translation_camera_from_world[None, :]

    # Project 3d inliers into pixel coordinates using the camera model
    projected_pixel_coordinates = pycolmap_camera.img_from_cam(camera_frame_points)

    # Compute reprojection residuals for inliers
    residuals: NDArray[float64] = norm(projected_pixel_coordinates - points2d_inliers, axis=1).astype(float64)

    # Compute median reprojection error among inliers
    reprojection_error_median = float(median(residuals))

    return LocalizationMetrics(inlier_ratio=inlier_ratio, reprojection_error_median=reprojection_error_median)
