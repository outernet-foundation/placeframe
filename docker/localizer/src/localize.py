from __future__ import annotations

from collections.abc import Callable
from os import environ
from typing import Any, cast

from core.axis_convention import AxisConvention, change_basis_unity_from_opencv_pose
from core.calibration import CalibrationArtifact
from core.camera_config import PinholeCameraConfig
from core.image_preprocess import canonicalize_image, canonicalize_intrinsics, tile_image
from core.lightglue import Descriptors, Keypoints, MatchIndices
from core.localization_metrics import LocalizationMetrics
from core.model_wrappers import (
    LocalFeatureOutput,
    make_global_descriptor_extractor,
    make_local_feature_extractor,
    make_local_feature_matcher_for_tensors,
)
from core.opq import decode_descriptors
from core.image_preprocess import NumQueryTiles
from core.model_wrappers import RetrievalDim
from core.tensor_types import TT
from core.transform import Float3, Float4, Transform
from numpy import asarray, float32, vstack
from pycolmap import AbsolutePoseEstimationOptions, RANSACOptions
from pycolmap import Camera as ColmapCamera
from pycolmap._core import Rigid3d, estimate_and_refine_absolute_pose  # type: ignore  # noqa: PLC2701 — no public API
from scipy.spatial.transform import Rotation
from torch import Tensor, cuda, topk  # type: ignore

from .build_metrics import build_localization_metrics
from .map import Map
from .torch_ops import amax, from_numpy, matmul, permute, stack, to, transpose

DEVICE = "cuda" if cuda.is_available() else "cpu"

# Pipeline-tuning constants. Folded into pipeline_version (the localizer's git SHA), so changes
# bump pipeline_version automatically and the calibration loader hard-fails on mismatch.
RANSAC_THRESHOLD = 8.0
RETRIEVAL_TOP_K = 12

# Quality floor for accepting a localization. See the BAND-AID block in
# localize_image_against_reconstruction.
MIN_NUM_INLIERS = 50
MIN_INLIER_COVERAGE = 0.15

global_descriptor_extractor: Callable[[Tensor], TT[RetrievalDim]]
local_feature_extractor: Callable[[Tensor], LocalFeatureOutput]
local_feature_matcher: Callable[
    [list[tuple[str, str]], Keypoints, Descriptors, dict[str, tuple[int, int]], int],
    MatchIndices,
]


class LocalizationError(ValueError):
    pass


def load_models():
    if environ.get("CODEGEN"):
        return

    from neural_networks.models import load_aliked, load_DIR, load_lightglue
    from torch import set_grad_enabled

    print(f"Using device: {DEVICE}")

    # Turn off gradient calculations globally (we only do inference here)
    set_grad_enabled(False)

    global global_descriptor_extractor, local_feature_extractor, local_feature_matcher
    global_descriptor_extractor = make_global_descriptor_extractor(load_DIR(DEVICE))
    local_feature_extractor = make_local_feature_extractor(load_aliked(device=DEVICE))
    local_feature_matcher = make_local_feature_matcher_for_tensors(load_lightglue(DEVICE), DEVICE)


def localize_image_against_reconstruction(
    map: Map,
    camera: PinholeCameraConfig,
    axis_convention: AxisConvention,
    image_buffer: bytes,
    retrieval_top_k: int | None,
    ransac_threshold: float | None,
    pipeline_version: str,
    calibration: CalibrationArtifact,
) -> tuple[Transform, LocalizationMetrics]:
    if retrieval_top_k is None:
        retrieval_top_k = RETRIEVAL_TOP_K
    if ransac_threshold is None:
        ransac_threshold = RANSAC_THRESHOLD
    # Extract features from query image
    image = canonicalize_image(image_buffer, camera.orientation)
    rgb_tensor = from_numpy(asarray(image, dtype=float32)).permute(2, 0, 1).div(255.0)
    query_keypoints_tensor, query_descriptors_tensor = local_feature_extractor(
        rgb_tensor.unsqueeze(0).to(device=DEVICE)
    )

    descriptor_per_query_tile: list[TT[RetrievalDim]] = []
    for tile in tile_image(image):
        tile_tensor = from_numpy(asarray(tile, dtype=float32)).permute(2, 0, 1).div(255.0)
        descriptor_per_query_tile.append(global_descriptor_extractor(tile_tensor.unsqueeze(0).to(device=DEVICE)))
    query_tile_descriptors: TT[NumQueryTiles, RetrievalDim] = stack(descriptor_per_query_tile, dim=0)

    # Per-database-image similarity is the max over all (query_tile, database_tile) pairs for that image.
    database_descriptors = to(from_numpy(map.tile_descriptors), DEVICE)
    similarity_pairs = permute(matmul(query_tile_descriptors, transpose(database_descriptors, 1, 2)), (1, 0, 2))
    per_image_similarity = amax(similarity_pairs, dim=(0, 2))
    top_k_image_indices: list[int] = topk(per_image_similarity, retrieval_top_k).indices.cpu().tolist()  # type: ignore
    matched_image_ids = [map.ordered_image_ids[i] for i in top_k_image_indices]

    # Decode descriptors of matched database images
    descriptors = decode_descriptors(
        map.opq_matrix, map.product_quantizer, {image_id: map.pq_codes[image_id] for image_id in matched_image_ids}
    )

    # Prepare database image data for matching
    keypoints = Keypoints({
        str(image_id): from_numpy(map.keypoints[image_id]).to(DEVICE) for image_id in matched_image_ids
    })
    descriptors = Descriptors({
        str(image_id): from_numpy(descriptors[image_id]).to(DEVICE) for image_id in matched_image_ids
    })
    sizes = {str(image_id): map.image_sizes[str(image_id)] for image_id in matched_image_ids}

    # Prepare query image data for matching
    keypoints["query"] = query_keypoints_tensor.to(DEVICE)
    descriptors["query"] = query_descriptors_tensor.to(DEVICE)
    sizes["query"] = (image.height, image.width)

    # Match features between query and database images
    pairs = [(str(image_id), "query") for image_id in matched_image_ids]

    match_indices = local_feature_matcher(pairs, keypoints, descriptors, sizes, len(pairs))

    # Count raw LightGlue matches before 3D filtering
    num_matches = sum(match_indices[key][0].shape[0] for key in match_indices)

    # Collect 2D-3D correspondences
    query_keypoint_indices: list[int] = []
    point3d_indices: list[int] = []
    for image_id in matched_image_ids:
        for database_image_keypoint_index, query_image_keypoint_index in zip(*match_indices[(str(image_id), "query")]):
            point2D = map.images[image_id].points2D[int(database_image_keypoint_index)]  # noqa: N806 — pycolmap CV notation

            if not point2D.has_point3D():
                continue

            query_keypoint_indices.append(int(query_image_keypoint_index))
            point3d_indices.append(int(point2D.point3D_id))

    # Verify we have enough correspondences
    if not query_keypoint_indices:
        raise LocalizationError("No matching keypoints found")

    # Create COLMAP camera model
    width, height, *params = canonicalize_intrinsics(camera)
    pycolmap_camera = ColmapCamera(width=width, height=height, model="PINHOLE", params=params)

    # Set estimation options
    ransac_options = RANSACOptions()
    ransac_options.max_error = ransac_threshold
    estimation_options = AbsolutePoseEstimationOptions()
    estimation_options.ransac = ransac_options

    # Estimate pose
    points2D = keypoints["query"][query_keypoint_indices].cpu().numpy()  # noqa: N806 — pycolmap CV notation
    points3D = vstack([map.points3D[i].xyz for i in point3d_indices])  # noqa: N806 — pycolmap CV notation
    pnp_result = cast(
        dict[str, Any] | None,
        estimate_and_refine_absolute_pose(
            points2D, points3D, pycolmap_camera, estimation_options, return_covariance=True
        ),
    )

    # Check if pose estimation was successful
    if pnp_result is None:
        raise LocalizationError("Pose estimation failed")

    # Change basis if needed
    cam_from_world = cast(Rigid3d, pnp_result["cam_from_world"])
    translation = cam_from_world.translation
    rotation = cam_from_world.rotation.matrix()
    if axis_convention == AxisConvention.UNITY:
        translation, rotation = change_basis_unity_from_opencv_pose(translation, rotation)
    rotation = Rotation.from_matrix(rotation).as_quat()

    # Build final transform
    transform = Transform(
        translation=Float3(x=translation[0], y=translation[1], z=translation[2]),
        rotation=Float4(x=rotation[0], y=rotation[1], z=rotation[2], w=rotation[3]),
    )

    # Build metrics
    metrics = build_localization_metrics(
        pnp_result,
        points2D,
        points3D,
        pycolmap_camera,
        num_matches,
        width,
        height,
        pipeline_version,
        calibration,
    )

    # THIS IS A BAND-AID. Remove once the calibration system actually computes
    # meaningful confidence values from the localization result.
    #
    # build_metrics.py calls apply_global_calibration(calibration, Features.zeros()).
    # Zero-valued features mean the logistic regression sees no real inputs from
    # this localization, so metrics.confidence.{tight,loose} reduce to constants
    # (sigmoid of the model intercept under the identity-bootstrap calibration)
    # that are identical for a great pose and a garbage one. is_calibrated=True
    # is misleading — the model is fitted to nothing.
    #
    # Once features are plumbed through and the calibration model is refit against
    # labeled data, replace this with a confidence-based check, e.g.:
    #     if metrics.confidence.tight < TIGHT_MIN: raise LocalizationError(...)
    if metrics.num_inliers < MIN_NUM_INLIERS or metrics.inlier_coverage < MIN_INLIER_COVERAGE:
        raise LocalizationError(
            f"Below quality floor: num_inliers={metrics.num_inliers} (min {MIN_NUM_INLIERS}), "
            f"inlier_coverage={metrics.inlier_coverage:.3f} (min {MIN_INLIER_COVERAGE})"
        )

    # Success
    print(transform.model_dump_json(indent=2))
    print(metrics.model_dump_json(indent=2))
    return transform, metrics
