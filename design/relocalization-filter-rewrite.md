---
updated: 2026-06-12
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

### What the old filter did

`packages/unity/Placeframe/Assets/Package/Core/Runtime/RelocalizationFilter.cs` was a pure-functional
static class implementing an SE(3) tangent-space Kalman filter with a chi-squared innovation gate
and a smoothstep slew between an "estimate" and a "displayed" frame. It was well-architected for
its size, but had four structural problems:

1. **Rejection-inflate-recovery was the wrong failure mode.** After a gate rejection the covariance
   diagonal grew up to bootstrap; after a few consecutive rejections the gate effectively
   re-bootstrapped via the side door and admitted the next measurement regardless of quality. Also
   matrix-incoherent: only the diagonal was touched, off-diagonals were stale, result was not
   guaranteed PSD. **Correct shape:** N consecutive rejections triggers an explicit `Reset()`.
2. **Snap-vs-slew test used *posterior* covariance — backwards.** Posterior shrinks fast after the
   EKF update, so within a handful of measurements any meaningful refinement registered as a >6σ
   Mahalanobis shift and *snapped*. The test should have used the *prior* covariance — "is this
   shift surprising given what we knew before?"
3. **VIO drift model was dimensionally wrong.** `sigma_motion` was `0.01 * distance_meters` applied
   uniformly to all 6 tangent axes and only on translation. Rotation drift in modern VIO is
   *time*-proportional gyro drift; standing still indefinitely accumulates yaw drift, which the
   old model said was zero. Base process noise was per-*tick* not per-*second*, so
   localization-cadence changes silently shifted the prior's decay rate.
4. **Slew was fixed-duration and conflicted with the measurement rate.** A 1cm refinement and a
   30cm refinement both took 0.5s, so small ones crept and large ones flew. At ≥2Hz localization
   the displayed frame was permanently mid-slew — the user never saw the estimator's actual mean.

### What the server is actually sending

Three "quality" signals; status on the wire **as observed in Loki on 2026-06-12**:

- **6×6 `measurement_covariance`** computed as `α · PnP_covariance + β · I_6`. `PnP_covariance` is
  pycolmap's inverse-Hessian at the optimum (claims sub-mm precision — fiction; underreports real
  error by 3–6 orders of magnitude because it only models keypoint pixel noise, not map error, wrong
  matches, degeneracies, or local minima). `α`, `β` are scalars that calibration was supposed to
  learn; currently `α=1.0, β=1e-3` in a file literally labelled "placeholder"
  (`docker/localizer/calibration/global.json`). Calibration has never been run. **Phase 1 client
  filter ignores this.**
- **`confidence_tight`, `confidence_loose`** — logistic regression over 9 hand-crafted features
  (inliers, reprojection error, inlier coverage, map size, etc.). **CORRECTION TO PRIOR MEMORY:**
  this is **not** zeroed on the wire — observed range across 50 measurements is **0.255–0.950,
  mean 0.719, median 0.782**, varies meaningfully with measurement quality. The placeholder-zero
  model has been replaced or never deployed; either way, `confidence_tight` is a live, usable
  signal sitting unconsumed in the client. Track B's upside is bigger than originally predicted.
- **Raw diagnostics** (`inlier_ratio`, `num_inliers`, `num_matches`, `reprojection_error_median`,
  `inlier_coverage`) — measured server-side. `inlier_ratio` and `num_inliers` are now consumed by
  the new client filter as the Phase 1 quality gate.

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
   amplifies the failure mode. (Confirmed in the field — see "Field data" below: ~25m residuals
   with `confidence_tight = 0.58` and `0.90` observed.)
2. **VIO drift over distance kills freeze entirely.** The published alignment is `ECEF → Unity-world`.
   VIO drifts ~1–2% of distance traveled in translation, ~0.1–1°/min in rotation. A frozen alignment
   guarantees virtual content peels off the world as the user walks. **The alignment must update
   continuously** to compensate for VIO drift.

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

### The architectural shape (what was built)

A **complementary filter**: high-pass = VIO, low-pass = localization, output = blended pose.
Single knob (time constant), transparent, degrades gracefully when inputs are bad.

Concretely, top to bottom:

1. **Measurement intake.** Server response gives pose + covariance + confidence_tight. Drop
   below a threshold. Phase 1 gate = `inlier_ratio > T₁ AND num_inliers > T₂`. Phase 2 gate =
   `confidence_tight > tight_min`.
2. **VIO consistency check.** `expected_pose = last_accepted_measurement + vio_delta_since_then`.
   If new measurement disagrees with `expected_pose` by more than ~5× combined expected noise,
   mark anomalous. Configurable consecutive-anomaly count → re-localize.
3. **Mode selector.** Bootstrap / SteadyState. Re-localize = a snap in SteadyState, not a
   separate mode in the implementation.
   - **Bootstrap** (no prior): snap to first measurement.
   - **SteadyState**: low-pass with τ≈3s. `t = 1 - exp(-dt / τ)`. SE(3) update is slerp on
     rotation, lerp on translation.
   - **Re-localize** (sustained VIO disagreement): snap, reset history.
4. **Output.** Published alignment **is** the filter state. No separate "estimate" vs "displayed."
   The smoothing time constant *is* the stability mechanism.

Removed vs. old filter: EKF math, innovation-gate-with-covariance-inflation, posterior-based
snap test, `Se3.Log`/`Se3.Exp` covariance-propagation machinery (`Se3.Log` is still used for
residual measurement). About ⅓ the code.

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
- **Outdoor courtyard, uncontrolled** (this demo): closer to 50–70% with worse outlier behavior.
  Heavy gating + VIO cross-check + smoothing are doing the work here. Field data confirms:
  occasional ~23m teleports observed when bad measurements pile up.

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

## Field data — 2026-06-12 (two demo-site Loki sessions)

Backend now runs from **`make-it-sing/compose.local.yml`** (which `include:`s placeframe's compose
files via `PLACEFRAME_DIR=../placeframe`). Loki container name is `makeitsing-loki-1`, not the
placeframe-default name — `loki-query` CLI hard-codes the placeframe project name and won't work;
query Loki directly. The `demo-site` reconstruction is imported (UUID
`46890b09-ee89-4c47-8656-238d6b868dbc`, status `succeeded`) and live-served by the localizer.

### Run 1 — constants 0.4 / 30 / 2 (initial tuning from memory) — 57s, 50 measurements

```
24 reject/qualityGate (48%)   17 accept/ok (34%)
 4 accept/reLocalize (8%)      5 reject/vioAnomaly (10%)
Cadence ~0.95 Hz (median 1033ms). With 48% rejection, effective τ-relative cadence ~1.5 samples/τ.
```

- `inlier_ratio` distribution: mean 0.391, median **0.405**, min 0.181, max 0.766.
  Accepts mean 0.497 (min 0.404); QG-rejected mean 0.287 (max 0.387).
- `num_inliers` min observed: **39** (above the old 30 floor — `MinInliers=30` was dead code).
- `confidence_tight` distribution: range 0.255–0.950, mean 0.719, median 0.782. **Memory's claim
  that this is zeroed is wrong** — it's a live signal.
- 12-deep and 7-deep rejection cascades observed in the timeline. Every `accept/reLocalize` snap
  traced back to a multi-second rejection cascade that let VIO drift accumulate past anomaly
  threshold.

### Run 2 — constants 0.25 / 50 / 3 (current `RelocalizationFilter.cs`) — 115s, 75 measurements

```
32 accept/ok (43%)            12 accept/reLocalize (16%)   <-- snap rate up!
29 reject/vioAnomaly (39%)     2 reject/qualityGate (3%)
Cadence ~0.65 Hz.
```

| | Run 1 | Run 2 |
|---|---|---|
| QG rejects | 48% | **3%** |
| Snaps | 8% | **16%** (1 per 9.6s) |
| VIO anomalies | 10% | **39%** |
| Longest reject streak | 12 | 3 |
| Min `num_inliers` | 39 | 54 (above new 50 floor) |

**Quality-gate retune did exactly what was predicted** (48% → 3% rejects; 12-deep cascades gone;
remaining QG rejects are at ir=0.21–0.24, genuinely bad). **But the snap rate doubled** — the
VIO-anomaly→snap path is now the dominant failure mode.

Snap target-jump magnitudes (12 snaps in Run 2):

```
0.68m  2.10m  22.77m  1.49m  22.98m  1.44m  1.33m  2.32m  0.66m  0.77m  2.33m  1.39m
```

**Two snaps were >22m.** Raw residuals 24.5m and 25.3m, rotational residuals ~1.46–1.49 rad (~85°).
Their `confTight` values were **0.58 and 0.90** — high confidence on completely wrong measurements.
**This empirically confirms: `confidence_tight` does not catch perceptual aliasing; only the VIO
cross-check does.** Demo-killer scenarios.

Ping-pong observed at t+69.3..75.3s: `SNAP → anomaly → anomaly → SNAP` with 5.1s between snaps.
Raising `ReLocalizeAfterAnomalies` from 2→3 helped (each cascade now needs 3 hits), but a
**cooldown** is now empirically required.

Accepted vs anomaly residual distributions overlap at the threshold:

```
Accepted resid distribution:   median 0.23m,  max 0.58m
Anomaly resid bottom quartile: 0.50–0.65m  ←  inside the noise band
Anomaly resid top quartile:    2.5m–25m    ←  real failures
```

`VioAnomalyDistanceBase = 0.5m` sits at the boundary of legitimate noise. Raising to ~0.75m
would let borderline noise through (low-pass smooths it) while still catching 1m+ events.

Where the filter works correctly: 9 consecutive accepts at the end of Run 2 (t+92.8..109.8s),
residuals 0.13–0.42m, inlier counts 1000–3700. In well-mapped regions the filter is dead-quiet.
The problem is bad-viewpoint zones, not the filter algorithm.

## Rough spec outline

Treat this as the skeleton of the SPEC.md for the new filter. The runtime SPEC is at
`packages/unity/Placeframe/SPEC.md` (not co-located in `Core/Runtime/`).

1. **What this replaces and why** — point at the four structural problems above.
2. **What stability means here** — not "constant alignment"; "smooth tracking of VIO drift while
   rejecting per-shot noise." Calls out the freeze-is-wrong argument explicitly so future readers
   don't re-propose it.
3. **Inputs** — pose, raw covariance, confidence_tight, raw diagnostics (inlier_ratio, etc.). Note
   that Phase 1 ignores covariance and confidence_tight and gates on `inlier_ratio` / `num_inliers`.
4. **Mode selector** — Bootstrap / SteadyState (Re-localize is a snap action inside SteadyState).
5. **VIO consistency check** — `expected_pose = last_accepted + vio_delta`; distance-scaled
   translation gate plus rotation gate; N consecutive anomalies → re-localize. Primary
   anti-aliasing defence.
6. **Low-pass update** — `t = 1 - exp(-dt / τ)`, τ ≈ 3s default. Slerp/lerp on SE(3).
7. **Snap-magnitude gate** (new, post-field-data) — if `vioResidM > MaxSafeSnapDistance` and
   `confTight < HighConfidenceForSnap`, refuse the snap and stay stalled; let operator override
   rescue. Protects against the worst observed failure mode.
8. **Snap cooldown** (new, post-field-data) — `SecondsSinceLastSnap` field, gated in the snap
   branch. Prevents the observed 5-second ping-pong.
9. **Adaptive time constant** (optional): τ stretches when VIO reports stationary, shortens when
   walking fast.
10. **Phase 1 → Phase 2 migration table** — the four-decision table above.
11. **Operator override** — `SetEcefToUnityTransform` in `VisualPositioningSystem.cs:379` exists;
    wire to a button/gesture so demo operators can rescue a bad lock.
12. **Logging** — measurement-level: residual vs VIO, confidence values, gate decisions, mode
    transitions. **Already wired and producing data in Loki.**
13. **Non-goals** — multi-map handoff is deferred (architecture is map-agnostic; consumes ECEF-frame
    measurements regardless of source map; can be revisited without re-architecture).

## State

### Track A (Phase 1 filter rewrite) — **code written, NOT verified to compile**

**Runtime**: `RelocalizationFilter.cs` fully rewritten to the complementary-filter design.
- `FilterMode = Bootstrap | SteadyState`. `MeasurementRejection = None | QualityGate | VioAnomaly`.
- State shape: `AlignmentCurrent`, `AlignmentTarget`, `LastAcceptedMeasurement`,
  `ConsecutiveAnomalies`. Old EKF state (`AlignmentMean`, `AlignmentCovariance`, `SlewProgress`,
  `SlewStart`) gone.
- Quality gate: `inlier_ratio ≥ MinInlierRatio` AND `num_inliers ≥ MinInliers`.
- VIO check: `Se3.Log(LastAccepted⁻¹ · new)` residual; translation threshold
  `VioAnomalyDistanceBase + VioAnomalyDistanceRate · vio_distance`; rotation threshold
  `VioAnomalyRotationRadians`.
- `TickLowPass`: `t = 1 - exp(-dt / Tau)`, `Tau = 3s`. Bootstrap snaps; SteadyState low-passes.
- All EKF math removed: `MathNet.Numerics` import, `Innovation`, `PosteriorUpdate`, `KalmanUpdate`,
  `MahalanobisSquared`, `ProcessNoise`, `BootstrapCovariance`, `SmoothStep`, etc.

**Current tuning constants** (after this session's field-driven retune):
- `Tau = 3.0f`
- `MinInlierRatio = 0.25` (was 0.4 in the spec; lowered after Run 1)
- `MinInliers = 50` (was 30 in the spec; raised after Run 1 — old floor was dead code)
- `VioAnomalyDistanceBase = 0.5` — **field data says this should be ~0.75**, not yet applied
- `VioAnomalyDistanceRate = 0.1`
- `VioAnomalyRotationRadians = 5°`
- `ReLocalizeAfterAnomalies = 3` (was 2 in the spec)

**`VisualPositioningSystem.cs` wired through.** `FilterHealth` updated (`ConsecutiveAnomalies`,
`LastVioResidualMeters/Radians`); `LockupRejectionThreshold` removed (lockup is purely time-based
now); measurement-level log emits `inlierRatio`, `numInliers`, `confTight`, `vioResidM/Rad/
Distance/Thresh`, `mode`, `anomalies`, `reLocalized`. Logs are flowing to Loki successfully.

**`RelocalizationFilterTests.cs` rewritten against the new API** (244 lines → similar size).
Coverage: `InitialState`, `PassesQualityGate` (3 tests), first-accept-snap, QG-rejection preserves
state, QG does NOT increment anomalies, VIO anomaly increments + stalls,
`NConsecutiveAnomalies_TriggersReLocalize` (parametrised off `ReLocalizeAfterAnomalies` so future
bumps don't break it), one-anomaly-then-accept clears counter, threshold scales with distance,
SteadyState second-accept doesn't snap, `BypassInnovationGate` accepts low-quality and accepts
anomalous, `BypassKalman` forces snap, `TickLowPass` behaviours (Bootstrap no-op, dt≤0 no-op,
one-τ → 1-e⁻¹, half-τ → 1-e⁻⁰·⁵), `Reset` clears history but preserves `MostRecentMetrics`,
`ComputeAlignmentFromResult` invariant. Helper: `MakeLocalization(inlierRatio, numInliers,
mapTranslation)` constructs a result with identity `cameraFromMap` and `measurementMatrix`
translation `= -mapTranslation`, giving clean residual control independent of VIO motion. Drops
`using UnityEngine;` to avoid `Transform` ambiguity with `PlaceframeApiClient.Model.Transform`.

**`SPEC.md` updated** to match new constants (lines 79, 85, 86 → 0.25 / 50 / 3). New architecture
documented; freeze-is-wrong argument and VIO-cross-check-as-anti-aliasing rationale both in.
Phase 1/Phase 2 migration story preserved.

**Compile status: UNVERIFIED.** `uv run test-unity --project Placeframe` was attempted on
2026-06-12 but Unity's package registry (`packages.unity.com`) was returning 502s on
`com.unity.cloud.gltfast`, `com.unity.toolchain.linux-x86_64`, `com.unity.sysroot`. Confirmed
upstream outage via `curl`. The test runner also failed to start because of this. Until the
registry recovers and `test-unity` runs green, **assume the code may not compile** — there are
plausible failure modes (`LocalizationMetrics` constructor arg types, `Is.SameAs` semantics on
the metrics type, `float3 ↔ Vector3` implicit-conversion resolution at field assignments). User
constraint for the session was "do not run unity cli unless I tell you to" and the one explicit
authorisation (`run test-unity`) hit the registry outage.

### Track B/C/D — unchanged from prior memory

- **B — Phase 2 client plumbing** (~½ day). Read `confidence_tight`, compute `1 / trace(Σ)`
  weights, behind a build flag. **Higher-priority than before** because `confidence_tight` is
  empirically live (0.255–0.950 range) rather than zeroed.
- **C — Phase 2 calibration spike** (~2 days, timebox). Run `uv run fit-calibration` against the
  demo map via the two-reconstruction recipe. `fit-calibration` exists at
  `scripts/src/scripts/fit_calibration.py` with unit tests but has never run end-to-end against
  real data.
- **D — Demo-environment rehearsal** (continuous). Run 1 + Run 2 above are the first iterations.
  Two huge-residual events (~25m) point at specific viewpoints where the demo-site map has
  near-duplicate features matching a wrong region.

### Backend / data infrastructure (changed this session)

- The active backend is **make-it-sing's `compose.local.yml`**, which `include:`s placeframe's
  compose files. Run via `docker compose -f /make-it-sing/compose.local.yml --project-directory
  /make-it-sing up -d --quiet-pull --wait`. **NOT** `uv run up` from placeframe — that uses a
  different docker-compose project namespace and a different postgres volume.
- The `demo-site` reconstruction is imported into the current backend. Tar file at
  `/placeframe/demo-site.tar` (47M). Import command is `uv run reconstruction import demo-site.tar`
  (singular `reconstruction`, not `reconstructions`).
- The clean-slate procedure when stale postgres volumes from prior placeframe-namespace runs
  collide: `docker compose -f /make-it-sing/compose.local.yml --project-directory /make-it-sing
  down -v --remove-orphans`, then `docker compose -p placeframe down -v --remove-orphans`,
  then `docker volume prune -f`.
- Loki container under make-it-sing is `makeitsing-loki-1`, not `placeframe-loki-1`.
  `loki-query` CLI hard-codes the placeframe project name; query Loki HTTP API directly.

### Scratch / artefacts at repo root

- `response.md`–`response5.md`: pre-rewrite conversational synthesis. Still scratch.
- `response7.md`: missing or skipped (not produced).
- `response8.md`: this session's Run 1 Loki analysis, written 2026-06-12. Captures the field data
  and constant-retune recommendations.
- (`response6.md` was never produced — lost to a prior API error.)

### Pending pre-demo items

- Wire `SetEcefToUnityTransform` to an operator override button/gesture.
- Re-capture the demo-site map at demo time-of-day if possible (a 2hr sun-angle shift drops
  inlier counts 30–50%; overcast↔sunny worse). The two ~25m perceptual-aliasing snaps suggest
  specific viewpoints where current map has degenerate matches — closer mapping there is the
  source-level fix.

## Decisions

- **Complementary filter, not EKF.** Transparent, single knob, fails gracefully under bad covariance
  inputs.
- **No freeze-on-convergence.** Alignment updates continuously to track VIO drift; "stability"
  means smooth, slow updates, not constant alignment.
- **Three modes conceptually, two in code: Bootstrap / SteadyState** (Re-localize = snap inside
  SteadyState, not a separate mode).
- **VIO cross-check is the primary anti-aliasing defence**, not a gate inflation. Sustained
  disagreement = re-localize event, not "trust the measurements more."
- **τ ≈ 3s default in steady state**, tunable. Derived from walking-pace VIO drift timescales.
- **Ship Phase 1 first**, behind no flag. Phase 2 is a build-flagged client change that becomes
  the default the day calibration ships. Same architecture, different gauges.
- **Multi-map handoff deferred.** The filter is map-agnostic by design.
- **Pedestrian walking pace (~1.4 m/s) is the primary use case.** Vehicle-mounted and room-scale
  are not design points.
- **Calibration truth = SfM-refined poses from a full-frame reconstruction, residuals measured
  against a held-out 80%-frame reconstruction.** Avoids circularity, avoids trusting raw ZED X VIO.
- **Phase 1 gate constants tuned to 0.25 / 50 / 3** (was 0.4 / 30 / 2 in the original design),
  validated against Run 1 Loki data on 2026-06-12. Run 2 confirms the QG retune was correct
  (rejections 48% → 3%, no more cascades) but exposed the VIO-anomaly path as the new dominant
  failure mode.
- **`confidence_tight` is live on the wire** (NOT zeroed as the prior memory claimed). Track B
  plumbing should consume it.

## Open questions

- **Does the reconstructor actually do global bundle adjustment, and does it use stereo scale?**
  Prerequisite for the two-reconstruction calibration plan. Verify in `docker/reconstructor/`
  before betting Track C on it.
- **Does swapping `docker/localizer/calibration/global.json` change behavior at runtime, or does
  it require a redeploy?** Needs to be settled before Phase 2 plumbing matters.
- **Compile verification for the rewritten filter and tests.** Unity registry was down during
  the verification attempt. Re-run `uv run test-unity --project Placeframe` once registry is up.
- **Adaptive τ — Phase 1 or Phase 2?** Small refinement, natural in either.
- **Two pre-existing SPEC.md bugs noted but not fixed this session:** line 53 still references
  removed `CurrentUncertainty` in the public API list; line 86 says `VioAnomalyRotationBase` but
  the constant is `VioAnomalyRotationRadians`. Fold into next SPEC pass.
- **Should `response.md`–`response5.md` and `response8.md` be deleted, folded into the new
  SPEC.md, or left as scratch?** They duplicate content this memory captures.

## Key files

- `packages/unity/Placeframe/Assets/Package/Core/Runtime/RelocalizationFilter.cs` — the new
  complementary filter. Tuned constants live at lines 62–71. `ApplyMeasurement` ~line 90+,
  `TickLowPass` ~line 195+, `PassesQualityGate` ~line 228.
- `packages/unity/Placeframe/Assets/Package/Core/Runtime/VisualPositioningSystem.cs:379`
  (`SetEcefToUnityTransform`) — operator-override entry point; needs UI wiring pre-demo.
- `packages/unity/Placeframe/Assets/Package/Core/Tests/Editor/RelocalizationFilterTests.cs` —
  rewritten this session. Compile/run blocked by Unity registry outage on 2026-06-12.
- `packages/unity/Placeframe/SPEC.md` — updated for new architecture and 0.25/50/3 constants.
  Two known bugs at lines 53 and 86 (see Open questions).
- `docker/localizer/SPEC.md:186` — documents `α · PnP_covariance + β · I` design.
- `docker/localizer/calibration/global.json` — placeholder calibration. Phase 2 swaps it.
- `scripts/src/scripts/fit_calibration.py` — calibration fitter, unit-tested, never run e2e.
- `docker/reconstructor/` — verify global BA and stereo-scale usage before trusting two-recon plan.
- `/placeframe/demo-site.tar` — 47M reconstruction tar, imported as `demo-site` reconstruction
  UUID `46890b09-ee89-4c47-8656-238d6b868dbc`.
- `/make-it-sing/compose.local.yml` — the active backend stack for demo testing. Includes
  placeframe's compose files via `PLACEFRAME_DIR`.
- `response.md`–`response5.md`, `response8.md` — scratch at repo root. `response8.md` is this
  session's Run 1 analysis.

## Pending threads

- **Verify the new filter and tests compile.** `uv run test-unity --project Placeframe` once
  Unity's package registry is back up. **User constraint: do not run unity CLI without explicit
  permission.**
- **Apply the next round of field-driven changes** (Run 2 analysis recommendations, in priority
  order):
  1. **Snap cooldown.** New `double SecondsSinceLastSnap` on `FilterState`, incremented in
     `TickLowPass`, gates the snap branch in `ApplyMeasurement`. ~15 LOC. Demo-blocker per Run 2.
  2. **Raise `VioAnomalyDistanceBase` to ~0.75m.** One-line tweak. Lifts threshold out of the
     legitimate-noise band (accepted residuals max 0.58m, anomaly bottom quartile 0.50–0.65m).
  3. **Snap-magnitude gate.** New constants `MaxSafeSnapDistance` (~5m) and
     `HighConfidenceForSnap` (~0.95). If `vioResidM > MaxSafeSnapDistance` AND `confTight <
     HighConfidenceForSnap`, refuse the snap; stay stalled and let operator override rescue.
     Protects against the observed ~25m teleports with confTight 0.58 and 0.90.
- **Fix the two SPEC.md bugs** carried over from the rewrite: `CurrentUncertainty` (line 53),
  `VioAnomalyRotationBase` → `VioAnomalyRotationRadians` (line 86).
- **Wire Track B (Phase 2 plumbing) sooner than originally scoped.** `confidence_tight` is live
  on the wire — read it client-side, optionally use as a soft gate (drop below ~0.30) and as a
  blend weight on the low-pass.
- **Recapture demo-site map at demo time-of-day**, with particular attention to viewpoints that
  produced the ~25m perceptual aliasing in Run 2.
- **Operator-override UI wiring** (`SetEcefToUnityTransform` → button/gesture).
- Verify reconstructor pipeline: global BA + stereo scale. Open `docker/reconstructor/` and the
  reconstruction pipeline docs.
- Confirm whether the localizer reloads `calibration/global.json` without a redeploy.
- Track C spike on `fit-calibration` with the two-reconstruction recipe. Timebox 2 days.
- Decide fate of `response*.md` at repo root.
