# End-to-end testing and calibration — Intent

> Execution and progress tracked in [`plan.md`](plan.md).
> This initiative fuses two previously-separate efforts: the parameter-sweep harness (originally `test-placeframe-e2e.md`, deleted in `c84375ea`, recoverable from git history) and the VPS calibration design (originally Phase 3 of `vps-redesign-intent.md`).

## Status

Code-complete plus a single-capture starter calibration. **The full multi-capture corpus and the ~15-hour parameter sweep are explicitly out of scope for this effort.**

The goal of this initiative is twofold:

1. Land code that is logically correct end-to-end so that, when the multi-capture corpus is later assembled, the existing code path produces a production calibration without further engineering work blocking the run.
2. Run that code path against the one capture we already have to produce a *known-bad-but-real* starter calibration. That starter calibration unblocks band-aid removal (`IDENTITY_BOOTSTRAP_SENTINEL`, `MIN_NUM_INLIERS`, `MIN_INLIER_COVERAGE`, hand-set `-4.595` intercept) and lets the system run on real fitted confidence — overfit and unreliable, but real — until the corpus run replaces it.

The initiative also produces, as a deliverable, an unambiguous corpus-gathering spec for future-operator-self.

**Architectural correction in flight (chunks 5–7 of plan.md).** Chunks 1–4 landed the harness repair, map-quality metrics, pose-error labeling, and `fit_calibration.py`. After chunk 4, an audit surfaced that the harness was architected to own the calibration pipeline's input data (a sibling `placeframe-test-captures/` directory), output schema (`e2e-results.json`), and provenance bundling — drift driven by a single API gap (no way to build a reconstruction with frames excluded, so the harness invented a modify-and-reupload-the-tar workaround). Chunk 5 has now closed the API gap (held-out frames are a first-class `ReconstructionOptions` field, filtered by the reconstructor at the `frames.csv` parse boundary). Chunks 6–7 collapse both scripts to thin orchestrators over backend ids: `run_e2e.py` → `tune_reconstruction.py` (PB sweep only); `fit_calibration.py` becomes a one-shot end-to-end command driven by `--captures <id>` or `--reconstructions <id>`. See "Why these are one effort" and "Architecture" below — both have been rewritten for the post-refactor design.

The current state is a half-state:
- The calibration runtime loader has a hand-set band-aid intercept (`-4.595`) and a never-removed `IDENTITY_BOOTSTRAP_SENTINEL` skip path.
- `apply_global_calibration` is called with `Features.zeros()` because no real features are plumbed (the typed `Features` seam landed but the placeholder passes zero-valued features).
- `localize.py` carries a raw-metric quality floor (`MIN_NUM_INLIERS=50`, `MIN_INLIER_COVERAGE=0.15`) as a band-aid for the constant-confidence stub.
- `Σ_meas = PnP_cov / tight²` conflates "geometric uncertainty" with "trustworthiness" — works only because `tight` is pinned at 0.01.
- The harness/fit boundary is wrong-architected (see above).

This initiative climbs out of all of that.

## Why these are one effort

The discovery that drove fusion of Phase 2e and Phase 3: the e2e harness is the calibration data-generation pipeline. The two are the same workflow with overlapping needs.

- Algorithm 1 of the calibration design (ZED held-out fitting) requires a corpus of capture sessions, each rebuilt with ~10% of frames withheld, the held-out frames localized against the rebuilt map, and `(metrics, pose_error)` rows pooled into a fit.
- The PB recon-options sweep produces `(metrics, recon_config)` cells across the same captures. Run with held-out frames and pose-error labels, those cells *are* the calibration training rows.
- The harness already runs cross-device localization (e.g. phone-frame against ZED-built map). Algorithm 2's phone-side data is one column of the same matrix.

The original plan separated Phase 2e ("repair harness, run sweep, pick reconstruction defaults") and Phase 3 ("fit calibration against the picked defaults") as if they were sequential and independent. They aren't — the sweep cells are the calibration training rows. The sweep gives a richer training set (multiple recon configs × multiple loc configs × multiple captures); the calibration fits across all of them; the sweep can rank parameter choices using fitted confidence as one of its metrics.

**Clarification on what "one effort" means after the chunk-5–7 refactor.** Fusing the two efforts does *not* mean fusing the two scripts. The first iteration (chunks 1–4) put both the PB sweep and the calibration-corpus generation inside one script (`run_e2e.py`) that owned input data, ran reconstructions, ran localizations, labeled pose errors, and wrote a sidecar JSON file that `fit_calibration.py` read separately. That collapsed two roles into one Python file and ended up with bad coupling. The chunk-5–7 refactor splits responsibilities cleanly: held-out-frame labeling becomes a first-class backend capability (`ReconstructionOptions.held_out_frame_timestamps` + a `localization_evaluations` cache table); `tune_reconstruction.py` does *only* the PB sweep over backend captures and emits a tuning report; `fit_calibration.py` does *only* corpus assembly + fit, also driven by backend ids. They share infrastructure (the held-out-frames API, the localization-evaluations table) but no code path or intermediate file.

## What this initiative produces

**Code deliverables:**

1. ✅ Repair `scripts/src/scripts/test_placeframe_e2e.py`: S608 / ASYNC240 / broken `main()` were already addressed in `dddeca1d`; chunk 1 added the `--single-config` flag (deliverable 2) and confirmed basedpyright clean.
2. ✅ Add a `--single-config` flag to the harness: short-circuits Phase 4 to `[None]` (server-default recon config) and replaces the `LOC_RETRIEVAL_TOP_K` × `LOC_RANSAC_THRESHOLD` cross product with `[(None, None)]`. Used for fast iteration and for incremental refits.
3. ✅ Pose-error labeling. The diagnostic lives in the **reconstructor**, not the harness. The reconstruction's truth-frame alignment is still the prior single-anchor `Sim3d` in `colmap.py` (preserves the "first registered frame == map origin" contract downstream consumers rely on); rigid Umeyama (closed-form Kabsch via numpy SVD) is computed *separately* over all registered frames as a per-capture diagnostic and the residual is emitted on `ReconstructionMetrics` as `truth_alignment_rms_residual_m` / `truth_alignment_max_residual_m`. The Umeyama transform itself is not applied to the reconstruction. Per-capture residuals ride the manifest. Harness captures held-out frame truth poses in `_prepare_capture` and computes `err_t_m` / `err_r_deg` per localization in Phase 6 by inverting the localizer's `camera_from_map` Transform. `pytransform3d` not added — `scipy.spatial.transform.Rotation.magnitude()` covers the rotation-error need.
4. ✅ Map-quality features: `map_image_count`, `map_point_count`, `map_avg_track_length`, `map_bounding_volume_m3`, `map_viewpoint_diversity`. Folded into `ReconstructionMetrics` (single concept; same plumbing as existing track-length and reprojection-error fields). Reconstructor computes them inside `build_reconstruction_metrics` at map-build time and writes them to `manifest.json` in MinIO alongside the rest of the metrics block. Harness fetches the manifest per reconstruction at row-emission time. The user-controlled `is_indoor` boolean lives as a column on `reconstructions` (default false) since it isn't a reconstruction output.
5. ✅ Create `scripts/src/scripts/fit_calibration.py`: reads one or more `e2e-results.json` files (each is a serialized `E2EResults`), pools succeeded localizations, joins map-quality features + `is_indoor` per reconstruction, builds the 11-feature vector, fits sklearn `LogisticRegression(class_weight='balanced')` + `IsotonicRegression(out_of_bounds='clip')` for tight (5cm/1°) and loose (30cm/5°) labels, fits Σ_meas (α, β) via `scipy.optimize.minimize` on the 6-D SE(3) residual NLL. Writes the artifact to `config/calibration/global.json` with `--pipeline-version` baked in. Fit report (printed + serialized in `fit_metadata.validation`) includes per-capture Procrustes residuals (`truth_alignment_*` from chunk 3's reconstructor diagnostic), Brier scores for tight/loose, reliability bins, sample counts, and a `notes` list capturing degenerate-fit fallbacks. To fit α/β, `LocalizationMetrics` now exposes `pnp_covariance` (raw 6×6 inverse PnP Hessian) alongside `measurement_covariance` (runtime-applied Σ_meas) — two fields by design so the frontend filter stays calibration-agnostic and the fit consumer gets the raw input. Pose-error labeling: the harness already computes `err_t_m`/`err_r_deg`; chunk 4 added `se3_residual` (6-vector via `pytransform3d.transformations.exponential_coordinates_from_transform`) and `query_image_diagonal_px` to each row. 5 unit tests cover separable-feature accuracy, single-class collapse, artifact-block presence (which exercises the Σ_meas α/β fit end-to-end on synthetic 6-D residuals), artifact round-trip, no-usable-rows error path.
6. ✅ **Held-out frames as a first-class `ReconstructionOptions` field** *(architectural correction; plan.md chunk 5)*. `held_out_frame_timestamps: list[int] | None = None` added to `ReconstructionOptions` in `packages/python/core/src/core/reconstruction_options.py`. Type is `list[int]` (Unix milliseconds, matching the `long timestampMilliseconds` produced by Unity's `CaptureManager.cs`). **No `reconstructions` table column** — `ReconstructionOptions` is already round-tripped through MinIO inside `ReconstructionManifest.options`, so the manifest already carries the held-out set without additional schema. The reconstructor (`run_reconstruction.py`) builds a `set[int] | None` from `manifest.options.held_out_frame_timestamps` and threads it into `Rig.__init__`, which `continue`s on rows whose `int(frame_id)` is in the set inside the existing `frames.csv` loop in `rig.py`. The image-list materialization further down `run_reconstruction.py` drops the held-out images naturally because their poses are no longer in `frame_poses`. Reverses resolved decision #3 ("Held-out frames stay implemented as harness-side tar surgery"): the harness no longer modifies tars; the API does the right thing through the existing manifest path.
7. ✅ **`localization_evaluations` cache table + API endpoints** *(architectural correction; plan.md chunk 6)*. Table keyed by `(reconstruction_id, frame_timestamp bigint, retrieval_top_k integer, ransac_threshold double precision, pipeline_version text)` storing the localizer outputs (`inlier_ratio`, `reproj_error_median`, `num_inliers`, `num_correspondences`, `num_matches`, `inlier_coverage`, `pnp_covariance double precision[]` — 6×6 flat row-major (36 elements), `query_image_diagonal_px`), the truth-error labels (`err_t_m`, `err_r_deg`, `se3_residual double precision[]` — length 6), and `succeeded`. Typed arrays rather than `jsonb` because the existing schema has zero `json`/`jsonb` columns and stays uniformly typed. CHECK constraints enforce labels-iff-succeeded plus array-length invariants. `pipeline_version` is on the unique key so localizer code changes accumulate rows alongside historical data rather than overwriting it. Schema in `database/24_localization_evaluations.sql`. Endpoints in `docker/api/src/routers/localization_evaluations.py`: `POST /reconstructions/{reconstruction_id:uuid}/localization-evaluations` (upsert via `INSERT ... ON CONFLICT DO UPDATE` — cache-table semantics: second write with the same key is a refresh, not a conflict, so the harness can loop POST-only without a GET-first dance) and `GET /reconstructions/{reconstruction_id:uuid}/localization-evaluations?pipeline_version=...` (list with optional filter). RLS uses only the tenant policy; no orchestrator bypass; no supplementary indexes (the 5-tuple unique constraint serves `WHERE reconstruction_id = ?` as a prefix scan). 6 live HTTP integration tests in `docker/api/tests/test_localization_evaluations.py` cover create, upsert overwrite, version coexistence, filter, failed-with-null-labels, and path/body id mismatch.
   - **Codegen-side ARRAY type binding** (`build/src/build_scripts/placeframe/sqlacodegen_generator.py`). sqlacodegen emits `mapped_column(ARRAY(Double(...)))` which trips basedpyright `reportUnknownArgumentType` (ARRAY's generic `_T` can't be inferred from a `_TypeEngineArgument[_T]` whose inner is a generic-without-binding). The custom generator now intercepts `ARRAY` columns and renders `ARRAY[<python_type>](<inner>)` — pyright back-infers the inner type from ARRAY's `_T`. No suppressions, generated file ships clean. Documented in the generator's top docstring under "ARRAY GENERIC PARAM."
   - **`upload-time` supply-chain noise absorbed.** Chunks 3/4/5 reverted `upload-time` field additions on PyTorch wheel URLs in `docker/neural-networks-base/pylock.neural-networks-{cpu,cuda,rocm}.toml` to avoid the docker-rebuild cascade. Chunk 6 takes the cascade once and commits the regenerated locks because preflight's `lock_python(check=True)` step otherwise blocks CI for any subsequent chunk that touches Dockerfile-bearing services. After this commit, future chunks can run `lock-python` cleanly.
8. **Decouple harness from calibration; both scripts collapse to backend-id orchestrators** *(architectural correction; plan.md chunk 7)*. Rename `scripts/src/scripts/run_e2e.py` → `scripts/src/scripts/tune_reconstruction.py`; strip to PB recon-sweep only; input becomes `--captures <id>`; output is a tuning report. Rewrite `scripts/src/scripts/fit_calibration.py` so a single invocation does the whole thing: `uv run fit-calibration --captures <id> --pipeline-version <sha>` selects held-out frames per capture, discovers/creates reconstructions with `held_out_frame_timestamps` set, localizes the held-out frames, writes results to `localization_evaluations`, reads them back as the corpus, fits, writes `global.json`. Add `--reconstructions <id>` mode for fitting against pre-built reconstructions; add `--no-fit` to populate the cache without fitting. This chunk has three load-bearing sub-pieces called out below; each requires a comment block in the code capturing the present choice and the documented improvement axis. Delete `scripts/src/scripts/e2e_results.py` and the harness-side tar manipulation (`_prepare_capture`, modify-and-reupload, `placeframe-test-captures/` dependency). Update `scripts/tests/test_fit_calibration.py` to mock API client / localization-evaluations responses. Update `pyproject.toml` script entry: `test-placeframe-e2e` → `tune-reconstruction`.

   **8a. Held-out-frame selection — pluggable selector with a stride starter.** A `HeldOutFrameSelector` protocol behind a name (`--held-out-selector stride` is the default; future strategies register by name without touching the orchestration loop or the cache contract). The `StrideHeldOutSelector` ships now: `target_count = 100` (overridable via `--held-out-count`), `stride = max(1, len(timestamps) // target_count)`, `selected = timestamps[stride // 2 :: stride]`. Required big comment block explains: (a) chosen because it is deterministic, scales to capture length, gives even temporal spacing → roughly even spatial spacing on smooth capture paths; (b) known limitations — does not protect against connectivity loss (held-outs may be frames the SfM needed for tracks; the resulting map is then worse than what gets deployed and we calibrate against a worse map than reality), does not actively distribute spatially, fixed count rather than fraction-of-redundant-frames; (c) ideas for later — post-build filter (drop held-outs the SfM unregistered, augment from registered pool); spatial-bin (voxelize positions, pick one per voxel for even spatial coverage); hybrid stride+voxel; count-as-fraction-of-registered. The architectural shape is the load-bearing piece — adding a new strategy must not require surgery to `fit_calibration.py`'s orchestration loop or the localization-evaluations contract.

   **8b. Reconstruction reuse — match on the full `ReconstructionOptions` blob.** For each capture, list reconstructions via `GET /capture-sessions/{id}/reconstructions`, filter to `orchestration_status = 'succeeded'`, fetch each candidate's `manifest.json` from MinIO, and reuse iff `manifest.options == requested_options` (Pydantic equality on the full blob, including `held_out_frame_timestamps`). The "requested options" are constructed by the script from `ReconstructionOptions(held_out_frame_timestamps=selected_timestamps)` — server defaults for every other knob. If no match: create a new reconstruction with those exact options and wait for it to succeed. Required big comment block explains: (a) full-blob match is the chosen invariant — calibrations must be fit against one pipeline configuration, mixing recons built with different options into one corpus contaminates the fit; (b) ideas for later — options-hash column on `reconstructions` (or a derived view) to skip the manifest fetch on big corpora, opt-in `--match-options-on=held_out_only` flag for development workflows where the operator explicitly knows other options are immaterial.

   **8c. Localizer determinism (cache-key contract).** Add a one-time seed at the top of `localize_image_against_reconstruction` in `docker/localizer/src/localize.py`: `pycolmap._core.set_random_seed(LOCALIZER_RANDOM_SEED); torch.manual_seed(LOCALIZER_RANDOM_SEED)` with `LOCALIZER_RANDOM_SEED = 0` as a module constant. **Do not** enable `torch.backends.cudnn.deterministic` or `CUBLAS_WORKSPACE_CONFIG` — those carry a 10–30% latency cost and the residual non-determinism (last-digit drift in conv outputs) is below the discrete inlier-set threshold the fit cares about. The seed change is a localizer code change, so it bumps `pipeline_version` automatically; the cache key includes `pipeline_version`, so old non-deterministic rows from before this commit aren't treated as if they followed the new contract.
9. Plumb features through `apply_global_calibration`: `build_metrics.py:66` currently passes `Features.zeros()`. The typed seam landed early (drive-by during chunk 4 review): `core.calibration.Features` Pydantic model with all 11 named float fields, `FEATURE_NAMES` derived from `Features.model_fields`, `apply_global_calibration(features: Features)` signature replacing the prior `dict[str, float]`, and load-time `_validate_feature_names` rejecting artifacts whose `logistic_feature_names` don't match. Remaining work: build a real `Features` instance at the `build_metrics.py` call site from transformed metrics + map features.
10. Decouple `Σ_meas` from confidence in `build_metrics.py`: replace `PnP_cov / tight²` with `α · PnP_cov + β · I` (α, β read from the fitted calibration artifact). Confidence becomes a gate: `if metrics.confidence.loose < calibration.loose_min: raise LocalizationError(...)` in `localize.py`. **The thresholds (`loose_min`, `tight_min`) are fields on `CalibrationArtifact`, not module constants in the localizer.** Future calibration changes are artifact-only with no code edit; that's the whole reason this seam exists.
11. Remove the band-aids: `IDENTITY_BOOTSTRAP_SENTINEL` and its skip in `calibration.py`; `MIN_NUM_INLIERS` / `MIN_INLIER_COVERAGE` in `localize.py`; the hand-set `-4.595` intercept in `global.json`; the `CONFIDENCE_TIGHT_FLOOR` floor in `build_metrics.py`. These all happen once the starter calibration (next deliverable) is committed.
12. ~~Per-map calibration loader path: lazy MinIO fetch + cache, fall back to global-only if absent.~~ **Both the per-map fitter (Algorithm 3) and the loader are deferred to a later phase.** The original split landed only the loader plumbing now and deferred the fitter; on closer inspection the loader is dead code with no exercise until the fitter exists (Algorithm 3 is gated on Phase 5 phone-side correction landing), and untested-by-real-data scaffolding drifts. Adding the loader at the same time as the fitter is one line in `apply_global_calibration` and one line in the localizer's map-load path — no architectural risk in deferring. Tracked as a Phase 3 deferred follow-up in `plan.md`.

**Run-and-commit deliverables (single-capture starter calibration):**

13. Upload the one capture we have via the normal API path (if not already in the backend); run `uv run fit-calibration --captures <id> --pipeline-version <sha>`. Produces ~11 labeled rows. Commit the resulting `config/calibration/global.json` to the repo with a header comment that it is a known-bad single-capture starter, not a production calibration.
14. Set `loose_min` / `tight_min` in the starter `global.json`. Hand-set values for the starter: `loose_min = 0.25` (in the gap between the chunk-9 fit's loose=0 failure cluster and loose=0.5 success cluster) and `tight_min = 0.0` (no-op; the chunk-9 fit's tight model is degenerate at ~0 because no held-out frame cleared the tight error budget — no positive class for tight to fit on). The corpus-run version of `fit_calibration.py` will derive both from the success-cluster distribution; for the starter, hand-setting them here documents the intent and unblocks the band-aid removal without committing to a code-side constant that would need re-tuning when corpus calibration ships.

**Documentation deliverable:**

15. Corpus-gathering instructions (this file's "Corpus-gathering spec" section). Unambiguous enough to execute cold.

**Frontend follow-up (out of scope this initiative):**

- `BaseProcessNoise{Translation,Rotation}VariancePerTick` and `SnapThresholdSigmas` in `RelocalizationFilter` are tuned against the heuristic Σ_meas. With Σ_meas now decoupled and fitted, these need re-tuning. Tracked as scaffolding to be replaced; the starter calibration isn't reliable enough to drive that re-tuning meaningfully — defer until the multi-capture corpus run.

**Non-deliverables (explicit):**

- Running the full parameter sweep. Estimated ~15 hours per full run; not part of this effort.
- Gathering additional captures beyond the one we have.
- Producing a *production* `config/calibration/global.json`. The starter calibration that ships from this initiative is overfit-to-one-scene by construction; production calibration depends on the multi-capture corpus run later.
- Algorithm 2 (phone-side pairwise calibration). Algorithm specified below for completeness; code lands in a later phase.
- Algorithm 3 (per-map fitting). Algorithm specified below; code lands in a later phase.

## What this initiative validates and what it doesn't

We *do* run the full code path end-to-end this initiative — single-config harness + fit + commit + band-aid removal — against the one capture we have. That validates more than the previous "code-only" framing:

- The harness's full path (upload → reconstruct → localize → label → row emission) executes against real data.
- `fit_calibration.py` actually produces an artifact, not just unit-tested in isolation.
- The runtime loader reads the produced artifact and `apply_global_calibration` emits real (varying) confidence values.
- The reconstructor computes the new metrics into `manifest.json`, the harness fetches them per reconstruction at row-emission time.
- The decoupled Σ_meas formula (α · PnP_cov + β · I) executes against the real innovation gate in the Bayesian filter.

What we *can't* validate with a single capture: that the fitted logistic generalizes (it won't — it overfits to that one scene's metric distribution by construction), that map-quality features have signal (they're constants within a single map), that confidence is well-calibrated against held-out reality. Those answers come from the multi-capture corpus run. The starter calibration is functional, not trustworthy.

Smaller-scope validations not requiring the harness run:

- `fit_calibration.py` Procrustes solve unit-tested on synthetic point pairs with known alignment.
- Σ_meas α, β fit unit-tested on synthetic 6D residuals with known covariance.
- Round-trip artifact write/read.
- Hand-written calibration → known feature vector → expected confidence (loader correctness).

## Libraries used

The math is mostly off-the-shelf. Things to know about up front:

- **pycolmap** — `Sim3d` is used by the reconstructor to apply the single-anchor truth-frame alignment to the COLMAP reconstruction (already a reconstructor dep). The diagnostic Procrustes (rigid Umeyama / Kabsch via numpy SVD) is computed against the same registered frames but its transform is not applied to the reconstruction — only the residual is reported. Hand-rolled because it's small enough that a library wasn't worth pulling in, and pycolmap's `Sim3d.estimate` wasn't needed once we only required rigid (unit-scale) alignment.
- **scipy** — `spatial.ConvexHull(centers).volume` for `map_bounding_volume_m3`; `optimize.minimize` for the Σ_meas α, β MLE.
- **sklearn** — `linear_model.LogisticRegression`, `isotonic.IsotonicRegression`, `metrics.brier_score_loss`, `calibration.calibration_curve`.
- **pytransform3d** — SE(3) `log` for computing the 6-D residuals fed to the Σ_meas fit. Added to the `scripts` package as a dep of the harness (the harness pre-computes the residual via `exponential_coordinates_from_transform` and stores the 6-vector on each row, so the fit script consumes it without recomputing).

Things hand-rolled (small, well-defined):

- **Viewpoint diversity** — design metric, no library covers it. Pick a definition (variance of unit viewing-direction vectors); ~10 lines numpy.
- **Σ_meas α/β NLL** — custom 2-D Gaussian negative-log-likelihood passed to `scipy.optimize.minimize`; ~20 lines.

## Architecture

Post-refactor (chunks 5–7 of plan.md). Captures live in the backend via the normal upload path; both scripts orchestrate over backend ids and write/read through the API. There is no sidecar JSON file and no parallel data store.

```
       ┌────────────────────────────────────────────────────────────────┐
       │ Backend (PostgreSQL + MinIO)                                   │
       │                                                                │
       │  capture_sessions ─── tar in MinIO (frames.csv + images)       │
       │       │                                                        │
       │       ▼                                                        │
       │  reconstructions                                               │
       │       │                                                        │
       │       ├── manifest in MinIO                                    │
       │       │     - options (incl. held_out_frame_timestamps)        │
       │       │     - metrics (incl. map quality)                      │
       │       │                                                        │
       │       ▼                                                        │
       │  localization_evaluations  *NEW*                               │
       │     keyed by (reconstruction_id, frame_timestamp bigint,       │
       │                retrieval_top_k, ransac_threshold,              │
       │                pipeline_version)                               │
       │     stores localizer outputs + err_t_m/err_r_deg/se3_residual  │
       └─────────────────────────▲─────────────────────▲────────────────┘
                                 │                     │
        write evaluations +      │                     │  read corpus
        trigger reconstructions  │                     │  + fit + write
                                 │                     │  global.json
       ┌─────────────────────────┴────┐    ┌───────────┴────────────────┐
       │ scripts/tune_reconstruction. │    │ scripts/fit_calibration.py │
       │  py  *RENAMED from run_e2e* │    │                            │
       │                              │    │  --captures <id>           │
       │  --captures <id> [<id>...]   │    │    or                      │
       │                              │    │  --reconstructions <id>    │
       │  PB sweep over recon options │    │  --pipeline-version <sha>  │
       │  (one recon per cell, no     │    │                            │
       │  held-out frames here — pure │    │  - pick held-out frames    │
       │  parameter tuning).          │    │  - create reconstructions  │
       │                              │    │    with frames excluded    │
       │  Emits a tuning report.      │    │  - localize held-out       │
       │                              │    │    frames; cache to        │
       │                              │    │    localization_evaluations│
       │                              │    │  - read cache as corpus    │
       │                              │    │  - fit logistic + isotonic │
       │                              │    │  - fit Σ_meas α, β         │
       │                              │    │  - write config/           │
       │                              │    │    calibration/global.json │
       └──────────────────────────────┘    └────────────┬───────────────┘
                                                        │
                                                        ▼
                                       ┌────────────────────────────────┐
                                       │ Localizer (deployed)           │
                                       │  load_global_calibration() at  │
                                       │  boot; features plumbed into   │
                                       │  apply_global_calibration();   │
                                       │  returns calibrated Confidence │
                                       └────────────────────────────────┘
```

`fit_calibration.py` runs in two input modes:
- **`--captures <id>`**: full pipeline — picks held-out frames, creates fresh reconstructions (default recon options) with `held_out_frame_timestamps` set, localizes held-out frames, writes evaluations to the cache, fits, writes artifact.
- **`--reconstructions <id>`**: skips reconstruction; uses already-built reconstructions whose `held_out_frame_timestamps` are already set. Localizes held-out frames if not already cached, otherwise reads straight from `localization_evaluations`. Cheap re-fit path.

Plus `--no-fit` for "populate the cache, don't fit yet" (e.g. for offline inspection of evaluation rows).

**Localization is driver-side, not server-side.** `fit_calibration.py` fetches each held-out frame image via `GET /capture_sessions/{id}/images/{frame_timestamp}`, POSTs it to the existing localizer `/localize` endpoint, computes truth-error labels driver-side, and POSTs the evaluation row to `/reconstructions/{id}/localization-evaluations`. The localizer stays a pure function with no awareness of `localization_evaluations`. The capture data path is via two surgical API endpoints — `GET /capture_sessions/{id}/frames.csv` and `GET /capture_sessions/{id}/images/{frame_timestamp}` — not direct MinIO access; the API is the single read path.

`tune_reconstruction.py` is unrelated to fit-calibration's flow. It exists to compare PB cells of recon options across captures and emit a report; no held-out frames, no calibration corpus, no `localization_evaluations` writes. The two scripts share the held-out-frames API (chunk 5) and the cache table (chunk 6) only as available infrastructure — `tune_reconstruction.py` doesn't use either.

## Algorithm 1: ZED held-out fitting

Source: every capture session in the corpus that contributes a built map.

Procedure per capture:
1. **Hold out frames at map-build time.** A pluggable selector (default `StrideHeldOutSelector`) chooses ~100 timestamps per capture (overridable via `--held-out-count`) at an even temporal stride: `stride = max(1, len(timestamps) // target_count)`, `selected = timestamps[stride // 2 :: stride]`. Those timestamps go into `ReconstructionOptions.held_out_frame_timestamps`; the reconstructor filters them out of `frames.csv` and skips the matching images at build time. Rebuild the COLMAP map from the remaining frames. The selector is intentionally pluggable so a more spatially-aware strategy (voxel-bin, post-build connectivity-aware filter) can land later without touching the orchestration loop.
2. **Reconstructor aligns the map to truth.** The reconstructor pins the first registered frame's COLMAP pose to its `frames.csv` truth pose via single-anchor `Sim3d`; this places the rebuilt map in the capture's truth frame. Separately and only as a diagnostic, the reconstructor solves rigid (no-scale) Procrustes (Umeyama / Kabsch via numpy SVD) over all registered frames and emits per-capture residuals (`truth_alignment_rms_residual_m`, `truth_alignment_max_residual_m`); these ride the manifest and the operator (or the fit script in chunk 4) uses them to filter unreliable captures out of the corpus. The Procrustes transform itself is not applied to the reconstruction.
3. **Per held-out frame**:
   - Run the localizer on the held-out frame against the rebuilt map. The map is already in truth-frame from the single-anchor alignment, so the localizer's `camera_from_map` Transform doubles as `camera_from_world`.
   - Invert to get the estimated camera position and orientation in world (truth) frame.
   - Compare to the held-out frame's truth pose from `frames.csv` (read directly in the capture's native axis convention; the localizer's Transform is in the same convention since the API converts back from OpenCV at the boundary, so no basis change is needed).
   - Compute `err_t = ||truth_position − estimated_position||` (Euclidean, meters) and `err_r = ‖log(R_truth · R_estimated⁻¹)‖` (geodesic, degrees, via `scipy.spatial.transform.Rotation.magnitude`).
   - Record `(metrics, map_features, recon_config, loc_config, device, err_t, err_r)`.
4. **Pool across all captures and configs.** Add binary labels: `success_tight = err_t < 5cm AND err_r < 1°`, `success_loose = err_t < 30cm AND err_r < 5°`.
5. **Fit logistic regression** (sklearn `LogisticRegression(class_weight='balanced')`) on the feature vector. Features: `log(num_inliers + 1)`, `inlier_ratio`, `reproj_err / image_diagonal_pixels`, `inlier_coverage`, `log(num_matches + 1)`, `log(map_image_count + 1)`, `log(map_point_count + 1)`, `map_avg_track_length`, `log(map_bounding_volume_m3 + 1)`, `map_viewpoint_diversity`, `is_indoor`.
6. **Fit isotonic** (sklearn `IsotonicRegression(out_of_bounds='clip')`) on the logistic output against the same labels.
7. **Fit Σ_meas scaling.** For each held-out localization, compute the SE(3) residual `e = log(P_truth_in_map · P_estimated⁻¹) ∈ ℝ⁶` (using `pytransform3d.transformations.transform_log_from_transform`). Solve scalar α, β that maximize `Σᵢ log N(eᵢ; 0, α·PnP_covᵢ + β·I)` via `scipy.optimize.minimize` on the negative log-likelihood (small 2-D unconstrained MLE). The α, β scalars carry the empirical "actual pose-error spread relative to PnP_cov" signal that PnP_cov alone misses (mis-registered map points, wrong-but-confident inliers, etc.).
8. **Optional 10% holdout** for Brier score (`sklearn.metrics.brier_score_loss`) and reliability diagram (`sklearn.calibration.calibration_curve`); report in fit metadata.

Output: `{tight: {logistic, isotonic}, loose: {logistic, isotonic}, sigma_meas: {alpha, beta}, fit_metadata, pipeline_version}` written to `config/calibration/global.json`.

**Note on feature relevance with a small corpus.** Map-quality features are constants within a single capture's map-config combinations (the same map → the same features). With ≥3 distinct maps the features start to vary; with one capture they collapse into the intercept. The fitting code includes them unconditionally; the regression naturally weights them down to zero when they don't vary.

## Algorithm 2 — phone-side pairwise calibration (deferred)

Source: opt-in dogfooding sessions captured by the AndroidMobile app (per VPS Phase 4's logger), plus the cross-device cells the e2e harness already produces.

Procedure per session:
1. Enumerate localization pairs `(i, j)` where `j > i` and `||translation(T_vio_j) − translation(T_vio_i)|| ≤ 1.0 m` (limits VIO drift contribution to <1cm on flagship phones, <2cm on lower-end).
2. Per pair, compute pairwise error:
   - VIO-implied relative motion: `dT_vio = T_vio_j · T_vio_i⁻¹`.
   - Localizer-implied relative motion: `dT_loc = T_map_j · T_map_i⁻¹`.
   - Pairwise translation error: `err_t = ||translation(dT_loc) − translation(dT_vio)||`.
   - Pairwise rotation error: `err_r = angle_between(rotation(dT_loc), rotation(dT_vio))`.
3. Attribution: per individual localization, define `err_i = median over all pairs that include i of pair_err`. Robust to outlier pairs.
4. Pool across phone sessions. Fit isotonic correction `g(p) = empirical P(success | predicted_p_from_stage_1)`.

**Attribution caveat.** Pairwise errors confound the two localizations involved. Median-over-pairs is a coarse but robust attribution heuristic. A least-squares per-localization-error solve is the principled alternative. Median is the chosen baseline; LSQ is fallback if it proves insufficient.

**What this can't detect.** Errors systematically shared across all localizations in a session (e.g. miscalibrated phone intrinsics producing a constant offset on every query) get absorbed into the implicit `T_align` and produce zero pairwise residual. The user-facing manifestation — "consistent but slightly shifted world" — is the lowest-impact failure mode and is acceptable. Random outliers, the high-impact failure mode, are detected normally.

**Open question raised by harness fusion.** The harness already produces phone-against-ZED-map cells with Algorithm-1-style truth attribution (the phone's own `frames.csv`, Procrustes-aligned to the ZED-built map). If the phone capture's `frames.csv` truth is good enough, Algorithm 2's pairwise machinery may be unnecessary at our scale — directly-labeled phone-source data falls out of the same harness run. Worth examining when the corpus exists.

## Algorithm 3 — per-map fitting (deferred)

Same as Algorithm 2 but partitioned by map ID. Once a map accumulates ≥200 phone-side samples, fit a per-map isotonic on top of the global stage-1+stage-2 prediction:

```
predicted_p_global = stage1(metrics, map_features).then(stage2_isotonic)
permap_isotonic(p) = empirical P(success | predicted_p_global = p, map = M)
```

Per-map artifact uploaded to `s3://placeframe-maps/{map_id}/calibration.json`. The runtime loader path lands in this initiative; the fitting code itself is deferred until at least one map clears the sample threshold.

## Calibration runtime: loader, computation, failure modes

**Calibration loader at startup:**
1. Load global calibration from `/etc/placeframe/calibration/global.json` (Docker compose `configs:` volume; source of truth at `config/calibration/global.json` in the git repo).
2. Verify pipeline version. If `global.pipeline_version != localizer.pipeline_version`: hard-fail with a loud log explaining the mismatch and the fix (refit + commit + redeploy).
3. **Per-map calibrations are not loaded.** This describes the eventual end state: first localization request for a map triggers a lazy MinIO fetch + in-memory cache keyed by map ID; absent → log + fall back to global-only; pipeline-version-mismatched → log loudly + fall back to global-only. The loader is not implemented in this Phase — it lands together with Algorithm 3 (the per-map fitter) in a later phase, since there is no per-map artifact to read until the fitter exists. Until then, every query uses global-only.

**Confidence computation per query:**

```
features = transform(metrics, reconstruction_metrics, is_indoor)
  # log(num_inliers + 1), reproj_err / image_diagonal_pixels,
  # inlier_ratio (already 0-1), inlier_coverage (already 0-1),
  # log(map_image_count + 1), log(map_point_count + 1), map_avg_track_length,
  # log(map_bounding_volume_m3 + 1), map_viewpoint_diversity, is_indoor

p_global_tight = sigmoid(features @ global.tight.weights + global.tight.intercept)
p_global_loose = sigmoid(features @ global.loose.weights + global.loose.intercept)

p_calibrated_tight = global.tight.isotonic.apply(p_global_tight)
p_calibrated_loose = global.loose.isotonic.apply(p_global_loose)

if per_map_calibration_loaded:
  p_final_tight = per_map.tight.isotonic.apply(p_calibrated_tight)
  p_final_loose = per_map.loose.isotonic.apply(p_calibrated_loose)
else:
  p_final_tight = p_calibrated_tight
  p_final_loose = p_calibrated_loose

return Confidence(tight=p_final_tight, loose=p_final_loose, is_calibrated=True)
```

**Σ_meas computation per query** (decoupled from confidence):

```
Σ_meas = α · PnP_cov + β · I_6

  # α, β read from global.sigma_meas at startup.
  # Confidence does NOT scale Σ_meas. Confidence is used as a binary
  # gate upstream: localize.py rejects with LocalizationError if
  # metrics.confidence.loose < calibration.loose_min. Both thresholds
  # (loose_min, tight_min) are artifact fields, not module constants —
  # corpus calibration replaces them via global.json with no code edit.
  # Admitted measurements use this Σ_meas regardless of confidence value.
```

A few dozen FLOPs plus two isotonic lookups (binary search over ~100 breakpoints). Negligible cost.

**Failure modes:**

| Condition | Behavior | Rationale |
|---|---|---|
| Global calibration file missing at startup | Hard-fail startup | Indicates a broken deploy. |
| Global calibration pipeline-version mismatch | Hard-fail startup | Stale calibration vs new pipeline; refit required before serving. |
| Per-map calibration missing | Soft-fail: log + fall back to global-only | Expected for new/sparse-data maps; system still functional. |
| Per-map calibration pipeline-version mismatch | Soft-fail: log + fall back to global-only | Stale per-map; rebuild on next refit cycle. |

## Map quality features

Computed at map-build time inside `MetricsBuilder.build_reconstruction_metrics` and written to `manifest.json` in MinIO as part of the existing `ReconstructionMetrics` block — no separate "map quality" concept exists; these are reconstruction metrics. The harness fetches the manifest per reconstruction at row-emission time (same code path the existing `get_reconstruction_manifest` API already uses). At runtime the localizer reads them from the same manifest. `is_indoor` is also baked into `manifest.json` at create-time (snapshotted from the `reconstructions` row by `POST /reconstructions`), so the localizer reads all 6 map-side features from one place. Source-of-truth remains the row (column on `reconstructions`, user-toggleable, default false); the manifest snapshot is for the read path. When a toggle endpoint lands later, that endpoint must re-write `manifest.json` (single S3 PUT) to keep the snapshot fresh — a write-once path today since no toggle endpoint exists. The fit-side reads `is_indoor` directly from the row via `api.get_reconstruction(id=...)` rather than the manifest snapshot, so a stale snapshot only affects runtime confidence, not training labels.

- `map_image_count`: total registered images.
- `map_point_count`: total triangulated 3D points.
- `map_avg_track_length`: mean number of observations per 3D point.
- `map_bounding_volume_m3`: convex hull volume of camera centers, in cubic meters (`scipy.spatial.ConvexHull(centers).volume`).
- `map_viewpoint_diversity`: scalar derived from variance of camera viewing directions (higher = more directional coverage).
- `is_indoor`: boolean flag, set at upload time. Default false; toggleable per map.

These join into the calibration feature vector at query time and into the harness's labeled rows at fit time.

## Calibration artifact format

Single JSON document. ~3 KB global, ~1 KB per-map.

```json
{
  "schema_version": 1,
  "pipeline_version": "abc123def456...",
  "fit_metadata": {
    "fit_at": "2026-04-29T14:00:00Z",
    "fit_by": "scripts/fit_calibration.py v0.1",
    "sample_count": 8743,
    "validation": {
      "brier_tight": 0.092,
      "brier_loose": 0.041,
      "reliability_diagram_bins": [...],
      "procrustes_residuals_per_capture": {...}
    }
  },
  "global": {
    "tight": {
      "logistic": {
        "weights": [0.234, -1.83, 0.45, ...],
        "intercept": -2.14,
        "feature_names": ["log_inliers", "inlier_ratio", "reproj_err_norm", ...]
      },
      "isotonic": {
        "x_breakpoints": [0.01, 0.05, 0.10, ..., 0.99],
        "y_breakpoints": [0.02, 0.06, 0.12, ..., 0.97]
      }
    },
    "loose": { "logistic": {...}, "isotonic": {...} },
    "sigma_meas": {
      "alpha": 1.4,
      "beta": 0.0008
    }
  }
}
```

Per-map artifact has the same shape but only `tight.isotonic` and `loose.isotonic` blocks (the global logistic is the upstream).

## Storage and lifecycle

| Artifact | Path | Updated by | Cadence |
|---|---|---|---|
| Global calibration | `config/calibration/global.json` (git repo) | Engineer (PR after running fit pipeline) | Manual, on demand. Refit on every pipeline-affecting change to the localizer; otherwise refit when corpus grows meaningfully. |
| Per-map calibrations | `s3://placeframe-maps/{map_id}/calibration.json` (MinIO) | Fit pipeline (automated upload) | Manual, on demand. Per map, once sample count clears the threshold and is materially out of date. |
| Phone-side calibration data (raw logs) | `s3://placeframe-calibration-data/sessions/{session_id}.json` (MinIO) | AndroidMobile app (when dogfooding toggle is on) | Per session at session end |
| Localization evaluations cache | `localization_evaluations` table (PostgreSQL) | `fit_calibration.py` writes; reads directly during fit | Per (reconstruction, frame, retrieval_top_k, ransac_threshold). Idempotent upsert; rows persist across fit runs so re-fits don't re-localize. |

Updating global: run fit → `git diff` → review → PR → merge → deploy. No Docker rebuild (mounted as compose `configs:` volume).

Per-map: lazy load on first request, cached. Optional `POST /calibration/refresh/{map_id}` admin endpoint to invalidate cache after re-upload.

## Corpus-gathering spec (for future-operator-self)

When the time comes to gather the multi-capture corpus and run the *production* calibration (replacing the single-capture starter that ships at the end of this initiative), this is the spec.

### Where captures live

Captures live in the backend, period. Upload via the normal API path (the same one Unity's capture tooling uses) — there is no sibling directory and no harness-side tar shuffling. Each capture becomes a row in `capture_sessions` with its tar in MinIO.

If you're seeding a fresh dev environment with a known set of captures, upload them however you like (the existing `placeframe_api_client.upload_capture_session_tar` works fine from a one-off Python script). What matters is that by the time you run `fit-calibration`, the captures exist in `capture_sessions` and you have their UUIDs.

### What `capture.tar` is

A capture session tarball produced by the existing capture pipeline (ZED Capture for ZED, Capture Tool for ARFoundation). Inside:

- `manifest.json` — `CaptureSessionManifest`: axis convention, rigs (with cameras and intrinsics), capture interval.
- `rig0/frames.csv` — per-frame poses from the device's VIO/SLAM at capture time. Columns: `timestamp,tx,ty,tz,qx,qy,qz,qw`. **These are the truth poses Algorithm 1 uses for held-out-frame error labeling.**
- `rig0/camera0/{timestamp}.jpg` — frame images.
- `rig0/camera1/{timestamp}.jpg` — second eye, ZED only.

The capture pipelines already produce this layout; you don't have to construct it by hand.

### How many captures, what content

Minimums for a meaningful run:
- **At least 2 distinct ZED captures** (Algorithm 1 needs ZED truth poses; one capture alone gives no inter-capture variance).
- **At least 2 distinct physical scenes** so map-quality features have variance (otherwise they collapse to the intercept). Same scene captured twice doesn't count.
- **For cross-device validation**: matched ARFoundation captures at the same scenes. Cross-device localization happens automatically when both `is_indoor`-tagged maps exist for the same scene; the operator selects which captures share scenes via the `--captures` invocation.

Per capture:
- ≥ ~200 frames recommended. `fit-calibration` defaults to selecting up to 100 held-out queries per capture via the stride selector (`--held-out-count` overrides; `--held-out-selector` swaps strategies once additional ones land).
- Real scenes representative of deployment. Indoor for current target.
- Standard capture practice: continuous motion, varied viewpoint, minimal motion blur. The capture pipelines enforce some of this; the rest is operator discipline.

Stretch goals (for richer calibration):
- Multiple lighting conditions per scene (morning vs. evening).
- Indoor + outdoor mix once outdoor masking ships (Phase 2d).
- A range of map sizes (small room, large room, multi-room) to give `map_*` features genuine variance.

### How to run

Once the captures are uploaded:

```bash
# Optional first step: pick reconstruction defaults via the PB sweep.
# Outputs a tuning report; doesn't write to the calibration cache.
uv run tune-reconstruction --captures <id> [<id>...]

# Fit calibration end-to-end. One command. Selects held-out frames per capture
# (StrideHeldOutSelector by default), reuses existing reconstructions whose full
# ReconstructionOptions blob (including held-out set) matches what is requested
# — otherwise creates new ones — localizes held-out frames, caches evaluations
# in localization_evaluations (keyed on pipeline_version), fits, writes
# config/calibration/global.json.
uv run fit-calibration --captures <id> [<id>...] --pipeline-version <sha>

# Cheap re-fit against already-built reconstructions (skips reconstruction
# discovery; reuses cached localization_evaluations rows whose retrieval/ransac/
# pipeline_version match):
uv run fit-calibration --reconstructions <id> [<id>...] --pipeline-version <sha>

# Review the diff in config/calibration/global.json, commit, deploy.
```

`--pipeline-version` is **auto-detected** from the localizer's `GET /version` endpoint (the SHA is baked into the localizer image at build time via the `LOCALIZER_GIT_SHA` build arg). The flag remains as an *override* for development workflows where the operator iterates uncommitted localizer changes and wants their cache rows clearly labeled (e.g. `--pipeline-version dev-tylerh-2026-05-03`). The auto-detect default tamper-proofs the `localization_evaluations` cache-key contract — silent pooling of incompatible pipeline rows is otherwise an easy operator footgun. The runtime loader hard-fails if the deployed localizer's SHA doesn't match the artifact's `pipeline_version`. Refit on every pipeline-affecting change to the localizer.

### Verifying the run before trusting the output

The fit report (printed to stdout, also written next to the artifact) should be inspected before committing the calibration:

- **Procrustes residuals per capture**: meters of misalignment between truth and COLMAP poses. Large residuals (> a few cm typical session) indicate Procrustes is the noise floor and calibration won't be meaningful for that capture. Drop the capture or investigate.
- **Sample counts per cell**: too few labeled rows (< ~30) gives noisy logistic weights. Reflected in confidence intervals on the fit metadata.
- **Brier score**: lower is better; > 0.25 means the model is barely better than predicting the base rate. Investigate features that should have signal but don't.
- **Reliability diagram**: predicted-vs-actual probability binning. Should be roughly diagonal.

If any of these look bad, **don't ship the artifact**. Diagnose first.

## Resolved decisions

The questions that drove this document's design, and how each was resolved. Kept around so the resolution is traceable.

1. **Map-quality features live in the reconstruction's manifest** (S3), not as SQL columns on `reconstructions`. They're computed metrics, conceptually identical to the existing `ReconstructionMetrics` fields, so they share the same model and storage. Nullable columns would have leaked the "feature exists ↔ reconstruction succeeded" invariant into every reader; manifest-only avoids that. The harness fetches the manifest per reconstruction (single S3 GET each, sequential, negligible cost at corpus sizes through Phase 5). Runtime localizer reads from the same manifest. The user-controlled `is_indoor` boolean is the only column added to `reconstructions` since it isn't a reconstruction output.
2. **Map-quality features are included in the fit feature vector unconditionally.** The regression weights them to zero when they're constants (single-capture corpus). No gating on map count.
3. **~~Held-out frames stay implemented as harness-side tar surgery.~~ Reversed — chunks 5–7 of plan.md.** Held-out frames are now a first-class `ReconstructionOptions.held_out_frame_timestamps: list[int]` field. The reconstructor filters them at build time. **No new database column** — `ReconstructionOptions` already round-trips through MinIO inside `ReconstructionManifest.options`, so the requested held-out set is durably recorded against the reconstruction without schema change. `fit_calibration.py` reads the manifest to know which frames a reconstruction was built without. Original rationale ("avoid an API addition; the harness already does the surgery") was wrong-weighted: the surgery forced the harness to own input data, output schema, and provenance bundling, which then had to be unwound. Net cost of the corrected API addition is smaller than the drift it causes when omitted.
4. **Procrustes residuals are surfaced per-capture in the fit report.** Operator decides from the report whether to drop a capture; no auto-drop threshold in v1.
5. **`pipeline_version` chicken-and-egg is handled by operator discipline.** No auto-commit; the loader's startup hard-fail surfaces any mismatch before traffic flows.
6. **Σ_meas decoupled from confidence.** Replaced `PnP_cov / tight²` with `α · PnP_cov + β · I`, with α, β fit empirically in `fit_calibration.py` against held-out SE(3) residuals. Confidence becomes a binary gate (`loose < calibration.loose_min` rejects); admitted measurements use Σ_meas regardless of confidence value. **Thresholds (`loose_min`, `tight_min`) are fields on `CalibrationArtifact`, not module constants** in the localizer — corpus calibration replaces the artifact with no localizer code edit. Starter ships with `tight_min = 0.0` (no-op; tight is degenerate for the single-capture fit) and `loose_min = 0.25` (cluster-gap value); corpus run derives both from the success-cluster distribution.
7. **`--single-config` CLI flag** on `test-placeframe-e2e`. Short-circuits Phase 4 to `[None]` and skips the loc-config cross product. Used for fast iteration and incremental refits.
8. **Bad `frames.csv` truth has no code-side action.** Procrustes residual reporting (decision 4) is the operator-facing diagnostic. No "bad capture" flag in the schema.
9. **No synthetic corpus fixture.** CI is out of scope for this initiative; deferred to a separate effort if/when CI ever wants to exercise the harness path.
10. **Band-aids removed in this initiative**, not deferred. The single-capture starter calibration committed as deliverable 13 unblocks the swap. The localizer's gate constant moves from "module-level `TIGHT_MIN` baked from the starter fit's success cluster" to "`loose_min` / `tight_min` fields on `CalibrationArtifact`" (deliverable 14) — chosen so the corpus run replaces the threshold via `global.json` rather than via a code edit. The starter's `tight` model is degenerate (no positive class to fit on, since the chunk-9 held-out frames all exceeded the tight error budget), so `tight_min = 0.0` no-ops the tight gate and `loose_min = 0.25` (chunk-9 fit's success/failure cluster gap) carries the live gate until corpus calibration.
11. **Refit cadence is "manual, on demand."** Removed weekly/quarterly framing.
12. **`pipeline_version` is auto-detected from the localizer.** New `GET /version` endpoint on the localizer returns the SHA. The SHA was already baked into the localizer image via the pre-existing `GIT_COMMIT_SHA` build arg (populated from `git rev-parse HEAD` by the build script); the localizer reads it as `pipeline_version: str = environ["GIT_COMMIT_SHA"]`. Chunk 7 just exposed it via a new route — no new build arg needed. `fit-calibration` calls `/version` once at startup. `--pipeline-version` survives as a CLI override for dev iteration where the operator is on uncommitted code and wants distinctly-labeled cache rows. Resolves the chicken-and-egg footgun in decision 5 (operator-supplied string was easy to mis-pass, silently pooling incompatible rows into the fit corpus).
13. **Capture data fetched via API endpoints, not boto3.** Three new routes — `GET /capture_sessions/{id}/manifest.json` returning `application/json`, `GET /capture_sessions/{id}/frames.csv` returning `text/csv`, and `GET /capture_sessions/{id}/images/{frame_timestamp:int}` returning `image/jpeg`. Surgical (per-member) rather than full-tar because `fit-calibration` reads all of `frames.csv` and the manifest but only ~100 of potentially thousands of images per capture. The manifest endpoint was added because the existing `/rig_config` route is a dummy stub that doesn't read from the actual capture tar. All three share a stream-mode tar reader so per-call memory is O(member size). The API is the single read path; no boto3 in `scripts/`.
14. **Localization is driver-side in fit_calibration.** Fetch held-out frame from API → POST to existing localizer `/localize` → compute err_t/err_r driver-side against `frames.csv` truth → POST to `/reconstructions/{id}/localization-evaluations`. Considered alternative was a server-side `POST /reconstructions/{id}/evaluate-frame {frame_timestamp}` that would do fetch+localize+persist server-side; rejected because it would couple the localizer to MinIO/captures and to the evaluations table for a workflow that's purely orchestration.
15. **Localizer determinism.** `pycolmap._core.set_random_seed(0)` and `torch.manual_seed(0)` are set at the top of `localize_image_against_reconstruction` per-call. cudnn-deterministic flags and `CUBLAS_WORKSPACE_CONFIG` deliberately *not* enabled — the 10–30% latency hit isn't worth the residual non-determinism it eliminates (last-digit conv drift is below the discrete inlier-set threshold the fit cares about).
16. **`tune_reconstruction.py` evaluation criterion is map-quality metrics only for now.** Comparing PB cells by *localization quality* (held-out localizations per cell) is the correct figure of merit but requires running effectively the fit-calibration loop per cell — its own multi-hour effort, downstream of getting the calibration logic itself correct. Deferred to a follow-up phase. The chunk-7 version reports map quality (point count, track length, viewpoint diversity, bounding volume, image count, plus chunk-3 `truth_alignment_*` residuals) as a cheap proxy.
17. **Test depth for chunk-7 orchestrator: mock-only.** No live-stack integration test for `fit-calibration`; chunk 9 (single-capture starter run) *is* the integration test, performed by a human, with the bonus that its output is the artifact we ship. Live-stack tests would cost build-and-stack time on every CI run for marginal coverage when chunk 9 follows shortly.
18. **`is_indoor` source at runtime: snapshotted into the manifest at create-time.** The localizer needs `is_indoor` for the feature vector, but the row on `reconstructions` is the source of truth (user-toggleable). Considered alternatives: (b) localizer calls the API to fetch the row (adds api-client + service auth to the localizer, which currently never calls the API), (c) zero placeholder until later (defeats the chunk-8 "code logically complete" property). Chosen: bake `is_indoor` into `ReconstructionManifest` at `POST /reconstructions` time, so the localizer reads all 6 map-side features from one place. Mirrors how chunk 5 added `held_out_frame_timestamps` to manifest options. Write-once today (no toggle endpoint exists); when a toggle endpoint is added, it must re-write `manifest.json`. The fit-side keeps reading `is_indoor` from the row directly via `api.get_reconstruction(...)`, so a stale snapshot only affects runtime confidence, not training labels.
19. **Per-map calibration loader deferred together with the fitter.** The original chunk-8 split landed only the loader plumbing now (lazy MinIO fetch + global-only fallback) and deferred the fitter (Algorithm 3). On closer inspection the loader is dead code with no exercise until the fitter exists, and untested-by-real-data scaffolding drifts. Adding the loader at the same time as the fitter is one line in `apply_global_calibration` and one line in the localizer's map-load path — no architectural risk in deferring. Both now land together in a later phase; chunk 8 is just runtime feature plumbing + Σ_meas decoupling.
20. **Gate thresholds (`loose_min`, `tight_min`) live on `CalibrationArtifact`, not as localizer module constants.** Originally framed as "pick `TIGHT_MIN` from the starter fit's success-cluster distribution and bake into `localize.py`" — but that commits to a code change every time the calibration is refit (the threshold sits between empirical clusters whose location moves with each fit). Moving them to fields on the artifact lets corpus calibration replace the starter via `global.json` only, with no localizer code edit. Cost: one schema field, one loader read, one comparison — paid once. Benefit: the localizer is decoupled from threshold-tuning forever. **Why gate on `loose` in the starter, not `tight`:** the chunk-9 single-capture fit produced a degenerate `tight` model (all logistic weights zero, intercept −30, sigmoid ≈ 0 for any input) because every held-out frame's per-frame error exceeded the tight error budget — no positive class to fit on. `loose` carries real signal (non-trivial weights on `log_inliers` and `log_num_matches`) and its isotonic separates two empirical clusters at y=0 and y=0.5. Starter sets `loose_min = 0.25` (cluster-gap value) and `tight_min = 0.0` (no-op until corpus calibration produces a non-degenerate `tight` model).

## Risks and unknowns

- **Procrustes-as-truth assumption.** Algorithm 1 treats `T_truth_to_map · P_truth_i` as ground truth for the held-out frame. The truth source is `frames.csv` — the device's VIO/SLAM pose from capture time. ZED VIO is good but not perfect; ARFoundation VIO drifts noticeably over multi-minute sessions. The Procrustes residual on in-set images is the diagnostic, but it can mask issues: a globally-drifting VIO can be fit by Procrustes with low residual and still produce systematically biased held-out truth.
- **Single-capture starter calibration is overfit by construction.** The starter shipped from this initiative is fit on ~11 held-out localizations from one scene. It will not generalize. It is committed deliberately to unblock the band-aid removal and let the system run on real (varying) confidence — not because it's trustworthy. Production calibration depends on the multi-capture corpus run.
- **Pre-existing reconstructions lack the new metrics.** Manifests written before the metrics fields existed deserialize with `None` for those fields (Pydantic Optional defaults). The fit script skips rows whose manifest lacks the metrics rather than treating them as zero. Cheap to recompute by re-uploading the capture into a fresh reconstruction if the old map is still useful; otherwise let it age out.
- **Test corpus size for sweep.** The estimate of "~15 hours full run" comes from the orphaned md, and assumed 4 captures × 17 recon configs × N localizations. With more captures the runtime scales linearly in capture count and frame count. A corpus with ~10 captures and richer per-capture frame counts could easily push the full sweep past a day. The single-config mode is the workaround.
- **`pipeline_version` churn in active development.** Every commit that touches the localizer's relevant config invalidates the calibration. The starter calibration committed at the end of this initiative will go stale on the next localizer-touching commit. Loader hard-fail catches it; the operator refits.
- **Frontend filter constants are not re-tuned this initiative.** `BaseProcessNoise` and `SnapThresholdSigmas` were tuned against the heuristic Σ_meas. They're now miscalibrated against the decoupled Σ_meas + starter calibration. The starter is too unreliable to drive meaningful re-tuning; it'll feel rougher than identity-bootstrap until the corpus run lands. This is accepted cost.

## Where this used to live

For future archaeology if any of this content needs to be cross-referenced against the original sources:

- The orphaned `test-placeframe-e2e.md` was last present in `07133e66`. Read with `git show 07133e66:test-placeframe-e2e.md`.
- VPS Phase 3's calibration design lived in `vps-redesign-intent.md` as the "Calibration loader", "Confidence computation per query", "Map quality features", "Calibration", "Offline fitting pipeline" sections. Excised when this file was created — see git blame on `vps-redesign-intent.md`.
- VPS Phases 5 and 6 (phone-side correction, per-map overlay) referenced Algorithms 2 and 3 here; their algorithm bodies moved to this file under "Algorithm 2 / 3 (deferred)".
- Feature-pipeline Phase 2e referenced the e2e harness; that reference was excised when this file was created.
