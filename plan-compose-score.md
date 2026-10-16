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
- **No drift linting: single-source or nothing.** A drift class inside this repo is closed
  structurally (one declaration; renderings derive from it or validate against it at
  compile) or left alone — never handled by a standing comparator over two hand-maintained
  copies. The only standing checks are "generation has not run" gates (codegen staleness;
  the cutover regen bot). Comparators survive only at true external boundaries, and even
  there the contract artifact is generated (the Pulumi secret sync reads the generated
  mint list). The pre-existing version-coupling check in preflight is the same species —
  eventually generate `images.yml`'s base-tag line from `pyproject.toml` rather than
  extend the pattern.

## Shipped

- **B1 auth-structural** (see Settled) and **B2**: the converter release, gateway entrypoint
  by file presence, auth snippets as workload `files:`, `AUTH_MODE` extinct in both
  renderings.
- **Slice A**: SeaweedFS both tiers, S3 resource outputs feeding `S3_*` api env, score
  resource type renamed `oidc-issuer`.
- **Slice B**: compose observability (loki/alloy/grafana + chown sidecar, lock-hole images)
  and all k8s observability authoring — loki + grafana via digest-pinned OCI charts, alloy
  hand-written k8s twin (no upstream OCI chart exists). Chart pins: loki 7.3.0; grafana
  **10.5.14** (10.5.15+ flagged deprecated). Chart-value gotchas live as comments in
  `values/loki.yaml` itself (singleBinary reads its own `extraArgs`/`extraEnvFrom`,
  expand-env S3 holes, SimpleScalable targets zeroed). Alpine pin via the
  `wait-for-resources-image.tpl` patch template.
- **Generated-compose smoke test** passed in both auth modes (anonymous boots `disabled`,
  OIDC boots `keycloak` with unauthenticated 401s; gateway proxies api + `/auth/*`; all
  one-shots exit 0). The token flow stays unexercisable until Slice C's auth-initializer
  (no realm exists yet).
- **Dedup audit (2026-10)**: gateway snippets, audit sink, env-var names, alpine pin —
  verified single-sourced and closed. The prior-art survey's verdict lives under Open
  decisions.
- **Devkit 0.4.7** (PR #19 merged, released to PyPI, placeframe re-pinned in `c268b181`):
  authored mapping-form sources, `include:`/`include-yaml:` file inclusion, lock
  resolution, and the secrets contract — the mechanisms these rely on are described under
  Current state and exercised by items 1–3.
- **Items 1–4 (2026-10-16, `a0f20a27` + `1fcc43d1` + `f1848f6f`)**: the working-tree
  migration committed as one unit — mapping-form sources, include edits, lock refs
  (keycloak/alloy/fluent-bit `lock:`, loki/grafana values `lock-image:`, grafana with
  `digest_field: sha`), the secrets declaration + `secrets:` section + mint artifact,
  `requires: ">=0.4.7"`, and the rider edits. The compose regen reproduced the dev-checkout
  output with exactly the three known riders (api tree-sha, keycloak hole,
  config-sourced `DEPLOYMENT_ENVIRONMENT`) — no pin-induced output drift. Loki
  single-source shipped via the `structuredConfig` full-override (`loki.config: ""` +
  `include-yaml: workloads/loki/config.yaml`), not the plan's `loki.config` string route:
  the chart's `validate.yaml` demands a structured `schema_config` the string form cannot
  satisfy, and `calculatedConfig` merge-overlays onto the blanked base, so the rendered
  config equals the committed file semantically (chart scaffolding leaks nothing; comments
  drop in the round-trip). The k8s artifact regenerated and committed — chart docs sorted
  in, rendered loki config/alloy bytes/datasources verified against their sources, every
  lock-resolved digest byte-equal to `images.lock`, and the artifact carries zero
  hand-written digests. stack/AGENTS.md records the authoring law + mint-list pointer.

## Current state

- **Branches**: placeframe `more-final-polish`, local HEAD `f1848f6f` (three commits atop
  the pushed `e8421705`: the sources commit, the k8s artifact commit, the stack-doc prose
  commit — unpushed, ride the next operator hand-off; re-check `git log @{upstream}..HEAD`
  at session start). PR #143 (`More final polish`) is open against `dev` with a fully green
  Integrate run; landing is operator-owned (the `ready-to-merge` label, bors model). The
  GitHub remote is `outernet-foundation/plerion` (repo renamed; redirects cover old URLs).
  docker-devkit `dev` is merged and pushed; 0.4.7 is on PyPI and placeframe is re-pinned
  to it. Working tree is clean (`.placeframe/` logs are inert untracked runtime output).
- **Authoring format (0.4.7, the pinned devkit)**: sources are mapping-form YAML; markers
  are single-key plain-YAML mappings (lintability law): `include: <repo-root-relative
  path>` inserts file bytes verbatim; `include-yaml: <path>` parses and inserts structure
  (grafana's chart renders datasources through `tpl (toYaml $value)` and mangles strings;
  alloy's river config and loki's full-override need structure too — see Shipped for the
  structuredConfig route). Neither mode transforms content (`${S3_*}` holes survive; `$`
  handling stays per-consumer). Lock markers are single-key mappings resolved against the
  manifest's `.lock` pair — `lock: NAME` substitutes the full reference (k8s provisioners
  have no runtime env-file, so the lock is their single digest source), `lock-image: NAME`
  expands into registry/repository/tag/digest chart fields (`digest_field: sha` for
  grafana's bare-hex spelling). The secrets contract validates each rendering's consumed
  keys are a subset of the authored declaration — compose `${ALL_CAPS}` holes with
  `$`-parity (escaped configs.content doesn't count), k8s `secretKeyRef` entries naming
  the configured Secret — and writes the mint list artifact from the declaration alone.
- **Artifact staleness**: both artifacts are current as of `1fcc43d1` (compose regenerated
  with the three riders, k8s with charts + observability). Future source commits that
  touch a service's build context re-stale the tree-sha tags until the next deliberate
  regen, as always. Standing gotcha: the image/chart mirror runs only inside Integrate,
  which triggers on PRs to `dev` — a bare branch push never runs it, so a newly declared
  mirror waits for the next PR. The audit's two preflight guards were dropped under the
  no-linting law (Settled): the digest-equality guard is obsoleted by the devkit's lock-resolution, and
  the secrets-contract guard is replaced by the secrets declaration.
- **Resumption mechanics**: the pinned score tools, helm, and the repo-pinned uv live in
  `~/.local/bin`, not on the sandbox's default PATH (`export PATH="$HOME/.local/bin:$PATH"`;
  system uv can't read the lock). Post-re-pin, generation runs natively from the repo root:
   `uv run generate-score --target compose|k8s` — the interim dev-checkout invocation
   (`--project /workspace/docker-devkit`) is obsolete. The lifecycle verbs (`uv run
   up`/`down`/`build`) work natively against the 0.4.7 pin, secrets section included.
   Regeneration is deterministic across fresh runs; the order is commit
  sources → regenerate → commit artifacts. (uv once served a stale cached simple-index on a
  re-pin — `uv cache clean docker-devkit` before any future `uv lock --upgrade-package`.)
  The sandbox has no push scope — commit locally and hand off branch + HEAD at session end.
  docker-devkit is read via the `/workspace` bind mount (fetching its SSH remote fails).
- **Pulumi follow-up — deferred until this plan completes** (external, with the SaaS
  engineer): conform `placeframe-secrets` to the generated mint list
  `stack/generated/secrets.txt` (the mint list is the documented contract; drops are
  `AUTH_MODE`, `AUTH_URL`/`AUTH_TOKEN_URL`,
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

1. **Bucket contract** (after the naming decision below; order-flexible against 2). Flow
   the captures bucket through the s3 resource (`CAPTURES_BUCKET` output → api env),
   deleting the hardcoded `dev-captures` in `capture_sessions.py` — bucket naming becomes a
   provisioner-level fact as `reconstructions_bucket` already is. Apply the decision
   uniformly across both provisioners; record the bucket set in stack/AGENTS.md as
   load-bearing names beside the DNS list.
2. **Slice C — long tail.** cloudbeaver, auth-initializer, ngrok, rathole-client. Keycloak's
   k8s half renders via its official operator (Settled: operator-first for stateful infra).
   Riders from the audit: keycloak session/lifespan constants (`3600`/`2592000`, currently
   k8s-hardcoded and mirrored in `.env.sample` + the realm export) route through the config
   provisioner / `placeframe-secrets` — no third copy; both oidc provisioners use
   `{{ .State.realm }}` where the literal `placeframe-dev` appears, and the realm joins the
   load-bearing constants in stack/AGENTS.md.
3. **Slice D — GPU services.** reconstructor + localizer workload files; `gpus: all`,
   healthchecks, localizer network alias via patch templates; `service-port` resources for
   lease-server/localizer wiring. Per-variant generated core (Settled). Riders from the
   audit: build the healthcheck patch-template class for workload services — the plan's
   stated mechanism ("score-compose validates probes and ignores them → patch templates
   emit healthchecks") is unimplemented and the generated compose gates nothing on workload
   health today (score-compose silently drops the api/lease-server livenessProbes);
   `SERVICE_VERSION` envs carrying the tree-sha tags (OTel `service.version` vanishes in
   the generated stack today); `LOCALIZER_CONTAINER_URL` baked `localhost:8000` →
   `localizer:8000` once the alias exists.
4. **Seam generation + multi-artifact publish (B3+B4).** `generate-score` emits one compose
   per seam (subsetted workload lists per artifact); `publish-compose` publishes the five
   artifacts. Edge-anonymous is the gateway workload with its `files:` overridden out (a
   per-seam override file) plus no keycloak provisioner — that override *is* the "auth
   snippet presence" difference between the edges. `publish-compose` loses its config
   inlining (artifacts are born hermetic); env-stubbing, digest-pinning, and the publish
   call survive.
5. **Cutover.** `lifecycle.files` → generated files; delete the hand compose files;
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

- **Regeneration cadence** once generated compose is load-bearing (item 5): manual
  two-commit dance until cutover — the CI staleness gate stays off because every context
  SHA re-stales artifacts. Leaning for cutover: a CI bot that regenerates and auto-commits
  (canonical-message commits, the codegen-commit pattern).
- **Bucket naming** (decide before item 1): `dev-` prefix everywhere or nowhere. Today's
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
