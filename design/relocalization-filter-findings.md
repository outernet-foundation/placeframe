---
updated: 2026-06-13
---

# Multi-hypothesis relocalization filter — field-test findings and tuning plan

## Goal

Validate the `feature/better-filter` multi-hypothesis relocalization rewrite (Phase 1 of the plan in `relocalization-multi-hypothesis-plan.md`) against real device test runs, find why localization still misbehaves, and decide what to tune or instrument next. The rewrite's thesis: the old single SE(3) EKF collapsed ambiguity into one confident answer and could be forced to snap ~25m to a texture-rich wrong region; the fix is to hold competing hypotheses and let device motion arbitrate.

## State

Two device test runs analyzed via Loki + localizer docker logs. Stack is up; `demo-site.tar` map imported (reconstruction `46890b09-ee89-4c47-8656-238d6b868dbc`, 228 images / 40,506 points). DriftCorrectionController audit logging added and committed (`5951daf7`). No tuning/architectural code changes made yet — the action items below are proposals only.

**Run 1 (16:30, ~3.5 min):** Published frame stable, one bootstrap promotion (hyp0→hyp1) then zero promotions, no teleport. But it never exercised aliasing — all measurements within ~6m, no 25m-separated look-alike, so the headline anti-aliasing guarantee was not tested. Observed bank over-fragmenting one location: 4 hypotheses for a single ~6m area, hyp1/hyp2 only ~0.6m apart (right at the 0.5m association gate, and PnP residuals run 0.3–0.6m) — jitter alone splits the correct region into competing hypotheses.

**Run 2 (16:48:11→16:49:31, ~80s, fresh filter, IDs reset to 0):** The informative one. Phases: (1) bootstrap id=0 + 27 matches while walking, score→26.5; (2) brief spawns id=1,2 abandoned; (3) 23s standstill, id=0 score crawls 25.5→26.7; (4) divergence sweep — 5 spawns (id 3–7) in 7s as alignment swept ~6m (measTz 27.6→23.5) while moving; (5) id=7 cluster collects matches, score→9.8. **Leader never left id=0, zero promotions.** Published frame re-anchored 10 times (all small, eased, <1m, no teleport), walking Tz 31.6→28.2 over ~57s (the ~3.5m drift the user saw), then froze on id=0 at 16:49:08 while later measurements matched id=7 at Tz~23 — published frame ended ~5m diverged from the device's confident localizations and stayed there.

## Decisions / conclusions

- **Root cause is two independent problems.**
  1. **Server — incoherent retrieval (Mechanism A).** Localizer retrieval is spatially incoherent: spans of 12–24m on nearly every query, `image_ids` flip-flopping between disjoint map regions on consecutive ~1s frames *while the device stood still* (e.g. 16:48:56 span 24.04 mixing regions, 16:48:59 span 5.55 coherent, 16:49:00 span 20.91 mixing again). This is the source of the bad measurements. Each PnP solve is internally clean (confTight 0.95–0.99, 3k–5k inliers even on the divergent id=7 cluster), so confidence never flags it — confidence is an inlier-density proxy under the placeholder calibration, not a correctness signal.
  2. **Client — leader is structurally sticky (architectural bug, not a knob).** Decay is applied only to non-matched hypotheses (`MultiHypothesisFilter.cs:147–151`); the matched leader never decays, so its score is a monotonic lifetime accumulator. id=0 banked 26 during the motion-rich phase 1; the later, arguably-better id=7 cluster (higher inliers) tops out at 9.8 and can never overtake, since promotion compares absolute accumulated score (`:175`). The +2.0 PromotionMargin is irrelevant — the gap is 16 points the wrong way. The frame is permanently captured by whichever hypothesis won the early high-motion phase.

- **Corroboration of user's run-2 observations:** "drifted away then settled into OK state" = exactly the smooth Tz creep (10 eased corrections, no snap) then the freeze on id=0. ARFoundation tracking loss can neither be confirmed nor denied — `walked=` values look sane and the standstill chaos is clearly retrieval flip-flop not VIO, but there is no VIO/tracking-state logging at all. The "~10cm under ground" cannot be seen in these logs and won't be: that's a camera-height/extrinsics quantity, not the ECEF→Unity translation-Y the filter logs (which has ±0.4m noise); the Magic Leap depth test is the right instrument.

- **The architecturally correct client fix is to change score semantics, not nudge constants.** Score currently means "lifetime evidence"; the promotion decision needs "current belief strength." Make it a leaky integrator: decay all hypotheses every measurement including the matched leader (delete the `!= matched` guard, or add a time/distance leak to the leader), so the leader plateaus and a fresh strongly-supported cluster can catch it. With 0.98 decay the plateau is still ~50 at walking pace, so also shorten memory (e.g. 0.90, ~10-measurement window). Equivalently/additionally drive promotion off a recent-support-rate metric. Treat absolute-accumulator behavior as a bug to fix.

- **The architecturally correct server fix is retrieval coherence, not a filter band-aid.** Spatially cluster retrieved candidates and solve per-cluster (feed the filter one measurement per coherent region — exactly what the multi-hypothesis bank wants), and/or reject retrievals whose span exceeds a threshold (a 23m span for one query is by definition mixed-region). Higher-leverage than the client fix — fix retrieval and the filter has far less to defend against.

- Hold off touching the quality gate (`MinInliers=50` / `MinInlierRatio=0.25`) until the two above land — it's permissive but the frames it lets through matched the leader and did little harm.

## Action items (priority = expected impact, highest first)

1. **Fix retrieval coherence (server).** Cluster retrieved candidates by region, solve per-cluster, reject/flag 20m+ spans. Kills the source of bad measurements.
2. **Fix leader stickiness (client, architectural).** Leaky integrator (decay all incl. matched, shorter memory) or recent-support-rate promotion.
3. **Log leader + referee state (client diagnostics).** Add `leaderId`/`leaderScore` to every `step=reloc.measure` line (today `chosen=` is the association target, not the published leader — leader had to be inferred). Add a `step=reloc.referee` line in `UpdateLeader` on every accepted measurement (`leaderId leaderScore topId topScore gap dwellElapsed`) — prerequisite for trusting #2.
4. **Ship localizer `retrieval span` to Loki, keyed by request id (server diagnostics).** Today docker-only; correlating with client behavior is manual timestamp alignment. Join key + Loki shipping makes Mechanism-A detection one query. Consider adding `retrievalSpan`/region count to the response so the client can log it inline. Prerequisite for trusting #1.
5. **Log VIO/ARFoundation tracking-state + per-frame VIO jump magnitude (client diagnostics).** Log state transitions (Tracking↔Limited↔None) and inter-frame VIO delta in `AccumulateMotion`, flagging deltas above a threshold. Answers the currently-unanswerable "did tracking drop?".
6. **Log camera world/geodetic position per measurement.** `measTx/y/z` is an abstract transform component; the landed camera position makes "drifted away" measurable in ground-meters.

If implementing: do the score-semantics fix and logging as separate commits, and update the filter `SPEC.md` first (it documents the changing behavior) per the spec-first rule. Items 1,3,5,6 client-side `.cs`; #4 spans localizer + API response.

## Investigation methodology (reusable)

- **Two separate log sinks, correlated by timestamp:**
  - Client filter behavior → Loki, `service_name="capture-tool"`. Lines: `step=reloc.measure action={reject|spawn|match}` (carries `chosen`, `score`, `residM`, `gateThresh`, `vioDelta`, `measTx/y/z`; reject lines carry `reason=qualityGate`), `step=reloc.promote from=A to=B gap=…`, and now `step=reloc.frame` (`set`/`hold`/`correct`/`slewDone` with `walked`/`turned`) from the new DriftCorrectionController logging.
  - Server retrieval geometry → `docker logs placeframe-localizer-cuda-1` ONLY (localizer does NOT ship to Loki; present labels are `api`, `capture-tool`, `reconstructor`). Lines: `retrieval span(m): X.XX image_ids=[…]`, `localize timings(ms): …`.
- Query Loki with `uv run loki-query '<LogQL>' -n <limit> -d <forward|backward> -s <since>`.
- `chosen=N` is the association target, not the published leader — pull the structural events (bootstrap, spawn, promote) separately to know which hypothesis was actually rendered.
- Mechanism A (multi-modal/large-span retrieval, server-fixable) vs Mechanism B (clean small-span retrieval of a wrong look-alike, only client motion catches it): discriminate by reading `retrieval span(m)` on the bad-frame timestamps.
- Two preconditions for a meaningful test: the phone must run an APK built from this branch (else only server `retrieval span` lines appear, no bank behavior); and confTight is only a monotonic `num_inliers` proxy under the deployed placeholder `global.json` (`sigmoid(1.2·log1p(inliers) − 5.5)`), diagnostic only, never a correctness signal.

## Key files

- `relocalization-multi-hypothesis-plan.md` — the architecture vision this is Phase 1 of.
- `relocalization-filter-rewrite.md` — earlier rewrite memory with field-data findings.
- `packages/unity/Placeframe/Assets/Package/Core/Runtime/MultiHypothesisFilter.cs` — the bank; stickiness bug at `:147–151` (decay guard) and `:175` (absolute-score promotion compare).
- `packages/unity/Placeframe/Assets/Package/Core/Runtime/DriftCorrectionController.cs` — presentation layer; now emits `step=reloc.frame` audit logs (commit `5951daf7`).
- `docker/localizer/src/localize.py` — confidence gate removed; emits `retrieval span(m)` (docker-only).
- `packages/unity/Placeframe/SPEC.md` — filter behavior spec; update first if changing documented score/promotion semantics.
