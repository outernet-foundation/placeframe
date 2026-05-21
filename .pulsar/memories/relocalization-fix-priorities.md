---
updated: 2026-05-20
---

# Relocalization fix priorities (capture-tool validation mode)

## Goal

Two prior memos diagnosed a cluster of bugs in the AndroidMobile capture tool's "validation" (localize-against-a-just-built-map) flow:

- `.pulsar/capture-validation-bugs.md` — Stop→Start jump and far-room height bias; 4 DOF refactor design.
- `.pulsar/relocalization-filter-rejection-lockup.md` — chi² gate locks permanently after a VIO jump >~0.4 m because the rejection path doesn't write back `sigmaPredicted` to `state.AlignmentCovariance`.

On 2026-05-20 the user asked for an audit of the current code against those memos plus a review of the most-recent localization session against a freshly built map. The session was "pretty bad and unpredictable." Output: a ranked list of fixes, ordered by what would actually change the next session.

## State

- Audit complete. Every documented finding in both memos is **unfixed** on branch `fix/install-zed-aoa-gateway-and-pull-logging` (commit `c80193bd` at audit time). No code change yet for the relocalization issues themselves; the ranked list below is the next-session work.
- Two unrelated commits landed earlier in this same session and are not part of the relocalization fix queue:
  - `b6552560` — `CaptureController.cs` now refreshes the capture list every 5 s while logged-in + idle + zed-reachable (replaces the rising-edge-only `zedReachable` subscription that caused "capture not showing" after a transient AOA failure).
  - `aa706c03` + codegen `c80193bd` — `ReconstructionPublisher` now records per-phase wall-clock timings and persists them on `ReconstructionMetrics.phase_timings`. Reconstructor container still runs the old image; rebuild + bounce before the next reconstruction if you want timings captured.

### Audit table (all rows confirmed unfixed)

| Memo finding | Code location |
|---|---|
| Rejection path never writes back `AlignmentCovariance` (locks gate forever) | `RelocalizationFilter.cs:113-122`; only `KalmanUpdate` at line 340 writes covariance |
| Gravity snap mutates rotation, then translation is composed against uncorrected rotation | `RelocalizationFilter.cs:292, 295-297, 299-300` |
| Filter state survives Stop→Start | `VisualPositioningSystem.cs:35` (`static FilterState _state`); `StopLocalizing` (192-199) only disposes the subscription |
| Rejection silent (LogDebug only) | `VisualPositioningSystem.cs:262-273` |
| `LocalizationMap.transform` one-shot at load time; never re-syncs | `LocalizationMap.cs:119-120` (compare `GeoPose.cs:67` which subscribes to `OnEcefToUnityWorldTransformUpdated`) |
| `Reset()` exists but unreachable from validation UI | `RelocalizationFilter.cs:188`, only called from `SetEcefToUnityTransform` at `VisualPositioningSystem.cs:282` |
| No ARFoundation tracking-state subscription anywhere | Confirmed by grep |
| `Chi2_99_6dof = 16.81` constant | `RelocalizationFilter.cs:47` |

### Reviewed session: 2026-05-20 21:31:23 → 21:35:16 UTC

Pulled from Loki `{service_name="capture-tool"}`. 75 rejections, **0 accepts** over ~4 minutes.

- 21:31:39 — first measurement, `hadAccepted=True` (filter carried prior session's state). m²=37, ν≈0.24 m. Gate fires immediately.
- 21:31:43, 21:32:14, 21:33:14, 21:33:44 — four user-initiated Stop→Start cycles; none recover. Confirms "Stop→Start does not recover."
- 21:32:22 — residual jumps from ~0.25 m to ν=[1.36, 0.18, 0.64] (m²=1346). User walked or VIO jumped while the filter mean stayed pinned.
- 21:32:38 + 21:32:41 — two outlier PnPs (m²=7422, 9522, ν up to 13 m). `σ_predicted` spiked to ~2.5e-2 from the `0.01·|Δvio|` motion term, then collapsed back to ~5e-4 the next tick — the spike isn't written back, exactly per the lockup memo.
- 21:33:19 → 21:35:16 — residual essentially constant at ν≈[-0.55, -1.22, +0.87], |ν|≈1.55 m, ω_y≈0.05-0.07 rad. Sub-cm variation over ~50 measurements. Textbook lockup signature: state pinned, VIO 1.55 m away, gate closed forever.
- Rotation residual: ω_x, ω_z are always 0.0000; only ω_y nonzero. That's the gravity-snap stripping pitch/roll on the measurement side **before** it reaches the residual, so Bug 2 (pivot / far-room height) cannot be observed in this log — the filter never accepted.
- To unlock the 1.55 m residual via the `0.01·|Δvio|` term alone, the user would have had to walk ~25 m further. Confirms the rejection-lockup memo's numerical estimate.

## Decisions

### Ranked fix list (output of this session)

1. **Inflate `AlignmentCovariance` on the rejection path (cap at bootstrap).** `RelocalizationFilter.cs:113-122`. ~5 lines. **Only fix that would have changed today's session outcome.** Cap is essential — without it, the eventual unlock admits an outlier as eagerly as a good measurement.
2. **Reset filter on `StartLocalizing`.** `VisualPositioningSystem.cs:165` — add `_state = RelocalizationFilter.InitialState();` (or `Reset(_state, _state.AlignmentCurrent)` to keep the visible alignment until first re-accept). ~1-3 lines. The user reflexively did Stop→Start four times today; give that reflex a real recovery semantic.
3. **Surface lockup in UI + add a "Reset" button.** Add `ConsecutiveRejections` / `LastAcceptedTime` to `FilterState`; in `AppUI` show "localization lost" after N rejections or T seconds; button calls `Reset(_state, _state.AlignmentCurrent)`. ~30 lines. Today the user had zero in-app signal anything was wrong.
4. **`LocalizationMap` subscribes to `OnEcefToUnityWorldTransformUpdated`.** Mirror `GeoPose.cs:67`. ~10 lines. Fixes the "looks good, then drifts" contributor (point cloud frozen against load-time alignment). Independent of 1-3; bundle into a single PR if convenient.
5. **4 DOF refactor of `RelocalizationFilter`.** Fixes Bug 2 (gravity-snap pivot / far-room height bias). Large: rewrite filter, delete `Se3.Log/Exp`, port tests. Design is fully spec'd in `.pulsar/capture-validation-bugs.md` — do **not** re-surface its "open design decisions." **Do this AFTER 1+2** — right now Bug 2 is unobservable because the filter is locked.
6. **Reconstructor "last stable frame for origin pose."** Single-digit-line change in `colmap.py` / `rig.py`. Only matters once (5) is in (6 DOF flexibility absorbs map tilt; 4 DOF doesn't). Lands typical map gravity error from "~1°" to "~0.3-0.5°."
7. **ARFoundation tracking-state subscription → re-bootstrap on jump.** Per-platform, more work. Catches the 21:32:22-style jump at source. After 1+3 land it's a refinement, not a blocker.
8. **Decide legacy-map handling for the 4 DOF rollout.** Not code, but a precondition for (5): 4 DOF against an old tilted map renders bent geometry. Re-process vs version-flag — ask the user before (5) lands.

### Strategic ordering

- The (1)+(2)+(3) trio is the right first cut: tiny diff, restores in-session recovery, gives the user feedback.
- (4) is independent and cheap; bundle with 1-3 in a single PR.
- (5)+(6) are the proper Bug 2 story but must wait until you can see Bug 2 with a non-locked filter.

## Open questions

- Cap value for `AlignmentCovariance` on the rejection path — bootstrap covariance is the obvious choice but the cap shape (cap each diagonal vs cap the whole matrix vs cap eigenvalues) needs a pick.
- For (2), full reset (`InitialState()`) vs partial reset (clear `HasAcceptedMeasurement` + `LastAcceptedVioPosition` only). Full reset is simpler/safer; partial preserves the prior as a hint that's probably worthless after an arbitrary Stop interval.
- Thresholds for (3) — "lockup" trigger should be `ConsecutiveRejections > N` or `LastAcceptedTime > T`? Pick reasonable defaults (e.g. 5 rejections or 5 s) and surface in the UI.
- Whether to use ARFoundation's `XROrigin.Camera.trackingState` or a frame-to-frame VIO-delta heuristic for (7). No first-class "pose jumped" event; needs a small spike.
- Legacy-map handling for the 4 DOF rollout (re-process vs version-flag) — user decision required before (5).

## Key files

- `packages/unity/Placeframe/Assets/Package/Core/Runtime/RelocalizationFilter.cs` — `ApplyMeasurement` (99-168), rejection path (113-122) is fix (1)'s target; `Chi2_99_6dof = 16.81` (47); `ProcessNoise` (218-243); `ComputeAlignmentFromResult` gravity-snap (265-310, fix (5)); `Reset` (188).
- `packages/unity/Placeframe/Assets/Package/Core/Runtime/VisualPositioningSystem.cs` — `static FilterState _state` (35); `StartLocalizing` (156-180) is fix (2)'s target; `StopLocalizing` (183-189); silent-rejection log (~253-273).
- `packages/unity/Placeframe/Assets/Package/Core/Runtime/LocalizationMap.cs` — one-shot transform set at 119-120 (fix (4)'s target).
- `packages/unity/Placeframe/Assets/Package/Core/Runtime/GeoPose.cs:67` — correct subscription pattern to copy for (4).
- `packages/unity/Placeframe/Assets/Package/Core/Tests/Editor/RelocalizationFilterTests.cs` — needs the lockup regression test (post-1m-jump, 10 stationary measurements must eventually accept with fix (1)) added.
- `apps/AndroidMobile/Assets/Scripts/Capture/AppUI.cs`, `AppState.cs`, `LocalizationManager.cs` — validation UI wiring for fix (3) (lockup banner + reset button).
- `docker/reconstructor/src/reconstructor/colmap.py:160-178` and `rig.py:70-84` — single-anchor Sim3d alignment to first registered frame; target for fix (6).
- `.pulsar/capture-validation-bugs.md` — full 4 DOF refactor spec; do not re-derive.
- `.pulsar/relocalization-filter-rejection-lockup.md` — full mechanism + numerical estimates for fix (1); includes verification test sketch.

## Pending threads

- Start with fix (1): inflate `AlignmentCovariance = sigmaPredicted` on rejection, clamped to bootstrap covariance. Add the regression test from `relocalization-filter-rejection-lockup.md` § "Verification."
- Bundle (2) and (3) and (4) in the same PR with (1) — all small, all independent, together they make a session recoverable in-app.
- After landing 1-4, field-test: does a deliberate phone bump mid-validation re-lock within seconds rather than drifting until app restart?
- After 1-4 stabilize sessions enough to observe Bug 2, schedule the 4 DOF refactor (5). The design in `.pulsar/capture-validation-bugs.md` is settled — do not re-open it.
- Ask the user about legacy-map handling (8) before starting (5).
- Defer (6) until (5) is in. Defer (7) indefinitely unless 1-3 prove insufficient.
