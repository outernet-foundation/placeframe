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

## Rationale

- **Reconstructor and localizer split off the API rather than living inside it** because they hold GPU memory, run long jobs (reconstruction is minutes; the API request-loop is seconds), and ship with different dependency stacks (pycolmap, PyTorch with conditional `cpu` / `cuda` / `rocm` extras). Crashing them must not crash request handling.
- **Worker-pull (lease endpoints) instead of a push orchestrator**: reconstruction jobs are long, restart-survivable, and need at-most-once execution. The `reconstructor` claims work via `POST /internal/leases/request` and reports back via `/progress`/`/succeed`/`/fail`, with the API enforcing lease-state transitions and a 30-min reaper for dropped leases. This collapses what used to be a separate orchestrator service into a Postgres queue + worker poll, and gives crash recovery for free.
- **Keycloak instead of bespoke auth**: OIDC unlocks both human flows (browser login) and machine flows (client credentials for the reconstructor's lease calls) without writing token-issuance code. The cost is one extra container.
- **MinIO instead of a filesystem volume** for blobs: the same S3 API ports to a managed object store later, and Loki, captures, and reconstructions can all share one storage backend in dev without a migration when the stack moves out of compose.
- **Allowlist `.dockerignore`** (`*` then `!` entries) is the single source of truth for what affects image builds and the `CONTEXT_SHA` tag. BuildKit does not expose which context files a build actually used ([moby/buildkit#1181](https://github.com/moby/buildkit/issues/1181), open since 2019), so the allowlist is how we keep image identity deterministic. Adding a `COPY` for a path missing from the allowlist fails loudly; extra entries cause only spurious rebuilds.

## Operational debugging

Quick paths for investigating "what did the system actually do?" — log queries, blob inspection, DB inspection.

### Postgres

The application user is `placeframe_owner` (RLS policies are scoped to it). Not `postgres`:

```bash
docker exec placeframe-postgres-1 psql -U placeframe_owner -d placeframe -c "<query>"
```

A bare `psql -U postgres` lands in a default schema with no app tables visible.

### MinIO

Configure the `mc` alias inside the MinIO container using the credentials from `.env` (`MINIO_ACCESS_KEY` / `MINIO_SECRET_KEY` — `admin` / `password` in dev):

```bash
docker exec placeframe-minio-1 mc alias set local http://localhost:9000 admin password
docker exec placeframe-minio-1 mc ls --recursive local/dev-captures/
docker exec placeframe-minio-1 mc ls --recursive local/dev-reconstructions/
```

Bucket layout:

| Bucket | Key pattern | Notes |
|---|---|---|
| `dev-captures` | `<capture_session_id>.tar` | Single tarball per capture, not an unpacked tree. |
| `dev-reconstructions` | `<reconstruction_id>/{features.h5, global_descriptors.h5, opq_matrix.tf, pq_quantizer.pq, pairs.txt, sfm_model/*}` | One directory per reconstruction. `sfm_model/` is the final SfM output (frames.txt, points3D.npz, images.txt, etc.). **Presence of `sfm_model/` means SfM completed, regardless of what the DB says about status** — the final `/succeed` PUT can fail (see auth.py JWKS retry path) and orphan a reconstruction at `uploading`. |
| `loki` | (Loki internal) | Don't touch. |

### Loki

Loki holds logs from every service plus the phone-side capture-tool relay. Available `service_name` values:

```
alloy api capture-tool cloudbeaver gateway grafana keycloak loki
minio minio-logger ngrok postgres reconstructor-cuda zed-capture
```

(`state-sync` also appears in the label set — see the co-location note above; it's not part of Placeframe.)

Query template (LogQL via the HTTP API; run from the loki container so you don't have to plumb auth):

```bash
docker exec placeframe-loki-1 wget -qO- \
  'http://localhost:3100/loki/api/v1/query_range?query=%7Bservice_name%3D%22<svc>%22%7D&limit=200&direction=backward'
```

Useful filters appended to the query:

- `|= "<literal>"` — line filter, exact substring.
- `|~ "(?i)error|fail"` — regex filter, case-insensitive.

Scope to an incident with `&start=<unix-nanos>&end=<unix-nanos>`. Date-to-nanos: `date -d '13:11:00 UTC' +%s%N`.

List current label values: `wget -qO- 'http://localhost:3100/loki/api/v1/label/service_name/values'`.

### Where each service logs

- **api** → Loki `service_name="api"`. Every HTTP request, including `/internal/leases/<id>/{progress,succeed,fail}` from the reconstructor.
- **reconstructor-cuda** → Loki `service_name="reconstructor-cuda"` and `docker logs`. Per-image progress, MinIO put markers, lease lifecycle (`Acquired lease`, `Reconstruction succeeded`, `Reconstruction failed: …`). To observe end-to-end lease activity from the API side, query the **api** logs for `/internal/leases/` traffic — lease-request 404s mean "no work available", lease-progress 200s mean an active job is reporting in.
- **capture-tool** (phone) → Loki `service_name="capture-tool"`, pushed directly from the Unity app via the gateway. See `apps/AndroidMobile/CLAUDE.md` for relay details.

### Reconstructor lease lifecycle

The reconstructor is a worker that pulls work via the API:

1. `POST /internal/leases/request` — claim the next queued reconstruction (404 = no work).
2. Download `dev-captures/<capture_session_id>.tar` from MinIO.
3. Run pipeline (extract features → match → train OPQ/PQ → verify geometry → SfM).
4. Upload outputs to `dev-reconstructions/<reconstruction_id>/`.
5. `PUT /internal/leases/<reconstruction_id>/succeed` (or `/fail` on error).

Status updates between phases go through `PUT /internal/leases/<id>/progress`. If the final `/succeed` PUT fails, MinIO has the outputs but the DB still shows the in-progress status.
