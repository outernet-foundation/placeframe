# stack/

## What this is

The score tier: one authored description per service, compiled into two renderings —
four Docker compose artifacts under `stack/generated/compose/` (one per assembly unit:
the core bundle split per GPU variant, the keycloak bundle, the relay) and
`stack/generated/k8s/manifests.yaml` (Kubernetes, one monolithic artifact). Coverage is
the full stack — the hand compose files are deleted; `stack/score/` holds the authored
sources, `stack/generated/` the committed artifacts, and the repo's `boatyard.yml`
root `services:` vocabulary plus the `bundles:` selector in `boatyard.values.yaml` assemble
the artifacts at `up`/`down`, with boatyard emitting the gateway (caddy) from the routes
the workload annotations declare.

    stack/score/            authored
      api.yaml              workload contracts (tier-neutral), image sources declared as
      lease-server.yaml     boatyard annotations (dockerfile: or lock:); the image
                            line itself is never authored — generate-score injects the
                            composed reference before the score tools see the document
      keycloak.yaml         the tier-neutral OIDC provider — the container is keycloak on both
                            renderings, env fed by the oidc-issuer provisioner outputs
      reconstructor.yaml
      localizer.yaml        accelerator-carrying workloads fan on TORCH_DEVICE; the variant
                            fragment derives from the declared fan, never hand-spelled
      ngrok.yaml            compose-only relay workload — absent from the k8s workload list,
                            which is why it has no k8s provisioner twin
      compose/              provisioners for the compose rendering
      k8s/                  provisioners for the k8s rendering
      k8s/values/           helm values for the declared charts (k8s rendering only)
    boatyard.yml            the declaration: services (authored options and the core variants
                            group), base images, the k8s section
    boatyard.k8s-pins.yml   deploy record written only by `boatyard bump` (the k8s artifact's
                            image-tag pins); absent until the first certified bump
    stack/generated/        committed artifacts, never hand-edited
      compose/compose.{core-cuda,core-rocm}.yaml         core bundle per GPU variant
      compose/compose.auth-keycloak.yaml                  the OIDC provider bundle
      compose/compose.tunnel-ngrok.yaml                   the relay artifact
      k8s/manifests.yaml
      secrets.txt           mint list derived from the k8s rendering's consumed keys

The assembly is declared in `boatyard.yml`'s root `services:` map: each group authors its
option set (`options:` — `auth`/`keycloak`, `tunnel`/`ngrok`) or spells its workloads at the
group level (`workloads:` — `core`), where the option set derives from the single axis the
group's image closure fans (the Dockerfiles fan on `TORCH_DEVICE` into the
`core-cuda`/`core-rocm` options — the fan's one spelling is the built
`NEURAL_NETWORKS_BASE` entry in `base_images`), plus group-level `ports:` that ride
unconditionally (routes live in the workloads' `boatyard/route` annotations and
are adopted into the bundle records at lock and resolve).
`bundles:` names options only, by qualified `group-option` spelling. Provisioner registration derives by resource-type closure
over the rendering's workloads — no provisioner list is authored anywhere.
Deployment-surface behavior — healthchecks, gpu plumbing, the relay restart, the
wait-for-resources pin — is annotation-driven through boatyard's built-in patch
templates; this repo authors no patch template. Consumers assemble a backend by
including artifacts — `core-cuda + auth-keycloak + tunnel-ngrok` is the OIDC-with-relay assembly;
omitting keycloak is the anonymous edge. The k8s rendering is deliberately monolithic:
Argo applies one artifact wholesale, and assembly-by-inclusion is a compose-consumer
concept; the cluster edge is the Pulumi Ingress (infra repo), not a boatyard-emitted edge.

## Generate

`uv run boatyard generate-score [--target compose|k8s] [--local]` writes the artifacts
and deploys nothing. The compose artifacts carry `{ENTRY}__BOATYARD_TREE__*_SHA` slots —
`up` resolves them to working-tree tree tags per run (boatyard hashes the tree over the
`.dockerignore` allowlist; dirt is content, so the order is: commit the source change,
regenerate, commit the artifacts as their own canonical `Run generate-score` commit —
a regeneration run mid-edit produces artifacts naming that edit, not the committed
tree). The committed k8s artifact instead bakes the pins recorded in
`boatyard.k8s-pins.yml`, written only by `boatyard bump`: the bump refuses a dirty tree
and certifies that CI built and shelved images at exactly HEAD (`REGISTRY` names the
shelf) before pinning, then regenerates the k8s artifact itself — the k8s regeneration
and its pins always land together. `--local` skips the pins (tree-computed shas, local
storage class, gitignored `manifests.local.yaml`). Provisioner templates read the
service SHAs through `{{ env "NAME" }}` — boatyard exports the sha/image values to the
score tools.
This checkout carries ignored dirt under the allowlist (`__pycache__`, `build/`,
`egg-info/`, the vendored deep-image-retrieval `.venv`), and dirt hashes: a regeneration
run from this tree mints tags only this machine can reproduce, and CI's
`generate-score --check` (clean checkout) fails against them. Regenerate for commit from
a clean clone of the branch tip (`git clone --branch <branch> . /tmp/clean && cd /tmp/clean`,
run the verb there, copy `stack/generated/**` back); a regeneration run from the dirty
tree is for local `up` only — its tags name daemon-local bits.

The score tools (score-compose 0.42.0, score-k8s 0.15.0, helm 3.22.1) are pinned and
installed into `/usr/local/bin` by the verb itself (presence-probed first) — output
differs between releases, so the pin, not the environment, decides.

Staleness is gated in CI's build-docker getter, not preflight: its `generate-score --check`
step fetches the exact pinned score tools itself, regenerates in the runner checkout, and
fails on any git change under the config-derived outputs (the four compose artifacts,
`k8s/manifests.yaml`, `secrets.txt`), printing the diff — uncommitted edits heal by
regeneration, only committed state can drift. The compose artifacts no longer embed
`tree-<sha>` tags (the slots resolve per run), so source changes inside a service's
build context re-stale nothing on the compose side; the k8s artifact moves only through
`boatyard bump`, which pins exactly the CI-built HEAD. Regeneration is a deliberate
manual step (the gate verifies, never writes the tree), deterministic across fresh runs
(the tool state dirs are per-run temp; instance suffixes are name-derived hashes).

## Deploy: Docker

`uv run boatyard up` / `uv run boatyard down` assemble the graph from the root `services:`
map of `boatyard.yml`, selected through the `bundles:` list in `boatyard.values.yaml`:
`bundles:` names options by qualified spelling — the core variant (`core-cuda` or
`core-rocm` — the host picks its variant; both GPU workloads reserve devices, so a
GPU-less host cannot run the core), the auth edge (`auth-keycloak`; omitting it
is the anonymous edge), and at most the relay (`tunnel-ngrok`). Unknown names refuse loudly
listing the vocabulary; `uv run boatyard down` derives every candidate project name from
the config's full entry set plus the bare project name and removes the shared network
last, so teardown covers prior bring-ups under any selection. There is no `up --dev`: the dev toggles (RELOAD, DEBUG_*) bake as prod-safe literals
in the artifacts — the dev overlay is unbuilt, trigger-gated design in boatyard's
`design/dev-overlay.md`.
External consumers (Make-it-Sing) declare the published OCI bundles as `ref: oci://`
entries instead, or point a `path_overrides:` entry at a sibling checkout's
`stack/generated/compose/` output.

The gateway is emitted by boatyard from the routes the workload annotations declare —
never authored in `boatyard.yml`: `gateway_port: 8443` (an integer in `boatyard.yml`)
publishes the gateway's host port, the values file's typed `gateway_port:` override
retargets it, the gateway
listens `:8443` internally, and the route table (`/auth/*` strip-prefix to keycloak via
the keycloak workload's route annotation, `/grafana/*` and `/loki/*` unprotected plus
`/*` to the api via the api workload's route annotation) is authored workload surface
adopted into the bundle records — the gateway does no token validation (the `protected`
flag and its forward_auth emission are stripped; re-protection is a bundle-shipped
oauth2-proxy sidecar treaty, tracked as a comment beside the api's route annotation).
Host
ports beyond the door live in the config's `ports:` as integer defaults (api and
lease-server debug ports, localhost-bound; the seaweedfs-admin console) — consumer-side
published ports of services the bundles carry. The `boatyard/publish-port`
annotation is live grammar (consumed by lbe-toolkit's livekit tier); no workload here
carries one.

```bash
docker compose --project-directory . \
  -f stack/generated/compose/compose.core-cuda.yaml \
  -f stack/generated/compose/compose.auth-keycloak.yaml \
  -f stack/generated/compose/compose.tunnel-ngrok.yaml up -d
# teardown: same command with `down --remove-orphans`
# slots fill from the shell you invoke this in; `up`'s per-run env file (values + lock
# fans) is the sanctioned materialization and rides in the OS temp dir
```

Raw `docker compose` (the pressure valve) anchors at the repo root
(`--project-directory .` is required — compose otherwise anchors relative paths at the
first `-f` file's directory). This raw form has no edge — the edge exists only in
boatyard's materialized assembly.

The `tree-<sha>` image tags `up` resolves the compose slots into must exist before it
runs — the working-tree shas can name tags that have never been built or pushed, and the
pull fails with `not found`. Build the missing services first (`uv run boatyard build
--targets api`).

It reads `boatyard.values.yaml` the same way any assembly does (`KEYCLOAK_ADMIN_PASSWORD`
consumed only by the keycloak artifact — keycloak and its configurator ride that option;
the anonymous core never sees it). Reach the api through the edge at
`http://localhost:8443/schema` (or the values file's `gateway_port:` override when set).

## Deploy: Kubernetes

```bash
kubectl apply -f stack/generated/k8s/manifests.yaml
```

The cluster is a precondition. On the real cluster Argo CD applies this file (see the infra
repo); the Pulumi program creates the `placeframe-secrets` Secret every manifest references
and installs the Hetzner CSI driver behind the `hcloud-volumes` storage class. No host
ports: reach the api with `kubectl port-forward deploy/api 8000:8000`. The cluster edge is
the Pulumi Ingress (`/` → api, `/auth` and `/auth/*` → keycloak behind a StripPrefix
middleware); keycloak itself is the `keycloak` Deployment from this artifact — there is no
Keycloak CR, no operator, and no ExternalName alias, so `keycloak:8080` resolves natively
on both tiers.

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
`AUTH_JWKS_URL` as `http://keycloak:8080/realms/placeframe-dev/protocol/openid-connect/certs`
(the workload's own Service name — the same reference on both tiers).

k3d pulls through Docker Hub, whose unauthenticated rate limit is low enough to fail a cold
cluster; preload slow images with `docker save <image> | docker exec -i k3d-score-poc-server-0
ctr -n k8s.io images import -`.

## Divergence between the renderings

One authored source, two renderings — the deliberate differences, so nobody "fixes" them:

- Secrets: compose emits `${VAR:?err}` slots filled from the per-run env file at run time; k8s emits
  `secretKeyRef` wiring into `placeframe-secrets`. Each tier's native mechanism.
- Liveness/readiness: chart probes (loki, grafana) on k8s vs compose healthchecks; the
  built workloads declare `boatyard/probe-adapter` and boatyard's built-in
  template converts their httpGet probes into compose healthchecks.
- Host publishes ride the root config's `ports:` (api and lease-server localhost-bound
  debug ports, the seaweedfs-admin console) and the `gateway_port:` key's door publish —
  all compose-only, all consumer config; the k8s edge is the Pulumi-owned Ingress
  (`PUBLIC_URL` host, cert-manager issuer — per-site and Secret-resident, un-committable
  in a deterministic artifact).
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
tier in boatyard; re-evaluate if resource types
proliferate.

## Constraints

- **Provisioner sources are authored in mapping form; string form is compiler output.**
  `state`/`outputs`/`volumes`/`services`/`manifests` are authored as real YAML mappings and
  lists, compiled to score's YAML-in-a-string form in a per-run tempdir at generation —
  compiled output never goes back into a source. Single-key authoring markers ride in
  provisioner manifests and chart values alike: `include:`/`include-yaml: <repo-root-relative
  path>` inserts a file's bytes verbatim / parsed structure; `dockerfile: <repo-root-relative
  path>` composes the built-image reference (repository + directory stem + declared variant
  + the sha env slot) for provisioner `image:` fields; `lock: NAME`/`lock-image: NAME`
  substitutes a `boatyard.lock.yml` entry — the full digest reference for provisioner
  `image:` fields, or the registry/repository/tag/digest fields chart values
  want (`digest_field: sha` for grafana's bare-hex spelling) — object-typed image
  values only. Charts whose values schema types image fields as strings (the
  keycloak-operator chart: `operator.image`, `operator.envs.*`) take `lock: NAME`
  instead; the object form fails their values validation. `dockerfile:` is a
  provisioner-manifest marker — chart values take `lock:`/`lock-image:` only. The lock is the k8s
  provisioners' single digest source: they have no runtime env-file, so no compose-style
  `${VAR}` slot is available there.
- **K8s config content arrives by inclusion, never hand mirrors.** The alloy ConfigMap
  body is `include: workloads/alloy/config.alloy`; the loki chart's entire config is the
  committed `workloads/loki/config.yaml` through the `structuredConfig` full-override in
  `values/loki.yaml` (the chart's templated config is blanked; the chart validator still
  demands a structured `schema_config`, which is why the override rides `structuredConfig`
  rather than the `loki.config` string); grafana's datasources ride `include-yaml:`. One
  committed file feeds both renderings — no standing copy to keep in sync.
- **The mint list is derived, never authored.** generate-score walks the generated k8s
  artifact's `secretKeyRef`s into `placeframe-secrets` and writes
  `stack/generated/secrets.txt` — the exact key set that Secret must contain; a
  compose-only rendering mints an empty list. No secrets vocabulary is declared anywhere.
- **Compose artifacts are hermetic: zero host-filesystem references.** score-compose
  materializes workload `files:` as binds into its state dir; boatyard's post-pass
  rewrites every bind into a top-level `configs.content` entry with each `$` doubled (compose
  interpolation would otherwise eat loki's `${VAR}` and caddy's `{$VAR}`). A bind surviving in
  a generated compose is a bug.
- **No secret resolves at generation time.** Compose provisioners emit literal `${VAR:?err}`
  slots that docker fills from the per-run env file at run time (boatyard.values.yaml is the single credential
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
  config, the entrypoint wrapper's rendered audit sink, the edge's auth routes and the
  configurator's `KEYCLOAK_URL`); renaming one breaks the stack at runtime, not at
  generation. The compose services ride bare (`keycloak`) and the consumer's assembly
  attaches each to the shared network under an entry-prefixed alias, so the same bare
  spelling resolves on both tiers — the compose service name and the k8s Service. **Bucket names are load-bearing contract names
  the same way**: `captures`, `reconstructions`, `loki`, unprefixed in both tiers. The s3
  provisioners create exactly that set (initializer `S3_BUCKETS`) and expose
  `bucket`/`captures_bucket` as resource outputs the api consumes; loki's committed config
  addresses the `loki` bucket by literal, so the provisioner list and that config must
  stay in agreement.
- **The realm is converged post-boot by the configurator in both tiers.** The
  auth-initializer image waits for keycloak's admin API, then creates or updates the
  realm from `workloads/auth-initializer/realm-export/placeframe.json` — substituting the
  `${KEYCLOAK_*}` and `${PUBLIC_URL}` slots from its env (compose env-file slots, k8s
  `secretKeyRef`s; the mint list carries the three lifespan keys). The file-import path
  is dead: the realm-configurator Job is a bare Job, and KeycloakRealmImport cannot
  resolve slots. The export seeds no users; the optional `SEED_TEST_USERS` pairs
  (compose soft passthrough, k8s mint-list key) are create-or-updated by the
  configurator with `firstName`/`lastName`/`email` populated — a fresh 26.8.1 realm's
  default profile requires all three, or the first direct grant fails.
  `KEYCLOAK_ADMIN_PASSWORD` is consumed by both renderings.
- **The realm name and the magic uids are load-bearing constants — named here, not
  linted.** The keycloak realm `placeframe-dev` is baked into
  `workloads/auth-initializer/realm-export/placeframe.json` and every OIDC path derives
  from it. It is declared in the two oidc-issuer provisioner states and the compose
  observability state (bodies template `{{ .State.realm }}`); it never leaves the
  bundle — the door does no token validation, and the eventual oauth2-proxy validator
  sidecar gets it baked at generation the same way. Uids: loki runs as uid 10001
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
- **Workload files never author an `image:` line.** Each container declares exactly one source
  as a metadata annotation — `boatyard/dockerfile: <container>=<repo-root-relative
  Dockerfile path>` for built images or `boatyard/lock: <container>=<base_images key>`
  for pulled ones — and `generate-score` injects the composed reference (repository + stem +
  derived variant + tag: the per-machine tree slot on compose, the pin or tree tag on k8s)
  before the score tools see the document. The files are therefore not standalone-valid
  score documents; `${API_SHA}`-style slots survive only as data uses (`SERVICE_VERSION`).
- **Dev behavior toggles bake as literals; there is no dev overlay.** The api and
  lease-server `variables:` carry `RELOAD`/`DEBUG_API`/`DEBUG_WAIT_API` (and the
  lease-server's `DEBUG_LEASE_SERVER`/`DEBUG_WAIT_LEASE_SERVER` twins) at prod-safe
  `"false"` literals, and their entrypoints read exactly those names — debug-in-prod is
  unrepresentable. The overlay that would flip them is unbuilt, trigger-gated design
  in boatyard's `design/dev-overlay.md`.
- **No `depends_on` across workloads**: score has no such concept. Provisioner services gate
  on each other's health; workloads gate on the auto-emitted `wait-for-resources` service,
  whose alpine default image is redirected into the global `BOATYARD_BARRIER_IMAGE` slot by
  the barrier pass — filled from boatyard's own pin at bring-up, so the artifact carries no
  unpinned image and no lock entry. The gate emits only where a provisioner carries services, so the
  ngrok artifact carries none.
- **The relay is a compose-only workload** (`ngrok.yaml`, absent from the k8s workload
  list). Score workload specs cannot carry runtime `${VAR}`
  slots — score validates placeholders as dotted resource references — so the relay
  credentials ride the outputs-only `compose/tunnel.yaml` provisioner (`type:
  tunnel-config`, no services, no k8s twin) exactly like the placeframe-config valve.
  ngrok's domain cannot be a resource ref inside `command` either (score does not
  substitute there and `$$`-escapes the slot to a compose literal), so its command is a
  `/bin/sh -c` wrapper expanding `${NGROK_DOMAIN:-}` inside the container from the
  passthrough env. The workload's `boatyard/restart: on-failure` annotation (read
  by boatyard's built-in restart template, the value validated against the compose
  restart-policy enum at generation) sets `restart: on-failure` — the
  relay is a long-lived agent whose control endpoint flaps. No compose profile exists
  anywhere in the four artifacts; the relay forwards to the gateway by its reserved
  service name (`http://boatyard-gateway:8443`), so an assembly without it simply has
  no public edge.
- **Third-party k8s stamp-outs are charts where an OCI chart exists** — loki and grafana
  render from tag-form upstream-native OCI refs declared in `boatyard.yml`'s root
  `k8s.charts` map (`oci://host/path:tag`), resolved to digests through the `{NAME}_CHART`
  entries the `boatyard lock` verb writes into `boatyard.lock.yml` — generation renders the
  lock's mirror-prefixed digest ref (`helm template` against it), so a declared chart
  without its lock entry refuses at generation naming the relock path. The CI mirror job
  copies chart declarations like image declarations; declaring a chart the mirror job has
  not copied yet makes k8s generation fail until it runs. Keycloak runs as the workload
  Deployment (no chart — the operator managed a statefulness keycloak doesn't have).
  Chart values never carry secret values: they reference the existing `placeframe-secrets`
  Secret (`envValueFrom`/`extraEnvFrom`/`existingSecret`) or `${VAR}` config slots
  expanded in-container. Alloy has no upstream OCI chart, so `k8s/observability.yaml`
  hand-writes its Deployment + Service + ConfigMap (config body by inclusion; see above).
- **Restart policies stay undeclared everywhere except the relay** — workload services and
  provisioner services rely on compose's default; the one sanctioned exception is the
  relay's `boatyard/restart: on-failure` annotation. The hand stack's posture is
  identical.
- **Argo CD Jobs**: create/migrate/bucket Jobs carry `argocd.argoproj.io/hook: Sync` +
  `BeforeHookCreation` because a Job's spec.template is immutable — without the hook an image
  tag bump makes every later sync fail with "field is immutable". Re-runs are safe (create is
  idempotent, the migrator is a no-op on matching schemas, the bucket initializer only creates
  missing buckets).
- **GPU plumbing is annotation-driven per variant.** A workload declares
  `metadata.annotations.boatyard/gpu: "true"` — the single declaration of
  accelerator-carrying behavior. Everything else derives: the variant fragment in the
  injected image reference (the core group's variant options per compose output, fixed to
  `cuda` for the k8s rendering),
  boatyard's built-in gpu device templates (registered per the rendering's variant:
  NVIDIA device reservations for cuda, `/dev/kfd` + `/dev/dri` with the render/video
  groups for rocm), and boatyard's built-in gpu-pod template on k8s. The k8s plumbing
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
  reconstructor always-on). Boatyard's built-in scale-to-zero template sets
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
  asserts against the committed `stack/generated/k8s/manifests.yaml`: the GPU patches, the
  service-port URLs, and the KEDA CRs — and that no KEDA operator documents ride the
  artifact. The compose bundle split has its twin in
  `scripts/tests/test_score_compose_generation.py`, asserting the committed artifacts:
  four outputs, zero profiles, zero binds, zero published ports, the bare service
  names with no networks, the tier-neutral keycloak shapes (lock-pinned
  image, poll-gated configurator), and the relay restart/passthrough mechanics.
  Freshness itself is gated by `boatyard generate-score --check` in CI, so the tests
  assert structure against what is committed.

## See also

- [`boatyard's `AGENTS.md`](https://github.com/outernet-foundation/boatyard/blob/main/AGENTS.md)
  — `generate-score` internals (placeholder expansion, bind inlining, determinism suite).
- `workloads/AGENTS.md` — the running stack's service inventory, data flow, auth model.
