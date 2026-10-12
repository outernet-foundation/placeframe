---
updated: 2026-05-24
---

# Relocalization redesign — end-state technical design

This is a self-contained design document for the relocalization stack's
target end state. It describes (a) the filter that fuses VPS measurements
with VIO on-device, (b) where that filter lives in the repo, (c) the
offline machinery that picks every numerical threshold the filter uses,
and (d) how all of this reconciles with the existing calibration / tuning
infrastructure that was originally built around the current single-Gaussian
filter.

It is *not* a phased plan — no ordering, no scoping into units of work, no
sequencing decisions. The migration sequencing lives in the Linear project's
`blocks` graph (the *Calibrated, aliasing-robust relocalization* project).

## Why a redesign

The shipped filter has two failure modes that cannot be patched within the
single-Gaussian Kalman shape:

1. **Perceptual-aliasing lockup.** The first few measurements after a
   `Reset` happen to be a coherent wrong cluster (self-similar map region,
   partial visibility, repeated interior). The Kalman posterior collapses
   around that pose within a handful of accepts. Subsequent correct
   measurements then arrive at multi-meter residuals the Mahalanobis
   innovation gate cannot reopen on human-walk timescales. The filter is
   permanently locked on the wrong answer; the only recovery is a
   user-initiated Stop→Start.

2. **VIO jump non-response.** There is no subscription to any
   tracking-discontinuity signal. When the underlying VIO pose jumps (AR
   session re-init, tracking-loss recovery, Magic Leap 2 tracking-origin
   reset after ≥15 s of lost tracking), the filter has no signal that its
   prior is invalid. The next measurement looks like a multi-meter
   outlier and gets rejected indefinitely.

Both failure modes stem from the same architectural limitation: a single
Gaussian cannot carry information about competing alignment hypotheses,
and a single posterior cannot be "wrong but very confident" in a way the
filter can recover from. The robust-SLAM literature
(Lajoie/Carlone 2019 discrete-continuous, Latif's RRR 2013, Olson's
max-mixtures 2013, Augmented MCL 2001) converged on multi-hypothesis
representations as the right answer for exactly this class of problem.

A second architectural mistake compounds the above: the filter math today
lives inside a Unity assembly definition (`Placeframe.Core`) and depends
on `Unity.Mathematics`, even though it has no actual need for Unity-engine
types. That placement and that dependency block two things at once: (a)
the single-source-of-truth pattern required to drive the filter from
offline tuning code without a Python re-port, and (b) the plan to consume
the same filter from Unreal and Godot apps in the future.
`Unity.Mathematics` ships under the Unity Companion License, which
restricts use to "applications, software, or other content under a valid
Unity engine license" — incompatible with non-Unity consumers regardless
of how generously the clause is read. The redesign extracts the filter
into a portable class library with no Unity-licensed dependencies and
replaces the `Unity.Mathematics` types with an in-house value-type shim,
fixing the placement at the same time as the math change so we do not
move the filter twice.

## Scope guardrails

- **No anchor-level corrections.** We publish a similarity transform with
  slew, not ARCore-style anchor re-poses. Anchors are punted as a concept.
- **Gravity is punted.** No OS-fused gravity, no gravity-prior on the
  rotation, no gravity penalty in the cost. The reasoning lives in
  `docker/reconstructor/SPEC.md` "OS-fused gravity sensor (considered
  and rejected)".
- **VPS measurements never feed back into VIO** — loose coupling, matching
  VINS-Fusion / Kimera / Lightship. The filter consumes VIO as a
  read-only signal and publishes a corrective similarity transform on
  top; the underlying VIO pose stream is unaltered. Tight coupling
  (folding VPS residuals back into the VIO state) would couple
  on-device tracking continuity to network-bound query cadence and
  introduce a single source of catastrophic drift any time VPS
  delivers a mis-aligned cluster. The architectural separation is
  enforced by the filter's API surface — it has no path to mutate VIO
  state, only to publish over it.

## Current state of the world (what we have to change)

### The filter today

`packages/unity/Placeframe/Assets/Package/Core/Runtime/RelocalizationFilter.cs`
(382 lines) implements a single-Gaussian Kalman update over an SE(3) mean
and 6×6 covariance, with a Mahalanobis innovation gate (χ²_99,6 = 16.81),
a snap-on-first-accept publish path, a 0.5 s `SmoothStep` slew, and a
`(DriftPerMeter · |Δ_vio|)²` process-noise inflation against VIO motion.
It does not subscribe to any tracking-discontinuity signal. Snap-on-first
is the direct source of perceptual-aliasing lockup; the absent
discontinuity subscription is the direct source of the VIO-jump
non-response.

The filter depends on `Unity.Mathematics`,
`MathNet.Numerics.LinearAlgebra`, and `PlaceframeApiClient.Model` (for
the wire-type `MapLocalization`). Its `ApplyMeasurement` signature also
takes `CameraFrame`, a `Placeframe.Core` struct whose pose fields are
`UnityEngine.Vector3` / `Quaternion`, so the filter's input boundary
touches Unity-engine value types even though its body uses no
`MonoBehaviour`, `UnityEngine.Time`, or `GameObject`. Severing that
input coupling — replacing the `MapLocalization` + `CameraFrame`
signature with portable pose types — is part of the extraction, not
incidental to it. The asmdef `Placeframe.Core` at
`packages/unity/Placeframe/Assets/Package/Core/Runtime/Plerion.VPS.asmdef`
also references `UniTask`, `R3.Unity`, `PlaceframeApiClient`, and
`SharpZipLib` — but those are used by neighbors of the filter, not by
the filter itself.

`packages/unity/Placeframe/Assets/Package/Core/Runtime/VisualPositioningSystem.cs`
is the Unity-engine glue. It owns the `FilterState`, subscribes a
per-frame slew tick, drives `Localize()` (HTTP call to the localizer),
feeds results through `ApplyMeasurement`, and surfaces the
`BypassInnovationGate` / `BypassKalman` diagnostic toggles plus the
`LockupRejectionThreshold = 5` / `LockupSecondsThreshold = 5 s` lockup
banner.

### Tracking-discontinuity surface today

`packages/unity/Placeframe/Assets/Package/Core/Runtime/ICameraProvider.cs`
declares only `CameraConfig()` and `Frames(intervalSeconds, ...)`. There
is no discontinuity event. Both implementations
(`ARFoundation/Runtime/CameraProvider.cs` and
`MagicLeap/Runtime/MagicLeapCameraProvider.cs` — the latter behind
`#if MAGIC_LEAP`) build a `CameraFrame` from the active provider but
never surface tracking-state transitions to the filter.

### Calibration / tuning surface today

| Artifact | Role | Status |
|---|---|---|
| `config/calibration/global.json` | The calibration artifact loaded by the localizer at startup. | Hand-tuned placeholder. `pipeline_version="placeholder"` bypasses the version check; `sample_count=0`; both tolerance models use a 1-feature logistic on `log1p(num_inliers)` with weight `1.2` and intercept `-5.5`. `sigma_meas_alpha=1.0`, `sigma_meas_beta=1.0e-3`. `loose_min=0.25`, `tight_min=0.0`. |
| `packages/python/core/src/core/calibration.py` | Pydantic schema for the artifact (`SCHEMA_VERSION = 2`); `apply_global_calibration`. The `Features` model enumerates 10 features the logistic *could* use; today only `log_inliers` is non-zero. | Production-ready. |
| `scripts/src/scripts/fit_calibration.py` | Algorithm 1: corpus → logistic + isotonic + Σ_meas (α, β). Held-out frame selection → reconstruction reuse-or-create → per-frame localize → cache rows. | Production-ready. Has never been run against a real corpus. |
| `scripts/src/scripts/tune_reconstruction.py` | Plackett-Burman sweep over `ReconstructionOptions`. Scored by map-quality metrics only. | Production-ready *for what it does*. The top-of-file comment calls out the limitation: needs localization-quality eval per cell. |
| `scripts/src/scripts/held_out_selection.py` | Frame-selector registry. | Production-ready. |
| `database` `localization_evaluations` table | Corpus cache. Keyed by `(reconstruction_id, frame_timestamp, retrieval_top_k, ransac_threshold, pipeline_version)`. Stores PnP covariance + truth-residual SE(3). | Empty in production. |
| `docker/localizer/src/build_metrics.py` | Emits `confidence_tight`, `confidence_loose`, `measurement_covariance` per localization. `measurement_covariance = α · pnp_covariance + β · I`. | Live in the pipeline. Confidences are no-ops because the placeholder thresholds leave the gate barely active. |
| `docker/localizer/src/localize.py:232` | Server-side rejection gate: raises `LocalizationError` if `confidence_loose < loose_min` or `confidence_tight < tight_min`. | Active. Kicks in only on extreme low-inlier cases under the current placeholder thresholds. |
| `scripts/src/scripts/fit_calibration.py` | Latent bug: `fit_calibration` writes localization maps at identity pose. | Only matters if the reconstructor adopts non-identity ECEF placement. |

`packages/csharp/` does not exist, and the repo contains no non-Unity
.NET projects. The portable filter library is a from-scratch creation
with no prior stubs or scaffolding to reconcile.

`scripts/` is currently Python-only: `scripts/pyproject.toml`,
`scripts/src/scripts/*.py`, `scripts/tests/`, the entry points registered
as `uv run …` commands. There is no language-subdirectory split.

## End-state filter design

### Multi-hypothesis pool with spawn / merge / prune

The single-Gaussian `FilterState` is replaced with a dynamic pool. Each
hypothesis is an SE(3) Gaussian carrying:

- `AlignmentMean` (SE(3) mean as `double4x4`).
- `AlignmentCovariance` (6×6 covariance, same tangent convention as today).
- `LastAcceptedVioPosition` (per-hypothesis — load-bearing, see below).
- An exponentially-decayed log-likelihood (the hypothesis's *evidence*),
  decay timescale `τ_evidence`.
- A timestamp / sequence number for diagnostics.

Exactly one hypothesis is the **incumbent** (its mean is the
currently-published alignment). All others are **challengers**. The pool
size is dynamic — not capped at 2 — because aliasing in non-trivial maps
can produce 3+ simultaneously coherent clusters (long corridors,
repeating store interiors, partially visible structure). A capped pool
silently drops the third hypothesis and re-introduces a death-spiral
failure mode against highly self-similar maps.

#### Lifecycle rules

- **Spawn.** A measurement that fails the Mahalanobis innovation gate
  (`Chi2_99_6dof = 16.81`) against *every* active hypothesis spawns a
  new hypothesis seeded by that measurement with bootstrap covariance.
  This is the explicit "this measurement implies a cluster nobody is
  tracking" signal.
- **Fold-in.** A measurement that passes the gate against one or more
  hypotheses folds into each accepting hypothesis via Kalman update,
  contributing to each one's accumulated evidence.
- **Merge.** Two hypotheses whose symmetric KL divergence falls below
  `KL_merge` are merged into the Gaussian product. KL is the principled
  metric — two hypotheses with identical means and very different
  covariances are not the same hypothesis, and mean-distance alone would
  treat them as such.
- **Prune.** Evidence-ratio based, not time-based: a hypothesis whose
  log-likelihood deficit vs. the pool leader exceeds `T_prune` is
  dropped. Time-based pruning implicitly assumes measurement cadence is
  known; under VPS rate variation or temporary occlusion it would
  discard correct hypotheses.

#### Publish-swap rule (incumbent replacement)

A challenger replaces the published incumbent when **both** conditions
hold:

- **Bayes factor.** The challenger's windowed log-likelihood exceeds the
  incumbent's by `log K ≥ 4.6` (i.e. K ≥ 10² — Jeffreys' "decisive
  evidence" threshold).
- **Precision floor.** The challenger's posterior σ is below an absolute
  threshold (translation σ < 30 cm, rotation σ < 1°). This prevents
  swapping to a "broadly agreeing but uncertain" cluster.

There is **no time-based forced publish**. The literature flags forced
publishes as risky (publishing on a clock rather than on evidence). The
"no recent evidence" failure mode is handled separately by the watchdog
reset below — that resets state rather than publishing without grounds.

The Bayes-factor swap also handles **first publish** without a special
case: the initial pool is one uninformative-prior hypothesis with
bootstrap covariance; the first hypothesis to accumulate decisive Bayes-
factor evidence against that prior wins and gets published. The current
"snap on first accept" behavior, which is the source of perceptual-
aliasing lockup, is gone.

#### Process noise — per hypothesis, mandatory

Each hypothesis tracks its own `LastAcceptedVioPosition` and inflates
its covariance by `(DriftPerMeter · |Δ_vio|)²` since *that hypothesis's*
last fold-in. A shared process-noise pool causes a death spiral against
aliasing: a dormant correct hypothesis stays artificially tight around
its stale mean, future correct measurements arrive at residuals it
*would* accept under properly-inflated σ but *cannot* under the stale
σ, and the mechanism designed to break aliasing is itself defeated by
aliasing. Per-hypothesis process noise is the math change that makes
the architecture work.

#### Publish deadband

When a swap (or a refined incumbent fold-in) produces a new published
mean within ε of the currently-rendered transform (Mahalanobis-normalized
SE(3) tangent norm), the internal state updates but no slew fires. ε is
set by a perceptual threshold (anchor jitter at typical viewing
distance), not by an uncertainty bound. VIO yaw drift accumulates without
bound over a session — there is no sensor reference to bound it — so an
uncertainty-shaped deadband would either widen monotonically and stop
firing or, depending on direction, fire on every refinement. A
perceptual-mean deadband is decoupled from drift accumulation and stays
well-defined for the lifetime of a session.

#### Slew

The 0.5 s `SmoothStep` slew survives unchanged. On a successful swap (or
an above-deadband refinement), `SlewStart` becomes the currently-rendered
transform, `AlignmentCurrent` slews toward the new mean. The slew tick is
unaffected by the multi-hypothesis change.

### Tracking-discontinuity signal — platform-aware abstraction

The filter needs a "VIO pose just jumped" signal so it can reset all
hypotheses to a fresh uninformative prior. No single Unity-level event
reliably signals this on both supported platforms, so `ICameraProvider`
gains an `OnTrackingDiscontinuity` event (typed as `Observable<Unit>`)
that each platform implements appropriately.

**ARFoundation / Android** (`CameraProvider.cs`). No first-class
"pose jumped" event exists in ARFoundation. The discontinuity signal is
synthesized from:

- `ARTrackingState` transitions to `Tracking` from `None` / `Limited`,
  surfaced via `ARCameraManager.frameReceived`.
- `ARSession.stateChanged` for session-lifecycle resets.
- A per-frame **pose-delta heuristic**: cache the previous VIO pose,
  raise a discontinuity whenever the inter-frame motion exceeds a
  physically plausible bound. Initial bounds (> 0.5 m / frame at 30 Hz,
  > ~30° rotation) are starting points handed to the harness sweep
  alongside the rest of the filter thresholds; the final values come
  out of the same machinery. The heuristic is the only way to
  disambiguate "VIO drifted continuously while in `Limited`" from "VIO
  hard-reset on recovery", since the state transition fires for both.

**Magic Leap 2** (`MagicLeapCameraProvider.cs`). A clean first-class
signal exists via the OpenXR Magic Leap Localization Map feature.
Subscribe to:

- `OnEventDataLocalizationChangedCallback` (Localized re-entry,
  `NewSession`).
- `XRInputSubsystem.trackingOriginUpdated` — ML2's documented behavior is
  that tracking loss for ≥ 15 s forces a tracking-origin reset on
  recovery, and this is the canonical jump event.

The ML2 ARFoundation provider does *not* translate these into
ARFoundation events; subscribing to ML-native APIs is required. The same
pose-delta heuristic stays enabled on ML2 as a belt-and-braces backstop.

### Watchdog reset (no-evidence exit hatch)

If `T_watchdog` seconds elapse with no measurement passing any hypothesis
*and* the user has moved more than `X_watchdog` meters in VIO since the
last successful fold-in, all hypotheses are cleared and a fresh
uninformative-prior pool is spawned. This catches missed discontinuity
signals, prolonged VPS dropouts during motion, and any other "evidence
drought during motion" condition. It is not a forced publish — it
*resets* state. The next measurement that passes the gate spawns the new
incumbent normally.

### Diagnostic surfaces

These exist to support A/B comparison, field debugging, and the metrics
dialog — not to drive control decisions.

**Bypass toggles.** Three orthogonal diagnostic toggles, surfaced in the
UI metrics dialog:

- `BypassInnovationGate` (existing) — every measurement folds into every
  hypothesis regardless of Mahalanobis distance.
- `BypassKalman` (existing) — measurement replaces incumbent mean
  directly, no Kalman update.
- `BypassChallengers` (new) — caps the pool at one. Restores the
  single-Gaussian behavior for A/B comparison against the new filter
  using the same captured session.

**UI surfaces.** The current filter surfaces `ConsecutiveRejections`,
`SecondsSinceLastAccept`, `IsLocalizationLost`, and the most recent
metrics. The new filter additionally surfaces:

- Number of active hypotheses.
- Incumbent log-evidence.
- Best-challenger log-evidence.
- Log Bayes factor (challenger − incumbent).
- Seconds since last publish.

The "localization lost" banner driven by `LockupRejectionThreshold` and
`LockupSecondsThreshold` is replaced by a "challenger is winning"
indicator — that's the actual user-relevant signal under the new
architecture.

### What the user observes, old vs. new

| Scenario | Old behavior | New behavior |
|---|---|---|
| First lock after Stop→Start | Snaps to first PnP result | Builds evidence silently across several measurements, then publishes once when posterior is precise and prior is decisively beaten |
| Aliased first lock (wrong cluster) | Permanently stuck; Stop→Start required | Challenger accumulates the correct cluster's evidence, swap happens automatically |
| Tracking discontinuity (AR re-init, ML2 origin reset) | Filter rejects all post-jump measurements indefinitely | Filter reset on subscribed signal; recovers normally |
| VPS dropout for 30 s while moving | Filter accumulates process noise; resumes with stale mean | Watchdog reset on prolonged silence + motion; resumes from scratch |
| Steady-state with small VPS noise | Published transform jitters per measurement (within slew) | Internal mean updates continuously; published transform stays stable until deadband exceeded |
| Three coherent aliased clusters | Single posterior splits the difference between all three | Pool maintains all three; one wins on accumulated evidence |

## End-state code structure

### Repo layout

```
packages/csharp/
├── Placeframe.Filter/           # portable .NET class library (filter math)
├── Placeframe.Filter.Tests/     # xUnit tests
└── Placeframe.Filter.sln        # ties library + tests
scripts/
├── SPEC.md
├── README.md
├── python/
│   ├── pyproject.toml
│   ├── src/scripts/             # fit_calibration, tune_reconstruction, replay_filter, …
│   └── tests/
└── csharp/
    └── replay-filter/           # .NET console harness binary
```

Three role categories applied consistently:

- `packages/` — **libraries**, regardless of language. `packages/python/`,
  `packages/csharp/`, `packages/unity/`, `packages/generated/`.
- `apps/` — **user-facing products** (Unity apps shipped to humans).
  Unchanged.
- `scripts/` — **internal-tool executables**, regardless of language.
  `scripts/python/` and `scripts/csharp/` are siblings.
- `docker/` — **deployed services**. Unchanged.

The harness is an internal-tool executable, so it lives under `scripts/`.
Its source language is .NET (required because it links the filter
library), but that's an implementation detail of how the tool is built,
not a category change.

The operator-facing CLI is still Python: `scripts/python/src/scripts/replay_filter.py`
registered as `uv run replay-filter`. It shells out to the compiled
`scripts/csharp/replay-filter/` binary. Operators never invoke the .NET
binary directly. The Python CLI's subcommand structure (likely
`score` / `sweep` / `compare`) is a harness-implementation detail and
is not locked at design time.

### Filter as a portable .NET class library

The filter math is extracted from the Unity asmdef into a portable class
library at `packages/csharp/Placeframe.Filter/`. This library:

- Targets `netstandard2.1`. Compatible with Unity 2022 LTS Mono and with
  every modern .NET runtime the harness might use. Single DLL, three
  consumers, no multi-target complexity.
- Depends only on `MathNet.Numerics.LinearAlgebra` (for 6×6 covariance
  algebra, KL divergence, matrix inversion) and `System.Math` (for
  transcendentals). The small-vector / small-matrix / quaternion value
  types are an in-house shim (see "Math primitives shim" below). No
  `UnityEngine`, no `MonoBehaviour`, no `UnityEngine.Time`, no
  `GameObject`. The library carries no Unity-licensed dependencies, so
  Unreal and Godot consumers can link it directly when those apps
  materialize.
- Contains `RelocalizationFilter`, `Se3`, the relevant parts of
  `Double4x4` / `MathUtil` the filter consumes, all the multi-hypothesis
  pool types (`HypothesisPool`, per-hypothesis state record,
  `ApplyMeasurementOptions`, `StepResult`), and the lifecycle rules
  (spawn / merge / prune / swap / watchdog).
- Has its own xUnit test project under `dotnet test`, so filter tests no
  longer require the Unity Editor to run. The existing
  `RelocalizationFilterTests.cs` regressions transplant here; multi-
  hypothesis-specific tests (aliasing recovery, spawn / merge / prune,
  Bayes-factor swap, watchdog reset) are added alongside.

The library is consumed three ways:

1. **By Unity**, as a precompiled managed DLL integrated into the
   `Plerion.VPS.asmdef` assembly's reference set. Unity surfaces
   `MathNet.Numerics` through NuGetForUnity (`packages.config`) as an
   auto-referenced plugin, not through an asmdef precompiled reference, so
   the filter DLL is integrated by the mechanism Unity honors for managed
   plugins — placement in an auto-referenced plugin location (with its
   `.meta`) and/or an explicit `precompiledReferences` entry on the asmdef
   — and its `MathNet.Numerics` dependency must bind to the single
   NuGetForUnity-provided assembly rather than bundle a second copy. The
   `VisualPositioningSystem.cs` Unity-engine glue continues to own
   subscription wiring, the slew tick subscription, the HTTP `Localize()`
   call, and the platform-specific `ICameraProvider` plumbing; it just
   calls into the portable library for the actual math.
2. **By a .NET console harness** at `scripts/csharp/replay-filter/`. The
   harness reads a corpus JSON file (serialized `localization_evaluations`
   rows) and a threshold-config JSON file (every filter knob and the
   Σ_meas form), replays the corpus through the filter, and emits a
   per-session JSON metric report. Stateless, deterministic, no
   Postgres / MinIO / network access — pure file I/O. A Pydantic model
   on the Python side defines the corpus row shape and serializes to
   JSON; the harness deserializes against a matching C# record. One
   schema, two language bindings, JSON on the wire.
3. **By Python orchestrator code** at `scripts/python/src/scripts/replay_filter.py`,
   registered as `uv run replay-filter`. The orchestrator owns all
   stateful concerns: it queries `localization_evaluations` from
   Postgres, writes one corpus JSON file per replay scope, enumerates
   sweep cells, dispatches one harness invocation per cell via
   `common.bash` (passing corpus-file and threshold-config-file paths),
   and aggregates the per-cell JSON reports into a sweep summary.
   Subprocess + JSON, not Python.NET — keeps the harness pure /
   stateless, avoids a .NET-runtime hosting dependency in the Python
   venv, and means the harness binary is trivially testable in isolation
   from a hand-crafted corpus fixture.

There is exactly one implementation of the filter math, in C#, consumed
by Unity and by the offline harness via the same DLL. A Python port is
foreclosed by construction: the drift hazard between two implementations
of a non-trivial Kalman + Bayes-factor + spawn-merge-prune algorithm is
structural and cannot be reliably patched with parity tests. A
backend-stateful-session variant is foreclosed by the loose-coupling
constraint above and by the long-term direction of moving heavy work
(ALIKED / LightGlue / PnP) onto the client. A shared-native C++ / Rust
library is the correct *eventual* answer if and when the localizer
itself migrates to native code; for ~700 lines of filter math today it
does not justify a 5+ platform cross-compilation matrix, and at that
later point the C# filter becomes the reference for parity-testing the
native port.

### Math primitives shim

`Placeframe.Filter` ships its own value-type shim for the small-vector
and small-matrix algebra the filter uses:

- `Double3`, `Double4x4`, `Quaternion` — `[StructLayout(LayoutKind.Sequential)]`
  value types covering the ~20–30 operations the filter actually
  consumes (constructors, accessors, `mul`, `dot`, `cross`, `length`,
  `normalize`, quaternion product, quaternion-vector rotation).
- Transcendentals (`sin`, `cos`, `sqrt`, `tan`, `atan2`, `sincos`)
  delegate to `System.Math` (BCL, zero dependencies).
- The 6×6 covariance algebra (matrix inverse, KL divergence,
  Cholesky-based numerics for the precision floor and merge tests) stays
  on `MathNet.Numerics`. MathNet's `Matrix<double>` is the right shape
  for the larger matrices; the in-house shim covers the value-type
  small-matrix surface where MathNet would be ergonomically and
  performance-inappropriate.

### Boundary conventions — typed at the API surface

The filter's public API is canonical: it accepts and returns poses in
OPENCV / pycolmap convention, the same convention `LocalizationResult`
arrives in over the wire and the reconstructor stores. The existing
`AxisConvention` enum (`packages/python/core/src/core/axis_convention.py`,
cases `OPENCV` / `UNITY`) ports to a C# enum in `Placeframe.Filter`,
extensible to `Unreal` / `Godot` as those consumers materialize. The
existing `change_basis_X_from_Y_pose` helpers port to a `ChangeBasis`
static class in the same library, with matrix definitions identical to
the Python so the conversion is verifiable by inspection. Engine-specific
glue (`VisualPositioningSystem.cs` for Unity; future Unreal / Godot
equivalents) owns the conversion call at the filter boundary. The
filter itself does not branch on convention. Matches the existing rule
documented in `packages/python/core/SPEC.md`: "AxisConvention is a tag,
not a dispatch."

Internal implementation choices (Rodrigues' variant, V matrix definition,
quaternion product order, tangent ordering) are pinned by a two-line
comment at the top of `Se3.cs` citing the textbook form in use (e.g.
Solà, "A micro Lie theory for state estimation in robotics," §3.4) and
locked behaviourally by the convention-targeted unit tests below. A
future maintainer who reaches for a different V matrix definition fails
the adjoint-identity test immediately — stronger guarantee than a prose
spec they could quietly disagree with.

### Convention-targeted unit tests

The shim and `Se3` Lie algebra ops are TDD'd with tests designed so each
test fails for a *specific* class of convention error rather than just
"the math is wrong":

- **Column-vs-row swap** — `Translation(t) * (0,0,0,1)ᵀ == (t.x, t.y, t.z, 1)ᵀ`.
  Fails if matrices are built row-major or applied to row vectors.
- **Handedness flip** — `RotateY(π/2) * (1,0,0,1)ᵀ` has a sign-specific
  expected value that differs under a handedness swap.
- **Quaternion storage order** — `Quaternion.Identity` asserts the `w`
  component lives in the documented slot; fails immediately on a
  scalar-first / scalar-last mix-up.
- **Quaternion product order** — `(Q_x90 * Q_y90).Rotate((1, 0, 0))`
  asserts a specific value matching the pinned right-to-left composition
  convention.
- **Lie algebra round-trip** — `Se3.Log(Se3.Exp(xi)) ≈ xi` across
  translations spanning sub-mm to Earth-scale magnitudes and rotations
  spanning sub-degree to near-π. Tolerance `1e-12`.
- **Compose-inverse identity** — `Se3.Compose(Se3.Inverse(T), T) ≈ Identity`
  for random `T`.
- **Adjoint identity** — `Se3.Adjoint(T) * xi ≈ Se3.Log(T * Se3.Exp(xi) * Se3.Inverse(T))`.
  Catches transposed adjoint formulas, sign errors in the V matrix.
- **Small-angle singularities** — `Se3.Exp(xi)` for `|xi| ∈ {1e-12, 1e-9,
  1e-6, 1e-3, 1.0, π − 1e-3}`. Catches the "blew up at small angles
  because we divided by θ without the series expansion" failure mode.
- **Matrix-multiplication associativity** — `(A * B) * C ≈ A * (B * C)`
  to `1e-12`. Catches multiplication-kernel axis errors.

Filter-level behavioural tests sit on top of the primitive tests:
perfect-measurement convergence to truth, aliasing-recovery via
challenger swap, innovation-gate rejection of outliers, KL-driven merger
of converged hypotheses, evidence-based pruning, tracking-discontinuity
reset, watchdog reset, and `BypassChallengers` collapsing to single-
Gaussian behaviour for A/B comparison.

The convention-targeted tests are designed so a CI failure localizes the
bug class structurally: primitive tests red ⇒ shim or Lie-algebra bug;
primitives green and behavioural tests red ⇒ multi-hypothesis math bug.
Git-history bisection is not the localization mechanism. There is no
shadow-deployment, no oracle-capture against the existing filter, and no
bit-equal parity comparison: the filter is being rewritten end-to-end
(single-Gaussian → multi-hypothesis), pre-alpha, with no production
traffic worth preserving compatibility against.

### Tracking-discontinuity in the provider boundary

`ICameraProvider` gains:

```csharp
public interface ICameraProvider
{
    Observable<PinholeCameraConfig> CameraConfig();
    Observable<CameraFrame> Frames(float intervalSeconds, bool useCameraPoseAnchoring = false);
    Observable<Unit> OnTrackingDiscontinuity { get; }
}
```

The ARFoundation implementation merges `ARSession.stateChanged`,
`ARCameraManager.frameReceived` → `ARTrackingState` transitions, and the
pose-delta heuristic into one Observable. The Magic Leap implementation
merges the OpenXR Localization Map callbacks,
`XRInputSubsystem.trackingOriginUpdated`, and the same pose-delta
heuristic.

`VisualPositioningSystem.cs` subscribes to the event and calls `Reset`
on the hypothesis pool.

## End-state offline tuning machinery

The multi-hypothesis design introduces a set of numerical thresholds:
`T_prune`, `T_swap`, `ε_publish`, `τ_evidence`, `KL_merge`, the precision
floor (σ_t, σ_r), the watchdog `T` and `X`, the pose-delta heuristic
translation / rotation bounds. None can be picked sensibly from first
principles alone — they're picked by replaying corpora through the
filter and scoring session-level outcomes. The harness that does this
replay is part of the end state, alongside the surviving and reshaped
pieces of the original calibration / tuning infrastructure.

### Calibration-surface delta

Three pieces of the existing server-side calibration surface change
shape under the new filter; the changes are siblings of one another
because they all describe how the calibration-side artifact and
server-side gate relate to the on-device filter.

#### Σ_meas — load-bearing, expanded to feature-conditional

The Σ_meas fit is *more* important under the new filter, not less. Every
gate / spawn / swap / merge decision is driven by the innovation
Mahalanobis distance `residual^T (Σ_predicted + Σ_meas)^-1 residual`,
and the Bayes-factor swap is driven by log-likelihoods that include
`-½ log |Σ|`. A miscalibrated Σ_meas bends every threshold
simultaneously. Σ_meas is the single most load-bearing calibration
output for the new filter.

The form expands from global `α, β` constants to linear feature-conditional
`β`:

```
Σ_meas = α · pnp_covariance + β(features) · I
β(features) = β₀ + Σᵢ wᵢ · featureᵢ
```

**Feature set: 5 per-query features.** The fit consumes:

- `log_inliers` — `log1p(num_inliers)`
- `inlier_ratio` — `num_inliers / num_correspondences`
- `reproj_err_norm` — `reproj_error_median / query_image_diagonal_px`
- `inlier_coverage` — spatial spread of inliers across the image
- `log_num_matches` — `log1p(num_matches)`

All five are mechanically derivable from columns already in
`localization_evaluations`; no schema bump and no corpus re-run is
required. The transforms match the existing `Features.compute` in
`packages/python/core/src/core/calibration.py`.

**Per-map features intentionally excluded.** The existing `Features`
model also enumerates 5 per-map features (`log_map_image_count`,
`log_map_point_count`, `map_avg_track_length`,
`log_map_bounding_volume_m3`, `map_viewpoint_diversity`). These are
constant per `reconstruction_id` and characterize the map, not the
measurement. Σ_meas describes *per-measurement* noise; map character
reaches the filter through the multi-hypothesis architecture's mechanism
design (long-corridor maps spawn more hypotheses; aliasing-prone maps
require more accumulated evidence to swap). Including per-map features
in Σ_meas would be a category error.

**Fit form: L1-regularized maximum likelihood, `λ` chosen by 5-fold
cross-validation.** Locked from day one. The parameter vector is
`[α, β₀, w₁, w₂, w₃, w₄, w₅]` = 7 numbers, with `λ` chosen externally by
CV. The objective is the negative Gaussian log-likelihood of the
corpus's truth residuals under `Σ_meas`, plus an L1 penalty
`λ · Σᵢ |wᵢ|` on the feature weights (intercept `β₀` and `α` are
unpenalized). The fit is implemented as a custom `scipy.optimize.minimize`
call because `Σ_meas` appears inside the covariance argument of the
Gaussian, not as additive output noise — `sklearn.linear_model.LassoCV`
assumes the latter form and is not applicable. λ is picked by 5-fold
cross-validation over a small grid (the specific grid is illustrative;
expand or contract once the first real fit suggests a range), scoring
each candidate on held-out negative-log-likelihood without the penalty
term. The final fit refits on the full corpus with the chosen `λ`.

L1 over L2 is for **weight stability under correlated features and
interpretability of the surviving subset**, not primarily for sparsity.
Three of the five features (`log_inliers`, `log_num_matches`,
`inlier_ratio`) are derived from the same two underlying integers
(`num_inliers`, `num_correspondences`) and are documented-correlated; an
unregularized fit would produce high-variance weight estimates that
thrash across corpus refits while predictions stay nominally stable —
textbook multicollinearity, and a *quiet* failure mode (fit converges,
residuals look fine, weights are nonsense). Detecting that failure
would itself require the same cross-validation machinery L1 needs, so
the "start unregularized, add L1 if symptoms appear" deferral saves
nothing.

Sanity checks on the fit output are diagnostic-only — they shape the
operator's reading of a fit, not an automated feedback path. Weight
signs against physical priors (more inliers should give negative
`w_log_inliers`; worse reprojection should give positive
`w_reproj_err_norm`). Number of features surviving L1: zero or one
survivor is informative, not a bug — it means the data did not support
per-feature differentiation and global `β₀` carries the model; no
re-fit is triggered. The chosen `λ` magnitude: very large ⇒ data was
sparse; very small ⇒ corpus was rich enough that overfitting was not a
real concern.

Additional derivable features (`reproj_error_iqr`, `pnp_covariance`
trace / condition number, finer spatial-distribution features) are not
pre-committed; the L1 form lets them be added later without restructuring
the fit. Localizer-output additions that require schema work (match-
descriptor statistics, VIO instantaneous-velocity, image-quality
estimates) wait for a specific signal-deficit case.

The `CalibrationArtifact` schema (`packages/python/core/src/core/calibration.py`,
`SCHEMA_VERSION = 2` today) bumps to accommodate the feature-conditional
form: `sigma_meas_beta` becomes a `(β₀, w₁, …, w₅)` structure carrying
both the intercept and the per-feature weight vector. The `loose_min` /
`tight_min` fields are removed (see below).

#### Server-side confidence gate — removed

The server-side `confidence_loose < loose_min` / `confidence_tight <
tight_min` gate in `docker/localizer/src/localize.py:232` is removed. The
multi-hypothesis filter's innovation gate + spawn rule subsume "is this
measurement useful?" with strictly more context — they know the active
hypotheses, accumulated evidence, and per-hypothesis precision. A
server-side pre-rejection can only drop measurements the client filter
would have found genuinely useful, including the "looks unconfident but
corroborates the correct challenger" case that the new architecture
exists to solve.

`loose_min` / `tight_min` go away from the artifact. The logistic +
isotonic confidence prediction *math* survives as a diagnostic feature
surfaced in the UI and logger (useful for "this query was low-confidence
and got rejected — was that right?"), but it drives no control decisions.

#### Reconstruction tuning — expanded objective

`scripts/src/scripts/tune_reconstruction.py` survives with one
substantial change: the PB-sweep cell objective expands from "map-
quality metrics only" (point count, track length, viewpoint diversity,
bounding volume, image count, plus `truth_alignment_*` residuals) to an
*end-to-end published-transform error on held-out frames after running
them through the filter*. The deferred follow-up already called out in
the top-of-file comment of the script closes with this change.

Reconstruction options affect not just map quality but the *aliasing
structure* of the resulting map. Denser maps spawn fewer false-positive
clusters; viewpoint-diverse maps reduce the rate of
high-confidence-wrong PnP results. The right cell score is downstream
filter performance, not raw map structure.

#### Per-map calibration as diagnostic

Per-map data is **diagnostic, not a control surface**. The
multi-hypothesis architecture auto-adapts to per-map character through
its mechanism design: long-corridor maps spawn more hypotheses;
aliasing-prone maps require more evidence to swap; sparse maps get
wider Σ_meas through the feature-conditional fit. What the
auto-adaptation does not capture is narrow — *persistent per-map pose
bias* (a systematic offset baked into a specific map's
reconstruction-alignment) and *aliasing rate* (invisible from any
single query — a single global `T_swap` / `KL_merge` cannot be optimal
for both a 0.1%-aliasing map and a 30%-aliasing map). Magnitude
estimate: small for average maps; ~20–40% reduction in time-stuck for
aliasing-prone maps. An order of magnitude below the architectural
win.

The dogfooding logger surfaces when a specific map consistently
misbehaves; the action is to rebuild the map with better reconstruction
options (`tune_reconstruction.py` with its expanded cell objective),
not to bespoke-tune the filter around its flaws. Per-map filter tuning
is a workaround; per-map reconstruction-options tuning attacks the root.

**Diagnostic shape — five metrics, one per filter mechanism.** The
per-map summary is a defined view over per-query logger rows grouped by
`reconstruction_id`, not a separate emission. The logger emits per-query
rows as its single source of truth; the summary is computed
consumer-side (Grafana panel, ad-hoc script, admin UI). The five fields:

- `mean_swap_latency_seconds` — sessions where swaps occurred; mean
  seconds from session start to first publish-swap that survived.
  Probes the swap mechanism.
- `challenger_spawn_fraction` — `new_spawns / accepted_measurements`
  across sessions touching the map. Probes the spawn mechanism; high
  values are the aliasing signature.
- `swap_revert_rate` — fraction of swaps reverted within
  `2 · τ_evidence` seconds. Probes the evidence-decay + Bayes-factor
  interaction; high values indicate thrashing between hypotheses with
  borderline-decisive evidence.
- `steady_state_sigma_translation_m`, `steady_state_sigma_rotation_deg`
  — incumbent σ after the first sustained 30-second lock window per
  session, median over sessions. Probes the precision floor and Σ_meas.
- `watchdog_fires_per_session_minute` — total watchdog firings ÷ total
  session minutes. Probes the evidence-drought condition; high rate
  indicates measurements are being silently rejected by every
  hypothesis.

Each metric corresponds to a specific filter mechanism, so when one
fires high the action the operator takes is structurally legible from
the metric rather than requiring a learned mental model of a compound
score. A single headline score and "raw rows only, summarize ad hoc"
were both rejected: collapsing to one number throws away the action
information; deferring the summary definition entirely makes it
expensive to reverse-engineer the schema cold. Alerting thresholds are
not locked here — they require field data to calibrate against.

### Filter-replay harness

The harness — a new .NET console executable consuming the portable
`Placeframe.Filter` library — is the single piece of new infrastructure
that ties the rest together. It does not exist today.

Inputs:

- A corpus of `localization_evaluations` rows (PnP covariance, truth
  residual, per-frame features) for a chosen reconstruction or set of
  reconstructions.
- A threshold-config JSON specifying values for every numerical knob in
  the filter (`T_prune`, `T_swap`, `ε_publish`, `τ_evidence`,
  `KL_merge`, precision floor, watchdog `T` / `X`, pose-delta heuristic
  bounds) and the Σ_meas form (`α`, `β₀`, feature weights).
- A VIO trajectory and a truth trajectory, both per-frame. **Two
  distinct sources, not to be conflated:**
  - **VIO input to the filter**: the capture device's raw recorded
    VIO. For ZED-rig bootstrap corpora this is `frames.csv` content
    (rig-grade VIO) accessed via `GET /capture_sessions/{id}/frames.csv`.
    For field corpora (the dogfooding logger), this is the per-query
    VIO pose logged client-side by the phone or ML2.
  - **Truth label for scoring**: the BA-refined per-frame pose
    `frame_poses.npz` from the reconstruction, accessed via
    `GET /reconstructions/{id}/frame_poses` with the appropriate
    `axis_convention`. Field corpora use the same reconstruction-based
    truth path as bootstrap corpora — the phone capture session is
    reconstructed, BA-refined per-frame poses serve as truth, and the
    `truth_alignment_rms_residual_m` quality gate emitted by the
    reconstructor excludes sessions with VIO too noisy to support
    coherent reconstruction. Truth is consumed only by the scoring step,
    never fed into the filter as input.
  All adapters land in the same `(state, measurement, VIO_pose) → state'`
  replay loop with a separate `score(state.published, truth_pose)` call
  per step.

Outputs (per session):

- Truth-error of the published transform: mean, median, p95, max
  translation and rotation error against the ground truth.
- Time-to-first-correct-lock — seconds from session start until the
  published transform first comes within tolerance and stays there.
- Recovery time from injected aliasing — replay a deliberately-misleading
  cluster first, measure how long until the filter recovers.
- False-swap rate — number of swaps that moved the published transform
  further from truth.
- Spurious-spawn rate — hypotheses that spawned but never accumulated
  meaningful evidence (multi-hypothesis-specific noise indicator).
- Steady-state σ — locked-state incumbent uncertainty; reality-checks
  the precision floor.
- User-visible jitter — fraction of frames where the published transform
  moved by more than user-perceptual ε.

The harness is the substrate for every numerical-threshold pick. The
Python orchestrator at `scripts/python/src/scripts/replay_filter.py`
shells out to the harness via `common.bash`, one invocation per
(Σ_meas-config × threshold-config × corpus-subset) cell.

**Output destination — local for per-cell, MinIO for summary.** The
harness writes each per-cell JSON report to a sweep-scoped local working
directory the orchestrator picks. Hot-loop file I/O stays local; no
network round-trip per cell. After all cells complete the orchestrator
aggregates locally, then uploads two artifacts to MinIO under
`s3://placeframe-sweeps/<sweep-id>/`: the aggregated sweep summary and
the threshold-config / Σ_meas-config that produced it. Together those
are the durable, human-interesting record of the sweep and the basis for
cross-sweep comparison over time. Raw per-cell JSON is *not* uploaded
by default — it is deterministically recomputable from the corpus and
the configs. An opt-in `--archive-cells` flag uploads the per-cell blobs
when investigating a specific anomalous cell justifies the storage.

**CI coverage is deferred.** The initial harness build ships with no
preflight regression test; filter math is covered by
`Placeframe.Filter.Tests`, orchestrator plumbing by pytest, and the
orchestrator ↔ harness integration boundary is the genuinely-untested
surface. The right test for that boundary is a deterministic multi-cell
mini-sweep against a synthetic perfect-measurement fixture corpus, and
it is **step one before any future modification to the harness,
orchestrator, or filter post-initial-build** — written cold-start at
the moment a change is contemplated. The interim risk window is the
lowest-risk phase of the system's life.

### Aliasing-injection regression set

A separate fixture pipeline injects synthetic aliasing into corpus
replay: take real measurements, perturb the implied pose by a fixed
offset before feeding to the filter. This tests filter math rather than
feature-matching, which is sufficient to catch the lockup failure mode.
Field-captured aliasing examples are added to the regression set as real
failures accumulate in dogfooding. A "cross-region misleading" variant
(mislabelling measurements from one part of a self-similar map as
another) is an intermediate option if synthetic proves too easy.

### Layered offline-tuning loop

Tuning is layered, not joint. The three layers measure conceptually
different things against different objectives:

- **Σ_meas is a property of the localizer's output distribution.** It is
  fit from data by maximum-likelihood against truth residuals. Its
  correct value does not depend on filter behavior — treating it as a
  filter-tuning knob is a category error that produces a Σ_meas chosen
  to flatter the filter's score on the tuning corpus, brittle the
  moment field data drifts.
- **Filter thresholds are a property of how the filter should react to
  that distribution.** Given a fitted Σ_meas, they have a correct
  answer too — picked by replaying the corpus through the filter and
  scoring session-level metrics.
- **Reconstruction options affect the input distribution to the
  localizer.** Given a fixed filter, they are tuned to make the
  localizer's output distribution easier for that filter to consume.

Within the filter-thresholds layer the sweep is joint across all filter
knobs — thresholds inside the layer are not independent (`T_swap`
interacts with `KL_merge`, the precision floor interacts with
`τ_evidence`). Across layers there is no joint refinement pass; if
field data later shows specific cross-layer mis-tuning, address that
interaction specifically rather than widening the sweep to a global
joint search at our corpus size.

The step-by-step recipe for actually running this loop — corpus gather,
Σ_meas fit, filter-threshold sweep, reconstruction-options sweep, field
validation — is left to the implementer to work out at pickup.

### Two corpus phases — bootstrap and field

The loop above runs twice over the project's life, against two
fundamentally different corpora.

**Phase A — bootstrap corpus (ZED capture held-out frames).** The only
labeled corpus that exists today. Held-out frames from ZED captures are
localized against their own reconstructions via the Algorithm 1
machinery (`scripts/src/scripts/fit_calibration.py`, documented in
`scripts/SPEC.md`); per row the corpus carries a PnP measurement, a
truth label
(BA-refined `frame_poses.npz`), a VIO sample (rig-grade VIO from
`frames.csv`), and per-frame features. Useful for validating the fit
pipeline / harness / sweep machinery end-to-end against real data, and
for producing a non-placeholder calibration good enough to ship to early
dogfooding so the filter behaves reasonably during the field-data-
collection window. The bootstrap calibration is **explicitly throwaway**
— its output characterizes ZED-rig imagery against ZED-built maps with
rig-grade VIO, which is a different distribution on every axis from
deployment.

**Phase B — field corpus (phone / ML2 dogfooding logger).** The end-
state corpus. Real phone and ML2 queries against deployed maps with
real-device VIO. Truth attribution is the same path as Phase A —
reconstruct the phone capture session, take BA-refined per-frame poses
as truth, exclude sessions failing `truth_alignment_rms_residual_m`.
The fit code path is identical to Phase A; only the corpus source
differs. Σ_meas, filter thresholds, and reconstruction-options sweeps
run against this corpus and their outputs become the deployed
calibration.

Reconstruction-based truth attribution is the only path compatible with
the Σ_meas fit. The fit consumes a 6-D SE(3) truth residual per query
plus a covariance; that residual is computable only from a per-query
truth pose. A pairwise-VIO-calibration scheme — comparing VIO-implied
relative motion against VPS-implied relative motion across pairs of
queries — produces scalar errors per pair, attributable only to scalar
errors per localization, with session-shared rigid bias absorbed into
the implicit alignment and invisible to the residual. That signal shape
does not drive a per-query SE(3) covariance fit, and the architecture
provides no scalar-to-vector attribution path. When phone-session
reconstructions fail the quality gate often enough to thin the corpus
unworkably, the response is to improve phone capture quality (longer
baselines, keyframe spacing, ARFoundation pose-anchoring tuning), not
to introduce a parallel truth-attribution path under the same
calibration artifact.

When Phase B data arrives, the Phase A calibration is **replaced
wholesale, not refined**. The Phase A weight vector is not used as a
prior, warm-start, or comparison baseline — that would smuggle ZED-
distribution bias into the field calibration. The harness, the fit
code, and the calibration artifact schema are all designed against an
abstract corpus shape both phases produce, so swapping one for the other
is just changing the data source: Phase A is sourced from Postgres +
reconstruction artifacts via the Algorithm 1 adapter, Phase B from MinIO
blobs via the dogfooding-logger adapter, but the harness's corpus loader
sees one shape after deserialization.

### Dogfooding logger schema

The phone-side dogfooding logger writes per-query JSON to MinIO. The
per-query schema captures the measurement payload (metrics, covariance,
estimated pose, VIO pose, confidence) plus filter-state per query:
active hypothesis count, evidence per hypothesis, which hypothesis (if
any) accepted the measurement, swap events, watchdog firings, and
tracking-discontinuity firings. Without the filter-state fields the
logger data cannot be used to diagnose filter mis-tuning. Query images
themselves are not logged; the per-query schema is designed so a
`query_image_id` field referencing an upload to a separate bucket can
be added later without breaking parsers, in case image-attached
inspection of failure cases becomes necessary.

**Schema lands with the filter rewrite; phone-side instrumentation
follows separately.** The logger has two pieces with very different
cost profiles: (a) the per-query corpus row schema — its field set,
JSON shape, the MinIO object layout, and the ingestion endpoint
contract — and (b) the phone-side instrumentation that actually writes
those rows. The expensive-to-change-later piece is (a): it bakes into
MinIO records, ingestion code, the fit code, and the harness corpus
loader. The expensive-to-build piece is (b). Decision: design and lock
(a) alongside the filter rewrite, defer (b) until team capacity exists.
Phase B data can start flowing as soon as someone wires phone-side
logging against the already-stable schema, narrowing the
bootstrap-calibration-as-permanent failure mode without paying the
phone-side instrumentation cost up front.

## Key files (current state — start of the redesign)

Filter math + Unity glue:

- `packages/unity/Placeframe/Assets/Package/Core/Runtime/RelocalizationFilter.cs`
  — single-Gaussian filter; moves into the portable library and
  rewrites to multi-hypothesis.
- `packages/unity/Placeframe/Assets/Package/Core/Runtime/Se3.cs` — SE(3)
  Lie algebra; moves with the filter.
- `packages/unity/Placeframe/Assets/Package/Core/Runtime/MathUtil.cs`
  and the `Double4x4` helpers — partial move (only the parts the filter
  uses).
- `packages/unity/Placeframe/Assets/Package/Core/Runtime/VisualPositioningSystem.cs`
  — Unity-engine glue; stays in the Unity asmdef but rewires to consume
  the portable library, drops `LockupRejectionThreshold` /
  `LockupSecondsThreshold` (replaced by challenger-winning indicator),
  subscribes to `OnTrackingDiscontinuity`, and adds the watchdog timer.
- `packages/unity/Placeframe/Assets/Package/Core/Runtime/ICameraProvider.cs`
  — adds `OnTrackingDiscontinuity`.
- `packages/unity/Placeframe/Assets/Package/ARFoundation/Runtime/CameraProvider.cs`
  — implements `OnTrackingDiscontinuity` via `ARSession.stateChanged` +
  `ARTrackingState` transitions + pose-delta heuristic.
- `packages/unity/Placeframe/Assets/Package/MagicLeap/Runtime/MagicLeapCameraProvider.cs`
  — implements `OnTrackingDiscontinuity` via OpenXR Localization Map +
  `XRInputSubsystem.trackingOriginUpdated` + the same pose-delta
  heuristic backstop.
- `packages/unity/Placeframe/Assets/Package/Core/Runtime/Plerion.VPS.asmdef`
  — integrates `Placeframe.Filter.dll` (auto-referenced managed plugin
  and/or `precompiledReferences` entry).
- `packages/unity/Placeframe/Assets/Package/Core/Tests/Editor/RelocalizationFilterTests.cs`
  — existing tests; either move to the new `dotnet test` project
  wholesale, or duplicate scenarios there and leave a minimal smoke test
  in the Unity Editor harness.
- `apps/AndroidMobile/Assets/Scripts/Capture/AppUI.cs` — UI surfaces for
  the new filter-state (hypothesis count, evidence, Bayes factor,
  seconds since publish; drops the lockup banner).
- `packages/unity/Placeframe/SPEC.md` — update to describe the multi-
  hypothesis architecture and the portable-library boundary.

Calibration / tuning machinery:

- `scripts/src/scripts/fit_calibration.py` — Algorithm 1 corpus
  pipeline; the Σ_meas fit extends to feature-conditional `β(features)`.
- `scripts/src/scripts/tune_reconstruction.py` — PB sweep; cell-
  objective changes to "end-to-end filter performance on held-out
  frames".
- `scripts/src/scripts/held_out_selection.py` — selector registry;
  unchanged.
- `packages/python/core/src/core/calibration.py` — schema bump;
  remove `loose_min` / `tight_min`; expand `sigma_meas_alpha` / `sigma_meas_beta`
  to feature-conditional form.
- `packages/python/core/src/core/localization_metrics.py` —
  `confidence_tight` / `confidence_loose` become diagnostic-only fields.
- `docker/localizer/src/build_metrics.py` — site that emits Σ_meas;
  applies the feature-conditional form.
- `docker/localizer/src/localize.py:232` — server-side rejection gate;
  remove.
- `config/calibration/global.json` — schema-bump candidate; refit
  against a real corpus once the harness exists.
- `scripts/SPEC.md` — describes Algorithm 1 and the calibration data
  flow; update with the reconciled story.
- `docker/localizer/SPEC.md` — describes the calibration runtime and
  the `α · pnp_covariance + β · I` formula; update to reflect the
  feature-conditional expansion and the removal of the server-side
  gate.

New surface (does not exist today, post-Phase-0-reorg paths):

- `packages/csharp/Placeframe.Filter/` — portable .NET class library
  with the filter math. Contains the in-house `Double3`, `Double4x4`,
  `Quaternion` value-type shim; the `Se3` Lie algebra; the multi-
  hypothesis pool and lifecycle rules; and `MathNet.Numerics` consumers
  for the 6×6 covariance algebra.
- `packages/csharp/Placeframe.Filter/AxisConvention.cs` and
  `packages/csharp/Placeframe.Filter/ChangeBasis.cs` — C# ports of the
  existing Python `AxisConvention` enum and `change_basis_X_from_Y_pose`
  helpers. Same matrix definitions; verifiable against the Python by
  inspection. Engine-specific glue calls these at the filter boundary.
- `packages/csharp/Placeframe.Filter.Tests/` — xUnit test project
  running under `dotnet test`. Convention-targeted primitive tests plus
  filter-level behavioural tests.
- `packages/csharp/Placeframe.Filter.sln` — solution file tying
  library and tests.
- `scripts/csharp/replay-filter/` — .NET console harness binary
  consuming the portable filter library.
- `scripts/python/src/scripts/replay_filter.py` — Python orchestrator
  entry point registered as `uv run replay-filter`. Pulls corpus rows
  from Postgres, enumerates sweep cells, shells out to the harness via
  `common.bash`, and aggregates per-cell JSON into a sweep summary.

## References

Filter / robust-loop-closure prior art:

- Lajoie et al., RA-L 2019 — discrete-continuous graphical models for
  perceptual aliasing.
  https://dspace.mit.edu/bitstream/handle/1721.1/136194/1810.11692.pdf
- Latif, Cadena, Neira, RRR (IJRR 2013) — cluster-consistency for loop
  closure.
  http://webdiis.unizar.es/~ylatif/papers/IJRR.pdf and code at
  https://github.com/ylatif/rrr
- Olson & Agarwal, max-mixtures (IJRR 2013).
  https://april.eecs.umich.edu/pdfs/olson2013ijrr.pdf
- Thrun / Fox / Burgard, Augmented MCL 2001 — w_fast / w_slow ratio.
  http://robots.stanford.edu/papers/thrun.robust-mcl.pdf
- VINS-Fusion loose coupling pattern (loop closure never feeds VIO).
  https://github.com/HKUST-Aerial-Robotics/VINS-Fusion — issue #8 has
  the authors' explicit statement.
- Niantic Lightship VPS cadence model (1–3 s queries,
  `ContinuousLocalizationEnabled` defaults False).
  https://www.lightship.games/docs/ardk/vps/vps_localization.html

Tracking-discontinuity signal sources:

- ARCore `TrackingFailureReason` enum (no pose-jump event, only
  quality-of-tracking reasons).
  https://developers.google.com/ar/reference/java/com/google/ar/core/TrackingFailureReason
- ARFoundation `TrackingState` enum (5.0).
  https://docs.unity3d.com/Packages/com.unity.xr.arfoundation@5.0/api/UnityEngine.XR.ARSubsystems.TrackingState.html
- `arfoundation-samples` #261 — Limited-state recovery gap.
  https://github.com/Unity-Technologies/arfoundation-samples/issues/261
- Magic Leap 2 — Handling Tracking Loss Events (OpenXR).
  https://developer-docs.magicleap.cloud/docs/guides/unity-openxr/head-tracking/unity-tracking-loss/
- Magic Leap 2 — Localization Map API overview.
  https://developer-docs.magicleap.cloud/docs/guides/unity-openxr/localization-map/localization-map-api-overview/
- ML2 forum — OpenXR Unity `ARSession` status (confirms the ML provider
  does not translate ML-native events into ARFoundation events).
  https://forum.magicleap.cloud/t/openxr-unity-arsession-status/3899
