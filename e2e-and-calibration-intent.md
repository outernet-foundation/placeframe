# End-to-end testing and calibration — Intent

> Execution and progress tracked in [`plan.md`](plan.md).
> This initiative fuses two previously-separate efforts: the parameter-sweep harness (originally `test-placeframe-e2e.md`, deleted in `c84375ea`, recoverable from git history) and the VPS calibration design (originally Phase 3 of `vps-redesign-intent.md`).

## Status

Code only. **No corpus exists yet, and the full parameter sweep is explicitly out of scope for this effort.**

The goal of this initiative is to land code that is logically correct end-to-end so that, when a corpus is later assembled, the existing code path produces a real calibration without further engineering work blocking the run. It also produces, as a deliverable, an unambiguous corpus-gathering spec for future-operator-self.

The current state is a half-state:
- The e2e harness has lint/type errors and a half-finished signature change in `main()`.
- The calibration runtime loader has a hand-set band-aid intercept (`-4.595`) and a never-removed `IDENTITY_BOOTSTRAP_SENTINEL` skip path.
- `apply_global_calibration` is called with `features={}` because no features are plumbed.
- `localize.py` carries a raw-metric quality floor (`MIN_NUM_INLIERS=50`, `MIN_INLIER_COVERAGE=0.15`) as a band-aid for the constant-confidence stub.
- `scripts/src/scripts/fit_calibration.py` doesn't exist.
- The maps schema has no map-quality columns and the reconstructor doesn't compute them.

This initiative climbs out of that.

## Why these are one effort

The discovery that drove fusion: the e2e harness is the calibration data-generation engine. They are not two scripts that happen to share captures; they are the same script with overlapping outputs.

- Algorithm 1 of the calibration design (ZED held-out fitting) requires a corpus of capture sessions, each rebuilt with ~10% of frames withheld, the held-out frames localized against the rebuilt map, and `(metrics, pose_error)` rows pooled into a fit. The held-out-tar machinery this requires is exactly what `_prepare_capture` in `test_placeframe_e2e.py:156` already does (it withholds every 9th frame, rebuilds the tar, keeps the withheld frames as queries).
- The e2e harness already produces `(metrics, location, device_type, recon_config)` rows for every (held-out frame × map × loc-config) cell. What's missing for Algorithm 1 is the *pose-error labeling step* — Procrustes-align each capture's `frames.csv` truth to the rebuilt COLMAP map, transform the held-out frame's truth pose, compare to the localizer's estimate, record `err_t` and `err_r`. That's a delta to the harness, not a new script.
- The harness's Phase 6 already runs cross-device localization (e.g. phone-frame against ZED-built map). Algorithm 2's phone-side data is one column of the same matrix.

The original plan separated Phase 2e ("repair harness, run sweep, pick reconstruction defaults") and Phase 3 ("fit calibration against the picked defaults") as if they were sequential and independent. They aren't — the sweep cells are the calibration training rows. The sweep gives a richer training set (multiple recon configs × multiple loc configs × multiple captures); the calibration fits across all of them; the sweep can rank parameter choices using fitted confidence as one of its metrics.

## What this initiative produces

**Code deliverables:**

1. Repair `scripts/src/scripts/test_placeframe_e2e.py`: fix the S608 false-positive on `_build_insert_sql`, fix the ASYNC240 violation on the glob, complete the half-finished signature change so `main()` actually passes `tar_paths` into `_run`, re-verify `basedpyright` passes.
2. Extend the harness to label pose error per held-out frame: Procrustes-align `frames.csv` truth poses to the rebuilt COLMAP map, transform held-out truth into map frame, compute `err_t` and `err_r` against the localizer estimate, persist alongside the existing metrics.
3. Add map-quality features to the schema and reconstructor: columns on `localization_maps` (or `reconstructions`) for `map_image_count`, `map_point_count`, `map_avg_track_length`, `map_bounding_volume_m3`, `map_viewpoint_diversity`, `is_indoor`. Reconstructor computes them at map-build time. Migration backfills existing rows.
4. Create `scripts/src/scripts/fit_calibration.py`: pulls the labeled rows produced by the harness (or invokes the harness in a "fit-only" mode), pools them, fits Algorithm 1's logistic + isotonic for tight and loose, writes `config/calibration/global.json` with the localizer's git SHA as `pipeline_version`. Emits a fit report (Brier, reliability, sample count, Procrustes residual per capture).
5. Plumb features through `apply_global_calibration`: `build_metrics.py:66` currently passes `features={}`. Wire transformed metrics + map features into the dict keyed by the calibration's `feature_names`.
6. Remove the band-aids: `IDENTITY_BOOTSTRAP_SENTINEL` and its skip in `calibration.py`; `MIN_NUM_INLIERS` / `MIN_INLIER_COVERAGE` in `localize.py` (replace with `if metrics.confidence.tight < TIGHT_MIN`); the hand-set `-4.595` intercept in `global.json`. **These removals only happen once a real fitted calibration is committed**; they cannot land before the corpus exists.
7. Per-map calibration loader path: lazy MinIO fetch + cache, fall back to global-only if absent. **Per-map fitting (Algorithm 3) is deferred to a later phase.** Only the loader plumbing lands now.
8. Frontend Σ_meas re-tuning: a noted follow-up, not code in this initiative. The `BaseProcessNoise` and `SnapThresholdSigmas` constants in `RelocalizationFilter` are tuned against fitted σ_meas — which doesn't exist until the corpus is gathered. Tracked as scaffolding to be replaced.

**Documentation deliverable:**

9. Corpus-gathering instructions (this file's "Corpus-gathering spec" section). Unambiguous enough to execute cold.

**Non-deliverables (explicit):**

- Running the parameter sweep. Estimated ~15 hours per full run; not part of this effort.
- Gathering any captures.
- Producing a real `config/calibration/global.json` artifact. The bootstrap identity stays in place until the corpus is gathered and the fit is run.
- Algorithm 2 (phone-side pairwise calibration). Algorithm specified below for completeness; code lands in a later phase.
- Algorithm 3 (per-map fitting). Algorithm specified below; code lands in a later phase.

## What "logically correct without a corpus" means

The validation bar for this initiative is intentionally bounded: code that compiles, type-checks, lints, and passes whatever unit tests are reasonable to write without real data. That covers more than it sounds:

- The harness can run end-to-end against an empty corpus (zero captures discovered) and exit cleanly. This is a real test — it exercises auth, API client, file discovery, and the no-data path.
- The harness can run against a fake corpus of 1 trivial capture to verify the upload → reconstruct → localize → label → record path. (Trivial = a few synthetic-or-existing frames; doesn't have to produce a meaningful map.)
- `fit_calibration.py` can be unit-tested for the Procrustes solve (synthetic point pairs with known alignment) and for round-trip artifact write/read.
- The runtime loader change (features plumbed through) can be tested by feeding a hand-written calibration with known weights and verifying the output Confidence matches the math.
- The schema migration applies clean against the test database and the reconstructor populates the new columns on the next reconstruction.

What we *can't* validate without a corpus: that the fitted logistic produces meaningful probabilities, that the Procrustes residuals are small enough for truth poses to be useful, that map-quality features actually have signal, that calibration generalizes across captures. Those are the things the corpus run will answer.

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
2. **Solve `T_truth_to_map` via Procrustes/Umeyama** on the in-set images: each in-set image has both a COLMAP-reconstructed pose `P_map_i` (in map frame) and a `frames.csv` truth pose `P_truth_i` (in capture-session local frame, sourced from the device's VIO/SLAM at capture time). Solve the rigid + scale alignment closed-form on `(P_truth_i, P_map_i)` pairs.
3. **Per held-out frame**:
   - Transform its truth pose into map frame: `P_truth_in_map = T_truth_to_map · P_truth`.
   - Run the localizer on the held-out frame against the rebuilt map: `(P_estimated, metrics)`.
   - Compute pose errors: `err_t = ||translation(P_truth_in_map) − translation(P_estimated)||`, `err_r = angle_between(rotation(P_truth_in_map), rotation(P_estimated))`.
   - Record `(metrics, map_features, recon_config, loc_config, device, err_t, err_r)`.
4. **Pool across all captures and configs.** Add binary labels: `success_tight = err_t < 5cm AND err_r < 1°`, `success_loose = err_t < 30cm AND err_r < 5°`.
5. **Fit logistic regression** (sklearn `LogisticRegression(class_weight='balanced')`) on the feature vector. Features: `log(num_inliers + 1)`, `inlier_ratio`, `reproj_err / image_diagonal_pixels`, `inlier_coverage`, `log(num_matches + 1)`, `log(map_image_count + 1)`, `log(map_point_count + 1)`, `map_avg_track_length`, `log(map_bounding_volume_m3 + 1)`, `map_viewpoint_diversity`, `is_indoor`.
6. **Fit isotonic** (sklearn `IsotonicRegression(out_of_bounds='clip')`) on the logistic output against the same labels.
7. **Optional 10% holdout** for Brier score and reliability diagram; report in fit metadata.

Output: `{tight: {logistic, isotonic}, loose: {logistic, isotonic}, fit_metadata, pipeline_version}` written to `config/calibration/global.json`.

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
features = transform(metrics, map_quality_features)
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

A few dozen FLOPs plus two isotonic lookups (binary search over ~100 breakpoints). Negligible cost.

**Failure modes:**

| Condition | Behavior | Rationale |
|---|---|---|
| Global calibration file missing at startup | Hard-fail startup | Indicates a broken deploy. |
| Global calibration pipeline-version mismatch | Hard-fail startup | Stale calibration vs new pipeline; refit required before serving. |
| Per-map calibration missing | Soft-fail: log + fall back to global-only | Expected for new/sparse-data maps; system still functional. |
| Per-map calibration pipeline-version mismatch | Soft-fail: log + fall back to global-only | Stale per-map; rebuild on next refit cycle. |

## Map quality features

Computed at map-build time, stored as columns on `localization_maps` (or `reconstructions` — see open question 1):

- `map_image_count`: total registered images.
- `map_point_count`: total triangulated 3D points.
- `map_avg_track_length`: mean number of observations per 3D point.
- `map_bounding_volume_m3`: convex hull volume of camera centers, in cubic meters.
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
    "loose": { "logistic": {...}, "isotonic": {...} }
  }
}
```

Per-map artifact has the same shape but only `tight.isotonic` and `loose.isotonic` blocks (the global logistic is the upstream).

## Storage and lifecycle

| Artifact | Path | Updated by | Cadence |
|---|---|---|---|
| Global calibration | `config/calibration/global.json` (git repo) | Engineer (PR after running fit pipeline) | When sweep produces a meaningful update |
| Per-map calibrations | `s3://placeframe-maps/{map_id}/calibration.json` (MinIO) | Fit pipeline (automated upload) | Per map: when sample count grows 50% or weekly |
| Phone-side calibration data (raw logs) | `s3://placeframe-calibration-data/sessions/{session_id}.json` (MinIO) | AndroidMobile app (when dogfooding toggle is on) | Per session at session end |

Updating global: run fit → `git diff` → review → PR → merge → deploy. No Docker rebuild (mounted as compose `configs:` volume).

Per-map: lazy load on first request, cached. Optional `POST /calibration/refresh/{map_id}` admin endpoint to invalidate cache after re-upload.

## Corpus-gathering spec (for future-operator-self)

When the time comes to gather the corpus and run the calibration for real, this is the spec.

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

## Open questions

These are the questions left unresolved by this document. They're the agenda for resuming this initiative cold.

1. **Where do map-quality columns live: `localization_maps` or `reconstructions`?** Maps are the calibration-relevant unit (calibration is a map-aware decision), but the features are computed during reconstruction. Tradeoff: features-on-reconstructions means joining at calibration time; features-on-maps means duplicating if a reconstruction backs multiple maps (currently it can't — there's a `UNIQUE (reconstruction_id)` constraint — but the data model doesn't actively prevent the future possibility).

2. **Map-features-as-features-vs-deferred for the first fit.** Including them in the logistic when we have one or two maps is meaningless (constants). Land the schema + reconstructor changes now, but does the *fitting code* include them in the feature vector unconditionally and let the regression weight them to zero, or does it gate them on having ≥3 distinct maps in the corpus? Recommended: unconditional + let regression handle it. Confirm.

3. **Held-out at map-build infrastructure: harness-side tar surgery vs. reconstructor-side option.** The harness today preprocesses tars to remove withheld frames before upload (`_prepare_capture`). The earlier draft of Phase 3 considered adding `held_out_image_ids` to `ReconstructionOptions` instead. Tar surgery is what's already implemented; recommended: keep it. Confirm.

4. **Procrustes-residual surfacing.** For each (capture, recon_config) pair, the Procrustes solve on in-set images has a residual. Large residuals mean the truth source (frames.csv) is too noisy for Algorithm 1 to work for that capture. The fit report should surface these per-capture so bad captures are identifiable. **Should the fit script also automatically drop captures with residuals above a threshold?** If yes, what threshold (in meters)? Recommended: surface per-capture, don't auto-drop in v1; let the operator decide from the report.

5. **`pipeline_version` chicken-and-egg.** `fit_calibration.py` embeds the localizer's git SHA at fit time. The deploy after fitting must come from that same SHA — there's a window where the calibration is fit, the SHA changes (someone commits something localizer-touching), and the now-stale calibration would hard-fail on the next deploy. **Should the fit script also auto-commit (or auto-PR) the calibration with a fixed SHA reference**, so the calibration commit *is* the deploy point? Or is "operator discipline" sufficient? Recommended: operator discipline; the loader's hard-fail surfaces the mismatch before serving traffic.

6. **Σ_meas scaling formula.** Currently `Σ_meas = PnP_cov / tight²` with a hand-tuned 10000× inflation via the `tight = 0.01` band-aid intercept. Once the band-aid is gone, real fitted `tight` values are typically much higher (e.g. 0.7), giving only ~2× inflation — likely too tight. The intent doc flags the formula as "a tuning detail in the offline calibration step's 'what does Σ_meas mean' decision" — but doesn't specify what the replacement is. Three options:
   - Keep the formula, accept that `Σ_meas` will be too tight in practice, and re-tune `RelocalizationFilter.BaseProcessNoise` and `SnapThresholdSigmas` to compensate at the filter level.
   - Replace the formula with one fit empirically: `Σ_meas = α · PnP_cov + β · I` with `α, β` chosen so the empirical pose-error distribution on the held-out set matches the predicted Σ_meas (a one-time offline calibration on top of the calibration).
   - Defer this question to Phase 5 when phone-side data validates the formula end-to-end against VIO drift.
   Recommended: option (b), small offline addition to `fit_calibration.py`. Confirm.

7. **Harness "single-config" / "fit-only" mode.** Today the harness runs the full Plackett-Burman sweep (17 configs). For fast iteration during this initiative — and for incremental refits when only the corpus has changed, not the parameter grid — a single-config mode that uses server defaults for everything is needed. Should this be a new CLI flag, an env var, or a separate entry point? Recommended: `--single-config` flag on `test-placeframe-e2e`.

8. **Per-capture `frames.csv` truth-pose quality varies by device.** ZED VIO is high-quality and multi-second-stable. ARFoundation VIO is also good but session-relative; for short sessions (< a few minutes) it's plenty for Procrustes. **What do we do if a capture's frames.csv truth is bad?** No code-level answer; this is a runtime open question that surfaces via Procrustes residual reporting (see #4).

9. **Fit script test surface.** Procrustes solve on synthetic point pairs is a clean unit test. Round-trip artifact write/read is a smoke test. The full fit-against-real-data path can't be tested without a corpus. **Is there value in a "tiny synthetic corpus" fixture — a hand-constructed ~10-image-per-capture setup checked into the repo — that lets us at least exercise the harness's full path in CI?** Tradeoff: real CI signal vs. tens of MB of binary fixtures. Recommended: defer; the harness's no-data path (zero captures discovered) is the CI test.

10. **Removing the `MIN_NUM_INLIERS` / `MIN_INLIER_COVERAGE` band-aid before the corpus exists.** The replacement is `if metrics.confidence.tight < TIGHT_MIN: raise LocalizationError(...)`. **`TIGHT_MIN` defaults to what?** Today's band-aid rejects garbage; pre-corpus the calibration is identity-bootstrap so `tight` is constant (0.01) and a `tight < TIGHT_MIN` check is trivial. The band-aid stays in place until a real fitted calibration exists; this is the "removal happens after corpus" piece of code deliverable 6. Confirm.

11. **The intent doc framing of "calibration refit cadence."** The original `vps-redesign-intent.md` said "weekly initially, slowing to quarterly." With ~15-hour fits and the harness doubling as the parameter sweep, that cadence was always aspirational. Realistic cadence: refit on every pipeline-affecting change, otherwise once when the corpus first lands. **Does the doc need an explicit cadence section, or is "manual on demand" the truthful description?** Recommended: just say "manual on demand" and remove the weekly/quarterly framing.

## Risks and unknowns

- **Procrustes-as-truth assumption.** Algorithm 1 treats `T_truth_to_map · P_truth_i` as ground truth for the held-out frame. The truth source is `frames.csv` — the device's VIO/SLAM pose from capture time. ZED VIO is good but not perfect; ARFoundation VIO drifts noticeably over multi-minute sessions. The Procrustes residual on in-set images is the diagnostic, but it can mask issues: a globally-drifting VIO can be fit by Procrustes with low residual and still produce systematically biased held-out truth.
- **Cold-start with one capture in the corpus.** Even with one capture, the harness can run end-to-end and produce a fitted artifact. The artifact will overfit to that capture's scene/lighting/device and won't generalize. Operator discipline: don't ship a single-capture fit as the production calibration.
- **Schema migration backfill.** Existing reconstructions in the database don't have map-quality features computed. The migration backfills with NULLs (or computes from stored COLMAP output if accessible). NULL handling in `apply_global_calibration` needs explicit policy — feature-vector NaN propagates to logistic NaN. Recommended: NULLs treated as feature-vector zeros at runtime, with a log line; the fit script only uses rows where features are populated.
- **Test corpus size for sweep.** The estimate of "~15 hours full run" comes from the orphaned md, and assumed 4 captures × 17 recon configs × N localizations. With more captures the runtime scales linearly in capture count and frame count. A corpus with ~10 captures and richer per-capture frame counts could easily push the full sweep past a day. The single-config mode is the workaround.
- **`pipeline_version` churn in active development.** Every commit that touches the localizer's relevant config invalidates the calibration. During this initiative the fit doesn't run, so churn doesn't bite. Once a real calibration is committed, this becomes a real friction point — see open question 5.

## Where this used to live

For future archaeology if any of this content needs to be cross-referenced against the original sources:

- The orphaned `test-placeframe-e2e.md` was last present in `07133e66`. Read with `git show 07133e66:test-placeframe-e2e.md`.
- VPS Phase 3's calibration design lived in `vps-redesign-intent.md` as the "Calibration loader", "Confidence computation per query", "Map quality features", "Calibration", "Offline fitting pipeline" sections. Excised when this file was created — see git blame on `vps-redesign-intent.md`.
- VPS Phases 5 and 6 (phone-side correction, per-map overlay) referenced Algorithms 2 and 3 here; their algorithm bodies moved to this file under "Algorithm 2 / 3 (deferred)".
- Feature-pipeline Phase 2e referenced the e2e harness; that reference was excised when this file was created.
