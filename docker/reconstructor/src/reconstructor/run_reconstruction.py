from __future__ import annotations

import tarfile
from collections.abc import Callable
from io import BytesIO
from pathlib import Path
from typing import Any
from uuid import UUID

from common.boto_clients import create_s3_client
from core.camera_config import PinholeCameraConfig
from core.capture_session_manifest import CaptureSessionManifest
from core.image_preprocess import canonicalize_image, tile_image
from core.h5 import write_features, write_global_descriptors
from core.lightglue import DescriptorsArrays, KeypointsArrays, MatchIndices
from core.model_wrappers import (
    LocalFeatureOutput,
    make_global_descriptor_extractor,
    make_local_feature_extractor,
    make_local_feature_matcher_for_arrays,
)
from core.opq import encode_descriptors, train_opq_matrix, train_pq_quantizer, write_opq_matrix, write_pq_quantizer
from core.reconstruction_manifest import ReconstructionManifest
from core.model_wrappers import RetrievalDim
from core.tensor_types import TT
from neural_networks.models import load_aliked, load_DIR, load_lightglue
from numpy import asarray, ascontiguousarray, float32, random, stack, vstack
from numpy.typing import NDArray  # noqa: TID251 — Phase T piece 3 follow-up migration
from pycolmap._core import set_random_seed  # noqa: PLC2701 — no public API
from torch import Tensor, cuda, from_numpy, set_grad_enabled  # type: ignore

from .colmap import run_colmap_reconstruction
from .metrics_builder import MetricsBuilder
from .options_builder import OptionsBuilder
from .pairs import generate_image_pairs, write_pairs
from .rig import Rig
from .settings import get_settings

DEVICE = "cuda" if cuda.is_available() else "cpu"

WORK_DIR = Path("/tmp/reconstruction")
CAPTURE_SESSION_DIRECTORY = WORK_DIR / "capture_session"

global_descriptor_extractor: Callable[[Tensor], TT[RetrievalDim]]
local_feature_extractor: Callable[[Tensor], LocalFeatureOutput]
local_feature_matcher: Callable[
    [list[tuple[str, str]], KeypointsArrays, DescriptorsArrays, dict[str, tuple[int, int]], int],
    MatchIndices,
]

# Underlying ALIKED model retained for per-job `dkd.n_limit` configuration; the typed wrapper
# above is the call-path entry point.
_aliked_model: Any = None


def load_models():
    print(f"Using device: {DEVICE}")

    # Turn off gradient calculations globally (we only do inference here)
    set_grad_enabled(False)

    global _aliked_model, global_descriptor_extractor, local_feature_extractor, local_feature_matcher
    _aliked_model = load_aliked(device=DEVICE)
    global_descriptor_extractor = make_global_descriptor_extractor(load_DIR(DEVICE))
    local_feature_extractor = make_local_feature_extractor(_aliked_model)
    local_feature_matcher = make_local_feature_matcher_for_arrays(load_lightglue(DEVICE), DEVICE)


def run_reconstruction(reconstruction_id: UUID, capture_id: UUID):

    settings = get_settings()
    s3_client = create_s3_client(
        minio_endpoint_url=settings.minio_endpoint_url,
        minio_access_key=settings.minio_access_key,
        minio_secret_key=settings.minio_secret_key,
    )

    def _put_reconstruction_object(key: str, body: bytes):
        print(f"Putting object in bucket {settings.reconstructions_bucket} with key {reconstruction_id}/{key}")
        s3_client.put_object(Bucket=settings.reconstructions_bucket, Key=f"{reconstruction_id}/{key}", Body=body)

    print(
        f"Downloading capture session archive for capture session ID: {capture_id} from bucket {settings.captures_bucket}"
    )
    bytes = s3_client.get_object(Bucket=settings.captures_bucket, Key=f"{capture_id}.tar")["Body"].read()
    print(f"Downloaded capture session archive, size: {len(bytes)} bytes")
    # Download and validate capture session manifest
    with tarfile.open(fileobj=BytesIO(bytes), mode="r:*") as tar:
        tar.extractall(path=CAPTURE_SESSION_DIRECTORY)

    with open(CAPTURE_SESSION_DIRECTORY / "manifest.json", "rb") as file:
        capture_session_manifest = CaptureSessionManifest.model_validate_json(file.read().decode("utf-8"))

    # Load rigs (applying axis convention transformations as needed)
    rigs = {
        rig.id: Rig(
            rig,
            capture_session_manifest.axis_convention,
            (CAPTURE_SESSION_DIRECTORY / f"{rig.id}/frames.csv").read_text(),
        )
        for rig in capture_session_manifest.rigs
    }

    # Download and validate reconstruction manifest
    manifest = ReconstructionManifest.model_validate_json(
        s3_client.get_object(Bucket=settings.reconstructions_bucket, Key=f"{reconstruction_id}/manifest.json")[
            "Body"
        ].read()
    )

    options = OptionsBuilder(manifest.options)
    metrics = MetricsBuilder()

    if manifest.options.random_seed is not None:
        random.seed(manifest.options.random_seed)  # noqa: NPY002 — pycolmap reads numpy's global random state; can't use default_rng()
        set_random_seed(manifest.options.random_seed)

    # Apply per-reconstruction keypoint cap by mutating the DKD module's threshold-mode n_limit.
    # ALIKED itself is loaded once at startup; only this cap is per-job.
    _aliked_model.dkd.n_limit = options.max_keypoints_per_image()

    # Generate image pairs
    pairs = generate_image_pairs(rigs, options.neighbors_count(), options.rotation_threshold_deg())
    file_name, file_bytes = write_pairs(pairs, WORK_DIR)
    _put_reconstruction_object(key=file_name, body=file_bytes)

    # Extract features
    global_descriptors: dict[str, NDArray[float32]] = {}  # noqa: TID251 — Phase T piece 3 follow-up migration
    keypoints = KeypointsArrays({})
    descriptors = DescriptorsArrays({})
    sizes: dict[str, tuple[int, int]] = {}
    image_list: list[tuple[str, PinholeCameraConfig]] = [
        (f"{rig_id}/{camera[0].id}/{frame_id}.jpg", camera[0].camera_config)
        for rig_id, rig in rigs.items()
        for camera in rig.cameras.values()
        for frame_id in rig.frame_poses.keys()
    ]
    for index, (image_name, camera_config) in enumerate(image_list):
        print(f"Extracting features: image {index + 1} of {len(image_list)}")

        image_path = CAPTURE_SESSION_DIRECTORY / image_name
        image = canonicalize_image(image_path.read_bytes(), camera_config.orientation)
        rgb_tensor = from_numpy(asarray(image, dtype=float32)).permute(2, 0, 1).div(255.0)

        # Write image back to disk, so incremental_mapping samples the processed image for point cloud colorization
        image.save(image_path)

        tile_descriptors: list[TT[RetrievalDim]] = []
        for tile in tile_image(image):
            tile_tensor = from_numpy(asarray(tile, dtype=float32)).permute(2, 0, 1).div(255.0)
            tile_descriptors.append(global_descriptor_extractor(tile_tensor.unsqueeze(0).to(device=DEVICE)))

        image_keypoints, image_descriptors = local_feature_extractor(rgb_tensor.unsqueeze(0).to(device=DEVICE))

        global_descriptors[image_name] = stack(
            [tile_descriptor.cpu().numpy().astype(float32, copy=False) for tile_descriptor in tile_descriptors], axis=0
        )
        keypoints[image_name] = image_keypoints.cpu().numpy().astype(float32, copy=False)
        descriptors[image_name] = image_descriptors.cpu().numpy().astype(float32, copy=False)
        sizes[image_name] = (image.height, image.width)

    # Write global descriptors to storage
    file_name, file_bytes = write_global_descriptors(WORK_DIR, global_descriptors)
    _put_reconstruction_object(key=file_name, body=file_bytes)

    # Update metrics
    metrics.metrics.average_keypoints_per_image = float(
        sum(len(keypoints[name]) for name in keypoints.keys()) / len(keypoints)
    )

    # Combine all descriptors into a single array for training OPQ and PQ
    descriptor_array = ascontiguousarray(vstack([descriptor for descriptor in descriptors.values()]), dtype=float32)

    # Train OPQ matrix
    opq_matrix = train_opq_matrix(
        options.compression_opq_number_of_subvectors(),
        options.compression_opq_number_of_training_iterations(),
        descriptor_array,
    )
    file_name, file_bytes = write_opq_matrix(opq_matrix, WORK_DIR)
    _put_reconstruction_object(key=file_name, body=file_bytes)

    # Train PQ quantizer
    product_quantizer = train_pq_quantizer(
        options.compression_opq_number_of_subvectors(),
        options.compression_opq_number_of_bits_per_subvector(),
        opq_matrix,
        descriptor_array,
    )
    file_name, file_bytes = write_pq_quantizer(product_quantizer, WORK_DIR)
    _put_reconstruction_object(key=file_name, body=file_bytes)

    # Encode image descriptors
    image_codes = encode_descriptors(opq_matrix, product_quantizer, descriptors)
    file_name, file_bytes = write_features(WORK_DIR, keypoints, image_codes)
    _put_reconstruction_object(key=file_name, body=file_bytes)

    # Match features
    match_indices = local_feature_matcher(pairs, keypoints, descriptors, sizes, options.lightglue_batch_size())
    if cuda.is_available():
        cuda.empty_cache()

    # Run COLMAP reconstruction
    sfm_output_path = WORK_DIR / "sfm_output"
    sfm_output_path.mkdir(parents=True, exist_ok=True)
    reconstruction = run_colmap_reconstruction(
        WORK_DIR, sfm_output_path, CAPTURE_SESSION_DIRECTORY, options, metrics, rigs, keypoints, pairs, match_indices
    )

    # Verify reconstruction was successful and write to storage

    if reconstruction is None:
        print("Reconstruction failed, no model was created")
        manifest.status = "failed"
        manifest.error = "No model was created"
    else:
        for file_path in sfm_output_path.rglob("*"):
            if file_path.is_file():
                _put_reconstruction_object(
                    key=f"sfm_model/{file_path.relative_to(sfm_output_path)}", body=file_path.read_bytes()
                )

    # Update and write reconstruction manifest
    manifest.metrics = metrics.metrics
    manifest.status = "succeeded"
    _put_reconstruction_object(key="manifest.json", body=manifest.model_dump_json().encode("utf-8"))
