# Score: one source, both Docker and Kubernetes

Placeframe's server stack runs today as Docker Compose (`uv run up`). This directory
evaluates [Score](https://docs.score.dev) as a way to describe each service **once**
and generate both a runnable Docker `compose.yaml` **and** Kubernetes manifests from
that single description — so the project can move toward a Kubernetes/SaaS deployment
without hand-maintaining two definitions that drift apart.

It is a proof-of-concept covering a slice of the stack: **api**, **lease-server**, and
the **gateway** (Caddy), backed by a **postgres** database and **MinIO** object storage.
From the authored workload files, `score-compose` produces Docker output and `score-k8s`
produces Kubernetes output; the services boot and serve `/health` on both, reachable
through the gateway. See `.pulsar/memories/score-poc.md` for what was proven, what was not
ported, and the open infra decision.

## What's in this directory

The authored workload files (`api.yaml`, `lease-server.yaml`, `gateway.yaml`) and the
`restart-policy.tpl` compose patch are the source. Everything else is generated or
tool-managed:

| Path | Origin | In git? |
|------|--------|---------|
| `api.yaml`, `lease-server.yaml`, `gateway.yaml` | authored — the workload contracts | yes |
| `restart-policy.tpl` | authored — compose-only patch template | yes |
| `compose.yaml` | `score-compose generate` | no — gitignored (resolved secrets) |
| `manifests.yaml` | `score-k8s generate` | no — gitignored (resolved secrets) |
| `.score-compose/`, `.score-k8s/` | `init` | state gitignored; provisioner catalogs regenerable |

Secret values (the generated DB password, MinIO keys) appear only in the generated
output and the `state.yaml` files — never in `api.yaml`. Those paths are gitignored,
so nothing sensitive is committed.

> **Run every `score-*` command from inside `score/`.** `generate` looks for the
> `.score-compose/` / `.score-k8s/` state directory in the current directory; running
> from the repo root fails with a "project not initialised" error.

## Prerequisites

- **`score-compose` 0.42.0** and **`score-k8s` 0.15.0** on PATH (install the exact
  release binaries and checksum-verify them — pinned, no moving versions).
- **Docker** — for the Docker target.
- **[`k3d`](https://k3d.io) 5.x** and **`kubectl`** — for the Kubernetes target (any
  conformant cluster works; k3d is the throwaway local option).
- The `api` image available locally (via `uv run build`/`up`) or registry access. It
  is private on `ghcr.io`, so a cluster without ghcr credentials needs it imported
  (see the Kubernetes section).

## First-time setup

The `.score-compose/` and `.score-k8s/` state directories are gitignored, so after a
fresh clone you initialise both projects once. The compose project also registers
`restart-policy.tpl` — a patch that adds `restart: unless-stopped` to the api service.
That is a compose-only concern: Kubernetes restarts crashed pods natively, so the k8s
side needs no equivalent.

```bash
cd score
score-compose init --project placeframe --no-sample --patch-templates ./restart-policy.tpl
score-k8s init --no-sample
```

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
k3d image import ghcr.io/outernet-foundation/placeframe/api:<API_SHA> -c score-poc
kubectl apply -f manifests.yaml
kubectl rollout status deployment/api --timeout=150s
```

Then connect via a port-forward (leave it running in its own terminal):

```bash
kubectl port-forward deploy/api 8000:8000        # -> http://localhost:8000/health
```

Stop it: `k3d cluster delete score-poc`

`k3d image import` is needed because the api image is private and not in the cluster's
registry — a production cluster with ghcr credentials pulls it normally.

## What the provisioners stand up (and the one real gap)

- **`db` (type: postgres)** — a **vanilla** `postgres` (StatefulSet + PVC on k8s;
  service + volume on compose) with a single generated role and an **empty database**.
  It is *not* the custom placeframe postgres image, and it has none of the
  `placeframe_*` roles or schema that `create-database` / `database-migrator` produce.
  So the api boots and serves `/health`, but any endpoint that queries real tables
  will fail. Closing this needs a **custom `postgres` provisioner** — the one
  substantial piece of work remaining.
- **`bucket` (type: s3)** — a real MinIO (`quay.io/minio/minio`) with a service
  account, access/secret keys, and a bucket, created by an init step (a
  `restart: "no"` service on compose, a `Job` on k8s). No custom provisioner needed —
  object storage works out of the box.

## Image pinning gap

The `api` image is pinned by content-addressed SHA tag, but the images the **default
provisioners** inject are **moving references**, which violate the repo-wide "pin
everything / no `:latest`" rule:

- `mirror.gcr.io/postgres:17-alpine` — moving tag
- `quay.io/minio/minio` — no tag (effectively `:latest`)
- `alpine` (the compose resource-wait gate) — no tag, no registry host

Pinning these means overriding the default provisioners with custom ones that
reference images by digest (`@sha256:...`), or rewriting the image fields at generate
time from `.env.shas` / `.env.lock`. Acceptable for a throwaway PoC; a blocker for
real adoption.

## Regenerating

`api.yaml` is the source of truth. After editing it, re-run the matching `generate`
command; the generated `compose.yaml` / `manifests.yaml` are overwritten in place.
Resource outputs (the generated password, MinIO keys, bucket name) are cached in the
`state.yaml` files and reused across runs, so credentials stay stable until the state
directory is deleted.
