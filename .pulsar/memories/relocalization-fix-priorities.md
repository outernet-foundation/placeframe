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

**Fixes 1-3 landed on branch `fix/install-zed-aoa-gateway-and-pull-logging`:**

- `0fe490c8` — Inflate filter covariance on rejection (fix 1). Rejection path now writes `sigmaPredicted` (clamped to bootstrap) back to `AlignmentCovariance`. Lockup-after-VIO-jump no longer permanent.
- `6c7bc7be` — Reset filter history on `StartLocalizing` (fix 2). `StartLocalizing` calls `Reset(_state, _state.AlignmentCurrent)` after validation, clears `_lastAcceptedTime`, `LastRejectionReason`, `LastInnovationMahalanobisSquared`. Stop→Start is now a real recovery action; the visible alignment is preserved until the next accept so the point cloud doesn't flash to identity.
- `d738045d` — Surface lockup in validation metrics dialog (fix 3, slimmed). Added `int ConsecutiveRejections` to `FilterState` (incremented on reject, zeroed on accept). New `FilterHealth` snapshot struct in `VisualPositioningSystem.cs`. Metrics dialog shows a red "localization lost" banner and the `FilterHealth` inspector when `Localizing && (ConsecutiveRejections > 5 || SecondsSinceLastAccept > 5)`. Bottom-bar Metrics button label turns red on lockup. **No dedicated Reset button** — Stop→Start post-fix-2 is the reset path.

**Fix 4 struck from queue.** Audit assumed `LocalizationMap` set its transform one-shot at load time with no re-sync. False — the `LocalizationMap.prefab` has a `GeoPose` sibling MonoBehaviour. `GeoPose.OnEnable` subscribes to `OnEcefToUnityWorldTransformUpdated` (`GeoPose.cs:67`) and `GeoPose.LateUpdate` back-fills its stored ECEF origin whenever the transform changes externally (`GeoPose.cs:76-86`). So `LocalizationMap.cs:119-120`'s direct transform write is reconciled the same frame, and subsequent alignment updates correctly re-apply the loaded ECEF. The "looks good, then drifts" symptom — if real — must come from a different source; re-observe on device with the lockup banner before re-prioritizing.

Narrow race remains: if `OnEcefToUnityWorldTransformUpdated` fires between `LocalizationMap`'s transform write and the next `GeoPose.LateUpdate`, `GeoPose` re-applies its pre-load ECEF (probably identity from `Awake`) and stomps the freshly-set transform. Frame-aligned, not systemic. Not worth fixing speculatively.

Two unrelated commits from the same session, not part of the relocalization fix queue:

- `b6552560` — `CaptureController.cs` refreshes the capture list every 5 s while logged-in + idle + zed-reachable.
- `aa706c03` + codegen `c80193bd` — `ReconstructionPublisher` records per-phase wall-clock timings on `ReconstructionMetrics.phase_timings`. Reconstructor container still runs the old image; rebuild + bounce before the next reconstruction if you want timings captured.

### Audit table

| Memo finding | Code location | Status |
|---|---|---|
| Rejection path never writes back `AlignmentCovariance` (locks gate forever) | `RelocalizationFilter.cs:113-122` | **Fixed** (`0fe490c8`) |
| Filter state survives Stop→Start | `VisualPositioningSystem.cs:35` `static FilterState _state` | **Fixed** (`6c7bc7be`) |
| Rejection silent (LogDebug only) | `VisualPositioningSystem.cs:262-273` | **Fixed** (`d738045d`) — banner in metrics dialog + red bottom-bar Metrics label on lockup |
| `Reset()` exists but unreachable from validation UI | `RelocalizationFilter.cs:188` | **Fixed** by Stop→Start path (`6c7bc7be`); no dedicated UI Reset button |
| `LocalizationMap.transform` one-shot at load time; never re-syncs | `LocalizationMap.cs:119-120` | **Not a bug** — `LocalizationMap.prefab` has a `GeoPose` sibling that re-applies on `OnEcefToUnityWorldTransformUpdated` |
| Gravity snap mutates rotation, then translation is composed against uncorrected rotation | `RelocalizationFilter.cs:292, 295-297, 299-300` | Unfixed (fix 5 — 4 DOF refactor) |
| No ARFoundation tracking-state subscription anywhere | Confirmed by grep | Unfixed (fix 7, deferred) |
| `Chi2_99_6dof = 16.81` constant | `RelocalizationFilter.cs:47` | Unchanged |

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

### Ranked fix list

1. ~~**Inflate `AlignmentCovariance` on the rejection path (cap at bootstrap).**~~ **Done** (`0fe490c8`). Rejection branch now caps `sigmaPredicted` diagonals at `BootstrapCovariance` and writes back to `rejectedState.AlignmentCovariance`.
2. ~~**Reset filter on `StartLocalizing`.**~~ **Done** (`6c7bc7be`). `StartLocalizing` calls `Reset(_state, _state.AlignmentCurrent)` (visible alignment preserved). Stop→Start is now a real recovery action.
3. ~~**Surface lockup in UI.**~~ **Done** (`d738045d`). `ConsecutiveRejections` moved into `FilterState`; wall-clock and view-model stay in VPS as `_lastAcceptedTime` / `IsLocalizationLost` / `FilterHealth.Snapshot()`. Metrics dialog shows a red "localization lost" banner and `ReadonlyInspector(filterHealth)` when `Localizing && (ConsecutiveRejections > 5 || SecondsSinceLastAccept > 5)`. Bottom-bar Metrics button label turns red on lockup. **No dedicated Reset button** — Stop→Start equals Reset post-fix-2.
4. ~~**`LocalizationMap` subscribes to `OnEcefToUnityWorldTransformUpdated`.**~~ **Struck — not a bug.** `LocalizationMap.prefab` already has a `GeoPose` sibling. `GeoPose.OnEnable` subscribes (`GeoPose.cs:67`); `GeoPose.LateUpdate` back-fills the stored ECEF when the transform is written externally. The direct `transform.position` write at `LocalizationMap.cs:119-120` is reconciled the same frame. If the "looks good, then drifts" symptom recurs on device, re-investigate; do not assume this was the cause.
5. **4 DOF refactor of `RelocalizationFilter`.** Fixes Bug 2 (gravity-snap pivot / far-room height bias). Large: rewrite filter, delete `Se3.Log/Exp`, port tests. Design is fully spec'd in `.pulsar/capture-validation-bugs.md` — do **not** re-surface its "open design decisions." **Next up.** Now that 1-3 are in and lockups recover in-session, the locked-filter blind spot is gone and Bug 2 should be observable on the next field session.
6. **Reconstructor "last stable frame for origin pose."** Single-digit-line change in `colmap.py` / `rig.py`. Only matters once (5) is in (6 DOF flexibility absorbs map tilt; 4 DOF doesn't). Lands typical map gravity error from "~1°" to "~0.3-0.5°."
7. **ARFoundation tracking-state subscription → re-bootstrap on jump.** Per-platform, more work. Catches the 21:32:22-style jump at source. Refinement after 1-3; revisit if 1-3 prove insufficient.
8. **Decide legacy-map handling for the 4 DOF rollout.** Not code, but a precondition for (5): 4 DOF against an old tilted map renders bent geometry. Re-process vs version-flag — ask the user before (5) lands.

### Strategic ordering

- (1)+(2)+(3) shipped. Field-test next session: does a deliberate phone bump now show the lockup banner, and does Stop→Start recover?
- (4) struck; the assumed bug doesn't exist.
- (5) is next. Block on (8) — user decision on legacy maps — before starting the filter rewrite.
- (6) waits on (5); (7) is a deferred refinement.

## Open questions

- Whether to use ARFoundation's `XROrigin.Camera.trackingState` or a frame-to-frame VIO-delta heuristic for (7). No first-class "pose jumped" event; needs a small spike.
- Legacy-map handling for the 4 DOF rollout (re-process vs version-flag) — user decision required before (5).

### Resolved during 2026-05-20 session

- Cap shape for fix (1) — picked: per-diagonal clamp at bootstrap covariance.
- Reset semantics for fix (2) — picked: `Reset(_state, _state.AlignmentCurrent)` (partial), preserving visible alignment.
- Lockup thresholds for fix (3) — picked: 5 rejections OR 5 seconds since last accept.
- Whether to add a dedicated Reset button in the UI — picked: no, Stop→Start is the reset path post-fix-2.

## Key files

- `packages/unity/Placeframe/Assets/Package/Core/Runtime/RelocalizationFilter.cs` — `ApplyMeasurement` (rejection path now writes covariance back, fix 1); `ConsecutiveRejections` field on `FilterState` (incremented on reject, zeroed on accept, fix 3); `ComputeAlignmentFromResult` gravity-snap (~265-310, **fix 5 target**); `Reset(state, alignment)` (called by `StartLocalizing` post-fix-2).
- `packages/unity/Placeframe/Assets/Package/Core/Runtime/VisualPositioningSystem.cs` — `static FilterState _state`; `StartLocalizing` now calls `Reset(_state, _state.AlignmentCurrent)`; `FilterHealth` snapshot struct + `_lastAcceptedTime`, `LastRejectionReason`, `LastInnovationMahalanobisSquared`, `IsLocalizationLost` (thresholds: 5 rejections / 5 s).
- `apps/AndroidMobile/Assets/Scripts/Capture/AppUI.cs` — `LocalizationMetricsDialog` shows red "localization lost" banner + `ReadonlyInspector(filterHealth)` on lockup; bottom-bar Metrics button label colors red on lockup. R3 `Observable.EveryUpdate(UnityFrameProvider.Update)` ticks the `FilterHealth` snapshot.
- `packages/unity/Placeframe/Assets/Package/Core/Tests/Editor/RelocalizationFilterTests.cs` — lockup regression test is **still TODO** (post-1m-jump, 10 stationary measurements must eventually accept). `ConsecutiveRejections` on `FilterState` now makes the assertion trivial.
- `docker/reconstructor/src/reconstructor/colmap.py:160-178` and `rig.py:70-84` — single-anchor Sim3d alignment to first registered frame; target for fix (6).
- `.pulsar/capture-validation-bugs.md` — full 4 DOF refactor spec for fix (5); do not re-derive.
- `.pulsar/relocalization-filter-rejection-lockup.md` — full mechanism + numerical estimates for fix (1); includes verification test sketch.

## Pending threads

- **Field-test fixes 1-3 on device.** Validation session against a freshly built map: deliberate phone bump should briefly raise `ConsecutiveRejections`, show the red banner if it exceeds threshold, and recover within seconds (covariance writeback unlocks the gate). Stop→Start should recover from any locked state without restarting the app. If "looks good then drifts" recurs, the cause is **not** fix-4-as-memo'd (struck) — re-investigate.
- **Add the lockup regression test** to `RelocalizationFilterTests.cs` per `relocalization-filter-rejection-lockup.md` § "Verification." Now trivial because `FilterState.ConsecutiveRejections` is directly assertable.
- **Ask the user about legacy-map handling (8)** before starting fix (5). 4 DOF against an old tilted map renders bent geometry; need a re-process vs version-flag decision.
- **Start fix (5)** — 4 DOF refactor of `RelocalizationFilter`. Design fully spec'd in `.pulsar/capture-validation-bugs.md`; do not re-open. Blocked on (8).
- Defer (6) until (5) is in. Defer (7) indefinitely unless field-testing 1-3 proves insufficient.
