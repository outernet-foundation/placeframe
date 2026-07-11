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
|   |                      pose-prior write (single-camera only), gravity-aligned Sim3d,
|   |                      prior-drift Umeyama diagnostic, npz writers
|   |-- keyframes.py       Distance-based keyframe pre-pass per rig (VIO translation deltas)
|   |-- rig.py             Parses frames.csv (gravity-only, position+gravity, or legacy
|   |                      position+rotation), applies axis conventions, builds ColmapRigConfig
|   |-- pairs.py           Sequential + spatial + retrieval pair generation, plus intra-frame
|   |                      stereo pairs
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

1. **(pre-work, status=`EXTRACTING_FEATURES`)** Set by the lease handler (`docker/api/src/routers/leases.py:71-72`) when the lease is granted. The reconstructor's first acts under this status are `s3_client.get_object(captures_bucket, "<capture_id>.tar")["Body"].read()` (whole tar into RAM), `tarfile.extractall` into `/tmp/reconstruction/capture_session`, `manifest.json` parse into `CaptureSessionManifest`, and rig build (`rig.py`): each rig must have exactly one ref-sensor camera with identity pose; multi-camera rigs are restricted to the OpenCV axis convention; held-out frame timestamps drop matching rows from `frame_poses` here. Each rig then runs an offline distance-based keyframe pre-pass (`keyframes.select_keyframes_by_distance`) over per-frame VIO translations and `frame_poses` is filtered down to the kept set. No per-step progress.
2. **`EXTRACTING_FEATURES` (with progress)** -- per image: orientation-canonicalize, write back over the on-disk JPG (so COLMAP samples the processed image for point-cloud colorization), then run ALIKED locally and DIR per-tile globally. ALIKED's `dkd.n_limit` was mutated on the module-global model instance at the top of the pipeline to honor `max_keypoints_per_image` (default 2500). `global_descriptors.h5` uploads at the end of this phase. `set_phase(EXTRACTING_FEATURES, total=len(images))` re-emits with the real total, replacing the lease-time no-progress placeholder. After all features are extracted (still under `EXTRACTING_FEATURES`, no phase change), `pairs.generate_image_pairs` (`src/reconstructor/pairs.py`) runs once over three pair sources together: sequential (each frame paired with the next `sequential_window`, default 10, frames in its rig's timestamp-sorted order), spatial (each frame paired with its `spatial_neighbors`, default 25, closest in-range neighbours by VIO position within `spatial_max_distance_m`, default 6.0 m — skipped when positions are absent), and retrieval (top `retrieval_neighbors`, default 20, by global-descriptor cosine similarity, max-pooled over per-image tiles and L2-normalized, gated by `retrieval_min_score` plus `retrieval_min_distance_m` when position priors are available). Frame-pair tuples expand into image pairs by crossing all cameras of rig A against all cameras of rig B, plus all intra-frame camera pairs. Pairs are canonicalized as `(min, max)`, deduped, sorted, and `pairs.txt` uploads.
3. **`TRAINING_OPQ_MATRIX`** -- all per-image descriptors are `vstack`-ed into one contiguous array; FAISS trains the OPQ matrix; `opq_matrix.tf` uploads. No per-step progress (single FAISS call).
4. **`TRAINING_PRODUCT_QUANTIZER`** -- FAISS trains the PQ over OPQ-rotated descriptors; `pq_quantizer.pq` uploads. `encode_descriptors` produces per-image uint8 PQ codes; `features.h5` uploads (containing keypoints + PQ codes).
5. **`MATCHING_FEATURES`** -- LightGlue matches each pair with the per-job `lightglue_batch_size`. Progress callback fires per pair; this is the first phase with per-step progress emitted from inside the pipeline. `cuda.empty_cache()` releases LightGlue's working memory before pycolmap allocates.
6. **`VERIFYING_GEOMETRY`** -- COLMAP database is opened. Cameras, images, keypoints, and per-ref-sensor `PosePrior`s are written (the prior write is skipped on captures whose `frames.csv` carries no position columns — see "frames.csv schema" below). `apply_rig_config` ties images to rig constraints. Matches go in. Then a `ThreadPoolExecutor` fans out `estimate_two_view_geometry` per pair; results return to the main thread which serializes the writes (sqlite is thread-affine). Every two-view result is written; there is no prior-based rejection at this stage. Progress callback fires per completed pair. `MetricsBuilder.build_verified_matches_metrics` runs after close; it bucketizes per pair-type (stereo / same-sensor / cross-sensor) by string-parsing `<rig>/<camera>/<frame>.jpg` image names.
7. **`RECONSTRUCTING`** -- `pycolmap._core.incremental_mapping` is called with two callbacks: `initial_image_pair_callback` and `next_image_callback`. `_IncrementalMappingProgress` (`colmap.py:255`) tracks per-attempt registered count and bumps `_attempt` when a new model attempt starts after a previous attempt registered anything. COLMAP returns a list of models when it cannot fit everything into one; the reconstructor picks the model with the most registered images. The phase total `len(colmap_image_ids)` is an upper bound -- COLMAP may drop or filter-out images.
8. **(post-SfM, in `RECONSTRUCTING`)** A single `Sim3d` aligns the chosen reconstruction to the map frame in two parts. Rotation: for each registered frame with a `gravity_in_rig_local` sample, project it through the recon's own rig rotation to get a gravity sample in recon-world; aggregate by per-component median + renormalize; solve the rotation taking that vector to map-down via `Rotation.align_vectors`. Translation: shift so the first registered frame (sorted by integer `frame_id` across rigs) lands at the origin (`colmap.py:193-219`). When no frame carries a gravity sample, the rotation falls back to identity and `gravity_aligned_in_map_frame=False` lands in metrics. The rigid Umeyama best-fit of map centers to position priors is computed only for monocular captures (where translations exist) and recorded as the prior-drift residual; the transform itself is never applied. `points3D.npz`, `frame_poses.npz`, and the COLMAP plaintext model are written to disk in `WORK_DIR/sfm_output/`. The `sfm_model/` tree then uploads via `sfm_output_path.rglob("*")` + one synchronous `put_object` per file. No phase change; status stays at `RECONSTRUCTING` through the upload.

The publisher (`src/reconstructor/progress_publisher.py`) uses `asyncio.run_coroutine_threadsafe` to dispatch `update_progress` calls from the executor thread back to the main event loop. `on_progress` is throttled to ~2 Hz; `set_phase` always flushes. Failures are logged via a done-callback but never raised back into the pipeline -- a long stretch of API failures during progress writes is silently swallowed.

### Artifact layout in MinIO

Per reconstruction id under `dev-reconstructions/<id>/`:

| Key | Phase that produced it | Notes |
|---|---|---|
| `pairs.txt` | pair generation | Each line `image_a image_b`. |
| `pairs_with_source.csv` | pair generation | Header `image_a,image_b,source`. `source` ∈ {`intra_frame_stereo`, `sequential`, `spatial`, `retrieval`}, assigned by `SOURCE_PRECEDENCE` in `pairs.py`. Companion to `pairs.txt`; lets post-hoc diagnostics classify each candidate pair without reconstructing the source from the option grid. |
| `global_descriptors.h5` | EXTRACTING_FEATURES | Per-image (per-tile) DIR retrieval vectors. |
| `opq_matrix.tf` | TRAINING_OPQ_MATRIX | FAISS-serialized OPQ rotation. |
| `pq_quantizer.pq` | TRAINING_PRODUCT_QUANTIZER | FAISS-serialized PQ. |
| `features.h5` | TRAINING_PRODUCT_QUANTIZER | Keypoints + PQ codes. |
| `sfm_model/` | RECONSTRUCTING (post-SfM) | COLMAP text dump (cameras.txt, images.txt, points3D.txt, frames.txt) + `points3D.npz` + `frame_poses.npz`. |
| `database.db` | RECONSTRUCTING (post-SfM) | SQLite COLMAP database in its final post-incremental-mapping state. Carries cameras, images, keypoints, raw matches, and two-view geometries; the verified-pair subset is recoverable from the `two_view_geometries` table. Uploaded last so its presence implies SfM ran to completion. |

Presence of a complete `sfm_model/` is the strongest signal a reconstruction's outputs are final; nothing in the bucket carries an explicit completion sentinel.

### Map-frame alignment

The map frame is the COLMAP reconstruction's world after a single post-SfM `Sim3d` that puts the first registered frame at the origin and rotates so that the capture's gravity direction lies along the map-frame down axis (OPENCV `+Y`).

1. **Rotation: median per-frame gravity.** Every registered frame whose `frames.csv` row carries a `(gx, gy, gz)` triple contributes one sample. The sample is in the frame's local rig coordinates; the recon's own rig rotation projects it into recon-world. Aggregation is per-component median across all samples, then renormalization. `scipy.spatial.transform.Rotation.align_vectors` solves the rotation taking the aggregate to `[0, 1, 0]` (OPENCV down). Median (vs. mean) absorbs per-frame IMU noise and motion-blur outliers; aggregating across the trajectory absorbs VIO tilt drift in either direction. When no frame carries a gravity sample, rotation falls back to identity and `gravity_aligned_in_map_frame=False` records that the map's up axis is whatever COLMAP picked.
2. **Translation: first-frame origin.** After the rotation is known, the translation component of the `Sim3d` is chosen to place the first registered frame's camera center (sorted by integer `frame_id` so multi-rig captures interleave by timestamp) at the origin. This preserves the load-bearing downstream contract "first registered frame == map origin in capture-side coordinates," which lets the localizer's `camera_from_map` double as `camera_from_world` for queries from the same capture.

Separately, on captures that supply position priors (single-camera path; see "frames.csv schema variants" below), the reconstructor solves a rigid Umeyama best-fit of map centers to priors and records the residual as `prior_drift_residual_rms_m` / `_max_m`. **The fit is never applied** — the residual is a per-capture diagnostic for the calibration-corpus filter and for ad-hoc inspection. It is not a quality gate: a correct loop-closed reconstruction must disagree with drifted VIO by several meters, so thresholding on RMS-against-priors false-positives on exactly the reconstructions the pipeline is meant to produce. On the multi-camera priors-off path the residual is `None`.

`frames.csv` is recorded live (each row appended at frame-capture time, not regenerated post-hoc) — verified at `docker/zed-capture/src/zed/zed.py` (`update_pose` + immediate `csv_writer.writerow`) and `packages/unity/Placeframe/Assets/Package/Core/Runtime/CaptureManager.cs` (`AutoFlush=true`). The live append matters because gravity is sampled per-frame: late frames carry the SDK's converged gravity estimate, early frames carry the cold-start estimate, and the post-SfM median absorbs the spread.

### Map gravity accuracy

Per-frame gravity feeds the median across all registered frames, so the map's down axis tracks the SDK's gravity estimate aggregated over the whole capture. Per-frame angular error from the SDK at typical capture conditions:

| Source                                                                                | Typical per-frame gravity error                   |
|---|---|
| ARFoundation (ARCore / ARKit)                                                         | 0.5--1° after warm-up, worse for first few seconds |
| ZED X with `enable_imu_fusion=True` (`docker/zed-capture/src/zed/zed.py`)              | <0.5°                                              |

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

Sampling `Sensor.TYPE_GRAVITY` (Android) / `CMMotionManager.deviceMotion.gravity` (iOS) / `SensorsData.get_imu_data()` (ZED) as the per-frame gravity source instead of projecting the SDK's world-down into rig-local coords was considered. Rejected because: at rest, OS gravity and the AR SDK's world-Y agree (both ultimately derive from the same accelerometer reading); during motion they can differ transiently, but that difference vanishes the moment the device is stationary. AR SDKs already run continuous gravity refinement internally, so a warmed-up SDK's reported `world_from_rig` rotation at a stable frame is at least as good as a separately-sampled OS sensor would be. Reopen only if measurements show median-of-per-frame gravity is materially insufficient at our target scales.

### Held-out frames protocol

`ReconstructionOptions.held_out_frame_timestamps: list[int] | None` (Unix milliseconds, matching the first column of each rig's `frames.csv`). Round-trips through MinIO via `manifest.options`; no SQL column exists for it. `Rig.__init__` drops matching frame rows from `frame_poses`, and the image-list construction in `run_reconstruction.py` drops the corresponding images naturally because their poses are no longer present. The calibration pipeline uses this to build a map with specific frames excluded so those frames can later be localized as held-out queries.

### Lease lifecycle cross-reference

The full lease state machine lives in `docker/api/src/routers/leases.py`. Worth knowing here:

- A row's `status` column itself encodes the lease ("claimed" = any non-terminal, non-QUEUED state). There is no separate lease table.
- `LEASE_TIMEOUT = 30 minutes` runs at the start of every `request_lease`: any non-terminal, non-QUEUED row whose `updated_at` is older than 30 minutes flips to `FAILED` with error `"Lease timed out"`. `updated_at` is touched by a Postgres trigger on every progress write, so 2 Hz publisher heartbeats keep the lease alive indefinitely.
- `succeed_lease` merges new `metrics` into the existing `manifest.options` to produce `Manifest(options=existing.options, metrics=data)` and writes it back to the JSONB column. `fail_lease` does not touch the manifest.

## Constraints

**Priors-on in pair gen, priors-off in BA for multi-camera rigs.** Position priors travel two paths through the reconstructor with very different sensitivity to VIO drift. **Pair generation** uses priors to *choose candidate pairs* (the spatial-neighbour source and the retrieval-distance dedup gate); two-view geometric verification then filters those candidates, so bidirectional drift of a few meters costs only a handful of cheaply-rejected pair tests. **Bundle adjustment** uses priors as a quadratic `PosePrior` loss, so N-meter drift in the priors injects N-meter errors into global geometry — this is the failure mode that motivated priors-off for multi-camera captures (`17af01a0`). The split: multi-camera captures (any rig with more than one camera) run **priors-off in BA** — the stereo baseline anchors metric scale, `PosePrior` rows are not written, and the final standalone BA pass keeps `sensor_from_rig` pinned so the 7-DOF gauge can't dissolve baseline-supplied scale — but **priors-on in pair gen**: `frame_poses[*].translation` is populated from `frames.csv` and consumed by the spatial pair source. Monocular captures run priors-on in both paths: position priors are the only metric-scale and absolute-pose source for BA, and the spatial source pairs them up the same way. The BA gate lives in `colmap.py`'s `write_pose_prior` site (explicitly conditioned on `options.is_multi_camera_capture`, not on `translation is None`). The structural decision is computed by the reconstructor from `Rig.is_multi_camera` — there is no API-side default and no `ReconstructionOptions` toggle. Monocular captures reject 3-column gravity-only `frames.csv` at rig construction.

**`frames.csv` schema is column-count-dispatched.** Three value-column layouts share one parser (`rig._parse_frame_pose`): 3 values `gx,gy,gz` (gravity only; legacy gravity-only experimental schema), 6 values `tx,ty,tz,gx,gy,gz` (position + gravity — what ZED captures write now and the canonical shape for multi-camera capture devices), and 7 values `tx,ty,tz,qx,qy,qz,qw` (legacy position + quaternion; rotation read and discarded — what ARFoundation captures write). The `(gx, gy, gz)` triple is the unit down vector expressed in that frame's local rig coordinates, derived capture-side from the SDK's `world_from_rig` rotation and the SDK world's down axis. The capture upload validator (`docker/api/src/routers/capture_sessions.py:_validate_monocular_rigs_have_position_priors`) rejects 3-value files for monocular rigs at upload time; multi-camera rigs accept any of the three layouts. Translations are kept regardless of rig structure — pair generation consumes them on every path.

**Keyframe selection by VIO translation distance.** Each rig runs an offline pre-pass over its `frame_poses[*].translation` series. The first frame of the rig is always kept; each subsequent frame is kept iff its translation from the last-kept keyframe is at least `keyframe_min_distance_m` (default 0.3 m). Output filters `frame_poses` down to the kept set and the rest of the pipeline sees only keyframes. The previous Lucas-Kanade-parallax selector was removed: median optical flow integrates apparent motion regardless of baseline, so pure rotation in place produced clusters of zero-baseline keyframes, pure forward motion produced too few, and textureless walls forced every frame to be kept via the LK-failure fall-through. Distance-based selection on device priors sidesteps all three failure modes by reading the camera's own VIO translation directly. Requires translations to be present — captures whose `frames.csv` lacks position columns fail loudly at the keyframe step rather than silently degrading to LK behaviour.

**Worker-loop-over-Postgres lease, not a message queue.** Reconstruction is long, restart-survivable, and at-most-once-execution semantics matter (running twice wastes GPU minutes and re-uploads identical artifacts). A Postgres row with `FOR UPDATE SKIP LOCKED` selection gives all three properties without standing up a separate queue. The row also doubles as the user-facing status, which removes a sync.

**Single-process, single-job worker.** GPU memory ownership is exclusive in practice (LightGlue + ALIKED + DIR + pycolmap allocations would fight for VRAM under concurrency). Letting the worker hold at most one job and scaling horizontally by replicas keeps the GPU-allocation model simple. The cost is that mutable globals (`_aliked_model.dkd.n_limit`, `DEVICE`) are safe -- a constraint that would break under in-process concurrency.

**Sync pipeline on a thread, not async coroutines.** pycolmap is C++ with the GIL released; numpy and FAISS likewise. Async-rewriting the pipeline would buy nothing because there is no IO interleaving to exploit during compute phases. The thread-plus-publisher shim is the minimum machinery needed to keep the event loop alive for progress writes.

**Progress writes are fire-and-forget with done-callbacks.** A reconstruction that fails to write progress for a stretch is *still* a reconstruction; aborting compute when the API is briefly unavailable would be strictly worse. The trade-off: a long API outage during a job means the UI loses visibility, and the API-side lease reaper may mark the row `FAILED` if the outage exceeds 30 minutes despite the job actually being healthy.

**Manifest as single source of truth for `ReconstructionOptions`.** Options are written into `manifest.options` at create-time by the API and read at run-time by the reconstructor. No SQL columns mirror them. Reasoning: options are a per-job request envelope, not an indexable property of the row. The same logic extends to `held_out_frame_timestamps`, `is_indoor`, and (post-run) `ReconstructionMetrics`.

**One bundle of artifacts per reconstruction id, S3 prefix-keyed.** All outputs live under `<id>/`, so DELETE cascades and retry-cleanup can operate on a single prefix without a manifest of keys. The cost: there is no explicit "I am done" sentinel inside the prefix; completion is inferred from the presence of `sfm_model/`.

**The incremental-pipeline controller drops Ceres linear-solver knobs.** `IncrementalPipelineOptions::GlobalBundleAdjustment()` (`colmap/controllers/incremental_pipeline.cc:159-233`, verified at COLMAP SHA `dec2ec4b4daa53f51cbe0d25edb28bcd2c164718`) returns a fresh `BundleAdjustmentOptions` populated from `IncrementalPipelineOptions` fields. The set of fields it copies includes the refine_* booleans, the per-call iter caps, the function tolerances, and `ba_use_gpu`. It does **not** copy `linear_solver_type`, `preconditioner_type`, or `auto_select_solver_type` -- those defaults stay as constructed (`auto_select_solver_type = true`, which at our scale resolves to `SUITE_SPARSE`). There is no Python-side path through `pycolmap.incremental_mapping()` to override the linear-solver choice for global BA. The `OptionManager` indirection that the COLMAP CLI uses to inject these is not exposed in the pybind11 surface for `incremental_mapping`.

**cuDSS / GPU BA is equivalent to SuiteSparse at our problem size.** A custom pycolmap wheel built against Ceres+cuDSS was measured on capture `68cd9dfd` (n=318 cameras, RTX 4080) and produced no measurable wall-clock improvement vs. SuiteSparse. The custom-wheel infrastructure has been removed; not worth re-pursuing unless problem size grows by an order of magnitude.

**GLOMAP cannot replace incremental SfM for our use case.** `pycolmap.global_mapping()` (the GLOMAP entry point) does not apply pose-prior position residuals during its bundle-adjustment stage. Priors are only fed into rotation averaging (`colmap/sfm/global_mapper.cc:113-122`); the BA stage calls plain `RunBundleAdjustment` without prior residuals (`global_mapper.cc:324-325, 360-361` contain TODOs explicitly noting this is unimplemented). For ARFoundation mono captures, priors are the only thing pinning scale and absolute pose, so a GLOMAP run would float the entire reconstruction during BA. Incremental SfM is the only viable path while GLOMAP lacks priors-in-BA support.

**Rig refinement at the end, not throughout.** The reconstructor runs `pycolmap.incremental_mapping` with rig refinement disabled (`ba_refine_sensor_from_rig=False`, `constant_rigs` populated with the rig ids), then runs one final standalone `pycolmap.bundle_adjustment(reconstruction, opts)` with rig refinement re-enabled. Rig refinement on every one of ~33 global-BA events during a typical incremental run scales N times; doing it once at the end against the final geometry is structurally cheaper, and the standalone BA gets an uncapped solve to let the rig parameters settle.

**`mapper.ba_global_ignore_redundant_points3D = True`.** Two-stage solve: BA without redundant 3D points first, then refine pruned points with everything else fixed. Same final geometry, smaller main problem. Activates only when the reconstruction has at least 10 registered frames (COLMAP-side gate).

**`bundle_adjustment_global_max_refinements` is hardcoded at 3.** Below COLMAP's default of `5` but above the dev-time minimum of `1`. Each refinement is one full BA solve plus `CompleteAndMergeTracks` plus outlier filter; three refinements buy the outlier-discovery a multi-refinement schedule provides per global-BA event at a known ~20% wall-time cost that we accept on every run. The final standalone BA pass with rig refinement re-enabled (see "Rig refinement at the end" below) backstops further. Not a `ReconstructionOptions` knob — `BUNDLE_ADJUSTMENT_GLOBAL_MAX_REFINEMENTS` in `options_builder.py`.

**Pair generation is sequential + spatial + retrieval; pair acceptance is not gated by priors.** Three pair sources cover three complementary failure modes. **Sequential** (each frame paired with the next `sequential_window` frames in its rig's timestamp order — COLMAP `SequentialMatcher` / hloc `pairs_from_sequential` equivalent) builds the temporal backbone and catches rapid intra-frame rotation and stationary moments with sub-baseline-threshold motion. **Spatial** (each frame paired with the closest `spatial_neighbors` in-range neighbours within `spatial_max_distance_m` by VIO position) is the local-neighbourhood loop-closure primitive: drift-robust at moderate distances because errors of a few meters don't change which frames are room-neighbours, and pair-gen-only consumption means a wrongly-included drift-distant pair just fails two-view verification cheaply. Skipped when positions are absent (the legacy 3-value `frames.csv` schema). **Retrieval** (top `retrieval_neighbors` by global-descriptor cosine similarity, max-pooled over per-image tiles and L2-normalised, gated by `retrieval_min_score` plus `retrieval_min_distance_m` when positions are present) covers cross-trajectory loop closures where VIO drift exceeded `spatial_max_distance_m` so spatial missed them — descriptor similarity is the only available signal at that range. The three sources union and dedup at the end; two-view RANSAC is trusted as-is — no prior-rotation gate between `estimate_two_view_geometry` and the database write. Priors-as-pair-gen-signal is structurally separate from priors-as-BA-constraint: a drifted prior at pair-gen time costs a verification miss, not a poisoned global geometry.

**Per-frame pose uncertainty (Mahalanobis pair gating) is deliberately not pursued.** A whitened residual gate was prototyped and removed. The ZED SDK only computes `Pose.pose_covariance()` when `PositionalTrackingParameters.enable_area_memory = False`; the capture tool (`docker/zed-capture/src/zed/zed.py`) inherits the SDK default `True` so the field reads zero. Disabling area memory imposes unbounded VIO drift — Jinyu et al. (Sensors 2022, indoor ZED 2 benchmark with loop closure disabled) measured 1.0% translational drift over a 145 m corridor, 5.5% over an 84 m hallway, and 40% over a 514 m outdoor walk, with rotational error dominating the failure mode. That rotational drift is exactly the signal a Mahalanobis gate would consume, so degrading the prior to feed the gate is perverse. ARFoundation exposes no covariance at any layer (no ARKit, no ARCore numeric uncertainty), so a Mahalanobis branch would only ever be a partial cover, with a flat-angle fallback needed anyway. No published end-to-end pipeline feeds per-frame VIO covariance into COLMAP BA or a pre-BA pair gate; the dominant pattern is a single static sigma, which is what `pose_prior_position_sigma_m` already is. If revisited, the integration point is COLMAP's existing `PosePrior.position_covariance` (per-image 3×3, ingested by `pose_prior_mapper`), not a hand-rolled pair-time gate.

**Captures arrive as a single continuous trajectory in one coordinate frame.** Each capture's `frames.csv` reports every pose in one frame: no `segment_id` column, no per-segment Sim3 grouping. The reconstructor reads one continuous prior trajectory per rig. Considered and rejected: exposing capture-side discontinuities (VIO loop-closure jumps, multi-anchor handovers) to the reconstructor as segmented priors. `pycolmap.PosePrior` exposes only `position` + `position_covariance` + `coordinate_system` — no trajectory-rig primitive; the existing `Rig` class is a *sensor* rig with fixed relative poses (e.g. ZED stereo baseline), not a trajectory grouping. The only ways to implement "rigid within segment, Sim3 between segments" are (a) submap reconstruction + `estimate_sim3d` merge — a custom SfM pipeline — or (b) outer BA → per-segment Procrustes → rewrite-priors loop — a research project. Neither is right-sized. The contract pushes discontinuity management capture-side (ARFoundation `CameraProvider.AnchorChain` for mobile, ZED area memory for box captures).

**Two pair-graph follow-ons explicitly deferred.** (1) *Registration-gap chord constraint* for content-impoverished spans where N consecutive frames fail to register (blank file-cabinet panels, striped wallpaper, ceiling tiles) and the survivors on either side have no shared observations to tie them together. `pycolmap` exposes no relative-pose residual API, so the constraint can't be wired through the existing surface — real options are a feature-extractor upgrade for low-content scenes, a register-on-prior fallback (risks injecting weakly-constrained frames into BA), or a post-hoc rejection (doesn't recover the map, just refuses to ship a wrong one). None is small. (2) *Frame-level post-BA position guard* — a finer-grained reject against the priors has the same architectural defect as a map-level RMS gate (priors-as-truth false-positives on correct loop closures), and no recovery path exists for the cases it would flag.

**`deterministic_seed` is the single reproducibility knob.** `ReconstructionOptions.deterministic_seed: int | None` is the only way to request a reproducible reconstruction. When set, the value pins the PRNG seed for the pipeline / triangulation / RANSAC AND forces single-threaded BA (`num_threads = 1` on both `IncrementalPipelineOptions` and the inner `mapper`). When `None`, the reconstruction is non-deterministic. The two older fields this replaces (`random_seed` and `single_threaded`) were footguns. `random_seed` alone was a lie: BA thread scheduling still varied between runs, so reruns drifted despite a pinned seed. `single_threaded` alone was a lie: each run drew a fresh PRNG seed, so reruns drifted despite pinned threading. Every "interesting" state of the original pair was the paired state; collapsing eliminates the broken-but-plausible combinations.

### Manifest in MinIO as the round-trip for `ReconstructionOptions`

**Context:** `ReconstructionOptions` is a per-job request envelope with ~20 nullable fields. It needs to travel from the API (request-time) to the reconstructor (run-time) and survive in storage for later inspection. The two candidates were: mirror as SQL columns, or write into MinIO alongside the artifacts.

**Constraint:** Store the full options structure in the row's `manifest` JSONB column under `Manifest.options`. The reconstructor reads it from the lease response; the API writes it at create-time. `held_out_frame_timestamps`, `is_indoor`, and post-run `ReconstructionMetrics` follow the same pattern.

**Consequences:** No schema migration for new option fields. The manifest is the single source of truth for "what was requested." Trade-off: options cannot be indexed in SQL; queries like "find reconstructions with random_seed=42" require a JSONB scan. Acceptable because options are inspected per-row, not filtered at scale.

### Map-frame alignment via per-frame gravity + first-frame origin

**Context:** The map's down axis and origin are downstream contracts: Cesium georegistration and AR vertical overlay expect a gravity-aligned map, and the localizer's `camera_from_map`-as-`camera_from_world` shortcut expects the first registered frame to sit at the origin. Multi-camera captures get metric scale from the rig baseline and loop closure from content retrieval, so position priors are not needed for either — and on captures where VIO area memory fails to close a revisit, position priors actively poison BA. The map-frame alignment mechanism therefore must work identically with priors on or off.

**Constraint:** Capture writes per-frame gravity (unit down in rig-local coords) into `frames.csv`. Post-SfM, the reconstructor builds one `Sim3d` whose rotation is the solution of `Rotation.align_vectors([0, 1, 0], median_per_component(gravity_samples_in_recon_world))` and whose translation places the first registered frame's center at the origin after rotation. Multi-camera captures (priors off) and single-camera captures (priors on) use the same mechanism; the only difference is whether `PosePrior` position rows were written during the BA phase. When no frame carries a gravity sample, rotation falls back to identity and `gravity_aligned_in_map_frame=False` lands in metrics.

**Consequences:** Median across the trajectory absorbs per-frame IMU noise and SDK cold-start drift; outlier frames (motion blur, brief tracking glitches) don't tilt the whole map. The "first registered frame == map origin" contract still holds. On the priors-on path, `pose_prior_position_sigma_m` remains a tunable: too tight forces VIO drift into the map, too loose lets the reconstruction float. The Umeyama best-fit of map centers to position priors is computed (priors-on path only) and surfaced as `prior_drift_residual_rms_m` / `_max_m` — a per-capture diagnostic for the calibration-corpus filter, never applied.

### The reconstruction-quality metrics are diagnostics, not gates

**Context:** `metrics_builder.py` emits a `ReconstructionMetrics` bundle — verified-match rates and per-pair inlier statistics, registration count and rate, reprojection-error percentiles, and the prior-drift Umeyama residual. The tempting expectation is that one of these grades whether a reconstruction is good enough to ship to a localizer client. None does. Each was tried as a gate and each grades something other than global geometric correctness.

**Constraint:** Treat every emitted metric as a per-reconstruction diagnostic, never as a ship/no-ship gate.

- **Prior-drift residual** (`prior_drift_residual_*_m`) and **Umeyama-fit scale** grade recon-vs-VIO-prior disagreement. On any capture whose VIO drifted, a correct loop-closed reconstruction *must* disagree with the priors by meters at the revisit — so these false-positive on exactly the reconstructions the pipeline exists to produce.
- **Reprojection error** grades whether BA converged cleanly, not whether it converged to the right global geometry: a meter-scale mid-trajectory teleport still has sub-pixel reprojection at both of its endpoints.
- **Registration count / rate** grades nothing about correctness — COLMAP registers 100% of images into a geometrically wrong map just as readily as into a right one.
- **Verified-match rate** and per-pair inlier statistics grade pair-input quality (how often `estimate_two_view_geometry` accepts a pair), not the assembled map.
- **Track-extent metrics** (long-range-track count, track-extent percentiles) are structurally blind to the dominant small-capture failure: an aliased pair registers its frame through COLMAP's structure-less PnP fallback and contributes ~0 tracks, so any track-based diagnostic is dominated by healthy frames and cannot see the teleport. A convex-hull-volume metric had the sharper version of this defect — a single teleport inflates the hull — and was removed (`fcee131c`).

**Consequences:** The one physical-world signal available without invoking the localizer is a *necessary* condition, not a sufficient one: a consecutive-keyframe center-to-center distance implying a sustained speed above the ~2.5 m/s indoor-handheld ceiling is a BA local-minimum teleport (healthy captures peak near 1.5 m/s; degenerate ones spike to 5–17 m/s). It catches gross teleports; it cannot catch a globally rotated-or-scaled map, a point cloud full of phantom 3D points the localizer can't match against, or any failure that doesn't surface as a per-pair velocity spike. The sufficient check — pose error of held-out frames localized against the finished map, truth being their capture-side priors — is what the `held_out_frame_timestamps` protocol (above) is the hook for.

### Retrieval is the verification-resistant pair source

**Context:** Pair generation draws from sources with qualitatively different *error* modes, and per-pair two-view geometric verification (RANSAC on the essential/fundamental matrix) is the one filter every candidate passes through. Whether that filter suffices depends on the source. The tempting move — tighten per-pair inlier thresholds until bad pairs fall out — works for some sources and fails for the one that produces the dominant failure mode on small dense indoor captures.

**Constraint:** A wrong **sequential** or **VIO-proximity (spatial)** pair is wrong because the two frames look at unrelated scene (temporal adjacency or VIO proximity broke down); unrelated scene does not fit a coherent two-view geometry, so RANSAC rejects it cheaply. These sources' errors are self-rejecting. A wrong **retrieval** pair is wrong because of *visual aliasing*: two different places that look alike — repeated office decor, or a dark exposure-collapsed frame whose global descriptor degenerates to gross layout and matches a bright hallway elsewhere. Aliased pairs carry high inlier counts and fit coherent two-view geometries; they are geometrically self-consistent and survive every per-pair threshold that does not also kill genuine wide-baseline loop closures. Retrieval's errors are verification-resistant.

**Consequences:** Per-pair geometric verification is necessary but not sufficient for retrieval pairs — the aliased pair is a needle that is itself made of hay, so no inlier-count threshold isolates it. Distinguishing a true loop closure from an alias requires a second signal independent of the pair's own two-view geometry — some evidence that the two frames are plausibly at the same physical place — because descriptor similarity alone cannot tell them apart. This is the structural reason the reconstructor cannot lean on a single global inlier threshold the way pure-SfM tools do on curated input.

## See also

- `docker/SPEC.md` -- stack-level data flow, MinIO bucket layout, and the multi-service relationships this reconstructor sits inside.
- `.pulsar/debugging.md` -- operator runbook including the "`sfm_model/` presence means SfM completed regardless of DB status" recovery hazard.
- `docker/api/src/routers/leases.py` -- the API-side lease state machine (request, progress, succeed, fail, reaper). Read this when reasoning about timeout or recovery behavior.
- `packages/python/core/src/core/reconstruction_options.py` and `reconstruction_metrics.py` -- the shared option / metric schema. The reconstructor reads options, writes metrics; both flow through the row's `manifest` column.
