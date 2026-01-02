from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Mapping, cast
from uuid import UUID

from core.h5 import FEATURES_FILE, GLOBAL_DESCRIPTORS_FILE, read_features, read_global_descriptors
from core.opq import OPQ_MATRIX_FILE, PQ_QUANTIZER_FILE, read_opq_matrix, read_pq_quantizer
from faiss import (  # type: ignore
    OPQMatrix,
    ProductQuantizer,
)
from numpy import float32, stack, uint8
from numpy.typing import NDArray
from pycolmap import Reconstruction
from pycolmap._core import ImageMap, Point3DMap

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client
else:
    S3Client = Any


@dataclass(frozen=True)
class Map:
    points3D: Point3DMap
    images: ImageMap
    ordered_image_ids: list[int]
    image_sizes: dict[str, tuple[int, int]]
    keypoints: dict[int, NDArray[float32]]
    pq_codes: dict[int, NDArray[uint8]]
    global_descriptors_matrix: NDArray[float32]
    opq_matrix: OPQMatrix
    product_quantizer: ProductQuantizer


def load_map(id: UUID, s3_client: S3Client, reconstruction_bucket: str, reconstructions_dir: Path) -> Map:
    for page in s3_client.get_paginator("list_objects_v2").paginate(Bucket=reconstruction_bucket, Prefix=f"{id}/"):
        for obj in page.get("Contents", []):
            key = obj["Key"]  # type: ignore
            if not (
                key.startswith(f"{id}/sfm_model/")
                or key
                in {
                    f"{id}/{GLOBAL_DESCRIPTORS_FILE}",
                    f"{id}/{FEATURES_FILE}",
                    f"{id}/{OPQ_MATRIX_FILE}",
                    f"{id}/{PQ_QUANTIZER_FILE}",
                }
            ):
                continue

            local_path = reconstructions_dir / str(id) / key[len(str(id)) :].lstrip("/")
            local_path.parent.mkdir(parents=True, exist_ok=True)
            print(f"Downloading s3://{reconstruction_bucket}/{key} to {local_path}")
            s3_client.download_file(reconstruction_bucket, key, str(local_path))

    reconstruction_path = reconstructions_dir / str(id)
    reconstruction = Reconstruction(str(reconstruction_path / "sfm_model"))
    ordered_image_ids: list[int] = sorted(cast(Mapping[int, Any], reconstruction.images).keys())
    ordered_image_names = [reconstruction.images[image_id].name for image_id in ordered_image_ids]
    global_descriptors_by_name = read_global_descriptors(reconstruction_path, ordered_image_names)
    (keypoints_by_name, pq_codes_by_name) = read_features(reconstruction_path, ordered_image_names)

    image_sizes: dict[str, tuple[int, int]] = {}
    global_descriptor_rows: list[NDArray[float32]] = []
    keypoints: dict[int, NDArray[float32]] = {}
    pq_codes: dict[int, NDArray[uint8]] = {}

    for image_id in ordered_image_ids:
        image = reconstruction.images[image_id]
        camera = reconstruction.cameras[image.camera_id]
        name = image.name
        image_sizes[str(image_id)] = (camera.height, camera.width)
        keypoints[image_id] = keypoints_by_name[name]
        pq_codes[image_id] = pq_codes_by_name[name]
        global_descriptor_rows.append(global_descriptors_by_name[name])

    return Map(
        reconstruction.points3D,
        reconstruction.images,
        ordered_image_ids,
        image_sizes,
        keypoints,
        pq_codes,
        stack(global_descriptor_rows, axis=0),
        read_opq_matrix(reconstruction_path),
        read_pq_quantizer(reconstruction_path),
    )
