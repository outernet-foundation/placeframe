from __future__ import annotations

from uuid import UUID

import numpy as np
import torch
from common.boto_clients import create_s3_client
from common.classes import CameraIntrinsics, Quaternion, Transform, Vector3
from common.make_multipar_json_dep import make_multipart_json_dep
from cv2 import COLOR_BGR2GRAY, COLOR_BGR2RGB, IMREAD_COLOR, cvtColor, imdecode
from fastapi import FastAPI
from hloc.extractors.dir import DIR
from hloc.extractors.superpoint import SuperPoint
from lightglue import LightGlue
from numpy import float32, frombuffer, uint8
from pycolmap import Camera, Reconstruction
from pycolmap._core import absolute_pose_estimation  # type: ignore
from pydantic import TypeAdapter
from torch import cuda, from_numpy, inference_mode, mv, topk  # type: ignore
from torch import float32 as torch_float32  # type: ignore

from .map import Map
from .settings import get_settings

DEVICE = "cuda" if cuda.is_available() else "cpu"
print(f"Using device: {DEVICE}")


WEIGHTS = "indoor"
RETRIEVAL_TOP_K = 5  # how many similar database images to keep
RANSAC_THRESHOLD = 12.0  # reprojection error in pixels

settings = get_settings()
s3_client = create_s3_client(
    s3_endpoint_url=settings.s3_endpoint_url, s3_access_key=settings.s3_access_key, s3_secret_key=settings.s3_secret_key
)

print(f"Loading retrieval model: {'deep-image-retrieval'}")

# PyTorch 2.6 flips torch.load default to weights_only=True, so we temporarily force legacy loading to read DIR’s pickled checkpoint;
# see: https://dev-discuss.pytorch.org/t/bc-breaking-change-torch-load-is-being-flipped-to-use-weights-only-true-by-default-in-the-nightlies-after-137602/2573
_orig_load = torch.load  # type: ignore


def _load_legacy(*args, **kwargs):  # type: ignore
    kwargs.setdefault("weights_only", False)  # type: ignore
    return _orig_load(*args, **kwargs)  # type: ignore


torch.load = _load_legacy
dir: DIR = DIR({}).to(DEVICE).eval()
torch.load = _orig_load

print(f"Loading feature extraction model: {'SuperPoint'}")

superpoint = SuperPoint({"weights": WEIGHTS}).to(DEVICE).eval()

print(f"Loading feature matching model: {'LightGlue'}")

LIGHTGLUE_MATCHER = LightGlue(features="superpoint", width_confidence=-1, depth_confidence=-1).eval().to(DEVICE)

app = FastAPI(title="FastAPI App")

reconstructions: dict[UUID, Reconstruction] = {}


INTR_ADAPTER: TypeAdapter[CameraIntrinsics] = TypeAdapter(CameraIntrinsics)
parse_camera = make_multipart_json_dep("camera", INTR_ADAPTER)


async def localize_image_against_reconstruction(map: Map, camera: Camera, image: bytes) -> Transform:
    # Load image into numpy buffer
    buffer = frombuffer(image, uint8)
    # Decode buffer into OpenCV BGR image array
    bgr_image = imdecode(buffer, IMREAD_COLOR)

    # Create RGB image tensor for NetVLAD
    rgb_image = cvtColor(bgr_image, COLOR_BGR2RGB)
    rgb_image_tensor = (
        from_numpy(rgb_image)  # H×W×3, uint8
        .permute(2, 0, 1)  # 3×H×W
        .unsqueeze(0)  # 1×3×H×W
        .to(device=DEVICE, dtype=torch_float32)
        / 255.0
    )  # Normalize

    # Create grayscale image tensor for SuperPoint
    grayscale_image = cvtColor(bgr_image, COLOR_BGR2GRAY)
    grayscale_image_tensor = (
        from_numpy(grayscale_image.astype(float32) / 255.0)
        .unsqueeze(0)  # 1×H×W
        .unsqueeze(0)  # 1×1×H×W
        .to(device=DEVICE, dtype=torch_float32)
    )

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
    sizes1 = torch.tensor([bgr_image.shape[:2]] * batch_size, device=DEVICE)

    print("Matching features")

    # Run LightGlue matcher
    with torch.inference_mode():
        match_tensors = LIGHTGLUE_MATCHER({
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

    # Estimate the camera pose using the 2D-3D correspondences
    pnp_result = absolute_pose_estimation(
        points2d,
        points3d,
        camera,
        estimation_options={"ransac": {"max_error": RANSAC_THRESHOLD}},
        refinement_options={},
    )

    if pnp_result is None:
        raise ValueError("Pose estimation failed")

    # return hstack((
    #     pnp_result["cam_from_world"].rotation.quat[[3, 0, 1, 2]],  # qw qx qy qz
    #     pnp_result["cam_from_world"].translation,
    # ))

    # world_from_cam = pnp_result["cam_from_world"].inverse()

    # return {
    #     "position": world_from_cam.translation.tolist(),
    #     "orientation": world_from_cam.rotation.quat[[3, 0, 1, 2]].tolist(),  # qw qx qy qz
    # }

    # position = world_from_cam.translation.tolist()
    # rotation = world_from_cam.rotation.quat[[3, 0, 1, 2]].tolist()  # qw qx qy qz

    # return Transform(
    #     position=Vector3(x=position[0], y=position[1], z=position[2]),
    #     rotation=Quaternion(w=rotation[0], x=rotation[1], y=rotation[2], z=rotation[3]),  # qw qx qy qz
    # )

    print("Pose estimation succeeded, returning cam_from_world")

    return Transform(
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
