---
updated: 2026-06-13
---

# Multi-hypothesis relocalization: client filter-bank now → calibration → Gaussian-sum endpoint

## Goal

Fix the deepest design deficiency in Placeframe's relocalization stack: **the system
collapses an ambiguous situation into a single confident answer at every stage and has no
machinery to represent or defer that ambiguity.** It happens twice:

- **Server:** RANSAC collapses a (possibly multi-modal) correspondence set into one pose +
  one scalar confidence. A point estimate structurally cannot express "could be here, or 25m
  over there."
- **Client:** a single hold-or-snap anchor collapses a stream of measurements into one
  alignment. It can't hold "I think A, but B is live," so a run of consistent-but-wrong
  measurements forces a snap — the observed ~25m teleport.

This memory is the **forward-looking architecture plan**. It is the successor to the "rough
spec outline" in `relocalization-filter-rewrite.md` (which captures the just-shipped
single-hypothesis filter — the N=1 substrate this plan builds on). Read that memory for the
single-filter details, field data (Run 1 / Run 2 Loki sessions), and the four old-EKF bugs;
this one does not duplicate them.

Stakes: an upcoming primary demo is **outdoors in a convention-centre courtyard** at walking
pace (~1.4 m/s), uncontrolled lighting, crowds. The single-hypothesis filter survives on its
own merits; the bank is the load-bearing fix for the demo-killer teleport.

## The thesis (stated precisely, validated this session)

Multiple hypotheses at **both** levels. But the two levels cover **different failure modes**,
which is sharper than "we need both":

- **Client multi-hypothesis** defends against ambiguity that only *motion across frames* can
  resolve — a wrong region that looks right from one viewpoint. The server, working per-frame,
  is structurally blind to this.
- **Server multi-pose** defends against ambiguity *visible within a single frame* — retrieval
  straddling two look-alike regions, RANSAC picking the wrong cluster.

**User's hunch, which survived pushback: the client-side change is the more important of the
two.** Agreed. Client motion-consistency catches both Mechanism A and Mechanism B (below);
server multi-pose only catches A. The client filter-bank is potentially the *entire* game.

## The A-vs-B mechanism fork (the hinge the whole server investment turns on)

How `confidence` is *actually* computed today (placeholder calibration, from `build_metrics.py`
+ `calibration.py`): every logistic weight is zero except `log_inliers=1.2` (intercept −5.5),
isotonic step is identity, so:

```
confidence = sigmoid(1.2 · log1p(num_inliers) − 5.5)
```

Confidence is a **pure monotonic function of `num_inliers` of the winning RANSAC pose** —
nothing else. Inverting: confidence **0.90 ⟹ ~610 inliers**, **0.58 ⟹ ~127 inliers**. So the
two 25m snaps were not thin marginal fits — they were *fat, clean* fits in the wrong place.
**Mechanically, confidence is a feature-density / texture proxy, not a correctness signal.**
A texture-rich wrong region produces many inliers → high confidence. Even fully calibrated
(9-feature model) it scores the *winning* fit in isolation, with no term for "is there a
competing fit elsewhere" — so calibration alone cannot fix aliasing; the competing-hypothesis
information must come from clustering/sequential-RANSAC (server) or motion (client).

A confident-wrong-pose has two distinct mechanisms:

- **Mechanism A — multi-modal retrieval, RANSAC picks the wrong cluster.** Retrieval straddles
  regions A and B; both contribute correspondences; the wrong region wins (the other region's
  matches become uncounted RANSAC outliers, so they don't lower confidence). → `retrieval_span`
  **large**. Fixable server-side.
- **Mechanism B — clean retrieval of the wrong, self-consistent region.** The query's *global
  descriptor* is simply closest to region B; retrieval returns *only* B, RANSAC locks B cleanly.
  → `retrieval_span` **small**. **Server single-frame analysis is structurally blind to this** —
  only client motion-consistency can catch it.

A 610-inlier *clean* win is more consistent with **B** than A. **We cannot commit to the
server-side half until field data tells us whether bad snaps are A or B.** If B dominates,
server multi-pose work is wasted and the client bank is everything. This is why the
`retrieval_span_meters` logging earns its place before building anything — it is the A/B
discriminator.

## The client filter-bank (Phase 1, the load-bearing fix)

**One-sentence idea:** instead of one anchor that holds-or-snaps, keep a small set of candidate
anchors (K≈2–4), let each track the world on its own (each is exactly today's complementary
filter — **zero new filter math; the single filter is the N=1 case**), score them by *how well
they keep predicting where you are as you walk*, and only ever publish the best-scoring one. A
"snap" becomes a calm, evidence-backed promotion of whichever candidate earned it.

A hypothesis carries: the alignment it tracks (what it would publish), a **score** (track
record), and a short memory of *where you were* when it was last supported.

**Per-measurement algorithm** (after the same `inlier_ratio`/`num_inliers` quality gate as now):
1. **Predict** from each hypothesis: "where this pin says I am now" = last anchor + VIO motion
   since (the VIO-residual already computed, done per-pin).
2. **Associate**: find the pin whose prediction is closest to the measurement; if within gate it
   belongs to that pin, if far from *every* pin it belongs to nobody.
3. **Update or spawn**: belongs → low-pass-absorb + score up; nobody → spawn a new pin seeded at
   the measurement with a tiny score.
4. **Decay**: unsupported/contradicted pins lose score.
5. **Prune & cap**: drop below a floor, keep top K.

**Publish rule (per frame):** publish the top-scoring pin's smoothed alignment. Hand off only
when a *different* pin overtakes by a **margin** and **holds the lead for a dwell** (hysteresis).
That handoff is the only discontinuity, and it is now evidence-backed, not "3 anomalies in a row."

**The secret sauce — score by motion diversity, not count.** Reward a pin for being right
*across distance traveled*, not for being right many times. Weight each support by how far you've
moved since the pin was last supported. Ten confirmations standing still in a bad spot → almost
no credit; three confirmations across a 5m walk → strong credit. This is *literally the use of
motion the server can't access* — why this belongs on the client. It kills the 25m teleport:
spawn H_B when the bad measurement arrives, keep publishing H_A; H_B's repeated matches from one
spot earn almost nothing, it decays and is pruned; the published world never leaves A. And if B
were genuinely correct, B accumulates motion-diverse support, overtakes A, and gets a principled
promotion — same visual event as today's teleport, opposite epistemics.

**Complexity (honest):** ~2–3× the current filter's code, but the *risk* is concentrated in one
function (motion-weighted **scoring**) and one parameter set (promotion margin/dwell). This is a
stripped-down MHT / Gaussian-sum filter — textbook, not research. (Multi-hypothesis tracking is
textbook; the motion-weighted scoring heuristic is a reasonable hand-rolled instance of MHT
scoring, not invented whole-cloth.) No new heavy math, no perf concern (K≤4 transforms + scalars
at frame rate). Tuning failure modes: too twitchy → bank thrashes (ping-pong one level up); too
sticky → won't switch when the challenger is right — the same snap-tuning problem, plus one axis
of inter-pin arbitration. Testable: the existing `MakeLocalization` harness extends to "feed a
scripted A/B aliasing sequence, assert the published pin never leaves A." Bootstrap ties in:
at first fix there's no motion, so all pins are equally weak — the bank naturally encodes
"don't commit hard until a pin earns motion-diverse support."

## The full plan — sequential spine + parallel tracks

Organizing principle: **build Phase 1 as the degenerate case of the final design, so every
later step is filling in an implementation behind an interface that already exists — never a
restructure.** The only genuinely forced ordering is *calibration before heavy*; everything
else is parallelizable.

### Sequential spine

- **Phase 1 — Client filter-bank, heuristic scoring.** The load-bearing fix. Robust to the
  uncalibrated covariance we have today because it never touches it. Deliverable: the 25m
  teleport becomes "hold the wrong hypothesis and discard it." Survives the demo on its own.
- **Phase 2 — Calibration.** The gate that unlocks everything principled. **Hard prerequisite:**
  verify the reconstructor does *global* bundle adjustment and uses *stereo* scale — if not,
  calibration measures a warped map and is invalid (fix the reconstruction pipeline first).
  Then run the two-reconstruction recipe (full-frame R1 as truth, 80%-frame R2 as map, query the
  held-out 20%) via `fit-calibration` (exists, never run e2e). Produces a Σ you can believe.
- **Phase 3 — Swap the inner estimator to Gaussian-sum (the "heavy" endpoint).** Fill in the
  covariance implementation behind the hypothesis interface from Phase 1: each hypothesis becomes
  a proper Kalman estimator carrying a posterior covariance; scoring becomes accumulated
  log-likelihood ratio; convergence/promotion becomes "posterior variance below threshold."
  A-B against the heuristic; only switch if calibrated Σ actually wins. **This is the complete
  final solution: a Gaussian-sum (multi-hypothesis EKF) bank.**

### Parallel tracks (gated by data, not by the spine)

| Track | What | Gate / trigger |
|---|---|---|
| **D — Diagnostics** | Field sessions reading `retrieval_span_meters` + per-measurement logs. Determines Mechanism A vs B, and bootstrap-vs-midsession aliasing. | Rebuild+redeploy localizer to start producing data. **Gates Track S and the bootstrap decision.** |
| **S — Server multi-pose** | Retrieval-clustering / sequential-RANSAC → return *multiple* pose hypotheses; schema change (`Localization` → list). Most valuable at bootstrap. | **Only if Track D shows Mechanism A matters** (large span on bad snaps). If B dominates, defer/skip. |
| **M — Map recapture** | Re-map ambiguous zones at demo lighting. Source-level fix no filter fully replaces. | Independent; always net-positive. Do before the demo. |
| **0 — Demo tourniquet** | Snap cooldown, **motion-based** (not confidence-based) snap-magnitude gate, operator override. | Time-boxed by demo date. Mostly subsumed by the bank later — **except operator override, which carries forward permanently.** |

## Light vs heavy estimator — and why heavy is the right destination

When a measurement arrives, both answer "how surprised should hypothesis H be, how far should
it move?" — by comparing measurement to H's prediction, but surprise depends on fuzziness:

- **Light reading (LLR on measurement covariance):** accounts only for the *measurement's*
  fuzziness; treats H's guess as an exact point. Score = `log N(residual; 0, Σ)` accumulated as
  a log-likelihood ratio. Uses the server-provided Σ but needs **no per-hypothesis covariance
  state** → hypothesis state shape unchanged → switching from the heuristic is just two functions
  + plumbing.
- **Heavy reading (full Gaussian-sum filter):** each hypothesis also tracks its *own* confidence,
  which rises/falls correctly — a fresh shaky H defers to measurements, a rock-solid H holds
  firm; uncertainty grows on its own as you walk (VIO drift) and shrinks on good measurements.
  This is the *optimal Bayesian* answer when assumptions hold. It changes the hypothesis state
  shape (per-hypothesis posterior covariance).

**Decision (corrected this session): heavy is the right endpoint — plan for it.** Earlier
framing leaned toward light on a "keep the no-EKF posture" aesthetic, which was cost
pre-filtering and was retracted. The old single-EKF didn't fail because covariance filtering is
wrong; it failed from four implementation bugs, garbage (uncalibrated) covariance input, and —
structurally — *one Gaussian can't be multi-modal*. The heavy multi-hypothesis version **is** a
Gaussian-sum filter (multi-hypothesis EKF): N Gaussians, one per hypothesis, which fixes the
multi-modal problem directly and is the literal textbook tool for continuous-state estimation
under ambiguous data association. It is strongest exactly where we're weakest: new-hypothesis
uncertainty, principled convergence/promotion (posterior variance below threshold — the Phase-2
table's criterion, which *requires* per-hypothesis covariance), and varying measurement quality.

**The one hard sequencing constraint (not aesthetic):** heavy's optimality is conditional on
trustworthy covariance. A full Gaussian-sum filter on garbage Σ is *more* dangerous than the
heuristic — EKFs launder bad numbers into confident-looking posteriors and "confidently converge
to the wrong answer." So **calibration must precede heavy.** That is the only forced ordering.

## Early decisions to make NOW (Phase 1) so later phases are fill-ins, not rebuilds

The crux of the user's question. Each converts a future "restructure" into a future "fill in a
method":

1. **Hypothesis is an interface, not a struct.** Methods `predict(dt)`, `update(measurement)`,
   `uncertainty()`, `score`. Phase 1 `uncertainty()` = constant/heuristic; Phase 3 = real
   covariance.
2. **Split the estimator from the renderer.** Internal estimate (becomes jittery Kalman in
   Phase 3) vs. a published low-passed display. Build the split now even though Phase 1's estimate
   is already smooth → adopting Kalman later moves smoothing to the renderer with zero display
   regression.
3. **Scoring behind a seam** — `scoreAssociation(hypothesis, measurement, vioDelta) → Δscore`.
   Phase 1 = motion-diversity; later = LLR.
4. **Gating behind a seam** — `gate(hypothesis, measurement) → matchQuality`. Phase 1 = distance
   threshold (already have it: the VIO anomaly threshold); later = Mahalanobis χ².
5. **Specify the process-noise model correctly now** even if Phase 1 only partly uses it:
   rotation drift *time*-proportional, translation drift *distance*-proportional, **per-second not
   per-tick** (the old bug #3). Phase 3 fills in numbers, doesn't rediscover the bug.
6. **Plumb measurement covariance to the client but leave it unconsumed in Phase 1.** Already on
   the wire (Track B). Phase 2/3 just starts reading an input that's already arriving.
7. **Keep both scoring/gating implementations behind a build flag — never delete the heuristic.**
   The switchability seam *is* the A-B/fallback seam: if calibration turns out mediocre, fall back
   without surgery.
8. **Referee is scoring-agnostic** — publish-top-score, cap-at-K, promotion margin+dwell all
   consume "a score," whatever produces it. Bank machinery never changes across phases (only the
   threshold *units* get retuned).
9. **Stable measurement-level log schema across all phases** — residual, score, chosen
   hypothesis, gate decision, uncertainty, mode. Field analysis stays comparable Phase 1 → 3.
10. **Map-agnostic measurement intake** — the bank consumes ECEF-frame measurements regardless of
    source map. Multi-map handoff later with no re-architecture.

**Cost of the heuristic→heavy switch, given these seams:** the *diff* is small (two functions +
plumb Σ in). The real cost is **retuning** — heuristic score and log-likelihood are different
scales, so promotion margin / dwell / prune floor all need re-tuning against field data; in
calendar time that empirical work dwarfs the code change.

## Decision gates (conscious forks + what resolves each)

- **D1 — destination = Gaussian-sum bank.** ✅ Decided this session.
- **D2 — build server-side multi-pose (Track S)?** Resolved by Track D field data: large
  `retrieval_span` on bad snaps → yes; small → defer, client is everything.
- **D3 — heuristic bank tuning.** Resolved by Phase 1 field sessions (where it thrashes; promotion
  margin/dwell).
- **D4 — is the reconstructor BA/scale valid?** Hard prerequisite before Phase 2. If invalid, fix
  the reconstruction pipeline first.
- **D5 — actually switch to heavy?** Resolved by Phase 3 A-B: only if calibrated Σ beats the
  heuristic. Don't switch on faith.
- **D6 — is bootstrap aliasing real?** Resolved by Track D (bad snaps at first-fix vs mid-session).
  If real, prioritize Track S and a refuse-to-commit-at-bootstrap rule, since client motion can't
  defend the first fix.

## State (this session — 2026-06-13)

- **Single-hypothesis complementary filter verified: compiles clean, 45/45 tests pass.**
  `uv run test-unity --project Placeframe`. Cleared the "verify the new filter compiles" thread
  from `relocalization-filter-rewrite.md`. The plausible failure modes that memory flagged
  (`LocalizationMetrics` ctor types, `Is.SameAs`, `float3↔Vector3`) did **not** materialize.
  - First `test-unity` run failed with a wall of R3/Polly errors — a **red herring**:
    `test-unity` does **not** run the NuGet restore (only `compile-unity` does), and
    `Assets/Packages/` was empty. After `dotnet nugetforunity restore`, the project built fine.
    (Worth folding into tooling: `test-unity` should restore, or fail loudly when Packages/ empty.)
  - One test fixed: `RelocalizationFilterTests.cs:207`, tolerance `1e-9 → 1e-6`. A
    `float4x4` element carries float32 rounding (~1.5e-9 on 0.1) compared against a `double`
    literal — a **test-tolerance bug, not a filter bug**. No filter logic touched.
- **Server confidence gate removed** (`docker/localizer/src/localize.py`): deleted the
  `if metrics.confidence_loose < … raise LocalizationError(…)` block. Mental-model correction
  established first: `tight_min=0.0` made the tight gate a no-op already; the loose gate was
  `sigmoid(1.2·log1p(num_inliers)−5.5) ≥ 0.25` ≈ "reject if `num_inliers ≲ 38`" in a logistic
  costume — never a fitted calibration. `confidence_loose`/`_tight` still computed by
  `build_localization_metrics`, still returned in `metrics`, now flow as **pure diagnostics** with
  no accept/reject power. `calibration` and `LocalizationError` still legitimately used (covariance
  computation; real failure modes — no matches, PnP failure). ruff clean.
- **`retrieval_span_meters` logging added** (`docker/localizer/src/localize.py`, right after
  retrieval): max pairwise distance between retrieved cameras' world-space centers. The
  **Mechanism-A-vs-B discriminator**. Emits a JSON line
  `{"retrieval_image_ids": [...], "retrieval_span_meters": ...}`. Added `import json` and
  `sqrt, stack` to numpy import. ruff clean. **NOT yet producing data — needs a localizer
  rebuild + redeploy.**
- **`response9.md` written** at repo root — the full client filter-bank ELI5 (one-sentence idea,
  GPS-pins metaphor, per-measurement algorithm, publish rule, motion-diversity scoring, 25m
  walkthrough, complexity table). Joins the `response*.md` scratch pile; undecided fate.

### Pre-existing failures characterized (not ours, flagged per handoff convention)

- `docker/localizer/tests/test_build_metrics.py` — **3 failures, pre-existing** (fail identically
  on clean tree). Cause: **pycolmap 4.0.4** in the freshly-synced venv — its camera projection
  method now takes a `cam_points` kwarg the test's mock-camera lambda lacks
  (`build_metrics.py:59: TypeError ...<lambda>() got an unexpected keyword argument 'cam_points'`).
  Stale-test-vs-library mismatch; may not reflect CI depending on what the localizer's pylock
  pins. Wants a separate look.
- **basedpyright on `localize.py` cannot run meaningfully standalone** — pycolmap is not installed
  in the workspace venv (`ModuleNotFoundError`), so all pycolmap accessor types go Unknown. The
  64 baseline + 6 new errors are the *same artifact* (`reportUnknownMemberType` on pycolmap
  accessors), not real defects; the committed file doesn't fail CI with 64 errors. A real type
  gate needs `uv sync --all-packages --extra cuda`.

## Why Loki could not retroactively confirm the 25m aliasing hypothesis

Investigated and hit a hard wall: **the retrieval set is never logged.** Retrieved image IDs are
computed at `localize.py:118` (`matched_image_ids = [...]`) and never emitted. The localizer's
entire stdout footprint scraped into Loki is three `print()`s at the end of `localize()` —
timings (line 233), the `transform` JSON (236), the `metrics` JSON (237). There is no line saying
which DB images were retrieved or which map regions they came from. The litestar app is built with
`logging_config=None` (`main.py:129`) so no request-level logging either, and the query frame
arrives as an in-memory `UploadFile` and is **not persisted** — the exact frames can't be
re-localized after the fact. So the precise thing ("did the top-12 for those two queries span two
separated regions?") was discarded at line 118 of every localization and is unrecoverable from
Loki. **This is exactly why `retrieval_span_meters` logging was added** — it captures the
discriminator going forward.

## Decisions

- **Destination is a Gaussian-sum (multi-hypothesis EKF) bank.** ✅ Decided. Not a crawl back to
  the failed single-EKF — it's covariance math done *correctly*, in the *multi-modal* form that
  addresses why the single EKF failed.
- **Phase 1 = heuristic client filter-bank with motion-diversity scoring.** No covariance touched;
  robust to today's uncalibrated Σ; survives the demo on its own.
- **Calibration before heavy is the one forced ordering.** Gaussian-sum on garbage Σ is more
  dangerous than the heuristic.
- **Client multi-hypothesis is more important than server multi-pose.** Client motion-consistency
  catches both A and B; server multi-pose only A. Server work is *gated* by field data showing A.
- **Confidence is not a correctness signal** under placeholder calibration (it's a num_inliers /
  texture proxy); even calibrated it can't catch competing-hypothesis aliasing. Gating moved off
  the server entirely; confidence kept as a pure diagnostic.
- **Cut the seams up front** (the 10 early decisions): hypothesis-as-interface, estimator/renderer
  split, swappable scoring + gating behind a build flag (never delete the heuristic), correct
  process-noise model spec, plumb-but-don't-consume Σ, scoring-agnostic referee, stable log schema,
  map-agnostic intake.
- **Operator override carries forward permanently**, unlike the rest of the demo tourniquet.

## Open questions

- **A vs B: are the bad snaps large-span (A) or small-span (B)?** Resolved only by field data
  once `retrieval_span_meters` is live. **Gates whether Track S is worth building at all.**
- **Is bootstrap aliasing real (bad snaps at first-fix vs mid-session)?** If real, client motion
  can't defend the first fix → prioritize Track S + a refuse-to-commit-at-bootstrap rule.
- **Does the reconstructor do *global* BA and use *stereo* scale?** Hard prerequisite for Phase 2
  (carried from the filter-rewrite memory). Verify in `docker/reconstructor/` before Phase 2.
- **Does swapping `docker/localizer/calibration/global.json` change runtime behavior, or need a
  redeploy?** Settle before Phase 2 plumbing matters.
- **Motion-diversity scoring function exact form** — the one part of Phase 1 not yet pinned down;
  the place to "poke harder" before implementation.
- **Fate of `response*.md` scratch (now through `response9.md`)** — fold into a durable design
  note / `SPEC.md` section, or delete.

## Key files

- `packages/unity/Placeframe/Assets/Package/Core/Runtime/RelocalizationFilter.cs` — the
  single-hypothesis complementary filter; the **N=1 substrate** the bank is built from. Verified
  45/45 this session.
- `packages/unity/Placeframe/Assets/Package/Core/Runtime/VisualPositioningSystem.cs` — wires the
  filter through; `SetEcefToUnityTransform` (~line 379) is the operator-override entry point that
  carries forward permanently.
- `packages/unity/Placeframe/Assets/Package/Core/Tests/Editor/RelocalizationFilterTests.cs` —
  `MakeLocalization` harness extends directly to scripted A/B aliasing test scenarios. Tolerance
  fix at line 207 this session.
- `packages/unity/Placeframe/SPEC.md` — runtime spec; natural home for the bank design section
  (successor to the filter-rewrite "rough spec outline").
- `docker/localizer/src/localize.py` — confidence gate removed; `retrieval_span_meters` logging
  added (after retrieval, ~line 118-120). Retrieval set was previously discarded at line 118.
- `docker/localizer/src/build_metrics.py` / `calibration.py` — confidence = monotonic in
  `num_inliers` under placeholder calibration. `build_metrics.py:59` is the pre-existing pycolmap
  `cam_points` test failure.
- `docker/localizer/calibration/global.json` — placeholder; `tight_min=0.0`, loose model is
  num_inliers-only. Phase 2 replaces it.
- `scripts/src/scripts/fit_calibration.py` — two-reconstruction calibration fitter; unit-tested,
  never run e2e (Phase 2 / Track C).
- `docker/reconstructor/` — verify global BA + stereo scale before betting Phase 2 on it.
- `response9.md` (repo root) — this session's client filter-bank ELI5. Scratch; undecided fate.
- `.pulsar/memories/relocalization-filter-rewrite.md` — the companion memory: single-filter state,
  Run 1 / Run 2 field data, the four old-EKF bugs, the make-it-sing backend / Loki details.

## Pending threads

- **Rebuild + redeploy the localizer** so `retrieval_span_meters` (and the now-diagnostic
  confidence) start flowing to Loki. First concrete step — nothing downstream resolves without it.
- **Field session reading `retrieval_span_meters`** on the bad-snap zones → resolve the A/B fork
  (gates Track S) and the bootstrap question (gates D6).
- **Implement Phase 1 client filter-bank** with the 10 seams cut up front. Pin the
  motion-diversity scoring function first. Extend `MakeLocalization` tests to A/B aliasing
  scenarios.
- **Commit hygiene:** this session's code changes (`RelocalizationFilterTests.cs` tolerance,
  `localize.py` gate removal + retrieval-span logging) are not yet committed and must commit
  separately from prose (`response9.md`, this memory). Code and prose never share a commit.
- **Verify reconstructor global BA + stereo scale** (`docker/reconstructor/`) before Phase 2.
- **Confirm `calibration/global.json` hot-reload vs redeploy.**
- **Wire `SetEcefToUnityTransform` to an operator override** button/gesture (demo tourniquet item
  that carries forward).
- **Recapture the demo-site map at demo lighting** for the ambiguous zones (Track M).
- **Decide fate of `response*.md` scratch.**
- **Pre-existing localizer test failures** (`test_build_metrics.py`, pycolmap 4.0.4 `cam_points`)
  want a separate look — confirm against CI's pinned pycolmap.
