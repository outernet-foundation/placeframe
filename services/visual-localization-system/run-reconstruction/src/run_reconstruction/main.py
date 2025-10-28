from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path
from tarfile import open as open_tar
from typing import Dict, List, Tuple, TypedDict, cast

import torch
from common.boto_clients import create_s3_client
from cv2 import COLOR_BGR2GRAY, COLOR_BGR2RGB, IMREAD_COLOR, cvtColor, imdecode
from h5py import File
from hloc.extractors.dir import DIR
from hloc.extractors.superpoint import SuperPoint
from lightglue import LightGlue
from numpy import array, eye, float32, float64, frombuffer, hstack, int32, ndarray, nonzero, stack, uint8, uint32
from numpy.typing import NDArray
from pycolmap import (
    Camera,
    Database,
    IncrementalMapperOptions,
    IncrementalPipelineOptions,
    PosePrior,
    RANSACOptions,
    Rigid3d,
    Rotation3d,
    TwoViewGeometry,
    TwoViewGeometryOptions,
)
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
POSE_NEIGHBOR_COUNT = 12
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


class RigCamera(TypedDict):
    id: str
    model: str
    width: int
    height: int
    intrinsics: NDArray[float32]
    ref_sensor: bool | None
    rotation: NDArray[float32]
    translation: NDArray[float32]


class Rig(TypedDict):
    id: str
    cameras: list[RigCamera]


class RigConfig(TypedDict):
    rigs: list[Rig]


class Image:
    def __init__(
        self,
        frame_id: str,
        rig_id: str,
        camera: RigCamera,
        frame_rotation_world_to_camera: Rotation,
        frame_translation_world_to_camera: ndarray,
        png_buffer: bytes,
    ):
        self.name = f"{rig_id}/{camera['id']}/{frame_id}.jpg"
        self.rig_id = rig_id
        self.camera_id = camera["id"]

        rig_R = Rotation.from_quat(camera["rotation"])
        rig_t = array(camera["translation"], dtype=float)
        self.rotation = Rotation.from_quat(camera["rotation"]) * frame_rotation_world_to_camera
        self.translation = rig_R.apply(frame_translation_world_to_camera) + rig_t

        extrinsic_matrix = hstack((self.rotation.as_matrix(), self.translation.reshape(3, 1)))
        intrinsics_matrix = array(
            [
                [camera["intrinsics"][0], 0, camera["intrinsics"][2]],
                [0, camera["intrinsics"][1], camera["intrinsics"][3]],
                [0, 0, 1],
            ],
            dtype=float32,
        )
        self.projection_matrix = intrinsics_matrix @ extrinsic_matrix

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


def main():
    print(f"Starting reconstruction {settings.reconstruction_id}")

    # run_json = json.loads(_get_capture_object("run.json").decode("utf-8"))
    run_json = json.load(
        s3_client.get_object(Bucket=settings.reconstructions_bucket, Key=f"{settings.reconstruction_id}/run.json")[
            "Body"
        ]
    )
    run_json["status"] = "running"
    _put_reconstruction_object(key="run.json", body=json.dumps(run_json).encode("utf-8"))

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
        if not all(ref_sensor["rotation"] == array([0, 0, 0, 1], dtype=float32)):
            raise ValueError(f"Reference sensor {ref_sensor['id']} in rig {rig['id']} must have identity rotation")
        if not all(ref_sensor["translation"] == array([0, 0, 0], dtype=float32)):
            raise ValueError(f"Reference sensor {ref_sensor['id']} in rig {rig['id']} must have zero translation")

    images: Dict[str, Image] = {}
    for rig in rigs:
        for line in _get_capture_object(f"{rig['id']}/frames.csv").decode("utf-8").splitlines()[1:]:  # Skip header
            frame_id, tx, ty, tz, qx, qy, qz, qw = line.strip().split(",")
            frame_rotation_world_to_camera = Rotation.from_quat([float(qx), float(qy), float(qz), float(qw)])
            frame_translation_world_to_camera = array([float(tx), float(ty), float(tz)], dtype=float)

            for camera in rig["cameras"]:
                image = Image(
                    frame_id,
                    rig["id"],
                    camera,
                    frame_rotation_world_to_camera,
                    frame_translation_world_to_camera,
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

    superpoint = SuperPoint({"weights": WEIGHTS}).to(DEVICE).eval()

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

    # for image in images.values():
    #     # Upload to S3
    #     _put_reconstruction_object(
    #         key=f"features/{image.name}.npz",
    #         body=json.dumps({
    #             "keypoints": keypoints[image.name].cpu().numpy().astype(float32).tolist(),
    #             "descriptors": descriptors[image.name].cpu().numpy().astype(float32).tolist(),
    #             "global_descriptor": global_descriptors[image.name].cpu().numpy().astype(float32).tolist(),
    #         }).encode("utf-8"),
    #     )

    print("Matching features")

    # Find pairs of images to match
    pairs_by_pose_proximity = pairs_from_poses(
        [
            ImageTransform(name, rotation, translation)
            for name, (rotation, translation) in {
                img.name: (img.rotation.as_matrix(), img.translation) for img in images.values()
            }.items()
        ],
        min(POSE_NEIGHBOR_COUNT, max(1, len(images) - 1)),
    )

    # Canonicalize and deduplicate pairs
    pairs = {tuple(sorted((a, b))) for a, b in pairs_by_pose_proximity if a != b}

    PAIRS_FILE.parent.mkdir(parents=True, exist_ok=True)
    PAIRS_FILE.write_text("\n".join(f"{a} {b}" for a, b in pairs))

    _put_reconstruction_object(key="pairs.txt", body=PAIRS_FILE.read_bytes())

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
                model=camera["model"],
                width=camera["width"],
                height=camera["height"],
                params=array(camera["intrinsics"], dtype=float64),
            )
            the_camera.has_prior_focal_length = True

            camera_id_to_colmap_camera_id[(rig["id"], camera["id"])] = database.write_camera(the_camera)
            rig_camera_configs.append(
                pycolmapRigConfigCamera(
                    image_prefix=f"{rig['id']}/{camera['id']}/",
                    ref_sensor=camera["ref_sensor"] or False,
                    cam_from_rig=Rigid3d(
                        rotation=Rotation3d(array(camera["rotation"], dtype=float64)),
                        translation=array(camera["translation"], dtype=float64).reshape(3, 1),
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

        C_world = -(image.rotation.as_matrix().T @ image.translation)
        database.write_pose_prior(
            colmap_image_id,
            PosePrior(
                position=C_world.reshape(3, 1), position_covariance=(POSE_PRIOR_POS_SIGMA_M**2) * eye(3, dtype=float64)
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

    # print(f"Total pairs: {len(pairs)}")
    # for a, b in list(pairs)[:5]:
    #     print(f"  Sample pair: {a} <-> {b}")
    #     print(f"    Image IDs: {image_id_to_pycolmap_id[a]} <-> {image_id_to_pycolmap_id[b]}")

    # Apply rig configuration to database
    # (This must be done after all cameras and images have been added)
    # apply_rig_config(rig_configs, database)

    # Write two-view geometries (matches) to database
    for a, b in pairs:
        matches = valid_matches[(a, b)].astype(uint32, copy=False)
        database.write_matches(image_id_to_pycolmap_id[a], image_id_to_pycolmap_id[b], matches)
        # database.write_two_view_geometry(
        #     image_id_to_pycolmap_id[a], image_id_to_pycolmap_id[b], TwoViewGeometry(inlier_matches=matches)
        # )

    database.close()

    # verify_matches(str(COLMAP_DB_PATH), str(PAIRS_FILE), options=dict(ransac=dict(max_num_trials=20000, min_inlier_ratio=0.1)))
    verify_matches(
        str(COLMAP_DB_PATH),
        str(PAIRS_FILE),
        options=TwoViewGeometryOptions(
            ransac=RANSACOptions(max_num_trials=50000, min_inlier_ratio=0.05, max_error=4.0), compute_relative_pose=True
        ),
    )

    db2 = Database(str(COLMAP_DB_PATH))
    cameras = db2.read_all_cameras()
    for cam in cameras:
        print(f"Camera {cam.camera_id}: {cam.model} {cam.width}x{cam.height} {cam.params}")

    two_view_geometries = db2.read_two_view_geometries()
    for geometry in two_view_geometries:
        for thing in geometry:
            if isinstance(thing, TwoViewGeometry):
                print(
                    f"TwoViewGeometry with {len(thing.inlier_matches)} inlier matches and tri_angle {thing.tri_angle} and config {thing.config}"
                )
    db2.close()

    print("Running reconstruction")

    IMAGES_DIRECTORY.mkdir(parents=True, exist_ok=True)
    reconstructions = incremental_mapping(
        database_path=str(COLMAP_DB_PATH),
        image_path=str(IMAGES_DIRECTORY),
        output_path=str(COLMAP_SFM_DIRECTORY),
        options=IncrementalPipelineOptions(
            use_prior_position=True,
            # ba_refine_sensor_from_rig=False,
            mapper=IncrementalMapperOptions(init_min_num_inliers=15, init_min_tri_angle=0.5),
            # concerningly none of the three follwing options are having any effect
            # multiple_models=False,
            # max_num_models=1,
            # min_model_size=MIN_MODEL_SIZE,
        ),
    )

    if len(reconstructions) == 0:
        run_json["status"] = "failed"
        run_json["error"] = "No model was created"

    with File(GLOBAL_DESCRIPTORS_FILE, "w") as gfile:
        for name, gdesc in global_descriptors.items():
            grp = gfile.require_group(name)  # type: ignore
            if "global_descriptor" in grp:
                del grp["global_descriptor"]
            grp.create_dataset("global_descriptor", data=_to_f32(gdesc), compression="gzip", compression_opts=3)  # type: ignore

    with File(FEATURES_FILE, "w") as ffile:
        for name in global_descriptors.keys():  # ensures the same set/order as globals
            grp = ffile.require_group(name)  # type: ignore
            if "keypoints" in grp:
                del grp["keypoints"]
            if "descriptors" in grp:
                del grp["descriptors"]
            grp.create_dataset("keypoints", data=_to_f32(keypoints[name]), compression="gzip", compression_opts=3)  # type: ignore
            grp.create_dataset("descriptors", data=_to_f32(descriptors[name]), compression="gzip", compression_opts=3)  # type: ignore
            # Optional: store SuperPoint scores (not used by your loader, but handy)
            if name in scores:
                if "scores" in grp:
                    del grp["scores"]
                grp.create_dataset("scores", data=_to_f32(scores[name]), compression="gzip", compression_opts=3)  # type: ignore

    _put_reconstruction_object(key="global_descriptors.h5", body=GLOBAL_DESCRIPTORS_FILE.read_bytes())
    _put_reconstruction_object(key="features.h5", body=FEATURES_FILE.read_bytes())

    # Choose the reconstruction with the most registered images
    best_id = max(range(len(reconstructions)), key=lambda i: reconstructions[i].num_reg_images())
    best = reconstructions[best_id]

    best_out = COLMAP_SFM_DIRECTORY / "best"
    best_out.mkdir(parents=True, exist_ok=True)
    best.write_text(str(best_out))
    best.export_PLY(str(best_out / "points3D.ply"))

    # Upload everything from best_out
    for file_path in best_out.rglob("*"):
        if file_path.is_file():
            _put_reconstruction_object(key=f"sfm_model/{file_path.relative_to(best_out)}", body=file_path.read_bytes())

    run_json["status"] = "succeeded"

    _put_reconstruction_object(key="run.json", body=json.dumps(run_json).encode("utf-8"))


if __name__ == "__main__":
    main()
