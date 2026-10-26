# Compose → score initiative plan

The end state: no hand-authored compose files — the stack is score-generated in
`stack/generated/compose`, decomposed into five published OCI artifacts, and consumers
assemble their own backend by `include:`-ing artifacts instead of flipping
`COMPOSE_PROFILES`/`AUTH_MODE` switches. The k8s manifests (SaaS/Pulumi tier) are the second
rendering of the same score sources and ride along. At cutover this plan completes its job:
whatever drift ledger residue remains migrates into `stack/AGENTS.md` and this file is
deleted — two permanent drift registries would themselves be drift.

## Settled — do not re-litigate

- **No drift linting: single-source or nothing.** A drift class is closed structurally
  (one declaration; renderings derive from it) or left alone — never a standing comparator
  over two hand-maintained copies. This law governs the ledger below.
- **Score tools pinned**: score-compose 0.42.0, score-k8s 0.15.0, helm 3.22.1. Output
  differs across versions; `ensure_score_tools` fetches the pinned set.
- **Infra authoring layers by category**: score stays the workload tier; stateful infra is
  operator-first (postgres via CNPG at promotion time, keycloak via its official
  operator); third-party stamp-outs are Helm charts rendered by `helm template` inside
  generate-score — helm is a renderer, never a deployer; Argo never knows helm exists.
  Kustomize is permanently out. Charts follow the image laws: digest-pinned, org-mirrored,
  values never carry secrets (they reference existing Secrets).
- **Generated compose is hermetic at rest**: zero host-filesystem references, zero secrets.
  The bind→`configs.content` conversion is the docker-devkit converter's job — patch
  templates cannot host it (no disk access). A bind surviving in a generated compose is an
  artifact bug.
- **The hand compose files are dead.** No work item keeps them coherent; intermediate
  breakage is accepted. They stay on disk as porting references only and are formally
  deleted at cutover.
- **The infra Pulumi tier keeps the cluster layer** (k3s, Cilium, hcloud CSI,
  cert-manager, Argo, the NVIDIA device plugin, cluster-autoscaler, the AWS/GCP/Nebius
  GPU-worker programs, DNS). The Ingress→`gateway:8443` edge stays Pulumi — its host is
  `PUBLIC_URL`, per-site and Secret-resident, un-committable in a deterministic artifact;
  it joins `placeframe-secrets` and the storage class in the "program provides, manifests
  depend on" set. The hand-rolled reconstructor + KEDA path (`program/reconstructor.py`)
  is Slice D's porting reference and dies from infra when the artifact carries the
  workload (TODO.md).
- **KEDA CRs are absorbed; the operator stays cluster tier.** The k8s rendering carries the
  reconstructor's ScaledObject + TriggerAuthentication — scale-to-zero on queued
  reconstructions (postgres trigger, 300 s cooldown), ported from the infra Pulumi prior
  art. The operator itself is cluster machinery — a cluster-wide reconciler, peer of the
  NVIDIA device plugin — and its permanent home is the infra Pulumi layer (the existing
  `install_keda` helm release, pinned 2.20.2). App artifacts declare CRs; the platform
  installs the reconciler: one operator serves every app on the cluster, two installs
  fight over the shared CRDs and metrics APIService, and KEDA publishes no OCI chart
  anyway (classic helm repo or GitHub-release YAML — neither rides the digest-pinned OCI
  mirror path). A vendored-bytes detour (committed release YAML spliced through a
  `vendored_manifests` devkit field) was reverted before that field ever shipped; the
  artifact's KEDA content is exactly the two CRs. Documented prerequisite: no operator →
  the reconstructor sits at `spec.replicas: 0` forever. No committed credentials — the
  TriggerAuthentication wires a `secretTargetRef` into
  `placeframe-secrets` (`DATABASE_ORCHESTRATION_USER_PASSWORD` is already on the mint list);
  host/port/dbname/user literals ride the provisioner state. `maxReplicaCount` bakes as a
  literal — per-cloud node caps stay in the ASG/MIG/CAS layer. Argo's selfHeal fights KEDA
  over `/spec/replicas` unless the Application carries `ignoreDifferences` — Application-side
  config, i.e. infra's (TODO.md).
- **GPU shape: per-variant generated core.** The service stays `reconstructor`; variant
  generation substitutes the variant image + device patch (`placeframe-core-cuda` /
  `-rocm`). Accelerator choice is which artifact a consumer includes — never a runtime
  switch.
- **Object storage is SeaweedFS everywhere**, at the fixed service names `seaweedfs`/
  `seaweedfs-audit` (baked-in references reach them by DNS name). MinIO is dead in both
  tiers.
- **Auth is structural.** `AUTH_ISSUER_URL` presence selects OIDC vs anonymous inside the
  api. Issuer set requires `AUTH_JWKS_URL`/`AUTH_AUTHORIZATION_ENDPOINT`/
  `AUTH_TOKEN_ENDPOINT` (explicit — split-horizon kills discovery; no derivation); issuer +
  cleartext `http://` PUBLIC_URL is a boot error. `/server-info`'s `auth_mode` wire values
  unchanged.
- **Auth snippets ride as score workload `files:`** in `gateway.yaml` — one source for both
  renderings; snippet presence *is* the auth-mode difference between the gateway artifacts.
- **auth-initializer is the post-boot admin-API realm configurator** (both tiers). The
  file-import path is dead: operator-managed pods carry no initContainers, and a
  KeycloakRealmImport CR cannot resolve holes. K8s keycloak state is ephemeral H2 until a
  db spec lands — realm (re)configuration is idempotent and users are dev-tier. The
  operator's `<cr>-service` DNS supplants the `keycloak` literal in k8s JWKS guidance.
  Full spec in `stack/AGENTS.md`.
- **Keycloak 26.8.1, official operator chart on k8s** (the chart exists only at 26.8.0+,
  experimental — operator and server versions align). Neither the chart nor the image is
  org-mirrored yet; both gate the k8s regen on the mirror job, and split landing (sources +
  compose artifact commit first, stale k8s accepted in between) is the pattern.
- **Test users are operator-opt-in config, not artifact content.** The configurator seeds
  the `SEED_TEST_USERS` pairs (`username:password`, comma-separated) after the realm sync —
  idempotent create-or-update; empty seeds nothing (compose `.env` soft passthrough, k8s
  mint-list key). A fresh 26.8.1 realm's default profile requires `firstName`, `lastName`,
  *and* `email` — all three are populated (`<username>@seed.invalid`) or the first direct
  grant fails. No `mint-user` verb; no `userProfileConfiguration` in the export — KC's
  profile defaults stay intact for real users.
- **The `placeframe-worker` client is dead** — nothing has signed worker JWTs since
  lease-auth retirement; the realm export and the api's `azp` branches carry no worker
  surface. Don't re-introduce one.
- **CloudBeaver stays out of placeframe** — removed rather than ported (barely used, more
  work than it was worth).

## Drift ledger

Status vocabulary: `OPEN-closable-now` (closes with a named work item), `OPEN-blocked`
(names the unblocking item), `BY-DESIGN` (terminal residue — deliberate divergence between
the renderings; not drift to close). Entries are scrubbed when their closure lands.

**Validated at generation (closed by construction):** workload→resource output wiring,
secret-key consumption ⊆ `secrets.yaml` declaration, lock-resolved digests, shared config
file bodies (`include:`/`include-yaml:` — one committed file feeds both renderings).

**OPEN-closable-now**:

- **Infra's Pulumi reconstructor workload** (`placeframe-pulumi` branch:
  `deploy_reconstructor` + `reconstructor-probe.yaml` + `EnableLocalNode.py` in
  `program/reconstructor.py`) — a second, stale copy of the workload (`MINIO_*` envs,
  `dev-captures` bucket, tree-pinned images). Closes with the TODO'd infra deletion;
  until then the SaaS cluster has two owners of the `reconstructor` Deployment name
  (Argo prune vs Pulumi). The operator half of that file (`install_keda`) is not drift —
  it is the operator's permanent home (Settled).

The founding set (workload healthchecks, `SERVICE_VERSION` envs, realm name, magic
uids) landed with the early slices; new drift found on later slices joins here if it
closes completely with what is ported at the time.

**OPEN-blocked**:

- **Provisioner semantic core** (env sets, command lines, job logic duplicated per
  resource pair) — structural closure means a shared resource-semantics authoring tier in
  docker-devkit (author each resource type once as data; per-platform emitters). Not
  gated on ports — gated on the docker-devkit publishing decision (Open decisions). With
  placeframe-only scope and five stable resource types, the pairwise edits are cheaper
  than the emitters; re-evaluate if publishing proceeds or resource types proliferate.

**BY-DESIGN** (terminal residue):

- `${VAR:?err}` env holes (compose) vs `secretKeyRef` wiring (k8s) — each tier's native
  secret mechanism.
- Chart probes (k8s observability) vs compose healthchecks.
- Host ports and the `seaweedfs-admin` service exist only in compose.
- Tunnels are compose-only (one artifact per relay, no profiles); k8s has no relay.
- Grafana auth modes: anonymous dev (compose) vs credentialed via existingSecret (k8s).
- Grafana root-URL spelling: `${PUBLIC_URL}`-composed vs request-derived placeholders —
  one semantic, two idioms.
- The CNPG alternative twin (`k8s/postgres-cnpg.yaml`, unregistered until promoted).
- `PGDATA` subdir and storage class/size literals exist only in the k8s StatefulSets.
- Ordering semantics: compose gates on health via depends_on; k8s rests on Argo Sync-hook
  weights (now explicit) plus job retry-idempotency — and the hook weights are inert
  under bare `kubectl apply`, by design.
- The Ingress/TLS edge exists only in Pulumi — `PUBLIC_URL` host, cert-manager issuer.
- KEDA scale-to-zero exists only on k8s; compose runs the reconstructor always-on.
- KEDA `maxReplicaCount` and the trigger SQL bake as literals; per-cloud node caps live
  in the ASG/MIG/CAS layer.
- Argo Application-level config (the KEDA replicas `ignoreDifferences`) lives in infra,
  not the artifact.
- The KEDA operator itself lives in the infra Pulumi layer; only its CRs ride the
  artifact.

## Work items (ordered)

1. **Seam generation + multi-artifact publish (B3+B4).** `generate-score` emits one
   compose per seam (subsetted workload lists per artifact); `publish-compose` publishes
   the six artifacts. Seams are compose-only: the k8s rendering stays one monolithic
   `manifests.yaml` — Argo applies it wholesale, and assembly-by-inclusion is a
   compose-consumer concept (the SaaS cluster picks nothing: cuda, keycloak, no relay).
   `gateway-open` is the gateway workload with its `files:` and
   `resources.auth` overridden out (a per-seam override file — the gateway's realm env
   hangs off the keycloak provisioner) plus no keycloak provisioner — that override *is*
   the auth-snippet presence difference between the gateway artifacts. `publish-compose` loses its
   config inlining (artifacts are born hermetic); env-stubbing, digest-pinning, and the
   publish call survive. The per-variant core landed with Slice D: `compose_output`
   carries `{gpu}`, workload images carry `${GPU_VARIANT}`, and the six-artifact set
   fans out as core-cuda/core-rocm + gateway-open/gateway-keycloak +
   tunnel-ngrok/tunnel-rathole — one artifact per relay, both first-class (Make-it-Sing is
   only one consumer), and no compose profile survives the split; the
   `tunnel-gate-exclusion.tpl` carve-out dies with the last profile-gated service.
 2. **Cutover.** `lifecycle.files` → generated files; delete the hand compose files;
    Make-it-Sing re-pins to `core-cuda` + `gateway-keycloak` + `tunnel-rathole` (its env
   renames go live here — it still includes the old published bundle by digest today);
   `.env.sample` drops `COMPOSE_PROFILES`; re-think preflight's `compose.postgres.yml`
   role. `compose.dev.yml` survives as the hand overlay on generated files, never
   published. Migrate the ledger residue into `stack/AGENTS.md` and delete this plan.

## Mechanics that shape execution

- **Regeneration order**: commit sources → regenerate → commit artifacts. Staleness between
  those commits is accepted; preflight does not gate it (every context SHA re-stales the
  tree-sha tags).
- Runtime `.env` holes survive only as provisioner outputs inserted verbatim — the
  `placeframe-config` provisioner is the passthrough valve, and the seam split's relay
  credentials ride the same pattern (`tunnel-config`, outputs-only). Score workload specs
  cannot carry `${VAR}` holes at all (score validates placeholders as dotted resource
  references), and resource refs are not substituted inside `command` args (score-compose
  `$$`-escapes them to compose literals) — the ngrok domain expands in-container through a
  `/bin/sh -c` wrapper instead.
- Generated workload services are named `<workload>-<container>` (`api-api`); patches must
  compute names, never hardcode.
- Cross-workload `depends_on` is not a score concept — the auto-built `wait-for-resources`
  gate replaces it; poll-retry absorbs ordering. The gate emits only where a provisioner
  carries services, so seams whose provisioners are outputs-only (gateway-open, tunnels)
  carry no gate at all.
- Seam tests: platform-variance → score file; docker-only detail → patch template;
  generation-time baking vs runtime `.env` hole → config provisioner. The seam split is
  locked by `scripts/tests/test_score_compose_generation.py` (six outputs, zero profiles,
  zero binds, auth-difference between the gateway artifacts, relay mechanics).

## Open decisions

- **Regeneration cadence** once generated compose is load-bearing (item 2): manual
  two-commit dance until cutover — the CI staleness gate stays off because every context
  SHA re-stales artifacts. Leaning for cutover: a CI bot that regenerates and auto-commits
  (canonical-message commits, the codegen-commit pattern).
- **docker-devkit publishing** (post-initiative, decision-gated — also gates the
  semantic-core ledger entry). The 2026-10 prior-art survey found the integrated whole —
  committed, deterministic, hermetic dual compose+k8s rendering with lock-coupled mirror
  governance and fail-closed lifecycle — nowhere; parts are precedented (Score; Flux
  Mirror for org-mirroring; Compose Bridge for one-shot compose→k8s). If yes: de-org-ify
  first (config knobs for the placeframe-shaped paths and defaults; soft deps on
  bashrun/strictyaml/build-artifact-registry), frame it as "the determinism + governance
  layer for Score" (the spec community's active drift discussion is the entry point), and
  put cosign/referrers mirror verification on the roadmap before Flux Mirror grows a
  consumer-side lifecycle. Risks: Docker's first-party convergence eroding the value prop
  from below; the treadmill of tracking score-compose/score-k8s output changes; the niche
  ceiling of dual-runtime-from-one-source.

## Current state

- **Next session starts here**: the push+pin landed — docker-devkit
  `score-gpu-variants` is pushed (`7fa29ea`) and placeframe is git-pinned to it
  (root `AGENTS.md` carries the exception note). The ball is the operator opening
  the PR to `dev`: the mirror job runs (keycloak operator chart + 26.8.1 images),
  publish-compose publishes the six artifacts, and preflight runs green under the
  pin (verified locally: full scripts battery, basedpyright, native regeneration
  byte-identical to the committed artifacts). After the PR: the mirror-gated k8s
  regen below, then work item 2 (cutover).
- **Item 1 landed** (commits `04c9022b`..`47881ff7` + devkit `491f4fb`/`7fa29ea`):
  the devkit seam schema replaced the flat compose fields (seams × gpu variants →
  per-output flattening; overrides with null-deletion merge, compose-only); the six
  artifacts are generated, deterministic, hermetic, and `docker compose config`-valid
  in both the OIDC (core-cuda + gateway-keycloak + tunnel-rathole) and anonymous
  (core-rocm + gateway-open + tunnel-ngrok) assemblies. The relays became compose-only
  workloads (credentials through an outputs-only `tunnel-config` provisioner; ngrok's
  domain through a shell wrapper — score substitutes nothing inside command args);
  `tunnel-gate-exclusion.tpl` and both tunnel provisioner pairs died with the last
  profile; the api's `AUTH_JWKS_URL` moved to the config passthrough so the core
  seam carries no oidc-issuer; `publish-compose` publishes the six from the
  generated files (no config inlining; single CI leg, no variant matrix).
- **k8s deliberately stale** — unchanged: the operator chart and the 26.8.1 images
  are declared but not mirrored, and k8s generation fails on the chart fetch until
  the mirror job runs (Integrate, PR to `dev`; a bare branch push never runs it).
  The k8s sources carry the seam split's k8s-side edits (config provisioner's
  `auth_jwks_url`, no tunnel provisioner) whenever that regen runs;
  `scripts/tests/test_score_k8s_generation.py` locks the k8s mechanics (GPU patches,
  KEDA CRs, service-port URLs, no operator documents) and its compose twin locks the
  seam split.
- **SaaS-engineer coordination**: his deploy branches
  (`cnpg-dev`/`placeframe-deploy`/`pf-secrets-dev`/`score-dev`) carry score-up/score-down
  wrappers, a CNPG backend option, and deploy-time fixes; he consumes the generated k8s
  artifact, which the seam split does not reshape. External deploy-time actions live in
  `TODO.md` (repo root) — mint `POSTGRES_ADMIN_USER`, the three `KEYCLOAK_*` lifespan
  keys, mint-list conformance, Argo path fix, MinIO removal, and the reconstructor split
  (delete the Pulumi workload path, keep `install_keda` as the operator's permanent
  home).
- **Branches**: `score-compose`, squashed and rebased onto `origin/dev` (`daf491a9`,
  post-#150). Landing is operator-owned (bors model); the sandbox has no push scope —
  commit locally, hand off branch + HEAD at session end. Remote is
  `outernet-foundation/plerion`. docker-devkit `dev` is merged/pushed; 0.4.7 is on PyPI
  and locked here — the seam work rides `score-gpu-variants` (unpushed) and couples
  by git pin.
- **Artifacts**: compose current with the seam split (six files; the mirror gap on the
  keycloak 26.8.1 image bites `up` of the gateway-keycloak artifact — bridge with a
  local pull of the upstream digest or a `KEYCLOAK_IMAGE` override). The
  tree-sha tags in the artifacts must exist before `up` (build missing services
  first, `uv run build -t api -t gateway --gpu none`).
- **Smoke-verified on the seam artifacts** (isolated `-p` projects, fresh volumes,
  keycloak 26.8.1 bridged by a local upstream-digest pull): the OIDC assembly
  (core-cuda + gateway-keycloak + tunnel-rathole) fully healthy — configurator realm
  sync complete, gateway `/server-info` in keycloak mode, `/schema` 200; the rathole
  relay correctly names its empty passthrough holes and restart-waits (no tunnel
  creds in this `.env`). The anonymous assembly (core + gateway-open) fully healthy
  with no keycloak container and the gateway serving. Both parse+interpolate
  (`docker compose config`); the publish-side bake path (substitution + digest
  pinning with stubbed digests) parses standalone for all six. Concurrent
  assemblies on one host collide on the baked host ports (8443; `seaweedfs-admin`
  via `SEAWEEDFS_ADMIN_PORT`, grafana via `GRAFANA_PORT`) — dev-host reality, not an
  artifact bug. Prior smoke facts stand.
- **Resumption mechanics**: the pinned score tools, helm, and repo-pinned uv live in
  `~/.local/bin`, not on the sandbox's default PATH (`export PATH="$HOME/.local/bin:$PATH"`).
  Generation runs natively from the repo root: `uv run generate-score --target compose|k8s`
  (`--local` for k3s against the gitignored local artifact) — until the devkit re-pin,
  from `/workspace/docker-devkit/.venv/bin/generate-score` instead (the repo venv's
  locked 0.4.7 predates the seam fields; the two new test modules likewise only run
  under the devkit venv or post-pin). Lifecycle verbs (`uv run up`/`down`/`build`) work
  natively (same re-pin caveat). Regeneration is deterministic across fresh runs.
  `uv cache clean docker-devkit` before any future `uv lock --upgrade-package` (once
  served a stale cached simple-index). docker-devkit is read via the `/workspace` bind
  mount (fetching its SSH remote fails).
- **Authoring format and artifact laws live in `stack/AGENTS.md`** (mapping-form markers,
  include/lock resolution, hermeticity, load-bearing DNS/bucket names, GPU/variant
  mechanics, KEDA absorption, seam/override mechanics, patch-template gotchas) — not
  duplicated here.
