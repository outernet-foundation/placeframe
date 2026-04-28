---
id: T116
title: Deployment config renderer for Compose and k8s manifests
status: plan-needed
depends_on: [T114]
---

# T116: Deployment config renderer for Compose and k8s manifests

## Goal

Build a Python tool that generates both Docker Compose files (local dev) and Kubernetes manifests (k3s production) from a shared service configuration, eliminating config duplication between environments.

## Context

T109 research (`.pulsar/research/hetzner-infrastructure.md`, section 6) evaluated existing tools and found none solve the dual-target problem cleanly.

### Why not existing tools?

| Tool | Problem |
|---|---|
| Kompose | One-time migration only. Doesn't handle init services, health-gated deps, profiles, `include` directives |
| Tanka | k8s only, adds Jsonnet (niche language), Grafana VC-backed |
| cdk8s | k8s only, AWS-controlled, heavyweight |
| Timoni | k8s only, pre-1.0, CUE lang |
| Helm + Compose | Works but duplicates every service definition across ~15 services |

### Current Compose complexity

`compose.yml` has ~15 services with:
- `x-image-ref` extension fields and `${VAR:?err}` env-var references (resolved from `.env.lock`)
- `depends_on` with health conditions
- Profiles (e.g. ngrok for local-only)
- `include` directives (e.g. `compose.postgres.yml`)
- Init/one-shot services (`initialize-minio`, `create-database`, `auth-initializer`)
- Docker socket mounts (local-only)

### Recommended approach: custom Python renderer

A Python script that reads a shared config (YAML/TOML/dataclasses) and renders both targets:
- **Compose renderer**: straightforward dict-to-YAML
- **k8s renderer**: Deployments, Services, ConfigMaps, PVCs, init containers (from one-shot services)
- Integrates with existing `.env.lock` digest pinning
- Estimated scope: 500-800 lines for both renderers + shared config schema
- No external dependencies beyond PyYAML
- Can evolve incrementally — start with k8s side only, keep existing Compose as-is initially

### Alternative: Helm + keep Compose (the "boring" path)

If the custom renderer feels too ambitious, the fallback is maintaining Helm charts alongside the existing Compose file. More duplication but zero new tooling. Most teams do this.

## Key files

- `docker/compose.yml` — existing Compose file (source of truth for service definitions)
- `docker/compose.postgres.yml` — included Compose file
- `.env.lock` — pinned image digests
- New: shared service config (YAML/TOML in `infrastructure/` or `deploy/`)
- New: renderer script (in `scripts/src/scripts/` or `build/src/build_scripts/`)
- New: generated k8s manifests output directory

## Approach

Not yet determined. Key decisions: config format (YAML vs TOML vs Python dataclasses), how to handle environment-specific overrides (local-only services, production-only settings), whether to start by generating k8s from existing Compose or define a new shared format from scratch.

## Done when

- Shared config captures all ~15 services with their ports, env vars, volumes, health checks, dependencies
- Compose renderer produces a `compose.yml` functionally equivalent to the current one
- k8s renderer produces manifests that deploy successfully to the k3s cluster (T114)
- Init/one-shot services rendered as k8s init containers or Jobs
- Local-only services (ngrok, cloudbeaver) excluded from production output
- `.env.lock` digest pinning feeds into both targets
- New `uv run` command registered for generation (e.g. `uv run generate-deploy`)
- Generated output checked into repo (like other generated packages)

## Next step

Wait for T114 (k3s cluster) to exist so the k8s output can be tested. Can begin design work earlier by analyzing the current Compose file and defining the shared config schema.
