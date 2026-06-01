---
updated: 2026-06-01
---

# Stock pycolmap rig verification + post-pass VIO-EM filter on capture 4bd303f1

## Goal

Get a clean reconstruction on the test capture
`4bd303f1-d6c4-4867-8e35-f788c810ce26` — registered-frame count near
the full 222 while killing two known sequential teleports — using
stock `pycolmap.geometric_verification(rig_verification=True)` plus a
post-verification VIO-EM consistency check, with the verification
RANSAC tuned aggressively enough to be acceptable wall-clock and the
VIO-EM thresholds set against the actual disagreement distribution
rather than a guess.

Two persistent teleports in baseline output (`displacement-check`):

```
1780106858515 → 1780106859015   ~Δt=0.5s   recon=2.13m  prior=0.26m
1780106864515 → 1780106865515   ~Δt=1.0s   recon=3.33m  prior=1.03m
```

Stock `geometric_verification(rig_verification=True)` alone on this
capture registers `108-122 / 222` depending on RANSAC settings — the
failure mode the rewrite-era work was trying to fix.

## State

This is the chapter **after** the hand-rolled-rig-verification chapter
captured in `.pulsar/memories/geometric-verification-rewrite.md`. That
rewrite landed (`f2fce95d` through `8529515b`) but the bin-back logic
produced implausibly clean output (0 rejected, 0 empty constituents,
ran almost instantly) and the user judged it broken. Everything from
that chapter has been reverted.

- **Reverted to single-file `colmap.py`.** Commit `39f8a72c` rolls
  back the multi-file split and the hand-rolled EM + rig phases.
  Commit `7dd0ef22` calls stock
  `pycolmap.geometric_verification(rig_verification=True)` once and
  trusts the C++ implementation for both passes. The
  `verifying_rig_geometry` enum value, the EM/rig dataclasses, the
  custom `ThreadPoolExecutor`, the bin-back code — all gone.
- **`use_existing_relative_pose` experiment failed.** Commits
  `2d5cbb24` (seed `two_view_geometries` from VIO priors and enable
  `use_existing_relative_pose=True`) and revert `0d1401f9` bracket
  the finding: the flag only short-circuits the EM pass, not the
  rig pass. Rig pass is where the wall-clock lives, so net speedup
  on this capture is **zero**. Not worth carrying.
- **RANSAC tightened, twice.**
  - `59b4fcd5`: `max_num_trials=1000, confidence=0.99`. Verification
    runs ~6 min. Registration `218/222`. Long-range track count drops
    81% vs no rig pass. Teleport speeds drop from
    `6.49 m/s` / `7.03 m/s` to `4.27 m/s` / `3.32 m/s` — but the
    two teleports still appear in `displacement-check`.
  - `2dfedde0`: `max_num_trials=500, confidence=0.95`. Verification
    ~3 min. Combined with the **broken-math** VIO-EM check this
    collapsed the map to 80/222 (rotation rejection 85%, translation
    rejection 81%) — see VIO-EM bug below; the collapse was the
    bug, not the RANSAC setting. With VIO-EM disabled, `500/0.95`
    registers 108/222 and runs the rig pass in ~2 min.
- **VIO-EM math bug found and fixed.** Commit `0672dca9` —
  `FramePose.rotation` was being consumed as `rig_from_world` but
  the Unity/ZED capture writes `world_from_rig`. The composed
  `cam2_from_cam1` was inverted, so 80%+ of pairs failed the
  agreement check on a sign flip. This resolves the hypothesis (a)
  coordinate-convention question in the previous version of this
  memory.
- **Post-verification VIO-EM check structurally in place.** Commit
  `065fdf36` reinstated `_apply_vio_em_check` in `colmap.py` after
  the stock `geometric_verification` call. Original thresholds:
  - `pair_vio_em_max_rotation_disagreement_deg = 15`
  - `pair_vio_em_max_translation_direction_deg = 30`
  - `pair_vio_em_min_baseline_m = 0.3`
  Even with the math fix, the 30° translation threshold is too
  tight (see diagnostic distribution below) — the filter is wired
  correctly but the thresholds need to be set against measured
  disagreement.
- **Progress reporting through `geometric_verification` works now.**
  `cf2e3ce2` polls `two_view_geometries` row count via a read-only
  SQLite connection (WAL mode makes the concurrent read safe).
  `f01b0f2e` moves the poller into a `subprocess.Popen` child
  because the in-process daemon thread was GIL-blocked by the C++
  call. `6e74fa78` switches the metric from `COUNT(*)` (which
  saturates after the fast EM pass) to
  `COUNT(*) WHERE config = 9` — zero at start, grows monotonically
  through the rig pass, plateaus at the rig-validated count.
  Confirmed live growth `0 → 185 → 369 → … → 3928` per 5 s.
- **Three-way per-pair diagnostic landed.** Commit `06a07742` adds
  `scripts/src/scripts/two_view_diagnostic.py` and a `uv run`
  entry. For each strictly sequential same-camera pair (no spatial
  window, no loop closures) it computes `cam_b_from_cam_a` three
  ways:
  1. **VIO**: from `frames.csv` + per-camera extrinsics.
  2. **Verification**: from `two_view_geometries.cam2_from_cam1`
     in `database.db` (N/A for `config = UNDEFINED`).
  3. **Final reconstruction**: from each image's pose in
     `images.txt` (N/A when either frame is unregistered).
  Outputs rotation + translation-direction disagreement for all
  three pairings (1↔2, 1↔3, 2↔3) plus distribution stats.
- **Diagnostic results on capture 4bd303f1 (no-VIO-EM run
  `053156e6…`):**

  | comparison | median | p95 | p99 | max |
  |---|---|---|---|---|
  | 1↔2 rotation (VIO vs verif) | 0.56° | 7.67° | 14.46° | 18.34° |
  | 1↔2 translation (VIO vs verif) | 4.59° | 59.20° | 93.21° | 103.02° |
  | 1↔3 rotation (VIO vs recon) | 0.56° | 11.31° | 88.15° | 88.71° |
  | 1↔3 translation (VIO vs recon) | 4.79° | 76.71° | 115.84° | 125.61° |
  | 2↔3 rotation (verif vs recon) | 0.14° | 1.04° | 84.30° | 90.86° |
  | 2↔3 translation (verif vs recon) | 0.73° | 6.55° | 139.90° | 169.35° |

  Rotation is tight everywhere; translation-direction noise is
  large in the p95-p99 tail. The natural distribution explains why
  the original 30° translation threshold killed half the
  CALIBRATED_RIG pairs even on a healthy capture.
- **Three regimes from the diagnostic:**
  1. **"Verif wrong, BA trusted it"** — 1↔2 large, 1↔3 large,
     2↔3 *small*. Examples: `829515→830014` (VIO↔verif 0.4°/98°,
     verif↔recon 0.2°/1.2°), `874015→874515` (verif↔recon
     0.06°/0.09°). These are exactly the pairs VIO-EM should
     reject.
  2. **"Bad pair is elsewhere"** — 1↔2 small, 1↔3 large.
     Verification got this pair right; BA dragged the frames into
     bad poses via chains through other pairs. VIO-EM on this
     pair won't fix it.
  3. **"Tail noise"** — large 1↔2 translation but reconstruction
     still placed frames sensibly. Killing these pairs throws
     away useful constraints.
- **Two known teleports — their per-pair anatomy:**
  - `858515 → 859015`: `config = 9` (CALIBRATED_RIG, was used).
    VIO↔verif rotation 4.09°, translation **56.06°**. Recon
    baseline 0.324 m vs VIO 0.261 m. This is a Regime-1 pair —
    exactly what a VIO-EM check is designed to catch, and a
    translation threshold ≥ 60° lets it survive while a 30°
    threshold would have killed it together with half the map.
  - `864515 → 865515`: `config = 0` (UNDEFINED) — already
    rejected by `geometric_verification` itself. Both frames
    still got registered via chains through *other* pairs.
    VIO-EM on this pair is a no-op; the teleport is Regime 2,
    fixable only by killing whichever upstream pair gave BA
    enough confidence to drag these frames apart.
- **Threshold proposal under evaluation: rotation 25°,
  translation 60°.** Sits above the typical p95 of healthy pairs
  (so doesn't kill the noise tail) but cleanly catches Regime 1
  pairs like teleport 1 (`56°` survives the noise-tail threshold,
  but a tighter Regime-1-specific check would still flag it via
  the verif↔recon agreement signal). User asked: "run both and
  compare" — meaning current `15°/30°` vs proposed `25°/60°` — and
  was interrupted before that ran.
- **Live-DB introspection via SQLite WAL works** for ad-hoc checks
  while verification is running:
  ```
  docker exec -it <recon container> python3 -c \
    "import sqlite3; \
     c = sqlite3.connect('file:/tmp/reconstruction/database.db?mode=ro', uri=True); \
     print(c.execute('SELECT config, COUNT(*) FROM two_view_geometries GROUP BY config').fetchall())"
  ```
  `config = 9` is `CALIBRATED_RIG` — the rig-pass rewrite by COLMAP's
  C++ `EstimateRigTwoViewGeometries`. Validated count on this
  capture: ~3909-3928 pairs.
- **Pair generation default on this capture: 7999 pairs.**
  Breakdown with `spatial_neighbor_radius_m = 0`,
  `retrieval_top_k = 0`:
  ```
  intra_frame_stereo = 111
  sequential         = 7888
  total              = 7999
  ```
  Roughly half (~4090) end up `UNDEFINED` after verification; the
  other half (~3909) become `CALIBRATED_RIG`.
- **`config = 9` translation IS metric.** Unlike `CALIBRATED`
  (essential-matrix decomposition, unit-norm by convention) and
  `UNCALIBRATED` (fundamental-matrix, also up-to-scale), the rig
  pass uses GR6P (generalized relative pose) on the multi-camera
  rig and the known stereo baseline anchors true scale. So for the
  ~3909 CALIBRATED_RIG pairs the VIO-EM check can compare
  *magnitudes* as well as directions if we want — translation is
  in meters.
- **Pair generation source precedence is fixed.** In
  `pairs.py:generate_image_pairs` the order is
  `intra_frame_stereo > sequential > spatial > retrieval`. A pair
  promoted by an earlier source isn't re-emitted by a later one.
- **The incremental mapper is a pure reader of
  `two_view_geometries`.** Any pair with `config != UNDEFINED`
  gets used; the mapper doesn't filter further. Writing an empty
  `TwoViewGeometry` via `update_two_view_geometry` (commit
  `e5dc4414`) is how the VIO-EM check rejects a pair — the row
  stays, the geometry goes to `UNDEFINED` and the mapper ignores
  it.

## Decisions

- **Stock `pycolmap.geometric_verification(rig_verification=True)`
  is the right shape.** The hand-roll experiment proved both that
  the C++ rig pass is non-trivial to mirror correctly in Python
  (bin-back was wrong — produced 0 rejections, ran instantly,
  obviously broken) and that we have no GIL-release problem
  worth solving — the stock call is acceptable wall-clock once
  RANSAC is tightened. Progress reporting via SQLite-row-count
  subprocess closes the previously-blocking "silent C++ block"
  argument.
- **`use_existing_relative_pose` does not help.** Documented dead
  end. Removed. Reason: only EM pass short-circuits; rig pass is
  the bottleneck.
- **RANSAC tuning sits at `500 / 0.95`.** Latest commit `2dfedde0`.
  Rig pass kills most outliers on its own at this setting and the
  ~3 min wall-clock is acceptable.
- **VIO-EM check stays.** The math bug is fixed; the structural
  place is correct (post-verification, on the survivor pool).
  Threshold tuning is the remaining live question.
- **Bin-back rig-rewrite is out.** COLMAP's C++ does the rewrite
  itself; `config = 9` shows it. We are not in the rewrite
  business anymore.

## Open questions

- **At what thresholds does VIO-EM actually catch Regime-1
  teleports without killing the p95 noise tail?** Diagnostic
  numbers suggest rotation ≥ 25°, translation ≥ 60° is the
  natural floor for "anomalous" given this capture's distribution.
  Need to A/B the current `15°/30°` and proposed `25°/60°` and
  measure both teleport survival and overall registration count.
  This is the immediate next experiment.
- **Can we exploit the metric translation magnitude on
  `config = 9` pairs?** Currently the check only uses
  translation direction. The CALIBRATED_RIG pairs carry real
  baselines in meters; comparing recon vs VIO magnitude (with a
  configurable tolerance, e.g. 2×) would catch pairs where the
  direction agrees but the magnitude is implausibly large — a
  potentially cleaner signal than direction-angle for the kind
  of "drift inside a stationary moment" failure.
- **Teleport 2 (`864515→865515`) is Regime 2 — VIO-EM cannot
  catch it.** It will need a different mechanism: identify and
  reject the upstream pair(s) that let BA drag these
  already-unverified frames apart. Diagnostic columns 2↔3 large
  with 1↔2 small flag candidates.
- **Is `500 / 0.95` actually the right RANSAC point?**
  `1000 / 0.99` doubles wall-clock to ~6 min but pushed
  registration to `218/222`. With a working VIO-EM at sensible
  thresholds, the tighter RANSAC may be the right place to land.

## Key files

- `docker/reconstructor/src/reconstructor/colmap.py` — single-file
  pipeline. Contains the stock `geometric_verification(...)` call,
  the SQLite-subprocess progress poller (spawned around the
  `geometric_verification` call), and `_apply_vio_em_check` on
  the survivor pool.
- `docker/reconstructor/src/reconstructor/options_builder.py` —
  RANSAC tuning (`max_num_trials=500, confidence=0.95`) and the
  `pair_vio_essential_matrix_options` factory that wires the
  VIO-EM thresholds through.
- `docker/reconstructor/src/reconstructor/rig.py` —
  `FramePose.rotation` now correctly consumed as `world_from_rig`
  per commit `0672dca9`.
- `docker/reconstructor/src/reconstructor/pairs.py` —
  `generate_image_pairs` with source precedence
  `intra_frame_stereo > sequential > spatial > retrieval`.
- `packages/python/core/src/core/reconstruction_options.py` —
  `pair_vio_em_max_rotation_disagreement_deg`,
  `pair_vio_em_max_translation_direction_deg`,
  `pair_vio_em_min_baseline_m` field definitions. Defaults still
  at `15° / 30° / 0.3 m`; the threshold-tuning experiment will
  set these as queue overrides first, then promote winners.
- `scripts/src/scripts/two_view_diagnostic.py` — three-way
  per-pair diagnostic (VIO vs verification vs final reconstruction)
  used to characterize the disagreement distribution and pick
  thresholds against it. Run via `uv run two-view-diagnostic`.
- `scripts/src/scripts/displacement_check.py` — teleport diagnostic.
  Run after reconstruction; emits `Δt`, `recon`, `prior`, `speed`.
- `.pulsar/memories/geometric-verification-rewrite.md` — **prior
  chapter, do not edit.** Captures the hand-rolled rig + bin-back
  experiment that landed and was reverted.
- `.pulsar/memories/reconstruction-aliasing-failure-modes.md` —
  long-form context upstream of both chapters.

## Pending threads

1. **Run the `15°/30°` vs `25°/60°` A/B on capture 4bd303f1**
   ("run both and compare" — user was interrupted before this).
   Compare registered frames, both teleports' survival in
   `displacement-check`, and CALIBRATED_RIG kill count.
2. **Add a magnitude check on `config = 9` pairs.** Compare recon
   translation magnitude to VIO translation magnitude with a
   ratio threshold (e.g. reject if ratio > 2×). Wire as a new
   `pair_vio_em_max_translation_magnitude_ratio` option. Test on
   teleport 1 — it should fire (recon 0.324 m vs VIO 0.261 m is
   only 24% off, so a 2× threshold wouldn't catch it on
   magnitude; teleport 1 is a direction-only kill).
3. **Investigate Regime-2 teleport 2.** Identify which upstream
   pair gave BA enough confidence to place these two
   unverified-against-each-other frames in implausibly different
   poses. The 2↔3 column of the diagnostic is the entry point.
4. **Re-evaluate RANSAC tuning** once VIO-EM thresholds are
   settled. `500/0.95` and `1000/0.99` both on the table;
   `218/222` at `1000/0.99` is still the headline number to beat.
5. **Update `docker/reconstructor/SPEC.md`** (prose-only commit
   per spec-first rule) to capture the post-revert pipeline shape:
   stock `geometric_verification` + post-pass VIO-EM, SQLite
   subprocess progress poller, no hand-rolled verification phases.
   Pending across this memory and the prior chapter.
