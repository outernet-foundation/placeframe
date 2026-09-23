from dataclasses import dataclass

from core.axis_convention import AxisConvention, basis_change_opencv_from_unity
from core.camera_config import PinholeCameraConfig, SphericalCameraConfig
from core.capture_session_manifest import RigCameraConfig, RigConfig
from core.image_preprocess import LOCAL_FEATURE_RESIZE_SHORTER_SIDE, canonicalize_intrinsics
from core.reconstruction_options import ReconstructionOptions
from core.transform import Float3, Float4
from numpy import array, eye, float64
from numpy.typing import NDArray  # noqa: TID251 — tracked in PLE-233
from panorama.projection import View, cam_from_rig, camera_params, layout, opencv_from_cam
from pycolmap import Camera as ColmapCamera
from pycolmap import RigConfig as ColmapRigConfig
from pycolmap import RigConfigCamera as ColmapRigConfigCamera
from pycolmap import Rigid3d, Rotation3d
from scipy.spatial.transform import Rotation


@dataclass(frozen=True)
class SphericalExpansion:
    """A spherical camera, and the views a reconstructor models it through.

    The frames of `source_camera_id` are whole spheres, which no COLMAP camera
    model can represent. Each view is rendered from them as an equidistant
    fisheye narrow enough to model (see the panorama package); all views share
    the sphere's optical centre, so they differ only by rotation.
    """

    source_camera_id: str
    config: SphericalCameraConfig
    views: tuple[View, ...]
    reference: View
    size: int
    fov_deg: float

    def camera_id(self, view: View) -> str:
        """Derived camera id, and so the image folder the rendered views go in."""
        return f"{self.source_camera_id}_{view.name}"


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
        options: ReconstructionOptions | None = None,
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

        options = options or ReconstructionOptions()
        self.id = rig_config.id
        self.ref_camera_id = ref_sensor.id
        self.is_multi_camera = len(rig_config.cameras) > 1
        self.cameras: dict[str, tuple[RigCameraConfig, ColmapCamera]] = {}
        self.spherical_expansion: SphericalExpansion | None = _spherical_expansion(rig_config, options)
        rig_camera_configs: list[ColmapRigConfigCamera] = []

        if self.spherical_expansion is not None:
            expansion = self.spherical_expansion
            # The views replace the sphere, so one of them has to be COLMAP's
            # reference sensor; that moves the rig frame into its camera frame,
            # which `rig_from_manifest_rig` below carries into the frame poses.
            # is_multi_camera stays False: it means "a baseline anchors metric
            # scale, so bundle adjustment can drop position priors", and views of
            # one sphere share an optical centre, so they anchor nothing.
            canonical = LOCAL_FEATURE_RESIZE_SHORTER_SIDE  # square views, so both sides land here
            for view in expansion.views:
                self.cameras[expansion.camera_id(view)] = (
                    ref_sensor,
                    ColmapCamera(
                        width=canonical,
                        height=canonical,
                        model="OPENCV_FISHEYE",
                        params=camera_params(canonical, expansion.fov_deg),
                    ),
                )
                rig_camera_configs.append(
                    ColmapRigConfigCamera(
                        image_prefix=f"{rig_config.id}/{expansion.camera_id(view)}/",
                        ref_sensor=view == expansion.reference,
                        cam_from_rig=Rigid3d(
                            rotation=Rotation3d(matrix=cam_from_rig(view, expansion.reference)),
                            # One sphere, one optical centre: the views differ by rotation alone.
                            translation=array([0.0, 0.0, 0.0], dtype=float64).reshape(3, 1),
                        ),
                    )
                )
        else:
            for camera in rig_config.cameras:
                if not isinstance(camera.camera_config, PinholeCameraConfig):
                    raise TypeError(
                        f"Camera {camera.id} is a {type(camera.camera_config).__name__}; "
                        "only pinhole and spherical cameras can be reconstructed"
                    )
                width, height, *params = canonicalize_intrinsics(camera.camera_config)
                self.cameras[camera.id] = (
                    camera,
                    ColmapCamera(width=width, height=height, model="PINHOLE", params=params),
                )

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

        # The camera COLMAP treats as the rig's reference: a rendered view when the
        # capture is spherical, since the sphere itself is not one of its cameras.
        self.ref_colmap_camera_id = (
            ref_sensor.id
            if self.spherical_expansion is None
            else self.spherical_expansion.camera_id(self.spherical_expansion.reference)
        )

        # Rotation taking a direction in the manifest's rig frame into COLMAP's.
        # They differ only when a rendered view became the reference sensor; the
        # two frames always share an origin, so positions need no correction.
        self.rig_from_manifest_rig: NDArray[float64] = (
            eye(3) if self.spherical_expansion is None else opencv_from_cam(self.spherical_expansion.reference).T
        )

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
            # world_from_rig and rig-local gravity are stated in the manifest's rig
            # frame; carry both into COLMAP's (identical unless a view is the reference).
            self.frame_poses[frame_id] = FramePose(
                translation=translation,
                rotation=Rotation3d(matrix=rotation_matrix @ self.rig_from_manifest_rig.T),
                gravity_in_rig_local=self.rig_from_manifest_rig @ gravity_in_rig_local,
            )


def _spherical_expansion(rig_config: RigConfig, options: ReconstructionOptions) -> SphericalExpansion | None:
    """The spherical camera of this rig, with the views to render from it.

    Only a rig that is a single spherical camera is supported: mixing a sphere
    with other sensors would need the views composed with that camera's own pose
    in the rig, and no capture does that yet.
    """
    spherical = [c for c in rig_config.cameras if isinstance(c.camera_config, SphericalCameraConfig)]
    if not spherical:
        return None
    if len(rig_config.cameras) > 1:
        raise ValueError(f"Rig {rig_config.id} mixes a spherical camera with other cameras, which is not supported")

    camera = spherical[0]
    config = camera.camera_config
    assert isinstance(config, SphericalCameraConfig)
    if config.projection != "EQUIRECTANGULAR":
        raise ValueError(f"Camera {camera.id} has {config.projection} frames; only EQUIRECTANGULAR is supported")
    if config.orientation != "TOP_LEFT":
        raise ValueError(f"Camera {camera.id} has orientation {config.orientation}; spherical frames must be upright")
    if not 0 < options.spherical_view_fov_deg < 180:
        raise ValueError(
            f"spherical_view_fov_deg is {options.spherical_view_fov_deg}; COLMAP's fisheye models cannot "
            "represent a ray 90 degrees off axis, so a view must stay under 180 degrees"
        )

    views = layout(options.spherical_layout)
    return SphericalExpansion(
        source_camera_id=camera.id,
        config=config,
        views=views,
        reference=views[0],
        size=options.spherical_view_size,
        fov_deg=options.spherical_view_fov_deg,
    )
