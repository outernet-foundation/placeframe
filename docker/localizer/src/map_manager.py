from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from shutil import rmtree
from threading import Lock
from typing import Any, Mapping, cast
from uuid import UUID

from common.boto_clients import create_s3_client
from core.axis_convention import AxisConvention
from core.camera_config import PinholeCameraConfig
from core.h5 import FEATURES_FILE, GLOBAL_DESCRIPTORS_FILE, read_features, read_global_descriptors
from core.opq import OPQ_MATRIX_FILE, PQ_QUANTIZER_FILE, read_opq_matrix, read_pq_quantizer
from numpy import float32, stack, uint8
from numpy.typing import NDArray
from pycolmap import Reconstruction

from .localize import localize_image_against_reconstruction
from .map import Map
from .schemas import LoadState, LoadStateResponse, Localization
from .settings import get_settings

RECONSTRUCTIONS_DIR = Path("/tmp/reconstructions")
RETRIEVAL_TOP_K = 12  # how many similar database images to keep
RANSAC_THRESHOLD = 12.0  # reprojection error in pixels


_executor = ThreadPoolExecutor(max_workers=2)
_load_lock = Lock()
_load_state: dict[UUID, LoadState] = {}
_load_error: dict[UUID, str] = {}
_maps: dict[UUID, Map] = {}

settings = get_settings()
s3_client = create_s3_client(
    minio_endpoint_url=settings.minio_endpoint_url,
    minio_access_key=settings.minio_access_key,
    minio_secret_key=settings.minio_secret_key,
)


def start_load(id: UUID):
    with _load_lock:
        state = _load_state.get(id)
        if state is not None:
            return state
        _load_state[id] = LoadState.LOADING

        def _on_done(future: Future[None]) -> None:
            try:
                future.result()
            except Exception as e:
                print(f"Failed to load reconstruction {id}: {e}")
                with _load_lock:
                    _load_state[id] = LoadState.FAILED
                    _load_error[id] = str(e)
            else:
                with _load_lock:
                    _load_state[id] = LoadState.READY

        future = _executor.submit(_load, id)
        future.add_done_callback(_on_done)
        return LoadState.LOADING


def unload(id: UUID) -> Map | None:
    with _load_lock:
        _load_state.pop(id, None)
        _load_error.pop(id, None)
    _maps.pop(id, None)
    rmtree(RECONSTRUCTIONS_DIR / str(id))


def get_load_state(id: UUID):
    with _load_lock:
        return LoadStateResponse(status=_load_state.get(id, LoadState.PENDING), error=_load_error.get(id))


def localize(camera: PinholeCameraConfig, axis_convention: AxisConvention, image: bytes):
    return [
        Localization(id=id, transform=result[0], metrics=result[1])
        for id, result in zip(
            _maps.keys(),
            [
                localize_image_against_reconstruction(
                    map=_maps[id],
                    camera=camera,
                    axis_convention=axis_convention,
                    image_buffer=image,
                    retrieval_top_k=RETRIEVAL_TOP_K,
                    ransac_threshold=RANSAC_THRESHOLD,
                )
                for id in _maps.keys()
            ],
        )
    ]


def _load(id: UUID):
    for page in s3_client.get_paginator("list_objects_v2").paginate(
        Bucket=settings.reconstructions_bucket, Prefix=f"{id}/"
    ):
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

            local_path = RECONSTRUCTIONS_DIR / str(id) / key[len(str(id)) :].lstrip("/")
            local_path.parent.mkdir(parents=True, exist_ok=True)
            print(f"Downloading s3://{settings.reconstructions_bucket}/{key} to {local_path}")
            s3_client.download_file(settings.reconstructions_bucket, key, str(local_path))

    reconstruction_path = RECONSTRUCTIONS_DIR / str(id)
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

    _maps[id] = Map(
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
