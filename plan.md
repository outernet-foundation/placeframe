# Plan

Future-work tracker. Done initiatives have been folded into colocated `SPEC.md` / `CLAUDE.md` files alongside the code they describe. This file holds only what's still ahead.

> Durable design lives in:
> - `packages/unity/Placeframe/SPEC.md` — VPS frontend, Bayesian filter, slew loop
> - `docker/localizer/SPEC.md` — API contract, calibration runtime, determinism, tensor ops, bring-up findings
> - `packages/python/core/SPEC.md` — calibration types, image preprocessing, static tensor shape typing
> - `database/CLAUDE.md` — `localization_evaluations` cache contract
> - `scripts/SPEC.md` — Algorithm 1, fit-calibration architecture, held-out frame selection, corpus-gathering procedure
> - `docker/reconstructor/SPEC.md` — truth-frame alignment, Procrustes diagnostic, map-quality metrics, held-out-frames protocol
> - `packages/python/neural-networks/SPEC.md` — model loaders, license posture, masking design

## Phase status

| # | Phase | Status |
|---|---|---|
| 2d | Semantic-segmentation masking | Not started — required for outdoor operation |
| 4 | Dogfooding logger | Not started |
| 5 | Phone-side correction | Not started |
| 6 | Per-map overlay (opportunistic) | Not started |
| 7 | Grafana / Loki integration | Not started — implementation plan in `docs/grafana-integration.md` |
| T-widening | Static tensor typing repo-wide migration | Localizer-scope prototype landed; widening deferred. Orthogonal — no specific phasing dependency. |

## Critical path

```
Phase 2d ─► Phase 4 ─► Phase 5 ─► (Phase 6 opportunistic)
```

Phase 2d enables outdoor operation. Phase 4 builds the logger that Phase 5's calibration data flows through. Phase 5 produces the multi-capture corpus that replaces the starter calibration. Phase 6 opens up once a single map has accumulated ≥200 phone-side samples and clearly matters.

## Phase 2d — Semantic-segmentation masking (3-day time-box)

OneFormer (MIT) loaded once at service startup, run right after `canonicalize_image()`, mask applied in image space before feature extraction.

- Reconstructor: OneFormer-Swin-L (one-time cost at map build).
- Localizer: OneFormer-Swin-T (~100–200ms GPU; tolerable for 1Hz queries).
- Hard-coded COCO transient class list: `person, bicycle, car, motorcycle, bus, train, truck, boat, traffic light, bird, cat, dog, horse, sheep, cow`.
- Fallback when masked image has fewer than `MIN_KEYPOINTS_AFTER_MASK` keypoints (default 50): retry without mask, log.
- After landing, re-run `fit_calibration.py` against the new pipeline_version. Commit the refit `config/calibration/global.json`. ZED-only data is sufficient for this refit; the Phase-5 phone correction is unaffected.

**Time-box rule**: if Day 4 is spent on environment, dependency, or model-loading wrestling, Phase 2d defers to a post-Phase-6 follow-up. The cost of deferral is one additional future calibration refit when masking later lands.

**Risks**:
- OneFormer GPU memory pressure on shared device (OneFormer-T + ALIKED + LightGlue + DIR). Should fit on an A4000-class card; verify on the deployment GPU before committing.
- Mask boundary keypoints may be unstable. Mask dilation (default 0) is the tuning knob; revisit if observed.
- Crowded-scene masking failure (plazas dominated by people may end up with insufficient keypoints). The fallback bounds this risk; crowded scenes get the worst of both worlds — no masking benefit, slower than baseline. Acceptable for v1.

End of Phase 2d: transient scene content suppressed from features in both pipelines; calibration refit against the masked pipeline.

## Phase 4 — Dogfooding logger

Zero UX impact. Adds the plumbing required to gather phone-side calibration data. Built right before it's needed (Phase 5) so the schema and feature set are informed by lived experience.

- Toggle in AndroidMobile settings UI ("Contribute calibration data"), persisted to PlayerPrefs. Default: off.
- Per-query log buffer in memory: `{server_request_timestamp, server_response, vio_pose_at_request_time, frame_index}` per localization.
- Session boundary (app backgrounded, toggle off, app exits): serialize the session log to JSON and upload to `POST /calibration-data`.
- Backoff/retry: if upload fails, persist locally and retry on next session start. Cap local persistence at e.g. 100 MB.
- API endpoint writes JSON directly to MinIO at `s3://placeframe-calibration-data/sessions/{session_id}.json`. No DB row needed.

Schema of the uploaded JSON (from initial design — confirm with lived Phase 3 experience before locking):

```json
{
  "schema_version": 1,
  "session_id": "uuid",
  "device_class": "Pixel 7" or similar,
  "os": "Android 14",
  "app_version": "0.1.0+47",
  "map_id": "uuid",
  "pipeline_version": "abc123...",
  "queries": [
    {
      "timestamp_ms": 1714400000000,
      "metrics": { "NumInliers": 234, "InlierRatio": 0.41, ... },
      "covariance": [[...6x6...]],
      "estimated_pose_in_map": { "translation": [...], "rotation_quat": [...] },
      "vio_pose": { "translation": [...], "rotation_quat": [...] },
      "confidence": { "tight": 0.65, "loose": 0.91 }
    }
  ]
}
```

Query images are not logged. The schema is designed so they can be added later (a `query_image_id` field referencing an upload to a separate bucket) without breaking parsers.

End of Phase 4: directed data-gathering sessions can be run with the known user pool to produce phone-side samples on demand.

## Phase 5 — Phone-side correction (multi-capture corpus run)

Replaces the single-capture starter calibration with a production calibration fit on multiple captures plus phone-side data.

### Multi-capture corpus run

- Gather corpus per `scripts/SPEC.md` "Corpus-gathering procedure": ≥2 distinct ZED captures, ≥2 distinct physical scenes.
- Run `fit-calibration --captures <id> [<id>...]` — produces a real production calibration replacing the starter.
- Derive `loose_min` / `tight_min` from the success-cluster distribution (replaces the hand-set starter values 0.25 / 0.0).
- Commit, deploy.

### Algorithm 2 — pairwise VIO calibration

For phone-side data (Phase 4 logger output), Algorithm 2 fits a stage-2 isotonic correction on top of the global stage-1 prediction.

Procedure per dogfooding session:

1. Enumerate localization pairs `(i, j)` where `j > i` and `||translation(T_vio_j) − translation(T_vio_i)|| ≤ 1.0 m` (limits VIO drift contribution to <1cm on flagship phones, <2cm on lower-end).
2. Per pair, compute pairwise error:
   - VIO-implied relative motion: `dT_vio = T_vio_j · T_vio_i⁻¹`.
   - Localizer-implied relative motion: `dT_loc = T_map_j · T_map_i⁻¹`.
   - Pairwise translation error: `err_t = ||translation(dT_loc) − translation(dT_vio)||`.
   - Pairwise rotation error: `err_r = angle_between(rotation(dT_loc), rotation(dT_vio))`.
3. Attribution: per individual localization, define `err_i = median over all pairs that include i of pair_err`. Robust to outlier pairs.
4. Pool across phone sessions. Fit isotonic correction `g(p) = empirical P(success | predicted_p_from_stage_1)`.
5. Insert into the global artifact as a stacked isotonic, refit, deploy.

**Attribution caveat**: pairwise errors confound the two localizations involved. Median-over-pairs is a coarse but robust attribution heuristic. A least-squares per-localization-error solve is the principled alternative — fallback if median proves insufficient.

**What this can't detect**: errors systematically shared across all localizations in a session (e.g. miscalibrated phone intrinsics producing a constant offset on every query) get absorbed into the implicit `T_align` and produce zero pairwise residual. The user-facing manifestation is "consistent but slightly shifted world" — the lowest-impact failure mode and acceptable. Random outliers, the high-impact failure mode, are detected normally.

**Open question raised by harness fusion**: the calibration pipeline already produces phone-against-ZED-map cells with Algorithm-1-style truth attribution (the phone's own `frames.csv`, Procrustes-aligned to the ZED-built map). If the phone capture's `frames.csv` truth is good enough, Algorithm 2's pairwise machinery may be unnecessary — directly-labeled phone-source data falls out of the same fit-calibration run. Worth examining when the corpus exists.

### Frontend filter retune

Re-tune `RelocalizationFilter.BaseProcessNoise{Translation,Rotation}VariancePerTick` and `SnapThresholdSigmas` against the production calibration's fitted Σ_meas. The single-capture starter is too unreliable to drive meaningful retune.

End of Phase 5: phone-side confidence is well-calibrated. The system hits its design goals for both ZED- and phone-source queries.

## Phase 6 — Per-map overlay (opportunistic)

Per-map fitting and the runtime loader land together. Defer until at least one map crosses the 200-sample threshold and clearly matters.

### Algorithm 3 — per-map fitting

Same as Algorithm 2 but partitioned by map ID. Once a map accumulates ≥200 phone-side samples, fit a per-map isotonic on top of the global stage-1+stage-2 prediction:

```
predicted_p_global = stage1(metrics, map_features).then(stage2_isotonic)
permap_isotonic(p) = empirical P(success | predicted_p_global = p, map = M)
```

Per-map artifact uploaded to `s3://placeframe-maps/{map_id}/calibration.json`.

### Per-map calibration loader

Lazy MinIO fetch on first localization request for a map; in-memory cache keyed by map ID. Absent → log + fall back to global-only. Pipeline-version-mismatched → log loudly + fall back to global-only.

In `apply_global_calibration`, the per-map isotonic stacks on top of the global pipeline:

```python
if per_map_calibration_loaded:
  p_final_tight = per_map.tight.isotonic.apply(p_calibrated_tight)
  p_final_loose = per_map.loose.isotonic.apply(p_calibrated_loose)
else:
  p_final_tight = p_calibrated_tight
  p_final_loose = p_calibrated_loose
```

Optional `POST /calibration/refresh/{map_id}` admin endpoint to invalidate cache after re-upload.

End of Phase 6: per-map calibration rolls in map-by-map as data accumulates.

## Phase 7 — Grafana / Loki integration

Implementation plan in `docs/grafana-integration.md`. Phase entry is a placeholder for status tracking; the doc itself is the implementation spec.

## Phase T — Static tensor typing widening

Localizer-scope prototype landed (see `packages/python/core/SPEC.md` "Static tensor shape typing"). Widening pieces, deferrable / orthogonal:

### Localizer / reconstructor full coverage

- `Map.keypoints` and `Map.pq_codes` typed with rank-correct shapes (`NumKeypoints` brand acknowledging per-image variation; rank and last-axis size still meaningful).
- `axis_convention.py` translations / rotations / quaternions typed with `ndarray[tuple[Literal[3]], ...]` etc.

### Repo-wide `NDArray` migration

Per-file commits, grouped by module for reviewer-friendly diffs. End state: zero `from numpy.typing import NDArray` outside generated code; zero `# noqa: TID251`.

Files currently importing `NDArray` (per `# noqa: TID251 — Phase T piece 3 follow-up migration` annotations):
- `docker/zed-capture/src/zed/zed_wrapper.py` — translation/orientation/image data; small fixed shapes.
- `docker/reconstructor/src/reconstructor/{run_reconstruction,rig,colmap,metrics_builder}.py` — covered alongside the localizer migration; many shared types.
- `docker/localizer/src/{map,build_metrics}.py` — covered by the per-file migration.
- `packages/python/core/src/core/{axis_convention,h5,opq}.py` — h5 / opq specifics.
- `packages/python/neural-networks/src/neural_networks/models.py` — DIR / ALIKED preprocessing arrays.
- `scripts/src/scripts/{tune_reconstruction,fit_calibration}.py` — PB-sweep tabulation arrays and the calibration fit's feature/covariance arrays; small fixed shapes.

### Repo-wide `Tensor` migration

Replace bare `Tensor` with `TT[*Shape]` where shape is known. Grow `torch_ops.py` opportunistically as migration touches each file. `Tensor` survives only at boundaries with un-typable third-party calls (neural net outputs, pycolmap returns), wrapped at the seam.

### Lint tightening

Once `NDArray` and `Tensor` migrations land:
- Add `reportExplicitAny` to `basedpyright` config to catch new `cast(Tensor, ...)` / `Any` escape hatches.
- Add `flake8-tidy-imports` ban on bare `torch.Tensor` in domain modules (allow only in `torch_ops.py`-style wrappers via `per-file-ignores`).

**Risks**:
- Migration is large (~50+ usage sites across the listed files). Mitigation: per-file commits with a common pattern.
- PEP 646 limits (no per-element bounds on `TypeVarTuple`) force per-rank `@overload` sets in `torch_ops.py`. Manageable; just verbose.

End of Phase T: tensor shapes are statically checked at function/assignment boundaries throughout the codebase.

## Deferred follow-ups

Items not gated on a phase but tracked so they're not forgotten.

### `tune_reconstruction.py` localization-quality eval per PB cell

The current version compares cells by *map-quality metrics only* (point count, track length, viewpoint diversity, bounding volume, image count, plus the `truth_alignment_*` residuals). The genuine figure of merit — *localization quality* per cell — requires running held-out localizations per cell, effectively a per-cell fit-calibration loop. Lands as its own effort after Phase 3 closes out and the parameter-tuning loop is the bottleneck. A top-of-file comment in `tune_reconstruction.py` calls out the limitation.

### Generated API client auth

The openapi-generator output emits `_auth_settings: List[str] = []` on every method and `Configuration.auth_settings()` returns `{}`, so `Configuration(access_token=…)` is stored but never sent. Top-level OpenAPI `security: [{oauth2:[openid]},{bearerAuth:[]}]` is in the spec; the generator isn't propagating it onto operations during codegen.

`fit_calibration` works around it via `api_client.set_default_header("Authorization", f"Bearer {…}")`. Every other consumer of `placeframe_api_client` (Unity `legacy/`, future scripts) likely has the same blind spot.

Proper fix: investigate the openapi-generator-cli version's behavior, possibly upgrade or pass `--global-property-default-security` (or equivalent) so emitted methods carry the spec's security list.

### DIR replacement (opportunistic)

DIR works and is license-clean, but is dated and self-vendored. Modern alternatives (EigenPlaces, SALAD, DINOv2 + GeM pooling) outperform AP-GeM on standard benchmarks. Re-evaluate when retrieval becomes a bottleneck; bundle ahead of any planned calibration refit if pursued. Square-tile aggregation composes with any successor unchanged.

## Open investigations

### Reconstructor pose-inversion idiom — drive-by cleanup

Three sites in the reconstructor hand-roll `world_from_X = X_from_world⁻¹` as `rot.matrix().T` plus `-rot.T @ trans` instead of using `pycolmap.Rigid3d.inverse()`:

- `docker/reconstructor/src/reconstructor/colmap.py` — Umeyama diagnostic, `rig_from_world` → camera center.
- `docker/reconstructor/src/reconstructor/colmap.py` — `rig_from_world` → `world_from_rig` for the npz writer.
- `docker/reconstructor/src/reconstructor/metrics_builder.py` — `rig_from_world` → viewing-direction column for `map_viewpoint_diversity`.

Same fix at all three sites — assign `world_from_X = X_from_world.inverse()` once and read `.rotation.matrix()` / `.translation` off it. No behavior change, reads as "obviously the inverse." Single drive-by commit.
