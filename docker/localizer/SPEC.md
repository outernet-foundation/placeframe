# docker/localizer/

## What this is

A Litestar ASGI service that answers `POST /localization`: given a query image plus one or more target reconstruction IDs, it returns each camera's 6-DOF pose in that reconstruction's coordinate frame, with a calibrated confidence pair and a 6x6 measurement covariance for the downstream Bayesian filter. Also exposes `GET /version` returning the build-time git SHA as the pipeline version. The phone client never reaches this service directly — it's behind `docker/api/`, which proxies via the generated `placeframe_localizer_client`. Stack-level context (where the localizer sits in the capture -> reconstruct -> localize flow, log query patterns, MinIO bucket layout) lives in `docker/SPEC.md`; this file covers the subsystem.

## Shape

### Module map

```
docker/localizer/
  Dockerfile               FROM neural-networks-base; bakes LOCALIZER_SHA (build-context hash) late
  entrypoint.sh            uvicorn src.main:app --host 0.0.0.0 --port 8000
  pyproject.toml           pycolmap, faiss-cpu, scipy, litestar; torch undeclared
                           (DEP003 ignore — pulled in via neural-networks extras)
  src/
    main.py                Litestar app + the /localization handler + S3 client
                           + calibration load + the per-process Map cache
    localize.py            load_models() (DIR/ALIKED/LightGlue) + the pipeline
    map.py                 Map dataclass + load_map (MinIO download + hydrate)
    build_metrics.py       PnP + features + calibration -> LocalizationMetrics
    schemas.py             Pydantic response models
    settings.py            MinIO + RECONSTRUCTIONS_BUCKET env config
    torch_ops.py           per-rank @overload typed torch primitives
    dump_openapi.py        CODEGEN=1 + print app.openapi_schema.to_schema()
  tests/test_build_metrics.py   the only test file
  openapi.json             committed; consumed by generate-clients
```

External support modules under `packages/python/core/src/core/`: `calibration` (Features / CalibrationArtifact / apply_global_calibration), `h5` (read_features / read_global_descriptors), `opq` (read_opq_matrix / read_pq_quantizer / decode_descriptors), `image_preprocess` (canonicalize_image / canonicalize_intrinsics / tile_image with shorter-side 1024px + 0.5 overlap), `model_wrappers` (factories around neural_networks.models.load_DIR / load_aliked / load_lightglue), `localization_metrics` (`RETRIEVAL_TOP_K_DEFAULT=12`, `RANSAC_THRESHOLD_DEFAULT=8.0`).

### Boot lifecycle

All heavy state loads at module import. `uvicorn src.main:app` imports `src.main`, which:

1. Reads settings, creates a long-lived boto3 S3 client (`src/main.py:46`).
2. Guards on `CODEGEN`. When unset (the production path):
   - `load_models()` (`src/localize.py:58`) imports `neural_networks.models` and materializes `global_descriptor_extractor` (DIR), `local_feature_extractor` (ALIKED), `local_feature_matcher` (LightGlue) on `DEVICE = "cuda" if cuda.is_available() else "cpu"`. Models stay GPU-resident for the container's lifetime.
   - `pipeline_version = environ["LOCALIZER_SHA"]` is captured for the cache-key contract. `LOCALIZER_SHA` is the content-addressed hash of the localizer image's build context (computed by `build_scripts.placeframe.context_sha.compute_service_shas`); it changes whenever the inference pipeline changes and nothing else, so unrelated repo commits do not invalidate calibration.
   - `load_global_calibration("/etc/placeframe/calibration/global.json", pipeline_version)` reads the artifact and hard-fails if missing, if `schema_version != 2`, or if its pinned `pipeline_version` doesn't match the image's `LOCALIZER_SHA`. The literal sentinel `"placeholder"` (from `core.calibration.PLACEHOLDER_PIPELINE_VERSION`) bypasses the version check with a stderr warning — intended only for placeholder calibrations whose values don't depend on the pipeline (zeroed weights, fixed sigmas).
3. Defines the `LocalizationRequest` model and the `localize_image` + `get_localizer_version` handlers, then constructs the Litestar app.

There is no shutdown hook — model memory, S3 client, downloaded artifacts on disk, and the in-memory `Map` cache all live until the container is killed.

The `CODEGEN` branch is the only opt-out: `src/dump_openapi.py` sets `os.environ["CODEGEN"] = "1"` before importing `src.main`, so codegen can produce the OpenAPI spec without torch / pycolmap / a calibration file present. `settings.get_settings()` is also CODEGEN-aware (`Settings.model_construct()` skips env-var validation).

### Request flow

`POST /localization` (`src/main.py:76`):

```
multipart body
  - reconstruction_ids: list[UUID]
  - metrics: dict[UUID, ReconstructionMetrics]   (per-recon map metrics)
  - camera_config: PinholeCameraConfig
  - axis_convention: AxisConvention              (OPENCV | UNITY)
  - retrieval_top_k: int | None                  (default 12)
  - ransac_threshold: float | None               (default 8.0)
  - image: UploadFile

for id in reconstruction_ids:
    if id not in _maps:
        _maps[id] = load_map(id, s3_client, bucket, /tmp/reconstructions, metrics[id])
    try:
        result = localize_image_against_reconstruction(_maps[id], ...)
        results.append(Localization(id, transform, metrics))
    except LocalizationError as e:
        errors.append(f"Reconstruction {id}: {e}")

if not results:
    raise HTTPException(422, "; ".join(errors))
return results
```

Per-reconstruction errors are tolerated; only an empty result set produces a 422. The success response omits failed entries silently — a caller seeing `len(result) < len(reconstruction_ids)` cannot recover the per-id reason.

`GET /version` (`src/main.py:118`) returns the module-level `pipeline_version` as `text/plain`.

### Map loading

`src/map.py:42` `load_map` is synchronous and called inline from the async handler:

1. Paginate `s3.list_objects_v2(Bucket=bucket, Prefix=f"{id}/")` and download every key matching `{id}/sfm_model/...` or one of `global_descriptors.h5`, `features.h5`, `opq_matrix.tf`, `pq_quantizer.pq` into `/tmp/reconstructions/{id}/`.
2. `pycolmap.Reconstruction(.../sfm_model)` reads the COLMAP binaries (`points3D.bin`, `images.bin`, `cameras.bin`).
3. For each sorted image_id, hydrate `image_sizes[(h, w)]`, `keypoints[float32]` from `features.h5`, `pq_codes[uint8]` from the same file, and append the variable-tile-count `[tiles, RetrievalDim]` global descriptors from `global_descriptors.h5` into a list.
4. Zero-pad the per-image tile descriptor list into one rank-3 ndarray of shape `[NumImages, MaxTiles, RetrievalDim]` (the unused slots are zero so the later `amax` over query-tile x db-tile pairs naturally drops them).
5. Load the faiss `OPQMatrix` and `ProductQuantizer` from `opq_matrix.tf` / `pq_quantizer.pq`.
6. Re-validate the API-forwarded `ReconstructionMetrics` as `RawMapMetrics` — drops every field except the five the calibration features consume (`map_image_count`, `map_point_count`, `map_avg_track_length`, `map_bounding_volume_m3`, `map_viewpoint_diversity`).

Returns a frozen `Map` dataclass. Cached in `_maps: dict[UUID, Map]` (`src/main.py:44`) for the container's lifetime.

### Pipeline

```
canonicalize_image            EXIF rotate -> lanczos resize so short side = 1024 -> RGB
        |
        +--> ALIKED              local keypoints + descriptors
        |
        +--> tile_image          square 1024-tiles, 0.5 overlap
                |
                +--> DIR         global descriptor per tile -> stack
                       |
                       +--> sim  query_tiles x db_tile_descriptors (matmul + permute)
                              |
                              +--> amax over (query_tile, db_tile) per image
                                     |
                                     +--> topk -> matched_image_ids
                                            |
                                            +--> decode_descriptors (OPQ.reverse_transform
                                                  o PQ.decode o L2-normalize)
                                                    |
                                                    +--> LightGlue match
                                                           query x each db image
                                                           |
                                                           +--> 2D-3D correspondences
                                                                  via images[id].points2D
                                                                  (drop pts without point3D_id)
                                                                  |
                                                                  +--> RANSAC + PnP
                                                                        return_covariance=True
                                                                          |
                                                                          +--> change_basis
                                                                                if axis=UNITY
                                                                                |
                                                                                +--> Features
                                                                                +--> apply_calibration
                                                                                +--> sigma_meas =
                                                                                       a*PnP_cov + b*I_6
                                                                                +--> gate on
                                                                                       calibration.{loose,tight}_min
                                                                                +--> return Transform +
                                                                                       LocalizationMetrics
```

Each GPU-bound stage ends with `cuda.synchronize()` so the per-stage timings logged at completion (`localize timings(ms): canonicalize=... aliked=... dir_tiles=... retrieval=... matching=... pnp=... total=...`) reflect wall time rather than just kernel-launch. Median per-request total is ~700ms on the bring-up test map.

Database descriptors round-trip through OPQ + PQ (lossy uint8 codes -> decoded float32 -> reverse-transformed -> L2-normalized). Query descriptors are fresh-and-full-precision. LightGlue matches across the asymmetric pair.

Determinism: `set_random_seed(0)` and `manual_seed(0)` are called per request. `cudnn.deterministic` and `CUBLAS_WORKSPACE_CONFIG` are intentionally left off — their 10-30% latency cost outweighs the residual non-determinism, which sits below the discrete inlier-set threshold any cache-key consumer cares about. The seed contract exists so `localization_evaluations` cache rows keyed on `(reconstruction_id, frame_timestamp, retrieval_top_k, ransac_threshold, pipeline_version)` are reproducible against a given image.

### Calibration

A single global calibration JSON is bind-mounted via compose `configs:`:

- Source of truth: `config/calibration/global.json` (git).
- Container path: `/etc/placeframe/calibration/global.json` (mode 0444; mounted in `compose.cuda.yml` and `compose.rocm.yml`).
- Validator: `core.calibration.load_global_calibration` enforces `schema_version == 2` and `pipeline_version == localizer's LOCALIZER_SHA`. Either mismatch hard-fails the container. The literal sentinel `"placeholder"` (`core.calibration.PLACEHOLDER_PIPELINE_VERSION`) bypasses the version check with a loud stderr warning — for placeholder calibrations whose values are pipeline-independent.

The artifact carries: per-tolerance (`tight` / `loose`) `logistic_weights: Features`, `logistic_intercept`, plus optional isotonic remapping `(x_breakpoints, y_breakpoints)`. Confidence per query is `sigmoid(intercept + weights @ features.values())`, then optionally `numpy.interp(raw, x_breakpoints, y_breakpoints)`. `Features.compute` packs ten scalars (`log1p(num_inliers)`, `inlier_ratio`, `reproj_error_median / query_image_diagonal_px`, `inlier_coverage`, `log1p(num_matches)`, four log/passthrough map features, `map_viewpoint_diversity`).

The artifact also carries `sigma_meas_alpha`, `sigma_meas_beta`, `loose_min`, `tight_min`. `measurement_covariance = alpha * pnp_covariance + beta * I_6`. The server-side gate at `src/localize.py:232` raises `LocalizationError` if `confidence_loose < loose_min or confidence_tight < tight_min`. With the current placeholder artifact (`loose_min = tight_min = 0.0`) this gate is a no-op.

The current `global.json` is a placeholder: zeroed weights/intercepts, `alpha = 1.0`, `beta = 1e-4`, both mins 0.0, sample_count 0, `pipeline_version = "placeholder"`. Confidences resolve to 0.5 for every query and the gate never fires. The `"placeholder"` sentinel disarms the pipeline-version check so the placeholder file survives pipeline changes without a refit. Replace via `uv run fit-calibration` against a real capture corpus.

### Deployment

`compose.cuda.yml` (mirrored by `compose.rocm.yml`):

```
localizer-cuda:
  image: ghcr.io/.../localizer-cuda:${LOCALIZER_SHA:?err}
  expose: ["8000"]
  networks: { default: { aliases: ["localizer"] } }   # api hits http://localizer:8000
  gpus: all
  configs:
    - source: localizer-calibration-global
      target: /etc/placeframe/calibration/global.json
      mode: 0444
  environment:
    MINIO_ENDPOINT_URL, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, RECONSTRUCTIONS_BUCKET
```

No healthcheck. No `restart` policy. No `depends_on`. The API service treats the localizer as a best-effort backend and returns 502 if the `localize_image` round-trip raises a non-422 `ApiException`.

The Dockerfile bakes `LOCALIZER_SHA` in the *last* `ENV` layer, so only that layer invalidates when the build-context hash changes. `PYTORCH_ALLOC_CONF=expandable_segments:True` is set in the image — PyTorch's default caching allocator fragments under varying per-request peaks (query images of different sizes, varying top-K, varying keypoint counts) and eventually OOMs despite ample free memory. Expandable segments use CUDA virtual memory to grow segments on demand.

## Constraints

**Models, calibration, and S3 client load at module import — no async startup hook.** Litestar's lifespan hooks would let the loader run async, but the loads are CPU/GPU-blocking and run exactly once, so async buys nothing. Module import is the simplest correct shape.

**Per-map artifacts are downloaded inline on first request, not pre-warmed.** A pre-warm would need a Postgres dependency (to know which reconstruction IDs exist) and a startup ordering constraint with the API. Inline-on-first-use trades a one-time slow request per never-before-seen ID for zero coupling. The cost: the `Map` cache is unbounded and `/tmp/reconstructions/` accumulates indefinitely. Acceptable on the current scale (small number of maps per deployment); becomes a real leak in production.

**Database descriptors are OPQ + PQ compressed, query descriptors are not.** OPQ + PQ shrinks per-image descriptor storage by ~30x with a precision floor that LightGlue tolerates well in the asymmetric q->db direction. Compressing the query side too would save no storage (it's transient) and pay the encode + decode cost on the hot path.

**Padded `[NumImages, MaxTiles, RetrievalDim]` tile-descriptor tensor with `amax` retrieval.** Two design pressures: (a) database images have variable tile counts (a 4:3 image yields one tile, a panoramic capture might yield seven); (b) the retrieval similarity needs to be a single GPU op, not a per-image loop. Zero-padding plus `amax` over the query-tile and db-tile axes naturally drops the padded zeros (||q||*||0|| = 0 < any real cosine) and lets the similarity matrix be a single batched matmul. The max over both tile axes is the right reduction because retrieval cares about "any tile of the query looks like any tile of the database image."

**Custom `core.tensor_types.TT[*Shape]` plus `torch_ops.py` per-rank @overload wrappers.** Static typing the rank and dim brands (`NumImages`, `RetrievalDim`, `MaxTiles`, `NumQueryTiles`, `NumKeypoints`) catches "wrong axis to reduce" bugs at type-check time. Per-rank @overload sets are required because PEP 646's `TypeVarTuple` doesn't admit per-element bounds. The wrapper module grows opportunistically — a wrapper exists for an operation when erasing dim names at that boundary loses type information worth preserving.

**`sigma_meas = alpha * pnp_covariance + beta * I_6` rather than confidence-scaled covariance.** PnP's analytic inverse-Hessian covariance reports ~1e-6 variance (sub-mm) — wildly tighter than the actual SE(3) error spread, because it doesn't model mis-registered map points or wrong-but-confident inliers. An earlier `sigma_meas = pnp_cov / tight^2` formula was rejected by the Bayesian filter's innovation gate on nearly every measurement. The `alpha`, `beta` fit absorbs the empirical spread; confidence becomes a separate binary gate, not a covariance scaler.

**Pipeline version is the localizer image's `LOCALIZER_SHA` (build-context hash), baked at build time.** This is the cache-key contract for `localization_evaluations` rows produced by `scripts/fit_calibration.py`. Pipeline-tuning constants (`RANSAC_THRESHOLD_DEFAULT`, `RETRIEVAL_TOP_K_DEFAULT`, the seed value, the OPQ/PQ subvector counts) live as module-level Python constants — baked into the image — so changing them forces a code change inside the localizer's build context, a new `LOCALIZER_SHA`, and automatic invalidation of any calibration that was fit against the previous pipeline. Env-var tunables would silently bypass this. The hash is intentionally scoped to the localizer's build context rather than the repo's git HEAD: unrelated commits (Unity apps, prose, other services) do not invalidate calibration. The cost is that *every* localizer-affecting change requires a paired calibration refit + `global.json` commit before the container boots cleanly — except when the calibration uses the `"placeholder"` sentinel, which disarms the check explicitly for pipeline-independent values (zeroed weights, fixed sigmas).

**The localizer talks reconstructions; the API talks maps.** The `map_id -> reconstruction_id` indirection lives in the API, which also composes the final world-space pose by combining the localizer's `cam_from_reconstruction` transform with the map row's anchor `Transform`. The localizer never sees the world-space anchor; it operates purely in reconstruction-local coordinates. Decoupling means a reconstruction can back multiple maps (different anchors of the same scan) without re-uploading artifacts.

**`async def localize_image` with synchronous body.** The async signature is required by Litestar's route handler protocol; the body is synchronous because every heavy step is. With one uvicorn worker, requests serialize on the event loop. Concurrent throughput would require either offloading to `_executor` (declared but unused) or running multiple workers — but the GPU is the bottleneck either way and they'd serialize on it. The current shape acknowledges this.

## See also

- `docker/SPEC.md` — stack-level data flow, log query patterns, MinIO bucket layout, reconstructor lease lifecycle. The localizer is one consumer of `dev-reconstructions/`; this file does not restate the bucket schema.
- `packages/python/core/` — `calibration.py` (Features / CalibrationArtifact / apply_global_calibration), `h5.py`, `opq.py`, `image_preprocess.py`, `model_wrappers.py`, `localization_metrics.py` carry the shared domain types and the canonical hyperparameter defaults the localizer reads.
- `scripts/python/src/scripts/fit_calibration.py` — produces `config/calibration/global.json` from a labeled corpus. The localizer is strictly a consumer; refits land as commits to that file plus a paired image rebuild at the same `LOCALIZER_SHA`.
- `build/src/build_scripts/placeframe/context_sha.py` — defines `compute_service_shas`, which derives `LOCALIZER_SHA` (and one such SHA per service) from the localizer image's build context per the `.dockerignore` allowlist convention described in the repo `CLAUDE.md`.
- `docker/api/src/routers/localization.py` — the only caller. Performs the `map_id -> reconstruction_id` indirection and composes the world-space pose from the map row's anchor `Transform`.
