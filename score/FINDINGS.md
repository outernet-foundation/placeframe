# Score PoC — findings and the infra decision

This is the outcome of evaluating [Score](https://docs.score.dev) as a single source
that generates both the Docker Compose stack and Kubernetes manifests, so Placeframe
can move toward a Kubernetes/SaaS deployment without hand-maintaining two definitions
that drift. `README.md` (next to this file) is the operator runbook; this file is the
decision record.

## Scope tested

From single per-workload Score files, `score-compose` generates a Docker `compose.yaml`
and `score-k8s` generates Kubernetes manifests. Ported and run end-to-end on **both**
targets: `api`, `lease-server`, `gateway`, backed by a `postgres` and a `minio` (`s3`)
provisioned dependency. Everything below was verified on Docker and on a k3d cluster.

## What works (proven)

- **One source, two targets.** The same `api.yaml` (etc.) generates a runnable Docker
  stack and a k3d-deployable manifest set. `/health` returns `200` on both.
- **The gateway front door.** Hitting the gateway (Caddy) on `:8443` reverse-proxies to
  `api:8000` on both targets — the real UI path, not the bare api.
- **Dependency wiring.** `${resources.db.*}` / `${resources.bucket.*}` placeholders
  resolve to real, reachable services; the api connects to its provisioned postgres and
  minio on both platforms.
- **Secrets handled correctly.** Compose gets plaintext env; Kubernetes gets a `Secret`
  object referenced via `secretKeyRef`. Values never appear in the authored files.
- **MinIO is free.** The default `s3` provisioner stands up a real MinIO with a service
  account, keys, and a bucket — no custom code.
- **Resource sharing.** Two workloads sharing a database is expressed with a common
  resource `id` (`placeframe-db`); without it, each gets its own database on a shared
  server.
- **Platform-specific tweaks have a home.** A patch template injects
  `restart: unless-stopped` into the compose output (Kubernetes restarts pods natively),
  applied at generate time so it survives regeneration.

## Mechanics learned

- **Provisioner = the seam.** A resource declares a *need* (`db: {type: postgres}`); the
  provisioner builds it per target and reports outputs that fill the placeholders. This
  is the separation Compose can't express and the reason Score is on the table.
- **No Jobs / no `depends_on` in the spec — but provisioners emit them.** The s3 bucket
  setup came out as a `restart: "no"` service on compose and a real `Job` on k8s. You
  can't author ordering; the provisioner materialises it, and app-level crash-loops
  cover the rest (observed: the k8s bucket Job restarted until minio was ready).
- **Portability wrinkles are real.** An `httpGet` livenessProbe is kept on k8s but
  **dropped** by `score-compose` (warns "not supported"). And `rollout status
  deployment/api` reports Ready before postgres is up, because the api has no
  readinessProbe/dependency gate. Same source, different behaviour per target — know it.

## The wall: default provisioners vs. hardcoded infra

The api ported cleanly because it is **env-driven** — it reads whatever endpoint,
bucket, and credentials are injected. The rest of the stack is **config-driven** and
hardcodes its expectations, which the default provisioners' random names do not satisfy:

- **loki** bakes `endpoint: minio:9000` and `bucketnames: loki` into its config (only
  credentials are env-driven). The `s3` provisioner produces a randomly-named minio
  (`minio-XXXX`) and a random bucket — neither matches, and loki's config can't be
  pointed at them.
- **api / lease-server** need a database with specific `placeframe_*` roles that
  `create-database` + `database-migrator` produce. The `postgres` provisioner gives a
  single generated role and an empty schema — enough to boot and serve `/health`, but
  not for real data operations.

So `/health` works everywhere, but any real data path fails, and loki/observability
cannot use the provisioner's minio as-is.

## The infra decision (for the team)

Porting the config-hardcoded services forces a choice about how postgres and minio are
modeled. This is the strategic fork; it was deliberately **not** decided in the PoC.

- **Option A — Workloads (faithful).** Model postgres and minio as real Score workloads
  named `postgres` / `minio`, using the placeframe images and their init jobs
  (`create-database`, `initialize-minio`, `initialize-loki`). Every service connects the
  way it does in Compose. *Pro:* the full stack actually runs on both targets, most
  mechanical. *Con:* postgres is always a container — this abandons Score's
  managed-DB-in-prod separation, i.e. it is "Compose re-expressed in Score."
- **Option B — Custom provisioners.** Keep the resource model but author custom
  `postgres` and `s3` provisioners that stand up the real images with the expected
  names, buckets, and roles. *Pro:* preserves managed-in-prod binding — the main reason
  to adopt Score for a SaaS move. *Con:* substantial provisioner-authoring effort before
  anything past the api runs end-to-end.

The tension is direct: Option A gives a working full stack now but discards the feature
that motivated Score; Option B keeps that feature but is real engineering. The decision
hinges on how pervasively production will use managed dependencies (managed Postgres,
object storage, cache): if pervasive, B earns its cost; if it is mostly containers with
one managed Postgres, A plus a later targeted provisioner is enough.

## Also unresolved: image pinning

The api image is pinned by SHA, but provisioner-injected images
(`postgres:17-alpine`, untagged `quay.io/minio/minio`, `alpine`) are moving references
that violate the repo's no-`:latest` rule. Pinning them means custom provisioners
(Option B) or a generate-time driver that rewrites image fields from `.env.shas` /
`.env.lock`. Either way it rides along with the infra decision above.

## Status

- **Committed and running on both targets:** `api`, `lease-server`, `gateway` (workload
  files in this directory). Not ported: observability (loki/alloy/grafana), cloudbeaver,
  keycloak, the DB-setup init chain, and networking (rathole/ngrok) — all blocked on the
  infra decision above.
- **Recommendation:** decide Option A vs B based on the managed-dependency question
  before porting further. The PoC has answered its question — Score generates and runs
  both targets from one source — and has bounded the remaining cost precisely.
