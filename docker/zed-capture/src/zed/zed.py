from __future__ import annotations

from concurrent.futures import Future
from csv import writer
from dataclasses import dataclass
from logging import getLogger
from pathlib import Path
from queue import Empty, Queue
from threading import Thread
from time import perf_counter, time
from typing import Union, cast
from uuid import UUID, uuid4

from core.axis_convention import AxisConvention
from core.camera_config import PinholeCameraConfig
from core.capture_session_manifest import CaptureSessionManifest, RigCameraConfig, RigConfig
from core.transform import Float3, Float4
from numpy import asarray, float64
from PIL import Image
from pyzed.sl import (
    DEPTH_MODE,
    POSITIONAL_TRACKING_MODE,
    REFERENCE_FRAME,
    RESOLUTION,
    SVO_COMPRESSION_MODE,
    UNIT,
    VIDEO_SETTINGS,
    VIEW,
    Camera,
    InitParameters,
    Mat,
    Pose,
    PositionalTrackingParameters,
    RecordingParameters,
    Rect,
)
from scipy.spatial.transform import Rotation

from .zed_wrapper import (
    close_camera,
    disable_positional_tracking,
    disable_recording,
    enable_positional_tracking,
    enable_recording,
    get_camera_information,
    get_camera_settings,
    get_data,
    get_orientation_quaternion,
    grab,
    open_camera,
    retrieve_image,
    set_camera_settings,
    set_camera_settings_roi,
    update_pose,
)

logger = getLogger(__name__)


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
        self._pose = Pose()

    def start_capture(self, interval: float) -> UUID:
        reply: Future[UUID] = Future()
        self._commands.put(_StartCapture(interval=interval, reply=reply))
        return reply.result()

    def stop_capture(self) -> None:
        reply: Future[None] = Future()
        self._commands.put(_StopCapture(reply=reply))
        reply.result()

    # Reads mutable fields from a non-actor thread. Both fields are single-
    # reference Python attributes, so the GIL makes each read atomic; callers
    # see a self-consistent snapshot of each field but not necessarily of the
    # pair. Good enough for a status endpoint.
    def state(self) -> State:
        return State(capture_id=self._current_id, last_exception=self._last_exception)

    def run(self) -> None:
        while True:
            try:
                command = self._commands.get(timeout=self._queue_timeout())

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

                    self._capture_interval = None
                    self._next_capture_time = None

                    try:
                        self._stop()
                    except Exception as e:
                        command.reply.set_exception(e)
                        continue
                    finally:
                        self._current_id = None

                    command.reply.set_result(None)
            except Empty:
                pass

            if self._next_capture_time is None:
                continue

            try:
                self._tick()
            except Exception as e:
                logger.exception("Exception occurred during frame capture")
                self._last_exception = str(e)

    def _queue_timeout(self) -> float:
        if self._next_capture_time is None:
            return 0.1
        return 0.0

    def _tick(self) -> None:
        assert self._capture_interval is not None
        assert self._next_capture_time is not None

        self._advance_tracker()
        if time() >= self._next_capture_time:
            logger.info("Capturing frame")
            self._persist_current_frame()
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
        self._rig_directory().mkdir(parents=True, exist_ok=True)
        self._camera0_directory().mkdir(parents=True, exist_ok=True)
        self._camera1_directory().mkdir(parents=True, exist_ok=True)

        logger.info("Opening ZED camera")

        init = InitParameters()
        init.camera_resolution = RESOLUTION.HD1080
        init.coordinate_units = UNIT.METER
        init.camera_fps = 30
        init.enable_image_enhancement = True
        init.sdk_verbose = True
        init.depth_mode = DEPTH_MODE.NONE
        # Without this the SDK keeps running depth in the background to stabilize tracking, even when depth_mode is NONE.
        init.depth_stabilization = 0
        open_camera(self._camera, init)

        if get_camera_settings(self._camera, VIDEO_SETTINGS.SHARPNESS) != 4:
            set_camera_settings(self._camera, VIDEO_SETTINGS.SHARPNESS, 4)

        recording_params = RecordingParameters()
        recording_params.video_filename = str(self._rig_directory() / "video.svo2")
        recording_params.compression_mode = SVO_COMPRESSION_MODE.H265
        enable_recording(self._camera, recording_params)

        # TODO: _meter_and_lock was written for ZED 2 (USB) — may not work on ZED X (GMSL2/ISP)
        # print("Metering and locking exposure, gain, and white balance")
        # exposure, gain, white_balance = self._meter_and_lock(0.25, 0.25, 0.5, 0.5)
        # with open(self._output_directory() / "metered_values.json", "w") as config_file:
        #     dump({"exposure": exposure, "gain": gain, "white_balance": white_balance}, config_file, indent=4)

        positionTrackingParameters = PositionalTrackingParameters()
        positionTrackingParameters.enable_imu_fusion = True
        positionTrackingParameters.set_floor_as_origin = False
        positionTrackingParameters.mode = POSITIONAL_TRACKING_MODE.GEN_3
        logger.info(
            "Enabling positional tracking mode=%s depth_mode=%s depth_stabilization=%d",
            positionTrackingParameters.mode.name,
            init.depth_mode.name,
            init.depth_stabilization,
        )
        enable_positional_tracking(self._camera, positionTrackingParameters)

        logger.info("Writing manifest.json")

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

        with open(self._output_directory() / "manifest.json", "w") as config_file:
            config_file.write(
                CaptureSessionManifest(
                    axis_convention=AxisConvention.OPENCV,
                    capture_interval_seconds=self._capture_interval,
                    rigs=[
                        RigConfig(
                            id="rig0",
                            cameras=[
                                RigCameraConfig(
                                    id="camera0",
                                    ref_sensor=True,
                                    rotation=Float4(x=0.0, y=0.0, z=0.0, w=1.0),
                                    translation=Float3(x=0.0, y=0.0, z=0.0),
                                    camera_config=PinholeCameraConfig(
                                        width=left_camera.image_size.width,
                                        height=left_camera.image_size.height,
                                        orientation="TOP_LEFT",
                                        fx=left_camera.fx,
                                        fy=left_camera.fy,
                                        cx=left_camera.cx,
                                        cy=left_camera.cy,
                                    ),
                                ),
                                RigCameraConfig(
                                    id="camera1",
                                    ref_sensor=False,
                                    rotation=Float4(
                                        x=stereo_transform_rotation[0],
                                        y=stereo_transform_rotation[1],
                                        z=stereo_transform_rotation[2],
                                        w=stereo_transform_rotation[3],
                                    ),
                                    translation=Float3(
                                        # TODO: Figure out why the x component needs to be negated
                                        x=-stereo_transform_translation[0],
                                        y=stereo_transform_translation[1],
                                        z=stereo_transform_translation[2],
                                    ),
                                    camera_config=PinholeCameraConfig(
                                        width=right_camera.image_size.width,
                                        height=right_camera.image_size.height,
                                        orientation="TOP_LEFT",
                                        fx=right_camera.fx,
                                        fy=right_camera.fy,
                                        cx=right_camera.cx,
                                        cy=right_camera.cy,
                                    ),
                                ),
                            ],
                        )
                    ],
                ).model_dump_json(indent=4)
            )

        logger.info("Writing frame.csv header")

        with open(self._rig_directory() / "frames.csv", "w", newline="") as csv_file:
            csv_writer = writer(csv_file)
            csv_writer.writerow(["timestamp_ms", "gx", "gy", "gz"])

        logger.info("Capture started")

    def _stop(self):
        disable_recording(self._camera)
        disable_positional_tracking(self._camera)
        close_camera(self._camera)
        logger.info("Capture stopped")

    def _advance_tracker(self) -> None:
        grab(self._camera)
        update_pose(self._camera, self._pose, REFERENCE_FRAME.WORLD)

    def _persist_current_frame(self) -> None:
        timestamp = int(self._pose.timestamp.get_milliseconds())
        rotation_world_from_camera = get_orientation_quaternion(self._pose)

        # ZED's positional tracking initialises its world frame gravity-aligned (IMAGE/OpenCV convention:
        # +Y down). Projecting world's +Y axis into the current rig-local frame yields gravity-in-rig.
        # Camera0 is the reference sensor with identity rig↔camera0, so this is also gravity-in-camera0.
        rotation_camera_from_world = Rotation.from_quat(rotation_world_from_camera).as_matrix().T
        gravity_in_rig_local = rotation_camera_from_world @ asarray([0.0, 1.0, 0.0], dtype=float64)

        with open(self._rig_directory() / "frames.csv", "a", newline="") as csv_file:
            csv_writer = writer(csv_file)
            csv_writer.writerow([timestamp, *gravity_in_rig_local.tolist()])

        image_buffer = Mat()
        retrieve_image(self._camera, image_buffer, VIEW.LEFT)
        self._write_jpeg(image_buffer, self._camera0_directory() / f"{timestamp}.jpg")
        retrieve_image(self._camera, image_buffer, VIEW.RIGHT)
        self._write_jpeg(image_buffer, self._camera1_directory() / f"{timestamp}.jpg")

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
        settle_buffer = Mat()
        start = perf_counter()
        settle_for = 1.5
        while (perf_counter() - start) < settle_for:
            try:
                grab(self._camera)
                retrieve_image(self._camera, settle_buffer, VIEW.LEFT_UNRECTIFIED)
            except Exception:
                logger.exception("Exception occurred while settling")

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
