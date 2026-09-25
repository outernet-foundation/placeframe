---
updated: 2026-06-13
---

# Never-recovering false-lock after per-cluster solving + batch ingestion shipped

## Goal

Explain why a device localization session (~18:20:06–18:23:28, demo-site scan) ended **badly false-locked in a way that never recovered**, and decide the next fix. This session ran against the *post-fix* code: per-cluster retrieval solving + client batch ingestion (commit `703e8802`) and the new instrumentation (commit `e3b82ad8`) were both deployed. So this is a fresh diagnosis of failure modes that survived — or were introduced by — those changes, distinct from the pre-fix analysis in `relocalization-filter-findings.md`. The user is confident the failure is filter/tuning logic, not scan quality, and would not be fixed by a better capture.

## State

Diagnosis only — **no fix authored or authorized**. Three findings, root cause is Finding 1:

1. **Client filter is structurally false-locked (root cause of "never recovered").** Two compounding mechanics, both visible in the new `step=reloc.batch` / `step=reloc.prune` / `step=reloc.challenger` logs:
   - **Capacity eviction churn.** With `MaxHypotheses=4` and up to 2 clusters per query, each batch spawns new-pose hypotheses at `SpawnSeedScore=0.10`, and the very next spawn (often *same batch*) evicts them via `PruneWeakestNonLeader` — e.g. `prune reason=capacity id=8 score=0.100` immediately followed by `spawn chosen=9`. New ids cycled 9→57, one per query, never surviving to a second match. **A new correct pose can therefore never accumulate the ≥2 matches it needs to mount a challenge** — it is structurally guaranteed to die at seed score before its second supporting measurement arrives.
   - **Promotion can never fire.** From ~18:22:15 the challenger id=3 carried a *higher* score than leader id=2, but the gap was always <0.6 — never the `PromotionMargin=2.0`. So `challenger=-1` for the entire back half and leader id=2 stayed frozen (last changed 18:20:22). The leader that won the early phase is locked in; nothing can legally displace it.

2. **The clustering change misfires on this map's geometry.** Within every multi-cluster query, clusters whose keyframe *camera-center* centroids are 10–23 m apart all solve the query to **near-identical camPos (±0.2 m)** — e.g. 18:22:15, 4 clusters at centroids spanning ~20 m all → camPos ≈ (-1.2, 9.3). Cause: the scan is a **perimeter-facing-center capture of a circular courtyard** — keyframes ring the space but all observe the *same shared central structure*, so the 2D–3D correspondence set is coherent (one real pose) even though the cameras that contributed it are spatially dispersed. Clustering by camera-center proximity then **splits one good correspondence set into redundant clusters that each re-solve to the same pose**, flooding the filter with duplicate measurements and saturating its 4 slots. This **reframes the sibling memory's "Mechanism A"**: the retrieval is *not* incoherent in correspondence space (each solve is clean); it is spatially dispersed in camera-center space, which is exactly what the new clustering key keys on — so the fix designed to separate aliases instead manufactures duplicates here.

3. **VIO ↔ map disagreement during the divergence (undisambiguable with current logs).** While the published frame swept, `vioDelta` was only ~0.2–0.3 m/frame yet map camPos swept ~9 m and the alignment marched `measTz` −53→−60 — across solves that were all high quality (inliers up to ~3200, confTight ~0.98). Two candidate explanations remain open: (a) ARFoundation tracking degraded, or (b) device was near-stationary and symmetric structure let PnP sweep a family of equally-good poses. **Cannot be told apart without the still-unimplemented VIO/tracking-state and camera-height logging** (items 5 & 6 in `relocalization-filter-findings.md`).

## Decisions / conclusions

- **The user is correct: this is filter logic, scan-irrelevant.** A better capture would not fix capacity churn, the unreachable promotion margin, or the duplicate-cluster flooding.
- **Recommended first fix is Finding 1** — the score/eviction/promotion semantics — because it is the direct cause of the symptom the user saw (frozen leader, no recovery). This aligns with the sibling memory's action item #2 (leader stickiness / leaky integrator + recent-support-rate promotion) but the *mechanism* here is different from the pre-fix one: pre-fix it was a monotonic non-decaying leader accumulator; post-batch-ingestion it is **capacity eviction killing challengers before they can grow + an absolute promotion margin (2.0) that a slot-starved challenger can never reach**. A correct fix must address both: let a fresh well-supported pose survive long enough to accumulate (don't evict at seed score within the same batch that spawned it / raise `MaxHypotheses` or protect recent spawns), and make promotion reachable (recent-support-rate or a relative/leaky-score comparison rather than an absolute 2.0 gap on a churning score).
- **Finding 2 means the clustering key is wrong for center-facing captures.** Camera-center proximity is not the right coherence signal when all keyframes observe a shared structure; clustering should key on something that reflects *solved-pose* agreement (or dedupe clusters that solve to the same camPos) rather than spawning a measurement per spatially-separated camera group. Flagged for design discussion before touching it — it interacts directly with Finding 1's slot pressure.
- **Finding 3 is blocked on instrumentation, not analysis.** Implement the deferred VIO/tracking-state + camera-height logging before trying to resolve it.

## Open questions

- Finding 1 fix shape: raise `MaxHypotheses`, protect recent spawns from same-batch eviction, switch promotion to recent-support-rate, make score a leaky integrator — or some combination? Needs a design pass; the caps and promotion rule interact.
- Finding 2: change the clustering key, dedupe clusters by solved camPos, or cap clusters more aggressively when their solves agree? Should the localizer collapse clusters that produce near-identical poses before returning them?
- Finding 3: is the divergence tracking loss or symmetric-PnP sweep? Unanswerable until VIO/tracking-state + camera-height logging lands.

## Key files

- `relocalization-filter-findings.md` — **read first**; the pre-per-cluster-fix analysis and the 6-item action list (items 5 & 6 = the VIO/tracking-state + camera-position logging this diagnosis is blocked on). This memory is its successor for the post-`703e8802` world.
- `packages/unity/Placeframe/Assets/Package/Core/Runtime/MultiHypothesisFilter.cs` — batch ingestion (`ApplyMeasurements`), `PruneWeakestNonLeader` (capacity eviction), `UpdateLeader` (promotion). Where Finding 1 lives.
- `packages/unity/Placeframe/Assets/Package/Core/Runtime/RelocalizationConfig.cs` — the knobs: `MaxHypotheses=4`, `SpawnSeedScore=0.1`, `PromotionMargin=2.0`, `ScoreDecayPerMeasurement=0.98`, `SupportReward*`.
- `docker/localizer/src/localize.py` — per-cluster solving + the new per-cluster diagnostic logs; `cluster_retrieved_images` keys on camera-center proximity (Finding 2).

## Pending threads

- Decide and implement the Finding 1 fix (filter score/eviction/promotion). Highest value; directly causes the observed never-recovering lock. **Not yet authorized** — diagnose-first per repo rules.
- Implement the deferred VIO/tracking-state + camera-height logging (sibling items 5 & 6) so Finding 3 becomes answerable.
- Revisit the clustering key for center-facing captures (Finding 2) once Finding 1's slot semantics are settled.
