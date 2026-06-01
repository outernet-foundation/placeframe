---
updated: 2026-06-01
---

# Hand-roll the full geometric verification stage (EM + rig) in Python

## Goal

Replace the stock `pycolmap.geometric_verification(rig_verification=True)`
call in `_verify_two_view_geometries` with a fully-owned Python loop
that does **both** the per-pair essential-matrix pass **and** the
rig-constrained second pass (GR6P / `estimate_generalized_relative_pose`).
The stock entry point does not release the GIL, takes ~30 minutes on
this capture's pair count, and emits no progress signal — owning the
loop is the right structural fix. It folds the per-pair VIO-EM check
back to the natural seam, gives uniform progress accounting and kill
story across both halves, and eliminates the recurring "what is
pycolmap silently doing" surprise (we lost rig verification in
`ddcb5033` without noticing).

The user explicitly chose this larger structural rewrite over a
smaller subprocess-polling band-aid. Direct quote: *"if we do this,
then we should revert the change to use geometric_verification and
do that bit ourselves too, and just do all of it ourselves, shouldn't
we?"*

## State

- **Rewrite is landed.** Three commits on `misc-fixes`:
  - `f2fce95d` — hand-rolled two-phase verification with rig pass and
    parallel workers. EM phase + rig phase live in
    `_verify_two_view_geometries`; rig phase has its own publisher
    status `verifying_rig_geometry`.
  - `a78dc0b2` — drop VIO-EM consistency check, leave rig pass as
    the rig-aware filter (was killing 93% of pairs when inline).
  - `978940bd` — move VIO-EM check to run after rig pass on the
    survivor pool (current HEAD-ish behavior; outcome was barely
    different from inline).
- **GIL release confirmed empirically.** Both
  `estimate_two_view_geometry` and `estimate_generalized_relative_pose`
  release the GIL. The hand-rolled `ThreadPoolExecutor` over 7999
  pairs completes in **seconds** on this capture, vs ~30 min for
  stock `geometric_verification`. The subprocess-pool escape hatch
  was not needed.
- **Best result so far on `4bd303f1`** (commit `a78dc0b2`, rig pass
  but no VIO-EM): **220 / 222 images registered** (vs 122/222 baseline
  under stock `geometric_verification` + post-pass VIO-EM). EM phase
  keeps 3175/7999; rig pass eligible=799, accepted=798, rejected=1.
- **Residual teleports remain.** The two timestamps the prior memory
  flagged (`858015→858515`, `864515→865015→865515`) still appear in
  `displacement-check` output for the 220/222 run:
  ```
  1780106865015 → 1780106865515  Δt=0.50s recon=17.74m prior=0.29m speed=35.49 m/s
  1780106864515 → 1780106865015  Δt=0.50s recon=14.41m prior=1.26m speed=28.83 m/s
  1780106859515 → 1780106860015  Δt=0.50s recon=2.87m  prior=0.35m speed=5.73 m/s
  1780106858515 → 1780106859015  Δt=0.50s recon=2.16m  prior=0.26m speed=4.32 m/s
  ```
- **VIO-EM-as-pre-write filter is too aggressive.** Both inline and
  post-rig placement give ~85% rejection rate
  (`rotation` and `translation` thresholds each fire on ~85% of
  the same pairs — not catching disjoint outliers). Inline → 16/222
  registered; post-rig → 206 pairs written, still kills the run.
  At current thresholds (15° rotation / 30° translation), the check
  is broken on this capture's drift profile, not catching the
  teleports it was designed to address.
- **No SPEC.md update yet.** The reconstructor SPEC is stale and
  the rewrite is a natural prose-first opportunity. Still pending.

## Decisions

- **Hand-roll both passes in Python.** Done. Stock
  `pycolmap.geometric_verification(...)` is gone; EM + rig live in
  our own loop with our own progress publisher cadence.
- **Parallelize both passes.** Done. `ThreadPoolExecutor` against
  `pycolmap.estimate_two_view_geometry` (EM phase) and
  `pycolmap.estimate_generalized_relative_pose` (rig phase). Both
  pycolmap calls release the GIL — confirmed by observation of
  near-instant completion on 7999 pairs. `deterministic_seed != None`
  forces both pools to `max_workers=1` for reproducibility.
- **Order**: EM phase first (per-pair RANSAC, writes
  `two_view_geometries` rows). Then rig phase: enumerate frame-pairs
  with `num_image_pairs > 1`, pool inlier correspondences across the
  constituent image-pairs, call `estimate_generalized_relative_pose`
  with `cams_from_rig` + `cameras` prebuilt once. On reject, delete
  the constituent image-pair rows.
- **New publisher status added.** `verifying_rig_geometry` was added
  alongside the existing `verifying_geometry`. The rig pass counts
  frame-pairs, not image-pairs, so giving it its own status label
  means operators can tell which half of verification is moving.
  SQL enum + datamodels + clients all regenerated.
- **Stereo gets the rig pass for free; no separate VIO-EM check for
  stereo.** Confirmed — both stereo cameras share the same VIO frame
  at the same instant, so the rig calibration is the correct oracle.
- **VIO-EM check applies (when on) to sequential pairs only.**
  Spatial (off by default) and retrieval are excluded by design.
- **Match-spread filter stays out.** Prior reassessment held — net
  negative on this capture. The rig pass and two-phase ingest
  largely subsume what it was supposed to catch.

## Open questions

- **Should the hand-roll mirror C++'s per-image-pair inlier rebinning
  inside the rig pass?** Verified by reading `two_view_geometry.cc`
  in the COLMAP source: when GR6P succeeds, C++ does **not** keep the
  original monocular EM TVGs unchanged. Instead it:
  1. Bins the global GR6P `inlier_mask` back into per-image-pair
     groups (`two_view_geometry.cc` lines 422–430).
  2. Each surviving image-pair gets a **rig-derived**
     `cam2_from_cam1` (computed as
     `cam2_from_rig2 * rig2_from_rig1 * Inverse(cam1_from_rig1)`) —
     the rig's solved relative pose, not the monocular EM pose.
  3. Each image-pair's TVG config is set to `CALIBRATED_RIG`.
  4. Image-pairs whose contributions ended up with **zero**
     inliers in the global mask get an **empty** TVG (cam2_from_cam1
     absent, inlier_matches empty) — effectively deleted from the
     mapper's view.

  Our hand-roll just says "rig succeeded → keep original monocular
  EM TVG unchanged." This is plausibly **the** divergence that lets
  the residual teleports through: image-pairs whose EM solution
  disagreed with the rig still survive in our pipeline, where in
  C++ they'd be reduced to a near-empty CALIBRATED_RIG TVG.
  Implementing this mirroring is the leading candidate next step.

- **VIO-EM check: drop entirely or fix thresholds?** At the current
  86% rejection rate, the check is broken on this capture's drift
  profile. Options are (a) loosen thresholds (15° → 30° rotation,
  30° → 60° translation) — likely widens until residual teleports
  also pass; (b) keep thresholds, accept that VIO-EM is a wrong-shape
  filter here; (c) leave the per-image-pair rig rebinning to do the
  job and drop VIO-EM altogether. (c) is the leading candidate, since
  the divergence above explains why teleports survive without
  invoking VIO at all.

- **Why is the rig pass rejecting only 1/798 frame-pairs?** Expected
  more on a capture with known aliasing. Probably because GR6P pools
  inliers across all 4 constituent image-pairs and the 3 healthy
  ones outvote the 1 aliased one in the RANSAC consensus — exactly
  the failure mode per-image-pair rebinning is designed to handle.

- **Inlier-count floor for the rig pass.** Reuses
  `two_view_min_num_inliers` from `TwoViewGeometryOptions`. No need
  to invent a separate knob.

## Key files

- `docker/reconstructor/src/reconstructor/colmap_pipeline.py` —
  contains the new `_verify_two_view_geometries` orchestrator,
  `_run_em_phase` / `_verify_pair_em`, `_run_rig_phase` /
  `_verify_frame_pair_rig`, `_build_rig_ransac_options`, and (in
  `978940bd`) `_apply_vio_em_filter` as a post-rig pass. Removed:
  `_check_sequential_pairs_against_vio`, the multiprocessing
  workaround, the `geometric_verification` / `GeometricVerifierOptions`
  / `ExistingMatchedPairingOptions` imports.
- `docker/reconstructor/src/reconstructor/pairs.py` — pair generation;
  intra-frame-stereo + sequential combos that make frame-pairs
  eligible for the rig pass (`num_image_pairs > 1`).
- `packages/python/core/src/core/reconstruction_options.py` /
  `OptionsBuilder` — RANSAC + two-view-geometry options.
  `two_view_min_num_inliers` is reused as the rig pass floor.
- `database/*.sql` — `reconstruction_status` enum gained
  `verifying_rig_geometry`. Datamodels + API clients regenerated in
  `37656c7f`.
- `docker/reconstructor/SPEC.md` — **stale**. Still needs to capture
  this rewrite, the EM + rig phase split, and the new publisher
  status. Prose-only commit per CLAUDE.md spec-first rule.
- `.pulsar/memories/reconstruction-aliasing-failure-modes.md` —
  long-form context for everything upstream of this rewrite.

## Pending threads

1. **Implement per-image-pair inlier rebinning in the rig pass** to
   mirror C++ `EstimateRigTwoViewGeometries`. After GR6P returns
   `inlier_mask`, bin the mask back into the constituent image-pairs,
   write a CALIBRATED_RIG TVG with the rig-derived `cam2_from_cam1`
   for each survivor, and write an empty TVG for image-pairs that
   ended up with zero rig-consensus inliers. Strong candidate to
   close out the two residual teleports without needing the VIO-EM
   check at all.
2. **Re-run end-to-end on `4bd303f1`** after the rebinning lands.
   Track:
   - rig-pass per-image-pair rejection counts (expect aliased
     stereo-pair constituents to be dropped explicitly);
   - sequential teleport pairs at `858015→858515` and
     `864515→865015→865515` (expect them to die naturally);
   - registered-frame count (should stay near 220/222).
3. **Decide VIO-EM fate** after step 2. If per-image-pair rebinning
   catches the teleports, drop VIO-EM entirely as redundant. If
   teleports survive, revisit thresholds with diagnostic logging
   of the actual `cos_rotation` / `cos_translation_direction`
   distributions to choose them empirically rather than by
   intuition.
4. **Update `docker/reconstructor/SPEC.md`** (prose-only commit) to
   describe the hand-rolled two-phase verification, the new
   `verifying_rig_geometry` publisher status, and roll up the
   still-stale lines from the prior memory in the same pass.
5. **Fix stale `--sequential-window` help text** in
   `scripts/sweep_postprocess.py` and `scripts/displacement_check.py`
   (carried over from the prior memory's queue — not landed yet).
