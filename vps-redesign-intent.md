# VPS Confidence, Calibration, and Fusion — Intent

> Execution and progress tracked in [`plan.md`](plan.md).
> Companion design intent: [`e2e-and-calibration-intent.md`](e2e-and-calibration-intent.md) — owns the calibration internals (Algorithms 1–3, fit pipeline, runtime loader, artifact format, corpus). This file owns the VPS frontend (Bayesian filter, slew, dogfooding logger) and the localizer's API contract for calibrated responses.

## Status

Design intent. Going-for-broke version: the goal is a system that is as accurate as practical under as many conditions as practical, with no compromises taken for shippability that aren't necessary.

Phases 0, 1, and 2a have shipped and the system has been used end-to-end against a real reconstructed map. The findings below update the design forward.

## Production bring-up findings

### Calibration-stub band-aids in place pending the e2e-and-calibration initiative

`apply_global_calibration(calibration, features={})` currently returns model-intercept constants because no features are plumbed through and the model is the identity bootstrap. This breaks two downstream consumers, both of which have band-aids in place that are removed when the first real calibration ships. See [`e2e-and-calibration-intent.md`](e2e-and-calibration-intent.md) for the full plan.

**1. Confidence values (`tight`, `loose`) are constants** — same for great and garbage poses. A confidence-based gate at the localizer or filter would treat all results identically. *Band-aid*: a hard floor on raw metrics (`MIN_NUM_INLIERS = 50`, `MIN_INLIER_COVERAGE = 0.15` in `docker/localizer/src/localize.py`) rejects garbage results before they propagate. Replaced by `if metrics.confidence.tight < TIGHT_MIN: raise LocalizationError(...)` once the corpus is gathered and a real calibration is fit.

**2. Σ_meas scaling collapses** — `Σ_meas = PnP_cov / tight²` with constant `tight = 0.5` gives only 4× inflation. PnP's analytic Hessian covariance is wildly tight (~1e-6 variance, σ ≈ 0.3mm), so post-scaling Σ_meas is still absurdly tight. The Bayesian filter's innovation gate then rejects nearly every measurement as implausibly far. *Band-aid*: the bootstrap calibration's `tight.logistic.intercept` is set to `ln(0.01/0.99) ≈ -4.595` so `sigmoid(intercept) = tight = 0.01`, producing 10000× covariance inflation and effective σ_meas ≈ 10cm. Runtime logic in `build_metrics.py` is unchanged — the `Σ_meas / tight²` formula does the right thing once `tight` is a sensible constant. Replaced by per-localization tight values from a fitted model once the corpus is gathered.

### Σ_posterior lock-in (fixed; re-tuning deferred to post-calibration)

Observed in production: once the filter had accepted ~30 measurements during a stable session, σ_posterior shrank to ~σ_meas/√N (~2cm on each axis). Subsequent measurements that disagreed with the converged posterior by more than ~3σ got rejected by the innovation gate, even when their quality metrics were statistically identical to accepted ones. The filter "locked in" to its first cluster of measurements and couldn't absorb new evidence.

This was the textbook "no process noise" failure mode. The pre-fix `ProcessNoise(currentVioPosition, lastAcceptedVioPosition)` added Σ proportional to translated distance and nothing when the device was stationary. Stationary observation → unbounded σ_posterior shrinkage → over-confident filter.

**Fix shipped**: added `BaseProcessNoise{Translation,Rotation}VariancePerTick` constants (1e-4 m², 1e-6 rad²) to `RelocalizationFilter`, applied unconditionally in `ProcessNoise()`. Sized so steady-state σ_posterior stays roughly σ_meas/3 at the current 1Hz query cadence and bootstrap σ_meas. The numbers are coarse band-aids — they get re-tuned once σ_meas comes from a fitted model rather than the bootstrap intercept (see [`e2e-and-calibration-intent.md`](e2e-and-calibration-intent.md)). Cost: visible micro-jitter in steady-state instead of full stop. Tradeoff is product-dependent — for "place a virtual object on a surface" UX, the prior rock-solid behavior may be preferable; for "produce ground-truth pose telemetry", the per-tick noise is correct.

### Frontend metrics-event design gap

The original design exposed `OnEcefToUnityWorldTransformUpdated` as the only event. Once the Bayesian filter is steady-state, that event fires only on snap (rare) or during slew animations (brief, and only when σ_posterior shifts enough to trigger a slew). UI consumers that want per-measurement metrics — including any "live metrics" diagnostic display — can't bind to it usefully. Added `OnMetricsReceived` event + `LastReceivedMetrics` static property that fire on every API response regardless of filter accept/reject. Reflected in Frontend changes section below.

### LightGlue per-request time (was dominant, no longer)

Per-stage instrumentation in `docker/localizer/src/localize.py` (logged as `localize timings(ms): canonicalize=… aliked=… …`) originally showed LightGlue matching at ~250 ms (44% of total per-request time). That finding motivated an investigation into LightGlue's pruning/precision flags; the durable record lives in the comment on `load_lightglue` in `packages/python/neural-networks/src/neural_networks/models.py`. Net effect of the shipped change (`depth_confidence=0.95`, `mp=True`): matching dropped to ~140 ms median (29-query sweep), no longer the dominant phase — roughly comparable to `dir_tiles + matching_setup` combined.

Relevant for Phase 2d (masking) sizing: per-request total varies with map size and query difficulty; against the test map used during bring-up, post-V2 total runs ~700 ms median (down from ~840 ms pre-V2 on the same map). Masking adds OneFormer-Swin-T at ~100–200 ms. Total stays under the 1 Hz client cycle budget but with less headroom than the pre-V2 numbers suggested. ALIKED + DIR remain cheap enough that masking is still affordable.

### Operating-point reality check

System currently lands at ~1cm visual misalignment in indoor testing. This is at or slightly below what the published literature reports as the noise floor for hloc-style pipelines (LaMAR, KAPTURE, hloc indoor benchmarks all report 2-10cm depending on scene difficulty). Further accuracy gains would require things outside Phase 3's scope: per-device intrinsics calibration, map georeferencing against ground truth, or fundamentally different feature extractors. Filter tuning alone won't help meaningfully — the σ_posterior lock-in fix above is about responsiveness/correctness of the average, not about reducing the floor itself.

## Context

### What this system is

Placeframe is a self-hosted XR relocalization service. A Unity client (currently Android phone in the Capture Tool app) periodically captures camera frames, sends them to the localizer, and uses the returned 6-DOF pose to align its local VIO (ARFoundation) coordinate system to a prebuilt COLMAP map. The aligned coordinate system enables placing and reading global-coordinate anchored content on the device.

### Current state (before this redesign)

The Visual Positioning System (`packages/unity/Placeframe/Assets/Package/Core/Runtime/VisualPositioningSystem.cs`) runs a 1-second-interval localization coroutine. Each result goes through:

1. A single-metric rejection: drop the result if `NumInliers < 175`.
2. A "minimum adjustment" rejection: drop if both translation delta and rotation delta from the current alignment are below noise-floor thresholds.
3. Direct overwrite of the static `_unityFromEcefTransform` field.
4. An event that triggers downstream `Anchor` MonoBehaviours to lerp toward their newly-computed local positions.

There is no temporal logic, no multi-signal confidence, no covariance, no smoothing of the reference frame itself, no calibration. The `Anchor` class does per-frame visual lerping to absorb update jitter, with a 10m / 90° snap threshold — operationally a band-aid for the unfiltered upstream stream.

### Why this needs to change

The current pipeline conflates three failure modes that should be handled separately:

- **Per-result quality variance**: some localizations are great, some are noisy, some are wildly wrong. Inlier count alone doesn't separate these robustly — high-inlier-count results in textureless or repetitive scenes can still be wrong by meters.
- **Map-dependent metric meaning**: a localization with 200 inliers means very different things in a 5000-image dense indoor map vs a 200-image sparse outdoor map. A fixed inlier threshold is wrong somewhere.
- **Reference-frame jitter under correlated noise**: even a stream of "good" results contains correlated per-frame matching jitter. Each result snapping into the alignment manifests as visible scene wobble. The per-Anchor lerp absorbs only the visual symptom; it doesn't make the alignment itself more stable.

### Design goals

Stated in priority order:

1. **Calibrated confidence**: every result carries a probabilistic claim — `P(translation_error < 5cm AND rotation_error < 1°)` and `P(translation_error < 30cm AND rotation_error < 5°)` — fit on real data.
2. **Map-aware**: confidence interprets metrics in the context of the specific map being localized against, including its size, density, and other quality properties.
3. **Device-aware**: confidence calibration accounts for the distribution shift between map-source-device (ZED) and query-device (phone).
4. **Temporally stable alignment**: the global ECEF→Unity transform itself is smoothed by a Bayesian filter, not just snapped per-update.
5. **Smooth visual updates**: alignment changes apply via interpolation centralized at the VPS layer, not per-Anchor band-aids.
6. **Maintainable**: calibration artifacts iterate on a different cadence than localizer code; calibration changes don't require Docker rebuilds.

### Design non-goals

- **Multiple loaded maps**. The system supports only one active map at a time. Any references to "per-map" calibration mean per-map-fit-once, not multi-map fusion. Multi-map is its own future ticket.
- **ARFoundation `ARAnchor` integration**. True spatial anchoring (pinning content to local VIO features) is out of scope here; visual stability comes from the centralized slewer.
- **Online learning / continuous calibration**. Calibration is fit offline, deployed as static artifacts. Online adaptation is future work.

---

## Architectural overview

The redesign touches three layers:

```
                         ┌──────────────────────────────────┐
                         │  Unity client (AndroidMobile)    │
                         │                                  │
  Frame, VIO ─────────►  │  VisualPositioningSystem         │  ─────► AR session, GeoPose
                         │   - Bayesian filter on alignment │           render targets
                         │   - Mahalanobis innovation gate  │
                         │   - SE(3) slew loop              │
                         │   - dogfooding logger (toggle)   │
                         └─────────────┬────────────────────┘
                                       │ POST /localize
                                       │ POST /calibration-data (dogfooding only)
                                       ▼
  ┌───────────────────────────────────────────────────────────┐
  │ Localizer service                                         │
  │   - PnP + RANSAC + Hessian covariance                     │
  │   - Calibration loader: global (config volume) +          │
  │     per-map (MinIO, lazy)                                 │
  │   - Pipeline-version compatibility check at startup       │
  │   - Returns Confidence + Covariance + raw metrics         │
  └───────────────────────────────────────────────────────────┘
                                       ▲
                                       │ mounted at startup
                                       │
  ┌────────────────────┐       ┌───────┴──────────────────┐
  │ Git repo           │       │ MinIO                    │
  │  config/           │       │  maps/{id}/calibration   │
  │   calibration/     │       │  calibration-data/       │
  │   global.json      │       │   (raw dogfooding logs)  │
  └────────────────────┘       └──────────────────────────┘
            ▲                                ▲
            │                                │
        offline pipeline ─────────────────── │
        (scripts/fit_calibration.py)         │
            ▲                                │
            └────────────────────────────────┘
                  reads dogfooding data,
                  fits new calibration,
                  outputs JSON
```

**Backend**: localizer returns calibrated confidence and PnP covariance alongside existing metrics. Calibration artifacts are loaded at startup from two sources: global from a config-volume-mounted git-controlled file, per-map from MinIO alongside the map.

**Frontend**: VPS becomes a small Bayesian filter. New measurements gate via Mahalanobis distance, update a running posterior `(μ_align, Σ_align)` on the ECEF→Unity alignment, and the alignment slews toward the posterior mean over ~500ms. `GeoPose` (the renamed `Anchor`) reads the live alignment and recomputes its local pose; the Lerp inside it goes away.

**Calibration pipeline**: an offline Python job pulls dogfooding data, fits the two-stage calibration (ZED held-out + phone-side correction), produces JSON artifacts. Engineers review the diff and merge a PR for the global model. Per-map artifacts are produced automatically and uploaded to MinIO.

---

## Backend changes

### Localizer response: extended `LocalizationMetrics`

Add three fields to the existing `LocalizationMetrics` (defined in `packages/generated/csharp/api-client/...` and the corresponding Python pydantic model that the localizer returns):

- `Confidence`: a `Confidence` sub-object (see below). Contains both tight and loose tolerance probabilities.
- `Covariance`: a `float[6][6]` (or `float[36]` row-major) representing the 6-DOF pose covariance from the inverse Hessian at the PnP optimum. Computed by `pycolmap.absolute_pose_estimation` (or equivalent) with covariance return enabled. Meaningful as a sorting/weighting signal; not claimed as calibrated probability.
- `PipelineVersion`: a string identifier for the localizer pipeline version that produced this result. Allows clients to verify they're consuming results from a calibrated pipeline.

Confidence shape:

```
Confidence:
  tight:  float in [0, 1]   # P(translation_err < 5cm AND rotation_err < 1°)
  loose:  float in [0, 1]   # P(translation_err < 30cm AND rotation_err < 5°)
  is_calibrated: bool        # false only if calibration artifact unavailable; should never be false in practice
```

All raw metrics (`NumInliers`, `InlierRatio`, `ReprojectionErrorMedian`, `InlierCoverage`, `NumMatches`, `NumCorrespondences`) remain in the response. The frontend uses `Confidence` for gating; the raw metrics are kept for debugging, telemetry, and future re-fits.

### Pipeline version

The localizer computes a deterministic hash of all inputs that affect metric distributions:

- Feature extractor identity + version + critical hyperparameters (e.g., SuperPoint score threshold).
- Matcher identity + version + critical hyperparameters (e.g., LightGlue confidence threshold).
- RANSAC iteration count, inlier threshold, PnP solver choice.
- Image preprocessing (resize, normalization).

This hash is `PipelineVersion`. It's computed once at service startup and embedded in every response. Calibration artifacts carry the same hash as metadata; mismatch at startup is a hard failure (see "Failure modes" below).

### Calibration loader, confidence computation, map quality features

Owned by [`e2e-and-calibration-intent.md`](e2e-and-calibration-intent.md). Briefly: the localizer loads `config/calibration/global.json` at startup (hard-fails on missing file or pipeline-version mismatch), lazily loads per-map calibrations from MinIO on first request, computes `Confidence` from a logistic + isotonic over transformed metrics and map-quality features. Map-quality features (image count, point count, avg track length, bounding volume, viewpoint diversity, indoor flag) are computed at map-build time and stored on the maps table.

### Failure modes

| Condition | Behavior | Rationale |
|---|---|---|
| Global calibration file missing at startup | Hard-fail startup | Indicates a broken deploy. |
| Global calibration pipeline-version mismatch | Hard-fail startup | Indicates a stale calibration vs new pipeline; refit required before serving. |
| Per-map calibration missing | Soft-fail: log + fall back to global-only | Expected for new/sparse-data maps; system still functional. |
| Per-map calibration pipeline-version mismatch | Soft-fail: log + fall back to global-only | Stale per-map; rebuild on next refit cycle. |
| Localizer fails to produce a pose at all (e.g., not enough matches) | Existing behavior unchanged: error response | Pre-existing behavior. |

---

## Calibration

Owned in full by [`e2e-and-calibration-intent.md`](e2e-and-calibration-intent.md), including:

- The two-tolerance, two-model design (`tight`, `loose`) and rationale.
- The two-stage calibration (Stage 1 ZED held-out bulk, Stage 2 phone-side correction).
- The global-model + per-map-overlay hybrid.
- Algorithms 1 / 2 / 3 in full procedural detail.
- Calibration artifact format and storage lifecycle.
- The fit pipeline (`scripts/fit_calibration.py`).
- The fused e2e-harness-as-data-generator architecture and corpus-gathering spec.

This file's role re: calibration is limited to the API contract (LocalizationMetrics' Confidence/Covariance/PipelineVersion fields) above and the frontend's consumption of those fields below.

---

## Frontend changes

### `Anchor` → `GeoPose` rename

Pure mechanical refactor. The class at `packages/unity/Placeframe/Assets/Package/Core/Runtime/Anchor.cs` becomes `GeoPose.cs`. All usages, namespace references, and type names update. No semantic change in this rename. The OGC GeoPose 1.0 standard is informally referenced by the name; no formal conformance is claimed.

The per-frame Lerp inside this class is **removed**. Visual smoothing now comes from upstream (the VPS slewer), not per-GeoPose. The class becomes a thin transformer: ECEF position + rotation in, current Unity position + rotation out, recomputed when the VPS event fires.

### `VisualPositioningSystem` rewrite

The static class at `packages/unity/Placeframe/Assets/Package/Core/Runtime/VisualPositioningSystem.cs` undergoes substantial change. New responsibilities:

- Maintains a Bayesian filter over the alignment: `(μ_align, Σ_align)` where μ is a 4×4 SE(3) transform and Σ is a 6×6 covariance in se(3) tangent coordinates.
- Receives new measurements from the localization callback. Each measurement is `(T_meas, Σ_meas, confidence)`.
- Runs a Mahalanobis innovation gate on each measurement.
- Updates the posterior on accepted measurements.
- Decides snap vs slew based on posterior shift magnitude.
- Drives a slew loop in `Update()` that lerps `_unityFromEcefTransform_current` toward `_unityFromEcefTransform_target` using SE(3)-correct interpolation.

#### State

```csharp
private static double4x4 _unityFromEcefTransform_current = double4x4.identity;
private static double4x4 _unityFromEcefTransform_target  = double4x4.identity;
private static Matrix6x6 _alignmentCovariance            = LargeInitialUncertainty;
private static double4x4 _slewStart                      = double4x4.identity;
private static float     _slewProgress                   = 1f;  // 1 = settled
private static double    _lastMeasurementTimestamp;
```

#### Public API

```csharp
public static double4x4 EcefToUnityWorldTransform => _unityFromEcefTransform_current;
public static event Action OnEcefToUnityWorldTransformUpdated;
public static AlignmentUncertainty CurrentUncertainty => SummariseCovariance(_alignmentCovariance);
public static LocalizationMetrics MostRecentMetrics { get; private set; }
public static LocalizationMetrics LastReceivedMetrics { get; private set; }
public static event Action OnMetricsReceived;
```

`AlignmentUncertainty` is a small struct: `{ float TranslationStdMeters; float RotationStdDegrees; }`. UI consumers that want a scalar "how confident is alignment" use this.

`MostRecentMetrics` is the metrics from the last *accepted* measurement (filter state). `LastReceivedMetrics` is the metrics from the last *received* server response, regardless of filter accept/reject. `OnMetricsReceived` fires per API response. UI consumers wanting per-measurement updates bind to `OnMetricsReceived` rather than `OnEcefToUnityWorldTransformUpdated`, since the latter only fires on snap or during slew animations and goes silent in steady state.

#### Measurement processing

Triggered by the existing R3 observable when a localization response arrives. **All state mutations happen on the Unity main thread**: the R3 pipeline uses `ObserveOnMainThread()` (or equivalent in Unity-specific R3 binding) to marshal the callback before touching VPS state. The math itself can run on the background thread; only the apply-to-state step runs on main.

Algorithm:

```
on measurement (T_meas, Σ_meas, confidence):

  # 1. Hard floor on confidence — drop outright if even loose tolerance unlikely
  if confidence.loose < LooseLowerBound:  # default 0.1
    log_dropped("low confidence")
    return

  # 2. Predict prior. The alignment is a static relationship between ECEF and Unity
  #    world; device motion does not drift it, so the mean is unchanged. VIO motion
  #    inflates uncertainty only.
  vio_motion = VIOMotionSince(_lastMeasurementTimestamp)  # device motion accumulated since last accept
  μ_predicted = _alignmentMean
  Σ_predicted = _alignmentCovariance + ProcessNoise(vio_motion)
    # ProcessNoise: (drift_rate * ||vio_motion.translation||)^2 added to diagonal,
    # rotation drift proportional to motion. Default drift_rate = 0.01 (1%/m).

  # 3. Mahalanobis innovation gate
  residual_se3 = log(μ_predicted⁻¹ · T_meas)   # 6-vector in se(3) tangent space
  innovation_cov = Σ_predicted + Σ_meas
  m_dist = residual_se3.transpose() @ inv(innovation_cov) @ residual_se3
  if m_dist > Chi2_99_6dof:  # ~16.81
    log_dropped("innovation gate")
    return

  # 4. Bayesian update on the alignment posterior
  K = Σ_predicted @ inv(Σ_predicted + Σ_meas)             # Kalman gain
  μ_new = μ_predicted ⊕ (K @ residual_se3)                # exp-map back to SE(3)
  Σ_new = (I - K) @ Σ_predicted

  # 5. Decide snap vs slew
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
  _lastMeasurementTimestamp = now()

  if confidence.tight passes some threshold:
    weight measurement higher; drive faster convergence
    (handled implicitly via Σ_meas — a low-confidence measurement has wider Σ_meas)

  log_accepted(...)
```

#### Slew loop

In `Update()` on the main thread, every frame:

```
if _slewProgress < 1f:
  _slewProgress = min(1f, _slewProgress + Time.deltaTime / SlewDurationSeconds)
  t = SmoothStep(_slewProgress)  # eased curve
  _unityFromEcefTransform_current = SE3Lerp(_slewStart, _unityFromEcefTransform_target, t)
  OnEcefToUnityWorldTransformUpdated?.Invoke()
```

`SE3Lerp` decomposes both endpoints into `(translation, rotation_quaternion, scale)`, lerps translation linearly, slerps rotation, lerps scale linearly, recomposes. NEVER lerp the 4×4 matrix component-wise.

`SlewDurationSeconds` default: 0.5. Tunable in config.

#### Bootstrap

At session start, no prior:
- `_alignmentCovariance` initialized to a large-but-finite matrix (e.g., translation σ = 100m, rotation σ = 180°). This is a vague prior that's wider than any plausible alignment, so the first Mahalanobis gate accepts almost anything passing the loose-confidence floor.
- The first accepted measurement triggers a snap (because the posterior shift will exceed the 6σ slew threshold against the giant initial covariance). Subsequent measurements slew.

#### Concurrency model

- All VPS state mutations happen on the Unity main thread.
- The localization request (HTTP) runs async on a background thread.
- The R3 observable's subscription marshals the response onto the main thread via `ObserveOnMainThread` (or whichever Unity-binding equivalent exists in the R3 version in use; verify in `packages/unity/`).
- The Bayesian update math (~µs of work) runs synchronously on the main thread inside the marshalled callback. This is acceptable; the work is tiny.
- No locks required.

### Phone-side calibration data logging (dogfooding mode)

Add to `apps/AndroidMobile`:

- **Toggle**: a setting in the app's settings UI ("Contribute calibration data"). Persisted to PlayerPrefs. Default: off.
- **Per-query logging** (when toggle is on): for each localization request, capture `{server_request_timestamp, server_response, vio_pose_at_request_time, frame_index}`. Append to an in-memory session log.
- **Session boundary**: when the localization loop stops (app backgrounded, user toggles off, app exits), serialize the session log to JSON and upload to the API at `POST /calibration-data` (new endpoint).
- **Backoff / retry**: if upload fails, persist the JSON locally and retry on next session start. Cap local persistence at e.g. 100 MB.

Schema of the uploaded JSON:

```json
{
  "schema_version": 1,
  "session_id": "uuid",
  "device_class": "Pixel 7" or similar,
  "os": "Android 14",
  "app_version": "0.1.0+47",
  "map_id": "uuid",
  "pipeline_version": "abc123...",
  "queries": [
    {
      "timestamp_ms": 1714400000000,
      "metrics": { "NumInliers": 234, "InlierRatio": 0.41, ... },
      "covariance": [[...6x6...]],
      "estimated_pose_in_map": { "translation": [...], "rotation_quat": [...] },
      "vio_pose": { "translation": [...], "rotation_quat": [...] },
      "confidence": { "tight": 0.65, "loose": 0.91 }
    },
    ...
  ]
}
```

Note: query images are NOT logged. The schema is designed so they can be added later (an additional `query_image_id` field referencing an upload to a separate bucket) without breaking parsers.

API endpoint `POST /calibration-data` writes the JSON directly to MinIO at `s3://placeframe-calibration-data/sessions/{session_id}.json`. No DB row needed; the offline pipeline iterates the bucket.

---

## Open tunables

These are values the design depends on but where the right number is empirical and will be tuned post-deployment:

| Parameter | Default | Where used |
|---|---|---|
| Slew duration | 0.5 s | VPS slew loop |
| Snap threshold (sigmas) | 6 | VPS posterior-shift snap criterion |
| Process noise (VIO drift) | 1% / m | VPS prior prediction |
| Initial alignment covariance | σ_t = 100 m, σ_r = 180° | VPS bootstrap |
| Loose confidence floor | 0.1 | Hard reject below this |
| Per-map calibration sample threshold | 200 | When per-map fitting kicks in |
| Per-map calibration refit cadence | weekly OR +50% samples | Offline pipeline |
| Phone pair distance cap | 1.0 m | Algorithm 2 pairwise interval |
| Frontend tight-confidence gating threshold | n/a (use confidence as Σ_meas weight, no hard threshold) | VPS measurement processing |
| Base per-tick process noise | 1e-4 m² translation, 1e-6 rad² rotation (coarse — re-tuned against fitted σ_meas; see [`e2e-and-calibration-intent.md`](e2e-and-calibration-intent.md)) | VPS measurement processing — see "Σ_posterior lock-in" finding |

The frontend NOTABLY does not have a "reject if confidence < X" hard threshold (other than the `LooseLowerBound = 0.1` floor). Confidence flows into measurement processing as a measurement-covariance scaling — a low-confidence measurement is treated as a wide-σ measurement and naturally gets little weight in the Bayesian update, while a high-confidence measurement gets tight σ and dominates. This is the textbook Bayesian way to use a calibrated probability and avoids picking a magic threshold.

Concretely: `Σ_meas_scaled = Σ_meas / confidence.tight^2` (or similar — the precise scaling is a tuning detail in the offline calibration step's "what does Σ_meas mean" decision, which couples to how the covariance is interpreted post-calibration). This scaling is itself a calibration-time choice and will be revisited.

---

## Out of scope

- Multi-map handling.
- ARFoundation `ARAnchor` integration.
- Online / continuous calibration.
- Image-content logging in dogfooding (deferred but designed-for).
- Per-device-class calibration partitioning (currently treated as a single phone population).
- Background re-fitting automation (cron, CI scheduled jobs).
- Admin UI for calibration management.

---

## Risks and unknowns

- **PnP covariance calibration quality**. The Hessian-derived covariance assumes Gaussian residuals on the matched inlier set. With LightGlue's hard outlier pruning, the residual distribution may not be Gaussian, and the resulting covariance may be optimistic. We rely on the calibration step to empirically scale this if needed; no explicit calibration of `Σ_meas` is in v1. If the running filter behaves badly (overconfident on bad measurements), this is the first thing to investigate.
- **VIO drift on lower-end phones**. The 1% process noise default is reasonable for flagship phones. Lower-end Android may need 2-3%. Until per-device tuning exists, we treat the global default as a compromise.
- **Phone-side data sparsity at session start**. The two-stage calibration depends on having enough phone-side data to fit a meaningful stage 2 isotonic. Expect this to take weeks of dogfooding before the stage-2 layer is meaningful. Until then, the system is "ZED-calibrated" and will be miscalibrated for phone queries — better than uncalibrated, worse than fully calibrated.
- **Cold-start UX**. With a wide initial alignment prior, the first measurement that passes the loose-confidence floor will snap into place. If that first measurement is a low-quality outlier (which the calibration system thinks is loose-OK but is actually wrong), it will produce a visible bad initial alignment that subsequent measurements correct. Mitigations: tighten `LooseLowerBound`, require the first N measurements to pass a higher bar before exiting the `Initializing` state, or require multiple measurements to agree before exiting the bootstrap. Picked: defer mitigation to post-deployment tuning.
- **Pipeline-version churn**. Every change to the localizer's relevant config invalidates the calibration. Engineering discipline required to avoid trivial changes that break calibration.
