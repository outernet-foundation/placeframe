# Feature Pipeline Modernization — Intent

> Execution and progress tracked in [`plan.md`](plan.md).
> Companion design intent: [`vps-redesign-intent.md`](vps-redesign-intent.md) (Phases 0, 1, 3–6).

## Status

Design intent. The localizer's feature pipeline today has four definite problems and one optional upgrade. Each independently changes the localizer's `pipeline_version` hash, so each independently invalidates VPS calibration (see `vps-redesign-intent.md` "Pipeline version"). They're bundled into one initiative so calibration is fit once against the final pipeline.

**Design correction (mid-execution).** The original version of this doc bundled "aspect-ratio preprocessing" into a single piece treating cross-aspect mismatch as one problem. It's actually two distinct problems with different fixes, and the original retrieval-side fix proposed (letterbox to a fixed square inside the DIR head) was misguided — it was reaching for "fixed shape" without addressing the underlying *framing-mismatch* problem that whole-image retrieval suffers from when query and database aspect ratios differ. The corrected design splits the work into:

- **Piece 2 (local features)**: scale standardization via shorter-side resize. Per-keypoint matching naturally tolerates cross-aspect framing — only overlap matters; non-overlapping keypoints get rejected by RANSAC. Confirmed correct.
- **Piece 3 (retrieval)**: cross-aspect framing handled by square-tile aggregation, formerly listed as a non-goal. Promoted to Plan A based on field evidence (cross-device localization with mismatched aspect ratios produced visibly worse retrieval than same-device).

The Phase 2c work in `plan.md` already landed the piece-2 portion correctly; the in-DIR letterbox it also added is the misguided fix and needs to be reverted as part of Phase 2c-fixup before piece 3 lands.

## Context

### Current state

- **Detector/descriptor**: SuperPoint (MagicLeap weights, non-commercial research-only license). Loaded via `packages/python/neural-networks/src/neural_networks/models.py`.
- **Matcher**: LightGlue (Apache-2.0) with `features="superpoint"` checkpoint.
- **Retrieval**: DIR (ResNet-101-AP-GeM, BSD-3-Clause). Weights vendored as a self-hosted release artifact after the upstream Google Drive link broke.
- **Image preprocessing**: rotation only, via `core.camera_config.transform_image()`. No resize, crop, or aspect-ratio handling.
- **Masking**: none. Transient scene content (people, vehicles, vegetation, trash) contributes to both global and local features.

The same model stack runs in the reconstructor and the localizer; both call into the shared `models.py` loaders.

### Why this needs to change

- **License**: the SuperPoint MagicLeap weights cannot ship inside an Apache-2.0 codebase. `rpautrat/SuperPoint`'s MIT relabel is legally fragile because weights derive from MagicLeap's training. This is the most urgent of the four.
- **Local-feature scale**: ALIKED's receptive field is a fixed pixel patch. Without scale normalization, the same physical content produces different keypoint scales across cameras of different native resolutions; descriptors don't match across resolution gaps. The fix is scale standardization, not aspect-ratio handling — this affects the local-feature path only.
- **Retrieval cross-aspect framing**: a portrait query against a landscape-built map degrades retrieval because DIR (and any CNN-based global retrieval) produces *one descriptor per image* — a summary of all framed content. Cross-aspect query/database pairs summarize *different framed content* (the portrait excludes left/right strips, the landscape excludes top/bottom strips), so even when the actual scene overlaps perfectly, the global descriptors describe different overall framings and similarity drops. This is a framing problem, not a preprocessing-shape problem; it can't be fixed by reshaping the input. The fix is to give each image multiple framings (square-tile aggregation) so at least one tile pair frames similar content.
- **Transient content**: features extracted on people, vehicles, and other non-stable content generate matches that fail because the content moved between map-build time and query time. The Bayesian filter downstream can absorb some of this noise but not all.
- **Retrieval freshness**: DIR is dated (2019) and was self-vendored under duress. Modern alternatives are stronger and have cleaner upstream availability.

### Design goals (priority order)

1. License cleanliness across all model weights.
2. Cross-resolution scale standardization for the local-feature path.
3. Cross-aspect framing tolerance for the retrieval path.
4. Suppression of transient scene content from feature extraction.
5. Cleaner retrieval source (lower priority, may defer).

### Design non-goals

- Microservice extraction for the segmentation model. Both reconstructor and localizer remain monoliths; the segmentation step runs in-process.
- CPU-only inference paths.
- Per-device or per-scene tuning of segmentation thresholds.
- Mask caching across queries.
- Multi-scale or learned aggregation across retrieval tiles. Tiling itself (piece 3) addresses cross-aspect framing; multi-scale or attention-based tile aggregation can come later if retrieval is still a bottleneck after piece 3.

(Square-subimage tiling for retrieval was originally listed as a non-goal; it's now piece 3. See Status note.)

---

## The five pieces

### 1. SuperPoint → ALIKED

**License blocker. Smallest scope. First.**

- Replace `load_superpoint` with `load_aliked` in `models.py`. ALIKED is BSD-3-Clause (code + weights).
- Switch LightGlue's checkpoint to the official ALIKED-trained variant. Descriptor dim drops from 256 to 128; checkpoints are not interchangeable.
- ALIKED takes RGB float input; SuperPoint took grayscale. Adjust the tensor pipeline at the load site.
- Tune `detection_threshold` and `nms_radius` so keypoint density roughly matches SuperPoint's (used downstream by `MAX_KEYPOINTS_PER_IMAGE`).

Pre-market: no existing maps to migrate. Pure code swap.

### 2. Local-feature scale standardization

**Why:** ALIKED's receptive field is a fixed pixel patch (~30×30). At native phone resolution, that patch covers a tiny physical area (a few cm of a wall) and lands on sub-pixel texture; at lower resolution, the same patch covers a much larger physical region and lands on coarse structure. Cross-resolution descriptors describe different scales of reality and don't match. The fix is to standardize *physical-meters-per-pixel* across all images — done by resizing every input to a fixed shorter-side length.

**Mechanics:**

- Extend `transform_image()` (or sibling step) to resize the shorter side of every input to a fixed length (default 1024px), keeping aspect ratio, no padding.
- Update camera intrinsics correspondingly (per-axis scale) to keep PnP correct.
- ALIKED is fully convolutional and consumes variable HxW directly. LightGlue absorbs portrait↔landscape via keypoint coordinates — the per-keypoint matching paradigm naturally tolerates cross-aspect query/database pairs because matching only needs *overlapping content somewhere*: keypoints in the overlap match, keypoints in the non-overlap have no counterpart and get rejected by RANSAC. No retrieval-style framing fix is needed at this layer.

One-hook change shared across reconstructor and localizer. Reflected in `transform_image()` and `transform_intrinsics()` in `core.camera_config`. (Naming concern: "transform_image" doesn't telegraph that it resizes; consider renaming to e.g. `prepare_image_for_extraction` when piece 3 lands so all preprocessing functions sit alongside each other with honest names.)

### 3. Cross-aspect retrieval via square-tile aggregation

**Why:** DIR (and any CNN-backbone global retrieval — EigenPlaces, NetVLAD, SALAD, DINOv2-GeM) produces one descriptor per image, summarizing all framed content. Cross-aspect query/database pairs summarize *different* framed content even when the underlying scene is identical: a portrait query of a building and a landscape database image of the same building include/exclude different left/right/top/bottom strips. The global descriptors describe different overall framings and don't match well — and reshaping the input (resize, distort, letterbox) can't recover content that wasn't framed in the first place.

The fix isn't preprocessing — it's giving each image *multiple framings* so at least one tile pair frames similar content. This is the same idea referenced as "Square-subimage tiling" in the original non-goals list, now promoted based on field evidence.

**Mechanics:**

- Tile each image into M overlapping square crops (e.g., for a 1820×1024 landscape: 3 windows of 1024×1024 — left, center, right — with ~50% overlap; portrait inputs tile vertically with the same scheme rotated). The tiling is derived from the already-shorter-side-resized image (piece 2's output), so tile size = `LOCAL_FEATURE_RESIZE_SHORTER_SIDE` and the long axis determines M.
- Run DIR on each crop independently; produce M descriptors per image.
- **Database side** (reconstructor): store M descriptors per database image. OPQ index size and storage scale by M.
- **Query side** (localizer): tile the query the same way; produce M descriptors per query.
- **Similarity**: max over M_query × M_db pairs (default; mean is the alternative — TBD post-bringup once measurable).
- Top-K retrieval picks database images with at least one tile-pair scoring highly, regardless of how the query and database images were originally framed.

**Cost:** M× retrieval index storage (OPQ matrix and PQ codes), M× DIR forward passes per image (one-time at indexing, recurring per-query), M_query × M_db similarity work per (query, db-image) pair. Bounded — typical M = 3 to 5.

**Implementation surfaces:**

- `core/camera_config.py` (or a sibling preprocessing module) gains a `tile_for_retrieval()` helper that produces M square crops from a shorter-side-resized image.
- `DIR.forward()` reverts to a thin wrapper around the dirtorch model; the misguided letterbox added in Phase 2c is removed. Each tile is fed to `dir(...)` independently by the caller.
- Reconstructor (`run_reconstruction.py`) loops over tiles per database image; concatenated/structured descriptors flow into OPQ and PQ training and into the per-image descriptor cache. `Map` data structure stores M descriptors per image.
- Localizer (`localize.py`) tiles the query, produces M descriptors, and runs the top-K retrieval pass over `M_query × (M_db × num_db_images)` similarity scores.

### 4. Semantic-segmentation masking

**Time-boxed to 3 days. If it slips, defer to post-Phase 6.**

- OneFormer (MIT code + weights) loaded once at service startup.
- Reconstructor: OneFormer-Swin-L. One-time cost at map build; favor quality.
- Localizer: OneFormer-Swin-T. ~100–200ms GPU per query; tolerable for ~1Hz query rate.
- Inserted right after `transform_image()` in both pipelines.
- Hard-coded COCO transient class list: `person, bicycle, car, motorcycle, bus, train, truck, boat, traffic light, bird, cat, dog, horse, sheep, cow`. Tunable in config but not per-deployment.
- Mask applied in image space: pixels in masked regions zeroed before both DIR and ALIKED inference.
- Fallback: if a masked image has fewer than `MIN_KEYPOINTS_AFTER_MASK` (default 50) keypoints, retry without mask and log. Avoids over-masking failure on crowded scenes.

**Time-box rule**: if Day 4 is spent on environment/dependency/model-loading issues, the piece is deferred. Pieces 1 and 2 ship without it. The cost of deferral is a calibration refit when masking later lands.

### 5. DIR replacement (DEFERRED — optional upgrade)

DIR works and is license-clean, but is dated and self-vendored. Modern Apache/MIT alternatives:

- **EigenPlaces** (ICCV 2023, MIT) — purpose-built for VPR/localization retrieval. Beats AP-GeM on standard benchmarks. ResNet50 backbone, 2048-D descriptors.
- **SALAD** (CVPR 2024, MIT) — current SOTA, DINOv2 backbone. Heavier compute.
- **DINOv2 + GeM pooling** (Apache 2.0) — simplest path. No specialized training. Drops the dirtorch dependency entirely.

Deferred because retrieval quality isn't the bottleneck. Re-evaluate after pieces 1–3 land. If pursued, costs another calibration refit unless bundled before Phase 3.

---

## Sequencing and pipeline-version interaction

All of pieces 1–4 (and 5 if pursued) change the localizer's `pipeline_version` hash. The bundling logic:

- Each piece independently invalidates calibration.
- Bundling all pieces before VPS Phase 3 means calibration is fit once.
- Any piece deferred to after Phase 3 forces a calibration refit when it lands.

Therefore the order:

1. ALIKED swap (license urgency, smallest scope).
2. Local-feature scale standardization (clean signal for masking and tiling).
3. Square-tile retrieval aggregation (revert the Phase 2c letterbox first; then tile).
4. Semantic masking (biggest scope; time-boxed to 3 days; deferrable if it slips).
5. Repair `test-placeframe-e2e` script and rerun the parameter sweep against the new pipeline. Output informs Phase 3's calibration defaults.
6. VPS Phase 3 (ZED-only global calibration) — fits once against the final pipeline.

DIR replacement (piece 5) is opportunistic — bundle it ahead of Phase 3 if it's quick, otherwise leave it for a later focused upgrade. Note that DIR replacement and tiling compose: any successor retrieval model (EigenPlaces, SALAD, DINOv2+GeM) inherits the same global-descriptor / cross-aspect-framing problem and benefits from tiling unchanged.

---

## Failure modes

| Condition | Behavior |
|---|---|
| ALIKED checkpoint or weights unreachable at load | Hard-fail service startup with explicit error pointing at the vendored release artifact path. |
| OneFormer model unreachable | Hard-fail service startup if masking is enabled. |
| Masked image has fewer than `MIN_KEYPOINTS_AFTER_MASK` keypoints | Retry without mask, log. Localization continues. |
| Shorter-side resize produces visibly worse local matching than current | Single-hook revert path in `transform_image()`. |
| Square-tile retrieval produces worse top-K than untiled DIR for in-aspect queries | Configurable `RETRIEVAL_TILES_PER_IMAGE = 1` falls back to single-window behavior; revertible without removing the tiling code path. |

---

## Risks and unknowns

- **ALIKED keypoint density tuning**. Default thresholds may produce too few or too many keypoints; expect post-deployment tuning of `detection_threshold` and `nms_radius`.
- **OneFormer GPU memory pressure**. The localizer container holds OneFormer-T + ALIKED + LightGlue + DIR (or replacement) on one device. Should fit on an A4000-class card; verify on the deployment GPU before committing.
- **Mask boundary keypoints**. Features extracted at the boundary between masked and unmasked regions may be unstable. Mask dilation (default 0) is the tuning knob; revisit if observed.
- **Crowded-scene masking failure**. Plazas dominated by people may end up with insufficient keypoints. The fallback (retry without mask) bounds this risk but means crowded scenes get the worst of both worlds — no masking benefit, slower than baseline. Acceptable for v1.
- **Masking time-box overruns**. The 3-day budget is tight. Honest assessment: 50–70% likely it lands in budget. Deferral adds a future calibration refit, not an architectural problem.
- **Tile aggregation policy** (max vs mean, similarity weighting). Default is max-over-pairs; mean is the alternative if max ends up too noisy on tiles dominated by repetitive structure. Untested on real data — pick after Phase 2e parameter sweep covers it.
- **Tile geometry tuning**. M, tile size, and overlap are interrelated. Defaults (tile_size = `LOCAL_FEATURE_RESIZE_SHORTER_SIDE`, ~50% overlap, M = ⌈long_axis / (tile_size · overlap_stride)⌉) are reasonable but unmeasured. Sweep range during Phase 2e.
- **Retrieval index size**. M× growth in OPQ index storage and per-query similarity work. At M=3–5 and database sizes typical for VPS maps (few thousand images), this is workable. If M needs to grow further, OPQ subvector budget may need rebalancing.
- **In-aspect regression risk for tiling**. Tiling could underperform single-window retrieval on same-aspect query/database pairs (because tiles capture less context per descriptor). Honest unknown — measure during Phase 2e against the existing pre-2c-letterbox single-window baseline.

---

## Open tunables

| Parameter | Default | Where used |
|---|---|---|
| ALIKED `detection_threshold` | TBD post-bringup | feature extraction |
| ALIKED `nms_radius` | TBD post-bringup | feature extraction |
| Resize target shorter side | 1024 px | local-feature preprocessing (piece 2) |
| Retrieval tile size | = `LOCAL_FEATURE_RESIZE_SHORTER_SIDE` (1024 px) | retrieval tiling (piece 3) |
| Retrieval tile overlap fraction | 0.5 | retrieval tiling (piece 3) |
| `RETRIEVAL_TILES_PER_IMAGE` (M) | derived from long axis + overlap; min 1, typical 3–5 | retrieval tiling (piece 3) |
| Tile similarity aggregation | `max` (alternative: `mean`) | retrieval tiling (piece 3) |
| OneFormer reconstructor variant | Swin-L | masking |
| OneFormer localizer variant | Swin-T | masking |
| Transient class list | COCO things subset (above) | masking |
| Mask boundary dilation | 0 px | masking |
| `MIN_KEYPOINTS_AFTER_MASK` | 50 | masking fallback |
