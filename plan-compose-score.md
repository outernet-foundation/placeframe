# Compose → score initiative plan

The end state: no hand-authored compose files — the stack is score-generated in
`stack/generated/compose`, decomposed into five published OCI artifacts, and consumers
assemble their own backend by `include:`-ing artifacts instead of flipping
`COMPOSE_PROFILES`/`AUTH_MODE` switches. The k8s manifests (SaaS/Pulumi tier) are the second
rendering of the same score sources and ride along.

## Settled — do not re-litigate

- **Auth is structural.** `AUTH_ISSUER_URL` presence selects OIDC vs anonymous inside the api
  (B1, shipped). Issuer set requires `AUTH_JWKS_URL`/`AUTH_AUTHORIZATION_ENDPOINT`/
  `AUTH_TOKEN_ENDPOINT` (explicit — split-horizon kills discovery; no derivation); issuer +
  cleartext `http://` PUBLIC_URL is a boot error. `/server-info`'s `auth_mode` wire values
  unchanged.
- **Object storage is SeaweedFS everywhere.** MinIO is dead in both tiers. The score `s3`
  provisioner stands up SeaweedFS at the fixed names `seaweedfs`/`seaweedfs-audit` (the
  entrypoint wrapper's rendered fluent sink and loki's config reach them by DNS name).
- **The hand compose files are dead since the converter shipped.** No work item spends effort
  keeping them coherent; intermediate breakage is accepted, not repaired. The files stay on
  disk only as porting references for the slices and are formally deleted at cutover. This
  initiative is one unified project, not a compatibility bridge.
- **Generated compose is hermetic at rest: zero host-filesystem references.** score-compose
  materializes workload `files:` as bind mounts into its gitignored `.score-compose` state
  dir — its model is generate-and-run-here, incompatible with committed/published artifacts.
  The bridge is a docker-devkit `generate-score` post-pass that rewrites every bind into a
  top-level `configs.content` entry, doubling each `$` (compose interpolation would otherwise
  eat both loki's `${VAR}` and caddy's `{$VAR}` before the container sees them). A bind
  surviving in a generated compose is an artifact bug. Patch templates cannot host this
  conversion (no disk access; `.Workloads` carries literal content only).
- **Auth snippets ride as score workload `files:` with literal content in `gateway.yaml`** —
  one source for both renderings: score-k8s emits ConfigMap+mounts natively; score-compose's
  bind output feeds the generation converter.
- Score tools pinned: score-compose 0.42.0, score-k8s 0.15.0, helm 3.22.1 (output differs
  across versions). `ensure_score_tools` fetches the pinned set onto a fresh machine/CI
  runner (shipped in the 0.4.6 release; placeframe re-pinned).
- **Infra authoring layers by category**: score stays the workload tier; stateful infra goes
  operator-first (postgres via CNPG at promotion time, keycloak via its official operator
  when its k8s edge lands — Slice C); third-party stamp-outs go Helm charts rendered by
  `helm template` inside docker-devkit's generate-score — helm is a renderer, never a
  deployer. Everything renders at generation into the committed deterministic
  `manifests.yaml`; Argo never knows helm exists. Operators are cluster preconditions
  installed by the Pulumi/infra layer (same class as the Hetzner CSI driver); their CRs are
  ordinary manifest content. Kustomize is permanently out — variation is already handled by
  generation (env holes, `--local`, storage classes). Charts follow the image laws:
  digest-pinned, mirrored to the org namespace. Chart values never carry secrets — charts
  reference existing Secrets (`placeframe-secrets` pattern).
- **GPU shape: per-variant generated core.** The service stays `reconstructor`; each
  variant generation substitutes the variant image + device patch, producing
  `placeframe-core-cuda` / `placeframe-core-rocm`. Accelerator choice is which artifact a
  consumer includes — never a runtime switch (same model as the edge pair).
- **Deliberate provisioner pair-variance (won't close by design):** `${VAR:?err}` holes vs
  `secretKeyRef` wiring, chart probes vs compose healthchecks, host ports (compose only),
  grafana auth modes (anonymous dev vs credentialed k8s), the CNPG alternative twin. These
  are the two renderings differing, not drift — don't re-audit them.

## Shipped

- **B1 auth-structural** (see Settled) and **B2**: the converter release (docker-devkit 0.4.4,
  re-pinned through 0.4.6), gateway entrypoint by file presence, auth snippets as workload
  `files:`, `AUTH_MODE` extinct in both renderings.
- **Slice A**: SeaweedFS both tiers (compose provisioner + k8s twin, both MinIO provisioners
  deleted), S3 resource outputs feeding `S3_*` api env, score resource type renamed
  `oidc-issuer`.
- **Slice B**: compose observability (loki/alloy/grafana + chown sidecar, lock-hole images)
  and all k8s observability authoring — loki + grafana via digest-pinned OCI charts, alloy
  hand-written k8s twin (no upstream OCI chart exists). Chart pins: loki 7.3.0; grafana
  **10.5.14** (10.5.15+ flagged deprecated). Chart-value gotchas live as comments in
  `values/loki.yaml` itself (singleBinary reads its own `extraArgs`/`extraEnvFrom`,
  expand-env S3 holes, SimpleScalable targets zeroed). Alpine pin via the
  `wait-for-resources-image.tpl` patch template.
- **Cleanup pass**: provisioners reorganised under `stack/score/{compose,k8s}/` with
  truncated names; `AUTH_JWKS_URL` passthrough fix; vestigial mounts and restart keys
  dropped; `stack/AGENTS.md` + `CLAUDE.md` replaced the tier README. The recursive
  image-glob scan (devkit PR #17) shipped in the 0.4.6 pin — nothing pending there.
- **Generated-compose smoke test** passed in both auth modes (anonymous boots `disabled`,
  OIDC boots `keycloak` with unauthenticated 401s; gateway proxies api + `/auth/*`; all
  one-shots exit 0). The token flow stays unexercisable until Slice C's auth-initializer
  (no realm exists yet).
- **Dedup audit residue** (2026-10): verified single-sourced and closed — gateway snippets,
  audit sink, env-var names, alpine pin. Every structurally correct closure is absorbed into
  the remaining items below; the prior-art survey's verdict lives under Open decisions.

## Current state

- **Branches**: placeframe `more-final-polish` — the operator pushed through `90abbf8f`
  (2026-10-15); unpushed = the two prior-session plan records plus this session's audit
  commits (check `git status` / `git log @{upstream}..HEAD` at session start — this file's
  counts go stale the moment work lands). docker-devkit `dev` @ `7d974c6` is 4 commits
  ahead of origin/dev (provisioner authoring format + file inclusion, each code+docs) —
  **no devkit push until item 1's lock-resolution joins them**; one patch release (0.4.7)
  carries all three features, unblocking the placeframe re-pin (item 3).
- **Working tree, uncommitted by design** (commits at item 3): the 10 registered provisioner
  files migrated to mapping form (zero-diff acceptance passed through the dev checkout);
  `k8s/observability.yaml`'s alloy ConfigMap body → `include:` marker;
  `k8s/values/grafana.yaml`'s datasources → `include-yaml:` marker;
  `compose/oidc-issuer.yaml` keycloak image → `${KEYCLOAK_IMAGE:?err}` (compose side now
  carries zero digests); `| default "hcloud-volumes"` fallbacks dropped from k8s
  postgres/seaweedfs `storageClassName` (generate-score always exports
  `SCORE_STORAGE_CLASS`; a silent default only masks a misconfigured direct score-k8s run).
- **Audit-hardening mechanical half shipped** (this session, three commits): mint-recipe
  `AUTH_AUDIENCE` fix; dead `BUCKET` constant deleted; lease-server `DEPLOYMENT_ENVIRONMENT`
  sourced from the config resource. These knowingly re-stale the compose artifact's
  api/lease-server tree-shas — accepted; regen rides item 3. The two preflight guards are
  **not** built — halted mid-build, decision under Open decisions.
- **k8s artifact regeneration gates**: the placeframe push has landed, but as of this
  session the CI mirror job has **not** copied the loki/grafana charts (registry-verified
  absent) — check whether the mirror run succeeded before item 4. Item 3's re-pin is the
  other gate (k8s sources will carry lock refs). The k8s artifact is stale in the interim
  (expected mid-initiative).
- **docker-devkit file inclusion + authored format** (rides 0.4.7, implemented + validated):
  markers are single-key plain-YAML mappings (lintability law): `include: <repo-root-relative
  path>` inserts file bytes verbatim; `include-yaml: <path>` parses and inserts structure
  (grafana's chart renders datasources through `tpl (toYaml $value)` and mangles strings;
  alloy's river config and loki's eventual full-override need bytes). Neither mode transforms
  content (`${S3_*}` holes survive; `$` handling stays per-consumer). Consumers: the compile
  pre-pass (mapping-form sources compile to score's string form in a per-run tempdir) and
  the chart-values pre-pass (marker-bearing values resolve to a tempdir copy for
  `helm template`). Known devkit debt: the inliner and uid-normalisation carry only
  volume-model typing tests.
- **Resumption mechanics**: the pinned score tools, helm, and the repo-pinned uv 0.12.15
  live in `~/.local/bin`, not on the sandbox's default PATH (`export
  PATH="$HOME/.local/bin:$PATH"`; system uv can't read the lock). Regeneration is
  `uv run generate-score` from the placeframe root, deterministic across fresh runs; the
  order is commit sources → regenerate → commit artifacts. The sandbox has no push scope —
  hand off branch + HEAD at session end. docker-devkit is read via the `/workspace`
  bind mount (fetching its SSH remote fails).
- **Pulumi follow-up — deferred until this plan completes** (external, with the SaaS
  engineer): conform `placeframe-secrets` to the mint-recipe key list in stack/AGENTS.md
  (the recipe is the documented contract; drops are `AUTH_MODE`, `AUTH_URL`/`AUTH_TOKEN_URL`,
  `MINIO_ACCESS_KEY`/`MINIO_SECRET_KEY`), plus the Slice A storage swap (SeaweedFS
  StatefulSet + audit relay + bucket Job in the manifests, api env MINIO_*→S3_* — the
  manifests themselves are already regenerated). The dev-stack Pulumi config keys feeding
  `pf-secrets` (e.g. `placeframe:minioSecretKey`) rename to their `s3*` spellings in the
  same pass — the camelCase→SNAKE mapping in `secrets_exec.py` then yields the `S3_*` env
  names the stack reads. His `placeframe-pulumi` branch findings (checked 2026-10, may be
  stale): the secrets block predates Slice A; his Argo Application points at `score/deploy`
  on placeframe `main`, a path that exists nowhere — reconcile the Argo source path at
  merge. **k8s postgres stays the StatefulSet provisioner until the CNPG package is agreed.**
  CNPG promotion prerequisites when that happens: slim `k8s/postgres-cnpg.yaml` (its minted
  passwords break determinism and commit secret values), host + digest-pin the `14-trusted`
  operand image (operator action; CI token cannot push to the placeframe ghcr namespace),
  operator install in Pulumi, `pf-postgres` → `pf-postgres-rw` DNS sync in his
  `reconstructor.py`, a PG-14-vs-compose-tier major-skew check, and a Pulumi-side Argo sync.

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

## Work items (ordered, remaining)

1. **docker-devkit lock-resolution.** Design the marker shape (e.g. `lock://KEYCLOAK_IMAGE`),
   implement + test: provisioner manifests and the chart-values pre-pass both resolve
   authored image references against `workloads/images.lock` at generation (including values
   `image.sha`/`digest` fields), making the lock the single digest source for both
   renderings. AGENTS.md row. Commit on `dev` — folds into the pending 0.4.7 (authoring
   format + inclusion + lock-resolution: one push, one release, one re-pin).
2. **k8s lock-ref migration + loki single-source** (rides the working tree, commits at
   item 3): the five hand-written k8s digests (keycloak, alloy, fluent-bit, loki values,
   grafana values) → lock refs; `values/loki.yaml` switches to the chart's `loki.config`
   full-override sourcing `workloads/loki/config.yaml` via `include-yaml:`, deleting the
   structured translation (the last large hand-copy). If the full-override cannot compose
   with singleBinary + the scaffolding toggles: fall back to the structured values and add
   a semantic-diff preflight guard over the shared block instead.
3. **Re-pin + commit the migration.** Once 0.4.7 lands: `uv cache clean docker-devkit`
   then `uv lock --upgrade-package docker-devkit` (a stale cached simple-index once served
   0.4.5 for a 0.4.6 request — clean first; re-run `uv run lock-python` if the workspace
   lock re-stales; per-service pylocks expected unaffected). Re-run
   `uv run generate-score --target compose` against the already-migrated tree and confirm
   zero diff through the released pin. Commit sources + lock — one commit covering the
   mapping-form migration, the include edits, the lock refs, the loki values switch, and
   the working-tree rider edits (keycloak lock hole, dropped storage-class defaults); consider `requires: ">=0.4.7"` in the same commit (older devkits fail
   loudly on mapping-form sources, so the loose range is safe but noisy). Then, as its own
   prose commit, stack/AGENTS.md gains the authored-format facts (mapping form is the
   authoring law; string form is compiler output; k8s config content arrives via inclusion,
   not hand mirrors — delete the alloy drift-risk note).
4. **Regenerate the k8s artifact** (needs the CI mirror job having copied the two charts —
   verify before starting — plus item 3). `uv run generate-score --target k8s`, inspect the
   merged manifests, commit. Assertions: chart docs sorted beside the score docs; the
   rendered alloy ConfigMap equals `workloads/alloy/config.alloy`; grafana's datasources
   ConfigMap equals the committed datasources file; the rendered loki config semantically
   equals `workloads/loki/config.yaml` (full-override composed with singleBinary — else
   item 2's fallback); every lock-resolved digest equals its `images.lock` entry;
   pre-existing k8s content (postgres/seaweedfs/gateway/api) reproduces identically, with
   the chart + observability additions on top; no unpinned/unmirrored images.
5. **Bucket contract** (after the naming decision below; order-flexible against 6). Flow
   the captures bucket through the s3 resource (`CAPTURES_BUCKET` output → api env),
   deleting the hardcoded `dev-captures` in `capture_sessions.py` — bucket naming becomes a
   provisioner-level fact as `reconstructions_bucket` already is. Apply the decision
   uniformly across both provisioners; record the bucket set in stack/AGENTS.md as
   load-bearing names beside the DNS list.
6. **Slice C — long tail.** cloudbeaver, auth-initializer, ngrok, rathole-client. Keycloak's
   k8s half renders via its official operator (Settled: operator-first for stateful infra).
   Riders from the audit: keycloak session/lifespan constants (`3600`/`2592000`, currently
   k8s-hardcoded and mirrored in `.env.sample` + the realm export) route through the config
   provisioner / `placeframe-secrets` — no third copy; both oidc provisioners use
   `{{ .State.realm }}` where the literal `placeframe-dev` appears, and the realm joins the
   load-bearing constants in stack/AGENTS.md.
7. **Slice D — GPU services.** reconstructor + localizer workload files; `gpus: all`,
   healthchecks, localizer network alias via patch templates; `service-port` resources for
   lease-server/localizer wiring. Per-variant generated core (Settled). Riders from the
   audit: build the healthcheck patch-template class for workload services — the plan's
   stated mechanism ("score-compose validates probes and ignores them → patch templates
   emit healthchecks") is unimplemented and the generated compose gates nothing on workload
   health today (score-compose silently drops the api/lease-server livenessProbes);
   `SERVICE_VERSION` envs carrying the tree-sha tags (OTel `service.version` vanishes in
   the generated stack today); `LOCALIZER_CONTAINER_URL` baked `localhost:8000` →
   `localizer:8000` once the alias exists.
8. **Seam generation + multi-artifact publish (B3+B4).** `generate-score` emits one compose
   per seam (subsetted workload lists per artifact); `publish-compose` publishes the five
   artifacts. Edge-anonymous is the gateway workload with its `files:` overridden out (a
   per-seam override file) plus no keycloak provisioner — that override *is* the "auth
   snippet presence" difference between the edges. `publish-compose` loses its config
   inlining (artifacts are born hermetic); env-stubbing, digest-pinning, and the publish
   call survive.
9. **Cutover.** `lifecycle.files` → generated files; delete the hand compose files;
   Make-it-Sing re-pins to `core-cuda` + `edge-keycloak` + `tunnel-rathole` (its env
   renames go live here — it still includes the old published bundle by digest today);
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
  converter; score-k8s needs no bridge (native ConfigMaps).

## Open decisions

- **Preflight guards** (halted mid-build; decide alongside item 4). The 2026-10 audit
  prescribed two standing guards in `scripts/preflight.py`. The **digest-equality** guard
  (every literal `mirror/…@sha256:` ref under `stack/score/k8s/**` equals its
  `images.lock` entry, matched by upstream tag, including values `sha`/`digest` fields) is
  obsoleted by item 1: lock-resolution makes the lock the single digest source for k8s
  sources too, leaving no hand-written digest to drift. The **secrets-contract** guard
  (every `secretKeyRef` key in the k8s sources appears in the stack/AGENTS.md mint recipe)
  guards a permanent contract with one real prior failure (`AUTH_AUDIENCE` omitted →
  pod-failing `CreateContainerConfigError`) — but its source of truth is a markdown code
  block parsed by regex, so landing it makes the recipe load-bearing for CI and that fact
  must be recorded in stack/AGENTS.md. Options: land the secrets guard alone; land neither;
  land both as originally written.
- **Regeneration cadence** once generated compose is load-bearing (item 9): manual
  two-commit dance until cutover — the CI staleness gate stays off because every context
  SHA re-stales artifacts. Leaning for cutover: a CI bot that regenerates and auto-commits
  (canonical-message commits, the codegen-commit pattern).
- **Bucket naming** (decide before item 5): `dev-` prefix everywhere or nowhere. Today's
  state is the only wrong answer: k8s applies it to 1 of 3 buckets (`dev-captures` but
  `reconstructions`), compose to 2 of 3, and the api hardcodes `dev-captures` for both
  tiers. If dev- everywhere: change k8s seaweedfs state/outputs (`reconstructions` →
  `dev-reconstructions`) + regen k8s. If nowhere: change the compose provisioner + `.env`
  defaults + regen compose. Either answer completes the slice — the `CAPTURES_BUCKET` env
  flow makes whichever string chosen a provisioner-level fact afterward.
- **docker-devkit publishing** (post-initiative, decision-gated — the plan completes
  regardless; this decides follow-on work). The 2026-10 prior-art survey: parts are
  precedented (Score itself; Flux Mirror, Aug 2026, for org-mirroring; Compose Bridge for
  one-shot compose→k8s), but the integrated whole — committed, deterministic, hermetic dual
  compose+k8s rendering with lock-coupled mirror governance and fail-closed lifecycle — was
  found nowhere. If yes: de-org-ify first (config knobs for the placeframe-shaped paths and
  defaults; soft deps on bashrun/strictyaml/build-artifact-registry), frame it as "the
  determinism + governance layer for Score" (the spec community's active drift discussion
  is the entry point for proposing the determinism suite upstream), and put
  cosign/referrers mirror verification on the roadmap before Flux Mirror grows a
  consumer-side lifecycle. Known risks: Docker's first-party convergence (Compose
  Bridge/Kanvas, `--lock-image-digests`) eroding the value prop from below; the permanent
  treadmill of tracking score-compose/score-k8s output changes; niche ceiling
  (dual-runtime-from-one-source is a philosophy, not a majority practice).
