# scripts/

## What this is

`scripts/` is a Python workspace member that ships the repo's Python CLI surface as `uv run` commands registered in `pyproject.toml`'s `[project.scripts]`. Three cohorts: codegen and repo-CI tooling (`generate-datamodels`, `publish-compose`, the CI sidecar `scripts/preflight.py`), small operational utilities (Unity adb-forward, Docker debug-target listing, Loki query), and the calibration pipeline (`fit-calibration`, `tune-reconstruction`, the held-out selector registry, the shared auth helper). The Docker-stack lifecycle commands (`up`, `down`, `build`) live in the standalone [`docker-devkit`](https://github.com/outernet-foundation/docker-devkit) repo; `lock-python` and `preflight-python` live in [`python-devkit`](https://github.com/outernet-foundation/python-devkit); `install` (download or build-then-install Unity APKs / linux executables) lives in the standalone [`unity-devkit`](https://github.com/outernet-foundation/unity-devkit) repo so cross-repo consumers can use it. The calibration pipeline and `publish-compose`'s config inlining carry the directory's tests; the operational utilities are small self-contained shell-out scripts.

`scripts/preflight.py` is the CI preflight sidecar and must stay at the directory root: github-actions-toolkit's preflight reusable invokes it by that exact path (`uv run --locked scripts/preflight.py`). It runs the python battery (`uv run --locked preflight-python`), then the repo checks in-process (image refs, image version couplings, database setup, datamodel codegen staleness), then the client staleness gate (`uv run --locked generate-clients --config openapi-client-codegen.yaml --check`).

## Shape

### Entry points

Registered in `scripts/pyproject.toml`:

| `uv run` command | Module | What it does |
|---|---|---|
| `generate-clients` | `openapi_client_codegen.cli:app` (alias) | Entry into [`openapi-client-codegen`](https://github.com/outernet-foundation/openapi-client-codegen)'s config-driven orchestrator; `openapi-client-codegen.yaml` at the repo root carries identity and spec commands. Needs Java 11+ on PATH. |
| `generate-datamodels` | `generate_datamodels.py` | Runs `sqlacodegen` (custom `PlaceframeDeclarativeGenerator` in `sqlacodegen_generator.py`) against the live postgres → `packages/generated/python/datamodels/` (SQLAlchemy + Pydantic DTOs). Requires the stack up; see the generation-pipeline ordering in the root `AGENTS.md`. |
| `publish-compose` | `publish_compose.py` | CI-only: bakes the compose bundle (var substituted, configs inlined, image refs digest-pinned) and publishes it to ghcr per cuda/rocm variant. Invoked from `integrate.yml`'s local `publish-compose` job; assumes the CI environment (GitHub token, ghcr login). |
| `forward-unity-android-debug-port` | `forward_unity_android_debug_port.py` | Auto-detects the single adb device, finds the listening Unity debugger port in 56000–56999 via `/proc/net/tcp{,6}`, and `adb forward tcp:56000 tcp:{found}`. |
| `list-debug-targets` | `list_debug_targets.py` | Enumerates Docker containers with a `service` label that publishes `5678/tcp`. Prints `{host_port}|{service} | {name} {job} {task}` lines for VS Code's attach picker. |
| `loki-query` | `loki_query.py` | Run a LogQL query against the local Loki via `docker exec placeframe-loki-1 wget`, formatting each entry as `HH:MM:SS LEVEL [logGroup] message` (plus exception chain when present). Flags: `--limit`, `--direction`, `--since`, `--raw`. Use this instead of hand-rolling URL-encoded `wget` invocations — the URL encoding is fragile (`+`/`%7C`/quote-escapes) and easy to get subtly wrong. |
| `tune-reconstruction` | `tune_reconstruction.py` | Plackett-Burman sweep over `ReconstructionOptions` per capture. One reconstruction per cell. Aggregates map-quality metrics into a JSON report. |
| `fit-calibration` | `fit_calibration.py` | Algorithm 1: pick held-out frames, build/reuse reconstructions, localize each held-out frame, fit logistic+isotonic for tight/loose success probability, fit Σ_meas `(α, β)`, write `images/localizer/calibration/global.json`. |

`api_auth.py` (shared) and `held_out_selection.py` (consumed by `fit-calibration`) are library modules, not entry points.

### Layout

    scripts/
      preflight.py                              -- CI preflight sidecar (toolkit contract: exact path), python battery + repo checks
      pyproject.toml                            -- workspace member; declares entry points
      src/scripts/
        generate_datamodels.py                  -- sqlacodegen datamodel generation
        sqlacodegen_generator.py                -- custom sqlacodegen DeclarativeGenerator (enums, passive deletes, ARRAY binding)
        publish_compose.py                      -- CI compose-bundle publish per variant
        api_auth.py                             -- async auth: read .env, POST Keycloak, default-header inject
        forward_unity_android_debug_port.py     -- adb port forward for Unity debug
        list_debug_targets.py                   -- enumerate docker containers exposing :5678
        tune_reconstruction.py                  -- PB sweep over ReconstructionOptions
        fit_calibration.py                      -- Algorithm 1 calibration pipeline
        held_out_selection.py                   -- HeldOutFrameSelector Protocol + stride impl
      tests/
        test_fit_calibration.py
        test_publish_compose.py                 -- config inlining (_inline_configs)

### Calibration pipeline data flow

The pipeline orchestrates over backend IDs and writes/reads through the API. There is no sidecar JSON file and no parallel store; the `localization_evaluations` DB table is the corpus cache.

    Backend (PostgreSQL + SeaweedFS)

      capture_sessions ---- tar in S3 (frames.csv + images)
            |
            v
      reconstructions
            |
            +---- manifest (inline on read model)
            |       - options (incl. held_out_frame_timestamps)
            |       - metrics (incl. map quality, truth-alignment Procrustes residuals)
            |
            v
      localization_evaluations
            keyed by (reconstruction_id, frame_timestamp,
                      retrieval_top_k, ransac_threshold, pipeline_version)
            stores localizer outputs + err_t_m / err_r_deg / se3_residual / pnp_covariance

          ^                                          ^
          | write evaluations,                       | read corpus,
          | trigger reconstructions                  | fit, write images/localizer/
                                                     |   calibration/global.json

      scripts/tune_reconstruction.py        scripts/fit_calibration.py

        --captures <id>...                     --captures <id>...    or
                                               --reconstructions <id>...
        PB sweep over recon options            [--pipeline-version <sha>]
        (one recon per cell, no held-out       [--no-fit]
        frames, no calibration cache writes)
                                                 - pick held-out frames per capture
        Emits a tuning report (JSON).            - reuse-or-create recon w/ those options
                                                 - localize held-out frames;
                                                   cache to localization_evaluations
                                                 - read cache as corpus
                                                 - fit logistic + isotonic
                                                 - fit Sigma_meas (alpha, beta)
                                                 - write images/localizer/calibration/global.json

The two scripts share `api_auth.authenticated_api_client` and the `localization_evaluations`/`reconstructions` API surface, but no code path or intermediate file. `tune-reconstruction` does not write to the calibration cache; `fit-calibration` does not call the PB sweep machinery.

### `fit-calibration` modes

- `--captures <id>...`: full pipeline. Selects held-out frames per capture (default `StrideHeldOutSelector`, target 100), reuses a reconstruction whose full `ReconstructionOptions` blob (including `held_out_frame_timestamps`) matches what is requested — otherwise creates a new one and polls to completion (`RECONSTRUCTION_POLL_S = 5`, `RECONSTRUCTION_TIMEOUT_S = 1800`). Localizes each held-out frame against the resulting map, writes an evaluation row to `localization_evaluations`. Reads the cache, fits, writes the artifact.
- `--reconstructions <id>...`: skip the build step. Uses pre-built reconstructions whose `held_out_frame_timestamps` are already set. Localizes any held-out frames not already cached, then reads the cache as corpus. Cheap re-fit path.
- `--no-fit`: populate the cache without writing the artifact (e.g. for offline inspection of evaluation rows).

`--pipeline-version` is auto-detected from `api.get_localizer_version()` when omitted. The override remains for development workflows where the operator iterates uncommitted localizer changes and wants their cache rows clearly labeled (e.g. `dev-tylerh-2026-05-03`). The runtime loader hard-fails if the deployed localizer's SHA doesn't match the artifact's `pipeline_version`.

### Algorithm 1 (held-out fitting)

The procedure `fit-calibration` runs per capture (`fit_calibration.py` and the reconstructor working in concert):

1. **Hold out frames at map-build time.** `HeldOutFrameSelector` (default stride) picks ~100 timestamps from `frames.csv`. Those go into `ReconstructionOptions.held_out_frame_timestamps`; the reconstructor filters them out of `frames.csv` and skips the matching images. The COLMAP map is built from the remaining frames.
2. **Reconstructor aligns the map to truth.** The reconstructor pins the first registered frame's COLMAP pose to its `frames.csv` truth pose via single-anchor `Sim3d`; this places the rebuilt map in the capture's truth frame. Separately and only as a diagnostic, the reconstructor solves rigid (no-scale) Procrustes over all registered frames and emits per-capture residuals (`truth_alignment_rms_residual_m`, `truth_alignment_max_residual_m`); these ride the manifest and the operator (or the fit script) uses them to filter unreliable captures. The Procrustes transform itself is not applied to the reconstruction. See `images/reconstructor/AGENTS.md`.
3. **Per held-out frame.** Run the localizer; the map is already in truth-frame so the localizer's `camera_from_map` doubles as `camera_from_world`. Invert to get the estimated camera pose. Compute `err_t = ||truth_position - estimated_position||` and `err_r = || log(R_truth * R_estimated^-1) ||` (degrees, via `scipy.spatial.transform.Rotation.magnitude`). Record `(metrics, map_features, recon_config, loc_config, device, err_t, err_r, se3_residual, pnp_covariance)` to `localization_evaluations`.
4. **Pool across all captures and configs**, add binary labels: `success_tight = err_t < 5cm AND err_r < 1deg`, `success_loose = err_t < 30cm AND err_r < 5deg`.
5. **Fit logistic regression** (`LogisticRegression(class_weight='balanced')`) on the 9-feature vector (`log(num_inliers+1)`, `inlier_ratio`, `reproj_err / image_diagonal_pixels`, `inlier_coverage`, `log(num_matches+1)`, `log(map_image_count+1)`, `log(map_point_count+1)`, `map_avg_track_length`, `map_viewpoint_diversity`).
6. **Fit isotonic** (`IsotonicRegression(out_of_bounds='clip')`) on the logistic output against the same labels.
7. **Fit Σ_meas scaling.** For each held-out localization, compute SE(3) residual `e = log(P_truth_in_map * P_estimated^-1) ∈ R^6`. Solve scalar `α, β` that maximize `sum_i log N(e_i; 0, alpha * PnP_cov_i + beta * I)` via `scipy.optimize.minimize(L-BFGS-B)`. The scalars carry the empirical "actual pose-error spread relative to PnP_cov" signal that PnP_cov alone misses.
8. **Optional 10% holdout** for Brier score and reliability diagram in fit metadata.

Output: `CalibrationArtifact(tight, loose, sigma_meas_alpha, sigma_meas_beta, loose_min, tight_min, ...)` written to `images/localizer/calibration/global.json` by default. Schema: `packages/python/core/AGENTS.md` "Calibration".

### Driver-side localization

`fit_calibration` fetches each held-out frame image via `GET /capture_sessions/{id}/images/{frame_timestamp}`, POSTs it to the existing localizer `/localize` endpoint, computes truth-error labels driver-side, and POSTs the evaluation row to `/reconstructions/{id}/localization-evaluations`. The localizer stays a pure function with no awareness of `localization_evaluations`. The capture data path is via three API endpoints — `GET /capture_sessions/{id}/manifest.json`, `GET /capture_sessions/{id}/frames.csv`, `GET /capture_sessions/{id}/images/{frame_timestamp}` — not direct S3 access; the API is the single read path.

The alternative — a server-side `POST /reconstructions/{id}/evaluate-frame` that would do fetch+localize+persist server-side — was rejected because it would couple the localizer to S3/captures and to the evaluations table for a workflow that's purely orchestration.

### Reconstruction reuse contract

`match_or_create_reconstruction(api, capture_id, requested_options)` lists candidates via `GET /capture_sessions/{id}/reconstructions`, fetches each, filters to `status == SUCCEEDED`, and reuses iff `ReconstructionOptions.model_validate(reconstruction.manifest["options"]) == requested_options` (Pydantic equality on the full blob, including `held_out_frame_timestamps`). `requested_options` is constructed from `ReconstructionOptions(held_out_frame_timestamps=selected_timestamps)` — server defaults for every other knob.

If no match, the function creates a new reconstruction with those exact options and polls `GET /reconstructions/{id}` every 5 s, with a 1800 s timeout. Raises on `FAILED` or `CANCELLED`.

The full-blob match is the strictest possible. Anything looser admits silent contamination of the corpus by reconstructions built with different options.

### Held-out selector registry

`HeldOutFrameSelector` is a Protocol; `_REGISTRY: dict[str, HeldOutFrameSelector]` exposes names to `fit_calibration`'s `--held-out-selector` flag. Adding a new strategy means a new class implementing the Protocol and a registry entry — `fit_calibration.py`'s orchestration loop and the `localization_evaluations` contract are unaffected. Today's only implementation is `StrideHeldOutSelector`:

    stride = max(1, len(timestamps) // target_count)
    selected = timestamps[stride // 2 :: stride]

Deterministic, scales to capture length, gives even temporal spacing → roughly even spatial spacing on smooth capture paths.

## Constraints

**One CLI package.** `scripts/` is the repo's single Python CLI package — the former `build-scripts` member under `build/` was dissolved into it (the split's dependency-surface rationale was void: one shared workspace venv, and the python battery syncs `--all-packages`, so both cohorts were always installed together anyway). The codegen/CI cohort keeps its heavier declared deps (`sqlacodegen`, `sqlalchemy`, `psycopg`, `datamodel-code-generator`) in this package's `pyproject.toml`, with deptry DEP002 ignores for the non-imported ones (`psycopg` loads as the SQLAlchemy DSN driver, `datamodel-code-generator` is invoked as a CLI by `generate-datamodels`). `scripts/preflight.py` stays at the directory root by toolkit contract: github-actions-toolkit's preflight reusable invokes it by that exact path.

**Pipeline orchestration over backend IDs, no sidecar store.** `fit-calibration` and `tune-reconstruction` both treat the API as the single source of truth: capture sessions, reconstructions, and evaluations are all addressed by UUID and read/written through generated API methods. No intermediate JSON files, no local SQLite, no harness-side tar shuffling. The corpus *is* the `localization_evaluations` table; the cache key is `(reconstruction_id, frame_timestamp, retrieval_top_k, ransac_threshold, pipeline_version)`.

**Auto-detect `pipeline_version` from the live localizer.** The `localization_evaluations` cache key is keyed on `pipeline_version`. If the operator mistypes the SHA, evaluation rows pool silently across incompatible pipeline runs and the fit is contaminated without warning. Pulling the value from `api.get_localizer_version()` makes that footgun unreachable. The override path remains for dev workflows where the operator iterates uncommitted changes and wants their cache rows labeled distinctly (e.g. `dev-tylerh-2026-05-03`). The runtime loader hard-fails on `pipeline_version` mismatch — the artifact is non-portable across localizer SHAs by design.

**Driver-side localization, not server-side.** A `POST /reconstructions/{id}/evaluate-frame` that did fetch+localize+persist server-side was considered and rejected. The localizer is a pure function from `(image, map_ids, camera_config)` to a pose+metrics response; adding a path that reaches into S3 and writes to the evaluations table would couple it to capture sessions, to the evaluations DB schema, and to the orchestration workflow's lifecycle. Keeping that orchestration in the driver script means the localizer stays cache-unaware and the script absorbs the per-frame retry / cache-skip / truth-comparison logic that has nothing to do with localization.

**Reconstruction reuse keys on the full options blob.** Calibrations are fit against one pipeline configuration. Mixing reconstructions built with different options (different RANSAC thresholds, different bundle-adjustment settings, different held-out sets) into one corpus contaminates the fit. The full-blob Pydantic-equality check is the strictest possible reuse predicate — looser checks admit silent contamination, and `tune_reconstruction.py` already covers the "exhaustive options sweep" use-case where reuse is undesired.

**`StrideHeldOutSelector` as the starter.** Deterministic (same `frames.csv` + `target_count` → same selection), scales to capture length, and gives roughly even spatial coverage on smooth capture paths (a continuous-walk operator's temporal stride approximates a spatial stride). Cheaper than computing positions from the CSV and voxel-binning. The Protocol registry exists so smarter strategies (post-build filter, spatial voxel-bin, hybrid) can be added without touching the orchestration loop.

**Single shared auth helper.** `api_auth.authenticated_api_client()` is an async context manager that reads `PUBLIC_DOMAIN` from `.env`, fetches a Keycloak token, and yields a `DefaultApi`. Both `fit_calibration` and `tune_reconstruction` use it. The token is injected as a default header rather than via `Configuration(access_token=...)` because the openapi-generator output emits empty `_auth_settings` on every method — the documented `access_token` kwarg has no effect end-to-end. This is a generator-config gap (every consumer of `placeframe_api_client` has the same blind spot), worked around locally because fixing the generator config is out of scope for this directory.

## See also

- [`docker-devkit`](https://github.com/outernet-foundation/docker-devkit) — the standalone package holding the Docker-stack lifecycle (`up`, `down`, `build`) and the SHA/auth helpers, a PyPI dependency of this package (`docker-devkit>=0.4`). `scripts/` imports from it (`docker_devkit.modes.parse_env_file` in `api_auth.py`); the inverse does not hold.
- [`unity-devkit`'s `AGENTS.md`](https://github.com/outernet-foundation/unity-devkit/blob/main/AGENTS.md) — the standalone Unity build toolkit, which also hosts the `install` command. `scripts/` no longer imports from it; the dependency was dropped when `install.py` moved.
- `images/localizer/AGENTS.md` — defines the `/version` and `/localize` endpoints that `fit-calibration` consumes and the `pipeline_version` baked into the localizer image.
- `images/reconstructor/AGENTS.md` — defines the single-anchor truth-frame alignment and the Procrustes-residual diagnostic metrics that Algorithm 1 step 2 relies on.
- `packages/python/core/AGENTS.md` "Calibration" — schema of `CalibrationArtifact`, `Features`, `ToleranceModel`, `RawMapMetrics`, `RawLocalizationMetrics`.
