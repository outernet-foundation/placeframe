#!/usr/bin/env python3
"""
Cut a 360 video into overlapping fisheye views that COLMAP can actually model.

COLMAP's fisheye models normalise by z before taking the ray angle, so they only
represent rays under 90 degrees off axis -- a hair under 180 degrees of field of
view, and numerically poor near that limit (verified with pycolmap: a ray 95
degrees off axis projects to NaN). A 360 panorama therefore has to be cut into
views narrower than that. Three 150-degree views at 120-degree spacing cover the
full circle with 30 degrees of overlap at each seam.

Each view is rendered directly from the equirectangular frame as an EQUIDISTANT
fisheye (r = f * theta), so its intrinsics are exact by construction rather than
estimated: with the image circle spanning the requested field of view,

    f = (size / 2) / (fov / 2)   [pixels per radian]

which is written to each view's camera.json as COLMAP's OPENCV_FISHEYE model
with zero distortion. Nothing needs calibrating.

Four views aimed at the vertices of a tetrahedron (--tetra) do better than three
around the equator: every pair of axes is 109.5 degrees apart, the worst-covered
direction on the sphere is 70.5 degrees from its nearest axis, and 150-degree
views therefore cover the whole sphere with 4.5 degrees to spare. Three
equatorial views at the same field of view cover 94% and miss the zenith and
nadir entirely.

Frames keep their source frame number (pano_<NNNNNN>.jpg) in every view, so the
same number names the same instant in all three -- what a later rig solve needs.

Run (sfai env, from placeframe/pano_mapping):
    python pano_to_fisheye.py VIDEO OUT_DIR [--views A=0 B=120 C=240] [--fov 150]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np


def fisheye_maps(pano_width: int, pano_height: int, size: int, fov_deg: float, yaw_deg: float,
                 pitch_deg: float = 0.0):
    """Remap tables from an equirectangular frame to one equidistant fisheye view.

    Camera frame is OpenCV's (x right, y down, z forward); the panorama has y up
    with its centre column at yaw 0. Pixels outside the image circle are masked.
    """
    focal = (size / 2) / np.radians(fov_deg / 2)
    centre = (size - 1) / 2

    px, py = np.meshgrid(np.arange(size, dtype=np.float32), np.arange(size, dtype=np.float32))
    dx, dy = px - centre, py - centre
    radius = np.hypot(dx, dy)
    theta = radius / focal                      # equidistant: angle from the view axis
    phi = np.arctan2(dy, dx)

    # Ray in camera coordinates, then into panorama coordinates (y flips: down -> up).
    cam = np.stack([np.sin(theta) * np.cos(phi), np.sin(theta) * np.sin(phi), np.cos(theta)], axis=-1)
    rays = cam * np.array([1.0, -1.0, 1.0], dtype=np.float32)

    # Positive pitch tilts the view up: about +x in a y-up frame that is a negative angle.
    yaw, pitch = np.radians(yaw_deg), np.radians(-pitch_deg)
    rot_pitch = np.array([[1, 0, 0], [0, np.cos(pitch), -np.sin(pitch)], [0, np.sin(pitch), np.cos(pitch)]])
    rot_yaw = np.array([[np.cos(yaw), 0, np.sin(yaw)], [0, 1, 0], [-np.sin(yaw), 0, np.cos(yaw)]])
    rays = rays @ (rot_yaw @ rot_pitch).T

    lon = np.arctan2(rays[..., 0], rays[..., 2])
    lat = np.arcsin(np.clip(rays[..., 1], -1.0, 1.0))
    map_x = ((lon / (2 * np.pi) + 0.5) * pano_width).astype(np.float32) % pano_width
    map_y = ((0.5 - lat / np.pi) * pano_height).astype(np.float32)

    inside = radius <= size / 2
    return map_x, map_y, inside, float(focal), float(centre)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("video", type=Path)
    ap.add_argument("out_dir", type=Path, help="parent of the per-view folders")
    ap.add_argument("--views", nargs="+", default=["A=0", "B=120", "C=240"],
                    help="NAME=YAW[,PITCH] in degrees per view; folder is <prefix><NAME>")
    ap.add_argument("--tetra", action="store_true",
                    help="shorthand for four views at the vertices of a tetrahedron (full sphere at fov>=141)")
    ap.add_argument("--prefix", default="crop", help="folder name prefix (default crop)")
    ap.add_argument("--fov", type=float, default=150.0, help="field of view per view (degrees)")
    ap.add_argument("--pitch", type=float, default=0.0, help="extra tilt applied to every view")
    ap.add_argument("--size", type=int, default=1600, help="output width = height (pixels)")
    ap.add_argument("--stride", type=int, default=5, help="keep every Nth source frame")
    ap.add_argument("--only", nargs="*", default=None, help="render only these view names")
    args = ap.parse_args()

    # "Edge-up" tetrahedron: two views tilted up, two down, so neither the zenith
    # nor the nadir (where the operator holding the camera is) sits in a view centre.
    tetra_tilt = 35.264
    if args.tetra:
        args.views = [f"A=45,{tetra_tilt}", f"B=135,{-tetra_tilt}", f"C=225,{tetra_tilt}", f"D=315,{-tetra_tilt}"]
    views: dict[str, tuple[float, float]] = {}
    for spec in args.views:
        name, _, angles = spec.partition("=")
        yaw, _, pitch = angles.partition(",")
        views[name] = (float(yaw), float(pitch or 0.0) + args.pitch)
    wanted = [v for v in views if args.only is None or v in args.only]

    capture = cv2.VideoCapture(str(args.video))
    if not capture.isOpened():
        raise SystemExit(f"could not open {args.video}")
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = capture.get(cv2.CAP_PROP_FPS)
    total = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    if width != 2 * height:
        print(f"warning: {width}x{height} is not 2:1, so it may not be equirectangular")
    print(f"{args.video.name}: {width}x{height}, {fps:.2f} fps, {total} frames; "
          f"keeping every {args.stride} ({total // args.stride} per view)")

    maps = {}
    for name in wanted:
        yaw, pitch = views[name]
        map_x, map_y, inside, focal, centre = fisheye_maps(width, height, args.size, args.fov, yaw, pitch)
        folder = args.out_dir / f"{args.prefix}{name}"
        (folder / "images").mkdir(parents=True, exist_ok=True)
        maps[name] = (map_x, map_y, inside, folder)
        # COLMAP's OPENCV_FISHEYE is equidistant plus a quartic polynomial; zero
        # coefficients leave exactly the projection rendered here.
        (folder / "camera.json").write_text(json.dumps({
            "model": "OPENCV_FISHEYE",
            "width": args.size, "height": args.size,
            "params": [focal, focal, centre, centre, 0.0, 0.0, 0.0, 0.0],
            "param_names": ["fx", "fy", "cx", "cy", "k1", "k2", "k3", "k4"],
            "fov_deg": args.fov, "yaw_deg": yaw, "pitch_deg": pitch,
            "source_video": str(args.video.resolve()), "source_size": [width, height],
            "frame_stride": args.stride, "source_fps": fps,
        }, indent=1))
        print(f"  {folder.name}: yaw {yaw:g} deg, pitch {pitch:g} deg, fov {args.fov:g} deg, f = {focal:.2f} px")

    written = 0
    for index in range(total):
        ok, frame = capture.read()
        if not ok:
            break
        if index % args.stride:
            continue
        for name, (map_x, map_y, inside, folder) in maps.items():
            view = cv2.remap(frame, map_x, map_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
            view[~inside] = 0
            cv2.imwrite(str(folder / "images" / f"pano_{index:06d}.jpg"), view,
                        [cv2.IMWRITE_JPEG_QUALITY, 95])
        written += 1
        if written % 10 == 0:
            print(f"  {written} frames", flush=True)
    capture.release()
    print(f"wrote {written} frames per view to {', '.join(f'{args.prefix}{n}' for n in wanted)}")


if __name__ == "__main__":
    main()
