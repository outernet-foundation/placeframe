# Score: one source, both Docker and Kubernetes

Placeframe's server stack runs today as Docker Compose (`uv run up`). This directory
evaluates [Score](https://docs.score.dev) as a way to describe each service **once**
and generate both a runnable Docker `compose.yaml` **and** Kubernetes manifests from
that single description — so the project can move toward a Kubernetes/SaaS deployment
without hand-maintaining two definitions that drift apart.

It is a proof-of-concept covering a slice of the stack: **api**, **lease-server**, and
the **gateway** (Caddy), backed by a **postgres** database (real `placeframe_*` roles and
schema, via a custom provisioner) and **MinIO** object storage. From the authored
workload files, `score-compose` produces Docker output and `score-k8s` produces
Kubernetes output; the services boot, serve `/health`, and handle real data operations on
both, reachable through the gateway. See `.pulsar/memories/score-poc.md` for what was
proven, what was not ported, and the open infra decision.

## Quick start (the `score-up` / `score-down` wrappers)

Two `uv run` commands wrap this entire runbook — first-time setup, generate, and
bring-up/tear-down — so you don't run the raw `score-compose` / `k3d` / `kubectl`
commands by hand (they still need the prerequisites below installed):

```bash
uv run score-up                  # Docker (default): spin up
uv run score-up --target k3s     # Kubernetes (throwaway k3d cluster): spin up
uv run score-down                # Docker: stop and wipe volumes
uv run score-down --target k3s   # Kubernetes: delete the cluster
```

- **Docker** publishes the gateway to your machine — open `http://localhost:8443/schema/swagger`.
- **k3s** has no published host port; after `score-up --target k3s`, connect with
  `kubectl port-forward deploy/gateway 8443:8443`, then open `http://localhost:8443`.
- The first run does the one-time `init` automatically; later runs skip it. `score-up`
  is re-runnable — it only creates the k3d cluster if one isn't already there.

How the wrappers work, at a glance:

| | `score-up --target docker` | `score-up --target k3s` |
|---|---|---|
| generate | `score-compose generate` → `compose.yaml` | `score-k8s generate` → `manifests.yaml` |
| bring up | `docker compose up -d` | create k3d cluster → preload images → `kubectl apply` → wait for the migrate Job + api |
| images | already local | preloaded into the node's containerd (list scraped from the manifest + k3s system images), so no Docker Hub pull is needed at deploy time |

The commands live in `placeframe-stack` (`score_up.py` / `score_down.py`) — a thin driver
over the steps documented below, which remain the reference for *what* the wrappers run
and for any manual or one-off work.

## What's in this directory

The authored workload files, the two custom-provisioner files, and the
`restart-policy.tpl` compose patch are the source. Everything else is generated or
tool-managed:

| Path | Origin | In git? |
|------|--------|---------|
| `api.yaml`, `lease-server.yaml`, `gateway.yaml` | authored — the workload contracts | yes |
| `placeframe-postgres.provisioners.yaml` | authored — custom postgres provisioner (Docker) | yes |
| `placeframe-postgres.k8s.provisioners.yaml` | authored — custom postgres provisioner (Kubernetes) | yes |
| `restart-policy.tpl` | authored — compose-only patch template | yes |
| `compose.yaml` | `score-compose generate` | no — gitignored (resolved secrets) |
| `manifests.yaml` | `score-k8s generate` | no — gitignored (resolved secrets) |
| `.score-compose/`, `.score-k8s/` | `init` | state gitignored; provisioner catalogs regenerable |

Secret values (the generated DB/role passwords, MinIO keys) appear only in the generated
output and the `state.yaml` files — never in the authored files. Those paths are
gitignored, so nothing sensitive is committed.

> **Run every `score-*` command from inside `score/`.** `generate` looks for the
> `.score-compose/` / `.score-k8s/` state directory in the current directory; running
> from the repo root fails with a "project not initialised" error.

## Prerequisites

- **`score-compose` 0.42.0** and **`score-k8s` 0.15.0** on PATH (install the exact
  release binaries and checksum-verify them — pinned, no moving versions).
- **Docker** — for the Docker target.
- **[`k3d`](https://k3d.io) 5.x** and **`kubectl`** — for the Kubernetes target (any
  conformant cluster works; k3d is the throwaway local option).
- The service images (`api`, `lease-server`, `gateway`, `postgres`, `database-manager`,
  `database-migrator`) available locally (via `uv run build`) or registry access. They
  are private on `ghcr.io`, so a cluster without ghcr credentials needs them imported
  (see the Kubernetes section).

## First-time setup

The `.score-compose/` and `.score-k8s/` state directories are gitignored, so after a
fresh clone you initialise both projects once. Each `init` **registers the custom
`placeframe-postgres` provisioner** for that target — this is mandatory: the workloads
declare `resources.db.type: placeframe-postgres`, so without it `generate` fails with an
"unknown resource type" error. The compose project additionally registers
`restart-policy.tpl`, a patch adding `restart: unless-stopped` to the api service (a
compose-only concern: Kubernetes restarts crashed pods natively).

```bash
cd score
score-compose init --project placeframe --no-sample \
  --provisioners ./placeframe-postgres.provisioners.yaml \
  --patch-templates ./restart-policy.tpl
score-k8s init --no-sample \
  --provisioners ./placeframe-postgres.k8s.provisioners.yaml
```

Editing a provisioner or the patch later? Re-run its `init` to re-register the updated
file (the tool copies it into the state dir; it does not track the file live).

## Run on Docker

```bash
cd score
score-compose generate api.yaml lease-server.yaml gateway.yaml \
  --publish 8000:api:8000 --publish 8443:gateway:8443
docker compose -p score-poc up -d
```

Then connect through the **gateway** on **`http://localhost:8443`** (the real front
door — Caddy reverse-proxying to the api), or the api directly on `http://localhost:8000`:

- `/health` → `{"status":"ok"}`
- `/schema/swagger` → interactive API explorer
- `/schema/openapi.json` → raw OpenAPI spec

Stop it: `docker compose -p score-poc down -v`

`-p score-poc` keeps this isolated from the real `uv run up` stack (project
`placeframe`), so the two never collide.

## Run on Kubernetes (throwaway k3d cluster)

```bash
cd score
score-k8s generate api.yaml lease-server.yaml gateway.yaml

k3d cluster create score-poc --no-lb --k3s-arg "--disable=traefik@server:0"

# Every service image is private on ghcr, so import them all (a cluster with ghcr
# credentials pulls them instead and you can skip this). postgres, database-manager
# and database-migrator are what the custom placeframe-postgres provisioner needs.
for svc in api lease-server gateway postgres database-manager database-migrator ; do
  k3d image import ghcr.io/outernet-foundation/placeframe/$svc:<SHA> -c score-poc
done

kubectl apply -f manifests.yaml
kubectl wait --for=condition=complete job/pf-postgres-create  --timeout=150s
kubectl wait --for=condition=complete job/pf-postgres-migrate --timeout=150s   # applies the schema
kubectl rollout status deployment/api --timeout=150s
```

The `pf-postgres` StatefulSet plus the `pf-postgres-create` and `pf-postgres-migrate`
Jobs all come from the custom postgres provisioner. The Jobs self-order by retrying
until postgres is ready (there is no `depends_on` in Kubernetes), then complete.

Then connect via a port-forward (leave it running in its own terminal):

```bash
kubectl port-forward deploy/gateway 8443:8443    # -> http://localhost:8443/health
```

Stop it: `k3d cluster delete score-poc`

The import step is needed because these images are private and not in the cluster's
registry — a production cluster with ghcr credentials pulls them normally.

### If pods hang `Pending` or `ImagePullBackOff` (Docker Hub rate limit)

Repeated `k3d cluster create` cycles can exhaust Docker Hub's anonymous pull limit, and
then a fresh k3d node cannot pull **its own k3s system images** — most visibly
`rancher/local-path-provisioner` and its `rancher/mirrored-library-busybox` volume
helper. Without the storage provisioner, every PVC stays `Pending` and the postgres /
minio StatefulSets never schedule (the api/gateway Deployments still run, which makes
it look like only "half" the stack came up).

`k3d image import` is unreliable for these (it can report success without the image
landing in the node's containerd). The dependable fix is to load every needed image
straight into the node's containerd via `ctr`, right after creating the cluster and
before applying — so deploy time needs zero Docker Hub:

```bash
NODE=k3d-score-poc-server-0
for img in \
  rancher/local-path-provisioner:v0.0.36 \
  rancher/mirrored-library-busybox:1.37.0 \
  quay.io/minio/minio \
  ghcr.io/outernet-foundation/placeframe/api:<API_SHA> \
  ghcr.io/outernet-foundation/placeframe/lease-server:<LEASE_SERVER_SHA> \
  ghcr.io/outernet-foundation/placeframe/gateway:<GATEWAY_SHA> \
  ghcr.io/outernet-foundation/placeframe/postgres:<POSTGRES_SHA> \
  ghcr.io/outernet-foundation/placeframe/database-manager:<DATABASE_MANAGER_SHA> \
  ghcr.io/outernet-foundation/placeframe/database-migrator:<DATABASE_MIGRATOR_SHA> ; do
  docker pull "$img"   # host is not rate-limited the same way; skip if already local
  docker save "$img" | docker exec -i $NODE ctr -n k8s.io images import -
done
kubectl -n kube-system rollout restart deploy/local-path-provisioner   # pick up the image
```

Verify with `docker exec $NODE crictl images`. The system-image versions
(`local-path-provisioner`, `busybox`) track the k3s release — read the exact tags from
`kubectl -n kube-system get deploy local-path-provisioner -o yaml` and the
`local-path-config` ConfigMap if they differ. `quay.io/minio/minio` is the default `s3`
provisioner's own image and is intentionally unpinned by that provisioner (see the Image
pinning gap below); preload whatever ref it currently emits.

## What the provisioners stand up

- **`db` (type: placeframe-postgres)** — a **custom** provisioner (in the two
  `placeframe-postgres.*.provisioners.yaml` files) that stands up the **real Placeframe
  postgres image** (PostGIS, SHA-pinned) and runs the **real placeframe tooling** to set
  it up, rather than a vanilla empty database:
  1. `database-manager` (the `create-database` op) creates the database and the four
     `placeframe_*` roles (`owner`, `api_user`, `auth_user`, `orchestration_user`);
  2. `database-migrator` (`pg-schema-diff`) applies the schema — the actual tables.

  On compose these are the `pf-postgres` service plus `pf-postgres-create` and
  `pf-postgres-migrate` (`restart: "no"`) services; on k8s, a Secret + StatefulSet +
  Service plus two Jobs. The postgres runs its image's `entrypoint-wrapper.sh` so PostGIS
  is trusted and `placeframe_owner` (a non-superuser) can create the extension during
  migration. Each workload consumes role-specific outputs
  (`${resources.db.api_username}`, `${resources.db.api_password}`, …); `api` and
  `lease-server` share one database via a common resource `id` (`placeframe-db`).
  **Result:** real data operations work, not just `/health`.
- **`bucket` (type: s3)** — the **default** provisioner: a real MinIO
  (`quay.io/minio/minio`) with a service account, access/secret keys, and a bucket,
  created by an init step (a `restart: "no"` service on compose, a `Job` on k8s). No
  custom provisioner needed — object storage works out of the box.

## Image pinning gap

Every image *we* author or provision is SHA-pinned: the workload images (`api`,
`lease-server`, `gateway`) and — because postgres now uses the custom provisioner — the
`postgres`, `database-manager`, and `database-migrator` images too. The remaining
unpinned references all come from the **default `s3` provisioner** and the
compose-side resource-wait gate, which violate the repo-wide "pin everything / no
`:latest`" rule:

- `quay.io/minio/minio` — no tag (effectively `:latest`)
- `alpine` (the compose resource-wait gate) — no tag, no registry host

Closing these means giving MinIO the same custom-provisioner treatment postgres got
(referencing a digest-pinned image), or rewriting the image fields at generate time
from `.env.lock`. Acceptable for a throwaway PoC; a blocker for real adoption.

## Regenerating

The authored files (the workloads + provisioners) are the source of truth. After editing
one, re-run the matching `generate` command; the generated `compose.yaml` /
`manifests.yaml` are overwritten in place. Resource outputs (the generated role
passwords, MinIO keys, bucket name) are cached in the `state.yaml` files and reused
across runs, so credentials stay stable until the state directory is deleted.
