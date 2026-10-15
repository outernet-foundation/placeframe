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
- **The hand compose files are dead from work item 1 onward.** No work item spends effort
  keeping them coherent; intermediate breakage is accepted, not repaired (B2's entrypoint,
  for instance, leaves the hand gateway without auth routing, and nobody wires snippets into
  `compose.yml`). The files stay on disk only as porting references for the slices and are
  formally deleted at cutover. This initiative is one unified project, not a compatibility
  bridge.
- **Generated compose is hermetic at rest: zero host-filesystem references.** score-compose
  materializes workload `files:` as bind mounts into its gitignored `.score-compose` state
  dir — its model is generate-and-run-here, incompatible with committed/published artifacts.
  The bridge is a docker-devkit `generate-score` post-pass that rewrites every bind into a
  top-level `configs.content` entry, doubling each `$` (the rule `publish_compose.py`'s
  `_inline_configs` already uses — compose interpolation would otherwise eat both loki's
  `${VAR}` and caddy's `{$VAR}` before the container sees them). A bind surviving in a
  generated compose is an artifact bug. Patch templates cannot host this conversion (no disk
  access; `.Workloads` carries literal content only).
- **Auth snippets ride as score workload `files:` with literal content in `gateway.yaml`** —
  one source for both renderings: score-k8s emits ConfigMap+mounts natively; score-compose's
  bind output feeds the generation converter.
- Score tools pinned: score-compose 0.42.0, score-k8s 0.15.0 (output differs across
  versions). Fetch release binaries onto PATH — docker-devkit's `ensure_score_tools` is
  dead code, nothing auto-fetches them.
- Generation resolves image SHAs from the **committed** tree: commit sources, regenerate,
  commit artifacts.

## Current state

- B1 complete on `more-final-polish` (API, compose.yml, .env.sample, score tier, docs;
  Make-it-Sing env sample conformed; OidcAuthBackend named for the protocol, not provider).
- **Work item 1 shipped (a–d)**: the converter is released — docker-devkit 0.4.4 (branch merged
  via PR #16 after review squash + rebase onto origin/dev, which carries PR #15's per-run state
  model: state dirs torn down post-generation, instance suffixes hash-normalised). placeframe
  pinned it (`uv lock --upgrade-package docker-devkit`, `requires: ">=0.4"` admits it) and
  regenerated both artifacts through the released tool — compose hermetic (zero binds, snippets
  inlined as `configs.content`), k8s ConfigMaps native, no `AUTH_MODE` in either rendering, and
  `stack/generated/k8s/.score-k8s/state.yaml` gone from the tier (expected under the new model).
  Known debt riding the release: the inliner and uid-normalisation carry only volume-model
  typing tests in docker-devkit.
- Resumption facts: the pinned score tools and the repo-pinned uv 0.12.15 both live in
  `~/.local/bin`, which is not on the sandbox's default PATH
  (`export PATH="$HOME/.local/bin:$PATH"`; the system uv 0.11.14 cannot read the lock).
  Regeneration is plain `uv run generate-score` from the placeframe root and is deterministic
  across fresh runs; commit sources first, then regenerate, then commit artifacts.
- **Pulumi follow-up — deferred until the rest of this plan completes** (external):
  `placeframe-secrets` gains `AUTH_ISSUER_URL` + `AUTH_AUTHORIZATION_ENDPOINT`/
  `AUTH_TOKEN_ENDPOINT`, and drops `AUTH_URL`/`AUTH_TOKEN_URL` and (already safe — the
  generated manifests no longer reference it) `AUTH_MODE`.
- **Next: Slice A (work item 2)** — the `MINIO_*`→`S3_*` fix below is its first move.
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
and auth snippet presence.

## Work items (ordered)

1. **B2 — gateway by file presence + generation hermeticity.** Three parts; (a) gates the
   regeneration, (b)/(c) are independent of it:
   a. **docker-devkit converter.** `generate-score` gains the bind→`configs.content`
      post-pass (+ tests; the zero-binds invariant above is its acceptance). Commit,
      hand off for push/release, then `uv lock --upgrade-package docker-devkit`.
   b. **Entrypoint rework.** `workloads/gateway/entrypoint.sh`: delete the AUTH_MODE
      branch, keep the PUBLIC_URL scheme/port parsing; export `FORWARDED_PROTO`/
      `FORWARDED_PORT` for the snippets to read via caddy's `{$VAR}`; `import
      /etc/caddy/snippets/site/*.conf` at site level and a `/etc/caddy/snippets/loki/*.conf`
      glob inside the static `handle /loki/*` (the loki proxy itself stays unconditional —
      anonymous clients push logs unauthenticated; only the `forward_auth` gate is
      snippet-borne). Verify caddy 2.8.4 treats no-match globs (missing dir included) as
      silent no-ops; gate on file presence if it warns.
   c. **Score sources.** `gateway.yaml`: drop `AUTH_MODE`; author the two snippet files
      (site/ + loki/) as literal `files:` content. Drop `AUTH_MODE` from the `.env` files.
      Hand compose untouched.
   d. **Regenerate** both artifacts (compose through the converter; k8s ConfigMaps native) —
      generator green. The k8s manifests stop referencing `AUTH_MODE`, clearing Pulumi to
      drop it from `placeframe-secrets`.
2. **Slice A — storage on SeaweedFS + provider-neutral edge.** S3 resource outputs feed
   `S3_ENDPOINT_URL`/`S3_ACCESS_KEY`/`S3_SECRET_KEY` (fixes the MINIO_* bug); SeaweedFS
   compose provisioner (weed server + admin console + audit relay + s3-initializer/
   bucket-init, ported from the hand compose corpse); delete both MinIO provisioners and
   write the SeaweedFS k8s twin (StatefulSet + services, postgres-provisioner pattern); loki
   config retargets off `minio:9000`. Rename score resource type `placeframe-keycloak` →
   `oidc-issuer`. Sync the SaaS engineer (env contract + storage swap).
3. **Slice B — observability.** loki/alloy/grafana as provisioner services; configs
   bind-mounted from committed paths and inlined to `configs.content` at generation by the
   B2 converter — no publish-time conversion exists or is needed. Workload `files:` with
   `source:` is unusable here (generate-score renders workloads into a tempdir, so source
   paths dangle); committed-path configs ride as provisioner-emitted binds. initialize-loki
   chown sidecar.
4. **Slice C — long tail.** cloudbeaver, auth-initializer, ngrok, rathole-client.
5. **Slice D — GPU services.** reconstructor + localizer workload files; `gpus: all`,
   healthchecks, localizer network alias via patch templates; `service-port` resources for
   lease-server/localizer wiring. The GPU-shape decision lands here (recommendation:
   per-variant generated core — the service stays `reconstructor`, only image + device
   patch differ per variant).
6. **Seam generation + multi-artifact publish (B3+B4).** `generate-score` emits one compose
   per seam (subsetted workload lists per artifact); `publish-compose` publishes the five
   artifacts. Edge-anonymous is the gateway workload with its `files:` overridden out (a
   per-seam override file) plus no keycloak provisioner — that override *is* the "auth
   snippet presence" difference between the edges. `publish-compose` loses its config
   inlining (artifacts are born hermetic); env-stubbing, digest-pinning, and the publish
   call survive.
7. **Cutover.** `lifecycle.files` → generated files; delete the hand compose files;
   Make-it-Sing re-pins to `core-cuda` + `edge-keycloak` + `tunnel-rathole`;
   `.env.sample` drops `COMPOSE_PROFILES`; `uv run up` UX unchanged; re-think preflight's
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
- score-compose's files→binds materialization is bridged only by the docker-devkit
  converter (work item 1a); score-k8s needs no bridge (native ConfigMaps).

## Open decisions

- GPU shape (per-variant generated core recommended).
- Regeneration cadence once generated compose is load-bearing (manual two-commit dance vs
  CI gate; the gate was disabled because every context SHA re-stales artifacts).
- docker-devkit coordination beyond the 1a converter: layout adoption (`deployfiles/`
  rename on its `rename-folders` branch), and pushing the `ensure_score_tools` dead-code
  fix upstream.
- Pin `alpine` (wait-for-resources gate) + the CNPG operand image before the tier is
  load-bearing.
- Linear ticket linkage for this plan (`linear` CLI unavailable in this sandbox).
