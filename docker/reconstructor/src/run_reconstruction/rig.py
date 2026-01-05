from core.axis_convention import AxisConvention, change_basis_opencv_from_unity_pose
from core.camera_config import transform_intrinsics
from core.capture_session_manifest import RigCameraConfig, RigConfig
from core.transform import Float3, Float4
from numpy import array, float64
from numpy.typing import NDArray
from pycolmap import Camera as ColmapCamera
from pycolmap import RigConfig as ColmapRigConfig
from pycolmap import RigConfigCamera as ColmapRigConfigCamera
from pycolmap import Rigid3d, Rotation3d
from scipy.spatial.transform import Rotation


class Transform:
    def __init__(self, rotation: NDArray[float64], translation: NDArray[float64]):
        self.rotation = rotation
        self.translation = translation


class Rig:
    def __init__(self, rig_config: RigConfig, axis_convention: AxisConvention, frames_csv: str):
        ref_sensors = [camera for camera in rig_config.cameras if camera.ref_sensor]
        if len(ref_sensors) != 1:
            raise ValueError(f"Rig {rig_config.id} must have exactly one reference sensor")
        ref_sensor = ref_sensors[0]
        if ref_sensor.rotation != Float4(w=1.0, x=0.0, y=0.0, z=0.0):
            raise ValueError(f"Reference sensor {ref_sensor.id} in rig {rig_config.id} must have identity rotation")
        if ref_sensor.translation != Float3(x=0.0, y=0.0, z=0.0):
            raise ValueError(f"Reference sensor {ref_sensor.id} in rig {rig_config.id} must have zero translation")

        # We should support this case, but it is not currently used anywhere, so I am punting on implementing it, and rasising an error instead.
        if len(rig_config.cameras) > 1 and axis_convention != AxisConvention.OPENCV:
            raise ValueError("Rigs with multiple cameras only support OPENCV axis convention")

        self.cameras: dict[str, tuple[RigCameraConfig, ColmapCamera]] = {}
        rig_camera_configs: list[ColmapRigConfigCamera] = []
        for camera in rig_config.cameras:
            width, height, *params = transform_intrinsics(camera.camera_config)
            self.cameras[camera.id] = (camera, ColmapCamera(width=width, height=height, model="PINHOLE", params=params))

            rig_camera_configs.append(
                ColmapRigConfigCamera(
                    image_prefix=f"{rig_config.id}/{camera.id}/",
                    ref_sensor=camera.ref_sensor or False,
                    cam_from_rig=Rigid3d(
                        rotation=Rotation3d(
                            Rotation.from_quat([
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

        self.frame_poses: dict[str, Transform] = {}
        for frame in frames_csv.splitlines()[1:]:  # Skip header
            frame_id, tx, ty, tz, qx, qy, qz, qw = frame.strip().split(",")
            rotation_world_from_rig = Rotation.from_quat([float(qx), float(qy), float(qz), float(qw)]).as_matrix()
            translation_world_from_rig = array([float(tx), float(ty), float(tz)], dtype=float)

            if axis_convention == AxisConvention.UNITY:
                (translation_world_from_rig, rotation_world_from_rig) = change_basis_opencv_from_unity_pose(
                    translation_world_from_rig, rotation_world_from_rig
                )

            self.frame_poses[frame_id] = Transform(
                rotation=rotation_world_from_rig, translation=translation_world_from_rig
            )
