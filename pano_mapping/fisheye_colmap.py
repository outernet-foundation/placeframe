#!/usr/bin/env python3
"""
Reconstruct one fisheye view folder (SIFT -> sequential matching -> COLMAP).

The view's intrinsics are known exactly -- pano_to_fisheye.py renders an
equidistant fisheye, so camera.json holds the matching OPENCV_FISHEYE
parameters -- which is why every intrinsic refinement flag is off here. The
camera is a single shared camera for the whole folder.

Two things specific to a rendered fisheye:
  * Everything outside the image circle is black, and that hard edge sits at the
    same pixels in every frame, so features on it would match frame to frame
    like a pattern glued to the lens. A circular camera mask (shrunk by
    --mask-margin) keeps the detector off it.
  * Frames come from a video, so pairs are sequential rather than exhaustive.

Outputs (under --out, default <view>/colmap):
  camera_mask.png   the circular mask handed to the feature extractor
  database.db       features and matches
  sfm_model/        the reconstruction (largest model, COLMAP binary)
  report.json       registered images, points, reprojection error

Run (sfai env, from placeframe/pano_mapping):
    python fisheye_colmap.py <view folder, e.g. .../cropA>
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import cv2
import numpy as np
import pycolmap


def write_camera_mask(camera: dict, margin: int, path: Path) -> None:
    """White where features are allowed: the image circle, shrunk by `margin`."""
    width, height = camera["width"], camera["height"]
    _, _, cx, cy = camera["params"][:4]
    mask = np.zeros((height, width), np.uint8)
    cv2.circle(mask, (int(round(cx)), int(round(cy))), int(min(width, height) / 2 - margin), 255, -1)
    path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(path), mask)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("view", type=Path, help="a crop<X> folder holding images/ and camera.json")
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--mask-margin", type=int, default=12, help="pixels to shrink the image circle by")
    ap.add_argument("--overlap", type=int, default=10, help="sequential matching window (frames)")
    ap.add_argument("--max-features", type=int, default=8192)
    ap.add_argument("--refine-intrinsics", action="store_true",
                    help="let bundle adjustment move the (exactly known) fisheye parameters")
    args = ap.parse_args()

    camera = json.loads((args.view / "camera.json").read_text())
    images = args.view / "images"
    out = args.out or args.view / "colmap"
    out.mkdir(parents=True, exist_ok=True)
    database = out / "database.db"
    if database.exists():
        database.unlink()
    mask_path = out / "camera_mask.png"
    write_camera_mask(camera, args.mask_margin, mask_path)

    count = len(list(images.glob("*.jpg")))
    params = ",".join(repr(p) for p in camera["params"])
    print(f"{count} images from {images}")
    print(f"camera: {camera['model']} {camera['width']}x{camera['height']} "
          f"fov {camera['fov_deg']}deg yaw {camera['yaw_deg']}deg, f={camera['params'][0]:.2f}px")

    reader = pycolmap.ImageReaderOptions(camera_model=camera["model"], camera_params=params,
                                         camera_mask_path=str(mask_path))
    extraction = pycolmap.FeatureExtractionOptions()
    extraction.sift.max_num_features = args.max_features
    print("extracting SIFT features...", flush=True)
    pycolmap.extract_features(database_path=database, image_path=images, camera_mode=pycolmap.CameraMode.SINGLE,
                              reader_options=reader, extraction_options=extraction)

    print(f"matching sequentially (overlap {args.overlap})...", flush=True)
    pairing = pycolmap.SequentialPairingOptions()
    pairing.overlap = args.overlap
    pairing.quadratic_overlap = True
    pycolmap.match_sequential(database_path=database, pairing_options=pairing)

    options = pycolmap.IncrementalPipelineOptions()
    if not args.refine_intrinsics:
        options.ba_refine_focal_length = False
        options.ba_refine_principal_point = False
        options.ba_refine_extra_params = False
    sfm_dir = out / "sfm_model"
    if sfm_dir.exists():
        shutil.rmtree(sfm_dir)
    sfm_dir.mkdir()
    print("incremental mapping...", flush=True)
    reconstructions = pycolmap.incremental_mapping(database_path=database, image_path=images,
                                                   output_path=sfm_dir, options=options)
    if not reconstructions:
        (out / "report.json").write_text(json.dumps({"images": count, "registered_images": 0}, indent=1))
        raise SystemExit("no reconstruction was produced")

    best = max(reconstructions.values(), key=lambda r: r.num_reg_images())
    report = {
        "view": str(args.view), "images": count,
        "models": len(reconstructions),
        "registered_images": best.num_reg_images(),
        "points3D": best.num_points3D(),
        "mean_reprojection_error_px": best.compute_mean_reprojection_error(),
        "mean_track_length": best.compute_mean_track_length(),
        "mean_observations_per_image": best.compute_mean_observations_per_reg_image(),
        "camera": {"model": camera["model"], "params": camera["params"], "refined": args.refine_intrinsics},
    }
    (out / "report.json").write_text(json.dumps(report, indent=1))
    print(f"{len(reconstructions)} model(s); best registers {best.num_reg_images()}/{count} images, "
          f"{best.num_points3D()} points, mean reproj {report['mean_reprojection_error_px']:.2f} px, "
          f"mean track {report['mean_track_length']:.1f}")
    print(f"wrote {out}/")


if __name__ == "__main__":
    main()
