# Score: one source, both Docker and Kubernetes

Placeframe's server stack runs today as Docker Compose (`uv run up`). This directory
evaluates [Score](https://docs.score.dev) as a way to describe each service **once** and
generate both a runnable Docker `compose.yaml` **and** Kubernetes manifests from that one
description — so the project can move toward Kubernetes without hand-maintaining two
definitions that drift apart. It is a proof-of-concept covering a slice of the stack:
**api**, **lease-server**, and the **gateway** (Caddy), backed by **postgres** (real
`placeframe_*` roles and schema) and **MinIO** object storage.

## Run it

Two `uv run` commands do everything — first-time setup, generate, bring-up, tear-down.
You do not run `score-compose` / `score-k8s` / `k3d` / `kubectl` by hand.

```bash
uv run score-up                               # Docker (default)
uv run score-up --target k3s                  # Kubernetes (throwaway k3d), StatefulSet postgres
uv run score-up --target k3s --postgres cnpg  # Kubernetes, CloudNativePG-managed postgres
uv run score-down                             # Docker: stop and wipe volumes
uv run score-down --target k3s                # Kubernetes: delete the cluster + wipe state
```

Then open the stack through the **gateway** (Caddy, the real front door):

- **Docker** publishes it to your machine → `http://localhost:8443/schema/swagger`.
- **k3s** has no host port → `kubectl port-forward deploy/gateway 8443:8443`, then
  `http://localhost:8443`.

Notes:

- `score-up` is re-runnable and only creates the k3d cluster when one isn't already there.
- **`--postgres`** (k3s only) picks the postgres backend: `statefulset` (default) or
  `cnpg` (see below). It is fixed per cluster — to switch, `score-down --target k3s`
  first (that wipes the cluster and generated state), then bring up again.

**Prerequisites:** `score-compose` 0.42.0 and `score-k8s` 0.15.0 on PATH, plus Docker; for
the k3s target also [`k3d`](https://k3d.io) 5.x and `kubectl`. The service images must be
available locally (`uv run build`) or pullable from `ghcr.io`.

The wrappers live in `placeframe-stack` (`score_up.py` / `score_down.py`). That code is the
reference for the exact steps each one runs (init, generate, k3d create, image preload,
CNPG operator install, `kubectl apply`, readiness waits) — this README does not duplicate
those command sequences.

## What's in this directory

The authored workload files, the custom-provisioner files, and the `restart-policy.tpl`
compose patch are the source; everything else is generated or tool-managed.

| Path | Origin | In git? |
|------|--------|---------|
| `api.yaml`, `lease-server.yaml`, `gateway.yaml` | authored — the workload contracts | yes |
| `placeframe-postgres.provisioners.yaml` | authored — custom postgres provisioner (Docker) | yes |
| `placeframe-postgres.k8s.provisioners.yaml` | authored — custom postgres provisioner (k8s, StatefulSet) | yes |
| `placeframe-postgres-cnpg.k8s.provisioners.yaml` | authored — alternative postgres provisioner (k8s, CloudNativePG) | yes |
| `placeframe-s3.provisioners.yaml` | authored — fixed-name MinIO provisioner (for Loki; not yet wired to the workloads) | yes |
| `../docker/postgres-cnpg/Dockerfile` | authored — trusted-PostGIS operand image for CNPG | yes |
| `restart-policy.tpl` | authored — compose-only patch template | yes |
| `compose.yaml`, `manifests.yaml` | generated | no — gitignored (resolved secrets) |
| `.score-compose/`, `.score-k8s/` | `init` | state gitignored; provisioner catalogs regenerable |

Generated DB/role passwords and MinIO keys appear only in the generated output and the
`state.yaml` files — never in the authored files. Those paths are gitignored, so nothing
sensitive is committed.

## What the provisioners stand up

- **`db` (type `placeframe-postgres`)** — a **custom** provisioner that stands up the real
  Placeframe postgres image (PostGIS, SHA-pinned) and runs the real Placeframe tooling
  rather than a vanilla empty database: `database-manager` creates the database and the
  four `placeframe_*` roles with their grants and row-level security, then
  `database-migrator` (`pg-schema-diff`) applies the schema. `api` and `lease-server`
  share one database via a common resource `id`. **Result:** real data operations work,
  not just `/health`.
- **`bucket` (type `s3`)** — the **default** provisioner: a real MinIO with a service
  account, keys, and a bucket. No custom provisioner needed.

## Postgres backends: StatefulSet or CloudNativePG

`--postgres` selects how postgres runs on Kubernetes; both use the same
`placeframe-postgres` resource type, so the workloads are identical either way.

- **`statefulset`** (default) — a raw `StatefulSet` + Service + a create Job + a migrate
  Job, all authored directly.
- **`cnpg`** — [CloudNativePG](https://cloudnative-pg.io), a Kubernetes *operator* that
  manages postgres: the provisioner emits one `Cluster` object and the operator reconciles
  it into pods, storage, services, and managed failover. The key design choice is that it
  **reuses the same tooling** as the StatefulSet path — the `Cluster` only bootstraps a
  bare database and owner (with `enableSuperuserAccess`), then the same `database-manager`
  create Job applies all roles/grants/RLS and the same `database-migrator` Job applies the
  schema. `score-up --postgres cnpg` installs the operator and builds the operand image
  automatically.

  The operand image (`../docker/postgres-cnpg/Dockerfile`, tag `14-trusted`) exists because
  CNPG runs its own instance manager, so PostGIS is marked *trusted* at build time (instead
  of via the StatefulSet image's runtime entrypoint) — letting the non-superuser
  `placeframe_owner` create the extension in the temporary databases `pg-schema-diff` uses.

## Known gap: image pinning

Every image *we* author or provision is SHA-pinned. The unpinned references all come from
tooling defaults and violate the repo-wide "pin everything / no `:latest`" rule — acceptable
for a throwaway PoC, a blocker for real adoption:

- `quay.io/minio/minio` (the default `s3` provisioner) — no tag.
- `alpine` (the compose resource-wait gate) — no tag, no registry host.
- `placeframe-postgres-cnpg:14-trusted` (the CNPG operand image) — built locally each
  `--postgres cnpg` spin-up, not registry-hosted or digest-pinned (the CI token cannot push
  to the placeframe `ghcr.io` namespace).

## See also

- `.pulsar/memories/score-poc.md` — what the PoC proved, what was not ported, and the open
  infra decision.
