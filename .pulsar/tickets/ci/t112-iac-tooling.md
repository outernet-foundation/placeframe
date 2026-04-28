---
id: T112
title: IaC tooling foundation (Pulumi vs OpenTofu + Ansible)
status: design-needed
depends_on: []
---

# T112: IaC tooling foundation (Pulumi vs OpenTofu + Ansible)

## Goal

Choose the IaC tooling stack for managing Hetzner infrastructure and set up the project scaffolding. This is the foundation that all subsequent infrastructure tickets build on.

## Context

T109 research (`.pulsar/research/hetzner-infrastructure.md`, section 1) evaluated the options:

### Pulumi

- Python SDK (`pulumi-hcloud` on PyPI), aligns with the project's language
- The provider is a bridge over `hetznercloud/terraform-provider-hcloud` — same resource coverage either way
- Apache-2.0 license (genuine FOSS)
- **VC-backed (Pulumi Inc., Series C, $75M+), no foundation governance** — open core model
- Pulumi Cloud (state backend) is proprietary SaaS, but self-managed backends (S3, local filesystem) are supported
- 101 GitHub stars, thin community layer over the Terraform bridge

### OpenTofu

- MPL-2.0, **Linux Foundation governance** — strongest FOSS story in IaC
- Uses the same Hetzner Terraform provider (maintained by Hetzner themselves, 689 stars)
- HCL instead of Python
- Mature ecosystem, large community, extensive documentation
- Binary-compatible with Terraform providers

### Ansible (required either way)

- Neither Pulumi nor OpenTofu can manage Hetzner dedicated (bare metal) servers — those use the Robot API, not the Cloud API
- Community Terraform providers for Robot exist but are abandoned (1-7 stars, last commits 2022-2023)
- Ansible is the battle-tested approach for dedicated server provisioning: order via Robot API, enable rescue mode, run installimage, configure via playbooks
- CI runners and GPU servers are dedicated — they need Ansible regardless of the Cloud IaC choice

### Key tradeoff

Python (Pulumi) vs HCL (OpenTofu) vs FOSS governance purity. The Apache-2.0 license protects Pulumi's code from relicensing, but the VC-backed single-company governance is a yellow flag under project FOSS principles. OpenTofu has the cleanest governance but requires learning HCL.

## Key files

- New: `infrastructure/` directory (or similar) for IaC project scaffolding
- New: Ansible playbooks for dedicated server provisioning

## Approach

Not yet determined. Decision needed: Pulumi or OpenTofu?

## Done when

- IaC tool chosen with rationale documented
- Project scaffolded: directory structure, dependency management, state backend configuration
- Ansible playbook structure for dedicated server provisioning
- Able to provision a test Hetzner Cloud VM and a test network via the chosen IaC tool
- Able to configure a test dedicated server via Ansible (if a server is available)

## Next step

Decide between Pulumi and OpenTofu. The FOSS governance argument favors OpenTofu. The Python argument favors Pulumi. Both use the same underlying Hetzner provider. Consider: is writing HCL for ~50-100 resources a meaningful barrier, or is it a one-time learning cost that pays off in governance confidence?
