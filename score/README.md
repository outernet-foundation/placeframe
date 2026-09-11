# Score: one source, both Docker and Kubernetes

Placeframe's server stack runs today as Docker Compose (`uv run up`). This directory
evaluates [Score](https://docs.score.dev) as a way to describe each service **once** and
generate both a runnable Docker `compose.yaml` **and** Kubernetes manifests from that one
description — so the project can move toward Kubernetes without hand-maintaining two
definitions that drift apart. It is a proof-of-concept covering a slice of the stack:
**api**, **lease-server**, and the **gateway** (Caddy), backed by **postgres** (real
`placeframe_*` roles and schema) and **MinIO** object storage.

## Generate

Generation is a separate step from deployment. `generate-score` writes the artifacts and
deploys nothing.

```bash
uv run generate-score                  # both artifacts
uv run generate-score --target compose # score/compose.yaml only
uv run generate-score --target k8s     # score/deploy/manifests.yaml only
```

Both outputs are committed. Image tags resolve from `compute_service_shas` — the same
function `up` and `build-docker` use — which reads **committed** state (`git ls-tree HEAD`),
not your working tree. So the order is: commit the source change, then regenerate, then
commit the artifacts. Generating first produces artifacts built against the previous tree,
and CI will flag them.

Regeneration is deterministic: with no upstream change, `git status` comes back clean.

## Deploy: Docker

```bash
uv run up   --compose-file score/compose.yaml --gpu none
uv run down --compose-file score/compose.yaml --gpu none -v
```

`stack-lifecycle` needs no changes — `--compose-file` puts it on its consumer-stack path.
`--gpu none` is required, not optional: both commands default to `--gpu auto`, which calls
`detect_gpu()` and raises when neither `nvidia-smi` nor `rocminfo` is present. The Score
stack has no GPU services.

The generated compose reads the same `.env` as the hand-authored stack, so the two agree on
every credential — there is no separate set of Score passwords to keep in step.

Reach it at `http://localhost:8443/schema/swagger`.

## Deploy: Kubernetes

```bash
kubectl apply -f score/deploy/manifests.yaml
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
  --from-literal=MINIO_ACCESS_KEY=$(openssl rand -hex 8) \
  --from-literal=MINIO_SECRET_KEY=$(openssl rand -hex 16) \
  --from-literal=KEYCLOAK_ADMIN_PASSWORD=$(openssl rand -hex 16) \
  --from-literal=PUBLIC_URL=http://localhost:8443 \
  --from-literal=AUTH_MODE=disabled \
  --from-literal=AUTH_AUDIENCE=placeframe-api \
  --from-literal=AUTH_ISSUER_URL= --from-literal=AUTH_URL= --from-literal=AUTH_TOKEN_URL= \
  --from-literal=DEPLOYMENT_ENVIRONMENT=development \
  --from-literal=KEYCLOAK_HOSTNAME=http://localhost:8443/auth

uv run generate-score --local --target k8s
kubectl apply -f score/manifests.yaml
```

`--local` writes to `score/manifests.yaml`, which is gitignored, and leaves the committed
`score/deploy/manifests.yaml` untouched. That separation is deliberate: `local-path` reaching
the real cluster leaves the Postgres and MinIO volumes unbindable on the next rebuild.

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

## CI enforces that the artifacts match their source

`preflight` runs `generate-score` and fails when `score/` comes back dirty, in the same shape
as its datamodel- and client-codegen checks. It checks and fails; it never commits, because
CI in this repo must not create commits on any branch. When it fires, run `uv run
generate-score` locally and commit the result.

Two things make that gate viable. `score/.score-k8s/state.yaml` is committed, because
`score-k8s` mints a random uid per workload on first sight and emits it as the
`app.kubernetes.io/instance` label — without the state file a fresh checkout regenerates
different manifests. And `generate-score` sorts the emitted documents, because `score-k8s`
emits workloads in Go map order, which is randomised.

## What's in this directory

The authored workload files, the custom-provisioner files, and the `restart-policy.tpl`
compose patch are the source; everything else is generated or tool-managed.

| Path | Origin | In git? |
|------|--------|---------|
| `api.yaml`, `lease-server.yaml`, `gateway.yaml` | authored — the workload contracts | yes |
| `placeframe-postgres.provisioners.yaml` | authored — custom postgres provisioner (Docker) | yes |
| `placeframe-postgres.k8s.provisioners.yaml` | authored — custom postgres provisioner (k8s, StatefulSet) | yes |
| `placeframe-postgres-cnpg.k8s.provisioners.yaml` | authored — alternative postgres provisioner (k8s, CloudNativePG) | yes |
| `placeframe-s3.provisioners.yaml` | authored — fixed-name MinIO provisioner, overrides the built-in `s3` | yes |
| `../docker/postgres-cnpg/Dockerfile` | authored — trusted-PostGIS operand image for CNPG | yes |
| `restart-policy.tpl` | authored — compose-only patch template | yes |
| `compose.yaml`, `deploy/manifests.yaml` | generated | yes — the reviewed artifacts |
| `.score-k8s/state.yaml` | `init` + `generate` | yes — pins the per-workload uids so generation reproduces |
| `.score-compose/`, rest of `.score-k8s/` | `init` | no — rewritten on every run |

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
  random credentials at generation time and uses a random service and bucket name that loki
  (its config hardcodes `minio:9000` and bucket `loki`) cannot reach.

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

  The operand image (`../docker/postgres-cnpg/Dockerfile`, tag `14-trusted`) exists because
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

MinIO is no longer on this list: the built-in `s3` provisioner's untagged
`quay.io/minio/minio` was replaced by `placeframe-s3.provisioners.yaml`, which is
digest-pinned.

## See also

- `.pulsar/memories/score-poc.md` — what the PoC proved, what was not ported, and the open
  infra decision.
