---
updated: 2026-05-31
---

# Retrieval-pair visual aliasing is the dominant reconstruction failure mode

## Goal

Document what we now know about how small ZED office captures degenerate
into BA teleports, after a 117-run parameter sweep, direct visual
inspection of the offending frames, and a follow-up architectural
discussion that reframes the problem. The headline conclusion has
sharpened: the failure is **not** a pair-filter-strictness problem and
cannot be tuned out at the filter layer. It's a *structural* problem —
retrieval is currently running with no spatial prior, which makes
visually-similar-but-physically-distant frames indistinguishable. The
durable fix is architectural (spatial gating + drift-aware priors), not
per-frame quality filtering.

This memory exists because the natural next move after seeing a teleport
is to reach for covisibility / inlier-ratio / covisibility-window knobs,
or for per-frame quality filters. We tried the former; we researched the
latter. Neither is the right shape. Future sessions should not retry
those branches without new information.

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

## The properly-stated foundational mistake

Retrieval is the only pair source with *no spatial bound*. Sequential is
bounded by keyframe index (±20). Stereo is bounded by same-timestamp.
Spatial is bounded by VIO position — but we turned spatial off
(`spatial_neighbors=0`) for the sweep, treating it as a secondary cue
rather than load-bearing. **A descriptor-only retriever with no spatial
prior will always be vulnerable to anything that produces high descriptor
similarity at the wrong place** — whether the wrongness comes from
descriptor degeneracy (Suspect A) or genuine ambiguity (Suspect B). This
is the architectural gap, not a tuning problem.

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
  than the user). This is the environmentally-recurring case: any
  office / hotel / museum / hospital with standardized repeated decor
  will hit this failure mode. Not actionable by a single-frame quality
  gate — the frame is intrinsically fine; the problem is *relational*.

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
   architectural fixes for B are:
   1. VIO position prior gating retrieval (only consider candidates
      within radius R of current frame's VIO estimate)
   2. Trajectory-distance-weighted retrieval
   3. Better descriptor with spatial / positional cues (gravity,
      semantic features)
   4. Stronger geometric verification with prior (verifier rejects
      pose solutions disagreeing with VIO by > threshold)
   5. Capture-level descriptor deduplication
   Of these, **(1) and (4) would byproduct-fix A** for free, because
   A's aliasing also relies on the retriever admitting a
   far-temporally-distant candidate. If we constrain retrieval by VIO
   position, A's spurious bright-frame matches from 25–30s earlier get
   rejected on distance grounds before descriptor similarity matters.
   (3) and (5) wouldn't fix A.

So the architectural pivot: don't ship the per-frame luminance/entropy
filter as the primary fix. It's a real Band-Aid for one specific failure
mode that is downstream of the deeper problem. Solve the deeper
problem and the Band-Aid becomes unnecessary.

Caveat we're transparent about: "spatial-prior gating fixes both" is
*plausible from one supporting datapoint*, not proven. The
architecturally correct experiment is to re-enable spatial retrieval
gating with a drift-aware bound, then re-run the sweep. If A and B both
go away, the hypothesis is confirmed. If only B goes away, A needs its
own treatment.

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

## The reactive (post-reconstruction) consistency check

Complementary to the preventive drift-aware filter: a local-window
VIO-consistency check on the *output* of reconstruction. Same data
(VIO `frames.csv` + recon `frames.txt`, keyed by timestamp), local
Umeyama transform over N≈10 neighbors, predict each frame's recon
position from its local VIO neighbors, flag if the actual recon
position disagrees by > threshold (~0.5–1.0m comfortably above noise,
calibrated against a known-clean reconstruction's 99th percentile).

This works *despite* VIO drift because drift is mostly secular: over a
~5s window of 10 keyframes, drift is millimeter-scale even on the buggy
capture. The local-window transform captures whatever absolute drift
exists *at that point in the capture*, and the prediction becomes a
high-confidence claim about where the frame should be *relative to its
local context*.

Three escalating implementation forms exist:

- **Form A — offline post-hoc validation pass.** ~80-line standalone
  script. Outputs flagged-frame list. Doesn't change reconstruction;
  just diagnoses. *The big win is it gives us a quantitative
  "is the map broken" metric that the deprecated
  `prior_drift_residual_rms_m` was trying to be — but local, so it
  survives secular VIO drift.*
- **Form B — two-pass reconstruction.** Run, run Form A, filter
  flagged frames' retrieval pairs out (the new `pairs_with_source.csv`
  artifact makes this a CSV filter), re-reconstruct. Wall-clock cost
  ~1.5–1.7x a single reconstruction with feature/OPQ/PQ stage reuse,
  closer to 2x naive. Also has the property that every reconstruction
  pays the bad-pass-1 tax — wasteful when most reconstructions are
  clean.
- **Form C — inline rejection during incremental mapping.** Hook into
  COLMAP's incremental pipeline so the consistency check fires during
  registration and rejects bad poses before they enter BA. Effort
  depends on what pycolmap exposes — best case 1–2 days (pycolmap has
  a `verify_pose_callback`), medium case 1–2 weeks (decompose into
  primitives and orchestrate the loop ourselves), hard case multi-week
  (modify COLMAP C++, fork/upstream). The progress-only callbacks our
  code currently uses (`initial_image_pair_callback`,
  `next_image_callback`) don't return decisions — we'd need an
  upstream callback that does. A ~30-minute pycolmap-source dive
  before quoting Form C effort with confidence is required and has
  not been done.

Form A only diagnoses; it does not fix anything by itself, but it's the
primitive everything else builds on and gives us the metric
infrastructure that's always useful.

## Preventive vs reactive — do we need both?

Not strictly redundant — they catch different failures — but if forced
to pick one, **reactive (Form C) is the correctness mechanism;
preventive is the efficiency mechanism.**

- **Preventive catches:** bad pairs that would otherwise consume
  matcher/verifier compute, *and* the "ghost frame" failure mode where
  bad pairs poison registration so completely the frame never lands in
  the map at all (reactive has nothing to flag for an absent frame).
- **Reactive catches:** pairs that are individually spatially-plausible
  but globally inconsistent — coincidental matches between frames that
  are near each other in VIO but don't actually share scene content,
  or pairs that pass spatial sanity but fool the 2-view verifier.

For optimal results, both. Mental model: preventive is a smart input
filter ("don't even ask the matcher about implausible pairs");
reactive is an output verifier ("validate the matcher's verdict against
VIO ground truth"). Same reason you want both type checking and
runtime tests.

Build order recommendation: Form A first (metric infrastructure,
cheap, always useful), preventive filter second (cheap, addresses bulk
of cases at low compute cost), Form C only if B's wall-clock /
ghost-frame properties become a real production problem.

## What per-frame quality filters could do (and why we deprioritized them)

For completeness, the research outcome on per-frame quality filtering.
We deliberately are not pursuing this as the primary fix — see the
"Suspect B should land first" argument — but the data is durable.

**Industry state:** essentially no mature OSS pipeline (ORB-SLAM3,
COLMAP, hloc, OpenVSLAM, pixel-perfect-sfm, kapture, DROID-SLAM) runs
a per-frame pixel-quality filter before feature extraction. COLMAP's
[official FAQ](https://colmap.github.io/faq.html) instructs users to
manually delete blurry frames; the community workaround is "sort by
JPEG file size, drop smallest 5%" — blurry frames compress smaller.
Niantic's per-frame gate is unpublished trade secret; they paper over
the failure mode with N redundant scans across hours instead.

**BRISQUE / NIQE / PIQE are the wrong tool.** They're trained on
natural-image distortion taxonomies (compression, motion blur, noise)
and the failure we saw — a content-collapsed frame with histogram
crushed near zero except for a few saturated highlights — falls
*outside* that taxonomy. They will fail to flag Suspect A *and* falsely
flag legitimate Manhattan-at-night frames because the NSS statistics
they're trained against don't match the night-urban distribution.

**If we did build one**, the recommended stack:

1. **Histogram content gate.** Per frame: fraction with `gray < 8`,
   fraction with `gray > 247`, Shannon entropy of 8-bit gray histogram.
   Reject when `(a) > 0.90 OR (b) > 0.30 OR entropy < 4.0 bits`.
   ~200µs/frame. Critically, this *does not* falsely reject a dim
   Manhattan street: nighttime urban scans still have entropy 6+ bits
   because streetlights, signs, pavement, sky each occupy distinct
   histogram bins. The dimness is *distributed*, not *collapsed*. The
   metric is a direct physical claim ("histogram too collapsed to
   carry signal"), not a proxy.
2. **Laplacian variance with per-scan percentile threshold.** Reject
   the bottom 5th percentile *if* absolute value is below a sanity floor
   (~50.0). The percentile-of-distribution approach is what mature DL
   dataset pipelines do — a night scan has lower absolute variance
   everywhere, but the *worst* frames within each scan are still the
   right ones to drop.
3. **Retrieval-side ratio-test gate (defense-in-depth).** After global
   descriptor retrieval, compute
   `(top1_similarity − topK_similarity) / top1_similarity`. If small
   (query is similar-ish to many database frames simultaneously),
   refuse to emit pairs and log it. Conceptually identical to Lowe's
   ratio test at the retrieval level. No published threshold — calibrate
   from our own captures.

**These would catch Suspect A but not Suspect B.** B's frame is
intrinsically fine; its problem is the existence of *other* similar
frames in the same capture. There is *zero* literature on detecting
"this scene appears elsewhere in this same capture" from a single
frame — by construction it can't be done.

## What the reconstructor now exports (code change, uncommitted at memorize time)

Two new permanent artifacts per reconstruction at
`dev-reconstructions/<id>/`:

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
registered the suspect frame" becomes a SQL query. New artifacts only
appear on reconstructions run *after* the reconstructor image is
rebuilt and redeployed; the 117 existing sweep runs have neither file.

**Files touched (uncommitted at memorize time):**

- `docker/reconstructor/src/reconstructor/pairs.py` (`PAIRS_WITH_SOURCE_FILE`
  constant + `write_pairs_with_source()`)
- `docker/reconstructor/src/reconstructor/run_reconstruction.py` (imports
  + 2 upload calls)
- `docker/reconstructor/SPEC.md` (two artifact-table rows; prose-only,
  separate commit per repo convention)

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
discriminate, and the structure-less-PnP mechanism explains why any
track-based metric will be blind to this failure shape.

VIO-prior-relative metrics (`prior_drift_residual_rms_m`, global
Umeyama residual) cannot be used as the complementary loop-closure
metric on the captures we're testing because VIO itself has substantial
drift — a *correct* recon that closes loops correctly diverges from
drifted VIO. The local-window VIO-consistency check (Form A above) is
the durable replacement: same data, local-window, survives secular drift.

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
  every stage.
- **DSO / LSD-SLAM**: direct (non-feature-based). Different paradigm.
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

1. **No spatial prior on retrieval by default.** We have the knob
   (`spatial_neighbors`); we treated it as ancillary and turned it off
   during the sweep that surfaced the problem.
2. **No descriptor-collapse detection on the retrieval side.** Industry
   doesn't do this either, so this is *frontier* not *underweighted*.
3. **No online consistency check between VIO and reconstruction during
   incremental mapping.** ORB-SLAM3-VI does this; we have all the data
   to do it offline and don't.

**Translation to where to invest:** the 4-source pair generator is a
strength, but it's misused — retrieval runs unconstrained while spatial
is treated as a secondary cue or turned off entirely. The architectural
correction is to make spatial constraints first-class for retrieval (in
either generous-global or drift-tolerant-relative form), accept that we
cannot run pure-visual-retrieval the way pure-SfM tools can, and align
with how VI-SLAM systems use IMU as an inseparable companion to vision
rather than a removable supplement.

## Decisions

- **Filter-side tuning is not the path forward.** Closed; do not
  relitigate without new evidence (e.g. a fundamentally different
  descriptor).
- **Per-frame quality filtering is *not* the primary fix.** It would
  Band-Aid Suspect A but leaves the bigger architectural problem
  unchanged. We have the recipe (histogram + Laplacian + retrieval
  ratio test) durably documented above if we ever want it; we are
  deliberately not building it now.
- **The architectural fix is spatial / drift-aware gating on retrieval
  candidates, plus reactive VIO-consistency checking on reconstruction
  output.** Both, in that order of priority.
- **Pose-prior reasoning has two roles**, evaluated independently:
  Role A (BA cost terms — `σ_prior` tuning question, optional, was
  mis-blamed for poisoning BA) and Role B (pair gating — load-bearing
  for robust input, currently absent, this is what we need to add).
- **Capture-side: keep recording position priors**, not just gravity —
  the recent gravity-only-zed-capture change is being reverted because
  Role B needs the position signal.
- **The displacement script lives in the repo now**
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
  lives here, plus the new `write_pairs_with_source()` writer.
- `docker/reconstructor/src/reconstructor/run_reconstruction.py` —
  where the new `pairs_with_source.csv` + `database.db` artifact
  uploads are wired.
- `docker/reconstructor/src/reconstructor/options_builder.py` — where
  per-source RANSAC thresholds (`retrieval_min_inlier_ratio`,
  `retrieval_min_num_inliers`) are or were dispatched. The split was
  reverted to uniform thresholds during the sweep; restoring it is a
  code change, not just config.
- `docker/reconstructor/SPEC.md` — being updated with the new artifact
  rows; prose commit kept separate from code per repo convention.
- `.pulsar/memories/reconstruction-validation.md` — the
  consecutive-frame displacement check rationale, the list of signals
  that do NOT measure reconstruction quality, and the held-out-frame
  localization harness that remains the unblocking infrastructure
  investment.
- `.pulsar/memories/bad-capture.md` — the original 12m-drift capture
  that triggered everything. Now annotated with the priors-off
  finding (recon converges fine without priors when aliasing isn't
  triggered).

## Pending threads

### Drift-aware retrieval candidate rejection (preventive filter)

Implement a pre-matching pair-generation filter that, for each
candidate pair `(a, b)`, computes the relative VIO displacement
`|vio_pos(b) − vio_pos(a)|` and rejects if it exceeds a threshold
consistent with maximum-plausible-loop-distance. Apply uniformly
across all pair sources (real work happens on retrieval;
stereo/sequential are no-ops or near-no-ops). Either a generous
global threshold (e.g., R = 15m on a capture with up to 12m drift)
or the principled drift-tolerant relative formulation (preferred).
This is the load-bearing architectural change.

### Form A: VIO-consistency reactive metric

Build the local-window post-hoc consistency script. ~80 lines.
Inputs: capture `frames.csv` + recon `frames.txt` keyed by timestamp.
For each registered frame, fit a local Umeyama transform over N=10
nearest-in-time neighbors, predict the frame's recon position from
its VIO position via that transform, flag if disagreement > ~0.5–1.0m.
Outputs flagged-frame list and a per-reconstruction
"fraction-flagged" metric to replace the deprecated
`prior_drift_residual_rms_m`.

### Form B / C decision

After Form A and the preventive filter are in place, decide whether
the additional cost of Form B (two-pass self-healing pipeline) or
Form C (inline rejection during incremental mapping) is justified
by residual failure modes. Form C needs a pycolmap-source dive
(~30 min) before its effort can be estimated with confidence. Don't
commit to either until Form A's flagged-frame distribution on real
captures clarifies how often residual aliasing slips through the
preventive filter.

### Re-run the sweep with spatial gating on

The original sweep held `spatial_neighbors=0` throughout, which we
now see was the wrong axis. The correct follow-up sweep varies the
spatial-gating bound (off / generous-global / drift-tolerant-relative
with varying R) and observes whether A and B both vanish, only B
vanishes, or neither vanishes. This is the experiment that
discriminates the "architectural fix solves both" hypothesis from
the "B is architectural, A still needs its own treatment" fallback.

### Build the held-out-frame localization harness

Still the unblocking infrastructure investment named in
`reconstruction-validation.md`. Every parameter argued about in this
session becomes grade-able only once this exists.
`held_out_frame_timestamps` on `ReconstructionOptions` is the hook.
