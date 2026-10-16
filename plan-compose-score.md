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
  MinIO provisioners existed only because loki's config once hardcoded `minio:9000`; loki
  now addresses `seaweedfs:8333` and the score `s3` provisioner stands up SeaweedFS at the
  fixed names `seaweedfs`/`seaweedfs-audit` (the entrypoint wrapper's rendered fluent sink
  and loki's config reach them by DNS name).
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
  versions). `ensure_score_tools` (revived, extended to fetch a pinned helm) makes the
  tools appear on a fresh machine/CI runner; until its release they are hand-fetched onto
  PATH.
- Generation resolves image SHAs from the **committed** tree: commit sources, regenerate,
  commit artifacts.
- **Infra authoring layers by category** (decided post-cleanup, gates Slice B): score
  stays the workload tier; stateful infra goes operator-first (postgres via CNPG at
  promotion time, keycloak via its official operator at the edge work item); third-party
  stamp-outs go Helm charts rendered by `helm template` inside docker-devkit's
  generate-score — helm is a renderer, never a deployer. Everything renders at generation
  into the committed deterministic `manifests.yaml`; Argo never knows helm exists.
  Operators are cluster preconditions installed by the Pulumi/infra layer (same class as
  the Hetzner CSI driver); their CRs are ordinary manifest content. Kustomize is
  permanently out — variation is already handled by generation (env holes, `--local`,
  storage classes). Charts follow the image laws: digest-pinned, mirrored to the org
  namespace. Chart values never carry secrets — charts reference existing Secrets
  (`placeframe-secrets` pattern).
- **GPU shape: per-variant generated core.** The service stays `reconstructor`; each
  variant generation substitutes the variant image + device patch, producing
  `placeframe-core-cuda` / `placeframe-core-rocm`. Accelerator choice is which artifact a
  consumer includes — never a runtime switch (same model as the edge pair).

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
- **Slice A shipped (work item 2)**: `api.yaml` feeds `S3_ENDPOINT_URL`/`S3_ACCESS_KEY`/
  `S3_SECRET_KEY` from the s3 resource (the MINIO_* defect is gone). Both MinIO
  provisioners deleted, replaced by `compose/seaweedfs.yaml` (weed
  server + admin console + audit relay + s3-initializer, ported from the hand compose
  corpse; credentials as `${S3_*:?err}` holes) and the k8s twin
  `k8s/seaweedfs.yaml` (Service + StatefulSet, audit relay
  Deployment + Service, s3-initializer bucket Job with `S3_*` secretKeyRefs; no admin
  console — k8s publishes no host ports). Score resource type `placeframe-keycloak` →
  `oidc-issuer` (the api
  resource id stays `placeframe-keycloak` — an id names the instance, not the
  implementation). Artifacts regenerated through the released converter: zero minio
  references, zero binds, deterministic across fresh runs. Loki's config was already on
  `seaweedfs:8333`; the generated tier now matches it via the provisioner endpoint.
- **docker-devkit re-pinned to 0.4.6** (the chart-render release; first `uv lock
  --upgrade-package docker-devkit` resolved 0.4.5 from a not-modified cached simple-index —
  `uv cache clean docker-devkit` fixed it). Both artifacts regenerated byte-identical
  through the released pin, as predicted; the lock bump does not feed service image globs,
  so no tree-tag movement and no artifacts commit. Per-service pylocks unaffected.
- **Slice B shipped (compose half + all k8s authoring)**: `compose/observability.yaml`
  (loki/alloy/grafana + initialize-loki chown sidecar, config binds of the committed
  `workloads/*/config.*` inlined `$`-doubled by the converter, `${LOKI_IMAGE:?err}`-style
  runtime holes, loki-data volume), `k8s/observability.yaml` (alloy Deployment + Service +
  ConfigMap; loki/grafana arrive via charts), workload wiring (`observability` resource
  type, id `placeframe-observability`, declared by api + lease-server feeding
  `loki_url`/`otlp_endpoint`), and the alpine pin
  (`compose/wait-for-resources-image.tpl` patch template → `${ALPINE_IMAGE:?err}`;
  ALPINE_IMAGE was already declared/locked). Compose artifact regenerated: deterministic
  across fresh runs, zero binds, `docker compose config`-valid, preflight exit 0.
- **Slice B deviations from the anticipated shape**: the grafana chart's newest release
  (10.5.15) is flagged deprecated, so the pin is **10.5.14**
  (`sha256:161aa072…0764e`) — the last non-deprecated; loki is the planned 7.3.0
  (`sha256:ba8b6b3e…d2f8`). **Alloy's chart has no OCI artifact** (ghcr.io/grafana/alloy
  and ghcr.io/grafana/helm-charts/alloy both "repository not known") — ChartConfig requires
  digest-pinned OCI refs, so alloy's k8s half is hand-written (the seaweedfs twin pattern)
  with a ConfigMap body mirroring `workloads/alloy/config.alloy` by hand (drift risk noted
  in stack/AGENTS.md). Loki chart gotchas folded into `values/loki.yaml`: singleBinary
  reads its own `extraArgs`/`extraEnvFrom` (not global — only the distributed templates
  concat global), `-config.expand-env=true` + `extraEnvFrom: placeframe-secrets` carries the
  S3 credentials as `${S3_*}` config holes (the chart's sanctioned pattern), and
  SimpleScalable targets must be zeroed or chart validation fails. Test pods, canary,
  gateway, memcached caches, and the rules sidecar all disabled in values; every rendered
  image lands as a mirror digest. Grafana k8s gets admin creds from `placeframe-secrets`
  (**new keys `GRAFANA_ADMIN_USER`/`GRAFANA_ADMIN_PASSWORD`** — k3d recipe and the Pulumi
  list updated) and no anonymous access, unlike the compose dev stack.
- **k8s artifact regeneration is pending the CI mirror job**: `helm template` pulls the
  org-mirrored form of each chart ref, and the mirror job has not copied loki/grafana yet
  (declare → mirror job → generate; single-writer law — no local mirror push from the
  sandbox). Values were validated against upstream refs directly (rendered output audited:
  Services `loki:3100`/`grafana:3000` match the gateway Caddyfile; single mirror-digest
  image per chart). After the operator pushes and the mirror job runs, `uv run
  generate-score --target k8s` unblocks; the k8s artifact is stale in the interim (expected
  mid-initiative).
- Resumption facts: the pinned score tools, helm v3.22.1, and the repo-pinned uv 0.12.15
  all live in `~/.local/bin`, which is not on the sandbox's default PATH
  (`export PATH="$HOME/.local/bin:$PATH"`; the system uv 0.11.14 cannot read the lock).
  Regeneration is plain `uv run generate-score` from the placeframe root and is deterministic
  across fresh runs; commit sources first, then regenerate, then commit artifacts. The
  branch's commits are unpushed until the operator pushes (sandbox has no push scope);
  hand off branch + HEAD at each session end. At this session's close: placeframe
  `more-final-polish` is 11 commits ahead of origin (the prior 9 plus the
  authoring-format plan record and this update; the working tree also holds the
  uncommitted provisioner migration). Operator pushes needed at close: placeframe
  `more-final-polish` (unblocks the CI mirror job for the two charts → k8s regen) and
  docker-devkit `dev` + the 0.4.7 patch release (the authoring-format code is already on
  `dev`, validated — see the record above).   The sandbox cannot fetch docker-devkit over its SSH remote —
  the bind-mounted checkout's refs are the truth (currently synced at `ea8b55f`, 2 commits
  ahead of origin/dev: the authoring-format code + docs, awaiting push + 0.4.7 release).
  Placeframe's working tree additionally holds the 10 migrated provisioner files
  (uncommitted by design — see the authoring-format record; they commit with the 0.4.7
  re-pin).

- **Next session, in order**:
  1. ~~docker-devkit provisioner authoring format~~ **done** (see the record above; `dev`
     is 2 commits ahead, hand off for push + the 0.4.7 release).
  2. **Re-pin + commit the migration**: once 0.4.7 lands, `uv cache clean docker-devkit`
     then `uv lock --upgrade-package docker-devkit` (per-service pylocks expected
     unaffected), re-run `uv run generate-score --target compose` against the already
     migrated working tree (confirm zero diff again through the released pin), then
     commit sources + lock. Consider whether `requires` should move to `>=0.4.7` in the
     same commit (0.4.6 fails loudly on mapping-form sources, so the loose range is safe
     but noisy). stack/AGENTS.md gains the authored-format facts (mapping form is the
     authoring law; string form is compiler output) with that commit.
  3. **Regenerate the k8s artifact** (needs the operator's placeframe push from the prior
     session's close + the mirror job having copied the two charts). `uv run
     generate-score --target k8s`, inspect the merged manifests (chart docs sorted beside
     the score docs; alloy twin present; no unpinned/unmirrored images), commit. This is
     also the first full exercise of the k8s authored provisioners (compose byte-identity
     is proven; k8s has compile round-trips only). Riding the 0.4.7 pin means one devkit
     version in play; pre-existing k8s content (postgres/seaweedfs/gateway/api) should
     reproduce identically, with the chart + observability additions on top.
  4. **Slice C (work item 4, long tail)**: cloudbeaver, auth-initializer, ngrok,
      rathole-client.
- **Cleanup pass shipped (between Slices A and B)**: provisioners reorganised into
  `stack/score/compose/` + `stack/score/k8s/` with truncated names (`compose/seaweedfs.yaml`
  etc.; registration lists in `docker-devkit.yaml` are the authority — score tooling imposes
  no file-naming requirements on authored sources). `AUTH_JWKS_URL` fixed from a baked
  keycloak literal to a passthrough in both renderings (the api's `check_auth_config` boots
  anonymous mode only when issuer and endpoints are all empty — the baked URL crashed
  anonymous boots). Vestigial efs mounts and all restart keys dropped; CNPG Jobs got Argo
  sync hooks; the k8s seaweedfs StatefulSet got a readiness probe mirroring the compose
  healthcheck; `restart-policy.tpl` deleted. `stack/score/README.md` replaced by
  `stack/AGENTS.md` + `CLAUDE.md` import. Pending: docker-devkit's `image_globs` went
  recursive (dev @ 90aad4d, unpushed) so preflight's unpinned-image scan covers the moved
  files — re-pin (`uv lock --upgrade-package docker-devkit`) once released.
- **Pulumi follow-up — deferred until the rest of this plan completes** (external):
  `placeframe-secrets` gains `AUTH_ISSUER_URL` + `AUTH_JWKS_URL` +
  `AUTH_AUTHORIZATION_ENDPOINT`/`AUTH_TOKEN_ENDPOINT` + `S3_ACCESS_KEY`/`S3_SECRET_KEY` +
  `GRAFANA_ADMIN_USER`/`GRAFANA_ADMIN_PASSWORD` (the k8s grafana chart reads its admin
  credentials from the Secret), and drops `AUTH_URL`/`AUTH_TOKEN_URL`, `MINIO_ACCESS_KEY`/`MINIO_SECRET_KEY`, and (already
  safe — the generated manifests no longer reference it) `AUTH_MODE`. The dev-stack Pulumi
  config keys feeding `pf-secrets` (e.g. `placeframe:minioSecretKey`) rename to their `s3*`
  spellings in the same pass — the camelCase→SNAKE mapping in `secrets_exec.py` then
  yields the S3_* env names the stack now reads. The SaaS engineer sync for Slice A is
  this secret-key contract plus the storage swap (SeaweedFS StatefulSet + audit relay +
  bucket Job in the manifests, api env MINIO_*→S3_*) — surfaced here; the manifests
  themselves are already regenerated. Findings from his `placeframe-pulumi` branch
  (checked 2026-10, may be stale): his `placeframe-secrets` block predates Slice A
  entirely (still MINIO_*/AUTH_MODE/AUTH_URL); his Argo Application points at
  `score/deploy` on placeframe `main` — a path that exists nowhere (his "score-split"
  hasn't landed; this branch carries `stack/generated/k8s/manifests.yaml`) — so the Argo
  source path needs reconciling at merge; his `reconstructor.py` hardcodes the
  StatefulSet DNS name `pf-postgres`. **k8s postgres stays the StatefulSet provisioner
  until the CNPG package is agreed with him.** CNPG promotion prerequisites when that
  happens: slim `k8s/postgres-cnpg.yaml` (its minted passwords break determinism and
  commit secret values into emitted manifests — latent while unregistered), host +
  digest-pin the `14-trusted` operand image (operator action; CI token cannot push to
  the placeframe ghcr namespace), operator install in Pulumi, `pf-postgres` →
  `pf-postgres-rw` DNS sync in `reconstructor.py`, and a PG-14-vs-compose-tier
  major-skew check.
- **Generated-compose smoke test passed (both auth modes, first runtime validation)**:
  anonymous boots `auth_mode:"disabled"`, OIDC boots `auth_mode:"keycloak"` with
  unauthenticated `/capture_sessions` → 401 (the `AUTH_JWKS_URL` passthrough holds at
  runtime); gateway proxies the api (`/schema` 200) and `/auth/*` → keycloak (302); all
  one-shots (create/migrate/initialize-s3/wait-for-resources) exit 0. The token flow is
  unexercisable — auth-initializer (realm import) is Slice C, so keycloak has no
  `placeframe-dev` realm. Smoke fixes shipped: stack/AGENTS.md swagger URL corrected
  (`/schema`, not `/schema/swagger`) and the image prerequisite documented (fresh
  `tree-<sha>` tags must exist before `up` — api/gateway were unbuilt; `uv run build -t
  api -t gateway --gpu none`). Teardown side effect: `down --remove-orphans` also removes
  the hand `compose.postgres.yml` postgres (shared project name `placeframe`; its data
  volume survives). Keycloak admin/admin creds in the compose provisioner match the hand
  stack's posture — not a defect.
- **docker-devkit chart-render step implemented (next item 1 done, awaiting release)**: `dev`
  @ `01b0565` (code `8a77a61` + AGENTS.md docs), unpushed. `ScoreConfig` gains `charts:`
  (digest-pinned upstream-native OCI refs, parse-time validated; unique names;
  per-chart values files + optional namespace) and `helm_version` (required with
  charts); `generate-score --target k8s` runs `helm template` against the
  **org-mirrored** form of each ref (mirror section required — no mirror, no charts)
  and merges the blocks into the same kind/namespace/name-sorted `manifests.yaml`.
  Tool pinning flows through one shared policy: `tool_requirements(config, target)`
  (public, `ToolRequirement` descriptors carrying binary/version/release/archive/
  extract) feeds both the loud PATH gate inlined at the top of the `generate-score`
  CLI and `ensure_score_tools(config, bin_dir, target="both")` (fetches pinned
  helm beside the score tools; nested `linux-amd64/` member, strip-components).
  The `mirror` verb now copies chart declarations too (crane copies OCI charts
  byte-identically — the CI mirror job populates them, single-writer law intact).
  Smoke-verified end-to-end with helm v3.22.1: digest-pinned
  `oci://ghcr.io/grafana/helm-charts/loki@sha256:ba8b6b3ee954c9d6eeee713d148a22e6f73eb440189e11acd3112a06acdfd2f8`
  (tag 7.3.0) templates cleanly into `---\n# Source:` blocks, missing chart values
  (loki demands `storage.bucketNames` + schema config) fail loudly at generation.
  Helm current lines: v3.22.1 (v3 terminal) / v4.3.1 (v4 current) — Slice B pins
  explicitly; v3.22.1 is the smoke-verified one. Release handoff: operator pushes
  `dev` — now three commits ahead of origin/dev (code + docs + the operator's own
  `plan-image-identity.md` tree-tag audit, whose Part 1 defect is exactly the
  missing-`tree-<sha>`-tags failure the smoke test hit) — cuts the release, then
  `uv lock --upgrade-package docker-devkit` here (also closes preflight's scan gap
  over the moved provisioner files; re-run `uv run lock-python` if the workspace
  lock re-stales).
- **Provisioner authoring format — implemented on docker-devkit `dev`, migration validated
  in-tree** (designed prior session; built this session). docker-devkit `dev` carries two
  unpushed commits — `e11a790` (code: `provisioners.py` with `AuthoredProvisioner`,
  `extra="forbid"`, `state`/`outputs`/`volumes`/`services` as mappings, `manifests` as a
  list; the string-form law fires as per-field `mode="before"` validators, so pydantic
  wraps it into a loud `ValidationError`; `compiled_provisioners()` compiles into a
  per-run tempdir *under `score_dir`*, keeping `--provisioners` paths repo-relative;
  `ComposeDumper` moved there, imported back by the artifact dump; ~215 lines + ~250
  lines tests in `tests/test_provisioners.py`) and `ea8b55f` (AGENTS.md rows). Both
  renderings wrap init+generate in the compile; ruff + basedpyright strict + 165 tests
  green. Release handoff: operator pushes `dev` (now 2 ahead of origin/dev) and cuts
  **0.4.7** (additive). Placeframe's 10 registered provisioner files are **migrated to
  mapping form in the working tree, uncommitted** — running
  `uv run --with 'docker-devkit @ file:///workspace/docker-devkit' generate-score
  --target compose` through them reproduced the committed compose artifact with **zero
  diff** (the acceptance test), and no tempdir residue remains. They stay uncommitted
  until the 0.4.7 re-pin: committing them against the 0.4.6 lock would leave the branch
  unable to regenerate its own sources (0.4.6 has no compile step and fails loudly on
  mapping form). `k8s/postgres-cnpg.yaml` is deliberately left in string form — it is
  unregistered and carries an `init:` block, a field the authored format intentionally
  does not model; registering it would hit the loud format law and force that decision.
  The k8s authored files compile (round-trip verified) but get their first full exercise
  at the k8s regen (step 3 below).
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
3. **Slice B — observability.** Compose twins hand-written as provisioner services
   (loki/alloy/grafana — the `compose/seaweedfs.yaml` pattern: fixed DNS names,
   `${VAR:?err}` holes, healthchecks; configs as provisioner-emitted binds of the
   committed `workloads/*/config.*` paths, inlined `$`-doubled by the converter so loki's
   `-config.expand-env=true` still sees `${S3_ACCESS_KEY}` after compose interpolation;
   initialize-loki chown sidecar). The k8s half is the **first consumer of the
   docker-devkit chart-render step**: loki/alloy/grafana via the official Grafana charts,
   digest-pinned and mirrored; chart values reference existing Secrets, never carry them.
   Ride this regeneration with the alpine pin: a patch template sets the
   wait-for-resources gate image to a mirror digest, with `alpine` declared in
   `workloads/images.yml` so the mirror job picks it up.
4. **Slice C — long tail.** cloudbeaver, auth-initializer, ngrok, rathole-client.
5. **Slice D — GPU services.** reconstructor + localizer workload files; `gpus: all`,
   healthchecks, localizer network alias via patch templates; `service-port` resources for
   lease-server/localizer wiring. GPU shape settled (see Settled): per-variant generated
   core — the service stays `reconstructor`, only image + device patch differ per variant.
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

- Regeneration cadence once generated compose is load-bearing (work item 7): manual
  two-commit dance until cutover — the CI staleness gate stays off because every context
  SHA re-stales artifacts. Leaning for cutover: a CI bot that regenerates and
  auto-commits (canonical-message commits, the codegen-commit pattern).
