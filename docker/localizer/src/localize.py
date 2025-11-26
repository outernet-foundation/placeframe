from __future__ import annotations

from typing import Any, cast

import numpy as np
from core.classes import Quaternion, Transform, Vector3
from core.create_image_tensors import create_image_tensors
from core.lightglue import lightglue_match_tensors
from core.localization_metrics import LocalizationMetrics
from core.opq import decode_descriptors
from core.rig import PinholeCameraConfig, transform_intrinsics
from pycolmap import AbsolutePoseEstimationOptions, RANSACOptions
from pycolmap import Camera as ColmapCamera
from pycolmap._core import estimate_and_refine_absolute_pose  # type: ignore
from torch import cuda, from_numpy, mv, topk  # type: ignore

from .build_metrics import build_localization_metrics
from .map import Map

DEVICE = "cuda" if cuda.is_available() else "cpu"
print(f"Using device: {DEVICE}")


dir: Any = None
superpoint: Any = None
lightglue: Any = None


def load_models(max_keypoints: int):
    from neural_networks.models import load_DIR, load_lightglue, load_superpoint

    global dir, superpoint, lightglue
    dir = load_DIR(DEVICE)
    superpoint = load_superpoint(max_num_keypoints=max_keypoints, device=DEVICE)
    lightglue = load_lightglue(DEVICE)


def localize_image_against_reconstruction(
    map: Map, camera: PinholeCameraConfig, image_buffer: bytes, retrieval_top_k: int, ransac_threshold: float
) -> tuple[Transform, LocalizationMetrics]:
    # Extract features from query image
    (image, rgb_tensor, gray_tensor) = create_image_tensors(image_buffer, camera.rotation)
    superpoint_output = superpoint({"image": gray_tensor.unsqueeze(0).to(device=DEVICE)})
    query_global_descriptor = dir({"image": rgb_tensor.unsqueeze(0).to(device=DEVICE)})["global_descriptor"][0]

    # Retrieve similar database images
    similarity_scores = mv(from_numpy(map.global_descriptors_matrix).to(DEVICE), query_global_descriptor)
    topk_rows: list[int] = topk(similarity_scores, retrieval_top_k).indices.cpu().tolist()  # type: ignore
    matched_image_ids = [map.ordered_image_ids[i] for i in topk_rows]

    # Decode descriptors of matched database images
    descriptors = decode_descriptors(
        map.opq_matrix, map.product_quantizer, {image_id: map.pq_codes[image_id] for image_id in matched_image_ids}
    )

    # Prepare database image data for matching
    keypoints = {str(image_id): from_numpy(map.keypoints[image_id]).to(DEVICE) for image_id in matched_image_ids}
    descriptors = {str(image_id): from_numpy(descriptors[image_id]).to(DEVICE) for image_id in matched_image_ids}
    sizes = {str(image_id): map.image_sizes[str(image_id)] for image_id in matched_image_ids}

    # Prepare query image data for matching
    keypoints["query"] = superpoint_output["keypoints"][0].to(DEVICE)
    descriptors["query"] = superpoint_output["descriptors"][0].to(DEVICE)
    sizes["query"] = (image.height, image.width)

    # Match features between query and database images
    pairs = [(str(image_id), "query") for image_id in matched_image_ids]
    match_indices = lightglue_match_tensors(lightglue, pairs, keypoints, descriptors, sizes, len(pairs), DEVICE)

    # Collect 2D-3D correspondences
    query_keypoint_indices: list[int] = []
    point3d_indices: list[int] = []
    for image_id in matched_image_ids:
        for database_image_keypoint_index, query_image_keypoint_index in zip(*match_indices[(str(image_id), "query")]):
            point2D = map.images[image_id].points2D[int(database_image_keypoint_index)]

            if not point2D.has_point3D():
                continue

            query_keypoint_indices.append(int(query_image_keypoint_index))
            point3d_indices.append(int(point2D.point3D_id))

    # Verify we have enough correspondences
    if not query_keypoint_indices:
        raise ValueError("No matching keypoints found")

    # Create COLMAP camera model
    pycolmap_camera = ColmapCamera(
        width=camera.width, height=camera.height, model="PINHOLE", params=transform_intrinsics(camera)
    )

    # Set estimation options
    ransac_options = RANSACOptions()
    ransac_options.max_error = ransac_threshold
    estimation_options = AbsolutePoseEstimationOptions()
    estimation_options.ransac = ransac_options

    # Estimate pose
    points2D = keypoints["query"][query_keypoint_indices].cpu().numpy()
    points3D = np.vstack([map.points3D[i].xyz for i in point3d_indices])
    pnp_result = cast(
        dict[str, Any] | None,
        estimate_and_refine_absolute_pose(points2D, points3D, pycolmap_camera, estimation_options),
    )

    # Check if pose estimation was successful
    if pnp_result is None:
        raise ValueError("Pose estimation failed")

    # Build final transform
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

    # Build metrics
    metrics = build_localization_metrics(pnp_result, points2D, points3D, pycolmap_camera)

    # Success
    print(transform.model_dump_json(indent=2))
    print(metrics.model_dump_json(indent=2))
    return transform, metrics
