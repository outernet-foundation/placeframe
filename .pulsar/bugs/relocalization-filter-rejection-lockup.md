# RelocalizationFilter locks permanently after VIO discontinuity > ~0.4 m

**Severity**: high — silent, user-visible loss of localization with no in-app recovery path.

**Location**: `packages/unity/Placeframe/Assets/Package/Core/Runtime/RelocalizationFilter.cs` — `ApplyMeasurement` (lines 99–168), specifically the rejection path at lines 113–122.

## Symptom

After any VIO discontinuity larger than roughly 0.4 m (phone bump, ARFoundation tracking re-localization, brief tracking loss followed by re-acquire, Stop→Start of localization combined with VIO drift, etc.), the chi² innovation gate starts rejecting every subsequent measurement. The point cloud freezes in place while the device pose continues to drift in Unity world. User-visible: "localization just stopped updating; world looks wrong and stays wrong."

The only recovery paths from inside a normal validation session:

- App process restart (re-runs the `static FilterState _state = RelocalizationFilter.InitialState()` field initializer in `VisualPositioningSystem.cs:35`).
- Walking ~20+ m further from the last accepted VIO position (for a ~1 m jump — scales worse for bigger jumps).
- A call to `VisualPositioningSystem.SetEcefToUnityTransform(...)`, which is only invoked from authoring/registration tools (`legacy/Outernet.Client/Assets/AuthoringTools/LocationContentManager.cs:187`, `apps/MapRegistrationTool/Assets/LocationContentManager.cs:199`) — not reachable from the validation UI.

Stop → Start does **not** recover (see `.pulsar/memories/capture-validation-bugs.md` for the Stop→Start carry-over diagnosis, which is the same root mechanism).

## Mechanism

`ApplyMeasurement` computes the predicted covariance each tick as:

```csharp
var sigmaPredicted =
    state.AlignmentCovariance + ProcessNoise(currentVioPosition, state.LastAcceptedVioPosition);
```

`sigmaPredicted` is **never written back to `state.AlignmentCovariance`**. Process noise reaches the stored covariance only via the accepted-measurement path at line 340:

```csharp
var newCov = (Matrix<double>.Build.DenseIdentity(6) - kalmanGain) * sigmaPredicted;
```

On the rejection path (lines 113–122), the function returns early with `NewState = state` — `AlignmentCovariance` is untouched. So tick after tick, `sigmaPredicted` recomputes to the same value, and the gate test produces the same `MahalanobisSquared`. Once closed, the gate stays closed at exactly the same threshold forever (under stationary observation).

The motion-proportional process-noise term (`(0.01 · |Δvio|)²`, line 240) does fire on every recomputation, but it's based on `currentVio − lastAcceptedVio`. After a 1 m jump and a stationary user, that delta is ~1 m every tick, contributing 0.0001 m² per axis to `sigmaPredicted` — negligible.

### Numerical estimate

At steady-state with `BaseProcessNoiseTranslationVariancePerTick = 1e-4` (`RelocalizationFilter.cs:64`) and a typical PnP measurement variance `σ²_meas_t ≈ 0.01` per axis, the equilibrium posterior variance is `σ²_p ≈ 0.001` per axis → `σ_p ≈ 3 cm`. Innovation variance on the jumped axis: `σ²_p + σ²_meas ≈ 0.011`. Mahalanobis² for a translation-only residual of magnitude `Δ`: `Δ² / 0.011`. Gate threshold: `Chi2_99_6dof = 16.81`.

| VIO jump Δ | d² | Gate verdict |
|---|---|---|
| 0.2 m | 3.6 | accepted |
| 0.4 m | 14.5 | borderline |
| 0.5 m | 22.7 | **rejected** |
| 1.0 m | 91 | **rejected** |
| 5.0 m | 2273 | **rejected** |

For motion-proportional inflation to unlock a 1 m residual, the user must walk far enough that `(0.01 · Δvio)² > ~0.05 m²` per axis, i.e. `Δvio > 22 m`. For a 5 m jump: `Δvio > 122 m`. For a 10 m jump: `Δvio > 245 m`. Generally infeasible indoors.

## Fix sketch

Three escalating options, cheapest first.

1. **Inflate `AlignmentCovariance` on the rejection path.** Write `newState.AlignmentCovariance = sigmaPredicted` on rejection so the noise actually accumulates. ~5 lines. Restores the intended "uncertainty grows with time" behavior. Cap `AlignmentCovariance` at some maximum (e.g. the bootstrap covariance) so it can't grow unbounded across a long sequence of rejections — otherwise the eventual unlock will admit an outlier as eagerly as a good measurement.

2. **Consecutive-rejection counter that auto-bootstraps.** Add `ConsecutiveRejections` (or `LastAcceptedTime`) to `FilterState`. If the count exceeds a threshold (e.g. 5 rejections, or 5 s without an accept), call `Reset(state, state.AlignmentCurrent)` to wipe history and re-bootstrap covariance. The next measurement will snap because `HasAcceptedMeasurement = false`. ~15 lines. Belt-and-suspenders complement to (1).

3. **Detect VIO discontinuities at source.** Subscribe to ARFoundation tracking-state transitions (`XROrigin.Camera.trackingState`) or watch for large frame-to-frame VIO deltas; on a detected jump, immediately re-bootstrap covariance before the next measurement arrives. More principled but per-platform and more work. This is the "Bug 1 (2b)" thread in `.pulsar/memories/capture-validation-bugs.md`.

Recommendation: (1) is the right baseline fix — closes the silent-lockup mechanism with minimal surface area and no per-platform code. (2) layered on top makes recovery deterministic even for pathological covariance shapes. (3) is the principled long-term fix but can land later.

## Verification

Unit test in `RelocalizationFilterTests.cs`:

1. Run the filter to steady state by feeding ~30 stationary measurements with reasonable `σ_meas`.
2. Simulate a 1 m VIO jump (next frame has `CameraTranslationUnityWorldFromCamera` shifted by 1 m).
3. Feed the next measurement: assert `Rejection == InnovationGate`.
4. Without changing VIO, feed 10 more measurements consistent with the post-jump VIO: assert that the filter eventually accepts (with fix 1) or that `Reset` triggers after the configured rejection count (with fix 2).
5. Today, without either fix, this loop would reject all 10 measurements and never recover — that's the regression to lock in.

Field test: bump the phone hard mid-validation; confirm the point cloud re-locks within a few seconds rather than drifting indefinitely until app restart.

## Related

- `.pulsar/memories/capture-validation-bugs.md` — original Bug 1 (Stop → Start jump) covers a special case of this same mechanism (filter state carried across Stop→Start, then VIO drift gets baked in). This bug is the more general statement of the same root cause.
- `.pulsar/plans/capture-validation-bugs.md` — currently defers Bug 1 entirely to a separate plan. This finding strengthens the case for prioritizing fix (1) sooner; it's a one-liner with broad benefit, independent of the 4 DOF refactor.
