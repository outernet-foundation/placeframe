# pyright: reportUnknownMemberType=false, reportUnknownArgumentType=false, reportUnknownVariableType=false, reportIndexIssue=false
from __future__ import annotations

import numpy as np
import numpy.typing as npt
from pyzed import sl


def open_camera(cam: sl.Camera, init: sl.InitParameters) -> sl.ERROR_CODE:
    return cam.open(init)


def get_camera_information(cam: sl.Camera) -> sl.CameraInformation:
    return cam.get_camera_information()


def enable_positional_tracking(cam: sl.Camera, params: object) -> sl.ERROR_CODE:
    return cam.enable_positional_tracking(params)


def grab(cam: sl.Camera) -> sl.ERROR_CODE:
    return cam.grab()


def update_pose(cam: sl.Camera, pose: object, reference_frame: sl.REFERENCE_FRAME) -> sl.POSITIONAL_TRACKING_STATE:
    return cam.get_position(pose, reference_frame)


def get_translation_array(pose: sl.Pose) -> npt.NDArray[np.float64]:
    return np.asarray(pose.get_translation(sl.Translation()).get(), dtype=np.float64)


def get_orientation_quaternion(pose: sl.Pose) -> npt.NDArray[np.float64]:
    return np.asarray(pose.get_orientation(sl.Orientation()).get(), dtype=np.float64)


def retrieve_image(cam: sl.Camera, mat: object, view: sl.VIEW) -> sl.ERROR_CODE:
    return cam.retrieve_image(mat, view)


def set_camera_settings_roi(zed: sl.Camera, rect: sl.Rect) -> sl.ERROR_CODE:
    return zed.set_camera_settings_roi(sl.VIDEO_SETTINGS.AEC_AGC_ROI, rect)


def get_data(sl_mat: sl.Mat) -> np.ndarray:
    return sl_mat.get_data()
