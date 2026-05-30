# docker/

## What this is

Placeframe's server-side stack: a set of cooperating microservices that ingest capture sessions from phone clients, reconstruct sparse 3D maps, and serve real-time 6-DOF localization queries. Everything in this directory builds into a container that runs under `compose.yml`. The Unity apps in `apps/` consume this stack; this directory is the stack itself.

## Shape

### Services

| Service | Path | Technology | Role |
|---|---|---|---|
| `api` | `api/` | Litestar (ASGI) | Main REST API: users, places, captures, maps. |
| `localizer` | `localizer/` | Litestar (ASGI) | Image-to-map localization (LightGlue feature matching + RANSAC). |
| `reconstructor` | `reconstructor/` | Python + pycolmap | Builds sparse 3D maps from capture sessions. GPU-resident. Pulls work from the API via the lease endpoints. |
| `database-manager` | `database-manager/` | Python | Runs SQL migrations at startup, then exits. |
| `auth-initializer` | `auth-initializer/` | Python | Configures the Keycloak realm at startup, then exits. |
| `gateway` | `gateway/` | ngrok | Public HTTPS tunnel for clients outside the host. |
| `keycloak` | `keycloak/` | Keycloak 26 | OIDC / OAuth2 identity provider. |

**Observability**: `loki/` (log storage, monolithic mode), `alloy/` (Docker-socket log collector — auto-discovers new containers), `grafana/` (query UI). Loki writes to a `loki` bucket in the shared MinIO. Alloy mounts `/var/run/docker.sock` to discover containers; new services are picked up automatically with no per-service config.

**Backing services**: PostgreSQL 16, MinIO (S3-compatible object storage), CloudBeaver (web DB UI).

**Co-located, not part of Placeframe**: `state-sync` is a legacy Outernet `.NET` service (`legacy/Outernet.Server/`) that runs in the same compose stack but is unrelated to Placeframe's reconstruction or localization flow. It is mentioned here only to disambiguate compose output; do not reach for it when reasoning about Placeframe behavior.

**GPU**: `compose.yml` defines the stack; `compose.cuda.yml` and `compose.rocm.yml` add GPU overrides for `reconstructor` and `localizer`. The `up` script auto-detects the accelerator.

### Data flow

```
phone --[tar]--> api --[row+blob]--> MinIO
                  ^                    ^
                  |                    |
                  |         reconstructor pulls --[lease]--> [pipeline] --[h5/pq/sfm]--> MinIO
                  |                                                                        ^
phone --[query img]--> localizer --[lookup]------------------------------------------------'
```

1. **Capture**: a Unity phone client (`apps/AndroidMobile/`) records images + sensor data and POSTs a `.tar` to the API. The API stores the tar in `dev-captures/<capture_session_id>.tar` and inserts a row at `queued`.
2. **Reconstruction**: the `reconstructor` worker polls `POST /internal/leases/request` to claim queued work (no separate orchestrator service — it's a worker-pull architecture). On a successful claim, it downloads the tar, runs feature extraction → matching → OPQ/PQ training → geometric verification → SfM, uploads outputs to `dev-reconstructions/<reconstruction_id>/`, then `PUT`s `/internal/leases/<id>/succeed` (or `/fail`). Progress updates between phases go through `/internal/leases/<id>/progress`.
3. **Localization**: a Unity client posts a query image to `localizer`, which matches it against the stored map and estimates a 6-DOF pose via RANSAC / PnP.
4. **Georeferencing**: the Map Registration Tool (Unity standalone) can visually align point clouds against Cesium tilesets (OSM / Google Photorealistic Tiles) to anchor a map in real-world coordinates.

### Authentication

Every API endpoint requires an OAuth2 Bearer token from Keycloak. Dev credentials are `user` / `password` (configured in `keycloak/realm-export/placeframe.json`). The `reconstructor` worker uses the OAuth2 client-credentials flow for service-to-service calls against the lease endpoints.

The `gateway` is the only public ingress. It also fronts `/loki/` for the Unity log relay (clients push directly to Loki via the gateway with their existing Keycloak token).

## Constraints

- **Priors-on vs priors-off is structural, not policy.** The reconstructor decides per-capture from the rig: any rig with more than one camera makes the whole capture priors-off (stereo baseline anchors metric scale, PosePrior loss disabled, final-BA rig pinned). All-monocular captures run priors-on. There is no `ReconstructionOptions` field for the toggle and no API-side device-type defaulting. Capture upload enforces the static end of the invariant — see `_validate_monocular_rigs_have_position_priors` in `docker/api/src/routers/capture_sessions.py` — and the reconstructor enforces the dynamic end at rig load (`docker/reconstructor/src/reconstructor/rig.py`). See `docker/reconstructor/SPEC.md` for what each path does downstream.
- **Reconstructor and localizer split off the API rather than living inside it** because they hold GPU memory, run long jobs (reconstruction is minutes; the API request-loop is seconds), and ship with different dependency stacks (pycolmap, PyTorch with conditional `cpu` / `cuda` / `rocm` extras). Crashing them must not crash request handling.
- **Worker-pull (lease endpoints) instead of a push orchestrator**: reconstruction jobs are long, restart-survivable, and need at-most-once execution. The `reconstructor` claims work via `POST /internal/leases/request` and reports back via `/progress`/`/succeed`/`/fail`, with the API enforcing lease-state transitions and a 30-min reaper for dropped leases. This collapses what used to be a separate orchestrator service into a Postgres queue + worker poll, and gives crash recovery for free.
- **Keycloak instead of bespoke auth**: OIDC unlocks both human flows (browser login) and machine flows (client credentials for the reconstructor's lease calls) without writing token-issuance code. The cost is one extra container.
- **MinIO instead of a filesystem volume** for blobs: the same S3 API ports to a managed object store later, and Loki, captures, and reconstructions can all share one storage backend in dev without a migration when the stack moves out of compose.
- **Allowlist `.dockerignore`** (`*` then `!` entries) is the single source of truth for what affects image builds and the `CONTEXT_SHA` tag. BuildKit does not expose which context files a build actually used ([moby/buildkit#1181](https://github.com/moby/buildkit/issues/1181), open since 2019), so the allowlist is how we keep image identity deterministic. Adding a `COPY` for a path missing from the allowlist fails loudly; extra entries cause only spurious rebuilds.

## See also

- `.pulsar/debugging.md` — operator runbook for investigating "what did the system actually do?" (Postgres / MinIO / Loki query patterns, per-service log locations). The bucket-layout and log-location constraints surface from here; the runbook commands themselves live there.
- `docker/reconstructor/SPEC.md` and `docker/localizer/SPEC.md` — the two heavy GPU services that this stack hosts. Each carries its own subsystem constraints; this file covers the multi-service relationships.
