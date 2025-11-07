# pyright: reportUnknownMemberType=false, reportUnknownArgumentType=false, reportUnknownVariableType=false, reportIndexIssue=false
from __future__ import annotations

from numpy import asarray, float64, uint8
from numpy.typing import NDArray
from pyzed import sl


def reboot_camera(cam: sl.Camera):
    error = cam.reboot(0)  # type: ignore
    if error != sl.ERROR_CODE.SUCCESS:
        raise Exception(f"ZED Camera Reboot Error: {error}")


def open_camera(cam: sl.Camera, init: sl.InitParameters):
    error = cam.open(init)
    if error != sl.ERROR_CODE.SUCCESS:
        raise Exception(f"ZED Camera Open Error: {error}")


def close_camera(cam: sl.Camera):
    cam.close()


def set_camera_settings(cam: sl.Camera, setting: sl.VIDEO_SETTINGS, value: int):
    error = cam.set_camera_settings(setting, value)
    if error != sl.ERROR_CODE.SUCCESS:
        raise Exception(f"ZED Set Camera Settings Error: {error}")


def get_camera_settings(cam: sl.Camera, setting: sl.VIDEO_SETTINGS) -> int:
    error, value = cam.get_camera_settings(setting)
    if error != sl.ERROR_CODE.SUCCESS:
        raise Exception(f"ZED Get Camera Settings Error: {error}")
    return value


def get_camera_information(cam: sl.Camera) -> sl.CameraInformation:
    return cam.get_camera_information()


def enable_positional_tracking(cam: sl.Camera, params: object):
    error = cam.enable_positional_tracking(params)
    if error != sl.ERROR_CODE.SUCCESS:
        raise Exception(f"ZED Enable Positional Tracking Error: {error}")


def disable_positional_tracking(cam: sl.Camera):
    cam.disable_positional_tracking()


def grab(cam: sl.Camera):
    error = cam.grab()
    if error != sl.ERROR_CODE.SUCCESS:
        raise Exception(f"ZED Grab Error: {error}")


def update_pose(cam: sl.Camera, pose: object, reference_frame: sl.REFERENCE_FRAME) -> sl.POSITIONAL_TRACKING_STATE:
    return cam.get_position(pose, reference_frame)


def get_translation_array(pose: sl.Pose) -> NDArray[float64]:
    return asarray(pose.get_translation(sl.Translation()).get(), dtype=float64)


def get_orientation_quaternion(pose: sl.Pose) -> NDArray[float64]:
    return asarray(pose.get_orientation(sl.Orientation()).get(), dtype=float64)


def retrieve_image(cam: sl.Camera, mat: object, view: sl.VIEW):
    error = cam.retrieve_image(mat, view)
    if error != sl.ERROR_CODE.SUCCESS:
        raise Exception(f"ZED Retrieve Image Error: {error}")


def set_camera_settings_roi(zed: sl.Camera, rect: sl.Rect):
    error = zed.set_camera_settings_roi(sl.VIDEO_SETTINGS.AEC_AGC_ROI, rect)
    if error != sl.ERROR_CODE.SUCCESS:
        raise Exception(f"ZED Set Camera Settings ROI Error: {error}")


def get_data(sl_mat: sl.Mat) -> NDArray[uint8]:
    arr = asarray(sl_mat.get_data())
    if not arr.flags.c_contiguous:
        arr = asarray(arr)
    return arr.copy()
