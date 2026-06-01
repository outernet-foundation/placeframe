---
updated: 2026-06-01
---

# Hand-roll the full geometric verification stage (EM + rig) in Python

## Goal

Replace the current `pycolmap.geometric_verification(rig_verification=True)`
call in `_verify_two_view_geometries` with a fully-owned Python loop that
does **both** the per-pair essential-matrix pass **and** the rig-constrained
second pass (GR6P / `estimate_generalized_relative_pose`). The current call
into stock pycolmap does not release the GIL, which makes progress
reporting and per-pair filtering impossible without subprocess gymnastics.
Owning the loop is the right structural fix: it folds the lost
match-spread filter and the new VIO-EM check back to the natural seam,
eliminates the recurring "what is pycolmap silently doing" class of
surprise (we lost rig verification in `ddcb5033` without noticing, and
hit a hang in the rig pass with no progress signal), and gives one
uniform progress accounting / kill story across both halves.

The user explicitly chose this larger structural rewrite over the
smaller subprocess-polling band-aid currently sitting uncommitted in the
working tree. Direct quote: *"if we do this, then we should revert the
change to use geometric_verification and do that bit ourselves too, and
just do all of it ourselves, shouldn't we?"* — agreed by the assistant
with reasoning around symmetry / ownership / opacity bites.

## State

- **Pipeline state just before this work**: commit `e82a61ee` on branch
  `misc-fixes` is HEAD. The three "shipped last session" items
  (`pycolmap.geometric_verification(rig_verification=True)` with
  DB-row polling for progress, pair-time VIO-vs-essential-matrix check
  for sequential pairs, metric `sequential_window_m=3.0`) are in. The
  `reconstruction-aliasing-failure-modes` memory is the canonical
  long-form context.
- **Uncommitted work-in-progress** sits in
  `docker/reconstructor/src/reconstructor/colmap_pipeline.py`. It is a
  *subprocess* workaround for the GIL-not-released problem — the
  parent spawns a child via `multiprocessing.get_context("spawn")`
  that calls `geometric_verification`, while the parent polls the
  `two_view_geometries` row count from a read-only sqlite3 connection.
  This is the smaller band-aid. **Decision: this approach is being
  abandoned in favor of the full rewrite.** Either revert this diff
  before starting, or keep it staged temporarily and delete during
  the rewrite — but do not ship it.
- **The "test the three new changes on `4bd303f1`" item from the prior
  memory is now deferred.** Doing it on the soon-to-be-replaced
  pycolmap entry point burns time on architecture we're discarding.
  Run the validation on the hand-rolled stack instead.
- **No new captures or A/B runs since the prior memory.** The two
  residual teleports the VIO-EM check is meant to address
  (`858015→858515`, `864515→865015→865515`) remain untested.

## Decisions

- **Hand-roll both passes in Python.** Drop the stock
  `pycolmap.geometric_verification(...)` call entirely. EM phase + rig
  phase live in our own loop, with our own progress publisher cadence,
  our own per-pair filters at the natural seam.
- **Parallelize both passes.** User explicitly said *"we will need to
  parallelize the rig-verification too"*. The EM phase will use
  `ThreadPoolExecutor` against `pycolmap.estimate_two_view_geometry`
  (already pybind11-released GIL by precedent of how match_spatial
  internally threads). The rig phase will use the same pattern against
  `pycolmap.estimate_generalized_relative_pose`. Confirm GIL release
  empirically by watching CPU utilization on the first run; fall back
  to a subprocess pool only if a single Python thread is the bottleneck.
- **Order**: EM phase first (per-pair essential matrix RANSAC, writes
  `two_view_geometries` rows). Then rig phase: enumerate frame-pairs
  with `num_image_pairs > 1`, pool inlier correspondences across the 4
  cross-camera image-pairs, call
  `estimate_generalized_relative_pose(points2D1, points2D2,
  camera_idxs1, camera_idxs2, cams_from_rig, cameras,
  estimation_options=RANSACOptions(...))`. On `None` or below inlier
  threshold, delete the constituent image-pair `two_view_geometries`
  rows via `database.delete_two_view_geometry`.
- **Per-pair filters fold back inline.** The match-spread filter (this
  session removed) and the new VIO-EM consistency check belong as
  predicates inside the EM-phase loop, run on the surviving
  TwoViewGeometry before the database write. Don't keep them as
  separate post-passes once we own the seam.
- **Acceptable EM-phase slowdown**: COLMAP's batched C++ did ~8000
  pairs in 20s; Python thread-pool likely 60-90s. One-time tax on each
  reconstruction, noise relative to 5-30 min total pipeline. Subprocess
  pool is the escape hatch if it ever bites.
- **Stereo gets the rig pass for free; no separate VIO-EM check
  for stereo.** Both stereo cameras share the same VIO frame at the
  same instant, so VIO is identical for both — the correct oracle is
  `sensor_from_rig` (rig calibration), which the rig pass already uses.
- **VIO-EM check applies to sequential pairs only.** Stereo: covered by
  rig pass. Spatial (off by default): VIO drift over minutes makes the
  check tighter than needed, defensible with looser thresholds if
  re-enabled. Retrieval: VIO disagreement is exactly the signal we
  want retrieval to provide, the check would kill the pairs we need.
- **One alternative explicitly dismissed**: a one-line pycolmap patch
  adding `py::call_guard<py::gil_scoped_release>()` to
  `geometric_verification` would give us SQLite-polling visibility for
  free. Right answer in a fast-upstream-cycle universe; not waiting on
  pycolmap's real cycle time.

## Implementation outline

Lives in `docker/reconstructor/src/reconstructor/colmap_pipeline.py`.
Replace `_verify_two_view_geometries` with two-stage:

1. **EM phase loop.** For each candidate pair from the existing pair
   set, `ThreadPoolExecutor` submits a worker that:
   - reads the matches from the DB,
   - runs `pycolmap.estimate_two_view_geometry(...)` (the same call our
     old `ddcb5033` per-pair loop made),
   - applies inline match-spread filter (if we decide it's worth
     keeping — see "Open questions"),
   - applies inline VIO-EM check on sequential pairs,
   - writes `database.write_two_view_geometry(pair_id, tvg)` on
     success.
   Publisher progress ticks per pair.
2. **Rig phase loop.** Enumerate distinct frame-pairs with
   `num_image_pairs > 1` from the pair set (same set the EM phase
   just verified). For each frame-pair, `ThreadPoolExecutor` submits a
   worker that:
   - reads each constituent image-pair's `TwoViewGeometry` via
     `Database.read_two_view_geometry`,
   - gathers inlier 2D-2D correspondences and the per-correspondence
     camera-index assignment into the four flat arrays the GR6P
     entry point expects,
   - calls `pycolmap.estimate_generalized_relative_pose(...)` with
     `cams_from_rig` + `cameras` pre-built once at the top of the
     function from `rigs`,
   - if `None` or below an inlier-count floor, calls
     `database.delete_two_view_geometry` for each image-pair in the
     frame-pair.
   Publisher progress ticks per frame-pair.

Plumbing details (load-bearing):

- Build the `cams_from_rig` + `cameras` arrays once at function entry
  from `rigs`. The per-correspondence camera index is derived from
  which image-pair the correspondence came from (we already track this
  by construction in pair-gen).
- The existing `expected_count` plumbing in the publisher works for
  EM phase as-is (one tick per pair). Add a second phase publisher
  call (or extend the existing one) for the rig pass — one tick per
  frame-pair, with the count pre-computed from the pair-set.
- `VERIFYING_GEOMETRY` may want to split into `VERIFYING_GEOMETRY_EM`
  and `VERIFYING_GEOMETRY_RIG` publisher phases for observability,
  matching prior memory's note that no new publisher phase was added
  for the `geometric_verification` rig pass — this rewrite is the
  natural time to add the split.

## Open questions

- **Does `estimate_two_view_geometry` release the GIL?** Strongly
  suspected (pybind11 idiom for small per-call work) but not verified.
  First test: run the EM-phase thread pool with 8 workers, observe
  CPU utilization. If it pegs one core, subprocess-pool the EM phase.
- **Does `estimate_generalized_relative_pose` release the GIL?** Same
  unknown, same first test. The rig pass has fewer iterations
  (frame-pairs, not image-pairs), so single-threaded is a less painful
  fallback.
- **Match-spread filter: re-add or stay deleted?** Prior memory's
  honest reassessment was that it's plausibly net-negative on the
  cubicle capture (killed 12% of sequential / spatial pairs to catch
  only 4% of retrieval). Question for the rewrite: does it pay off in
  the *new* world where retrieval no longer enters the seed (two-phase
  ingest) and the rig pass catches one-side-lies aliasing on stereo
  pairs? Probably leave it out until evidence justifies adding back.
- **Inlier-count floor for the rig pass.** GR6P returns an inlier
  count; we need a threshold below which the frame-pair is deleted.
  Stock COLMAP uses a `min_num_inliers` from `TwoViewGeometryOptions`
  — reuse that, don't invent a new knob.
- **GR6P RANSAC options.** Reuse the EM phase's `RANSACOptions` until
  a reason to diverge surfaces.

## Key files

- `docker/reconstructor/src/reconstructor/colmap_pipeline.py` —
  contains `_verify_two_view_geometries`, the function being replaced.
  Currently has uncommitted subprocess WIP that should be reverted
  or discarded.
- `docker/reconstructor/src/reconstructor/pairs.py` — pair generation
  (sequential, spatial, retrieval, intra-frame-stereo). Lines ~109-110
  emit the cross-camera combos that make frame-pairs have
  `num_image_pairs > 1` and thus eligible for the rig pass.
- `packages/python/core/src/core/reconstruction_options.py` /
  `OptionsBuilder` — where the two_view_geometry / RANSAC options
  come from. New thresholds (if any) land here.
- `docker/reconstructor/SPEC.md` — **stale** at lines 56, 60, 164 per
  prior memory. The rewrite is a new prose-first opportunity to
  capture both this rewrite and the prior session's `geometric_verification`
  + DB-polling + VIO-EM + metric-window changes in one
  documentation pass. Per CLAUDE.md spec-first / prose-and-code-separate
  rules, the SPEC update lands in its own commit before the code.
- `.pulsar/memories/reconstruction-aliasing-failure-modes.md` — long-form
  context for everything upstream of this rewrite (failure modes,
  prior A/B runs, layered weak signals architecture).

## Pending threads

1. **Revert or discard the uncommitted subprocess WIP** in
   `colmap_pipeline.py` before starting the rewrite, so the diff is
   clean against `e82a61ee`.
2. **Implement the hand-rolled two-phase verification** per the
   outline above. Lint, type-check, run reconstructor tests.
3. **Validate empirically that GIL is released** on
   `estimate_two_view_geometry` and `estimate_generalized_relative_pose`
   by observing CPU utilization with the ThreadPoolExecutor. Fall back
   to subprocess pool per phase if needed.
4. **Run end-to-end on `4bd303f1`** with the hand-rolled stack +
   metric `sequential_window_m=3.0` + sequential VIO-EM check. Track:
   - rig-pass rejections (expect the 10-12 intra-frame-stereo
     "smell" to be caught explicitly now);
   - sequential VIO-EM rejections at the two residual teleport
     timestamps (`858015→858515`, `864515→865015→865515`);
   - registered-frame count; if VIO-EM thresholds (15° rot / 30°
     trans-direction) are too tight at this capture's ~12m drift,
     either retighten or accept the catch is real.
5. **Update `docker/reconstructor/SPEC.md`** (prose-only commit per
   CLAUDE.md spec-first rule) to describe the hand-rolled
   verification, the EM + rig phase split, and the new
   `VERIFYING_GEOMETRY_EM` / `VERIFYING_GEOMETRY_RIG` publisher
   phases if added. Roll up the still-stale lines 56, 60, 164 in
   the same pass.
6. **Fix the stale `--sequential-window` help text** in
   `scripts/sweep_postprocess.py` and `scripts/displacement_check.py`
   (carried over from the prior memory's queue — not landed yet).
