"""A/B a spherical capture's view projections against a real query image.

Renders one equirectangular frame several ways -- equidistant fisheye as the reconstructor does
today, rectilinear as a phone camera does -- and matches every rendered view against the same
query with the localizer's own ALIKED + LightGlue. The sphere, the query and the models are
identical across arms, so the only variable is how the sphere was projected.

Writes the rendered views, a contact sheet per arm, and side-by-side match drawings, so the
numbers can be checked against what the images actually look like.

    # 1. find a query/sphere pair that genuinely overlaps (this matters -- see below)
    uv run python scripts/experiments/projection_ab.py --list-pairs

    # 2. run the comparison
    uv run python scripts/experiments/projection_ab.py \
        --capture-tar data/captures/<capture_id>.tar \
        --sphere rig0/camera0/23000.jpg \
        --query ~/SemanticField/media/UnionSquare/LocalizationTestVideos/Usq_south/frame_000180.jpg \
        --out data/projection_ab/run1

Pick the pair with --list-pairs rather than by eye. A query and a sphere that do not see the
same place still produce a few dozen matches and a plausible-looking inlier count, because a
fundamental matrix fitted to a handful of points can absorb almost anything -- which makes every
arm score the same and the comparison meaningless.
"""

from __future__ import annotations

import argparse
import io
import json
import tarfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import torch
from PIL import Image

from core.image_preprocess import canonicalize_image
from core.lightglue import Descriptors, Keypoints
from core.model_wrappers import make_local_feature_extractor, make_local_feature_matcher_for_tensors
from neural_networks.models import load_aliked, load_lightglue
from panorama.projection import LAYOUTS, Projection, View, camera_model, focal_length, render, view_map

REPO_ROOT = Path(__file__).resolve().parents[2]
LOCALIZATIONS_DIR = REPO_ROOT / "data" / "localizations"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# The reconstructor canonicalizes to a 1024-pixel short side before extracting features, so this
# is the real pixel budget per view however large the render is. Rendering bigger only buys
# antialiasing.
SIZE = 1024

DEFAULT_ARMS = [
    "fisheye:150:tetrahedron",
    "fisheye:120:hexring",
    "rectilinear:60:ring",
    "rectilinear:75:ring",
    "rectilinear:90:ring",
]


@dataclass(frozen=True)
class Arm:
    projection: Projection
    fov_deg: float
    layout: str
    views: tuple[View, ...]

    @property
    def label(self) -> str:
        return f"{self.projection}-{self.fov_deg:g}-{self.layout}"


def ring(fov_deg: float, overlap: float) -> tuple[View, ...]:
    """Yaw-spaced level views covering 360 degrees with the given fractional overlap."""
    count = int(np.ceil(360.0 / (fov_deg * (1.0 - overlap))))
    return tuple(View(f"r{i:02d}", i * 360.0 / count, 0.0) for i in range(count))


def parse_arm(spec: str, overlap: float) -> Arm:
    try:
        projection, fov, layout = spec.split(":")
        fov_deg = float(fov)
    except ValueError:
        raise SystemExit(f"--arm wants projection:fov:layout, e.g. rectilinear:75:ring, not {spec!r}") from None
    if projection not in ("fisheye", "rectilinear"):
        raise SystemExit(f"unknown projection {projection!r}; use fisheye or rectilinear")
    views = ring(fov_deg, overlap) if layout == "ring" else LAYOUTS.get(layout, ())
    if not views:
        raise SystemExit(f"unknown layout {layout!r}; use ring or one of {', '.join(sorted(LAYOUTS))}")
    return Arm(projection, fov_deg, layout, views)


def list_pairs(limit: int) -> None:
    """Query/sphere pairs that are known to overlap, taken from past localization runs.

    A run recorded with --detail says which database image carried the most inliers for each
    query it localized, which is exactly a pair known to see the same place.
    """
    rows: list[tuple[int, str, str, str]] = []
    for run in sorted(LOCALIZATIONS_DIR.glob("*/results.json")):
        result = json.loads(run.read_text())
        for image in result.get("images", []):
            if image.get("status") != "ok" or not image.get("has_detail"):
                continue
            detail_path = run.parent / "details" / f"{image['index']}.json"
            if not detail_path.exists():
                continue
            pairs = json.loads(detail_path.read_text()).get("pairs", [])
            if not pairs:
                continue
            best = max(pairs, key=lambda p: p["num_inliers"])
            # rig0/camera0_C/23000.jpg -> the sphere it was rendered from
            parts = best["name"].split("/")
            sphere = f"{parts[0]}/{parts[1].rsplit('_', 1)[0]}/{parts[2]}" if len(parts) == 3 else best["name"]
            rows.append((best["num_inliers"], image.get("path") or "", sphere, result["capture_session_id"]))
    rows.sort(reverse=True)
    if not rows:
        raise SystemExit(
            f"No detailed localization runs under {LOCALIZATIONS_DIR}. Run a localization with Detail enabled first."
        )
    print(f"{'inliers':>8}  {'sphere':28}  query")
    for inliers, query, sphere, _capture in rows[:limit]:
        print(f"{inliers:8d}  {sphere:28}  {query}")
    print(f"\ncapture tar for the top row: data/captures/{rows[0][3]}.tar")


def draw_matches(
    view_rgb: np.ndarray,
    query_rgb: np.ndarray,
    view_pts: np.ndarray,
    query_pts: np.ndarray,
    inlier_mask: np.ndarray,
) -> np.ndarray:
    """Side-by-side with a line per match: green kept by the geometry, red rejected."""
    scale = query_rgb.shape[0] / view_rgb.shape[0]
    left = cv2.resize(view_rgb, (int(view_rgb.shape[1] * scale), query_rgb.shape[0]))
    canvas = np.zeros((query_rgb.shape[0], left.shape[1] + query_rgb.shape[1], 3), dtype=np.uint8)
    canvas[:, : left.shape[1]] = left
    canvas[:, left.shape[1] :] = query_rgb
    for (vx, vy), (qx, qy), keep in zip(view_pts, query_pts, inlier_mask):
        colour = (74, 222, 128) if keep else (113, 113, 247)
        a = (int(vx * scale), int(vy * scale))
        b = (int(qx) + left.shape[1], int(qy))
        cv2.line(canvas, a, b, colour, 1, cv2.LINE_AA)
        cv2.circle(canvas, a, 2, colour, -1)
        cv2.circle(canvas, b, 2, colour, -1)
    return canvas


def contact_sheet(images: list[tuple[str, np.ndarray]], columns: int = 4) -> np.ndarray:
    thumb = 320
    rows = int(np.ceil(len(images) / columns))
    sheet = np.zeros((rows * thumb, columns * thumb, 3), dtype=np.uint8)
    for i, (name, image) in enumerate(images):
        small = cv2.resize(image, (thumb, thumb))
        cv2.putText(small, name, (6, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)
        r, c = divmod(i, columns)
        sheet[r * thumb : (r + 1) * thumb, c * thumb : (c + 1) * thumb] = small
    return sheet


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--list-pairs", action="store_true", help="print query/sphere pairs known to overlap")
    parser.add_argument("--limit", type=int, default=15, help="how many pairs to list")
    parser.add_argument("--capture-tar", type=Path, help="the capture holding the equirectangular frames")
    parser.add_argument("--sphere", help="member inside the tar, e.g. rig0/camera0/23000.jpg")
    parser.add_argument("--query", type=Path, help="the query image to match against")
    parser.add_argument("--out", type=Path, default=Path("data/projection_ab/run"), help="output directory")
    parser.add_argument("--arm", action="append", default=None, help=f"projection:fov:layout (default: {DEFAULT_ARMS})")
    parser.add_argument("--overlap", type=float, default=0.25, help="fractional overlap for ring layouts")
    parser.add_argument("--size", type=int, default=SIZE, help="rendered view edge in pixels")
    parser.add_argument("--draw-top", type=int, default=2, help="how many views per arm to draw matches for")
    args = parser.parse_args()

    if args.list_pairs:
        list_pairs(args.limit)
        return
    for required in ("capture_tar", "sphere", "query"):
        if getattr(args, required) is None:
            raise SystemExit("--capture-tar, --sphere and --query are all required (or use --list-pairs)")

    arms = [parse_arm(s, args.overlap) for s in (args.arm or DEFAULT_ARMS)]
    out: Path = args.out
    out.mkdir(parents=True, exist_ok=True)

    with tarfile.open(args.capture_tar) as tar:
        member = tar.extractfile(args.sphere)
        if member is None:
            raise SystemExit(f"{args.sphere} is not a file in {args.capture_tar}")
        with Image.open(io.BytesIO(member.read())) as opened:
            sphere = np.asarray(opened.convert("RGB"), dtype=np.uint8)
    pano_h, pano_w = sphere.shape[:2]

    query_image = canonicalize_image(args.query.read_bytes(), "TOP_LEFT")
    query_rgb = np.asarray(query_image, dtype=np.uint8)
    cv2.imwrite(str(out / "query.jpg"), cv2.cvtColor(query_rgb, cv2.COLOR_RGB2BGR))

    diagonal_fov = 2 * np.degrees(np.arctan(np.hypot(query_image.width, query_image.height) / 2 / 1369.4))
    print(f"sphere {args.sphere}  {pano_w}x{pano_h}")
    print(f"query  {args.query.name}  {query_image.width}x{query_image.height}  (diagonal FoV ~{diagonal_fov:.0f} deg)")
    print(f"out    {out}\n")

    extractor = make_local_feature_extractor(load_aliked(device=DEVICE))
    matcher = make_local_feature_matcher_for_tensors(load_lightglue(DEVICE), DEVICE)

    def features(rgb: np.ndarray):
        tensor = torch.from_numpy(np.asarray(rgb, dtype=np.float32)).permute(2, 0, 1).div(255.0)
        return extractor(tensor.unsqueeze(0).to(DEVICE))

    query_kp, query_desc = features(query_rgb)
    summary: list[dict[str, Any]] = []

    for arm in arms:
        arm_dir = out / arm.label
        (arm_dir / "views").mkdir(parents=True, exist_ok=True)
        per_view: list[dict[str, Any]] = []
        drawables: list[tuple[int, str, np.ndarray, Any]] = []
        rendered_all: list[tuple[str, np.ndarray]] = []

        for view in arm.views:
            tables = view_map(pano_w, pano_h, view, args.size, arm.fov_deg, arm.projection)
            rendered = render(sphere, tables)
            cv2.imwrite(str(arm_dir / "views" / f"{view.name}.jpg"), cv2.cvtColor(rendered, cv2.COLOR_RGB2BGR))
            rendered_all.append((view.name, rendered))

            kp, desc = features(rendered)
            keypoints = Keypoints({"db": kp.to(DEVICE), "query": query_kp.to(DEVICE)})
            descriptors = Descriptors({"db": desc.to(DEVICE), "query": query_desc.to(DEVICE)})
            sizes = {"db": (args.size, args.size), "query": (query_image.height, query_image.width)}
            db_i, q_i = matcher([("db", "query")], keypoints, descriptors, sizes, 1)[("db", "query")]

            matches = int(db_i.shape[0])
            inliers, mask = 0, None
            view_pts = kp.cpu().numpy()[np.asarray(db_i, dtype=np.int64)] if matches else np.empty((0, 2))
            qry_pts = query_kp.cpu().numpy()[np.asarray(q_i, dtype=np.int64)] if matches else np.empty((0, 2))
            if matches >= 8:
                _, mask = cv2.findFundamentalMat(view_pts, qry_pts, cv2.USAC_MAGSAC, 3.0, 0.999, 10000)
                if mask is not None:
                    inliers = int(mask.sum())
            per_view.append({"view": view.name, "keypoints": int(kp.shape[0]), "matches": matches, "inliers": inliers})
            drawables.append((
                inliers,
                view.name,
                rendered,
                (view_pts, qry_pts, mask.ravel().astype(bool) if mask is not None else np.zeros(matches, dtype=bool)),
            ))

        cv2.imwrite(str(arm_dir / "contact_sheet.jpg"), cv2.cvtColor(contact_sheet(rendered_all), cv2.COLOR_RGB2BGR))
        for inliers, name, rendered, (vp, qp, keep) in sorted(drawables, reverse=True, key=lambda d: d[0])[
            : args.draw_top
        ]:
            drawing = draw_matches(rendered, query_rgb, vp, qp, keep)
            cv2.imwrite(str(arm_dir / f"matches_{name}_{inliers}inl.jpg"), cv2.cvtColor(drawing, cv2.COLOR_RGB2BGR))

        best = max(per_view, key=lambda v: v["inliers"])
        focal = focal_length(args.size, arm.fov_deg, arm.projection)
        summary.append({
            "arm": arm.label,
            "projection": arm.projection,
            "fov_deg": arm.fov_deg,
            "layout": arm.layout,
            "views": len(arm.views),
            "camera_model": camera_model(arm.projection),
            "px_per_deg_centre": round(float(focal * np.pi / 180), 2),
            "best_view": best,
            "total_matches": sum(v["matches"] for v in per_view),
            "total_inliers": sum(v["inliers"] for v in per_view),
            "per_view": per_view,
        })
        print(
            f"{arm.label:28s} {len(arm.views):2d} views  "
            f"{summary[-1]['px_per_deg_centre']:5.1f} px/deg  "
            f"best {best['view']}: {best['matches']:5d} matches / {best['inliers']:5d} inliers   "
            f"total inliers {summary[-1]['total_inliers']:6d}"
        )

    (out / "summary.json").write_text(
        json.dumps({"sphere": args.sphere, "query": str(args.query), "size": args.size, "arms": summary}, indent=1)
    )
    print(f"\nwrote {out}/summary.json")
    print(f"  per-arm rendered views:   {out}/<arm>/views/*.jpg")
    print(f"  all views at a glance:    {out}/<arm>/contact_sheet.jpg")
    print(f"  match drawings (top {args.draw_top}):   {out}/<arm>/matches_*.jpg   green = kept, red = rejected")


if __name__ == "__main__":
    main()
