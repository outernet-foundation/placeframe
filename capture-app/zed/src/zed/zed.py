from __future__ import annotations

from concurrent.futures import Future
from csv import writer
from dataclasses import dataclass
from json import dump
from pathlib import Path
from queue import Empty, Queue
from threading import Thread
from time import perf_counter, time
from traceback import format_exception
from typing import Union, cast
from uuid import UUID, uuid4

from core.rig import PinholeCamera, Rig, RigCamera, RigConfig
from core.transform import Quaternion, Vector3
from numpy import asarray, float64
from PIL import Image
from pyzed.sl import (
    REFERENCE_FRAME,
    RESOLUTION,
    UNIT,
    VIDEO_SETTINGS,
    VIEW,
    Camera,
    InitParameters,
    Mat,
    Pose,
    PositionalTrackingParameters,
    Rect,
)
from scipy.spatial.transform import Rotation

from .zed_wrapper import (
    close_camera,
    disable_positional_tracking,
    enable_positional_tracking,
    get_camera_information,
    get_camera_settings,
    get_data,
    get_orientation_quaternion,
    get_translation_array,
    grab,
    open_camera,
    retrieve_image,
    set_camera_settings,
    set_camera_settings_roi,
    update_pose,
)


@dataclass(frozen=True)
class State:
    capture_id: UUID | None
    last_exception: str | None


@dataclass(frozen=True)
class _StartCapture:
    interval: float
    reply: Future[UUID]


@dataclass(frozen=True)
class _StopCapture:
    reply: Future[None]


_Command = Union[_StartCapture, _StopCapture]


class InvalidStateException(Exception):
    pass


class Zed(Thread):
    def __init__(self, capture_directory: Path) -> None:
        super().__init__(name="CameraActor", daemon=True)
        self._capture_directory = capture_directory
        self._commands = Queue[_Command]()
        self._current_id: UUID | None = None
        self._capture_interval: float | None = None
        self._next_capture_time: float | None = None
        self._last_exception: str | None = None

        self._camera = Camera()
        self._image_buffer_matrix = Mat()
        self._pose = Pose()

    def start_capture(self, interval: float) -> UUID:
        reply: Future[UUID] = Future()
        self._commands.put(_StartCapture(interval=interval, reply=reply))
        return reply.result()

    def stop_capture(self) -> None:
        reply: Future[None] = Future()
        self._commands.put(_StopCapture(reply=reply))
        reply.result()

    def run(self) -> None:
        while True:
            try:
                command = self._commands.get(
                    timeout=0.1 if self._next_capture_time is None else max(0.0, self._next_capture_time - time())
                )

                if isinstance(command, _StartCapture):
                    if self._current_id is not None:
                        command.reply.set_exception(InvalidStateException("Capture already running"))
                        continue

                    self._current_id = uuid4()
                    self._last_exception = None
                    self._capture_interval = command.interval
                    self._next_capture_time = time()

                    try:
                        self._start()
                    except Exception as e:
                        self._current_id = None
                        self._capture_interval = None
                        self._next_capture_time = None
                        self._last_exception = str(e)
                        command.reply.set_exception(e)
                        continue

                    command.reply.set_result(self._current_id)

                else:
                    assert isinstance(command, _StopCapture)
                    if self._current_id is None:
                        command.reply.set_exception(InvalidStateException("No capture running"))
                        continue

                    self._current_id = None
                    self._capture_interval = None
                    self._next_capture_time = None

                    try:
                        self._stop()
                    except Exception as e:
                        command.reply.set_exception(e)
                        continue

                    command.reply.set_result(None)
            except Empty:
                pass

            if self._next_capture_time is not None:
                assert self._capture_interval is not None

                if time() >= self._next_capture_time:
                    try:
                        self._capture_frame()
                    except Exception as e:
                        # turn e into string including callstack

                        print(
                            f"Exception occurred during frame capture: {format_exception(type(e), e, e.__traceback__)}"
                        )
                        self._last_exception = str(e)

                    self._next_capture_time += self._capture_interval

    def _output_directory(self) -> Path:
        assert self._current_id is not None
        return self._capture_directory / str(self._current_id)

    def _rig_directory(self) -> Path:
        return self._output_directory() / "rig0"

    def _camera0_directory(self) -> Path:
        return self._rig_directory() / "camera0"

    def _camera1_directory(self) -> Path:
        return self._rig_directory() / "camera1"

    def _start(self):
        self._camera0_directory().mkdir(parents=True, exist_ok=True)
        self._camera1_directory().mkdir(parents=True, exist_ok=True)

        print("Opening ZED camera")

        init = InitParameters()
        init.camera_resolution = RESOLUTION.HD1080
        init.coordinate_units = UNIT.METER
        init.camera_fps = 30
        init.enable_image_enhancement = True
        init.sdk_verbose = True
        open_camera(self._camera, init)

        if get_camera_settings(self._camera, VIDEO_SETTINGS.SHARPNESS) != 4:
            set_camera_settings(self._camera, VIDEO_SETTINGS.SHARPNESS, 4)

        print("Metering and locking exposure, gain, and white balance")

        exposure, gain, white_balance = self._meter_and_lock(0.25, 0.25, 0.5, 0.5)
        with open(self._output_directory() / "metered_values.json", "w") as config_file:
            dump({"exposure": exposure, "gain": gain, "white_balance": white_balance}, config_file, indent=4)

        print("Enabling positional tracking")

        positionTrackingParameters = PositionalTrackingParameters()
        positionTrackingParameters.enable_imu_fusion = True
        positionTrackingParameters.set_floor_as_origin = False
        enable_positional_tracking(self._camera, positionTrackingParameters)

        print("Writing config.json")

        cam_info = get_camera_information(self._camera)
        # calibration_parameters = cam_info.camera_configuration.calibration_parameters_raw
        calibration_parameters = cam_info.camera_configuration.calibration_parameters
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

        with open(self._output_directory() / "config.json", "w") as config_file:
            config_file.write(
                RigConfig(
                    rigs=[
                        Rig(
                            id="rig0",
                            cameras=[
                                RigCamera(
                                    id="camera0",
                                    ref_sensor=True,
                                    rotation=Quaternion(x=0.0, y=0.0, z=0.0, w=1.0),
                                    translation=Vector3(x=0.0, y=0.0, z=0.0),
                                    intrinsics=PinholeCamera(
                                        model="PINHOLE",
                                        width=left_camera.image_size.width,
                                        height=left_camera.image_size.height,
                                        mirroring="None",
                                        rotation="None",
                                        fx=left_camera.fx,
                                        fy=left_camera.fy,
                                        cx=left_camera.cx,
                                        cy=left_camera.cy,
                                    ),
                                ),
                                RigCamera(
                                    id="camera1",
                                    ref_sensor=False,
                                    rotation=Quaternion(
                                        x=stereo_transform_rotation[0],
                                        y=stereo_transform_rotation[1],
                                        z=stereo_transform_rotation[2],
                                        w=stereo_transform_rotation[3],
                                    ),
                                    translation=Vector3(
                                        # TODO: Figure out why the x component needs to be negated
                                        x=-stereo_transform_translation[0],
                                        y=stereo_transform_translation[1],
                                        z=stereo_transform_translation[2],
                                    ),
                                    intrinsics=PinholeCamera(
                                        model="PINHOLE",
                                        width=right_camera.image_size.width,
                                        height=right_camera.image_size.height,
                                        mirroring="None",
                                        rotation="None",
                                        fx=right_camera.fx,
                                        fy=right_camera.fy,
                                        cx=right_camera.cx,
                                        cy=right_camera.cy,
                                    ),
                                ),
                            ],
                        )
                    ]
                ).model_dump_json(indent=4)
            )

        print("Write frame.csv header")

        with open(self._rig_directory() / "frames.csv", "w", newline="") as csv_file:
            csv_writer = writer(csv_file)
            csv_writer.writerow(["timestamp_ms", "tx", "ty", "tz", "qx", "qy", "qz", "qw"])

        print("Capture started")

    def _stop(self):
        disable_positional_tracking(self._camera)
        close_camera(self._camera)
        print("Capture stopped")

    def _capture_frame(self):
        print("Capturing frame")
        grab(self._camera)

        # Retrieve pose and write to disk
        update_pose(self._camera, self._pose, REFERENCE_FRAME.WORLD)
        timestamp = int(self._pose.timestamp.get_milliseconds())
        camera_center_in_world = get_translation_array(self._pose)
        rotation_world_from_camera = get_orientation_quaternion(self._pose)

        # Write pose to CSV
        with open(self._rig_directory() / "frames.csv", "a", newline="") as csv_file:
            csv_writer = writer(csv_file)
            csv_writer.writerow([timestamp, *camera_center_in_world.tolist(), *rotation_world_from_camera.tolist()])

        # Retrieve images and write to disk
        retrieve_image(self._camera, self._image_buffer_matrix, VIEW.LEFT)
        self._write_jpeg(self._image_buffer_matrix, self._camera0_directory() / f"{timestamp}.jpg")
        retrieve_image(self._camera, self._image_buffer_matrix, VIEW.RIGHT)
        self._write_jpeg(self._image_buffer_matrix, self._camera1_directory() / f"{timestamp}.jpg")

    def _meter_and_lock(self, rx: float, ry: float, rw: float, rh: float):
        # Enable auto-exposure and auto white balance
        set_camera_settings(self._camera, VIDEO_SETTINGS.AEC_AGC, 1)
        set_camera_settings(self._camera, VIDEO_SETTINGS.WHITEBALANCE_AUTO, 1)

        # Set ROI for metering
        info = get_camera_information(self._camera)
        w = info.camera_configuration.resolution.width
        h = info.camera_configuration.resolution.height
        # set_camera_settings_roi(self._camera, Rect(int(rx * w), int(ry * h), int(rw * w), int(rh * h)))
        set_camera_settings_roi(self._camera, Rect(0, 0, w, h))

        # Let camera settle
        start = perf_counter()
        settle_for = 1.5
        while (perf_counter() - start) < settle_for:
            try:
                grab(self._camera)
                retrieve_image(self._camera, self._image_buffer_matrix, VIEW.LEFT_UNRECTIFIED)
            except Exception as e:
                print(f"Exception occurred while settling: {e}")

        # Read current exposure, gain, and white balance values
        exposure = get_camera_settings(self._camera, VIDEO_SETTINGS.EXPOSURE)
        gain = get_camera_settings(self._camera, VIDEO_SETTINGS.GAIN)
        white_balance_temperature = get_camera_settings(self._camera, VIDEO_SETTINGS.WHITEBALANCE_TEMPERATURE)

        # Disable auto-exposure and auto white balance
        set_camera_settings(self._camera, VIDEO_SETTINGS.AEC_AGC, 0)
        set_camera_settings(self._camera, VIDEO_SETTINGS.WHITEBALANCE_AUTO, 0)

        # Lock metered values
        set_camera_settings(self._camera, VIDEO_SETTINGS.EXPOSURE, 40)
        set_camera_settings(self._camera, VIDEO_SETTINGS.GAIN, gain)
        set_camera_settings(self._camera, VIDEO_SETTINGS.WHITEBALANCE_TEMPERATURE, white_balance_temperature)

        return exposure, gain, white_balance_temperature

    def _write_jpeg(self, image_matrix_buffer: Mat, path: Path, quality: int = 75):
        arr = get_data(image_matrix_buffer)  # uint8, HxWx{3,4}
        if arr.ndim == 3 and arr.shape[2] >= 3:
            arr = arr[:, :, :3][:, :, ::-1]  # BG* -> RGB
        else:
            raise ValueError(f"Unexpected image shape {arr.shape} dtype {arr.dtype}")
        Image.fromarray(arr, mode="RGB").save(
            str(path), format="JPEG", quality=quality, optimize=True, progressive=True
        )
