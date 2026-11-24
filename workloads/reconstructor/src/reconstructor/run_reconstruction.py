from __future__ import annotations

import tarfile
from collections.abc import Callable
from io import BytesIO
from json import dumps
from os import environ
from pathlib import Path
from typing import Any
from uuid import UUID

from placeframe_common.boto_clients import create_s3_client
from placeframe_core.camera_config import PinholeCameraConfig
from placeframe_core.capture_session_manifest import CaptureSessionManifest
from placeframe_core.image_preprocess import canonicalize_image
from placeframe_core.h5 import (
    DESCRIPTORS_FILE,
    GLOBAL_DESCRIPTORS_FILE,
    KEYPOINTS_FILE,
    read_descriptors,
    read_global_descriptors,
    read_keypoints,
    write_descriptors,
    write_features,
    write_global_descriptors,
    write_keypoints,
)
from placeframe_core.lightglue import DescriptorsArrays, KeypointsArrays, MatchIndices
from placeframe_core.model_wrappers import (
    LocalFeatureOutput,
    make_global_descriptor_extractor,
    make_local_feature_extractor,
    make_local_feature_matcher_for_arrays,
)
from placeframe_core.opq import (
    OPQ_MATRIX_FILE,
    PQ_QUANTIZER_FILE,
    encode_descriptors,
    read_opq_matrix,
    read_pq_quantizer,
    train_opq_matrix,
    train_pq_quantizer,
    write_opq_matrix,
    write_pq_quantizer,
)
from placeframe_core.reconstruction_metrics import ReconstructionMetrics
from placeframe_core.reconstruction_options import ReconstructionOptions
from placeframe_core.model_wrappers import RetrievalDim
from placeframe_core.tensor_types import TT
from neural_networks.models import load_aliked, load_DIR, load_lightglue
from numpy import (
    array,
    asarray,
    ascontiguousarray,
    concatenate,
    float32,
    float64,
    int64,
    intp,
    random,
    savez_compressed,
    uint32,
    vstack,
)
from numpy.typing import NDArray  # noqa: TID251 — tracked in PLE-233
from placeframe_lease_server_client import ReconstructionStatus
from pycolmap._core import set_random_seed  # noqa: PLC2701 — no public API
from pydantic import TypeAdapter
from torch import Tensor, cuda, from_numpy, inference_mode  # type: ignore

from .colmap import COLMAP_DB_FILE, run_colmap_reconstruction
from .keyframes import select_keyframes_by_distance
from .metrics_builder import MetricsBuilder
from .options_builder import OptionsBuilder
from .pairs import generate_image_pairs, write_pairs, write_pairs_with_source
from .progress_publisher import ReconstructionPublisher
from .rig import Rig
from .settings import get_settings
from .shards import (
    FEATURE_SHARD_PREFIX,
    FEATURE_SHARD_SIZE,
    MATCHES_FILE,
    MATCH_SHARD_PREFIX,
    MATCH_SHARD_SIZE,
    OPQ_MARKER_KEY,
    PQ_MARKER_KEY,
    SHARD_PAIRS_FILE,
    SHARD_SIZES_FILE,
    TWO_VIEW_GEOMETRIES_FILE,
    VERIFICATION_SHARD_PREFIX,
    fetch_valid_shard_indexes,
    first_unmarked_index,
    get_object_bytes,
    load_stage_artifact,
    shard_count,
)
from .uploader import ArtifactUploader, compute_options_hash

DEVICE = "cuda" if cuda.is_available() else "cpu"

WORK_DIR = Path("/tmp/reconstruction")
CAPTURE_SESSION_DIRECTORY = WORK_DIR / "capture_session"

SIZES_ADAPTER = TypeAdapter(dict[str, tuple[int, int]])

COMPRESSION_OPQ_NUMBER_OF_SUBVECTORS = 16
COMPRESSION_OPQ_NUMBER_OF_BITS_PER_SUBVECTOR = 8
COMPRESSION_OPQ_NUMBER_OF_TRAINING_ITERATIONS = 20
LIGHTGLUE_BATCH_SIZE = 16

global_descriptor_extractor: Callable[[Tensor], TT[RetrievalDim]]
local_feature_extractor: Callable[[Tensor], LocalFeatureOutput]
local_feature_matcher: Callable[
    [
        list[tuple[str, str]],
        KeypointsArrays,
        DescriptorsArrays,
        dict[str, tuple[int, int]],
        int,
        Callable[[int], None] | None,
    ],
    MatchIndices,
]

# Underlying ALIKED model retained for per-job `dkd.n_limit` configuration; the typed wrapper
# above is the call-path entry point.
_aliked_model: Any = None


def load_models():
    print(f"Using device: {DEVICE}")

    global _aliked_model, global_descriptor_extractor, local_feature_extractor, local_feature_matcher
    _aliked_model = load_aliked(device=DEVICE)
    global_descriptor_extractor = make_global_descriptor_extractor(load_DIR(DEVICE))
    local_feature_extractor = make_local_feature_extractor(_aliked_model)
    local_feature_matcher = make_local_feature_matcher_for_arrays(load_lightglue(DEVICE), DEVICE)


@inference_mode()
def run_reconstruction(
    capture_id: UUID,
    reconstruction_options: ReconstructionOptions,
    publisher: ReconstructionPublisher,
    uploader: ArtifactUploader,
) -> ReconstructionMetrics:

    settings = get_settings()
    s3_client = create_s3_client(
        s3_endpoint_url=settings.s3_endpoint_url,
        s3_access_key=settings.s3_access_key,
        s3_secret_key=settings.s3_secret_key,
    )

    print(
        f"Downloading capture session archive for capture session ID: {capture_id} from bucket {settings.captures_bucket}"
    )
    bytes = get_object_bytes(s3_client, settings.captures_bucket, f"{capture_id}.tar")
    print(f"Downloaded capture session archive, size: {len(bytes)} bytes")
    # Download and validate capture session manifest
    with tarfile.open(fileobj=BytesIO(bytes), mode="r:*") as tar:
        tar.extractall(path=CAPTURE_SESSION_DIRECTORY)

    with open(CAPTURE_SESSION_DIRECTORY / "manifest.json", "rb") as file:
        capture_session_manifest = CaptureSessionManifest.model_validate_json(file.read().decode("utf-8"))

    held_out = (
        set(reconstruction_options.held_out_frame_timestamps)
        if reconstruction_options.held_out_frame_timestamps
        else None
    )

    # Load rigs (applying axis convention transformations as needed)
    rigs = {
        rig.id: Rig(
            rig,
            capture_session_manifest.axis_convention,
            (CAPTURE_SESSION_DIRECTORY / f"{rig.id}/frames.csv").read_text(),
            held_out_frame_timestamps=held_out,
        )
        for rig in capture_session_manifest.rigs
    }

    is_multi_camera_capture = any(rig.is_multi_camera for rig in rigs.values())
    options = OptionsBuilder(reconstruction_options, is_multi_camera_capture=is_multi_camera_capture)

    for rig in rigs.values():
        ordered_frame_ids = sorted(rig.frame_poses.keys(), key=int)
        translations_by_frame_id: dict[str, NDArray[float64]] = {
            frame_id: rig.frame_poses[frame_id].translation for frame_id in ordered_frame_ids
        }
        kept_frame_ids = set(
            select_keyframes_by_distance(
                ordered_frame_ids,
                translations_by_frame_id,
                min_distance_m=options.keyframe_min_distance_m(),
            )
        )
        rig.frame_poses = {frame_id: pose for frame_id, pose in rig.frame_poses.items() if frame_id in kept_frame_ids}
        print(f"Rig {rig.id}: kept {len(rig.frame_poses)} of {len(ordered_frame_ids)} frames as keyframes (distance)")

    if reconstruction_options.deterministic_seed is not None:
        random.seed(reconstruction_options.deterministic_seed)  # noqa: NPY002 — pycolmap reads numpy's global random state; can't use default_rng()
        set_random_seed(reconstruction_options.deterministic_seed)

    # Apply per-reconstruction keypoint cap by mutating the DKD module's threshold-mode n_limit.
    # ALIKED itself is loaded once at startup; only this cap is per-job.
    _aliked_model.dkd.n_limit = options.max_keypoints_per_image()

    # Extract features
    global_descriptors: dict[str, NDArray[float32]] = {}  # noqa: TID251 — tracked in PLE-233
    keypoints = KeypointsArrays({})
    descriptors = DescriptorsArrays({})
    sizes: dict[str, tuple[int, int]] = {}
    image_list: list[tuple[str, PinholeCameraConfig]] = [
        (f"{rig_id}/{camera[0].id}/{frame_id}.jpg", camera[0].camera_config)
        for rig_id, rig in rigs.items()
        for camera in rig.cameras.values()
        for frame_id in rig.frame_poses.keys()
    ]

    reconstruction_id = publisher.reconstruction_id
    options_hash = compute_options_hash(reconstruction_options)
    pipeline_version = environ["RECONSTRUCTOR_SHA"]

    # Rebuild state from shard markers that match this lease, so every shard loop starts at the first unmarked shard
    valid_feature_indexes = fetch_valid_shard_indexes(
        s3_client,
        settings.reconstructions_bucket,
        reconstruction_id,
        FEATURE_SHARD_PREFIX,
        options_hash,
        pipeline_version,
    )
    valid_match_indexes = fetch_valid_shard_indexes(
        s3_client,
        settings.reconstructions_bucket,
        reconstruction_id,
        MATCH_SHARD_PREFIX,
        options_hash,
        pipeline_version,
    )
    valid_verification_indexes = fetch_valid_shard_indexes(
        s3_client,
        settings.reconstructions_bucket,
        reconstruction_id,
        VERIFICATION_SHARD_PREFIX,
        options_hash,
        pipeline_version,
    )
    for shard_index in sorted(valid_feature_indexes):
        shard_prefix = f"{reconstruction_id}/{FEATURE_SHARD_PREFIX}/{shard_index:05d}"
        shard_directory = WORK_DIR / FEATURE_SHARD_PREFIX / f"{shard_index:05d}"
        shard_directory.mkdir(parents=True, exist_ok=True)
        sizes_body = get_object_bytes(s3_client, settings.reconstructions_bucket, f"{shard_prefix}/{SHARD_SIZES_FILE}")
        (shard_directory / SHARD_SIZES_FILE).write_bytes(sizes_body)
        for shard_file_name in (KEYPOINTS_FILE, DESCRIPTORS_FILE, GLOBAL_DESCRIPTORS_FILE):
            shard_file_body = get_object_bytes(
                s3_client, settings.reconstructions_bucket, f"{shard_prefix}/{shard_file_name}"
            )
            (shard_directory / shard_file_name).write_bytes(shard_file_body)

        shard_sizes = SIZES_ADAPTER.validate_json(sizes_body)
        shard_image_names = shard_sizes.keys()
        keypoints.update(read_keypoints(shard_directory, shard_image_names))
        descriptors.update(read_descriptors(shard_directory, shard_image_names))
        global_descriptors.update(read_global_descriptors(shard_directory, shard_image_names))
        sizes.update(shard_sizes)

    publisher.set_phase(ReconstructionStatus.EXTRACTING_FEATURES, total=len(image_list))
    feature_shard_count = shard_count(len(image_list), FEATURE_SHARD_SIZE)
    first_feature_shard = first_unmarked_index(feature_shard_count, valid_feature_indexes)
    image_progress = 0
    for shard_index in range(feature_shard_count):
        publisher.raise_if_lease_lost()
        shard_image_list = image_list[shard_index * FEATURE_SHARD_SIZE : (shard_index + 1) * FEATURE_SHARD_SIZE]

        # Refresh only the canonical images on disk because shards before the first unmarked one are already uploaded
        if shard_index < first_feature_shard:
            for image_name, camera_config in shard_image_list:
                image_progress += 1
                publisher.on_progress(image_progress)
                _write_canonical_image(image_name, camera_config)
            continue

        shard_keypoints: dict[str, NDArray[float32]] = {}
        shard_descriptors: dict[str, NDArray[float32]] = {}
        shard_global_descriptors: dict[str, NDArray[float32]] = {}
        shard_sizes: dict[str, tuple[int, int]] = {}
        for image_name, camera_config in shard_image_list:
            image_progress += 1
            publisher.on_progress(image_progress)

            image = _write_canonical_image(image_name, camera_config)
            rgb_tensor = from_numpy(asarray(image, dtype=float32)).permute(2, 0, 1).div(255.0)

            image_descriptor = global_descriptor_extractor(rgb_tensor.unsqueeze(0).to(device=DEVICE))
            image_keypoints, image_descriptors = local_feature_extractor(rgb_tensor.unsqueeze(0).to(device=DEVICE))

            shard_global_descriptors[image_name] = image_descriptor.cpu().numpy().astype(float32, copy=False)
            shard_keypoints[image_name] = image_keypoints.cpu().numpy().astype(float32, copy=False)
            shard_descriptors[image_name] = image_descriptors.cpu().numpy().astype(float32, copy=False)
            shard_sizes[image_name] = (image.height, image.width)

        keypoints.update(shard_keypoints)
        descriptors.update(shard_descriptors)
        global_descriptors.update(shard_global_descriptors)
        sizes.update(shard_sizes)

        shard_directory = WORK_DIR / FEATURE_SHARD_PREFIX / f"{shard_index:05d}"
        shard_directory.mkdir(parents=True, exist_ok=True)
        shard_files: dict[str, bytes] = {}
        for write_shard_files, shard_subset in (
            (write_keypoints, shard_keypoints),
            (write_descriptors, shard_descriptors),
            (write_global_descriptors, shard_global_descriptors),
        ):
            shard_file_name, shard_file_bytes = write_shard_files(shard_directory, shard_subset)
            shard_files[shard_file_name] = shard_file_bytes

        shard_files[SHARD_SIZES_FILE] = dumps(
            {image_name: [height, width] for image_name, (height, width) in shard_sizes.items()}, sort_keys=True
        ).encode("utf-8")
        uploader.put_shard(
            f"{FEATURE_SHARD_PREFIX}/{shard_index:05d}",
            shard_files,
            {"shard_index": shard_index, "shard_count": feature_shard_count},
        )

    # Write global descriptors to storage
    file_name, file_bytes = write_global_descriptors(WORK_DIR, global_descriptors)
    uploader.put_artifact(file_name, file_bytes)

    pairs = generate_image_pairs(
        rigs,
        global_descriptors,
        options.sequential_window_m(),
        options.retrieval_neighbors(),
        options.retrieval_min_score(),
    )
    file_name, file_bytes = write_pairs(pairs, WORK_DIR)
    uploader.put_artifact(file_name, file_bytes)
    file_name, file_bytes = write_pairs_with_source(pairs, WORK_DIR)
    uploader.put_artifact(file_name, file_bytes)

    # Combine all descriptors into a single array for training OPQ and PQ
    descriptor_array = ascontiguousarray(vstack([descriptor for descriptor in descriptors.values()]), dtype=float32)

    # Train OPQ matrix
    publisher.set_phase(ReconstructionStatus.TRAINING_OPQ_MATRIX)
    opq_matrix_bytes = load_stage_artifact(
        s3_client,
        settings.reconstructions_bucket,
        reconstruction_id,
        OPQ_MARKER_KEY,
        OPQ_MATRIX_FILE,
        options_hash,
        pipeline_version,
    )
    if opq_matrix_bytes is not None:
        (WORK_DIR / OPQ_MATRIX_FILE).write_bytes(opq_matrix_bytes)
    if opq_matrix_bytes is None:
        trained_opq_matrix = train_opq_matrix(
            COMPRESSION_OPQ_NUMBER_OF_SUBVECTORS,
            COMPRESSION_OPQ_NUMBER_OF_TRAINING_ITERATIONS,
            descriptor_array,
        )
        file_name, file_bytes = write_opq_matrix(trained_opq_matrix, WORK_DIR)
        uploader.put_artifact(file_name, file_bytes)
        uploader.put_stage_marker(OPQ_MARKER_KEY, {file_name: file_bytes})
    opq_matrix = read_opq_matrix(WORK_DIR)

    # Train PQ quantizer
    publisher.set_phase(ReconstructionStatus.TRAINING_PRODUCT_QUANTIZER)
    pq_quantizer_bytes = load_stage_artifact(
        s3_client,
        settings.reconstructions_bucket,
        reconstruction_id,
        PQ_MARKER_KEY,
        PQ_QUANTIZER_FILE,
        options_hash,
        pipeline_version,
    )
    if pq_quantizer_bytes is not None:
        (WORK_DIR / PQ_QUANTIZER_FILE).write_bytes(pq_quantizer_bytes)
    if pq_quantizer_bytes is None:
        trained_product_quantizer = train_pq_quantizer(
            COMPRESSION_OPQ_NUMBER_OF_SUBVECTORS,
            COMPRESSION_OPQ_NUMBER_OF_BITS_PER_SUBVECTOR,
            opq_matrix,
            descriptor_array,
        )
        file_name, file_bytes = write_pq_quantizer(trained_product_quantizer, WORK_DIR)
        uploader.put_artifact(file_name, file_bytes)
        uploader.put_stage_marker(PQ_MARKER_KEY, {file_name: file_bytes})
    product_quantizer = read_pq_quantizer(WORK_DIR)

    # Encode image descriptors
    image_codes = encode_descriptors(opq_matrix, product_quantizer, descriptors)
    file_name, file_bytes = write_features(WORK_DIR, keypoints, image_codes)
    uploader.put_artifact(file_name, file_bytes)

    image_name_pairs: list[tuple[str, str]] = [(pair.image_a, pair.image_b) for pair in pairs]

    # Match features
    publisher.set_phase(ReconstructionStatus.MATCHING_FEATURES, total=len(pairs))
    match_indices = local_feature_matcher(
        image_name_pairs,
        keypoints,
        descriptors,
        sizes,
        LIGHTGLUE_BATCH_SIZE,
        publisher.on_progress,
    )
    if cuda.is_available():
        cuda.empty_cache()

    # Shard only the upload of the matcher's outputs, because the array matcher runs whole under one descriptor transfer
    image_index_by_name = {
        image_name: image_index for image_index, (image_name, _camera_config) in enumerate(image_list)
    }
    match_shard_count = shard_count(len(pairs), MATCH_SHARD_SIZE)
    first_match_shard = first_unmarked_index(match_shard_count, valid_match_indexes)
    for shard_index in range(first_match_shard, match_shard_count):
        publisher.raise_if_lease_lost()
        shard_pairs = pairs[shard_index * MATCH_SHARD_SIZE : (shard_index + 1) * MATCH_SHARD_SIZE]
        pair_names: list[list[str]] = []
        pair_first: list[int] = []
        pair_second: list[int] = []
        match_offsets = [0]
        match_a_parts: list[NDArray[uint32]] = []
        match_b_parts: list[NDArray[uint32]] = []
        for pair in shard_pairs:
            indices_a, indices_b = match_indices.get((pair.image_a, pair.image_b)) or (
                array([], dtype=intp),
                array([], dtype=intp),
            )
            pair_names.append([pair.image_a, pair.image_b])
            pair_first.append(image_index_by_name[pair.image_a])
            pair_second.append(image_index_by_name[pair.image_b])
            match_a_parts.append(indices_a.astype(uint32, copy=False))
            match_b_parts.append(indices_b.astype(uint32, copy=False))
            match_offsets.append(match_offsets[-1] + len(indices_a))

        matches_buffer = BytesIO()
        savez_compressed(
            matches_buffer,
            pair_first=array(pair_first, dtype=int64),
            pair_second=array(pair_second, dtype=int64),
            match_a=concatenate(match_a_parts),
            match_b=concatenate(match_b_parts),
            match_offsets=array(match_offsets, dtype=int64),
        )
        uploader.put_shard(
            f"{MATCH_SHARD_PREFIX}/{shard_index:05d}",
            {
                SHARD_PAIRS_FILE: dumps(pair_names).encode("utf-8"),
                MATCHES_FILE: matches_buffer.getvalue(),
            },
            {"shard_index": shard_index, "shard_count": match_shard_count},
        )

    metrics_builder = MetricsBuilder()

    # Download each completed verification shard for replay in run_colmap_reconstruction
    for shard_index in sorted(valid_verification_indexes):
        shard_prefix = f"{reconstruction_id}/{VERIFICATION_SHARD_PREFIX}/{shard_index:05d}"
        shard_directory = WORK_DIR / VERIFICATION_SHARD_PREFIX / f"{shard_index:05d}"
        shard_directory.mkdir(parents=True, exist_ok=True)
        for shard_file_name in (SHARD_PAIRS_FILE, TWO_VIEW_GEOMETRIES_FILE):
            shard_file_body = get_object_bytes(
                s3_client, settings.reconstructions_bucket, f"{shard_prefix}/{shard_file_name}"
            )
            (shard_directory / shard_file_name).write_bytes(shard_file_body)

    # Run COLMAP reconstruction
    sfm_output_path = WORK_DIR / "sfm_output"
    sfm_output_path.mkdir(parents=True, exist_ok=True)
    reconstruction = run_colmap_reconstruction(
        WORK_DIR,
        sfm_output_path,
        CAPTURE_SESSION_DIRECTORY,
        options,
        metrics_builder,
        rigs,
        keypoints,
        pairs,
        match_indices,
        publisher,
        uploader,
        valid_verification_indexes,
    )

    publisher.raise_if_lease_lost()

    # Verify reconstruction was successful and write to storage

    uploader.drain()
    if reconstruction is None:
        print("Reconstruction failed, no model was created")
        metrics_builder.metrics.successful = False
        return metrics_builder.metrics

    for file_path in sfm_output_path.rglob("*"):
        if file_path.is_file():
            uploader.put_artifact(
                f"sfm_model/{file_path.relative_to(sfm_output_path)}",
                file_path.read_bytes(),
            )

    uploader.put_artifact(COLMAP_DB_FILE, (WORK_DIR / COLMAP_DB_FILE).read_bytes())

    uploader.drain()

    publisher.finalize_timings()
    metrics_builder.metrics.phase_timings = publisher.phase_timings
    metrics_builder.metrics.pipeline_version = pipeline_version

    metrics_builder.metrics.successful = True
    return metrics_builder.metrics


def _write_canonical_image(image_name: str, camera_config: PinholeCameraConfig):
    image_path = CAPTURE_SESSION_DIRECTORY / image_name
    image = canonicalize_image(image_path.read_bytes(), camera_config.orientation)

    # Write the processed image back to disk because incremental_mapping samples it for point cloud colorization
    image.save(image_path)
    return image
