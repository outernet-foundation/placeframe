# stack/

## What this is

The score tier: one authored description per service, compiled into two renderings —
`stack/generated/compose/compose.yaml` (Docker compose) and `stack/generated/k8s/manifests.yaml`
(Kubernetes). Coverage is a growing subset of the hand-authored compose stack at the repo root;
`stack/score/` holds the authored sources, `stack/generated/` the committed artifacts.

    stack/score/            authored
      api.yaml              workload contracts (tier-neutral), ${SHA} placeholders for image tags
      compose/              provisioners for the compose rendering
      k8s/                  provisioners for the k8s rendering
      k8s/values/           helm values for the declared charts (k8s rendering only)
    stack/generated/        committed artifacts, never hand-edited
      compose/compose.yaml
      k8s/manifests.yaml

## Generate

`uv run generate-score [--target compose|k8s] [--local]` writes the artifacts and deploys
nothing. Image tags resolve via `compute_service_shas` from the **committed** tree
(`git ls-tree HEAD`), so the order is: commit the source change, regenerate, commit the
artifacts. Generating first produces artifacts built against the previous tree.

The score tools (score-compose 0.42.0, score-k8s 0.15.0) must be on PATH at those exact
versions — output differs between releases. In the COI sandbox they live in `~/.local/bin`,
which is not on the default PATH.

Preflight does not gate these artifacts on staleness: every change inside a service's build
context (a dependency-lock bump included) re-stales the committed output through the embedded
`tree-<sha>` tags. Regeneration is a deliberate manual step, deterministic across fresh runs
(the tool state dirs are per-run temp; instance suffixes are name-derived hashes).

## Deploy: Docker

The generated compose has no entry in `docker-devkit.yaml`'s `lifecycle:` section, so bring it
up through raw `docker compose`, anchored at the repo root (`--project-directory .` is
required — compose otherwise anchors relative paths at the first `-f` file's directory):

```bash
docker compose --project-directory . \
  --env-file .env --env-file workloads/images.lock \
  -f stack/generated/compose/compose.yaml up -d
# teardown: same command with `down --remove-orphans`
```

The `tree-<sha>` image tags the generated compose references must exist before `up` — a
regeneration can reference tags that have never been built or pushed, and the pull fails
with `not found`. Build the missing services first (`uv run build -t api -t gateway
--gpu none`).

It reads the same `.env` as the hand stack. Reach it at `http://localhost:8443/schema`.

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
SeaweedFS volumes unbindable on the next rebuild. With no Pulumi locally, mint the Secret
first (every key below is referenced by the manifests):

```bash
k3d cluster create score-poc --no-lb --k3s-arg "--disable=traefik@server:0"
kubectl create secret generic placeframe-secrets \
  --from-literal=POSTGRES_ADMIN_PASSWORD=$(openssl rand -hex 16) \
  --from-literal=DATABASE_OWNER_PASSWORD=$(openssl rand -hex 16) \
  --from-literal=DATABASE_API_USER_PASSWORD=$(openssl rand -hex 16) \
  --from-literal=DATABASE_AUTH_USER_PASSWORD=$(openssl rand -hex 16) \
  --from-literal=DATABASE_ORCHESTRATION_USER_PASSWORD=$(openssl rand -hex 16) \
  --from-literal=S3_ACCESS_KEY=$(openssl rand -hex 8) \
  --from-literal=S3_SECRET_KEY=$(openssl rand -hex 16) \
  --from-literal=KEYCLOAK_ADMIN_PASSWORD=$(openssl rand -hex 16) \
  --from-literal=GRAFANA_ADMIN_USER=admin \
  --from-literal=GRAFANA_ADMIN_PASSWORD=$(openssl rand -hex 16) \
  --from-literal=PUBLIC_URL=http://localhost:8443 \
  --from-literal=AUTH_ISSUER_URL= \
  --from-literal=AUTH_JWKS_URL= \
  --from-literal=AUTH_AUTHORIZATION_ENDPOINT= --from-literal=AUTH_TOKEN_ENDPOINT= \
  --from-literal=DEPLOYMENT_ENVIRONMENT=development \
  --from-literal=KEYCLOAK_HOSTNAME=http://localhost:8443/auth
```

k3d pulls through Docker Hub, whose unauthenticated rate limit is low enough to fail a cold
cluster; preload slow images with `docker save <image> | docker exec -i k3d-score-poc-server-0
ctr -n k8s.io images import -`.

## Constraints

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
- **`AUTH_JWKS_URL` is a passthrough in both renderings**, never a baked keycloak URL: the api
  boots anonymous mode only when the issuer is empty *and* every auth endpoint is empty
  (`check_auth_config` in `workloads/api/src/settings.py`); a baked JWKS URL would crash
  anonymous boots.
- **Service names in provisioners are load-bearing DNS names.** `seaweedfs`,
  `seaweedfs-audit`, `pf-postgres`, `keycloak` are addressed by baked-in references (loki's
  config, the entrypoint wrapper's rendered audit sink, workload env); renaming one breaks
  the stack at runtime, not at generation.
- **Provisioners come in per-rendering pairs** — `compose/<name>.yaml` and `k8s/<name>.yaml`
  for the same resource type. Which file is registered is declared in `docker-devkit.yaml`'s
  `generate-score:` section (the `compose_provisioners` / `k8s_provisioners` lists); the score
  tools themselves impose no naming requirements on these files. `k8s/postgres-cnpg.yaml` is
  an unregistered alternative (CloudNativePG operator instead of a raw StatefulSet) —
  registering it *instead of* `k8s/postgres.yaml` switches the k8s backend with workloads
  unchanged. Its operand image is built from `workloads/postgres-cnpg/Dockerfile`
  (`placeframe-postgres-cnpg:14-trusted`, PostGIS marked trusted for non-superuser
  pg-schema-diff shadow databases).
- **Workload files are not standalone-valid score documents** — `${API_SHA}`-style image
  placeholders are expanded by `generate-score` from the committed tree before the score
  tools see them.
- **No `depends_on` across workloads**: score has no such concept. Provisioner services gate
  on each other's health; workloads gate on the auto-emitted `wait-for-resources` service,
  whose `alpine` default image is redirected through the `${ALPINE_IMAGE:?err}` lock hole by
  the `compose/wait-for-resources-image.tpl` patch template — the artifact carries no
  unpinned image.
- **Third-party k8s stamp-outs are charts where an OCI chart exists** — loki and grafana
  render from digest-pinned upstream-native OCI refs declared in `docker-devkit.yaml`
  (`generate-score.charts` + `helm_version`), pulled through the org mirror (the CI mirror
  job copies chart declarations like image declarations; declaring a chart the mirror job
  has not copied yet makes k8s generation fail until it runs). Chart values never carry
  secret values: they reference the existing `placeframe-secrets` Secret (`envValueFrom`/
  `extraEnvFrom`/`existingSecret`) or `${VAR}` config holes expanded in-container. Alloy has
  no upstream OCI chart, so `k8s/observability.yaml` hand-writes its Deployment + Service
  + ConfigMap — the ConfigMap body is a mirror of `workloads/alloy/config.alloy` and must
  be kept in sync with it by hand.
- **No restart policies are declared anywhere** — workload services, provisioner services,
  and the deleted patch template all rely on compose's default. The hand stack's posture is
  identical.
- **Argo CD Jobs**: create/migrate/bucket Jobs carry `argocd.argoproj.io/hook: Sync` +
  `BeforeHookCreation` because a Job's spec.template is immutable — without the hook an image
  tag bump makes every later sync fail with "field is immutable". Re-runs are safe (create is
  idempotent, the migrator is a no-op on matching schemas, the bucket initializer only creates
  missing buckets).

## See also

- `plan-compose-score.md` (repo root) — the initiative this tier serves: coverage slices,
  artifact split, open decisions.
- [`docker-devkit`'s `AGENTS.md`](https://github.com/outernet-foundation/docker-devkit/blob/main/AGENTS.md)
  — `generate-score` internals (placeholder expansion, bind inlining, determinism suite).
- `workloads/AGENTS.md` — the running stack's service inventory, data flow, auth model.
