# Plan

> Design intent: [`vps-redesign-intent.md`](vps-redesign-intent.md) (Phases 0, 1, 3–6).

This file tracks execution of the in-flight VPS initiative: phase definitions, status, tradeoffs taken, and scaffolding deliberately left for later phases to replace. Deleted when the initiative completes.

## Phase status

| # | Phase | Status |
|---|---|---|
| 0 | Schema + plumbing | ✅ Done |
| 1 | Frontend rewrite | ✅ Done |
| 2a | In-Unity NUnit tests for Phase 1 math | ✅ Done |
| 3 | ZED-only global calibration | Not started |
| 4 | Dogfooding logger | Not started |
| 5 | Phone-side correction | Not started |
| 6 | Per-map overlay (opportunistic) | Not started |

## Critical path

```
Phase 0 ─► Phase 1 ─► Phase 2a ─► Phase 3 ─► Phase 4 ─► Phase 5 ─► (Phase 6 opportunistic)
```

Strictly serial. With ~2 known users, total wall-clock time is dominated by coding work and a single directed data-gathering session at Phase 5, not by passive accumulation. There's no parallelism to exploit.

## Phases

### Phase 0 — Schema + plumbing

Foundation work. No user-visible impact.

- Extend `LocalizationMetrics` with `Confidence`, `Covariance`, `PipelineVersion` fields.
- Implement the calibration loader, with an identity global calibration committed (`tight: 0.5`, `loose: 0.9`). Hard-fail on missing or pipeline-version-mismatched calibration is wired up from day one; the bootstrap identity artifact uses an `"identity-bootstrap"` sentinel that the loader treats as "skip the equality check" while real calibration doesn't yet exist.
- `pipeline_version` is the localizer image's build-time git SHA, baked in via Dockerfile ARG.
- Plumb the real 6×6 PnP covariance from pycolmap (via `return_covariance=True`) into the populated `Covariance` field.
- Regenerate API and localizer clients so the new fields surface in the Unity frontend and the api ↔ localizer Python path.

### Phase 1 — Frontend rewrite (biggest visible UX win)

Delivers smooth, temporally stable alignment. Calibration is still identity at this point — measurement weighting is heuristic and will be re-tuned in Phase 3.

Math added in this phase (SE(3) Log/Exp, 6×6 covariance algebra, Bayesian filter logic) is written inline in the Unity package and stays there. Tests arrive in Phase 2a via Unity Test Framework — see the Phase 2a notes for why a previously-attempted standalone .NET package extraction was reverted.

Split into two commits, reviewed one at a time:

- **1a — `Anchor` → `GeoPose` rename + SE(3) interp utility** ✅ Done
  - Mechanical rename of `Anchor.cs` → `GeoPose.cs` and its inspector/scene references.
  - Remove the per-frame Lerp from the renamed class.
  - Add SE(3) interpolation utility (decompose, lerp/slerp components, recompose).
- **1b — VPS Bayesian filter rewrite** ✅ Done
  - Bayesian filter on SE(3) alignment with `(μ, Σ)` posterior, Mahalanobis innovation gate, snap-vs-slew decision, slew loop on `Update()`.
  - State mutations marshaled to the Unity main thread via `UniTask.SwitchToMainThread()` (existing pattern in this codebase; the intent's mention of `ObserveOnMainThread` is satisfied by the equivalent UniTask path).
  - Confidence-scaled `Σ_meas` (`Σ_meas / confidence.tight²`) — heuristic re-tuned in Phase 3.
  - VIO motion only inflates Σ via process noise; the alignment mean is unchanged between measurements (alignment is a static relationship between ECEF and Unity world; device motion doesn't drift it).
  - 6×6 algebra delegated to `MathNet.Numerics` (added as a NuGet dependency); SE(3) Log/Exp written inline.
  - No new test infrastructure: tests for the new math arrive in Phase 2 alongside the package extraction.

End of Phase 1: visible UX is dramatically smoother and more robust to outliers. Confidence in responses is identity-valued; the filter still benefits from real `Σ_meas` and the innovation gate. **All math added in this phase ships untested** — the SE(3) Log/Exp, Bayesian update, snap-vs-slew decision, and innovation gate are exercised only by manual on-device verification. Phase 2a backfills automated coverage via Unity Test Framework.

### Phase 2a — In-Unity NUnit tests for Phase 1 math

Phase 1 shipped untested math (SE(3) `Log`/`Exp`, 6×6 algebra, `RelocalizationFilter`). Phase 2a backfills coverage via **Unity Test Framework** (`com.unity.test-framework` 1.6.0, already in `manifest.json`), in-place.

- Editor-only test asmdef at `packages/unity/Placeframe/Assets/Package/Core/Tests/Editor/Placeframe.Core.Tests.asmdef`, referencing `Placeframe.Core`, `Unity.Mathematics`, `PlaceframeApiClient`, plus the NUnit/test-runner assemblies.
- 38 NUnit tests covering `Double4x4`, `LocationUtilities`, `Se3`, `WGS84`, and `RelocalizationFilter`.
- `uv run test-unity` headless runner: `Unity -batchmode -nographics -runTests -projectPath packages/unity/Placeframe -testPlatform EditMode -testResults artifacts/unity-test-results.xml -logFile -`.

End of Phase 2a: Phase 1's previously-untested math has TDD coverage; tests run locally via Unity batch mode.

### Phase 3 — ZED-only global calibration

The calibration pipeline goes live with bulk-only data (Algorithm 1). Phone queries still suffer device shift, but ZED-source queries get well-calibrated confidence.

- Map quality features: compute at map-build time and store in the maps table. Backfill for existing maps.
- `scripts/src/scripts/fit_calibration.py` with Algorithm 1 (ZED held-out) implemented.
- Commit the first non-identity `config/calibration/global.json`. Deploy.
- Remove the `IDENTITY_BOOTSTRAP_SENTINEL` skip in the calibration loader; real artifacts carry real pipeline versions and the equality check enforces match.
- Re-tune Phase 1's heuristic Σ_meas weighting now that confidence is meaningful (snap threshold, process noise, confidence-to-Σ_meas scaling).
- Implement the per-map calibration loader path (lazy MinIO fetch + cache), but defer the per-map fitting code to Phase 6.

End of Phase 3: confidence is well-calibrated for ZED-source queries; phone queries still suffer device shift but are meaningfully better than identity.

### Phase 4 — Dogfooding logger

Zero UX impact. Adds the plumbing required to gather phone-side calibration data. Built right before it's needed (Phase 5) so the schema and feature set are informed by Phase 3's experience.

- Toggle in AndroidMobile settings UI ("Contribute calibration data"), persisted to PlayerPrefs.
- Per-query log buffer matching the schema in the intent doc.
- `POST /calibration-data` endpoint on the API; writes JSON directly to MinIO.
- Backoff/retry with local persistence cap.

End of Phase 4: directed data-gathering sessions can be run with the known user pool to produce phone-side samples on demand.

### Phase 5 — Phone-side correction

Run a directed data-gathering session (a day or two of focused use across the 2–3 known users, possibly augmented by 1–2 invited testers) to produce phone-side calibration samples. Then fit the second calibration stage.

- Algorithm 2 (pairwise VIO calibration with median-over-pairs attribution) added to `fit_calibration.py`.
- Stage-2 isotonic correction fit and inserted into the global artifact.
- Re-fit, commit updated `global.json`, redeploy.

End of Phase 5: phone-side confidence is well-calibrated. The system now hits its design goals for both ZED- and phone-source queries.

### Phase 6 — Per-map overlay (opportunistic)

Per-map fitting code is deferred from Phase 3 (loader is in place, fitting isn't) until at least one map crosses the 200-sample threshold and clearly matters. Avoids writing fitting code that may never be exercised.

- Algorithm 3 added to `fit_calibration.py`.
- Per-map artifact upload + admin refresh endpoint.
- Rolls in map-by-map as data accumulates.

## Tradeoffs taken

- **Phase 1 ships before calibration exists.** Phase 1's measurement weighting uses heuristic Σ_meas scaling. When Phase 3's real calibration lands, those tunables (snap threshold, process noise, confidence-to-Σ_meas scaling) will need re-tuning. Tuning rework, not architectural rework.
- **Phase 1 math lives inline in Unity and is tested via Unity Test Framework.** SE(3) and Bayesian-filter math sit alongside the Unity runtime in `packages/unity/Placeframe/Assets/Package/Core/Runtime/`; tests are an Editor-only asmdef next to it.
- **Phase 2a blocked all subsequent VPS phases.** It would have been possible to ship calibration (Phase 3) on top of fully-untested math, but Phases 3–6 reference the math to interpret confidence-weighted measurements, and the test coverage cheaply catches regressions there.
- **Phase 4 lands after Phase 3, not before.** A previous iteration of this plan put the dogfooding logger before ZED calibration to compress passive-accumulation wall-clock. Pre-go-to-market that compression is illusory: with a small known user pool, phone-side data is gathered in directed sessions, not passively. Building the logger after Phase 3 also means its schema and feature set can be informed by Phase 3's lived experience, reducing rework risk.
- **Phase 6 fitting code is deferred.** The loader is in place from Phase 3, but writing the per-map fitting code is held back until at least one map clears the sample threshold. Risk: when that day comes, the fitting code is novel work that delays per-map calibration for that first map by a few days. Reward: avoids speculative code that may never run.
- **`pipeline_version` is the git SHA, not a selective hash.** Every commit invalidates calibration. We don't yet know which inputs actually shift the metric distribution; once Phase 3 is in production and we have evidence, this can become a selective hash. False-positive refit cost doesn't bite until Phase 3 anyway.

## Scaffolding inventory

Placeholders deliberately left by earlier phases, with the trigger for replacement. Line numbers approximate; resolve by symbol if drifted.

- `docker/localizer/src/build_metrics.py:62` — `apply_global_calibration(calibration, features={})` empty features dict. Phase 3 populates with transformed metrics + map quality features keyed by the calibration's `feature_names`.
- `config/calibration/global.json` — identity calibration: empty logistic weights, intercept-only (yields constant `tight=0.5` / `loose=0.9`), identity isotonic, `pipeline_version: "identity-bootstrap"`. Replaced wholesale by output of `scripts/fit_calibration.py` in Phase 3.
- `docker/localizer/src/calibration.py:56` — `IDENTITY_BOOTSTRAP_SENTINEL` and the equality-check skip in `load_global_calibration`. Both removed once Phase 3's first real calibration ships.
- Phase 1 inline math in `packages/unity/Placeframe/Assets/Package/Core/Runtime/` (SE(3) Log/Exp, 6×6 covariance algebra, `RelocalizationFilter`) stays here permanently. Tested in-place via Unity Test Framework in Phase 2a.
