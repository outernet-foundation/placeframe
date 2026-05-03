# Localizer Service

## What this is

The localizer service answers `POST /localize`: given a query image and a target reconstruction, it returns the camera's 6-DOF pose in the reconstruction's coordinate frame, plus calibrated confidence and a measurement covariance.

Operating instructions for running the service live in the top-level `CLAUDE.md`. This document covers the design rationale: API contract, calibration runtime, determinism guarantees, tensor operations, and bring-up findings that shaped the current state.

## Pipeline

```
query image ──► canonicalize_image (rotate to natural orientation)
                ├──► tile_image (square tiles for retrieval)
                │      └──► global_descriptor_extractor (DIR per tile)
                │             └──► top-K via similarity over (q_tile, db_tile) pairs
                ├──► local_feature_extractor (ALIKED keypoints + descriptors)
                └──► local_feature_matcher (LightGlue, query × top-K database images)
                       └──► 2D-3D correspondences via map.points2D
                              └──► RANSAC + PnP with covariance return
                                     └──► absolute pose + 6×6 inverse-Hessian covariance
                                            └──► build_metrics (apply calibration)
                                                   └──► gate on confidence.loose
                                                          └──► return Transform + LocalizationMetrics
```

The retrieval, feature extraction, matching, and PnP stages are timed per-call (`localize timings(ms): canonicalize=… aliked=… …`) for observability. CUDA kernels are async; each GPU-bound stage ends with `cuda.synchronize()` so timings reflect true wall time rather than just kernel-launch.

## API contract

### Response: `LocalizationMetrics`

In addition to raw metrics (`NumInliers`, `InlierRatio`, `ReprojectionErrorMedian`, `InlierCoverage`, `NumMatches`, `NumCorrespondences`):

- **`Confidence`** (`Confidence` sub-object):
  - `tight: float in [0, 1]` — `P(translation_err < 5cm AND rotation_err < 1°)`
  - `loose: float in [0, 1]` — `P(translation_err < 30cm AND rotation_err < 5°)`
  - `is_calibrated: bool` — false only if calibration unavailable; should never be false in production.
- **`PnpCovariance`** (`float[6][6]`, 6×6) — raw PnP covariance from the inverse Hessian at the optimum (`pycolmap.estimate_and_refine_absolute_pose(..., return_covariance=True)`). Surfaced *separately* from `MeasurementCovariance` so `fit_calibration` can solve for α/β; the frontend does not consume this directly.
- **`MeasurementCovariance`** (`float[6][6]`) — runtime-applied `Σ_meas = α · PnP_cov + β · I` using α/β read from the loaded calibration artifact. This is the field the frontend filter consumes.
- **`PipelineVersion`** (string) — the localizer image's git SHA at build time. Allows clients to verify they're consuming results from the calibrated pipeline they expect.

The two-fields rationale (raw + runtime-applied covariance): the server keeps applying the calibration formula so the frontend filter stays calibration-agnostic; `pnp_covariance` exists purely for the fit consumer. The alternative — single raw field with frontend-side α/β application — would push calibration math into the Unity client without justification.

### `GET /version`

Returns `{ git_sha: str }`. The SHA is baked into the image at build time via the `GIT_COMMIT_SHA` Docker build arg (set in `compose.bake.yml` to `${GIT_COMMIT_SHA:?err}`, populated by `build/src/build_scripts/placeframe/build_docker.py` from `git rev-parse HEAD`). The localizer reads it as `pipeline_version: str = environ["GIT_COMMIT_SHA"]` at startup.

`pipeline_version` is a code property of the localizer image, not an operator opinion. Auto-deriving it tamper-proofs the `localization_evaluations` cache-key contract against operator typos — silent cache pooling across incompatible pipelines is otherwise an easy operator footgun. `fit-calibration` retains a `--pipeline-version` CLI override for development workflows where the operator iterates uncommitted changes and wants their cache rows clearly labeled (e.g. `dev-tylerh-2026-05-03`).

## Calibration runtime

### Loader

At service startup:

1. Load global calibration from `/etc/placeframe/calibration/global.json` (Docker compose `configs:` volume; source of truth at `config/calibration/global.json` in the git repo).
2. Verify pipeline version. If `global.pipeline_version != localizer.pipeline_version`: **hard-fail** with a loud log explaining the mismatch and the fix (refit + commit + redeploy).
3. **Per-map calibrations are not loaded** in the current end state. The eventual design has the first localization request for a map trigger a lazy MinIO fetch + in-memory cache keyed by map ID; absent → log + fall back to global-only; pipeline-version-mismatched → log loudly + fall back to global-only. The loader bundles together with the per-map fitter (see `plan.md`).

### Confidence computation per query

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

return Confidence(tight=p_calibrated_tight, loose=p_calibrated_loose, is_calibrated=True)
```

`Features` is the typed seam (`core.calibration.Features` Pydantic model with all 11 named float fields). `FEATURE_NAMES` derives from `Features.model_fields` so the field set has one source of truth; load-time `_validate_feature_names` rejects artifacts whose `logistic_feature_names` don't match. `apply_global_calibration(features: Features)` takes the typed model rather than a `dict[str, float]`. Build-side row construction in `fit_calibration.py` and inference-side feature construction here both build `Features` instances, so the fit-time and inference-time feature sets are guaranteed to match by type.

A few dozen FLOPs plus two isotonic lookups (binary search over ~100 breakpoints). Negligible cost.

### Σ_meas computation per query

```
Σ_meas = α · PnP_cov + β · I_6
```

α, β come from the fitted calibration artifact at startup. Confidence does **not** scale `Σ_meas`. Confidence is the binary upstream gate; admitted measurements use `Σ_meas` regardless of confidence value.

### Confidence gate

```
if metrics.confidence.loose < calibration.loose_min or metrics.confidence.tight < calibration.tight_min:
    raise LocalizationError(...)
```

`loose_min` and `tight_min` are **fields on `CalibrationArtifact`**, not module constants. Corpus calibration replaces them via `global.json` only — no localizer code edit required. This is the whole reason the seam exists: the localizer is decoupled from threshold-tuning forever.

The starter calibration (single-capture) ships `loose_min = 0.25` (between the empirical loose=0 failure cluster and loose=0.5 success cluster) and `tight_min = 0.0` (no-op; the starter's tight model is degenerate at ~0 because every held-out frame's per-frame error exceeded the tight error budget — no positive class for tight to fit on). The corpus run derives both from the success-cluster distribution.

### Failure modes

| Condition | Behavior | Rationale |
|---|---|---|
| Global calibration file missing at startup | Hard-fail startup | Indicates a broken deploy. |
| Global calibration pipeline-version mismatch | Hard-fail startup | Stale calibration vs new pipeline; refit required before serving. |
| Per-map calibration missing (when loader exists) | Soft-fail: log + fall back to global-only | Expected for new/sparse-data maps; system still functional. |
| Per-map calibration pipeline-version mismatch (when loader exists) | Soft-fail: log + fall back to global-only | Stale per-map; rebuild on next refit cycle. |
| Localizer fails to produce a pose at all (e.g. not enough matches) | Existing error response | Pre-existing behavior. |

## Pipeline version contract

The localizer's git SHA at image-build time is `pipeline_version`. Pipeline-tuning constants (`RANSAC_THRESHOLD`, `RETRIEVAL_TOP_K`, etc.) live as module-level Python constants — baked into the image — so changing them requires a code change and bumps `pipeline_version` automatically, invalidating calibration. Env vars would silently bypass that invariant. Tuning these at deploy time is therefore not possible; that's the intended cost.

Every change to the localizer's relevant config invalidates calibration. Engineering discipline required to avoid trivial changes that break it. Once the system is in production with evidence of which inputs actually shift the metric distribution, this can become a selective hash; for now the false-positive refit cost is bounded.

## Determinism (cache-key contract)

`localization_evaluations` cache rows keyed on `(reconstruction_id, frame_timestamp, retrieval_top_k, ransac_threshold, pipeline_version)` are reproducible because `localize_image_against_reconstruction` seeds per-call:

```python
LOCALIZER_RANDOM_SEED = 0
pycolmap._core.set_random_seed(LOCALIZER_RANDOM_SEED)
torch.manual_seed(LOCALIZER_RANDOM_SEED)
```

`cudnn.deterministic` and `CUBLAS_WORKSPACE_CONFIG` are deliberately **not** enabled. Their 10–30% latency cost outweighs the residual non-determinism, which is below the discrete inlier-set threshold the fit cares about (last-digit drift in conv outputs, undetectable downstream of RANSAC).

Any change to seed scope or this calculus bumps `pipeline_version`, which tags a new cache key — old non-deterministic rows from before the seed contract aren't pooled with new ones.

## Tensor operations

Tensor-shape typing across the localizer uses `core.tensor_types.TT[*Shape]` plus per-rank wrapper modules:

- `docker/localizer/src/torch_ops.py` — thin per-rank torch wrappers (`from_numpy`, `to`, `stack`, `permute`, `transpose`, `matmul`, `amax`) typed via `@overload` so output shape flows from runtime args.
- `core.numpy_ops` — numpy sibling.

Wrappers grow opportunistically — a wrapper exists for an operation when erasing dim names at that boundary loses type information that we want to preserve. Per-rank `@overload` sets are required because PEP 646's `TypeVarTuple` doesn't admit per-element bounds; e.g. one `from_numpy` overload per supported rank, six `permute` overloads for 3D's permutations.

This module is the localizer's primary surface for the typed-tensor pattern. Domain-level shape semantics (dim brands like `NumImages`, `RetrievalDim`, `NumKeypoints`) live next to the concept that defines them in `core/` — see `packages/python/core/SPEC.md` "Static tensor shape typing."

## Bring-up findings

Surprises observed in the first end-to-end production runs that informed permanent design decisions.

### Σ_meas decoupling from confidence

Original formula was `Σ_meas = PnP_cov / tight²` with constant `tight = 0.5` giving only 4× inflation. PnP's analytic Hessian covariance is wildly tight (~1e-6 variance, σ ≈ 0.3mm), so post-scaling Σ_meas was still absurdly tight. The Bayesian filter's innovation gate then rejected nearly every measurement as implausibly far.

Replacing the formula with `α · PnP_cov + β · I` where α, β are empirically fit against held-out SE(3) residuals is the durable fix. The α, β scalars carry the empirical "actual pose-error spread relative to PnP_cov" signal that PnP_cov alone misses (mis-registered map points, wrong-but-confident inliers, etc.).

Confidence becomes a separate concern: a binary upstream gate, not a covariance scaler. Admitted measurements all use the fitted Σ_meas regardless of confidence value. Confidence flows into the frontend filter through the wide-vs-tight Σ that the calibration produces, not as a scalar.

### LightGlue per-request time

Per-stage instrumentation originally showed LightGlue matching at ~250 ms (44% of total per-request time, dominant stage). After tuning to `LightGlue(features="aliked", width_confidence=-1, depth_confidence=0.95, mp=True)` the median dropped to ~140 ms (29-query sweep), no longer dominant — roughly comparable to `dir_tiles + matching_setup` combined.

The durable record (V1/V2/V3 measurements, batching footgun, when V3 might become correct again) lives as a comment on `load_lightglue` in `packages/python/neural-networks/src/neural_networks/models.py`. Code is the source of truth; no SPEC duplication.

Per-request total runs ~700 ms median against the test map used during bring-up (down from ~840 ms pre-tuning on the same map). Adding OneFormer-Swin-T for masking will add ~100–200 ms — total stays under the 1Hz client cycle budget but with less headroom than the pre-tuning numbers suggested.

### Operating-point reality check

The system lands at ~1cm visual misalignment in indoor testing. This is at or slightly below what published literature reports as the noise floor for hloc-style pipelines (LaMAR, KAPTURE, hloc indoor benchmarks all report 2–10cm depending on scene difficulty). Further accuracy gains require things outside the scope of calibration tuning: per-device intrinsics calibration, map georeferencing against ground truth, or fundamentally different feature extractors. Filter tuning alone won't help meaningfully.

### Frontend metrics-event design gap

Once the Bayesian filter is steady-state, `OnEcefToUnityWorldTransformUpdated` fires only on snap (rare) or during slew animations (brief, only when σ_posterior shifts enough). UI consumers wanting per-measurement metrics — including any "live metrics" diagnostic display — couldn't bind to it usefully. `OnMetricsReceived` + `LastReceivedMetrics` exist for this case (every API response, regardless of filter accept/reject). See `packages/unity/Placeframe/SPEC.md`.

## Open tunables

| Parameter | Default | Where used |
|---|---|---|
| `RANSAC_THRESHOLD` | 8.0 | RANSAC inlier threshold |
| `RETRIEVAL_TOP_K` | 12 | top-K database images selected from retrieval |
| `LOCALIZER_RANDOM_SEED` | 0 | per-call torch + pycolmap seed |
