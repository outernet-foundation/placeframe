from __future__ import annotations

from os import environ
from typing import Any, cast
from uuid import UUID

import numpy as np
import torch
from common.boto_clients import create_s3_client
from core.classes import LocalizationMetrics
from core.rig import PinholeCamera
from core.transform import Quaternion, Transform, Vector3
from core.ugh import create_colmap_camera
from neural_networks.dir import load_DIR
from neural_networks.image import create_image_tensors
from neural_networks.lightglue import load_lightglue
from neural_networks.superpoint import load_superpoint
from numpy.typing import NDArray
from pycolmap import AbsolutePoseEstimationOptions, RANSACOptions, Reconstruction
from pycolmap._core import estimate_and_refine_absolute_pose  # type: ignore
from torch import cuda, inference_mode, mv, topk  # type: ignore

from .map import Map
from .settings import get_settings

WEIGHTS = "indoor"
MAX_KEYPOINTS = 2500
RETRIEVAL_TOP_K = 12  # how many similar database images to keep
RANSAC_THRESHOLD = 12.0  # reprojection error in pixels

settings = get_settings()
s3_client = create_s3_client(
    s3_endpoint_url=settings.s3_endpoint_url, s3_access_key=settings.s3_access_key, s3_secret_key=settings.s3_secret_key
)

if environ.get("CODEGEN"):
    dir: Any = None
    superpoint: Any = None
    lightglue: Any = None
else:
    DEVICE = "cuda" if cuda.is_available() else "cpu"
    print(f"Using device: {DEVICE}")

    print("Loading deep-image-retrieval model")
    dir = load_DIR(DEVICE)

    print("Loading superpoint model")
    superpoint = load_superpoint(WEIGHTS, MAX_KEYPOINTS, DEVICE)

    print("Loading lightglue model")
    lightglue = load_lightglue(DEVICE)


reconstructions: dict[UUID, Reconstruction] = {}


async def localize_image_against_reconstruction(
    map: Map, camera: PinholeCamera, image: bytes
) -> tuple[Transform, LocalizationMetrics]:
    pycolmap_camera = create_colmap_camera(camera)
    rgb_image_tensor, grayscale_image_tensor, image_size = create_image_tensors(camera.rotation, image, DEVICE)

    print("Extracting features")

    # Extract keypoints and global descriptor for query image
    with inference_mode():
        query_image_global_descriptor = dir({"image": rgb_image_tensor})["global_descriptor"][0]

        # Hloc's DIR wrapper moves the descriptor to the CPU for PCA whitening; move it back to DEVICE
        query_image_global_descriptor = query_image_global_descriptor.to(DEVICE)

        superpoint_output = superpoint({"image": grayscale_image_tensor})
        query_image_keypoints = superpoint_output["keypoints"][0]
        query_image_descriptors = superpoint_output["descriptors"][0]

    print("Retrieving similar database images")

    # Retrieve top K most similar database images
    similarity_scores = mv(map.global_matrix, query_image_global_descriptor)
    topk_rows: list[int] = topk(similarity_scores, RETRIEVAL_TOP_K).indices.cpu().tolist()  # type: ignore
    matched_names: list[str] = [map.image_names[i] for i in topk_rows]
    matched_image_ids: list[int] = [map.image_id_by_name[n] for n in matched_names]

    # Start padding logic
    batch_size = len(matched_image_ids)
    print(batch_size)
    descriptor_dimension = map.descriptors[matched_image_ids[0]].shape[0]
    max_keypoints = max(map.keypoints[i].shape[0] for i in matched_image_ids)

    padded_db_keypoints = torch.full(
        (batch_size, max_keypoints, 2), fill_value=-1.0, dtype=torch.float32, device=DEVICE
    )

    padded_db_descriptors = torch.zeros(
        (batch_size, descriptor_dimension, max_keypoints), dtype=torch.float32, device=DEVICE
    )

    for batch_index, matched_image_id in enumerate(matched_image_ids):
        num_image_keypoints = map.keypoints[matched_image_id].shape[0]
        padded_db_keypoints[batch_index, :num_image_keypoints, :] = map.keypoints[matched_image_id]
        padded_db_descriptors[batch_index, :, :num_image_keypoints] = map.descriptors[matched_image_id]

    keypoints0 = padded_db_keypoints
    descriptors0 = padded_db_descriptors
    keypoints1 = query_image_keypoints.unsqueeze(0).expand(batch_size, -1, -1)
    descriptors1 = query_image_descriptors.unsqueeze(0).expand(batch_size, -1, -1)

    descriptors0 = descriptors0.transpose(-1, -2)
    descriptors1 = descriptors1.transpose(-1, -2)

    sizes0 = torch.tensor(
        [
            (
                map.reconstruction.cameras[map.reconstruction.images[i].camera_id].height,
                map.reconstruction.cameras[map.reconstruction.images[i].camera_id].width,
            )
            for i in matched_image_ids
        ],
        device=DEVICE,
    )
    sizes1 = torch.tensor([image_size] * batch_size, device=DEVICE)

    print("Matching features")

    # Run LightGlue matcher
    with torch.inference_mode():
        match_tensors = lightglue({
            "image0": {"keypoints": keypoints0, "descriptors": descriptors0, "image_size": sizes0},
            "image1": {"keypoints": keypoints1, "descriptors": descriptors1, "image_size": sizes1},
        })["matches0"]

    print("Building 2D-3D correspondences")

    # Build 2D-3D correspondences
    correspondences: dict[int, int] = {}
    matches_numpy = match_tensors.cpu().numpy()
    for matched_image_id, matched_keypoints in zip(matched_image_ids, matches_numpy):
        # Skip this image if no matches were found
        match_image_matched_keypoints = np.where(matched_keypoints != -1)[0]
        if match_image_matched_keypoints.size == 0:
            continue

        matched_image = map.reconstruction.images[matched_image_id]

        for matched_image_keypoint_index in match_image_matched_keypoints:
            query_image_keypoint_index = matched_keypoints[matched_image_keypoint_index]
            point2D = matched_image.points2D[matched_image_keypoint_index]  # type: ignore

            # If this keypoint has a 3D point (i.e. it was triangulated during map construction),
            # and it is not already in the query_keypoint_to_point3d dictionary, add it
            if point2D.has_point3D() and query_image_keypoint_index not in correspondences:  # type: ignore
                correspondences[int(query_image_keypoint_index)] = int(point2D.point3D_id)  # type: ignore

    if not correspondences:
        raise ValueError("No matching keypoints found")

    query_keypoint_indices, point3d_indices = zip(*correspondences.items())

    # Select the matched 2D keypoints and convert from torch tensor to NumPy array
    points2d = (query_image_keypoints[list(query_keypoint_indices)]).cpu().numpy()

    # For each matched 2D keypoint, look up its corresponding 3D world point and
    # stack them into an (M, 3) NumPy array to feed into absolute_pose_estimation.
    points3d = np.vstack([map.reconstruction.points3D[i].xyz for i in point3d_indices])

    print("Estimating pose")

    ransac_options = RANSACOptions()
    ransac_options.max_error = RANSAC_THRESHOLD

    estimationOptions = AbsolutePoseEstimationOptions()
    estimationOptions.ransac = ransac_options

    # Estimate the camera pose using the 2D-3D correspondences
    pnp_result = cast(
        dict[str, Any] | None,
        estimate_and_refine_absolute_pose(points2d, points3d, pycolmap_camera, estimation_options=estimationOptions),
    )

    if pnp_result is None:
        raise ValueError("Pose estimation failed")

    # print every key in pnp_result for debugging
    for key in pnp_result.keys():
        print(f"PnP result key: {key}")

    transform = Transform(
        position=Vector3(
            x=float(pnp_result["cam_from_world"].translation[0]),
            y=float(pnp_result["cam_from_world"].translation[1]),
            z=float(pnp_result["cam_from_world"].translation[2]),
        ),
        rotation=Quaternion(
            x=float(pnp_result["cam_from_world"].rotation.quat[0]),
            y=float(pnp_result["cam_from_world"].rotation.quat[1]),
            z=float(pnp_result["cam_from_world"].rotation.quat[2]),
            w=float(pnp_result["cam_from_world"].rotation.quat[3]),
        ),
    )

    # Compute inlier ratio
    inlier_ratio = float(int(pnp_result["num_inliers"])) / float(int(points2d.shape[0]))

    # Get inliers for this PnP result
    points3d_inliers = points3d[pnp_result["inlier_mask"]]
    points2d_inliers = points2d[pnp_result["inlier_mask"]]

    # Transform 3d inliers from world frame into camera frame
    rotation_camera_from_world = pnp_result["cam_from_world"].rotation.matrix()
    translation_camera_from_world = np.asarray(pnp_result["cam_from_world"].translation, dtype=np.float64)
    camera_frame_points = (rotation_camera_from_world @ points3d_inliers.T).T + translation_camera_from_world[None, :]

    # Project 3d inliers into pixel coordinates using the camera model
    projected_pixel_coordinates = pycolmap_camera.img_from_cam(camera_frame_points)

    # Compute reprojection residuals for inliers
    residuals: NDArray[np.float64] = np.linalg.norm(projected_pixel_coordinates - points2d_inliers, axis=1).astype(
        np.float64
    )

    # Compute median reprojection error among inliers
    reprojection_error_median = float(np.median(residuals))

    print(f"Localization successful: {transform}")

    return transform, LocalizationMetrics(
        inlier_ratio=inlier_ratio,
        reprojection_error_median=reprojection_error_median,
        image_coverage=0.0,
        depth_z_90th_percentile=0.0,
        depth_z_10th_percentile=0.0,
    )
