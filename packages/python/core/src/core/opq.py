from pathlib import Path
from typing import cast

from faiss import (  # type: ignore
    OPQMatrix,
    ProductQuantizer,
    read_ProductQuantizer,  # type: ignore
    read_VectorTransform,  # type: ignore
    write_ProductQuantizer,  # type: ignore
    write_VectorTransform,  # type: ignore
)
from numpy import ascontiguousarray, float32, uint8
from numpy.linalg import norm
from numpy.typing import NDArray

OPQ_MATRIX_FILE = "opq_matrix.tf"
PQ_QUANTIZER_FILE = "pq_quantizer.pq"


def train_opq_matrix(number_of_subvectors: int, number_of_training_iterations: int, training_unit: NDArray[float32]):
    opq_matrix = OPQMatrix(training_unit.shape[1], number_of_subvectors)
    opq_matrix.niter = number_of_training_iterations
    opq_matrix.verbose = True
    opq_matrix.train(training_unit)  # type: ignore
    return opq_matrix


def train_pq_quantizer(
    number_of_subvectors: int, number_of_bits_per_subvector: int, opq_matrix: OPQMatrix, training_unit: NDArray[float32]
):
    rotated_training_unit = opq_matrix.apply(training_unit)  # type: ignore
    product_quantizer = ProductQuantizer(training_unit.shape[1], number_of_subvectors, number_of_bits_per_subvector)
    product_quantizer.verbose = True
    product_quantizer.train(rotated_training_unit)  # type: ignore
    return product_quantizer


def encode_descriptors(
    opq_matrix: OPQMatrix, product_quantizer: ProductQuantizer, image_descriptors: dict[str, NDArray[float32]]
):
    images_codes: dict[str, NDArray[uint8]] = {}
    for i, name in enumerate(image_descriptors.keys()):
        print(f"Encoding image {i + 1} of {len(image_descriptors)}")
        descriptors_contiguous = ascontiguousarray(image_descriptors[name])
        descriptors_rotated = cast(NDArray[float32], opq_matrix.apply(descriptors_contiguous))  # type: ignore
        codes = cast(NDArray[uint8], product_quantizer.compute_codes(descriptors_rotated))  # type: ignore
        images_codes[name] = codes

    return images_codes


def decode_descriptors(opq_matrix: OPQMatrix, product_quantizer: ProductQuantizer, pq_codes: dict[int, NDArray[uint8]]):
    descriptors: dict[int, NDArray[float32]] = {}
    for image_id, code in pq_codes.items():
        decoded = cast(NDArray[float32], product_quantizer.decode(code))  # type: ignore
        reversed_transformed = cast(NDArray[float32], opq_matrix.reverse_transform(decoded))  # type: ignore
        descriptors[image_id] = _l2_normalize_rows(reversed_transformed)

    return descriptors


def _l2_normalize_rows(matrix: NDArray[float32]) -> NDArray[float32]:
    return (matrix / (norm(matrix, axis=1, keepdims=True).astype(float32) + float32(1e-12))).astype(float32, copy=False)


def write_opq_matrix(opq_matrix: OPQMatrix, root_path: Path):
    path = root_path / OPQ_MATRIX_FILE
    write_VectorTransform(opq_matrix, str(path))
    return OPQ_MATRIX_FILE, path.read_bytes()


def write_pq_quantizer(pq_quantizer: ProductQuantizer, root_path: Path):
    path = root_path / PQ_QUANTIZER_FILE
    write_ProductQuantizer(pq_quantizer, str(path))
    return PQ_QUANTIZER_FILE, path.read_bytes()


def read_opq_matrix(root_path: Path):
    return cast(OPQMatrix, read_VectorTransform(str(root_path / OPQ_MATRIX_FILE)))


def read_pq_quantizer(root_path: Path):
    return cast(ProductQuantizer, read_ProductQuantizer(str(root_path / PQ_QUANTIZER_FILE)))
