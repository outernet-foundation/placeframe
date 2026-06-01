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

- **Rewrite is landed.** Five commits on `misc-fixes`:
  - `f2fce95d` — hand-rolled two-phase verification with rig pass and
    parallel workers. EM phase + rig phase live in
    `_verify_two_view_geometries`; rig phase has its own publisher
    status `verifying_rig_geometry`.
  - `a78dc0b2` — drop VIO-EM consistency check, leave rig pass as
    the rig-aware filter (was killing 93% of pairs when inline).
  - `978940bd` — move VIO-EM check to run after rig pass on the
    survivor pool.
  - `ca1167c3` — memory update.
  - `8529515b` (current HEAD-ish) — bin rig-pass inliers back per
    image-pair and rewrite `cam2_from_cam1`, mirroring C++
    `EstimateRigTwoViewGeometries`.
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
- **Most recent bin-back run (commit `8529515b`)** reported:
  ```
  [em_phase] kept=3177 undefined=0 low_inliers=4822
  [rig_phase] eligible=795 accepted=795 rejected=0 no_input_inliers=0 cross_rig_skipped=0
  [vio_em_filter] checked=3067 rejected_rotation=2585 rejected_translation=2663 skipped_no_rotation=0
  [verification] wrote 211 two_view_geometries of 7999 candidate pairs (rig_rewritten=101 em_only=110 empty=0)
  ```
  **The user judged this output absolutely not correct.** Direct quote:
  *"that is just absolutely not correct. for one thing it ran basically
  instantly. for another, the idea that rig verification rejected
  nothing make no sense at all. the logic must be wrong. also,
  completely disable the vio-em stuff."* The bin-back implementation
  needs to be re-examined — rig phase reporting `rejected=0,
  no_input_inliers=0, cross_rig_skipped=0, empty=0` despite a capture
  with known stereo aliasing is the smoking gun that the binning /
  pose-rewrite logic is wrong, not that the data is clean.
- **VIO-EM-as-pre-write filter is too aggressive.** Both inline and
  post-rig placement give ~85% rejection rate
  (`rotation` and `translation` thresholds each fire on ~85% of
  the same pairs — not catching disjoint outliers). Inline → 16/222
  registered; post-rig → 206 pairs written, still kills the run.
  At current thresholds (15° rotation / 30° translation), the check
  is broken on this capture's drift profile, not catching the
  teleports it was designed to address. **User decision: disable
  it entirely** before the next investigation pass.
- **Residual teleports remain** (from the 220/222 `a78dc0b2` run).
  The two timestamps the prior memory flagged
  (`858015→858515`, `864515→865015→865515`) still appear in
  `displacement-check` output:
  ```
  1780106865015 → 1780106865515  Δt=0.50s recon=17.74m prior=0.29m speed=35.49 m/s
  1780106864515 → 1780106865015  Δt=0.50s recon=14.41m prior=1.26m speed=28.83 m/s
  1780106859515 → 1780106860015  Δt=0.50s recon=2.87m  prior=0.35m speed=5.73 m/s
  1780106858515 → 1780106859015  Δt=0.50s recon=2.16m  prior=0.26m speed=4.32 m/s
  ```
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
- **Per-image-pair inlier rebinning is the right shape.** The C++
  source (`two_view_geometry.cc` lines 422–478) was confirmed:
  after GR6P succeeds, COLMAP bins the global inlier mask back into
  per-image-pair groups, rewrites each survivor's `cam2_from_cam1`
  from `cam2_from_rig2 * rig2_from_rig1 * Inverse(cam1_from_rig1)`,
  sets config to `CALIBRATED_RIG`, and empties (deletes) any
  constituent that ended up with zero rig-inliers. Our `8529515b`
  attempts this mirroring but produces implausibly clean output —
  the binning math or origin tracking is wrong. Re-examination is
  the next concrete action.
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
- **Disable VIO-EM entirely for the next run.** User directive after
  observing it kills 85% of sequential pairs without catching the
  teleports.
- **Match-spread filter stays out.** Prior reassessment held — net
  negative on this capture. The rig pass and two-phase ingest
  largely subsume what it was supposed to catch.

## Open questions

- **Why does the bin-back rig phase report zero rejects / zero empty
  constituents on a capture with known aliasing?** This is the
  load-bearing question. Suspects:
  1. **Origin tracking bug.** `ConstituentRecord.em_inlier_matches`
     and the global-correspondence-to-image-pair mapping may have a
     drift between EM-orientation indices and rig-orientation indices,
     so every global inlier looks like it landed in the "right"
     constituent.
  2. **`a_is_side1` orientation flag wrong.** If the GR6P solver's
     2D point set isn't actually pooled in the order the bin-back code
     assumes, the global `inlier_mask` indices map to the wrong
     constituents and end up uniformly distributed.
  3. **`cam2_from_cam1` rewrite identity-like.** If the rig-derived
     pose comes out near-identical to the EM pose for every pair,
     the rewrite is functionally a no-op and the apparent "rig
     succeeded everywhere" outcome reflects passing through the EM
     results unchanged.
  4. **RANSAC thresholds far too loose** so every pair clears the
     consensus. Less likely but check `min_num_inliers` and the
     ransac options handed to `estimate_generalized_relative_pose`.
  Investigation should add diagnostic logging of: pre-bin global
  inlier count vs sum-of-constituent inlier counts; per-constituent
  inlier-retention ratio; angle between rig-derived and EM-derived
  `cam2_from_cam1` per pair.

- **Once bin-back is correct, is VIO-EM still needed?** Hypothesis
  remains that a working bin-back catches the aliased stereo-pair
  constituents directly (those are the ones that lie about
  `cam2_from_cam1`), making VIO-EM redundant. Disabling VIO-EM in
  the next run will provide the cleaner signal.

- **Why is the rig pass rejecting only 1/798 (or 0/795) frame-pairs?**
  Even before bin-back, the *whole-frame-pair* reject count was
  vanishingly small. GR6P pools inliers across all 4 constituent
  image-pairs and the 3 healthy ones outvote the 1 aliased one in
  the RANSAC consensus. **This is exactly the failure mode
  per-image-pair rebinning was supposed to handle** — frame-pair
  succeeds, but the aliased constituent gets emptied via the bin
  step. The current bin-back evidently does not.

- **Inlier-count floor for the rig pass.** Reuses
  `two_view_min_num_inliers` from `TwoViewGeometryOptions`. No need
  to invent a separate knob.

## Key files

- `docker/reconstructor/src/reconstructor/colmap_pipeline.py` —
  contains the new `_verify_two_view_geometries` orchestrator,
  `_run_em_phase` / `_verify_pair_em`, `_run_rig_phase` /
  `_verify_frame_pair_rig`, `_build_rig_ransac_options`,
  `_apply_vio_em_filter`, and the new dataclasses `EmResult` /
  `ConstituentRecord` / `FramePairKey` introduced in `8529515b`
  for the bin-back. **`_verify_frame_pair_rig` is where the
  origin-tracking / pose-rewrite logic to audit lives.** Removed:
  `_check_sequential_pairs_against_vio`, the multiprocessing
  workaround, the `geometric_verification` /
  `GeometricVerifierOptions` / `ExistingMatchedPairingOptions`
  imports.
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
  this rewrite, the EM + rig phase split, the new publisher status,
  and the bin-back behavior once correct. Prose-only commit per
  CLAUDE.md spec-first rule.
- COLMAP source reference: `src/colmap/estimators/two_view_geometry.cc`
  lines 422–478 — canonical implementation of
  `EstimateRigTwoViewGeometries` that the Python bin-back must
  mirror.
- `.pulsar/memories/reconstruction-aliasing-failure-modes.md` —
  long-form context for everything upstream of this rewrite.

## Pending threads

1. **Audit `_verify_frame_pair_rig` bin-back logic in commit
   `8529515b`.** The implausibly clean output (rejected=0,
   no_input_inliers=0, empty=0, cross_rig_skipped=0) means the
   binning math is wrong somewhere. Concrete next move: add
   diagnostic logging that records, per frame-pair: pre-bin global
   inlier count, sum of per-constituent inlier counts after binning,
   per-constituent retention ratio, and the angular difference
   between the rig-derived and EM-derived `cam2_from_cam1`. Run
   once on `4bd303f1` and inspect.
2. **Disable VIO-EM entirely** (user directive) before the next
   diagnostic run, so the rig-phase signal is unconfounded.
3. **Re-run end-to-end on `4bd303f1`** after the bin-back fix lands.
   Track:
   - rig-pass per-image-pair rejection counts (expect aliased
     stereo-pair constituents to be dropped explicitly — non-zero
     `empty` count is the success signal);
   - sequential teleport pairs at `858015→858515` and
     `864515→865015→865515` (expect them to die naturally);
   - registered-frame count (should stay near 220/222).
4. **Decide VIO-EM fate** after step 3. If corrected bin-back
   catches the teleports, drop VIO-EM permanently. If teleports
   survive, revisit thresholds with diagnostic logging of the
   actual `cos_rotation` / `cos_translation_direction` distributions
   to choose them empirically rather than by intuition.
5. **Update `docker/reconstructor/SPEC.md`** (prose-only commit) to
   describe the hand-rolled two-phase verification, the new
   `verifying_rig_geometry` publisher status, the bin-back behavior,
   and roll up the still-stale lines from the prior memory in the
   same pass.
6. **Run a true A/B test campaign** once the bin-back is correct.
   User directive (line 102030 of transcript): the experiments over
   the last several sessions were confounded by the spatial-pairing
   flag still being on; a clean A/B that reverts various accumulated
   changes is needed to confirm the final solution is the simplest
   one that works.
7. **Fix stale `--sequential-window` help text** in
   `scripts/sweep_postprocess.py` and `scripts/displacement_check.py`
   (carried over from the prior memory's queue — not landed yet).
