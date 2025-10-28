import csv
import json
import os
import threading
import time
from pathlib import Path
from typing import cast

from common.classes import Quaternion, RigConfig, Vector3
from numpy import asarray, float64
from PIL import Image
from pyzed import sl
from scipy.spatial.transform import Rotation

from .zed_wrapper import (
    enable_positional_tracking,
    get_camera_information,
    get_data,
    get_orientation_quaternion,
    get_translation_array,
    grab,
    open_camera,
    retrieve_image,
    set_camera_settings_roi,
    update_pose,
)


class CaptureThread(threading.Thread):
    def __init__(self, stop_event: threading.Event, output_directory: Path, capture_interval: float):
        super().__init__(daemon=True)
        self.stop_event = stop_event
        self.output_directory = output_directory
        self.capture_interval = capture_interval
        self._exception = None

    def exception(self):
        return self._exception

    def run(self):
        # Prepare output directories
        rig_directory = self.output_directory / "rig0"
        cam0_directory = rig_directory / "camera0"
        cam1_directory = rig_directory / "camera1"
        cam0_directory.mkdir(parents=True, exist_ok=True)
        cam1_directory.mkdir(parents=True, exist_ok=True)

        # Start camera
        zed = sl.Camera()
        init = sl.InitParameters()
        init.camera_resolution = sl.RESOLUTION.HD2K
        init.coordinate_units = sl.UNIT.METER
        init.camera_fps = 15
        init.enable_image_enhancement = True
        err = open_camera(zed, init)
        if err != sl.ERROR_CODE.SUCCESS:
            raise RuntimeError(f"ZED open failed: {err.name} ({err.value})")

        # Set sharpness to a reasonable value
        zed.set_camera_settings(sl.VIDEO_SETTINGS.SHARPNESS, 4)

        # Meter and lock exposure, gain, and white balance
        exposure, gain, white_balance = self._meter_and_lock(zed, 0.25, 0.25, 0.5, 0.5)

        # Write metered values to disk for reference
        with open(os.path.join(self.output_directory, "metered_values.json"), "w") as config_file:
            json.dump({"exposure": exposure, "gain": gain, "white_balance": white_balance}, config_file, indent=4)

        # Retrieve calibration info
        cam_info = get_camera_information(zed)
        calibration_parameters = cam_info.camera_configuration.calibration_parameters_raw
        left_camera = calibration_parameters.left_cam
        right_camera = calibration_parameters.right_cam
        stereo_transform_matrix = asarray(
            getattr(calibration_parameters.stereo_transform, "m", calibration_parameters.stereo_transform),
            dtype=float64,
        )
        stereo_transform_translation = stereo_transform_matrix[:3, 3].tolist()
        stereo_transform_rotation = cast(
            list[float], Rotation.from_matrix(stereo_transform_matrix[:3, :3]).as_quat().tolist()
        )

        # Build rig config
        rigConfig: RigConfig = {
            "rigs": [
                {
                    "id": "rig0",
                    "cameras": [
                        {
                            "id": "camera0",
                            "ref_sensor": True,
                            "rotation": Quaternion(x=0.0, y=0.0, z=0.0, w=1.0),
                            "translation": Vector3(x=0.0, y=0.0, z=0.0),
                            "intrinsics": {
                                "model": "OPENCV",
                                "width": left_camera.image_size.width,
                                "height": left_camera.image_size.height,
                                "fx": left_camera.fx,
                                "fy": left_camera.fy,
                                "cx": left_camera.cx,
                                "cy": left_camera.cy,
                                "k1": left_camera.disto[0],
                                "k2": left_camera.disto[1],
                                "p1": left_camera.disto[2],
                                "p2": left_camera.disto[3],
                            },
                        },
                        {
                            "id": "camera1",
                            "ref_sensor": False,
                            "rotation": Quaternion(
                                x=stereo_transform_rotation[0],
                                y=stereo_transform_rotation[1],
                                z=stereo_transform_rotation[2],
                                w=stereo_transform_rotation[3],
                            ),
                            "translation": Vector3(
                                x=stereo_transform_translation[0],
                                y=stereo_transform_translation[1],
                                z=stereo_transform_translation[2],
                            ),
                            "intrinsics": {
                                "model": "OPENCV",
                                "width": right_camera.image_size.width,
                                "height": right_camera.image_size.height,
                                "fx": right_camera.fx,
                                "fy": right_camera.fy,
                                "cx": right_camera.cx,
                                "cy": right_camera.cy,
                                "k1": right_camera.disto[0],
                                "k2": right_camera.disto[1],
                                "p1": right_camera.disto[2],
                                "p2": right_camera.disto[3],
                            },
                        },
                    ],
                }
            ]
        }

        # Write rig config to disk
        with open(os.path.join(self.output_directory, "config.json"), "w") as config_file:
            json.dump(rigConfig, config_file, indent=4)

        # Enable positional tracking
        positionTrackingParameters = sl.PositionalTrackingParameters()
        positionTrackingParameters.enable_imu_fusion = True
        positionTrackingParameters.set_floor_as_origin = False
        enable_positional_tracking(zed, positionTrackingParameters)

        # Open frames.csv for writing
        csv_file = open(rig_directory / "frames.csv", "w", newline="")
        image_mat = sl.Mat()
        pose = sl.Pose()

        try:
            # Write CSV header
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(["timestamp", "tx", "ty", "tz", "qx", "qy", "qz", "qw"])

            # Capture loop
            next_capture = time.time()
            while not self.stop_event.is_set():
                # Wait until next capture time
                if time.time() < next_capture:
                    time.sleep(0.01)
                    continue

                # Grab frame
                while grab(zed) != sl.ERROR_CODE.SUCCESS:
                    time.sleep(0.003)
                    pass

                # Retrieve pose and write to disk
                update_pose(zed, pose, sl.REFERENCE_FRAME.WORLD)
                timestamp = int(pose.timestamp.get_milliseconds())
                t_arr = get_translation_array(pose)
                q_arr = get_orientation_quaternion(pose)
                csv_writer.writerow([timestamp, *t_arr.tolist(), *q_arr.tolist()])
                csv_file.flush()

                # Retrieve images and write to disk
                retrieve_image(zed, image_mat, sl.VIEW.LEFT_UNRECTIFIED)
                self._write_jpeg(image_mat, cam0_directory / f"{timestamp}.jpg", quality=95)
                retrieve_image(zed, image_mat, sl.VIEW.RIGHT_UNRECTIFIED)
                self._write_jpeg(image_mat, cam1_directory / f"{timestamp}.jpg", quality=95)

                next_capture += self.capture_interval

        except KeyboardInterrupt:
            print("Capture interrupted by user.")

        except Exception as e:
            self._exception = e

        finally:
            csv_file.close()
            zed.disable_positional_tracking()
            zed.close()

    def _meter_and_lock(self, zed: sl.Camera, rx: float, ry: float, rw: float, rh: float):
        # Enable auto-exposure and auto white balance
        zed.set_camera_settings(sl.VIDEO_SETTINGS.AEC_AGC, 1)
        zed.set_camera_settings(sl.VIDEO_SETTINGS.WHITEBALANCE_AUTO, 1)

        # Set ROI for metering
        info = get_camera_information(zed)
        w = info.camera_configuration.resolution.width
        h = info.camera_configuration.resolution.height
        rect = sl.Rect(int(rx * w), int(ry * h), int(rw * w), int(rh * h))
        set_camera_settings_roi(zed, rect)

        # Let camera settle
        start = time.perf_counter()
        settle_for = 1.5  # seconds
        mat = sl.Mat()
        while (time.perf_counter() - start) < settle_for:
            if grab(zed) == sl.ERROR_CODE.SUCCESS:
                # use unrectified LEFT so metering reflects the pixels we save
                retrieve_image(zed, mat, sl.VIEW.LEFT_UNRECTIFIED)

        # Read current exposure, gain, and white balance values
        exposure = zed.get_camera_settings(sl.VIDEO_SETTINGS.EXPOSURE)[1]
        gain = zed.get_camera_settings(sl.VIDEO_SETTINGS.GAIN)[1]
        white_balance_temperature = zed.get_camera_settings(sl.VIDEO_SETTINGS.WHITEBALANCE_TEMPERATURE)[1]

        # Disable auto-exposure and auto white balance
        zed.set_camera_settings(sl.VIDEO_SETTINGS.AEC_AGC, 0)
        zed.set_camera_settings(sl.VIDEO_SETTINGS.WHITEBALANCE_AUTO, 0)

        # Lock metered values
        zed.set_camera_settings(sl.VIDEO_SETTINGS.EXPOSURE, exposure)
        zed.set_camera_settings(sl.VIDEO_SETTINGS.GAIN, gain)
        zed.set_camera_settings(sl.VIDEO_SETTINGS.WHITEBALANCE_TEMPERATURE, white_balance_temperature)

        return exposure, gain, white_balance_temperature

    def _write_jpeg(self, sl_mat: sl.Mat, path: Path, quality: int = 95):
        Image.fromarray(get_data(sl_mat)[:, :, :3][:, :, ::-1], mode="RGB").save(
            str(path), format="JPEG", quality=quality, subsampling=0, optimize=True
        )
