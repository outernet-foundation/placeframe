# End-to-end testing and calibration — Intent

> Execution and progress tracked in [`plan.md`](plan.md).
> This initiative fuses two previously-separate efforts: the parameter-sweep harness (originally `test-placeframe-e2e.md`, deleted in `c84375ea`, recoverable from git history) and the VPS calibration design (originally Phase 3 of `vps-redesign-intent.md`).

## Status

Code-complete plus a single-capture starter calibration. **The full multi-capture corpus and the ~15-hour parameter sweep are explicitly out of scope for this effort.**

The goal of this initiative is twofold:

1. Land code that is logically correct end-to-end so that, when the multi-capture corpus is later assembled, the existing code path produces a production calibration without further engineering work blocking the run.
2. Run that code path against the one capture we already have to produce a *known-bad-but-real* starter calibration. That starter calibration unblocks band-aid removal (`IDENTITY_BOOTSTRAP_SENTINEL`, `MIN_NUM_INLIERS`, `MIN_INLIER_COVERAGE`, hand-set `-4.595` intercept) and lets the system run on real fitted confidence — overfit and unreliable, but real — until the corpus run replaces it.

The initiative also produces, as a deliverable, an unambiguous corpus-gathering spec for future-operator-self.

The current state is a half-state:
- The e2e harness has lint/type errors and a half-finished signature change in `main()`.
- The calibration runtime loader has a hand-set band-aid intercept (`-4.595`) and a never-removed `IDENTITY_BOOTSTRAP_SENTINEL` skip path.
- `apply_global_calibration` is called with `features={}` because no features are plumbed.
- `localize.py` carries a raw-metric quality floor (`MIN_NUM_INLIERS=50`, `MIN_INLIER_COVERAGE=0.15`) as a band-aid for the constant-confidence stub.
- `scripts/src/scripts/fit_calibration.py` doesn't exist.
- The maps schema has no map-quality columns and the reconstructor doesn't compute them.
- `Σ_meas = PnP_cov / tight²` conflates "geometric uncertainty" with "trustworthiness" — works only because `tight` is pinned at 0.01.

This initiative climbs out of all of that.

## Why these are one effort

The discovery that drove fusion: the e2e harness is the calibration data-generation engine. They are not two scripts that happen to share captures; they are the same script with overlapping outputs.

- Algorithm 1 of the calibration design (ZED held-out fitting) requires a corpus of capture sessions, each rebuilt with ~10% of frames withheld, the held-out frames localized against the rebuilt map, and `(metrics, pose_error)` rows pooled into a fit. The held-out-tar machinery this requires is exactly what `_prepare_capture` in `test_placeframe_e2e.py:156` already does (it withholds every 9th frame, rebuilds the tar, keeps the withheld frames as queries).
- The e2e harness already produces `(metrics, location, device_type, recon_config)` rows for every (held-out frame × map × loc-config) cell. What's missing for Algorithm 1 is the *pose-error labeling step* — Procrustes-align each capture's `frames.csv` truth to the rebuilt COLMAP map, transform the held-out frame's truth pose, compare to the localizer's estimate, record `err_t` and `err_r`. That's a delta to the harness, not a new script.
- The harness's Phase 6 already runs cross-device localization (e.g. phone-frame against ZED-built map). Algorithm 2's phone-side data is one column of the same matrix.

The original plan separated Phase 2e ("repair harness, run sweep, pick reconstruction defaults") and Phase 3 ("fit calibration against the picked defaults") as if they were sequential and independent. They aren't — the sweep cells are the calibration training rows. The sweep gives a richer training set (multiple recon configs × multiple loc configs × multiple captures); the calibration fits across all of them; the sweep can rank parameter choices using fitted confidence as one of its metrics.

## What this initiative produces

**Code deliverables:**

1. Repair `scripts/src/scripts/test_placeframe_e2e.py`: fix the S608 false-positive on `_build_insert_sql`, fix the ASYNC240 violation on the glob, complete the half-finished signature change so `main()` actually passes `tar_paths` into `_run`, re-verify `basedpyright` passes.
2. Add a `--single-config` flag to the harness: short-circuit Phase 4 to `[None]` (server-default recon config) and skip the `LOC_RETRIEVAL_TOP_K` × `LOC_RANSAC_THRESHOLD` cross product. Used for fast iteration and for incremental refits when only the corpus has changed.
3. Extend the harness to label pose error per held-out frame: Procrustes-align `frames.csv` truth poses to the rebuilt COLMAP map, transform held-out truth into map frame, compute `err_t` and `err_r` against the localizer estimate, persist alongside the existing metrics.
4. Add map-quality features to the reconstructor's metrics output: `map_image_count`, `map_point_count`, `map_avg_track_length`, `map_bounding_volume_m3`, `map_viewpoint_diversity`. Folded into `ReconstructionMetrics` (single concept; same plumbing as the existing track-length and reprojection-error fields). Reconstructor computes them inside `build_reconstruction_metrics` at map-build time and writes them to `manifest.json` in MinIO alongside the rest of the metrics block. Harness fetches the manifest per reconstruction at row-emission time. The user-controlled `is_indoor` boolean lives as a column on `reconstructions` (default false) since it isn't a reconstruction output.
5. Create `scripts/src/scripts/fit_calibration.py`: pulls the labeled rows produced by the harness, pools them, fits Algorithm 1 (logistic + isotonic for tight and loose, plus the Σ_meas α, β scalars described below). Writes `config/calibration/global.json` with the localizer's git SHA as `pipeline_version`. Emits a fit report (Brier, reliability, sample count, Procrustes residual per capture, fitted α/β).
6. Plumb features through `apply_global_calibration`: `build_metrics.py:66` currently passes `features={}`. Wire transformed metrics + map features into the dict keyed by the calibration's `feature_names`.
7. Decouple `Σ_meas` from confidence in `build_metrics.py`: replace `PnP_cov / tight²` with `α · PnP_cov + β · I` (α, β read from the fitted calibration artifact). Confidence becomes a gate: `if metrics.confidence.tight < TIGHT_MIN: raise LocalizationError(...)` in `localize.py`.
8. Remove the band-aids: `IDENTITY_BOOTSTRAP_SENTINEL` and its skip in `calibration.py`; `MIN_NUM_INLIERS` / `MIN_INLIER_COVERAGE` in `localize.py`; the hand-set `-4.595` intercept in `global.json`; the `CONFIDENCE_TIGHT_FLOOR` floor in `build_metrics.py`. These all happen once the starter calibration (next deliverable) is committed.
9. Per-map calibration loader path: lazy MinIO fetch + cache, fall back to global-only if absent. **Per-map fitting (Algorithm 3) is deferred to a later phase.** Only the loader plumbing lands now.

**Run-and-commit deliverables (single-capture starter calibration):**

10. Run the harness in `--single-config` mode against the one capture we have today. Produces ~11 labeled rows. Run `fit_calibration.py` against those rows; commit the resulting `config/calibration/global.json` to the repo with a header comment that it is a known-bad single-capture starter, not a production calibration.
11. Pick `TIGHT_MIN` from the starter fit's distribution of `tight` values on successful held-out localizations (e.g. some quantile of the success cluster). Bake into `localize.py` as a module constant.

**Documentation deliverable:**

12. Corpus-gathering instructions (this file's "Corpus-gathering spec" section). Unambiguous enough to execute cold.

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

- **pycolmap** — `Sim3d` and friends for the Procrustes/Umeyama alignment of truth poses to the COLMAP map (already a reconstructor dep; see `docker/reconstructor/src/reconstructor/colmap.py:138` for existing usage).
- **scipy** — `spatial.ConvexHull(centers).volume` for `map_bounding_volume_m3`; `optimize.minimize` for the Σ_meas α, β MLE.
- **sklearn** — `linear_model.LogisticRegression`, `isotonic.IsotonicRegression`, `metrics.brier_score_loss`, `calibration.calibration_curve`.
- **pytransform3d** — SE(3) `log` for computing the 6-D residuals fed to the Σ_meas fit. New dep, added to the `scripts` package.

Things hand-rolled (small, well-defined):

- **Viewpoint diversity** — design metric, no library covers it. Pick a definition (variance of unit viewing-direction vectors); ~10 lines numpy.
- **Σ_meas α/β NLL** — custom 2-D Gaussian negative-log-likelihood passed to `scipy.optimize.minimize`; ~20 lines.

## Architecture

```
                          ┌──────────────────────────────┐
                          │ Corpus (offline, on disk)    │
                          │ ../placeframe-test-captures/ │
                          │   {location}/{device}/       │
                          │     capture.tar              │
                          └──────────────┬───────────────┘
                                         │
                                         ▼
                       ┌──────────────────────────────────────┐
                       │ scripts/test_placeframe_e2e.py       │
                       │  Phase 1: discover                   │
                       │  Phase 2: prepare (withhold frames)  │
                       │  Phase 3: upload                     │
                       │  Phase 4: generate config matrix     │
                       │  Phase 5: reconstruct (per config)   │
                       │  Phase 6: localize held-out frames   │
                       │  Phase 7: label pose error  *NEW*    │
                       │  Phase 8: persist rows               │
                       └──────────────┬───────────────────────┘
                                      │ rows: (metrics, map_features,
                                      │        recon_config, loc_config,
                                      │        device, err_t, err_r)
                                      ▼
                       ┌──────────────────────────────────────┐
                       │ scripts/fit_calibration.py  *NEW*    │
                       │  - pool rows                         │
                       │  - fit logistic + isotonic           │
                       │  - fit Σ_meas α, β                   │
                       │  - emit fit report                   │
                       │  - write config/calibration/         │
                       │    global.json                       │
                       └──────────────┬───────────────────────┘
                                      │
                                      ▼
                       ┌──────────────────────────────────────┐
                       │ Localizer (deployed)                 │
                       │  - load_global_calibration() at boot │
                       │  - features plumbed into             │
                       │    apply_global_calibration()        │
                       │  - returns calibrated Confidence     │
                       └──────────────────────────────────────┘
```

The harness can run in two modes:
- **Full sweep**: 17 recon configs × N captures × 9 loc configs per held-out frame. Many hours. Used to pick reconstruction defaults *and* fit calibration in one pass.
- **Fit-only / single-config**: one recon config (server defaults), one loc config (server defaults), all captures. Much faster. Used during code iteration and for incremental calibration refits when the sweep hasn't recently been run.

Both modes produce the same row schema; `fit_calibration.py` is mode-agnostic.

## Algorithm 1: ZED held-out fitting

Source: every capture session in the corpus that contributes a built map.

Procedure per capture:
1. **Hold out frames at map-build time.** Withhold every 9th frame (the harness's existing scheme — 1/9 ≈ 11% held-out). Rebuild the COLMAP map from the remaining 8/9.
2. **Solve `T_truth_to_map` via Procrustes/Umeyama** on the in-set images: each in-set image has both a COLMAP-reconstructed pose `P_map_i` (in map frame) and a `frames.csv` truth pose `P_truth_i` (in capture-session local frame, sourced from the device's VIO/SLAM at capture time). Solve the rigid + scale alignment closed-form on `(P_truth_i, P_map_i)` pairs using pycolmap's `Sim3d` primitives (the reconstructor already uses these at `colmap.py:138`).
3. **Per held-out frame**:
   - Transform its truth pose into map frame: `P_truth_in_map = T_truth_to_map · P_truth`.
   - Run the localizer on the held-out frame against the rebuilt map: `(P_estimated, metrics)`.
   - Compute pose errors: `err_t = ||translation(P_truth_in_map) − translation(P_estimated)||`, `err_r = angle_between(rotation(P_truth_in_map), rotation(P_estimated))`.
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
3. **Per-map calibrations are NOT loaded eagerly.** First localization request for a map triggers a lazy MinIO fetch + in-memory cache keyed by map ID. If absent: log, fall back to global-only. If pipeline-version-mismatched: log loudly, fall back to global-only.

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
  # metrics.confidence.tight < TIGHT_MIN. Admitted measurements use
  # this Σ_meas regardless of confidence value.
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

Computed at map-build time inside `MetricsBuilder.build_reconstruction_metrics` and written to `manifest.json` in MinIO as part of the existing `ReconstructionMetrics` block — no separate "map quality" concept exists; these are reconstruction metrics. The harness fetches the manifest per reconstruction at row-emission time (same code path the existing `get_reconstruction_manifest` API already uses). At runtime the localizer reads them from the same manifest. `is_indoor` is the exception — a user-controlled boolean column on `reconstructions`, since it isn't computed from the reconstruction.

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

Updating global: run fit → `git diff` → review → PR → merge → deploy. No Docker rebuild (mounted as compose `configs:` volume).

Per-map: lazy load on first request, cached. Optional `POST /calibration/refresh/{map_id}` admin endpoint to invalidate cache after re-upload.

## Corpus-gathering spec (for future-operator-self)

When the time comes to gather the multi-capture corpus and run the *production* calibration (replacing the single-capture starter that ships at the end of this initiative), this is the spec.

### Layout

Create a directory **as a sibling of the placeframe repo root** (not inside it):

```
~/code/                      # or wherever the repo lives
  placeframe/                # this repo
  placeframe-test-captures/  # sibling — corpus lives here
    {location}/
      {device}/
        capture.tar
```

The harness reads from `../placeframe-test-captures/` relative to the repo root — `REPO_ROOT.parent / "placeframe-test-captures"` in the script.

### What `{location}` is

A short string identifier for the physical scene. The harness uses it to pair captures across devices: a ZED capture and a phone capture with the same `{location}` directory name will be cross-device-localized against each other's maps. Use any human-readable name that's stable across captures of the same place. Example: `lab-east-corner`, `garage-bay-2`.

### What `{device}` is

Exactly one of:
- `zed` — for ZED rig captures.
- `arfoundation` — for AndroidMobile (ARFoundation) captures.

These map to `DeviceType.ZED` and `DeviceType.ARFOUNDATION` in the API client. Other names are skipped with a warning.

### What `capture.tar` is

A capture session tarball produced by the existing capture pipeline (ZED Capture for ZED, Capture Tool for ARFoundation). Inside:

- `manifest.json` — `CaptureSessionManifest`: axis convention, rigs (with cameras and intrinsics), capture interval.
- `rig0/frames.csv` — per-frame poses from the device's VIO/SLAM at capture time. Columns: `timestamp,tx,ty,tz,qx,qy,qz,qw`. **These are the truth poses Algorithm 1 Procrustes-aligns to the rebuilt map.**
- `rig0/camera0/{timestamp}.jpg` — frame images.
- `rig0/camera1/{timestamp}.jpg` — second eye, ZED only.

The capture pipelines already produce this layout; you don't have to construct it by hand.

### How many captures, what content

Minimums for a meaningful run:
- **At least 2 distinct ZED captures** (Algorithm 1 needs ZED truth poses; one capture alone gives no inter-capture variance).
- **At least 2 distinct locations** so map-quality features have variance (otherwise they collapse to the intercept). Same scene captured twice doesn't count.
- **For cross-device validation**: matched ARFoundation captures at the same locations.

Per capture:
- ≥ ~100 frames recommended (the harness withholds 1/9, so ~11 held-out queries per capture; 4 captures gives ~44 queries × 17 recon configs × 9 loc configs ≈ 6700 labeled rows).
- Real scenes representative of deployment. Indoor for current target.
- Standard capture practice: continuous motion, varied viewpoint, minimal motion blur. The capture pipelines enforce some of this; the rest is operator discipline.

Stretch goals (for richer calibration):
- Multiple lighting conditions per location (morning vs. evening).
- Indoor + outdoor mix once outdoor masking ships (Phase 2d).
- A range of map sizes (small room, large room, multi-room) to give `map_*` features genuine variance.

### How to run

Once the corpus is in place:

```bash
# Full sweep (~15 hours): 17 recon configs × N captures × 9 loc configs per held-out frame
uv run test-placeframe-e2e

# Fit-only / single-config (much faster): server-default recon + loc config, all captures
uv run test-placeframe-e2e --single-config   # (flag TBD — see open question 7)

# Fit calibration from the harness's row output
uv run fit-calibration

# Review the diff in config/calibration/global.json, commit, deploy
```

`fit_calibration.py` reads the localizer's git SHA at run time and embeds it as `pipeline_version`. The deploy after fitting must be from that same SHA. Refit on every pipeline-affecting change to the localizer.

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
3. **Held-out frames stay implemented as harness-side tar surgery.** Already-implemented `_prepare_capture` keeps; no `held_out_image_ids` reconstructor option.
4. **Procrustes residuals are surfaced per-capture in the fit report.** Operator decides from the report whether to drop a capture; no auto-drop threshold in v1.
5. **`pipeline_version` chicken-and-egg is handled by operator discipline.** No auto-commit; the loader's startup hard-fail surfaces any mismatch before traffic flows.
6. **Σ_meas decoupled from confidence.** Replaced `PnP_cov / tight²` with `α · PnP_cov + β · I`, with α, β fit empirically in `fit_calibration.py` against held-out SE(3) residuals. Confidence becomes a binary gate (`tight < TIGHT_MIN` rejects); admitted measurements use Σ_meas regardless of confidence value.
7. **`--single-config` CLI flag** on `test-placeframe-e2e`. Short-circuits Phase 4 to `[None]` and skips the loc-config cross product. Used for fast iteration and incremental refits.
8. **Bad `frames.csv` truth has no code-side action.** Procrustes residual reporting (decision 4) is the operator-facing diagnostic. No "bad capture" flag in the schema.
9. **No synthetic corpus fixture.** CI is out of scope for this initiative; deferred to a separate effort if/when CI ever wants to exercise the harness path.
10. **Band-aids removed in this initiative**, not deferred. The single-capture starter calibration committed as deliverable 10 unblocks the swap. `TIGHT_MIN` is read off the starter fit's success-cluster distribution rather than guessed (deliverable 11).
11. **Refit cadence is "manual, on demand."** Removed weekly/quarterly framing.

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
