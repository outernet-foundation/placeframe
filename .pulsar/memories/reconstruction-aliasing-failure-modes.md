---
updated: 2026-05-31
---

# Retrieval-pair visual aliasing is the dominant reconstruction failure mode

## Goal

Document what we now know about how small ZED office captures degenerate
into BA teleports, after a 117-run parameter sweep, direct visual
inspection of the offending frames, an architectural reframing of the
problem, the shipping of two preventive filters (drift-aware
displacement and match-spread), and a follow-up reconstruction on the
bad capture that showed *both* preventive bets are inert or wrong-shape
in isolation. The headline has sharpened again: aliasing in cubicle-style
environments is solved by **layered weak signals**, not any single silver
bullet — and a meaningful chunk of the "obvious" individual signals
either fail in the data regime we care about (sub-meter VIO drift makes
displacement filter inert on tiny captures with high drift) or attack
the wrong shape of aliasing (match-spread assumes concentration, but
real office aliasing is *distributed similarity* across many repeated
features).

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

**The custom-fork of the COLMAP incremental pipeline loop in
`colmap_pipeline.py` should probably be ripped out later if the
preventive layer ends up addressing the whole problem on its own.**
Forking the upstream pipeline is real maintenance debt — every pycolmap
upgrade is a manual reconciliation. We are deliberately leaving both
reactive (Form C, the fork) and preventive (drift-aware displacement +
match-spread, both shipped this session) in place initially so we can
measure whether reactive ever fires in real captures. **The latest
recon (`a0015cec` on capture `4bd303f1` with all three on) shows
reactive *is* still firing heavily** (47 rejections / 71 passes on this
specific capture) — so the fork stays for now. The trigger to revisit
removal is "reactive stops firing across a representative capture set
once the preventive layer is improved beyond what we have today."

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

The two architectural bets we shipped (displacement + match-spread) are
both inert or wrong-shape on the bad capture:

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

After two preventive filters delivered inert results, what's actually
left in the toolbox that's monocular-compatible and addresses
*distributed* aliasing?

1. **Gravity rotation consistency at 2-view stage.** We already record
   gravity. For pair `(a, b)`, the visual relative rotation should
   match the relative gravity rotation between the frames (within
   ~5°). Catches aliased pairs where the device is oriented materially
   differently between visits. *Does not* catch aliased pairs where
   the device happens to be at the same orientation in both rooms
   (common in cubicles — facing forward both times). Probably partial
   help. Cheap to implement (gravity vectors already in
   `frames.csv`).

2. **vio_check with looser threshold.** Today's 1.0 m is killing loop
   closures wholesale (47 rejections / 71 passes on this capture). A
   3 – 5 m threshold might preserve some loop closures while still
   killing the worst aliases (5 – 20 m disagreements are still clearly
   bad). This is parameter tuning, not new architecture. Cheapest move
   on this list.

3. **Refuse structure-less PnP / minimum 3D-observation gate.**
   Defense-in-depth. Attacks the ghost-frame mechanism directly
   without depending on what the matches look like. Two
   implementation forms:
   - (a) Track pair source through to registration; refuse
     structure-less when *only* retrieval-linked matches support the
     registration.
   - (b) Post-registration support-count gate: after
     `register_next_image` succeeds, count inlier 2D-3D
     correspondences with existing Point3Ds, deregister if below a
     threshold (e.g. 200). Memory's diagnosis says ghost frames have
     <79 observations vs ~720 median, so a 200-observation threshold
     would cleanly separate them.
   Form (b) is much cleaner — single number, same shape as vio_check,
   no need to thread pair-source metadata through COLMAP internals.
   **Significant overlap with vio_check:** vio_check already rejects
   most ghost frames via "your placement disagrees with VIO
   neighbors." This filter would catch the narrow gap where the
   ghost frame happens to be near its VIO neighbors (rare on a drifty
   capture) or where vio_check skips due to too few registered VIO
   neighbors. Recommended *only if* vio_check leaves a measurable gap
   empirically. Don't build speculatively. Also: grows the fork we
   want to shrink.

4. **Capture-time descriptor deduplication.** Cluster global
   descriptors across the capture, refuse retrieval pairs to
   over-represented clusters. Doesn't care if matches concentrate or
   spread — works on the descriptor itself. Has real risk of killing
   legitimate loops to popular areas (entrances, intersections).
   Industry move (Niantic does a variant).

5. **Reframe to capture-time UX intervention.** Mature monocular SfM
   in cubicles may genuinely require a capture-time intervention
   (dedicated dense scan in repeating-decor areas, multi-pass) rather
   than offline post-hoc filtering. ARKit/ARCore solve this by being
   online and yelling at the user when tracking confidence drops.
   We are offline and silent. Pair this with a capture-quality gate
   that fails loudly when no filter rescues a capture, so the system
   refuses to ship a broken map.

**Ranking** (subject to revision): the cheapest immediate move is (2)
threshold-loosen vio_check; the highest-leverage architectural move
is (1) gravity rotation. (3) is defense-in-depth, build only if data
shows the gap. (4) and (5) are bigger swings, both worth specifying
formally if (1) + (2) don't move the needle.

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
  default), reactive Form C (shipped, hardened with
  `estimate_sim3d_robust` + sorted index + options-plumbed
  threshold). Plus future additions: gravity rotation consistency,
  vio_check threshold loosening, possibly refuse-structure-less-PnP
  and capture-time descriptor deduplication.
- **Form C lives in `colmap_pipeline.py` as a fork.** It now uses
  `estimate_sim3d_robust` instead of explicit SVD Umeyama, a pre-built
  sorted-by-timestamp VIO index for O(log N) neighbor lookup, and a
  plumbed-through `vio_check_max_disagreement_m` option (default
  1.0 m).
- **The fork is provisional.** It's still firing heavily on `4bd303f1`
  (47 rejections / 71 passes on `a0015cec`). Stays until preventive
  filters are strong enough to make it inert.
- **Stereo-depth-consistency check retracted.** ARFoundation
  monocular path must work; stereo-only signals can't be primary.
- **Match-spread: ship-pending evaluation.** It's in the default
  pipeline as of the `a0015cec` run; the asymmetric collateral
  (sequential/spatial rejected at 12% vs retrieval at 4%) is a
  red flag. May get reverted from default after broader evaluation.
- **`vio_check_max_disagreement_m` is now a plumbed
  `ReconstructionOptions` field** (default 1.0 m). Sweepable.
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
  Form C reactive VIO-consistency check lives here. Custom-fork of
  `pycolmap/python/examples/custom_incremental_pipeline.py`. Now uses
  `estimate_sim3d_robust` via `_robust_sim3_fit`, pre-built
  sorted-by-timestamp VIO index in `IncrementalContext`,
  `vio_check_max_disagreement_m` plumbed via context from
  `ReconstructionOptions`. `vio_check` returns bool with logging
  internalised. **Slated for removal if the preventive filters
  subsume it** — currently still firing heavily, so it stays.
- `docker/reconstructor/src/reconstructor/options_builder.py` — where
  per-source RANSAC thresholds and the new
  `vio_check_max_disagreement_m()` accessor live. The
  retrieval-strictness split was reverted to uniform thresholds
  during the sweep; restoring it is a code change, not just config.
- `docker/reconstructor/src/reconstructor/options.py` /
  `ReconstructionOptions` (Pydantic) — now carries
  `vio_check_max_disagreement_m: float = 1.0` and
  `pair_min_match_spread: float = 0.08` (the match-spread threshold).
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

## Pending threads

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

Today's 1.0 m default is killing loop closures wholesale on
`a0015cec` (47 rejects, 71 passes). Try 3.0 m and 5.0 m. Either:
- Catches the obviously-bad teleports (10 – 20 m) without trampling
  loop closures, OR
- The reactive filter is genuinely too coarse on this capture and
  needs companion signals
Cheap experiment; do before any more architectural builds.

### Refuse structure-less PnP / 3D-observation count gate (form b)

Defense-in-depth. Only build if data shows vio_check leaves a
measurable gap. Concretely: instrument vio_check to log "would
refuse-structure-less have caught this too?" for several real
captures. If the gap is single-digit, don't build. If it's
double-digit, build form (b) — post-registration count of
observations against existing Point3Ds, deregister below threshold
(e.g. 200). Has cluster-aliasing blind spot (multiple aliased frames
support each other and build enough mutual structure to pass).

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

### Measure whether Form C still fires once preventive layer matures

Same as before: instrument the `vio_check` log line, aggregate over
a representative capture set, look at rejection rates after the
preventive layer is improved beyond the current displacement +
match-spread combination (i.e., after gravity rotation and possibly
refuse-structure-less-PnP are also in). If the rejection rate goes
to ~zero, the fork is doing nothing useful and the maintenance cost
no longer justifies it — that's the trigger to delete
`colmap_pipeline.py` and restore a single `IncrementalPipeline.run()`
call. If reactive keeps firing, both stay.
