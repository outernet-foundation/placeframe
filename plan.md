# Plan

> Design intents:
> - VPS redesign: [`vps-redesign-intent.md`](vps-redesign-intent.md) (Phases 0, 1, 2a, 4).
> - Feature pipeline modernization: [`feature-pipeline-intent.md`](feature-pipeline-intent.md) (Phases 2b, 2c, 2c-fixup, 2d).
> - End-to-end testing and calibration: [`e2e-and-calibration-intent.md`](e2e-and-calibration-intent.md) (Phase 3 — fused initiative; downstream Phases 5, 6 execute its deferred algorithms).
> - Static tensor shape typing: [`static-tensor-typing-intent.md`](static-tensor-typing-intent.md) (Phase T).

This file tracks execution of all in-flight initiatives: phase definitions, status, tradeoffs taken, and scaffolding deliberately left for later phases to replace. Deleted when all initiatives complete.

## Phase status

| # | Phase | Initiative | Status |
|---|---|---|---|
| 0 | Schema + plumbing | VPS | ✅ Done |
| 1 | Frontend rewrite | VPS | ✅ Done |
| 2a | In-Unity NUnit tests for Phase 1 math | VPS | ✅ Done |
| 2b | SuperPoint → ALIKED | Pipeline | ✅ Done |
| 2c | Local-feature scale standardization (formerly "Aspect-ratio preprocessing") | Pipeline | ✅ Done — but the in-DIR letterbox added under this phase is misguided and is reverted in 2c-fixup |
| 2c-fixup | Revert in-DIR letterbox; add square-tile retrieval aggregation | Pipeline | ✅ Done — optional `transform_image` rename deferred |
| T | Static tensor shape typing | Typing | Prototype landed; widening deferred. Orthogonal — no specific phasing dependency. |
| 3 | End-to-end testing and calibration (code + single-capture starter; multi-capture corpus deferred) | E2E+calibration | In progress — execution chunks 1–6 of 10 landed (harness repair, map-quality metrics, Procrustes pose-error labeling, `fit_calibration.py`, held-out-frames as a `ReconstructionOptions` field, `localization_evaluations` cache table + API). Chunk 7 (script refactor: harness/fit-script decouple) and chunks 8–10 (runtime feature plumbing, starter run, band-aid removal) remain. |
| 2d | Semantic-segmentation masking (~3-day implementation) | Pipeline | Not started — moved after Phase 3; required for outdoor operation |
| 4 | Dogfooding logger | VPS | Not started |
| 5 | Phone-side correction | VPS | Not started |
| 6 | Per-map overlay (opportunistic) | VPS | Not started |

## Critical path

```
Phase 0 ─► 1 ─► 2a ─► 2b ─► 2c ─► 2c-fixup ─► T ─► 3 ─► 2d ─► 4 ─► 5 ─► (6 opportunistic)
```

Strictly serial. With ~2 known users, total wall-clock time is dominated by coding work and a single directed data-gathering session at Phase 5, not by passive accumulation. There's no parallelism to exploit.

Phase 2d (semantic-segmentation masking) was originally bundled ahead of Phase 3 to avoid a calibration refit. It's been moved to *after* Phase 3 because (a) the band-aids in `localize.py` and the bootstrap calibration are real friction during ongoing testing, (b) the calibration logic doesn't change based on whether masking is in place — only the data distribution does, so the cost of the reorder is exactly one offline refit when masking lands (a few hours of GPU compute on already-collected data, no new data acquisition), and (c) lived experience with calibrated confidence will inform 2d's tuning.

The "Phase 2e" parameter-sweep work originally listed in `feature-pipeline-intent.md` has been merged into Phase 3. The discovery: the e2e harness is the calibration data-generation engine — the sweep cells are the calibration training rows. See [`e2e-and-calibration-intent.md`](e2e-and-calibration-intent.md) "Why these are one effort." Phase 2e no longer exists as a distinct phase.

Phase 3 lands code completion *plus* a single-capture starter calibration. Chunks 1–4 landed the harness repair, map-quality metrics, pose-error labeling, and `fit_calibration.py`. Chunks 5–7 are an architectural correction discovered after chunk 4: the harness ended up owning input data (a sibling `placeframe-test-captures/` directory), output schema (`e2e-results.json`), and provenance bundling because the reconstructor lacked a "build excluding these frames" capability. Chunk 5 closed that API gap (held-out frames are now a first-class `ReconstructionOptions` field, filtered in the reconstructor at the `frames.csv` parse boundary). Chunk 6 added the `localization_evaluations` cache table + REST endpoints so localization outcomes can be persisted by key and re-read cheaply. Chunk 7 collapses both scripts to thin orchestrators over backend ids: turns `run_e2e.py` into `tune_reconstruction.py` (PB sweep only) and turns `fit_calibration.py` into a one-shot end-to-end command that reads captures/reconstructions from the database. Chunks 8–10 then plumb runtime features, run the starter against the one capture, and remove the band-aids. **The multi-capture corpus is not gathered, the full ~15-hour parameter sweep is not run, and the production calibration is not produced this phase.** A standalone deliverable of Phase 3 is the corpus-gathering spec in the intent file, ready to execute when the operator goes to assemble the multi-capture corpus and run the production fit.

**Phase 2c-fixup** exists because the original Phase 2c bundled together two distinct fixes that should have been separate: scale standardization for local features (correctly addressed by shorter-side resize, kept) and cross-aspect framing handling for retrieval (incorrectly addressed by an in-DIR letterbox with mean padding, reverted). The corrective phase reverts the letterbox and adds the actually-correct fix — square-tile aggregation on the retrieval path. See `feature-pipeline-intent.md` Status section for why the original design was wrong.

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

### Phase 2b — SuperPoint → ALIKED

License blocker. SuperPoint's MagicLeap weights are non-commercial research-only and cannot ship under Apache 2.0.

- Replace `load_superpoint` with `load_aliked` in `packages/python/neural-networks/src/neural_networks/models.py` ✅.
- Switch LightGlue's checkpoint to the official ALIKED variant (`features="aliked"`) ✅. Descriptor dim drops from 256 to 128; downstream consumers (`lightglue_match_tensors`, OPQ training) are dim-agnostic.
- Drop the grayscale tensor pipeline at the load sites in `localize.py` / `run_reconstruction.py`; ALIKED consumes the existing RGB tensor directly ✅.
- `detection_threshold` and `nms_radius` left at ALIKED defaults (`0.2`, `2`); deferred to post-bringup tuning when keypoint density is observable on real data.

Pre-market: no maps to migrate, pure code swap. Generated OpenAPI artifacts (`docker/api/openapi.json`, `packages/generated/**`) carry one stale "SuperPoint" string in `average_keypoints_per_image`'s description; sweeps in on the next `generate-clients` run.

End of Phase 2b: Apache-2.0-clean feature pipeline. Local matching produces the same shape of result it did before, with different magnitudes. Calibration remains identity (Phase 3 not yet fit).

### Phase 2c — Local-feature scale standardization

> **Scope correction**: this phase originally bundled local-feature scale handling and a retrieval-side letterbox (treating cross-aspect mismatch as a single problem). Those are actually two distinct problems; the local-feature half landed correctly here, the retrieval half landed incorrectly here and is reverted in Phase 2c-fixup. See `feature-pipeline-intent.md` Status note.

Today the pipeline (pre-2c) applies only orientation correction in `transform_image()`. ALIKED's receptive field is fixed in pixels, so the same physical content at different camera resolutions produces different keypoint scales — descriptors don't match across resolution gaps. The fix is scale standardization via shorter-side resize. (For cross-aspect retrieval framing — the *separate* problem — see Phase 2c-fixup.)

- Resize-shorter-side added to `transform_image()` ✅. `LOCAL_FEATURE_RESIZE_SHORTER_SIDE = 1024`. Aspect ratio preserved; no padding for the local-feature path. Standardizes physical-meters-per-pixel so ALIKED's receptive field sees comparable structure regardless of source camera resolution.
- `transform_intrinsics()` now applies the same per-axis resize ratio to `(width, height, fx, fy, cx, cy)` so PnP stays correct ✅.
- DIR also letterboxes to a square inside `DIR.forward` ✅ — **but this is misguided**: it tries to address cross-aspect retrieval framing via a non-standard mean-pad-with-handwave-zero-contribution mechanism, when the real cross-aspect retrieval problem is framing-mismatch (different content captured) which can't be fixed by reshaping the input. Reverted in Phase 2c-fixup.

End of Phase 2c: local-feature path is scale-standardized. Cross-aspect retrieval is *not* solved — that requires Phase 2c-fixup.

### Phase 2c-fixup — Revert in-DIR letterbox; add square-tile retrieval aggregation

Cross-aspect query/database mismatch makes whole-image DIR descriptors compare different framed content (a portrait excludes left/right strips of a landscape and vice versa). The Phase 2c letterbox tried to fix this with mean-padding inside `DIR.forward` but it's the wrong fix — reshaping the input can't recover content that wasn't framed in the first place. The correct fix is to give each image *multiple framings* via square-tile aggregation; at least one tile pair frames similar content and surfaces the match.

**Revert work:**

- Letterbox removed from `DIR.forward` ✅; `_letterbox_to_square` helper dropped ✅.

**Tiling work:**

- `tile_for_retrieval(image)` helper added to `core/camera_config.py` ✅. Takes a shorter-side-resized PIL image and produces M overlapping `LOCAL_FEATURE_RESIZE_SHORTER_SIDE × LOCAL_FEATURE_RESIZE_SHORTER_SIDE` square crops along the long axis. `RETRIEVAL_TILE_OVERLAP_FRACTION = 0.5` (~50% overlap); M derived from long-axis length.
- Reconstructor runs DIR over each tile per database image and stores `(M, D)` descriptors per image ✅. OPQ/PQ training operates on the local (ALIKED) descriptors only — global-descriptor tiling doesn't affect that path.
- Localizer tiles the query ✅. Similarity is computed as a `(M_q, sum_M_db)` matrix; per-database-image similarity is the max over all `(query_tile, db_tile)` pairs (mathematically equivalent to max over query-tile axis followed by scatter-max grouped by image). Top-K picks images by aggregated similarity.
- `Map` grew a `(sum_M_db, D)` `global_descriptors_matrix` plus a parallel `tile_to_image_row` index mapping each row to its position in `ordered_image_ids` ✅.

**Naming cleanup (deferred):** `transform_image()` still doesn't telegraph that it resizes. With `tile_for_retrieval()` now sitting alongside `transform_image()`, the natural rename to `prepare_image_for_extraction()` / `prepare_image_for_retrieval()` is straightforward — but it touches multiple callers across services and was held back to keep the tiling commit reviewable on its own. Worth a follow-up commit, or fold into the next pipeline change.

**Risks (unmeasured):**

- Tile aggregation policy (`max` vs `mean`) — default `max`; revisit when the Phase 3 e2e harness's parameter sweep first runs.
- M, tile size, overlap — defaults look reasonable; sweep range when the Phase 3 e2e harness's parameter sweep first runs.
- M× growth in OPQ index storage — manageable at M = 3–5 for current map sizes.
- In-aspect regression risk: tiling could underperform single-window retrieval on same-aspect query/database pairs (less context per descriptor). Configurable `RETRIEVAL_TILES_PER_IMAGE = 1` falls back to single-window without removing the code path.

End of Phase 2c-fixup: cross-aspect retrieval is correctly addressed. The pipeline now has two preprocessing paths sitting side-by-side with honest names: local features get aspect-preserved shorter-side resize; retrieval gets that plus square tiling.

### Phase T — Static tensor shape typing

A localizer-scope prototype landed alongside Phase 2c-fixup. `core/tensor_types.py` holds only the `TT[*Shape]` torch shim; dim brands sit next to the concept that defines them — `NumImages` / `MaxTiles` / `NumQueryTiles` in `core/image_preprocess.py`, `RetrievalDim` / `NumKeypoints` / `LocalDescDim` in `core/model_wrappers.py`, `NumMatches` in `core/lightglue.py`. `docker/localizer/src/torch_ops.py` exposes thin generic torch wrappers (`from_numpy`, `to`, `stack`, `permute`, `transpose`, `matmul`, `amax`) as `@overload`-driven, `Literal`-typed dim/axis functions so the runtime arg drives the output shape through the type system. `core/numpy_ops.py` is the numpy sibling (`zeros` per rank; rank-1 `nonzero` and `compress`); `Map.load_map` uses it with `NumImages(...) / MaxTiles(...) / RetrievalDim(...)` brand constructors at the shape tuple, and `lightglue_match_tensors` uses it to drop the match-index branding casts. `core/model_wrappers.py` houses four `make_*` factories — `make_global_descriptor_extractor` (DIR), `make_local_feature_extractor` (ALIKED), `make_local_feature_matcher_for_tensors` and `make_local_feature_matcher_for_arrays` (LightGlue, tensor-input and numpy-input variants) — consumed by both `localize.py` and `run_reconstruction.py` so their `load_models()` is three lines instead of hand-rolled inner closures. `core/lightglue.py` is fully off `NDArray` and exports `Keypoints` / `Descriptors` / `KeypointsArrays` / `DescriptorsArrays` `NewType` brands so positional swaps at the matcher are caught statically. The workspace venv now syncs with `--extra cpu` (`uv sync --all-packages --extra cpu`) so torch resolves locally; pyright shows zero errors introduced by Phase T (one residual upstream `from torch import from_numpy` stub-unknown that pre-dates the work). The remaining 11 `NDArray` imports across the codebase carry `# noqa: TID251 — Phase T piece 3 follow-up migration` to keep lint clean. Sits between 2c-fixup and 2d so the new code in 2d (semantic-segmentation masking) lands typed instead of paying retroactive migration cost.

**E2E verification (gate before widening):**

- Run `tune-reconstruction` (formerly `test-placeframe-e2e`; renamed in Phase 3 chunk 7) or `fit-calibration` against the post-prototype pipeline. Confirm reconstruction completes and localization produces a non-degenerate pose.
- The `global_descriptor_extractor` wrapper (replacing the prior `dir` global) in `localize.py` / `run_reconstruction.py` and the retrieval-block matmul rearrangement (`torch_ops.transpose` + `torch_ops.matmul` + `torch_ops.permute`) are mechanical translations of the prior code; bisecting against `403d9fd1` ("Add square-tile retrieval aggregation") isolates any regression.
- Block widening migration until this passes.

**Localizer / reconstructor full coverage:**

- `Map.keypoints` and `Map.pq_codes` typed with rank-correct shapes (`NumKeypoints` brand acknowledging per-image variation; rank and last-axis size still meaningful).
- ~~`aliked_output` typed via Protocol or TypedDict — analog of the `global_descriptor_extractor` wrapper, but for ALIKED's keypoint/descriptor output.~~ Done in the prototype: `local_feature_extractor` wrapper returns typed tuple.
- ~~`lightglue_match_tensors` signature carries shape brands.~~ Done in the prototype: `local_feature_matcher` wrapper + `MatchIndices` type alias.
- `axis_convention.py` translations / rotations / quaternions typed with `ndarray[tuple[Literal[3]], ...]` etc.

**Repo-wide `NDArray` migration:**

- Eleven files import `NDArray` (from Ruff `TID251` enumeration). Migrate each to `ndarray[tuple[..., ...], dtype[T]]` with explicit shape brands.
- Per-file commits, grouped by module for reviewer-friendly diffs.
- End state: zero `from numpy.typing import NDArray` outside generated code; zero `# noqa: TID251`.

**Repo-wide `Tensor` migration:**

- Replace bare `Tensor` with `TT[*Shape]` where shape is known. Grow `torch_ops.py` opportunistically as migration touches each file. `Tensor` survives only at boundaries with un-typable third-party calls (neural net outputs, pycolmap returns), wrapped at the seam.

**Lint tightening:**

- Add `reportExplicitAny` to basedpyright config to catch new `cast(Tensor, ...)` / `Any` escape hatches.
- Add `flake8-tidy-imports` ban on bare `torch.Tensor` in domain modules; allow only in `torch_ops.py`-style wrappers via `per-file-ignores`.

**Risks:**

- Migration is large (~50+ usage sites across 11 files for the `NDArray` migration alone). Mitigation: per-file commits with a common pattern.
- PEP 646 limits (no per-element bounds on `TypeVarTuple`) force per-rank `@overload` sets in `torch_ops.py`. Manageable; just verbose.
- Pyright's PEP 646 support has rough edges on advanced unifications. We're pyright-only in basedpyright strict mode, so fine.

End of Phase T: tensor shapes are statically checked at function/assignment boundaries throughout the localizer, reconstructor, `core`, and `neural-networks` packages. New tensor code in subsequent phases lands typed by default, with lint enforcing it. No runtime overhead; no library dependency.

### Phase 3 — End-to-end testing and calibration (code + single-capture starter; multi-capture corpus deferred)

Fuses the previously-separate "Phase 2e" (e2e harness repair + parameter sweep) and "Phase 3" (ZED-only global calibration) under the realization that the e2e harness *is* the calibration data-generation engine. Full design in [`e2e-and-calibration-intent.md`](e2e-and-calibration-intent.md); the 11 design questions are resolved in that file's "Resolved decisions" section.

Scope this turn: full code path lands, plus a single-capture starter calibration produced by running the code against the one capture we already have. **No additional captures are gathered, no full parameter sweep is run, and the starter calibration is known-bad-but-real — not the production calibration.**

Code deliverables (full list in the intent file):

- Repair `scripts/src/scripts/run_e2e.py` (originally `test_placeframe_e2e.py`; lint/type errors S608, ASYNC240, broken `main()`, `basedpyright` clean).
- Add a `--single-config` flag to the harness (server-default recon + loc, skips the cross product).
- Add a pose-error-labeling step. Reconstructor places the rebuilt map in the capture's truth frame via the existing single-anchor `Sim3d` and emits a separate rigid Umeyama residual as a per-capture VIO-quality diagnostic. Harness compares the localizer's `camera_from_map` to the held-out frame's `frames.csv` truth pose to record `err_t`, `err_r` per held-out frame.
- Add the 5 map-quality features (`map_image_count`, `map_point_count`, `map_avg_track_length`, `map_bounding_volume_m3`, `map_viewpoint_diversity`) to `ReconstructionMetrics`; reconstructor populates them inside `build_reconstruction_metrics` at map-build time; they ride the existing manifest-in-S3 path. Add `is_indoor` boolean column to `reconstructions` (default false; user-toggle, not a reconstruction output). Harness fetches the manifest per reconstruction at row-emission time.
- Create `scripts/src/scripts/fit_calibration.py` implementing Algorithm 1 (ZED held-out logistic + isotonic fit + Σ_meas α/β scalar fit, with reporting).
- Plumb features through `apply_global_calibration`: replace the `Features.zeros()` placeholder in `build_metrics.py:66` with a real `Features` instance built from transformed metrics + map quality features. The typed seam already landed (see chunk 5 note below).
- Decouple Σ_meas from confidence in `build_metrics.py`: replace `PnP_cov / tight²` with `α · PnP_cov + β · I` (α, β read from artifact). Confidence becomes a gate via `if metrics.confidence.tight < TIGHT_MIN: raise LocalizationError(...)` in `localize.py`.
- ~~Implement the per-map calibration loader path (lazy MinIO fetch + cache, soft-fall-back to global-only). Per-map fitting (Algorithm 3) is *not* implemented; deferred to Phase 6.~~ **Both the loader and the fitter are deferred to Phase 6 (revised during chunk 8).** Originally only the fitter was deferred and the loader was scoped into chunk 8; on closer inspection the loader is dead code with no exercise until the fitter exists, so they bundle together. See chunk 8 below and the Phase 3 deferred follow-ups list.

Run-and-commit deliverables (single-capture starter):

- Run the harness in `--single-config` mode against the one existing capture; run `fit_calibration.py` on the resulting rows; commit the produced `global.json` to the repo with a header comment marking it as a known-bad single-capture starter.
- Pick `TIGHT_MIN` from the starter fit's success-cluster distribution; bake into `localize.py`.
- Remove the `IDENTITY_BOOTSTRAP_SENTINEL` skip in `calibration.py`, the `MIN_NUM_INLIERS` / `MIN_INLIER_COVERAGE` band-aid in `localize.py`, the hand-set `-4.595` intercept in the previous identity-bootstrap `global.json`, and the `CONFIDENCE_TIGHT_FLOOR` floor in `build_metrics.py`.

Documentation deliverable:

- The corpus-gathering spec in the intent file, unambiguous enough to execute cold.

Deferred until multi-capture corpus exists (out of scope this turn):

- Re-tuning `RelocalizationFilter.BaseProcessNoise{Translation,Rotation}VariancePerTick` and `SnapThresholdSigmas` against fitted Σ_meas. The single-capture starter is too unreliable to drive meaningful tuning; the system will feel rougher than the identity-bootstrap baseline until the corpus run lands.
- Running the full parameter sweep (~15 hours estimated).
- Replacing the starter calibration with a production one fit on multiple captures.

End of Phase 3: the harness is repaired and emits labeled rows; `fit_calibration.py` exists and is tested against synthetic data plus exercised against the one real capture; the runtime loader plumbs features and decoupled Σ_meas end-to-end; the schema is migrated; a starter calibration is committed; band-aids are removed. The system runs on real (varying, overfit) confidence. The operator is unblocked from going to gather the multi-capture corpus and replace the starter.

**Execution chunks** (each lands as one or more reviewable commits; each is a stoppable pause point):

1. ✅ **Harness repair** — fix S608 / ASYNC240 / broken `main()`; add `--single-config` flag. Landed.
2. ✅ **Reconstructor map-quality metrics + `is_indoor` column** — 5 features folded into `ReconstructionMetrics` and populated inside `build_reconstruction_metrics` at map-build time (`scipy.spatial.ConvexHull` for volume); manifest-in-S3 carries them. `is_indoor` boolean column added to `reconstructions`. Landed.
3. ✅ **Procrustes pose-error labeling** — single-anchor `Sim3d` alignment retained as the reconstruction's truth-frame transform (preserves "first registered frame == map origin" contract that downstream consumers rely on); rigid Umeyama (closed-form Kabsch via numpy SVD) computed *separately* over all registered frames purely as a per-capture diagnostic, not applied to the reconstruction. Both blocks share a `_registered_frames(rigs, colmap_image_ids, reconstruction)` generator that handles multi-camera rigs (e.g. ZED stereo where one Frame is shared across left/right). Per-capture residuals surface as `truth_alignment_rms_residual_m` / `truth_alignment_max_residual_m` on `ReconstructionMetrics`. Harness captures held-out frame truth in `_prepare_capture` and computes `err_t_m` / `err_r_deg` per localization in Phase 6 by inverting the localizer's `camera_from_map` Transform (both sides in the capture's native axis convention; no basis change needed since the API converts back from OpenCV at the boundary). `pytransform3d` not added — `scipy.spatial.transform.Rotation` covers the rotation-magnitude need. Landed.
   - Architecture choice: reconstructor emits both the alignment and the diagnostic (Architecture A). The Umeyama math lives in `docker/reconstructor/src/reconstructor/colmap.py` because the residual is naturally a per-reconstruction property and the reconstructor already had the (truth-pose, map-pose) pairs in scope; the harness consumes the result via the manifest. Considered alternative B (harness fetches per-image map poses through a new API endpoint and runs Umeyama itself) was rejected as more code, more API surface, and pulling pycolmap into `scripts` for no gain.
   - Runtime impact: none. The reconstruction's absolute frame is unchanged from prior behavior — single-anchor Sim3d still pins the first registered frame's truth pose as the map origin. The diagnostic Umeyama is computed but never applied. Existing maps in MinIO are bit-compatible.
   - `lock-python` was deliberately NOT run for chunk 3 — `scripts` (where numpy/scipy were added) has no Dockerfile, so per-service `pylock.toml` files don't need to change. See [`uv-lockfile-supply-chain-noise.md`](uv-lockfile-supply-chain-noise.md) for why running `lock-python` would have cascaded a bogus docker rebuild and what we'll do when a future chunk forces the issue.
4. ✅ **`fit_calibration.py`** — `scripts/src/scripts/fit_calibration.py` reads one or more `e2e-results.json` files (decoupled mode, option (a) of the resolved prerequisite — the harness already persists `E2EResults` to disk via `model_dump_json`). Pools succeeded localizations, joins map-quality features + `is_indoor` from each row's reconstruction, builds the 11-feature vector per intent doc Algorithm 1 step 5, fits sklearn `LogisticRegression(class_weight='balanced')` + `IsotonicRegression(out_of_bounds='clip')` for tight (5cm/1°) and loose (30cm/5°) success labels, fits Σ_meas (α, β) via `scipy.optimize.minimize` on the 6-D SE(3) residual NLL. Writes the artifact to `config/calibration/global.json` with the operator-supplied `--pipeline-version` baked in. Fit report includes per-capture Procrustes residuals (read off `truth_alignment_*` from chunk 3), Brier scores, reliability bins, sample counts, and a `notes` list capturing degenerate-fit fallbacks. 5 unit tests (`scripts/tests/test_fit_calibration.py`) cover separable-feature accuracy, single-class collapse, artifact-block presence (which exercises the Σ_meas α/β fit end-to-end), artifact round-trip, and the no-usable-rows error path. `pytransform3d` added to `scripts/pyproject.toml` (used by the harness, not the fit script — the harness pre-computes the SE(3) residual via `exponential_coordinates_from_transform` and stores the 6-vector on each row).
   - Schema additions landed in this chunk: `pnp_covariance: list[list[float]]` on `LocalizationMetrics` (raw 6×6 inverse PnP Hessian, surfaced alongside the runtime-applied `measurement_covariance` so the fit can solve α/β; chunk 8 will switch the runtime formula from `PnP_cov / tight²` to `α · PnP_cov + β · I`); `pnp_covariance` / `se3_residual` / `query_image_diagonal_px` on `LocalizationResult`; the 5 map-quality fields on `ReconMetrics`; `is_indoor` on `ReconstructionResult` (fetched via `api.get_reconstruction(id=...)` since it lives on the `reconstructions` table, not the manifest).
   - Two-fields rationale: server keeps applying the calibration formula so the frontend filter stays calibration-agnostic; `pnp_covariance` exists purely for the fit consumer. The alternative — single raw field with frontend-side α/β application — would push calibration math into the Unity client, which we'd rather avoid until there's a reason.
   - sklearn lacks PEP 561 stubs; imports carry `# type: ignore[import-untyped]` per the existing convention for `pycolmap`, `faiss`, `torch` in the localizer.
   - `lock-python` deliberately NOT run (same rationale as chunk 3): `scripts` has no Dockerfile, so per-service `pylock.toml` files don't move; only `uv.lock` is regenerated. The neural-networks-base pylocks would have picked up the documented `upload-time` supply-chain noise; reverted before commit.
5. ✅ **Held-out frames as a first-class `ReconstructionOptions` field.** *(architectural refactor)* The harness used to fork captures (download, modify in memory to drop frames, re-upload as a new capture session) because the reconstructor had no way to skip frames at build time. That ownership of input data was the load-bearing reason `run_e2e.py` ended up with `placeframe-test-captures/` as its source of truth and an `e2e-results.json` intermediate file as its output contract. With the API gap closed, the script refactor (chunk 7) becomes mechanical.
   - `held_out_frame_timestamps: list[int] | None = None` added to `ReconstructionOptions` in `packages/python/core/src/core/reconstruction_options.py`. Type is `list[int]` because `frames.csv` timestamps are Unix milliseconds (`long timestampMilliseconds = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds()` in Unity's `CaptureManager.cs`). **No `reconstructions` table column added** — `ReconstructionOptions` already round-trips through MinIO via `ReconstructionManifest.options` (written at create-time by `docker/api/src/routers/reconstructions.py`, read at run-time by `docker/reconstructor/src/reconstructor/run_reconstruction.py`). The manifest is the single source of truth for what was requested.
   - `docker/reconstructor/src/reconstructor/run_reconstruction.py` builds a `set[int] | None` from `manifest.options.held_out_frame_timestamps` and threads it into each `Rig(...)`. `Rig.__init__` (in `rig.py`) takes the optional `held_out_frame_timestamps: set[int] | None` kwarg and `continue`s on rows whose `int(frame_id)` is in the set, inside the existing `for frame in frames_csv.splitlines()[1:]` loop. The image-list materialization at `run_reconstruction.py` (now ~line 142) drops the held-out images naturally because their poses are no longer in `frame_poses`.
   - `uv run generate-datamodels` produced no diff (no SQL change). `uv run lock-python` regenerated only the documented `upload-time` supply-chain noise on `docker/neural-networks-base/pylock.*.toml`; reverted per chunks 3/4 pattern (no Dockerfile-bearing service grew a dep). `uv run generate-clients --config build/openapi-projects.json --project docker/api` surfaced the field in `docker/api/openapi.json`, the Python API client, and the C# API client.
   - Test: `docker/reconstructor/tests/test_rig.py` resolves the MinIO endpoint from `MINIO_ENDPOINT_URL` or via `docker inspect` of `placeframe-minio-1`, pulls a capture tar live from the captures bucket, instantiates `Rig` with one `held_out_frame_timestamps` value and asserts that timestamp's pose is missing while siblings remain. Skips cleanly if MinIO isn't reachable. Tests aren't in the basedpyright `include` list, so the boto-stub-related type errors are inert (same baseline as the existing localizer test).
   - Landed.
6. ✅ **`localization_evaluations` cache table + API endpoints.** *(architectural refactor)* Localizing a held-out frame against a reconstruction is deterministic given the keyed inputs *plus* `pipeline_version` (the localizer's git SHA, baked into its image) — neural-net forward passes plus pycolmap RANSAC seeded explicitly in chunk 7 (see "Determinism" note there). Persisting evaluation outcomes lets `fit_calibration.py` re-fit cheaply without re-running localizations.
   - Table `localization_evaluations` in `database/24_localization_evaluations.sql`, keyed by `(reconstruction_id, frame_timestamp bigint, retrieval_top_k integer, ransac_threshold double precision, pipeline_version text)`. Value columns: localizer-output features the fit consumes (`inlier_ratio`, `reproj_error_median`, `num_inliers`, `num_correspondences`, `num_matches`, `inlier_coverage`, `pnp_covariance double precision[]` — 6×6 flat row-major, 36 elements; `query_image_diagonal_px`), truth-error labels (`err_t_m`, `err_r_deg`, `se3_residual double precision[]` — length 6), and `succeeded boolean`. CHECK constraints enforce labels-iff-succeeded (`succeeded = (err_t_m IS NOT NULL) AND succeeded = (err_r_deg IS NOT NULL) AND succeeded = (se3_residual IS NOT NULL) AND succeeded = (pnp_covariance IS NOT NULL)`) plus array-length CHECKs for `se3_residual` (=6) and `pnp_covariance` (=36) when present. Tenant-only RLS; no orchestrator bypass; no supplementary indexes (the 5-tuple unique constraint serves `WHERE reconstruction_id = ?` as a prefix scan).
   - **POST upsert via `INSERT ... ON CONFLICT DO UPDATE`** on the unique 5-tuple. Second write with the same key is a refresh, not a conflict — `pipeline_version`-in-key invariant protects against silent overwrites from committed code changes; uncommitted iteration is on the operator. Returns the row (same `id` across upserts).
   - API endpoints in `docker/api/src/routers/localization_evaluations.py`: `POST /reconstructions/{reconstruction_id:uuid}/localization-evaluations` (upsert; rejects path/body id mismatch with 400) and `GET /reconstructions/{reconstruction_id:uuid}/localization-evaluations?pipeline_version=...` (list with optional filter). Mounted alongside existing per-reconstruction sub-resources.
   - **`ARRAY[float](Double(...))` codegen fix in `build/src/build_scripts/placeframe/sqlacodegen_generator.py`.** sqlacodegen renders array columns as `ARRAY(Double(...))`, but `mapped_column(ARRAY(Double(...)))` triggers basedpyright `reportUnknownArgumentType`: `ARRAY[_T]`'s element type can't be inferred from a `_TypeEngineArgument[_T]` whose inner is itself a generic-without-binding. `render_column_type()` now intercepts `ARRAY` columns and emits `ARRAY[<python_type>](<inner>)`, binding the generic explicitly — pyright back-infers the inner type from ARRAY's `_T`. One narrow `cast(TypeEngine[Any], coltype.item_type)` at the seam (item_type is itself typed `TypeEngine[Unknown]`); generated file ships clean. No suppressions added.
   - Codegen pipeline executed: `uv run migrate-database`, `uv run generate-datamodels`, `uv sync --all-packages && uv run lock-python`, `uv run generate-clients --config build/openapi-projects.json --project docker/api`. Surface area: `LocalizationEvaluationCreate` / `LocalizationEvaluationRead` DTOs, `LocalizationEvaluation` SQLAlchemy table, helpers (`localization_evaluation_to_dto`, etc.), Python+C# API client classes for both POST and GET endpoints.
   - **`upload-time` supply-chain noise absorbed.** `lock-python` regenerated `docker/neural-networks-base/pylock.neural-networks-{cpu,cuda,rocm}.toml` with `upload-time = ...,` fields appended to PyTorch's `download-r2.pytorch.org` wheel URLs (PyTorch's index now exposes `data-upload-time`). Hashes/URLs/versions unchanged. Chunks 3/4/5 reverted this noise to avoid the docker-rebuild cascade; chunk 6 takes the cascade once and commits the regenerated locks because preflight's `lock_python(check=True)` step fails on staleness, blocking CI for any subsequent chunk that touches Dockerfile-bearing services. After this commit, future chunks can run `lock-python` cleanly. The cascade rebuilt every service that pulls neural-networks-base; verified all images build and the stack runs through the integration test.
   - Tests: `docker/api/tests/test_localization_evaluations.py` — 6 live HTTP integration tests against the dev stack. Resolves api base URL via `API_BASE_URL` env or `docker inspect placeframe-api-1`; resolves Keycloak via `AUTH_BASE_URL`/`PUBLIC_DOMAIN` env or `.env`-file fallback. Each test allocates a fresh capture session + reconstruction so the FK is satisfied without depending on dev-fixture state (postgres data is wiped by preflight; the test must re-bootstrap from scratch). Coverage: POST returns `LocalizationEvaluationRead` with all label fields populated; same-key POST upserts (id reused, value columns overwritten); different `pipeline_version` creates a distinct row; `pipeline_version` GET filter; failed-evaluation persists with `null` truth labels; path/body id mismatch → 400. Skips cleanly if API/Keycloak unreachable.
   - Landed.
7. ✅ **Script refactor: decouple harness from calibration.** *(NEW — architectural refactor)* With chunks 5 and 6 in place, both scripts collapse to thin orchestrators over backend ids. The chunk's purpose is the disentanglement itself — making the parameter-tuning loop *good* is explicitly out of scope (see "tune_reconstruction quality eval" deferred note below). Landed as **eight commits** (seven planned plus one extra for an additional API endpoint surfaced during execution). Sub-chunks 4–6 below collapsed into a single `Refactor scripts: …` commit because the intermediate states leave `pytransform3d` declared but unused (run_e2e.py was the sole consumer until fit_calibration's rewrite picked it back up); committing those sub-chunks separately would have produced two preflight-red intermediate commits, defeating the "preflight green per commit" property. Codegen artifacts split into their own commit per chunk-6 convention.
   1. **Localizer determinism seed** — `LOCALIZER_RANDOM_SEED = 0` module constant in `docker/localizer/src/localize.py`; `pycolmap._core.set_random_seed(LOCALIZER_RANDOM_SEED); torch.manual_seed(LOCALIZER_RANDOM_SEED)` at the top of `localize_image_against_reconstruction` (per-call, not module-init — guarantees per-localization determinism). Do **not** enable `torch.backends.cudnn.deterministic` or `CUBLAS_WORKSPACE_CONFIG` — those carry a 10–30% latency cost and the residual non-determinism (last-digit drift in conv outputs) is below the discrete inlier-set threshold the fit cares about. The seed change bumps the localizer image's content; the cache key includes `pipeline_version`, so old non-deterministic rows from before this commit don't get pooled with new ones.
   2. **Capture-session API endpoints** for surgical fetch. Three routes: `GET /capture_sessions/{id}/manifest.json` returns the parsed device manifest (`text/json`); `GET /capture_sessions/{id}/frames.csv` returns the truth-pose CSV (`text/csv`); `GET /capture_sessions/{id}/images/{frame_timestamp:int}` returns a single held-out frame (`image/jpeg`). All three share a `_extract_member_bytes` helper that streams the tar (`tarfile` mode `r|*`) so per-call memory is O(member size) rather than O(tar size). **No boto3 direct fetch** in fit_calibration — the API is the single read path. Surgical (per-member) rather than full-tar because `fit-calibration` reads all of `frames.csv` and the manifest but only ~100 of potentially thousands of images per capture. The manifest endpoint was added mid-chunk after fit_calibration's design surfaced the need for camera-config + axis-convention, which the existing dummy `/rig_config` route doesn't provide. Codegen surfaces all three in the API client.
   3. **Localizer `/version` endpoint** wired to the existing `GIT_COMMIT_SHA` build arg. New route `GET /version` on the localizer service returning `{git_sha: str}`. The SHA was already baked into the localizer image at build time via the pre-existing `GIT_COMMIT_SHA` Docker build arg (set in `compose.bake.yml` to `${GIT_COMMIT_SHA:?err}`, populated by `build/src/build_scripts/placeframe/build_docker.py` from `git rev-parse HEAD`); the localizer reads it as `pipeline_version: str = environ["GIT_COMMIT_SHA"]` at startup. Chunk 7 just exposes it via the new route — no new build arg needed. Reason: `pipeline_version` is a code property of the localizer image, not an operator opinion — auto-deriving it tamper-proofs the cache-key contract against operator typos (silent cache pooling across incompatible pipelines is a footgun). `--pipeline-version <str>` on `fit-calibration` becomes an *override* for development workflows where the operator iterates uncommitted changes and wants their cache rows clearly labeled (e.g. `dev-tylerh-2026-05-03`); when omitted, fit-calibration fetches `/version` once at startup via the localizer-client.
   4. **Rename + strip `run_e2e.py` → `tune_reconstruction.py`.** Delete `_prepare_capture`, `WithheldFrame`, all calibration-corpus emission code, and the `placeframe-test-captures/` sibling-directory read path. Keep only the Plackett-Burman cross product over `ReconstructionOptions` cells. Input becomes `--captures <id> [<id>...]` (backend `capture_session_id`s); output is a tuning report keyed on PB cell × map-quality metrics from each cell's reconstruction manifest. Update `scripts/pyproject.toml`: `test-placeframe-e2e = "scripts.run_e2e:app"` → `tune-reconstruction = "scripts.tune_reconstruction:app"`.
      - **Deferred (separate phase): tune_reconstruction quality eval.** The chunk-7 version compares PB cells by *map-quality metrics only* (point count, track length, viewpoint diversity, bounding volume, image count, plus the chunk-3 `truth_alignment_*` residuals). The genuine figure of merit — *localization quality* per cell, measured by held-out localizations — requires running effectively the fit-calibration loop per cell, which is its own multi-hour effort and is not what chunk 7 is about. A top-of-file comment block in `tune_reconstruction.py` calls out the limitation, and the Phase 3 deferred list at the bottom of this Phase records the follow-up: extend `tune_reconstruction.py` (or a sibling) to evaluate held-out-localization aggregate metrics per PB cell once the calibration work itself is done.
   5. **`held_out_selection.py` — pluggable selector with stride starter.** Define `HeldOutFrameSelector` Protocol and `HeldOutSelectionOptions` dataclass with `target_count: int = 100`. Ship one implementation, `StrideHeldOutSelector`: `stride = max(1, len(timestamps) // target_count); selected = timestamps[stride // 2 :: stride]` returning Unix-ms `list[int]`. Invoked by name (default `stride`) so a future `--held-out-selector spatial-bin` lands without touching anything outside this module. **Required big comment block** explaining: (a) the simplest temporal-stride approach is the chosen starter — deterministic, scales to capture length, gives roughly even spatial coverage on smooth capture paths; (b) known limitations — does not protect against connectivity loss (held-out frames may be ones the SfM needed for tracks), does not actively distribute spatially in non-smooth captures, fixed count rather than fraction-of-redundant-frames; (c) ideas for later — post-build filter (drop held-outs the SfM unregistered, augment from registered pool), spatial-bin (voxelize positions and pick one per bin), hybrid stride+voxel, count-as-fraction-of-registered. The architectural shape now (selector behind a name) is the load-bearing piece — adding a new strategy must not require surgery to `fit_calibration.py`'s orchestration loop or the localization-evaluations contract.
   6. **`fit_calibration.py` rewrite as one-shot orchestrator + reconstruction-reuse helper + e2e_results.py deletion + test rewrite.** New CLI: `uv run fit-calibration --captures <id> [<id>...] [--pipeline-version <sha>]`. Modes: `--reconstructions <id>...` (skip selection/build), `--no-fit` (populate cache only). When `--pipeline-version` is omitted, fetch from localizer `/version`.
      - **Stages, in order:**
        1. For each `--captures` id: fetch `frames.csv` via the new API endpoint; run `StrideHeldOutSelector(frames_csv, target_count=100)` → `list[int]` ms timestamps.
        2. For each capture: `match_or_create_reconstruction(api, capture_id, requested_options)`. Lists existing reconstructions, fetches each candidate's manifest.json, reuses iff `manifest.options == requested_options` (full Pydantic equality on the blob, including `held_out_frame_timestamps`). Otherwise `POST /reconstructions` with those exact options and **synchronously poll `GET /reconstructions/{id}/status`** until `succeeded` (5s poll interval, 1800s timeout, raises on `failed`). The "requested options" are `ReconstructionOptions(held_out_frame_timestamps=selected_timestamps)` — server defaults for every other knob. **Required big comment block** in the reuse function explaining: (a) full-blob match is the chosen invariant — calibrations must be fit against one pipeline configuration, mixing recons built with different options into one corpus contaminates the fit; (b) ideas for later — options-hash column on `reconstructions` to skip the manifest fetch, opt-in `--match-options-on=held_out_only` flag for development workflows where the operator knows other options are immaterial.
        3. **Driver-side localization** (not server-side). For each (reconstruction, held-out frame): fetch the frame image via the new `/capture_sessions/{id}/images/{ts}` endpoint, POST to the existing localizer `/localize` endpoint against the reconstruction id, compute `err_t_m`/`err_r_deg`/`se3_residual` against the held-out truth pose from `frames.csv` (same math as the chunk-3 harness), POST to `/reconstructions/{id}/localization-evaluations` (upserts on the chunk-6 5-tuple key). Driver-side keeps the localizer a pure function and avoids server-side filesystem coupling — fit-calibration owns the orchestration; the services stay narrow.
        4. Read corpus rows back via `GET /reconstructions/{id}/localization-evaluations?pipeline_version=<sha>` for each reconstruction; pool; fit (existing `LogisticRegression` + `IsotonicRegression` + Σ_meas α/β code preserved verbatim — operates on `Features` rows, the type-safe seam from chunk 4).
        5. Write `config/calibration/global.json`.
      - Move the corpus-row schema (was `LocalizationResult`/`ReconMetrics`/`ReconstructionResult` in `e2e_results.py`) into `fit_calibration.py` as in-memory types built from API client responses + `localization_evaluations` reads. **Delete `scripts/src/scripts/e2e_results.py`.**
      - **Mock-only tests** in `scripts/tests/test_fit_calibration.py` (no live HTTP). The orchestrator's real-system confidence comes from chunk 9 (single-capture starter run) — that run *is* the integration test, and its output is the artifact we ship. Adding a chunk-6-style live-stack test for the orchestrator costs build-and-stack time on every CI run for marginal extra coverage when chunk 9 follows shortly. Existing 5 fit-math tests become mock-based against API client / `localization_evaluations` payloads (the math is unchanged, so assertions are largely preserved). Sixth test for `StrideHeldOutSelector` (deterministic output for a known timestamp list, mid-stride offset, edge cases for small `target_count`).
   7. **plan.md / intent.md updates** — chunk 7 marked landed; resolved decisions appended to the intent doc; deferred follow-ups recorded in this Phase's deferred list.
   - *Pause point — after this, code is fully decoupled. fit_calibration is a one-shot command. The intent doc's "corpus-gathering spec" reflects the final architecture (no sibling directory; captures live in the backend via the normal upload path).*
8. ✅ **Runtime feature plumbing + Σ_meas decoupling** — build a real `Features` instance from transformed metrics + map quality features and pass it to `apply_global_calibration`; replace `PnP_cov / tight²` with `α · PnP_cov + β · I`; bake `is_indoor` into `ReconstructionManifest` so the localizer reads it via the same manifest path as the 5 map-quality features. Landed as **three commits**: (a) source change adding `is_indoor` to `ReconstructionManifest` and populating it at `POST /reconstructions` from the row; (b) regenerated API clients; (c) localizer-side feature plumbing — `Map` carries the 6 map-side feature values pulled from `manifest.json` at `load_map` time; `_build_features` constructs the runtime `Features` instance from per-query metrics + `Map`; `Σ_meas = α · PnP_cov + β · I` (drops `CONFIDENCE_TIGHT_FLOOR`); 3 new unit tests in `docker/localizer/tests/test_build_metrics.py` (mock-only, mirror the chunk-7 mock-only convention). The `MIN_NUM_INLIERS` / `MIN_INLIER_COVERAGE` band-aid in `localize.py` stays through chunk 8 — its accompanying comment was rewritten so it no longer claims `Features.zeros()` is being passed (chunk 10 removes the band-aid). *Pause point — after this, code is logically complete but not yet servable; next chunk produces the calibration that makes it live.*
   - **Typed seam already landed** (drive-by during chunk 4 review): `core.calibration.Features` Pydantic model with all 11 named float fields and a `Features.zeros()` placeholder; `FEATURE_NAMES` derived from `Features.model_fields` (single source of truth); `apply_global_calibration(features: Features)` signature replaces the prior `dict[str, float]`; load-time `_validate_feature_names` check rejects artifacts whose `logistic_feature_names` don't match `FEATURE_NAMES` (identity-bootstrap empty list still allowed). `build_metrics.py:66` currently passes `Features.zeros()` — the chunk-8 work is to construct a real `Features` at that call site from the transformed metrics + map features. The fit-side row construction in `fit_calibration.py` already builds `Features` instances and derives the numpy row from them, so the fit-time and inference-time feature sets are guaranteed to match by type.
   - **`is_indoor` plumbing**: lives on the `reconstructions` row only today; fit-side reads it via `api.get_reconstruction(id=...)`. Chunk 8 adds it to `ReconstructionManifest` at create-time (in `docker/api/src/routers/reconstructions.py`) so the localizer reads it from the same manifest it already pulls for the 5 map-quality features. This is a write-once path today (no toggle endpoint exists). When a toggle endpoint lands later, that endpoint must re-write `manifest.json` — a single S3 PUT. Mirrors how chunk 5 added `held_out_frame_timestamps` to manifest options.
   - **Per-map loader punted** to land alongside Algorithm 3 (per-map fitting) in Phase 6. The original chunk-8 scope included a lazy MinIO loader for `s3://placeframe-reconstructions/{id}/calibration.json` with global-only fallback. Dropped because: (a) Algorithm 3 (the *fitter* that produces the artifact) is deferred to Phase 6, gated on Phase 5 phone-side correction landing; (b) the loader is dead code with zero exercise until then, and untested-by-real-data code drifts; (c) the "land it now to make Phase 6 mechanical" argument is weak — adding the loader at Phase 6 is one line in `apply_global_calibration` and one line at the localizer's map-load path, so deferring carries no architectural risk. See "Phase 3 deferred follow-ups" entry below.
9. **Run starter** — bring up Docker stack; upload the one capture we have via the normal API path if not already present; `uv run fit-calibration --captures <id> --pipeline-version <sha>`; inspect fit report; commit `config/calibration/global.json` with known-bad-starter header.
10. **Band-aid removal + `TIGHT_MIN`** — pick `TIGHT_MIN` from starter fit's success-cluster distribution; remove `IDENTITY_BOOTSTRAP_SENTINEL`, `MIN_NUM_INLIERS`/`MIN_INLIER_COVERAGE`, hand-set `-4.595` intercept, `CONFIDENCE_TIGHT_FLOOR`; run `uv run --no-sync preflight` to confirm CI-clean.

**Phase 3 deferred follow-ups** (out of scope for this Phase; landing later phases):

- **`tune_reconstruction.py` localization-quality eval per PB cell.** The chunk-7 version compares cells by map-quality metrics only. The genuine figure of merit — *localization quality* per cell — requires running held-out localizations per cell, effectively a per-cell fit-calibration loop. Punted because chunk 7's purpose is the disentanglement, and the parameter-tuning loop quality is downstream of the calibration work itself being correct. Lands as its own effort after Phases 3 and 8 close out.
- **Multi-capture corpus run + production calibration.** Replaces the single-capture starter shipped at the end of Phase 3. The corpus-gathering spec in [`e2e-and-calibration-intent.md`](e2e-and-calibration-intent.md) is the executable spec.
- **Frontend-filter retune** (`BaseProcessNoise{Translation,Rotation}VariancePerTick`, `SnapThresholdSigmas`) against the production calibration's Σ_meas. Single-capture starter is too unreliable to drive meaningful retune.
- **Per-map calibration loader** — lazy MinIO fetch of `{id}/calibration.json` with global-only fallback, plus the `apply_global_calibration` second-isotonic stack-up. Lands together with Algorithm 3 (per-map fitting) in Phase 6 — there's no per-map artifact to read until the fitter exists, and bundling the two avoids landing dead code that drifts without exercise.

### Phase 2d — Semantic-segmentation masking (3-day time-box)

Originally bundled ahead of Phase 3 to avoid a calibration refit; reordered to land *after* Phase 3 because Phase 3's logic doesn't depend on whether masking is in place — only the metric distribution shifts. One offline refit when masking lands is the entire cost of the reorder.

OneFormer (MIT) loaded once at service startup, run right after `transform_image()`, mask applied in image space before feature extraction.

- Reconstructor: OneFormer-Swin-L (one-time cost at map build).
- Localizer: OneFormer-Swin-T (~100–200ms GPU; tolerable for 1Hz queries).
- Hard-coded COCO transient class list: `person, bicycle, car, motorcycle, bus, train, truck, boat, traffic light, bird, cat, dog, horse, sheep, cow`.
- Fallback when masked image has fewer than `MIN_KEYPOINTS_AFTER_MASK` keypoints (default 50): retry without mask, log.
- After landing, re-run `fit_calibration.py` (Phase 3 Algorithm 1) against the new pipeline_version. Commit the refit `config/calibration/global.json`. ZED-only data is sufficient for this refit; the Phase-5 phone correction is unaffected.

**Time-box rule**: if Day 4 is spent on environment, dependency, or model-loading wrestling, Phase 2d defers to a post-Phase-6 follow-up. The cost of deferral is one *additional* future calibration refit when masking later lands.

End of Phase 2d: transient scene content suppressed from features in both pipelines; calibration refit against the masked pipeline.

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

- **Phase 1 ships before calibration exists.** Phase 1's measurement weighting uses heuristic Σ_meas scaling. When the production multi-capture calibration lands (post-Phase-3, after the corpus run), those tunables (snap threshold, process noise) will need re-tuning. Tuning rework, not architectural rework.
- **Phase 1 math lives inline in Unity and is tested via Unity Test Framework.** SE(3) and Bayesian-filter math sit alongside the Unity runtime in `packages/unity/Placeframe/Assets/Package/Core/Runtime/`; tests are an Editor-only asmdef next to it.
- **Phase 2a blocked all subsequent VPS phases.** It would have been possible to ship calibration (Phase 3) on top of fully-untested math, but Phases 3–6 reference the math to interpret confidence-weighted measurements, and the test coverage cheaply catches regressions there.
- **Phase 2e merged into Phase 3.** Originally separate ("repair harness, run sweep, pick reconstruction defaults" → "fit calibration against the picked defaults"). Discovery during planning: the harness *is* the calibration data-generation engine — the sweep cells are the calibration training rows. Algorithm 1's held-out tar machinery is exactly what `_prepare_capture` already implements. Maintaining them as separate phases would have meant duplicating the upload+reconstruct+localize loop across two scripts. The fused intent file ([`e2e-and-calibration-intent.md`](e2e-and-calibration-intent.md)) owns both.
- **Phase 3's harness was originally architected wrong; chunks 5–7 correct it.** The original Phase 3 design treated the e2e harness as the data-store-and-orchestrator for calibration: it read capture tars from a sibling `placeframe-test-captures/` directory, modified them in memory to withhold frames, re-uploaded as new capture sessions, ran reconstructions, ran localizations, and persisted everything to a sidecar `e2e-results.json` file that `fit_calibration.py` read separately. The load-bearing reason was a single API gap — the reconstructor had no way to build a map "excluding these frames," so the harness invented the modify-and-reupload workaround. Once the harness owned tar surgery, it grew to also own input source, output schema, and provenance bundling — drift that wasn't forced by the API gap. The corrective refactor (chunks 5–7) makes held-out frames a first-class `ReconstructionOptions` field (no schema change — the field rides the existing `ReconstructionManifest.options` round-trip through MinIO), adds a `localization_evaluations` cache table keyed on `(reconstruction_id, frame_timestamp, retrieval_top_k, ransac_threshold, pipeline_version)`, and collapses both scripts to thin orchestrators over backend ids. Cost: one Pydantic field + reconstructor filter (chunk 5), one new SQL table + two API endpoints (chunk 6), plus a ~1-day script rewrite (chunk 7). Reward: one source of truth (the database), no parallel data store, no inter-script JSON contract, no `e2e_results.py` module, and the corpus-gathering spec becomes "upload N captures via the normal API path" instead of "place tars in a sibling directory." Resolved decision #3 in the intent file (held-out frames stay in the harness) is reversed; the rest of Phase 3 (chunks 8–10) is unaffected.
- **Phase 3 ships a single-capture starter calibration, not a production one.** Running `fit_calibration.py` against one capture produces a calibration that overfits to that scene. We commit it anyway (with a "known-bad starter, not production" header) because doing so unblocks band-aid removal and lets the system run on real (varying) confidence — overfit is still better than constant-pinned-at-0.01. The production calibration depends on the multi-capture corpus run. Cost of this choice: the system will feel rougher than identity-bootstrap until the corpus run, because the frontend filter constants are tuned against the heuristic Σ_meas and the starter's α/β shifts that floor.
- **Phases 2b/2c/2c-fixup bundle ahead of Phase 3; Phase 2d does not.** Originally all of 2b–2e bundled ahead of Phase 3 to fit calibration once. 2d (masking) was reordered to land after Phase 3 because (a) the band-aids are real friction during ongoing testing, (b) calibration logic is unchanged with or without masking — only the metric distribution shifts, so the cost is one offline refit on already-collected data with no new data-acquisition cycle, and (c) lived experience with calibrated confidence informs masking tuning. 2b/2c/2c-fixup still bundle ahead because they were already done before this reorder.
- **Phase 2d is time-boxed and deferrable.** Masking is the largest scope and the most likely to overrun. The 3-day budget plus a hard defer-to-post-Phase-6 fallback bounds the delay. Deferral cost is one *additional* future refit on top of the one accepted by the reorder.
- **Phase 4 lands after Phase 3, not before.** A previous iteration of this plan put the dogfooding logger before ZED calibration to compress passive-accumulation wall-clock. Pre-go-to-market that compression is illusory: with a small known user pool, phone-side data is gathered in directed sessions, not passively. Building the logger after Phase 3 also means its schema and feature set can be informed by Phase 3's lived experience, reducing rework risk.
- **Phase 6 fitting code and loader both deferred.** Originally only the fitting code (Algorithm 3) was deferred and the runtime loader landed in Phase 3; revised during chunk 8 to defer both together. Reasoning: the loader is dead code with no exercise until the fitter exists, and untested-by-real-data scaffolding drifts. Bundling them when the fitter lands costs one line in `apply_global_calibration` and one line at the localizer's map-load path — no architectural risk in deferring. Risk: when Phase 6 lands, slightly more novel work delays per-map calibration for the first map by maybe a day. Reward: avoids speculative scaffolding that may never run.
- **`pipeline_version` is the git SHA, not a selective hash.** Every commit invalidates calibration. We don't yet know which inputs actually shift the metric distribution; once Phase 3 is in production and we have evidence, this can become a selective hash. False-positive refit cost doesn't bite until Phase 3 anyway.
- **Pipeline-tuning constants live as module-level Python constants in the localizer, not env vars.** `RANSAC_THRESHOLD`, `RETRIEVAL_TOP_K`, and similar per-pipeline knobs are baked into the image so changing them requires a code change and bumps `pipeline_version` (the localizer's git SHA), automatically invalidating calibration. Env vars would silently bypass that invariant. Implication: tuning these at deploy time isn't possible — that's the intended cost.
- **`transform_image()` does work the name doesn't telegraph (resize + discard pixels).** Currently lives because the function predates the resize semantics. Not corrected at Phase 2c landing time; Phase 2c-fixup is the natural place to rename to a paired pair (`prepare_image_for_extraction` / `prepare_image_for_retrieval`) since both functions land alongside each other in that phase.
- **Phase 2c was scoped wrong.** Cross-aspect mismatch was treated as one problem with one preprocessing fix; it's actually two distinct problems (scale for local features vs framing for retrieval) requiring different fixes (resize vs tile). Phase 2c-fixup is the corrective step. The local-feature half (shorter-side resize + intrinsics) landed correctly under 2c and stays. The retrieval half (in-DIR letterbox with mean padding) is reverted in 2c-fixup and replaced with square-tile aggregation — the technique originally listed as a non-goal in `feature-pipeline-intent.md` but promoted to the actually-correct fix once the framing-vs-shape distinction was understood. Cost of the misstep: one extra commit on the branch and a brief design tangent; no production impact since calibration is still identity.

## Open investigations

Threads that aren't a phase but are tracked so they're not forgotten.

### ~~LightGlue per-query latency~~ — concluded

Shipped `LightGlue(features="aliked", width_confidence=-1, depth_confidence=0.95, mp=True)`. Matching latency dropped from ~250 ms to ~140 ms median (29-query sweep). The durable record — flag rationale, batching footgun, V3 alternative tested and rejected on both services, pattern of when V3 might become correct again — lives in the comment on `load_lightglue` in `packages/python/neural-networks/src/neural_networks/models.py`. Paper-trail numbers below.

**Localizer per-variant** (single query, 10 calls each, deterministic per cell):

| Variant | matching ms (median) | num_matches | total ms |
|---|---|---|---|
| Baseline (w=-1, d=-1) | 266 | 20,541 | 840 |
| V1 (w=-1, d=0.95) | 248 | 20,551 | 825 |
| **V2 shipped** (w=-1, d=0.95, mp=True) | **160** | 20,536 | **740** |
| V3 rejected (batch=1, w=0.99, d=0.95, mp=True) | 152 | 20,662 | 711 |

**Reconstructor V3 vs V2** (same capture, 3,304 pairs):

| Variant | matching wall time | per-pair |
|---|---|---|
| V2 (batched B=16) | 27.9 s | 8.4 ms |
| V3 (un-batched B=1) | 33.4 s | 10.1 ms |

**Tier 1 localizer sweep** (29 paired queries across the same map): V3 wins 10/29, loses 18/29, ties 1. Mean V3−V2 matching delta: **+8 ms slower**. The original single-query V3 win was a sampling artifact — V3 wins on hard queries (V2 >170 ms) and loses on easy ones (V2 <130 ms); most queries are easy. V2 picked everywhere; the `perf_counter` line in `run_reconstruction.py` stays as reconstructor observability.

### Reconstructor pose-inversion idiom — drive-by cleanup

Three sites in the reconstructor hand-roll `world_from_X = X_from_world⁻¹` as `rot.matrix().T` plus `-rot.T @ trans` instead of using `pycolmap.Rigid3d.inverse()` (which exists, returns the inverted `Rigid3d`):

- `docker/reconstructor/src/reconstructor/colmap.py:178` — Umeyama diagnostic, `rig_from_world` → camera center (added in chunk 3 of Phase 3).
- `docker/reconstructor/src/reconstructor/colmap.py:218–219` — `rig_from_world` → `world_from_rig` for the npz writer.
- `docker/reconstructor/src/reconstructor/metrics_builder.py:145–150` — `rig_from_world` → viewing-direction column for `map_viewpoint_diversity`.

Pattern surfaced during the chunk 4 audit. Same fix at all three sites — assign `world_from_X = X_from_world.inverse()` once and read `.rotation.matrix()` / `.translation` off it. No behavior change, reads as "obviously the inverse." Do as a single drive-by commit after the rest of Phase 3's calibration work lands (chunks 5–7); deliberately not bundled with chunk 4 to keep that commit's diff focused on calibration.

The harness has the same idiom at `scripts/run_e2e.py` (`_localize_and_label`) but operates on numpy rotation/translation rather than `Rigid3d`, so the equivalent fix would be a `pytransform3d.invert_transform` 4×4 round-trip — neutral on line count and not worth folding in. After Phase 3 chunk 7 the harness rewrite supersedes this either way (the `_localize_and_label` body lands inside `fit_calibration.py`); leave as-is.

## Scaffolding inventory

Placeholders deliberately left by earlier phases, with the trigger for replacement. Line numbers approximate; resolve by symbol if drifted.

- `docker/localizer/src/build_metrics.py` — `apply_global_calibration(calibration, features=Features.zeros())` zero-valued `Features` placeholder. Replaced with a real `Features` instance built from transformed metrics + map quality features in Phase 3 chunk 8. Same file: `Σ_meas = PnP_cov / tight²` band-aid replaced by `Σ_meas = α · PnP_cov + β · I` reading α/β from the calibration artifact (Phase 3 chunk 8); `CONFIDENCE_TIGHT_FLOOR` removed.
- `config/calibration/global.json` — identity calibration: empty logistic weights, intercept-only, identity isotonic, `pipeline_version: "identity-bootstrap"`. The `tight.logistic.intercept` was tweaked from `0.0` to `-4.59511985013459` (so `sigmoid → 0.01`) as a band-aid to give the `Σ_meas / tight²` formula sensible 10000× covariance inflation. Replaced in Phase 3 chunk 9 by output of `scripts/fit_calibration.py` run on the one existing capture — known-bad single-capture starter calibration, not production. Production calibration replaces the starter after the multi-capture corpus run.
- `docker/localizer/src/localize.py` — `MIN_NUM_INLIERS = 50` / `MIN_INLIER_COVERAGE = 0.15` raw quality floor band-aid. Rejects garbage localizations that the broken confidence stub can't filter. Replaced in Phase 3 chunk 10 by `if metrics.confidence.tight < TIGHT_MIN: raise LocalizationError(...)`; `TIGHT_MIN` picked from the starter fit's success-cluster distribution.
- `packages/python/core/src/core/calibration.py` — `IDENTITY_BOOTSTRAP_SENTINEL` and the equality-check skip in `load_global_calibration`. Both removed in Phase 3 chunk 10 once the starter calibration ships.
- `scripts/src/scripts/run_e2e.py` — currently dual-purpose (PB sweep + calibration corpus generation) and reads from a sibling `placeframe-test-captures/` directory, doing tar surgery to withhold frames before re-uploading. Renamed to `tune_reconstruction.py` and stripped to PB-sweep-only in Phase 3 chunk 7; takes backend capture ids as input.
- `scripts/src/scripts/e2e_results.py` — Pydantic schema (`E2EResults` / `LocalizationResult` / `ReconstructionResult` / `ReconMetrics`) bridging harness output to fit input via an on-disk `e2e-results.json` file. Deleted in Phase 3 chunk 7; corpus rows become in-memory types built from API client responses + `localization_evaluations` reads.
- ~~VPS frontend lacks σ_posterior floor / per-tick process noise. Filter locks in after ~30 stationary measurements.~~ Shipped early as a per-tick base process noise term in `RelocalizationFilter.ProcessNoise()` — `BaseProcessNoise{Translation,Rotation}VariancePerTick` added unconditionally. Numbers (1e-4 m², 1e-6 rad²) are coarse and will be re-tuned against fitted Σ_meas after the multi-capture corpus run; the Phase 3 starter calibration is too unreliable to drive meaningful re-tuning.
- Phase 1 inline math in `packages/unity/Placeframe/Assets/Package/Core/Runtime/` (SE(3) Log/Exp, 6×6 covariance algebra, `RelocalizationFilter`) stays here permanently. Tested in-place via Unity Test Framework in Phase 2a.
