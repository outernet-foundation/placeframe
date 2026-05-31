---
updated: 2026-05-31
---

# Retrieval-pair visual aliasing is the dominant reconstruction failure mode

## Goal

Document what we now know about how small ZED office captures degenerate
into BA teleports, after a 117-run parameter sweep and direct visual
inspection of the offending frames. The headline conclusion: the failure
is **not** a pair-filter-strictness problem and cannot be tuned out at
the filter layer. It's a *bad-input* problem — a small number of
individual frames have global descriptors that genuinely alias to
unrelated parts of the trajectory, and the only durable fixes are at
retrieval-side or upstream of retrieval.

This memory exists because the natural next move after seeing a teleport
on a small capture is to reach for covisibility / inlier-ratio /
covisibility-window knobs. We tried that. It does not work. Future
sessions should not retry that branch without new information.

## The three pair sources have qualitatively different failure modes

This framing came out of first-principles reasoning during the session
and survived the sweep. It is the load-bearing mental model for every
pair-gen decision downstream.

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

## The 117-run sweep (null result)

Capture under test: `4bd303f1-d6c4-4867-8e35-f788c810ce26` — the
worst-aliasing of the three small ZED office captures. Spatial pairs
were disabled throughout the sweep (`spatial_neighbors=0`), leaning
entirely on sequential + covisibility-filtered retrieval. The matrix
is in `sweep-matrix.md` at the repo root (4 retrieval-strictness ×
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
within ±10% across all cells, so it could not discriminate this
capture's behaviour either.

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
   capture.** Roughly equal long-range-track volume across wildly
   different `max_speed` outcomes means we cannot distinguish "good
   loops fired" from "aliased pairs fired" by track shape alone on
   this scene.

## The two specific aliasing patterns the sweep surfaced

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
~25–30 seconds *earlier* in the trajectory — strongly suggestive of
visual identity to those earlier frames. t=…859015 retrieved to several
past-time clusters plus a small future one.

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

A parallel subagent did direct visual inspection of the suspect frames
and confirmed **two distinct aliasing mechanisms**:

- **Suspect A (t=…865015) — exposure collapse.** A severely under-exposed
  frame caused by auto-exposure failure transitioning through a dark
  doorway. Its global descriptor degenerates to low-frequency layout
  cues (faint ceiling-light highlights) and matches *bright* hallway
  frames on overall layout alone. Classic dark-frame retrieval collapse.
  *Actionable* — a luminance / dynamic-range gate can reject this frame
  in isolation before pair gen.
- **Suspect B (t=…859015) — repeated-scene aliasing.** A hallway
  junction with a printer/cubicle/framed-art configuration that the
  operator walked past at multiple distinct physical locations. The
  descriptor cannot disambiguate the recurrences because the scene
  legitimately looks the same. Not actionable by a single-frame quality
  gate — this is genuine scene repetition.

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

## Worth knowing about the displacement test script

`scripts/src/scripts/displacement_check.py` and its sibling
`sweep_postprocess.py` are the durable forms of the script that had
been recreated under `/tmp/recon_audit/` across multiple sessions. They
were committed to the repo during this session and audited for math
correctness against the rig-center → world transform.

The displacement test catches the *bad-pair* failure mode (BA teleports
manifesting as per-keyframe-pair speed > 2.5 m/s). It does **not**
detect the opposite failure of *missing* loop closures — a recon that
drifts unconstrained because retrieval got over-filtered will look
"clean" to the displacement test. The `long_range_track_count` metric
was added as the complementary signal but on `4bd303f1` it does not
discriminate (see sweep result above). On other captures it may.

VIO-prior-relative metrics (`prior_drift_residual_rms_m`, Umeyama
residual) cannot be used as the complementary loop-closure metric on
the captures we're testing because VIO itself has substantial drift —
a *correct* recon that closes loops correctly diverges from drifted
VIO. We've been re-tripped by this trap several times; the sweep doc
calls it out explicitly.

## Decisions made

- **Filter-side tuning is not the path forward** for the aliasing
  problem. Closed; do not relitigate without new evidence (e.g. a
  fundamentally different descriptor).
- **The displacement script lives in the repo now**
  (`scripts/src/scripts/displacement_check.py`), not in `/tmp`.
- **The sweep evidence and matrix are committed at the repo root**
  (`sweep-matrix.md`).

## What to investigate next

The session ended on the question "what other single-frame metrics,
computable in isolation, can pre-flag harmful frames before pair
generation?" The general principle that fell out: a frame is harmful
in isolation when its descriptor degenerates to something *non-specific*,
so it matches whatever shares its layout (Suspect A is the canonical
example). A pre-pair-gen quality gate could catch this class.

Constraint the user named: the system needs to keep working for
"nighttime scan" — but specifically nighttime on Manhattan city streets,
where there is still substantial light from street lights. The luminance
threshold cannot be so strict that it rejects legitimate low-light
captures, only catastrophic auto-exposure failures.

Mechanisms worth thinking through (no work done yet):

- **Luminance / dynamic-range gate.** Reject frames with mean luminance
  below some threshold, or with histogram concentrated in the bottom
  decile. Catches Suspect A directly.
- **Descriptor "informativeness" check.** A frame whose global
  descriptor cosine-similarity to many distant frames is uniformly high
  is suspect — its descriptor is non-specific. Detectable from the
  retrieval similarity distribution alone.
- **Feature-detector yield.** Frames returning very few ALIKED
  keypoints — the existing `<10 valid corners` fall-through path —
  are suspect for the same reason.

The repeated-scene case (Suspect B) is **not** addressable by any
single-frame metric and probably requires a different layer of defense
(e.g. a retrieval descriptor that's less layout-dominated, or an
alternative loop-closure source we haven't built).

## The deeper unresolved question

The architectural conclusion that fell out earlier in the session, and
that the sweep validates: **an indoor capture with self-intersecting
trajectory and good VIO should not depend on retrieval as a
loop-closure source.** Sequential gives you the skeleton; spatial
(VIO-kNN) gives you the loops; the map closes without retrieval at all.
Retrieval is needed when VIO is unreliable (outdoor / sparse-loop /
monocular). On our captures, the ZED's stereo+IMU VIO is reliable
*after* the recent capture-side fixes, so the long-term move may be to
demote retrieval to an opt-in source rather than always-on. The current
priors-restored pipeline (per `pair-generation-plan.md`) re-enables
the spatial source; whether retrieval can then be turned off entirely
on multi-camera ZED captures is an open experiment.

## Key files

- `sweep-matrix.md` — the 120-run sweep matrix design, fixed
  parameters, axes, and metric definitions. Read first before re-running.
- `pair-generation-plan.md` — the priors-restored pipeline that the
  spatial source slots into. Action items are the active code change
  list. The "what we're explicitly rejecting and why" section ends a
  cluster of debates that should not be reopened without new evidence.
- `scripts/src/scripts/displacement_check.py` — committed displacement
  metric + track-extent metric. The math passes audit. Use the Typer
  CLI; don't rebuild it under `/tmp/`.
- `scripts/src/scripts/sweep_postprocess.py` — reads the sweep
  output, computes per-cell medians and spreads.
- `docker/reconstructor/src/reconstructor/pairs.py` — `generate_image_pairs`
  is where the retrieval / spatial / sequential sources are emitted.
  The covisibility filter (`retrieval_covisibility_window`,
  `retrieval_covisibility_min_support`) lives here.
- `docker/reconstructor/src/reconstructor/options_builder.py` — where
  per-source RANSAC thresholds (`retrieval_min_inlier_ratio`,
  `retrieval_min_num_inliers`) are or were dispatched. The split was
  reverted to uniform thresholds during the sweep; restoring it is a
  code change, not just config.
- `.pulsar/memories/reconstruction-validation.md` — the
  consecutive-frame displacement check rationale, the list of signals
  that do NOT measure reconstruction quality, and the held-out-frame
  localization harness that remains the unblocking infrastructure
  investment.

## Pending threads

### Build a pre-pair-gen frame-quality gate

The single-frame-detectable suspects (Suspect A class) can be rejected
before they reach retrieval. Smallest useful version: luminance gate
calibrated against the nighttime-Manhattan constraint, plus optionally
a descriptor-informativeness check using the retrieval similarity
distribution. Validate by re-running `4bd303f1` with the gate in place
and confirming t=…865015 is dropped and the BA teleport disappears.

### Decide whether retrieval should be opt-in on multi-camera ZED captures

With the priors-restored pipeline from `pair-generation-plan.md`,
spatial covers the close-range loop-closure load. The hypothesis that
retrieval becomes net-negative on captures with reliable VIO is
testable: run the 5-capture validation pass with retrieval disabled
and compare displacement + long-range-track outcomes.

### Build the held-out-frame localization harness

Still the unblocking infrastructure investment named in
`reconstruction-validation.md`. Every parameter argued about in this
session becomes grade-able only once this exists. `held_out_frame_timestamps`
on `ReconstructionOptions` is the hook.
