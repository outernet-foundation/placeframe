# stack/

## What this is

The score tier: one authored description per service, compiled into two renderings —
five Docker compose artifacts under `stack/generated/compose/` (one per assembly bundle,
the core bundle split per GPU variant) and `stack/generated/k8s/manifests.yaml`
(Kubernetes, one monolithic artifact). Coverage is the full stack — the hand compose
files are deleted; `stack/score/` holds the authored sources, `stack/generated/` the
committed artifacts, and the repo's `docker-devkit.yaml` root `bundles:` plus the
`BUNDLES=` selector in `.env` assemble the artifacts at `up`/`down`.

    stack/score/            authored
      api.yaml              workload contracts (tier-neutral), ${SHA} placeholders for image tags,
      lease-server.yaml     ${GPU_VARIANT} placeholders where a workload is accelerator-carrying
      gateway-open.yaml     the gateway pair — both `metadata.name: gateway`, one file per
      gateway-keycloak.yaml auth mode (the file *is* the auth-mode difference)
      reconstructor.yaml
      localizer.yaml
      tunnel-ngrok.yaml     compose-only relay workload — absent from the k8s workload list,
                            which is why it has no k8s provisioner twin
      compose/              provisioners for the compose rendering
      k8s/                  provisioners for the k8s rendering
      k8s/values/           helm values for the declared charts (k8s rendering only)
    stack/secrets.yaml      tier-neutral secrets/env declaration (both renderings)
    stack/generated/        committed artifacts, never hand-edited
      compose/compose.core-{cuda,rocm}.yaml               core bundle per GPU variant
      compose/compose.gateway-{open,keycloak}.yaml       gateway bundle, anonymous / OIDC edge
      compose/compose.tunnel-ngrok.yaml                  the ngrok relay artifact
      k8s/manifests.yaml
      secrets.txt           mint list generated from the secrets declaration

The bundles are declared in `docker-devkit.yaml`'s root `bundles:` map: each bundle
names its workloads (bare filenames under `stack/score/`) and its `vars` (`GPU_VARIANT`
for the core pair); the output path derives from the bundle name. Provisioner
registration derives by resource-type closure over the rendering's workloads — no
provisioner list is authored anywhere. Deployment-surface behavior — healthchecks, gpu
plumbing, the relay restart, host publishes, the wait-for-resources pin — is
annotation-driven through the devkit's built-in patch templates; this repo authors
no patch template. Consumers assemble a backend by including artifacts —
`core-cuda + gateway-keycloak + tunnel-ngrok` is the OIDC-with-relay assembly;
`gateway-open` is the gateway with its auth snippet files and oidc-issuer resource
absent (the file *is* the auth-mode difference between the gateway artifacts) and
references no oidc-issuer resource, so keycloak rides only the
gateway-keycloak artifact. The k8s rendering is deliberately monolithic: Argo applies
one artifact wholesale, and assembly-by-inclusion is a compose-consumer concept.

## Generate

`uv run generate-score [--target compose|k8s] [--local]` writes the artifacts and deploys
nothing. Image tags resolve via `compute_service_shas` from the **committed** tree
(`git ls-tree HEAD`), so the order is: commit the source change, regenerate, commit the
artifacts as their own canonical `Run generate-score` commit. Generating first produces
artifacts built against the previous tree.

The score tools (score-compose 0.42.0, score-k8s 0.15.0) must be on PATH at those exact
versions — output differs between releases. In the COI sandbox they live in `~/.local/bin`,
which is not on the default PATH.

Staleness is gated in CI's build-docker getter, not preflight: its `generate-score --check`
step fetches the exact pinned score tools itself, regenerates in the runner checkout, and
fails on any git change under the config-derived outputs (the five compose artifacts,
`k8s/manifests.yaml`, `secrets.txt`), printing the diff — uncommitted edits heal by
regeneration, only committed state can drift. Every change inside a service's build
context (a dependency-lock bump included) re-stales the committed output through the
embedded `tree-<sha>` tags, so each source change carries its regeneration in the same
PR. Regeneration is a deliberate manual step (the gate verifies, never writes the tree),
deterministic across fresh runs (the tool state dirs are per-run temp; instance suffixes
are name-derived hashes).

## Deploy: Docker

`uv run up` / `uv run down` (docker-devkit) assemble the graph from the root
`bundles:` map of `docker-devkit.yaml`, selected through `BUNDLES=` in `.env` (the
`COMPOSE_PROFILES` precedence: shell env over `.env`): `BUNDLES=` names declared
bundles, layering `core-cuda` (or `core-rocm` — the host picks its variant; both GPU
workloads reserve devices, so a GPU-less host cannot run the core), one gateway
bundle, and at most one relay. Unknown names refuse loudly listing the vocabulary;
`uv run down` layers every declared bundle unconditionally so teardown covers prior
bring-ups under a different selection. The old `AUTH_ISSUER_URL`/`NGROK_AUTHTOKEN`
env-conditioned axes are dead — the selector is structural (`BUNDLES=`), and the
auth-mode choice is which gateway bundle the host names; the `AUTH_*` block remains
the api's own config either way. `up --dev` generates the dev overlay per-run (never
committed): every assembly service whose Dockerfile declares a genuine multi-stage
`dev` stage gets `image: {repository}/{service}:dev` plus the repo-root→`/app:ro`
bind, and each workload's `outernet.internal/dev-toggles` pairs become
`${NAME:-default}` environment holes, so `.env` debug overrides apply only under
`--dev`. External consumers (Make-it-Sing) assemble by `include:`-ing the published
OCI bundles instead.

The gateway's published host port is env-driven through its
`outernet.internal/publish: ${GATEWAY_PORT:-8443}/8443` annotation: an existing
host's `GATEWAY_PORT` value now governs prod (the old dev overlay remap is gone), so
retarget deliberately — `.env.sample` ships `GATEWAY_PORT=8443`. The api and
lease-server debug ports publish always, localhost-bound
(`127.0.0.1/${API_DEBUG_PORT:-5679}/5678`, `127.0.0.1/${LEASE_SERVER_DEBUG_PORT:-5683}/5678`).

```bash
docker compose --project-directory . \
  --env-file .env --env-file docker-devkit.lock \
  -f stack/generated/compose/compose.core-cuda.yaml \
  -f stack/generated/compose/compose.gateway-keycloak.yaml \
  -f stack/generated/compose/compose.tunnel-ngrok.yaml up -d
# teardown: same command with `down --remove-orphans`
```

Raw `docker compose` (the pressure valve) anchors at the repo root
(`--project-directory .` is required — compose otherwise anchors relative paths at the
first `-f` file's directory).

The `tree-<sha>` image tags the generated compose references must exist before `up` — a
regeneration can reference tags that have never been built or pushed, and the pull fails
with `not found`. Build the missing services first (`uv run build -t api -t gateway
--gpu none`).

It reads `.env` the same way any assembly does (`KEYCLOAK_ADMIN_PASSWORD` consumed only by
the gateway-keycloak artifact — keycloak and its configurator ride that bundle; the core and
gateway-open never see it). Reach it at `http://localhost:${GATEWAY_PORT:-8443}/schema`.

## Deploy: Kubernetes

```bash
kubectl apply -f stack/generated/k8s/manifests.yaml
```

The cluster is a precondition. On the real cluster Argo CD applies this file (see the infra
repo); the Pulumi program creates the `placeframe-secrets` Secret every manifest references
and installs the Hetzner CSI driver behind the `hcloud-volumes` storage class. No host ports:
reach the gateway with `kubectl port-forward deploy/gateway 8443:8443`.

Against a local cluster (k3d), generate with `--local`: it selects the `local-path` storage
class and writes to the gitignored `stack/generated/k8s/manifests.local.yaml`, leaving the
committed artifact untouched — `local-path` reaching the real cluster leaves the Postgres and
SeaweedFS volumes unbindable on the next rebuild. Create the cluster with
`k3d cluster create score-poc --no-lb --k3s-arg "--disable=traefik@server:0"`. Install KEDA
next — the operator is cluster tier (infra's Pulumi release on the real cluster; nothing
rides the artifact): `kubectl apply -f https://github.com/kedacore/keda/releases/download/v2.20.2/keda-2.20.2-core.yaml`
— without its CRDs the artifact's ScaledObject does not apply, and without the operator the
reconstructor sits at zero replicas. With no Pulumi locally, mint the Secret
first: every key in the generated mint list `stack/generated/secrets.txt` must exist on the
`placeframe-secrets` Secret (random hex for the credentials, real values or empty strings
for the passthroughs like `PUBLIC_URL` and the `AUTH_*` block). For OIDC mode mint
`AUTH_JWKS_URL` as `http://keycloak-service:8080/realms/placeframe-dev/protocol/openid-connect/certs`
(split-horizon: the api reaches the operator-owned Service directly). The artifact includes
cluster-scoped CRDs + RBAC from the keycloak-operator chart — the k3d admin context
admits them; a restricted Argo target must too.

k3d pulls through Docker Hub, whose unauthenticated rate limit is low enough to fail a cold
cluster; preload slow images with `docker save <image> | docker exec -i k3d-score-poc-server-0
ctr -n k8s.io images import -`.

## Divergence between the renderings

One authored source, two renderings — the deliberate differences, so nobody "fixes" them:

- Secrets: compose emits `${VAR:?err}` holes filled from `.env` at run time; k8s emits
  `secretKeyRef` wiring into `placeframe-secrets`. Each tier's native mechanism.
- Liveness/readiness: chart probes (loki, grafana) on k8s vs compose healthchecks; the
  built workloads declare `outernet.internal/probe-adapter` and the devkit's built-in
  template converts their httpGet probes into compose healthchecks.
- Host publishes ride the workloads' `outernet.internal/publish` annotations (api 8000
  + its localhost debug port, gateway `${GATEWAY_PORT:-8443}`, ngrok 4040) and the
  `seaweedfs-admin` console's provisioner-emitted hole: all compose-only; the k8s edge
  is the Pulumi-owned Ingress (`PUBLIC_URL` host, cert-manager issuer — per-site and
  Secret-resident, un-committable in a deterministic artifact).
- The relay is compose-only (its own artifact); the SaaS cluster has no relay.
- Grafana: anonymous auth on compose vs credentialed `existingSecret` on k8s; root URL
  spelled from `${PUBLIC_URL}` on compose vs request-derived placeholders on k8s — one
  semantic, two idioms.
- `PGDATA` subdir and storage class/size literals exist only in the k8s StatefulSets;
  ordering rests on compose health `depends_on` vs Argo sync-hook weights plus job
  retry-idempotency (the weights are inert under bare `kubectl apply`, by design).
- KEDA: scale-to-zero exists only on k8s (compose runs the reconstructor always-on);
  `maxReplicaCount` and the trigger SQL bake as literals with per-cloud node caps in
  the ASG/MIG/CAS layer; the operator and the Argo `ignoreDifferences` for
  `/spec/replicas` live in the infra Pulumi layer, not the artifact.

Pending external work lives in `TODO.md` (repo root): the infra-side deletion of the
Pulumi reconstructor workload (until it lands, the SaaS cluster has two owners of the
`reconstructor` Deployment — Argo prune vs Pulumi) and the Argo/Secret mint items. The
per-resource-pair provisioner duplication (env sets and command lines repeated across
the compose/k8s pairs) is deliberate: with placeframe-only scope and five stable
resource types, pairwise edits are cheaper than a shared resource-semantics authoring
tier in docker-devkit; re-evaluate if docker-devkit is published or resource types
proliferate.

## Constraints

- **Provisioner sources are authored in mapping form; string form is compiler output.**
  `state`/`outputs`/`volumes`/`services`/`manifests` are authored as real YAML mappings and
  lists, compiled to score's YAML-in-a-string form in a per-run tempdir at generation —
  compiled output never goes back into a source. Single-key authoring markers ride in
  provisioner manifests and chart values alike: `include:`/`include-yaml: <repo-root-relative
  path>` inserts a file's bytes verbatim / parsed structure, and `lock: NAME`/
  `lock-image: NAME` substitutes a `docker-devkit.lock` entry — the full digest reference for
  provisioner `image:` fields, or the registry/repository/tag/digest fields chart values
  want (`digest_field: sha` for grafana's bare-hex spelling) — object-typed image
  values only. Charts whose values schema types image fields as strings (the
  keycloak-operator chart: `operator.image`, `operator.envs.*`) take `lock: NAME`
  instead; the object form fails their values validation. The lock is the k8s
  provisioners' single digest source: they have no runtime env-file, so no compose-style
  `${VAR}` hole is available there.
- **K8s config content arrives by inclusion, never hand mirrors.** The alloy ConfigMap
  body is `include: workloads/alloy/config.alloy`; the loki chart's entire config is the
  committed `workloads/loki/config.yaml` through the `structuredConfig` full-override in
  `values/loki.yaml` (the chart's templated config is blanked; the chart validator still
  demands a structured `schema_config`, which is why the override rides `structuredConfig`
  rather than the `loki.config` string); grafana's datasources ride `include-yaml:`. One
  committed file feeds both renderings — no standing copy to keep in sync.
- **The secrets declaration is the consumed-key contract.** `stack/secrets.yaml`
  declares every `ALL_CAPS` key either rendering consumes; generate-score validates each
  generated artifact's consumed keys (compose `${VAR}` holes; k8s `secretKeyRef`s into
  `placeframe-secrets`) are a subset of it, and writes `stack/generated/secrets.txt` — the
  mint list of Secret-resident keys — from the declaration alone.
- **Compose artifacts are hermetic: zero host-filesystem references.** score-compose
  materializes workload `files:` as binds into its state dir; the docker-devkit post-pass
  rewrites every bind into a top-level `configs.content` entry with each `$` doubled (compose
  interpolation would otherwise eat loki's `${VAR}` and caddy's `{$VAR}`). A bind surviving in
  a generated compose is a bug.
- **No secret resolves at generation time.** Compose provisioners emit literal `${VAR:?err}`
  holes that docker fills from `--env-file` at run time (`.env` is the single credential
  source, shared with the hand stack); k8s provisioners emit `encodeSecretRef` pointers into
  the externally managed `placeframe-secrets` Secret — score-k8s has no configMap equivalent,
  so non-secret config rides the same Secret. Both artifacts are safe to commit.
- **`AUTH_JWKS_URL` is a config-provisioner passthrough in both renderings**, never a baked
  keycloak URL: the api boots anonymous mode only when the issuer is empty *and* every auth
  endpoint is empty (`check_auth_config` in `workloads/api/src/settings.py`); a baked JWKS
  URL would crash anonymous boots. It moved onto `placeframe-config` with the bundle split —
  the core artifact carries no oidc-issuer provisioner, so no workload in it may hang auth
  wiring off that resource type.
- **Service names in provisioners are load-bearing DNS names.** `seaweedfs`,
  `seaweedfs-audit`, `pf-postgres`, `keycloak` are addressed by baked-in references (loki's
  config, the entrypoint wrapper's rendered audit sink, the gateway auth snippets); renaming
  one breaks the stack at runtime, not at generation. On k8s the operator owns the real
  keycloak Service (`keycloak-service`, from the Keycloak CR name) and the provisioner
  emits an ExternalName alias so the single-sourced `keycloak:8080` references in the
  gateway snippets resolve on both tiers; minted k8s JWKS URLs should target
  `keycloak-service:8080` directly. **Bucket names are load-bearing contract names
  the same way**: `captures`, `reconstructions`, `loki`, unprefixed in both tiers. The s3
  provisioners create exactly that set (initializer `S3_BUCKETS`) and expose
  `bucket`/`captures_bucket` as resource outputs the api consumes; loki's committed config
  addresses the `loki` bucket by literal, so the provisioner list and that config must
  stay in agreement.
- **The realm is converged post-boot by the configurator in both tiers.** The
  auth-initializer image waits for keycloak's admin API, then creates or updates the
  realm from `workloads/auth-initializer/realm-export/placeframe.json` — substituting the
  `${KEYCLOAK_*}` and `${PUBLIC_URL}` holes from its env (compose `.env` holes, k8s
  `secretKeyRef`s; the mint list carries the three lifespan keys). The file-import path
  is dead: operator-managed pods carry no initContainers, and KeycloakRealmImport cannot
  resolve holes. The export seeds no users; the optional `SEED_TEST_USERS` pairs
  (compose soft passthrough, k8s mint-list key) are create-or-updated by the
  configurator with `firstName`/`lastName`/`email` populated — a fresh 26.8.1 realm's
  default profile requires all three, or the first direct grant fails.
  `KEYCLOAK_ADMIN_PASSWORD` is consumed by both renderings.
- **The realm name and the magic uids are load-bearing constants — named here, not
  linted.** The keycloak realm `placeframe-dev` is baked into
  `workloads/auth-initializer/realm-export/placeframe.json` and every OIDC path derives
  from it. It is declared in the two oidc-issuer provisioner states and the compose
  observability state (bodies template `{{ .State.realm }}`); the gateway receives it as
  the `AUTH_REALM` env from the oidc-issuer resource output and the forward_auth snippet
  addresses it via the caddy `{$AUTH_REALM}` placeholder. Uids: loki runs as uid 10001
  — compose fixes volume ownership via the initialize-loki chown sidecar, k8s via the
  chart's default securityContext. Keycloak's k8s half is H2-ephemeral (no data PVC,
  no fsGroup concern) until a db spec lands; same number, different mechanisms per tier
  where volumes still exist.
- **Provisioners come in per-rendering pairs** — `compose/<name>.yaml` and `k8s/<name>.yaml`
  for the same resource type. Which files ship derives by resource-type closure over the
  rendering's workloads (per-bundle workloads for compose, the `k8s:` workload list for
  k8s): a provisioner rides a rendering exactly when one of its workloads references the
  resource type — no provisioner list is authored, and an orphan file (a type nothing
  references) silently no-ships. The score tools themselves impose no naming requirements
  on these files.
- **Workload files are not standalone-valid score documents** — `${API_SHA}`-style image
  placeholders are expanded by `generate-score` from the committed tree before the score
  tools see them.
- **Dev behavior toggles bake as literals; the dev overlay is generated.** The api and
  lease-server `variables:` carry `RELOAD`/`DEBUG_API`/`DEBUG_WAIT_API` (and the
  lease-server's `DEBUG_LEASE_SERVER`/`DEBUG_WAIT_LEASE_SERVER` twins) at prod-safe
  `"false"` literals, and their entrypoints read exactly those names — debug-in-prod is
  unrepresentable. The `outernet.internal/dev-toggles` annotation on each workload
  (comma-separated `NAME=default` pairs carrying the *dev* defaults) is read by devkit
  code at `up --dev`: the generated overlay turns the pairs into `${NAME:-default}`
  holes, so `.env` overrides apply only under `--dev`.
- **No `depends_on` across workloads**: score has no such concept. Provisioner services gate
  on each other's health; workloads gate on the auto-emitted `wait-for-resources` service,
  whose `alpine` default image is redirected through the `${ALPINE_IMAGE:?err}` lock hole by
  the devkit's built-in gate-pin template — the artifact carries no
  unpinned image. The gate emits only where a provisioner carries services, so the
  gateway-open and tunnel artifacts carry none.
- **The relay is a compose-only workload** (`tunnel-ngrok.yaml`, absent from the k8s
  workload list). Score workload specs cannot carry runtime `${VAR}`
  holes — score validates placeholders as dotted resource references — so the relay
  credentials ride the outputs-only `compose/tunnel.yaml` provisioner (`type:
  tunnel-config`, no services, no k8s twin) exactly like the placeframe-config valve.
  ngrok's domain cannot be a resource ref inside `command` either (score does not
  substitute there and `$$`-escapes the hole to a compose literal), so its command is a
  `/bin/sh -c` wrapper expanding `${NGROK_DOMAIN:-}` inside the container from the
  passthrough env. The workload's `outernet.internal/restart: on-failure` annotation (read
  by the devkit's built-in restart template, the value validated against the compose
  restart-policy enum at generation) sets `restart: on-failure` — the
  relay is a long-lived agent whose control endpoint flaps. No compose profile exists
  anywhere in the five artifacts; the relay forwards to the gateway by Docker DNS name, so
  an assembly without it simply has no public edge.
- **Third-party k8s stamp-outs are charts where an OCI chart exists** — loki, grafana, and
  the keycloak operator render from tag-form upstream-native OCI refs declared in
  `docker-devkit.yaml`'s root `k8s.charts` map (`oci://host/path:tag`), resolved to
  digests through the `{NAME}_CHART` entries `build --lock-only` writes into
  `docker-devkit.lock` — generation renders the lock's mirror-prefixed digest ref
  (`helm template` against it), so a declared chart without its lock entry refuses at
  generation naming the relock path. The CI mirror job copies chart declarations like
  image declarations; declaring a chart the mirror job has not copied yet makes k8s
  generation fail until it runs. The operator chart ships its CRDs under
  `templates/crds/`, so `helm template` renders
  them into the artifact — Argo/kubectl-apply sees the CRDs before the Keycloak CR.
  Chart values never carry secret values: they reference the existing `placeframe-secrets`
  Secret (`envValueFrom`/`extraEnvFrom`/`existingSecret`) or `${VAR}` config holes
  expanded in-container. Alloy has no upstream OCI chart, so `k8s/observability.yaml`
  hand-writes its Deployment + Service + ConfigMap (config body by inclusion; see above).
- **Restart policies stay undeclared everywhere except the relay** — workload services and
  provisioner services rely on compose's default; the one sanctioned exception is the
  relay's `outernet.internal/restart: on-failure` annotation. The hand stack's posture is
  identical.
- **Argo CD Jobs**: create/migrate/bucket Jobs carry `argocd.argoproj.io/hook: Sync` +
  `BeforeHookCreation` because a Job's spec.template is immutable — without the hook an image
  tag bump makes every later sync fail with "field is immutable". Re-runs are safe (create is
  idempotent, the migrator is a no-op on matching schemas, the bucket initializer only creates
  missing buckets).
- **GPU plumbing is annotation-driven per variant.** A workload declares
  `metadata.annotations.outernet.internal/gpu: "true"` — the single declaration of
  accelerator-carrying behavior. Everything else derives: `${GPU_VARIANT}` in the workload
  image name (substituted per compose output and fixed to `cuda` for the k8s rendering),
  the devkit's built-in gpu device templates (registered per the rendering's variant:
  NVIDIA device reservations for cuda, `/dev/kfd` + `/dev/dri` with the render/video
  groups for rocm), and the devkit's built-in gpu-pod template on k8s. The k8s plumbing
  contract with the cluster tier (Pulumi-owned):
  runtimeClassName `nvidia`, nodeSelector `placeframe.io/gpu=true`, `nvidia.com/gpu: 1` —
  the NVIDIA device plugin and GPU-worker labeling live in infra, and renaming any of the
  three breaks scheduling, not generation. The annotation is org-namespaced; the
  nodeSelector label stays `placeframe.io/gpu`, exactly what Pulumi labels GPU nodes with.
- **Cross-workload URLs ride the native `service-port` resource** — `${resources.x.hostname}`
  resolves to the same string on both tiers (compose: the workload `hostname:` field, which
  Docker's embedded DNS serves; k8s: the per-workload Service). The api's
  `LOCALIZER_CONTAINER_URL` and the reconstructor's `LEASE_SERVER_URL` are wired this way;
  no alias patch templates and no hardcoded `<workload>-<container>` names.
- **KEDA scale-to-zero is declared as a workload resource** (`type: keda-scaled-object`): the
  k8s provisioner renders the ScaledObject (postgres trigger on queued reconstructions,
  300 s cooldown, `maxReplicaCount: 8` baked — per-cloud node caps stay in the ASG/MIG/CAS
  layer) plus a TriggerAuthentication whose only `secretTargetRef` is the password into
  `placeframe-secrets`; host/port/dbName/userName bake as literal trigger metadata from the
  provisioner state. The compose twin is an outputs-less no-op (compose runs the
  reconstructor always-on). The devkit's built-in scale-to-zero template sets
  `spec.replicas: 0` on any Deployment
  whose workload declares the resource — Argo's selfHeal fights KEDA over that field unless
  the Application carries `ignoreDifferences` (infra-side config). The operator itself is
  cluster tier — infra's Pulumi helm release installs it, peer of the NVIDIA device plugin
  (a cluster-wide reconciler serving any app; its CRDs/RBAC would demand admin-scope applies
  from the app target, and a second install on a shared cluster fights over the shared
  CRDs and metrics APIService). The artifact's CRs assume it exists: no operator → the
  reconstructor sits at `spec.replicas: 0` forever.
- **Patch-template authoring gotchas (both tools).** (a) In score-k8s patch templates, map
  fields on the root dot (`.Workloads`) resolve to zero values *inside* a `range` body —
  capture `{{- $workloads := .Workloads }}` before ranging. (b) Provisioner `manifests`
  values that carry quotes (the KEDA trigger query's `'queued'`) must be manifest literals,
  never `{{ .State.x }}` templates: templated values render after the compile's yaml dump,
  where no escaping can apply.
- **The generated k8s mechanics are test-locked** — `scripts/tests/test_score_k8s_generation.py`
  regenerates the k8s manifests from the real sources (charts stripped: their mirror gap is
  environmental, not structural) and asserts the GPU patches, the service-port URLs, and the
  KEDA CRs — and that no KEDA operator documents ride the artifact. The compose bundle split
  has its twin in `scripts/tests/test_score_compose_generation.py`: five outputs, zero
  profiles, zero binds, the collapsed service names, the snippet/auth difference between
  the gateway artifacts, and the relay restart/passthrough mechanics. Both skip when the
  pinned tool is off PATH or the
  installed docker-devkit predates the root-config bundle fields.

## See also

- [`docker-devkit's `AGENTS.md`](https://github.com/outernet-foundation/docker-devkit/blob/main/AGENTS.md)
  — `generate-score` internals (placeholder expansion, bind inlining, determinism suite).
- `workloads/AGENTS.md` — the running stack's service inventory, data flow, auth model.
