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

### OS gravity vs VIO world-Y (refined; the OS-sensor route is now de-prioritized)

Earlier drafts of this memory pushed adding `Sensor.TYPE_GRAVITY` (Android) / `CMMotionManager.deviceMotion.gravity` (iOS) / `SensorsData.get_imu_data()` (ZED) as a new capture-format column. After user pushback, that plan was walked back. The honest summary:

- **At rest, OS gravity and the AR SDK's world-Y agree** (both ultimately derive from the same accelerometer reading directly measuring gravity-in-device-frame). The "we're leveraging different signals" framing was overstated.
- **During motion they can differ transiently**, because the two filters have different gains/time-constants, but that difference vanishes the moment the device is stationary.
- **The dominant fix is WHEN you sample, not WHICH source.** A warmed-up AR SDK at a stationary moment already gives you near-sensor-floor gravity via its reported camera rotation -- the non-yaw part of `R_unityWorldCamera` at a stable last frame *is* the SDK's current best estimate of "how the camera is tilted relative to true vertical." ARCore/ARKit/ZED SDK are doing continuous gravity refinement internally; their last-stable-frame output is probably close to what a separately-sampled OS gravity sensor would give.
- The OS-sensor route remains available as a future addition if measurements show the AR SDK's world-Y is meaningfully worse than independently-sampled gravity. Not blocked; just unjustified at this point.

### The simplified layered fix (revised 2026-05-20)

Reconstructor change in `colmap.py:182-200`. The current code uses the first registered frame's truth pose (from `frames.csv`) as the anchor for the Sim3d that aligns the reconstruction to the rig coordinate frame. Replace this with:

1. **Translation: from the first registered frame.** Sorted by integer `frame_id` (timestamp) across all rigs. The map origin lands where capture started — natural reference for manual Cesium georegistration. Translation is essentially arbitrary for localization correctness; this choice is purely an operator-convenience signal.

2. **Rotation: from the latest stationary-detected frame.** Walk backwards through the registered frames; classify a frame as "stationary" if the translation delta and frame-to-frame rotation magnitude over a sliding window (say 30 frames ≈ 1 s) are both below thresholds. Take the rotation from the latest such frame. VIO has had the full session to refine its world-Y by that point.

3. **Fallback if no stationary window exists.** Use the median rotation across the last 25% of registered frames. Random per-frame motion contamination averages down; the result is still much better than the first frame's cold-start gravity. Avoids hard-failing on fly-through captures.

4. **No capture-format change. No operator requirements.** Stationary detection uses only the pose deltas already in `frames.csv` — translation delta is a position-jitter proxy, frame-to-frame rotation delta is a gyro-magnitude proxy. The system works regardless of whether the operator pauses before stopping capture.

The original framing of this fix in this memo (verbatim: "Use the last stable frame for the origin's pose") had both translation and rotation come from the same stable frame, plus an optional multi-sample averaging step. That was rejected because:
- Taking translation from a late frame puts the map origin wherever the user happened to stop — arbitrary, anti-intuitive for georegistration.
- The user explicitly does not want operator-side requirements ("pause before stopping"). The stationary-detection-from-pose-deltas approach removes that requirement entirely; the average-multiple-samples extension is a further refinement we could add later but isn't needed for the baseline.

Confirmed: `frames.csv` is recorded **live** (each row appended at frame-capture time, not regenerated post-hoc) — verified at `docker/zed-capture/src/zed/zed.py:309-322` (`update_pose` + immediate `csv_writer.writerow`) and `packages/unity/Placeframe/Assets/Package/Core/Runtime/CaptureManager.cs:43` (`AutoFlush=true`). So frame 0's row reflects the SDK's world-Y as of T_0 (cold-start) and frame N's row reflects the SDK's world-Y as of T_N (converged). The plan relies on this distinction — if the capture tools ever switch to post-hoc pose recording, the rotation-from-late-frame strategy becomes a no-op.

### Stationary detection thresholds (starting values)

- **Window size**: 30 frames (~1 s at 30 fps).
- **Translation delta**: total translation traversed in the window < 2 cm. Hand-jitter floor for a held device.
- **Frame-to-frame rotation magnitude**: each consecutive frame's `R_i · R_{i-1}^-1` rotation angle < ~0.5°, summed across the window < 5° (or: max single-frame delta < 1°). Catches pure in-place panning that wouldn't show up in translation delta alone.
- Tunable empirically. The cost of being too strict is falling back to the "median of last 25%" path (still good); the cost of being too loose is admitting a moving frame whose gravity is contaminated.

### Implementation footprint

- ~30-50 lines of Python in `colmap.py` (sliding-window stationary detection helper + anchor-selection logic).
- Possibly extract the stationary-detection helper to a small standalone function for reuse.
- One change to the `Sim3d` construction at `colmap.py:189-200`: the rotation and translation now come from different frames, so the formula needs to build `anchor_frame_prior_pose` as a `Transform(rotation=R_chosen, translation=T_first)` rather than reading both off one anchor.
- Anchor's COLMAP rig pose (`anchor_rig_from_world_transform`) stays as the first registered frame's. The Sim3d math is internally consistent because the Sim3d only needs *one* target pose; we're free to pick (R_chosen, T_first) as that target.

### Final accuracy estimate for "sample gravity at the last stable frame"

**Accuracy defined**: angular error between the direction declared as "world up" in the reconstructed map and true local vertical (opposite to actual gravity), in degrees. Decomposes into:
- **Random** -- changes run-to-run on same device (sensor noise, sample timing, recent motion). Averages down with multiple samples.
- **Systematic** -- consistent across runs under same conditions (residual online-bias estimate, camera-IMU extrinsic miscal, thermal state). Doesn't average within a session but varies between sessions/devices.

Does *not* include map origin position, scale, or yaw alignment between captures -- just tilt of the map's Y axis from true gravity.

Error budget (rough order-of-magnitude, speculative from MEMS literature, not measured against the actual pipeline):

| Source | Typical contribution |
|---|---|
| Accelerometer sensor noise at rest | 0.1° (random) |
| Online bias residual after a warmed-up session | 0.05--0.2° (systematic per session) |
| Camera-to-IMU extrinsic miscalibration | 0.05--0.2° (systematic per device) |
| Thermal drift during a long session | 0.1° (systematic per session) |
| Gyro bias contribution to attitude at rest | <0.05° (negligible) |
| Linear-accel residual in the last frame | 0--0.5° (depends on how stationary) |

Estimated end-to-end accuracy for the recommended approach:

- **Typical** (warmed-up session, genuinely stationary last frame, room temp): **0.3--0.5°**. Plan around this.
- **Best** (averaging ~10 stationary samples, well-calibrated ZED X or high-tier phone): **~0.1--0.2°**. Approaching the practical floor.
- **Worst** (short session, thermally stressed device, residual motion in last frame, cheap commodity IMU): **1--2°**. Defend with the stationary-detection threshold -- refuse the sample if motion is above it.

### Leverage table -- visible vertical overlay error at distance D from map origin

| Distance | 2° (broken / worst case) | 0.5° (typical w/ last-stable) | 0.3° (typical w/ last-stable) | 0.1° (averaged best case) |
|---|---|---|---|---|
| 1 m   | 3.5 cm | 0.9 cm | 0.5 cm | 0.2 cm |
| 5 m   | 17 cm  | 4.4 cm | 2.6 cm | 0.9 cm |
| 20 m  | 70 cm  | 17 cm  | 10 cm  | 3.5 cm |
| 50 m  | 1.75 m | 44 cm  | 26 cm  | 9 cm   |

For the scales Placeframe actually targets (room and building, up to ~20 m), this approach delivers visible overlay error in the single-digit-centimeter range typically, ~17 cm worst-case multi-room. That's much better than what 6 DOF with the current pivot bug delivers, and probably indistinguishable from a properly-fixed 6 DOF filter in practice. The accuracy story is good enough to commit to the 4 DOF plan **without** the OS gravity-sensor capture-format change.

Important comparison: even a *fixed* 6 DOF filter would have ~1° per-measurement PnP rotation noise contributing leveraged error at distance. The 6 DOF flexibility only absorbs map tilt if per-measurement pitch/roll is unbiased. 6 DOF is **not** obviously better than 4 DOF for the relevant scales.

### Note on the 0.1° vs 1° figures

Sensor floor for consumer MEMS is ~0.1° in quiescent conditions. The 1° figure earlier in the discussion is *end-to-end system delivery* (AR SDK output that integrates bias, motion contamination, calibration imperfection over a session). User caught the gap. The reason last-stable-frame helps: bias estimation and continuous world-frame refinement that have run for the whole session are far better than what existed at session start, recovering the system error from "~1°" to "~0.3--0.5°" -- not the full ten-fold recovery to sensor floor, but meaningful. Independent OS-sensor sampling would mostly duplicate work the SDK is already doing.

### How to measure this for real

No published benchmark gives attitude error directly for ARCore/ARKit/ZED X. To get real numbers for this pipeline: capture against a precision inclinometer, or compare independent captures of a known-vertical reference (plumb line, building corner). Cheapest proxy: capture the same scene twice, fit floor planes in both reconstructions, measure the angle between them -- that's a lower bound on random error including between-session systematic differences.

### Localization-time gravity (deferred)

Reconstruction-time gravity error is **permanent in the map and affects every future user** -- high leverage to fix. Localization-time gravity error (querying device's current world-Y drifted from true vertical) is **transient per-session**, typically smaller (AR session has had warm-up time before the user opens validation mode), affects only that one user's overlay, self-corrects on session restart -- lower leverage. **Ship reconstruction-time gravity pinning first; defer localization-time correction unless a real symptom is observed.** If it ever matters, the fix is ~30 lines in `Localize` / `ComputeAlignmentFromResult`, or (better) sending the device's gravity vector with the localization request as a PnP prior.

## Decisions

- The 4 DOF (yaw + R^3) state-representation refactor of `RelocalizationFilter` is the agreed direction for the pivot bug. User indicated next step is **implement, not design more**.
- The "open design decisions" in the earlier draft were not actually open (yaw extraction = Z-projection; multi-map ECEF out of scope; backend keeps 6×6 covariance and client projects). Implementer should not surface these as open questions.
- **No permanent feature flag for 4 vs 6 DOF.** Permanent toggles mean "we never resolved the question." If a validation-period A/B is wanted, prefer a **shadow filter** (both filters update on every measurement, one drives rendering, surface the divergence in the metrics UI) over a runtime toggle. Has a clean "delete after validation" exit. User did not explicitly green-light building the shadow filter; treat as available option, not required.
- **Reconstructor companion work: "translation from first registered frame, rotation from latest stationary frame, fallback to median rotation across last 25%."** Earlier framing had both components come from one "last stable frame" plus operator-pause-before-stop assumption; both walked back. New framing splits the components by their actual roles (translation = georegistration convenience; rotation = gravity quality) and uses pose-delta-based stationary detection so no operator behavior is required. No capture-format change. OS-sensor route remains a future option but currently unjustified. Implementation ~30-50 lines of Python in `colmap.py`.
- **Stationary detection thresholds**: window of 30 frames (~1 s at 30 fps); translation traversal < 2 cm; per-frame rotation magnitude < ~0.5° (cumulative < 5°). Tunable empirically.
- **Investigation branch is `investigation/validation-mode-bugs`** (created at user's request). Memory has been committed three times during the session prior to this entry (`602da12f`, `b717cd67`, `6748d0b7`); this update is the fourth.
- Trust-but-verify: initial Explore-agent pass produced an overview with inaccuracies (claimed `ComputeAlignmentFromResult` was strictly correct). Direct file reads confirmed the gravity-snap-then-translate bug. Use the same pattern for implementation review.

## Open questions

- Whether to build the dual/shadow filter for the validation period, or just ship 4 DOF and rely on the reconstructor fixes. User leaned toward "trust upstream gravity" by end of session; implementer should ask before building the dual-filter scaffolding.
- The reconstructor anchor change is being landed **before** the 4 DOF refactor (not bundled). Sequencing rationale: tightens upstream gravity first so the 4 DOF assumption (zero tilt in the map) is well-grounded when (5) is field-tested.
- Stationary detection thresholds need empirical tuning. Starting values: 30-frame window, < 2 cm translation traversal, < 0.5° per-frame rotation magnitude.
- Refusal behavior for captures that produce no stationary window: not needed in the baseline plan — the "median rotation across last 25%" fallback handles fly-through captures without hard-failing. Revisit only if field data shows the fallback produces unacceptably tilted maps.
- Whether the OS-fused gravity sensor capture-format change is ever needed. Currently deferred indefinitely; revisit only if measurements show pose-delta-based stationary detection is materially worse than an independent gravity signal. The user explicitly questioned whether this added value at all, given AR SDKs do their own gravity refinement.
- Which ARFoundation signal to use for VIO-discontinuity detection: no first-class "pose jumped" event. Options: `ARSession.sessionStateChanged` (coarse), tracking-state transitions on `XROrigin.Camera.trackingState`, or detect large frame-to-frame VIO deltas ourselves. Needs a small spike. Independent of the 4 DOF refactor.
- Whether Bug 1's fix should reset the entire `_state` or only clear `HasAcceptedMeasurement` + `LastAcceptedVioPosition` so the first measurement snaps. Full reset is simpler/safer; partial reset preserves the prior as a hint, which is probably worthless after an arbitrary stop interval.
- Validation harness for the gravity-pinning change: cheapest path is capture-the-same-scene-twice and measure floor-plane angle between reconstructions. More rigorous would be capturing against a precision inclinometer or a known plumb-line reference. Decision deferred to implementer.

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
- **Reconstructor anchor change: translation from first registered frame, rotation from latest stationary frame (or median rotation across last 25% as fallback).** Implementation ~30-50 lines of Python in `colmap.py:182-200`. Stationary detection from pose deltas in `frames.csv` — no capture-format change, no operator requirement. Companion to the 4 DOF refactor; tightens typical map tilt from "~1°" (first-frame, possibly cold-start) to "~0.3-0.5°" (warmed-up converged gravity). **Land this before (5).**
- **Decide legacy-map handling.** 4 DOF filter against old (tilted) maps will look bent. Re-process vs version-flag-and-use-6DOF-for-legacy. Ask user.
- **Verify Bug 2 field hypothesis.** Revisit the far room via different paths; if offset is consistent it's the alignment math (4 DOF refactor will fix it), if path-dependent it's reconstruction warp (separate problem). Worthwhile even after shipping the refactor.
- **(Deferred, not active.)** OS-fused gravity sensor capture-format change. Was previously a planned thread; demoted to a future option pending evidence the last-stable-frame VIO output is insufficient. Don't pre-build.
