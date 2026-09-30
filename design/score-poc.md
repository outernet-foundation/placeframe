---
updated: 2026-07-09
---

# Evaluate Score as one source generating both the Docker and Kubernetes deployment

## Goal

Placeframe's server stack runs today as Docker Compose (`uv run up`). The move toward a
Kubernetes/SaaS deployment risks maintaining two independent definitions — the Compose
stack and a hand-written Kubernetes one — that drift apart. Evaluate [Score](https://docs.score.dev)
as a single per-workload source (`score.yaml`) that generates **both** a runnable Docker
`compose.yaml` (via `score-compose`) and Kubernetes manifests (via `score-k8s`), so
"no drift between different pieces of code" holds while still supporting Kubernetes and
keeping Compose usable. Work lives in `score/`.

## State (what the PoC proved)

Verified end-to-end on Docker and on a k3d cluster, from single authored workload files:

- **One source, two targets.** The same `score/api.yaml` (etc.) generates a runnable Docker
  stack and k3d-deployable manifests; `/health` returns `200` on both.
- **Ported and running on both:** `api`, `lease-server`, `gateway` (Caddy front door),
  backed by a `postgres` (custom provisioner) and `minio` (`s3` provisioner).
- **Dependency wiring** via `${resources.*}` placeholders resolves to real, reachable
  services on both platforms. Secrets: plaintext env on compose, a `Secret` object
  (`secretKeyRef`) on k8s; never in the authored files.
- **Resource sharing** across workloads needs a common `id` (`placeframe-db`): same type
  alone gives a shared server but separate databases; same `id` gives the same database.
- **The no-Jobs gap is bridged by provisioners.** Score itself has no Job/`depends_on`,
  but a provisioner emits a `restart: "no"` service (compose) or a `Job` (k8s), and
  crash-loop-until-ready supplies the runtime ordering (observed: the k8s bucket + create
  Jobs restarted until their dependency was ready, then completed).
- **Custom `postgres` provisioner (both targets).** Instead of the vanilla default (one
  generated role, empty DB), a custom provisioner stands up the real Placeframe postgres
  image and runs the real `database-manager` (`create-database`) to create the actual
  `placeframe_*` roles. Verified by connecting to the DB *as* `placeframe_api_user` on
  both Docker and Kubernetes. One resource type (`placeframe-postgres`), two
  target-specific provisioner files (compose emits services; k8s emits Secret + StatefulSet
  + Service + Job).
- **Portability wrinkles found:** an `httpGet` livenessProbe is kept on k8s but dropped by
  `score-compose` (warns "not supported"); `rollout status deployment/api` reports Ready
  before postgres is up because the api has no readinessProbe/dependency gate.

## Decision (the infra fork — not yet made)

The api ported cleanly because it is **env-driven** (reads whatever endpoint/creds are
injected). Config-driven services **hardcode** their expectations, which the default
provisioners' random names/buckets/roles do not satisfy:

- **loki** bakes `endpoint: minio:9000` and `bucketnames: loki` into its config; the `s3`
  provisioner produces a randomly-named minio and bucket.
- **api/lease-server** need the specific `placeframe_*` roles (solved for postgres via the
  custom provisioner; the same shape would be needed for other config-hardcoded services).

So porting the rest forces a choice, deliberately left to the team:

- **Option A — Workloads (faithful).** Model postgres/minio as plain Score workloads using
  the real images + init jobs. Full stack runs on both; most mechanical. Cost: postgres is
  always a container — abandons the managed-DB-in-prod separation (i.e. "Compose in Score").
- **Option B — Custom provisioners.** Keep the resource model, author custom provisioners
  that stand up the real images with the expected names/buckets/roles (as done for
  postgres). Preserves managed-in-prod binding — Score's main benefit. Cost: real
  provisioner-authoring work per config-hardcoded dependency.

The hinge: how pervasively production uses managed dependencies (managed Postgres, object
storage, cache). Pervasive → B earns its cost; mostly containers with one managed Postgres
→ A plus a targeted provisioner suffices.

## Open questions

- **Image pinning.** The api image is SHA-pinned and the custom postgres provisioner pins
  its images, but the default provisioners inject moving references (`postgres:17-alpine`,
  untagged `quay.io/minio/minio`, `alpine`) — violates the repo no-`:latest` rule. Fix
  rides along with Option B, or a generate-time driver rewriting image fields from
  `.env.shas` / `.env.lock`.
- **Migrations.** The custom postgres provisioner runs `create-database` (roles) but not
  `database-migrator` (schema/tables). `/health` works; real data operations need a migrate
  step added to the provisioner — and the migrator image bakes in `database/*.sql`, so a
  new schema file requires rebuilding that image before it applies.

## Key files

- `score/api.yaml`, `score/lease-server.yaml`, `score/gateway.yaml` — authored workloads.
- `score/placeframe-postgres.provisioners.yaml` (compose), `score/placeframe-postgres.k8s.provisioners.yaml` (k8s) — the custom postgres provisioner, one per target.
- `score/restart-policy.tpl` — compose patch template adding `restart: unless-stopped`.
- `score/README.md` — operator runbook (setup, generate, run, connect, both targets).

## Pending threads

- Decide Option A vs B (the managed-dependency question) before porting the remaining
  services (loki/alloy/grafana, cloudbeaver, keycloak, the init chain, networking).
- Add the `database-migrator` step to the custom postgres provisioner for real data.
- Close the image-pinning gap.
