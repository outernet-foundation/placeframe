# test-placeframe-e2e: Implementation Context

## What this script does

Systematically evaluates reconstruction and localization quality across different parameter configurations, device types, and physical locations. The goal is parameter optimization — finding which reconstruction/localization knobs produce the best localization metrics, including cross-device scenarios (e.g., localizing a phone image against a ZED-built map).

## Current state

The script exists at `scripts/src/scripts/test_placeframe_e2e.py` and the entry point is registered in `scripts/pyproject.toml` as `test-placeframe-e2e`. The script is functionally complete but has quality problems that need fixing before it passes lint/type checks.

## Files

- **Script**: `scripts/src/scripts/test_placeframe_e2e.py`
- **Entry point**: `scripts/pyproject.toml` → `test-placeframe-e2e = "scripts.test_placeframe_e2e:app"`
- **Dependencies added to `scripts/pyproject.toml`**: `core`, `placeframe-api-client`, `httpx>=0.28.1`

## Problems to fix

### 1. Lint errors (must fix before merging)

Two ruff errors remain:

- **S608** on `_build_insert_sql` (line ~151): `f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"` triggers "Possible SQL injection vector through string-based query construction." The keys come from our own hardcoded dicts, not user input, so this is a false positive. Options: (a) restructure to avoid dynamic SQL entirely (maybe maintain a canonical column list), (b) get user approval to add `noqa: S608`.

- **ASYNC240** on glob call: `captures_dir.glob(...)` inside the async `_run` function triggers "Async functions should not use pathlib.Path methods." The fix was started but not finished — `_run` now takes `tar_paths: list[Path]` as a param, but `main()` at the bottom was never updated to pass it. Fix: add `tar_paths = sorted(captures_dir.glob("*/*/capture.tar"))` to `main()` and pass it to `_run`.

### 2. The `main()` function is broken

`main()` still calls `_run(captures_dir, output_db)` with 2 args, but `_run` now expects 3 (`captures_dir`, `output_db`, `tar_paths`). The glob needs to happen in `main()` (sync) and get passed to `_run` (async).

### 3. Inline SQL in report section (readability concern, not a blocker)

The Phase 7 report section (lines ~519-636) has 4 raw SQL SELECT queries inline in `_run`. These are analytical aggregation queries — they're inherently SQL and arguably fine. The INSERT SQL was already fixed with the dict-based `_insert_result` + `_recon_row` approach. The user may want to revisit whether the report queries should be extracted or restructured, but they work correctly as-is.

### 4. Type check status

The script passed `basedpyright` (0 errors) before the last round of edits. It should still pass but hasn't been re-verified after the S608/ASYNC240 fixes.

## Architecture (7 phases)

1. **Discover captures** — Walk `../placeframe-test-captures/{location}/{device}/capture.tar`, parse `manifest.json` for axis convention + camera configs
2. **Prepare captures** — For each tar, withhold every 9th frame (0-indexed: indices 8, 17, 26...) as localization query images. Rebuild tar without those frames. For ZED stereo: withhold both camera0 and camera1 images, use camera0 as query.
3. **Upload captures** — POST each modified tar to the API once
4. **Generate experiment matrix** — 17 configs: 1 baseline (all server defaults) + 16 Plackett-Burman screening rows for 10 factors
5. **Run reconstructions** — 4 captures × 17 configs = 68 reconstructions, sequentially. Poll status every 10s. On success, create a localization map with identity transform.
6. **Cross-device localization** — For each location, localize ALL withheld query images (from ALL captures at that location) against ALL maps at that location. Localization param grid: `retrieval_top_k` × `ransac_threshold` = 3×3 = 9 combos per query-map pair.
7. **Report** — Query SQLite, produce markdown summary

## Key API client details

All from `placeframe_api_client` (generated, at `packages/generated/python/api-client/`):

| Method | Signature |
|--------|-----------|
| `create_capture_session` | `(CaptureSessionCreate) → CaptureSessionRead` |
| `upload_capture_session_tar` | `(id: UUID, file: tuple[str, bytes]) → None` |
| `create_reconstruction` | `(ReconstructionCreateWithOptions) → ReconstructionRead` |
| `get_reconstruction_status` | `(id: UUID) → OrchestrationStatus` |
| `get_reconstruction_manifest` | `(id: UUID) → ReconstructionManifest` |
| `create_localization_map` | `(LocalizationMapCreate) → LocalizationMapRead` |
| `localize_image` | `(map_ids, camera_config, axis_convention, retrieval_top_k, ransac_threshold, image) → list[MapLocalization]` |

- **Auth**: Password grant to Keycloak at `https://{PUBLIC_DOMAIN}/auth/realms/placeframe-dev/protocol/openid-connect/token`, client_id=`placeframe-api`, username=`user`, password=`password`
- **API URL**: `https://{PUBLIC_DOMAIN}` (read from `.env`)
- **SSL**: `verify=False` for httpx, `ssl_ca_cert=False` for generated client (ngrok handles TLS)

## Key model details

- `ReconstructionOptions` — all fields Optional, None = server default. The 10 factors we vary: `neighbors_count`, `ransac_max_error`, `ransac_min_inlier_ratio`, `triangulation_minimum_angle`, `use_prior_position`, `bundle_adjustment_refine_focal_length`, `bundle_adjustment_refine_principal_point`, `bundle_adjustment_refine_additional_params`, `mapper_filter_max_reprojection_error`, `triangulation_complete_max_reprojection_error`
- `ReconstructionMetrics` — fields: `total_images`, `registered_images`, `registration_rate`, `num_3d_points`, `reprojection_pixel_error_50th_percentile`, `reprojection_pixel_error_90th_percentile`, etc.
- `LocalizationMetrics` — fields: `inlier_ratio`, `reprojection_error_median`, `num_inliers`, `num_correspondences`, `num_matches`, `inlier_coverage`
- `OrchestrationStatus` — enum: `queued`, `pending`, `running`, `succeeded`, `cancelled`, `failed`
- `DeviceType` — enum: `ARFoundation`, `Zed`
- `AxisConvention` — enum: `OPENCV`, `UNITY`

## Design rules applied

- **No single-use helpers** — everything called from one site is inlined, except helpers that reduce nesting (`_prepare_capture`, `_run_reconstruction`)
- **Multi-call-site helpers** — `_recon_row` (builds base row dict, called from recon failure path + localization loop), `_insert_result` (dict-based INSERT, called from both paths), `_build_insert_sql` (called by `_insert_result`)
- **Dict-based SQL inserts** — row dicts with keys = column names, no hand-written column lists or positional `?` markers
- **Flat loops** — localization tasks pre-computed as flat list via list comprehension + `itertools.product`, iterated with `continue` for early exits
- **Dataclasses** — `CaptureInfo`, `WithheldFrame`, `ReconResult`

## SQLite schema

Single `results` table. Each row is either a failed-reconstruction record (localization fields NULL) or a localization result (all fields populated). Schema defined in `CREATE_TABLE_SQL` constant in the script.

## Test captures layout

```
../placeframe-test-captures/
  {location}/
    {device}/          # "zed" or "arfoundation"
      capture.tar      # contains manifest.json, rig0/frames.csv, rig0/camera0/*.jpg, etc.
```

4 captures expected: 2 locations × 2 devices.

## Estimated scale

- 68 reconstructions (~10 min each = ~11 hours)
- ~7,200 localizations (~2 sec each = ~4 hours)
- Total runtime: ~15 hours for a full run
