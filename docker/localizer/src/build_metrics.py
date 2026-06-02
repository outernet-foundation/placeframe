from typing import Any

from core.localization_metrics import LocalizationMetrics
from numpy import asarray, eye, float64, hypot, median, ndarray
from numpy.linalg import norm
from numpy.typing import NDArray  # noqa: TID251 — Phase T piece 3 follow-up migration
from pycolmap import Camera as ColmapCamera
from scipy.spatial import ConvexHull

from core.calibration import (
    CalibrationArtifact,
    Features,
    RawLocalizationMetrics,
    apply_global_calibration,
)

from .map import Map


def _compute_inlier_coverage(points2d_inliers: ndarray, image_width: int, image_height: int) -> float:
    if points2d_inliers.shape[0] < 3:
        return 0.0
    try:
        hull = ConvexHull(points2d_inliers)
        return float(hull.volume) / (image_width * image_height)
    except Exception:
        return 0.0


def build_localization_metrics(
    pnp_result: dict[str, Any],
    points2d: ndarray,
    points3d: ndarray,
    pycolmap_camera: ColmapCamera,
    num_matches: int,
    image_width: int,
    image_height: int,
    pipeline_version: str,
    calibration: CalibrationArtifact,
    map: Map,
) -> LocalizationMetrics:
    num_inliers = int(pnp_result["num_inliers"])
    num_correspondences = int(points2d.shape[0])

    # Compute inlier ratio
    inlier_ratio = float(num_inliers) / float(num_correspondences)

    # Get inliers for this PnP result
    inlier_mask = pnp_result["inlier_mask"]
    points3d_inliers = points3d[inlier_mask]
    points2d_inliers = points2d[inlier_mask]

    # Transform 3d inliers from world frame into camera frame
    rotation_camera_from_world = pnp_result["cam_from_world"].rotation.matrix()
    translation_camera_from_world = asarray(pnp_result["cam_from_world"].translation, dtype=float64)
    camera_frame_points = (rotation_camera_from_world @ points3d_inliers.T).T + translation_camera_from_world[None, :]

    # Project 3d inliers into pixel coordinates using the camera model
    projected_pixel_coordinates = pycolmap_camera.img_from_cam(cam_points=camera_frame_points)

    # Compute reprojection residuals for inliers
    residuals: NDArray[float64] = norm(projected_pixel_coordinates - points2d_inliers, axis=1).astype(float64)

    # Compute median reprojection error among inliers
    reprojection_error_median = float(median(residuals))

    # Compute inlier coverage
    inlier_coverage = _compute_inlier_coverage(points2d_inliers, image_width, image_height)

    features = Features.compute(
        localization=RawLocalizationMetrics(
            num_inliers=num_inliers,
            inlier_ratio=inlier_ratio,
            reproj_error_median=reprojection_error_median,
            inlier_coverage=inlier_coverage,
            num_matches=num_matches,
            query_image_diagonal_px=float(hypot(image_width, image_height)),
        ),
        map_metrics=map.map_metrics,
    )
    confidence_tight, confidence_loose, confidence_is_calibrated = apply_global_calibration(
        calibration, features=features
    )

    pnp_covariance = pnp_result["covariance"]
    measurement_covariance = (
        calibration.sigma_meas_alpha * pnp_covariance + calibration.sigma_meas_beta * eye(6)
    ).tolist()

    return LocalizationMetrics(
        inlier_ratio=inlier_ratio,
        reprojection_error_median=reprojection_error_median,
        num_inliers=num_inliers,
        num_correspondences=num_correspondences,
        num_matches=num_matches,
        inlier_coverage=inlier_coverage,
        confidence_tight=confidence_tight,
        confidence_loose=confidence_loose,
        confidence_is_calibrated=confidence_is_calibrated,
        measurement_covariance=measurement_covariance,
        pnp_covariance=pnp_covariance.tolist(),
        pipeline_version=pipeline_version,
    )
