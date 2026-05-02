# Plan

> Design intents:
> - VPS redesign: [`vps-redesign-intent.md`](vps-redesign-intent.md) (Phases 0, 1, 3–6).
> - .NET package refactor: [`package-refactor-intent.md`](package-refactor-intent.md) (Phase 2).

This file tracks execution of the in-flight initiatives above: phase definitions, status, tradeoffs taken, and scaffolding deliberately left for later phases to replace. Deleted when both initiatives complete.

## Phase status

| # | Phase | Status |
|---|---|---|
| 0 | Schema + plumbing | ✅ Done |
| 1 | Frontend rewrite | In progress |
| 2 | .NET package refactor | Not started |
| 3 | ZED-only global calibration | Not started |
| 4 | Dogfooding logger | Not started |
| 5 | Phone-side correction | Not started |
| 6 | Per-map overlay (opportunistic) | Not started |

## Critical path

```
Phase 0 ─► Phase 1 ─► Phase 2 ─► Phase 3 ─► Phase 4 ─► Phase 5 ─► (Phase 6 opportunistic)
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

Math added in this phase (SE(3) Log/Exp, 6×6 covariance algebra, Bayesian filter logic) is written inline in the Unity package and gets extracted to `Placeframe.Math` in Phase 2. No `Placeframe.Math` package exists yet during Phase 1.

Split into two commits, reviewed one at a time:

- **1a — `Anchor` → `GeoPose` rename + SE(3) interp utility** ✅ Done
  - Mechanical rename of `Anchor.cs` → `GeoPose.cs` and its inspector/scene references.
  - Remove the per-frame Lerp from the renamed class.
  - Add SE(3) interpolation utility (decompose, lerp/slerp components, recompose).
- **1b — VPS Bayesian filter rewrite**
  - Bayesian filter on SE(3) alignment with `(μ, Σ)` posterior, Mahalanobis innovation gate, snap-vs-slew decision, slew loop on `Update()`.
  - R3 main-thread marshaling for state mutations.
  - Confidence-scaled `Σ_meas` (`Σ_meas / confidence.tight²`) — heuristic re-tuned in Phase 3.
  - VIO motion only inflates Σ via process noise; the alignment mean is unchanged between measurements (alignment is a static relationship between ECEF and Unity world; device motion doesn't drift it).
  - No new test infrastructure: tests for the new math arrive in Phase 2 alongside the package extraction.

End of Phase 1: visible UX is dramatically smoother and more robust to outliers. Confidence in responses is identity-valued; the filter still benefits from real `Σ_meas` and the innovation gate.

### Phase 2 — .NET package refactor

Extract math and cross-platform business logic from the Unity package into standalone .NET packages. See [`package-refactor-intent.md`](package-refactor-intent.md).

- Create `packages/csharp/Placeframe.Math` (`netstandard2.1`) — depends on `MathNet.Numerics` + `Unity.Mathematics`. Move SE(3) Log/Exp, 6×6 covariance algebra, `BayesianAlignmentFilter`, `Double4x4`, `LocationUtilities`, the math half of `ExtensionMethods`. Replace the inline VPS-Phase-1 implementation with `using Placeframe.Math;` consumption.
- Create `packages/csharp/Placeframe.Math.Tests` (`net8.0`, NUnit) — TDD coverage retroactively backfilled for the math moved in.
- Create `packages/csharp/Placeframe.Core` (`netstandard2.1`) — Auth, the HTTP-side of localization (request assembly, response parsing). Cross-platform; no `UnityEngine` dependency.
- Create `packages/csharp/Placeframe.Core.Tests` (`net8.0`, NUnit).
- Add `uv run build-dotnet-packages` (or equivalent) to `dotnet build` the projects and copy DLLs (`Placeframe.Math.dll`, `Placeframe.Core.dll`, `MathNet.Numerics.dll`) into `packages/unity/Placeframe/Assets/Plugins/`.
- Update `Plerion.VPS.asmdef` to reference the precompiled DLLs as `precompiledReferences`.
- Mass-update Unity-side `using` statements to point at the new namespaces.
- Future (out of scope for this phase but tracked): publish `Placeframe.Math` and `Placeframe.Core` as versioned NuGet packages from the existing CI pipeline. Replace local DLL-drop with NuGetForUnity-consumed packages.

End of Phase 2: math is testable in pure .NET via `dotnet test`. Unity package is a thin shell over cross-platform libraries. No semantic changes — pure refactor.

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
- **Phase 1 math is written inline in Unity, then immediately extracted.** Phase 1 introduces SE(3) and Bayesian-filter math directly in the Unity package; Phase 2 immediately moves it to `Placeframe.Math`. Risk: a small amount of rework to extract. Reward: Phase 1 ships the user-visible UX win without blocking on the package-architecture refactor, and Phase 2 picks up cleanly with the math already in a stable shape.
- **Phase 2 (refactor) blocks all subsequent VPS phases.** It would be possible to ship calibration (Phase 3) on top of inline-Unity math, but the testability gain from extracting first is worth the wait — Phases 3–6 will reference the math to interpret confidence-weighted measurements and the test coverage from Phase 2 catches regressions cheaply.
- **Phase 4 lands after Phase 3, not before.** A previous iteration of this plan put the dogfooding logger before ZED calibration to compress passive-accumulation wall-clock. Pre-go-to-market that compression is illusory: with a small known user pool, phone-side data is gathered in directed sessions, not passively. Building the logger after Phase 3 also means its schema and feature set can be informed by Phase 3's lived experience, reducing rework risk.
- **Phase 6 fitting code is deferred.** The loader is in place from Phase 3, but writing the per-map fitting code is held back until at least one map clears the sample threshold. Risk: when that day comes, the fitting code is novel work that delays per-map calibration for that first map by a few days. Reward: avoids speculative code that may never run.
- **`pipeline_version` is the git SHA, not a selective hash.** Every commit invalidates calibration. We don't yet know which inputs actually shift the metric distribution; once Phase 3 is in production and we have evidence, this can become a selective hash. False-positive refit cost doesn't bite until Phase 3 anyway.

## Scaffolding inventory

Placeholders deliberately left by earlier phases, with the trigger for replacement. Line numbers approximate; resolve by symbol if drifted.

- `docker/localizer/src/build_metrics.py:62` — `apply_global_calibration(calibration, features={})` empty features dict. Phase 3 populates with transformed metrics + map quality features keyed by the calibration's `feature_names`.
- `config/calibration/global.json` — identity calibration: empty logistic weights, intercept-only (yields constant `tight=0.5` / `loose=0.9`), identity isotonic, `pipeline_version: "identity-bootstrap"`. Replaced wholesale by output of `scripts/fit_calibration.py` in Phase 3.
- `docker/localizer/src/calibration.py:56` — `IDENTITY_BOOTSTRAP_SENTINEL` and the equality-check skip in `load_global_calibration`. Both removed once Phase 3's first real calibration ships.
- Phase 1 inline math in `packages/unity/Placeframe/Assets/Package/Core/Runtime/` (SE(3) Log/Exp, 6×6 covariance algebra, `BayesianAlignmentFilter`). Extracted to `packages/csharp/Placeframe.Math/` in Phase 2. No semantic changes during extraction.
