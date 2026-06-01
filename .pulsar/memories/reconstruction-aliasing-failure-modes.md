---
updated: 2026-06-01
---

## What's new (2026-06-01, late-night: queued items shipped)

The three "Queued for next session" items from the previous entry shipped
in commit `418c7c18` ("Switch to geometric_verification with rig pass,
add VIO-EM check, metric sequential window"), plus codegen in `34b17489`.

- **Rig-aware verification wired back via `pycolmap.geometric_verification`
  with DB polling for progress.** `_verify_two_view_geometries` no longer
  hand-rolls a per-pair `estimate_two_view_geometry` threadpool; it now
  spawns `geometric_verification(database_path,
  verifier_options=GeometricVerifierOptions(rig_verification=True),
  pairing_options=ExistingMatchedPairingOptions(),
  two_view_geometry_options=...)` on a worker thread and ticks the
  progress publisher from a separate read-only `sqlite3` connection
  polling `SELECT COUNT(*) FROM two_view_geometries` every ~1s. The
  outer pipeline (`run_colmap_pipeline_with_vio_check`) is restructured
  into staged `with Database.open(...)` blocks so the file is closed
  during each verification call. This restores the rig-aware GR6P-RANSAC
  pass that we lost in `ddcb5033`. One localized `# pyright: ignore` at
  the import line for the unparameterized `os.PathLike` stub — matches
  the existing `Database.open` precedent.
- **Pair-time VIO-vs-essential-matrix check for sequential pairs only.**
  New `_check_sequential_pairs_against_vio` runs after phase-1
  verification (skipped for phase-2 retrieval, where VIO drift across a
  loop closure can legitimately disagree). For each `SEQUENTIAL` pair
  with VIO rotation present, it composes `vio_cam_b_from_cam_a` from rig
  pose + per-camera `sensor_from_rig`, compares rotation (trace) and
  translation direction (dot-product) against the essential matrix, and
  deletes failing `two_view_geometries` rows. New `ReconstructionOptions`
  fields: `pair_vio_em_max_rotation_disagreement_deg` (default 15°),
  `pair_vio_em_max_translation_direction_deg` (default 30°),
  `pair_vio_em_min_baseline_m` (default 0.3 m). To enable this,
  `FramePose` now retains the quaternion from 7-column `frames.csv`
  (previously dropped) with OpenCV-from-Unity basis conjugation; ZED
  captures (6-column gravity-only) skip the check silently.
- **Sequential window is now metric.** `sequential_window: int` (count)
  → `sequential_window_m: float` (metres of straight-line VIO
  displacement), default **3.0 m**. Each frame *i* pairs with every
  later frame *j* whose VIO displacement from *i* is ≤ the budget;
  spatial dedup updated to use the actual paired-partner set instead of
  temporal-index distance.
- **Retrieval is now off by default** (was already disabled before this
  session as part of the strip-to-bare work). Last toggle of the
  session: "change the options to completely disable retrieval, and
  rerun codegen. then run a reconstruction in that state."
- **No end-to-end reconstruction run with these three changes yet.**
  Preflight pieces that ran cleanly: `ruff check`, `basedpyright`
  (strict), `pytest docker/reconstructor/tests/`, `deptry-check`,
  `generate-clients --project docker/api`. The "test this on
  `4bd303f1`" work is the immediate next step.
- **SPEC.md is stale.** `docker/reconstructor/SPEC.md` lines 56, 60, 164
  still describe the old fixed-count sequential window, the per-pair
  `estimate_two_view_geometry` loop, and the absence of a VIO-EM check.
  Per CLAUDE.md's spec-first rule the spec update should land before
  any further code change in those areas; not yet done. Also stale:
  `scripts/sweep_postprocess.py` and `scripts/displacement_check.py`
  keep their own `--sequential-window` typer arg whose help text now
  references a reconstruction option that no longer exists by that
  name.

## Queued for next session (post-compact)

Both deferred to next session — the "Queued" items from the prior entry
just shipped; these replace them.

1. **Run the three new changes end-to-end on `4bd303f1`.** That's the
   immediate validation: confirm rig verification fires on the
   intra-frame-stereo pairs it used to miss, the VIO-EM check trims the
   two residual sequential-driven teleports at `858015→858515` and
   `864515→865015→865515`, and the metric `sequential_window_m=3.0`
   produces sane coverage. Track per-source rejection counts. The
   capture has ~12 m VIO drift; if the VIO-EM check thresholds (15°
   rot / 30° trans-direction) end up too tight at this drift level,
   either retighten the threshold or accept that the catch is real and
   the cost is registered-frame count.
2. **Update `docker/reconstructor/SPEC.md`** (prose-only commit, per
   CLAUDE.md spec-first / prose-and-code-separate rules) to describe
   the new architecture: `geometric_verification` + DB-row polling,
   VIO-vs-essential-matrix sequential check, metric sequential window.
   Lines 56, 60, 164 are the stale spots.
3. **Fix the stale `--sequential-window` help text** in
   `scripts/sweep_postprocess.py` and `scripts/displacement_check.py`.
   The scripts can keep their own keyframe-index-distance threshold (it
   means something different from the reconstructor option now), but
   the help text should stop referencing a reconstruction option that
   has been renamed.

## What's new (2026-06-01, strip-to-bare + lost rig verification)

- **Strip-to-bare runs on `4bd303f1` at `sequential_window=10`** (a tighter
  window than the historical 20) under two-phase ingest. Two new runs:
  - `cb6a77b1-050f-48ca-b279-28912dea2925` — window=10, retrieval ON,
    everything else stripped. 120 / 220 frames mapped, worst teleport
    4.28 m/s at `858015→858515`, second-worst 3.37 m/s. 2 long-range
    tracks. Pose-graph rejections (sequential): 1,026.
  - `6f5a03ee-f31b-41b6-8876-896606af5585` — window=10, retrieval OFF,
    same otherwise. 122 / 220 frames, worst teleport **6.96 m/s** at
    `864515→865015`, 2nd-worst 4.23 m/s. **0 long-range tracks.**
    Pose-graph rejections (sequential): 398.
- **At window=10, retrieval is marginally *defensive*, not contaminating.**
  Worst teleport got *worse* (4.28 → 6.96 m/s) when retrieval was
  removed. Frame 78 (`1780106865015`, the dark blurry hallway) failed
  to register at all in `cb6a77b1` (retrieval-on filtered it out via
  lack of supporting evidence) but in `6f5a03ee` it registered at a
  wrong position 3.48 m off from frame 77. This is the inverse of the
  window=20 picture, where retrieval *amplified* aliasing
  catastrophically. The interaction is:
  - window=20 + retrieval ON: 25.83 m/s (catastrophic)
  - window=20 + retrieval OFF: 6.86 m/s (sequential-driven)
  - window=10 + retrieval ON: 4.28 m/s, 120 frames
  - window=10 + retrieval OFF: 6.96 m/s, 122 frames
- **The window=10 residual teleports are pure Phase-1 sequential
  failures.** Same two timestamp regions regardless of retrieval state:
  `858015 → 858515` (densely connected, accumulated misregistration
  around frame 67) and `864515 → 865015 → 865515` (thin connectivity,
  fast motion, frame 78 the dark blurry frame either drops out or lands
  wrong). These survive everything the current stack defends against.
- **Rig-aware verification was silently lost in `ddcb5033`.** The OLD
  pipeline (commit `bcf0ecec`) called
  `match_spatial(database_path=..., matching_options=options.feature_matching_options(), verification_options=options.two_view_geometry_options())`
  with `feature_matching_options().rig_verification = True` via a
  `ReconstructionOptions.rig_verification` field (since culled in
  `0b3a4aa0`). Commit `ddcb5033` ("Verify two-view geometry per-pair so
  the phase reports progress") switched to a per-pair
  `pycolmap._core.estimate_two_view_geometry(...)` threadpool to get
  per-pair progress callbacks, and the rig flag fell on the floor —
  `estimate_two_view_geometry` doesn't accept it. **The 10–12
  intra-frame-stereo pose-graph rejections we've been calling a
  "smell" are not calibration drift — they are stereo pairs whose
  essential matrix doesn't satisfy the fixed rig baseline making it
  through unfiltered.**
- **The rig pass is more powerful than just stereo.** Pair generation
  (`pairs.py:109-110`) emits all cross-camera combos: every sequential
  (or retrieval, or spatial) frame-pair between two multi-camera
  rig snapshots produces 4 image-pairs (c0-c0, c0-c1, c1-c0, c1-c1).
  COLMAP's rig pass (second pass on top of normal verification) scans
  for frame-pairs with `num_image_pairs > 1`, pools all four
  correspondences, and jointly fits one `rig2_from_rig1` via a
  generalized-camera RANSAC (GR6P, `EstimateGeneralizedRelativePose`).
  For our rig-locked stereo case `rig2_from_rig1` is constrained to
  the rig calibration and each pair's `cam2_from_cam1` is *synthesized
  analytically* from `sensor_from_rig` rather than re-fit; inlier mask
  comes from the joint solve; pair config is overwritten to
  `CALIBRATED_RIG` (config 8). This **catches perceptual aliasing
  where one camera's matches lie and the other's don't** — exactly
  the framed-picture / cubicle surface, and it applies to retrieval
  and spatial frame-pairs too, not just stereo.
- **Stock entry point exists and is a strict replacement for
  `match_spatial`.** `pycolmap.geometric_verification(database_path,
  verifier_options=GeometricVerifierOptions(rig_verification=True),
  pairing_options=ExistingMatchedPairingOptions(),
  two_view_geometry_options=...)` does exactly what `match_spatial`
  did when matches were already in the DB: short-circuits already-
  verified pairs (`cache->ExistsInlierMatches`), then runs the rig
  pass on top. We can keep the per-pair threadpool exactly as-is and
  append one whole-DB call after Phase 1 to layer the rig pass on top
  (Phase 2 retrieval pairs are all single-camera, so rig pass is a
  no-op there).
- **Progress callback recovery via DB-row polling.** The blocker that
  originally drove the per-pair fork was no per-pair progress on
  `match_spatial`. Path forward without re-forking: spawn
  `geometric_verification` in a background thread, poll
  `SELECT COUNT(*) FROM two_view_geometries WHERE config = 8` against
  a pre-counted expected (number of multi-image frame-pairs in our
  generated pair set), publish progress every ~200 ms. The rig pass
  commits per frame-pair on COLMAP's internal threadpool so the count
  grows in real time. SQLite concurrent reads don't block writes
  regardless of journal mode. `ExistingMatchedPairingOptions` only
  exposes `batch_size`, no `pair_ids` filter — partitioning externally
  isn't doable (it would silently disable rig verification by hiding
  multi-image frame-pairs from each partition).
- **New check identified: pair-time VIO-vs-essential-matrix
  consistency.** No current check compares the essential-matrix-implied
  relative R + t-direction against the VIO-implied relative R +
  t-direction. The drift-budget filter uses VIO but discards
  orientation (position-distance only). The pose-graph check has the
  right shape but uses the partial reconstruction as oracle, which
  can confirm its own past mistakes during early-seed contamination
  (the documented failure mode). The new check would run at the
  two-view-geometry verification stage, compute VIO's implied
  relative pose between the two frames, and reject the pair if the
  essential matrix disagrees by more than (say) 15° rotation /
  30° translation-direction. Rejects aliased pairs *before* Phase 1
  — closes the seed-phase gap the model-as-oracle pose-graph check
  structurally cannot. Cheap, monocular-OK (only needs direction,
  not metric scale), independent of the seed.
- **Per-source applicability of the new VIO-vs-essential check**
  (load-bearing):
  - **Sequential**: temporally adjacent (typical 0.5s, max ~5s within
    window=10). VIO drift over that window is sub-degree /
    sub-decimeter. Plenty of headroom below the aliasing signal
    (~15° rotation, ~30° translation direction). **Check applies
    cleanly.**
  - **Stereo** (`intra_frame_stereo`): both cameras share the same
    VIO frame at the same instant — VIO is identical for both, so
    the VIO-implied relative pose is zero. Meaningless oracle. The
    correct oracle for stereo is the rig's `sensor_from_rig` (which
    is what `rig_verification=True` provides above).
  - **Spatial** (currently disabled): VIO-position-proximate but
    temporally distant. VIO drift over minutes can be 1°+ rotation
    and meters of position. Defensible with looser thresholds if
    spatial ever turns back on; skip for now.
  - **Retrieval**: the whole *point* is to correct accumulated VIO
    drift across long loop-closure intervals. By construction VIO
    and the true relative pose disagree significantly here — that's
    the signal we want retrieval to provide. **Must skip** or the
    check kills exactly the pairs we need.

## Status note on the prior "Queued for next session" block

Both items below were the queue at the end of the earlier 2026-06-01
session. Both shipped in commit `418c7c18`. Kept verbatim for
historical context; the live queue is the post-shipment block near
the top of the file ("Queued for next session (post-compact)" under
the late-night entry).

1. **Wire rig-aware verification back via `geometric_verification(...)`
   with `rig_verification=True`.** Replace (or append after) the
   per-pair threadpool. Progress via DB-row polling on `config = 8`
   count (~30 lines, Option 1 from this session's research). Add a
   new publisher phase `VERIFYING_RIG_GEOMETRY`. The
   `ReconstructionOptions.rig_verification` field that existed in
   `bcf0ecec` and got culled in `0b3a4aa0` does not need to come
   back — just wire the flag on at the call site.
   **Status: SHIPPED in `418c7c18`.** The chosen polling cadence was
   ~1 s on a read-only sqlite3 connection. No new publisher phase
   was added — the existing phase nomenclature carried it.
2. **Add pair-time VIO-vs-essential-matrix consistency check at the
   two-view verification stage, sequential pairs only.** Thresholds
   ~15° rotation / 30° translation direction. Plumb via two new
   `ReconstructionOptions` fields. Skip stereo (covered by
   `rig_verification`), spatial (off, would need different
   thresholds), and retrieval (would kill the signal we want).
   **Status: SHIPPED in `418c7c18`.** Three options ended up plumbed,
   not two (rotation, translation-direction, *and* a baseline floor).
   Defaults: 15°, 30°, 0.3 m. `FramePose` had to be widened to retain
   the quaternion from 7-column `frames.csv` (previously dropped); ZED
   captures (6-column gravity-only) skip the check silently.

## What's new (2026-05-31, late-night session)

- **Two-phase retrieval ingest shipped** (commit `e9565dca`). Phase 1 builds a
  trajectory from `intra_frame_stereo + sequential + spatial` only — retrieval
  matches are withheld from the database entirely so they cannot poison the
  seed, dominate any PnP solve, or self-validate as a cluster. Phase 2 writes
  retrieval matches + two-view geometries into the same database, builds a
  fresh `IncrementalPipeline` against the augmented cache, binds a fresh
  `IncrementalMapper` to the best Phase 1 `Reconstruction` via
  `begin_reconstruction`, sets `fix_existing_frames=True` for
  `triangulate_image` / `complete_and_merge_tracks` / `retriangulate` so the
  retrieval correspondences cannot pull existing poses, then releases the
  fix-frames constraint for `iterative_global_refinement` to absorb the loop
  closures. The pose-graph check runs in both phases; in Phase 2 its oracle
  (the Phase 1 model) is uncontaminated by construction. **No phase-3
  straggler pass** — frames orphaned from Phase 1 stay orphaned.
- **Defaults changed** (commit `9515401a`):
  - `spatial_neighbors`: `25 → 0` (spatial pairing disabled by default)
  - `vio_check_max_disagreement_m`: `1.0 → 1e9` (vio_check effectively
    disabled by default; code path stays live, set to a finite value to
    re-enable)
- **Three A/B runs on `4bd303f1`** under the new architecture. The teleports
  on this capture are *not* primarily retrieval-driven, despite what the
  earlier framing assumed:
  - `1e5508c2` (two-phase + spatial on, vio_check off): same four teleports
    as pose-graph-only baseline (max 15.95 m/s), same exact timestamps.
    Retrieval rejections went 4→14 (Phase 2's stiff oracle catches more),
    but those weren't the dominant poison.
  - `32951227` (two-phase + spatial OFF, vio_check off): the two severe
    teleports at `1780106840515` / `841015` (~15 m/s) **eliminated**. Two
    residual ~4 m/s teleports at `…859015` and `…865515` survived. Cost:
    154/222 frames mapped (−29% coverage), long-range tracks 4643→690
    (−85%). Retrieval rejections jumped to 80 — the now-untwisted model
    surfaces aliases that were hidden when the graph was bent.
- **Spatial pairs are the dominant teleport vector on this capture, not
  retrieval.** The original framing put retrieval at the center; the data
  here say spatial-near-but-visually-aliased pairs are the primary poisoning
  source. The user's read is unambiguous: "spatial off always. it is just a
  bad idea, period." The default change makes this stick.
- **Residual ~4 m/s teleports are sequential-driven.** Survived all three
  A/B configurations at the same timestamps; not eliminated by removing
  spatial or by withholding retrieval. By elimination, they're aliased
  two-view geometries between temporally-adjacent keyframes within
  `sequential_window=20`. Open hypothesis: the sequential window is simply
  too wide — narrowing it from 20 to a smaller value may be the cheap fix.
- **Three failure modes of the pose-graph check, named.** The earlier
  memory had "early-seed contamination" alone. Two more were identified:
  - **(1) Early-seed contamination.** Alias gets baked in before the
    `min_registered_frames` gate (default 15); the check never fires on
    it, and afterward the region is "the model's truth."
  - **(2) Same-registration PnP domination.** A new frame registers via
    PnP using *all* its matches at once. If the aliased partner has more
    inliers than the correct partners (which is exactly the case for
    visually-strong aliases), the new frame's pose absorbs the alias
    *during the registration step itself*. Then the check on that frame
    flags the *correct* partners as the disagreers — the wrong side wins.
  - **(3) Co-misregistered cluster.** Two or more aliased frames register
    such that their relative poses are mutually consistent with the alias.
    Self-consistent island; from inside it every pair agrees with every
    other pair, so the check has no leverage. Tight 3-frame clusters can
    validate each other indefinitely.
  Unifying principle: the check fails whenever the model already agrees
  with the lying pair at the moment of the check. Early-seed is one way
  to get there; PnP-domination and co-registration are two others, and
  both can happen long after the 15-frame threshold.
- **vio_check non-redundancy formalized.** vio_check is the only oracle
  that *doesn't care what the model thinks* — VIO doesn't get
  contamination-propagated. It's the architecturally appropriate defense
  against all three pose-graph failure modes (subject to its own
  drift-budget limitation). Code stayed; only the default flipped.
- **Stereo rejections diagnosed.** The 4–6 `intra_frame_stereo`
  rejections per run are not a calibration smell — they're a tell that
  the model in that neighborhood is wrong, because stereo's relative
  pose is *ground truth* by rig construction. Stereo rejections mark the
  spots where contamination has already bent the model.
- **A/B methodology acknowledged as flawed.** Nine independent
  aliasing-related levers are now on by default, layered without
  isolation: drift-budget, retrieval inlier strictness, raised global
  inlier floor, match-spread, retrieval covisibility, pose-graph check,
  two-phase ingest, vio_check (now off), and retrieval-specific RANSAC.
  Every "win" we've attributed to a single patch has been measured
  against a baseline that included the rest of the stack. We do not
  know which patches are load-bearing and which are dead weight. The
  next investigation block must be a **strip-to-bare**: start from
  two-phase + spatial-off + everything-else-at-pycolmap-defaults
  (`bare`), then add patches back one at a time, on this capture *and*
  on ARFoundation-grade captures.
- **Match-spread decision deferred again.** Still in the default
  pipeline. The strip-to-bare test will tell us whether it pays off net.

## Commits this session

| commit | subject |
|---|---|
| `c242a429` | Add pair-level pose-graph consistency check |
| `7ef967c8` | Run generate-clients |
| `e9565dca` | Add two-phase retrieval ingest to incremental reconstruction |
| `9515401a` | Default spatial_neighbors to 0 and vio_check to 1e9 |
| `1f9164b3` | Run generate-clients |

## Captures referenced this session

- `1e5508c2-2b20-4cf2-9673-14ad76cf9990` — two-phase ingest + spatial on,
  vio_check off. Same teleports as pose-graph-only baseline.
- `32951227-2ed9-49ef-afb6-7e66f1d77a5c` — two-phase ingest + spatial
  off, vio_check off. The principled-but-coverage-expensive run. Severe
  teleports eliminated, residual sequential-driven teleports survive,
  long-range tracks collapse 85%.
- `cb6a77b1-050f-48ca-b279-28912dea2925` — window=10, retrieval ON,
  strip-to-bare. 120/220 frames mapped, worst teleport 4.28 m/s.
  Establishes that retrieval at window=10 is mildly defensive on this
  capture.
- `6f5a03ee-f31b-41b6-8876-896606af5585` — window=10, retrieval OFF,
  strip-to-bare. 122/220 frames mapped, worst teleport 6.96 m/s.
  Surfaces that the two residual teleports are pure Phase-1 sequential
  failures independent of retrieval.

---

# Retrieval-pair visual aliasing is the dominant reconstruction failure mode

## Goal

Document what we now know about how small ZED office captures degenerate
into BA teleports, after a 117-run parameter sweep, direct visual
inspection of the offending frames, an architectural reframing of the
problem, the shipping of three filters (drift-aware displacement,
match-spread, and a pose-graph consistency check at the model boundary),
and a follow-up reconstruction on the bad capture that produced the
first qualitative architectural win and *also* surfaced the next hard
boundary: early-seed contamination. The headline has sharpened again:
aliasing in cubicle-style environments is solved by **layered weak
signals**, not any single silver bullet — and a meaningful chunk of the
"obvious" individual signals either fail in the data regime we care
about (sub-meter VIO drift makes displacement filter inert on tiny
captures with high drift), attack the wrong shape of aliasing
(match-spread assumes concentration, but real office aliasing is
*distributed similarity* across many repeated features), or arrive too
late in the reconstruction lifecycle to defend the *seed* (pose-graph
consistency requires a model to police, so the first ~15 frames are
structurally undefended).

This memory exists because the natural next move after seeing a teleport
is to reach for one more filter or one tighter threshold. We tried those
branches. The actual path forward is to layer multiple weak signals into
a strong joint decision, *and* to ship a capture-quality gate so the
system refuses to deliver a broken map rather than ship one silently.
Future sessions should not retry single-signal "this will solve it" bets
without new information.

## The three pair sources have qualitatively different failure modes

This framing came out of first-principles reasoning during an earlier
session and survived the sweep and two filter trials. It is the
load-bearing mental model for every pair-gen decision downstream.

- **Sequential** pairs cannot be wrong by construction. Temporal
  adjacency ≈ geometric adjacency. Even on quick turns the geometric
  verifier rejects mismatches because the failure is *incoherent* (random
  scene change between adjacent frames).
- **Spatial / VIO-kNN** pairs, when wrong, are wrong because VIO drifted.
  The two frames then look at *unrelated* parts of the scene. Unrelated
  scenes don't fit a homography or essential matrix — RANSAC rejects them.
  **Spatial's errors are self-rejecting.**
- **Retrieval** pairs, when wrong, are wrong because of *visual aliasing*
  — same-looking-but-different scene. Two paintings with similar
  composition, two hallway-junction printers, an under-exposed frame
  that descriptor-collapses to overall layout. Those bad pairs have
  high inlier counts, fit coherent two-view geometries, and survive
  every per-pair threshold we can set without also killing genuine
  wide-baseline pairs. **Retrieval's errors are verification-resistant.**

The asymmetry is the whole game. RANSAC + inlier thresholds work for
sequential and spatial but break down for retrieval, not because the
thresholds are wrong but because retrieval's bad pairs are
geometrically consistent. You're filtering a needle from a haystack
where the needle is also hay.

## The properly-stated foundational mistake

Retrieval is the only pair source with *no spatial bound*. Sequential is
bounded by keyframe index (±20). Stereo is bounded by same-timestamp.
Spatial is bounded by VIO position — but we turned spatial off
(`spatial_neighbors=0`) for the original sweep, treating it as a
secondary cue rather than load-bearing. **A descriptor-only retriever
with no spatial prior will always be vulnerable to anything that
produces high descriptor similarity at the wrong place** — whether the
wrongness comes from descriptor degeneracy (Suspect A) or genuine
ambiguity (Suspect B). This is the architectural gap, not a tuning
problem.

This reframes "pose priors" into two structurally distinct roles that
must be evaluated independently:

- **Role A — BA cost terms.** Priors enter BA as `‖recon_pose −
  vio_pose‖² / σ_prior²` cost terms. Dangerous if `σ_prior` is set as if
  VIO were trustworthy when in fact VIO has 12m of drift. The original
  "priors poison BA" diagnosis was correctly identifying *this* failure
  but mis-attributed: it's not "priors poison BA," it's "priors with a
  too-tight σ poison BA." Set `σ_prior` commensurate to actual VIO
  uncertainty and they stop poisoning even with drift present.
  Additionally: COLMAP's prior mechanism uses *absolute* positions,
  which is what gets corrupted by secular drift; a *relative-displacement*
  prior formulation would survive secular drift cleanly.
- **Role B — Pair-generation / match-filtering signal.** The retriever
  can't distinguish a true loop closure from spurious aliasing using
  descriptor similarity alone. Any second signal that informs "these
  two frames are plausibly at the same place" lets you reject candidates
  that disagree. **This is what every robust system has and what
  placeframe does not.** ORB-SLAM3's motion model is this. VINS-Fusion's
  IMU integration is this. ARKit/ARCore are this. Niantic's prior pose
  is this. The form varies, but every system has something beyond
  descriptor similarity to constrain pair selection. Pure COLMAP/hloc
  skip this only because they assume curated input and accept manual
  inspection — that's not our regime.

We turned off Role A in priors-off mode (correctly, given the buggy
absolute VIO). We *also* turned off Role B (`spatial_neighbors=0`) and
didn't notice we were turning off something load-bearing. The
"foundational mistake" is properly stated as: we conflated Role A and
Role B and disabled both together. The earlier "we don't even need
priors because stereo gives metric scale" reasoning was right about
stereo's role but wrong about Role B — stereo gives intra-frame
geometry, not cross-time pair gating.

## The 117-run sweep (null result)

Capture under test: `4bd303f1-d6c4-4867-8e35-f788c810ce26` — the
worst-aliasing of the three small ZED office captures. Spatial pairs
were disabled throughout the sweep (`spatial_neighbors=0`), leaning
entirely on sequential + covisibility-filtered retrieval. The matrix
is in `.pulsar/notes/sweep-matrix.md` (4 retrieval-strictness ×
[1 K=0 + 9 K·W combos] × 3 replicates = 120 attempted, 117 succeeded).

**Result: 0/117 cleared the bar.** The cleanest single run was
`max_speed = 4.26 m/s` (70% over the 2.5 m/s walking-pace threshold)
with 2 bad pairs. 7 of 117 came in under 5 m/s and were scattered
across non-adjacent cells, strongly suggesting stochastic hits rather
than a structural sweet spot. Within most cells the replicate spread
(4–43 m/s) exceeded the differences between cell medians — the
filter knobs were quieter than the run-to-run noise.

The `long_range_track_count` complementary metric (designed to detect
the opposite failure of over-filtering retrieval to nothing) was flat
within ±10% across all cells (4664–5106), so it could not discriminate
this capture's behaviour either. *Mechanism for the flatness:* the
suspect frames register via COLMAP's structure-less PnP fallback and
contribute ~0 tracks regardless of config, so any track-based metric
is dominated by healthy frames and systematically blind to this failure
shape.

Structural readings:

1. **The pair-filter parameter space we tested cannot defeat this
   capture's aliasing.** K, W, and retrieval inlier strictness are all
   *downstream* of retrieval candidate generation. If retrieval is
   proposing aliased high-confidence matches, no filter on those
   candidates fixes the input.
2. **The covisibility filter (K, W) basically didn't matter** at the
   retrieval-strictness levels we ran. K=0 (filter off) cells performed
   comparably to K=2..5 cells at the same strictness. The expensive
   thing the codebase built buys very little when retrieval verification
   is already strict — and at looser verification it doesn't rescue
   either.
3. **The track-extent metric is not a useful discriminator on this
   capture** (and any 3D-track-based diagnostic is structurally blind to
   the structure-less-PnP failure mode). Roughly equal long-range-track
   volume across wildly different `max_speed` outcomes means we cannot
   distinguish "good loops fired" from "aliased pairs fired" by track
   shape alone.

## The two specific aliasing patterns the sweep surfaced (and a third found later)

Across the 117 runs the worst-tear pair was concentrated on a tiny
number of timestamps. Two suspect frames in capture `4bd303f1` are
responsible for ~95% of all worst-pair tears:

| prev_ts → curr_ts | runs | recon Δ | prior Δ | implied speed |
|---|---|---|---|---|
| 1780106864515 → 1780106865015 | 48 | 3.50 m | 1.26 m | 6.99 m/s |
| 1780106865015 → 1780106865515 | 39 | 14.28 m | 0.29 m | 28.57 m/s |
| 1780106858515 → 1780106859015 | 24 | 3.23 m | 0.26 m | 6.46 m/s |
| 1780106859015 → 1780106859515 | 6 | 3.90 m | 0.31 m | 7.80 m/s |

Two suspect frames: **t=…865015** and **t=…859015**.

Cross-checking the candidate-pair list confirmed the aliased partners
were always retrieval pairs (by construction: with `spatial_neighbors=0`
and `sequential_window=20`, anything farther than 20 keyframes apart is
retrieval-sourced). t=…865015 retrieved to a tight 5-second cluster
~25–30 seconds *earlier* in the trajectory. t=…859015 retrieved to
several past-time clusters plus a small future one.

The suspect's track-graph footprint is the smoking gun: across all 117
runs, the suspect frame at t=…865015 has **median connectedness ≈ 2.7%
of a normal frame's** (max 10.7%, min 0%). In 25/117 runs (21%) it
isn't even registered. In the other 92 it's registered but observes
≤79 3D points vs ~720 median — a near-island in the map. This is the
COLMAP "structure-less PnP" signature: the aliased retrieval pair gives
the matcher enough 2D–2D correspondences to satisfy structure-less pose
estimation; COLMAP places the frame at the (wrong) implied pose; BA
can't find consistent 3D structure to anchor it, so the frame ends up
barely connected. The frame survives, but it drags BA into the wrong
local minimum on the adjacent sequential pair.

**Mechanism corollaries:**

- 3D-track-based diagnostics (`long_range_track_count`,
  `p95_track_extent`, prior residual) all systematically miss this
  failure because the bad pair doesn't produce tracks.
- Downstream filters that operate on tracks or 3D residuals cannot
  help by construction. Mitigation has to be upstream (retrieval), at
  the verification stage (something that rejects 2D match support
  before structure-less PnP accepts it), or at the registration
  policy (e.g., refuse structure-less fallback for retrieval-linked
  images, only allow it for sequential-linked).

A parallel subagent did direct visual inspection of the suspect frames
and confirmed **two distinct aliasing mechanisms**:

- **Suspect A (t=…865015) — exposure collapse.** A severely under-exposed
  frame caused by auto-exposure failure transitioning through a dark
  doorway. Its global descriptor degenerates to low-frequency layout
  cues (faint ceiling-light highlights) and matches *bright* hallway
  frames on overall layout alone. Classic dark-frame retrieval collapse.
  Individually addressable by a luminance / dynamic-range gate, but see
  the architectural argument below — we deliberately are not chasing
  this fix in isolation.
- **Suspect B (t=…859015) — repeated-scene aliasing.** A hallway
  junction with framed-art / printer / cubicle decor. The user
  identified that there is only *one* printer in the office but
  *multiple* pieces of hung black-and-white art, so the most likely
  aliased element is the artwork, not the printer (the subagent's
  initial verdict named the printer but had less ground-truth context
  than the user). This was originally characterized as
  "few-feature concentration aliasing" but the match-spread filter trial
  (below) reclassified it: **the actual office-aliasing shape is
  *distributed similarity***. Two cubicles share many features (chairs,
  monitors, desks, wall textures, floor patterns), not just one repeated
  artwork. Aliased pairs in this regime have matches spread across the
  whole image, just like real matches do. **The "single repeated object"
  framing was too narrow.** This recharacterization matters because it
  invalidates concentration-based defenses — see "what match-spread
  taught us" below.

## Why this means "no filter combination wins here"

A cluster aliasing pattern — multiple aliased frames on both sides of a
true revisit — is structurally indistinguishable from a real loop
closure by any graph-consensus test like covisibility. The bad cluster
has the same neighborhood-support shape as a good cluster. The earlier
hypothesis that covisibility would subsume the per-source retrieval
strictness defense (`retrieval_min_inlier_ratio=0.40`,
`retrieval_min_num_inliers=50`) was wrong: the strict per-pair defense
was doing real work by killing aliased-but-individually-marginal
cluster members one at a time, and covisibility doesn't replace that.

This was tested directly in three runs on `4bd303f1`:

| run | spatial | covis | retrieval thresholds | max speed |
|---|---|---|---|---|
| `ff98f3c0` spatial-only | yes (fixed) | no | (0.40, 50) per-source | **6.58 m/s** |
| `3ccdc65e` covis + revert | yes (fixed) | yes | (0.25, 30) uniform | **44.41 m/s** |
| `a94dd13c` no-spatial | off | yes | (0.25, 30) uniform | **48.41 m/s** |

Same three bad pairs across all three runs. Removing spatial made things
slightly *worse* (it had been contributing some real loop closures that
partially counterbalanced). Covisibility-with-loose-per-pair failed
catastrophically vs strict-per-pair-without-covisibility.

## Where Suspect B should land in priority order

The user's read, which we now agree with: **B is the more important
failure mode to fix** — not because it occurs more often than A on this
specific capture, but because:

1. B is environment-recurring (any office / museum / hotel will hit
   it). A is more situational (specific lighting transition during a
   specific keyframe).
2. B has no isolation-metric fix, full stop. Any B fix is necessarily
   architectural — so it's the harder problem and worth solving first.
3. **The right architectural B fix byproduct-fixes A.** The candidate
   architectural fixes for B that we listed (VIO-position-gated
   retrieval, trajectory-distance-weighted retrieval, descriptor with
   positional cues, stronger geometric verification with prior,
   capture-level descriptor dedup) — VIO-gated retrieval and stronger
   geometric verification with prior would byproduct-fix A for free
   because A's spurious bright-frame matches from 25–30s earlier get
   rejected on distance grounds before descriptor similarity matters.

Caveat we are now being honest about: "spatial-prior gating fixes both"
was plausible from one supporting datapoint, not proven. The
follow-up experiment (running on capture `a0015cec` with the preventive
displacement filter on) showed displacement filter is **inert on a
small capture with high VIO drift** — the geometric ceiling is real.
See "what the new filters taught us" below.

## The drift-aware spatial-prior formulation

Because the absolute VIO is drifted (~12m on the bad capture), naive
"reject candidates more than R meters from current frame's VIO
position" doesn't work — it both rejects good loop closures (after
hours of drift, the true revisit is several meters away in VIO space)
and admits bad ones (when the alias is within drift distance).

The principled formulation exploits the **secular** nature of VIO drift
— absolute positions drift, but local relative displacement between
nearby keyframes is accurate to centimeters.

For each candidate pair `(a, b)`:
- Compare candidate's `vio_pos(b) − vio_pos(a)` against the
  sequential-VIO-implied displacement over the same trajectory window.
- Reject if they disagree by more than a threshold tuned to relative VIO
  noise (sub-meter).

This is conceptually how every VI-SLAM system uses IMU bias: absolute
state is unreliable but local state is dependable, so constraints are
expressed locally and biased states cancel out.

**Apply uniformly across all pair sources.** Stereo (same timestamp)
and sequential (±20 keyframes) trivially satisfy any reasonable check;
the meaningful work happens on retrieval. A uniform code path is
architecturally cleaner than retrieval-only, and the redundant checks
cost microseconds.

## The reactive (post-reconstruction) consistency check — Form C, now hardened

Complementary to the preventive drift-aware filter: a local-window
VIO-consistency check on the *output* of reconstruction. Same data
(VIO + recon poses, keyed by timestamp), local Sim3 transform over
N≈10 neighbors, predict each frame's recon position from its local
VIO neighbors, flag if the actual recon position disagrees by >
threshold.

This works *despite* VIO drift because drift is mostly secular: over a
~5s window of 10 keyframes, drift is millimeter-scale even on the buggy
capture. The local-window transform captures whatever absolute drift
exists *at that point in the capture*, and the prediction becomes a
high-confidence claim about where the frame should be *relative to its
local context*.

**Form C status (current):** built, landed, and refactored. Lives in
`docker/reconstructor/src/reconstructor/colmap_pipeline.py` as a
custom-fork of the upstream `IncrementalPipeline.run()`. Substantive
changes during this session:

- `vio_check(...)` now returns `bool` directly (the structured log
  moved inside the function; the structure_less suffix was dropped from
  the log line since it was redundant with caller context).
- The SVD-based local Umeyama fit was replaced with pycolmap's
  `estimate_sim3d_robust` (LO-RANSAC Sim3 fit with `max_error` tied
  to the same disagreement threshold). The math block went from ~14
  lines of explicit SVD to one helper call. The robust fit absorbs
  one or two bad-neighbor outliers that the SVD fit had no defense
  against.
- The neighbor lookup uses a pre-built sorted-by-timestamp index of
  VIO entries (`IncrementalContext.sorted_vio_entries`). `bisect_left`
  + alternating outward walk replaces the previous O(N_registered)
  linear scan for each check. Complexity is now O(log N + K · avg_skip)
  per call.
- The disagreement threshold (formerly module constant
  `VIO_CHECK_MAX_DISAGREEMENT_M`) is now plumbed through as
  `ReconstructionOptions.vio_check_max_disagreement_m`, default
  `1.0` m, accessible via `OptionsBuilder.vio_check_max_disagreement_m()`.
  The constant is gone. The same value also gates the RANSAC inlier
  threshold inside the Sim3 fit — one knob, consistent semantics.
- `VIO_CHECK_MIN_NEIGHBORS=6` stays as a module constant (it's
  mathematically fixed by Sim3 having 7 DOF). `VIO_CHECK_WINDOW=10`
  stays as a constant for now (borderline tunable, deferred).
  `VIO_CHECK_MIN_VIO_SPREAD_M2` was deleted entirely — the robust
  Sim3 fit's RANSAC handles degenerate neighborhoods without a
  pre-check.
- Frame unwinding goes through `ObservationManager.deregister_frame`
  (keeps the correspondence graph consistent; the bare
  `Reconstruction.deregister_frame` leaves stale entries). A
  Python-side skip-list filters `find_next_images` because manual
  deregistration doesn't bump COLMAP's internal `reg_trials` counter.

**Pycolmap stub bug accepted with one localized suppression:**
`estimate_sim3d_robust` is stub-typed `-> Sim3d | None` but actually
returns `dict | None` at runtime. The mismatch is concentrated in a
`_robust_sim3_fit(...) -> Sim3d | None` helper with one localized
`# type: ignore[index]` and a comment explaining the upstream stub
bug. This is the rare "no other way" case CLAUDE.md describes —
calling code stays honest.

## Three filter timings: preventive, mid-pipeline, reactive

Filters now sit at three distinct points in the per-frame lifecycle.
Each catches a different failure shape; together they are not redundant:

- **Preventive (candidate-pair stage).** Drift-aware displacement
  filter and match-spread filter run before pycolmap touches the pair
  at all. Cheapest. Catches bad pairs before matcher/verifier compute
  is spent, *and* prevents the "ghost frame" failure mode where bad
  pairs poison registration so completely the frame never lands in
  the map (later filters have nothing to flag for an absent frame).
- **Mid-pipeline (model-boundary stage).** The new pose-graph
  consistency check runs after `triangulate_image` but before
  `iterative_local_refinement`. Uses the partial model as a *local
  internal* oracle — pair-implied vs model-estimated relative pose.
  Catches pairs that pass pre-admission filters and the 2-view
  verifier but disagree with the rest of the pose graph. Cannot
  defend the seed phase (no graph to police until ~15 frames are
  registered).
- **Reactive (post-registration stage).** Form C / vio_check runs
  after `register_next_image`. Uses *external* VIO as the oracle —
  predict the just-registered frame's recon position from a local
  Sim3 fit to neighbors, reject if the actual placement disagrees by
  > threshold. Catches frames that survive both preventive and
  mid-pipeline checks because the contamination is internally
  self-consistent (two aliased pairs mutually supporting each other),
  which the model-as-oracle is structurally blind to. Coarser than
  pose-graph in the loop-closure regime (VIO drift dominates), so
  vio_check's threshold must be loose enough not to kill loop
  closures.

Mental model: preventive is a smart input filter ("don't even ask the
matcher about implausible pairs"); mid-pipeline is an internal
consistency check ("the partial model already implicitly rejects
this — surface it before BA absorbs it"); reactive is an external
ground-truth check ("the model can't catch what it's been fooled into
believing — VIO can, because it's independent"). Same reason mature
systems run all three in a defense-in-depth stack.

**The custom-fork of the COLMAP incremental pipeline loop in
`colmap_pipeline.py` is doing more work than it was a session ago.**
With the pose-graph check now also hosted in the fork, fork-removal
is further off. Forking the upstream pipeline is still real
maintenance debt — every pycolmap upgrade is a manual reconciliation
— but the trigger to revisit removal ("reactive *and* mid-pipeline
stop firing across a representative capture set") is materially
harder to hit than it was when only vio_check lived in the fork.

## What we built this session: two preventive filters, and what they taught us

Two preventive filters shipped during this session, in addition to the
Form C refactor:

### 1. Drift-aware displacement filter (in `pairs.py`)

Compares each candidate pair's relative VIO displacement against a
distance budget. The principled drift-tolerant relative formulation
described above. Apply uniformly across all pair sources; the real
work happens on retrieval.

**Empirical result on `a0015cec` (rerun of `4bd303f1` with defaults):
0 rejections.** The filter is *inert* on this capture. The mechanism is
information-theoretic: on a ~10 m capture with ~12 m of VIO drift, the
aliased pair's VIO-implied displacement (~25–30 s of drift between
visits to the same physical place) is within the same order of
magnitude as the maximum-plausible-loop-distance budget. The signal is
**exhausted**. No threshold inside the displacement-only filter can
distinguish aliased pairs from true loop closures on this capture.

**This does *not* mean the filter is useless.** On typical
ARFoundation/ARKit/ARCore captures (sub-meter drift over a 30-second
indoor walk), the same filter would do meaningful work — those captures
have a working signal-to-noise ratio. The filter is correctly built;
the bad capture is just past its information-theoretic ceiling. We
should not conflate "inert on this capture" with "useless."

### 2. Match-spread filter (in `_verify_two_view_geometries`)

For each pair surviving RANSAC, compute the normalized std-dev of
inlier match positions in each image, take the worse-spread image's
score, reject pairs below threshold (default 0.08). The intuition:
artwork-aliased pairs concentrate matches on the few visually-similar
features; true wide-baseline pairs spread matches across the whole
image. Implementation operates *outside* the COLMAP fork, at the
verification stage, hooked in right after pycolmap's
`estimate_two_view_geometry` returns.

**Math:** for uniformly-distributed matches over a normalized region
`w × h`, `spread ≈ sqrt(w·h) / 3.46`. Setting `spread = 0.08` and
solving gives `w·h ≈ 7.7%` — matches concentrated in less than 7.7% of
image area get rejected. A half-image vertical strip (`0.5 × 1.0`)
scores 0.204 — well above threshold, kept easily. Small-overlap loop
closures where the overlap is `0.25 × 0.25` (score ~0.072) get
rejected. The asymmetry that saves most real loop closures: true
partial-overlap matches typically span the full vertical extent of an
indoor scene (floor-to-ceiling), so a thin vertical strip overlap still
has decent vertical spread.

**Empirical result on `a0015cec` (defaults: 0.08 threshold):**

- Rejections: 1901 total
  - 992 sequential (~12.3% of sequential)
  - 884 spatial (~11.6% of spatial)
  - 25 retrieval (~4.2% of retrieval)
- Final reconstruction: 51 keyframe pairs (up from 29 without
  match-spread), max speed 0.94 m/s (clean), 0 long-range tracks
  (still no loop closures), max track extent 40 (sequential-window
  ceiling).

**The bad news.** Match-spread only caught **4.2% of retrieval pairs**.
The aliased retrieval pairs in this capture do *not* concentrate
matches in a small region — they have matches spread across the whole
image, because cubicle-style aliasing shares many distributed features
(chairs, monitors, desks, walls), not one repeated artwork. The
filter's assumption (concentration = aliasing) is **wrong-shape** for
the dominant failure mode. Worse, it killed sequential and spatial
pairs at 12.3% / 11.6% rates — far more than the retrieval target.
The asymmetry is the wrong sign: we kill legitimate close-by pairs
more aggressively than we kill the aliasing target.

**Why this happened: I underestimated cubicle aliasing.** The
"Suspect B = artwork = single repeated object" framing in the
original memory was too narrow. Real cubicle aliasing is
*distributed similarity*: many shared features in both rooms produce
matches that spread out just like true matches do. Concentration is
not the discriminating signal.

**Calibration doesn't rescue this.** Lower threshold (0.04) would
reduce sequential/spatial rejection but catch even fewer of the
distributed retrieval aliases. The filter's shape is wrong, not its
threshold.

### Honest reassessment after both bets shipped

The two preventive architectural bets shipped (displacement + match-spread)
are both inert or wrong-shape on the bad capture:

- *Displacement* signal exhausted (small-capture geometric ceiling)
- *Concentration* signal wrong-shape (distributed-similarity aliasing
  has spread-out matches)

This forces the architectural reframe: the path forward is **layered
weak signals**, not a single silver bullet. Each individual signal will
catch a different failure mode; the joint decision becomes strong even
when each component is weak. The displacement filter is one weak
signal that pays off on production-quality ARFoundation captures.
Match-spread, as currently shaped, may not pay off anywhere — it's
plausibly net negative because of the sequential/spatial collateral.
*Decision pending* on whether match-spread stays in the default
pipeline.

### 3. Pose-graph consistency check at the model boundary (the (a)-shaped fix)

After the two preventive bets came up inert, the user pushed back from
first principles: "during the actual incremental mapping step, when we
register frames and then bundle adjust, it seems like when we get aliased
pairs we should somehow be able to detect it, even without reference to
pose priors, simply because the bundle adjuster suddenly finds itself
having to bend over backwards to accommodate a pair that is
fundamentally inconsistent with the rest of the pose graph." This is
correct, and it identifies a different oracle entirely: **the
already-built model itself.**

Three implementation strategies were considered:

- **(a)** Pre-admission check at the candidate-pair boundary: compare
  the pair's two-view-geometry-implied relative pose against the
  model's current estimated relative pose for the same image endpoints.
- **(b)** Snapshot the model, admit the pair, run partial BA, rollback
  if disagreement explodes. Pycolmap doesn't support snapshot/rollback;
  rebuilding it would re-implement a chunk of the mapper for a noisier
  signal than (a) gives for free.
- **(c)** Post-BA disagreement detection. Observer-effect problem: once
  BA has absorbed the bad pair's evidence, the "model-estimated
  relative pose" is no longer independent of the candidate — the
  signal you want to measure has been partially canceled by the very
  contamination you're trying to detect. Degrades exactly in
  proportion to badness.

**(a) is architecturally correct.** Catches at the boundary closest to
introduction. Symmetric across pair sources (one code path for
sequential / spatial / retrieval / intra-frame-stereo). Matches what
mature systems do (ORB-SLAM3, Kimera, HLOC all score candidate loop
closures against the existing pose graph before merging). Composes with
our existing python pipeline fork.

**Pure-python implementable, no pycolmap C++ fork.** The required
primitives are all exposed on the python surface:

- `TwoViewGeometry.cam2_from_cam1` — pair-implied relative pose
  (essential-matrix decomposition during two-view verification, stored
  in the DB).
- `Reconstruction.images[id].cam_from_world()` — model-estimated
  absolute pose (note: method call, not property).
- `DatabaseCache.correspondence_graph.image_pairs` /
  `extract_two_view_geometry` — enumerate the partners a just-registered
  frame shares verified geometry with.
- `ObservationManager.delete_observation(point3D_id, image_id)` /
  `delete_point3D` — surgical excision of the 2D observations a
  poisoned pair contributed.

The one structural caveat: `triangulate_image()` is per-image, not
per-pair — it processes all of frame N's matches with already-registered
partners in one C++ call. We can't pre-filter by partner. The workaround
gets (a)-equivalent semantics: register, classify partners as
poisoned/clean, triangulate, then excise the poisoned partners'
observations from the newly-created points before BA runs. Functionally
identical to refusing admission because BA never sees the contamination
— wasted work is a couple of triangulation milliseconds per poisoned
pair.

The "deferred-pair queue" the (a) shape needs becomes implicit in this
workaround. A pair (A, B) where only A is registered doesn't appear in
`compute_poisoned_partners(A)` because B isn't a partner yet; when B
registers later, `compute_poisoned_partners(B)` automatically considers A.
No new bookkeeping.

**The structural limit of (a), confirmed by data:** at the *very
beginning* of the reconstruction, the model has no structure to check
against — so the first aliased pair, if it happens to seed the
reconstruction, slips through. Defended only by the existing front-door
layer (two-view verification, covisibility filter, drift budget,
vio_check, gravity-rotation when it ships). (a) becomes load-bearing
once the graph has more than a handful of frames; it does not replace
the front-door filters, it complements them.

**Implementation shipped (uncommitted at write time):**

- `_check_and_excise_poisoned_pairs` called inside
  `_run_incremental_registration_step` after each per-frame
  `triangulate_image`, before `iterative_local_refinement`. For each
  already-registered partner sharing a verified two-view geometry with
  the just-triangulated frame, compares the partner's pair-implied
  relative pose against the model-estimated relative pose; partners
  exceeding either rotation or translation-direction threshold get
  their match-induced observations excised from the new frame via
  `ObservationManager.delete_observation` before BA sees them.
- Four new `ReconstructionOptions` plumbed through a new
  `PairPoseGraphOptions` accessor on `OptionsBuilder`:
  rotation-disagreement-deg, translation-direction-disagreement-deg,
  baseline floor (skip pair if translation magnitude is below this; the
  translation-direction check is meaningless at near-zero baseline),
  min-registered-frames gate (skip the check until the model has at
  least N frames; default 15). The displacement-filter accessors were
  collapsed into a `PairDisplacementOptions` dataclass at the same time
  to stay under the PLR0904 public-method limit.
- Rejection counts tracked per `PairSource` and printed once at run
  end, matching the existing match-spread / vio_check log shape.

**A/B test result on capture `4bd303f1` (run `174b20f3-5af2-4203-b57f-38aff5f423f8`):**

Test condition: pose-graph check on at defaults (15° rotation,
30° translation-direction, 0.3m baseline floor, 15-frame gate), vio_check
neutralized via `vio_check_max_disagreement_m=1e9` (the code path stays
live but every disagreement passes). All other filters at defaults.

| metric | prior `a0015cec` (vio_check@1m on) | this run (pose-graph on, vio_check off) |
|---|---:|---:|
| keyframe pairs | 51 | 109 |
| max speed | 0.94 m/s | 15.56 m/s |
| p99 speed | — | 13.43 m/s |
| pairs > 2.5 m/s | 0 | 4 |
| long-range tracks | **0** | **5031** |
| p95 track extent | — | 99 keyframes |

Reconstruction itself succeeded — 220/222 images mapped, 36,173 3D
points, avg track length 4.4, reprojection median 0.72px / p90 1.49px.

Pose-graph rejections by source:

| source | count |
|---|---:|
| sequential | 358 |
| spatial | 224 |
| retrieval | 4 |
| intra_frame_stereo | 4 |

By reason: 92 rotation-only, 156 translation-only, 342 both. Total 594
rejections.

**Three findings, separated:**

**(1) Loop closures preserved — the architectural win.** Previously,
vio_check@1m killed every loop closure on this capture — 0 long-range
tracks across 117 sweep runs. With the pose-graph check as the
consistency oracle instead, 5031 long-range tracks survived, p95 reaching
99 keyframes. The pose graph is structurally tighter than it has ever
been on this capture. This is real and exactly the failure mode the new
check should handle: a model-local consistency oracle is less coarse
than a VIO-drift-bounded absolute-position oracle.

**(2) Teleports still leak — the architectural limit.** Four pairs
exceed 2.5 m/s, two of them severe (7.78m and 7.01m in 0.5s windows).
The timestamps (~`1780106840…` and `…858515 → …859015`) match the
*exact* aliased-pair regions identified earlier. The pose-graph check
did not catch them. Two probable mechanisms:

- **Early contamination, below the gate.** Bad pairs admitted before
  frame ~15 contaminated the seed model. The check ignores partners by
  design when `num_reg_images < 15` — that's exactly where the
  contamination lives. Once the seed is bad, the "model as oracle"
  becomes self-consistent in its wrongness and the check is structurally
  blind. Confirmed by data.
- **Co-misregistered pairs.** If both frames of an aliased pair are
  placed wrongly *together* (same alias drives both), their relative
  pose still agrees with the pair's implied geometry — both wrong in
  the same way. The check can't fire.

**(3) Sequential dominance is a red flag.** 358 sequential rejections vs
4 retrieval is the wrong sign relative to design intent. Sequential pairs
are temporally adjacent — they should almost never violate 15°/30°
unless one of the two frames is itself wrong. The model is rejecting
its *own* legitimate sequential geometry because earlier contamination
deformed nearby poses. This is the check picking up the splatter from
contamination that landed before it could intervene, not the check
working as designed. The retrieval source — the one we built it for —
barely fires because by the time those retrieval pairs are checked, the
model has already absorbed enough alias that the retrieval pair "agrees"
with it.

**(4) Intra-frame-stereo rejecting at all (4) is suspect.** Stereo pairs
have known calibrated geometry; the check should never fire. Either
thresholds are slightly tight or the stereo two-view geometry diverges
from rig calibration in a way worth investigating. Small absolute
number, but a smell.

### Two oracles, two blind spots (why vio_check is not redundant)

The pose-graph check and `vio_check` are **complementary, not
redundant** — they fail in different ways:

- **vio_check** is a *frame-level absolute-pose* check using *VIO as an
  external prior*. Rejects the whole frame when its just-assigned recon
  position disagrees with VIO-predicted recon position by > threshold.
  Oracle is external to the model.
- **pose-graph check** is a *pair-level relative-pose* check using the
  *model itself as a local prior*. Excises individual partner
  contributions when partner's pair-implied relative pose disagrees with
  the model's estimated relative pose. Oracle is internal.

VIO drifts but doesn't get contaminated by alias propagation, so
vio_check catches the case where the model is internally self-consistent
in its wrongness (two aliased pairs that mutually support each other —
the pose-graph check is structurally blind to this). The pose-graph
check catches the case where VIO is too drifty to be a reliable absolute
reference (the cubicle capture's exact problem — vio_check@1m killed
loop closures because VIO drift outran the budget). Different blind
spots.

**Don't drop vio_check.** The A/B test above intentionally disabled it
to isolate the pose-graph signal; that's a clean-test choice, not a
final architectural decision. The natural follow-up is the
both-checks-on configuration: pose-graph at current defaults +
vio_check at a *loose* threshold (3m or 5m) to gate the seed phase
while letting pose-graph carry the long tail. That tests the
"complementary, not redundant" hypothesis directly.

## Monocular constraint: ARFoundation must also work

A key constraint surfaced this session: the system must work for
captures from the ARFoundation capture tool, which is **monocular**.
This invalidates any signal that depends on stereo (so the
stereo-depth-consistency check, which seemed strong on ZED-only, is
off the table as a primary fix). All filters from here on need to
work on monocular input.

Implication: ARFoundation captures get the benefit of ARKit/ARCore VIO,
which is genuinely excellent (sub-meter drift over indoor walks). That
means the *displacement filter* will likely pay off on the bulk of
production captures even though it's inert on this ZED-stress-test
capture. We should not conflate the two regimes when evaluating
filters.

## Remaining monocular-compatible options (the honest short list)

After three filters delivered partial results — preventive displacement
inert, preventive match-spread wrong-shape, pose-graph consistency
preserves loop closures but leaks seed-phase teleports — what's
actually left in the toolbox that's monocular-compatible and addresses
*distributed* aliasing in the seed phase?

1. **Both-on configuration (pose-graph + vio_check at loose threshold).**
   The most natural next experiment. Re-enable vio_check at 3 – 5 m
   (loose enough to preserve loop closures, tight enough to gate the
   seed phase against the worst teleports), with the pose-graph check
   on at current defaults. Directly tests the "complementary, not
   redundant" hypothesis. Cheapest move. **Do this first.**

2. **Gravity rotation consistency at 2-view stage.** We already record
   gravity. For pair `(a, b)`, the visual relative rotation should
   match the relative gravity rotation between the frames (within
   ~5°). Catches aliased pairs where the device is oriented materially
   differently between visits. *Does not* catch aliased pairs where
   the device happens to be at the same orientation in both rooms
   (common in cubicles — facing forward both times). Partial help.
   Cheap. **Operates at the front door, before the seed forms — so it
   can defend the phase the pose-graph check cannot.**

3. **Tighter pose-graph thresholds during the seed phase.** Special-case
   the first ~15 frames with much tighter rotation / translation-direction
   thresholds against whatever model fragments exist. Trade-off: with
   so few partners, the model itself is noisy, so the check is noisy.
   Probably partial. Worth trying if (1) and (2) leave seed-phase
   teleports intact.

4. **Refuse structure-less PnP / minimum 3D-observation gate.**
   Defense-in-depth. Originally proposed as a complement to vio_check;
   now mostly *subsumed* by the pose-graph check (which excises the
   match contributions that would otherwise enable structure-less
   fallback). Build only if data shows a measurable gap that neither
   the pose-graph check nor a re-enabled vio_check covers. Lower
   priority than it was before option 3 of this list existed.

5. **Capture-time descriptor deduplication.** Cluster global
   descriptors across the capture, refuse retrieval pairs to
   over-represented clusters. Doesn't care if matches concentrate or
   spread — works on the descriptor itself. Has real risk of killing
   legitimate loops to popular areas (entrances, intersections).
   Industry move (Niantic does a variant).

6. **Reframe to capture-time UX intervention.** Mature monocular SfM
   in cubicles may genuinely require a capture-time intervention
   (dedicated dense scan in repeating-decor areas, multi-pass) rather
   than offline post-hoc filtering. ARKit/ARCore solve this by being
   online and yelling at the user when tracking confidence drops.
   We are offline and silent. Pair this with a capture-quality gate
   that fails loudly when no filter rescues a capture, so the system
   refuses to ship a broken map.

**Ranking** (post-pose-graph-shipment): cheapest immediate move is (1)
both-checks-on. Highest-leverage architectural front-door add that
defends the seed phase is (2) gravity rotation. (3) is a tuning
experiment cheap enough to fold into (1)'s follow-ups. (4) is now
demoted — substantially overlapped by what we shipped. (5) and (6)
are still bigger swings.

**No stereo-depth check.** Initially proposed as the highest-value
add, retracted once the monocular ARFoundation constraint surfaced.

## What the reconstructor exports (artifacts)

Two artifacts per reconstruction at `dev-reconstructions/<id>/`:

- **`pairs_with_source.csv`** — `image_a,image_b,source` per candidate
  pair. Source ∈ `{intra_frame_stereo, sequential, spatial, retrieval}`
  assigned by `SOURCE_PRECEDENCE`. Replaces the manual
  keyframe-distance classification we kept rebuilding.
- **`database.db`** — the COLMAP SQLite database in its
  post-incremental-mapping state. Carries cameras, images, keypoints,
  raw matches, AND `two_view_geometries` (the verified-pair subset
  that survived LO-RANSAC). Uploaded last so its presence still implies
  SfM ran to completion.

With both artifacts, "which specific retrieval pair survived and
registered the suspect frame" becomes a SQL query.

## Worth knowing about the displacement test script

`scripts/src/scripts/displacement_check.py` and its sibling
`sweep_postprocess.py` are the durable forms of the script that had
been recreated under `/tmp/recon_audit/` across multiple sessions.

The displacement test catches the *bad-pair* failure mode (BA teleports
manifesting as per-keyframe-pair speed > 2.5 m/s). It does **not**
detect the opposite failure of *missing* loop closures — a recon that
drifts unconstrained because retrieval got over-filtered will look
"clean" to the displacement test. The `long_range_track_count` metric
was added as the complementary signal but on `4bd303f1` it does not
discriminate, and the structure-less-PnP mechanism explains why any
track-based metric will be blind to this failure shape.

## Placeframe vs prior art

A map of where placeframe sits relative to standard SLAM/SfM/VPS systems:

- **COLMAP**: pure SfM, batch, offline, no priors. For unstructured
  photo collections. Placeframe uses it as a component.
- **hloc**: COLMAP + NetVLAD-retrieval-driven pair generation. Most
  direct architectural precedent. No VIO integration — same
  "well-curated input" assumption as COLMAP.
- **ORB-SLAM3 / ORB-SLAM3-VI**: real-time online SLAM, stereo or
  monocular, optional inertial. The IMU integration in -VI is exactly
  the Role B signal we're missing.
- **VINS-Fusion / OKVIS / OpenVINS**: visual-inertial SLAM. SoTA for
  the robust-pair-selection problem. Tight IMU-visual coupling at
  every stage. **They expose per-frame covariance**, letting a
  chi-squared test reject candidate loops by "is this match consistent
  with how uncertain we *actually* are at this time gap?" We can't do
  this — ZED VIO doesn't expose covariance, and ARFoundation's even
  more opaque.
- **DSO / LSD-SLAM**: direct (non-feature-based). Different paradigm.
- **DROID-SLAM, NeRF-SLAM**: don't filter pairs; let bad matches lose
  to good ones in joint global optimization. Different paradigm.
- **VPS (Niantic Lightship, Google Cloud Anchors, Apple Shared World
  Anchors)**: closest commercial analogs. All proprietary, all use
  IMU/VIO heavily, all require curated capture flows (Niantic
  explicitly requires N redundant scans across hours). The design
  lesson: don't fight aliasing with cleverer offline filters — fight
  it with redundant capture or online IMU constraints baked into pair
  selection.

**Where placeframe is distinctive:**

1. Trusts the capture device's onboard VIO output rather than running
   its own. Unusual. Flip side: if device VIO is buggy (the ZED
   capture bug), placeframe inherits the bug and has no way to correct
   it internally.
2. Per-source verification thresholds (sequential vs retrieval).
   Defensible.
3. Custom 4-source pair generator (stereo + sequential + spatial +
   retrieval). Most systems have one or two; this is genuinely unique.

**Where placeframe underweights known practice:**

1. **No spatial prior on retrieval by default.** Now shipped as the
   displacement filter; inert on this capture due to information-
   theoretic exhaustion, but expected to do real work on
   ARFoundation-quality VIO.
2. **No per-frame VIO covariance.** Capture devices don't expose it
   (frontier, not underweighted).
3. **No online consistency check between VIO and reconstruction during
   incremental mapping.** ORB-SLAM3-VI does this; we now do too,
   offline, via Form C inline VIO check in the forked
   `colmap_pipeline.py`.

**Translation to where to invest:** the 4-source pair generator is a
strength, but it's misused — retrieval runs unconstrained relative to
the rich signals available. The architectural correction is to layer
multiple weak signals (displacement budget + gravity rotation +
match-spread or successor + reactive vio_check + capture-quality
gate) rather than searching for a single silver bullet, accept that
we cannot run pure-visual-retrieval the way pure-SfM tools can, and
align with how VI-SLAM systems use IMU as an inseparable companion to
vision rather than a removable supplement.

## Decisions

- **Filter-side tuning is not the path forward.** Closed; do not
  relitigate without new evidence (e.g. a fundamentally different
  descriptor).
- **Per-frame quality filtering (BRISQUE/NIQE/PIQE, histogram, blur)
  is *not* the primary fix.** It would Band-Aid Suspect A but leaves
  the bigger architectural problem unchanged.
- **The architectural fix is layered weak signals**: displacement
  budget (preventive, shipped, inert on bad capture but useful for
  ARFoundation-grade VIO), match-spread (preventive, shipped,
  wrong-shape on cubicles — decision pending on whether to keep in
  default), reactive Form C / vio_check (shipped, hardened with
  `estimate_sim3d_robust` + sorted index + options-plumbed
  threshold), **pose-graph consistency check at the model boundary**
  (shipped, uncommitted at write time, preserves loop closures but
  cannot defend the seed phase). Plus future additions: gravity
  rotation consistency, both-checks-on configuration, possibly
  capture-time descriptor deduplication.
- **The pose-graph check is the (a)-shaped architectural fix.**
  Pre-admission relative-pose consistency between pair-implied geometry
  and model-estimated geometry. Implemented purely on the python side
  via excision-of-observations (BA never sees the contamination),
  no pycolmap C++ fork. Lives in the same python pipeline fork as
  vio_check. Demonstrated the first qualitative win on `4bd303f1`:
  5031 long-range tracks (up from 0), p95 extent 99 keyframes.
- **Pose-graph check has a structural seed-phase blind spot.** The
  first ~15 frames have no graph to police against (`min_registered_frames`
  gate, default 15). Aliased pairs that contaminate the seed survive,
  and downstream sequential-pair rejections become the splatter from
  that early contamination. Confirmed empirically on the A/B run.
- **Vio_check and pose-graph check are complementary, not redundant.**
  Different oracles: external VIO vs internal model. Different blind
  spots: VIO drifts but doesn't get contamination-propagated; the
  model gets contamination-propagated but is locally less coarse than
  VIO. Don't drop either. The both-on configuration is the next test.
- **Form C lives in `colmap_pipeline.py` as a fork.** It now uses
  `estimate_sim3d_robust` instead of explicit SVD Umeyama, a pre-built
  sorted-by-timestamp VIO index for O(log N) neighbor lookup, and a
  plumbed-through `vio_check_max_disagreement_m` option (default
  1.0 m). With the pose-graph check now also in the same fork, the
  fork is doing *more* work, not less — the "rip out the fork" trigger
  has moved further away.
- **Stereo-depth-consistency check retracted.** ARFoundation
  monocular path must work; stereo-only signals can't be primary.
- **Match-spread: ship-pending evaluation.** It's in the default
  pipeline as of the `a0015cec` run; the asymmetric collateral
  (sequential/spatial rejected at 12% vs retrieval at 4%) is a
  red flag. May get reverted from default after broader evaluation.
- **`vio_check_max_disagreement_m` is now a plumbed
  `ReconstructionOptions` field** (default 1.0 m). Sweepable.
  Setting it to `1e9` effectively neutralizes the check (useful for
  A/B isolation of the pose-graph check, as in run `174b20f3`).
- **PairPoseGraphOptions and PairDisplacementOptions accessors on
  OptionsBuilder.** The displacement-filter accessors were collapsed
  into a `PairDisplacementOptions` dataclass to stay under PLR0904
  when the four new pose-graph accessors landed. Pattern of grouping
  related accessors into dataclasses is now established for future
  filter additions.
- **Pose-prior reasoning has two roles**, evaluated independently:
  Role A (BA cost terms — σ_prior tuning question, optional, was
  mis-blamed for poisoning BA) and Role B (pair gating — load-bearing
  for robust input, currently weakly addressed by the displacement
  filter, needs more layers).
- **Capture-side: keep recording position priors**, not just gravity.
  Role B needs the position signal.
- **The displacement script lives in the repo**
  (`scripts/src/scripts/displacement_check.py`), not in `/tmp`.
- **The sweep evidence and matrix are committed under**
  `.pulsar/notes/sweep-matrix.md`.

## Key files

- `.pulsar/notes/sweep-matrix.md` — the 120-run sweep matrix design,
  fixed parameters, axes, and metric definitions. Read first before
  re-running.
- `.pulsar/notes/pair-generation-plan.md` — the priors-restored
  pipeline that the spatial source slots into. Action items are the
  active code change list. The "what we're explicitly rejecting and
  why" section ends a cluster of debates that should not be reopened
  without new evidence.
- `scripts/src/scripts/displacement_check.py` — committed displacement
  metric + track-extent metric. The math passes audit. Use the Typer
  CLI; don't rebuild it under `/tmp/`.
- `scripts/src/scripts/sweep_postprocess.py` — reads the sweep output,
  computes per-cell medians and spreads.
- `docker/reconstructor/src/reconstructor/pairs.py` —
  `generate_image_pairs` is where retrieval / spatial / sequential
  sources are emitted. The covisibility filter
  (`retrieval_covisibility_window`, `retrieval_covisibility_min_support`)
  lives here, plus the drift-aware displacement filter and the
  `write_pairs_with_source()` writer.
- `docker/reconstructor/src/reconstructor/run_reconstruction.py` —
  where the `pairs_with_source.csv` + `database.db` artifact uploads
  are wired.
- `docker/reconstructor/src/reconstructor/colmap_pipeline.py` — the
  Form C reactive VIO-consistency check *and* the new pose-graph
  consistency check at the model boundary live here. Custom-fork of
  `pycolmap/python/examples/custom_incremental_pipeline.py`. Form C
  uses `estimate_sim3d_robust` via `_robust_sim3_fit`, pre-built
  sorted-by-timestamp VIO index in `IncrementalContext`,
  `vio_check_max_disagreement_m` plumbed via context from
  `ReconstructionOptions`. The pose-graph check is
  `_check_and_excise_poisoned_pairs`, called inside
  `_run_incremental_registration_step` after `triangulate_image` and
  before `iterative_local_refinement`. It enumerates partners via the
  correspondence graph's `image_pairs`, pulls each pair's
  `TwoViewGeometry.cam2_from_cam1`, compares to the model's
  `Reconstruction.images[id].cam_from_world()` (method, not property),
  and excises poisoned partners' contributions via
  `ObservationManager.delete_observation`. `_log_pose_graph_check`
  prints per-source rejection counts at run end, mirroring the
  existing `_log_vio_check` / match-spread shapes. **Fork removal is
  further off now** — the fork hosts more load-bearing logic than
  before.
- `docker/reconstructor/src/reconstructor/options_builder.py` — where
  per-source RANSAC thresholds, the `vio_check_max_disagreement_m()`
  accessor, the new `PairPoseGraphOptions` accessor, and the
  refactored `PairDisplacementOptions` accessor (collapsed from four
  scalar accessors to one dataclass to stay under PLR0904) live.
- `docker/reconstructor/src/reconstructor/options.py` /
  `ReconstructionOptions` (Pydantic) — now carries
  `vio_check_max_disagreement_m: float = 1.0`,
  `pair_min_match_spread: float = 0.08`, and four pose-graph fields:
  rotation-disagreement-deg, translation-direction-disagreement-deg,
  baseline-floor-m, min-registered-frames-gate (default 15). The
  pose-graph defaults are 15° rotation, 30° translation-direction,
  0.3 m baseline floor.
- The match-spread filter logic lives in `_verify_two_view_geometries`
  in the reconstructor; threshold is `pair_min_match_spread`. The
  helper that scores a pair is `_pair_passes_match_spread`.
- `docker/reconstructor/SPEC.md` — being updated with the new artifact
  rows and filter options; prose commit kept separate from code per
  repo convention.
- `.pulsar/memories/reconstruction-validation.md` — the
  consecutive-frame displacement check rationale, the list of signals
  that do NOT measure reconstruction quality, and the held-out-frame
  localization harness that remains the unblocking infrastructure
  investment.
- `.pulsar/memories/bad-capture.md` — the original 12 m-drift capture
  that triggered everything. Now annotated with the priors-off
  finding (recon converges fine without priors when aliasing isn't
  triggered).

## Captures referenced

- `4bd303f1-d6c4-4867-8e35-f788c810ce26` — the original bad capture
  (worst-aliasing small ZED office, 117-run sweep target).
- `17af01a0-58fa-4fdb-8e5c-9ed736baab18` — the 12 m-drift capture
  that originally motivated the priors-off investigation. See
  `bad-capture.md`.
- `a0015cec-9a7a-44b9-943f-bdfa5f5e0e8d` — re-run of `4bd303f1`
  with defaults *after* both preventive filters and the hardened
  Form C shipped (displacement budget + match-spread @0.08 +
  vio_check @1.0 m). Showed displacement filter inert, match-spread
  catches only 4.2% of retrieval pairs while killing 12% of
  sequential/spatial, vio_check still firing 47/71. The "honest
  reassessment" run.
- `174b20f3-5af2-4203-b57f-38aff5f423f8` — A/B test of the new
  pose-graph check on `4bd303f1` with vio_check neutralized
  (`vio_check_max_disagreement_m=1e9`). Pose-graph defaults: 15° rot,
  30° trans-direction, 0.3 m baseline, 15-frame gate. **First run on
  this capture ever to produce loop closures** (5031 long-range
  tracks, p95 extent 99 keyframes) but four seed-phase teleports
  still leaked (max 15.56 m/s). Sequential-rejection dominance (358
  vs 4 retrieval) confirmed contamination-splatter mechanism. The
  "architectural win + seed-phase limit" run.

## Pending threads

### Strip-to-bare A/B matrix (partly executed 2026-06-01, still open)

We have nine layered aliasing patches on by default and no isolated
measurement of which are load-bearing. Acknowledged as a methodology
failure: all "wins" so far were measured against baselines that
included the rest of the stack.

Phase A — start from `bare`: only two-phase ingest + `spatial_neighbors=0`
on, everything else at pycolmap defaults. Specifically off / at default:

- `pair_max_displacement_scene_m` / `drift_rate_m_per_s` (drift budget)
- `pair_min_match_spread` (match-spread filter)
- `retrieval_min_inlier_ratio` / `retrieval_min_num_inliers` (retrieval-specific RANSAC strictness)
- `two_view_min_num_inliers` (raised global inlier floor)
- `retrieval_covisibility_*` (singleton-retrieval filter)
- `pair_pose_graph_*` (post-triangulation consistency check)
- `vio_check_max_disagreement_m` (already off by default at `1e9`)

Two `bare`-flavored runs landed this session on `4bd303f1` at
`sequential_window=10`: `cb6a77b1` (retrieval ON) and `6f5a03ee`
(retrieval OFF). Key findings: (a) at window=10, retrieval is mildly
defensive, not contaminating — opposite of the window=20 picture;
(b) the residual teleports at `858015→858515` and `864515→865015→865515`
are pure Phase-1 sequential failures, surviving every config tested.
ARFoundation-grade capture still not run.

Then add patches back one at a time, ordered by prior-belief contribution:
pose-graph check first (it's the closest to architecturally load-bearing
under the new defaults), then narrowing `sequential_window`, then the
rest. Goal: the minimum essential patch set that produces clean
reconstructions on both capture regimes.

The user's stated rule: spatial off always. Do not relitigate.

### Investigate sequential aliasing (the residual teleport vector)

Status as of 2026-06-01: confirmed by elimination. At `window=10`,
regardless of retrieval state, the two residual teleports survive at
`858015→858515` (densely connected zone, frame 67 misregistration)
and `864515→865015→865515` (thin connectivity / fast motion zone,
frame 78 the dark blurry frame either drops out or lands wrong).
Magnitudes are ~4 m/s when retrieval is on, ~7 m/s when off. These
are Phase-1 sequential pairs whose two-view essential matrix
disagrees with the actual VIO-implied relative pose, but neither
the pose-graph check (no seed model to police) nor the
displacement-budget filter (no orientation signal) catches them.

The proposed fix is the **pair-time VIO-vs-essential-matrix
consistency check**. **Shipped 2026-06-01 in `418c7c18`**, sequential
pairs only by construction (see the per-source applicability table
above). Validation against the two residual teleports has not yet
been run end-to-end; that is the next session's first task.

Tighter `sequential_window` is now a different knob — it became metric
(`sequential_window_m: float`, default 3.0 m, also shipped in
`418c7c18`). Coverage cost of further tightening will be brutal: at
the previous index-based `window=10` we already drop from 220 → ~120
mapped frames.

### Add phase-3 straggler-retrieval registration (deferred)

Two-phase ingest deliberately ships without a phase-3 pass that would
register Phase 1-orphaned frames via retrieval matches. Cost is real:
on `32951227`, 68/222 frames are orphans (mostly because spatial-off
removed a fallback path). Reintroducing a phase-3 risks the same
poisoning the two-phase split eliminated, but now against a stiff
oracle so the pose-graph check should bite correctly. Build only
after the strip-to-bare establishes a known-clean baseline.

### Run on ARFoundation-grade capture

Every result so far is on `4bd303f1`, a ZED capture with anomalously
high (~12m) VIO drift. ARFoundation captures will have sub-meter VIO
drift, which fundamentally changes the regime — the drift-budget
filter that was inert on `4bd303f1` should do real work; vio_check at
a finite (loose) threshold may make sense again. Strip-to-bare must
include at least one ARFoundation capture so we're not optimizing for
one corner.

### Both-checks-on A/B — folded into strip-to-bare

The prior "both-checks-on" experiment plan (vio_check at 3-5m + pose-graph
defaults) is now a *cell* in the strip-to-bare matrix above, not its own
thread. Re-enabling vio_check at a finite threshold becomes one of the
patches we add back during the strip-to-bare evaluation. The pose-graph
check is the one that defaults to on under the new architecture; vio_check
re-enable is the cheapest cell to test because the code already exists
and only the threshold flips.

### Decide: keep or revert match-spread in default pipeline

The match-spread filter as shipped has the wrong sign asymmetry on
the bad capture (more aggressive on sequential/spatial than on
retrieval). Two options:

1. Lower threshold to 0.04 — preserves more sequential/spatial but
   catches even fewer of the distributed retrieval aliases. Probably
   doesn't fix the shape mismatch.
2. Revert from default; keep the code but set
   `pair_min_match_spread = 0.0` as the default (filter disabled
   unless explicitly opted in).

Decision pending broader evaluation across multiple captures (not
just the worst-case stress test).

### Gravity rotation consistency at 2-view stage

The next-highest-leverage architectural add. For each candidate pair
`(a, b)`, compare the visual relative rotation (from RANSAC essential
matrix) against the relative gravity rotation
(`R_relative @ gravity_a ≈ gravity_b`). Reject if disagreement > a
few degrees. Operates outside the COLMAP fork at the verification
stage, same as match-spread. Gravity vectors already live in
`frames.csv`. Plumb threshold as another `ReconstructionOptions`
field.

### Cheap parameter tuning: loosen `vio_check_max_disagreement_m`

Folded into the both-checks-on A/B above. 1.0 m default is too tight;
try 3.0 m and 5.0 m as part of the pose-graph + vio_check joint
configuration. The cleaner version of this experiment is now the
both-on test, not vio_check alone.

### Investigate intra-frame-stereo rejections (RESOLVED 2026-06-01, FIX SHIPPED)

Diagnosed: the rejections are not a calibration smell. They are
stereo pairs whose unconstrained essential matrix doesn't satisfy the
fixed rig baseline making it through unfiltered, because commit
`ddcb5033` silently dropped rig-aware verification when it switched
from `match_spatial` to per-pair `estimate_two_view_geometry`.
Fix shipped in `418c7c18` — `geometric_verification(...,
rig_verification=True)` with DB-row polling for progress. Validation
that the per-source stereo rejection count drops to ~0 is part of the
next session's end-to-end run.

### Refuse structure-less PnP / 3D-observation count gate (form b)

**Demoted.** Originally proposed as defense-in-depth on top of
vio_check. The pose-graph check substantially subsumes it (excising
the match contributions that would have enabled structure-less
fallback). Only revisit if data from the both-checks-on test shows a
specific failure mode neither vio_check nor pose-graph catches that
this filter would.

### Capture-quality gate (ship loudly-broken-or-nothing)

Mature monocular-SfM-in-cubicles realistically requires a "this
capture is unrecoverable" detector that refuses to ship a broken
map. Form A from the earlier memory (offline VIO-consistency metric
on the recon output) is the data primitive. Combine with: registered
fraction, average track length, BA residual distribution, vio_check
firing rate. Threshold tuned against a known-clean reconstruction's
99th percentile. ~80 lines. Needs ARFoundation-side capture-time
hooks to actually tell the user "rescan" — but the offline detector
is buildable now.

### Re-run the sweep with the new defenses on

The original 117-run sweep had `spatial_neighbors=0` and no
displacement filter, match-spread, or hardened Form C. The correct
follow-up varies the gravity-rotation threshold and the
`vio_check_max_disagreement_m` knob, with displacement filter on
generous-relative mode. Goal: bound the achievable
max_speed-per-capture under the layered-defense regime. Run on
multiple captures (not just `4bd303f1`) so the sample includes
ARFoundation-grade VIO inputs where the displacement filter is
expected to be load-bearing.

### Held-out-frame localization harness (still unblocked)

Still the unblocking infrastructure investment named in
`reconstruction-validation.md`. Every parameter argued about in this
work becomes grade-able only once this exists.
`held_out_frame_timestamps` on `ReconstructionOptions` is the hook.

### Measure whether Form C / pose-graph check fire once preventive layer matures

Instrument the `_log_vio_check` and `_log_pose_graph_check` summaries,
aggregate over a representative capture set, look at rejection rates
after the preventive layer is improved beyond the current displacement
+ match-spread combination (i.e., after gravity rotation is added at
the front door). If the rejection rates for both reactive checks go
to ~zero, the fork is doing nothing useful and the maintenance cost
no longer justifies it — that's the trigger to delete
`colmap_pipeline.py` and restore a single `IncrementalPipeline.run()`
call. If either keeps firing, the fork stays. Given the new
pose-graph check is doing genuinely load-bearing work on the bad
capture (preserving 5031 long-range tracks where vio_check alone
killed all of them), the fork-removal trigger is materially further
off than it was before this session.
