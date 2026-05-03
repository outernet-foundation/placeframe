# Aggressive rebase + MD cleanup plan

> Target: collapse 98 commits on `feature/vps-refactor` (the range `762ba23e..HEAD`) into ~58 commits via fixups, doc-commit dissolutions, drive-by reorderings, and a final MD-reorganization commit. Original commits stay individual unless they're legitimately doing the same thing (per user guidance). Codegen artifacts kept separate with canonical messages per the `CLAUDE.md` codegen-hygiene rule. The four `*-intent.md` design docs fold into permanent colocated `SPEC.md` / `CLAUDE.md` files so future Claude sessions inherit the context. `plan.md` shrinks to a future-work-only document; the other root-level `*.md` files either move to `docs/` or get deleted.

## State assessment (read at investigation time)

- Branch is at `38102dd9 Phase 3 chunk 10`, working tree clean, 31 commits ahead of `origin/feature/vps-refactor`. Tracking remote is in sync with the local branch.
- **Rebase scope: 98 commits in `762ba23e..HEAD`.** Everything at or before `762ba23e` ("Update CLAUDE.md with conventions and tooling notes for this branch") is shared with `origin/dev` and **must not be touched** — that includes the multipart-JSON fixes, Outernet.Logging package extraction, AndroidMobile/legacy-client migration, `.env.local.lock` removal, and the merge commits (`4f76fd75`, `1234d9fe`, `f4daae97`).
- **`origin/dev` is one commit ahead of this branch's base.** `origin/dev` tip is `190942b2` ("Update Capture Tool to newest ObserveThing/Stateful/Nessle packages"). This branch hasn't been rebased onto it yet. As part of this rebase pass, we incorporate `190942b2` as the new base for the 98 in-scope commits.
- `c97a9d04` ("Containerize ZED capture and refresh workspace infra", 2026-04-28) is the natural seam *within* the rebase range: 8 commits between `762ba23e` (exclusive) and `c97a9d04` (inclusive) are workspace-infra cleanup; the 90 commits after `c97a9d04` are VPS-refactor work proper.
- 11 `.md` files in repo root totaling 2,281 lines:
  - `CLAUDE.md` (150) — top-level project instructions; **stays**.
  - `README.md` (92) — top-level readme; **stays**.
  - `plan.md` (394) — execution status across all initiatives; **scrubbed to future-work-only**.
  - `vps-redesign-intent.md` (418) — VPS frontend + calibration runtime API + dogfooding logger design; **broken up into colocated SPECs**.
  - `e2e-and-calibration-intent.md` (484) — calibration internals (Algorithms 1–3, fit pipeline, runtime loader, artifact format, corpus); **broken up into colocated SPECs**.
  - `feature-pipeline-intent.md` (193) — feature pipeline modernization (ALIKED, scale standardization, retrieval, masking); **broken up into colocated SPECs**.
  - `static-tensor-typing-intent.md` (135) — Phase T prototype + future widening plan; **broken up into colocated SPECs**.
  - `code-review.md` (38) — open audit items from chunk 4; **resolve inline (delete file, fold any kept items into commit messages or fix them)**.
  - `grafana-integration.md` (215) — Loki integration future-work plan; **content moves into `plan.md` as new Phase 7, file deleted from root**.
  - `uv-lockfile-supply-chain-noise.md` (75) — known-issue documentation; **moves to `docker/neural-networks-base/CLAUDE.md` (the affected directory)**.
  - `vscode-container-access.md` (87) — dev environment notes; **moves to `.coi/CLAUDE.md`** (or to `CLAUDE.md` "Claude Code Environment Notes" section as inline content).

Existing colocated docs in the repo (precedent for the SPEC.md/CLAUDE.md pattern this plan extends):
- `apps/AndroidMobile/CLAUDE.md`, `docker/zed-capture/CLAUDE.md`, `.github/workflows/CLAUDE.md`, `build/src/build_scripts/placeframe/ci/CLAUDE.md` — instruction-flavored, "what Claude needs to know to operate here."
- `packages/unity/Logging/SPEC.md` — design-flavored, "what this is and why."

The pattern: **CLAUDE.md = operating instructions; SPEC.md = design rationale.** The intent files are design rationale, so they fold into `SPEC.md` files.

## Goals (recap)

1. **Significantly fewer commits.** ~15 broad-category commits, not 111 fine-grained ones. Each commit is one reviewable scope.
2. **Reorder drive-bys earlier.** Move applicable drive-by changes ahead of `c97a9d04` so the post-`c97a9d04` history is purely VPS-refactor work.
3. **Permanent intent file homes.** Each intent file's durable content (design decisions, rationale, "why this way") moves into a colocated `SPEC.md` next to the code it describes; future-work content moves into `plan.md`.
4. **`plan.md` becomes a clean future-work doc.** Strike all "Done" sections and tradeoffs already taken — those have moved into SPEC files. What remains is only what's still ahead.
5. **Root cleared of in-flight `.md` files.** Only `CLAUDE.md`, `README.md`, and (for now) `plan.md` survive at the root.
6. **Backup branch first.** A `backup/vps-refactor-pre-aggressive-rebase` branch pushed to origin before any history-rewriting starts, so the pre-rebase state remains reachable for as long as the user wants.

## Open questions (resolve before executing)

1. **Backup branch retention policy.** ✅ **Resolved: keep `backup/vps-refactor-pre-aggressive-rebase` and the `backup/pre-aggressive-rebase` tag on origin indefinitely.** Delete only on explicit user instruction.
2. **Intent → SPEC.md placement.** ✅ **Resolved**:
   - Six target locations confirmed (see "Target SPEC.md / CLAUDE.md placement" below).
   - Unity SPEC lands at the **package root** (`packages/unity/Placeframe/SPEC.md`), matching the existing `packages/unity/Logging/SPEC.md` precedent — not deeper at `Assets/Package/Core/SPEC.md`.
   - `localization_evaluations` cache contract lives in `database/CLAUDE.md` (schema is source of truth).
   - **LightGlue tuning record dropped from SPEC entirely** — the existing code comment on `load_lightglue` is the source of truth; no SPEC duplication.
   - No additional SPEC at compose-level / Docker-stack-composition level; existing top-level `CLAUDE.md` covers it.
3. **`code-review.md` items.** ✅ **Resolved: delete outright.** Both items are marginal; item 2 (manual pose inversion) may already be moot after chunk 7's harness rewrite; item 1 (silent-skip in `_build_feature_row`) is speculative. If either ever bites in practice, fixes are cheap.
4. **`grafana-integration.md` future-work.** ✅ **Resolved: move wholesale to `docs/grafana-integration.md`.** Preserves implementation-fidelity content for the future implementer; root is cleared. New `docs/` directory created in the MD-reorg commit. `plan.md` Phase 7 entry references the doc but doesn't duplicate its content.
5. **`vscode-container-access.md`.** ✅ **Resolved: move wholesale to `docs/vscode-container-access.md`**, consistent with Q4. Preserves the option-exploration record for any future revisit.
6. **`uv-lockfile-supply-chain-noise.md`.** ✅ **Resolved: delete outright.** No colocated relocation, no `docs/` move. Issue is no longer actively tracked.
7. **Codegen commits — separate or folded?** ✅ **Resolved: always separate, always with a canonical message.** Codegen artifacts under `packages/generated/` live in dedicated commits; messages are exactly `Run generate-clients`, `Run generate-datamodels`, or `Run generate-clients and generate-datamodels` — no body, no reference to source. Reviewers skip codegen commits; the canonical message + always-separate rule makes them spottable at a glance. Rule added to top-level `CLAUDE.md` under "Generation pipeline" so it survives this rebase as a durable convention. Topology table updated to keep one codegen commit per source-category (multiple existing codegen commits within a category fold into one canonical-message codegen commit; each category's codegen commit immediately follows its source commit).
8. **Granularity inside Phase 3 (commit #17).** ✅ **Resolved by topology restructure.** Q9's "preserve individuals" principle dissolved the bundle: chunks 5, 6, and 7 are now separate subsections (chunk 5 at #45–46, chunk 6 at #47–48, chunk 7 at #49–52). There is no longer a #17 mega-commit to split; the granularity is finer than the original 17a/17b proposal would have produced.
9. **Drive-by commit reordering scope.** ✅ **Resolved**:
   - `15fdd4d3` (pylock noise absorption) moves earlier into the prologue zone.
   - Chunk-9 fix-attribution narrative does not get a standalone commit; relevant content folds into commit bodies of the chunks it amended.
   - Phase 2b (ALIKED swap), Phase 2c (image-preprocessing module), Phase 2c-fixup (square-tile retrieval), **and the LightGlue tuning commit** (`585997cd`) **all move to the prologue zone** (between ZED capture and Phase 0) as the consolidated "Feature pipeline modernization" zone (zone C). Low conflict risk — those changes touch `models.py`, `core/camera_config.py`, and create `core/image_preprocess.py`, paths that VPS Phase 0/1/2a do not touch. LightGlue tuning depends on ALIKED so slots after `f1d4d2f7` within the zone.
   - **New zone D: backend API surface additions and fixes.** The capture-session API endpoints (`e2bafd90` + `19b382d6` + their codegen) and the cascade S3 prefix deletion bug fix (`f73ef13e`) **move out of chunks 7 and 9** into a new zone between feature pipeline (C) and VPS redesign main bulk (E). These are pre-VPS-redesign in spirit — exposing existing tar contents and fixing a pre-existing leak — not redesign work.
   - Phase T (static tensor typing prototype) **stays in the main VPS bulk**. Phase T's 65-line diff in `localize.py` plus changes to `build_metrics.py` and `map.py` overlap heavily with Phase 0's PnP-covariance plumbing and bring-up's band-aid sites in the same files; moving Phase T pre-VPS would force Phase 0/1/2a/bring-up to cherry-pick onto Phase T's typed seam against diffs written against pre-T code. Conflict risk too high to justify the noise reduction.
   - Several late-branch drive-bys consolidate via `--fixup` into earlier instances of the same change: `b4554e50` ("Narrow dockerignore allowlist…", duplicate subject of `a595a622`) → fixup into prologue; `84c13788` (pessimistic tight intercept refining the existing band-aid) → fixup into `a1cdf031`; `d7aa60d0` ("Log per-stage timings", same subject as `d2b48fea`) → fixup into `d2b48fea`; `e077e214` (chunk-9-vintage `pnp_covariance` 6×6 schema correction) → fixup into chunk 6's `7539b733`; `9eda1b2e` (Bearer-token injection in fit_calibration) → fixup into chunk 7's script-rewrite `338b6366`.
10. **Squash candidate annotations from chunk 9.** ✅ **Resolved: strip annotation lines entirely** from the resulting combined commit messages. The annotation pattern was an execution-time tracking aid; once the squash happens, the diff is the truth. No "Includes: X" trails appended.
11. **Memory updates after the rebase.** ✅ **Resolved: skip entirely.** SPEC.md / CLAUDE.md files are the durable record; Claude Code auto-loads CLAUDE.md per directory. Memory pointers to those files would be redundant. Memory is ephemeral in this container; the only thing that survives sessions is what's checked into the repo.

## Target SPEC.md / CLAUDE.md placement

Each intent file is broken up by *what code the content describes* and lands next to that code. Phase-status / "in flight, will be done in chunk N" content is always future-work and lands in `plan.md`. Tradeoffs already taken and design decisions already made are durable and land in `SPEC.md`.

### `vps-redesign-intent.md` (418 lines)

| Content | Destination |
|---|---|
| VPS frontend (`RelocalizationFilter` design, Bayesian SE(3) update, snap-vs-slew, innovation gate, σ_posterior lock-in fix, anchor naming) | `packages/unity/Placeframe/SPEC.md` (new — package root, matching `packages/unity/Logging/SPEC.md` precedent) |
| API contract for calibrated responses (Confidence/Covariance/PipelineVersion) | `docker/localizer/SPEC.md` (new), under "API contract" |
| Dogfooding logger schema + endpoint design (Phase 4) | Stays in `plan.md` as Phase 4 future work — not yet built |
| Phone-side correction algorithm (Phase 5) | Stays in `plan.md` as Phase 5 future work |
| Per-map fitting (Phase 6) | Stays in `plan.md` as Phase 6 future work |
| Production bring-up findings (band-aids, lock-in fix, σ_meas analysis) | `docker/localizer/SPEC.md` "Bring-up findings" section — durable post-mortem |

### `e2e-and-calibration-intent.md` (484 lines)

| Content | Destination |
|---|---|
| Calibration artifact format, `CalibrationArtifact` schema, `loose_min` / `tight_min` semantics, `apply_global_calibration` contract | `packages/python/core/SPEC.md` (new), under "Calibration" |
| Algorithm 1 (ZED held-out logistic + isotonic + Σ_meas α/β fit) | `scripts/SPEC.md` (new), under "fit_calibration.py" |
| Held-out frame selection (`StrideHeldOutSelector` Protocol, target_count, future-work selectors) | `scripts/SPEC.md`, under "Held-out frame selection" |
| `localization_evaluations` cache table contract (5-tuple key, upsert semantics, RLS, no extra indexes) | `database/CLAUDE.md` (new) — schema is the source of truth |
| Reconstruction-reuse helper (full-blob options match, manifest fetch) | `scripts/SPEC.md` |
| Determinism guarantees (`LOCALIZER_RANDOM_SEED`, why cuDNN-deterministic isn't enabled, cache-key contract) | `docker/localizer/SPEC.md` |
| Pipeline-version contract (git SHA via `GIT_COMMIT_SHA`, `/version` endpoint, override flag) | `docker/localizer/SPEC.md` |
| Truth-frame Procrustes / Umeyama design (single-anchor Sim3d kept; Umeyama as diagnostic-only) | `docker/reconstructor/SPEC.md` (new) |
| Map-quality metrics (5 features, ConvexHull, manifest-in-S3) | `docker/reconstructor/SPEC.md` |
| Algorithm 2 (pairwise VIO calibration), Algorithm 3 (per-map fitting) | Stays in `plan.md` Phase 5 / Phase 6 |
| Corpus-gathering spec for the future operator | `scripts/SPEC.md` "Corpus-gathering procedure" — durable executable spec |

### `feature-pipeline-intent.md` (193 lines)

| Content | Destination |
|---|---|
| ALIKED rationale (license-clean), licensing posture | `packages/python/neural-networks/SPEC.md` (new) |
| Image preprocessing module design (`transform_image()` / shorter-side resize, retrieval tiling, `LOCAL_FEATURE_RESIZE_SHORTER_SIDE`, `RETRIEVAL_TILE_OVERLAP_FRACTION`) | `packages/python/core/SPEC.md` "Image preprocessing" section |
| Square-tile retrieval aggregation rationale (why max over (q_tile, db_tile), in-DIR letterbox post-mortem) | `packages/python/core/SPEC.md` |
| LightGlue tuning record (V1/V2/V3 measurements, why V2 was chosen) | **Drop entirely.** Already lives as a comment on `load_lightglue` in `packages/python/neural-networks/src/neural_networks/models.py`; code is the source of truth, no SPEC duplication. |
| Semantic masking (Phase 2d) | Stays in `plan.md` — not yet built |

### `static-tensor-typing-intent.md` (135 lines)

| Content | Destination |
|---|---|
| Prototype design (where dim brands live, `make_*` factory pattern, `core.lightglue` `NewType` brands, why `core` not `neural_networks`) | `packages/python/core/SPEC.md` "Static tensor shape typing" section |
| `torch_ops.py` / `numpy_ops.py` design (why per-rank wrappers, PEP 646 rationale) | `docker/localizer/SPEC.md` "Tensor operations" section, plus a short pointer from `packages/python/core/SPEC.md` |
| Future widening (NDArray migration roadmap, lint tightening) | Stays in `plan.md` as Phase T future work |

### Other root .md files

| File | Action |
|---|---|
| `code-review.md` | Delete. Both items are marginal and tracked elsewhere (pose-inversion in `plan.md` open investigations; Optional-checks judged not load-bearing). |
| `grafana-integration.md` | Move wholesale to `docs/grafana-integration.md` (new directory). `plan.md` Phase 7 entry references it. |
| `uv-lockfile-supply-chain-noise.md` | Delete outright. |
| `vscode-container-access.md` | Move wholesale to `docs/vscode-container-access.md`. |
| `plan.md` | Scrub all Done sections and Tradeoffs-taken; keep only future-work phases (Phase 2d, 4, 5, 6, T-widening, deferred follow-ups, possibly new Phase 7). |
| `CLAUDE.md` | Stays. May absorb a short paragraph from `vscode-container-access.md`. |
| `README.md` | Stays untouched. |

## Target commit topology

Order is the post-rebase order from oldest to newest. The new base is `origin/dev` tip (`190942b2`).

**Guiding principle**: preserve original commits as individual commits unless they are legitimately doing the same thing. Consolidate only when (a) two adjacent commits address one logical change (e.g. a fix and its refinement), or (b) a late commit is a `--fixup` of an earlier one (same subject / same intent). Multiple separate concerns in the same broad category stay as separate commits — being in the same "phase" or "chunk" is not sufficient cause to consolidate.

**Codegen rule** (Q7): codegen artifacts always live in dedicated commits with the canonical message `Run generate-clients`, `Run generate-datamodels`, or `Run generate-clients and generate-datamodels`. No body, no rationale.

**Doc commits dissolve**: pure plan/intent edits ("Mark chunk N done", "Refresh plan and intents", etc.) do not survive — their content lives in the rewritten `plan.md` HEAD or in the new SPEC files via the final MD-reorg commit.

### A. Workspace infra prologue (8 in-scope originals + 1 reordered drive-by)

| # | Subject | Source commit |
|---|---|---|
| 1 | Pin openapi-generator-cli via openapitools.json | `4ae50b4b` |
| 2 | Add dev fallback for unity-library cache restore | `4b73fba6` |
| 3 | Default install branch to current git branch and infer single-target installs | `8256fd4d` |
| 4 | Document VS Code container access options for nested Docker | `f2de4cee` (file at root; final MD-reorg commit relocates to `docs/`) |
| 5 | Enable PyTorch expandable segments in localizer and reconstructor | `1a937918` |
| 6 | Narrow dockerignore allowlist within packages/ to dirs Dockerfiles actually consume | `a595a622` (with `b4554e50` fixed up — duplicate subject, late re-narrow) |
| 7 | Document uv lockfile supply-chain noise issue | `aa0f3e26` (file at root; final MD-reorg commit deletes per Q6) |
| 8 | Containerize ZED capture and refresh workspace infra | `c97a9d04` |
| 9 | Absorb upload-time supply-chain noise in neural-networks pylocks | `15fdd4d3` (moved from chunk-6 vintage per Q9) |

### B. ZED capture pipeline (preserve original)

| # | Subject | Source commit |
|---|---|---|
| 10 | Add ZED box capture pipeline: bound HTTP transport, captive portal spoof, and Loki log relay | `7f991b08` |
| 11 | Run generate-clients | `02a95f3b` (renamed to canonical message) |
| 12 | Route CaptureController errors through Outernet log pipeline | `31683c7c` |
| 13 | Restore typed HttpHeaders local in AndroidBoundHttpHandler response header copy | `36517f25` |
| 14 | Reject capture uploads with insufficient temporal coverage | `5353602d` |

### C. Feature pipeline modernization (NEW position — moved here from main bulk per Q9)

| # | Subject | Source commit |
|---|---|---|
| 15 | Replace SuperPoint with ALIKED for license-clean feature extraction | `f1d4d2f7` |
| 16 | Move image preprocessing to its own module; standardize per-axis intrinsics | `6c3ac826` |
| 17 | Move ransac_threshold and retrieval_top_k constants to localizer | `33048721` |
| 18 | Add square-tile retrieval aggregation; revert in-DIR letterbox | `8b33e34c` |
| 19 | Run generate-clients | `407b1095` + `3e1be173` consolidated (same source-change scope) |
| 20 | Enable LightGlue depth-confidence early stop and mixed precision | `585997cd` (moved from main bulk; depends on ALIKED so slots after #15) |

Doc commits `d1e091d9`, `8c433c97`, `44d19de3`, `26bd957f`, `f721aec6`, `1312f771`, `05e3d20d` dissolve via MD reorg. Per Q2, the V1/V2/V3 measurement record stays only in the existing code comment on `load_lightglue` — no SPEC duplication.

**Conflict-risk note**: `585997cd` adds 3 lines to `docker/reconstructor/src/reconstructor/run_reconstruction.py` (likely a `perf_counter` observability line). Phase T (which stays in main bulk at commit #26) touches the same file with 59 lines of typed-seam refactoring. Cherry-picking Phase T onto a base that already has `585997cd`'s 3-line addition should rebase cleanly because the additions are in different sections of the file (timing observability vs. model-call seam). If a conflict surfaces during execution, the resolution is mechanical (preserve both changes).

### D. Backend API surface additions and fixes (NEW position — moved here from chunks 7 and 9 per user request)

| # | Subject | Source commit |
|---|---|---|
| 21 | Add capture-session frames.csv, per-frame image, and manifest.json API endpoints | `e2bafd90` + `19b382d6` consolidated (all "add capture-session API endpoints" — same thing) |
| 22 | Run generate-clients | `a3e834f8` + `3f6b49e9` consolidated |
| 23 | Cascade S3 prefix deletion in DELETE /reconstructions/{id} | `f73ef13e` (moved from chunk 9; pre-existing bug fix, not VPS-redesign work) |

**Conflict-risk note**: Commit 23 modifies `delete_reconstruction` in `docker/api/src/routers/reconstructions.py`. Chunk 8 (`ae18197b`, new #53) modifies `create_reconstruction` in the same file. Different handler functions — clean rebase. The capture-session endpoints likely live in their own router file with no later modifications.

### E. VPS redesign main bulk

#### Phase 0 — schema + plumbing

| # | Subject | Source commit |
|---|---|---|
| 24 | Add Phase 0 calibration loader, identity bootstrap, and PnP covariance plumbing | `d5b39778` |
| 25 | Run generate-clients | `da6087e9` + `b5ab0df9` consolidated |

Doc commit `b0517b54` dissolves.

#### Phase 1 — Bayesian SE(3) filter + GeoPose rename (split into 1a / 1b per the original review intent in plan.md)

| # | Subject | Source commit |
|---|---|---|
| 26 | Rename Anchor to GeoPose, drop its per-frame Lerp, add SE(3) Interpolate | `326ac34e` |
| 27 | Replace VPS direct-overwrite with Bayesian SE(3) filter and centralized slew | `3d558f82` (incorporates VIO prediction-step fix from `d3d0aa10` net of `f9e99c10`'s revert) |

Doc commits `427d2ba0`, `129b130a` dissolve.

#### Phase 2a — In-Unity NUnit tests

| # | Subject | Source commit |
|---|---|---|
| 28 | Add Unity Test Framework coverage for VPS Phase 1 math + headless test runner | `f35c142e` |

`f9e99c10` is the package-refactor revert; net-net empty after `d3d0aa10`'s VIO-fix piece is preserved in commit #27 — dissolves.

#### Phase T — Static tensor shape typing prototype

| # | Subject | Source commit |
|---|---|---|
| 29 | Start static tensor shape typing initiative with localizer-scope prototype | `7bb05c4b` |

Doc commit `9bcd7dc6` dissolves.

#### Production bring-up

| # | Subject | Source commit |
|---|---|---|
| 30 | Surface per-phase reconstruction progress to capture tool UI | `2fca270c` |
| 31 | Add raw-quality floor and Σ_meas inflation band-aids for bring-up | `a1cdf031` (with `84c13788` fixed up — pessimistic tight intercept refines this band-aid) |
| 32 | Log per-stage timings of each successful localization | `d2b48fea` (with `d7aa60d0` fixed up — duplicate subject, late iteration) |
| 33 | Add base per-tick process noise so VPS filter cannot lock in | `f7ebc280` |
| 34 | Bind metrics dialog to OnMetricsReceived instead of transform-updated event | `b2254309` (Unity-side late drive-by; standalone commit) |

Doc commits `f55d052e`, `74a7020d`, `92062e2f`, `106be94f` dissolve.

#### Phase 3

**Chunk 1 — harness repair**

| # | Subject | Source commit |
|---|---|---|
| 35 | Add --single-config flag to e2e harness for starter calibration runs | `f1b63b1b` |

Doc commits `e382de67`, `548ea5cb`, `47dd59b8` dissolve.

**Chunk 2 — `is_indoor` flag + map-quality metrics**

| # | Subject | Source commit |
|---|---|---|
| 36 | Add is_indoor flag to reconstructions | `ab1f2687` |
| 37 | Run generate-datamodels | `69ea1d94` |
| 38 | Compute map-quality metrics at map-build time | `1eececab` |
| 39 | Run generate-clients | `81a8ed26` |

Doc commit `69fc1a67` dissolves. (`is_indoor` and map-quality are different things — separate per principle.)

**Chunk 3 — Procrustes pose-error labeling**

| # | Subject | Source commit |
|---|---|---|
| 40 | Procrustes-align reconstruction to truth and label held-out pose error | `51528284` |
| 41 | Run generate-clients | `f50df79d` |

Doc commit `665d68a2` dissolves.

**Chunk 4 — `fit_calibration.py` + raw PnP covariance**

| # | Subject | Source commit |
|---|---|---|
| 42 | Surface raw PnP covariance on LocalizationMetrics for calibration fitting | `d3b66ffe` |
| 43 | Run generate-clients | `19ae259f` |
| 44 | Add fit_calibration.py and extend harness rows with the inputs it consumes | `d1064706` |

Doc commits `65db8200`, `bc483a90`, `efabee75`, `cf43b7ad` dissolve. (Code-review.md content evaporates per Q3.)

**Chunk 5 — held-out frames as `ReconstructionOptions`**

| # | Subject | Source commit |
|---|---|---|
| 45 | Filter held-out frame timestamps from reconstructions | `c768581c` |
| 46 | Run generate-clients | `24592206` |

Doc commit `e7237cbd` dissolves.

**Chunk 6 — `localization_evaluations` cache**

| # | Subject | Source commit |
|---|---|---|
| 47 | Add localization_evaluations cache table and API | `7539b733` (with `e077e214` fixed up — chunk-9-vintage 6×6 schema correction belongs here per Q9) |
| 48 | Run generate-clients and generate-datamodels | `a3ec973b` |

Doc commits `d9cd76d9`, `e7cab489` dissolve.

**Chunk 7 — script refactor + localizer /version endpoint**

(Capture-session API endpoints + their codegen moved to zone D as commits #21/#22.)

| # | Subject | Source commit |
|---|---|---|
| 49 | Seed pycolmap and torch in localize_image_against_reconstruction | `3873483d` |
| 50 | Add GET /version endpoint to localizer | `54cd3ec7` |
| 51 | Run generate-clients | `87de7a57` |
| 52 | Refactor scripts: tune_reconstruction PB sweep, fit_calibration one-shot orchestrator | `338b6366` (with `9eda1b2e` fixed up — Bearer-token injection lives inside the rewritten fit_calibration script per Q9) |

Doc commit `7ef81e0c` dissolves.

**Chunk 8 — runtime feature plumbing**

| # | Subject | Source commit |
|---|---|---|
| 53 | Snapshot reconstruction is_indoor into manifest at create-time | `ae18197b` |
| 54 | Run generate-clients | `514278c5` |
| 55 | Plumb real Features into apply_global_calibration; replace `PnP_cov / tight²` with `α·PnP_cov + β·I` | `d752259a` |

Doc commit `8fd4cac1` dissolves.

**Chunk 9 — starter calibration**

(Cascade S3 deletion moved to zone D as commit #23.)

| # | Subject | Source commit |
|---|---|---|
| 56 | Land chunk-9 starter calibration | `35c9f6c3` |

Doc commits `e2ccbd42`, `2b25c97c`, `fd397d45` dissolve.

**Chunk 10 — band-aid removal**

| # | Subject | Source commit |
|---|---|---|
| 57 | Replace inlier-floor band-aid with calibration-driven gate; add `loose_min`/`tight_min` to CalibrationArtifact | `38102dd9` + `9c79ee72` consolidated (both chunk-10 source work — same thing) |

### F. MD reorganization

| # | Subject | Notes |
|---|---|---|
| 58 | Relocate design intents to colocated SPEC.md files; scrub plan.md to future-work-only | New commit; not derived from existing. Touches all SPEC.md / CLAUDE.md targets per the MD plan + relocates `vscode-container-access.md` to `docs/`, moves `grafana-integration.md` to `docs/`, deletes `code-review.md` and `uv-lockfile-supply-chain-noise.md`, dissolves the four `*-intent.md` files. |

### Net target

**98 → 58 commits** (41% reduction). Breakdown:

- **Workspace infra prologue (A)**: 8 originals + 1 reordered drive-by = **9 commits**
- **ZED capture pipeline (B)**: **5 commits** (preserved as-is)
- **Feature pipeline modernization (C)**: 4 source + 1 codegen + 1 LightGlue tuning = **6 commits**
- **Backend API surface additions and fixes (D)**: capture-session endpoints (1) + codegen (1) + cascade S3 deletion (1) = **3 commits**
- **VPS redesign main bulk (E)**: Phase 0 (2) + Phase 1 (2) + Phase 2a (1) + Phase T (1) + bring-up (5) + Phase 3 (Chunk 1: 1, Chunk 2: 4, Chunk 3: 2, Chunk 4: 3, Chunk 5: 2, Chunk 6: 2, Chunk 7: 4, Chunk 8: 3, Chunk 9: 1, Chunk 10: 1) = **34 commits**
- **MD reorganization (F)**: **1 commit**

**Constraint during rebase**: any existing commit that mixes source AND codegen must be split. Most existing commits are clean (one or the other) since they were authored under the chunk-6 separation convention.

## Drive-by reordering and fixup consolidations

Per Q9, the following physical reorderings and fixups happen during the rebase. Everything else in the original 98-commit history either stays in chronological position, dissolves (doc-only commits), or is handled by the topology table above.

| Action | Commit(s) | Target | Rationale |
|---|---|---|---|
| Reorder earlier | `15fdd4d3` "Absorb upload-time supply-chain noise…" | New position 9 (end of prologue zone A) | Workspace-infra concern, absorbed once; Q9(a) approved the move. |
| Reorder earlier (with Phase 2b/2c/2c-fixup) | `f1d4d2f7`, `6c3ac826`, `33048721`, `8b33e34c` + their codegen pair | New zone C (between ZED and Phase 0) | Feature-pipeline modernization is conceptually pre-VPS; touches different paths than Phase 0/1/2a. Q9 confirmed this move; Phase T does NOT move (high conflict risk). |
| Reorder earlier (with feature pipeline) | `585997cd` "Enable LightGlue depth-confidence early stop and mixed precision" | New zone C, position 20 (after ALIKED + 2c-fixup) | LightGlue tuning belongs with the feature pipeline modernization it concludes. Depends on ALIKED so slots after `f1d4d2f7`. Low conflict risk — touches `models.py` (no later commit re-modifies) and adds 3 lines to `run_reconstruction.py` (Phase T's 59-line refactor of the same file rebases cleanly when applied later). |
| Reorder earlier (new zone D) | `e2bafd90` + `19b382d6` (capture-session endpoints) and `a3e834f8` + `3f6b49e9` (their codegen) | New zone D, positions 21 + 22 | Capture-session endpoints expose tar contents that already existed in MinIO; this is API hygiene, not VPS-redesign work. Touches `docker/api/src/routers/capture_sessions.py` (or similar), no later modifications. |
| Reorder earlier (new zone D) | `f73ef13e` "Cascade S3 prefix deletion in DELETE /reconstructions/{id}" | New zone D, position 23 | Pre-existing bug fix (orphaned S3 bytes after row deletion) surfaced during chunk 9 but not VPS-redesign work. Modifies `delete_reconstruction` in `docker/api/src/routers/reconstructions.py`; chunk 8's `ae18197b` modifies `create_reconstruction` in the same file — different handlers, clean rebase. |
| Fixup into earlier | `b4554e50` "Narrow dockerignore allowlist…" | `a595a622` (commit 6) | Duplicate subject; same kind of work, late re-narrow. |
| Fixup into earlier | `84c13788` "Bake pessimistic tight intercept…" | `a1cdf031` (commit 27) | Refines the same band-aid the original commit added. |
| Fixup into earlier | `d7aa60d0` "Log per-stage timings…" | `d2b48fea` (commit 28) | Duplicate subject; late iteration of the same logging change. |
| Fixup into earlier | `e077e214` "Store pnp_covariance as 6x6…" | `7539b733` (commit 44) | Chunk-9-vintage schema correction belongs in the chunk-6 commit it fixes. |
| Fixup into earlier | `9eda1b2e` "Inject Bearer token…" | `338b6366` (commit 51) | Auth header injection lives inside the rewritten fit_calibration script. |
| Combine into one | `38102dd9` + `9c79ee72` | New commit 57 | Both are chunk-10 source work (gate + threshold fields) — same thing. |
| Combine into one | `e2bafd90` + `19b382d6` | New commit 47 | Both are "add capture-session API endpoints" — same thing. |
| Combine into one | `407b1095` + `3e1be173` | New commit 19 | Both are codegen for the same source-change scope (Phase 2b/2c). |
| Combine into one | `da6087e9` + `b5ab0df9` | New commit 21 | Both are codegen for Phase 0 fields + READMEs. |
| Combine into one | `a3e834f8` + `3f6b49e9` | New commit 48 | Both are codegen for capture-session endpoints. |

**Doc commits that dissolve** (≈18 commits, all pure `plan.md` / `*-intent.md` edits): `e382de67`, `548ea5cb`, `47dd59b8`, `d1e091d9`, `8c433c97`, `44d19de3`, `26bd957f`, `f721aec6`, `b0517b54`, `427d2ba0`, `129b130a`, `9bcd7dc6`, `f55d052e`, `74a7020d`, `92062e2f`, `106be94f`, `1312f771`, `05e3d20d`, `69fc1a67`, `665d68a2`, `e7237cbd`, `d9cd76d9`, `e7cab489`, `7ef81e0c`, `e2ccbd42`, `2b25c97c`, `fd397d45`, `8fd4cac1`, `65db8200`, `bc483a90`, `efabee75`, `cf43b7ad`, `b631e95e`. Their content moves into the rewritten `plan.md` HEAD or the new SPEC files via the final MD-reorg commit.

**Reverted-track collapse**: `d3d0aa10` ("Add package refactor intent, slot it as new Phase 2, fix VIO prediction step") + `f9e99c10` (which dropped that track) — net diff is just the VIO prediction-step fix. That fix folds into commit 23 (Phase 1b — Bayesian SE(3) filter); the package-refactor intent file evaporates with the revert.

## Step-by-step execution

### Step 0 — Backup and branch

```sh
# 1. Tag the pre-rebase HEAD locally so it's findable even if the branch is force-pushed.
git tag -a backup/pre-aggressive-rebase -m "Pre-aggressive-rebase snapshot of feature/vps-refactor"

# 2. Push a backup branch to origin. Distinct name from the working branch so it's not affected by force-pushes.
git branch backup/vps-refactor-pre-aggressive-rebase
git push origin backup/vps-refactor-pre-aggressive-rebase
git push origin backup/pre-aggressive-rebase  # also push the tag

# 3. Create the working branch for the rebase. Operate on this branch so feature/vps-refactor is untouched until verified.
git checkout -b rebase/vps-refactor-clean
```

Risk: the existing `feature/vps-refactor` is already pushed; the backup branch protects the pre-rebase history regardless of what we do to `feature/vps-refactor`. Force-push of `feature/vps-refactor` happens only after the cleaned-up branch is verified and the user signs off.

### Step 0.5 — Incorporate `origin/dev`'s one-extra-commit (`190942b2`)

`origin/dev` is one commit ahead of this branch's base (`762ba23e`). The new tip `190942b2` ("Update Capture Tool to newest ObserveThing/Stateful/Nessle packages") needs to be the new base of our 98 in-scope commits.

```sh
# Fetch origin (the COI environment may not have ssh creds; user runs this manually if needed).
git fetch origin

# Rebase onto origin/dev. Uses the existing 98 commits — preflight green per commit at this point.
# Conflict expectation: low. 190942b2 touches Unity package versions; this branch's Unity work is on a
# different package (Placeframe), so the only collision risk is if both touched packages.json or
# packages-lock.json. If conflicts surface, resolve in favor of origin/dev for the manifest entries
# 190942b2 introduced and re-add this branch's package additions on top.
git rebase origin/dev
```

After this step, `rebase/vps-refactor-clean` has 98 commits sitting on top of `190942b2` instead of `762ba23e`. The next steps' rebase scope becomes `190942b2..HEAD`.

### Step 1 — MD reorganization (executed first, on top of current HEAD)

Doing the MD reorg first means it lands as ONE clean commit on top of current HEAD; afterward the rebase can squash that single commit into commit #18 of the target topology without it tangling with the code commits.

1. Create `SPEC.md` files at each target location (see "Target SPEC.md / CLAUDE.md placement" above), populated by extracting the relevant durable sections from the four intent files. Cold-reader test: a future Claude Code session opening, e.g., `docker/localizer/SPEC.md` should be able to make sense of the design rationale without needing to find any of the deleted root .md files.
2. Create `docker/neural-networks-base/CLAUDE.md` (lockfile-noise blurb) and absorb `vscode-container-access.md` into the top-level `CLAUDE.md`'s environment-notes section.
3. Create new `plan.md` from scratch: phase-status table with only `Not done` rows; future phases (2d, 4, 5, 6, T-widening, 7); deferred follow-ups list. All Done sections deleted. Critical-path arrow shrinks. Tradeoffs-taken section deleted (those tradeoffs are now durable in the SPEC files).
4. Delete `code-review.md`, `grafana-integration.md`, `uv-lockfile-supply-chain-noise.md`, `vscode-container-access.md`, `vps-redesign-intent.md`, `e2e-and-calibration-intent.md`, `feature-pipeline-intent.md`, `static-tensor-typing-intent.md` from the root.
5. Run preflight (`uv run --no-sync preflight`) to confirm the MD-only changes don't break anything; preflight reads no .md files for code purposes, so this is a no-op check.
6. Commit as **"Relocate design intents to colocated SPEC.md files; scrub plan.md to future-work-only."** Single commit.

### Step 2 — Aggressive squash rebase

```sh
git rebase -i origin/dev
```

In the editor, transform the 99-line todo (98 in-scope commits + the new MD-reorg commit) into the target topology:

- Lines 1–8 (pre-`c97a9d04` zone, the 8 infra-prologue commits): fixup all 8 into commit #1 of the topology.
- Lines ~9–98 (post-`c97a9d04` zone): fixup/squash per category per the topology table.
- Line 99 (new MD-reorg commit): move to the very end as commit #14, or fold into commit #13 if user prefers (proposed: keep as a standalone "MD reorganization" commit since it's a different category from any code commit).
- Drive-by `15fdd4d3` (pylock noise absorption): cut from its current line and paste into the pre-`c97a9d04` zone, fixed up into commit #1.

Conflict resolution risks:
- Reordering `15fdd4d3` ahead of chunk 6 will conflict if any post-`c97a9d04` commit on the path also touches `docker/neural-networks-base/pylock.*.toml`. Audit: only chunk-6-vintage commits touch those paths (chunk 6 is where the absorption originally happened). The absorption diff is what `15fdd4d3` already contains; should rebase cleanly on the older base.
- The chunk-9 fixup squashes already happened in this session — three commits (`e077e214`, `9eda1b2e`, `f73ef13e`) carry merged-fixup history. Tree hash is verified identical pre/post that earlier squash. Re-squashing them into commit #12 / #13 is safe.
- Two reverted approaches surface as paired commits to collapse cleanly: `d3d0aa10` (added a package-refactor intent file) + `f9e99c10` (dropped that track) — both squash into commit #4/#5 (Phase 1/2a) leaving no artifact. Similarly the Phase 2c letterbox lived briefly in `6c3ac826` and was reverted in `8b33e34c` — squashing both into commit #7 leaves the final state correct.

### Step 3 — Verify post-rebase tree

```sh
# Tree hash must match HEAD before the rebase began (the MD-reorg commit changes file content,
# so compare against the MD-reorg commit's tree, not the original HEAD's tree).
git rev-parse rebase/vps-refactor-clean^{tree}  # must equal the MD-reorg commit's tree hash.

# Run the full preflight on the rebased HEAD.
uv run --no-sync preflight

# Spot-check a handful of intermediate commits to confirm they're internally consistent
# (each commit should leave preflight green, since each was already preflight-green pre-rebase).
git checkout <commit-7>; uv run --no-sync preflight
git checkout <commit-12>; uv run --no-sync preflight
# etc.
```

### Step 4 — Force-push (gated on user sign-off)

```sh
# Only after explicit user approval.
git checkout feature/vps-refactor
git reset --hard rebase/vps-refactor-clean
git push --force-with-lease origin feature/vps-refactor
```

`--force-with-lease` (not `--force`) so a concurrent push from elsewhere prevents stomping. The backup branch on origin is unaffected.

## Risks and rollback

| Risk | Mitigation |
|---|---|
| Force-push wipes work that's only on the remote `feature/vps-refactor` | Backup branch + tag pushed in step 0; use `--force-with-lease` in step 4. |
| Conflict during squash that materially alters semantics | Each commit must pass preflight; verify tree hash equals MD-reorg-commit tree hash before any force-push. If a conflict can't be resolved cleanly, abort the rebase (`git rebase --abort`) and reassess; original branch is untouched until step 4. |
| Intent content gets lost in the SPEC migration | The MD-reorg commit (step 1) is isolatable and reviewable as a single diff — read the full diff before any squashing happens. |
| Future Claude session doesn't know intents moved | Memory entries (step 5) plus inline pointers in the new SPEC.md files. |
| Reordering across `c97a9d04` produces semantic conflicts in pylock files | Audit `15fdd4d3` ahead of time — confirm no later commit fights with it on `docker/neural-networks-base/pylock.*.toml`. If conflict, abandon that one drive-by reorder and leave `15fdd4d3` post-`c97a9d04`. |
| Phase 3 collapse (commits 14–17) hides too much in too few commits to be reviewable | If 4 commits feels too coarse, split #16 into 16a (backend gap closure) and 16b (script refactor) — that's 5 commits for Phase 3 and feels right. User decides at execute time. |

## Net result (target)

- **98 → ~58 commits** on `feature/vps-refactor` (41% reduction; mostly via doc-commit dissolutions, ~5 fixups, ~5 same-thing combinations, and codegen-message canonicalization), all sitting on top of the new `origin/dev` tip `190942b2`. Original commits preserved as individuals where possible; codegen commits remain separate per the convention added to `CLAUDE.md`.
- **11 → 3 root-level `.md` files** (`CLAUDE.md`, `README.md`, `plan.md`).
- **5 new colocated `SPEC.md` files** + **1 new colocated `CLAUDE.md` file**, each under the directory whose code they describe — surviving as durable artifacts that future Claude sessions automatically pick up.
- `plan.md` becomes a tight future-work-only doc (Phase 2d, 4, 5, 6, T-widening, deferred follow-ups, possibly Phase 7 grafana).
- Backup branch + tag preserved on origin so the pre-rebase history remains reachable as long as the user wants.
- **Untouched: everything at or before `762ba23e`.** The multipart-JSON merges, Outernet.Logging package extraction, AndroidMobile/legacy-client migration, `.env.local.lock` removal — all stay exactly as they are on `origin/dev`. This rebase only operates on the 98 commits this branch added.
