# Placeframe Unity Package

## What this is

The Unity-side of Placeframe's relocalization pipeline. Periodically captures camera frames, sends them to the localizer service, and uses the returned 6-DOF pose to align local VIO (ARFoundation) coordinates to a prebuilt COLMAP map. The aligned coordinate system enables placing and reading global-coordinate-anchored content on the device.

This document describes the design rationale for the package's runtime behavior. Operating instructions for the project as a whole live in the top-level `CLAUDE.md`.

## Architecture

Three pieces sit under `Assets/Package/Core/Runtime/`:

- **`VisualPositioningSystem.cs`** — static class running a 1Hz localization coroutine and feeding results into `RelocalizationFilter`.
- **`RelocalizationFilter`** — Bayesian filter over the ECEF→Unity alignment. State `(μ, Σ)` where μ is a 4×4 SE(3) transform and Σ is a 6×6 covariance in se(3) tangent coordinates.
- **`GeoPose.cs`** — thin transformer: ECEF position + rotation in, current Unity position + rotation out. Recomputed when VPS publishes a transform-updated event. Carries no smoothing of its own.

```
camera frame ──► /localize ──► (T_meas, Σ_meas, confidence)
                                       │
                                       ▼
                               RelocalizationFilter
                               - innovation gate
                               - Bayesian update
                               - snap vs slew
                                       │
                                       ▼
                          _unityFromEcefTransform_current
                          + OnEcefToUnityWorldTransformUpdated
                                       │
                                       ▼
                                   GeoPose.cs
                                   (recomputes its
                                    Unity transform)
```

The OGC GeoPose 1.0 standard is informally referenced by the name; no formal conformance is claimed.

## Design goals (priority order)

1. **Calibrated confidence**: every localization carries a probabilistic claim — `P(translation_error < 5cm AND rotation_error < 1°)` (`tight`) and `P(translation_error < 30cm AND rotation_error < 5°)` (`loose`) — fit on real data. The filter consumes `Σ_meas` directly; confidence is a binary reject gate upstream of the filter (server-side; see `docker/localizer/SPEC.md`).
2. **Map-aware confidence**: probabilities interpret raw metrics in the context of the specific map (size, density, indoor/outdoor, viewpoint diversity).
3. **Device-aware confidence**: calibration accounts for distribution shift between map-source-device (ZED) and query-device (phone).
4. **Temporally stable alignment**: the global ECEF→Unity transform itself is smoothed by the filter, not just snapped per-update.
5. **Smooth visual updates**: alignment changes apply via SE(3) interpolation centralized at the VPS layer. `GeoPose` no longer Lerps internally — visual smoothness comes from upstream.
6. **Maintainable**: calibration artifacts iterate on a different cadence than localizer code; calibration changes don't require Docker rebuilds.

### Non-goals

- Multiple simultaneously-loaded maps. Multi-map fusion is its own future work.
- ARFoundation `ARAnchor` integration (true spatial anchoring). Visual stability comes from the centralized slewer.
- Online / continuous calibration. Calibration is fit offline and deployed as static artifacts.

## `RelocalizationFilter` design

### State

```csharp
private static double4x4 _unityFromEcefTransform_current = double4x4.identity;
private static double4x4 _unityFromEcefTransform_target  = double4x4.identity;
private static Matrix6x6 _alignmentCovariance            = LargeInitialUncertainty;
private static double4x4 _slewStart                      = double4x4.identity;
private static float     _slewProgress                   = 1f;  // 1 = settled
private static double    _lastMeasurementTimestamp;
```

### Public API

```csharp
public static double4x4 EcefToUnityWorldTransform => _unityFromEcefTransform_current;
public static event Action OnEcefToUnityWorldTransformUpdated;
public static AlignmentUncertainty CurrentUncertainty => SummariseCovariance(_alignmentCovariance);
public static LocalizationMetrics MostRecentMetrics { get; private set; }
public static LocalizationMetrics LastReceivedMetrics { get; private set; }
public static event Action OnMetricsReceived;
```

`AlignmentUncertainty` is a small struct: `{ float TranslationStdMeters; float RotationStdDegrees; }`. UI consumers that want a scalar "how confident is the alignment" use this.

`MostRecentMetrics` is the metrics from the last *accepted* measurement (filter state). `LastReceivedMetrics` is the metrics from the last *received* server response, regardless of filter accept/reject. `OnMetricsReceived` fires per API response. UI consumers wanting per-measurement updates bind to `OnMetricsReceived` rather than `OnEcefToUnityWorldTransformUpdated`, since the latter only fires on snap or during slew animations and goes silent in steady state. This split exists because diagnostic UI for a steady-state filter has no other event to bind to.

### Measurement processing

Triggered by the R3 observable when a localization response arrives. **All state mutations happen on the Unity main thread**: the R3 pipeline marshals the callback (via `UniTask.SwitchToMainThread()` — the existing pattern in this codebase) before touching VPS state. The math itself can run on the background thread; only the apply-to-state step runs on main. The Bayesian update math is microseconds of work, so running it on the main thread inside the marshalled callback is fine. No locks required.

```
on measurement (T_meas, Σ_meas, confidence):

  # Server-side gate has already rejected confidence.loose < calibration.loose_min;
  # measurements that arrive here pass the gate.

  # Predict prior. The alignment is a static relationship between ECEF and Unity
  # world; device motion does not drift it, so the mean is unchanged. VIO motion
  # inflates uncertainty only.
  vio_motion = VIOMotionSince(_lastMeasurementTimestamp)
  μ_predicted = _alignmentMean
  Σ_predicted = _alignmentCovariance + ProcessNoise(vio_motion)
    # ProcessNoise: (drift_rate * ||vio_motion.translation||)^2 added to diagonal,
    # rotation drift proportional to motion. Default drift_rate = 0.01 (1%/m).
    # Plus BaseProcessNoise{Translation,Rotation}VariancePerTick (1e-4 m², 1e-6 rad²)
    # added unconditionally — see "σ_posterior lock-in" below.

  # Mahalanobis innovation gate
  residual_se3 = log(μ_predicted⁻¹ · T_meas)   # 6-vector in se(3) tangent space
  innovation_cov = Σ_predicted + Σ_meas
  m_dist = residual_se3.transpose() @ inv(innovation_cov) @ residual_se3
  if m_dist > Chi2_99_6dof:  # ~16.81
    log_dropped("innovation gate")
    return

  # Bayesian update
  K = Σ_predicted @ inv(Σ_predicted + Σ_meas)
  μ_new = μ_predicted ⊕ (K @ residual_se3)
  Σ_new = (I - K) @ Σ_predicted

  # Snap vs slew
  posterior_shift = log(_unityFromEcefTransform_current⁻¹ · μ_new)
  shift_mag = sqrt(posterior_shift.transpose() @ inv(Σ_new) @ posterior_shift)
  if shift_mag > SnapThresholdSigmas:  # default 6σ
    _unityFromEcefTransform_current = μ_new
    _slewProgress = 1f
  else:
    _slewStart = _unityFromEcefTransform_current
    _unityFromEcefTransform_target = μ_new
    _slewProgress = 0f
  _alignmentCovariance = Σ_new
```

### Slew loop

In `Update()` on the main thread, every frame:

```
if _slewProgress < 1f:
  _slewProgress = min(1f, _slewProgress + Time.deltaTime / SlewDurationSeconds)
  t = SmoothStep(_slewProgress)
  _unityFromEcefTransform_current = SE3Lerp(_slewStart, _unityFromEcefTransform_target, t)
  OnEcefToUnityWorldTransformUpdated?.Invoke()
```

`SE3Lerp` decomposes both endpoints into `(translation, rotation_quaternion, scale)`, lerps translation linearly, slerps rotation, lerps scale linearly, recomposes. **Never lerp the 4×4 matrix component-wise.**

`SlewDurationSeconds` default: 0.5.

### Bootstrap

At session start, no prior:
- `_alignmentCovariance` initialized to a large-but-finite matrix (translation σ = 100m, rotation σ = 180°). Vague enough that the first innovation gate accepts almost any plausible measurement.
- The first accepted measurement triggers a snap (posterior shift exceeds 6σ against the giant initial covariance). Subsequent measurements slew.

### σ_posterior lock-in

Without a per-tick base process noise term, σ_posterior shrinks to ~σ_meas/√N after N stationary measurements. Once it gets small enough, subsequent measurements that disagree with the converged posterior by >3σ get rejected by the innovation gate even when their quality metrics are statistically identical to accepted ones. The filter "locks in" to its first cluster of measurements and can't absorb new evidence — the textbook "no process noise" failure mode.

The pre-fix `ProcessNoise(currentVioPosition, lastAcceptedVioPosition)` only added Σ proportional to translated distance. Stationary observation → unbounded σ_posterior shrinkage → over-confident filter.

`BaseProcessNoise{Translation,Rotation}VariancePerTick` constants (1e-4 m², 1e-6 rad²) are added unconditionally on every measurement. Sized so steady-state σ_posterior stays roughly σ_meas/3 at 1Hz query cadence and bootstrap σ_meas. The cost is visible micro-jitter in steady-state instead of full stop. The tradeoff is product-dependent — for "place a virtual object on a surface" UX the prior rock-solid behavior may be preferable; for "produce ground-truth pose telemetry" the per-tick noise is correct. These numbers re-tune against fitted Σ_meas once corpus calibration replaces the starter (see `plan.md`).

## Confidence usage

The frontend has **no `if confidence < X reject`** — that gate lives server-side in the localizer (see `docker/localizer/SPEC.md`). Measurements that reach the filter have already passed `confidence.loose >= calibration.loose_min`.

Confidence flows into the filter through `Σ_meas`, not as a scalar trigger. The textbook Bayesian way to use a calibrated probability: a low-confidence measurement is treated as a wide-σ measurement and naturally gets little weight in the Bayesian update; a high-confidence measurement gets tight σ and dominates. No magic threshold to pick frontend-side.

`Σ_meas` itself comes from the localizer as `α · PnP_cov + β · I` where α/β are fit empirically per-pipeline-version (server-side). The frontend filter consumes this Σ as authoritative — it does not rescale by confidence, does not floor, does not clamp.

## Open tunables

These have empirical defaults; the right values are tuning details for post-deployment.

| Parameter | Default | Where used |
|---|---|---|
| Slew duration | 0.5 s | slew loop |
| Snap threshold (sigmas) | 6 | posterior-shift snap criterion |
| Process noise (VIO drift) | 1% / m | prior prediction |
| Initial alignment covariance | σ_t = 100 m, σ_r = 180° | bootstrap |
| `BaseProcessNoiseTranslationVariancePerTick` | 1e-4 m² | per-tick prior inflation (lock-in fix) |
| `BaseProcessNoiseRotationVariancePerTick` | 1e-6 rad² | per-tick prior inflation (lock-in fix) |
| `SnapThresholdSigmas` | 6 | snap-vs-slew criterion |

## Risks and unknowns

- **PnP covariance is optimistic.** The Hessian-derived covariance assumes Gaussian residuals on the matched inlier set. With LightGlue's hard outlier pruning the residual distribution may not be Gaussian, and the resulting covariance may be tighter than reality. The α/β empirical fit (`α · PnP_cov + β · I`) is the corrective surface — it absorbs the model error empirically against held-out frames. If the running filter behaves badly (overconfident on bad measurements), revisit the fit.
- **VIO drift on lower-end phones.** The 1% process noise default is reasonable for flagship phones; lower-end Android may need 2-3%. Until per-device tuning exists, the global default is a compromise.
- **Cold-start UX.** With a wide initial alignment prior, the first measurement that passes the server-side gate snaps into place. If that first measurement is a low-quality outlier (gate-passable but actually wrong), it produces a visible bad initial alignment that subsequent measurements correct. Mitigations available: tighten `loose_min`, require N measurements to pass a higher bar before exiting `Initializing`, or require multiple measurements to agree before exiting bootstrap. Defer mitigation to post-deployment tuning.

## Out of scope

- Multi-map handling.
- ARFoundation `ARAnchor` integration.
- Online / continuous calibration.
- Image-content logging in dogfooding (deferred but designed-for; see `plan.md`).
- Per-device-class calibration partitioning (currently treated as a single phone population).
- Background re-fitting automation (cron, CI scheduled jobs).
- Admin UI for calibration management.
