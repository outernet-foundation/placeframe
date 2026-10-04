"""A/B a spherical capture's view projections against the global-descriptor retrieval step.

The sibling projection_ab.py asks whether a rendered view matches a query's *local* features
better. This asks the earlier question: does retrieval even put the right view in the shortlist?

That step compares one DIR descriptor per whole image, so unlike local matching it is not enough
for the view and the query to overlap -- what the rest of the frame contains counts too. A
150-degree fisheye view holds roughly thirteen times the solid angle of a phone query and spends
a fifth of its pixels on black border, so its descriptor summarizes mostly things the query
cannot see.

Database: every view of a set of spheres, rendered per arm. Queries: frames whose true sphere is
known, taken from past --detail localization runs. Metric: where the true sphere's best view
lands in the cosine ranking.

    uv run python scripts/experiments/retrieval_ab.py --capture-tar data/captures/<id>.tar \
        --max-spheres 120 --out data/retrieval_ab/run1
"""

from __future__ import annotations

import argparse
import io
import json
import tarfile
from pathlib import Path
from typing import Any

import numpy as np
import torch
from PIL import Image

from core.image_preprocess import canonicalize_image
from core.model_wrappers import make_global_descriptor_extractor
from neural_networks.models import load_DIR
from panorama.projection import LAYOUTS, View, render, view_map

REPO_ROOT = Path(__file__).resolve().parents[2]
LOCALIZATIONS_DIR = REPO_ROOT / "data" / "localizations"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
SIZE = 1024

DEFAULT_ARMS = ["fisheye:150:tetrahedron", "fisheye:120:hexring", "rectilinear:75:ring"]


def ring(fov_deg: float, overlap: float = 0.25) -> tuple[View, ...]:
    count = int(np.ceil(360.0 / (fov_deg * (1.0 - overlap))))
    return tuple(View(f"r{i:02d}", i * 360.0 / count, 0.0) for i in range(count))


def parse_arm(spec: str) -> tuple[str, float, tuple[View, ...]]:
    projection, fov, layout = spec.split(":")
    fov_deg = float(fov)
    if projection == "equirect":
        # No views: the sphere is its own image. fov_deg is the vertical band kept, so 180 is
        # the whole panorama and 90 keeps the middle half, dropping zenith and nadir where
        # equirectangular stretching is worst and where a level query looks least.
        return projection, fov_deg, ()
    views = ring(fov_deg) if layout == "ring" else LAYOUTS[layout]
    return projection, fov_deg, views


def equirect_image(sphere: np.ndarray, band_deg: float) -> np.ndarray:
    """The panorama itself, cropped to a horizontal band and scaled to a 1024 short side."""
    height = sphere.shape[0]
    keep = round(height * min(band_deg, 180.0) / 180.0)
    top = (height - keep) // 2
    cropped = sphere[top : top + keep]
    # Short side to 1024 as canonicalize_image would, but never wider than 2048 -- otherwise a
    # narrow band blows up to 6000 pixels across and gets several times the pixel budget of
    # every rendered-view arm, which would flatter it for the wrong reason.
    scale = min(SIZE / cropped.shape[0], 2 * SIZE / cropped.shape[1])
    return np.asarray(
        Image.fromarray(cropped).resize(
            (max(1, round(cropped.shape[1] * scale)), max(1, round(cropped.shape[0] * scale))),
            Image.Resampling.LANCZOS,
        ),
        dtype=np.uint8,
    )


def ground_truth(capture_id: str) -> list[tuple[str, str]]:
    """(query path, true sphere member) for queries this capture already localized.

    The sphere that carried the most inliers is the one the query really sees, so it is the
    right answer for retrieval to find.
    """
    out: dict[str, str] = {}
    for run in sorted(LOCALIZATIONS_DIR.glob("*/results.json")):
        result = json.loads(run.read_text())
        if result.get("capture_session_id") != capture_id:
            continue
        for image in result.get("images", []):
            if image.get("status") != "ok" or not image.get("has_detail"):
                continue
            detail = run.parent / "details" / f"{image['index']}.json"
            if not detail.exists():
                continue
            pairs = json.loads(detail.read_text()).get("pairs", [])
            if not pairs:
                continue
            best = max(pairs, key=lambda p: p["num_inliers"])
            if best["num_inliers"] < 30:
                continue
            parts = best["name"].split("/")
            if len(parts) != 3:
                continue
            out[image["path"]] = f"{parts[0]}/{parts[1].rsplit('_', 1)[0]}/{parts[2]}"
    return sorted(out.items())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--capture-tar", type=Path, required=True)
    parser.add_argument("--capture-id", default=None, help="defaults to the tar's stem")
    parser.add_argument("--max-spheres", type=int, default=120, help="database size (true spheres always included)")
    parser.add_argument("--arm", action="append", default=None)
    parser.add_argument("--out", type=Path, default=Path("data/retrieval_ab/run"))
    args = parser.parse_args()

    capture_id = args.capture_id or args.capture_tar.stem
    arms = [parse_arm(s) for s in (args.arm or DEFAULT_ARMS)]
    args.out.mkdir(parents=True, exist_ok=True)

    truth = ground_truth(capture_id)
    if not truth:
        raise SystemExit(f"no detailed localization runs for capture {capture_id}")
    true_spheres = {sphere for _, sphere in truth}
    print(f"queries with a known true sphere: {len(truth)}  (over {len(true_spheres)} distinct spheres)")

    with tarfile.open(args.capture_tar) as tar:
        members = sorted(m.name for m in tar.getmembers() if m.isfile() and m.name.startswith("rig0/camera0/"))
        distractors = [m for m in members if m not in true_spheres]
        stride = max(1, len(distractors) // max(1, args.max_spheres - len(true_spheres)))
        database_spheres = sorted(true_spheres | set(distractors[::stride]))
        print(f"database spheres: {len(database_spheres)} of {len(members)} in the capture\n")

        spheres: dict[str, np.ndarray] = {}
        for name in database_spheres:
            extracted = tar.extractfile(name)
            assert extracted is not None
            with Image.open(io.BytesIO(extracted.read())) as opened:
                spheres[name] = np.asarray(opened.convert("RGB"), dtype=np.uint8)

    extractor = make_global_descriptor_extractor(load_DIR(DEVICE))

    def descriptor(rgb: np.ndarray) -> np.ndarray:
        tensor = torch.from_numpy(np.asarray(rgb, dtype=np.float32)).permute(2, 0, 1).div(255.0)
        with torch.inference_mode():
            return extractor(tensor.unsqueeze(0).to(DEVICE)).cpu().numpy()

    print("query descriptors...")
    query_desc = {
        path: descriptor(np.asarray(canonicalize_image(Path(path).read_bytes(), "TOP_LEFT"), dtype=np.uint8))
        for path, _ in truth
    }

    summary: list[dict[str, Any]] = []
    pano_h, pano_w = next(iter(spheres.values())).shape[:2]

    for projection, fov_deg, views in arms:
        label = (
            f"equirect-{fov_deg:g}band-1view"
            if projection == "equirect"
            else f"{projection}-{fov_deg:g}-{len(views)}views"
        )
        tables = (
            {}
            if projection == "equirect"
            else {v.name: view_map(pano_w, pano_h, v, SIZE, fov_deg, projection) for v in views}
        )  # type: ignore[arg-type]
        names: list[tuple[str, str]] = []
        vectors: list[np.ndarray] = []
        for sphere_name, sphere in spheres.items():
            if projection == "equirect":
                vectors.append(descriptor(equirect_image(sphere, fov_deg)))
                names.append((sphere_name, "pano"))
                continue
            for v in views:
                vectors.append(descriptor(render(sphere, tables[v.name])))
                names.append((sphere_name, v.name))
        database = np.stack(vectors)
        database /= np.linalg.norm(database, axis=1, keepdims=True)

        sphere_order = sorted({n for n, _ in names})
        sphere_index = {n: i for i, n in enumerate(sphere_order)}
        owner = np.array([sphere_index[n] for n, _ in names])

        ranks: list[int] = []
        sphere_ranks: list[int] = []
        margins: list[float] = []
        for path, true_sphere in truth:
            q = query_desc[path]
            sims = database @ (q / np.linalg.norm(q))
            order = np.argsort(-sims)
            is_true = np.array([names[i][0] == true_sphere for i in order])
            rank = int(np.argmax(is_true)) + 1 if is_true.any() else len(order)
            ranks.append(rank)

            # Rank the PLACE, not the image: score each sphere by its best view, so an arm with
            # more views per sphere is not penalised for filling the shortlist with its own
            # alternatives. This is the comparison that is independent of database size.
            per_sphere = np.full(len(sphere_order), -np.inf)
            np.maximum.at(per_sphere, owner, sims)
            s_order = np.argsort(-per_sphere)
            sphere_ranks.append(int(np.argmax(s_order == sphere_index[true_sphere])) + 1)
            best_true = float(sims[[i for i in range(len(names)) if names[i][0] == true_sphere]].max())
            best_other = float(sims[[i for i in range(len(names)) if names[i][0] != true_sphere]].max())
            margins.append(best_true - best_other)

        ranks_a, sranks_a = np.array(ranks), np.array(sphere_ranks)
        row = {
            "arm": label,
            "projection": projection,
            "fov_deg": fov_deg,
            "views_per_sphere": len(views),
            "database_images": len(names),
            "recall@1": float((ranks_a <= 1).mean()),
            "recall@5": float((ranks_a <= 5).mean()),
            "recall@10": float((ranks_a <= 10).mean()),
            "recall@20": float((ranks_a <= 20).mean()),
            "median_rank": float(np.median(ranks_a)),
            "sphere_recall@1": float((sranks_a <= 1).mean()),
            "sphere_recall@3": float((sranks_a <= 3).mean()),
            "sphere_recall@5": float((sranks_a <= 5).mean()),
            "sphere_recall@10": float((sranks_a <= 10).mean()),
            "median_sphere_rank": float(np.median(sranks_a)),
            "sphere_ranks": sphere_ranks,
            "mean_margin": float(np.mean(margins)),
            "ranks": ranks,
        }
        summary.append(row)
        print(
            f"{label:28s} db={len(names):5d}  R@1={row['recall@1']:.2f} R@5={row['recall@5']:.2f} "
            f"R@10={row['recall@10']:.2f} R@20={row['recall@20']:.2f}  "
            f"median rank={row['median_rank']:.0f}  margin={row['mean_margin']:+.4f}"
        )

    (args.out / "summary.json").write_text(
        json.dumps({"capture": capture_id, "queries": len(truth), "arms": summary}, indent=1)
    )
    print(f"\nwrote {args.out}/summary.json")


if __name__ == "__main__":
    main()
