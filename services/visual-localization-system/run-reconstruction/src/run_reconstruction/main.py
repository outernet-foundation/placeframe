from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path
from tarfile import open as open_tar
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, cast

import torch
from common.boto_clients import create_s3_client
from common.classes import Quaternion, RigCamera, RigConfig, Vector3, get_camera_intrinsics_type
from common.reconstruction_manifest import ReconstructionManifest
from cv2 import COLOR_BGR2GRAY, COLOR_BGR2RGB, IMREAD_COLOR, cvtColor, imdecode
from h5py import File
from hloc.extractors.dir import DIR
from hloc.extractors.superpoint import SuperPoint
from lightglue import LightGlue
from numpy import (
    array,
    asarray,
    eye,
    float16,
    float32,
    float64,
    frombuffer,
    int32,
    ndarray,
    nonzero,
    percentile,
    stack,
    uint8,
    uint32,
)
from numpy.linalg import norm
from numpy.typing import NDArray
from pycolmap import (
    Camera,
    Database,
    ImageMap,
    IncrementalPipelineOptions,
    Point3D,
    Point3DMap,
    PosePrior,
    RANSACOptions,
    Rigid3d,
    Rotation3d,
    TwoViewGeometryOptions,
)
from pycolmap import Image as PycolmapImage
from pycolmap import Image as pycolmapImage
from pycolmap import RigConfig as pycolmapRigConfig
from pycolmap import RigConfigCamera as pycolmapRigConfigCamera
from pycolmap._core import incremental_mapping, verify_matches
from scipy.spatial.transform import Rotation
from torch import Tensor, cuda, no_grad
from torch import float32 as torch_float32

from src.run_reconstruction.find_pairs import ImageTransform, pairs_from_poses

from .settings import get_settings
from .utility import tensor_from_numpy

settings = get_settings()

DEVICE = "cuda" if cuda.is_available() else "cpu"
print(f"Using device: {DEVICE}")

UINT64_MAX = 18446744073709551615  # sentinel used by Point2D.point3D_id default

WORK_DIR = Path("/tmp/reconstruction")
OUTPUT_DIRECTORY = WORK_DIR / "outputs"
IMAGES_DIRECTORY = WORK_DIR / "images"
IMAGES_DIRECTORY.mkdir(parents=True, exist_ok=True)
PAIRS_FILE = WORK_DIR / "pairs.txt"
GLOBAL_DESCRIPTORS_FILE = WORK_DIR / "global_descriptors.h5"
FEATURES_FILE = WORK_DIR / "features.h5"
COLMAP_DB_PATH = OUTPUT_DIRECTORY / "database.db"
COLMAP_SFM_DIRECTORY = OUTPUT_DIRECTORY / "sfm_model"
COLMAP_SFM_DIRECTORY.mkdir(parents=True, exist_ok=True)

WEIGHTS = "indoor"
DEFAULT_NEIGHBORS_COUNT = 12
RETRIEVAL_TOP_K = 20
# Prior weights (tweak as you like)
POSE_PRIOR_ROT_SIGMA_DEG = 5.0  # 1-sigma on rotation, in degrees
POSE_PRIOR_POS_SIGMA_M = 0.25  # 1-sigma on position, in meters
MIN_MODEL_SIZE = 10  # minimum number of registered images for a model to be valid
# TRACK_MIN_NUM_MATCH = 15
# BUNDLE_ADJUST_MAX_REPROJECTION = 1.0

s3_client = create_s3_client(
    s3_endpoint_url=settings.s3_endpoint_url, s3_access_key=settings.s3_access_key, s3_secret_key=settings.s3_secret_key
)


def _put_reconstruction_object(key: str, body: bytes):
    print(f"Putting object in bucket {settings.reconstructions_bucket} with key {settings.reconstruction_id}/{key}")
    s3_client.put_object(Bucket=settings.reconstructions_bucket, Key=f"{settings.reconstruction_id}/{key}", Body=body)


class Image:
    def __init__(
        self,
        frame_id: str,
        rig_id: str,
        camera: RigCamera,
        rotation_frame_from_world: Rotation,
        translation_frame_from_world: ndarray,
        buffer: bytes,
    ):
        self.name = f"{rig_id}/{camera['id']}/{frame_id}.jpg"
        self.rig_id = rig_id
        self.camera_id = camera["id"]
        rotation_camera_from_rig = Rotation.from_quat([
            camera["rotation"]["x"],
            camera["rotation"]["y"],
            camera["rotation"]["z"],
            camera["rotation"]["w"],
        ])
        translation_camera_from_rig = camera["translation"]
        self.rotation_camera_from_world = rotation_camera_from_rig * rotation_frame_from_world
        self.translation_camera_from_world = rotation_camera_from_rig.apply(translation_frame_from_world) + [
            translation_camera_from_rig["x"],
            translation_camera_from_rig["y"],
            translation_camera_from_rig["z"],
        ]

        self.bgr_image = imdecode(frombuffer(buffer, uint8), IMREAD_COLOR)
        rgb_image = cvtColor(self.bgr_image, COLOR_BGR2RGB)
        grayscale_image = cvtColor(self.bgr_image, COLOR_BGR2GRAY)

        self.rgb_tensor = (
            tensor_from_numpy(rgb_image)  # H×W×3, uint8
            .to(dtype=torch_float32, device=DEVICE)
            .permute(2, 0, 1)  # → 3×H×W
            .div(255.0)  # → Normalized float32
        )

        self.grayscale_tensor = (
            tensor_from_numpy(grayscale_image)  # H×W, uint8
            .to(dtype=torch_float32, device=DEVICE)
            .unsqueeze(0)  # → 1×H×W
            .div(255.0)  # → Normalized float32
        )

        destination = IMAGES_DIRECTORY / self.name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(buffer)


def _to_f32(t: Tensor) -> ndarray:
    return t.detach().cpu().numpy().astype(float32, copy=False)


def _to_f16(t: Tensor) -> ndarray:
    return t.detach().cpu().numpy().astype(float16, copy=False)


def main():
    print(f"Starting reconstruction {settings.reconstruction_id}")

    manifest: ReconstructionManifest = ReconstructionManifest.model_validate_json(
        s3_client.get_object(Bucket=settings.reconstructions_bucket, Key=f"{settings.reconstruction_id}/manifest.json")[
            "Body"
        ].read()
    )
    manifest.status = "running"
    _put_reconstruction_object(key="manifest.json", body=manifest.model_dump_json().encode("utf-8"))

    print("Loading capture data")

    # TODO: revise api to explode tar into s3 objects
    capture_tar = s3_client.get_object(Bucket=settings.captures_bucket, Key=f"{settings.capture_id}.tar")["Body"].read()

    def _get_capture_object(key: str) -> bytes:
        with open_tar(fileobj=BytesIO(capture_tar), mode="r:*") as tar:
            member = tar.getmember(key)
            file = tar.extractfile(member)
            assert file is not None
            return file.read()

    rigs = cast(RigConfig, json.loads(_get_capture_object("config.json").decode("utf-8")))["rigs"]

    # validate that each rig has exactly one reference sensor, and that the rotation and translation are identity for that sensor
    for rig in rigs:
        ref_sensors = [camera for camera in rig["cameras"] if camera["ref_sensor"]]
        if len(ref_sensors) != 1:
            raise ValueError(f"Rig {rig['id']} must have exactly one reference sensor")
        ref_sensor = ref_sensors[0]
        if ref_sensor["rotation"] != Quaternion(w=1.0, x=0.0, y=0.0, z=0.0):
            raise ValueError(f"Reference sensor {ref_sensor['id']} in rig {rig['id']} must have identity rotation")
        if ref_sensor["translation"] != Vector3(x=0.0, y=0.0, z=0.0):
            raise ValueError(f"Reference sensor {ref_sensor['id']} in rig {rig['id']} must have zero translation")

    images: Dict[str, Image] = {}
    for rig in rigs:
        for line in _get_capture_object(f"{rig['id']}/frames.csv").decode("utf-8").splitlines()[1:]:  # Skip header
            frame_id, tx, ty, tz, qx, qy, qz, qw = line.strip().split(",")
            frame_rotation_camera_from_world = Rotation.from_quat([float(qx), float(qy), float(qz), float(qw)])
            frame_translation_camera_from_world = array([float(tx), float(ty), float(tz)], dtype=float)

            for camera in rig["cameras"]:
                image = Image(
                    frame_id,
                    rig["id"],
                    camera,
                    frame_rotation_camera_from_world,
                    frame_translation_camera_from_world,
                    _get_capture_object(f"{rig['id']}/{camera['id']}/{frame_id}.jpg"),
                )
                images[image.name] = image

    print(f"Loading retrieval model: {'deep-image-retrieval'}")

    # PyTorch 2.6 flips torch.load default to weights_only=True, so we temporarily force legacy loading to read DIR’s pickled checkpoint;
    # see: https://dev-discuss.pytorch.org/t/bc-breaking-change-torch-load-is-being-flipped-to-use-weights-only-true-by-default-in-the-nightlies-after-137602/2573
    _orig_load = torch.load  # type: ignore

    def _load_legacy(*args, **kwargs):  # type: ignore
        kwargs.setdefault("weights_only", False)  # type: ignore
        return _orig_load(*args, **kwargs)  # type: ignore

    torch.load = _load_legacy
    dir: DIR = DIR({}).to(DEVICE).eval()
    torch.load = _orig_load

    print(f"Loading feature extraction model: {'SuperPoint'}")

    config: dict[str, Any] = {"weights": WEIGHTS}
    if manifest.options.max_keypoints_per_image is not None:
        config["max_keypoints"] = manifest.options.max_keypoints_per_image
    superpoint = SuperPoint(config).to(DEVICE).eval()

    print(f"Loading feature matching model: {'SuperGlue'}")

    # superglue = SuperGlue({"weights": WEIGHTS}).to(DEVICE).eval()
    matcher = LightGlue(features="superpoint", width_confidence=-1, depth_confidence=-1).eval().to(DEVICE)

    print("Extracting features")

    global_descriptors: dict[str, Tensor] = {}
    keypoints: dict[str, Tensor] = {}
    descriptors: dict[str, Tensor] = {}
    scores: dict[str, Tensor] = {}
    for image in images.values():
        print(f"  {image.name}")

        with no_grad():
            # Extract global descriptor using NetVLAD
            global_descriptors[image.name] = dir({"image": image.rgb_tensor.unsqueeze(0)})["global_descriptor"][0]

            # Extract local features and descriptors using SuperPoint
            superpoint_output = superpoint({"image": image.grayscale_tensor.unsqueeze(0)})
            keypoints[image.name] = superpoint_output["keypoints"][0]
            descriptors[image.name] = superpoint_output["descriptors"][0]
            scores[image.name] = superpoint_output["scores"][0]

    manifest.metrics.average_keypoints_per_image = float(sum(len(kp) for kp in keypoints.values()) / len(keypoints))
    _put_reconstruction_object(key="manifest.json", body=manifest.model_dump_json().encode("utf-8"))

    print("Matching features")

    # Find pairs of images to match
    if manifest.options.neightbors_count == -1:
        # exhaustive matching
        pairs_by_pose_proximity = [
            (a.name, b.name) for i, a in enumerate(images.values()) for j, b in enumerate(images.values()) if i < j
        ]
    else:
        pairs_by_pose_proximity = pairs_from_poses(
            [
                ImageTransform(name, rotation, translation)
                for name, (rotation, translation) in {
                    img.name: (img.rotation_camera_from_world.as_matrix(), img.translation_camera_from_world)
                    for img in images.values()
                }.items()
            ],
            min(manifest.options.neightbors_count or DEFAULT_NEIGHBORS_COUNT, max(1, len(images) - 1)),
        )

    # Canonicalize and deduplicate pairs
    pairs = {tuple(sorted((a, b))) for a, b in pairs_by_pose_proximity if a != b}

    PAIRS_FILE.parent.mkdir(parents=True, exist_ok=True)
    PAIRS_FILE.write_text("\n".join(f"{a} {b}" for a, b in pairs))

    # Match features using SuperGlue and add matches to COLMAP database
    all_matches: dict[Tuple[str, str], Tensor] = {}
    for imageA, imageB in pairs:
        print(f"  {imageA}:{imageB}")

        image_size = torch.tensor([images[imageA].bgr_image.shape[:2]], device=DEVICE)

        all_matches[(imageA, imageB)] = matcher({
            "image0": {
                "keypoints": keypoints[imageA].unsqueeze(0),
                "descriptors": descriptors[imageA].unsqueeze(0).transpose(-1, -2),
                "image_size": image_size,
            },
            "image1": {
                "keypoints": keypoints[imageB].unsqueeze(0),
                "descriptors": descriptors[imageB].unsqueeze(0).transpose(-1, -2),
                "image_size": image_size,
            },
        })["matches0"][0]

    valid_matches: dict[Tuple[str, str], NDArray[int32]] = {}
    for imageA, imageB in pairs:
        matches = all_matches[(imageA, imageB)].cpu().numpy().astype(int32)

        # Filter invalid matches
        valid_mask = matches >= 0
        query_indices = nonzero(valid_mask)[0]
        train_indices = matches[valid_mask]

        # Convert matches to COLMAP format
        valid_matches[(imageA, imageB)] = stack((query_indices, train_indices), axis=1).astype(int32)

        # # Upload to S3
        # _put_reconstruction_object(
        #     key=f"matches/{f'{imageA}_{imageB}'.replace('/', '_')}.npz",
        #     body=json.dumps({"matches": two_view_geometries[(imageA, imageB)].tolist()}).encode("utf-8"),
        # )

    for (imageA, imageB), matches in valid_matches.items():
        print(f"Pair {imageA}-{imageB}: {len(matches)} matches")
        # Check for duplicate query indices (same point matched multiple times)
        unique_query = len(set(matches[:, 0]))
        if unique_query != len(matches):
            print(f"  WARNING: {len(matches) - unique_query} duplicate query indices!")

    print("Seeding COLMAP database")

    if COLMAP_DB_PATH.exists():
        COLMAP_DB_PATH.unlink()
    database = Database(str(COLMAP_DB_PATH))

    # Write cameras to database and create rig configuration
    camera_id_to_colmap_camera_id: dict[Tuple[str, str], int] = {}
    rig_configs: List[pycolmapRigConfig] = []
    for rig in rigs:
        rig_camera_configs: List[pycolmapRigConfigCamera] = []
        for camera in rig["cameras"]:
            the_camera = Camera(
                width=camera["intrinsics"]["width"],
                height=camera["intrinsics"]["height"],
                model=camera["intrinsics"]["model"],
                params=get_camera_intrinsics_type(camera["intrinsics"]),
            )
            the_camera.has_prior_focal_length = True

            camera_id_to_colmap_camera_id[(rig["id"], camera["id"])] = database.write_camera(the_camera)

            R_cam_from_rig = Rotation.from_quat([
                camera["rotation"]["x"],
                camera["rotation"]["y"],
                camera["rotation"]["z"],
                camera["rotation"]["w"],
            ]).as_matrix()

            rig_camera_configs.append(
                pycolmapRigConfigCamera(
                    image_prefix=f"{rig['id']}/{camera['id']}/",
                    ref_sensor=camera["ref_sensor"] or False,
                    cam_from_rig=Rigid3d(
                        rotation=Rotation3d(R_cam_from_rig),
                        translation=array(
                            [camera["translation"]["x"], camera["translation"]["y"], camera["translation"]["z"]],
                            dtype=float64,
                        ).reshape(3, 1),
                    ),
                )
            )
        rig_configs.append(pycolmapRigConfig(cameras=rig_camera_configs))

    # Write images, pose priors, and keypoints to database
    image_id_to_pycolmap_id: dict[str, int] = {}
    for image in images.values():
        camera_id = camera_id_to_colmap_camera_id[(image.rig_id, image.camera_id)]
        print(f"  {image.name} with camera ID {camera_id}")
        colmap_image_id = database.write_image(
            pycolmapImage(name=image.name, camera_id=camera_id_to_colmap_camera_id[(image.rig_id, image.camera_id)])
        )
        image_id_to_pycolmap_id[image.name] = colmap_image_id

        keypoints_array = keypoints[image.name].detach().cpu().numpy().astype(float32, copy=False)
        keypoints_array += 0.5  # Convert from (x,y) corner to COLMAP center-of-pixel (x+0.5,y+0.5)
        database.write_keypoints(colmap_image_id, keypoints_array)

        camera_center_in_world = -(image.rotation_camera_from_world.as_matrix().T @ image.translation_camera_from_world)
        database.write_pose_prior(
            colmap_image_id,
            PosePrior(
                position=camera_center_in_world.reshape(3, 1),
                position_covariance=(POSE_PRIOR_POS_SIGMA_M**2) * eye(3, dtype=float64),
            ),
        )

        # cam_from_world = (R, t) already in your Image: image.rotation / image.translation
        # R_cw = image.rotation.as_matrix()  # 3x3
        # t_cw = image.translation.reshape(3, 1)  # 3x1

        # # Prior weights (tweak as you like)
        # POSE_PRIOR_ROT_SIGMA_DEG = 5.0  # 1-sigma on rotation, in degrees
        # POSE_PRIOR_POS_SIGMA_M = 0.25  # 1-sigma on position, in meters

        # cov_rot = (deg2rad(POSE_PRIOR_ROT_SIGMA_DEG) ** 2) * eye(3, dtype=float64)
        # cov_pos = (POSE_PRIOR_POS_SIGMA_M**2) * eye(3, dtype=float64)
        # cov_6x6 = diag([
        #     cov_rot[0, 0],
        #     cov_rot[1, 1],
        #     cov_rot[2, 2],
        #     cov_pos[0, 0],
        #     cov_pos[1, 1],
        #     cov_pos[2, 2],
        # ]).astype(float64)

        # database.write_pose_prior(
        #     colmap_image_id, PosePrior(cam_from_world=Rigid3d(Rotation3d(R_cw), t_cw), cam_cov_from_world=cov_6x6)
        # )

    # Apply rig configuration to database
    # (This must be done after all cameras and images have been added)
    # apply_rig_config(rig_configs, database)

    # Write two-view geometries (matches) to database
    for a, b in pairs:
        database.write_matches(
            image_id_to_pycolmap_id[a], image_id_to_pycolmap_id[b], valid_matches[(a, b)].astype(uint32, copy=False)
        )

    database.close()

    verify_matches(
        str(COLMAP_DB_PATH),
        str(PAIRS_FILE),
        options=TwoViewGeometryOptions(
            ransac=RANSACOptions(max_num_trials=50000, min_inlier_ratio=0.05, max_error=4.0), compute_relative_pose=True
        ),
    )

    print("Running reconstruction")

    options = IncrementalPipelineOptions()
    if manifest.options.use_prior_position is not None:
        options.use_prior_position = manifest.options.use_prior_position
    if manifest.options.ba_refine_sensor_from_rig is not None:
        options.ba_refine_sensor_from_rig = manifest.options.ba_refine_sensor_from_rig
    if manifest.options.ba_refine_focal_length is not None:
        options.ba_refine_focal_length = manifest.options.ba_refine_focal_length
    if manifest.options.ba_refine_principal_point is not None:
        options.ba_refine_principal_point = manifest.options.ba_refine_principal_point
    if manifest.options.ba_refine_extra_params is not None:
        options.ba_refine_extra_params = manifest.options.ba_refine_extra_params

    IMAGES_DIRECTORY.mkdir(parents=True, exist_ok=True)
    reconstructions = incremental_mapping(
        database_path=str(COLMAP_DB_PATH),
        image_path=str(IMAGES_DIRECTORY),
        output_path=str(COLMAP_SFM_DIRECTORY),
        options=options,
    )

    if len(reconstructions) == 0:
        manifest.status = "failed"
        manifest.error = "No model was created"

    # Choose the reconstruction with the most registered images
    best_id = max(range(len(reconstructions)), key=lambda i: reconstructions[i].num_reg_images())
    best = reconstructions[best_id]

    best_out = COLMAP_SFM_DIRECTORY / "best"
    best_out.mkdir(parents=True, exist_ok=True)
    best.write_text(str(best_out))
    best.export_PLY(str(best_out / "points3D.ply"))

    # Compute metrics
    points3d: Point3DMap = best.points3D
    points3d_values: Iterable[Point3D] = cast(Iterable[Point3D], points3d.values())  # type: ignore
    reconstruction_images: ImageMap = best.images
    reconstruction_image_values: Iterable[PycolmapImage] = cast(Iterable[PycolmapImage], reconstruction_images.values())  # type: ignore
    track_lengths = [len(p.track.elements) for p in points3d_values]

    reproject_errors: List[float] = []
    for image in reconstruction_image_values:
        for point2d in image.points2D:
            if point2d.point3D_id == UINT64_MAX or point2d.point3D_id not in points3d:
                continue
            projection: Optional[NDArray[float64]] = image.project_point(points3d[point2d.point3D_id].xyz)
            if projection is None:
                continue
            reproject_errors.append(
                float(
                    norm(asarray(projection, dtype=float64).reshape(2) - asarray(point2d.xy, dtype=float64).reshape(2))
                )
            )

    manifest.metrics.total_images = len(images)
    manifest.metrics.registered_images = best.num_reg_images()
    manifest.metrics.registration_rate = float(best.num_reg_images() / len(images) * 100.0)
    manifest.metrics.num_3d_points = len(points3d)
    manifest.metrics.track_length_50th_percentile = _percentile([float(L) for L in track_lengths], 50.0)
    manifest.metrics.percent_tracks_with_length_greater_than_or_equal_to_3 = float(
        sum(1 for L in track_lengths if L >= 3) / float(len(track_lengths)) * 100.0
    )
    manifest.metrics.reprojection_pixel_error_50th_percentile = _percentile(reproject_errors, 50.0)
    manifest.metrics.reprojection_pixel_error_90th_percentile = _percentile(reproject_errors, 90.0)
    _put_reconstruction_object(key="manifest.json", body=manifest.model_dump_json().encode("utf-8"))

    print("Uploading reconstruction results")

    with File(GLOBAL_DESCRIPTORS_FILE, "w") as gfile:
        for name, gdesc in global_descriptors.items():
            grp = gfile.require_group(name)  # type: ignore
            if "global_descriptor" in grp:
                del grp["global_descriptor"]
            grp.create_dataset("global_descriptor", data=_to_f32(gdesc), compression="gzip", compression_opts=3)  # type: ignore

    with File(FEATURES_FILE, "w") as ffile:
        for name in global_descriptors.keys():  # ensures the same set/order as globals
            grp = ffile.require_group(name)  # type: ignore

            # clean any existing
            if "keypoints" in grp:
                del grp["keypoints"]
            if "descriptors" in grp:
                del grp["descriptors"]
            if "scores" in grp:  # ensure dropped
                del grp["scores"]

            # write FP16 + gzip-9 + shuffle + chunks
            grp.create_dataset(  # type: ignore
                "keypoints",
                data=_to_f16(keypoints[name]),
                compression="gzip",
                compression_opts=9,
                shuffle=True,
                chunks=True,
            )

            grp.create_dataset(  # type: ignore
                "descriptors",
                data=_to_f16(descriptors[name]),
                compression="gzip",
                compression_opts=9,
                shuffle=True,
                chunks=True,
            )

    _put_reconstruction_object(key="global_descriptors.h5", body=GLOBAL_DESCRIPTORS_FILE.read_bytes())
    _put_reconstruction_object(key="features.h5", body=FEATURES_FILE.read_bytes())
    _put_reconstruction_object(key="pairs.txt", body=PAIRS_FILE.read_bytes())

    for file_path in best_out.rglob("*"):
        if file_path.is_file():
            _put_reconstruction_object(key=f"sfm_model/{file_path.relative_to(best_out)}", body=file_path.read_bytes())

    manifest.status = "succeeded"

    _put_reconstruction_object(key="manifest.json", body=manifest.model_dump_json().encode("utf-8"))


def _percentile(xs: Sequence[float], q: float):
    arr = asarray(xs, dtype=float64)
    if arr.size == 0:
        raise ValueError("Cannot compute percentile of empty array")
    return float(percentile(arr, q))


if __name__ == "__main__":
    main()
