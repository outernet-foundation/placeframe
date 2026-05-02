# Feature Pipeline Modernization — Intent

> Execution and progress tracked in [`plan.md`](plan.md).
> Companion design intent: [`vps-redesign-intent.md`](vps-redesign-intent.md) (Phases 0, 1, 3–6).

## Status

Design intent. The localizer's feature pipeline today has three definite problems and one optional upgrade. Each independently changes the localizer's `pipeline_version` hash, so each independently invalidates VPS calibration (see `vps-redesign-intent.md` "Pipeline version"). They're bundled into one initiative so calibration is fit once against the final pipeline.

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
- **Aspect ratio**: a portrait query against a landscape-built map degrades retrieval (DIR's global descriptor is shape-sensitive) and pushes feature distributions asymmetrically at extreme mismatches. Querying at the wrong shape is a design bug.
- **Transient content**: features extracted on people, vehicles, and other non-stable content generate matches that fail because the content moved between map-build time and query time. The Bayesian filter downstream can absorb some of this noise but not all.
- **Retrieval freshness**: DIR is dated (2019) and was self-vendored under duress. Modern alternatives are stronger and have cleaner upstream availability.

### Design goals (priority order)

1. License cleanliness across all model weights.
2. Robustness to query/database aspect-ratio mismatch.
3. Suppression of transient scene content from feature extraction.
4. Cleaner retrieval source (lower priority, may defer).

### Design non-goals

- Microservice extraction for the segmentation model. Both reconstructor and localizer remain monoliths; the segmentation step runs in-process.
- Square-subimage tiling. The hloc/LightGlue resize-shorter-side default handles aspect-ratio mismatch adequately; tiling is non-standard, multiplies cost, and is reserved as a Plan B if cross-aspect retrieval misbehaves after piece 2.
- CPU-only inference paths.
- Per-device or per-scene tuning of segmentation thresholds.
- Mask caching across queries.

---

## The four pieces

### 1. SuperPoint → ALIKED

**License blocker. Smallest scope. First.**

- Replace `load_superpoint` with `load_aliked` in `models.py`. ALIKED is BSD-3-Clause (code + weights).
- Switch LightGlue's checkpoint to the official ALIKED-trained variant. Descriptor dim drops from 256 to 128; checkpoints are not interchangeable.
- ALIKED takes RGB float input; SuperPoint took grayscale. Adjust the tensor pipeline at the load site.
- Tune `detection_threshold` and `nms_radius` so keypoint density roughly matches SuperPoint's (used downstream by `MAX_KEYPOINTS_PER_IMAGE`).

Pre-market: no existing maps to migrate. Pure code swap.

### 2. Aspect-ratio preprocessing

**Standard hloc-style handling.**

- Extend `transform_image()` (or sibling step) to resize the shorter side of every input to a fixed length (default 1024px), keeping aspect ratio, no padding. Local-feature path operates at variable HxW; the fully-convolutional ALIKED handles this natively. LightGlue absorbs portrait↔landscape via keypoint coordinates.
- Update camera intrinsics correspondingly to keep PnP correct.
- For the global retrieval head (DIR or replacement): letterbox to a fixed square at the retrieval head only. Mask the padded region from feature pooling so the descriptor isn't contaminated.

This is a one-hook change shared across reconstructor and localizer.

### 3. Semantic-segmentation masking

**Time-boxed to 3 days. If it slips, defer to post-Phase 6.**

- OneFormer (MIT code + weights) loaded once at service startup.
- Reconstructor: OneFormer-Swin-L. One-time cost at map build; favor quality.
- Localizer: OneFormer-Swin-T. ~100–200ms GPU per query; tolerable for ~1Hz query rate.
- Inserted right after `transform_image()` in both pipelines.
- Hard-coded COCO transient class list: `person, bicycle, car, motorcycle, bus, train, truck, boat, traffic light, bird, cat, dog, horse, sheep, cow`. Tunable in config but not per-deployment.
- Mask applied in image space: pixels in masked regions zeroed before both DIR and ALIKED inference.
- Fallback: if a masked image has fewer than `MIN_KEYPOINTS_AFTER_MASK` (default 50) keypoints, retry without mask and log. Avoids over-masking failure on crowded scenes.

**Time-box rule**: if Day 4 is spent on environment/dependency/model-loading issues, the piece is deferred. Pieces 1 and 2 ship without it. The cost of deferral is a calibration refit when masking later lands.

### 4. DIR replacement (DEFERRED — optional upgrade)

DIR works and is license-clean, but is dated and self-vendored. Modern Apache/MIT alternatives:

- **EigenPlaces** (ICCV 2023, MIT) — purpose-built for VPR/localization retrieval. Beats AP-GeM on standard benchmarks. ResNet50 backbone, 2048-D descriptors.
- **SALAD** (CVPR 2024, MIT) — current SOTA, DINOv2 backbone. Heavier compute.
- **DINOv2 + GeM pooling** (Apache 2.0) — simplest path. No specialized training. Drops the dirtorch dependency entirely.

Deferred because retrieval quality isn't the bottleneck. Re-evaluate after pieces 1–3 land. If pursued, costs another calibration refit unless bundled before Phase 3.

---

## Sequencing and pipeline-version interaction

All of pieces 1–3 (and 4 if pursued) change the localizer's `pipeline_version` hash. The bundling logic:

- Each piece independently invalidates calibration.
- Bundling all pieces before VPS Phase 3 means calibration is fit once.
- Any piece deferred to after Phase 3 forces a calibration refit when it lands.

Therefore the order:

1. ALIKED swap (license urgency, smallest scope).
2. Aspect-ratio preprocessing (clean signal for masking work and Phase 3 calibration).
3. Semantic masking (biggest scope; time-boxed to 3 days; deferrable if it slips).
4. Repair `test-placeframe-e2e` script and rerun the parameter sweep against the new pipeline. Output informs Phase 3's calibration defaults.
5. VPS Phase 3 (ZED-only global calibration) — fits once against the final pipeline.

DIR replacement (piece 4) is opportunistic — bundle it ahead of Phase 3 if it's quick, otherwise leave it for a later focused upgrade.

---

## Failure modes

| Condition | Behavior |
|---|---|
| ALIKED checkpoint or weights unreachable at load | Hard-fail service startup with explicit error pointing at the vendored release artifact path. |
| OneFormer model unreachable | Hard-fail service startup if masking is enabled. |
| Masked image has fewer than `MIN_KEYPOINTS_AFTER_MASK` keypoints | Retry without mask, log. Localization continues. |
| Aspect-ratio resize produces visibly worse retrieval than current | Single-hook revert path. |

---

## Risks and unknowns

- **ALIKED keypoint density tuning**. Default thresholds may produce too few or too many keypoints; expect post-deployment tuning of `detection_threshold` and `nms_radius`.
- **OneFormer GPU memory pressure**. The localizer container holds OneFormer-T + ALIKED + LightGlue + DIR (or replacement) on one device. Should fit on an A4000-class card; verify on the deployment GPU before committing.
- **Mask boundary keypoints**. Features extracted at the boundary between masked and unmasked regions may be unstable. Mask dilation (default 0) is the tuning knob; revisit if observed.
- **Crowded-scene masking failure**. Plazas dominated by people may end up with insufficient keypoints. The fallback (retry without mask) bounds this risk but means crowded scenes get the worst of both worlds — no masking benefit, slower than baseline. Acceptable for v1.
- **Masking time-box overruns**. The 3-day budget is tight. Honest assessment: 50–70% likely it lands in budget. Deferral adds a future calibration refit, not an architectural problem.

---

## Open tunables

| Parameter | Default | Where used |
|---|---|---|
| ALIKED `detection_threshold` | TBD post-bringup | feature extraction |
| ALIKED `nms_radius` | TBD post-bringup | feature extraction |
| Resize target shorter side | 1024 px | image preprocessing |
| OneFormer reconstructor variant | Swin-L | masking |
| OneFormer localizer variant | Swin-T | masking |
| Transient class list | COCO things subset (above) | masking |
| Mask boundary dilation | 0 px | masking |
| `MIN_KEYPOINTS_AFTER_MASK` | 50 | masking fallback |
