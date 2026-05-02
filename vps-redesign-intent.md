# VPS Confidence, Calibration, and Fusion — Intent

> Execution and progress tracked in [`plan.md`](plan.md).

## Status

Design intent. Going-for-broke version: the goal is a system that is as accurate as practical under as many conditions as practical, with no compromises taken for shippability that aren't necessary.

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

### Calibration loader

At startup the localizer:

1. **Loads global calibration** from a config file mounted at `/etc/placeframe/calibration/global.json`. Source of truth is the git repo at `config/calibration/global.json`, mounted via Docker compose `configs:` block.
2. **Verifies pipeline version**. If `global.PipelineVersion != localizer.PipelineVersion`: hard-fail startup with a loud log explaining the mismatch and the expected fix (run the offline fitting pipeline against the new version, commit the result, redeploy).
3. **Per-map calibrations** are NOT loaded eagerly. Each map has at most one calibration artifact at `s3://placeframe-maps/{map_id}/calibration.json`. The first request to localize against a map triggers a lazy load: fetch + cache in memory keyed by map ID. If absent, fall back to global-only for that map (logged, not failed). If present but pipeline-version-mismatched, log loudly and fall back to global-only.

### Confidence computation per query

Given raw `metrics`, the active map's metadata `map_quality_features`, and the loaded calibration:

```
features = transform(metrics, map_quality_features)
  # transformations: log(NumInliers + 1), ReprojErr / image_diagonal_pixels,
  # InlierRatio (already 0-1), InlierCoverage (already 0-1),
  # log(MapImageCount + 1), log(MapPointCount + 1), MapAvgTrackLength,
  # log(MapBoundingVolumeM3 + 1), MapViewpointDiversity, IsIndoor

p_global_tight = sigmoid(features @ global.tight.weights + global.tight.intercept)
p_global_loose = sigmoid(features @ global.loose.weights + global.loose.intercept)

# Stage 1 isotonic (calibrates the logistic output to actual P over training distribution)
p_calibrated_tight = global.tight.isotonic.apply(p_global_tight)
p_calibrated_loose = global.loose.isotonic.apply(p_global_loose)

# Stage 2 isotonic (per-map correction, identity if absent)
if per_map_calibration_loaded:
    p_final_tight = per_map.tight.isotonic.apply(p_calibrated_tight)
    p_final_loose = per_map.loose.isotonic.apply(p_calibrated_loose)
else:
    p_final_tight = p_calibrated_tight
    p_final_loose = p_calibrated_loose

return Confidence(tight=p_final_tight, loose=p_final_loose, is_calibrated=True)
```

Total cost: a few dozen FLOPS plus two isotonic lookups (binary search over ~100 breakpoints). Negligible (<10 µs per query).

### Map quality features

Extracted at map-build time and stored as part of the map's metadata (database row, alongside the map ID). Computed once when the map is reconstructed:

- `MapImageCount`: total registered images.
- `MapPointCount`: total triangulated 3D points.
- `MapAvgTrackLength`: mean number of observations per 3D point.
- `MapBoundingVolumeM3`: convex hull volume of the camera centers, in cubic meters.
- `MapViewpointDiversity`: scalar derived from the variance of camera viewing directions (higher = more directional coverage).
- `IsIndoor`: boolean flag, set at upload time as map metadata. Default false; toggleable per map.

These get joined into the calibration feature vector at query time. Schema lives in the maps table; serialized to the same map metadata document the localizer already loads.

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

### Two tolerances, two models

For each tolerance level, we fit an independent calibration model end-to-end. Models share the same input features but have different binary labels.

- **Tight**: label is `(translation_err < 5cm) AND (rotation_err < 1°)`. Frontend uses for primary gating decisions.
- **Loose**: label is `(translation_err < 30cm) AND (rotation_err < 5°)`. Frontend uses for sanity-checking ("is this a wild outlier?") and for graceful UX degradation.

Independent models because:

- Tight-tolerance success and loose-tolerance success are correlated but not identical, especially in the regime where calibration matters most (mediocre quality results).
- They have different operational uses on the frontend.
- Fit cost is trivial — fitting two logistic regressions instead of one is irrelevant to the pipeline.

### Two-stage calibration: bulk + correction

Two distinct datasets feed two distinct fitting steps:

**Stage 1 — Bulk training on ZED held-out data**.

Plentiful, free-from-pose-prior, comes from the same hardware that built the map. Fits a logistic regression mapping `(metrics, map_features) → P(success)`. Captures the *shape* of the calibration function — how InlierRatio relates to ReprojErr relates to MapPointCount relates to success. This is the bulk of the function and generalizes across deployment conditions.

**Stage 2 — Domain correction on phone-side data**.

A smaller dataset (~500 samples per device class) of phone queries with VIO-relative ground truth. Fits an isotonic regression on top of stage 1's output: `predicted_p → empirical P(success)` for phone-source queries. Corrects for the systematic distribution shift between ZED-source and phone-source images.

The two-stage design lets us use plentiful ZED data for the bulk fit while only requiring a small amount of phone data to handle device shift. If phone data is unavailable, stage 2 is identity (same as stage 1 output).

### Hybrid: global model + per-map overlay

Two layers stacked on each query:

1. **Global model** (trained on all available data, all maps pooled): logistic + isotonic, takes raw metrics and map-quality features as input. Always present.
2. **Per-map isotonic correction** (optional, fit lazily once a map has accumulated enough samples): a second isotonic on top of the global output. Identity when absent.

Per-map fitting trigger: when a map accumulates ≥200 phone-side samples with VIO-relative pose-error labels, the offline pipeline fits a per-map isotonic and uploads it to MinIO alongside the map. Refit cadence: weekly or whenever sample count grows by 50%, whichever comes first. (Tunable; not load-bearing.)

### Algorithm 1: ZED held-out fitting

Source: every ZED capture session that builds a map.

Procedure:

1. For each capture session contributing to the map:
   a. Hold out 10% of the session's images at map-build time. Build the COLMAP map from the remaining 90%.
   b. From the in-set images, COLMAP outputs reconstructed poses `P_map_i` (in F_map). The same images had ZED pose priors `P_zed_i` (in F_zed) at capture time.
   c. Solve `T_zed_to_map` via Procrustes/Umeyama on `(P_zed_i, P_map_i)` pairs. This is a rigid + scale alignment, closed form.
2. For each held-out image:
   a. Transform its ZED-prior pose into F_map: `P_truth = T_zed_to_map · P_zed`.
   b. Run the localizer on the held-out image against the built map: `P_estimated, metrics`.
   c. Compute pose errors: `err_t = ||translation(P_truth) − translation(P_estimated)||`, `err_r = angle_between(rotation(P_truth), rotation(P_estimated))`.
   d. Record `(metrics, map_quality_features, err_t, err_r)`.
3. Pool across all sessions and maps. Add binary labels (`success_tight = err_t<5cm AND err_r<1°`, similar for loose).
4. Fit logistic regression for each label using sklearn's `LogisticRegression(class_weight='balanced')`.
5. Fit isotonic regression on the logistic output using sklearn's `IsotonicRegression(out_of_bounds='clip')` against the same labels (calibration step — ensures output is a true probability).
6. Optionally hold out 10% of the pooled samples to compute Brier score and reliability diagrams; report in the fit metadata.

Output: `{tight: {weights, intercept, isotonic}, loose: {weights, intercept, isotonic}, fit_metadata, pipeline_version}`.

This stage runs as part of the offline fitting pipeline; see "Offline fitting pipeline" below.

### Algorithm 2: phone-side pairwise calibration

Source: opt-in dogfooding sessions captured by the AndroidMobile app.

Per session, the app logs every localization query:
- Server response: estimated pose `T_map_i`, metrics, confidence (whatever stage 1 said).
- Local snapshot at the moment the query was captured: VIO pose `T_vio_i`, monotonic timestamp, frame index.

Per session, after upload:

1. Enumerate localization pairs `(i, j)` where `j > i` and `||translation(T_vio_j) − translation(T_vio_i)|| ≤ 1.0 m` (limits VIO drift contribution to <1cm on flagship phones, <2cm on lower-end).
2. For each pair, compute pairwise error:
   - VIO-implied relative motion: `dT_vio = T_vio_j · T_vio_i⁻¹`.
   - Localizer-implied relative motion: `dT_loc = T_map_j · T_map_i⁻¹`.
   - Pairwise translation error: `err_t = ||translation(dT_loc) − translation(dT_vio)||`.
   - Pairwise rotation error: `err_r = angle_between(rotation(dT_loc), rotation(dT_vio))`.
   - Note: pairwise error reflects *combined* error of the two localizations. A clean attribution requires more than this — see "Attribution" below.
3. Attribution: for each individual localization, define `err_i = median over all pairs that include i of pair_err`. Robust to outlier pairs; assigns each localization a per-frame error label.
4. Add binary labels per localization (using attributed `err_i`).
5. Pool across phone sessions. Fit isotonic correction `g(p) = empirical P(success | predicted_p_from_stage_1)`.

Output: `{tight: {isotonic}, loose: {isotonic}}`.

**Attribution caveat**. Pairwise errors confound the two localizations involved. Median-over-pairs is a coarse but robust attribution heuristic. A more principled alternative is a least-squares formulation (each pair's error is the L2 sum of its two localizations' errors; solve a per-localization-error system). Median-over-pairs is the chosen baseline; LSQ refinement remains an option if the heuristic proves insufficient.

**What this CAN'T detect**. Errors that are systematically shared across all localizations in a session (e.g., a phone with miscalibrated intrinsics that produces a constant 30cm offset on every query) get absorbed into the implicit `T_align` and produce zero pairwise residual. The system would calibrate as "all localizations look perfect" while being absolutely wrong. This is acceptable: the user-facing experience of "consistent but slightly shifted world" is visually stable and is the lowest-impact failure mode. Random outlier localizations — the high-impact failure mode — are detected normally because they stick out from neighboring localizations.

### Algorithm 3: per-map fitting

Same as Algorithm 2, but partitioned by map ID. Once a map has ≥200 phone-side samples, the offline pipeline fits a per-map isotonic on top of the global stage-1+stage-2 prediction:

```
predicted_p_global = stage1(metrics, map_features).then(stage2_isotonic)
# Per-map isotonic learns:
#   permap_isotonic(p) = empirical P(success | predicted_p_global = p, map = M)
```

Output uploaded to `s3://placeframe-maps/{map_id}/calibration.json`.

### Calibration artifact format

Single JSON document, ~3 KB for global, ~1 KB per map.

```json
{
  "schema_version": 1,
  "pipeline_version": "abc123def456...",
  "fit_metadata": {
    "fit_at": "2026-04-29T14:00:00Z",
    "fit_by": "scripts/fit_calibration.py v0.1",
    "sample_count": 8743,
    "validation": {
      "brier_tight": 0.092,
      "brier_loose": 0.041,
      "reliability_diagram_bins": [...]
    }
  },
  "global": {
    "tight": {
      "logistic": {
        "weights": [0.234, -1.83, 0.45, ...],
        "intercept": -2.14,
        "feature_names": ["log_inliers", "inlier_ratio", "reproj_err_norm", ...]
      },
      "isotonic": {
        "x_breakpoints": [0.01, 0.05, 0.10, ..., 0.99],
        "y_breakpoints": [0.02, 0.06, 0.12, ..., 0.97]
      }
    },
    "loose": { "logistic": {...}, "isotonic": {...} }
  }
}
```

Per-map artifact has the same shape but only `tight.isotonic` and `loose.isotonic` blocks (no logistic — the global one is the upstream).

### Storage and lifecycle

| Artifact | Path | Updated by | Cadence |
|---|---|---|---|
| Global calibration | `config/calibration/global.json` (git repo) | Engineer (PR after running offline pipeline) | When offline pipeline produces a meaningful update — initially weekly, slowing to quarterly |
| Per-map calibrations | `s3://placeframe-maps/{map_id}/calibration.json` (MinIO) | Offline pipeline (automated upload) | Per map: when sample count grows 50% or weekly, whichever first |
| Phone-side calibration data (raw logs) | `s3://placeframe-calibration-data/sessions/{session_id}.json` (MinIO) | AndroidMobile app (when dogfooding toggle is on) | Per session at session end |

The global calibration mounts into the localizer container as a Docker compose `configs:` volume. Updating is: run offline pipeline → `git diff` → review → PR → merge → deploy → service restart on next deploy. No Docker rebuild.

Per-map calibrations are loaded lazily by the localizer on first request to that map. Cached in memory. Optional `POST /calibration/refresh/{map_id}` admin endpoint to invalidate the cache after a per-map upload (otherwise picks up on next localizer restart).

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
```

`AlignmentUncertainty` is a small struct: `{ float TranslationStdMeters; float RotationStdDegrees; }`. UI consumers that want a scalar "how confident is alignment" use this.

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

## Offline fitting pipeline

A new Python script: `scripts/src/scripts/fit_calibration.py`. Run manually (or scheduled). Pulls data, fits, produces artifacts.

### Inputs

- ZED held-out data: regenerated on demand from existing capture sessions in MinIO. The script invokes the localizer in batch mode against held-out images and records `(metrics, pose_error)` rows.
- Phone-side data: read from the `placeframe-calibration-data` bucket in MinIO (uploaded by AndroidMobile dogfooding).
- Map metadata: read from the maps table in PostgreSQL.

### Output

- Updated `config/calibration/global.json` (engineer reviews diff and commits).
- One per-map calibration JSON per map that meets the sample threshold, uploaded directly to `s3://placeframe-maps/{map_id}/calibration.json`.
- A fitting report (Brier scores, reliability diagrams, sample counts, fit dates) printed to stdout and saved to `config/calibration/last_fit_report.md` (also git-committed).

### Steps

1. Fetch ZED capture sessions and their builds. For each: run held-out generation if not already present.
2. Fetch phone-side calibration data from MinIO. Filter by pipeline version (skip mismatches with current).
3. Compute pairwise pose errors per phone session (Algorithm 2).
4. Pool ZED held-out and phone-attributed data. Fit stage 1 logistic + stage 1 isotonic for tight and loose.
5. Fit stage 2 isotonic (phone-only correction) for tight and loose.
6. For each map with ≥200 phone samples: fit per-map isotonic. Write to MinIO.
7. Write global JSON to `config/calibration/global.json`.
8. Generate report with validation metrics (Brier, reliability binning).
9. Print summary; exit nonzero if any sanity checks fail (e.g., Brier > some ceiling, sample count anomalously low).

### Cadence

- Initial: run weekly during early calibration data accumulation (manual).
- Steady state: monthly or quarterly (manual, once calibration is stable).
- After any pipeline change in the localizer: mandatory re-fit before redeploy. Pipeline version mismatch enforces this.

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
