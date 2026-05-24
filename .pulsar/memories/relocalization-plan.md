---
updated: 2026-05-24
---

# Relocalization redesign — implementation plan kernel

This is the order-of-operations companion to
`.pulsar/memories/relocalization-redesign.md`. The design doc describes
the end state (what the system looks like when this is done); this doc
describes the sequencing to get there — what lands first, what depends
on what, and the specific recipe for the offline-tuning loop the design
doc treats abstractly.

Three pieces of content live here:

1. The `scripts/` reorganization that must land before any .NET code is
   introduced under `scripts/csharp/` (Phase 0 — precondition).
2. The intra-PR commit sequencing for the filter rewrite itself, which
   replaces a sequential-PR split as the bug-localization mechanism.
3. The step-by-step recipe for running the layered offline-tuning loop
   (corpus → Σ_meas → filter thresholds → reconstruction options → field
   validation), once the harness exists.

The *principle* that tuning is layered (not joint) stays in the design
doc as a design-time constraint. The specific procedural recipe lives
here because it is order-of-operations content.

## Phase 0 — `scripts/` reorganization

The end-state repo layout requires moving every existing file under
`scripts/` into `scripts/python/` to make room for `scripts/csharp/`.
This is a pure rename plus path-update operation — no behavior change,
no logic change. It must land *before* any .NET code is introduced under
`scripts/csharp/` so the new code is born in the post-reorg world and is
not moved twice.

Specifically the reorg:

- Moves `scripts/pyproject.toml`, `scripts/src/scripts/*.py`, and
  `scripts/tests/` under `scripts/python/`.
- Leaves `scripts/SPEC.md` and `scripts/README.md` at the `scripts/`
  root — those describe the directory itself, cross-language.
- Updates the root `pyproject.toml`'s uv workspace member declaration
  from `scripts` to `scripts/python`.
- Regenerates `uv.lock`.
- Updates every internal path reference: `scripts/SPEC.md`, any
  `CLAUDE.md` mentions, any CI workflow paths.
- Deletes the abandoned `packages/csharp/Placeframe/` and
  `packages/csharp/Placeframe.Tests/` stubs (just `bin/` and `obj/`
  cruft — no source, no .csproj).

The Python-side build tooling at `build/openapi-generator/`,
`build/openapi-projects.json`, `build/unity-projects.json`, and
`build/ruff.toml` already lives under `build/`, not `scripts/`, and is
unaffected by the reorg.

Treated as Phase 0 because it's a precondition for the redesign work,
not part of it. Clean as its own PR.

## Filter rewrite — intra-PR commit sequencing

The shim adoption and the multi-hypothesis rewrite land together, in one
PR. Pre-alpha, no production traffic, and the existing single-Gaussian
filter is already disabled in practice often enough that preserving its
behavior across an intermediate refactor commit has no real value — the
regression contract it would protect is a contract on broken behavior
we're discarding wholesale. A sequential "shim port first, then
multi-hypothesis rewrite" pair of PRs was considered and rejected on
those grounds.

The bisection structure a sequential split would have bought (failure ⇒
which PR caused it) is replaced by *intra-PR commit sequencing* plus the
convention-targeted primitive tests described in the design doc. The
primitive tests fail on specific classes of convention error
independent of any filter on top, so a CI failure inside the PR
localizes by test layer: primitive tests red ⇒ shim bug; primitives
green + behavioural tests red ⇒ multi-hypothesis math bug.

The non-math debugging surface — Unity ↔ portable-DLL integration
plumbing (IL2CPP, asmdef precompiled-reference paths, MathNet version
conflicts between Unity's bundled DLL and the library's NuGet reference,
.meta-file handling, Mono-vs-modern-.NET runtime quirks) — is the one
surface the primitive tests cannot help with. It is isolated by
**mandatory** commit sequencing inside the PR:

1. **First commit (load-bearing).** Stand up
   `packages/csharp/Placeframe.Filter/` and `Placeframe.Filter.Tests/`
   with the in-house shim primitives, the `Se3` Lie-algebra ops, the
   `AxisConvention` / `ChangeBasis` ports, and a stub
   `RelocalizationFilter` that throws `NotImplementedException`. Land
   the convention-targeted primitive tests in this commit and confirm
   they pass. Wire the DLL into `Plerion.VPS.asmdef`. Confirm Unity
   opens, compiles, and the stub loads — the integration pipeline is
   proven before any filter math depends on it.
2. **Second commit.** Implement the multi-hypothesis filter against the
   shim. Land the filter-level behavioural tests (perfect-measurement
   convergence, aliasing-recovery via challenger swap, KL-driven merger,
   evidence-based pruning, watchdog reset, `BypassChallengers`
   collapsing to single-Gaussian behaviour).
3. **Third commit.** Rewire `VisualPositioningSystem.cs` to the new
   filter API. Update UI surfaces
   (`apps/AndroidMobile/Assets/Scripts/Capture/AppUI.cs`) to expose
   hypothesis count, evidence, log Bayes factor, seconds since publish.
   Subscribe to `OnTrackingDiscontinuity`. Add the watchdog timer.

The first commit is load-bearing: it must land green before any
multi-hypothesis math is written. If the Unity-side packaging fights at
that point, it fights in isolation rather than tangled with
algorithmic-correctness debugging.

## Layered offline-tuning recipe

Run order once the filter is in place and the harness is built. The
*why* of the layering lives in the design doc ("Layered offline-tuning
loop"); this is the *how*.

1. **Gather corpus** via `fit_calibration --captures …`. Produces real
   `localization_evaluations` rows with truth residuals and PnP
   covariance. Uses the existing Algorithm 1 machinery unchanged.
2. **Fit Σ_meas** (α, β₀, feature weights) via the extended
   maximum-likelihood fit in `fit_calibration_from_corpus`. This is a
   data-fit step, not a filter-quality step. Lock the result.
3. **Sweep filter thresholds** in the harness with Σ_meas locked. Grid
   search over the multi-dimensional threshold space — thresholds within
   the filter-layer are not independent (`T_swap` interacts with
   `KL_merge`, the precision floor interacts with `τ_evidence`), so the
   sweep within this layer is joint. Score each cell on the
   session-level metrics defined in the design doc; pick the best cell.
4. **Sweep reconstruction options** via `tune_reconstruction.py`
   extended to use end-to-end filter performance on held-out frames as
   its cell objective. Filter thresholds and Σ_meas are locked.
5. **Field-validate** with phone-side dogfooding data on the logger
   schema described in the design doc's "Dogfooding logger schema"
   subsection. Per-map diagnostics feed back into reconstruction-options
   retunes (step 4), not into filter retunes (step 3).

When Phase B field data is first available, the whole loop runs again
against the field corpus — see "Two corpus phases" in the design doc
for the wholesale-replacement decision.

## Open sequencing questions

- **Phase 0 timing.** Can land any time, but landing it close in time to
  the filter rewrite minimizes the window where dependents need to
  understand two layouts. Suggested: land Phase 0, then the filter PR,
  in successive sessions.
- **Aliasing-injection fixture priority.** Synthetic fixtures are cheap;
  field-captured fixtures wait on dogfooding accumulation. The
  synthetic set should land alongside or just after the filter rewrite,
  not deferred — the recovery-time metric depends on it.
- **CI for the harness boundary.** Deferred until any post-initial-build
  modification to the harness, orchestrator, or filter (design doc
  documents the trigger). The first such modification's first commit
  writes the boundary test.

## Key files

The plan is a sequencing document; its file list is the union of files
touched by the design doc, taken in order of commit. See the design
doc's "Key files" section for the canonical list of paths.

## Related

- `.pulsar/memories/relocalization-redesign.md` — the end-state design
  this plan sequences.
