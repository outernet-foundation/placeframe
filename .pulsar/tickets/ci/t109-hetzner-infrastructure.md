---
id: T109
title: Hetzner infrastructure for CI runners and cloud deployment
status: done
depends_on: []
---

# T109: Hetzner infrastructure for CI runners and cloud deployment

## Goal

Stand up Hetzner-based infrastructure to serve two needs: (1) self-hosted GitHub Actions runners for Unity CI builds, eliminating per-job container startup, disk cleanup, ORAS cache round-trips, and ephemeral environment setup; and (2) a production cloud deployment of Placeframe with k3s orchestration, capable of scaling localizer and reconstructor workloads horizontally.

## Context

### CI motivation

The current Unity CI pipeline runs on GitHub-hosted `ubuntu-latest` runners inside GameCI Docker containers. Even with warm ORAS caches, every job pays ~3 min of overhead: pulling the ~4 GB Unity container image, freeing disk space (removing pre-installed Android SDK, .NET, GHCup, Swift via volume-mounted `/to_clean/*`), installing .NET 8.0, installing ORAS + zstd, and restoring the Unity license from ORAS. On cache miss, the critical path (Outernet.Client linux64) reaches 62 min due to full asset reimport and shader compilation.

With self-hosted runners, the Unity editor, .NET, ORAS, and license are pre-installed. Library caches live on local NVMe — no ORAS round-trip at all. The entire setup/teardown overhead disappears, and builds with warm local caches should complete in 3-5 minutes.

The Library cache key was changed from `{project}-{platform}-{manifest_hash}` to `{project}-{platform}-{branch}` (this session) to treat the cache as a warm-start rather than exact-match, ensuring cache hits on every build after the first on a branch.

### Production deployment motivation

Placeframe needs a hosted cloud deployment. The localizer and reconstructor services may need to scale widely and suddenly. The standard approach (AWS EKS) is rejected in favor of Hetzner for cost, simplicity, and alignment with FOSS principles. k3s (lightweight Kubernetes — same API, same kubectl, same Helm, single binary) is the orchestration layer.

### Architecture discussed

| Concern | Solution |
|---|---|
| Orchestration | k3s cluster on Hetzner Cloud VMs |
| IaC | Pulumi with hcloud provider |
| CI runners | 1-2 Hetzner dedicated servers (bare metal), separate from production cluster |
| Database | Postgres on a dedicated Hetzner Cloud VM, outside k3s cluster |
| Autoscaling | HPA for pods + Hetzner Cloud Autoscaler for nodes |
| Ingress | Traefik (bundled with k3s) or nginx-ingress |
| TLS | cert-manager + Let's Encrypt |
| Local dev | Docker Compose (existing) |
| Config source of truth | Custom format rendering to both Compose and Helm |

### Key design decisions from discussion

- **CI and production on separate infrastructure.** CI runners execute PR code (different trust boundary) and are bursty. Production needs predictable performance. CI uses dedicated servers (bare metal, great price/perf, persistent state). Production uses Hetzner Cloud VMs (Pulumi-managed, scalable).
- **k3s over vanilla k8s.** k3s is full Kubernetes (same API) in a single binary. No managed k8s on Hetzner, and bootstrapping kubeadm is unnecessary complexity. Adding a node is a one-liner.
- **Postgres outside the cluster.** Keep the database off k3s so cluster scaling is a pure compute operation. Self-managed Postgres on a Hetzner Cloud VM with persistent volume is simplest and most aligned with FOSS principles. Managed alternatives (Aiven in Hetzner Falkenstein) are fallback options.
- **Pulumi for IaC.** There is a Pulumi provider for Hetzner Cloud (VMs, networks, firewalls, volumes, load balancers). Hetzner Dedicated (bare metal) is less automatable — ordered once, configured with Ansible or similar. This is fine for CI runners (set up once).
- **Abstraction layer for deployment config.** The existing Docker Compose service definitions are the source of truth. A rendering layer produces the final compose file (local dev) or Helm charts / k8s manifests (production) from a shared config plus per-environment overrides. The `.env.lock` with pinned image digests already does half of this.
- **Scaling strategy.** Localizer and reconstructor as k8s Deployments with HPA (scale on queue depth or CPU). Hetzner Cloud Autoscaler adds/removes VMs when cluster capacity is exhausted.

### Relationship to other tickets

- T75 (win64 IL2CPP CI) involves a self-hosted Windows runner. The Hetzner Linux CI runners are separate infrastructure but the operational patterns (runner agent as systemd service, persistent caches) overlap.
- T78 (Unity build time optimization) established the ORAS caching strategy that self-hosted runners would partially replace (local disk caches instead of ORAS round-trips).

## Key files

- `.github/workflows/build-unity.yml` — Unity CI workflow (would change `runs-on` for self-hosted)
- `build/src/build_scripts/placeframe/ci/build_unity.py` — Unity build script (setup steps become no-ops or simplified on self-hosted)
- `build/src/build_scripts/shared/setup.py` — disk space freeing logic (unnecessary on self-hosted)
- `build/src/build_scripts/shared/setup_oras.py` — ORAS installation (pre-installed on self-hosted)
- `build/src/build_scripts/shared/cache.py` — ORAS cache save/restore (replaced by local disk on self-hosted)
- `docker/compose.yml` — existing service definitions (source of truth for deployment config)

## Approach

Not yet determined. Requires a research phase covering the Hetzner + k3s + Pulumi stack before planning implementation.

## Next step

**Research spike.** Investigate the following and produce a report in `.pulsar/research/`:

1. **Pulumi hcloud provider**: What it covers (VMs, networks, firewalls, volumes, load balancers), what it doesn't (dedicated servers), maturity/community health.
2. **Hetzner dedicated vs cloud**: Pricing comparison for CI-appropriate specs (16+ cores, 64+ GB RAM, NVMe). Dedicated server ordering flow and lead times. Cloud VM specs and pricing for production workloads.
3. **k3s on Hetzner**: Bootstrapping flow, networking (Flannel, Cilium), storage (Hetzner CSI driver for persistent volumes), the Hetzner Cloud Autoscaler (how it integrates with k3s, limitations).
4. **GitHub Actions self-hosted runner setup**: Runner agent installation, labels, security considerations (public repo implications), runner groups, auto-scaling patterns (ephemeral vs persistent mode).
5. **Postgres on Hetzner**: Self-managed on a Cloud VM (backup strategies with pgBackRest, replication options), vs. Aiven managed Postgres in Hetzner Falkenstein datacenter.
6. **Deployment config abstraction**: Survey existing tools (Kompose, Tanka, cdk8s, Timoni) for generating both Compose and k8s manifests from a shared source. Evaluate whether a thin custom layer on top of the existing compose.yml is simpler.

## Done when

- Research report produced covering all six areas above
- Architecture decision documented: which Hetzner products, k3s bootstrapping approach, IaC strategy, database hosting, deployment config tooling
- CI runner migration plan written (what changes in workflow files and build scripts)
- Production deployment plan written (k3s cluster topology, networking, storage, autoscaling)
- Implementation tickets created for each phase (CI runners, production cluster, deployment config layer)
