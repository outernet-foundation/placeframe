# workloads/

## What this is

Placeframe's server-side stack: a set of cooperating microservices that ingest capture sessions from phone clients, reconstruct sparse 3D maps, and serve real-time 6-DOF localization queries. Everything in this directory builds into a container that runs under the score-generated compose artifacts. The Unity apps in `apps/` consume this stack; this directory is the stack itself.

## Shape

### Services

| Service | Path | Technology | Role |
|---|---|---|---|
| `api` | `api/` | Litestar (ASGI) | Main REST API: users, places, captures, maps. User-facing surface, fronted by the gateway. |
| `lease-server` | `lease-server/` | Litestar (ASGI) | Control-plane work-queue: four lease endpoints (`request`, `progress`, `succeed`, `fail`) the reconstructor polls. Bound only to the compose-internal network — no gateway upstream, no auth middleware. |
| `localizer` | `localizer/` | Litestar (ASGI) | Image-to-map localization (LightGlue feature matching + RANSAC). |
| `reconstructor` | `reconstructor/` | Python + pycolmap | Builds sparse 3D maps from capture sessions. GPU-resident. Pulls work from `lease-server` via container DNS. |
| `database-manager` | `database-manager/` | Python | Runs SQL migrations at startup, then exits. |
| `auth-initializer` | `auth-initializer/` | Python | Configures the Keycloak realm post-boot, then exits: polls keycloak's admin API, then creates or updates the realm from the committed export over the admin REST API, substituting the `KEYCLOAK_*`/`PUBLIC_URL` holes from env; when `SEED_TEST_USERS` (`username:password` pairs) is set, also create-or-updates those users. The old file-import path is gone; in the score tier the emitted `keycloak-configurator` service (compose) and realm Job (k8s) run it. |
| `gateway` | — | (deleted) | The gateway workload, image, and entrypoint are gone: the front door is emitted by docker-devkit from the consumer config's routes (a pinned caddy whose Caddyfile renders at `up`), and auth-mode composition is the config's `auth`/`keycloak` option, not a container synthesizing a Caddyfile from mounted snippets. |
| `ngrok` | (no Dockerfile — upstream image) | ngrok | One compose option (`tunnel`/`ngrok` in `docker-devkit.yaml`); the artifact rides the assembly when named in `BUNDLES=`. Runs an [ngrok](https://ngrok.com) HTTP tunnel forwarding public traffic to the front door at `http://door:8443` (the devkit-emitted caddy edge; cleartext, HTTP/1.1 upstream). Consumers that need UDP plumbing (e.g. LiveKit's RTC media plane in Make-it-Sing) layer a different tunnel agent in their own compose. |
| `keycloak` | `keycloak/` | Keycloak 26 | OIDC / OAuth2 identity provider. Rides the `auth`/`keycloak` option (named in `BUNDLES=`); the option and the API's issuer-based auth mode are the same axis (see Authentication below). Tier-neutral: the same workload container runs on both renderings, its env fed by the oidc-issuer provisioner outputs. |

**Observability**: `loki/` (log storage, monolithic mode), `alloy/` (OTLP log relay), `grafana/` (query UI) — digest-pinned stock mirror images, not built wrappers. Configs ride compose top-level `configs:` from `workloads/loki/config.yaml`, `workloads/alloy/config.alloy`, and `workloads/grafana/provisioning/datasources/datasources.yaml`, mounted at the in-container paths the `command:` overrides reference. Loki writes to a `loki` bucket in the shared SeaweedFS; its config expands `${S3_ACCESS_KEY}`/`${S3_SECRET_KEY}` at runtime (`-config.expand-env=true`). Services push OTLP/gRPC to alloy on 4317 — alloy mounts no docker.sock and discovers nothing. The published OCI bundle carries the same inlined `content:` configs (docker-devkit's bind-inlining post-pass rewrites them at generation, `$`-doubled so env expansion stays in the container). The ZED box consumes the same stock images + its own configs from the [placeframe-capture-tool](https://github.com/outernet-foundation/placeframe-capture-tool) repo (`config.alloy` there is a mirror of this file — the one config the two stacks shared; `LOKI_WRITE_ENDPOINT` env drives the only difference).

**Backing services**: PostgreSQL 16, SeaweedFS (S3-compatible object storage; `seaweedfs` server + `seaweedfs-admin` web console + `seaweedfs-audit` relay).

**GPU**: the generated core artifact comes per accelerator (`compose.core-cuda.yaml` / `compose.core-rocm.yaml` under `stack/generated/compose/`); the host names its variant in `BUNDLES=`.

### Data flow

```
phone --[tar]--> api --[row+blob]--> SeaweedFS
                                        ^
                                        |
               reconstructor <--[lease]-- lease-server
                        |
                        '--[h5/pq/sfm]--> SeaweedFS
                                          ^
phone --[query img]--> localizer --[lookup]'
```

1. **Capture**: the capture-tool phone app (in the [placeframe-capture-tool](https://github.com/outernet-foundation/placeframe-capture-tool) repo) records images + sensor data and POSTs a `.tar` to the API. The API stores the tar in `captures/<capture_session_id>.tar` and inserts a row at `queued`.
2. **Reconstruction**: the `reconstructor` worker polls `lease-server`'s `POST /leases/request` over the compose network to claim queued work (no separate orchestrator service — it's a worker-pull architecture). On a successful claim, it downloads the tar, runs feature extraction → matching → OPQ/PQ training → geometric verification → SfM, uploads outputs to `reconstructions/<reconstruction_id>/`, then `PUT`s `/leases/<id>/succeed` (or `/fail`) to `lease-server`. Progress updates between phases go through `/leases/<id>/progress`.
3. **Localization**: a Unity client posts a query image to `localizer`, which matches it against the stored map and estimates a 6-DOF pose via RANSAC / PnP.
4. **Georeferencing**: out of scope for this stack — map-to-world registration against Cesium tilesets was the (now-deleted) Map Registration Tool's job; the Cesium asset pipeline under `build/` remains for producing tilesets.

### Authentication and public URL

The stack is parameterised by `PUBLIC_URL` plus the auth block:

- **`COMPOSE_PROFILES` is extinct**: assembly selection is structural. `uv run up` materializes the assembly from the options named in `BUNDLES=` (`.env`, shell-over-`.env` precedence) — the core variant (`cuda`/`rocm`), the auth edge (`keycloak` = OIDC edge; omitting it is the anonymous edge), and the relay when `ngrok` is named. `uv run down` materializes a name-only root and hands off `down --remove-orphans`, so teardown covers prior selections without resolving a single include. A stale `COMPOSE_PROFILES` line in `.env` fails loudly (it names profiles no artifact defines).

- **`PUBLIC_URL`**: full URL of the public-facing entry point, e.g. `https://yoursubdomain.ngrok-free.app` or `http://192.168.1.100:58080`. Single source of truth — compose plumbs it through to every downstream (Keycloak realm URLs, Grafana root URL, the door's forwarded-headers, OpenAPI server list) instead of each consumer reconstructing a domain + scheme by hand. The public-facing `AUTH_*` URLs in `.env` are derived from it by hand. The door always listens on cleartext `:8443`; TLS, when present, is terminated upstream by the tunnel relay. LAN-with-self-signed is not a supported shape (distributing an internal CA to every Unity client is the pain point air-gap mode exists to remove), so there is no `tls internal` listener.
- **The `AUTH_*` block (mode is structural, not told)**: at boot the API asks one question — was it given `AUTH_ISSUER_URL`? Set ⇒ the keycloak backend (JWKS verification of bearer tokens). Unset ⇒ the anonymous backend (one shared sentinel user/tenant, no credentials). The issuer never travels alone: `AUTH_JWKS_URL`, `AUTH_AUTHORIZATION_ENDPOINT`, and `AUTH_TOKEN_ENDPOINT` are required when it is set and must be absent when it is not — partial config is a loud boot error in `check_auth_config` (`workloads/api/src/settings.py`), not a runtime 401 mystery. `AUTH_AUDIENCE` defaults to `placeframe-api` (the realm export's client id) and is overridden only for a swapped provider whose `aud` differs from its client id. The API is an OIDC resource server: it knows the protocol, not the provider — every keycloak-specific spelling (realm path, `keycloak:8080`, the `/auth/` prefix) lives in the deployment edge that runs the provider, so none of the five are derivable by the API and compose passes all of them through as soft passthroughs (empty ⇒ unset). Setting the issuer while `PUBLIC_URL` is cleartext `http://` is rejected at API boot (OAuth credentials would travel unencrypted). `AUTH_MODE` is extinct everywhere in the stack: the API selects its mode from issuer presence, the keycloak bundle mounts exactly when the `auth`/`keycloak` option rides (an anonymous assembly mounts nothing), and the edge adds no auth of its own — the door's `protected`/forward_auth mechanism is stripped, and edge re-protection is a bundle-shipped oauth2-proxy sidecar treaty.

**Identity in anonymous mode.** When `AUTH_ISSUER_URL` is unset, the API ignores client identity entirely: every request is authenticated as a single shared anonymous user (a sentinel UUID) scoped to one shared tenant (the nil UUID `SHARED_ANONYMOUS_TENANT`), so all anonymous clients read and write the same data — one tenant, no per-device distinction. No header is required; an `X-Anonymous-Identity` header (Unity still sends `SystemInfo.deviceUniqueIdentifier`) is accepted but discarded. The anonymous backend mints the synthetic claims itself (`sub` = sentinel user, `tenant_id` = sentinel tenant); the shared identity is a UUID rather than a label like `"anonymous"` because the request identity is cast to `uuid` downstream — `app.user_id` and `current_tenant()` in `workloads/api/src/database.py`. There is no fake JWT signing. `AuthMiddleware` runs in both modes (installed unconditionally), so `connection.user` is always populated — the JWT `sub` under keycloak, the shared sentinel under anonymous — and no route handler carries a null-identity case. Both sentinels live in `workloads/api/src/constants.py`.

**Client-side auth mode.** The server is the source of truth: an unauthenticated `GET /server-info` reports `auth_mode` (derived from issuer presence — the wire values `"keycloak"`/`"disabled"` are unchanged) and, under keycloak, the public OIDC parameters (`issuer_url`, `auth_url`, `token_url`, `audience`) the client needs. Clients fetch it before login, so there is no local `useKeycloak` toggle and nothing about the realm, client id, or token endpoint is hardcoded client-side. The login UI splits into a connect step (enter URL → fetch `/server-info`) and a credentials step that appears only when the backend reports `keycloak`; a `disabled` backend goes straight in. A mismatch or unreachable backend surfaces at the connect step with a legible message — unreachable URL, not-a-Placeframe-server, or unsupported `auth_mode` — rather than as a silent 404/401 from the first auth or `/api/*` call. `/server-info` is exempted from `AuthMiddleware` via the `EXCLUDE_FROM_AUTH` list in `workloads/api/src/main.py` and appears in the OpenAPI schema so the generated clients expose it; it returns only public URLs, never the internal JWKS URL (`AUTH_JWKS_URL`, the compose-network endpoint which only the API reaches).

**Combinations.** Three combinations are supported:

- `https://…` + issuer set — tunneled (ngrok), OAuth (the default and the only public-facing shape).
- `https://…` + anonymous — tunneled, no auth (e.g. exposing a demo without credentialing).
- `http://…` + anonymous — air-gap LAN, cleartext, no auth.

The fourth combination, `http://…` + issuer set, is rejected at API boot by the cleartext-OAuth guard in `check_auth_config` (`workloads/api/src/settings.py`) — sending OAuth credentials in cleartext is the hazard, and the air-gap deployment shape exists specifically to remove the cert-distribution and OAuth ceremony.

**`lease-server`** has no auth middleware in any mode. It is bound only to the compose-internal network, has no gateway upstream and no host port; the reconstructor reaches it by container DNS. Network isolation is the boundary.

**Non-app services** (Grafana, the SeaweedFS admin console) keep their own internal auth in every mode. Anonymous mode disables Placeframe's app auth, not adjacent services' auth.

## Constraints

- **Priors-on vs priors-off is structural, not policy.** The reconstructor decides per-capture from the rig: any rig with more than one camera makes the whole capture priors-off (stereo baseline anchors metric scale, PosePrior loss disabled, final-BA rig pinned). All-monocular captures run priors-on. There is no `ReconstructionOptions` field for the toggle and no API-side device-type defaulting. The reconstructor enforces the invariant at rig load (`workloads/reconstructor/src/reconstructor/rig.py`) and downstream: a monocular capture supplying no position columns fails at the keyframe pre-pass and sequential pair generation, both of which require per-frame translations. See `workloads/reconstructor/AGENTS.md` for what each path does downstream.
- **Reconstructor and localizer split off the API rather than living inside it** because they hold GPU memory, run long jobs (reconstruction is minutes; the API request-loop is seconds), and ship with different dependency stacks (pycolmap, PyTorch with conditional `cpu` / `cuda` / `rocm` extras). Crashing them must not crash request handling.
- **Worker-pull (lease endpoints) instead of a push orchestrator**: reconstruction jobs are long, restart-survivable, and need at-most-once execution. The `reconstructor` claims work via `POST /leases/request` against `lease-server` and reports back via `/progress`/`/succeed`/`/fail`, with `lease-server` enforcing lease-state transitions and a 30-min reaper for dropped leases. This collapses what used to be a separate orchestrator service into a Postgres queue + worker poll, and gives crash recovery for free.
- **`lease-server` is a separate service, not a route group on `api`, and has no auth**: the lease endpoints are an in-cluster control-plane surface — they carry no meaningful user identity, and the previous design (lease routes on `api`, reconstructor authenticating via Keycloak client-credentials JWT) put the auth boundary in the wrong place. Auth ceremony was pure overhead: the middleware extracted `claims["sub"]` but nothing read it, no row was keyed on it, no authz branched on token type. The correct boundary for in-cluster service-to-service traffic is **the network**: `lease-server` binds only to the compose network with no host port and no gateway upstream, the reconstructor reaches it by container DNS, and no token is fetched or verified. Isolating it as its own service (rather than a second listener inside `api`) also gives failure isolation (a bug in lease handlers cannot crash user-facing routes), independent restart/deploy, and a tiny image free of Scalar UI, OAuth schemes, and the user-facing `AuthMiddleware`. Codegen mirrors the split: `lease-server` produces its own `placeframe_lease_client`, consumed only by the reconstructor; `placeframe_api_client` no longer advertises lease routes it cannot reach.
- **Keycloak instead of bespoke auth**: OIDC unlocks browser-based human flows for the user-facing `api` without writing token-issuance code. The cost is one extra container. The realm is seeded with no users — mint them via the admin API, or set `SEED_TEST_USERS=user:password,user2:password` and the configurator seeds them at boot. Either way a user needs `firstName`, `lastName`, and `email` populated or the first direct grant fails with "Account is not fully set up" (Keycloak 26's implicit verify-profile action; a fresh 26.8.1 realm's default profile requires all three).
- **`PUBLIC_URL` and auth mode are independent axes**: collapsing them into a single `MODE=public|airgap` switch would have been smaller, but the two concerns answer different questions — `PUBLIC_URL` controls how *clients connect* (domain vs. LAN IP, cleartext transport, port), the presence of `AUTH_ISSUER_URL` controls whether *requests carry user identity* (Keycloak JWT vs. a single shared anonymous identity). The `https://… + anonymous` combination — public tunnel, no auth — is a real configuration (demos, evaluation deployments) that a single switch could not express. The dangerous combination (`http://…` + issuer set, which would send OAuth credentials in cleartext) is rejected at API boot inside `check_auth_config`, the one component that knows both facts. LAN-with-self-signed (a third deployment shape that would need its own combination) is explicitly out of scope — distributing a per-deployment self-signed CA to every Unity client is the exact pain point the anonymous mode exists to remove.
- **S3-compatible object storage (SeaweedFS) instead of a filesystem volume** for blobs: the same S3 API ports to a managed object store later, and Loki, captures, and reconstructions can all share one storage backend in dev without a migration when the stack moves out of compose. `weed server` runs master+filer+volume+S3 in one process; the S3 identity config and the fluent audit sink are rendered from `S3_ACCESS_KEY` / `S3_SECRET_KEY` at container start by `workloads/seaweedfs/entrypoint-wrapper.sh`. The S3 audit log ships over the fluent protocol (no file/stdout mode in weed), so the `seaweedfs-audit` fluent-bit relay receives on 24224 and echoes every `s3.access` record to its own stdout, where alloy picks it up like any container. The admin console (`weed admin`) requires an explicit `-port.grpc` — its default gRPC port is HTTP port + 10000, which overflows the 16-bit range at 59001.
- **Allowlist `.dockerignore`** (`*` then `!` entries) is the single source of truth for what affects image builds and the `CONTEXT_SHA` tag. BuildKit does not expose which context files a build actually used ([moby/buildkit#1181](https://github.com/moby/buildkit/issues/1181), open since 2019), so the allowlist is how we keep image identity deterministic. Adding a `COPY` for a path missing from the allowlist fails loudly; extra entries cause only spurious rebuilds.

## Debugging

Operational commands for investigating "what did the system actually do?" — DB, blob, and log queries.

### Postgres

The application user is `placeframe_owner` (RLS policies are scoped to it), not `postgres`:

```bash
docker exec placeframe-pf-postgres-1 psql -U placeframe_owner -d placeframe -c "<query>"
```

A bare `psql -U postgres` lands in a default schema with no app tables visible.

### SeaweedFS / S3 buckets

Read bucket contents with the awscli image (creds from `.env`: `S3_ACCESS_KEY` / `S3_SECRET_KEY` — `admin` / `password` in dev; image ref from `docker-devkit.lock`):

```bash
docker run --rm --network placeframe_default \
  -e AWS_ACCESS_KEY_ID=admin -e AWS_SECRET_ACCESS_KEY=password -e AWS_DEFAULT_REGION=us-east-1 \
  $(grep INITIALIZE_S3_IMAGE docker-devkit.lock | cut -d= -f2) \
  s3 ls s3://captures/ --recursive --endpoint-url http://seaweedfs:8333
```

Single-object reads don't even need credentials — the weed filer serves buckets unauthenticated inside the compose network at `http://seaweedfs:8888/buckets/<bucket>/<key>`:

```bash
docker exec placeframe-seaweedfs-1 curl -s http://localhost:8888/buckets/captures/<id>.tar -o /tmp/capture.tar
```

The web console (`weed admin`, login `admin` / `S3_SECRET_KEY`) is published at `SEAWEEDFS_ADMIN_PORT` (59001). For cluster operations there is also `weed shell`: `docker exec placeframe-seaweedfs-1 weed shell -master=localhost:9333`.

Bucket schema and what each prefix contains is the bucket layout under `## Constraints` above. The operationally relevant gotcha: presence of `sfm_model/` under `reconstructions/<id>/` means SfM completed, regardless of what the DB says — the final `/succeed` PUT can fail and orphan a reconstruction at `uploading`.

### Reconstruction audit

Pull a reconstruction's SfM artifacts and its capture's priors side by side to check a finished map against its capture — the input to the consecutive-frame displacement check (`uv run displacement-check`) and the held-out-frame protocol described in `design/reconstruction-validation.md`.

**Pull SfM artifacts + capture priors from SeaweedFS** (awscli invocation as above):

```bash
RID=<recon_id>; CID=<capture_session_id>; WORK=/tmp/recon_audit/$RID
mkdir -p "$WORK/sfm" "$WORK/cap"
for f in frames.txt frame_poses.npz rigs.txt cameras.txt images.txt; do
  docker run --rm --network placeframe_default -v "$WORK/sfm":/work \
    -e AWS_ACCESS_KEY_ID=admin -e AWS_SECRET_ACCESS_KEY=password -e AWS_DEFAULT_REGION=us-east-1 \
    $(grep INITIALIZE_S3_IMAGE docker-devkit.lock | cut -d= -f2) \
    s3 cp s3://reconstructions/$RID/sfm_model/$f /work/$f --endpoint-url http://seaweedfs:8333
done
docker exec placeframe-seaweedfs-1 curl -s http://localhost:8888/buckets/captures/$CID.tar -o /tmp/cap.tar
docker cp placeframe-seaweedfs-1:/tmp/cap.tar "$WORK/cap.tar"
tar -xf "$WORK/cap.tar" -C "$WORK/cap" manifest.json rig0/frames.csv
```

**Inspect a recon's options + key metrics from Postgres** (app user, per the Postgres note above — `-U postgres` cannot see the `reconstructions` table):

```bash
docker exec placeframe-pf-postgres-1 psql -U placeframe_owner -d placeframe -c "
  SELECT manifest->'options', manifest->'metrics'->'all_verified_matches',
         manifest->'metrics'->'map_image_count'
  FROM reconstructions WHERE id='<rid>';"
```

**Queue a rerun** — unchanged, or with a single `ReconstructionOptions` field overridden, without a code change:

```bash
docker exec placeframe-pf-postgres-1 psql -U placeframe_owner -d placeframe -c "
  INSERT INTO reconstructions (tenant_id, capture_session_id, status, manifest_version, manifest)
  SELECT tenant_id, capture_session_id, 'queued'::reconstruction_status, manifest_version,
         jsonb_set(manifest, '{options,<field>}', to_jsonb(<value>))  -- or bare 'manifest' to rerun as-is
  FROM reconstructions WHERE id='<source_recon_id>' RETURNING id;"
```

`uv run reconstruction create <capture> --options-json '{...}'` is the typed alternative to the `jsonb_set` override.

**Frame file layouts** (for parsing SfM output against capture priors):

- `frames.csv` (capture priors, `world_from_rig`, OPENCV axis): `timestamp_ms,gx,gy,gz` (gravity-only — current ZED), +`tx,ty,tz`, or +quaternion. Schema in `workloads/reconstructor/AGENTS.md` "frames.csv schema".
- `sfm_model/frames.txt` (COLMAP rig output, `rig_from_world`): `FRAME_ID RIG_ID QW QX QY QZ TX TY TZ NUM_DATA_IDS [SENSOR_TYPE SENSOR_ID DATA_ID]…`. Hamilton quaternion; rig center in world = `-R(rig_from_world).T @ t(rig_from_world)`.
- `sfm_model/images.txt`: odd lines `IMAGE_ID QW QX QY QZ TX TY TZ CAMERA_ID IMAGE_NAME`; map IMAGE_ID → timestamp via `rig\d+/camera\d+/(\d+)\.jpg`.

### Loki

Loki holds logs from every service plus the phone-side capture-tool relay. Available `service_name` values:

```
alloy api capture-tool door grafana keycloak loki
ngrok postgres reconstructor-cuda seaweedfs seaweedfs-audit zed-capture
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
- **reconstructor-cuda** → Loki `service_name="reconstructor-cuda"` and `docker logs`. Per-image progress, S3 put markers, lease lifecycle (`Acquired lease`, `Reconstruction succeeded`, `Reconstruction failed: …`). To observe end-to-end lease activity from the API side, query the **api** logs for `/internal/leases/` traffic — lease-request 404s mean "no work available", lease-progress 200s mean an active job is reporting in.
- **capture-tool** (phone) → Loki `service_name="capture-tool"`, pushed directly from the Unity app via the gateway. The app lives in the [placeframe-capture-tool](https://github.com/outernet-foundation/placeframe-capture-tool) repo; relay details are documented there.
- **zed-capture** (ZED box) → Loki `service_name="zed-capture"`, but **only while the phone is AOA-connected and logged in**. The box has no direct backend link: its logs are drained from box-side `aoa-loki` by the phone's `LogDrainController` and pushed verbatim to the backend Loki. An empty `{service_name="zed-capture"}` result usually means the phone isn't draining (no AOA link, not logged in, or nothing newer than the drain cursor) — not that the box logged nothing. The whole box side of this drain (AOA link, box-Loki, SSH access) is capture-repo territory — see placeframe-capture-tool's `workloads/zed-capture/AGENTS.md`.

## See also

- `workloads/reconstructor/AGENTS.md` and `workloads/localizer/AGENTS.md` — the two heavy GPU services that this stack hosts. Each carries its own subsystem constraints; this file covers the multi-service relationships.
