from io import BytesIO
from pathlib import Path
from tarfile import open as open_tar
from typing import TYPE_CHECKING, Any

from core.classes import Quaternion, Vector3
from core.rig import Config, RigCameraConfig, RigConfig, Transform, transform_intrinsics
from numpy import array, float64
from pycolmap import Camera as ColmapCamera
from pycolmap import RigConfig as ColmapRigConfig
from pycolmap import RigConfigCamera as ColmapRigConfigCamera
from pycolmap import Rigid3d, Rotation3d
from scipy.spatial.transform import Rotation

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client
else:
    S3Client = Any


class Rig:
    def __init__(self, rig_config: RigConfig, frames_csv: str):
        ref_sensors = [camera for camera in rig_config.cameras if camera.ref_sensor]
        if len(ref_sensors) != 1:
            raise ValueError(f"Rig {rig_config.id} must have exactly one reference sensor")
        ref_sensor = ref_sensors[0]
        if ref_sensor.rotation != Quaternion(w=1.0, x=0.0, y=0.0, z=0.0):
            raise ValueError(f"Reference sensor {ref_sensor.id} in rig {rig_config.id} must have identity rotation")
        if ref_sensor.translation != Vector3(x=0.0, y=0.0, z=0.0):
            raise ValueError(f"Reference sensor {ref_sensor.id} in rig {rig_config.id} must have zero translation")

        self.cameras: dict[str, tuple[RigCameraConfig, ColmapCamera]] = {}
        rig_camera_configs: list[ColmapRigConfigCamera] = []
        for camera in rig_config.cameras:
            self.cameras[camera.id] = (
                camera,
                ColmapCamera(
                    width=camera.camera_config.width,
                    height=camera.camera_config.height,
                    model="PINHOLE",
                    params=transform_intrinsics(camera.camera_config),
                ),
            )

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
            rotation_world_from_rig = Rotation.from_quat([float(qx), float(qy), float(qz), float(qw)])
            translation_world_from_rig = array([float(tx), float(ty), float(tz)], dtype=float)
            self.frame_poses[frame_id] = Transform(
                rotation=rotation_world_from_rig.as_matrix(), translation=translation_world_from_rig
            )


def load_capture_session_manifest(
    captures_bucket: str, capture_id: str, s3_client: S3Client, capture_session_directory: Path
):
    with open_tar(
        fileobj=BytesIO(s3_client.get_object(Bucket=captures_bucket, Key=f"{capture_id}.tar")["Body"].read()),
        mode="r:*",
    ) as tar:
        tar.extractall(path=capture_session_directory)

    with open(capture_session_directory / "config.json", "rb") as file:
        config = Config.model_validate_json(file.read().decode("utf-8"))

    return {rig.id: Rig(rig, (capture_session_directory / f"{rig.id}/frames.csv").read_text()) for rig in config.rigs}
