# Capture-tool validation mode: fix plan

Source memory: `.pulsar/memories/capture-validation-bugs.md` (full diagnosis, rationale, and accuracy analysis). This file is the execution order — it does not re-derive the design.

Branch: `investigation/validation-mode-bugs`.

## TL;DR

Fix the "point cloud too high in rooms far from the map origin" bug at two layers:

1. **Frontend (`RelocalizationFilter`):** replace 6 DOF SE(3) state with 4 DOF (yaw + R³). Today's gravity-snap mutates rotation post-composition while leaving translation alone, which pivots the correction around the map origin and produces D·sin(θ) vertical error at distance D. Encoding the constraint in the state representation makes the bug class structurally impossible — the projection naturally pivots on the camera, where the measurement is anchored.
2. **Reconstructor (`colmap.py` / `rig.py`):** pin the map origin's gravity to the *last* warmed-up stationary frame instead of the first registered frame. Tightens worst-case map tilt from ~1° to ~0.3–0.5°.

Three locked decisions worth flagging up front: yaw extraction uses Z-projection (graceful near vertical); 6→4 covariance projection uses a diagonal-dominant Jacobian in v1 (TODO marker for full Jacobian); chi² gate becomes 13.28 (4 DOF) instead of 16.81 (6 DOF). Three open questions need a user answer before coding: shadow-filter for validation period or not; land the reconstructor change alongside the refactor or as a follow-up; what to do about legacy maps with tilt already baked in.

Bug-1 (post-Stop/Start jump) and its sub-issues are deferred — see "Out of scope" below.

## Bug being fixed

**Far-from-origin height bias.** Point cloud is consistently too high in rooms distant from the map origin. Caused by the gravity-snap in `ComputeAlignmentFromResult` mutating rotation while leaving translation alone — pivots the correction around the map origin instead of the camera. A 1° pitch correction at 20 m produces ~35 cm vertical lift, which matches the field observation.

## Decisions already locked

Do not re-surface these as open questions when implementing.

- 4 DOF state (yaw + R³) replaces 6 DOF SE(3) in `RelocalizationFilter`. The gravity-snap post-projection goes away because the projection lives in the state representation itself.
- Yaw extraction uses Z-projection (`atan2(mapForwardInUnity.x, mapForwardInUnity.z)`) — degrades gracefully at near-vertical singularity.
- Backend keeps 6×6 PnP covariance; the 6→4 projection happens client-side.
- v1 covariance projection uses diagonal-dominant Jacobian; full Jacobian (with cross-terms scaling in `|t_mapFromCamera|`) is a follow-up TODO.
- Chi² gate is 13.28 (4 DOF, 99%), not 16.81 (6 DOF).
- No permanent 4-vs-6 DOF feature flag. A shadow filter (both update, one drives rendering, divergence in metrics UI) is an *option*, not a requirement — ask the user before building it.

## Open questions — ask before acting

- **Shadow filter?** Build it for a validation period, or just ship 4 DOF and trust the reconstructor fix?
- **Land reconstructor "last stable frame" change alongside the 4 DOF refactor, or as a follow-up?** Either is defensible; the leverage math justifies 4 DOF even without it at room/building scale.
- **Legacy maps.** A 4 DOF filter against a map with tilt baked in will look bent. Re-process all legacy maps, or version-flag them and keep 6 DOF for the legacy path?

## Phase 1 — 4 DOF refactor of `RelocalizationFilter`

The pivot bug disappears structurally when the constraint lives in the state representation. This is the main change.

### Files

- `packages/unity/Placeframe/Assets/Package/Core/Runtime/RelocalizationFilter.cs` — substantial rewrite.
- `packages/unity/Placeframe/Assets/Package/Core/Runtime/VisualPositioningSystem.cs` — small (state struct shape changed; `EcefToUnityWorldTransform` still returns `double4x4`, assembled on read).
- `packages/unity/Placeframe/Assets/Package/Core/Runtime/Se3.cs` — delete `Exp` / `Log` (no tangent space needed).
- `packages/unity/Placeframe/Assets/Package/Core/Runtime/MathUtil.cs` — add `WrapAngle(double)` and `YawFromRotation(double3x3)` (document the near-vertical singularity).
- `packages/unity/Placeframe/Assets/Package/Core/Tests/Editor/RelocalizationFilterTests.cs` — rewrite for 4D state.
- `packages/unity/Placeframe/SPEC.md` — note the 4 DOF assumption and dependence on upstream gravity.

### State

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

### Bootstrap and process noise

- `BootstrapSigmaYawRadians = π`; `BootstrapSigmaTranslationMeters = 100`; 4×4 diagonal `[π², 100², 100², 100²]`.
- Process noise: 4×4 diagonal `[yaw_var, t_var, t_var, t_var]` plus `(0.01 × |Δvio|)²` on all four diagonals (same per-meter drift model as today).

### Measurement projection

`ComputeAlignmentFromResult` returns `(yawMeas, tMeas)` and a 4×4 covariance. **Delete the current gravity-correction step** — the projection enforces gravity alignment in the geometrically correct place.

```csharp
// 1. Compose rotation (no gravity correction).
var R_unityFromMap = R_unityWorldCamera * R_cameraFromMap;
// 2. Extract yaw from R_unityFromMap (Z-projection variant).
var mapForwardInUnity = R_unityFromMap * new double3(0, 0, 1);
var yawMeas = math.atan2(mapForwardInUnity.x, mapForwardInUnity.z);
// 3. Translation anchored on the camera.
var R_yawOnly = QuaternionAroundY(yawMeas);
var tMeas = t_unityWorldCamera - math.mul(R_yawOnly, t_mapFromCamera);
```

### Covariance projection (6×6 → 4×4)

v1: diagonal-dominant Jacobian (yaw ← ωy, tx ← νx, etc.). `Σ_meas_4 = H_diag · Σ_meas_6 · H_diagᵀ`. Drops cross-correlation between discarded pitch/roll and kept dimensions. Mark TODO for full Jacobian; revisit if the filter looks under-confident at non-zero `t_mapFromCamera`.

### Innovation / gate / Kalman / slew

- Residual: `[wrap(yawMeas - yawState), tMeas - tState]` with `wrap(θ) = ((θ + π) mod 2π) − π`.
- Mahalanobis gate: **chi² 99%, 4 DOF = 13.28** (replace `Chi2_99_6dof = 16.81`).
- Kalman update is 4D; no SE(3) exp/log.
- Slew: linear on translation; shortest-arc on yaw.

### Tests

- Rewrite `RelocalizationFilterTests` for 4D state.
- New regression: a measurement whose composed rotation has 2° pitch input must produce **zero** vertical offset at a map point 20 m from origin (this is the bug).
- New: yaw residual wraps correctly across ±π.
- Bootstrap → first measurement snaps (port from existing).

### Pitfalls

1. Yaw is S¹ — residuals must wrap modulo 2π or the filter spazzes near ±π.
2. Yaw extraction degenerates at pitch = ±90°. Z-projection variant degrades gracefully; document it.
3. The chi² gate constant changes — easy to miss.
4. v1 covariance projection drops cross-correlation between discarded pitch/roll and kept dimensions; mark the TODO.
5. The structural constraint is only as good as upstream gravity. A *legacy* map built before reconstructor gravity fixes will look bent under a 4 DOF filter — see legacy-maps open question above.

### Validation

- `RelocalizationFilterTests` green.
- Headless Unity compile check (from `/placeframe/CLAUDE.md`):
  ```bash
  /opt/unity/$(awk '/^m_EditorVersion:/{print $2}' packages/unity/Placeframe/ProjectSettings/ProjectVersion.txt)/Editor/Unity \
    -batchmode -nographics -quit \
    -projectPath packages/unity/Placeframe \
    -logFile - 2>&1 | grep -E "error CS|Compilation"
  ```
- Field test: re-walk the multi-room scene that exposed the bug; far-room height bias should be gone or at single-digit-cm range.
- Ask the user before committing the first cut.

## Phase 2 — Reconstructor: last-stable-frame for origin

Tightens worst-case map tilt from ~1° (first-frame, possibly cold-start) to ~0.3–0.5° (warmed-up stationary frame).

### Scope

- `docker/reconstructor/src/reconstructor/colmap.py:160-178` — single-anchor Sim3d alignment; switch the anchor from the first registered frame to the last stable one.
- `docker/reconstructor/src/reconstructor/rig.py:70-84` — supplies the truth poses; may need to expose tracking-state and motion data per frame.
- Stationary-detection helper: tracking-state OK + gyro magnitude below threshold for N consecutive frames + non-gravity linear-accel below threshold.
- Pin map "up" to the **non-yaw component** of that frame's reported camera rotation.

### Decisions deferred to implementer

- Concrete numeric thresholds (gyro magnitude rad/s, linear-accel m/s², sliding-window N). Pick from MEMS spec sheets and tune empirically.
- Warmup window per source — ARFoundation ~3 s, ZED ~1 s. Store as per-source config (capture format already records the source), not a magic number.
- Refusal behavior when no warmed-up stationary frame exists. Better than silently producing a tilted map. Decide error message and how it surfaces to the operator.

### Explicitly out of scope

OS-fused gravity sensor (`Sensor.TYPE_GRAVITY` / `CMMotionManager.gravity` / ZED `SensorsData`) as a new capture-format column. Walked back in design — the AR SDK's reported camera rotation at a warmed-up stationary frame is already a near-equivalent signal. Revisit only if measurements show it's materially worse than independently-sampled gravity.

### Validation

Cheapest path: capture the same scene twice, fit floor planes in both reconstructions, measure the angle between them — that's a lower bound on random error including between-session systematic differences. More rigorous: precision inclinometer or known plumb-line reference.

## Phase 3 — Field verification

Re-walk the far room via different paths after Phase 1 lands. If the offset is consistent across paths, the alignment math fix is sufficient. If path-dependent, that's reconstruction warp (separate problem outside this plan).

## Commit hygiene

From `/placeframe/CLAUDE.md` and Pulsar shared conventions:

- Prose (`*.md`) and source code commit separately, even when changed in the same session.
- If `SPEC.md` and code disagree, update the spec first and surface the diff, *then* change the code.
- Codegen artifacts (`packages/generated/`) live in dedicated commits with canonical messages (`Run generate-clients`, etc.). Not expected to be relevant for this plan unless the reconstructor change touches API routes.

## Out of scope

- **Bug 1 (post-Stop/Start jump)** and its sub-issues — filter state carryover in `StartLocalizing`, ARFoundation tracking-discontinuity detection, and `LocalizationMap`'s one-shot transform write that never re-syncs to `OnEcefToUnityWorldTransformUpdated`. All documented in `.pulsar/memories/capture-validation-bugs.md`; address in a separate plan.
- Localization-time gravity correction. Reconstruction-time error is permanent in the map and affects every user; localization-time error is per-session, smaller (AR session has had warm-up), self-corrects on session restart. Defer unless a real symptom is observed.
- OS-fused gravity sensor capture-format change. Demoted to a future option; do not pre-build.
