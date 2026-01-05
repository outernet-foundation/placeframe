from enum import Enum

from numpy import array, float64
from numpy.typing import NDArray
from scipy.spatial.transform import Rotation


class AxisConvention(Enum):
    OPENCV = "OPENCV"
    UNITY = "UNITY"


basis_unity = array([[1, 0, 0], [0, 1, 0], [0, 0, 1]])
basis_opencv = array([[1, 0, 0], [0, -1, 0], [0, 0, 1]])
basic_change_unity_from_opencv = basis_unity.T @ basis_opencv
basis_change_opencv_from_unity = basic_change_unity_from_opencv.T


def change_basis_opencv_from_unity_pose(
    translation: NDArray[float64], rotation: NDArray[float64]
) -> tuple[NDArray[float64], NDArray[float64]]:
    new_translation = basis_change_opencv_from_unity @ translation
    new_rotation = basis_change_opencv_from_unity @ rotation @ basic_change_unity_from_opencv
    return new_translation, new_rotation


def change_basis_unity_from_opencv_pose(
    translation: NDArray[float64], rotation: NDArray[float64]
) -> tuple[NDArray[float64], NDArray[float64]]:
    new_translation = basic_change_unity_from_opencv @ translation
    new_rotation = basic_change_unity_from_opencv @ rotation @ basis_change_opencv_from_unity
    return new_translation, new_rotation


def change_basis_unity_from_opencv_points(points: NDArray[float64]) -> NDArray[float64]:
    return (basic_change_unity_from_opencv @ points.T).T


def change_basis_unity_from_opencv_poses(
    translations: NDArray[float64], orientations_xyzw: NDArray[float64]
) -> tuple[NDArray[float64], NDArray[float64]]:
    new_translations = change_basis_unity_from_opencv_points(translations)

    rotation_matrices = Rotation.from_quat(orientations_xyzw).as_matrix()
    new_rotation_matrices = basic_change_unity_from_opencv @ rotation_matrices @ basis_change_opencv_from_unity
    new_orientations_xyzw = Rotation.from_matrix(new_rotation_matrices).as_quat()

    return new_translations, new_orientations_xyzw
