from __future__ import annotations

from concurrent.futures import Future
from csv import writer
from dataclasses import dataclass
from logging import getLogger
from pathlib import Path
from queue import Empty, Queue
from socket import AF_UNIX, SOCK_STREAM, socket
from threading import Thread
from time import monotonic, perf_counter, sleep, time
from typing import Union, cast
from uuid import UUID, uuid4

from core.axis_convention import AxisConvention
from core.camera_config import PinholeCameraConfig
from core.capture_session_manifest import CaptureSessionManifest, RigCameraConfig, RigConfig
from core.transform import Float3, Float4
from numpy import asarray, float64, ndarray
from PIL import Image
from pyzed.sl import (
    COORDINATE_SYSTEM,
    DEPTH_MODE,
    POSITIONAL_TRACKING_MODE,
    POSITIONAL_TRACKING_STATE,
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
    CameraOpenError,
    close_camera,
    disable_positional_tracking,
    disable_recording,
    enable_positional_tracking,
    enable_recording,
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

logger = getLogger(__name__)

# Persist only after the tracker holds OK this many consecutive grabs (~0.3 s at
# 30 Hz), so SEARCHING-state cold-start poses don't enter the trajectory. The
# backstop persists anyway if OK is never reached (feature-poor scene, covered lens).
STABILIZE_REQUIRED_OK_FRAMES = 10
STABILIZE_BACKSTOP_SECONDS = 8.0

# Cheap camera-readiness signal mirroring the wait_for_zed_camera boot gate: the
# SDK reaches the sensors via the nvargus socket and the V4L2 nodes, so their
# presence proxies camera-subsystem health. The idle actor re-probes it to drop a
# latched open failure once a cold-boot daemon race resolves.
ARGUS_SOCKET = Path("/tmp/argus_socket")
VIDEO_NODES = (Path("/dev/video0"), Path("/dev/video1"))
LAST_EXCEPTION_REPROBE_SECONDS = 2.0

# A cold-boot Camera.open can race the GMSL camera daemons before they finish
# bringing the sensors up. The install-zed path brings the stack up without the
# boot gate that would otherwise serialize this, so the open is the only place
# that sees current readiness. The failure is transient: retry within this window
# before surfacing it.
CAMERA_OPEN_RETRY_SECONDS = 30.0
CAMERA_OPEN_RETRY_INTERVAL_SECONDS = 1.0


@dataclass(frozen=True)
class State:
    capture_id: UUID | None
    tracking_state: str
    stabilizing: bool
    last_exception: str | None


@dataclass(frozen=True)
class _StartCapture:
    interval: float
    reply: Future[UUID]


@dataclass(frozen=True)
class _StopCapture:
    reply: Future[None]


@dataclass(frozen=True)
class _PersistJob:
    timestamp: int
    rig_directory: Path
    camera0_directory: Path
    camera1_directory: Path
    camera_center: list[float]
    rotation: list[float]
    left_pixels: ndarray
    right_pixels: ndarray


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
        self._consecutive_ok_frames = 0
        self._stabilize_deadline: float | None = None
        self._tracking_state: str = POSITIONAL_TRACKING_STATE.OFF.name
        self._last_exception: str | None = None
        self._next_reprobe_time: float = 0.0

        self._camera = Camera()
        self._pose = Pose()

        # Bounded so the writer never silently leaks behind; 4 slots is ~2 s of
        # headroom at the 500 ms persistence cadence, which is more than enough
        # for steady-state JPEG-encode + disk-write latency on the Jetson. If
        # the writer ever falls further behind than that, the grab thread blocks
        # on put — which surfaces the lag instead of hiding it.
        self._persist_queue: Queue[_PersistJob | None] = Queue(maxsize=4)
        self._writer_thread: Thread | None = None

    def start_capture(self, interval: float) -> UUID:
        reply: Future[UUID] = Future()
        self._commands.put(_StartCapture(interval=interval, reply=reply))
        return reply.result()

    def stop_capture(self) -> None:
        reply: Future[None] = Future()
        self._commands.put(_StopCapture(reply=reply))
        reply.result()

    # Reads mutable fields from a non-actor thread. Each is a single-reference
    # Python attribute, so the GIL makes each read atomic; callers see a self-
    # consistent snapshot of each field but not necessarily of the set (the
    # stabilizing derivation reads two fields). Good enough for a status endpoint.
    def state(self) -> State:
        return State(
            capture_id=self._current_id,
            tracking_state=self._tracking_state,
            stabilizing=self._current_id is not None and self._next_capture_time is None,
            last_exception=self._last_exception,
        )

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
                    self._next_capture_time = None
                    self._consecutive_ok_frames = 0
                    self._tracking_state = POSITIONAL_TRACKING_STATE.OFF.name

                    try:
                        self._start()
                    except Exception as e:
                        self._current_id = None
                        self._capture_interval = None
                        self._next_capture_time = None
                        self._stabilize_deadline = None
                        self._last_exception = str(e)
                        command.reply.set_exception(e)
                        continue

                    self._stabilize_deadline = time() + STABILIZE_BACKSTOP_SECONDS
                    command.reply.set_result(self._current_id)

                else:
                    assert isinstance(command, _StopCapture)
                    if self._current_id is None:
                        command.reply.set_exception(InvalidStateException("No capture running"))
                        continue

                    self._capture_interval = None
                    self._next_capture_time = None
                    self._stabilize_deadline = None
                    self._consecutive_ok_frames = 0
                    self._tracking_state = POSITIONAL_TRACKING_STATE.OFF.name

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

            if self._current_id is None:
                self._clear_latched_exception_if_camera_recovered()
                continue

            try:
                self._tick()
            except Exception as e:
                logger.exception("Exception occurred during frame capture")
                self._last_exception = str(e)

    def _queue_timeout(self) -> float:
        if self._current_id is None:
            return 0.1
        return 0.0

    def _clear_latched_exception_if_camera_recovered(self) -> None:
        if self._last_exception is None:
            return

        now = monotonic()
        if now < self._next_reprobe_time:
            return

        self._next_reprobe_time = now + LAST_EXCEPTION_REPROBE_SECONDS
        if self._camera_reachable():
            logger.info("Camera subsystem reachable again; clearing latched open failure")
            self._last_exception = None

    def _camera_reachable(self) -> bool:
        if any(not node.exists() for node in VIDEO_NODES):
            return False

        try:
            connection = socket(AF_UNIX, SOCK_STREAM)
            connection.settimeout(1.0)
            connection.connect(str(ARGUS_SOCKET))
            connection.close()
        except OSError:
            return False

        return True

    def _tick(self) -> None:
        assert self._capture_interval is not None

        state = self._advance_tracker()
        self._tracking_state = state.name

        if self._next_capture_time is None:
            self._begin_persisting_when_stable(state)
            return

        if time() >= self._next_capture_time:
            logger.info("Capturing frame")
            self._persist_current_frame()
            self._next_capture_time += self._capture_interval

    def _begin_persisting_when_stable(self, state: POSITIONAL_TRACKING_STATE) -> None:
        assert self._stabilize_deadline is not None

        if state == POSITIONAL_TRACKING_STATE.OK:
            self._consecutive_ok_frames += 1
        else:
            self._consecutive_ok_frames = 0

        if self._consecutive_ok_frames >= STABILIZE_REQUIRED_OK_FRAMES:
            logger.info("VIO stabilized (tracking=OK); beginning frame persistence")
        elif time() >= self._stabilize_deadline:
            logger.warning(
                "VIO stabilization backstop reached after %.1fs with tracking=%s; persisting anyway",
                STABILIZE_BACKSTOP_SECONDS,
                self._tracking_state,
            )
        else:
            return

        self._next_capture_time = time()

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
        # IMAGE is the OpenCV axis convention the manifest declares and the reconstructor assumes.
        init.coordinate_system = COORDINATE_SYSTEM.IMAGE
        init.camera_fps = 30
        init.enable_image_enhancement = True
        init.sdk_verbose = True
        init.depth_mode = DEPTH_MODE.NEURAL_LIGHT
        self._open_camera_with_retry(init)

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
            csv_writer.writerow(["timestamp_ms", "tx", "ty", "tz", "qx", "qy", "qz", "qw"])

        # Spawn last so an earlier failure in _start has no writer to tear down.
        self._writer_thread = Thread(target=self._writer_loop, name="ZedWriter", daemon=True)
        self._writer_thread.start()

        logger.info("Capture started")

    def _open_camera_with_retry(self, init: InitParameters) -> None:
        deadline = monotonic() + CAMERA_OPEN_RETRY_SECONDS
        attempt = 0
        while True:
            attempt += 1
            try:
                open_camera(self._camera, init)
                return
            except CameraOpenError as error:
                if monotonic() >= deadline:
                    raise

                logger.info(
                    "ZED open failed on attempt %d (camera subsystem not ready yet); retrying in %.0fs: %s",
                    attempt,
                    CAMERA_OPEN_RETRY_INTERVAL_SECONDS,
                    error,
                )
                sleep(CAMERA_OPEN_RETRY_INTERVAL_SECONDS)

    def _stop(self):
        # Drain pending writes before tearing down the SDK so the last few
        # persisted frames make it to disk. Sentinel + join leaves the queue
        # empty and the writer thread joined.
        if self._writer_thread is not None:
            self._persist_queue.put(None)
            self._writer_thread.join()
            self._writer_thread = None

        disable_recording(self._camera)
        disable_positional_tracking(self._camera)
        close_camera(self._camera)
        logger.info("Capture stopped")

    def _advance_tracker(self) -> POSITIONAL_TRACKING_STATE:
        grab(self._camera)
        return update_pose(self._camera, self._pose, REFERENCE_FRAME.WORLD)

    def _persist_current_frame(self) -> None:
        timestamp = int(self._pose.timestamp.get_milliseconds())
        camera_center = get_translation_array(self._pose).tolist()
        rotation = get_orientation_quaternion(self._pose).tolist()

        # retrieve_image must stay on the actor thread (the SDK's camera handle
        # is not thread-safe); the pixel data is copied off the SDK-owned Mat
        # before enqueueing so the next retrieve_image's reuse of the buffer
        # can't race the writer thread mid-encode.
        image_buffer = Mat()
        retrieve_image(self._camera, image_buffer, VIEW.LEFT)
        left_pixels = self._extract_rgb(image_buffer)
        retrieve_image(self._camera, image_buffer, VIEW.RIGHT)
        right_pixels = self._extract_rgb(image_buffer)

        self._persist_queue.put(_PersistJob(
            timestamp=timestamp,
            rig_directory=self._rig_directory(),
            camera0_directory=self._camera0_directory(),
            camera1_directory=self._camera1_directory(),
            camera_center=camera_center,
            rotation=rotation,
            left_pixels=left_pixels,
            right_pixels=right_pixels,
        ))

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

    def _extract_rgb(self, image_matrix_buffer: Mat) -> ndarray:
        arr = get_data(image_matrix_buffer)  # uint8, HxWx{3,4}
        if arr.ndim != 3 or arr.shape[2] < 3:
            raise ValueError(f"Unexpected image shape {arr.shape} dtype {arr.dtype}")
        # BG* -> RGB, then copy so the returned array doesn't alias the Mat's
        # backing buffer (which the next retrieve_image will overwrite).
        return arr[:, :, :3][:, :, ::-1].copy()

    def _writer_loop(self) -> None:
        while True:
            job = self._persist_queue.get()
            if job is None:
                return
            try:
                with open(job.rig_directory / "frames.csv", "a", newline="") as csv_file:
                    csv_writer = writer(csv_file)
                    csv_writer.writerow([job.timestamp, *job.camera_center, *job.rotation])
                self._encode_jpeg(job.left_pixels, job.camera0_directory / f"{job.timestamp}.jpg")
                self._encode_jpeg(job.right_pixels, job.camera1_directory / f"{job.timestamp}.jpg")
            except Exception:
                logger.exception("Persist failed for timestamp=%d", job.timestamp)

    def _encode_jpeg(self, pixels: ndarray, path: Path, quality: int = 75) -> None:
        Image.fromarray(pixels, mode="RGB").save(
            str(path), format="JPEG", quality=quality, optimize=True, progressive=True
        )
