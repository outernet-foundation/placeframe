#!/usr/bin/env python3
"""
Reconstruct several fisheye views of one 360 video together, as a camera rig.

Every view was rendered from the same panorama, so the views share an optical
centre exactly and differ only by the rotation each was rendered with. That is a
rig whose extrinsics are known in advance: rotation from each view's camera.json,
translation zero. Solving the views jointly holds them rigid instead of letting
four independent reconstructions drift apart, and a feature stays usable as it
passes from one view into the next.

Two consequences of the shared centre:
  * Images of the SAME instant have no baseline, so they can never triangulate.
    They are excluded from matching (--cross-overlap applies to other instants
    only), which also keeps degenerate pairs out of two-view geometry.
  * Rig translation is not merely unknown-but-small, it is exactly zero, so it is
    never refined. Only the rotations can be refined (--refine-rig), which is
    worth testing: measured against each other, the per-view reconstructions
    agreed with the designed rotations to within about half a degree, so the
    panorama is not a perfect single-viewpoint sphere.

Images are staged as symlinks (images/<view>/pano_<frame>.jpg) because COLMAP
groups a rig's images into frames by the part of the name after the per-camera
prefix -- the shared frame number.

Outputs (under --out):
  images/            symlinks, one folder per view
  database.db        features and matches
  sfm_model/         the reconstruction
  report.json        registration, errors, and the solved rig rotations

Run (sfai env, from placeframe/pano_mapping):
    python fisheye_rig_colmap.py VIEW_DIR... --out OUT [--refine-rig]
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import numpy as np
import pycolmap

from fisheye_colmap import write_camera_mask


def pano_from_cam(camera: dict) -> np.ndarray:
    """Rotation taking a ray in this view's camera frame into panorama axes.

    Mirrors pano_to_fisheye.fisheye_maps: the camera frame is OpenCV (y down),
    the panorama has y up, then the view's yaw and pitch are applied.
    """
    yaw, pitch = np.radians(camera["yaw_deg"]), np.radians(-camera["pitch_deg"])
    rot_yaw = np.array([[np.cos(yaw), 0, np.sin(yaw)], [0, 1, 0], [-np.sin(yaw), 0, np.cos(yaw)]])
    rot_pitch = np.array([[1, 0, 0], [0, np.cos(pitch), -np.sin(pitch)], [0, np.sin(pitch), np.cos(pitch)]])
    return rot_yaw @ rot_pitch @ np.diag([1.0, -1.0, 1.0])


def frame_number(name: str) -> int:
    return int(Path(name).stem.split("_")[-1])


def stage_images(views: dict[str, Path], out: Path) -> Path:
    """One folder of symlinks per view, so COLMAP sees <view>/<shared frame name>."""
    root = out / "images"
    if root.exists():
        shutil.rmtree(root)
    for name, view in views.items():
        folder = root / name
        folder.mkdir(parents=True)
        for image in sorted((view / "images").glob("*.jpg")):
            (folder / image.name).symlink_to(image.resolve())
    return root


def build_pairs(views: list[str], frames: list[int], same_overlap: int, cross_overlap: int) -> list[tuple[str, str]]:
    """Sequential pairs within a view, plus cross-view pairs at *different* instants."""
    pairs = []
    for i, frame in enumerate(frames):
        for vi, view in enumerate(views):
            for j in range(i + 1, min(i + 1 + same_overlap, len(frames))):
                pairs.append((f"{view}/pano_{frame:06d}.jpg", f"{view}/pano_{frames[j]:06d}.jpg"))
            for other in views[vi + 1:]:
                for j in range(i + 1, min(i + 1 + cross_overlap, len(frames))):
                    # both orderings: the views are not interchangeable in time
                    pairs.append((f"{view}/pano_{frame:06d}.jpg", f"{other}/pano_{frames[j]:06d}.jpg"))
                    pairs.append((f"{other}/pano_{frame:06d}.jpg", f"{view}/pano_{frames[j]:06d}.jpg"))
    return pairs


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("views", nargs="+", type=Path, help="view folders (each with images/ and camera.json)")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--ref", default=None, help="view whose camera frame is the rig frame (default: the first)")
    ap.add_argument("--same-overlap", type=int, default=10, help="sequential window within a view")
    ap.add_argument("--cross-overlap", type=int, default=3, help="window between different views")
    ap.add_argument("--mask-margin", type=int, default=12)
    ap.add_argument("--max-features", type=int, default=8192)
    ap.add_argument("--refine-rig", action="store_true", help="let bundle adjustment refine the rig rotations")
    ap.add_argument("--reuse-db", action="store_true",
                    help="keep an existing database (features, rig and matches do not depend on --refine-rig)")
    args = ap.parse_args()

    views = {v.name.replace("tetra", "").replace("crop", "") or v.name: v for v in args.views}
    cameras = {name: json.loads((path / "camera.json").read_text()) for name, path in views.items()}
    ref = args.ref or next(iter(views))
    args.out.mkdir(parents=True, exist_ok=True)

    sizes = {(c["width"], c["height"], tuple(c["params"])) for c in cameras.values()}
    if len(sizes) != 1:
        raise SystemExit("views were rendered with different intrinsics; this script assumes one shared camera model")
    model = next(iter(cameras.values()))

    image_root = stage_images(views, args.out)
    frames = sorted(frame_number(p.name) for p in (image_root / ref).glob("*.jpg"))
    print(f"{len(views)} views x {len(frames)} frames; rig frame = {ref}")

    database_path = args.out / "database.db"
    reuse = args.reuse_db and database_path.exists()
    if database_path.exists() and not reuse:
        database_path.unlink()
    mask_path = args.out / "camera_mask.png"
    write_camera_mask(model, args.mask_margin, mask_path)

    reader = pycolmap.ImageReaderOptions(camera_model=model["model"],
                                         camera_params=",".join(repr(p) for p in model["params"]),
                                         camera_mask_path=str(mask_path))
    extraction = pycolmap.FeatureExtractionOptions()
    extraction.sift.max_num_features = args.max_features
    if not reuse:
        print("extracting SIFT features (one camera per view)...", flush=True)
        pycolmap.extract_features(database_path=database_path, image_path=image_root,
                                  camera_mode=pycolmap.CameraMode.PER_FOLDER,
                                  reader_options=reader, extraction_options=extraction)

    # Rig: the reference view defines the rig frame, so cam_from_rig for view v is
    # P_v^T P_ref, with P the rotation from that view's camera frame to panorama axes.
    p_ref = pano_from_cam(cameras[ref])
    rig_cameras = []
    for name in views:
        cam_from_rig = pano_from_cam(cameras[name]).T @ p_ref
        rig_cameras.append(pycolmap.RigConfigCamera(
            image_prefix=f"{name}/",
            ref_sensor=(name == ref),
            cam_from_rig=pycolmap.Rigid3d(pycolmap.Rotation3d(cam_from_rig), np.zeros(3)),
        ))
    if not reuse:
        database = pycolmap.Database.open(str(database_path))
        pycolmap.apply_rig_config([pycolmap.RigConfig(cameras=rig_cameras)], database)
        database.close()

    pairs = build_pairs(list(views), frames, args.same_overlap, args.cross_overlap)
    pairs_path = args.out / "pairs.txt"
    if reuse:
        print(f"reusing {database_path} ({len(pairs)} pairs already matched)")
    else:
        pairs_path.write_text("".join(f"{a} {b}\n" for a, b in pairs))
        print(f"matching {len(pairs)} pairs "
              f"(within a view: +/-{args.same_overlap} frames; across views: +/-{args.cross_overlap}, "
              f"same instant excluded)...", flush=True)
        pairing = pycolmap.ImportedPairingOptions()
        pairing.match_list_path = str(pairs_path)
        pycolmap.match_image_pairs(database_path=database_path, pairing_options=pairing)

    options = pycolmap.IncrementalPipelineOptions()
    options.ba_refine_focal_length = False
    options.ba_refine_principal_point = False
    options.ba_refine_extra_params = False
    # Translation between the views is exactly zero (one panorama, one centre), so
    # the only rig freedom worth refining is rotation.
    options.ba_refine_sensor_from_rig = args.refine_rig
    sfm_dir = args.out / "sfm_model"
    if sfm_dir.exists():
        shutil.rmtree(sfm_dir)
    sfm_dir.mkdir()
    print(f"incremental mapping (rig rotations {'refined' if args.refine_rig else 'fixed'})...", flush=True)
    reconstructions = pycolmap.incremental_mapping(database_path=database_path, image_path=image_root,
                                                   output_path=sfm_dir, options=options)
    if not reconstructions:
        raise SystemExit("no reconstruction was produced")
    best = max(reconstructions.values(), key=lambda r: r.num_reg_images())

    # Solved rig rotations, against the ones the views were rendered with. The
    # reference sensor has no stored transform (it defines the rig frame).
    camera_of_view = {image.name.split("/")[0]: image.camera_id for image in best.images.values()}
    rig_error_deg = {}
    for rig in best.rigs.values():
        for sensor_id in rig.sensor_ids():
            name = next((v for v, cid in camera_of_view.items() if cid == sensor_id.id), None)
            if name is None:
                continue
            # The reference sensor defines the rig frame and stores no transform.
            solved = (np.eye(3) if rig.is_ref_sensor(sensor_id)
                      else rig.sensor_from_rig(sensor_id).rotation.matrix())
            designed = pano_from_cam(cameras[name]).T @ p_ref
            delta = solved @ designed.T
            rig_error_deg[name] = float(np.degrees(np.arccos(np.clip((np.trace(delta) - 1) / 2, -1, 1))))
    print("rig rotation vs the rendered geometry: " +
          ", ".join(f"{v} {d:.3f} deg" for v, d in sorted(rig_error_deg.items())))

    report = {
        "views": list(views), "ref_view": ref, "frames": len(frames),
        "images": len(views) * len(frames),
        "models": len(reconstructions),
        "registered_images": best.num_reg_images(),
        "registered_frames": best.num_reg_frames(),
        "points3D": best.num_points3D(),
        "mean_reprojection_error_px": best.compute_mean_reprojection_error(),
        "mean_track_length": best.compute_mean_track_length(),
        "refine_rig": args.refine_rig,
        "pairs": len(pairs),
        "rig_rotation_error_deg": rig_error_deg,
    }
    (args.out / "report.json").write_text(json.dumps(report, indent=1))
    print(f"{len(reconstructions)} model(s); best registers {best.num_reg_images()}/{report['images']} images "
          f"({best.num_reg_frames()}/{len(frames)} frames), {best.num_points3D()} points, "
          f"mean reproj {report['mean_reprojection_error_px']:.2f} px, mean track {report['mean_track_length']:.1f}")
    print(f"wrote {args.out}/")


if __name__ == "__main__":
    main()
