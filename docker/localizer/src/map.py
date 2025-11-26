from __future__ import annotations

from dataclasses import dataclass

from faiss import (  # type: ignore
    OPQMatrix,
    ProductQuantizer,
)
from numpy import float32, uint8
from numpy.typing import NDArray
from pycolmap._core import ImageMap, Point3DMap


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
