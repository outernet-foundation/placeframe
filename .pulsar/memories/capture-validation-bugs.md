---
updated: 2026-05-17
---

# Capture-tool validation mode: post-Stop/Start jump and far-from-origin point-cloud height error

## Goal

Two reproducible bugs in the AndroidMobile capture tool's "validation" (localize-against-a-just-built-map) mode, observed on a larger multi-room map:

1. **Stop -> Start jump.** After Stop then Start, localization briefly looks good, then "jumps" to an incorrect pose and stays there.
2. **Far-room height bias.** In the room where the scan started (map origin), localizations are good. In a far room at the opposite end of the map, the point cloud is consistently significantly too high.

Investigate root cause, distinguish math/geometry bugs from possible reconstruction warp, and prepare fixes.

## State

Diagnosis only -- no code changes yet. Investigation done on branch `investigation/validation-mode-bugs`. Findings verified by reading source directly (not just by trusting a sub-agent), so the line numbers and code structure below are confirmed against the working tree at this commit.

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

The user is right that **the visible symptom is a rotation error**, not a translation error: "things are too high in room B but fine in room A" is exactly what a small rotation error pivoted around the map origin produces (point at distance D from the map origin moves ~D * sin(θ)). A 1° pitch correction at 20 m = ~35 cm vertical lift -- matches the observation.

The mathematical equivalence: keeping `t` unchanged while rotating `R` is the same as "rotating around the map origin." The (R, t) pair is internally inconsistent with the camera anchor -- if you ask "where does the composed transform place the camera?" after the gravity snap, the answer has been shoved sideways by `θ * |camera - map_origin|`. Two valid framings of the *same* bug:

- "R is correct but pivoted around the wrong point" (user's framing).
- "t is wrong given the new R" (the local-fix framing).

User pushed back on the local fix ("compute then patch with a `_corrected` variable" is a code smell) and that pushback led to the proposal below.

### The deeper insight: the gravity snap exists for a real reason

User wrote the snap originally because: ARFoundation gravity and reconstructor gravity are both correct in principle, but **each individual VPS measurement has 6 DOF noise**, so the Kalman filter can converge with a slight tilt baked in. The snap exists to **structurally remove two DOF (pitch and roll) that we have a-priori knowledge are zero**, so the filter can't wander on them. That rationale is sound.

The bug is just *where* the constraint is encoded: a per-measurement post-hoc projection on the output of a 6 DOF composition introduces the pivot problem. The principled fix is to **encode the constraint in the state representation itself**: parameterize the alignment as 4 DOF (yaw + R^3 translation) instead of full SE(3). Then:

- The filter literally cannot represent a tilted alignment; the constraint is structural, not enforced.
- `AlignmentCovariance` becomes 4x4. No variance budget wasted on dimensions we know are zero.
- Process noise, the innovation gate, and the Kalman update all run in 4D.
- Each 6 DOF VPS measurement is projected to 4D on the way in via a measurement model `h: SE(3) -> (yaw, R^3)`. The projection has a **natural pivot -- the camera position**, because that's where the measurement is anchored. "Rotate around the camera" falls out of the geometry rather than being a separate manual step.
- No `_corrected` variable, no second translation formula, no inconsistency to repair.

This is the change the user's original rationale actually implies; the current code is an approximation of it.

## Decisions

- Diagnosis posted to user; no code changed in this session. User asked to memorize before proceeding.
- Investigation done on a fresh branch `investigation/validation-mode-bugs` (created at user's request).
- Trust-but-verify approach worked: an initial Explore-agent pass produced a useful overview but had inaccuracies, e.g. claimed `ComputeAlignmentFromResult` was strictly correct. Direct file reads were needed to confirm the gravity-snap-then-translate bug.
- The user pushed back on the local "recompute t" fix as a code smell ("we'd do a thing wrong, do another thing based on the wrong thing, then undo the wrongness"). That pushback was correct and led to the 4 DOF state-representation proposal.
- The 4 DOF proposal is the agreed direction; the user asked "draft the proposed change" as the next step.

## Open questions

- Which of the Bug-2 hypotheses dominates -- math (now identified as the constraint placement), real reconstruction bow, or a combination? Field test (same far room via different paths; trajectory plot from `GetReconstructionFramePoses`) would resolve it.
- Should the Bug-1 fix reset the entire `_state`, or only clear `HasAcceptedMeasurement` + `LastAcceptedVioPosition` so the first measurement snaps? Full reset is simpler and safer; partial reset preserves the prior as a hint, which is probably worthless after an arbitrary stop interval.
- Best ARFoundation signal for VIO-discontinuity detection: there is no first-class "pose jumped" event. Options include `ARSession.sessionStateChanged` (coarse), tracking-state transitions on `XROrigin.Camera.trackingState`, or detecting large frame-to-frame deltas in the VIO pose ourselves. Needs a small spike.

### Caveats / catches of the 4 DOF approach (none are dealbreakers, but worth keeping in mind)

1. **6 DOF measurement -> 4D state projection isn't free.** PnP gives a 6D pose + 6x6 covariance. Need a nonlinear measurement model `h: SE(3) -> (yaw, R^3)` with Jacobian; 6x6 covariance has to be folded into 4x4 via `H * Sigma * H^T`. Standard EKF mechanics, but real work.
2. **Yaw extraction degenerates near pitch = +/- 90 degrees.** Gimbal-lock-adjacent. Won't bite for a roughly-upright handheld phone but is a real failure mode at the extremes.
3. **Yaw is S^1, not R.** Residuals must wrap modulo 2*pi -- easy to forget; filter spazzes near +/- pi if you don't.
4. **Strongest caveat:** the structural constraint is *only as good as the upstream gravity guarantees*. If a particular reconstructed map has a small tilt baked in, the 4 DOF filter will force 0 tilt and the resulting alignment will be slightly bent. A 6 DOF filter would absorb the map tilt at the cost of the leverage bug. So the 4 DOF approach is strictly better *only* if the reconstructor's gravity alignment is trustworthy. Worth a sanity check on what the reconstructor actually guarantees.
5. **Innovation gate threshold changes.** Chi^2 99% at 4 DOF = 13.28 vs 16.81 at 6 DOF. Trivial code change but easy to miss.
6. The user asked whether they should only return a 4 DOF pose from the backend. Answer is no: keep the backend 6 DOF and project on the *client* side. The two extra DOF carry information in the measurement covariance even after projection, and the backend may serve other consumers with different constraints.
7. The user asked whether the ECEF math breaks down at scale. Answer: not at single-map scale. The intended workflow already uses multiple maps for large areas, so a single map staying small enough that float-precision around ECEF coordinates is non-pathological is by design.

## Key files

- `packages/unity/Placeframe/Assets/Package/Core/Runtime/VisualPositioningSystem.cs` -- `StartLocalizing` / `StopLocalizing` (156-190); `Localize` and silent-rejection debug log (~215, ~253); `EcefToUnityWorld` (192-205); `OnEcefToUnityWorldTransformUpdated` event.
- `packages/unity/Placeframe/Assets/Package/Core/Runtime/RelocalizationFilter.cs` -- EKF on SE(3); `shouldSnap` gate (137); `ProcessNoise` (218-243); `ComputeAlignmentFromResult` gravity-snap bug (265-310); chi-squared gate `Chi2_99_6dof = 16.81`. **Primary target of the 4 DOF refactor.**
- `packages/unity/Placeframe/Assets/Package/Core/Runtime/Se3.cs` -- exp/log; will need a sibling type or simplification for the 4 DOF (yaw + R^3) parameterization.
- `packages/unity/Placeframe/Assets/Package/Core/Tests/Editor/RelocalizationFilterTests.cs` -- must be ported alongside the filter refactor.
- `packages/unity/Placeframe/Assets/Package/Core/Runtime/LocalizationMap.cs` -- one-shot transform write in `DownloadMapAndLoad` (119-120); never resubscribes to `OnEcefToUnityWorldTransformUpdated`.
- `packages/unity/Placeframe/Assets/Package/Core/Runtime/GeoPose.cs` -- the *correct* pattern: subscribes to `OnEcefToUnityWorldTransformUpdated` at line 67 and re-applies on every update.
- `packages/unity/Placeframe/Assets/Package/ARFoundation/Runtime/CameraProvider.cs` -- only place `ARSessionState` is referenced; used as gate (lines 144, 263), not as event source.
- `apps/AndroidMobile/Assets/LocalizationManager.cs` (14-46) and `apps/AndroidMobile/Assets/Scripts/Capture/AppUI.cs` (398-495) and `apps/AndroidMobile/Assets/Scripts/Capture/AppState.cs` (16-81) -- the validation UI / state wiring driving `StartLocalizing` / `StopLocalizing` via `App.state.localizing`.

## Pending threads

- **Draft the 6 DOF -> 4 DOF (yaw + R^3) refactor of `RelocalizationFilter`.** User explicitly asked for this as the next step. Touches `FilterState`, `ProcessNoise`, `ApplyMeasurement`, `ComputeAlignmentFromResult`, the `Se3` helpers (or a new 4 DOF parameterization), and the filter tests. Do not commit -- the user wants to see the draft first.
- **Fix Bug 1 (filter state carry-over).** Reset `_state` in `StartLocalizing` (or at minimum clear `HasAcceptedMeasurement` and `LastAcceptedVioPosition`) so the first post-Start measurement snaps rather than slews from a stale prior. Independent of the 4 DOF refactor.
- **Fix Bug 1 (VIO jump unhandled).** Subscribe to an ARFoundation tracking-discontinuity signal and re-bootstrap the filter covariance on detected jumps so the chi-squared gate softens enough to accept the next measurement. Independent of the 4 DOF refactor.
- **Fix the LocalizationMap drift.** Make `LocalizationMap` subscribe to `OnEcefToUnityWorldTransformUpdated` like `GeoPose` does, so the point cloud tracks the live alignment instead of freezing at load-time. Independent of the 4 DOF refactor.
- **Verify Bug 2 hypothesis in the field.** Revisit the far room via different paths; if offset is consistent it's the alignment math (4 DOF refactor will fix it), if path-dependent it's reconstruction warp (separate problem).
- **Confirm the reconstructor's gravity-alignment guarantees** before relying on the 4 DOF structural constraint (caveat 4 above).
