---
updated: 2026-05-24
---

# Relocalization redesign — implementation plan

Ordered steps to move the repo from its current state to the end state in
`.pulsar/memories/relocalization-redesign.md` (the locked design). Each phase
lists concrete actions and an exit check. Rationale lives in the design doc;
this file is the sequence of work.

## Ground rules

- Run the phases in dependency order; do not parallelize the C#/Unity and
  Python tracks.
- Treat the existing calibration Python — `calibration.py`,
  `fit_calibration.py`, `tune_reconstruction.py`, the `localization_evaluations`
  cache flow, and `config/calibration/global.json` — as reference only. Rebuild
  to the end state; do not incrementally extend it.
- Do not gather a real corpus before Phase 6. The code that gathers it is
  rewritten in Phase 5.
- Ship the multi-hypothesis filter to demos only in Phase 7. Phase 1 is the
  interim demo path.
- Commit prose (`*.md`) separately from code, including the SPEC updates below.

## Phase order

| # | Phase | Depends on |
|---|---|---|
| 1 | Capture Tool demo bypass workaround ✅ done | — |
| 2 | `scripts/` reorganization ✅ done | — |
| 3 | Native filter core + multi-hypothesis filter + Unity integration | 2 |
| 4 | Filter-replay harness + orchestrator + aliasing fixtures | 2, 3 |
| 5 | Calibration & tuning rebuild | 3, 4 (recon objective only) |
| 6 | Bootstrap tuning loop → shippable calibration | 4, 5 |
| 7 | Ship the real filter to the Capture Tool | 3, 6 |
| — | Deferred: phone dogfooding + Phase B field loop | 7 |

Phase 2 gates only Phase 4 (the harness lives under `scripts/csharp/`), not
Phase 3 (`packages/cpp/` + `packages/csharp/`); it may land anywhere before
Phase 4.

---

## Phase 1 — Capture Tool demo bypass workaround ✅ done

**Status:** done on `feature/relocalization-redesign`. The two bypass toggles are
consolidated into one "Disable filtration (raw localization)" toggle that sets
both flags, with the underlying toggles retained under a "Diagnostics" header; a
"Lock in"/"Localize" label now surfaces the localize start/stop control in the
Validation UI. Compiles via
`uv run compile-unity --project CaptureTool --build android-mobile`. The on-device
confirmation below (raw-track → stop → frozen) remains an operator step — no phone
was attached when the work landed.

Both capabilities already exist: filtration-off = `BypassInnovationGate` +
`BypassKalman` together (separate toggle rows at
`apps/AndroidMobile/Assets/Scripts/Capture/AppUI.cs:345-353`); lock-in =
`StopLocalizing()` (exposed via the localize start/stop control).

- In `AppUI.cs`, consolidate the two bypass toggles into one "Disable
  filtration (raw localization)" affordance that sets both flags together. Keep
  the two underlying toggles available for diagnostics.
- Make the localize start/stop ("lock in") control obvious in the demo flow.
- Confirm on device: raw-track while moving → stop localizing → alignment stays
  frozen.

This affordance is reconciled into the new toggle set in Phase 3 F3.

**Exit:** a demo operator can raw-track then lock in on the Capture Tool with no
rebuild.

---

## Phase 2 — `scripts/` reorganization ✅ done

**Status:** done on `feature/relocalization-redesign`. `scripts/{pyproject.toml,src,tests}`
moved under `scripts/python/` (pure git renames); `scripts/SPEC.md` and
`scripts/README.md` stayed at the root. Root `pyproject.toml` workspace member
(`scripts` → `scripts/python`) and pytest `testpaths` repointed; the `scripts/**/src/**`
basedpyright globs and the path-less `scripts = { workspace = true }` source needed no
change. `uv.lock` regenerated (`scripts` now `editable = "scripts/python"`).
`uv run preflight` green and all `uv run` entry points resolve. Prose updated in
`scripts/SPEC.md`, `packages/python/core/SPEC.md`, and `docker/localizer/SPEC.md`.
Committed to this branch rather than a standalone PR since the whole redesign rides one
branch. Stale `scripts/src/...` references in `.pulsar/bugs/` and `.pulsar/memories/`
were left as-is (work-tracking artifacts, some describing the pre-move baseline).

- Move `scripts/pyproject.toml`, `scripts/src/scripts/*.py`, and
  `scripts/tests/` under `scripts/python/`.
- Leave `scripts/SPEC.md` and `scripts/README.md` at the `scripts/` root.
- In root `pyproject.toml`: change the uv workspace `members` entry and the
  `scripts = { workspace = true }` source from `scripts` to `scripts/python`,
  and the pytest `testpaths` entry `scripts/tests` → `scripts/python/tests`.
  Confirm the ruff/basedpyright `scripts/**/...` include globs still match the
  new layout.
- Run `uv run lock-python` to regenerate `uv.lock`.
- Update `scripts/`-path references in `scripts/SPEC.md` and any `CLAUDE.md`.
  Confirm no `scripts/` path references exist in `.github/workflows/` at edit
  time.

**Exit:** `uv run preflight` green from the new layout; all `uv run <name>`
entry points resolve. Lands as its own PR.

---

## Phase 3 — Native filter core + multi-hypothesis filter + Unity integration

One PR of three commits in order. F1 must land green before any
multi-hypothesis math is written.

### F1 — native scaffold + prove the plugin loads on every target

Stand up the toolchain and interop with no real math, to de-risk them in
isolation.

- Create `packages/cpp/Placeframe.Native/`: `CMakeLists.txt`, the `extern "C"`
  ABI header (`placeframe_filter_create` / `_destroy` / `_observe` /
  `_publish` / diagnostics; `Pose7` and `Cov6x6` POD structs), a trivial
  identity-round-trip implementation, and a native test target. Vendor Eigen
  and Sophus via CMake `FetchContent` pinned to exact commit hashes.
- Create the managed UPM wrapper `packages/csharp/Placeframe.Native/` (asmdef
  `Placeframe.Native`, id `org.outernet.placeframe.native`): the
  `[DllImport("placeframe_native")]` P/Invoke surface over the ABI, the
  `AxisConvention` enum, the `ChangeBasis` static class, `package.json`, and a
  `Plugins/` tree with committed `.meta` files (PluginImporter `platformData`
  per the legacy Immersal precedent). Port `AxisConvention` / `ChangeBasis`
  from the Python `change_basis_*` helpers with identical matrix definitions.
- Add the `uv run build-native` driver (a Python orchestrator around CMake)
  that builds the target's ABI(s) — `arm64-v8a`, Android `x86_64`, and host —
  and stages the binaries into `Plugins/Android/{arm64-v8a,x86_64}/` and the
  host plugin folder, with the `.so`/`.dll`/`.dylib` gitignored. Wire it into
  `prepare_unity_project()` ahead of the Unity batchmode invocation.
- Reference the managed `Placeframe.Native` wrapper from the `Placeframe.Core`
  asmdef and both app manifests.
- Prove it **builds, loads, and round-trips a call** on arm64-v8a (CaptureTool),
  Android-x86_64 (Magic Leap), and host — and that the .NET harness links the
  same host binary. No filter math yet.

### F2 — implement the multi-hypothesis filter in C++

- Implement the dynamic hypothesis pool in C++: per-hypothesis SE(3) Gaussian
  (`Sophus::SE3d` mean + 6×6 covariance) + `LastAcceptedVioPosition` +
  exponentially-decayed log-evidence; incumbent + challengers; lifecycle rules
  (spawn on gate-fail-against-all, fold-in on accept, KL-merge, evidence-ratio
  prune); Bayes-factor publish-swap (`log K ≥ 4.6`) gated by the precision
  floor (σ_t < 30 cm, σ_r < 1°); per-hypothesis process noise; publish
  deadband; the 0.5 s `SmoothStep` slew; `BypassChallengers` (caps the pool at
  1). The whole lifecycle lives in C++ so device and harness run identical
  decisions. Covariance algebra is Eigen (`LLT` / `.inverse()` / `.solve()`);
  the Lie algebra is Sophus; the ABI's rotation-first 6×6 block order is
  permuted to Sophus's translation-first tangent internally.
- Land native behaviour tests: perfect-measurement convergence, aliasing-
  recovery via challenger swap, innovation-gate outlier rejection, KL-driven
  merger, evidence-based pruning, watchdog reset, `BypassChallengers`
  collapsing to single-Gaussian. Land native ABI tests: covariance block order,
  scalar-last quaternion storage, canonical-only I/O, and a
  create/observe/publish/destroy round-trip.
- Define and lock the corpus / dogfooding-logger row schema: a Pydantic model +
  matching C# record carrying the measurement payload and the per-query
  filter-state diagnostics (active hypothesis count, per-hypothesis evidence,
  accepting hypothesis, swap/watchdog/discontinuity firings). Leave room for a
  later `query_image_id` field without breaking parsers.

### F3 — rewire Unity glue

- Rewrite `VisualPositioningSystem.cs` to drive the filter through the P/Invoke
  wrapper; it owns subscription wiring, the slew tick, the HTTP `Localize()`
  call, unpacking `LocalizationResult` / `CameraFrame` into canonical poses, and
  the `ChangeBasis` conversion at the boundary.
- Add `OnTrackingDiscontinuity` (`Observable<Unit>`) to `ICameraProvider`.
  Implement in `CameraProvider.cs` (ARFoundation: `ARSession.stateChanged` +
  `ARTrackingState` transitions + pose-delta heuristic) and
  `MagicLeapCameraProvider.cs` (OpenXR Localization Map callbacks +
  `XRInputSubsystem.trackingOriginUpdated` + the same pose-delta backstop).
  Subscribe in VPS and `Reset` the pool. Add the watchdog timer.
- Drop `LockupRejectionThreshold` / `LockupSecondsThreshold` and the
  "localization lost" banner. Add the "challenger is winning" indicator and the
  new diagnostic surfaces (hypothesis count, incumbent/best-challenger
  log-evidence, log Bayes factor, seconds since publish) in `AppUI.cs`.
  Reconcile the Phase 1 affordance into the
  `BypassChallengers`/`BypassInnovationGate`/`BypassKalman` toggle set.
- Update `packages/unity/Placeframe/SPEC.md` (separate prose commit) for the
  multi-hypothesis architecture and the native-core boundary.

**Exit:** native tests green for `Placeframe.Native`; `uv run build-native`
produces and stages the plugin for all three targets;
`uv run compile-unity --project CaptureTool --build android-mobile` green with
the plugin loading on-device; the .NET harness links the host build. The filter
runs on-device against the current placeholder calibration. Not shipped to
demos (Phase 7).

---

## Phase 4 — Filter-replay harness + orchestrator + aliasing fixtures

- Build `scripts/csharp/replay-filter/` — a .NET console binary that P/Invokes
  the host build of the native `Placeframe.Native` (produced by `uv run
  build-native`). It reads a corpus JSON file + a threshold-config JSON
  (every filter knob + the Σ_meas form), replays the
  `(state, measurement, VIO_pose) → state'` loop with a per-step
  `score(published, truth)`, and emits a per-session JSON report (truth-error
  mean/median/p95/max, time-to-first-correct-lock, aliasing recovery time,
  false-swap rate, spurious-spawn rate, steady-state σ, user-visible jitter).
  Stateless, deterministic, pure file I/O.
- Build `scripts/python/src/scripts/replay_filter.py`, registered as
  `uv run replay-filter`. It queries `localization_evaluations` from Postgres,
  writes one corpus JSON per replay scope, enumerates sweep cells, shells out to
  the harness via `common.bash` (one invocation per cell), aggregates per-cell
  JSON locally, and uploads the sweep summary + the producing configs to
  `s3://placeframe-sweeps/<sweep-id>/`. Per-cell blobs upload only under
  `--archive-cells`.
- Bind the F2 corpus-row schema in both (Pydantic ↔ C# record, JSON on the
  wire).
- Add aliasing-injection fixtures: synthetic perturbation of real measurements
  (fixed pose offset before the filter) to drive the recovery-time metric.
- Ship the harness with no preflight regression test for the
  orchestrator↔harness boundary. Before the first future change to the harness,
  orchestrator, or filter, first write a deterministic multi-cell mini-sweep
  against a synthetic perfect-measurement fixture corpus.
- Decide whether the native-core tests (and the `ChangeBasis` C# xUnit tests)
  join `uv run preflight` or run as a separate CI job. Either way CI must run
  `uv run build-native` (NDK + CMake) before any Unity build or harness link.

**Exit:** `uv run replay-filter` runs a trivial sweep end-to-end against a
hand-crafted fixture corpus and produces an aggregated summary.

---

## Phase 5 — Calibration & tuning rebuild

- Expand Σ_meas from global `α, β` to `Σ_meas = α·pnp_covariance + β(features)·I`
  with `β(features) = β₀ + Σᵢ wᵢ·featureᵢ` over the 5 per-query features
  (`log_inliers`, `inlier_ratio`, `reproj_err_norm`, `inlier_coverage`,
  `log_num_matches`). Exclude per-map features. Fit by L1-regularized maximum
  likelihood, `λ` by 5-fold CV, via a custom `scipy.optimize.minimize` (Σ_meas
  sits inside the covariance argument, so `LassoCV` does not apply).
- Bump `CalibrationArtifact` (`packages/python/core/src/core/calibration.py`)
  `SCHEMA_VERSION` 2 → 3: `sigma_meas_beta` becomes a `(β₀, w₁…w₅)` structure;
  remove `loose_min` / `tight_min`.
- Remove the server-side confidence gate at `docker/localizer/src/localize.py:232`
  (the `confidence_loose < loose_min` / `confidence_tight < tight_min` raise).
- In `docker/localizer/src/build_metrics.py`, apply the feature-conditional
  Σ_meas. Keep `confidence_tight` / `confidence_loose` (logistic + isotonic
  math) as diagnostic-only fields that drive no control decision; mark them so
  in `packages/python/core/src/core/localization_metrics.py`.
- Change the `tune_reconstruction.py` cell objective from map-quality metrics to
  end-to-end published-transform error on held-out frames run through the Phase
  4 harness. (Only this step depends on Phase 4.)
- Rewrite `config/calibration/global.json` to the new schema (re-derived by a
  real fit in Phase 6).
- No `generate-clients` / `generate-datamodels` and no DB migration: the
  artifact is not a wire type, and all 5 features already have columns in
  `localization_evaluations`.
- Update `scripts/SPEC.md` and `docker/localizer/SPEC.md` (separate prose
  commits) for the feature-conditional form, the removed server gate, and the
  reconciled data flow.

**Exit:** the fit runs against the Phase 4 corpus shape and produces a
schema-valid `CalibrationArtifact`; the localizer loads it; preflight green.

---

## Phase 6 — Bootstrap tuning loop (Phase A corpus)

Run the layered loop once against the bootstrap (ZED held-out) corpus. Layered,
not joint across layers; joint within the filter-threshold layer (`T_swap` ×
`KL_merge`, precision floor × `τ_evidence`).

1. Gather the corpus via `fit-calibration --captures …` (rebuilt Algorithm 1
   machinery) — produces real `localization_evaluations` rows with truth
   residuals + PnP covariance from ZED captures.
2. Fit Σ_meas (α, β₀, feature weights) via the Phase 5 ML fit; lock the result.
3. Sweep filter thresholds in the harness with Σ_meas locked — joint grid over
   `T_prune`, `T_swap`, `ε_publish`, `τ_evidence`, `KL_merge`, precision floor,
   watchdog `T`/`X`, pose-delta bounds. Score on the design-doc session-level
   metrics; pick the best cell.
4. Sweep reconstruction options via the Phase-5-extended `tune_reconstruction.py`
   (end-to-end filter performance on held-out frames), with filter thresholds +
   Σ_meas locked.
5. Write the resulting `config/calibration/global.json`.

**Exit:** a fitted, non-placeholder calibration good enough for early
dogfooding. Throwaway — replaced wholesale (not refined, not used as a prior)
when Phase B field data arrives.

---

## Phase 7 — Ship the real filter to the Capture Tool

- Make the multi-hypothesis filter + Phase 6 calibration the Capture Tool
  default.
- Demote the Phase 1 raw-passthrough from default to a reachable diagnostic
  toggle.

**Exit:** Capture Tool builds and runs the new filter against the Phase 6
calibration on-device; the demo workaround is still reachable. MakeItSing adopts
the same native core on the colleague's schedule.

---

## Deferred — phone dogfooding instrumentation + Phase B field loop

- Build the phone-side instrumentation that writes the corpus/logger rows
  (schema already locked in Phase 3 F2).
- Re-run the entire Phase 6 loop against the field corpus; its output replaces
  the bootstrap calibration wholesale as the deployed calibration.

## Related

- `.pulsar/memories/relocalization-redesign.md` — the locked end-state design
  this plan sequences.
