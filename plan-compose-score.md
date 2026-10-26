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
   carries `{gpu}`, workload images carry `${GPU_VARIANT}`, and the five-artifact set
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

- Runtime `.env` holes survive only as provisioner outputs inserted verbatim — the
  `placeframe-config` provisioner is the passthrough valve.
- Generated workload services are named `<workload>-<container>` (`api-api`); patches must
  compute names, never hardcode.
- Cross-workload `depends_on` is not a score concept — the auto-built `wait-for-resources`
  gate replaces it; poll-retry absorbs ordering.
- Seam tests: platform-variance → score file; docker-only detail → patch template;
  generation-time baking vs runtime `.env` hole → config provisioner.
- Regeneration order: commit sources → regenerate → commit artifacts. Staleness between
  those commits is accepted; preflight does not gate it (every context SHA re-stales the
  tree-sha tags).
- Profile-gated provisioner services had to be carved out of the auto-built
  `wait-for-resources` gate (`compose/patches/tunnel-gate-exclusion.tpl`): docker compose treats
  an inactive-profile service as undefined, so a `required` gate entry breaks every
  operator who didn't enable the profile — and the gateway forwards to whichever relay
  runs alongside it; it does not depend on the relay being up. The exclusion set is
  derived from the generated compose itself (every service declaring `profiles`), not a
  hardcoded service list. The tunnel seam split removes the last profile-gated service,
  so the carve-out (and the template) dies with item 1.

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

- **Next session starts here**: work item 1 — seam generation + multi-artifact publish.
  Slice D landed (see below); the k8s artifact regen remains gated on the keycloak mirror
  job and carries Slice D's sources (the KEDA CRs; the operator itself is cluster tier)
  whenever it runs, and `scripts/tests/test_score_k8s_generation.py` already locks the k8s
  mechanics
  (GPU patches, KEDA CRs, service-port URLs, no operator documents) against the real
  sources with charts stripped.
- **Slice D landed**: reconstructor + localizer workload files (`placeframe.io/gpu`
  annotation, `${GPU_VARIANT}` images), per-variant compose outputs
  (`compose.cuda.yaml`/`compose.rocm.yaml` replacing the single artifact), compose device
  patch templates per variant, k8s `patches/gpu-pod.tpl` + `patches/scale-to-zero.tpl` patch
  templates,
  the `keda-scaled-object` provisioner pair (k8s renders ScaledObject +
  TriggerAuthentication; compose twin is a no-op), and native `service-port` wiring for
  `LOCALIZER_CONTAINER_URL`/`LEASE_SERVER_URL`. The plan's "localizer
  network alias via patch templates" was superseded:
  score-compose's service-port hostname output resolves identically on both tiers, so
  no alias is needed.
- **docker-devkit coupling**: item 1's seam generation extends docker-devkit branch
  `score-gpu-variants` (branched from `dev` at `1f2c829`; it already carries the variant
  config fields and a `vendored_manifests` add-then-remove, net absent) — one lineage, one
  hand-off. Coupling strategy: placeframe pins docker-devkit **by git SHA**, not via the
  PyPI release. Sequencing is forced (uv fetches the SHA from origin): devkit commits land
  locally → operator pushes the branch → placeframe pins the pushed SHA
  (`[tool.uv.sources]` git source) → `uv lock && uv sync --all-packages`. The pushed
  branch self-reports `0.0.0.dev0`, the dev sentinel that bypasses the `requires`
  self-check — verbs work under the pin with no version bump; `requires: ">=0.4.9"`
  stays as the honest released floor for the eventual registry re-pin (additive →
  `0.4.9` per the devkit's pre-1.0 patch flow; the repo is public, so CI resolves the
  git pin unauthenticated). At the pin commit, root `AGENTS.md`'s "release-only
  consumption" note gains its git-pin exception (prose commit, separate from the
  pyproject/lock code commit). Until the push+pin land, every docker-devkit verb in
  this repo refuses loudly (`requires: ">=0.4.9"` vs the locked 0.4.7); preflight is
  unaffected (raw docker compose). Until then, generation runs from the devkit
  checkout's venv (`/workspace/docker-devkit/.venv/bin/generate-score`).
- **Branches**: `score-compose`, squashed and rebased onto `origin/dev` (`daf491a9`,
  post-#150). The pre-squash lineage survives at `backup-pre-chapter-consolidation`; earlier
  squash lineages under the other `backup-pre-*` branches. Landing is
  operator-owned (bors model); the sandbox has no push scope — commit locally, hand off
  branch + HEAD at session end. Remote is `outernet-foundation/plerion` (renamed;
  redirects cover old URLs). docker-devkit `dev` is merged/pushed; 0.4.7 is on PyPI and
  re-pinned here.
- **SaaS-engineer coordination**: his deploy work is no longer deferred —
  `cnpg-dev`/`placeframe-deploy`/`pf-secrets-dev`/`score-dev` carry score-up/score-down
  wrappers, a CNPG backend option, and deploy-time fixes. He consumes the generated k8s
  artifact; coordinate k8s provisioner edits with him — the keycloak-operator switch
  (landed in source) is the largest yet. External deploy-time actions live in
  `TODO.md` (repo root) — mint `POSTGRES_ADMIN_USER`, the three `KEYCLOAK_*` lifespan
  keys, mint-list conformance, Argo path fix, MinIO removal, and the reconstructor split
  (delete the Pulumi workload path, keep `install_keda` as the operator's permanent
  home). His `placeframe-pulumi`
  branch is surveyed (Settled): the cluster tier stays — KEDA operator included; the
  reconstructor workload scaffolding is absorbed by Slice D and deleted his-side per the
  TODO items.
- **Artifacts**: compose current with the Slice D landing (per-variant; the mirror gap on the
  keycloak 26.8.1 image bites compose `up` — bridge with a local pull of the upstream
  digest or a `KEYCLOAK_IMAGE` override pointing at `quay.io/...@sha256:...`); **k8s
  deliberately stale** — the operator chart and the 26.8.1 images are declared but not
  mirrored, and k8s generation fails on the chart fetch until the mirror job runs
  (Integrate, PR to `dev`). After the mirror lands: `uv run generate-score --target k8s`,
  then verify the operator path (CRD admission, `keycloak-service` DNS, configurator
  Job) on k3d. Standing gotcha: the image/chart mirror runs only inside Integrate, which
  triggers on PRs to `dev` — a bare branch push never runs it.
- **Smoke-verified on the generated compose.cuda.yaml** (isolated `-p` project, fresh
  volumes, locally built reconstructor-cuda/localizer-cuda at the artifact's tree tags):
  full stack healthy — reconstructor polling lease-server through the service-port
  hostname (clean 404 no-work loops), both GPU containers seeing the RTX 4080 through
  the device reservation, localizer healthy on its `/version` probe, api →
  `localizer:8000` returning 200, gateway serving `/server-info`. Prior smoke facts
  stand: anonymous + keycloak modes (configurator realm sync, `SEED_TEST_USERS`,
  direct grant, JWT validation, 401 on garbage); keycloak 26.8.1 boots fine with an
  `http://` `KC_HOSTNAME`.
- **Resumption mechanics**: the pinned score tools, helm, and repo-pinned uv live in
  `~/.local/bin`, not on the sandbox's default PATH (`export PATH="$HOME/.local/bin:$PATH"`).
  Generation runs natively from the repo root: `uv run generate-score --target compose|k8s`
  (`--local` for k3s against the gitignored local artifact) — until the devkit re-pin,
  from `/workspace/docker-devkit/.venv/bin/generate-score` instead. Lifecycle verbs
  (`uv run up`/`down`/`build`) work natively (same re-pin caveat). Regeneration is
  deterministic across fresh runs. `uv cache clean docker-devkit` before any future
  `uv lock --upgrade-package` (once served a stale cached simple-index). docker-devkit
  is read via the `/workspace` bind mount (fetching its SSH remote fails).
- **Authoring format and artifact laws live in `stack/AGENTS.md`** (mapping-form markers,
  include/lock resolution, hermeticity, load-bearing DNS/bucket names, GPU/variant
  mechanics, KEDA absorption, patch-template gotchas) — not duplicated here.
