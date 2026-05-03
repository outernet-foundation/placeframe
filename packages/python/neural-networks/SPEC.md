# neural-networks — model loaders

`packages/python/neural-networks` holds the loaders for the deep-learning models the localizer and reconstructor use: ALIKED (local feature extractor + descriptor), LightGlue (matcher), DIR (global descriptor for retrieval). Models are loaded once at service startup; per-request inference is driven by the `core/model_wrappers.py` factories so the typed-tensor seam stays consistent across services. See `packages/python/core/SPEC.md` "Static tensor shape typing" for the wrapper layer.

## License posture

All shipped weights are license-clean for commercial use:

| Component | Source | License |
|---|---|---|
| ALIKED | upstream | BSD-3-Clause (code + weights) |
| LightGlue | upstream | Apache-2.0; ALIKED-trained checkpoint |
| DIR (ResNet-101-AP-GeM) | self-hosted release artifact | BSD-3-Clause; weights vendored after the upstream Google Drive link broke |

ALIKED replaced an earlier SuperPoint stack. SuperPoint's MagicLeap weights are non-commercial research-only and could not ship inside an Apache-2.0 codebase; `rpautrat/SuperPoint`'s MIT relabel is legally fragile because the weights derive from MagicLeap's training. ALIKED's BSD-3-Clause licensing on both code and weights is unambiguous.

## ALIKED

`load_aliked(device=DEVICE)` returns the model. The `core/model_wrappers.py` `make_local_feature_extractor` factory wraps it and returns the typed callable used by both `localize.py` and `run_reconstruction.py`.

ALIKED is fully convolutional and consumes variable HxW directly, so the local-feature path doesn't need a fixed input size. ALIKED takes RGB float input (SuperPoint took grayscale); the tensor pipeline at the load site feeds RGB directly. Descriptor dim is 128 (SuperPoint's was 256); LightGlue's checkpoint is `features="aliked"` to match.

`detection_threshold` and `nms_radius` are left at ALIKED defaults (`0.2`, `2`); tuning is post-bringup once keypoint density on real data is observable.

ALIKED's receptive field is a fixed pixel patch (~30×30). At native phone resolution that patch covers a tiny physical area and lands on sub-pixel texture; at lower resolution the same patch covers a much larger physical region and lands on coarse structure. Cross-resolution descriptors describe different scales of reality and don't match. The shorter-side resize in `core.image_preprocess.canonicalize_image` standardizes physical-meters-per-pixel before features are extracted (see `packages/python/core/SPEC.md` "Image preprocessing").

## LightGlue

`load_lightglue(device)` returns the matcher. Tuning details (V1/V2/V3 measurement record, batching footgun, when V3 might become correct again) live as a comment on `load_lightglue` in `models.py`. The code comment is the source of truth — no SPEC duplication.

The `core/model_wrappers.py` `make_local_feature_matcher_for_tensors` and `make_local_feature_matcher_for_arrays` factories wrap it; `core/lightglue.py` exports `Keypoints` / `Descriptors` / `KeypointsArrays` / `DescriptorsArrays` `NewType` brands so positional swaps at the matcher are caught statically.

## DIR (retrieval)

`load_DIR(device)` returns the global-descriptor model. DIR works and is license-clean, but is dated (2019) and self-vendored. Modern Apache/MIT alternatives (EigenPlaces — ICCV 2023 MIT, SALAD — CVPR 2024 MIT, DINOv2 + GeM pooling — Apache 2.0) outperform AP-GeM on standard benchmarks but retrieval quality isn't the current bottleneck. Replacement is opportunistic; bundle ahead of any planned calibration refit if pursued.

Any successor retrieval model inherits the same global-descriptor / cross-aspect-framing problem and benefits from square-tile aggregation unchanged (see `packages/python/core/SPEC.md` "Image preprocessing").

`DIR.forward` is a thin wrapper around the dirtorch model; it does no preprocessing. Each tile is fed independently by the caller. An earlier in-DIR letterbox + mean-padding attempt to address cross-aspect framing was misguided and was removed in favor of square-tile aggregation upstream.

## Failure modes

| Condition | Behavior |
|---|---|
| ALIKED checkpoint or weights unreachable at load | Hard-fail service startup with explicit error pointing at the vendored release artifact path. |
| OneFormer model unreachable (when masking ships) | Hard-fail service startup if masking is enabled. |
| Shorter-side resize produces visibly worse local matching than current | Single-hook revert path in `core.image_preprocess.canonicalize_image`. |
| Square-tile retrieval produces worse top-K than untiled DIR for in-aspect queries | Configurable `RETRIEVAL_TILES_PER_IMAGE = 1` falls back to single-window behavior; revertible without removing the tiling code path. |

## Conditional torch extras

The package declares `cpu`, `cuda`, and `rocm` extras that pin the matching PyTorch build. The Docker images install one extra; the workspace venv typically uses `--extra cpu` for local type-checking (`uv sync --all-packages --extra cpu`). Without the extra, `from torch import …` resolves as Unknown for pyright and other `reportUnknown*` errors drown out real signal.

## Future work (semantic masking)

OneFormer (MIT code + weights) is the planned masking model — Swin-L variant in the reconstructor (one-time cost at map-build), Swin-T variant in the localizer (~100–200 ms GPU per query; tolerable for ~1Hz queries). Inserted right after `canonicalize_image()` in both pipelines. Hard-coded COCO transient class list. Mask applied in image space — pixels in masked regions zeroed before both DIR and ALIKED inference. Fallback if a masked image has fewer than `MIN_KEYPOINTS_AFTER_MASK` keypoints: retry without mask and log.

Required for outdoor operation: city-street scenes are dominated by parked cars, pedestrians, and other transient content; without masking, features extracted on those objects produce matches that fail at query time (the cars moved, the people moved, the street furniture rotated). Indoor-only operation tolerates the absence because indoor transient content is sparser.

Tracked in `plan.md` as Phase 2d.
