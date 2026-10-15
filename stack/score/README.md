# Score: one source, both Docker and Kubernetes

Placeframe's server stack runs today as Docker Compose (`uv run up`). The authored
sources here describe each service **once** and generate both a runnable Docker compose
file **and** Kubernetes manifests from that one description — the compose stack and the
k8s manifests are two renderings of one input, so they cannot drift from each other.
Coverage is a slice of the stack: **api**, **lease-server**, and the **gateway** (Caddy),
backed by **postgres** (real `placeframe_*` roles and schema) and **SeaweedFS** object
storage.

## Layout

`stack/score/` is the authored tier (workload files, custom provisioners, the
`restart-policy.tpl` compose patch). `stack/generated/` is the compiled tier:
`compose/compose.yaml` and `k8s/manifests.yaml` are the committed artifacts. Hand compose
files at the repo root stay authored until full-stack Score coverage ports them.

## Generate

Generation is a separate step from deployment. `generate-score` writes the artifacts and
deploys nothing.

```bash
uv run generate-score                  # both artifacts
uv run generate-score --target compose # stack/generated/compose/compose.yaml only
uv run generate-score --target k8s     # stack/generated/k8s/manifests.yaml only
```

Both outputs are committed. Image tags resolve from `compute_service_shas` — the same
function `up` and `build-docker` use — which reads **committed** state (`git ls-tree HEAD`),
not your working tree. So the order is: commit the source change, then regenerate, then
commit the artifacts. Generating first produces artifacts built against the previous tree,
and CI will flag them.

Regeneration is deterministic: with no upstream change, `git status` comes back clean.

Regeneration needs a docker-devkit release carrying the bind→`configs.content` converter:
the gateway's snippet `files:` come out of `score-compose` as binds into its state
directory, and the converter inlines them so the compose artifact carries zero
host-filesystem references. placeframe's `uv.lock` carries that release (docker-devkit
0.4.4), so the committed artifacts are always generated through the converter.

## Deploy: Docker

The generated compose has no declared lifecycle in `docker-devkit.yaml` (the `lifecycle:`
section drives the hand-authored stack), so bring it up through the raw `docker compose`
pressure valve, anchored at the repo root:

```bash
docker compose --project-directory . \
  --env-file .env --env-file workloads/images.lock \
  -f stack/generated/compose/compose.yaml up -d
docker compose --project-directory . \
  --env-file .env --env-file workloads/images.lock \
  -f stack/generated/compose/compose.yaml down --remove-orphans
```

`--project-directory .` is required: compose otherwise anchors relative paths at the
directory of the first `-f` file, and the generated file lives in a nested tree.

The generated compose reads the same `.env` as the hand-authored stack, so the two agree on
every credential — there is no separate set of Score passwords to keep in step.

Reach it at `http://localhost:8443/schema/swagger`.

## Deploy: Kubernetes

```bash
kubectl apply -f stack/generated/k8s/manifests.yaml
```

The cluster is a precondition, not part of the deploy. On the real cluster, Argo CD applies
this file itself (see the infra repo); the Pulumi program also creates the `placeframe-secrets`
Secret every manifest references and installs the Hetzner CSI driver that provides
`hcloud-volumes`.

There is no host port, so reach the gateway with
`kubectl port-forward deploy/gateway 8443:8443`.

### Against a local cluster

A PersistentVolumeClaim names the *kind* of disk it wants. The default is `hcloud-volumes`,
Hetzner's CSI class; a local cluster has no such class, so its PVCs sit `Pending` forever and
nothing starts. k3s offers `local-path` instead:

```bash
k3d cluster create score-poc --no-lb --k3s-arg "--disable=traefik@server:0"

# No Pulumi locally, so mint the Secret the manifests reference:
kubectl create secret generic placeframe-secrets \
  --from-literal=POSTGRES_ADMIN_PASSWORD=$(openssl rand -hex 16) \
  --from-literal=DATABASE_OWNER_PASSWORD=$(openssl rand -hex 16) \
  --from-literal=DATABASE_API_USER_PASSWORD=$(openssl rand -hex 16) \
  --from-literal=DATABASE_AUTH_USER_PASSWORD=$(openssl rand -hex 16) \
  --from-literal=DATABASE_ORCHESTRATION_USER_PASSWORD=$(openssl rand -hex 16) \
  --from-literal=S3_ACCESS_KEY=$(openssl rand -hex 8) \
  --from-literal=S3_SECRET_KEY=$(openssl rand -hex 16) \
  --from-literal=KEYCLOAK_ADMIN_PASSWORD=$(openssl rand -hex 16) \
  --from-literal=PUBLIC_URL=http://localhost:8443 \
  --from-literal=AUTH_ISSUER_URL= \
  --from-literal=AUTH_AUTHORIZATION_ENDPOINT= --from-literal=AUTH_TOKEN_ENDPOINT= \
  --from-literal=DEPLOYMENT_ENVIRONMENT=development \
  --from-literal=KEYCLOAK_HOSTNAME=http://localhost:8443/auth

uv run generate-score --local --target k8s
kubectl apply -f stack/generated/k8s/manifests.local.yaml
```

`--local` writes to `stack/generated/k8s/manifests.local.yaml`, which is gitignored, and
leaves the committed `stack/generated/k8s/manifests.yaml` untouched. That separation is
deliberate: `local-path` reaching the real cluster leaves the Postgres and SeaweedFS
volumes unbindable on the next rebuild.

k3d pulls through Docker Hub, whose unauthenticated rate limit is low enough to fail a cold
cluster. If pulls fail, preload the image into the node:

```bash
docker pull <image> && docker save <image> \
  | docker exec -i k3d-score-poc-server-0 ctr -n k8s.io images import -
```

Tear down with `k3d cluster delete score-poc`.

**Prerequisites:** `score-compose` 0.42.0 and `score-k8s` 0.15.0 on PATH, plus Docker; for
the Kubernetes path also [`k3d`](https://k3d.io) 5.x and `kubectl`. The service images must
be available locally (`uv run build`) or pullable from `ghcr.io`.

## CI does not verify the generated artifacts

The staleness gate is disabled: the check and its score-tool fetch were dropped from
`scripts/preflight.py` when the repo preflight was inlined there. The artifacts embed `tree-<sha>` image
tags resolved from `compute_service_shas`, so every change inside a service's build context —
a dependency-lock bump included — re-stales the committed output. Rather than pair every such
change with a regeneration commit, regeneration is a manual step: follow the order in Generate
above (commit the source change, regenerate, commit the artifacts).

Generation remains deterministic: `generate-score` sorts the emitted documents (score-k8s
emits workloads in Go map order, which is randomised), and the tool state dirs are per-run
temp with the per-workload instance suffixes rewritten to name-derived hashes — a fresh
checkout regenerates byte-identical artifacts with nothing stateful committed.

## What's in this directory

The authored workload files, the custom-provisioner files, and the `restart-policy.tpl`
compose patch are the source; everything else is generated or tool-managed.

| Path | Origin | In git? |
|------|--------|---------|
| `api.yaml`, `lease-server.yaml`, `gateway.yaml` | authored — the workload contracts | yes |
| `placeframe-postgres.provisioners.yaml` | authored — custom postgres provisioner (Docker) | yes |
| `placeframe-postgres.k8s.provisioners.yaml` | authored — custom postgres provisioner (k8s, StatefulSet) | yes |
| `placeframe-postgres-cnpg.k8s.provisioners.yaml` | authored — alternative postgres provisioner (k8s, CloudNativePG) | yes |
| `oidc-issuer.provisioners.yaml` | authored — OIDC issuer provisioner (Docker; dev keycloak) | yes |
| `oidc-issuer.k8s.provisioners.yaml` | authored — OIDC issuer provisioner (k8s, keycloak StatefulSet + auth-initializer) | yes |
| `placeframe-seaweedfs.provisioners.yaml` | authored — SeaweedFS provisioner (Docker), overrides the built-in `s3` | yes |
| `placeframe-seaweedfs.k8s.provisioners.yaml` | authored — SeaweedFS provisioner (k8s, StatefulSet + audit relay + bucket Job) | yes |
| `../workloads/postgres-cnpg/Dockerfile` | authored — trusted-PostGIS operand image for CNPG | yes |
| `restart-policy.tpl` | authored — compose-only patch template | yes |
| `../generated/compose/compose.yaml`, `../generated/k8s/manifests.yaml` | generated | yes — the reviewed artifacts |
| `.score-compose/`, `../generated/k8s/.score-k8s/` | tool state | no — per-run temp, torn down after generation |

Generation resolves no secret. The compose provisioners emit `${VAR:?err}` placeholders that
docker resolves from `--env-file` at run time, exactly as the hand-authored `compose.yml`
does; the k8s provisioners resolve every credential to an `encodeSecretRef` pointer into the
externally-managed `placeframe-secrets` Secret. Both artifacts are therefore safe to commit.

Image tags come from `compute_service_shas` at generation time — the same function `up` and
`build-docker` use — so no `tree-<sha>` tag is ever hand-edited. The workload files carry
`${API_SHA}`-style placeholders for this and are not standalone-valid Score documents.

## What the provisioners stand up

- **`db` (type `placeframe-postgres`)** — a **custom** provisioner that stands up the real
  Placeframe postgres image (PostGIS, SHA-pinned) and runs the real Placeframe tooling
  rather than a vanilla empty database: `database-manager` creates the database and the
  four `placeframe_*` roles with their grants and row-level security, then
  `database-migrator` (`pg-schema-diff`) applies the schema. `api` and `lease-server`
  share one database via a common resource `id`. **Result:** real data operations work,
  not just `/health`.
- **`bucket` (type `s3`)** — a **custom** provisioner overriding the built-in, which mints
  random credentials at generation time and uses a random service and bucket name nothing
  in the stack can reach. The custom one stands up the real SeaweedFS stack — the `weed
  server` (master+filer+volume+S3 gate on 8333, S3 identity and fluent audit sink rendered
  from env by the entrypoint wrapper), the fluent audit relay, and the admin console — and
  converges the real buckets (`dev-captures`, `dev-reconstructions`, `loki`) with the real
  `s3-initializer` image. Service names are fixed (`seaweedfs`, `seaweedfs-audit`) because
  the wrapper's rendered audit sink and loki's config address them by DNS name. The k8s
  twin is the same shape without the admin console (no host ports to publish through):
  Service + StatefulSet, audit relay Deployment + Service, bucket Job.
- **`auth` (type `oidc-issuer`)** — named for the protocol, not the provider: the resource
  type says what the workloads need (a JWKS URL), the provisioner files say keycloak. A
  swapped issuer implementation registers a different provisioner for the same type.
  Compose gets a minimal dev keycloak; k8s gets a keycloak StatefulSet with the realm
  imported by the auth-initializer initContainer.

## Postgres backends: StatefulSet or CloudNativePG

Both use the same `placeframe-postgres` resource type, so the workloads are identical either
way; which one applies is set by whichever provisioner file is registered.

- **`statefulset`** (default) — a raw `StatefulSet` + Service + a create Job + a migrate
  Job, all authored directly.
- **`cnpg`** — [CloudNativePG](https://cloudnative-pg.io), a Kubernetes *operator* that
  manages postgres: the provisioner emits one `Cluster` object and the operator reconciles
  it into pods, storage, services, and managed failover. The key design choice is that it
  **reuses the same tooling** as the StatefulSet path — the `Cluster` only bootstraps a
  bare database and owner (with `enableSuperuserAccess`), then the same `database-manager`
  create Job applies all roles/grants/RLS and the same `database-migrator` Job applies the
  schema. The operator install and the operand-image build are manual steps.

  The operand image (`../workloads/postgres-cnpg/Dockerfile`, tag `14-trusted`) exists because
  CNPG runs its own instance manager, so PostGIS is marked *trusted* at build time (instead
  of via the StatefulSet image's runtime entrypoint) — letting the non-superuser
  `placeframe_owner` create the extension in the temporary databases `pg-schema-diff` uses.

## Known gap: image pinning

Every image *we* author or provision is SHA-pinned. The unpinned references all come from
tooling defaults and violate the repo-wide "pin everything / no `:latest`" rule — acceptable
for a throwaway PoC, a blocker for real adoption:

- `alpine` (the compose resource-wait gate) — no tag, no registry host.
- `placeframe-postgres-cnpg:14-trusted` (the CNPG operand image) — built locally, not
  registry-hosted or digest-pinned (the CI token cannot push to the placeframe `ghcr.io`
  namespace).

MinIO is gone from this tier entirely (SeaweedFS replaced it in both renderings); the
seaweedfs-path images are pinned — the built images by `tree-<sha>` tags, the audit relay
by the `SEAWEEDFS_AUDIT_IMAGE` lock hole (compose) and its mirror digest (k8s).

## See also

- `.pulsar/memories/score-poc.md` — what the PoC proved, what was not ported, and the open
  infra decision.
