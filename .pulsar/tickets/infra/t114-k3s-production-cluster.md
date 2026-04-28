---
id: T114
title: k3s production cluster on Hetzner Cloud
status: plan-needed
depends_on: [T112]
---

# T114: k3s production cluster on Hetzner Cloud

## Goal

Stand up a k3s cluster on Hetzner Cloud VMs capable of running Placeframe services in production, with autoscaling, ingress, TLS, and persistent storage.

## Context

T109 research (`.pulsar/research/hetzner-infrastructure.md`, sections 2 and 3) established the architecture.

### Cluster topology

Starter cluster (~76 EUR/month with shared vCPU, ~162 EUR/month with dedicated):
- 3x control plane nodes (CX33: 4 vCPU, 8 GB) with embedded etcd for HA
- 3x worker nodes (CPX42: 8 vCPU, 16 GB) for application workloads
- All on Hetzner private network, k3s inter-node traffic over private interface

### Bootstrapping

Three options identified, in order of simplicity:
1. **`hetzner-k3s` CLI** ([vitobotta/hetzner-k3s](https://github.com/vitobotta/hetzner-k3s)) — single binary, YAML config, ~2k stars. Automatically installs CCM, CSI, autoscaler. Simplest path but another tool outside the IaC stack.
2. **IaC (Pulumi/OpenTofu) + cloud-init** — provision VMs via IaC, bootstrap k3s via cloud-init scripts or `k3sup`. More control, more work, consistent with T112's IaC tooling.
3. **Patterns from `kube-hetzner`** Terraform module (~3.8k stars) — battle-tested patterns (MicroOS, component selection, network topology) transferable regardless of IaC tool.

### Networking

- **Flannel** (default CNI): works well on Hetzner, must bind to private interface (`--flannel-iface=enp7s0`). Simple, low overhead.
- **Cilium** (alternative): eBPF-based, Hubble observability, WireGuard encryption. More config. Open UDP 51871 if using WireGuard.
- **Hetzner private networks**: up to 100 nodes per network (scaling limitation).
- **Hetzner Load Balancers**: automatically provisioned via `Service type: LoadBalancer` through hcloud-cloud-controller-manager. ~5 EUR/month. Must use `use-private-ip` annotation.

### Storage

- **hcloud-csi**: official driver, maintained by Hetzner. Automatic PVC provisioning, ReadWriteOnce only, 10 GB to 10 TB.
- **Performance warning**: network-attached volumes with 3x replication. Advertised 5,000 sustained IOPS, but real-world random 4K writes ~325 IOPS. Local NVMe is ~33,000 IOPS (10x faster). Not suitable for database workloads (see T115).

### Autoscaling

- Kubernetes cluster-autoscaler with built-in Hetzner provider. Works with k3s via cloud-init join scripts.
- **Known bug**: route cleanup on scale-down ([kubernetes/autoscaler#4049](https://github.com/kubernetes/autoscaler/issues/4049)) — stale pod routes when nodes are removed. Mitigate with large subnets.
- **PDB interaction bug** ([#9111](https://github.com/kubernetes/autoscaler/issues/9111)): autoscaler may refuse to scale down underutilized nodes with PDBs + topology spread constraints.

### Ingress + TLS

- Traefik (bundled with k3s) or nginx-ingress behind Hetzner LB
- cert-manager + Let's Encrypt for TLS
- Default Traefik config needs hardening (unsecured dashboard, no HTTPS redirect)

### GPU workloads

Hetzner Cloud does NOT offer GPU VMs. GPU is bare-metal only:
- GEX44: RTX 4000 SFF Ada, 20 GB VRAM, 184 EUR/month
- GEX131: RTX PRO 6000 Blackwell, 96 GB VRAM, 889 EUR/month

These are non-elastic dedicated servers. If localizer/reconstructor workloads need GPU and demand is bursty, options are: fixed GPU capacity (accept idle cost), schedule GPU jobs to k3s nodes backed by bare metal (using labels/taints), or hybrid with a hyperscaler GPU fallback for burst. This is a design decision for this ticket.

## Key files

- New: IaC definitions for Hetzner Cloud VMs, networks, firewalls, LBs (in `infrastructure/` from T112)
- New: k3s bootstrap configuration (cloud-init scripts or `hetzner-k3s` config)
- New: Helm values / manifests for cluster components (CCM, CSI, autoscaler, cert-manager, ingress)
- `docker/compose.yml` — reference for service definitions (source of truth for what needs to run in production)

## Approach

Not yet determined. Key decisions: bootstrapping tool choice, Flannel vs Cilium, GPU workload strategy.

## Done when

- k3s cluster running on Hetzner Cloud with HA control plane (3 nodes)
- Worker nodes provisioned and joined
- hcloud-cloud-controller-manager installed (LoadBalancer service type works)
- hcloud-csi-driver installed (PVC provisioning works)
- Ingress controller configured with TLS via cert-manager + Let's Encrypt
- Cluster autoscaler configured and tested (scale up on demand, scale down on idle)
- Firewall rules configured (private network for inter-node, public for ingress only)
- `kubectl` access configured for the team
- At least one Placeframe service deployed as a test (e.g. the API) to validate the full path: DNS → LB → ingress → service → pod

## Next step

Wait for T112 (IaC tooling) decision, then plan the cluster bootstrap.
