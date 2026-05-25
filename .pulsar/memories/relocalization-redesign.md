---
updated: 2026-05-24
---

# Relocalization redesign — end-state technical design

This is a self-contained design document for the relocalization stack's
target end state. It describes (a) the filter that fuses VPS measurements
with VIO on-device, (b) where that filter lives in the repo, (c) the
offline machinery that picks every numerical threshold the filter uses,
and (d) how all of this reconciles with the calibration / tuning
infrastructure.

It is *not* a phased plan — no ordering, no scoping into units of work, no
sequencing decisions. The migration sequencing, the `scripts/`
reorganization, and the step-by-step tuning recipe live in
`.pulsar/memories/relocalization-plan.md`.

## Design rationale

The filter must survive two failure modes a single-Gaussian Kalman shape
cannot:

1. **Perceptual-aliasing lockup.** The first few measurements after a
   `Reset` can be a coherent wrong cluster (self-similar map region,
   partial visibility, repeated interior). A single-Gaussian posterior
   collapses around that pose within a handful of accepts; subsequent
   correct measurements then arrive at multi-meter residuals a Mahalanobis
   innovation gate cannot reopen on human-walk timescales, locking the
   filter on the wrong answer until a user-initiated Stop→Start.

2. **VIO jump non-response.** Absent a tracking-discontinuity signal, a VIO
   pose jump (AR session re-init, tracking-loss recovery, Magic Leap 2
   tracking-origin reset after ≥15 s of lost tracking) leaves the filter
   with no signal that its prior is invalid; the next measurement looks
   like a multi-meter outlier and is rejected indefinitely.

Both stem from the same limitation: a single Gaussian cannot carry
information about competing alignment hypotheses, and a single posterior
cannot be "wrong but very confident" in a recoverable way. The robust-SLAM
literature (Lajoie/Carlone 2019 discrete-continuous, Latif's RRR 2013,
Olson's max-mixtures 2013, Augmented MCL 2001) converged on multi-hypothesis
representations for exactly this class of problem.

The filter is a native C++ core (Eigen + Sophus), not engine code, for two
reasons. First, one implementation serves every consumer: Unity links it as
a native plugin via P/Invoke, the offline replay harness links the same
binary, and eventual Unreal / Godot apps link it directly — so the device
and the harness run bit-identical math *and* lifecycle, with no second port
to drift against. Second, C++ is the one ecosystem whose off-the-shelf
numerics already speak our conventions: Eigen is column-major and
`Eigen::Quaterniond` stores `[x,y,z,w]` (scalar-last), matching the
wire / reconstructor convention, and Sophus provides SE(3)
`exp` / `log` / `Adjoint` directly — so the convention-bug-prone Lie-algebra
and covariance code is library calls, not hand-rolled math.

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

## End-state filter design

### Multi-hypothesis pool with spawn / merge / prune

The single-Gaussian `FilterState` is replaced with a dynamic pool. Each
hypothesis is an SE(3) Gaussian carrying:

- `AlignmentMean` (SE(3) mean, `Sophus::SE3d`).
- `AlignmentCovariance` (6×6 covariance in the canonical rotation-first
  tangent convention).
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
factor evidence against that prior wins and gets published. There is no
snap-on-first-accept — first publish waits for decisive evidence, which is
what keeps perceptual aliasing from locking in a wrong first cluster.

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

The published transform slews to a new mean over 0.5 s via `SmoothStep`.
On a successful swap (or an above-deadband refinement), `SlewStart` becomes
the currently-rendered transform and `AlignmentCurrent` slews toward the
new mean.

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

- `BypassInnovationGate` — every measurement folds into every hypothesis
  regardless of Mahalanobis distance.
- `BypassKalman` — measurement replaces incumbent mean directly, no Kalman
  update.
- `BypassChallengers` — caps the pool at one, collapsing to single-Gaussian
  behavior for A/B comparison against the multi-hypothesis filter using the
  same captured session.

**UI surfaces.** The metrics dialog surfaces:

- Number of active hypotheses.
- Incumbent log-evidence.
- Best-challenger log-evidence.
- Log Bayes factor (challenger − incumbent).
- Seconds since last publish.

A "challenger is winning" indicator surfaces the user-relevant signal that
a swap is imminent, rather than a "localization lost" banner.

### What the user observes

| Scenario | Behavior |
|---|---|
| First lock after Stop→Start | Builds evidence silently across several measurements, then publishes once when the posterior is precise and the prior is decisively beaten |
| Aliased first lock (wrong cluster) | A challenger accumulates the correct cluster's evidence; the swap happens automatically |
| Tracking discontinuity (AR re-init, ML2 origin reset) | Filter reset on the subscribed signal; recovers normally |
| VPS dropout for 30 s while moving | Watchdog reset on prolonged silence + motion; resumes from scratch |
| Steady-state with small VPS noise | Internal mean updates continuously; published transform stays stable until the deadband is exceeded |
| Three coherent aliased clusters | Pool maintains all three; one wins on accumulated evidence |

## End-state code structure

### Repo layout

```
packages/
├── cpp/
│   └── Placeframe.Native/       # native filter core (extern "C" ABI, Eigen/Sophus, lifecycle)
└── csharp/
    └── Placeframe.Native/       # managed UPM wrapper (P/Invoke, AxisConvention, ChangeBasis, Plugins/)
scripts/
├── SPEC.md
├── README.md
├── python/
│   ├── pyproject.toml
│   ├── src/scripts/             # fit_calibration, tune_reconstruction, replay_filter, …
│   └── tests/
└── csharp/
    └── replay-filter/           # .NET console harness (P/Invokes the host build of the core)
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
Its source language is .NET (required because it P/Invokes the native
filter core), but that's an implementation detail of how the tool is built,
not a category change.

The operator-facing CLI is still Python: `scripts/python/src/scripts/replay_filter.py`
registered as `uv run replay-filter`. It shells out to the compiled
`scripts/csharp/replay-filter/` binary. Operators never invoke the .NET
binary directly. The Python CLI's subcommand structure (likely
`score` / `sweep` / `compare`) is a harness-implementation detail and
is not locked at design time.

### Filter as a native C++ core

The filter — per-hypothesis SE(3) Gaussian, error-state EKF update,
innovation gate, KL divergence, moment-matching merge, evidence decay,
Bayes-factor publish-swap, deadband, slew, **and** the multi-hypothesis
lifecycle (spawn / fold-in / merge / prune) — is a native C++ library at
`packages/cpp/Placeframe.Native/`. It:

- Is built with **CMake**, cross-compiled for the two Android ABIs via the
  NDK toolchain file — `arm64-v8a` for the phone Capture Tool, `x86_64` for
  the Magic Leap 2's x86_64 SoC — and natively for the host (the Editor and
  the harness). No iOS target exists, so the plugin is dynamic libraries
  only — no `__Internal` static-link path.
- Vendors **Eigen and Sophus via CMake `FetchContent` pinned to exact
  commit hashes**. Both are header-only, so this is checkout-and-include and
  satisfies "pin everything" without submodule UX. Eigen supplies the value
  types and 6×6 covariance algebra (`LLT` / `.inverse()` / `.solve()`);
  Sophus supplies `SE3d::exp` / `log` / `Adjoint`. There is no hand-rolled
  Lie algebra and no math shim.
- Exposes a flat `extern "C"` ABI behind an **opaque typed handle**
  (`placeframe_filter_create` / `_destroy` / `_observe` / `_publish` plus
  diagnostics getters). Poses and covariance cross as blittable POD
  structs — `Pose7` (`tx,ty,tz, qx,qy,qz,qw`) and `Cov6x6` (36 doubles) —
  so the managed side marshals nothing and a mis-sized array cannot be
  passed. The API is pull-based (managed calls native; no native→managed
  callbacks, no `[MonoPInvokeCallback]`). Errors cross as a status code,
  never as exceptions.
- Speaks only the canonical OpenCV / pycolmap convention. The 6×6 covariance
  block order is fixed to the rotation-first tangent; Sophus's
  translation-first tangent is permuted internally and never leaks across
  the boundary.

**Package identity.** The native core is the system's engine-agnostic
native-code foundation — C++ behind a flat P/Invoke ABI, consumed by Unity
and the offline harness alike — so it is named for what it is:
`Placeframe.Native`. The managed wrapper at `packages/csharp/Placeframe.Native/`
(asmdef `Placeframe.Native`, id `org.outernet.placeframe.native`) is a UPM
package carrying the P/Invoke surface, `AxisConvention`, `ChangeBasis`, and a
`Plugins/` tree of staged native binaries. The Unity package that owns the VPS
facade, camera providers, and auth glue keeps its established `Placeframe.Core`
name and the bare `org.outernet.placeframe` id — renaming it would churn that
id across every consuming app manifest and its C# namespace for no benefit —
and depends on `Placeframe.Native`. Both that binding and the harness consume
the wrapper; the dependency direction is `Placeframe.Core → Placeframe.Native`.

The rule for what belongs in the core: **geometry and numerics live here;
neural-network inference does not.** The learned models (ALIKED local
features, DIR retrieval, LightGlue matching) are engine-specific — on Unity
they run through Sentis (ONNX) on the GPU/NPU — so they stay engine-native and
feed features across the ABI into the core. The core's eventual scope is the
localizer's whole *geometry tier* (retrieval scoring, OPQ/PQ decode, 2D-3D
correspondence, PnP/RANSAC, pose refinement, covariance), which is already C++
upstream (pycolmap is COLMAP/Ceres/Eigen; FAISS is C++); because it is all
native code, the `Placeframe.Native` package accommodates that migration
without a later rename. Map *building* (the
reconstructor's SfM) stays server-side.

The core is consumed three ways from one binary:

1. **By Unity**, as a native plugin. The compiled per-ABI `.so` (and the host
   `.so`/`.dll`/`.dylib`) are staged into the `Placeframe.Native` wrapper's
   `Plugins/` tree, the binaries gitignored and their `.meta` files committed
   (PluginImporter `platformData` per the legacy Immersal precedent). A
   `[DllImport("placeframe_native")]` surface in the wrapper resolves
   `libplaceframe_native.so` from the APK at run time (the precedent is
   `MagicLeapCameraNative.cs`'s `[DllImport]`). On-device Unity is IL2CPP, but
   the math runs in the native plugin, not in managed code, so it is identical
   to the harness's by construction. `VisualPositioningSystem.cs` continues to
   own subscription wiring, the slew tick, the HTTP `Localize()` call, and the
   `ICameraProvider` plumbing; it calls into the wrapper for the actual math.
2. **By a .NET console harness** at `scripts/csharp/replay-filter/`, which
   P/Invokes the **same** C ABI against the host build of the core — same
   header, same symbols. Because it links the identical native code, replay
   is bit-identical to device for the whole filter, math and lifecycle. The
   harness reads a corpus JSON file (serialized `localization_evaluations`
   rows) and a threshold-config JSON file (every filter knob and the Σ_meas
   form), replays the corpus through the filter, and emits a per-session JSON
   metric report. Stateless, deterministic, no Postgres / MinIO / network
   access — pure file I/O. A Pydantic model on the Python side defines the
   corpus row shape and serializes to JSON; the harness deserializes against a
   matching C# record. One schema, two language bindings, JSON on the wire.
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

There is exactly one implementation of the filter, in native C++, linked by
Unity (as a plugin) and by the offline harness (the host build) from the same
source. A second port — a Python re-implementation or a hand-maintained
managed copy — is foreclosed by construction: the drift hazard between two
implementations of a non-trivial Kalman + Bayes-factor + spawn-merge-prune
algorithm is structural and cannot be reliably patched with parity tests, and
bit-identical replay is the entire reason the harness links the same binary. A
backend-stateful-session variant is foreclosed by the loose-coupling
constraint above and by the long-term direction of moving heavy work (ALIKED /
LightGlue / PnP) onto the client — where the native core is the natural home
for that geometry tier as it migrates on-device.

### Boundary conventions — managed at the engine edge

The native ABI is canonical: it accepts and returns poses in OpenCV /
pycolmap convention, the same convention `LocalizationResult` arrives in over
the wire and the reconstructor stores. Conversion to and from an engine's
native convention is **managed C#**, in the `Placeframe.Native` wrapper: an
`AxisConvention` enum (cases `OPENCV` / `UNITY`, extensible to `Unreal` /
`Godot`) and a `ChangeBasis` static class of `change_basis_X_from_Y`
conjugation helpers, ported from the Python `change_basis_*` helpers
(`packages/python/core/src/core/axis_convention.py`) with identical matrix
definitions so the conversion is verifiable by inspection. These encode our
semantic convention, not a library's, so they stay hand-written, and they are
shared by Unity and the harness (both .NET). Engine-specific glue
(`VisualPositioningSystem.cs` for Unity; future Unreal / Godot equivalents)
calls `ChangeBasis.*` at the boundary, so the native core never sees a foreign
convention. This matches the rule in `packages/python/core/SPEC.md`:
"AxisConvention is a tag, not a dispatch."

The internal Lie-algebra and covariance conventions are not pinned by prose —
Sophus and Eigen own them. The one convention the system asserts itself is the
C ABI contract: scalar-last quaternion storage and the rotation-first 6×6
covariance block order, locked behaviourally by the native ABI tests below.

### Tests

Three test surfaces, by where the code lives:

- **Native ABI + convention tests** (C++, `packages/cpp/Placeframe.Native/tests/`).
  Assert the boundary contract: scalar-last quaternion storage, the
  rotation-first 6×6 covariance block order, canonical-only input/output, and
  a clean `create` → `observe` → `publish` → `destroy` round-trip. The
  Lie-algebra and covariance numerics themselves are not re-tested — Eigen and
  Sophus own those guarantees.
- **Native filter behaviour tests** (C++). Perfect-measurement convergence to
  truth, aliasing-recovery via challenger swap, innovation-gate rejection of
  outliers, KL-driven merger of converged hypotheses, evidence-based pruning,
  tracking-discontinuity reset, watchdog reset, and `BypassChallengers`
  collapsing to single-Gaussian behaviour for A/B comparison.
- **`ChangeBasis` tests** (C# xUnit, alongside the managed wrapper). The
  basis-change conjugations stay managed, so they are tested managed —
  column-vs-row, handedness, quaternion storage order, and OpenCV↔Unity↔ECEF
  round-trips against the Python reference values.

Filter behaviour is additionally validated end-to-end through the replay
harness against the evaluation corpus. A failure localizes the bug class
structurally: native ABI tests red ⇒ boundary contract; native behaviour
tests red ⇒ multi-hypothesis math; `ChangeBasis` tests red ⇒ convention
conversion. There is no shadow-deployment, no oracle-capture against any prior
filter, and no bit-equal parity comparison against engine code — device and
harness run the same native binary, so they cannot disagree.

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

`VisualPositioningSystem.cs` subscribes to the event and calls `Reset` on the
pool through the P/Invoke wrapper.

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

`scripts/python/src/scripts/tune_reconstruction.py` survives with one
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

The harness — a .NET console executable that P/Invokes the host build of the
native `Placeframe.Native` library — is the single piece of new infrastructure
that ties the rest together.

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
preflight regression test; filter math is covered by the native
`Placeframe.Native` tests, orchestrator plumbing by pytest, and the
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
validation — lives in `.pulsar/memories/relocalization-plan.md`.

### Two corpus phases — bootstrap and field

The loop above runs twice over the project's life, against two
fundamentally different corpora.

**Phase A — bootstrap corpus (ZED capture held-out frames).** The only
labeled corpus that exists today. Held-out frames from ZED captures are
localized against their own reconstructions via the Algorithm 1
machinery (`scripts/python/src/scripts/fit_calibration.py`, documented in
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

## Key files

Native filter core:

- `packages/cpp/Placeframe.Native/` — the native filter: `extern "C"` ABI
  header, the multi-hypothesis pool and lifecycle, Eigen/Sophus numerics, the
  CMake build, and native ABI + behaviour tests.

Managed wrapper — UPM package, asmdef `Placeframe.Native`, id `org.outernet.placeframe.native`:

- `packages/csharp/Placeframe.Native/` — the `[DllImport]` P/Invoke surface,
  `package.json`, and the `Plugins/` tree holding the staged per-ABI native
  binaries and their committed `.meta` files.
- `packages/csharp/Placeframe.Native/AxisConvention.cs`, `ChangeBasis.cs` — C#
  ports of the Python `AxisConvention` enum and `change_basis_X_from_Y_pose`
  helpers; identical matrix definitions, verifiable against the Python by
  inspection.

Unity engine binding — UPM package `Placeframe.Core`, id `org.outernet.placeframe`, depends on `Placeframe.Native`:

- `packages/unity/Placeframe/Assets/Package/Core/Runtime/VisualPositioningSystem.cs`
  — Unity-engine glue: owns subscription wiring, the slew tick, the HTTP
  `Localize()` call, `ChangeBasis` conversion at the boundary, the watchdog
  timer, and the `OnTrackingDiscontinuity` subscription that resets the pool.
- `.../Core/Runtime/ICameraProvider.cs` — declares `OnTrackingDiscontinuity`.
- `.../ARFoundation/Runtime/CameraProvider.cs` — implements it via
  `ARSession.stateChanged` + `ARTrackingState` transitions + pose-delta
  heuristic.
- `.../MagicLeap/Runtime/MagicLeapCameraProvider.cs` — implements it via OpenXR
  Localization Map + `XRInputSubsystem.trackingOriginUpdated` + the same
  pose-delta backstop.
- `.../Core/Runtime/Plerion.VPS.asmdef` — the `Placeframe.Core` asmdef;
  references the managed `Placeframe.Native` wrapper.
- `apps/AndroidMobile/Assets/Scripts/Capture/AppUI.cs` — UI surfaces for the
  filter state (hypothesis count, evidence, Bayes factor, seconds since
  publish; the "challenger is winning" indicator).
- `packages/unity/Placeframe/SPEC.md` — the multi-hypothesis architecture and
  the native-core boundary.

Harness:

- `scripts/csharp/replay-filter/` — .NET console harness; P/Invokes the host
  build of the native core.
- `scripts/python/src/scripts/replay_filter.py` — Python orchestrator
  (`uv run replay-filter`); pulls corpus rows from Postgres, enumerates sweep
  cells, shells out to the harness via `common.bash`, aggregates per-cell JSON.

Calibration / tuning machinery:

- `scripts/python/src/scripts/fit_calibration.py` — Algorithm 1 corpus
  pipeline; the Σ_meas fit extends to feature-conditional `β(features)`.
- `scripts/python/src/scripts/tune_reconstruction.py` — PB sweep; cell-
  objective changes to "end-to-end filter performance on held-out
  frames".
- `scripts/python/src/scripts/held_out_selection.py` — selector registry;
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
