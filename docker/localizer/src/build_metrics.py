from math import log1p
from typing import Any

from core.localization_metrics import LocalizationMetrics
from numpy import asarray, eye, float64, hypot, median, ndarray
from numpy.linalg import norm
from numpy.typing import NDArray  # noqa: TID251 — Phase T piece 3 follow-up migration
from pycolmap import Camera as ColmapCamera
from scipy.spatial import ConvexHull

from core.calibration import CalibrationArtifact, Features, apply_global_calibration

from .map import Map


def _compute_inlier_coverage(points2d_inliers: ndarray, image_width: int, image_height: int) -> float:
    if points2d_inliers.shape[0] < 3:
        return 0.0
    try:
        hull = ConvexHull(points2d_inliers)
        return float(hull.volume) / (image_width * image_height)
    except Exception:
        return 0.0


def _build_features(
    *,
    num_inliers: int,
    inlier_ratio: float,
    reprojection_error_median: float,
    inlier_coverage: float,
    num_matches: int,
    image_diagonal_px: float,
    map: Map,
) -> Features:
    return Features(
        log_inliers=float(log1p(num_inliers)),
        inlier_ratio=inlier_ratio,
        reproj_err_norm=reprojection_error_median / image_diagonal_px,
        inlier_coverage=inlier_coverage,
        log_num_matches=float(log1p(num_matches)),
        log_map_image_count=float(log1p(map.map_image_count)),
        log_map_point_count=float(log1p(map.map_point_count)),
        map_avg_track_length=map.map_avg_track_length,
        log_map_bounding_volume_m3=float(log1p(map.map_bounding_volume_m3)),
        map_viewpoint_diversity=map.map_viewpoint_diversity,
        is_indoor=1.0 if map.is_indoor else 0.0,
    )


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

    inlier_ratio = float(num_inliers) / float(num_correspondences)

    inlier_mask = pnp_result["inlier_mask"]
    points3d_inliers = points3d[inlier_mask]
    points2d_inliers = points2d[inlier_mask]

    rotation_camera_from_world = pnp_result["cam_from_world"].rotation.matrix()
    translation_camera_from_world = asarray(pnp_result["cam_from_world"].translation, dtype=float64)
    camera_frame_points = (rotation_camera_from_world @ points3d_inliers.T).T + translation_camera_from_world[None, :]

    projected_pixel_coordinates = pycolmap_camera.img_from_cam(camera_frame_points)

    residuals: NDArray[float64] = norm(projected_pixel_coordinates - points2d_inliers, axis=1).astype(float64)

    reprojection_error_median = float(median(residuals))

    inlier_coverage = _compute_inlier_coverage(points2d_inliers, image_width, image_height)

    image_diagonal_px = float(hypot(image_width, image_height))
    features = _build_features(
        num_inliers=num_inliers,
        inlier_ratio=inlier_ratio,
        reprojection_error_median=reprojection_error_median,
        inlier_coverage=inlier_coverage,
        num_matches=num_matches,
        image_diagonal_px=image_diagonal_px,
        map=map,
    )
    confidence = apply_global_calibration(calibration, features=features)

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
        confidence=confidence,
        measurement_covariance=measurement_covariance,
        pnp_covariance=pnp_covariance.tolist(),
        pipeline_version=pipeline_version,
    )
