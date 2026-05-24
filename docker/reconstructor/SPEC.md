# docker/reconstructor/

## What this is

The reconstructor is a single-process GPU worker that turns capture sessions into sparse 3D maps. It pulls jobs over a Postgres-backed lease API, downloads a tar of images and VIO truth poses from MinIO, runs a six-phase pipeline (extract features, generate pairs, train OPQ/PQ, encode, match, verify two-view geometry, run COLMAP incremental SfM), and writes the resulting artifacts back to MinIO at `dev-reconstructions/<reconstruction_id>/`. Stack-level data flow and the recovery gap that motivates this SPEC's failure-mode section are in `docker/SPEC.md`.

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
|   |                      pose-prior write, translation-only Sim3d, Umeyama diagnostic, npz writers
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

1. **(pre-work, status=`EXTRACTING_FEATURES`)** Set by the lease handler (`docker/api/src/routers/leases.py:71-72`) when the lease is granted. The reconstructor's first acts under this status are `s3_client.get_object(captures_bucket, "<capture_id>.tar")["Body"].read()` (whole tar into RAM), `tarfile.extractall` into `/tmp/reconstruction/capture_session`, `manifest.json` parse into `CaptureSessionManifest`, and rig build (`rig.py`): each rig must have exactly one ref-sensor camera with identity pose; multi-camera rigs are restricted to the OpenCV axis convention; held-out frame timestamps drop matching rows from `frame_poses` here. No per-step progress.
2. **(silent)** Pair generation. `pairs.generate_image_pairs` (`src/reconstructor/pairs.py:17`) builds proximal frame pairs by camera-center Euclidean distance gated on optical-axis angular difference (`rotation_threshold_deg`, default 30); torch `topk` selects up to `neighbors_count` (default 12) neighbors per frame. Image pairs cross all cameras of rig A against all cameras of rig B for each proximal frame pair, plus all intra-frame camera pairs. Pairs are canonicalized as `(min, max)`, deduped, sorted. `pairs.txt` uploads immediately. No phase change; status stays at `EXTRACTING_FEATURES`.
3. **`EXTRACTING_FEATURES` (with progress)** -- per image: orientation-canonicalize, write back over the on-disk JPG (so COLMAP samples the processed image for point-cloud colorization), then run ALIKED locally and DIR per-tile globally. ALIKED's `dkd.n_limit` was mutated on the module-global model instance at the top of the pipeline to honor `max_keypoints_per_image` (default 2500). `global_descriptors.h5` uploads at the end of this phase. `set_phase(EXTRACTING_FEATURES, total=len(images))` re-emits with the real total, replacing the lease-time no-progress placeholder.
4. **`TRAINING_OPQ_MATRIX`** -- all per-image descriptors are `vstack`-ed into one contiguous array; FAISS trains the OPQ matrix; `opq_matrix.tf` uploads. No per-step progress (single FAISS call).
5. **`TRAINING_PRODUCT_QUANTIZER`** -- FAISS trains the PQ over OPQ-rotated descriptors; `pq_quantizer.pq` uploads. `encode_descriptors` produces per-image uint8 PQ codes; `features.h5` uploads (containing keypoints + PQ codes).
6. **`MATCHING_FEATURES`** -- LightGlue matches each pair with the per-job `lightglue_batch_size`. Progress callback fires per pair; this is the first phase with per-step progress emitted from inside the pipeline. `cuda.empty_cache()` releases LightGlue's working memory before pycolmap allocates.
7. **`VERIFYING_GEOMETRY`** -- COLMAP database is opened. Cameras, images, keypoints, and per-ref-sensor `PosePrior`s are written. `apply_rig_config` ties images to rig constraints. Matches go in. Then a `ThreadPoolExecutor` fans out `estimate_two_view_geometry` per pair; results return to the main thread which serializes the writes (sqlite is thread-affine -- see `colmap.py:107`). Progress callback fires per completed pair. `MetricsBuilder.build_verified_matches_metrics` runs after close; it bucketizes per pair-type (stereo / same-sensor / cross-sensor) by string-parsing `<rig>/<camera>/<frame>.jpg` image names.
8. **`RECONSTRUCTING`** -- `pycolmap._core.incremental_mapping` is called with two callbacks: `initial_image_pair_callback` and `next_image_callback`. `_IncrementalMappingProgress` (`colmap.py:255`) tracks per-attempt registered count and bumps `_attempt` when a new model attempt starts after a previous attempt registered anything. COLMAP returns a list of models when it cannot fit everything into one; the reconstructor picks the model with the most registered images. The phase total `len(colmap_image_ids)` is an upper bound -- COLMAP may drop or filter-out images.
9. **(post-SfM, in `RECONSTRUCTING`)** Translation-only `Sim3d` applied to the chosen reconstruction so the first registered frame (sorted by integer `frame_id`) lands at the origin (`colmap.py:192-200`). Rotation was already anchored to VIO world during BA via the pose priors written at phase 7. Procrustes residual computed and recorded (not applied). `points3D.npz`, `frame_poses.npz`, and the COLMAP plaintext model are written to disk in `WORK_DIR/sfm_output/`. The `sfm_model/` tree then uploads via `sfm_output_path.rglob("*")` + one synchronous `put_object` per file. No phase change; status stays at `RECONSTRUCTING` through the upload.

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
| `sfm_model/` | RECONSTRUCTING (post-SfM) | COLMAP text dump (cameras.txt, images.txt, points3D.txt, frames.txt) + `points3D.npz` + `frame_poses.npz`. |

Presence of a complete `sfm_model/` is the strongest signal a reconstruction's outputs are final; nothing in the bucket carries an explicit completion sentinel.

### Truth-frame alignment and the Procrustes diagnostic

The map's relationship to the capture's VIO truth frame is established in two stages:

1. **Rotation: pose priors during BA.** Each registered ref-sensor image gets a `PosePrior` carrying its `frames.csv` translation (expressed in the gravity-aligned VIO world frame) with a per-call sigma (`colmap.py:96-108`). Bundle adjustment with N priors spread over the trajectory pins COLMAP world rotation to VIO world rotation to within sub-degree by construction -- the only rotation that lets all N camera positions match their priors is the one that aligns COLMAP world to VIO world. No explicit rotation correction is applied; introducing one (e.g. snapping a chosen frame's pose to its VIO pose) would force one frame to fit exactly at the cost of pulling every other frame off its prior.
2. **Translation: translation-only `Sim3d` post-BA.** After BA converges, `best_reconstruction.transform` is called with a `Sim3d` whose rotation is identity and whose translation places the first registered frame (sorted by integer `frame_id` so multi-rig captures interleave by timestamp) at the origin (`colmap.py:192-200`). The map origin lands where capture started -- natural reference for manual Cesium georegistration. This preserves the load-bearing downstream contract "first registered frame == map origin in truth coordinates", which makes the localizer's `camera_from_map` double as `camera_from_world` for queries from the same capture.

Separately, the reconstructor solves rigid (no-scale) Umeyama Procrustes over all registered frames against their truth poses and records the residual as `truth_alignment_rms_residual_m` and `truth_alignment_max_residual_m`. **The Procrustes transform is not applied** -- only the residual surfaces, as a per-capture VIO-quality diagnostic that the calibration pipeline uses to filter unreliable captures. Requires >=3 registered frames; otherwise the reconstruction fails with a `RuntimeError` from `colmap.py:210-211`.

`frames.csv` is recorded live (each row appended at frame-capture time, not regenerated post-hoc) -- verified at `docker/zed-capture/src/zed/zed.py:309-322` (`update_pose` + immediate `csv_writer.writerow`) and `packages/unity/Placeframe/Assets/Package/Core/Runtime/CaptureManager.cs:43` (`AutoFlush=true`). Frame 0's row reflects the SDK's world-Y as of T_0 (cold-start), and frame N's row reflects the SDK's world-Y as of T_N (converged). Pose-prior anchoring weights every registered frame in BA, so cold-start error on early frames is averaged across the trajectory rather than baked into the origin.

### Map gravity accuracy

End-to-end angular error between the map's Y axis and true local vertical, after the pose-prior BA anchor, at typical capture conditions:

| Source                                                                                | Typical end-to-end gravity error                  |
|---|---|
| ARFoundation (ARCore / ARKit)                                                         | 0.5--1° after warm-up, worse for first few seconds |
| ZED X with `enable_imu_fusion=True` (`docker/zed-capture/src/zed/zed.py:217-222`)      | <0.5°                                              |

Leverage table -- visible vertical overlay error at horizontal distance D from map origin for a given tilt:

| Distance | 1°     | 0.5°   | 0.3°   |
|---|---|---|---|
| 1 m      | 1.7 cm | 0.9 cm | 0.5 cm |
| 5 m      | 8.7 cm | 4.4 cm | 2.6 cm |
| 20 m     | 35 cm  | 17 cm  | 10 cm  |
| 50 m     | 87 cm  | 44 cm  | 26 cm  |

For room and building scales (up to ~20 m) the pose-prior anchor delivers single-digit-cm typical and ~17 cm worst-case multi-room overlay error -- acceptable for the AR use cases Placeframe targets.

To measure attitude error for real (no published benchmark exists for ARCore/ARKit/ZED X), the cheapest proxy is to capture the same scene twice and fit floor planes in both reconstructions: the angle between them is a lower bound on between-session random+systematic error. More rigorous: capture against a precision inclinometer or a known plumb-line reference.

### OS-fused gravity sensor (considered and rejected)

Sampling `Sensor.TYPE_GRAVITY` (Android) / `CMMotionManager.deviceMotion.gravity` (iOS) / `SensorsData.get_imu_data()` (ZED) as a separate per-frame capture-format column was considered as a way to tighten map gravity below 0.5°. Rejected because: at rest, OS gravity and the AR SDK's world-Y agree (both ultimately derive from the same accelerometer reading); during motion they can differ transiently, but that difference vanishes the moment the device is stationary. AR SDKs already run continuous gravity refinement internally, so a warmed-up SDK's reported camera rotation at a stable frame is at least as good as a separately-sampled OS sensor would be. Reopen only if measurements show pose-prior gravity is materially insufficient at our target scales.

### Held-out frames protocol

`ReconstructionOptions.held_out_frame_timestamps: list[int] | None` (Unix milliseconds, matching the first column of each rig's `frames.csv`). Round-trips through MinIO via `manifest.options`; no SQL column exists for it. `Rig.__init__` drops matching frame rows from `frame_poses`, and the image-list construction in `run_reconstruction.py` drops the corresponding images naturally because their poses are no longer present. The calibration pipeline uses this to build a map with specific frames excluded so those frames can later be localized as held-out queries.

### Lease lifecycle cross-reference

The full lease state machine lives in `docker/api/src/routers/leases.py`. Worth knowing here:

- A row's `status` column itself encodes the lease ("claimed" = any non-terminal, non-QUEUED state). There is no separate lease table.
- `LEASE_TIMEOUT = 30 minutes` runs at the start of every `request_lease`: any non-terminal, non-QUEUED row whose `updated_at` is older than 30 minutes flips to `FAILED` with error `"Lease timed out"`. `updated_at` is touched by a Postgres trigger on every progress write, so 2 Hz publisher heartbeats keep the lease alive indefinitely.
- `succeed_lease` merges new `metrics` into the existing `manifest.options` to produce `Manifest(options=existing.options, metrics=data)` and writes it back to the JSONB column. `fail_lease` does not touch the manifest.

## Constraints

**Worker-loop-over-Postgres lease, not a message queue.** Reconstruction is long, restart-survivable, and at-most-once-execution semantics matter (running twice wastes GPU minutes and re-uploads identical artifacts). A Postgres row with `FOR UPDATE SKIP LOCKED` selection gives all three properties without standing up a separate queue. The row also doubles as the user-facing status, which removes a sync.

**Single-process, single-job worker.** GPU memory ownership is exclusive in practice (LightGlue + ALIKED + DIR + pycolmap allocations would fight for VRAM under concurrency). Letting the worker hold at most one job and scaling horizontally by replicas keeps the GPU-allocation model simple. The cost is that mutable globals (`_aliked_model.dkd.n_limit`, `DEVICE`) are safe -- a constraint that would break under in-process concurrency.

**Sync pipeline on a thread, not async coroutines.** pycolmap is C++ with the GIL released; numpy and FAISS likewise. Async-rewriting the pipeline would buy nothing because there is no IO interleaving to exploit during compute phases. The thread-plus-publisher shim is the minimum machinery needed to keep the event loop alive for progress writes.

**Progress writes are fire-and-forget with done-callbacks.** A reconstruction that fails to write progress for a stretch is *still* a reconstruction; aborting compute when the API is briefly unavailable would be strictly worse. The trade-off: a long API outage during a job means the UI loses visibility, and the API-side lease reaper may mark the row `FAILED` if the outage exceeds 30 minutes despite the job actually being healthy.

**Manifest as single source of truth for `ReconstructionOptions`.** Options are written into `manifest.options` at create-time by the API and read at run-time by the reconstructor. No SQL columns mirror them. Reasoning: options are a per-job request envelope, not an indexable property of the row. The same logic extends to `held_out_frame_timestamps`, `is_indoor`, and (post-run) `ReconstructionMetrics`.

**First-frame origin instead of Procrustes mean.** Downstream consumers rely on "first registered frame == map origin". Applying Procrustes would average the truth-vs-map residual across all frames, which slightly improves the global fit but breaks the per-capture origin contract that the localizer depends on. Procrustes is therefore only a diagnostic. The origin anchor itself is a translation-only `Sim3d`; rotation alignment to VIO world is handled separately by pose priors during BA.

**One bundle of artifacts per reconstruction id, S3 prefix-keyed.** All outputs live under `<id>/`, so DELETE cascades and retry-cleanup can operate on a single prefix without a manifest of keys. The cost: there is no explicit "I am done" sentinel inside the prefix; completion is inferred from the presence of `sfm_model/`.

**The incremental-pipeline controller drops Ceres linear-solver knobs.** `IncrementalPipelineOptions::GlobalBundleAdjustment()` (`colmap/controllers/incremental_pipeline.cc:159-233`, verified at COLMAP SHA `dec2ec4b4daa53f51cbe0d25edb28bcd2c164718`) returns a fresh `BundleAdjustmentOptions` populated from `IncrementalPipelineOptions` fields. The set of fields it copies includes the refine_* booleans, the per-call iter caps, the function tolerances, and `ba_use_gpu`. It does **not** copy `linear_solver_type`, `preconditioner_type`, or `auto_select_solver_type` -- those defaults stay as constructed (`auto_select_solver_type = true`, which at our scale resolves to `SUITE_SPARSE`). There is no Python-side path through `pycolmap.incremental_mapping()` to override the linear-solver choice for global BA. The `OptionManager` indirection that the COLMAP CLI uses to inject these is not exposed in the pybind11 surface for `incremental_mapping`.

**cuDSS / GPU BA is equivalent to SuiteSparse at our problem size.** A custom pycolmap wheel built against Ceres+cuDSS was measured on capture `68cd9dfd` (n=318 cameras, RTX 4080) and produced no measurable wall-clock improvement vs. SuiteSparse. The custom-wheel infrastructure has been removed; not worth re-pursuing unless problem size grows by an order of magnitude.

**GLOMAP cannot replace incremental SfM for our use case.** `pycolmap.global_mapping()` (the GLOMAP entry point) does not apply pose-prior position residuals during its bundle-adjustment stage. Priors are only fed into rotation averaging (`colmap/sfm/global_mapper.cc:113-122`); the BA stage calls plain `RunBundleAdjustment` without prior residuals (`global_mapper.cc:324-325, 360-361` contain TODOs explicitly noting this is unimplemented). For ARFoundation mono captures, priors are the only thing pinning scale and absolute pose, so a GLOMAP run would float the entire reconstruction during BA. Incremental SfM is the only viable path while GLOMAP lacks priors-in-BA support.

**Rig refinement at the end, not throughout.** The reconstructor runs `pycolmap.incremental_mapping` with rig refinement disabled (`ba_refine_sensor_from_rig=False`, `constant_rigs` populated with the rig ids), then runs one final standalone `pycolmap.bundle_adjustment(reconstruction, opts)` with rig refinement re-enabled. Rig refinement on every one of ~33 global-BA events during a typical incremental run scales N times; doing it once at the end against the final geometry is structurally cheaper, and the standalone BA gets an uncapped solve to let the rig parameters settle.

**`mapper.ba_global_ignore_redundant_points3D = True`.** Two-stage solve: BA without redundant 3D points first, then refine pruned points with everything else fixed. Same final geometry, smaller main problem. Activates only when the reconstruction has at least 10 registered frames (COLMAP-side gate).

**`bundle_adjustment_global_max_refinements` defaults to 1, dev-biased.** Well below COLMAP's default of `5`. Each refinement is one full BA solve plus `CompleteAndMergeTracks` plus outlier filter; cutting from 3 to 1 saves roughly 3x of the pose-prior BA block at the cost of fewer outlier-cleanup passes per global-BA event. For production-quality map builds, callers should override to `3` (or higher) and accept the wall-time cost. The final standalone BA pass partially backstops the lower default, but it cannot recover all the outlier-discovery a multi-refinement schedule provides during the incremental phase. Repo policy, not a defect: iteration speed during pipeline development outweighs marginal map-quality improvements; production map builds explicitly opt back into the higher quality.

**`deterministic_seed` is the single reproducibility knob.** `ReconstructionOptions.deterministic_seed: int | None` is the only way to request a reproducible reconstruction. When set, the value pins the PRNG seed for the pipeline / triangulation / RANSAC AND forces single-threaded BA (`num_threads = 1` on both `IncrementalPipelineOptions` and the inner `mapper`). When `None`, the reconstruction is non-deterministic. The two older fields this replaces (`random_seed` and `single_threaded`) were footguns. `random_seed` alone was a lie: BA thread scheduling still varied between runs, so reruns drifted despite a pinned seed. `single_threaded` alone was a lie: each run drew a fresh PRNG seed, so reruns drifted despite pinned threading. Every "interesting" state of the original pair was the paired state; collapsing eliminates the broken-but-plausible combinations.

### Manifest in MinIO as the round-trip for `ReconstructionOptions`

**Context:** `ReconstructionOptions` is a per-job request envelope with ~20 nullable fields. It needs to travel from the API (request-time) to the reconstructor (run-time) and survive in storage for later inspection. The two candidates were: mirror as SQL columns, or write into MinIO alongside the artifacts.

**Constraint:** Store the full options structure in the row's `manifest` JSONB column under `Manifest.options`. The reconstructor reads it from the lease response; the API writes it at create-time. `held_out_frame_timestamps`, `is_indoor`, and post-run `ReconstructionMetrics` follow the same pattern.

**Consequences:** No schema migration for new option fields. The manifest is the single source of truth for "what was requested." Trade-off: options cannot be indexed in SQL; queries like "find reconstructions with random_seed=42" require a JSONB scan. Acceptable because options are inspected per-row, not filtered at scale.

### Pose priors anchor rotation; translation-only Sim3d anchors first-frame origin

**Context:** An earlier approach pinned the first registered frame's full COLMAP pose to its `frames.csv` truth pose via a single-anchor `pycolmap.Sim3d`. Cold-start gravity error on that first frame -- VIO's world-Y not yet refined when capture began -- leaked directly into the map's gravity axis, where it leveraged into vertical overlay error scaling with distance from origin (~1 cm per meter at 0.5° tilt). The alternative of fitting all registered frames to truth via Procrustes was rejected because averaging the truth-vs-map residual across all frames breaks the per-capture "first registered frame == map origin" contract that the localizer's `camera_from_map`-as-`camera_from_world` shortcut depends on.

**Constraint:** Write a translation-only `PosePrior` (with per-call sigma) into the COLMAP database for every registered ref-sensor image. Bundle adjustment with N priors spread across the trajectory pins COLMAP world rotation to VIO world rotation to within sub-degree by construction -- the only rotation that lets all N priors fit their image centers is the one that aligns COLMAP world to VIO world. After BA, apply a translation-only `Sim3d` (rotation = identity, translation = -first_camera_position) so the first registered frame's center lands at the origin. Procrustes Umeyama is computed but not applied; it surfaces as `truth_alignment_rms_residual_m` and `truth_alignment_max_residual_m` per-capture diagnostics that the calibration pipeline uses to filter unreliable captures from the corpus.

**Consequences:** Cold-start gravity error is averaged across all priors instead of being baked into the origin's rotation, lowering typical map gravity error from ~1° to ~0.3--0.5° (ARFoundation) and to <0.5° (ZED X with IMU fusion). The downstream contract "first registered frame == map origin in truth coordinates" still holds for translation. Trade-off: the pose-prior sigma (`options.pose_prior_position_sigma_m()`) is a tunable that affects how strongly BA is pulled toward VIO truth vs. visual reprojection -- too tight forces VIO drift into the map, too loose lets the reconstruction float.

## See also

- `docker/SPEC.md` -- stack-level data flow, MinIO bucket layout, and the multi-service relationships this reconstructor sits inside.
- `.pulsar/debugging.md` -- operator runbook including the "`sfm_model/` presence means SfM completed regardless of DB status" recovery hazard.
- `docker/api/src/routers/leases.py` -- the API-side lease state machine (request, progress, succeed, fail, reaper). Read this when reasoning about timeout or recovery behavior.
- `packages/python/core/src/core/reconstruction_options.py` and `reconstruction_metrics.py` -- the shared option / metric schema. The reconstructor reads options, writes metrics; both flow through the row's `manifest` column.
