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
    # World-frame position of the rig (= camera0 center in world). Unity emits this as
    # CameraTranslationUnityWorldFromCamera; ZED writes it as the SDK's world_from_rig translation.
    translation: NDArray[float64]
    # world_from_rig rotation derived from the VIO quaternion.
    rotation: Rotation3d
    # Unit down vector ([0, 1, 0] in OpenCV world) re-expressed in rig-local coordinates via
    # rig_from_world = world_from_rig.T applied to world-down.
    gravity_in_rig_local: NDArray[float64]


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
            frame_id, tx, ty, tz, qx, qy, qz, qw = frame.strip().split(",")
            if held_out_frame_timestamps is not None and int(frame_id) in held_out_frame_timestamps:
                continue
            translation = array([float(tx), float(ty), float(tz)], dtype=float64)
            rotation_matrix = Rotation.from_quat([float(qx), float(qy), float(qz), float(qw)]).as_matrix()
            if axis_convention == AxisConvention.UNITY:
                translation = basis_change_opencv_from_unity @ translation
                rotation_matrix = basis_change_opencv_from_unity @ rotation_matrix @ basis_change_opencv_from_unity.T
            # OpenCV world-down is [0, 1, 0]; rig_from_world @ world_down = rotation_matrix.T @ [0, 1, 0]
            # which is the second row of rotation_matrix.
            gravity_in_rig_local = rotation_matrix[1, :].astype(float64, copy=True)
            self.frame_poses[frame_id] = FramePose(
                translation=translation,
                rotation=Rotation3d(matrix=rotation_matrix),
                gravity_in_rig_local=gravity_in_rig_local,
            )
