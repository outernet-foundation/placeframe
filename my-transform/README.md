# Deploying the generated Kubernetes manifests

This directory holds the Compose Bridge transform; `uv run generate-k3s` runs it and writes deployable manifests to `out/`. This is the operator runbook for taking those manifests to a cluster. For *why* the transform is shaped the way it is, see `SPEC.md`.

## Prerequisites

- `kubectl` (v1.30+) and, for a throwaway local cluster, [`k3d`](https://k3d.io). Any conformant cluster works; `out/base` uses the cluster's default storage class, while `out/overlays/desktop` assumes the `hostpath` class Docker Desktop provides.
- The target environment's **`.env`** on the machine you run `generate-k3s` from. Secret values are read from it and never stored in git.
- Registry access for the private app images (`ghcr.io/outernet-foundation/placeframe/*`) — see "Private images".

## Test it locally

From-scratch flow to run the whole stack on a laptop. Run each command in order, in **one** terminal.

```bash
# 1. Generate manifests from your .env (secret values are read from it into
#    out/base/.secrets/, which is gitignored)
uv run generate-k3s

# 2. Spin up a throwaway cluster
k3d cluster create placeframe --no-lb \
  --k3s-arg "--disable=traefik@server:0" \
  --k3s-arg "--disable=metrics-server@server:0"

# 3. Give the cluster ghcr credentials (skip if your node can already pull
#    ghcr.io/outernet-foundation/* — see "Private images")
kubectl create namespace placeframe
kubectl -n placeframe create secret docker-registry ghcr \
  --docker-server=ghcr.io --docker-username=<you> --docker-password=<token>
kubectl -n placeframe patch serviceaccount default  -p '{"imagePullSecrets":[{"name":"ghcr"}]}'
kubectl -n placeframe patch serviceaccount wait-for -p '{"imagePullSecrets":[{"name":"ghcr"}]}'

# 4. Deploy and wait for the boot chain (jobs run first, then services)
kubectl apply -k out/base
kubectl -n placeframe wait --for=condition=complete job/database-migrator --timeout=200s
kubectl -n placeframe rollout status deployment/api     --timeout=180s
kubectl -n placeframe rollout status deployment/gateway --timeout=120s

# 5. Connect: open a tunnel to the gateway (leave this running in its own terminal)
kubectl -n placeframe port-forward svc/gateway 8443:8443
```

Then open a browser:

| URL | What you get |
|-----|--------------|
| `http://localhost:8443/` | app / API |
| `http://localhost:8443/schema` | interactive API docs |
| `http://localhost:8443/grafana/` | Grafana |
| `http://localhost:8443/cloudbeaver/` | database browser |

Quick terminal check (the exact gateway → `api:8000` route): `curl -s http://localhost:8443/health` → `{"status":"ok"}`.

Tear the whole thing down with `k3d cluster delete placeframe`.

## Re-deploying

Kubernetes Jobs are immutable, so `kubectl apply` over an existing deploy fails on the init/one-shot Jobs (`spec.template: field is immutable`). Reset before re-applying:

```bash
kubectl delete namespace placeframe --ignore-not-found --wait
kubectl apply -k out/base
```

Two things that will bite otherwise:

- **Run the reset from one terminal only.** Two concurrent `delete namespace` calls race an `apply` and leave the namespace stuck `Terminating` with the pods gone.
- **The reset wipes Postgres/MinIO data** (fresh volumes each time). That is the reliable path while Jobs stay immutable, and it avoids a subtler trap: a `database-migrator` that fails once then succeeds leaves the Job with `failed>0`, which the `wait-for` init image treats as never-complete — wedging everything downstream. A clean namespace guarantees the jobs run once, cleanly.

## Private images

The manifests carry no `imagePullSecret`, so a node not already authenticated to `ghcr.io` cannot pull the app images. Authenticate the cluster's nodes, or create a namespaced pull secret and attach it to the `default` and `wait-for` service accounts (step 3 above).

## Secrets on another machine

Secret values live only in `.env` and, after a deploy, in the cluster's `Secret` objects — never in git. To reproduce a deploy elsewhere, bring your `.env` and re-run `generate-k3s`; to read a live value from a running cluster:

```bash
kubectl -n placeframe get secret minio-secret-key \
  -o jsonpath='{.data.minio_secret_key}' | base64 -d
```

## External ingress

Every `Service` is `ClusterIP`, including `gateway`. Nothing is reachable from outside the cluster until the `gateway` service is fronted by an ingress controller, a `LoadBalancer`, or a `NodePort` (or, for a quick check, `kubectl port-forward` as in step 5). Wiring that front door is deployment-specific and left to the operator.
