"""Export a localization recording and a reconstruction into a self-contained fusion-test run.

This is the only part of fusion-test that touches Placeframe: it unpacks the recording, localizes
every still against the reconstruction (through the API, cached under data/fusion/recordings/ so a
re-export localizes nothing again), and reads the reconstruction's COLMAP model for its points and
the map images that saw them. Everything it writes is plain JSON, JPEG and NumPy:

    runs/<recording>_<reconstruction>/
      camera.json        upright intrinsics of the video and still images
      vio.json           every video frame and still: time, tracking state, camera pose in Unity world
      vps.json           every still's localization: pose, covariance, metrics, inlier 2D-3D pairs;
                         plus the device's own live attempts
      map.npz            points (Unity axes), colours, and the map images with the points each saw
      images/video/<timestamp_ns>.jpg, images/stills/<timestamp_ns>.jpg   upright

Run from the repo root (it needs the workspace and the API's .env):

    uv run python fusion-test/export.py RECONSTRUCTION_ID path/to/recording.tar
"""

from __future__ import annotations

import argparse
import json
import sys
import tarfile
from asyncio import run
from pathlib import Path
from typing import Any
from uuid import UUID

import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation

from scripts import howard_test, offline_fusion

FUSION_TEST_DIR = Path(__file__).resolve().parent
RUNS_DIR = FUSION_TEST_DIR / "runs"
JPEG_QUALITY = 95
# OpenCV (COLMAP) to Unity axes: y flips.
BASIS = np.diag([1.0, -1.0, 1.0])
BASIS4 = np.diag([1.0, -1.0, 1.0, 1.0])
MATCH_INLIER = 2  # localizer detail pair status
# A database keypoint the localizer reports is one of the map image's own keypoints; anything
# further than this from every one of them is a mismatch, not a rounding difference.
KEYPOINT_MATCH_TOLERANCE_PX = 0.05


def pose_dict(matrix: np.ndarray) -> dict[str, list[float]]:
    return {
        "position": [float(v) for v in matrix[:3, 3]],
        "rotation_xyzw": [float(v) for v in Rotation.from_matrix(matrix[:3, :3]).as_quat()],
    }


def transform_dict(t: dict[str, Any]) -> np.ndarray:
    r = t["rotation"]
    return offline_fusion.pose_matrix(
        [t["translation"]["x"], t["translation"]["y"], t["translation"]["z"]], [r["x"], r["y"], r["z"], r["w"]]
    )


# --- the COLMAP model ---------------------------------------------------------------------------


def read_colmap(tar_path: Path) -> dict[str, Any]:
    """Points and images from the reconstruction tar's sfm_model/, in Unity axes."""
    with tarfile.open(tar_path) as tar:
        points_text = tar.extractfile("sfm_model/points3D.txt")
        images_text = tar.extractfile("sfm_model/images.txt")
        assert points_text is not None and images_text is not None
        point_lines = points_text.read().decode().splitlines()
        image_lines = images_text.read().decode().splitlines()

    ids, xyz, rgb, error, track_length = [], [], [], [], []
    for line in point_lines:
        if line.startswith("#") or not line.strip():
            continue
        parts = line.split()
        ids.append(int(parts[0]))
        xyz.append([float(v) for v in parts[1:4]])
        rgb.append([int(v) for v in parts[4:7]])
        error.append(float(parts[7]))
        track_length.append((len(parts) - 8) // 2)
    point_ids = np.array(ids)
    index_of = {pid: i for i, pid in enumerate(ids)}

    images: dict[int, dict[str, Any]] = {}
    rows = [line for line in image_lines if not line.startswith("#")]
    for header, keypoints in zip(rows[0::2], rows[1::2], strict=True):
        parts = header.split()
        image_id = int(parts[0])
        qw, qx, qy, qz = (float(v) for v in parts[1:5])
        camera_from_world = offline_fusion.pose_matrix([float(v) for v in parts[5:8]], [qx, qy, qz, qw])
        values = np.array(keypoints.split(), dtype=np.float64).reshape(-1, 3)
        images[image_id] = {
            "name": parts[9],
            # Unity camera from Unity world: the same change of basis on both sides.
            "camera_from_map": BASIS4 @ camera_from_world @ BASIS4,
            "keypoints": values[:, :2],
            "point_index": np.array([index_of.get(int(p), -1) for p in values[:, 2]]),
        }
    return {
        "point_ids": point_ids,
        "xyz": (np.array(xyz) @ BASIS).astype(np.float64),
        "rgb": np.array(rgb, dtype=np.uint8),
        "error": np.array(error, dtype=np.float32),
        "track_length": np.array(track_length, dtype=np.int32),
        "images": images,
    }


def write_map(path: Path, model: dict[str, Any]) -> None:
    image_ids = sorted(model["images"])
    centres, forwards, offsets, observed = [], [], [0], []
    for image_id in image_ids:
        image = model["images"][image_id]
        map_from_camera = np.linalg.inv(image["camera_from_map"])
        centres.append(map_from_camera[:3, 3])
        forwards.append(map_from_camera[:3, 2])  # Unity camera looks down +z
        seen = image["point_index"][image["point_index"] >= 0]
        observed.append(seen)
        offsets.append(offsets[-1] + len(seen))
    np.savez_compressed(
        path,
        points=model["xyz"].astype(np.float32),
        colors=model["rgb"],
        point_error=model["error"],
        track_length=model["track_length"],
        colmap_point_ids=model["point_ids"],
        image_ids=np.array(image_ids),
        image_names=np.array([model["images"][i]["name"] for i in image_ids]),
        image_centres=np.array(centres, dtype=np.float32),
        image_forwards=np.array(forwards, dtype=np.float32),
        # The points image k saw: image_points[image_point_offsets[k]:image_point_offsets[k + 1]].
        image_point_offsets=np.array(offsets, dtype=np.int64),
        image_points=np.concatenate(observed).astype(np.int32),
    )


# --- VPS ----------------------------------------------------------------------------------------


def inlier_pairs(
    detail: dict[str, Any], model: dict[str, Any], width: int, height: int, trees: dict[int, cKDTree]
) -> tuple[list[list[float]], list[int], int]:
    """The localization's PnP inliers as (still pixel, map point index), with how many inliers could
    not be tied to a map point. Query keypoints are in the localizer's canonical image (upright,
    1024 px shorter side); database keypoints are the map image's own, so they look up its points."""
    canonical = detail["camera"]
    sx, sy = width / canonical["width"], height / canonical["height"]
    uv: list[list[float]] = []
    points: list[int] = []
    unmatched = 0
    for pair in detail.get("pairs", []):
        image = model["images"].get(pair["image_id"])
        status = np.array(pair.get("status", []))
        if image is None or not len(status):
            continue
        inliers = np.flatnonzero(status == MATCH_INLIER)
        if not len(inliers):
            continue
        tree = trees.get(pair["image_id"])
        if tree is None:
            tree = trees[pair["image_id"]] = cKDTree(image["keypoints"])
        database = np.array(pair["database_xy"], dtype=np.float64)[inliers]
        query = np.array(pair["query_xy"], dtype=np.float64)[inliers]
        distance, nearest = tree.query(database)
        point_index = image["point_index"][nearest]
        good = (distance <= KEYPOINT_MATCH_TOLERANCE_PX) & (point_index >= 0)
        unmatched += int((~good).sum())
        uv.extend([[round(float(x) * sx, 2), round(float(y) * sy, 2)] for x, y in query[good]])
        points.extend(int(p) for p in point_index[good])
    return uv, points, unmatched


def fix_entry(
    index: int,
    still: offline_fusion.Frame,
    start_ns: int,
    request: offline_fusion.VpsRequest,
    model: dict[str, Any],
    still_size: tuple[int, int],
    trees: dict[int, cKDTree],
) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "still": index,
        "timestamp_ns": still.timestamp_ns,
        "t": (still.timestamp_ns - start_ns) / 1e9,
        "ok": request.response is not None,
        "error": request.error,
    }
    response = request.response
    if response is None:
        return entry
    metrics = response["metrics"]
    detail = response.get("detail") or {}
    map_transform = transform_dict(response["map_transform"])
    uv, points, unmatched = inlier_pairs(detail, model, *still_size, trees)
    entry.update({
        "camera_from_map": pose_dict(transform_dict(response["camera_from_map_transform"])),
        # The map's ECEF placement in Unity basis; identity for a map that is not georegistered.
        "ecef_from_map": pose_dict(offline_fusion.unity_from_map_basis(map_transform[:3, 3], map_transform[:3, :3])),
        "measurement_covariance": metrics["measurement_covariance"],
        "pnp_covariance": metrics.get("pnp_covariance"),
        "metrics": {k: v for k, v in metrics.items() if k not in ("measurement_covariance", "pnp_covariance")},
        "gate": detail.get("gate"),
        "retrieved": [
            {"image_id": p["image_id"], "name": p["name"], "num_inliers": p["num_inliers"]}
            for p in detail.get("pairs", [])
        ],
        "inliers": {"uv": uv, "point": points, "unmatched": unmatched},
    })
    return entry


def live_entries(directory: Path, start_ns: int) -> list[dict[str, Any]]:
    path = directory / "vps.jsonl"
    if not path.exists():
        return []
    entries = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        attempt = json.loads(line)
        attempt["t"] = (attempt["timestamp_ns"] - start_ns) / 1e9
        entries.append(attempt)
    return entries


# --- images and poses ---------------------------------------------------------------------------


def write_images(frames: list[offline_fusion.Frame], folder: Path, orientation: str) -> tuple[int, int]:
    folder.mkdir(parents=True, exist_ok=True)
    size = (0, 0)
    for frame in frames:
        target = folder / f"{frame.timestamp_ns}.jpg"
        with Image.open(frame.path) as image:
            upright = offline_fusion.upright(image.convert("RGB"), orientation)
            size = upright.size
            if not target.exists():
                upright.save(target, quality=JPEG_QUALITY)
    return size


def intrinsics_dict(camera: dict[str, Any], stored_path: Path) -> dict[str, Any]:
    with Image.open(stored_path) as image:
        width, height = image.size
    fx, fy, cx, cy = offline_fusion.upright_intrinsics(camera, width, height)
    if camera["orientation"] == "LEFT_TOP":
        width, height = height, width
    return {"width": width, "height": height, "fx": fx, "fy": fy, "cx": cx, "cy": cy}


def frame_entries(frames: list[offline_fusion.Frame], start_ns: int, folder: str) -> list[dict[str, Any]]:
    return [
        {
            "index": i,
            "timestamp_ns": frame.timestamp_ns,
            "t": (frame.timestamp_ns - start_ns) / 1e9,
            "image": f"images/{folder}/{frame.timestamp_ns}.jpg",
            "tracking_state": frame.tracking_state,
            "unity_from_camera": pose_dict(frame.unity_from_camera),
        }
        for i, frame in enumerate(frames)
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("reconstruction_id", type=UUID)
    parser.add_argument("tar", type=Path, help="Localization recording tar")
    parser.add_argument("--name", help="Run folder name (default <recording>_<reconstruction>, 8 chars each)")
    args = parser.parse_args()

    tar_path: Path = args.tar.resolve()
    reconstruction_id: UUID = args.reconstruction_id
    name = args.name or f"{tar_path.stem[:8]}_{str(reconstruction_id)[:8]}"
    out = RUNS_DIR / name
    out.mkdir(parents=True, exist_ok=True)

    print("unpacking recording", file=sys.stderr)
    directory = howard_test._unpack_recording(tar_path)  # noqa: SLF001
    recording = offline_fusion.load_recording(directory)
    start_ns = recording.video[0].timestamp_ns
    orientation = recording.camera["orientation"]

    print("reading the reconstruction's model", file=sys.stderr)
    reconstruction_tar = howard_test._cached_tar_path(reconstruction_id)  # noqa: SLF001
    if not reconstruction_tar.exists():

        async def fetch() -> None:
            async with howard_test.authenticated_api_client() as api:
                await howard_test._ensure_cached_tar(api, reconstruction_id)  # noqa: SLF001

        run(fetch())
    model = read_colmap(reconstruction_tar)
    write_map(out / "map.npz", model)

    print(f"localizing {len(recording.stills)} stills (cached ones are reused)", file=sys.stderr)
    vps_params = offline_fusion.VpsParams()
    requests = [offline_fusion.VpsRequest(still, still.timestamp_ns, still.timestamp_ns) for still in recording.stills]
    api_points, _ = run(howard_test._localize_requests(reconstruction_id, recording, requests, vps_params))  # noqa: SLF001
    # The API's points and the model's must be the same points in the same axes.
    distance, _ = cKDTree(model["xyz"]).query(api_points[:: max(1, len(api_points) // 2000)])
    if float(np.median(distance)) > 1e-3:
        sys.exit(f"The model's points do not match the API's (median gap {np.median(distance):.3f} m)")

    print("writing images", file=sys.stderr)
    write_images(recording.video, out / "images" / "video", orientation)
    still_size = write_images(recording.stills, out / "images" / "stills", orientation)

    camera = {
        "orientation_recorded": orientation,
        "note": "Intrinsics of the upright images in images/; Unity camera axes (x right, y up, z forward): "
        "u = cx + fx * x / z, v = cy - fy * y / z",
        "video": intrinsics_dict(recording.camera, recording.video[0].path),
        "stills": intrinsics_dict(recording.camera, recording.stills[0].path),
        "recorded": recording.camera,
    }
    (out / "camera.json").write_text(json.dumps(camera, indent=2))

    video_index = {frame.timestamp_ns: i for i, frame in enumerate(recording.video)}
    stills = frame_entries(recording.stills, start_ns, "stills")
    for entry in stills:
        entry["video_index"] = video_index.get(entry["timestamp_ns"])
    vio = {
        "recording": tar_path.stem,
        "device_model": recording.manifest.get("device_model"),
        "start_ns": start_ns,
        "note": "Poses are the camera's in Unity world (x right, y up, z forward)."
        + (
            " Recorded in the device's own tracking space and fitted into Unity world."
            if recording.pose_space_fit
            else ""
        ),
        "pose_space_fit": recording.pose_space_fit,
        "video": frame_entries(recording.video, start_ns, "video"),
        "stills": stills,
    }
    (out / "vio.json").write_text(json.dumps(vio))

    trees: dict[int, cKDTree] = {}
    fixes = [
        fix_entry(i, still, start_ns, request, model, still_size, trees)
        for i, (still, request) in enumerate(zip(recording.stills, requests, strict=True))
    ]
    vps = {
        "reconstruction_id": str(reconstruction_id),
        "params": {
            "retrieval_top_k": vps_params.retrieval_top_k,
            "ransac_threshold": vps_params.ransac_threshold,
            "use_chunking": vps_params.use_chunking,
        },
        "note": "One localization of every still, offline. inliers.uv is in the upright still's pixels; "
        "inliers.point indexes map.npz points. live is what the device itself got, possibly against "
        "another map (live[].result.id).",
        "fixes": fixes,
        "live": live_entries(directory, start_ns),
    }
    (out / "vps.json").write_text(json.dumps(vps))

    ok = [f for f in fixes if f["ok"]]
    print(
        f"{out}: {len(recording.video)} frames, {len(fixes)} stills ({len(ok)} localized), "
        f"{len(model['xyz'])} map points, {len(vps['live'])} live attempts",
        file=sys.stderr,
    )
    if ok:
        unmatched = sum(f["inliers"]["unmatched"] for f in ok)
        total = sum(len(f["inliers"]["point"]) for f in ok) + unmatched
        print(f"inliers tied to map points: {total - unmatched}/{total}", file=sys.stderr)


if __name__ == "__main__":
    main()
