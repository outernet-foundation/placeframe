# Hetzner Infrastructure for CI Runners and Cloud Deployment

Research conducted 2026-03-18. Context: T109 — evaluating Hetzner + k3s + Pulumi stack for self-hosted CI runners and production Placeframe deployment.

## The question

What's the right infrastructure stack for Placeframe on Hetzner? Specifically: IaC tooling (Pulumi vs alternatives), server specs and pricing, k3s bootstrapping and operations, GitHub Actions self-hosted runner setup (on a public repo), PostgreSQL hosting, and deployment config abstraction (Compose + k8s from shared source).

Constraints: FOSS only, no vendor lock-in. Hetzner already chosen over hyperscalers. k3s chosen over vanilla k8s.

---

## 1. Pulumi hcloud Provider

### Coverage

The `pulumi-hcloud` provider exposes ~30 resource types covering all major Hetzner Cloud resources: Servers, Networks/Subnets/Routes, Firewalls, Load Balancers, Volumes, SSH Keys, Floating/Primary IPs, Placement Groups, Certificates, DNS Zones/Records, and Storage Boxes.

**Not covered:** Hetzner Robot (dedicated/bare metal servers), Object Storage (S3-compatible), managed Kubernetes. The dedicated server gap is significant for the CI runner use case.

### Maturity and governance

| Metric | Pulumi hcloud | Terraform hcloud (upstream) |
|---|---|---|
| Stars | 101 | 689 |
| Contributors | 18 (mostly Pulumi bots) | 60 (including Hetzner staff) |
| License | Apache-2.0 | MPL-2.0 |
| Latest release | v1.32.1 (Feb 2026) | v1.60.1 (Mar 2026) |
| Maintainer | Pulumi Inc. | **Hetzner Cloud GmbH** |

The Pulumi provider is a **bridged Terraform provider** — it wraps `hetznercloud/terraform-provider-hcloud` via `pulumi-terraform-bridge`. Feature parity tracks upstream. Python SDK (`pulumi-hcloud` on PyPI) has full typing and auto-generated docs.

### FOSS assessment

Pulumi CLI and SDKs are Apache-2.0 (genuine FOSS). Pulumi Cloud (state backend) is proprietary SaaS, but self-managed backends (S3, local filesystem) are supported. Pulumi Inc. is **VC-backed (Series C, $75M+)** with no foundation governance — open core model. The Apache-2.0 license prevents a BSL-style rug-pull, but governance is single-company.

**OpenTofu** (MPL-2.0, Linux Foundation governance) + the Hetzner Terraform provider is the strongest FOSS story in IaC. Uses HCL instead of Python. The Terraform hcloud provider is maintained by Hetzner themselves (profitable, privately held German company since 1997).

### Dedicated server provisioning

No IaC tool handles Hetzner dedicated servers well. Community Terraform providers exist but are abandoned. Recommended approach: **Ansible** or direct Robot API calls. Order once, configure with Ansible, maintain as long-lived infrastructure. This is fine for CI runners (set up once, rarely changed).

### Recommendation

Pulumi is viable if the team prefers Python over HCL. The VC governance is a yellow flag but the Apache-2.0 license provides protection. OpenTofu is the FOSS-purist choice. Either way, dedicated servers need Ansible regardless.

---

## 2. Hetzner Pricing and Specs

### CI runners (dedicated bare metal)

| Model | CPU | Cores | RAM | Storage | Price/mo | Setup |
|---|---|---|---|---|---|---|
| AX41-NVMe | Ryzen 5 3600 | 6C/12T | 64 GB DDR4 | 2x 512 GB NVMe | ~37 EUR | ~39 EUR |
| **AX102** | **Ryzen 9 7950X3D** | **16C/32T** | **128 GB DDR5** | **2x 1.92 TB NVMe** | **~126 EUR** | **~79 EUR** |
| AX162-R | EPYC 9454P | 48C/96T | 256 GB DDR5 ECC | 2x 3.84 TB NVMe | ~199 EUR | ~79 EUR |

**AX102 is the sweet spot** for Unity CI: 16 cores, 128 GB RAM, 3.84 TB NVMe for ~126 EUR/month. An equivalent AWS instance (c6i.4xlarge, 16 vCPU, 32 GB, no local storage) costs ~580 USD/month on-demand.

Ordering is **not instant** — hours to a few business days for standard configs. Datacenters: Falkenstein, Nuremberg, Helsinki (Germany/Finland only for dedicated).

### Production k3s cluster (Cloud VMs)

Relevant tiers for k3s nodes:

| Series | Type | vCPU model | Example | Price/mo |
|---|---|---|---|---|
| CX | Shared x86 | Intel/AMD | CX33: 4 vCPU, 8 GB, 80 GB — 5.49 EUR | Cheapest |
| CPX | Shared x86 | AMD | CPX42: 8 vCPU, 16 GB, 320 GB — 19.99 EUR | Good value |
| CCX | Dedicated x86 | AMD EPYC | CCX33: 8 vCPU, 32 GB, 240 GB — 48.49 EUR | No noisy neighbor |
| CAX | Shared ARM | Ampere | CAX31: 8 vCPU, 16 GB, 160 GB — 12.49 EUR | ARM only |

A reasonable starter k3s cluster (3 control + 3 worker): ~76 EUR/month with shared vCPU, ~162 EUR/month with dedicated vCPU.

### GPU

**Hetzner Cloud does NOT offer GPU VMs.** GPU is bare-metal only:

| Model | GPU | VRAM | Price/mo |
|---|---|---|---|
| GEX44 | RTX 4000 SFF Ada | 20 GB GDDR6 ECC | 184 EUR |
| GEX131 | RTX PRO 6000 Blackwell | 96 GB GDDR7 ECC | 889 EUR |

GEX44 is relevant for localizer/reconstructor inference. These are dedicated servers — no elastic scale-up/down.

### Other costs

| Resource | Price |
|---|---|
| Block Volumes | 0.044 EUR/GB/month |
| Load Balancer | ~5.50 EUR/month |
| Object Storage | 4.99 EUR/month (includes 1 TB storage + 1 TB egress) |
| Traffic (EU) | 20-60 TB included; overage 1 EUR/TB |
| Floating IPv4 | 3.00 EUR/month |

Traffic pricing is the biggest win: 1 EUR/TB vs AWS's ~87 USD/TB.

### Price increase warning

Hetzner raises prices **April 1, 2026** (up to 37% on some products). Ordering before April 1 may lock in current pricing for existing products.

---

## 3. k3s on Hetzner

### Bootstrapping options

Three approaches, in order of recommendation:

1. **`hetzner-k3s` CLI** ([vitobotta/hetzner-k3s](https://github.com/vitobotta/hetzner-k3s)) — single binary, YAML config, ~2k stars, actively maintained. Creates HA clusters with embedded etcd, installs CCM, CSI, autoscaler automatically. Supports Flannel and Cilium. Simplest path.

2. **Manual bootstrap via Pulumi/Ansible** — use `pulumi-hcloud` to provision VMs/networks/firewalls, cloud-init or `k3sup` to install k3s over SSH. More control, more work.

3. **`kube-hetzner` Terraform module** — ~3,800 stars, battle-tested, but Terraform-specific and has a single primary maintainer (bus factor). Uses openSUSE MicroOS (immutable OS with auto-updates). Patterns are highly transferable even if not using Terraform directly.

The archived `pulumi-hcloud-kube-hetzner` (20 stars, archived Aug 2025) is not recommended.

### Networking

**Flannel (default):** Works well. Must bind to private network interface (`--flannel-iface=enp7s0`). Simple, low overhead.

**Cilium:** Supported, offers eBPF networking, Hubble observability, WireGuard encryption. More config. If using WireGuard, open UDP 51871 between nodes.

**Hetzner private networks:** Up to 100 nodes per network (scaling limitation). k3s inter-node traffic should run over private network. The hcloud-cloud-controller-manager handles Load Balancer integration.

**Hetzner Load Balancers:** Automatically provisioned via `Service type: LoadBalancer`. ~5 EUR/month. Must use `use-private-ip` annotation or health checks may fail.

### Storage (hcloud-csi)

Official driver maintained by Hetzner. Automatic PVC provisioning via `hcloud-volumes` StorageClass. ReadWriteOnce only. 10 GB to 10 TB per volume.

**Performance reality check:** Hetzner volumes are network-attached with 3x replication. Advertised: 5,000 sustained IOPS. Real-world random 4K writes: **~325 IOPS**. Local NVMe on the VM: ~33,000 IOPS (10x faster). **Do not run databases on Hetzner volumes** — use local NVMe with replication instead.

### Cluster Autoscaler

The upstream `kubernetes/autoscaler` has a built-in Hetzner provider. Works with k3s via cloud-init that joins new nodes as agents. Both `hetzner-k3s` and `kube-hetzner` integrate it.

**Known bugs:**
- Route cleanup on scale-down ([#4049](https://github.com/kubernetes/autoscaler/issues/4049)): stale pod routes when nodes are removed, causing broken networking if IPs are reused. Mitigate with large subnets.
- PDB + TopologySpreadConstraints interaction ([#9111](https://github.com/kubernetes/autoscaler/issues/9111)): autoscaler may refuse to scale down underutilized nodes.

### Ingress + TLS

Standard pattern: Hetzner LB → Traefik (bundled with k3s) or nginx-ingress → cert-manager + Let's Encrypt. Default Traefik config is not production-ready (unsecured dashboard, no HTTPS redirect) — customize via `HelmChartConfig` or deploy your own.

---

## 4. GitHub Actions Self-Hosted Runners

### Setup

Install runner agent, register with a time-limited token, run as systemd service (`svc.sh install`). Custom labels (`unity`, `hetzner`) control targeting via `runs-on: [self-hosted, Linux, unity]`. Auto-updates happen between jobs.

### Public repo security — critical concern

**GitHub's official position:** "Self-hosted runners should almost never be used for public repositories." Anyone can fork the repo, add a workflow targeting self-hosted runners, open a PR, and execute arbitrary code on your servers. The [Shai-Hulud worm (Nov 2025)](https://www.sysdig.com/blog/how-threat-actors-are-using-self-hosted-github-actions-runners-as-backdoors) demonstrated this at scale.

There is **no process isolation between jobs** on persistent runners. Jobs run as the same OS user. A malicious job can bypass post-job cleanup, leave persistent backdoors, and inspect other processes.

### Hardened architecture for a public repo

1. **Require approval for all outside collaborators** on fork PR workflows (repo Actions settings).
2. **Self-hosted runner jobs trigger on `push` only, never `pull_request`.** PRs run preflight on GitHub-hosted `ubuntu-latest` (current behavior). Unity builds run after merge.
3. **Register at organization level** in a restricted runner group (requires GitHub Team plan).
4. **Dedicated low-privilege user**, no sudo. Monitor for rogue processes.
5. **Alternative: companion private repo pattern** — a private repo where the runner is registered, triggered by `repository_dispatch` from the public repo. Completely isolates the runner from fork PRs.

### Persistent vs ephemeral

Persistent mode is correct for Unity builds. The Library cache (5-20+ GB per project/platform) is the key asset — ephemeral runners would need ORAS restoration every job, adding minutes. Persistent runners keep it on local NVMe.

Cleanup between jobs: remove build artifacts but preserve Library. Kill orphaned Unity processes. Monitor disk space. Weekly prune caches for deleted branches.

### Multi-runner on one machine

Possible (separate directories, separate systemd services), but **not recommended for Unity builds** — Unity is too resource-hungry. One runner agent per machine for Unity. A second lightweight runner for non-Unity jobs is fine with concurrency groups.

### Actions Runner Controller (ARC)

Kubernetes-only. Could run on the k3s production cluster for non-Unity jobs (Docker builds, linting, tests) with ephemeral pods. Not applicable to bare-metal Unity runners.

---

## 5. PostgreSQL on Hetzner

### Self-managed with Autobase (recommended)

[Autobase](https://github.com/vitabaks/autobase) (formerly postgresql_cluster, MIT-licensed) automates production PostgreSQL on Hetzner Cloud:
- Patroni + etcd for HA and automatic failover
- PgBouncer for connection pooling
- pgBackRest with Hetzner Object Storage for backups (PITR)
- Hetzner Cloud Load Balancer as entry point
- Web console for management

**Cost estimate — 3-node HA cluster:**

| Component | Spec | Monthly (EUR) |
|---|---|---|
| 3x CCX23 | 4 vCPU, 16 GB each | ~75 |
| Load Balancer | LB11 | ~6 |
| Object Storage (backups) | 1 TB included | ~5 |
| **Total** | | **~86** |

Smaller setup (2 nodes): ~55 EUR/month.

**Use local NVMe for the data directory** (WAL + data files) — 40,000+ IOPS vs ~325 IOPS on network volumes. Rely on streaming replication + pgBackRest for durability.

### Managed alternatives

**Aiven:** Does NOT run on Hetzner. Nearest is UpCloud Frankfurt. Business-8 (2 CPU, 8 GB, HA) costs $400/month — 4x the self-managed equivalent. Proprietary platform, VC-backed. Conflicts with FOSS principles.

**Ubicloud:** Runs on Hetzner bare metal in Germany. AGPL-3.0 (genuine FOSS, self-hostable). Standard-4 (4 vCPU, 16 GB, 128 GB) is $99/month but single-node only. VC-backed (YC W24, $16M seed).

**Hetzner:** Does not offer managed PostgreSQL for Cloud customers.

### Recommendation

**Autobase on Hetzner Cloud.** All components are genuine FOSS with independent communities (Patroni, pgBackRest, etcd, PgBouncer). MIT-licensed automation. No proprietary management layer. ~86 EUR/month for a production HA cluster. If Autobase maintainers disappear, the Ansible playbooks and underlying tools still work.

---

## 6. Deployment Config Abstraction

### The problem

Placeframe uses Docker Compose for local dev (~15 services with health-gated dependencies, profiles, includes, init containers, `.env.lock` digest pinning). Production needs k8s manifests for k3s. How to avoid maintaining two completely separate configs?

### Tools evaluated

| Tool | Solves dual-target? | FOSS clean? | Verdict |
|---|---|---|---|
| **Kompose** | No (one-time migration) | Yes (k8s SIG) | Bootstrap only — doesn't handle init services, health deps, profiles, includes |
| **Tanka** | No (k8s only) | Yellow (Grafana, VC-backed) | Adds Jsonnet, doesn't solve Compose side |
| **cdk8s** | No (k8s only) | Red (AWS-controlled) | Heavyweight, governance concern |
| **Timoni** | No (k8s only) | Pre-1.0, CUE lang | Too immature |
| **Helm + Compose** | Manual sync | Yes | Most teams do this. Real duplication, but well-understood |
| **Custom Python layer** | Yes | N/A (yours) | Best fit for Placeframe |
| **Compose on k8s** | N/A | N/A | Dead end (docker/compose-on-kubernetes archived 2020) |

### Recommendation: Custom Python renderer

None of the existing tools solve the dual-target problem cleanly. A custom Python script that reads a shared config and renders both `compose.yml` and k8s manifests is the best fit because:

- Integrates with existing generation pipeline (`scripts/src/scripts/`, `.env.lock` digest pinning)
- Handles project-specific patterns (init containers from one-shot services, local-only services excluded from production)
- No new language (Python only), no external dependencies beyond PyYAML
- Estimated scope: 500-800 lines for both renderers + shared config schema
- Can evolve incrementally — start with k8s side only, keep existing Compose as source of truth initially

Use Kompose once to see what the k8s equivalent looks like, then build a renderer that handles your specific patterns.

The "boring" alternative (Helm charts + keep Compose as-is) works too, with the tradeoff being config duplication across ~15 services.

---

## Architecture Recommendations

### CI runners

- **1-2x AX102** (16C/32T, 128 GB, 3.84 TB NVMe) at ~126 EUR/month each
- Persistent self-hosted runners with Unity Library on local NVMe
- `push`-only triggers for self-hosted jobs; PRs use GitHub-hosted runners for preflight
- Require approval for fork PR workflows
- One Unity runner agent per machine; optional lightweight runner for non-Unity jobs

### Production cluster

- **k3s on Hetzner Cloud VMs**, bootstrapped with `hetzner-k3s` CLI or Pulumi + cloud-init
- 3 control plane nodes (CX33: 4 vCPU, 8 GB) + 3 worker nodes (CPX42: 8 vCPU, 16 GB) — ~76 EUR/month
- Flannel for networking (simplest), Traefik for ingress, cert-manager for TLS
- Hetzner Cloud Autoscaler for worker node scaling
- GPU workloads (localizer/reconstructor) on GEX44 bare metal (184 EUR/month) if needed

### Database

- **Autobase on Hetzner Cloud** — 3-node Patroni cluster on CCX23 instances
- pgBackRest to Hetzner Object Storage for backups
- Local NVMe for data directory, streaming replication for durability
- ~86 EUR/month

### IaC

- **Pulumi** (Python SDK) for Cloud VMs, networks, firewalls, volumes, LBs
- **Ansible** for dedicated server provisioning (CI runners, GPU servers)
- Self-managed Pulumi state backend (S3-compatible Hetzner Object Storage or local)
- Alternative: OpenTofu for stronger FOSS governance (HCL instead of Python)

### Deployment config

- Custom Python renderer producing both Compose and k8s manifests from shared config
- Existing `.env.lock` digest pinning feeds into both targets

### Total estimated monthly cost

| Component | EUR/month |
|---|---|
| 2x AX102 CI runners | ~252 |
| k3s cluster (6 nodes) | ~76-162 |
| PostgreSQL cluster (3 nodes + LB + storage) | ~86 |
| 1x GEX44 GPU server | ~184 |
| Networking (LBs, floating IPs) | ~15 |
| **Total** | **~613-699** |

Without the GPU server: ~429-515 EUR/month. Equivalent AWS infrastructure would cost roughly 4-10x more.

---

## Sources

### Pulumi / IaC
- [pulumi/pulumi-hcloud GitHub](https://github.com/pulumi/pulumi-hcloud) — 101 stars, Apache-2.0, bridged Terraform provider
- [hetznercloud/terraform-provider-hcloud GitHub](https://github.com/hetznercloud/terraform-provider-hcloud) — 689 stars, MPL-2.0, maintained by Hetzner
- [Pulumi hcloud Registry](https://www.pulumi.com/registry/packages/hcloud/)
- [OpenTofu](https://opentofu.org/) — MPL-2.0, Linux Foundation governance

### Hetzner pricing
- [Hetzner Dedicated Server Matrix](https://www.hetzner.com/dedicated-rootserver/matrix-ax/)
- [Hetzner Cloud Pricing](https://www.hetzner.com/cloud/pricing/)
- [Hetzner GEX44 GPU Server](https://www.hetzner.com/dedicated-rootserver/gex44/)
- [Hetzner Object Storage](https://www.hetzner.com/storage/object-storage)
- [Hetzner Price Adjustment April 2026](https://www.hetzner.com/pressroom/statement-price-adjustment/)

### k3s on Hetzner
- [vitobotta/hetzner-k3s](https://github.com/vitobotta/hetzner-k3s) — ~2k stars, simplest bootstrapping tool
- [kube-hetzner/terraform-hcloud-kube-hetzner](https://github.com/kube-hetzner/terraform-hcloud-kube-hetzner) — ~3.8k stars, battle-tested patterns
- [hetznercloud/csi-driver](https://github.com/hetznercloud/csi-driver) — official CSI, maintained by Hetzner
- [hetznercloud/hcloud-cloud-controller-manager](https://github.com/hetznercloud/hcloud-cloud-controller-manager)
- [Kubernetes Autoscaler Hetzner provider](https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler/cloudprovider/hetzner/README.md)
- [Autoscaler route cleanup bug #4049](https://github.com/kubernetes/autoscaler/issues/4049)

### Self-hosted runners
- [GitHub Docs: Self-Hosted Runners](https://docs.github.com/actions/hosting-your-own-runners/managing-self-hosted-runners/adding-self-hosted-runners)
- [GitHub Docs: Secure Use Reference](https://docs.github.com/en/actions/reference/security/secure-use)
- [Sysdig: Shai-Hulud worm using self-hosted runners](https://www.sysdig.com/blog/how-threat-actors-are-using-self-hosted-github-actions-runners-as-backdoors)
- [GitHub Actions Runner Controller (ARC)](https://docs.github.com/en/actions/concepts/runners/actions-runner-controller)

### PostgreSQL
- [Autobase (formerly postgresql_cluster)](https://github.com/vitabaks/autobase) — MIT, automated HA Postgres on Hetzner
- [Autobase Hetzner deployment docs](https://autobase.tech/docs/deployment/hetzner)
- [Ubicloud Managed PostgreSQL on Hetzner](https://www.ubicloud.com/blog/open-and-portable-managed-postgresql-avail-hetzner)
- [Aiven pricing](https://aiven.io/pricing) / [cloud regions](https://aiven.io/docs/platform/reference/list_of_clouds)

### Deployment config
- [Kompose](https://kompose.io/) — k8s SIG project, one-time Compose-to-k8s conversion
- [Docker Compose Bridge](https://docs.docker.com/compose/bridge/) — experimental, Docker Desktop only
- [Tanka](https://github.com/grafana/tanka) — Jsonnet-based, k8s only
- [cdk8s](https://cdk8s.io/) — AWS-backed, k8s only
- [Timoni](https://timoni.sh/) — CUE-based, pre-1.0
