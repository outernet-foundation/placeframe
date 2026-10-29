"""Assemble the per-query diagnostic payload from the pipeline's intermediate state.

Everything here is read-only bookkeeping over values `localize_image_against_reconstruction`
already computed. It runs only when a caller asks for detail, because the per-match arrays
cost more to serialize than the pose they explain.
"""

from __future__ import annotations

from typing import Any, cast

from core.axis_convention import AxisConvention, change_basis_unity_from_opencv_pose
from core.calibration import CalibrationArtifact
from core.camera_config import PinholeCameraConfig
from core.image_preprocess import canonicalize_intrinsics
from core.lightglue import Keypoints, MatchIndices
from core.localization_detail import (
    MATCH_INLIER,
    MATCH_NO_POINT3D,
    MATCH_OUTLIER,
    GateDetail,
    LocalizationDetail,
    PairDetail,
)
from core.localization_metrics import LocalizationMetrics
from core.transform import Float3, Float4, Transform
from numpy import arccos, asarray, clip, degrees, float64, isfinite, median, vstack
from numpy.linalg import norm
from pycolmap import AbsolutePoseEstimationOptions
from pycolmap import Camera as ColmapCamera
from pycolmap._core import Rigid3d, estimate_and_refine_absolute_pose  # type: ignore  # noqa: PLC2701 — no public API
from scipy.spatial.transform import Rotation

from .map import Map

# A pair's own pose is drawn next to the pooled one as evidence for or against it, so it has to
# rest on enough points to be a pose at all: PnP needs four, and RANSAC on a dozen-odd
# correspondences "succeeds" on nearly anything. Below this many inliers the pair gets no pose.
PAIR_POSE_MIN_INLIERS = 12


def camera_from_map_transform(cam_from_world: Rigid3d, axis_convention: AxisConvention) -> Transform:
    """A COLMAP `cam_from_world` pose in the response's form and axis convention."""
    translation = asarray(cam_from_world.translation, dtype=float64)
    rotation = asarray(cam_from_world.rotation.matrix(), dtype=float64)
    if axis_convention == AxisConvention.UNITY:
        translation, rotation = change_basis_unity_from_opencv_pose(translation, rotation)
    quaternion = Rotation.from_matrix(rotation).as_quat()
    return Transform(
        translation=Float3(x=translation[0], y=translation[1], z=translation[2]),
        rotation=Float4(x=quaternion[0], y=quaternion[1], z=quaternion[2], w=quaternion[3]),
    )


def _pair_pose(
    query_points: list[Any],
    map_points: list[Any],
    pycolmap_camera: ColmapCamera,
    estimation_options: AbsolutePoseEstimationOptions,
) -> tuple[Rigid3d, int] | None:
    """PnP over one pair's correspondences alone, or None when it does not yield a usable pose."""
    if len(query_points) < PAIR_POSE_MIN_INLIERS:
        return None
    result = cast(
        dict[str, Any] | None,
        estimate_and_refine_absolute_pose(
            vstack(query_points), vstack(map_points), pycolmap_camera, estimation_options
        ),
    )
    if result is None or int(result["num_inliers"]) < PAIR_POSE_MIN_INLIERS:
        return None
    return cast(Rigid3d, result["cam_from_world"]), int(result["num_inliers"])


def _camera_centre_and_axis(pose: Rigid3d) -> tuple[Any, Any]:
    """World-frame optical centre and viewing direction of a `cam_from_world` pose."""
    rotation = asarray(pose.rotation.matrix(), dtype=float64)
    translation = asarray(pose.translation, dtype=float64)
    centre = -rotation.T @ translation
    # Third row of R is the camera's +Z (forward) axis expressed in world coordinates.
    axis = rotation.T @ asarray([0.0, 0.0, 1.0], dtype=float64)
    return centre, axis


def build_localization_detail(
    *,
    map: Map,
    camera: PinholeCameraConfig,
    matched_image_ids: list[int],
    retrieval_scores: list[float],
    match_indices: MatchIndices,
    keypoints: Keypoints,
    correspondence_sources: list[tuple[int, int]],
    inlier_mask: Any | None,
    reprojection_errors: Any | None,
    cam_from_world: Rigid3d | None,
    pycolmap_camera: ColmapCamera,
    estimation_options: AbsolutePoseEstimationOptions,
    axis_convention: AxisConvention,
    top_k: int,
    ransac_threshold: float,
    num_query_keypoints: int,
    timings: dict[str, float],
    metrics: LocalizationMetrics | None,
    calibration: CalibrationArtifact,
    failure_reason: str | None,
) -> LocalizationDetail:
    # (database image, slot in that pair's match list) -> index into the flat correspondence
    # list, which is the index space both `inlier_mask` and `reprojection_errors` live in.
    correspondence_of_slot: dict[tuple[int, int], int] = {
        source: index for index, source in enumerate(correspondence_sources)
    }

    query_keypoints = keypoints["query"].cpu().numpy()

    query_centre = None
    query_axis = None
    if cam_from_world is not None:
        query_centre, query_axis = _camera_centre_and_axis(cam_from_world)

    pairs: list[PairDetail] = []
    for rank, image_id in enumerate(matched_image_ids):
        database_indices, query_indices = match_indices[(str(image_id), "query")]
        database_keypoints = keypoints[str(image_id)].cpu().numpy()
        height, width = map.image_sizes[str(image_id)]

        query_xy: list[list[float]] = []
        database_xy: list[list[float]] = []
        status: list[int] = []
        residuals: list[float] = []

        num_inliers = 0
        num_correspondences = 0
        inlier_residuals: list[float] = []
        pair_query_points: list[Any] = []
        pair_map_points: list[Any] = []

        for slot in range(len(database_indices)):
            database_index = int(database_indices[slot])
            query_index = int(query_indices[slot])
            database_xy.append([
                round(float(database_keypoints[database_index][0]), 2),
                round(float(database_keypoints[database_index][1]), 2),
            ])
            query_xy.append([
                round(float(query_keypoints[query_index][0]), 2),
                round(float(query_keypoints[query_index][1]), 2),
            ])

            correspondence = correspondence_of_slot.get((image_id, slot))
            if correspondence is None:
                # Matched, but the database keypoint carries no triangulated point, so PnP
                # never saw this pair. Counted separately from an outlier on purpose.
                status.append(MATCH_NO_POINT3D)
                residuals.append(-1.0)
                continue

            num_correspondences += 1
            pair_query_points.append(query_keypoints[query_index])
            point3d_id = map.images[image_id].points2D[database_index].point3D_id
            pair_map_points.append(map.points3D[point3d_id].xyz)
            residual = float(reprojection_errors[correspondence]) if reprojection_errors is not None else -1.0
            # A correspondence whose 3D point falls behind the estimated camera projects to
            # NaN or infinity. Left alone it serializes as JSON `null`, which the generated
            # clients reject outright ("reprojection_error_px.27.float: Input should be a valid
            # number"), failing the whole response over an undefined residual. Negative means
            # undefined here, and `status` says which kind: MATCH_NO_POINT3D for a match PnP
            # never saw, MATCH_OUTLIER for one that reprojected nowhere real.
            if not isfinite(residual):
                residual = -1.0
            residuals.append(round(residual, 3))

            is_inlier = bool(inlier_mask[correspondence]) if inlier_mask is not None else False
            if is_inlier:
                num_inliers += 1
                status.append(MATCH_INLIER)
                if residual >= 0.0:
                    inlier_residuals.append(residual)
            else:
                status.append(MATCH_OUTLIER)

        distance_m = None
        view_angle_deg = None
        if query_centre is not None and query_axis is not None:
            # cam_from_world() composes frame_from_world with sensor_from_rig, so a rig capture's
            # per-camera pose is correct here rather than silently collapsing to the rig origin.
            database_centre, database_axis = _camera_centre_and_axis(map.images[image_id].cam_from_world())
            distance_m = float(norm(database_centre - query_centre))
            cosine = float(database_axis @ query_axis)
            view_angle_deg = float(degrees(arccos(clip(cosine, -1.0, 1.0))))

        pair_pose = _pair_pose(pair_query_points, pair_map_points, pycolmap_camera, estimation_options)

        pairs.append(
            PairDetail(
                rank=rank,
                image_id=image_id,
                name=map.images[image_id].name,
                width=width,
                height=height,
                retrieval_score=retrieval_scores[rank],
                num_keypoints=int(database_keypoints.shape[0]),
                num_matches=len(database_indices),
                num_correspondences=num_correspondences,
                num_inliers=num_inliers,
                inlier_ratio=(num_inliers / num_correspondences) if num_correspondences else 0.0,
                reprojection_error_median=float(median(inlier_residuals)) if inlier_residuals else None,
                distance_m=distance_m,
                view_angle_deg=view_angle_deg,
                camera_from_map_transform=(
                    camera_from_map_transform(pair_pose[0], axis_convention) if pair_pose is not None else None
                ),
                pose_num_inliers=pair_pose[1] if pair_pose is not None else 0,
                query_xy=query_xy,
                database_xy=database_xy,
                status=status,
                reprojection_error_px=residuals,
            )
        )

    query_width, query_height, fx, fy, cx, cy = canonicalize_intrinsics(camera)

    gate = None
    if metrics is not None:
        gate = GateDetail(
            loose_min=calibration.loose_min,
            tight_min=calibration.tight_min,
            passed=(
                metrics.confidence_loose >= calibration.loose_min and metrics.confidence_tight >= calibration.tight_min
            ),
        )

    return LocalizationDetail(
        reconstruction_id="",
        # The canonicalized intrinsics, which is the frame every keypoint coordinate above is
        # expressed in -- not the caller's original pixel dimensions.
        camera=PinholeCameraConfig(
            width=query_width, height=query_height, orientation="TOP_LEFT", fx=fx, fy=fy, cx=cx, cy=cy
        ),
        retrieval_top_k=top_k,
        ransac_threshold=ransac_threshold,
        num_query_keypoints=num_query_keypoints,
        timings_ms={name: value * 1000.0 for name, value in timings.items()},
        pairs=pairs,
        camera_from_map_transform=(
            camera_from_map_transform(cam_from_world, axis_convention) if cam_from_world is not None else None
        ),
        metrics=metrics,
        gate=gate,
        failure_reason=failure_reason,
    )
