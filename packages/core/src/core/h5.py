from pathlib import Path
from typing import Any, Iterable, Mapping, cast

from h5py import Dataset, File, Group
from numpy import asarray, float32, uint8
from numpy.typing import NDArray

GLOBAL_DESCRIPTORS_DATASET_NAME = "global_descriptor"
KEYPOINTS_DATASET_NAME = "keypoints"
PQ_CODES_DATASET_NAME = "pq_codes"
GLOBAL_DESCRIPTORS_FILE = "global_descriptors.h5"
FEATURES_FILE = "features.h5"


def write_global_descriptors(root_path: Path, global_descriptors: Mapping[str, NDArray[float32]]):
    path = root_path / GLOBAL_DESCRIPTORS_FILE
    with File(str(path), "w") as file:
        for name, global_descriptor in global_descriptors.items():
            group = file.create_group(name)
            _create_dataset(group, GLOBAL_DESCRIPTORS_DATASET_NAME, global_descriptor)

    return GLOBAL_DESCRIPTORS_FILE, path.read_bytes()


def write_features(root_path: Path, keypoints: Mapping[str, NDArray[float32]], pq_codes: Mapping[str, NDArray[uint8]]):
    path = root_path / FEATURES_FILE
    with File(str(path), "w") as file:
        for name, image_keypoints in keypoints.items():
            group = file.create_group(name)
            _create_dataset(group, KEYPOINTS_DATASET_NAME, image_keypoints)
            _create_dataset(group, PQ_CODES_DATASET_NAME, pq_codes[name])

    return FEATURES_FILE, path.read_bytes()


def _create_dataset(group: Group, name: str, data: Any):
    group.create_dataset(name, data=data, compression="gzip", compression_opts=9, shuffle=True, chunks=True)


def read_global_descriptors(root_path: Path, image_names: Iterable[str]) -> dict[str, NDArray[float32]]:
    result: dict[str, NDArray[float32]] = {}
    with File(str(root_path / GLOBAL_DESCRIPTORS_FILE), "r") as file:
        for name in image_names:
            group = cast(Group, file[name])
            result[name] = asarray(cast(Dataset, group[GLOBAL_DESCRIPTORS_DATASET_NAME])[()], dtype=float32)

    return result


def read_features(
    root_path: Path, image_names: Iterable[str]
) -> tuple[dict[str, NDArray[float32]], dict[str, NDArray[uint8]]]:
    keypoints_by_name: dict[str, NDArray[float32]] = {}
    pq_codes_by_name: dict[str, NDArray[uint8]] = {}

    with File(str(root_path / FEATURES_FILE), "r") as file:
        for name in image_names:
            group = cast(Group, file[name])
            keypoints_by_name[name] = asarray(cast(Dataset, group[KEYPOINTS_DATASET_NAME])[()], dtype=float32)
            pq_codes_by_name[name] = asarray(cast(Dataset, group[PQ_CODES_DATASET_NAME])[()], dtype=uint8)

    return keypoints_by_name, pq_codes_by_name
