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
| 3 | End-to-end testing and calibration (code + single-capture starter; multi-capture corpus deferred) | E2E+calibration | Not started |
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

Phase 3 lands code completion *plus* a single-capture starter calibration. The harness is repaired, `fit_calibration.py` lands, the schema migrates, runtime loader plumbs features and the decoupled Σ_meas formula. The harness then runs in `--single-config` mode against the one capture we have today; `fit_calibration.py` produces a known-bad-but-real `global.json`; the `IDENTITY_BOOTSTRAP_SENTINEL`, `MIN_NUM_INLIERS`, `MIN_INLIER_COVERAGE`, and `-4.595` band-aids are removed in the same close. **The multi-capture corpus is not gathered, the full ~15-hour parameter sweep is not run, and the production calibration is not produced this phase.** A standalone deliverable of Phase 3 is the corpus-gathering spec in the intent file, ready to execute when the operator goes to assemble the multi-capture corpus and run the production fit.

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

- Run `test-placeframe-e2e` (or manual smoke if the harness is broken — Phase 3 backlog) against the post-prototype pipeline. Confirm reconstruction completes and localization produces a non-degenerate pose.
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

- Repair `scripts/src/scripts/test_placeframe_e2e.py` (S608, ASYNC240, broken `main()`, `basedpyright` clean).
- Add a `--single-config` flag to the harness (server-default recon + loc, skips the cross product).
- Extend the harness with a pose-error-labeling step (Procrustes-align `frames.csv` truth to rebuilt COLMAP map; record `err_t`, `err_r` per held-out frame).
- Add map-quality columns to the `reconstructions` table (`map_image_count`, `map_point_count`, `map_avg_track_length`, `map_bounding_volume_m3`, `map_viewpoint_diversity`, `is_indoor`); reconstructor populates them at map-build time; migration backfills; harness joins via `localization_maps.reconstruction_id`.
- Create `scripts/src/scripts/fit_calibration.py` implementing Algorithm 1 (ZED held-out logistic + isotonic fit + Σ_meas α/β scalar fit, with reporting).
- Plumb features through `apply_global_calibration` (replace `features={}` in `build_metrics.py:66`).
- Decouple Σ_meas from confidence in `build_metrics.py`: replace `PnP_cov / tight²` with `α · PnP_cov + β · I` (α, β read from artifact). Confidence becomes a gate via `if metrics.confidence.tight < TIGHT_MIN: raise LocalizationError(...)` in `localize.py`.
- Implement the per-map calibration loader path (lazy MinIO fetch + cache, soft-fall-back to global-only). Per-map fitting (Algorithm 3) is *not* implemented; deferred to Phase 6.

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

1. **Harness repair** — fix S608 / ASYNC240 / broken `main()`; add `--single-config` flag.
2. **Schema + reconstructor map-quality features** — 6 columns on `reconstructions`; reconstructor populates them at map-build time (`scipy.spatial.ConvexHull` for volume); migration backfills; harness joins via `localization_maps.reconstruction_id`. Runs the full regen pipeline (`migrate-database` → `generate-datamodels` → `lock-python` → `generate-clients`).
3. **Procrustes pose-error labeling** — Umeyama via pycolmap `Sim3d` primitives; SE(3) residuals via `pytransform3d`; per-capture residual surfacing; persist labeled rows.
4. **`fit_calibration.py`** — pool rows; sklearn logistic + isotonic; `scipy.optimize.minimize` for α/β; Brier + calibration_curve report; artifact write; unit tests (Procrustes solve, α/β solve, round-trip).
5. **Runtime feature plumbing + Σ_meas decoupling + per-map loader** — replace `features={}` with real feature dict; replace `PnP_cov / tight²` with `α · PnP_cov + β · I`; lazy MinIO per-map loader with global-only fallback. *Pause point — after this, code is logically complete but not yet servable; next chunk produces the calibration that makes it live.*
6. **Run starter** — bring up Docker stack; `uv run test-placeframe-e2e --single-config`; `uv run fit-calibration`; inspect fit report; commit `config/calibration/global.json` with known-bad-starter header.
7. **Band-aid removal + `TIGHT_MIN`** — pick `TIGHT_MIN` from starter fit's success-cluster distribution; remove `IDENTITY_BOOTSTRAP_SENTINEL`, `MIN_NUM_INLIERS`/`MIN_INLIER_COVERAGE`, hand-set `-4.595` intercept, `CONFIDENCE_TIGHT_FLOOR`; run `uv run --no-sync preflight` to confirm CI-clean.

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
- **Phase 3 ships a single-capture starter calibration, not a production one.** Running `fit_calibration.py` against one capture produces a calibration that overfits to that scene. We commit it anyway (with a "known-bad starter, not production" header) because doing so unblocks band-aid removal and lets the system run on real (varying) confidence — overfit is still better than constant-pinned-at-0.01. The production calibration depends on the multi-capture corpus run. Cost of this choice: the system will feel rougher than identity-bootstrap until the corpus run, because the frontend filter constants are tuned against the heuristic Σ_meas and the starter's α/β shifts that floor.
- **Phases 2b/2c/2c-fixup bundle ahead of Phase 3; Phase 2d does not.** Originally all of 2b–2e bundled ahead of Phase 3 to fit calibration once. 2d (masking) was reordered to land after Phase 3 because (a) the band-aids are real friction during ongoing testing, (b) calibration logic is unchanged with or without masking — only the metric distribution shifts, so the cost is one offline refit on already-collected data with no new data-acquisition cycle, and (c) lived experience with calibrated confidence informs masking tuning. 2b/2c/2c-fixup still bundle ahead because they were already done before this reorder.
- **Phase 2d is time-boxed and deferrable.** Masking is the largest scope and the most likely to overrun. The 3-day budget plus a hard defer-to-post-Phase-6 fallback bounds the delay. Deferral cost is one *additional* future refit on top of the one accepted by the reorder.
- **Phase 4 lands after Phase 3, not before.** A previous iteration of this plan put the dogfooding logger before ZED calibration to compress passive-accumulation wall-clock. Pre-go-to-market that compression is illusory: with a small known user pool, phone-side data is gathered in directed sessions, not passively. Building the logger after Phase 3 also means its schema and feature set can be informed by Phase 3's lived experience, reducing rework risk.
- **Phase 6 fitting code is deferred.** The loader is in place from Phase 3, but writing the per-map fitting code is held back until at least one map clears the sample threshold. Risk: when that day comes, the fitting code is novel work that delays per-map calibration for that first map by a few days. Reward: avoids speculative code that may never run.
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

## Scaffolding inventory

Placeholders deliberately left by earlier phases, with the trigger for replacement. Line numbers approximate; resolve by symbol if drifted.

- `docker/localizer/src/build_metrics.py` — `apply_global_calibration(calibration, features={})` empty features dict. Plumbed through with transformed metrics + map quality features in Phase 3 (code deliverable). Same file: `Σ_meas = PnP_cov / tight²` band-aid replaced by `Σ_meas = α · PnP_cov + β · I` reading α/β from the calibration artifact (Phase 3); `CONFIDENCE_TIGHT_FLOOR` removed.
- `config/calibration/global.json` — identity calibration: empty logistic weights, intercept-only, identity isotonic, `pipeline_version: "identity-bootstrap"`. The `tight.logistic.intercept` was tweaked from `0.0` to `-4.59511985013459` (so `sigmoid → 0.01`) as a band-aid to give the `Σ_meas / tight²` formula sensible 10000× covariance inflation. Replaced in Phase 3 by output of `scripts/fit_calibration.py` run on the one existing capture in `--single-config` mode — known-bad single-capture starter calibration, not production. Production calibration replaces the starter after the multi-capture corpus run.
- `docker/localizer/src/localize.py` — `MIN_NUM_INLIERS = 50` / `MIN_INLIER_COVERAGE = 0.15` raw quality floor band-aid. Rejects garbage localizations that the broken confidence stub can't filter. Replaced in Phase 3 by `if metrics.confidence.tight < TIGHT_MIN: raise LocalizationError(...)`; `TIGHT_MIN` picked from the starter fit's success-cluster distribution.
- `docker/localizer/src/calibration.py:56` — `IDENTITY_BOOTSTRAP_SENTINEL` and the equality-check skip in `load_global_calibration`. Both removed in Phase 3 once the starter calibration ships.
- ~~VPS frontend lacks σ_posterior floor / per-tick process noise. Filter locks in after ~30 stationary measurements.~~ Shipped early as a per-tick base process noise term in `RelocalizationFilter.ProcessNoise()` — `BaseProcessNoise{Translation,Rotation}VariancePerTick` added unconditionally. Numbers (1e-4 m², 1e-6 rad²) are coarse and will be re-tuned against fitted Σ_meas after the multi-capture corpus run; the Phase 3 starter calibration is too unreliable to drive meaningful re-tuning.
- Phase 1 inline math in `packages/unity/Placeframe/Assets/Package/Core/Runtime/` (SE(3) Log/Exp, 6×6 covariance algebra, `RelocalizationFilter`) stays here permanently. Tested in-place via Unity Test Framework in Phase 2a.
