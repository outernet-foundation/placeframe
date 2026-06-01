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
RANSAC tuned aggressively enough to be acceptable wall-clock.

The two persistent teleports in baseline output (`displacement-check`):

```
1780106858515 → 1780106859015   ~Δt=0.5s   recon ≫ prior
1780106864515 → 1780106865015   ~Δt=0.5s   recon ≫ prior
1780106865015 → 1780106865515   ~Δt=0.5s   recon ≫ prior
```

Stock `geometric_verification(rig_verification=True)` alone on this
capture registers `122 / 222` — the failure mode the rewrite-era work
was trying to fix.

## State

This is the chapter **after** the hand-rolled-rig-verification chapter
captured in `.pulsar/memories/geometric-verification-rewrite.md`. That
rewrite landed (`f2fce95d` through `8529515b`) but the bin-back logic
produced implausibly clean output and the user judged it broken.
Everything from that chapter has been reverted.

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
  - `2dfedde0` (current HEAD-ish): `max_num_trials=500, confidence=0.95`.
    Verification ~3 min. Combined with VIO-EM check this **collapses
    the map to 42/222** — rotation rejection 85%, translation
    rejection 81%. Same failure mode as the original hand-roll era.
    The `500/0.95` setting is not viable while VIO-EM is on.
- **Post-verification VIO-EM check added back.** Commit `065fdf36`
  reinstates `_apply_vio_em_check` in `colmap.py` after the stock
  `geometric_verification` call. Thresholds carried over from the
  earlier hand-roll era:
  - `pair_vio_em_max_rotation_disagreement_deg = 15`
  - `pair_vio_em_max_translation_direction_deg = 30`
  - `pair_vio_em_min_baseline_m = 0.3`
  These are far too tight for the VIO drift profile on this
  capture — kills the run as soon as RANSAC tightens.
- **Live-DB introspection via SQLite WAL works.** While verification
  is running, peek at `two_view_geometries.config` counts without
  blocking COLMAP:
  ```
  docker exec -it <recon container> python3 -c \
    "import sqlite3; \
     c = sqlite3.connect('file:/tmp/reconstruction/database.db?mode=ro', uri=True); \
     print(c.execute('SELECT config, COUNT(*) FROM two_view_geometries GROUP BY config').fetchall())"
  ```
  `config = 9` is `CALIBRATED_RIG` — the rig-pass rewrite by COLMAP's
  C++ `EstimateRigTwoViewGeometries` (the very logic the failed
  hand-rolled bin-back was trying to mirror).
- **Frames.csv on this capture is 8-col.** Columns:
  `timestamp, tx, ty, tz, qx, qy, qz, qw`. Full VIO pose including
  rotation. Earlier session belief that ZED capture writes
  gravity-only VIO was **wrong** — the rotation prior is real.
  Means VIO-EM has a meaningful rotation oracle to compare against,
  so a 90% rejection rate is not "no signal to use" — it's a
  genuine mismatch somewhere.
- **Default pair generation on this capture: 7999 pairs.**
  Breakdown with default options
  (`spatial_neighbor_radius_m = 0`, `retrieval_top_k = 0`):
  ```
  intra_frame_stereo = 111
  sequential         = 7888
  total              = 7999
  ```
  The earlier cloned-options regime (`spatial=25, retrieval=20`)
  yielded 15635 pairs — much heavier verification load, not used now.
- **Pair generation source precedence is fixed.** In
  `pairs.py:generate_image_pairs` the order is
  `intra_frame_stereo > sequential > spatial > retrieval`. A pair
  promoted by an earlier source isn't re-emitted by a later one.
  The drift-budget gate applies post-source.

## Decisions

- **Stock `pycolmap.geometric_verification(rig_verification=True)`
  is the right shape.** The hand-roll experiment proved both that
  the C++ rig pass is non-trivial to mirror correctly in Python
  (bin-back was wrong) and that we have no GIL-release problem
  worth solving — the stock call is acceptable wall-clock once
  RANSAC is tightened.
- **`use_existing_relative_pose` does not help.** Documented dead
  end. Removed. Reason: only EM pass short-circuits; rig pass is
  the bottleneck.
- **RANSAC tuning sits at `500 / 0.95`.** Latest commit `2dfedde0`.
  Acceptable on its own (rig pass kills most outliers); broken
  when combined with current VIO-EM thresholds.
- **VIO-EM check stays in the tree but the thresholds are wrong.**
  The check is structurally where we want it (post-verification,
  on the survivor pool); the empirical rejection rate at
  `15° / 30° / 0.3 m` is the smoking gun that something is
  geometrically off, not that the thresholds need a quick widen.
- **Bin-back rig-rewrite is out.** Now that we call stock
  `geometric_verification` and inspect via SQLite, `config = 9`
  shows COLMAP is doing the rewrite itself. We are not in the
  rewrite business anymore.

## Open questions

- **Why does VIO-EM reject 80%+ of pairs at 15° / 30°?** The most
  load-bearing question. Three hypotheses to investigate in a
  fresh session, ordered by likelihood and cost to test:
  1. **Coordinate-convention mismatch (most likely, cheapest).**
     `FramePose.rotation` in `rig.py` is *assumed* to be
     `rig_from_world`. The ZED capture pipeline may actually
     write `world_from_rig`, or some other convention.
     Compose two adjacent-frame VIO transforms by hand on this
     capture and see what rotation magnitude comes out vs.
     what device motion over ~0.5 s would imply. If composed
     `rig2_from_rig1` is huge between two physically-still frames,
     the convention is inverted.
  2. **Accumulated VIO drift legitimately > 15° rotation over the
     capture duration.** Possible but doesn't fit the 80%+
     headline rate — drift accumulates over time, so the
     rejection rate would skew toward late-vs-early pairs, not
     uniform. Worth plotting rejection rate vs. pair timestamp
     separation to falsify.
  3. **`cam2_from_cam1` composition in `_apply_vio_em_check`
     correct but sign-flipped somewhere downstream** (e.g. the
     comparison takes the wrong angle or compares against the
     conjugate). Lower-probability because the same code shape
     ran inline during the hand-roll era and produced the same
     ~85% rejection rate — the bug, if it's a bug, predates the
     revert.

- **Do the two teleports survive a working VIO-EM check, or are
  they only catchable by rig-aware logic?** Answerable once
  hypothesis (a) is resolved.

- **Is `500 / 0.95` actually the right RANSAC point, or would
  `1000 / 0.99` (218/222) be preferable once VIO-EM is fixed?**
  `1000 / 0.99` doubled wall-clock to ~6 min but preserved
  registration. The choice depends on whether the tighter
  setting is genuinely catching teleport-relevant pairs or
  just losing matches.

## Key files

- `docker/reconstructor/src/reconstructor/colmap.py` — single-file
  pipeline. Contains the stock `geometric_verification(...)` call
  near line 140 and `_apply_vio_em_check` near line 298. This is
  where the VIO-EM threshold investigation lives.
- `docker/reconstructor/src/reconstructor/options_builder.py` —
  RANSAC tuning at lines 61-62 (`max_num_trials=500, confidence=0.95`).
  `pair_vio_essential_matrix_options` factory at line 115 wires
  the thresholds through.
- `docker/reconstructor/src/reconstructor/rig.py` —
  `FramePose.rotation` is the consumer of the VIO quaternion. This
  is where the coordinate-convention assumption is encoded; check
  here first when testing hypothesis (a).
- `docker/reconstructor/src/reconstructor/pairs.py` —
  `generate_image_pairs` with source precedence
  `intra_frame_stereo > sequential > spatial > retrieval`.
- `packages/python/core/src/core/reconstruction_options.py` —
  `pair_vio_em_max_rotation_disagreement_deg`,
  `pair_vio_em_max_translation_direction_deg`,
  `pair_vio_em_min_baseline_m` field definitions (lines ~121-129).
- `scripts/src/scripts/displacement_check.py` — teleport diagnostic.
  Run after reconstruction; emits `Δt`, `recon`, `prior`, `speed`.
- `/tmp/queue_recon.py` — session-local queue helper using default
  `ReconstructionOptions()`. Not in repo; re-derive if needed.
- `.pulsar/memories/geometric-verification-rewrite.md` — **prior
  chapter, do not edit.** Captures the hand-rolled rig + bin-back
  experiment that landed and was then reverted. Read for the
  C++ `EstimateRigTwoViewGeometries` reference and the
  bin-back-was-wrong post-mortem; ignore the "still pending"
  threads, all of which are obsoleted by the revert.
- `.pulsar/memories/reconstruction-aliasing-failure-modes.md` —
  long-form context upstream of both chapters.

## Pending threads

1. **Investigate hypothesis (a) first.** Compose two adjacent-frame
   VIO transforms by hand on capture `4bd303f1` using
   `FramePose.rotation`'s current convention. If the magnitude
   contradicts plausible device motion, the convention is
   inverted — fix `rig.py` and rerun. This is the cheapest test
   and the most likely culprit.
2. **If (a) is clean, falsify (b)** by plotting VIO-EM rejection
   rate vs. timestamp separation across the pair list. Uniform
   rejection rate falsifies drift accumulation.
3. **If (a) and (b) are both clean, audit (c)** by logging the
   actual `cos_rotation` / `cos_translation_direction` distributions
   out of `_apply_vio_em_check` and choosing thresholds empirically.
4. **Decide VIO-EM fate after (1)-(3).** If a fixed VIO-EM at
   plausible thresholds catches the two teleports, keep it. If
   not, drop it permanently and chase the teleports via
   rig-aware logic only.
5. **Re-evaluate RANSAC tuning** once VIO-EM is either fixed or
   removed. `500/0.95` and `1000/0.99` are both on the table;
   `218/222` at `1000/0.99` is the headline number to beat.
6. **Update `docker/reconstructor/SPEC.md`** (prose-only commit per
   spec-first rule) to capture the post-revert pipeline shape:
   stock `geometric_verification` + optional post-pass VIO-EM,
   no hand-rolled phases. Pending across both this memory and
   the prior chapter.
