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

### Bug 2 root cause (most likely: ~40% math; ~40% geometric leverage of small real rotation error; ~20% actual reconstruction bow)

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

After the gravity snap, the composed `transform_unityFromMap` is no longer a rigid-body composition: the translation pins the map origin where the original (un-snapped) rotation put it, and then the gravity-snapped rotation rotates the rest of the map around that pinned origin. A pitch correction of θ around the map origin moves a point at distance D from the map origin by ~D * sin(θ).

A 1° systematic pitch bias from PnP (entirely plausible) lifts (or lowers) a point 20 m away by ~35 cm -- matches the observed magnitude. "Consistently too high in the same far room" is exactly the shape of a small systematic pitch correction applied about a far pivot.

To distinguish math bug from real reconstruction bow: revisit the far room via different paths. Consistent same-height offset = alignment math; path-dependent = reconstruction warp. Also can fetch reconstruction frame poses via `GetReconstructionFramePoses` and plot the trajectory in map coordinates to look for bow directly.

## Decisions

- Diagnosis posted to user; no code changed in this session. User asked to memorize before proceeding.
- Investigation done on a fresh branch `investigation/validation-mode-bugs` (created at user's request before memorize).
- Trust-but-verify approach worked: an initial Explore-agent pass produced a useful overview but had inaccuracies, e.g. claimed `ComputeAlignmentFromResult` was strictly correct. Direct file reads were needed to confirm the gravity-snap-then-translate bug.

## Open questions

- Which of the three Bug-2 hypotheses dominates? Field test (same far room via different paths; trajectory plot from `GetReconstructionFramePoses`) would resolve it.
- Should the Bug-1 fix reset the entire `_state`, or only clear `HasAcceptedMeasurement` + `LastAcceptedVioPosition` so the first measurement snaps? Full reset is simpler and safer; partial reset preserves the prior as a hint, which is probably worthless after an arbitrary stop interval.
- Best ARFoundation signal for VIO-discontinuity detection: there is no first-class "pose jumped" event. Options include `ARSession.sessionStateChanged` (coarse), tracking-state transitions on `XROrigin.Camera.trackingState`, or detecting large frame-to-frame deltas in the VIO pose ourselves. Needs a small spike.
- Is gravity snapping in `ComputeAlignmentFromResult` actually needed? If the VPS rotation is already gravity-aligned (it should be -- the map is georeferenced), the snap is redundant and the cleanest fix is to delete it. If the VPS pitch is unreliable, the snap stays but must be applied **before** translation is computed (or recompose translation about the camera pivot, not the map origin).

## Key files

- `packages/unity/Placeframe/Assets/Package/Core/Runtime/VisualPositioningSystem.cs` -- `StartLocalizing` / `StopLocalizing` (156-190); `Localize` and silent-rejection debug log (~215, ~253); `EcefToUnityWorld` (192-205); `OnEcefToUnityWorldTransformUpdated` event.
- `packages/unity/Placeframe/Assets/Package/Core/Runtime/RelocalizationFilter.cs` -- EKF on SE(3); `shouldSnap` gate (137); `ProcessNoise` (218-243); `ComputeAlignmentFromResult` gravity-snap bug (265-310); chi-squared gate `Chi2_99_6dof = 16.81`.
- `packages/unity/Placeframe/Assets/Package/Core/Runtime/LocalizationMap.cs` -- one-shot transform write in `DownloadMapAndLoad` (119-120); never resubscribes to `OnEcefToUnityWorldTransformUpdated`.
- `packages/unity/Placeframe/Assets/Package/Core/Runtime/GeoPose.cs` -- the *correct* pattern: subscribes to `OnEcefToUnityWorldTransformUpdated` at line 67 and re-applies on every update.
- `packages/unity/Placeframe/Assets/Package/ARFoundation/Runtime/CameraProvider.cs` -- only place `ARSessionState` is referenced; used as gate (lines 144, 263), not as event source.
- `apps/AndroidMobile/Assets/LocalizationManager.cs` (14-46) and `apps/AndroidMobile/Assets/Scripts/Capture/AppUI.cs` (398-495) and `apps/AndroidMobile/Assets/Scripts/Capture/AppState.cs` (16-81) -- the validation UI / state wiring driving `StartLocalizing` / `StopLocalizing` via `App.state.localizing`.

## Pending threads

- **Fix Bug 1 (filter state carry-over).** Reset `_state` in `StartLocalizing` (or at minimum clear `HasAcceptedMeasurement` and `LastAcceptedVioPosition`) so the first post-Start measurement snaps rather than slews from a stale prior.
- **Fix Bug 1 (VIO jump unhandled).** Subscribe to an ARFoundation tracking-discontinuity signal and re-bootstrap the filter covariance on detected jumps so the chi-squared gate softens enough to accept the next measurement.
- **Fix the LocalizationMap drift.** Make `LocalizationMap` subscribe to `OnEcefToUnityWorldTransformUpdated` like `GeoPose` does, so the point cloud tracks the live alignment instead of freezing at load-time.
- **Fix Bug 2 (gravity-snap composition).** Either (a) drop the gravity snap entirely and trust VPS rotation, or (b) recompose translation about the camera pivot using the snapped rotation, so the result remains a valid rigid-body transform.
- **Verify Bug 2 hypothesis in the field.** Revisit the far room via different paths; if offset is consistent it's the alignment math, if path-dependent it's reconstruction warp. Also plot `GetReconstructionFramePoses` output to inspect for bow directly.
- User asked "Want me to do either?" at end of last turn -- the next session should ask which fix to take first, or just start with the cheapest (Bug 1 state reset + `LocalizationMap` resubscribe).
