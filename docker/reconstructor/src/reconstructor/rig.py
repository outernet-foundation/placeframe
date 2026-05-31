from dataclasses import dataclass

from core.axis_convention import AxisConvention, basis_change_opencv_from_unity
from core.capture_session_manifest import RigCameraConfig, RigConfig
from core.image_preprocess import canonicalize_intrinsics
from core.transform import Float3, Float4
from numpy import array, float64
from numpy.typing import NDArray  # noqa: TID251 — Phase T piece 3 follow-up migration
from pycolmap import Camera as ColmapCamera
from pycolmap import RigConfig as ColmapRigConfig
from pycolmap import RigConfigCamera as ColmapRigConfigCamera
from pycolmap import Rigid3d, Rotation3d
from scipy.spatial.transform import Rotation


@dataclass(frozen=True)
class FramePose:
    translation: NDArray[float64] | None
    gravity_in_rig_local: NDArray[float64] | None


class Rig:
    def __init__(
        self,
        rig_config: RigConfig,
        axis_convention: AxisConvention,
        frames_csv: str,
        held_out_frame_timestamps: set[int] | None = None,
    ):
        ref_sensors = [camera for camera in rig_config.cameras if camera.ref_sensor]
        if len(ref_sensors) != 1:
            raise ValueError(f"Rig {rig_config.id} must have exactly one reference sensor")
        ref_sensor = ref_sensors[0]
        if ref_sensor.rotation != Float4(w=1.0, x=0.0, y=0.0, z=0.0):
            raise ValueError(f"Reference sensor {ref_sensor.id} in rig {rig_config.id} must have identity rotation")
        if ref_sensor.translation != Float3(x=0.0, y=0.0, z=0.0):
            raise ValueError(f"Reference sensor {ref_sensor.id} in rig {rig_config.id} must have zero translation")

        if len(rig_config.cameras) > 1 and axis_convention != AxisConvention.OPENCV:
            raise ValueError("Rigs with multiple cameras only support OPENCV axis convention")

        self.id = rig_config.id
        self.ref_camera_id = ref_sensor.id
        self.is_multi_camera = len(rig_config.cameras) > 1
        self.cameras: dict[str, tuple[RigCameraConfig, ColmapCamera]] = {}
        rig_camera_configs: list[ColmapRigConfigCamera] = []
        for camera in rig_config.cameras:
            width, height, *params = canonicalize_intrinsics(camera.camera_config)
            self.cameras[camera.id] = (camera, ColmapCamera(width=width, height=height, model="PINHOLE", params=params))

            rig_camera_configs.append(
                ColmapRigConfigCamera(
                    image_prefix=f"{rig_config.id}/{camera.id}/",
                    ref_sensor=camera.ref_sensor or False,
                    cam_from_rig=Rigid3d(
                        rotation=Rotation3d(
                            matrix=Rotation.from_quat([
                                camera.rotation.x,
                                camera.rotation.y,
                                camera.rotation.z,
                                camera.rotation.w,
                            ]).as_matrix()
                        ),
                        translation=array(
                            [camera.translation.x, camera.translation.y, camera.translation.z], dtype=float64
                        ).reshape(3, 1),
                    ),
                )
            )

        self.colmap_rig_config = ColmapRigConfig(cameras=rig_camera_configs)

        self.frame_poses: dict[str, FramePose] = {}
        for frame in frames_csv.splitlines()[1:]:
            fields = frame.strip().split(",")
            frame_id = fields[0]
            if held_out_frame_timestamps is not None and int(frame_id) in held_out_frame_timestamps:
                continue
            pose = _parse_frame_pose(fields[1:], axis_convention)
            if not self.is_multi_camera and pose.translation is None:
                raise ValueError(
                    f"Monocular rig {rig_config.id} requires per-frame position priors in frames.csv "
                    f"(frame {frame_id} has only gravity columns)"
                )
            self.frame_poses[frame_id] = pose


def image_name(rig_id: str, camera_id: str, frame_id: str) -> str:
    return f"{rig_id}/{camera_id}/{frame_id}.jpg"


def _parse_frame_pose(values: list[str], axis_convention: AxisConvention) -> FramePose:
    if len(values) == 3:
        # gx, gy, gz — gravity samples only, no position prior.
        gravity = array([float(values[0]), float(values[1]), float(values[2])], dtype=float64)
        if axis_convention == AxisConvention.UNITY:
            gravity = basis_change_opencv_from_unity @ gravity
        return FramePose(translation=None, gravity_in_rig_local=gravity)

    if len(values) == 6:
        # tx, ty, tz, gx, gy, gz — VIO position plus gravity samples.
        translation = array([float(values[0]), float(values[1]), float(values[2])], dtype=float64)
        gravity = array([float(values[3]), float(values[4]), float(values[5])], dtype=float64)
        if axis_convention == AxisConvention.UNITY:
            translation = basis_change_opencv_from_unity @ translation
            gravity = basis_change_opencv_from_unity @ gravity
        return FramePose(translation=translation, gravity_in_rig_local=gravity)

    if len(values) == 7:
        # tx, ty, tz, qx, qy, qz, qw — VIO position with quaternion; rotation discarded, only the
        # position is consumed downstream when the rig is monocular.
        translation = array([float(values[0]), float(values[1]), float(values[2])], dtype=float64)
        if axis_convention == AxisConvention.UNITY:
            translation = basis_change_opencv_from_unity @ translation
        return FramePose(translation=translation, gravity_in_rig_local=None)

    raise ValueError(f"Unrecognized frames.csv row width: {len(values) + 1} columns")
