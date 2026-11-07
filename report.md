# dev_hh Disposition: Inventory, Decisions, and Plan of Attack

Scope: the 92 commits by `how-huang-sfai` (Howard) between `dev` (`13c62b54`, 2026-08-24) and
`dev_hh` HEAD (`210b17aa`, 2026-11-06). Everything below is attributable to Howard unless stated
otherwise. This document is a primer (§0–§1) and decision record (§2–§3) for the dev_hh
disposition; §5 is a phase skeleton to be elaborated into the executable plan by a later
session, not the plan itself.

## 0. Topology and strategy (primer)

`dev_hh` is **not** 343 commits of contractor work. It is `dev` plus exactly 92 commits, all by
Howard:

```
main ── ... ── 61c2822e (PR #117)
                \
                 dev ── ... ── 13c62b54 ────────── dev has moved on with Tyler/Joshua/Elliot work
                                   \
                                    + 92 commits (how-huang-sfai) ── dev_hh HEAD 210b17aa
```

`git diff main...dev_hh` shows 343 commits / ~650k deleted lines, but 251 of those commits and all
of the `legacy/` + `apps/` deletions are Tyler's work already sitting on `dev`, awaiting merge to
`main`. The correct Howard diff is `git diff dev...dev_hh`: **~15k insertions across five areas,
plus regenerated clients**. Any merge review of `dev_hh` must separate Howard's 92 from the `dev`
backlog — merging `dev_hh` pulls in both.

**Integration is a port, not a merge.** Since Howard branched (2026-08-24, merge-base `13c62b54`),
`dev`'s tip has restructured the services tree: `docker/` is now `workloads/` (the reconstructor
lives at `workloads/reconstructor/…`), `build/` no longer exists, and a `stack/` tree plus SeaweedFS
have appeared. Howard's 92 commits all touch the old paths. Landing any of his service changes on
current `dev` means re-implementing them against the restructured tree, not cherry-picking; every
path reference in §1.5 and §4 below is a pre-restructure (`docker/…`) path.

**The restructure also splits Howard's Unity work across two repos.** `packages/unity/Placeframe`
still exists on `dev`, so the package-side changes (LocalizationRecorder.cs, RelocalizationFilter
gate fix, VisualPositioningSystem/ICameraProvider/CameraProvider/CaptureManager) land here. But
`apps/` and `zed/` no longer exist in this repo at all — the CaptureTool app and the zed actor now
live in the **placeframe-capture-tool** repo — so Howard's `apps/CaptureTool/*` changes
(LocalizationManager recorder wiring, the Validate-tab record button in AppUI, `AppState.recording`,
CaptureController's published-map preference fix) must be re-landed *there*, not here. The core
Python package was also renamed on `dev` (`core` → `placeframe_core`), which every ported import
must absorb.

**dev_hh is a quarry, not a branch.** Nothing merges or rebases wholesale: the 92 commits are
disassembled into four destinations — placeframe `dev` (server capabilities, generic lens/rig
capabilities, Unity recorder), placeframe-capture-tool (app wiring), a long-lived research branch
(fusion program, server-side spherical pipeline), and the future dashboard repo (frontend, client
spherical) — after which dev_hh is archived. Howard's tooling talks to the stack over HTTP, so the
seam that keeps him working is a dev-built stack, not a rebased branch: once the §4.1 ports land
on `dev`, his un-rebased checkout keeps running against a current stack until the extraction
replaces it.

## 1. Inventory: what he built (primer)

Five clusters. Line counts are hand-written source, excluding generated code.

### 1.1 The dashboard UI (`dashboard/`)

A single-page web app: Vite + React + TypeScript + three.js frontend (~7.9k lines incl. CSS), and a
"backend" that is a thin HTTP shell around the `howard-test` CLI.

- **`dashboard/frontend/`** — one page (`CapturesPage.tsx`, 1190 lines): a tree of captures →
  reconstructions → localization runs, with actions on every row (reconstruct, visualize, localize,
  publish/unpublish map, delete, rename, import, export zip/poses/views, cancel). Major components:
  - `viewer/PointCloudScene.ts` (1091) + `ViewerPage.tsx` — a CloudCompare-style three.js
    point-cloud viewer (orbit/pan/dolly, camera frustums/arrows/trajectory, frame labels, ortho +
    perspective projection, measure overlay/scale, multi-map overlay layers, localized-pose overlay).
  - `align/AlignPage.tsx` (551) — coarse by-eye placement of several maps, ICP refinement, merged
    capture creation.
  - `FusionPlayer.tsx`, `RunCharts.tsx`, `FrameDetailsDialog.tsx`, `DetailsDialog.tsx`,
    `ReconstructionFrames.tsx`, `RunResults.tsx`, `DirectoryBrowserDialog.tsx`, `ActionDialogs.tsx`.
- **`dashboard/backend/app.py`** (1692 lines) — a standalone Litestar app (own `uv` project and
  venv, deliberately **not** a member of the placeframe workspace), ~50 routes. Every action shells
  out to `uv run howard-test <cmd> --json` with cwd pinned to the placeframe repo root; listings of
  localizations/alignments/poseless-sets/fusion-runs read `placeframe/data/` JSON files directly;
  in-memory fire-and-poll job registry; no authentication (localhost tool).
- `dashboard/run.sh` — starts both dev servers (8010 backend, 5174 frontend).
- `dashboard/project.md` — Howard's own detailed design log. Read it; it is accurate.

### 1.2 The CLI layer: `howard-test` (`scripts/`)

The dashboard's real backend. `scripts/src/scripts/howard_test.py` is **4,482 lines, ~40 typer
commands, 170 functions** — captures/reconstructions listing, upload, reconstruct (incl. cancel,
poll, cache), poseless-folder reconstruction (fabricates a synthetic straight-line trajectory to
satisfy the priors schema, then neutralizes it with `pose_prior_position_sigma_m=1000`), import
(capture/reconstruction tars, .insv spherical video), export (zip, poses, views), transform-reconstruction
(Sim(3) copy for map overlays), merge-aligned, publish/unpublish map, delete/rename, visualize
(matplotlib PNG), `points` (binary protocol to stdout for the viewer), localize (per-image loop
writing `data/localizations/<run_id>/results.json` + `progress.json`), reconstruction-frames /
frame-detail / map-images (the Localization Details view), offline-fusion, imu-scale, icp-align.

Helper modules: `icp_align.py` (318 — trimmed ICP refinement of a coarse map placement),
`imu_scale.py` (418 — metric scale for an up-to-scale spherical reconstruction from the .insv's own
IMU, ORB-SLAM3-style inertial init), `offline_fusion.py` (582 — replay a recorded localization run
through the ported Kalman filter and render frames for the FusionPlayer). Plus `api_auth.py`
extension (`PLACEFRAME_API_URL` local short-circuit past the ngrok relay), `scripts/pyproject.toml`
entry point + deps, and five new test files (`test_direct_store`, `test_icp_align`,
`test_poseless_keyframes`, `test_spherical_cache`, `test_spherical_defaults`).

**Critically, the CLI also reaches around the API**: oversized captures/reconstructions (>1 GB
body limit) are stored by `docker exec placeframe-minio-logger-1 mc pipe` directly into MinIO
buckets, then the row is created bodyless via `POST /capture_sessions/bulk`. Dev-stack-only by
construction.

### 1.3 Spherical capture support

End-to-end support for 360° cameras (Insta360 .insv). The *capture tar* holds raw equirectangular
frames plus a manifest declaring `projection: EQUIRECTANGULAR` — a well-formed tar placeframe
can't distinguish by origin — and all view derivation happens at reconstruction time:

- `packages/python/panorama/` — new workspace package (1,185 src + 446 test lines): .insv container
  parsing (two-lens video tracks, IMU + frame-time records), equirect→fisheye view projection with
  four layouts (tetrahedron/cube/hexring/dodecahedron), video frame sampling. **Zero placeframe
  dependencies** (numpy only; `av`/opencv behind a `video` extra).
- `packages/python/core/` — `SphericalCameraConfig` + `CameraConfig` union in the capture manifest
  schema; four new `ReconstructionOptions` (`spherical_layout`, `spherical_view_fov_deg`,
  `spherical_view_size`, `spherical_sequential_views`) plus `cross_rig_pair_distance_m`.
- `docker/reconstructor/` — `SphericalExpansion` in `rig.py` (a spherical camera becomes N rendered
  fisheye views), `spherical.py` (renders kept keyframes' views after keyframe selection), view
  pairing in `pairs.py`, no-intrinsic-refinement in `options_builder.py` (rendered views have exact
  intrinsics; refining them collapsed dodecahedron models via COLMAP's bogus-camera filter), new
  tests (5 files, ~770 lines).
- Import flows in the CLI (`import-spherical --insv-width`, `reconstruct-spherical`, `inspect-video`,
  `export-views`), spherical-cache flag on captures.
- Research precursors: `pano_mapping/` (507 lines, standalone scripts) and
  `scripts/experiments/` (projection_ab, retrieval_ab).

### 1.4 VIO/VPS fusion research program

- **Unity**: `LocalizationRecorder.cs` (307 lines, in the Placeframe package) records a validation
  run — every camera frame as video, full-res stills at 4 Hz, tracker poses at 30 Hz, live VPS
  requests/results — to a tar; wired into CaptureTool's Validate tab with a record button and
  into `VisualPositioningSystem`/`ICameraProvider`.
- **`fusion-test/`** (2,211 lines) — self-contained offline replay harness (numpy/scipy/matplotlib
  only; only `export.py` touches placeframe): schedule simulation (device 1 Hz + latency + drops),
  three fusion algorithms (a faithful port of `RelocalizationFilter.cs`, snap, sliding-window),
  metrics (registration px, error-vs-reference, smoothness), parameter sweeps, a matplotlib
  frame-by-frame player.
- **Calibration schema v3** — `CalibrationArtifact` gained separate rotation/translation variance
  floors (`sigma_meas_beta_rotation/translation`, was one beta); `fit_calibration.py` and the
  placeholder `global.json` updated with empirically-derived floors (0.3° / 20 cm) that fix the
  innovation gate rejecting good fixes. `RelocalizationFilter.cs` fix keeping the innovation gate
  meaningful under `BypassKalman`.
- `howard-test offline-fusion` + the dashboard's FusionPlayer/RunCharts consume recordings too.
- `artifacts/vps-fusion.html` (694 lines) — a tracked walkthrough artifact (.gitignore adjusted to
  track exactly this one file).

### 1.5 Service changes inside placeframe proper

Destinations in §3. Summary by service (`dev...dev_hh`, excluding codegen):

| Area | Files | Delta | Substance |
|---|---|---|---|
| `docker/api` | 3 routers | +124 | cancel route; localize `use_chunking`/`detail` params + 422 reason/`extra` forwarding; capture-delete tar cleanup + 409 guard; expanded-captures deterministic newest-first order; import-tar attaches to existing capture |
| `docker/lease-server` | leases.py | +15 | progress/finalize writes for a cancelled row answered with 409 |
| `docker/localizer` | 5 src | +500 | new `build_detail.py` (opt-in per-pair diagnostics); `LocalizationFailure` payloads; `use_chunking` batch flag; per-request `cuda.empty_cache()` |
| `docker/reconstructor` | 12 src | +900 | cancellation plumbing; `batching.py` keypoint-budget batch sizing; spherical pipeline; cross-rig pairing; no-refine rendered views |
| `packages/python/core` | 6 | +180 | spherical schema; `localization_detail.py`; lightglue host-staged tensors (GPU fix); calibration v3 |
| `packages/python/common` | 2 | +31 | `limits.py` (`REQUEST_MAX_BODY_SIZE` shared constant); `extra` passthrough in error handler |
| `packages/unity` + `apps/CaptureTool` | 11 | +544 | LocalizationRecorder + wiring; RelocalizationFilter gate fix; CaptureTool prefers published-map reconstruction |
| `packages/generated` | 51 | +4,309 | codegen (incl. `generate_datamodels.py` fix marking bigint columns int64 so generated clients don't parse them as 32-bit) |
| root | pyproject/.gitignore/.env.sample/compose.gpu | — | panorama workspace member; `/data/` ignore; `PLACEFRAME_API_URL` docs; `LIGHTGLUE_BATCH_SIZE` passthrough |

### 1.6 How the pieces couple today

```
Browser ── HTTP ── dashboard/backend (Litestar, standalone venv :8010, no auth)
                        │   1. subprocess: uv run howard-test <cmd> --json  (cwd = placeframe root)
                        │   2. direct reads: placeframe/data/{localizations,poseless_sets,
                        │      alignments,fusion,map_images,visualizations,capture_sources.json}
                        ▼
                 howard-test CLI (scripts/, ~5.8k lines with helpers)
                    │        │        │        │
                    │        │        │        └── docker exec placeframe-minio-logger-1 mc pipe
                    │        │        │            (MinIO direct store around the 1 GB body limit)
                    │        │        └── data/ tar/result caches (reconstructions/<id>.tar, ...)
                    │        └── .env (PUBLIC_URL / PLACEFRAME_API_URL, Keycloak client creds)
                    └── placeframe_api_client (generated) ── HTTP ── placeframe API ── Postgres/MinIO
```

Four couplings bind the dashboard to dev_hh:

1. **The backend's only data path is the CLI subprocess** (~13 shell-out call sites; the CLI is
   the auth boundary, orchestrator, and cache manager, and imports `placeframe_api_client`,
   `core`, `common`, `panorama` from the workspace).
2. **Dashboard state lives in placeframe's untracked `data/` tree** — runs, poseless registry,
   alignments, fusion runs, capture-source index, tar caches: one machine's filesystem as a
   database.
3. **Oversized uploads bypass the API entirely** (the `docker exec` MinIO store), dev-stack-only.
4. **The dashboard depends on dev_hh's server endpoints** (cancel, `detail`, `use_chunking`, 422
   `extra` forwarding, import-attach, deterministic ordering) — a dashboard pointed at a
   pre-dev_hh stack silently loses features; the §4.1 ports close this.

Each coupling is dissolved by a §2 decision and a §4 work item.

### 1.7 Porting guidance: what to trust

Howard's strong code deserves lighter review than his structurally weak choices:

- The cancellation design (refused progress write as the worker's only cancellation signal) is a
  correct and elegant fit for the worker-pull lease architecture, properly documented in
  `docker/reconstructor/AGENTS.md`.
- The no-intrinsic-refinement rule for rendered views came from a real, diagnosed failure mode
  (COLMAP's bogus-camera filter collapsing an 80-frame model to 28 frames) and carries its
  diagnosis.
- Opt-in detail payloads, failure diagnostics surviving the raise, GPU-memory reasoning with
  explicit budgets and derivations — all sound.
- Test discipline is real: 14 new test files across panorama, reconstructor, localizer, scripts.
  Commit discipline is excellent: 92 coherent commits, each with rationale; AGENTS.md docs
  updated in the same commits that change behavior.

Known defects and where each dies: dashboard-on-CLI (D1); filesystem-as-database (D3); the MinIO
bypass (§4.3.5); the `howard_test.py` monolith (dissolves into §4 items); silent credential
holding (D6 — v1 accepts it against auth-disabled stacks, the deferred auth work ends it); the
spherical `is_spherical` data-cache (dies with the CLI). The fusion filter's three ports
(`RelocalizationFilter.cs`, `fusion-test/fusion/algorithms/kalman.py`, `offline_fusion.py`) are
intentional duplication for fidelity and will drift — §6 risk.

## 2. Decisions

Each entry: the decision, why, what it concedes. Together they define the end state.

**D1 — The dashboard is a pure frontend; its backend is deleted.**
The dashboard becomes a hosted SPA — TypeScript + three.js + a generated TS api-client — talking
directly to the placeframe API. No backend service of its own: no subprocess orchestration, no
job registry, no filesystem state, no credential holder. The current backend's three substances
resolve as: dumb pipes to the CLI (~2/3 of routes, zero logic) die in favor of direct client
calls; dashboard-local state moves into Postgres behind the API (D3); the job engine and
computation become worker/lease job types (D4). Migration is route-by-route and Howard is never
blocked: his backend keeps working via the CLI while endpoints land on `dev`; each dashboard
route flips from subprocess/filesystem to a direct client call as its endpoint appears; `app.py`
is deleted last, as an empty shell. Concessions: the frontend fetch layer is rewritten against
the TS client and the viewer loads via presigned streaming (the components and three.js code
survive); directory-browse and save-to-folder UX become File System Access and browser
downloads.

```
  hosted SPA (TS + three.js + TS api-client, zero install, v1 unauthenticated)
      │ WebCodecs + WebGL ingest (panorama math ported to GLSL)
      │ multipart presigned upload ──► MinIO
      ▼
  placeframe API (auth_mode = "disabled" for v1)
      │            ── Postgres (captures, reconstructions, runs, alignments, provenance)
      │            ── MinIO presigned GET (points/poses/views)
      └── worker/lease jobs (reconstruct, batch-localize, ICP, merge, imu-scale, cancel)

  research home: fusion-test, offline_fusion, FusionPlayer
```

**D2 — Ingest runs in the browser; there is no companion CLI.**
The heavy media work of spherical ingest — .insv decode, equirect→fisheye view rendering, tar
assembly, multi-GB upload — is browser-native: WebCodecs `VideoDecoder` (hardware H.264 in all
modern browsers); WebGL2/WebGPU fragment shaders for view rendering (the four layouts'
projection math is small, pure, and tested — porting to GLSL is mechanical, and the GPU
outperforms the numpy reference); File System Access API stream-writes the tar (tar is
sequentially streamable by design, so memory stays bounded at any size); upload is multipart
PUT on presigned URLs straight to MinIO — the same large-object ingest path placeframe needs
regardless (§4.3.5). The .insv demux is a bounded TS port of `panorama`'s parser. Concessions:
the full path requires a Chromium-family browser (`showDirectoryPicker` for poseless image
folders); H.264 footage is required for universal decode (HEVC only where the platform supports
it); the Python `panorama` package remains the reference implementation — and the research loop
on the research branch — until the browser port reaches parity, then dies with it. `RunCharts`
survives on real run data from the API; `FusionPlayer` and `offline_fusion` leave the dashboard
with the fusion program (D7).

**D3 — Dashboard state lives in Postgres behind the API; no second datastore is ever built.**
Localization runs, alignments, image-set (poseless) registrations, and provenance become API
resources. The `localization_evaluations` table is the precedent — calibration-corpus results
already go to Postgres via the API this way. Concession: placeframe gains the schema + routes +
job work of §4.3; that productization is the project's center of gravity, not the extraction.

**D4 — Long-running operations are worker/lease job types, not client orchestration.**
Batch-localize, ICP, merge, and imu-scale run as service jobs with API progress endpoints,
reusing the cancellation mechanism judged sound in §1.7. The dashboard's in-memory fire-and-poll
registry dies; the browser polls API progress.

**D5 — The spherical pipeline is client-side in its entirety; the server stays spherical-agnostic.**
The SPA decodes/stitches the .insv, renders fisheye views, optionally thins to keyframes,
stream-assembles an ordinary multi-camera fisheye tar, and uploads it (D2). Placeframe accepts
those tars through four generic capabilities (§4.2) and holds no spherical knowledge: the tar is
well-formed and origin-agnostic, which the pipeline already respects. Concessions: layout choice
freezes at import (re-import = re-pick the source file, provenance pre-filled); the capture no
longer stores the raw sphere; Howard's server-side re-reconstruct-with-different-layout loop
(he A/B'd layouts constantly) survives only on the research branch, as throwaway scaffolding.

**D6 — v1 is unauthenticated, targeting auth-disabled deployments.**
The SPA runs only against stacks with `auth_mode = "disabled"` (already supported —
`docker/api/src/auth.py:51`; anonymous shared identity, optional `x-anonymous-identity` UUID
header), which covers every dev/operator stack the tool targets. User-facing auth — Keycloak
auth-code + PKCE, CORS on the API — is deferred until the dashboard must face an auth-enabled
deployment; the API speaks client-credentials only today, and a browser can't hold client
secrets. Same-origin hosting from the stack defers the CORS question too.

**D7 — The fusion program lives on a research branch now, its own repo eventually.**
`fusion-test/`, `offline_fusion.py`, `FusionPlayer`, and `artifacts/vps-fusion.html` move to a
long-lived unmerged branch cut from post-§4.1 `dev`, rebased on a set cadence. The product
pieces land elsewhere: the Unity recorder + camera-provider interfaces + `RelocalizationFilter`
fix on `dev`'s `packages/unity`, the CaptureTool wiring in placeframe-capture-tool, calibration
schema v3 on `dev`. Concession: the branch needs an owner or staleness recurs (§6).

**D8 — dev_hh is a quarry, not a branch.**
Nothing merges or rebases wholesale (§0). The 92 commits disassemble into the four §3
destinations; dev_hh is archived at the end. After the phase-3 splits, dev_hh accepts
dashboard/CLI/client-spherical commits only — anything else diverges from its landed port
(§6 risk).

**D9 — Intrinsics refinement flips to off, gated on an A/B.**
The refine-focal/distortion default is an inherited COLMAP stock default, not a design choice
(§4.4), and it systematically damages localization accuracy. Decided in principle; gated on one
real-capture refine-on/off comparison, which does not exist in the repo. The exact-intrinsics
marker (§4.2.2) is designed only after this lands.

## 3. Disposition manifest

Every dev_hh cluster → destination. Nature: *port* (behavior re-landed on the restructured
tree, with tests), *minimal-port* (throwaway scaffolding), *rewrite*, *new* (built fresh on
`dev`), *dissolve* (absorbed into other destinations), *delete*, *drop*. Phases refer to §5.

| Cluster | From (dev_hh) | Destination | Nature | Phase |
|---|---|---|---|---|
| Rig-verification crash guard | `docker/reconstructor/…/colmap.py:229-247` | `dev` `workloads/` | port — live hazard today | 1 |
| Geometry-derived pairing rules | `docker/reconstructor/pairs.py` | `dev` `workloads/` | port — inert for today's captures | 1 |
| Server capabilities: cancel route, 409s, cancellation plumbing, localize `detail`/`use_chunking`, `LocalizationFailure`, `empty_cache`, `limits`/`extra`, bigint codegen fix | `docker/api`, `lease-server`, `localizer`, `reconstructor`, `core`, `common` | `dev` `workloads/` + `packages/` | port, item-by-item | 2 |
| GPU robustness: lightglue host-staging, keypoint-budget batching, `LIGHTGLUE_BATCH_SIZE` | `localizer`, `reconstructor`, root compose | `dev` | port | 2 |
| `cross_rig_pair_distance_m` | `core` + `reconstructor` | `dev` | port | 2 |
| Calibration schema v3 (variance floors) | `core`, `fit_calibration.py` | `dev` | port | 2 |
| `PLACEFRAME_API_URL` short-circuit + `.env.sample` docs | `scripts/api_auth.py` | `dev` `scripts/` | port | 2 |
| Unity recorder + camera providers + `RelocalizationFilter` fix | `packages/unity` | `dev` `packages/unity` | port | 3 |
| CaptureTool wiring (record button, `AppState.recording`, LocalizationManager, published-map fix) | `apps/CaptureTool` | placeframe-capture-tool | port | 3 |
| Fusion program (`fusion-test/`, `offline_fusion.py`, `FusionPlayer`, `vps-fusion.html`) | various | research branch → own repo later | move | 3 |
| Server-side spherical pipeline (`SphericalExpansion`, `spherical.py`, spherical pairing, four `spherical_*` options) | `docker/reconstructor` + `core` schema | research branch | minimal-port — dies at browser parity | 3 |
| `panorama` package | `packages/python/panorama` | research branch (reference); browser port lives in dashboard repo | rewrite (GLSL/TS) | 4–5 |
| New dev surface (§4.3: TS client, runs + batch-localize, artifact streaming, presigned ingest, alignments + ICP, image-set captures, provenance, imu-scale job) | — | `dev` | new | 4 |
| Dashboard frontend (viewer, align page, components) | `dashboard/frontend` | dashboard repo | port + fetch-layer rewrite | 5 |
| `howard-test` CLI + helpers | `scripts/howard_test.py`, `icp_align.py`, `imu_scale.py`, `offline_fusion.py` | dissolves: orchestration → §4.3 items; `icp_align`/`imu_scale` → reconstructor; `offline_fusion` → research branch | dissolve | 2–5 |
| Dashboard backend | `dashboard/backend/app.py` | deleted (empty shell first) | delete | 5 |
| `data/` tree state | `placeframe/data/` | Postgres via API; caches dissolve into artifact streaming | dissolve | 4 |
| MinIO `docker exec` bypass | `scripts/howard_test.py` | replaced by presigned multipart ingest (§4.3.5) | delete | 4 |
| Research scratch (`pano_mapping/`, `scripts/experiments/`) | standalone | dropped (confirm — §7) | drop | 5 |

## 4. Placeframe work items

Everything that lands on `dev`: mechanical ports (§4.1), the four design-bearing generic
capabilities (§4.2), new product surface (§4.3), and one mainline fix (§4.4).

### 4.1 Ports from dev_hh (mechanical, item-by-item merge with tests)

All are pre-restructure (`docker/…`) paths; land against `workloads/` + `placeframe_core`.

- **API**: `PUT /reconstructions/{id}/cancel`; localize `use_chunking` + `detail` params; 422
  reason/`extra` failure forwarding; import-tar attaching to an existing capture; capture-delete
  MinIO cleanup + 409 guard; expanded-captures newest-first ordering.
- **lease-server + reconstructor**: the cancellation mechanism (409 refusal of progress/finalize
  writes; worker-side `ReconstructionCancelled` plumbing) — architecturally sound for the
  worker-pull design.
- **localizer**: `build_detail.py` + detail plumbing (opt-in, hot path unaffected);
  `LocalizationFailure` structured payloads; `use_chunking` flag; per-request `cuda.empty_cache()`.
- **core/common**: `localization_detail.py`; `limits.py` (`REQUEST_MAX_BODY_SIZE` shared
  constant); `extra` passthrough in the shared error handler; bigint-int64 datamodels codegen
  fix (re-landed in the post-`build/` codegen tree); calibration schema v3 (separate
  rotation/translation variance floors, empirically-derived 0.3° / 20 cm).
- **GPU robustness**: lightglue host-staged batch tensors; `batching.py` keypoint-budget rule;
  `LIGHTGLUE_BATCH_SIZE` compose passthrough.
- **`cross_rig_pair_distance_m`** pairing option (client-orchestrated merging still uploads
  combined captures that reconstruct server-side).
- **`PLACEFRAME_API_URL` short-circuit** (295 ms → 1.5 ms per call when the stack is behind
  ngrok) + `.env.sample` docs.

### 4.2 Four generic capabilities for client-rendered spherical tars

Everything placeframe needs to accept the dashboard's fisheye tars; no spherical logic:

1. **Fisheye camera vocabulary.** `CameraConfig` is `Pinhole | Spherical`; a tar of rendered
   OPENCV_FISHEYE views cannot be described. Add a fisheye member to the manifest schema
   (+ codegen, + the reconstructor's manifest→pycolmap camera construction). Fisheye support was
   already wanted for its own sake. (`panorama.projection` also supports *rectilinear* views —
   `camera_model()` returns `PINHOLE` — but nothing selects it; the shipped pipeline is
   fisheye-only, with rectilinear living in `scripts/experiments/projection_ab.py` as an A/B arm.
   A rectilinear/dodecahedron-only dashboard variant would need zero new lens vocabulary — §7.)
2. **Exact-intrinsics handling.** A per-camera marker distinguishing exact intrinsics
   (factory-calibrated, rendered-by-construction) from estimated ones. Depends on D9: once
   placeframe trusts device intrinsics by default, the marker's job narrows to flagging the
   *estimated* kind (e.g. Howard's poseless `fx=width` guess), which is also the only case where
   refinement is wanted.
3. **Pairing rules derived from rig geometry.** (a) Skip intra-frame pairs between co-located
   cameras — two photos from the same optical centre cannot triangulate, so matching them is
   pure waste; (b) optionally, prune sequential cross-camera pairs whose axes diverge beyond an
   angle threshold — pure efficiency, omit and everything still works, slower. Both derivable
   from the manifest's per-camera rotation/translation.
4. **Rig-verification crash guard for co-located rigs.** COLMAP's rig verification assumes a
   rig's cameras are physically apart; a view-rig (all cameras at one point) makes pycolmap
   4.0.4 walk off the end of a vector and **SIGABRT the worker container** — the job then sits
   claimed until the 30-minute reaper requeues it. Must-not-crash, not a nicety. Generic gate:
   cameras sharing an optical centre (per-camera translations ≈ 0).

Items 3 and 4 are standalone-landable on current `dev` ahead of everything else: both rules are
provably inert for every capture type placeframe accepts today (ZED stereo: 12 cm baseline,
parallel axes — both thresholds keep everything; ARFoundation: mono), so they change no existing
behavior while preparing for client-rendered tars. Item 4 is a live hazard on `dev` today, not a
hypothetical: current `dev` enables rig verification unconditionally
(`GeometricVerifierOptions(rig_verification=True)`,
`workloads/reconstructor/src/reconstructor/colmap.py:232` — no co-located gate exists there), so
a hand-crafted co-located multi-camera manifest kills the worker today.

### 4.3 New surface (the productization)

Real product features the pure-frontend dashboard makes necessary — each is schema + routes +
job types + tests on `dev`, landed on its own merits:

1. **TS api-client target** in openapi-clientgen (python + csharp today), published or
   tarball-referenced for npm consumption. Gates the frontend migration.
2. **Localization runs in Postgres + batch-localize job** — a run resource with progress,
   executed through the worker/lease architecture. The CLI's per-image loop dissolves.
3. **Artifact streaming** — presigned MinIO GETs for points/poses/views; the viewer's binary
   protocol hits the API and the CLI's local tar caches dissolve.
4. **Large-object ingest** — presigned multipart PUT + bodyless create (the bodyless half
   already exists via `POST /capture_sessions/bulk`). Replaces the `docker exec` MinIO bypass;
   the browser and the CaptureTool are both presigned clients.
5. **Alignments + ICP + merge as map management** — alignment table relating reconstructions,
   transform payloads, `icp_align.py` beside the reconstructor, merged-capture creation via the
   existing upload path.
6. **Image-set captures as a first-class type** — the poseless synthetic-trajectory hack becomes
   real schema support for captures without device poses ("reconstruct from loose photos").
7. **Capture provenance field** — the source-video pointer recorded at creation, replacing
   `capture_sources.json`.
8. **imu-scale as a reconstructor-side job** — scale recovery consumes the reconstruction's own
   poses plus the capture's IMU samples, both server-side after upload; the fisheye tar schema
   gains IMU members to carry them (§7).
9. **User-facing auth — deferred** (D6). Keycloak auth-code + PKCE + CORS when the dashboard
   must face an auth-enabled deployment.

### 4.4 Mainline defect: intrinsics refinement defaults to on

Not Howard's. Placeframe's design intent is that capture intrinsics are device-reported and
factory-calibrated, and were meant to be trusted (never refined). The code does the opposite,
on current `dev` and everywhere else (`workloads/reconstructor/src/reconstructor/
options_builder.py` on dev's tip; `docker/reconstructor/…` at Howard's merge-base and on
`dev_hh`):

```python
incremental_pipeline_options.ba_refine_focal_length = True   # line 71 on dev tip
incremental_pipeline_options.ba_refine_extra_params = True   # line 73
bundle_adjustment_options.refine_focal_length = True         # line 92, final BA
bundle_adjustment_options.refine_extra_params = True         # line 94
```

Focal length and distortion coefficients are refined for every real capture. (Principal point is
never refined, and rig extrinsics aren't refined in the incremental pass — the line was already
half-drawn.) The True/True/False set is exactly pycolmap/COLMAP's stock defaults written out
explicitly (since Tyler's `3b33d91f`, 2026-06-01, and earlier refactors) — an inherited default,
not a decision. Howard did not change it: his `has_rendered_views` carve-out skips refinement
only for rendered views. Why it matters for a localization product: refinement drifts map
cameras away from the true device intrinsics, while every later query localizes with its own
true factory intrinsics — a systematic map/query mismatch invisible in reprojection metrics that
lands in localization error. All current capture strategies (ARFoundation ARCamera, ZED factory
calibration) deliver calibrated intrinsics; the only estimated intrinsics in the system are
Howard's two client-side fabrications (poseless `fx=width` guess, rendered views). Flipping is
gated on the D9 A/B.

## 5. Plan of attack (skeleton)

Five phases; each ends CI-green on `dev` with Howard unblocked. A later session elaborates this
into tickets and sequences — the phases themselves are settled.

1. **Stop the bleeding.** Land the rig-verification guard + geometry-derived pairing rules
   (§4.2.3–4; the guard fixes a live SIGABRT). Kick off the refinement on/off A/B — long
   data-run lead time, and it gates D9 and the §4.2.2 marker.
   *End state: dev's co-located-rig hazard gone; no other behavior change.*
2. **Port §4.1** onto the restructured tree, each item independently merged with its tests.
   *End state: Howard's dev_hh tooling runs un-rebased against a dev-built stack; staleness
   stops compounding.*
3. **Split the homes.** Unity recorder + camera-provider interfaces + `RelocalizationFilter`
   fix → `packages/unity` on `dev`; CaptureTool wiring → placeframe-capture-tool; cut the
   research branch from post-phase-2 `dev` carrying the fusion program + the server-side
   spherical pipeline (minimal port — throwaway at browser parity; Howard's stack builds from
   it; someone owns its rebase cadence).
   *End state: both Unity repos green; dev_hh is a dashboard/CLI-only quarry.*
4. **Productize §4.3** on `dev`, dependency-ordered: the TS client first (gates all frontend
   work), then the load-bearing three — runs in Postgres, artifact streaming, presigned
   ingest — then alignments/ICP, image-set captures, provenance, imu-scale.
   *End state: dashboard routes flip from subprocess/filesystem to direct client calls as
   endpoints appear; trailing features ship in the SPA as their endpoints land.*
5. **Extract and delete.** The dashboard repo is the hosted SPA + browser ingest — easy paths
   first (plain tars, poseless folders), .insv decode last, golden-image tests against the numpy
   reference. `app.py` is deleted as an empty shell; dev_hh is archived; the research branch's
   server-side spherical dies when browser ingest reaches parity.
   *End state: the D1 diagram is reality.*

## 6. Risks

- **Browser ingest is the only new-technology risk.** Mitigations: the numpy reference with its
  tests; golden-image tests against it; easy-paths-first staging; prototype the WebCodecs/GLSL
  path early relative to need.
- **Image-set captures can balloon** (real schema design, the likeliest §4.3 item to slip).
  Never let it sit on the critical path — the SPA ships without it until ready.
- **Research-branch staleness recurs unless someone owns the rebase cadence.** dev_hh rotted
  because nobody absorbed dev's motion for three months; the branch repeats that failure mode
  by default.
- **Howard as a moving target.** dev_hh keeps receiving commits until phase 5. The phase-3 rule
  (dashboard/CLI/client-spherical only — D8) is what keeps landed ports from silently diverging;
  it requires actual communication with Howard, not a plan bullet.
- **Filter triplication drift.** The fusion filter exists as three intentional ports (§1.7) that
  will drift until the fusion program consolidates in its own repo.
- **Codegen archaeology.** `build/` no longer exists on `dev`; the bigint fix and any spherical-
  era schema regen must be re-found in the post-restructure codegen tree, with canonical
  separate codegen commits.

## 7. Open questions

Each gates something; none blocks starting phase 1.

- **Rectilinear vs fisheye for browser-rendered views.** Fisheye costs the lens-vocabulary
  addition (§4.2.1; wanted anyway, supports the wide layouts); rectilinear/dodecahedron-only
  costs zero vocabulary but paints the pipeline into a narrow corner. Recommendation: fisheye.
  Decide before landing §4.2.1.
- **Refinement-flip A/B** (D9). One real-capture refine-on/off comparison through
  fit-calibration / localization metrics. Long lead time — start in phase 1.
- **Fisheye-tar IMU members** (§4.3.8). Which IMU records ride in the tar, in what format, so
  the reconstructor can run scale recovery.
- **HEVC footage and non-Chromium browsers** (D2). Accepted v1 constraints or blockers? Product
  call.
- **Keycloak user-auth design** (§4.3.9). Deferred; auth-code + PKCE flow details, token
  lifetimes, role model, CORS scope — design before building, when an auth-enabled dashboard
  becomes a requirement.
- **Research scratch disposition.** `pano_mapping/` (superseded by the panorama package) and
  `scripts/experiments/` (projection/retrieval A/Bs) — likely dropped at extraction, confirm
  before.
