from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Mapping, cast
from uuid import UUID

from core.calibration import RawMapMetrics
from core.h5 import FEATURES_FILE, GLOBAL_DESCRIPTORS_FILE, read_features, read_global_descriptors
from core.opq import OPQ_MATRIX_FILE, PQ_QUANTIZER_FILE, read_opq_matrix, read_pq_quantizer
from core.reconstruction_metrics import ReconstructionMetrics
from faiss import OPQMatrix, ProductQuantizer  # type: ignore
from numpy import dtype, float32, ndarray, uint8
from numpy.typing import NDArray  # noqa: TID251 — Phase T piece 3 follow-up migration
from pycolmap import Reconstruction
from pycolmap._core import ImageMap, Point3DMap

from core.image_preprocess import MaxTiles, NumImages
from core.model_wrappers import RetrievalDim
from core.numpy_ops import zeros

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
    tile_descriptors: ndarray[tuple[NumImages, MaxTiles, RetrievalDim], dtype[float32]]
    opq_matrix: OPQMatrix
    product_quantizer: ProductQuantizer
    map_metrics: RawMapMetrics


def load_map(
    id: UUID,
    s3_client: S3Client,
    reconstruction_bucket: str,
    reconstructions_dir: Path,
    raw_metrics: ReconstructionMetrics,
) -> Map:
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

    assert raw_metrics.map_image_count is not None
    assert raw_metrics.map_point_count is not None
    assert raw_metrics.map_avg_track_length is not None
    assert raw_metrics.map_bounding_volume_m3 is not None
    assert raw_metrics.map_viewpoint_diversity is not None
    map_metrics = RawMapMetrics(
        map_image_count=raw_metrics.map_image_count,
        map_point_count=raw_metrics.map_point_count,
        map_avg_track_length=raw_metrics.map_avg_track_length,
        map_bounding_volume_m3=raw_metrics.map_bounding_volume_m3,
        map_viewpoint_diversity=raw_metrics.map_viewpoint_diversity,
    )

    reconstruction_path = reconstructions_dir / str(id)
    reconstruction = Reconstruction(str(reconstruction_path / "sfm_model"))
    ordered_image_ids: list[int] = sorted(cast(Mapping[int, Any], reconstruction.images).keys())
    ordered_image_names = [reconstruction.images[image_id].name for image_id in ordered_image_ids]
    global_descriptors_by_name = read_global_descriptors(reconstruction_path, ordered_image_names)
    (keypoints_by_name, pq_codes_by_name) = read_features(reconstruction_path, ordered_image_names)

    image_sizes: dict[str, tuple[int, int]] = {}
    keypoints: dict[int, NDArray[float32]] = {}
    pq_codes: dict[int, NDArray[uint8]] = {}
    per_image_tile_descriptors: list[NDArray[float32]] = []

    for image_id in ordered_image_ids:
        image = reconstruction.images[image_id]
        camera = reconstruction.cameras[image.camera_id]
        name = image.name
        image_sizes[str(image_id)] = (camera.height, camera.width)
        keypoints[image_id] = keypoints_by_name[name]
        pq_codes[image_id] = pq_codes_by_name[name]
        per_image_tile_descriptors.append(global_descriptors_by_name[name])

    padded_tile_descriptors = zeros(
        (
            NumImages(len(ordered_image_ids)),
            MaxTiles(max(tiles.shape[0] for tiles in per_image_tile_descriptors)),
            RetrievalDim(per_image_tile_descriptors[0].shape[1]),
        ),
        dtype=float32,
    )
    for image_index, tiles in enumerate(per_image_tile_descriptors):
        padded_tile_descriptors[image_index, : tiles.shape[0]] = tiles

    return Map(
        reconstruction.points3D,
        reconstruction.images,
        ordered_image_ids,
        image_sizes,
        keypoints,
        pq_codes,
        padded_tile_descriptors,
        read_opq_matrix(reconstruction_path),
        read_pq_quantizer(reconstruction_path),
        map_metrics=map_metrics,
    )
