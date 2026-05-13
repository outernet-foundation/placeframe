# docker/reconstructor/

## What this is

The reconstructor is a single-process GPU worker that turns capture sessions into sparse 3D maps. It pulls jobs over a Postgres-backed lease API, downloads a tar of images and VIO truth poses from MinIO, runs an eight-phase pipeline (extract features, generate pairs, train OPQ/PQ, encode, match, verify two-view geometry, run COLMAP incremental SfM, upload), and writes the resulting artifacts back to MinIO at `dev-reconstructions/<reconstruction_id>/`. Stack-level data flow and the recovery gap that motivates this SPEC's failure-mode section are in `docker/SPEC.md`.

## Shape

### Layout

```
docker/reconstructor/
|-- Dockerfile             FROM neural-networks-base; PYTORCH_ALLOC_CONF=expandable_segments:True
|-- entrypoint.sh          uv run reconstructor (debugpy when DEBUG=true)
|-- pyproject.toml         core, common, placeframe-api-client, pycolmap, scipy
|-- src/reconstructor/
|   |-- main.py            worker_loop -- lease poll + dispatch + succeed/fail
|   |-- run_reconstruction.py   model load + pipeline orchestrator
|   |-- colmap.py          COLMAP DB build, two-view verification, incremental SfM,
|   |                      single-anchor Sim3d alignment, Umeyama diagnostic, npz writers
|   |-- rig.py             Parses frames.csv, applies axis conventions, builds ColmapRigConfig
|   |-- pairs.py           Pose-proximity pair generation + intra-frame stereo pairs
|   |-- options_builder.py ReconstructionOptions -> pycolmap option structs
|   |-- metrics_builder.py Verified-match buckets + reconstruction-quality metrics
|   |-- progress_publisher.py ~2 Hz throttled progress PUT into the API
|   `-- settings.py        pydantic-settings: API URL, auth, MinIO creds, bucket names
`-- tests/
    `-- test_rig.py        Held-out-timestamp filter (the only test)
```

### Lease loop

`main.worker_loop` (`src/reconstructor/main.py:26`) is a single coroutine that:

1. Builds a `TokenManager` against `auth_token_url` with the RSA private key at `private_key_path` (`common.token_manager.TokenManager`, OAuth2 client-credentials with a JWT client-assertion).
2. Loops:
   - Refreshes the bearer token; writes it into both `configuration.access_token` and `api_client.default_headers["Authorization"]`.
   - `await api.request_lease()`. 404 -> sleep 5 s. Any other `ApiException` -> log critical error, sleep 5 s. There is no exponential backoff and no separate 401 handler (the next iteration's token refresh covers token expiry).
   - Build a `ReconstructionPublisher` and dispatch `run_reconstruction(...)` onto `loop.run_in_executor(None, ...)`. The pipeline is fully sync; the default executor (a `ThreadPoolExecutor`) runs it on a worker thread while the event loop stays live to service progress writes.
   - On success: `await api.succeed_lease(reconstruction_id, metrics)`. On any pipeline-or-succeed exception: `await api.fail_lease(reconstruction_id, str(e))`.
   - `CancelledError` exits cleanly. Any other exception sleeps 5 s and re-loops.

Concurrency: the worker holds at most one in-flight job. Horizontal scale is N replicas; `request_lease` uses `SELECT ... FOR UPDATE SKIP LOCKED` on the API side so replicas can poll the queue safely. The DB-side `LEASE_TIMEOUT = 30 minutes` (`docker/api/src/routers/leases.py:21`) is the only ceiling on a job; the worker enforces no wall-clock limit of its own.

SIGTERM is wired through `signal(SIGTERM, handle_sigterm)` to raise `CancelledError`. The event loop catches it cleanly, but the executor thread cannot be cancelled, so a SIGTERM mid-reconstruction lets the pipeline keep running until it returns. The worker may exit before having marked the lease terminal.

### Pipeline phases

`run_reconstruction(reconstruction_id, capture_id, options, publisher)` (`src/reconstructor/run_reconstruction.py:78`) is `@inference_mode()` and returns a `ReconstructionMetrics`. Phases are published via `ReconstructionPublisher.set_phase`, which corresponds to the `ReconstructionStatus` enum that the row's `status` column tracks. Order:

1. **`DOWNLOADING`** -- `s3_client.get_object(captures_bucket, "<capture_id>.tar")["Body"].read()` pulls the entire tar into RAM, then `tarfile.extractall` into `/tmp/reconstruction/capture_session`. `manifest.json` is parsed into `CaptureSessionManifest`. Rigs are built (`rig.py`): each rig must have exactly one ref-sensor camera with identity pose; multi-camera rigs are restricted to the OpenCV axis convention; held-out frame timestamps drop matching rows from `frame_poses` here.
2. **(silent)** Pair generation. `pairs.generate_image_pairs` (`src/reconstructor/pairs.py:17`) builds proximal frame pairs by camera-center Euclidean distance gated on optical-axis angular difference (`rotation_threshold_deg`, default 30); torch `topk` selects up to `neighbors_count` (default 12) neighbors per frame. Image pairs cross all cameras of rig A against all cameras of rig B for each proximal frame pair, plus all intra-frame camera pairs. Pairs are canonicalized as `(min, max)`, deduped, sorted. `pairs.txt` uploads immediately. No phase is published for this step.
3. **`EXTRACTING_FEATURES`** -- per image: orientation-canonicalize, write back over the on-disk JPG (so COLMAP samples the processed image for point-cloud colorization), then run ALIKED locally and DIR per-tile globally. ALIKED's `dkd.n_limit` was mutated on the module-global model instance at the top of the pipeline to honor `max_keypoints_per_image` (default 2500). `global_descriptors.h5` uploads at the end of this phase.
4. **`TRAINING_OPQ_MATRIX`** -- all per-image descriptors are `vstack`-ed into one contiguous array; FAISS trains the OPQ matrix; `opq_matrix.tf` uploads. No per-step progress (single FAISS call).
5. **`TRAINING_PRODUCT_QUANTIZER`** -- FAISS trains the PQ over OPQ-rotated descriptors; `pq_quantizer.pq` uploads. `encode_descriptors` produces per-image uint8 PQ codes; `features.h5` uploads (containing keypoints + PQ codes).
6. **`MATCHING_FEATURES`** -- LightGlue matches each pair with the per-job `lightglue_batch_size`. Progress callback fires per pair; this is the first phase with per-step progress. `cuda.empty_cache()` releases LightGlue's working memory before pycolmap allocates.
7. **`VERIFYING_GEOMETRY`** -- COLMAP database is opened. Cameras, images, keypoints, and per-ref-sensor `PosePrior`s are written. `apply_rig_config` ties images to rig constraints. Matches go in. Then a `ThreadPoolExecutor` fans out `estimate_two_view_geometry` per pair; results return to the main thread which serializes the writes (sqlite is thread-affine -- see `colmap.py:107`). Progress callback fires per completed pair. `MetricsBuilder.build_verified_matches_metrics` runs after close; it bucketizes per pair-type (stereo / same-sensor / cross-sensor) by string-parsing `<rig>/<camera>/<frame>.jpg` image names.
8. **`RECONSTRUCTING`** -- `pycolmap._core.incremental_mapping` is called with two callbacks: `initial_image_pair_callback` and `next_image_callback`. `_IncrementalMappingProgress` (`colmap.py:255`) tracks per-attempt registered count and bumps `_attempt` when a new model attempt starts after a previous attempt registered anything. COLMAP returns a list of models when it cannot fit everything into one; the reconstructor picks the model with the most registered images. The phase total `len(colmap_image_ids)` is an upper bound -- COLMAP may drop or filter-out images.
9. **(post-SfM, in `RECONSTRUCTING`)** Single-anchor `Sim3d` alignment applied to the chosen reconstruction (`colmap.py:166`). Procrustes residual computed and recorded (not applied). `points3D.npz`, `frame_poses.npz`, and the COLMAP plaintext model are written to disk in `WORK_DIR/sfm_output/`.
10. **`UPLOADING`** -- `sfm_output_path.rglob("*")` plus one synchronous `put_object` per file under `sfm_model/<relative>`. No concurrency, no retry. This phase covers *only* the `sfm_model/` tree; everything else was uploaded during its compute phase.

The publisher (`src/reconstructor/progress_publisher.py`) uses `asyncio.run_coroutine_threadsafe` to dispatch `update_progress` calls from the executor thread back to the main event loop. `on_progress` is throttled to ~2 Hz; `set_phase` always flushes. Failures are logged via a done-callback but never raised back into the pipeline -- a long stretch of API failures during progress writes is silently swallowed.

### Artifact layout in MinIO

Per reconstruction id under `dev-reconstructions/<id>/`:

| Key | Phase that produced it | Notes |
|---|---|---|
| `pairs.txt` | pair generation | Each line `image_a image_b`. |
| `global_descriptors.h5` | EXTRACTING_FEATURES | Per-image (per-tile) DIR retrieval vectors. |
| `opq_matrix.tf` | TRAINING_OPQ_MATRIX | FAISS-serialized OPQ rotation. |
| `pq_quantizer.pq` | TRAINING_PRODUCT_QUANTIZER | FAISS-serialized PQ. |
| `features.h5` | TRAINING_PRODUCT_QUANTIZER | Keypoints + PQ codes. |
| `sfm_model/` | UPLOADING | COLMAP text dump (cameras.txt, images.txt, points3D.txt, frames.txt) + `points3D.npz` + `frame_poses.npz`. |

Presence of a complete `sfm_model/` is the strongest signal a reconstruction's outputs are final; nothing in the bucket carries an explicit completion sentinel.

### Truth-frame alignment and the Procrustes diagnostic

The first registered frame's COLMAP pose is pinned to its `frames.csv` truth pose via a single-anchor `pycolmap.Sim3d`. This is the load-bearing geometry contract: downstream consumers (the localizer in particular) rely on "first registered frame == map origin in truth coordinates", which makes the localizer's `camera_from_map` doubles as `camera_from_world` for queries from the same capture.

Separately, the reconstructor solves rigid (no-scale) Umeyama Procrustes over all registered frames against their truth poses and records the residual as `truth_alignment_rms_residual_m` and `truth_alignment_max_residual_m`. **The Procrustes transform is not applied** -- only the residual surfaces, as a per-capture VIO-quality diagnostic that the calibration pipeline uses to filter unreliable captures. Requires >=3 registered frames; otherwise the reconstruction fails with a `RuntimeError` from `colmap.py:189`.

### Held-out frames protocol

`ReconstructionOptions.held_out_frame_timestamps: list[int] | None` (Unix milliseconds, matching the first column of each rig's `frames.csv`). Round-trips through MinIO via `manifest.options`; no SQL column exists for it. `Rig.__init__` drops matching frame rows from `frame_poses`, and the image-list construction in `run_reconstruction.py` drops the corresponding images naturally because their poses are no longer present. The calibration pipeline uses this to build a map with specific frames excluded so those frames can later be localized as held-out queries.

### Lease lifecycle cross-reference

The full lease state machine lives in `docker/api/src/routers/leases.py`. Worth knowing here:

- A row's `status` column itself encodes the lease ("claimed" = any non-terminal, non-QUEUED state). There is no separate lease table.
- `LEASE_TIMEOUT = 30 minutes` runs at the start of every `request_lease`: any non-terminal, non-QUEUED row whose `updated_at` is older than 30 minutes flips to `FAILED` with error `"Lease timed out"`. `updated_at` is touched by a Postgres trigger on every progress write, so 2 Hz publisher heartbeats keep the lease alive indefinitely.
- `succeed_lease` merges new `metrics` into the existing `manifest.options` to produce `Manifest(options=existing.options, metrics=data)` and writes it back to the JSONB column. `fail_lease` does not touch the manifest.

## Rationale

**Worker-loop-over-Postgres lease, not a message queue.** Reconstruction is long, restart-survivable, and at-most-once-execution semantics matter (running twice wastes GPU minutes and re-uploads identical artifacts). A Postgres row with `FOR UPDATE SKIP LOCKED` selection gives all three properties without standing up a separate queue. The row also doubles as the user-facing status, which removes a sync.

**Single-process, single-job worker.** GPU memory ownership is exclusive in practice (LightGlue + ALIKED + DIR + pycolmap allocations would fight for VRAM under concurrency). Letting the worker hold at most one job and scaling horizontally by replicas keeps the GPU-allocation model simple. The cost is that mutable globals (`_aliked_model.dkd.n_limit`, `DEVICE`) are safe -- a constraint that would break under in-process concurrency.

**Sync pipeline on a thread, not async coroutines.** pycolmap is C++ with the GIL released; numpy and FAISS likewise. Async-rewriting the pipeline would buy nothing because there is no IO interleaving to exploit during compute phases. The thread-plus-publisher shim is the minimum machinery needed to keep the event loop alive for progress writes.

**Progress writes are fire-and-forget with done-callbacks.** A reconstruction that fails to write progress for a stretch is *still* a reconstruction; aborting compute when the API is briefly unavailable would be strictly worse. The trade-off: a long API outage during a job means the UI loses visibility, and the API-side lease reaper may mark the row `FAILED` if the outage exceeds 30 minutes despite the job actually being healthy.

**Manifest as single source of truth for `ReconstructionOptions`.** Options are written into `manifest.options` at create-time by the API and read at run-time by the reconstructor. No SQL columns mirror them. Reasoning: options are a per-job request envelope, not an indexable property of the row. The same logic extends to `held_out_frame_timestamps`, `is_indoor`, and (post-run) `ReconstructionMetrics`.

**Single-anchor `Sim3d` alignment instead of Procrustes.** Downstream consumers rely on "first registered frame == map origin". Applying Procrustes would average the truth-vs-map residual across all frames, which slightly improves the global fit but breaks the per-capture origin contract that the localizer depends on. Procrustes is therefore only a diagnostic.

**One bundle of artifacts per reconstruction id, S3 prefix-keyed.** All outputs live under `<id>/`, so DELETE cascades and retry-cleanup can operate on a single prefix without a manifest of keys. The cost: there is no explicit "I am done" sentinel inside the prefix; completion is inferred from the presence of `sfm_model/`.

## Known gaps

- **No reconciliation between MinIO and DB status.** If `succeed_lease` fails after `sfm_model/` has fully uploaded, the row stays at `UPLOADING` until the API-side reaper marks it `FAILED` 30 minutes later, even though the artifacts are complete. Nothing scans MinIO to recover. `docker/SPEC.md` flags this; the worker code path is `src/reconstructor/main.py:74-82` (succeed/fail both inside the outer try, no retry on the lease finalization itself).
- **`fail_lease` failure cascades to "lease never marked terminal".** When `await api.fail_lease(...)` raises (transient API outage), the exception escapes to the outer critical-error handler. The lease then dangles until the 30-minute reaper.
- **SIGTERM does not stop in-flight reconstruction.** The executor thread is uncancellable; a SIGTERM cancels the event loop's wait but the pipeline keeps running until it returns naturally. A graceful shutdown that lets the current job finish is the practical behavior; an aborted-job-with-clean-state shutdown is not implemented.
- **Retry does not purge prior MinIO outputs.** `POST /reconstructions/{id}/retry` (`docker/api/src/routers/reconstructions.py:192`) flips a FAILED/CANCELLED row back to QUEUED without deleting the `<id>/` prefix. The next reconstruction overwrites by key, so duplicate keys are clean, but artifacts written under prefixes the new run doesn't visit (e.g. an old `sfm_model/extra_model_N/`) survive.
- **Capture tar held entirely in RAM.** `run_reconstruction.py:96` reads the whole `.tar` into `bytes` before extracting. For multi-GB captures this is a hard RAM ceiling; streaming extract would suffice.
- **`CAPTURE_SESSION_DIRECTORY` is not cleaned between jobs.** `/tmp/reconstruction/capture_session` is the extraction target; `tarfile.extractall` overlays on top of any existing tree. Stale files from a previous job that aren't overwritten by the new tar persist.
- **`_aliked_model.dkd.n_limit` is mutated on a module-global singleton** (`run_reconstruction.py:131`) per job. Safe only because the worker is single-job-per-process; a second concurrent job in the same process would race.
- **`options.single_threaded` is silently ignored.** The field exists in `ReconstructionOptions`; the matching `incremental_pipeline_options.num_threads = 1` lines in `options_builder.py:72-73` are commented out. "Deterministic mode" is not actually wired up.
- **`options.bundle_adjustment_refine_additional_params` is silently ignored.** Declared in `reconstruction_options.py:105`; `OptionsBuilder.incremental_pipeline_options` has no corresponding `ba_refine_extra_params` assignment.
- **`OptionsBuilder.feature_matching_options` is dead.** LightGlue replaced COLMAP feature matching; the function builds a `FeatureMatchingOptions` that nobody reads.
- **`pairs.pairs_from_retrieval` is dead.** Defined in `pairs.py:79` but unreferenced; appears to be a vestige of an earlier retrieval-based pair-gen path.
- **Multi-model situations are not surfaced in metrics.** `colmap.py:153` has a `# TODO: Write information to metrics about this for visibility`. When `incremental_mapping` returns multiple models the worker picks the largest and discards the rest; the existence of multiple models is invisible to the API.
- **Phase naming is misleading.** `UPLOADING` is *only* the `sfm_model/` tree upload; everything else is uploaded during its compute phase. "Stuck at UPLOADING" can also mean "stuck before the upload loop starts."
- **Pair generation publishes no phase.** The transition `DOWNLOADING -> EXTRACTING_FEATURES` skips over pair generation, so the row sits at `DOWNLOADING` while pairs are being computed.
- **`OPQ_MATRIX_FILE` / `PQ_QUANTIZER_FILE` phases publish no per-step progress** (single FAISS call each). UI sees a phase change with no in-phase movement until the next phase.
- **No integration test.** `tests/test_rig.py` only covers the held-out filter on `Rig`. The pipeline as a whole has no end-to-end test; `tests/__init__.py` is empty.
- **`template.Dockerfile` is empty** (one blank line); `README.md` is empty. Both are vestigial.
- **`# noqa: TID251 -- Phase T piece 3 follow-up migration`** markers in `run_reconstruction.py`, `colmap.py`, `pairs.py`, `metrics_builder.py`, `rig.py`. Temporal language plus an external-context pointer; both violate the project conventions on comments.

## Decisions

### D1 -- Single-anchor Sim3d alignment over Procrustes (2025-09)

**Status:** accepted

**Context:** Reconstructions produce maps that the localizer queries at runtime. The localizer treats `camera_from_map` as `camera_from_world` for queries served from the same capture. This only works if "map origin" has a defined relationship to "world origin". Two candidates: pin the first registered frame, or fit all registered frames to truth via Procrustes.

**Decision:** Pin the first registered frame's COLMAP pose to its `frames.csv` truth pose via a single-anchor `pycolmap.Sim3d`. Compute Procrustes residual separately as a per-capture diagnostic; do not apply it.

**Consequences:** Localizer code is simpler (no per-query alignment). Procrustes residual surfaces as `truth_alignment_rms_residual_m` and `truth_alignment_max_residual_m`, which the calibration pipeline uses to filter unreliable captures from the corpus. The Procrustes fit itself is computed once at map-build time; runtime impact is none. Trade-off: maps from captures with poor VIO inherit the poor truth pose of their first registered frame as their origin; the diagnostic surfaces this but doesn't correct it.

### D2 -- Manifest in MinIO as the round-trip for `ReconstructionOptions` (2025-09)

**Status:** accepted

**Context:** `ReconstructionOptions` is a per-job request envelope with ~20 nullable fields. It needs to travel from the API (request-time) to the reconstructor (run-time) and survive in storage for later inspection. Options: mirror as SQL columns, or write into MinIO alongside the artifacts.

**Decision:** Store the full options structure in the row's `manifest` JSONB column under `Manifest.options`. The reconstructor reads it from the lease response; the API writes it at create-time. `held_out_frame_timestamps`, `is_indoor`, and post-run `ReconstructionMetrics` follow the same pattern.

**Consequences:** No schema migration for new option fields. The manifest is the single source of truth for "what was requested." Trade-off: options cannot be indexed in SQL; queries like "find reconstructions with random_seed=42" require a JSONB scan. This is acceptable because options are inspected per-row, not filtered at scale.

## See also

- `docker/SPEC.md` -- stack-level data flow, MinIO bucket layout, lease lifecycle from the operational-debugging angle. Includes the "sfm_model/ presence means SfM completed regardless of DB status" recovery hazard documented from the operator's perspective.
- `docker/api/src/routers/leases.py` -- the API-side lease state machine (request, progress, succeed, fail, reaper). Read this when reasoning about timeout or recovery behavior.
- `packages/python/core/src/core/reconstruction_options.py` and `reconstruction_metrics.py` -- the shared option / metric schema. The reconstructor reads options, writes metrics; both flow through the row's `manifest` column.
