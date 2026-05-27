# scripts/SPEC.md

## What this is

`scripts/` is a Python workspace member that ships a set of operator-facing CLIs registered as `uv run` commands in `pyproject.toml`'s `[project.scripts]`. The package contains two cohorts: small operational utilities (Unity adb-forward, Docker debug-target listing, GitHub-Actions artifact install, ZED Box SSH deploy) and the calibration pipeline (`fit-calibration`, `tune-reconstruction`, the held-out selector registry, the shared auth helper). The Docker-stack lifecycle commands (`up`, `down`, `build`, `migrate-database`, `generate-clients`, `generate-datamodels`, `lock-python`, `deptry-check`, `preflight`) do not live here — they live in the sibling `build-scripts` package under `build/`. The calibration pipeline is the load-bearing part of this directory and the only piece with tests; the operational utilities are small self-contained shell-out scripts.

## Shape

### Entry points

Registered in `scripts/pyproject.toml`:

| `uv run` command | Module | What it does |
|---|---|---|
| `forward-unity-android-debug-port` | `forward_unity_android_debug_port.py` | Auto-detects the single adb device, finds the listening Unity debugger port in 56000–56999 via `/proc/net/tcp{,6}`, and `adb forward tcp:56000 tcp:{found}`. |
| `list-debug-targets` | `list_debug_targets.py` | Enumerates Docker containers with a `service` label that publishes `5678/tcp`. Prints `{host_port}|{service} | {name} {job} {task}` lines for VS Code's attach picker. |
| `install` | `install.py` | Downloads the latest GitHub Actions Unity build artifact for `(project, target)` on the current branch (overridable), caches it under `~/.placeframe/builds/{run_id}/`, and `adb install`s the APK or `bash_handoff`s the linux64 executable. |
| `install-zed` | `install_zed.py` | End-to-end SSH deploy of the `zed-capture` container onto a Jetson over the box's wired-ethernet link: SSH bootstrap, Docker install, NVIDIA runtime, disable of NVIDIA's USB device-mode service (frees the USB-C port for AOA host duty), image acquisition (ghcr pull or local cross-compile + `docker save \| ssh docker load`), compose+systemd unit install, `docker compose up`. |
| `loki-query` | `loki_query.py` | Run a LogQL query against the local Loki via `docker exec placeframe-loki-1 wget`, formatting each entry as `HH:MM:SS LEVEL [logGroup] message` (plus exception chain when present). Flags: `--limit`, `--direction`, `--since`, `--raw`. Use this instead of hand-rolling URL-encoded `wget` invocations — the URL encoding is fragile (`+`/`%7C`/quote-escapes) and easy to get subtly wrong. |
| `tune-reconstruction` | `tune_reconstruction.py` | Plackett-Burman sweep over `ReconstructionOptions` per capture. One reconstruction per cell. Aggregates map-quality metrics into a JSON report. |
| `fit-calibration` | `fit_calibration.py` | Algorithm 1: pick held-out frames, build/reuse reconstructions, localize each held-out frame, fit logistic+isotonic for tight/loose success probability, fit Σ_meas `(α, β)`, write `config/calibration/global.json`. |

`api_auth.py` (shared) and `held_out_selection.py` (consumed by `fit-calibration`) are library modules, not entry points.

### Layout

    scripts/
      pyproject.toml                              -- workspace member; declares entry points
      src/scripts/
        api_auth.py                               -- async auth: read .env, POST Keycloak, default-header inject
        forward_unity_android_debug_port.py       -- adb port forward for Unity debug
        list_debug_targets.py                     -- enumerate docker containers exposing :5678
        install.py                                -- download + install Unity CI artifact
        install_zed.py                            -- SSH deploy ZED Box
        tune_reconstruction.py                    -- PB sweep over ReconstructionOptions
        fit_calibration.py                        -- Algorithm 1 calibration pipeline
        held_out_selection.py                     -- HeldOutFrameSelector Protocol + stride impl
      tests/
        test_fit_calibration.py                   -- the only test file in the directory

### Calibration pipeline data flow

The pipeline orchestrates over backend IDs and writes/reads through the API. There is no sidecar JSON file and no parallel store; the `localization_evaluations` DB table is the corpus cache.

    Backend (PostgreSQL + MinIO)

      capture_sessions ---- tar in MinIO (frames.csv + images)
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
          | trigger reconstructions                  | fit, write global.json

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
                                                 - write config/calibration/global.json

The two scripts share `api_auth.authenticated_api_client` and the `localization_evaluations`/`reconstructions` API surface, but no code path or intermediate file. `tune-reconstruction` does not write to the calibration cache; `fit-calibration` does not call the PB sweep machinery.

### `fit-calibration` modes

- `--captures <id>...`: full pipeline. Selects held-out frames per capture (default `StrideHeldOutSelector`, target 100), reuses a reconstruction whose full `ReconstructionOptions` blob (including `held_out_frame_timestamps`) matches what is requested — otherwise creates a new one and polls to completion (`RECONSTRUCTION_POLL_S = 5`, `RECONSTRUCTION_TIMEOUT_S = 1800`). Localizes each held-out frame against the resulting map, writes an evaluation row to `localization_evaluations`. Reads the cache, fits, writes the artifact.
- `--reconstructions <id>...`: skip the build step. Uses pre-built reconstructions whose `held_out_frame_timestamps` are already set. Localizes any held-out frames not already cached, then reads the cache as corpus. Cheap re-fit path.
- `--no-fit`: populate the cache without writing the artifact (e.g. for offline inspection of evaluation rows).

`--pipeline-version` is auto-detected from `api.get_localizer_version()` when omitted. The override remains for development workflows where the operator iterates uncommitted localizer changes and wants their cache rows clearly labeled (e.g. `dev-tylerh-2026-05-03`). The runtime loader hard-fails if the deployed localizer's SHA doesn't match the artifact's `pipeline_version`.

### Algorithm 1 (held-out fitting)

The procedure `fit-calibration` runs per capture (`fit_calibration.py` and the reconstructor working in concert):

1. **Hold out frames at map-build time.** `HeldOutFrameSelector` (default stride) picks ~100 timestamps from `frames.csv`. Those go into `ReconstructionOptions.held_out_frame_timestamps`; the reconstructor filters them out of `frames.csv` and skips the matching images. The COLMAP map is built from the remaining frames.
2. **Reconstructor aligns the map to truth.** The reconstructor pins the first registered frame's COLMAP pose to its `frames.csv` truth pose via single-anchor `Sim3d`; this places the rebuilt map in the capture's truth frame. Separately and only as a diagnostic, the reconstructor solves rigid (no-scale) Procrustes over all registered frames and emits per-capture residuals (`truth_alignment_rms_residual_m`, `truth_alignment_max_residual_m`); these ride the manifest and the operator (or the fit script) uses them to filter unreliable captures. The Procrustes transform itself is not applied to the reconstruction. See `docker/reconstructor/SPEC.md`.
3. **Per held-out frame.** Run the localizer; the map is already in truth-frame so the localizer's `camera_from_map` doubles as `camera_from_world`. Invert to get the estimated camera pose. Compute `err_t = ||truth_position - estimated_position||` and `err_r = || log(R_truth * R_estimated^-1) ||` (degrees, via `scipy.spatial.transform.Rotation.magnitude`). Record `(metrics, map_features, recon_config, loc_config, device, err_t, err_r, se3_residual, pnp_covariance)` to `localization_evaluations`.
4. **Pool across all captures and configs**, add binary labels: `success_tight = err_t < 5cm AND err_r < 1deg`, `success_loose = err_t < 30cm AND err_r < 5deg`.
5. **Fit logistic regression** (`LogisticRegression(class_weight='balanced')`) on the 11-feature vector (`log(num_inliers+1)`, `inlier_ratio`, `reproj_err / image_diagonal_pixels`, `inlier_coverage`, `log(num_matches+1)`, `log(map_image_count+1)`, `log(map_point_count+1)`, `map_avg_track_length`, `log(map_bounding_volume_m3+1)`, `map_viewpoint_diversity`, `is_indoor`).
6. **Fit isotonic** (`IsotonicRegression(out_of_bounds='clip')`) on the logistic output against the same labels.
7. **Fit Σ_meas scaling.** For each held-out localization, compute SE(3) residual `e = log(P_truth_in_map * P_estimated^-1) ∈ R^6`. Solve scalar `α, β` that maximize `sum_i log N(e_i; 0, alpha * PnP_cov_i + beta * I)` via `scipy.optimize.minimize(L-BFGS-B)`. The scalars carry the empirical "actual pose-error spread relative to PnP_cov" signal that PnP_cov alone misses.
8. **Optional 10% holdout** for Brier score and reliability diagram in fit metadata.

Output: `CalibrationArtifact(tight, loose, sigma_meas_alpha, sigma_meas_beta, loose_min, tight_min, ...)` written to `config/calibration/global.json` by default. Schema: `packages/python/core/SPEC.md` "Calibration".

### Driver-side localization

`fit_calibration` fetches each held-out frame image via `GET /capture_sessions/{id}/images/{frame_timestamp}`, POSTs it to the existing localizer `/localize` endpoint, computes truth-error labels driver-side, and POSTs the evaluation row to `/reconstructions/{id}/localization-evaluations`. The localizer stays a pure function with no awareness of `localization_evaluations`. The capture data path is via three API endpoints — `GET /capture_sessions/{id}/manifest.json`, `GET /capture_sessions/{id}/frames.csv`, `GET /capture_sessions/{id}/images/{frame_timestamp}` — not direct MinIO access; the API is the single read path.

The alternative — a server-side `POST /reconstructions/{id}/evaluate-frame` that would do fetch+localize+persist server-side — was rejected because it would couple the localizer to MinIO/captures and to the evaluations table for a workflow that's purely orchestration.

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

**Two packages for "Python scripts registered as `uv run` commands."** `scripts/` and `build/` (the `build-scripts` package) both ship `[project.scripts]` entries. The split is by topic, not by mechanism: `build-scripts` orchestrates the Docker stack lifecycle and the code-generation pipeline (lives next to `compose.*.yml` and `openapi-generator/` it operates on); `scripts/` is everything else (operator/dev utilities and the calibration pipeline). `scripts/` imports from `build-scripts`, not vice versa. The rationale is one of co-location: the lifecycle commands live next to the configs they read; the operator-CLI bucket lives separately so its dependency surface (numpy/scipy/sklearn/pytransform3d for fit-calibration, plus typer/httpx for the utilities) does not bleed into the lighter codegen-and-compose tooling.

**Pipeline orchestration over backend IDs, no sidecar store.** `fit-calibration` and `tune-reconstruction` both treat the API as the single source of truth: capture sessions, reconstructions, and evaluations are all addressed by UUID and read/written through generated API methods. No intermediate JSON files, no local SQLite, no harness-side tar shuffling. The corpus *is* the `localization_evaluations` table; the cache key is `(reconstruction_id, frame_timestamp, retrieval_top_k, ransac_threshold, pipeline_version)`.

**Auto-detect `pipeline_version` from the live localizer.** The `localization_evaluations` cache key is keyed on `pipeline_version`. If the operator mistypes the SHA, evaluation rows pool silently across incompatible pipeline runs and the fit is contaminated without warning. Pulling the value from `api.get_localizer_version()` makes that footgun unreachable. The override path remains for dev workflows where the operator iterates uncommitted changes and wants their cache rows labeled distinctly (e.g. `dev-tylerh-2026-05-03`). The runtime loader hard-fails on `pipeline_version` mismatch — the artifact is non-portable across localizer SHAs by design.

**Driver-side localization, not server-side.** A `POST /reconstructions/{id}/evaluate-frame` that did fetch+localize+persist server-side was considered and rejected. The localizer is a pure function from `(image, map_ids, camera_config)` to a pose+metrics response; adding a path that reaches into MinIO and writes to the evaluations table would couple it to capture sessions, to the evaluations DB schema, and to the orchestration workflow's lifecycle. Keeping that orchestration in the driver script means the localizer stays cache-unaware and the script absorbs the per-frame retry / cache-skip / truth-comparison logic that has nothing to do with localization.

**Reconstruction reuse keys on the full options blob.** Calibrations are fit against one pipeline configuration. Mixing reconstructions built with different options (different RANSAC thresholds, different bundle-adjustment settings, different held-out sets) into one corpus contaminates the fit. The full-blob Pydantic-equality check is the strictest possible reuse predicate — looser checks admit silent contamination, and `tune_reconstruction.py` already covers the "exhaustive options sweep" use-case where reuse is undesired.

**`StrideHeldOutSelector` as the starter.** Deterministic (same `frames.csv` + `target_count` → same selection), scales to capture length, and gives roughly even spatial coverage on smooth capture paths (a continuous-walk operator's temporal stride approximates a spatial stride). Cheaper than computing positions from the CSV and voxel-binning. The Protocol registry exists so smarter strategies (post-build filter, spatial voxel-bin, hybrid) can be added without touching the orchestration loop.

**Single shared auth helper.** `api_auth.authenticated_api_client()` is an async context manager that reads `PUBLIC_DOMAIN` from `.env`, fetches a Keycloak token, and yields a `DefaultApi`. Both `fit_calibration` and `tune_reconstruction` use it. The token is injected as a default header rather than via `Configuration(access_token=...)` because the openapi-generator output emits empty `_auth_settings` on every method — the documented `access_token` kwarg has no effect end-to-end. This is a generator-config gap (every consumer of `placeframe_api_client` has the same blind spot), worked around locally because fixing the generator config is out of scope for this directory.

**`install-zed` disables L4T's USB device-mode service.** NVIDIA's stock `nv-l4t-usb-device-mode.service` pins the USB-C port as a peripheral (CDC ethernet gadget + mass-storage); the AOA host-mode link needs the port available for host duty. `install-zed` `systemctl disable --now`s the unit on every run (idempotent, no-op once disabled). The connectivity model is otherwise pure wired ethernet: SSH targets the box's RJ-45 address at `user@100.64.0.1` with the host's cable-side end at `100.64.0.2`. Image pulls go directly to ghcr.io from the box. The `--build` path replaces ghcr with a transient Docker registry on the host (`docker run -d -p 5000:5000 registry@sha256:...`): `docker buildx bake --push` cross-compiles `zed-capture` + `aoa-bridge` for ARM64 and pushes to it, then the box pulls from `100.64.0.2:5000`. `100.64.0.2:5000` is added to the box-side `/etc/docker/daemon.json` `insecure-registries` so the box's daemon accepts the plain-HTTP pull. Pulls are layer-aware, so iterative dev only ships changed layers across the cable.

**The box subnet sits in RFC 6598, not RFC1918.** `100.64.0.0/24` is inside RFC 6598 Shared Address Space (`100.64.0.0/10`, the same range Tailscale uses for its overlay). The rationale is that COI-sandboxed agent containers on the host enforce a default-deny on RFC1918 destinations: a box on `10.0.0.1` is unreachable from inside a sandbox slot. Putting the box outside RFC1918 lets sandbox traffic reach it via the sandbox's `0.0.0.0/0` allow rule, without weakening LAN isolation.

**`install-zed` owns the host-side networking the box depends on.** Beyond box-side configuration, the script also (a) creates or updates the host's `zedbox` NetworkManager connection at `100.64.0.2/24` on an auto-detected unused wired interface, before the SSH probe so a fresh host bootstraps in one invocation; (b) writes `/etc/sysctl.d/99-zedbox.conf` to enable `net.ipv4.ip_forward=1` persistently (without relying on Docker as a side-effect); (c) adds `100.64.0.0/24` to firewalld's trusted zone and enables masquerade on the public zone, so the box can reach the public internet through the host. A fresh-Ubuntu host with no other tooling can run `install-zed` and get a fully working box→internet path.

**`install-zed` uses an SSH control-master multiplexer.** A single TCP connection is established once and reused for every subsequent SSH/scp invocation (`-o ControlMaster=auto -o ControlPath=/tmp/install-zed-ssh-%C -o ControlPersist=120`). Without this, each of the ~20 SSH calls in the deploy would pay the TCP+TLS handshake cost; with it, the deploy completes in roughly one round-trip per command. The control socket is torn down at exit via `stack.callback`.

## See also

- `build/` (the `build-scripts` workspace package) — sibling Python CLI package holding the Docker-stack lifecycle and codegen entry points (`up`, `down`, `build`, `migrate-database`, `generate-clients`, `generate-datamodels`, `lock-python`, `deptry-check`, `preflight`). `scripts/` imports from it (`build_scripts.placeframe.projects.load_unity_projects` in `install.py`; `build_scripts.placeframe.context_sha.compute_service_shas` in `install_zed.py`); the inverse does not hold.
- `docker/localizer/SPEC.md` — defines the `/version` and `/localize` endpoints that `fit-calibration` consumes and the `pipeline_version` baked into the localizer image.
- `docker/reconstructor/SPEC.md` — defines the single-anchor truth-frame alignment and the Procrustes-residual diagnostic metrics that Algorithm 1 step 2 relies on.
- `packages/python/core/SPEC.md` "Calibration" — schema of `CalibrationArtifact`, `Features`, `ToleranceModel`, `RawMapMetrics`, `RawLocalizationMetrics`.
- `docker/aoa-bridge/CLAUDE.md` — AOA-bridge protocol, USB host/accessory roles, and the phone-side counterpart files that the on-box `aoa_bridge.py` handshake binds against.
