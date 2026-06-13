from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from os import environ
from time import perf_counter
from typing import Any, cast

from core.axis_convention import AxisConvention, change_basis_unity_from_opencv_pose
from core.camera_config import PinholeCameraConfig
from core.image_preprocess import canonicalize_image, canonicalize_intrinsics
from core.lightglue import Descriptors, Keypoints, MatchIndices
from core.localization_metrics import RANSAC_THRESHOLD_DEFAULT, RETRIEVAL_TOP_K_DEFAULT, LocalizationMetrics
from core.model_wrappers import (
    LocalFeatureOutput,
    make_global_descriptor_extractor,
    make_local_feature_extractor,
    make_local_feature_matcher_for_tensors,
)
from core.opq import decode_descriptors
from core.model_wrappers import RetrievalDim
from core.tensor_types import TT
from core.transform import Float3, Float4, Transform
from numpy import asarray, float32, ndarray, sqrt, stack, vstack
from pycolmap import AbsolutePoseEstimationOptions, RANSACOptions
from pycolmap import Camera as ColmapCamera
from pycolmap._core import Rigid3d, estimate_and_refine_absolute_pose, set_random_seed  # type: ignore  # noqa: PLC2701 — no public API
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial.transform import Rotation
from torch import Tensor, cuda, inference_mode, manual_seed, topk  # type: ignore

from .build_metrics import build_localization_metrics
from core.calibration import CalibrationArtifact
from .map import Map
from .torch_ops import from_numpy, to

DEVICE = "cuda" if cuda.is_available() else "cpu"


# Seeded each call so localization_evaluations cache rows keyed on pipeline_version are
# reproducible — fit_calibration treats (reconstruction_id, frame_timestamp, retrieval_top_k,
# ransac_threshold, pipeline_version) as a deterministic cache key. cudnn-deterministic and
# CUBLAS_WORKSPACE_CONFIG are deliberately not enabled: the 10–30% latency cost outweighs
# the residual non-determinism, which is below the discrete inlier-set threshold the fit cares about.
LOCALIZER_RANDOM_SEED = 0

# Retrieval can pull look-alike images from distinct map regions; clustering camera centers by
# proximity lets each region be solved separately rather than blended into one wrong pose. A
# cluster must clear both floors to yield a pose; at most MAX_CLUSTERS_PER_QUERY are returned.
CLUSTER_LINKAGE_DISTANCE_METERS = 5.0
MIN_CLUSTER_CORRESPONDENCES = 12
MIN_CLUSTER_INLIERS = 30
MAX_CLUSTERS_PER_QUERY = 2

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

    print(f"Using device: {DEVICE}")

    global global_descriptor_extractor, local_feature_extractor, local_feature_matcher
    global_descriptor_extractor = make_global_descriptor_extractor(load_DIR(DEVICE))
    local_feature_extractor = make_local_feature_extractor(load_aliked(device=DEVICE))
    local_feature_matcher = make_local_feature_matcher_for_tensors(load_lightglue(DEVICE), DEVICE)


@inference_mode()
def localize_image_against_reconstruction(
    map: Map,
    camera: PinholeCameraConfig,
    axis_convention: AxisConvention,
    image_buffer: bytes,
    retrieval_top_k: int | None,
    ransac_threshold: float | None,
    pipeline_version: str,
    calibration: CalibrationArtifact,
) -> list[tuple[Transform, LocalizationMetrics]]:

    set_random_seed(LOCALIZER_RANDOM_SEED)
    manual_seed(LOCALIZER_RANDOM_SEED)

    # Per-stage timing instrumentation. CUDA kernels are async, so each GPU-bound stage ends
    # with cuda.synchronize() to attribute its true wall time rather than just kernel-launch.
    timings: dict[str, float] = {}

    def _gpu_sync() -> None:
        if DEVICE == "cuda":
            cuda.synchronize()

    t0 = perf_counter()

    # Extract features from query image
    image = canonicalize_image(image_buffer, camera.orientation)
    timings["canonicalize"] = perf_counter() - t0

    t = perf_counter()
    rgb_tensor = from_numpy(asarray(image, dtype=float32)).permute(2, 0, 1).div(255.0)
    query_keypoints_tensor, query_descriptors_tensor = local_feature_extractor(
        rgb_tensor.unsqueeze(0).to(device=DEVICE)
    )
    _gpu_sync()
    timings["aliked"] = perf_counter() - t

    t = perf_counter()
    query_descriptor: TT[RetrievalDim] = global_descriptor_extractor(rgb_tensor.unsqueeze(0).to(device=DEVICE))
    _gpu_sync()
    timings["dir"] = perf_counter() - t

    t = perf_counter()
    database_descriptors = to(from_numpy(map.descriptors), DEVICE)
    per_image_similarity = database_descriptors @ query_descriptor
    top_k = retrieval_top_k if retrieval_top_k is not None else RETRIEVAL_TOP_K_DEFAULT
    top_k_image_indices: list[int] = topk(per_image_similarity, top_k).indices.cpu().tolist()  # type: ignore
    matched_image_ids = [map.ordered_image_ids[i] for i in top_k_image_indices]
    timings["retrieval"] = perf_counter() - t

    # Cluster retrieved camera centers by proximity; a large span signals aliased multi-region retrieval.
    retrieved_centers = stack([map.images[image_id].projection_center().ravel() for image_id in matched_image_ids])
    retrieval_span_meters, num_clusters, cluster_labels = cluster_retrieved_images(
        retrieved_centers, CLUSTER_LINKAGE_DISTANCE_METERS
    )
    print(f"retrieval span(m): {retrieval_span_meters:.2f} clusters={num_clusters} image_ids={matched_image_ids}")

    t = perf_counter()
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
    _gpu_sync()
    timings["matching_setup"] = perf_counter() - t

    t = perf_counter()
    # Match features between query and database images
    pairs = [(str(image_id), "query") for image_id in matched_image_ids]

    match_indices = local_feature_matcher(pairs, keypoints, descriptors, sizes, len(pairs))
    _gpu_sync()
    timings["matching"] = perf_counter() - t

    # Create the COLMAP camera model and shared RANSAC options once; every per-cluster solve reuses them.
    width, height, *params = canonicalize_intrinsics(camera)
    pycolmap_camera = ColmapCamera(width=width, height=height, model="PINHOLE", params=params)  # noqa: N806 — pycolmap CV notation

    ransac_options = RANSACOptions()
    ransac_options.max_error = ransac_threshold if ransac_threshold is not None else RANSAC_THRESHOLD_DEFAULT
    estimation_options = AbsolutePoseEstimationOptions()
    estimation_options.ransac = ransac_options

    # Group each cluster's 2D-3D correspondences and raw match count over its own images.
    cluster_query_keypoints: dict[int, list[int]] = defaultdict(list)
    cluster_point3d_indices: dict[int, list[int]] = defaultdict(list)
    cluster_num_matches: dict[int, int] = defaultdict(int)
    for image_index, image_id in enumerate(matched_image_ids):
        label = int(cluster_labels[image_index])
        database_keypoint_indices, query_keypoint_indices = match_indices[(str(image_id), "query")]
        cluster_num_matches[label] += int(database_keypoint_indices.shape[0])

        for database_image_keypoint_index, query_image_keypoint_index in zip(
            database_keypoint_indices, query_keypoint_indices
        ):
            point2D = map.images[image_id].points2D[int(database_image_keypoint_index)]  # noqa: N806 — pycolmap CV notation

            if not point2D.has_point3D():
                continue

            cluster_query_keypoints[label].append(int(query_image_keypoint_index))
            cluster_point3d_indices[label].append(int(point2D.point3D_id))

    # Solve PnP per cluster; a wrong-region cluster shows weak inlier support and is dropped here.
    t = perf_counter()
    solved_clusters: list[tuple[int, Transform, LocalizationMetrics, list[int]]] = []
    for label, query_keypoints in cluster_query_keypoints.items():
        if len(query_keypoints) < MIN_CLUSTER_CORRESPONDENCES:
            continue

        points2D = keypoints["query"][query_keypoints].cpu().numpy()  # noqa: N806 — pycolmap CV notation
        points3D = vstack([map.points3D[i].xyz for i in cluster_point3d_indices[label]])  # noqa: N806 — pycolmap CV notation
        pnp_result = cast(
            dict[str, Any] | None,
            estimate_and_refine_absolute_pose(
                points2D, points3D, pycolmap_camera, estimation_options, return_covariance=True
            ),
        )

        if pnp_result is None or int(pnp_result["num_inliers"]) < MIN_CLUSTER_INLIERS:
            continue

        cam_from_world = cast(Rigid3d, pnp_result["cam_from_world"])
        translation = cam_from_world.translation
        rotation = cam_from_world.rotation.matrix()
        if axis_convention == AxisConvention.UNITY:
            translation, rotation = change_basis_unity_from_opencv_pose(translation, rotation)
        rotation = Rotation.from_matrix(rotation).as_quat()

        transform = Transform(
            translation=Float3(x=translation[0], y=translation[1], z=translation[2]),
            rotation=Float4(x=rotation[0], y=rotation[1], z=rotation[2], w=rotation[3]),
        )
        metrics = build_localization_metrics(
            pnp_result,
            points2D,
            points3D,
            pycolmap_camera,
            cluster_num_matches[label],
            width,
            height,
            pipeline_version,
            calibration,
            map,
        )
        cluster_image_ids = [
            matched_image_ids[i] for i in range(len(matched_image_ids)) if int(cluster_labels[i]) == label
        ]
        solved_clusters.append((int(pnp_result["num_inliers"]), transform, metrics, cluster_image_ids))
    timings["pnp"] = perf_counter() - t

    if not solved_clusters:
        raise LocalizationError("No retrieval cluster cleared the correspondence and inlier floors")

    # Keep the strongest clusters by inlier support for the client filter to arbitrate.
    solved_clusters.sort(key=lambda cluster: cluster[0], reverse=True)
    selected = solved_clusters[:MAX_CLUSTERS_PER_QUERY]

    timings["total"] = perf_counter() - t0
    print("localize timings(ms): " + " ".join(f"{k}={v * 1000:.0f}" for k, v in timings.items()))
    for num_inliers, _, _, cluster_image_ids in selected:
        print(f"cluster: inliers={num_inliers} images={cluster_image_ids}")

    return [(transform, metrics) for _, transform, metrics, _ in selected]


# Single-linkage clustering of retrieved camera centers: images whose centers fall within
# linkage_distance_meters land in one connected component. Returns (span, cluster count, per-image labels).
def cluster_retrieved_images(retrieved_centers: ndarray, linkage_distance_meters: float) -> tuple[float, int, ndarray]:
    pairwise_offsets = retrieved_centers[:, None, :] - retrieved_centers[None, :, :]
    pairwise_distances = sqrt((pairwise_offsets**2).sum(axis=-1))
    num_clusters, cluster_labels = connected_components(
        csr_matrix(pairwise_distances < linkage_distance_meters), directed=False
    )
    return float(pairwise_distances.max()), num_clusters, cluster_labels
