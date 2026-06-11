---
updated: 2026-06-11
---

# Rewrite RelocalizationFilter as a VIO-cross-checked complementary filter; ship before demos

## Goal

Replace the current SE(3) tangent-space EKF in `RelocalizationFilter` with a simpler, more transparent
complementary-filter design that survives an outdoor courtyard demo at walking pace, with no calibration
data on the wire. The current filter has structural pathologies (rejection-inflate, posterior-based
snap test, dimensionally-wrong VIO drift model, fixed-duration slew) that no constant-tuning can fix,
and it consumes a measurement covariance that the server cannot honestly produce today.

Stakes: an upcoming primary demo is **outdoors in a convention-centre courtyard** at walking pace
(~1.4 m/s, pedestrian). Texture is good but lighting is uncontrolled and crowds occlude. The
demo can ship without calibration; the filter has to be correct without it.

## Background context (why this is being rewritten)

### What the current filter does

`packages/unity/Placeframe/Assets/Package/Core/Runtime/RelocalizationFilter.cs` is a pure-functional
static class implementing an SE(3) tangent-space Kalman filter with a chi-squared innovation gate
and a smoothstep slew between an "estimate" and a "displayed" frame. It is well-architected for
its size, but it has four structural problems:

1. **Rejection-inflate-recovery is the wrong failure mode** (`RelocalizationFilter.cs:128–137`).
   After a gate rejection the covariance diagonal grows up to bootstrap; after a few consecutive
   rejections the gate effectively re-bootstraps via the side door and admits the next measurement
   regardless of quality. Also matrix-incoherent: only the diagonal is touched, off-diagonals are
   stale, result is not guaranteed PSD. **Correct shape:** N consecutive rejections triggers an
   explicit `Reset()`.

2. **Snap-vs-slew test uses *posterior* covariance — backwards** (`RelocalizationFilter.cs:171`).
   Posterior shrinks fast after the EKF update, so within a handful of measurements any meaningful
   refinement registers as a >6σ Mahalanobis shift and *snaps*. The test should use the *prior*
   covariance — "is this shift surprising given what we knew before?"

3. **VIO drift model is dimensionally wrong** (`RelocalizationFilter.cs:252–276`). `sigma_motion`
   is `0.01 * distance_meters` applied uniformly to all 6 tangent axes and only on translation.
   Rotation drift in modern VIO is *time*-proportional gyro drift; standing still indefinitely
   accumulates yaw drift, which this model says is zero. Base process noise is per-*tick* not
   per-*second*, so localization-cadence changes silently shift the prior's decay rate.

4. **Slew is fixed-duration and conflicts with the measurement rate** (`RelocalizationFilter.cs:208–222`).
   A 1cm refinement and a 30cm refinement both take 0.5s, so small ones creep and large ones fly.
   At ≥2Hz localization the displayed frame is permanently mid-slew — the user never sees the
   estimator's actual mean.

### What the server is actually sending

Three "quality" signals; **all three are currently broken or unused**:

- **6×6 `measurement_covariance`** computed as `α · PnP_covariance + β · I_6`. `PnP_covariance` is
  pycolmap's inverse-Hessian at the optimum (claims sub-mm precision — fiction; underreports real
  error by 3–6 orders of magnitude because it only models keypoint pixel noise, not map error, wrong
  matches, degeneracies, or local minima). `α`, `β` are scalars that calibration was supposed to
  learn; currently `α=1.0, β=1e-3` in a file literally labelled "placeholder"
  (`docker/localizer/calibration/global.json`). Calibration has never been run.
- **`confidence_tight`, `confidence_loose`** — logistic regression over 9 hand-crafted features
  (inliers, reprojection error, inlier coverage, map size, etc.). Current placeholder model has all
  weights zero, intercept = -5.5 → sigmoid ≈ 0.0040 for every query. **Client filter doesn't read
  either confidence value.**
- **Raw diagnostics** (`inlier_ratio`, `num_inliers`, `num_matches`, `reprojection_error_median`,
  `inlier_coverage`) — measured server-side, nobody downstream consumes them.

The reference for the covariance-vs-confidence design is `docker/localizer/SPEC.md:186` which
explicitly documents that `α · PnP + β · I` is the chosen form because raw PnP covariance reports
~1e-6 variances. The calibration story exists on paper; it has never been executed.

### Why filter design depends on calibration

Without calibration, the covariance on the wire is a "number-shaped vibe": any filter that weights
measurements by `1/σ²` weights them by a number the solver invented multiplied by a hand-tuned
guess. EKFs are especially sensitive to covariance miscalibration — they can confidently converge
to the wrong answer. Confidence-weighted averages degrade more gracefully.

### Why "freeze on convergence" was rejected

An early proposal was "low-pass + freeze when converged." This is **wrong** for two reasons:

1. **Perceptual aliasing.** A hallway-with-identical-doors environment confirms its own wrong lock —
   the wrong location really does look like the right location from similar viewpoints. Freeze
   amplifies the failure mode.
2. **VIO drift over distance kills freeze entirely.** The published alignment is `ECEF → Unity-world`.
   VIO drifts ~1–2% of distance traveled in translation, ~0.1–1°/min in rotation. A frozen alignment
   guarantees virtual content peels off the world as the user walks (place a sign on a building,
   walk a block, turn around — sign is 1m off). **The alignment must update continuously** to
   compensate for VIO drift.

So stability is not "the alignment matrix is constant." It is **the rate and smoothness of alignment
updates** — fast enough to track VIO drift (cm-scale over ~10s at walking pace), slow enough to
suppress per-shot PnP noise. That separation by timescale is what the low-pass time constant buys.

### Walking-pace numbers (drives the time constant)

At 1.4 m/s with typical modern VIO:

| Time | Distance | Translation drift | Rotation drift |
|------|----------|-------------------|----------------|
| 10s  | 14m      | 14–28 cm          | 0.02–0.17°     |
| 60s  | 84m      | 0.8–1.7 m         | 0.1–1°         |
| 5min | 420m     | 4–8 m             | 0.5–5°         |

Low-pass τ must be **shorter than VIO drift becomes visible (<< 10s)** and **longer than the
measurement period (>> 0.5s)**. Target: **~3–5s in steady state**, tunable. With τ=3s, a 10cm
correction moves the alignment ~0.5mm per 60Hz frame — below perceptual threshold. A 50cm
correction moves 2–3mm/frame — perceptible but not jarring.

### The architectural shape (what to build)

A **complementary filter**: high-pass = VIO, low-pass = localization, output = blended pose.
Single knob (time constant), transparent, degrades gracefully when inputs are bad.

Concretely, top to bottom:

1. **Measurement intake.** New server response gives pose + covariance + confidence_tight. Drop
   below a threshold. Phase 1 gate = `inlier_ratio > T₁ AND num_inliers > T₂`. Phase 2 gate =
   `confidence_tight > tight_min`.
2. **VIO consistency check.** `expected_pose = last_accepted_measurement + vio_delta_since_then`.
   If new measurement disagrees with `expected_pose` by more than ~5× combined expected noise,
   mark anomalous. Two consecutive anomalous measurements → re-localize.
3. **Mode selector.** Bootstrap / Steady-state / Re-localize.
   - **Bootstrap** (no prior): snap to first measurement.
   - **Steady-state**: low-pass with τ≈3s. `t = 1 - exp(-dt / τ)`. SE(3) update is slerp on
     rotation, lerp on translation.
   - **Re-localize** (sustained VIO disagreement): snap, reset history.
4. **Output.** Published alignment **is** the filter state. No separate "estimate" vs "displayed."
   The smoothing time constant *is* the stability mechanism.

What's gone vs. current: EKF math, innovation-gate-with-covariance-inflation, posterior-based
snap test, `Se3.Log`/`Se3.Exp` tangent-space machinery. About ⅓ the code.

### Phase 1 vs Phase 2 — same architecture, different gauges

The architecture above does not depend on calibration. The decision boundaries inside it do:

| Decision | Phase 1 (uncalibrated) | Phase 2 (calibrated) |
|----------|------------------------|----------------------|
| Accept measurement? | `inlier_ratio > T₁` (hand-tuned) | `confidence_tight > tight_min` (learned) |
| Average weight? | Uniform | `1 / trace(Σ)` (inverse variance) |
| VIO anomaly? | Hand-tuned distance threshold | `Mahalanobis > k · σ_calibrated` |
| Converged? | Hand-tuned dispersion threshold | Posterior variance below threshold |

Phase 1 → Phase 2 is **four constants/expressions**, not a re-architecture.

### Quality estimates

- Homogeneous environments (curated demo space): Phase 1 ≈ 80–95% of Phase 2.
- Heterogeneous environments: Phase 1 ≈ 50–70% of Phase 2.
- **Outdoor courtyard, uncontrolled** (this demo): closer to 50–70% with worse outlier behavior —
  expect visible 30cm wobbles when a bad measurement slips the gate, occasional 1m+ jumps if
  multiple pile up. Heavy gating + VIO cross-check + smoothing are doing the work here.

### Calibration concern: ZED X VIO is not ground truth

User flagged that the original calibration plan (hold out 20% of map-capture frames, use their VIO
poses as truth) is wrong. ZED X VIO drifts double-digit meters across a city-block capture before
loop closure. **Raw VIO poses are not calibration-quality truth.**

The proposal that survives is **two-reconstruction calibration**:

1. Run reconstruction #1 with **all** frames → poses_R1 (SfM-refined, globally bundle-adjusted).
2. Run reconstruction #2 with **80%** of frames → map_R2.
3. Query the held-out 20% against map_R2 via the live localizer → poses_predicted.
4. Residuals = `poses_predicted` vs. `poses_R1` for the held-out frames. Fit `α, β`.

This is **not circular**, but for a non-obvious reason: we're not measuring localizer error against
absolute world truth — we're measuring it against the **map's own coordinate system**, which is
exactly what a user experiences in production. SfM defines the coordinate system; the localizer's
job is to land queries in it; the calibration measures how well it does at that. The localizer in
step 3 is matching keypoints against 3D points it didn't help create — same situation as a live
query.

Two crucial caveats on whether SfM poses can be truth at all:

- **Bundle adjustment must be global**, not just local pose refinement. COLMAP/GLOMAP do real
  global BA; need to **verify our reconstructor actually does this**. Closed-loop trajectories
  (courtyard revisits) have their drift eaten by loop closure constraints. Open-ended trajectories
  ("walk down a block, don't return") retain residual drift between endpoints that BA literally
  cannot correct.
- **Scale must come from stereo**, not be discarded. ZED X is stereo → metric scale native, so it's
  fine — but verify the reconstruction pipeline uses the stereo baseline rather than throwing it
  away. If BA isn't real or scale is dropped, the maps themselves are drift-warped and the
  calibration problem becomes a map-quality problem.

(The response6.md draft on this was interrupted mid-thought by an API outage and was never written
to disk. The reconstructor-side verification is the open thread.)

## Rough spec outline

Treat this as the skeleton of the SPEC.md for the new filter. Co-locate with the runtime code at
`packages/unity/Placeframe/Assets/Package/Core/Runtime/SPEC.md` (or wherever the existing filter
spec lives — check before writing).

1. **What this replaces and why** — point at the four structural problems above.
2. **What stability means here** — not "constant alignment"; "smooth tracking of VIO drift while
   rejecting per-shot noise." Calls out the freeze-is-wrong argument explicitly so future readers
   don't re-propose it.
3. **Inputs** — pose, raw covariance, confidence_tight, raw diagnostics (inlier_ratio, etc.). Note
   that Phase 1 ignores covariance and confidence_tight and gates on `inlier_ratio` / `num_inliers`.
4. **Mode selector** — Bootstrap / Steady-state / Re-localize. State transitions explicit.
5. **VIO consistency check** — `expected_pose = last_accepted + vio_delta`; 5× combined-noise gate;
   2 consecutive anomalies → re-localize. Primary anti-aliasing defence.
6. **Low-pass update** — `t = 1 - exp(-dt / τ)`, τ ≈ 3s default. Slerp/lerp on SE(3).
7. **Adaptive time constant** (optional, Phase 1 OK to ship without): τ stretches when VIO reports
   stationary, shortens when walking fast.
8. **Phase 1 → Phase 2 migration table** — the four-decision table above.
9. **Operator override** — `SetEcefToUnityTransform` in `VisualPositioningSystem.cs:379` exists;
   wire to a button/gesture so demo operators can rescue a bad lock.
10. **Logging** — measurement-level: residual vs VIO, confidence values, gate decisions, mode
    transitions. For post-mortems on demo day.
11. **Non-goals** — multi-map handoff is deferred (architecture is map-agnostic; consumes ECEF-frame
    measurements regardless of source map; can be revisited without re-architecture).

## State

- Server-side analysis is **done in conversation**, not in code. Findings live in
  `response.md`–`response5.md` at the repo root (verbatim transcripts of the conversation; these
  files exist but are scratch, not committed convention-compliant prose — they should be reviewed
  and either folded into the new SPEC.md or deleted).
- `response6.md` was never written; the API errored before the Write call. The two-reconstruction
  calibration analysis it contained is captured above.
- `new-filter.md` (the full spec the user asked for) was **never produced** — API errors interrupted
  it. The spec outline above is what was meant to seed that file.
- No code has been written. No tickets cut.
- Track plan was agreed in conversation but not formalized:
  - **A — Phase 1 filter rewrite** (~1–2 days, safety net). Build the complementary filter.
  - **B — Phase 2 client plumbing** (~½ day, behind a build flag). Read `confidence_tight`, compute
    `1 / trace(Σ)` weights. Lets us flip Phase 2 on the day calibration ships.
  - **C — Phase 2 calibration spike** (~2 days, timebox). Run `uv run fit-calibration` against
    the demo map via the two-reconstruction recipe. `fit-calibration` exists at
    `scripts/src/scripts/fit_calibration.py` with unit tests but has never run end-to-end against
    real data. Bug discovery is the unknown.
  - **D — Demo-environment rehearsal** (continuous). Walk the demo space at demo time-of-day with
    the latest filter. Tune Phase 1 gate, find failure modes, feed Track C.
- Pre-demo checklist items: operator override (wire `SetEcefToUnityTransform` to button/gesture),
  full measurement-level logging.
- Two things flagged as higher-leverage than the filter rewrite for demo quality: **recapture the
  map at demo time-of-day** (a 2hr sun-angle shift drops inlier counts 30–50%; overcast↔sunny
  worse), and the operator override.

## Decisions

- **Complementary filter, not EKF.** Transparent, single knob, fails gracefully under bad covariance
  inputs.
- **No freeze-on-convergence.** Alignment updates continuously to track VIO drift; "stability"
  means smooth, slow updates, not constant alignment.
- **Three modes: Bootstrap / Steady-state / Re-localize.** Snap on bootstrap and re-localize;
  low-pass in steady-state.
- **VIO cross-check is the primary anti-aliasing defence**, not a gate inflation. Sustained
  disagreement = re-localize event, not "trust the measurements more."
- **τ ≈ 3s default in steady state**, tunable. Derived from walking-pace VIO drift timescales.
- **Ship Phase 1 first**, behind no flag. Phase 2 is a build-flagged client change that becomes
  the default the day calibration ships. Same architecture, different gauges.
- **Multi-map handoff deferred.** The filter is map-agnostic by design; per-map offset learning
  can slot in upstream of the filter without re-architecture.
- **Pedestrian walking pace (~1.4 m/s) is the primary use case.** Vehicle-mounted and room-scale
  are not design points.
- **Calibration truth = SfM-refined poses from a full-frame reconstruction, residuals measured
  against a held-out 80%-frame reconstruction.** Avoids the circularity that a single-reconstruction
  hold-out has, and avoids trusting raw ZED X VIO.

## Open questions

- **Does the reconstructor actually do global bundle adjustment, and does it use stereo scale?**
  Both are prerequisites for the two-reconstruction calibration plan working. Verify in
  `docker/reconstructor/` before betting Track C on it.
- **Does swapping `docker/localizer/calibration/global.json` change behavior at runtime, or does
  it require a redeploy?** Needs to be settled before Phase 2 plumbing matters.
- **What is the right `inlier_ratio` / `num_inliers` threshold for the courtyard demo?** Comes
  out of Track D rehearsal; not derivable from first principles.
- **Adaptive τ — Phase 1 or Phase 2?** Small refinement, natural in either. Defaults to Phase 1
  unless it creates schedule risk.
- **Should `response.md`–`response5.md` be deleted, folded into the new SPEC.md, or left as
  scratch?** They duplicate content this memory captures.

## Key files

- `packages/unity/Placeframe/Assets/Package/Core/Runtime/RelocalizationFilter.cs` — the filter being
  replaced. Lines 128–137 (rejection-inflate), 171 (posterior snap test), 208–222 (fixed-duration
  slew), 252–276 (VIO drift model) are the structural problems.
- `packages/unity/Placeframe/Assets/Package/Core/Runtime/VisualPositioningSystem.cs:379`
  (`SetEcefToUnityTransform`) — the existing re-bootstrap entry point; the operator-override button
  hooks here.
- `docker/localizer/SPEC.md:186` — documents the `α · PnP_covariance + β · I` design and that current
  values are placeholders.
- `docker/localizer/calibration/global.json` — the placeholder calibration file the localizer reads;
  Phase 2 swaps it.
- `scripts/src/scripts/fit_calibration.py` (+ `scripts/tests/test_fit_calibration.py`) — the
  calibration fitter. Implemented, unit-tested, never run end-to-end against real data.
- `docker/reconstructor/` — verify global BA and stereo-scale usage before trusting the
  two-reconstruction calibration plan.
- `response.md`, `response2.md`, `response3.md`, `response4.md`, `response5.md` — at the repo root,
  the verbatim conversational synthesis that fed this memory. Scratch; review and clean up.

## Pending threads

- Write the actual `SPEC.md` for the new filter from the outline above (the requested `new-filter.md`
  was lost to an API error; capture it as a co-located `SPEC.md` per project convention, not a
  top-level scratch file).
- Verify reconstructor pipeline: global BA + stereo scale. Open `docker/reconstructor/` and the
  reconstruction pipeline docs.
- Start Track A — implement the complementary filter, replacing `RelocalizationFilter.cs`. ~1–2
  days. Safety net for demo.
- Track B plumbing: read `confidence_tight`, compute `1 / trace(Σ)`, both behind a build flag.
- Track C spike on `fit-calibration` with the two-reconstruction recipe. Timebox 2 days.
- Confirm whether the localizer reloads `calibration/global.json` without a redeploy.
- Pre-demo: wire `SetEcefToUnityTransform` to an operator button/gesture; add measurement-level
  logging; recapture the demo map at demo time-of-day if possible.
- Decide fate of `response*.md` at repo root.
