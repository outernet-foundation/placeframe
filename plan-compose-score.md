# Compose → score initiative plan

The remaining work to reach the end state: no hand-authored compose files — the stack is
score-generated in `stack/generated/compose`, decomposed into five published OCI artifacts,
and consumers assemble their own backend by `include:`-ing artifacts instead of flipping
`COMPOSE_PROFILES`/`AUTH_MODE` switches. The k8s manifests (SaaS/Pulumi tier) are the second
rendering of the same score sources and ride along.

Replaces `compaction.md`, `plan-auth-refactor.md`, and `design/compose-artifact-split.md`
(all deleted; B1 is shipped; the artifact table and structural rules are carried below).

## Settled — do not re-litigate

- **Auth is structural.** `AUTH_ISSUER_URL` presence selects OIDC vs anonymous inside the api
  (B1, shipped). Issuer set requires `AUTH_JWKS_URL`/`AUTH_AUTHORIZATION_ENDPOINT`/
  `AUTH_TOKEN_ENDPOINT` (explicit — split-horizon kills discovery; no derivation); issuer +
  cleartext `http://` PUBLIC_URL is a boot error. `/server-info`'s `auth_mode` wire values
  unchanged.
- **Object storage is SeaweedFS everywhere.** MinIO is dead in both tiers. The fixed-name
  MinIO provisioners existed only because loki's config hardcoded `minio:9000` — retarget
  loki to the SeaweedFS S3 endpoint instead.
- Score tools pinned: score-compose 0.42.0, score-k8s 0.15.0 (output differs across
  versions). Fetch release binaries onto PATH — docker-devkit's `ensure_score_tools` is
  dead code, nothing auto-fetches them.
- Generation resolves image SHAs from the **committed** tree: commit sources, regenerate,
  commit artifacts.

## Current state

- B1 complete on `more-final-polish` (API, compose.yml, .env.sample, score tier, docs;
  Make-it-Sing env sample conformed; OidcAuthBackend named for the protocol, not provider).
- **`generate-score` is red**: `gateway.yaml` still references the config resource's retired
  `auth_mode` output (deliberate dangle — work item 1 removes it). `stack/generated/` holds
  the last-good artifacts and stays deployable.
- **Pulumi coordination owed** (external): `placeframe-secrets` gains `AUTH_ISSUER_URL` +
  `AUTH_AUTHORIZATION_ENDPOINT`/`AUTH_TOKEN_ENDPOINT` (drops old `AUTH_URL`/
  `AUTH_TOKEN_URL`); keeps `AUTH_MODE` until a post-B2 regeneration rolls out.
- **Load-bearing defect**: `api.yaml` feeds `MINIO_ENDPOINT_URL`/`MINIO_ACCESS_KEY`/
  `MINIO_SECRET_KEY` but Settings reads `S3_*` — object storage silently unconfigured in
  both generated renderings, including the k8s manifests the SaaS engineer builds on.
- Make-it-Sing still includes the old published bundle by digest; its new env names go live
  only when it re-pins (work item 7).

## Target: five artifacts

| Artifact | Contents | Variant-tagged |
|---|---|---|
| `placeframe-core-<variant>` | api, lease-server, postgres, seaweedfs, cloudbeaver, database-manager, database-migrator, loki, alloy, grafana, initialize-loki, reconstructor, localizer | yes (cuda/rocm) |
| `placeframe-edge-keycloak` | gateway (auth snippets mounted), keycloak, auth-initializer | no |
| `placeframe-edge-anonymous` | gateway (no auth snippets) | no |
| `placeframe-tunnel-ngrok` | ngrok | no |
| `placeframe-tunnel-rathole` | rathole-client | no |

The gateway lives in the edge, not core: artifacts own their services wholly (zero
cross-include overrides), core has no public surface on its own, and the auth choice is
which edge you include. The edge pair is two generations differing in keycloak provisioner
and auth snippet configs presence.

## Work items (ordered)

1. **B2 — gateway by file presence** (small; unblocks generation). `workloads/gateway/
   entrypoint.sh`: delete the AUTH_MODE branch, keep the PUBLIC_URL scheme/port parsing;
   emit auth directives via `import /etc/caddy/snippets/*.conf` globs (Caddy no-match
   imports are silent no-ops; gate on file presence if a version warns). Drop `AUTH_MODE`
   from `gateway.yaml`, `.env` files, and (post-regeneration) the k8s secret. Regenerate —
   the generator goes green.
2. **Slice A — storage on SeaweedFS + provider-neutral edge.** S3 resource outputs feed
   `S3_ENDPOINT_URL`/`S3_ACCESS_KEY`/`S3_SECRET_KEY` (fixes the MINIO_* bug); SeaweedFS
   compose provisioner (weed server + admin console + audit relay + s3-initializer/
   bucket-init, from hand compose.yml); delete both MinIO provisioners and write the
   SeaweedFS k8s twin (StatefulSet + services, postgres-provisioner pattern); loki config
   retargets off `minio:9000`. Rename score resource type `placeframe-keycloak` →
   `oidc-issuer`. Sync the SaaS engineer (env contract + storage swap).
3. **Slice B — observability.** loki/alloy/grafana as provisioner services; configs
   bind-mounted from committed paths locally, bind→content conversion at publish
   (`docker compose publish` refuses bind mounts — the conversion is mandatory before
   publishing any file-carrying service); initialize-loki chown sidecar.
4. **Slice C — long tail.** cloudbeaver, auth-initializer, ngrok, rathole-client.
5. **Slice D — GPU services.** reconstructor + localizer workload files; `gpus: all`,
   healthchecks, localizer network alias via patch templates; `service-port` resources for
   lease-server/localizer wiring. The GPU-shape decision lands here (recommendation:
   per-variant generated core — the service stays `reconstructor`, only image + device
   patch differ per variant).
6. **Seam generation + multi-artifact publish (B3+B4).** `generate-score` emits one compose
   per seam (subsetted workload lists per artifact); `publish-compose` publishes the five
   artifacts.
7. **Cutover.** `lifecycle.files` → generated files; delete hand compose; Make-it-Sing
   re-pins to `core-cuda` + `edge-keycloak` + `tunnel-rathole`; `.env.sample` drops
   `AUTH_MODE`/`COMPOSE_PROFILES`; `uv run up` UX unchanged; re-think preflight's
   `compose.postgres.yml` role. `compose.dev.yml` survives as the hand overlay on generated
   files, never published.

## Mechanics that shape execution

- Runtime `.env` holes survive only as provisioner outputs inserted verbatim — the
  `placeframe-config` provisioner is the passthrough valve.
- score-compose validates probes and ignores them → patch templates emit healthchecks.
- Generated workload services are named `<workload>-<container>` (`api-api`); patches must
  compute names, never hardcode; the gateway Caddyfile proxies by generated service name.
- Cross-workload `depends_on` is not a score concept — the auto-built `wait-for-resources`
  gate replaces it; poll-retry absorbs ordering.
- Seam tests: platform-variance → score file; docker-only detail → patch template;
  generation-time baking vs runtime `.env` hole → config provisioner.

## Open decisions

- GPU shape (per-variant generated core recommended).
- Regeneration cadence once generated compose is load-bearing (manual two-commit dance vs
  CI gate; the gate was disabled because every context SHA re-stales artifacts).
- docker-devkit layout adoption (`deployfiles/` rename on its `rename-folders` branch), and
  pushing the `ensure_score_tools` dead-code fix upstream.
- Pin `alpine` (wait-for-resources gate) + the CNPG operand image before the tier is
  load-bearing.
- Linear ticket linkage for this plan (`linear` CLI unavailable in this sandbox).
