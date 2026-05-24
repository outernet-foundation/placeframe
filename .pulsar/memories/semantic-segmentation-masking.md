---
updated: 2026-05-24
---

# Semantic-segmentation masking for transient scene content

## Goal

Suppress transient scene content (people, vehicles, animals) from
features in both the reconstruction and localization pipelines so the
system works outdoors. Today, outdoor capture in any location with
foot or vehicle traffic produces unstable maps and unreliable
localizations because features land on moving subjects.

The approach is a single semantic-segmentation pass right after
`canonicalize_image()`, with the mask applied in image space before
feature extraction. Calibration refits against the masked pipeline
once it lands.

## State

Not started. 3-day time-box with a deferral rule (see Decisions).
No code, no model pulled, no compose changes.
The localizer's `canonicalize_image()` seam is the established hook
point for an image-space mask step — no architectural prerequisite is
missing.

## Decisions

- **Model: OneFormer (MIT-licensed).**
  - Reconstructor: OneFormer-Swin-L (one-time cost at map build, accuracy matters more than latency).
  - Localizer: OneFormer-Swin-T (~100–200ms GPU; tolerable for 1Hz queries).
- **Transient class list (hard-coded, COCO labels):** `person, bicycle,
  car, motorcycle, bus, train, truck, boat, traffic light, bird, cat,
  dog, horse, sheep, cow`. Hard-coded rather than configurable because
  the list is stable across deployments and a config surface adds
  drift risk for no benefit.
- **Fallback when masked image yields too few keypoints.** If the
  masked image has fewer than `MIN_KEYPOINTS_AFTER_MASK` keypoints
  (default 50), retry the extraction without the mask and log. Bounds
  the crowded-scene failure mode at "no masking benefit + one extra
  pass," which is acceptable for v1.
- **Mask boundary keypoint stability.** Mask dilation defaults to 0;
  raise if observed boundary-keypoint instability hurts matching.
- **Calibration refit is part of the deliverable, not a follow-up.**
  After landing, re-run `fit_calibration.py` against the new
  `pipeline_version` and commit the refit `config/calibration/global.json`.
  ZED-only data is sufficient for the refit; the phone-side path is
  unaffected.
- **3-day time-box with deferral rule.** If Day 4 is being spent on
  environment, dependency, or model-loading wrestling, the work
  defers. The cost of deferral is one additional future calibration
  refit when masking later lands — not a multiplier on the rest of the
  initiative.

## Open questions

- **OneFormer-T memory footprint on the deployment GPU.** Verify the
  shared GPU can fit OneFormer-T + ALIKED + LightGlue + DIR
  simultaneously. Expected fit on A4000-class; confirm before
  committing.
- **Mask dilation default.** Start at 0; raise to 4-8px only if
  boundary instability is observed during dogfooding.

## Key files

- `docker/localizer/src/` — `canonicalize_image()` site is the
  insertion point for the localizer-side mask pass.
- `docker/reconstructor/src/` — same insertion logic on the
  reconstruction side; uses the larger OneFormer-Swin-L variant.
- `packages/python/neural-networks/SPEC.md` — masking design lives
  here once it lands; existing model-loader patterns set the shape for
  loading OneFormer at service startup.
- `config/calibration/global.json` — the artifact that gets refit
  against the masked pipeline as part of the deliverable.

## Pending threads

1. Verify OneFormer-T fits in the localizer's GPU budget alongside
   ALIKED + LightGlue + DIR. If not, escalate (smaller model variant,
   schedule mask + features serially instead of in parallel, etc.).
2. Implement the mask pass in `canonicalize_image()` with the COCO
   transient class list and the `MIN_KEYPOINTS_AFTER_MASK` fallback.
3. Implement the matching pass in the reconstructor; verify with one
   outdoor capture that previously failed.
4. Re-run `fit_calibration.py` against the new `pipeline_version`,
   commit `config/calibration/global.json`.
