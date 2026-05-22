---
updated: 2026-05-22
---

# Relocalization lockups persist after fix-1 covariance writeback

## Goal

After fix 1 (`0fe490c8`, rejection path writes `sigmaPredicted` back to `state.AlignmentCovariance`, capped at bootstrap) and fix 2 (`6c7bc7be`, Stop→Start resets the filter), the 2026-05-22 capture-tool session still locked up multiple times. The user toggled `bypass=gate+kalman` to manually break out and the localization snapped to the correct pose immediately, proving the localizer itself was returning a correct answer the gate refused to admit. The fixed filter is not recovering on human timescales. Identify why and propose a real fix.

## State

### Reviewed session: 2026-05-22, 11:58 → 12:35 UTC (capture-tool, Loki `{service_name="capture-tool"} |= "loc.measure"`)

166 measurements, 125 accepts, 41 rejects, organized into four distinct lockup blocks:

| Start (UTC) | End | Rejects | Peak m² | Residual | sigTx growth | Exit |
|---|---|---|---|---|---|---|
| 12:00:22 | 12:00:29 | 8 | 1439 | ~1.7 m on z | 1.11e-3 → 1.83e-3 | session ended (33 min gap) |
| 12:33:26 | 12:33:53 | ~27 | 26566 | ~6.4 m on z | 7.8e-4 → 1.29e-2 | user toggled `bypass=gate+kalman` at 12:33:54 — snap recovered |
| 12:34:34 | 12:34:36 | 3 | 23 | ~0.16 m on z | 4.1e-4 → 6.5e-4 | borderline — passed naturally |
| 12:34:56 | 12:34:58 (end) | ~3+ | 17588 | ~6.1 m on z | 1.5e-3 → 4.0e-3 | session ended still rejecting |

### Diagnosis (what the data says)

**These lockups are not ARFoundation VIO reference-frame jumps** (the Bug 1 hypothesis in `.pulsar/capture-validation-bugs.md` / fix 7 in the priority list). If ARF had jumped 5–6 m, both `currentVioPosition` and `measurement.Translation` would have shifted together; motion-term noise `(0.01·|Δvio|)²` would have grown sigTx by ~2.5e-3 m²/tick. Observed sigTx growth in block 2 (~4.4e-4/tick over 27 ticks) implies `|Δvio| ≈ 1.8 m` — mild user motion, not a teleport. The 6.4 m residual came from the *measurement side* changing (localizer-side disagreement, i.e. PnP returning two different coherent answers across a perceptual transition), while VIO stayed roughly continuous.

**Most plausible reading of block 2:**
- 12:33:15 — `StartLocalizing` → `Reset` → `HasAcceptedMeasurement=false`. The first post-Reset measurement (z = +4.36) unconditionally snapped `AlignmentCurrent` to itself via `RelocalizationFilter.cs:162` `shouldSnap = !state.HasAcceptedMeasurement || ...`.
- 12:33:17 → 12:33:25 — localizer kept returning the same wrong cluster (z = +4.36 ± 0.07). Each accept tightened the Kalman posterior down to sigTx ≈ 4e-4 (σ_t ≈ 2 cm).
- 12:33:26 — localizer returned the right answer (z = -0.48). 6.4 m residual vs. the locked-tight filter, m² = 26566, rejected forever after.

Block 4 looks identical. Block 1 is a smaller version (snap to z=-0.06, real answer at z=-0.69, locked at 1.7 m residual).

### Why fix-1 covariance writeback can't recover this

For a 6.4 m residual to clear the m²≤16.81 gate, need σ²_predicted ≥ 6.4²/16.81 ≈ 2.43 m².
- Base process noise alone (`1e-4`/tick): ~24,300 ticks → **6.7 hours** at 1 Hz.
- With 1.8 m of vio-distance motion term: ~7,500 ticks → **2 hours**.
- To recover within 10 s (≈10 ticks) needs ~0.24 m²/tick, requiring `|Δvio| ≈ 49 m` — physically infeasible indoors.

The fix-1 writeback prevents the *zero-growth* degenerate case (sigmaPredicted spike not written back). But linear, vio-distance-only inflation cannot pop the gate open against multi-meter residuals on human timescales. The 12:34:34 borderline case (m²=23, ν=0.16 m) recovered naturally — anything beyond ~0.4–0.5 m residual is effectively a permanent lockup.

### Fundamental hypothesis

The failure mode is **not** "rejection path doesn't write covariance back" (fixed). It is "the posterior covariance collapses to cm-scale within a few accepts, and the rejection path has no mechanism to *quickly* widen the gate when a consistent stream of disagreeing measurements arrives." Two compounding causes:

1. **Reset-snap commits unconditionally.** After `StartLocalizing → Reset`, the first PnP result becomes the filter mean. If those early accepts are an incorrect-but-coherent localizer cluster (perceptual aliasing, self-similar map regions, partial visibility, unlucky frame), the filter locks onto a place that's meters off; posterior covariance collapses around it; no later measurement can pry it back.
2. **Linear vio-distance-only inflation can't react to "10 consecutive measurements disagreed by 6 m".** A burst of high-m² rejections *is evidence* the mean is wrong, but every rejection is treated as a single-outlier trickle. Recovery is decoupled from the strength of evidence against the current mean. `ConsecutiveRejections` (added by fix 3) is currently UI-only; the filter math never sees it.

## Decisions

No code changes were made in this session — the user explicitly said "do not make any changes, just investigate and hypothesize." The proposed direction (not yet ratified by the user):

1. **Feed `ConsecutiveRejections` back into filter math.** When the count crosses a threshold (e.g. N=5, matching the existing UI threshold), aggressively re-inflate `AlignmentCovariance` toward `BootstrapCovariance()` or call `Reset` outright. This is roughly a one-line change in `ApplyMeasurement`'s rejection branch. Lets the next coherent measurement snap.
2. **Protect the first-snap-after-Reset.** Require 2–3 consecutive measurements within σ of each other before committing the first post-Reset mean. Prevents locking onto an outlier cluster on a single unlucky frame.
3. Note: even if fix 7 (ARFoundation tracking-state subscription) lands, it would not help the lockups observed today because they aren't triggered by detectable VIO jumps. The symptom (committed-to-wrong-mean with tight covariance) is identical for both root causes, so the recovery mechanism must work without relying on detecting the cause.

## Open questions

- Threshold tuning for the burst-rejection re-bootstrap (N consecutive rejections before forcing covariance inflation or full Reset). UI uses 5 — start there?
- Should burst-rejection trigger a soft inflation (swap to bootstrap covariance, keep mean) or a hard `Reset()` (clear mean too)? Soft preserves visible alignment until the next accept; hard guarantees the filter can land anywhere on the next measurement.
- Multi-frame agreement check for first-snap-after-Reset: how many consecutive frames within what σ? Adds latency to first lock; needs a small spike to measure cost.
- Is this strictly post-fix-2 (Reset on `StartLocalizing`) behavior, or did the unconditional first-snap exist before? Audit `RelocalizationFilter.cs:162` history.

## Key files

- `packages/unity/Placeframe/Assets/Package/Core/Runtime/RelocalizationFilter.cs` — `ApplyMeasurement` rejection branch (writes `sigmaPredicted` back, fix 1); line ~162 `shouldSnap = !state.HasAcceptedMeasurement || ...` (unprotected first-snap); `BootstrapCovariance()` and `Reset(state, alignment)` (candidate inflation targets); `FilterState.ConsecutiveRejections` (incremented on reject, zeroed on accept — currently UI-only signal).
- `packages/unity/Placeframe/Assets/Package/Core/Runtime/VisualPositioningSystem.cs` — `StartLocalizing` calls `Reset(_state, _state.AlignmentCurrent)` (fix 2); `FilterHealth` snapshot wires `ConsecutiveRejections` to the UI but not back into the filter.
- `.pulsar/memories/relocalization-fix-priorities.md` — prior ranked fix list; this memo extends item 1 (now insufficient) and reframes item 7 (ARF subscription wouldn't have helped this session).
- `.pulsar/relocalization-filter-rejection-lockup.md` — original lockup mechanism analysis; numerical estimates still hold but were *lower bounds* — the actual lockups in 2026-05-22 are even more degenerate than that memo predicted.
- `.pulsar/capture-validation-bugs.md` — Bug 1 ARF-jump hypothesis (real but not the cause of these lockups).

## Pending threads

- **Decide and implement a burst-rejection recovery path.** Most likely: in `ApplyMeasurement`'s rejection branch, when `state.ConsecutiveRejections >= N`, overwrite `state.AlignmentCovariance` with `BootstrapCovariance()` (soft inflation) or call `Reset` (hard). Pick threshold and soft-vs-hard before coding.
- **Decide and implement first-snap protection.** Require K consecutive within-σ measurements before committing the post-Reset mean. Modify the snap path in `ApplyMeasurement` (around line 162).
- **Add a regression test** for the 2026-05-22 lockup signature: snap to a 4 m-off cluster across 3–5 accepts (covariance collapses), then deliver a correct measurement, assert the filter recovers within K ticks. Belongs alongside the still-TODO 1m-jump test in `RelocalizationFilterTests.cs`.
- **Field-test on next capture session.** Should produce: zero permanent lockups even when localizer outputs disagreeing clusters; UI banner appears briefly during burst rejections then clears as the gate reopens.
