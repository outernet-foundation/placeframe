# docker/

## What this is

Placeframe's server-side stack: a set of cooperating microservices that ingest capture sessions from phone clients, reconstruct sparse 3D maps, and serve real-time 6-DOF localization queries. Everything in this directory builds into a container that runs under `compose.yml`. The Unity apps in `apps/` consume this stack; this directory is the stack itself.

## Shape

### Services

| Service | Path | Technology | Role |
|---|---|---|---|
| `api` | `api/` | Litestar (ASGI) | Main REST API: users, places, captures, maps. User-facing surface, fronted by the gateway. |
| `lease-server` | `lease-server/` | Litestar (ASGI) | Control-plane work-queue: four lease endpoints (`request`, `progress`, `succeed`, `fail`) the reconstructor polls. Bound only to the compose-internal network — no gateway upstream, no auth middleware. |
| `localizer` | `localizer/` | Litestar (ASGI) | Image-to-map localization (LightGlue feature matching + RANSAC). |
| `reconstructor` | `reconstructor/` | Python + pycolmap | Builds sparse 3D maps from capture sessions. GPU-resident. Pulls work from `lease-server` via container DNS. |
| `database-manager` | `database-manager/` | Python | Runs SQL migrations at startup, then exits. |
| `auth-initializer` | `auth-initializer/` | Python | Configures the Keycloak realm at startup, then exits. Gated by the `keycloak` compose profile (same as Keycloak itself). |
| `gateway` | `gateway/` | Caddy | Reverse proxy fronting every public surface (`api`, `localizer`, `/loki/`, `/grafana/`, Keycloak). Caddyfile is generated at container start by `entrypoint.sh` from `PUBLIC_URL` and `AUTH_MODE`; there is no static Caddyfile. `PUBLIC_URL` is parsed into scheme + port to emit the right `X-Forwarded-Proto` / `X-Forwarded-Port` headers upstream. The listener is always cleartext HTTP on `:8443` with h2c enabled — TLS is either terminated upstream by the tunnel relay (ngrok) or absent (LAN / air-gap). |
| `ngrok` | (no Dockerfile — upstream image) | ngrok | Always present in compose; self-skips when `NGROK_DOMAIN` is empty. When set, runs an [ngrok](https://ngrok.com) HTTP tunnel forwarding public traffic to the gateway at `http://gateway:8443` (cleartext, HTTP/2 upstream via h2c). Authenticates with `NGROK_AUTHTOKEN` from `.env`. Consumers that need UDP plumbing (e.g. LiveKit's RTC media plane in Make-it-Sing) layer a different tunnel agent in their own compose. |
| `keycloak` | `keycloak/` | Keycloak 26 | OIDC / OAuth2 identity provider. Gated by the `keycloak` compose profile — present only when `AUTH_MODE=keycloak`. |

**Observability**: `loki/` (log storage, monolithic mode), `alloy/` (Docker-socket log collector — auto-discovers new containers), `grafana/` (query UI). Loki writes to a `loki` bucket in the shared MinIO. Alloy mounts `/var/run/docker.sock` to discover containers; new services are picked up automatically with no per-service config.

**Backing services**: PostgreSQL 16, MinIO (S3-compatible object storage), CloudBeaver (web DB UI).

**GPU**: `compose.yml` defines the stack; `compose.cuda.yml` and `compose.rocm.yml` add GPU overrides for `reconstructor` and `localizer`. The `up` script auto-detects the accelerator.

### Data flow

```
phone --[tar]--> api --[row+blob]--> MinIO
                                       ^
                                       |
              reconstructor <--[lease]-- lease-server
                       |
                       '--[h5/pq/sfm]--> MinIO
                                          ^
phone --[query img]--> localizer --[lookup]'
```

1. **Capture**: a Unity phone client (`apps/CaptureTool/`) records images + sensor data and POSTs a `.tar` to the API. The API stores the tar in `dev-captures/<capture_session_id>.tar` and inserts a row at `queued`.
2. **Reconstruction**: the `reconstructor` worker polls `lease-server`'s `POST /leases/request` over the compose network to claim queued work (no separate orchestrator service — it's a worker-pull architecture). On a successful claim, it downloads the tar, runs feature extraction → matching → OPQ/PQ training → geometric verification → SfM, uploads outputs to `dev-reconstructions/<reconstruction_id>/`, then `PUT`s `/leases/<id>/succeed` (or `/fail`) to `lease-server`. Progress updates between phases go through `/leases/<id>/progress`.
3. **Localization**: a Unity client posts a query image to `localizer`, which matches it against the stored map and estimates a 6-DOF pose via RANSAC / PnP.
4. **Georeferencing**: the Map Registration Tool (Unity standalone) can visually align point clouds against Cesium tilesets (OSM / Google Photorealistic Tiles) to anchor a map in real-world coordinates.

### Authentication and public URL

The stack is parameterised by two independent env vars:

- **`PUBLIC_URL`**: full URL of the public-facing entry point, e.g. `https://yoursubdomain.ngrok-free.app` or `http://192.168.1.100:58080`. Single source of truth — compose plumbs it through to every downstream (API issuer URLs, Keycloak realm URLs, Grafana root URL, gateway forwarded-headers, OpenAPI server list) instead of each consumer reconstructing a domain + scheme by hand. The gateway always listens on cleartext `:8443` with h2c; TLS, when present, is terminated upstream by the tunnel relay. LAN-with-self-signed is not a supported shape (distributing an internal CA to every Unity client is the pain point air-gap mode exists to remove), so there is no `tls internal` listener.
- **`AUTH_MODE`**: `keycloak` (default) | `disabled`. Toggles whether `api` and the gateway's auth-fronted routes use Keycloak-issued JWTs or run unauthenticated. When `disabled`, Keycloak and `auth-initializer` are excluded from the stack via the `keycloak` compose profile, the gateway drops the `/auth/*` reverse-proxy block and the `forward_auth` directive in front of `/loki/*`, and `AuthMiddleware` in `api` skips JWT decode entirely.

**Identity in disabled mode.** When `AUTH_MODE=disabled`, the API ignores client identity entirely: every request is authenticated as a single shared anonymous user (a sentinel UUID) scoped to one shared tenant (the nil UUID `SHARED_ANONYMOUS_TENANT`), so all anonymous clients read and write the same data — one tenant, no per-device distinction. No header is required; an `X-Anonymous-Identity` header (Unity still sends `SystemInfo.deviceUniqueIdentifier`) is accepted but discarded. The shared identity is a UUID rather than a label like `"anonymous"` because the request identity is cast to `uuid` downstream — `app.user_id` and `current_tenant()` in `docker/api/src/database.py` — so a non-UUID identity raises at the database layer. There is no fake JWT signing. `AuthMiddleware` runs in both modes (installed unconditionally), so `connection.user` is always populated — the JWT `sub` under keycloak, the shared sentinel under disabled — and no route handler carries a null-identity case. Both sentinels live in `docker/api/src/constants.py`.

**Client-side auth mode.** The server is the source of truth: an unauthenticated `GET /server-info` reports `auth_mode` and, under keycloak, the public OIDC parameters (`issuer_url`, `auth_url`, `token_url`, `audience`) the client needs. Clients fetch it before login, so there is no local `useKeycloak` toggle and nothing about the realm, client id, or token endpoint is hardcoded client-side. The login UI splits into a connect step (enter URL → fetch `/server-info`) and a credentials step that appears only when the backend reports `keycloak`; a `disabled` backend goes straight in. A mismatch or unreachable backend surfaces at the connect step with a legible message — unreachable URL, not-a-Placeframe-server, or unsupported `auth_mode` — rather than as a silent 404/401 from the first auth or `/api/*` call. `/server-info` is exempted from `AuthMiddleware` via the `EXCLUDE_FROM_AUTH` list in `docker/api/src/main.py` and appears in the OpenAPI schema so the generated clients expose it; it returns only public URLs, never the internal `auth_certs_url` (the compose-network JWKS endpoint, which only the API reaches).

**Combinations.** Three combinations are supported:

- `https://…` + `keycloak` — tunneled (ngrok), OAuth (the default and the only public-facing shape).
- `https://…` + `disabled` — tunneled, no auth (e.g. exposing a demo without credentialing).
- `http://…` + `disabled` — air-gap LAN, cleartext, no auth.

The fourth combination, `http://…` + `keycloak`, is rejected at compose startup: sending OAuth credentials in cleartext is a footgun, and the air-gap deployment shape exists specifically to remove the cert-distribution and OAuth ceremony. The guard lives in `packages/python/placeframe-stack/src/placeframe_stack/modes.py` and keys off the parsed `PUBLIC_URL` scheme — token-on-the-wire is the actual hazard, not LAN-vs-tunnel.

**`lease-server`** has no auth middleware in any mode. It is bound only to the compose-internal network, has no gateway upstream and no host port; the reconstructor reaches it by container DNS. Network isolation is the boundary.

**Non-app services** (Grafana, CloudBeaver, MinIO) keep their own internal auth in every mode. `AUTH_MODE=disabled` disables Placeframe's app auth, not adjacent services' auth.

## Constraints

- **Priors-on vs priors-off is structural, not policy.** The reconstructor decides per-capture from the rig: any rig with more than one camera makes the whole capture priors-off (stereo baseline anchors metric scale, PosePrior loss disabled, final-BA rig pinned). All-monocular captures run priors-on. There is no `ReconstructionOptions` field for the toggle and no API-side device-type defaulting. The reconstructor enforces the invariant at rig load (`docker/reconstructor/src/reconstructor/rig.py`) and downstream: a monocular capture supplying no position columns fails at the keyframe pre-pass and sequential pair generation, both of which require per-frame translations. See `docker/reconstructor/AGENTS.md` for what each path does downstream.
- **Reconstructor and localizer split off the API rather than living inside it** because they hold GPU memory, run long jobs (reconstruction is minutes; the API request-loop is seconds), and ship with different dependency stacks (pycolmap, PyTorch with conditional `cpu` / `cuda` / `rocm` extras). Crashing them must not crash request handling.
- **Worker-pull (lease endpoints) instead of a push orchestrator**: reconstruction jobs are long, restart-survivable, and need at-most-once execution. The `reconstructor` claims work via `POST /leases/request` against `lease-server` and reports back via `/progress`/`/succeed`/`/fail`, with `lease-server` enforcing lease-state transitions and a 30-min reaper for dropped leases. This collapses what used to be a separate orchestrator service into a Postgres queue + worker poll, and gives crash recovery for free.
- **`lease-server` is a separate service, not a route group on `api`, and has no auth**: the lease endpoints are an in-cluster control-plane surface — they carry no meaningful user identity, and the previous design (lease routes on `api`, reconstructor authenticating via Keycloak client-credentials JWT) put the auth boundary in the wrong place. Auth ceremony was pure overhead: the middleware extracted `claims["sub"]` but nothing read it, no row was keyed on it, no authz branched on token type. The correct boundary for in-cluster service-to-service traffic is **the network**: `lease-server` binds only to the compose network with no host port and no gateway upstream, the reconstructor reaches it by container DNS, and no token is fetched or verified. Isolating it as its own service (rather than a second listener inside `api`) also gives failure isolation (a bug in lease handlers cannot crash user-facing routes), independent restart/deploy, and a tiny image free of Scalar UI, OAuth schemes, and the user-facing `AuthMiddleware`. Codegen mirrors the split: `lease-server` produces its own `placeframe_lease_client`, consumed only by the reconstructor; `placeframe_api_client` no longer advertises lease routes it cannot reach.
- **Keycloak instead of bespoke auth**: OIDC unlocks browser-based human flows for the user-facing `api` without writing token-issuance code. The cost is one extra container.
- **`PUBLIC_URL` and `AUTH_MODE` are independent axes**: collapsing them into a single `MODE=public|airgap` switch would have been smaller, but the two concerns answer different questions — `PUBLIC_URL` controls how *clients connect* (domain vs. LAN IP, cleartext transport, port), `AUTH_MODE` controls whether *requests carry user identity* (Keycloak JWT vs. a single shared anonymous identity). The `https://… + disabled` combination — public tunnel, no auth — is a real configuration (demos, evaluation deployments) that a single switch could not express. The dangerous combination (`http://… + keycloak`, which would send OAuth credentials in cleartext) is rejected at compose startup rather than encoded structurally; the guard is a single scheme check in `modes.py`, the flexibility is worth keeping. LAN-with-self-signed (a third deployment shape that would need its own combination) is explicitly out of scope — distributing a per-deployment self-signed CA to every Unity client is the exact pain point the air-gap mode exists to remove.
- **MinIO instead of a filesystem volume** for blobs: the same S3 API ports to a managed object store later, and Loki, captures, and reconstructions can all share one storage backend in dev without a migration when the stack moves out of compose.
- **Allowlist `.dockerignore`** (`*` then `!` entries) is the single source of truth for what affects image builds and the `CONTEXT_SHA` tag. BuildKit does not expose which context files a build actually used ([moby/buildkit#1181](https://github.com/moby/buildkit/issues/1181), open since 2019), so the allowlist is how we keep image identity deterministic. Adding a `COPY` for a path missing from the allowlist fails loudly; extra entries cause only spurious rebuilds.

## Debugging

Operational commands for investigating "what did the system actually do?" — DB, blob, and log queries. (The zed-box SSH / sandbox-key access path lives in `scripts/AGENTS.md`.)

### Postgres

The application user is `placeframe_owner` (RLS policies are scoped to it), not `postgres`:

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

Bucket schema and what each prefix contains is the MinIO bucket layout under `## Constraints` above. The operationally relevant gotcha: presence of `sfm_model/` under `dev-reconstructions/<id>/` means SfM completed, regardless of what the DB says — the final `/succeed` PUT can fail and orphan a reconstruction at `uploading`.

### Reconstruction audit

Pull a reconstruction's SfM artifacts and its capture's priors side by side to check a finished map against its capture — the input to the consecutive-frame displacement check (`uv run displacement-check`) and the held-out-frame protocol described in `design/reconstruction-validation.md`.

**Pull SfM artifacts + capture priors from MinIO** (after the `mc alias set` above):

```bash
RID=<recon_id>; CID=<capture_session_id>; WORK=/tmp/recon_audit/$RID
mkdir -p "$WORK/sfm" "$WORK/cap"
for f in frames.txt frame_poses.npz rigs.txt cameras.txt images.txt; do
  docker exec placeframe-minio-1 mc cp local/dev-reconstructions/$RID/sfm_model/$f /tmp/$f
  docker cp placeframe-minio-1:/tmp/$f "$WORK/sfm/$f"
done
docker exec placeframe-minio-1 mc cp local/dev-captures/$CID.tar /tmp/cap.tar
docker cp placeframe-minio-1:/tmp/cap.tar "$WORK/cap.tar"
tar -xf "$WORK/cap.tar" -C "$WORK/cap" manifest.json rig0/frames.csv
```

**Inspect a recon's options + key metrics from Postgres** (app user, per the Postgres note above — `-U postgres` cannot see the `reconstructions` table):

```bash
docker exec placeframe-postgres-1 psql -U placeframe_owner -d placeframe -c "
  SELECT manifest->'options', manifest->'metrics'->'all_verified_matches',
         manifest->'metrics'->'map_image_count'
  FROM reconstructions WHERE id='<rid>';"
```

**Queue a rerun** — unchanged, or with a single `ReconstructionOptions` field overridden, without a code change:

```bash
docker exec placeframe-postgres-1 psql -U placeframe_owner -d placeframe -c "
  INSERT INTO reconstructions (tenant_id, capture_session_id, status, manifest_version, manifest)
  SELECT tenant_id, capture_session_id, 'queued'::reconstruction_status, manifest_version,
         jsonb_set(manifest, '{options,<field>}', to_jsonb(<value>))  -- or bare 'manifest' to rerun as-is
  FROM reconstructions WHERE id='<source_recon_id>' RETURNING id;"
```

`uv run reconstruction create <capture> --options-json '{...}'` is the typed alternative to the `jsonb_set` override.

**Frame file layouts** (for parsing SfM output against capture priors):

- `frames.csv` (capture priors, `world_from_rig`, OPENCV axis): `timestamp_ms,gx,gy,gz` (gravity-only — current ZED), +`tx,ty,tz`, or +quaternion. Schema in `docker/reconstructor/AGENTS.md` "frames.csv schema".
- `sfm_model/frames.txt` (COLMAP rig output, `rig_from_world`): `FRAME_ID RIG_ID QW QX QY QZ TX TY TZ NUM_DATA_IDS [SENSOR_TYPE SENSOR_ID DATA_ID]…`. Hamilton quaternion; rig center in world = `-R(rig_from_world).T @ t(rig_from_world)`.
- `sfm_model/images.txt`: odd lines `IMAGE_ID QW QX QY QZ TX TY TZ CAMERA_ID IMAGE_NAME`; map IMAGE_ID → timestamp via `rig\d+/camera\d+/(\d+)\.jpg`.

### Loki

Loki holds logs from every service plus the phone-side capture-tool relay. Available `service_name` values:

```
alloy api capture-tool cloudbeaver gateway grafana keycloak loki
minio minio-logger ngrok postgres reconstructor-cuda zed-capture
```

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

For repeated queries, use `uv run loki-query` (`scripts/AGENTS.md`) — it handles the URL encoding and formats output as `HH:MM:SS LEVEL [logGroup] message`.

### Where each service logs

- **api** → Loki `service_name="api"`. Every HTTP request, including `/internal/leases/<id>/{progress,succeed,fail}` from the reconstructor.
- **reconstructor-cuda** → Loki `service_name="reconstructor-cuda"` and `docker logs`. Per-image progress, MinIO put markers, lease lifecycle (`Acquired lease`, `Reconstruction succeeded`, `Reconstruction failed: …`). To observe end-to-end lease activity from the API side, query the **api** logs for `/internal/leases/` traffic — lease-request 404s mean "no work available", lease-progress 200s mean an active job is reporting in.
- **capture-tool** (phone) → Loki `service_name="capture-tool"`, pushed directly from the Unity app via the gateway. See `apps/CaptureTool/CLAUDE.md` for relay details.
- **zed-capture** (ZED box) → Loki `service_name="zed-capture"`, but **only while the phone is AOA-connected and logged in**. The box has no direct backend link: its logs are drained from box-side `aoa-loki` by the phone's `LogDrainController` and pushed verbatim to the backend Loki. An empty `{service_name="zed-capture"}` result usually means the phone isn't draining (no AOA link, not logged in, or nothing newer than the drain cursor) — not that the box logged nothing. To read the box directly, `ssh zed-box` (see `scripts/AGENTS.md`), then query box-side `aoa-loki` (`wget -qO- 'http://127.0.0.1:3100/loki/api/v1/query_range?query=%7Bservice_name%3D~%22.%2B%22%7D'`) or `sudo docker logs $(sudo docker ps -q --filter name=zed-capture)`. Full mechanism in `docker/zed-capture/CLAUDE.md`.

## See also

- `docker/reconstructor/AGENTS.md` and `docker/localizer/AGENTS.md` — the two heavy GPU services that this stack hosts. Each carries its own subsystem constraints; this file covers the multi-service relationships.
