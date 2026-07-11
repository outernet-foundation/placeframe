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

## See also

- `.pulsar/debugging.md` — operator runbook for investigating "what did the system actually do?" (Postgres / MinIO / Loki query patterns, per-service log locations). The bucket-layout and log-location constraints surface from here; the runbook commands themselves live there.
- `docker/reconstructor/AGENTS.md` and `docker/localizer/AGENTS.md` — the two heavy GPU services that this stack hosts. Each carries its own subsystem constraints; this file covers the multi-service relationships.
