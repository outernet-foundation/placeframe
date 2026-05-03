# Reconstructor Service

## What this is

The reconstructor builds a sparse 3D map (point cloud + camera poses) from a capture session's images and per-frame VIO truth poses. Output is a COLMAP reconstruction stored as a manifest + binary blobs in MinIO. Operating instructions for the service live in the top-level `CLAUDE.md`.

This document covers the durable design surfaces: the truth-frame alignment + Procrustes diagnostic, map-quality metrics computed at build time, and the held-out-frames protocol that the calibration pipeline depends on.

## Truth-frame alignment

The reconstructor pins the **first registered frame's COLMAP pose** to its `frames.csv` truth pose via single-anchor `Sim3d`. This places the rebuilt map in the capture's truth frame.

Single-anchor (rather than multi-anchor / Procrustes) is the intended invariant: downstream consumers rely on the contract that "first registered frame == map origin." Once that anchoring is set, the map's coordinate system is well-defined relative to the capture, and the localizer's `camera_from_map` Transform doubles as `camera_from_world` when serving frames from the same capture.

### Diagnostic Procrustes residual

Separately and only as a diagnostic, the reconstructor solves rigid (no-scale) Procrustes — Umeyama / Kabsch via numpy SVD — over **all** registered frames (truth pose vs COLMAP pose pairs). The Procrustes transform itself is **not applied to the reconstruction**; only the residual is reported.

Per-capture residuals surface on `ReconstructionMetrics`:
- `truth_alignment_rms_residual_m`
- `truth_alignment_max_residual_m`

These ride the manifest. The fit pipeline (or operator review) uses them to filter unreliable captures out of the corpus: large residuals (> a few cm typical session) indicate Procrustes is the noise floor and calibration won't be meaningful for that capture.

### Architecture rationale

The reconstructor emits both the alignment and the diagnostic. The Umeyama math lives in `colmap.py` because the residual is a per-reconstruction property and the reconstructor already has `(truth-pose, map-pose)` pairs in scope. A `_registered_frames(rigs, colmap_image_ids, reconstruction)` generator handles multi-camera rigs (e.g. ZED stereo where one Frame is shared across left/right) so the alignment block and the diagnostic block share frame extraction.

The considered alternative — having the calibration script fetch per-image map poses through a new API endpoint and run Umeyama itself — was rejected as more code, more API surface, and pulling pycolmap into `scripts` for no gain.

The diagnostic is computed once at map-build time. **Runtime impact: none.** The reconstruction's absolute frame is unchanged from prior single-anchor behavior.

## Map-quality metrics

Computed at map-build time inside `MetricsBuilder.build_reconstruction_metrics` and written to `manifest.json` in MinIO as part of the existing `ReconstructionMetrics` block. There is no separate "map quality" concept — these are reconstruction metrics, conceptually identical to track-length and reprojection-error fields that already lived on the same model.

| Metric | Definition |
|---|---|
| `map_image_count` | Total registered images. |
| `map_point_count` | Total triangulated 3D points. |
| `map_avg_track_length` | Mean number of observations per 3D point. |
| `map_bounding_volume_m3` | Convex hull volume of camera centers, in cubic meters (`scipy.spatial.ConvexHull(centers).volume`). |
| `map_viewpoint_diversity` | Scalar derived from variance of camera viewing directions (higher = more directional coverage). Hand-rolled (~10 lines numpy); no library covers it. |

The user-controlled `is_indoor` boolean lives as a column on `reconstructions` (not as a reconstruction output). Default false; toggleable.

### `is_indoor` snapshotting into the manifest

The localizer needs `is_indoor` for the calibration feature vector at runtime. Source of truth is the `reconstructions` row (user-toggleable), but the localizer reads it from the manifest because the localizer never calls the API otherwise — adding api-client + service auth to the localizer for one boolean would be disproportionate.

`POST /reconstructions` snapshots `is_indoor` into `ReconstructionManifest` at create-time. The localizer reads all 6 map-side features (the 5 above plus `is_indoor`) from the same manifest path. This mirrors how `held_out_frame_timestamps` is snapshotted into `manifest.options`.

Today this is a write-once path because no toggle endpoint exists. When a toggle endpoint lands, that endpoint must re-write `manifest.json` (single S3 PUT) to keep the snapshot fresh. The fit-side reads `is_indoor` directly from the row via `api.get_reconstruction(...)`, so a stale snapshot only affects runtime confidence, not training labels.

### Why on the manifest, not as SQL columns

Map-quality features are computed metrics — conceptually identical to existing `ReconstructionMetrics` fields, so they share the same model and storage. Nullable columns would have leaked the "feature exists ↔ reconstruction succeeded" invariant into every reader. Manifest-only avoids that. The harness fetches the manifest per reconstruction (single S3 GET each, sequential, negligible cost at corpus sizes through Phase 5).

Pre-existing reconstructions written before these fields existed deserialize with `None` (Pydantic Optional defaults). Consumers skip rows whose manifest lacks the metrics rather than treating them as zero. Cheap to recompute by re-uploading the capture into a fresh reconstruction.

## Held-out frames protocol

`held_out_frame_timestamps: list[int] | None` is a field on `ReconstructionOptions`. Type is `list[int]` because `frames.csv` timestamps are Unix milliseconds, matching `long timestampMilliseconds = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds()` produced by Unity's `CaptureManager.cs`.

**No `reconstructions` table column** — `ReconstructionOptions` already round-trips through MinIO via `ReconstructionManifest.options` (written at create-time by `docker/api/src/routers/reconstructions.py`, read at run-time by `docker/reconstructor/src/reconstructor/run_reconstruction.py`). The manifest is the single source of truth for what was requested.

`run_reconstruction.py` builds a `set[int] | None` from `manifest.options.held_out_frame_timestamps` and threads it into each `Rig(...)`. `Rig.__init__` (in `rig.py`) takes the optional `held_out_frame_timestamps: set[int] | None` kwarg and `continue`s on rows whose `int(frame_id)` is in the set, inside the existing `for frame in frames_csv.splitlines()[1:]` loop. The image-list materialization further down `run_reconstruction.py` drops the held-out images naturally because their poses are no longer in `frame_poses`.

This API contract closes the gap that previously forced calibration scripts to do tar surgery (download capture, modify in memory to drop frames, re-upload as new capture session) just to control which frames participated in a build.

## DELETE cascade

`DELETE /reconstructions/{id}` cascades S3 cleanup of the `{id}/` prefix in `placeframe-reconstructions` before deleting the row. Without the cascade, deleting a row leaks the prefix's bytes — orphaned bytes accumulate forever. The cascade implementation lists and deletes the prefix's contents prior to `session.delete(row)`.

`DELETE /localization_maps/{id}` stays DB-only — LMs don't own an S3 prefix; their data lives in DB rows (`LocalizationMapCameraPosition`) and the alignment transform on the row itself. The 409-on-LM-exists guard on the reconstruction-delete endpoint stays as intentional safety: LM rows reference the reconstruction by FK, so deleting the reconstruction without first deleting its LMs would either fail the FK or orphan the LMs.

## Pose-inversion idiom

Three sites in the reconstructor compose `world_from_X = X_from_world⁻¹`. Use `pycolmap.Rigid3d.inverse()` (which exists, returns the inverted `Rigid3d`) — assign once and read `.rotation.matrix()` / `.translation` off the inverted value. Don't hand-roll `rot.matrix().T` plus `-rot.T @ trans`; the combined idiom is harder to read and easier to subtly break.
