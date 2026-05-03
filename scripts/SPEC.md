# scripts — orchestration utilities

`scripts/` holds Python scripts registered as `uv run` commands (entries in `scripts/pyproject.toml`). Operating instructions for the registered commands live in the top-level `CLAUDE.md`.

This SPEC covers the durable design of the calibration-pipeline scripts: the architectural split, Algorithm 1, the held-out frame selection seam, the reconstruction-reuse contract, and the corpus-gathering procedure.

## Architectural split

Two scripts orchestrate over backend ids and write/read through the API. There is no sidecar JSON file and no parallel data store.

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
       │       │     - metrics (incl. map quality + is_indoor)          │
       │       │                                                        │
       │       ▼                                                        │
       │  localization_evaluations                                      │
       │     keyed by (reconstruction_id, frame_timestamp,              │
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
       │  py                          │    │                            │
       │                              │    │  --captures <id> [<id>...] │
       │  --captures <id> [<id>...]   │    │    or                      │
       │                              │    │  --reconstructions <id>... │
       │  PB sweep over recon options │    │  [--pipeline-version <sha>]│
       │  (one recon per cell, no     │    │  [--no-fit]                │
       │  held-out frames here — pure │    │                            │
       │  parameter tuning).          │    │  - pick held-out frames    │
       │                              │    │  - reuse-or-create recon   │
       │  Emits a tuning report.      │    │  - localize held-out       │
       │                              │    │    frames; cache to        │
       │                              │    │    localization_evaluations│
       │                              │    │  - read cache as corpus    │
       │                              │    │  - fit logistic + isotonic │
       │                              │    │  - fit Σ_meas α, β         │
       │                              │    │  - write config/           │
       │                              │    │    calibration/global.json │
       └──────────────────────────────┘    └────────────────────────────┘
```

The two scripts share infrastructure (the held-out-frames API, the localization-evaluations table) but no code path or intermediate file. `tune_reconstruction.py` is unrelated to fit-calibration's flow — it exists to compare PB cells of recon options across captures and emit a report; no held-out frames, no calibration corpus, no `localization_evaluations` writes.

## fit_calibration.py

### Modes

- **`--captures <id>...`**: full pipeline — picks held-out frames, creates fresh reconstructions (default recon options) with `held_out_frame_timestamps` set, localizes held-out frames, writes evaluations to the cache, fits, writes artifact.
- **`--reconstructions <id>...`**: skips reconstruction; uses already-built reconstructions whose `held_out_frame_timestamps` are already set. Localizes held-out frames if not already cached, otherwise reads straight from `localization_evaluations`. Cheap re-fit path.
- **`--no-fit`**: populates the cache without fitting (e.g. for offline inspection of evaluation rows).

`--pipeline-version` is **auto-detected** from the localizer's `GET /version` endpoint when omitted. The flag remains as an *override* for development workflows where the operator iterates uncommitted localizer changes and wants their cache rows clearly labeled (e.g. `--pipeline-version dev-tylerh-2026-05-03`). The auto-detect default tamper-proofs the `localization_evaluations` cache-key contract — silent pooling of incompatible pipeline rows is otherwise an easy operator footgun. The runtime loader hard-fails if the deployed localizer's SHA doesn't match the artifact's `pipeline_version`.

### Driver-side localization

`fit_calibration` fetches each held-out frame image via `GET /capture_sessions/{id}/images/{frame_timestamp}`, POSTs it to the existing localizer `/localize` endpoint, computes truth-error labels driver-side, and POSTs the evaluation row to `/reconstructions/{id}/localization-evaluations`. The localizer stays a pure function with no awareness of `localization_evaluations`. The capture data path is via three surgical API endpoints — `GET /capture_sessions/{id}/manifest.json`, `GET /capture_sessions/{id}/frames.csv`, `GET /capture_sessions/{id}/images/{frame_timestamp}` — not direct MinIO access; the API is the single read path. All three share a stream-mode tar reader so per-call memory is O(member size).

Surgical rather than full-tar because `fit-calibration` reads all of `frames.csv` and the manifest but only ~100 of potentially thousands of images per capture.

The considered alternative — a server-side `POST /reconstructions/{id}/evaluate-frame {frame_timestamp}` that would do fetch+localize+persist server-side — was rejected because it would couple the localizer to MinIO/captures and to the evaluations table for a workflow that's purely orchestration.

## Algorithm 1: ZED held-out fitting

Source: every capture session in the corpus that contributes a built map.

Procedure per capture:

1. **Hold out frames at map-build time.** A pluggable selector (default `StrideHeldOutSelector`) chooses ~100 timestamps per capture (overridable via `--held-out-count`). Those timestamps go into `ReconstructionOptions.held_out_frame_timestamps`; the reconstructor filters them out of `frames.csv` and skips the matching images at build time. Rebuild the COLMAP map from the remaining frames.
2. **Reconstructor aligns the map to truth.** The reconstructor pins the first registered frame's COLMAP pose to its `frames.csv` truth pose via single-anchor `Sim3d`; this places the rebuilt map in the capture's truth frame. Separately and only as a diagnostic, the reconstructor solves rigid (no-scale) Procrustes (Umeyama / Kabsch via numpy SVD) over all registered frames and emits per-capture residuals (`truth_alignment_rms_residual_m`, `truth_alignment_max_residual_m`); these ride the manifest and the operator (or the fit script) uses them to filter unreliable captures out of the corpus. The Procrustes transform itself is not applied to the reconstruction. See `docker/reconstructor/SPEC.md`.
3. **Per held-out frame**:
   - Run the localizer on the held-out frame against the rebuilt map. The map is already in truth-frame from the single-anchor alignment, so the localizer's `camera_from_map` Transform doubles as `camera_from_world`.
   - Invert to get the estimated camera position and orientation in world (truth) frame.
   - Compare to the held-out frame's truth pose from `frames.csv` (read directly in the capture's native axis convention; the localizer's Transform is in the same convention since the API converts back from OpenCV at the boundary).
   - Compute `err_t = ||truth_position − estimated_position||` (Euclidean, meters) and `err_r = ‖log(R_truth · R_estimated⁻¹)‖` (geodesic, degrees, via `scipy.spatial.transform.Rotation.magnitude`).
   - Record `(metrics, map_features, recon_config, loc_config, device, err_t, err_r, se3_residual)` to `localization_evaluations`.
4. **Pool across all captures and configs.** Add binary labels: `success_tight = err_t < 5cm AND err_r < 1°`, `success_loose = err_t < 30cm AND err_r < 5°`.
5. **Fit logistic regression** (sklearn `LogisticRegression(class_weight='balanced')`) on the 11-feature vector. Features: `log(num_inliers + 1)`, `inlier_ratio`, `reproj_err / image_diagonal_pixels`, `inlier_coverage`, `log(num_matches + 1)`, `log(map_image_count + 1)`, `log(map_point_count + 1)`, `map_avg_track_length`, `log(map_bounding_volume_m3 + 1)`, `map_viewpoint_diversity`, `is_indoor`.
6. **Fit isotonic** (sklearn `IsotonicRegression(out_of_bounds='clip')`) on the logistic output against the same labels.
7. **Fit Σ_meas scaling.** For each held-out localization, compute the SE(3) residual `e = log(P_truth_in_map · P_estimated⁻¹) ∈ ℝ⁶`. Solve scalar α, β that maximize `Σᵢ log N(eᵢ; 0, α·PnP_covᵢ + β·I)` via `scipy.optimize.minimize` on the negative log-likelihood (small 2-D unconstrained MLE). The α, β scalars carry the empirical "actual pose-error spread relative to PnP_cov" signal that PnP_cov alone misses (mis-registered map points, wrong-but-confident inliers, etc.).
8. **Optional 10% holdout** for Brier score and reliability diagram; report in fit metadata.

Output: `{tight, loose, sigma_meas_alpha, sigma_meas_beta, loose_min, tight_min, ...}` written to `config/calibration/global.json`. See `packages/python/core/SPEC.md` "Calibration" for the artifact schema.

### Note on feature relevance with a small corpus

Map-quality features are constants within a single capture's map-config combinations (the same map → the same features). With ≥3 distinct maps the features start to vary; with one capture they collapse into the intercept. The fitting code includes them unconditionally; the regression naturally weights them down to zero when they don't vary.

## Held-out frame selection

`HeldOutFrameSelector` is a Protocol with named registrations (default `--held-out-selector stride`). Adding a new strategy must not require surgery to `fit_calibration.py`'s orchestration loop or the `localization_evaluations` contract — that decoupling is the load-bearing piece.

`StrideHeldOutSelector` is the starter implementation:

```
target_count = 100  # overridable via --held-out-count
stride = max(1, len(timestamps) // target_count)
selected = timestamps[stride // 2 :: stride]
```

Chosen because it is deterministic, scales to capture length, and gives even temporal spacing → roughly even spatial spacing on smooth capture paths.

**Known limitations**:
- Does not protect against connectivity loss. Held-outs may be frames the SfM needed for tracks; the resulting map is then worse than what gets deployed and we calibrate against a worse map than reality.
- Does not actively distribute spatially.
- Fixed count rather than fraction-of-redundant-frames.

**Strategy ideas not yet implemented** (drop-in via the Protocol):
- Post-build filter — drop held-outs the SfM unregistered, augment from the registered pool.
- Spatial-bin — voxelize positions, pick one per voxel for even spatial coverage.
- Hybrid stride+voxel.
- Count-as-fraction-of-registered.

## Reconstruction reuse

`match_or_create_reconstruction(api, capture_id, requested_options)` lists reconstructions via `GET /capture_sessions/{id}/reconstructions`, filters to `orchestration_status = 'succeeded'`, fetches each candidate's `manifest.json` from MinIO, and reuses iff `manifest.options == requested_options` (Pydantic equality on the full blob, including `held_out_frame_timestamps`). The "requested options" are constructed from `ReconstructionOptions(held_out_frame_timestamps=selected_timestamps)` — server defaults for every other knob.

If no match: create a new reconstruction with those exact options and synchronously poll `GET /reconstructions/{id}/status` until `succeeded` (5 s poll interval, 1800 s timeout, raises on `failed`).

**Why full-blob match is the chosen invariant**: calibrations must be fit against one pipeline configuration. Mixing reconstructions built with different options into one corpus contaminates the fit. The full-blob check is the strictest possible — anything looser admits silent contamination.

**Future work** (not yet built):
- Options-hash column on `reconstructions` (or a derived view) to skip the manifest fetch on big corpora.
- Opt-in `--match-options-on=held_out_only` flag for development workflows where the operator explicitly knows other options are immaterial.

## Corpus-gathering procedure

When the time comes to gather the multi-capture corpus and run the production calibration, this is the spec.

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
- **At least 2 distinct ZED captures.** Algorithm 1 needs ZED truth poses; one capture alone gives no inter-capture variance.
- **At least 2 distinct physical scenes** so map-quality features have variance (otherwise they collapse into the intercept). Same scene captured twice doesn't count.
- For cross-device validation: matched ARFoundation captures at the same scenes. Cross-device localization happens automatically when both `is_indoor`-tagged maps exist for the same scene; the operator selects which captures share scenes via the `--captures` invocation.

Per capture:
- ≥ ~200 frames recommended. `fit-calibration` defaults to selecting up to 100 held-out queries per capture via the stride selector (`--held-out-count` overrides).
- Real scenes representative of deployment.
- Standard capture practice: continuous motion, varied viewpoint, minimal motion blur.

Stretch goals (richer calibration):
- Multiple lighting conditions per scene (morning vs. evening).
- Indoor + outdoor mix once outdoor masking ships.
- A range of map sizes (small room, large room, multi-room) to give `map_*` features genuine variance.

### How to run

```bash
# Optional first step: pick reconstruction defaults via the PB sweep.
# Outputs a tuning report; doesn't write to the calibration cache.
uv run tune-reconstruction --captures <id> [<id>...]

# Fit calibration end-to-end. Selects held-out frames per capture (StrideHeldOutSelector
# by default), reuses existing reconstructions whose full ReconstructionOptions blob
# (including held-out set) matches what is requested — otherwise creates new ones —
# localizes held-out frames, caches evaluations in localization_evaluations (keyed on
# pipeline_version), fits, writes config/calibration/global.json.
uv run fit-calibration --captures <id> [<id>...]

# Cheap re-fit against already-built reconstructions:
uv run fit-calibration --reconstructions <id> [<id>...]

# Review the diff in config/calibration/global.json, commit, deploy.
```

### Verifying the run before trusting the output

The fit report (printed to stdout, also written next to the artifact) should be inspected before committing the calibration:

- **Procrustes residuals per capture**: meters of misalignment between truth and COLMAP poses. Large residuals (> a few cm typical session) indicate Procrustes is the noise floor and calibration won't be meaningful for that capture. Drop the capture or investigate.
- **Sample counts per cell**: too few labeled rows (< ~30) gives noisy logistic weights. Reflected in confidence intervals on the fit metadata.
- **Brier score**: lower is better; > 0.25 means the model is barely better than predicting the base rate. Investigate features that should have signal but don't.
- **Reliability diagram**: predicted-vs-actual probability binning. Should be roughly diagonal.

If any of these look bad, **don't ship the artifact**. Diagnose first.

## Risks and unknowns

- **Procrustes-as-truth assumption.** Algorithm 1 treats `T_truth_to_map · P_truth_i` as ground truth for the held-out frame. The truth source is `frames.csv` — the device's VIO/SLAM pose from capture time. ZED VIO is good but not perfect; ARFoundation VIO drifts noticeably over multi-minute sessions. The Procrustes residual on in-set images is the diagnostic, but it can mask issues: a globally-drifting VIO can be fit by Procrustes with low residual and still produce systematically biased held-out truth.
- **Pre-existing reconstructions lack the new metrics.** Manifests written before the metrics fields existed deserialize with `None` for those fields (Pydantic Optional defaults). The fit script skips rows whose manifest lacks the metrics rather than treating them as zero. Cheap to recompute by re-uploading the capture into a fresh reconstruction.
- **Sweep runtime** scales linearly in capture count and frame count. A corpus with ~10 captures and richer per-capture frame counts could push a full PB sweep past a day. The single-config mode is the workaround.
- **Generated API client auth.** `Configuration(access_token=…)` is stored but never sent: the openapi-generator output emits `_auth_settings: List[str] = []` on every method. `fit_calibration` works around it via `api_client.set_default_header("Authorization", f"Bearer {…}")`. The proper fix is in the openapi-generator config so emitted methods carry the spec's top-level security entries — every other consumer of `placeframe_api_client` likely has the same blind spot. Tracked in `plan.md`.
