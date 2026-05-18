---
updated: 2026-05-17
---

# Capture-tool validation mode: post-Stop/Start jump and far-from-origin point-cloud height error

## Goal

Two reproducible bugs in the AndroidMobile capture tool's "validation" (localize-against-a-just-built-map) mode, observed on a larger multi-room map:

1. **Stop -> Start jump.** After Stop then Start, localization briefly looks good, then "jumps" to an incorrect pose and stays there.
2. **Far-room height bias.** In the room where the scan started (map origin), localizations are good. In a far room at the opposite end of the map, the point cloud is consistently significantly too high.

Investigate root cause, distinguish math/geometry bugs from possible reconstruction warp, and prepare fixes. The user has decided to implement (next session) the 4 DOF refactor of `RelocalizationFilter` plus the reconstructor-side gravity-handling improvements that make 4 DOF unambiguously correct.

## State

Diagnosis complete; design for the 4 DOF refactor drafted; no code changes yet. Investigation done on branch `investigation/validation-mode-bugs`. Findings verified by reading source directly (not just by trusting a sub-agent), so the line numbers and code structure below are confirmed against the working tree at this commit.

### Bug 1 root cause (confirmed)

`VisualPositioningSystem.StopLocalizing()` (`VisualPositioningSystem.cs:183-189`) only disposes the frame-capture subscription. It does **not** touch the AR session, the loaded maps, or `_state` (the `RelocalizationFilter` state). `StartLocalizing()` (lines 156-180) creates a fresh subscription on the same `_state`. Consequences:

- `HasAcceptedMeasurement` stays `true` across Stop/Start, so the first post-Start measurement does **not** snap -- it slews (`RelocalizationFilter.cs:137`: `shouldSnap = !state.HasAcceptedMeasurement`). The 0.5 s smooth-step slew to the new posterior is the "looks very good" moment the user sees.
- Nothing in the repo subscribes to ARFoundation tracking discontinuity events. Grepping `trackingState|sessionStateChanged|ARSessionState|trackingLost` shows only `CameraProvider` referencing `ARSessionState`, and only as a precondition gate.
- When VIO jumps after the slew, `frame.CameraTranslationUnityWorldFromCamera` shifts by the jump magnitude on the next `Localize` call (~line 215). `ComputeAlignmentFromResult` produces a new alignment that disagrees with the prior by ~jump magnitude.
- `ProcessNoise` (`RelocalizationFilter.cs:218`) inflates Σ only by `(0.01 m * |Δ|)^2` -- for a ~1 m jump that is ~1e-4 m^2 added to a posterior translation variance of ~1e-2 m^2. The Mahalanobis^2 of the residual then blows past `Chi2_99_6dof = 16.81` and the measurement is **silently rejected** (only visible in the debug log at `VisualPositioningSystem.cs:253`).
- `AlignmentMean` stays anchored to the pre-jump frame. Every subsequent measurement keeps disagreeing with this stale prior and keeps getting gated out. The user sees the jump baked in and never recovered.

User's original hypothesis ("VIO jump after VPS lock gets baked in, nothing reacts to it") is correct, with the added multiplier that the rejection gate then locks the bad alignment in permanently.

### Bug 1 bonus finding (probably also contributes)

`LocalizationMap.cs:119-120` sets `transform.position` / `transform.rotation` **exactly once** in `DownloadMapAndLoad`, using whatever `EcefToUnityWorld` returns at that instant. Unlike `GeoPose.cs:67` -- which subscribes to `VisualPositioningSystem.OnEcefToUnityWorldTransformUpdated` and re-applies the transform -- `LocalizationMap` never re-syncs. So the point cloud's Unity-world pose is frozen against the alignment that existed when the HTTP fetch completed (possibly identity / stale), and never tracks subsequent filter updates. This is likely a second contributor to "looks good, then drifts."

### Bug 2 root cause (now reframed: not a "translation bug" but a constraint-encoded-in-wrong-place bug)

`RelocalizationFilter.ComputeAlignmentFromResult` (lines 265-310) corrects rotation but not translation. The sequence:

```
// L292: composed rotation, map -> unity world
rotationUnityFromMap = R_unityWorldCamera * R_cameraFromMap;

// L295-297: gravity-snap rotation -- strip roll/pitch, keep yaw
right   = rotate(rotationUnityFromMap, X);
forward = cross(right, Y_up);
rotationUnityFromMap = LookRotation(forward, Y_up);   // mutated

// L299-300: translation, computed from the UN-corrected rotation
translationUnityFromMap = R_unityWorldCamera * t_cameraFromMap + t_unityWorldCamera;
```

The visible symptom is a rotation error, not a translation error: "things are too high in room B but fine in room A" is exactly what a small rotation error pivoted around the map origin produces (point at distance D moves ~D * sin(θ)). A 1° pitch correction at 20 m = ~35 cm vertical lift -- matches the observation.

The mathematical equivalence: keeping `t` unchanged while rotating `R` is the same as "rotating around the map origin." The (R, t) pair is internally inconsistent with the camera anchor -- the gravity snap has implicitly shoved the composed transform sideways by `θ * |camera - map_origin|`. User pushed back on the local fix ("compute then patch with a `_corrected` variable" is a code smell) and that pushback led to the structural fix below.

### The deeper insight: the gravity snap exists for a real reason

User wrote the snap because each individual VPS measurement has 6 DOF noise, so the Kalman filter can converge with a slight tilt baked in. The snap exists to structurally remove two DOF (pitch and roll) that we have a-priori knowledge are zero, so the filter can't wander on them. That rationale is sound.

The bug is *where* the constraint is encoded: a per-measurement post-hoc projection on the output of a 6 DOF composition introduces the pivot problem. The principled fix is to **encode the constraint in the state representation itself**: parameterize the alignment as 4 DOF (yaw + R^3 translation) instead of full SE(3). Each 6 DOF VPS measurement is projected to 4D on the way in via a measurement model `h: SE(3) -> (yaw, R^3)`. The projection has a natural pivot -- the camera position -- because that's where the measurement is anchored. "Rotate around the camera" falls out of the geometry rather than being a separate manual step.

## The 4 DOF refactor design (drafted, not committed)

User explicitly asked for "draft the proposed change" and then later "I actually meant to just go ahead and implement the change" -- so next session is implementation, not more design.

### State representation

```csharp
public struct FilterState {
    public double Yaw;                            // radians, wrapped to (-π, π]
    public double3 Translation;                   // unity world meters
    public Matrix<double> AlignmentCovariance;    // 4×4, ordering [yaw, tx, ty, tz]
    public double YawCurrent;
    public double3 TranslationCurrent;
    public double YawSlewStart;
    public double3 TranslationSlewStart;
    public float SlewProgress;
    public double3? LastAcceptedVioPosition;
    public bool HasAcceptedMeasurement;
    public LocalizationMetrics MostRecentMetrics;
}
```

Public `EcefToUnityWorldTransform` continues to return `double4x4`, built on read from `(Yaw, Translation)` via `quaternion.AxisAngle(Y, Yaw)`. Keeps `EcefToUnityWorld` / `UnityWorldToEcef` / `GeoPose` / `LocalizationMap` consumers unchanged.

### Bootstrap, process noise

- `BootstrapSigmaYawRadians = π` (uniform on circle); `BootstrapSigmaTranslationMeters = 100`; 4×4 diagonal `[π², 100², 100², 100²]`.
- Process noise: drop one rotation row/col. 4×4 diagonal `[yaw_var, t_var, t_var, t_var]` plus `(0.01 × |Δvio|)²` on all four diagonals (same per-meter drift model).

### Measurement projection (this is where the bug class disappears)

`ComputeAlignmentFromResult` returns `(yawMeas, tMeas)` and a 4×4 covariance. **Delete the current gravity-correction step** -- the projection itself enforces gravity alignment, in the geometrically correct place.

```csharp
// 1. Compose rotation (no gravity correction)
var R_unityFromMap = R_unityWorldCamera * R_cameraFromMap;
// 2. Extract yaw from R_unityFromMap (Z-projection variant; degrades gracefully at singularity)
var mapForwardInUnity = R_unityFromMap * new double3(0, 0, 1);
var yawMeas = math.atan2(mapForwardInUnity.x, mapForwardInUnity.z);
// 3. Translation anchored on the camera
var R_yawOnly = QuaternionAroundY(yawMeas);
var tMeas = t_unityWorldCamera - math.mul(R_yawOnly, t_mapFromCamera);
```

### Covariance projection (6×6 → 4×4)

v1: diagonal-dominant Jacobian (yaw ← ωy, tx ← νx, etc.). `Σ_meas_4 = H_diag · Σ_meas_6 · H_diagᵀ`. Drops cross-correlation between discarded pitch/roll and kept dimensions. Mark as TODO; revisit with full Jacobian (4×6, cross-terms scale with `|t_mapFromCamera|`) if filter looks under-confident at non-zero `t_mapFromCamera`.

### Innovation / gate / Kalman / slew

- Residual: `[wrap(yawMeas - yawState), tMeas - tState]` where `wrap(θ) = ((θ + π) mod 2π) − π`.
- Mahalanobis gate: **Chi² 99%, 4 DOF = 13.28** (was 16.81 for 6 DOF). Trivial change, easy to miss.
- Kalman update is 4D; no SE(3) exp/log needed.
- Slew: linear on translation; shortest-arc on yaw.

### Helpers / deletions

- **Delete** `Se3.Log` / `Se3.Exp`. No tangent space needed.
- **Add** `MathUtil.WrapAngle(double)` and `MathUtil.YawFromRotation(double3x3)` (with documented near-vertical singularity).
- `Double4x4.FromTranslationRotation` stays -- used to assemble public `double4x4` on read.

### Tests

- Rewrite `RelocalizationFilterTests` for 4D state.
- New regression: a measurement whose composed rotation has 2° pitch input must produce **zero** vertical offset at a map point 20 m from origin (the original bug).
- New: yaw residual wraps correctly across ±π.
- Bootstrap → first measurement snaps (adapted from existing).
- VIO-jump simulation (leave for the Bug-1 fix).

### Files touched (estimate)

- `RelocalizationFilter.cs` -- substantial rewrite
- `VisualPositioningSystem.cs` -- small (state struct shape changed)
- `Se3.cs` -- delete most of it
- `MathUtil.cs` -- add `WrapAngle`, `YawFromRotation`
- `RelocalizationFilterTests.cs` -- rewrite
- Possibly `packages/unity/Placeframe/SPEC.md` -- note the 4 DOF assumption and dependence on upstream gravity

### Explicitly NOT in this refactor

- Stop→Start state-reset fix
- ARFoundation tracking-jump detection / covariance re-bootstrap on jumps
- `LocalizationMap` transform-update subscription

These are orthogonal and should land separately so test signal isn't muddied.

## The upstream gravity story (companion to the 4 DOF change)

The 4 DOF constraint is "only as good as the upstream gravity." Investigation answered how trustworthy that is, and led to a layered set of reconstructor-side improvements.

### What the reconstructor currently does

`docker/reconstructor/src/reconstructor/colmap.py:160-178` and `rig.py:70-84`: **no independent gravity estimation**. Reads truth poses from `frames.csv`, pins the map to the first registered frame's pose via single-anchor Sim3d alignment. There's a Procrustes residual surfaced as `truth_alignment_rms_residual_m` / `truth_alignment_max_residual_m`, but it's a diagnostic only. **The map's gravity = the capture tool's VIO gravity at the first frame, period.** That means trustworthiness collapses to the capture-side priors.

### Capture-side gravity quality

- **ARFoundation path** -- ARCore/ARKit gravity ~0.5–1° after warm-up, worse for first few seconds, worse during fast rotation. No per-frame confidence exposed. Note: `CameraProvider.cs:148-152` already strips pitch/roll when creating capture anchors (`Quaternion.Euler(0f, eulerAngles.y, 0f)`), so the 4 DOF assumption is already implicit in the capture path -- the filter would just match it.
- **ZED X path** -- `docker/zed-capture/src/zed/zed.py:217-222` enables `enable_imu_fusion = True` with `set_floor_as_origin = False`. ZED publishes <0.5° gravity-alignment typical with fusion enabled. Tighter than ARFoundation. Inherits the same architectural risk.
- **Localizer** (`docker/localizer/src/localize.py:189-197`) is pure 6 DOF PnP; no gravity constraint, no IMU hint.

### What "consensus gravity from priors" actually is (walked back)

User asked: does averaging gravity across frames help? An earlier turn implied "consensus gravity across all registered frames"; this was walked back as misleading. Every frame's pose is reported in the *same* VIO world frame whose Y was defined to be gravity at session start -- they tautologically agree. There is nothing to average across frame poses; the consensus would only be meaningful from per-frame raw IMU (not currently stored) or from scene geometry (floor plane / trajectory PCA / vertical vanishing points -- real but heavier algorithmic addition, also second-guesses the ZED's tuned fusion).

### What the SDKs actually report frame-to-frame

The world frame's Y axis is fixed at session start; later frames *don't* report a different gravity direction. But the world frame itself gets nudged retroactively as the SDK refines its IMU bias estimate during the first seconds. So "skip cold-start frames" works not because gravity stabilizes per frame, but because you're waiting for the SDK's world frame to stop being retroactively corrected. After settling, every later frame's rotation is in a known-good world frame.

Per-frame tracking state is exposed (`ARSession.state`, ZED `POSITIONAL_TRACKING_STATE`); rough captures (camera covered) degrade *positional* tracking, but pitch/roll stay pinned by the accelerometer regardless.

### The layered fix

1. **Use the last stable frame (not the first) to anchor the origin** -- one-line reconstructor change. Bias estimates have had the entire session to converge. "Last stable" = tracking state OK + low-motion filter to avoid catching put-down motion. Re-capture stability is fine because content is map-relative.
2. **Read the OS-fused gravity sensor at the anchor frame.** Available on every platform, independent of the AR SDK's session-start world frame:
   - Android: `Sensor.TYPE_GRAVITY` (virtual sensor, accel+gyro fused). Per-frame poll via `SensorManager`.
   - iOS: `CMMotionManager.deviceMotion.gravity`.
   - ZED X: `SensorsData.get_imu_data()` exposes fused accelerometer / gravity.
   Record per-frame gravity (3 floats, camera frame) in the capture format alongside the pose. At the anchor frame, gravity vector *is* the camera's "down"; define map +Y = its negation; pick +X/+Z from camera-forward projected onto the horizontal plane. VIO is used only for relative geometry between frames, never to choose world up.
3. **Average gravity over multiple stationary samples** at the anchor -- 10 samples → √10 → ~0.03° (free).

### Leverage table -- updated with sensor-floor accuracy

Worst-case visible vertical error at distance D for given tilt baked into the map:

| Distance | 2° (current ARCore worst case) | 0.3° (last-stable + OS gravity) | 0.1° (averaged) |
|---|---|---|---|
| 1 m   | 3.5 cm | 0.5 cm | 0.2 cm |
| 5 m   | 17 cm  | 2.6 cm | 0.9 cm |
| 20 m  | 70 cm  | 10 cm  | 3.5 cm |
| 50 m  | 1.75 m | 26 cm  | 9 cm   |

At 0.3° (the realistic target with last-stable-frame + OS gravity), even 50 m is fine for overlay use. The "warehouse-scale worry" disappears. 4 DOF is unambiguously correct for everything Placeframe is likely to target.

Important comparison: even a *fixed* 6 DOF filter would have ~1° per-measurement PnP rotation noise contributing leveraged error at distance. The 6 DOF flexibility only absorbs map tilt if per-measurement pitch/roll is unbiased. 6 DOF is **not** obviously better than 4 DOF for the relevant scales.

### Note on the 0.1° vs 1° figures

Sensor floor for consumer MEMS is ~0.1° in quiescent conditions. The 1° figure earlier in the discussion is *end-to-end system delivery* (AR SDK output that integrates bias, motion contamination, calibration imperfection over a session). The reason for raising the OS gravity sensor: you can largely reclaim the sensor floor by reading the fused gravity directly at a stationary moment, instead of inheriting whatever world frame the AR SDK happened to settle on. The 0.1° row in the leverage table reflects this.

## Decisions

- The 4 DOF (yaw + R^3) state-representation refactor of `RelocalizationFilter` is the agreed direction for the pivot bug. User indicated next step is **implement, not design more**.
- The "open design decisions" in the earlier draft were not actually open (yaw extraction = Z-projection; multi-map ECEF out of scope; backend keeps 6×6 covariance and client projects). Implementer should not surface these as open questions.
- **No permanent feature flag for 4 vs 6 DOF.** Permanent toggles mean "we never resolved the question." If a validation-period A/B is wanted, prefer a **shadow filter** (both filters update on every measurement, one drives rendering, surface the divergence in the metrics UI) over a runtime toggle. Has a clean "delete after validation" exit. User did not explicitly green-light building the shadow filter; treat as available option, not required.
- Reconstructor work (last-stable-frame anchor, OS gravity sensor logging, averaging) is companion work to the 4 DOF refactor. Independent commits, can ship separately.
- Investigation done on a fresh branch `investigation/validation-mode-bugs` (created at user's request). Memory was committed twice during the session (`602da12f`, `b717cd67`); this update is the third.
- Trust-but-verify: initial Explore-agent pass produced an overview with inaccuracies (claimed `ComputeAlignmentFromResult` was strictly correct). Direct file reads confirmed the gravity-snap-then-translate bug. Use the same pattern for implementation review.

## Open questions

- Whether to build the dual/shadow filter for the validation period, or just ship 4 DOF and rely on the reconstructor fixes. User leaned toward "trust upstream gravity" by end of session; implementer should ask before building the dual-filter scaffolding.
- Whether to land the reconstructor "last stable frame for origin" change alongside the 4 DOF refactor or as a follow-up. Either is defensible; the leverage math justifies 4 DOF even without it for the building scale, but the reconstructor change tightens worst-case error.
- Whether the capture format change (per-frame gravity vector from OS sensor) is in scope now or later. It is the strongest single mitigation but is a schema change with knock-on effects (datamodels regen, both capture tools, reconstructor consumer). Defensible to defer.
- Which ARFoundation signal to use for VIO-discontinuity detection: no first-class "pose jumped" event. Options: `ARSession.sessionStateChanged` (coarse), tracking-state transitions on `XROrigin.Camera.trackingState`, or detect large frame-to-frame VIO deltas ourselves. Needs a small spike. Independent of the 4 DOF refactor.
- Whether Bug 1's fix should reset the entire `_state` or only clear `HasAcceptedMeasurement` + `LastAcceptedVioPosition` so the first measurement snaps. Full reset is simpler/safer; partial reset preserves the prior as a hint, which is probably worthless after an arbitrary stop interval.

### Implementation catches for the 4 DOF refactor

1. Yaw is S^1 -- residuals must wrap modulo 2π. Filter spazzes near ±π if forgotten.
2. Yaw extraction degenerates near pitch = ±90°. Won't bite an upright handheld phone but is a real failure mode at extremes; Z-projection degrades gracefully.
3. Chi² gate is 13.28 not 16.81 -- easy to miss.
4. 6 DOF → 4D covariance projection has cross-terms with `|t_mapFromCamera|`. v1 uses diagonal-dominant; mark TODO.
5. The structural constraint is only as good as upstream gravity guarantees. If a *legacy* map (built before reconstructor gravity fixes) has tilt baked in, the 4 DOF filter forces 0 tilt and the alignment looks bent. Either re-process legacy maps or version-flag them. User did not pick a path -- ask before invalidating existing maps.

## Key files

- `packages/unity/Placeframe/Assets/Package/Core/Runtime/VisualPositioningSystem.cs` -- `StartLocalizing` / `StopLocalizing` (156-190); `Localize` and silent-rejection debug log (~215, ~253); `EcefToUnityWorld` (192-205); `OnEcefToUnityWorldTransformUpdated` event.
- `packages/unity/Placeframe/Assets/Package/Core/Runtime/RelocalizationFilter.cs` -- EKF on SE(3); `shouldSnap` gate (137); `ProcessNoise` (218-243); `ComputeAlignmentFromResult` gravity-snap bug (265-310); chi-squared gate `Chi2_99_6dof = 16.81`. **Primary target of the 4 DOF refactor.**
- `packages/unity/Placeframe/Assets/Package/Core/Runtime/Se3.cs` -- exp/log; mostly deleted by the 4 DOF refactor.
- `packages/unity/Placeframe/Assets/Package/Core/Runtime/MathUtil.cs` -- needs new `WrapAngle`, `YawFromRotation` helpers.
- `packages/unity/Placeframe/Assets/Package/Core/Tests/Editor/RelocalizationFilterTests.cs` -- must be ported alongside the filter refactor.
- `packages/unity/Placeframe/Assets/Package/Core/Runtime/LocalizationMap.cs` -- one-shot transform write in `DownloadMapAndLoad` (119-120); never resubscribes to `OnEcefToUnityWorldTransformUpdated`.
- `packages/unity/Placeframe/Assets/Package/Core/Runtime/GeoPose.cs` -- the *correct* pattern: subscribes to `OnEcefToUnityWorldTransformUpdated` at line 67 and re-applies on every update.
- `packages/unity/Placeframe/Assets/Package/ARFoundation/Runtime/CameraProvider.cs` -- only place `ARSessionState` is referenced (lines 144, 263); also `CameraProvider.cs:148-152` strips pitch/roll when creating capture anchors -- 4 DOF assumption is already implicit here.
- `apps/AndroidMobile/Assets/LocalizationManager.cs` (14-46), `apps/AndroidMobile/Assets/Scripts/Capture/AppUI.cs` (398-495), `apps/AndroidMobile/Assets/Scripts/Capture/AppState.cs` (16-81) -- the validation UI / state wiring driving `StartLocalizing` / `StopLocalizing` via `App.state.localizing`.
- `docker/reconstructor/src/reconstructor/colmap.py:160-178` and `rig.py:70-84` -- single-anchor Sim3d alignment to the first registered frame; **no independent gravity estimation**. Where the last-stable-frame anchor change lands.
- `docker/zed-capture/src/zed/zed.py:217-222` -- ZED `enable_imu_fusion = True`, `set_floor_as_origin = False`. Source for ZED gravity quality.
- `docker/localizer/src/localize.py:189-197` -- pure 6 DOF PnP, no gravity constraint.

## Pending threads

- **Implement the 6 DOF → 4 DOF refactor of `RelocalizationFilter`.** User said "go ahead and implement"; design above is the spec. Do NOT re-surface the "open design decisions" -- they're settled. Touches `RelocalizationFilter`, `VisualPositioningSystem` (state shape), `Se3` (mostly deleted), `MathUtil` (new helpers), `RelocalizationFilterTests` (rewrite), possibly `Placeframe/SPEC.md`. Branch is `investigation/validation-mode-bugs`. Ask user before committing the first cut.
- **Fix Bug 1 (filter state carry-over).** Reset `_state` in `StartLocalizing` (or at minimum clear `HasAcceptedMeasurement` and `LastAcceptedVioPosition`) so the first post-Start measurement snaps. Independent of the 4 DOF refactor.
- **Fix Bug 1 (VIO jump unhandled).** Subscribe to an ARFoundation tracking-discontinuity signal and re-bootstrap the filter covariance on detected jumps so the chi-squared gate softens enough to accept the next measurement. Independent of the 4 DOF refactor.
- **Fix the LocalizationMap drift.** Make `LocalizationMap` subscribe to `OnEcefToUnityWorldTransformUpdated` like `GeoPose` does, so the point cloud tracks the live alignment instead of freezing at load-time. Independent of the 4 DOF refactor.
- **Reconstructor: last-stable-frame for origin anchor.** One-line change in `colmap.py` / `rig.py`. Companion to the 4 DOF refactor; tightens worst-case map tilt from ~1–2° to ~0.5°.
- **Capture format: per-frame OS-fused gravity vector.** Bigger change (schema, both capture tools, reconstructor consumer); gives near-sensor-floor (~0.1° with averaging) map alignment. Defer-or-do decision pending.
- **Decide legacy-map handling.** 4 DOF filter against old (tilted) maps will look bent. Re-process vs version-flag-and-use-6DOF-for-legacy. Ask user.
- **Verify Bug 2 field hypothesis.** Revisit the far room via different paths; if offset is consistent it's the alignment math (4 DOF refactor will fix it), if path-dependent it's reconstruction warp (separate problem). Worthwhile even after shipping the refactor.
