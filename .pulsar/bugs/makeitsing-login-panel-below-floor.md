# Bug: MakeItSing login panel appears below floor on Magic Leap

## Status: not fixed; investigation paused pending design discussion

The branch is clean of all prior fix attempts and the diagnostic instrumentation added during this investigation — all reverted off `diagnostics/makeitsing-unity-env` so the file state matches `origin/dev`. This doc preserves the evidence and conclusions so the next attempt can start from a sharpened baseline.

## Symptom

On Magic Leap 2, the login panel **starts in the correct position in front of the user** on a fresh app launch, then drops to well below floor level "a moment later" (subjectively a fraction of a second to ~1 s).

User's reports across sessions:

> the login panel consistently appears well below the ground level, which is a bit annoying, i think perhaps the origin of xr scene is not using the normal 1.5m offset that makes it so the origin is around head height.

> i just noticed that the log in panel appears to initially show up right in front of me, but then move to below floor level.

> [after a minimal anchor fix attempt] that issue is still occuring. our fix did not work. The issue does appear to be a race condition, where when you start the app, the login panel starts in the right place, but then a moment later is below the floor.

## Telemetry captured during investigation

Diagnostic logging was added to `AppUI` and then removed; this is the data it collected on the most recent ML2 launch. `[AppUI] SystemUICanvas placed` fires once at canvas construction. `[AppUI] trackingOriginUpdated` fires whenever the OpenXR runtime re-anchors. Timestamps below are relative to the first event.

| Δt | Event | Camera world pos |
|---|---|---|
| +0.000s | `xrInputSubsystem subscribed running=True mode=Floor supported=11` | — |
| +0.002s | `xrPose t=+0.00s` | (0.000, **0.000**, 0.000) |
| +0.103s | `SystemUICanvas placed cameraPos=(0,0,0) canvasPos=(0,-0.330,1)` | (0.000, **0.000**, 0.000) |
| +0.322s | `trackingOriginUpdated mode=Device` | (0.000, **1.181**, -0.007) |
| +2.688s | `trackingOriginUpdated mode=Device` | (0.000, **1.181**, -0.007) |
| +5.186s | `trackingOriginUpdated mode=Floor` | (-0.001, **1.155**, 0.009) |
| +5.188s | `xrPose t=+0.10s` | (-0.001, 1.152, 0.012) |
| +5.587s | `xrPose t=+0.50s` | (-0.007, 1.074, 0.075) |

What this proves:

1. **Canvas was placed pre-snap.** Camera world pos at placement was (0, 0, 0); canvas anchored at world (0, -0.33, 1).
2. **Tracking origin re-anchored at t≈+0.322s.** Camera world Y jumped from 0 to 1.181 m discontinuously.
3. **Three `trackingOriginUpdated` events fire**, with mode walking Device → Device → Floor over 5 seconds. The XR Origin prefab has `m_RequestedTrackingOriginMode: 1` (Device); the subsystem reports `Floor` at subscription time, then events flip the active mode through `Device → Device → Floor`.
4. **Panel offset after snap = 1.181 − (−0.33) = ~1.51 m below the user's head.** Matches "below the floor" report.

Side observation (not actionable for this bug but worth noting elsewhere): the `xrPose` polled samples — intended to fire at t = 0, 0.1, 0.5, 1, 2, 3, 5 s after `Awake` via `UniTask.Delay` — clustered at ≥5.188 s real time. The async delay appears to stall while the XR session is initializing (player loop not ticking?). The `trackingOriginUpdated` events still carry actionable signal; the polled samples did not.

## Walking through the original hypotheses

1. **~~Camera position not meaningful at Awake.~~** Ruled out. The "starts right" phase confirms `Camera.main.transform.position` at placement-time was internally consistent with the rest of the world at that moment.
2. **ML runtime re-snaps its tracking origin after our placement.** Confirmed by telemetry.
3. **~~Something overriding the canvas transform every frame.~~** Ruled out — a per-frame override couldn't produce a discrete one-shot drop a moment after launch.
4. **~~`Camera.main` resolves to wrong camera.~~** Ruled out by the starts-right phase.

## What was tried and reverted

All four attempts below are no longer on the branch; they're listed only to keep future iterations from re-trying them.

1. **Deferred-placement helper.** `MonoBehaviour` that waited in `LateUpdate` for `Camera.main.transform.position.y > 0.1f` before writing the canvas's world position. Rejected by the user as too invasive.
2. **Structural refactor — rebuild canvas on every screen change.** Moved worldspace canvas creation out of `AppUI.Awake` into the reactive screen-switch observable, mirroring `legacy/Outernet.Client/Assets/SystemUI.cs`. Rejected as more invasive than the bug warrants.
3. **Switch tracking origin mode to Floor.** Changing `XR Origin.prefab`'s `m_RequestedTrackingOriginMode` from `1` (Device) to `2` (Floor). Not landed — legacy reference app uses `m_RequestedTrackingOriginMode: 1`, so matching legacy means *not* changing tracking mode.
4. **Minimal `position += camera.position;`** in `AppUI.SystemUICanvas`. Single-line change committed and field-tested — empirically did not fix the on-device symptom.

## Why the obvious next fix is uncertain

The clean expression of the working hypothesis — "ML2 re-snaps after placement; world-anchored canvas doesn't follow" — suggests parenting the canvas under the XR Origin so it rides the re-snap. That is plausible only if the rig's *transform* is what moves during the re-snap. The telemetry shows the camera's *world* position jumps from y=0 to y=1.18, but does not distinguish between:

- **(a) Rig translated.** The XR Origin GameObject's transform was moved (e.g., by `XROrigin.OnTrackingOriginUpdated` translating the rig to compensate for the runtime's new origin). In this case, parenting the canvas under the XR Origin would carry the canvas along — the bug doc's recommendation works.
- **(b) Camera local pose changed.** The rig stayed at identity and the `TrackedPoseDriver` on `Main Camera` wrote a new local position reflecting the runtime's re-anchored device pose. In this case, parenting the canvas under the XR Origin would leave the canvas at its old world position — the panel still ends up below the user's new head. The fix wouldn't work, and the canvas would have to be re-placed on `trackingOriginUpdated` (option 2 below) or parented under the camera itself with the offset baked in (head-locked, which the user does not want).

The XR Origin prefab has `m_CameraFloorOffsetObject: {fileID: 0}` and `m_CameraYOffset: 0`, which means the standard `XROrigin` height-compensation path has no offset object to translate. Whether the `XROrigin` component instead translates *itself* in (a)-style behavior, or leaves it to the camera in (b)-style behavior, depends on `Unity.XR.CoreUtils.XROrigin`'s implementation under the active OpenXR runtime — and we have not verified this empirically.

**This is the open question.** Either a Unity-side experiment (log `XROrigin.transform.position` alongside `Camera.main.transform.position` across the snap) or a discussion with the codebase author would resolve it. Until then, picking a fix is guesswork.

## Candidate fixes (re-stated with the (a)/(b) caveat)

1. **Parent the worldspace canvas under the XR Origin.** Smallest change. Only fixes the symptom under (a). Doesn't make (b) worse than today.
2. **Subscribe to `XRInputSubsystem.trackingOriginUpdated` and re-write the canvas's world position when it fires.** Surgical; works under both (a) and (b). Telemetry shows three events fire over 5 seconds; the re-placement would either run for each event or pick the final one (e.g., the first mode-change event). Introduces event-subscription lifecycle that didn't exist before.
3. **Re-place on first non-trivial pose event.** Defer placement to a frame where `Camera.main.transform.position.y > threshold` *or* the first `trackingOriginUpdated` fires, whichever first. Functionally the previously-rejected deferred-placement helper, scoped to the re-snap event.
4. **Structural rebuild on screen change.** Previously rejected on scope; documented for completeness because it would also fix this as a side effect.

The right choice depends on (a) vs (b) and on which behaviors the codebase author wants to commit to. Not picking one without that discussion.

## Verification once a fix lands

- Cold-launch the app on ML2, watch the login panel from headset POV.
- Pre-snap: panel should appear ~1 m in front, ~33 cm below eye height (current correct starting state).
- Post-snap: panel should stay in the same place relative to the user. Currently drops; after a working fix it should not.
- Repeat 3× across sessions to confirm not flake-dependent.

## Files of interest

- `apps/MakeItSing/Assets/App/UI/AppUI.cs` — `SystemUICanvas`, currently identical to `origin/dev` (no fix or telemetry).
- `apps/MakeItSing/Assets/App/Scene/XR Origin.prefab` — `m_RequestedTrackingOriginMode: 1` (Device), `m_CameraYOffset: 0`, `m_CameraFloorOffsetObject: 0`. Matches legacy.
- `apps/MakeItSing/Assets/App/Scene/AvatarViewComponent.cs:25` — other consumer of `Camera.main.transform.position`; sanity-check whichever fix lands against this code path.
- `legacy/Outernet.Client/Assets/SystemUI.cs` (lines 39–81, `ARLoginScreen()`) — reference structure where canvas+content is created reactively on `loggedIn` change.
- `legacy/Outernet.Client/Assets/OuternetClient/XR Origin.prefab` (lines 685–687) — same tracking-mode settings as MakeItSing.

## Next steps

1. Resolve the (a)/(b) question above — either via a one-shot diagnostic run that logs `XROrigin.transform` across the snap, or via direct discussion with the codebase author.
2. Pick a fix from the candidate list with the (a)/(b) answer in hand.
3. Implement and verify per the cold-launch procedure above.
