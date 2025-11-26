from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Literal

from common.boto_clients import create_s3_client
from core.create_image_tensors import create_image_tensors
from core.h5 import write_features, write_global_descriptors
from core.lightglue import lightglue_match
from core.opq import encode_descriptors, train_opq_matrix, train_pq_quantizer, write_opq_matrix, write_pq_quantizer
from core.reconstruction_manifest import ReconstructionManifest
from neural_networks.models import load_DIR, load_lightglue, load_superpoint
from numpy import ascontiguousarray, float32, random, vstack
from numpy.typing import NDArray
from pycolmap._core import set_random_seed
from torch import cuda, inference_mode

from .colmap import run_reconstruction
from .metrics_builder import MetricsBuilder
from .options_builder import OptionsBuilder
from .pairs import generate_image_pairs, write_pairs
from .rig import load_capture_session_manifest
from .settings import get_settings

WORK_DIR = Path("/tmp/reconstruction")
CAPTURE_SESSION_DIRECTORY = WORK_DIR / "capture_session"


def main():
    device = "cuda" if cuda.is_available() else "cpu"
    print(f"Using device: {device}")

    settings = get_settings()
    s3_client = create_s3_client(
        s3_endpoint_url=settings.s3_endpoint_url,
        s3_access_key=settings.s3_access_key,
        s3_secret_key=settings.s3_secret_key,
    )

    def _put_reconstruction_object(key: str, body: bytes):
        print(f"Putting object in bucket {settings.reconstructions_bucket} with key {settings.reconstruction_id}/{key}")
        s3_client.put_object(
            Bucket=settings.reconstructions_bucket, Key=f"{settings.reconstruction_id}/{key}", Body=body
        )

    # Download and validate capture session manifest
    rigs = load_capture_session_manifest(
        settings.captures_bucket, settings.capture_id, s3_client, CAPTURE_SESSION_DIRECTORY
    )

    # Download and validate reconstruction manifest
    manifest = ReconstructionManifest.model_validate_json(
        s3_client.get_object(Bucket=settings.reconstructions_bucket, Key=f"{settings.reconstruction_id}/manifest.json")[
            "Body"
        ].read()
    )

    options = OptionsBuilder(manifest.options)
    metrics = MetricsBuilder()

    if manifest.options.random_seed is not None:
        random.seed(manifest.options.random_seed)
        set_random_seed(manifest.options.random_seed)

    # Generate image pairs
    pairs = generate_image_pairs(rigs, options.neighbors_count(), options.rotation_threshold_deg())
    file_name, file_bytes = write_pairs(pairs, WORK_DIR)
    _put_reconstruction_object(key=file_name, body=file_bytes)

    # Load DIR and SuperPoint models
    dir = load_DIR(device)
    superpoint = load_superpoint(max_num_keypoints=options.max_keypoints_per_image(), device=device)

    # Extract features
    global_descriptors: dict[str, NDArray[float32]] = {}
    keypoints: dict[str, NDArray[float32]] = {}
    descriptors: dict[str, NDArray[float32]] = {}
    sizes: dict[str, tuple[int, int]] = {}
    image_list: list[tuple[str, Literal["None", "90_CW", "180", "90_CCW"]]] = [
        (f"{rig_id}/{camera[0].id}/{frame_id}.jpg", camera[0].camera_config.rotation)
        for rig_id, rig in rigs.items()
        for camera in rig.cameras.values()
        for frame_id in rig.frame_poses.keys()
    ]
    for index, (image_name, rotation) in enumerate(image_list):
        print(f"Extracting features: image {index + 1} of {len(image_list)}")

        image_path = CAPTURE_SESSION_DIRECTORY / image_name
        (image, rgb_tensor, gray_tensor) = create_image_tensors(image_path.read_bytes(), rotation)

        # Write image back to disk, so incremental_mapping samples the processed image for point cloud colorization
        image.save(image_path)

        with inference_mode():
            dir_output = dir({"image": rgb_tensor.unsqueeze(0).to(device=device)})
            superpoint_output = superpoint({"image": gray_tensor.unsqueeze(0).to(device=device)})

        global_descriptors[image_name] = dir_output["global_descriptor"][0].cpu().numpy().astype(float32, copy=False)
        keypoints[image_name] = superpoint_output["keypoints"][0].cpu().numpy().astype(float32, copy=False)
        descriptors[image_name] = superpoint_output["descriptors"][0].cpu().numpy().astype(float32, copy=False)
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

    # Load LightGlue model
    lightglue = load_lightglue(device)

    # Match features
    match_indices = lightglue_match(lightglue, pairs, keypoints, descriptors, sizes, batch_size=32, device=device)

    # Run COLMAP reconstruction
    reconstruction = run_reconstruction(
        WORK_DIR, CAPTURE_SESSION_DIRECTORY, options, metrics, rigs, keypoints, pairs, match_indices
    )

    # Verify reconstruction was successful
    if reconstruction is None:
        print("Reconstruction failed, no model was created")
        manifest.status = "failed"
        manifest.error = "No model was created"
    else:
        # Write reconstruction to storage
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            reconstruction.write_text(str(temp_path))
            reconstruction.export_PLY(str(temp_path / "points3D.ply"))
            for file_path in temp_path.rglob("*"):
                if file_path.is_file():
                    _put_reconstruction_object(
                        key=f"sfm_model/{file_path.relative_to(temp_path)}", body=file_path.read_bytes()
                    )

    # Update and write reconstruction manifest
    manifest.metrics = metrics.metrics
    manifest.status = "succeeded"
    _put_reconstruction_object(key="manifest.json", body=manifest.model_dump_json().encode("utf-8"))


if __name__ == "__main__":
    main()
