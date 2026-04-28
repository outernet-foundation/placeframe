---
id: T113
title: Self-hosted CI runners on Hetzner bare metal
status: plan-needed
depends_on: [T111, T112]
---

# T113: Self-hosted CI runners on Hetzner bare metal

## Goal

Provision Hetzner dedicated servers as self-hosted GitHub Actions runners and migrate all CI workflows from GitHub-hosted runners to self-hosted, eliminating per-job container startup overhead, ORAS cache round-trips, and dependency on GitHub-hosted compute.

## Context

T109 research (`.pulsar/research/hetzner-infrastructure.md`, sections 2 and 4) established the hardware and runner architecture.

### Hardware

The **AX102** is the recommended CI runner server: AMD Ryzen 9 7950X3D (16C/32T), 128 GB DDR5, 2x 1.92 TB NVMe Gen4, ~126 EUR/month. This replaces GitHub-hosted `ubuntu-latest` runners that currently pay ~3 min overhead per Unity job (pulling ~4 GB container image, freeing disk, installing .NET/ORAS, restoring license from ORAS). With warm local caches, Unity builds should complete in 3-5 minutes.

Available in Falkenstein, Nuremberg, Helsinki. Ordering takes hours to a few business days. Setup fee ~79 EUR.

**Important:** Hetzner raises prices April 1, 2026 (up to 37% on some products). Ordering before then may lock in current pricing.

### Runner architecture

- **Persistent mode** (not ephemeral) — Unity Library caches (5-20+ GB per project/platform) live on local NVMe. Ephemeral runners would need ORAS restoration every job.
- **One Unity runner agent per machine** — Unity is too resource-hungry for concurrent builds. A second lightweight runner for non-Unity jobs is fine with concurrency groups.
- **Systemd service** via the runner's `svc.sh install`. Dedicated low-privilege `github-runner` user, no sudo.
- **Runner labels**: `self-hosted`, `Linux`, `X64`, `unity`, `hetzner` — workflows target via `runs-on: [self-hosted, Linux, unity]`.
- **Organization-level runner groups** (requires GitHub Team plan) restrict which repos can use the runners.

### What becomes unnecessary on self-hosted

- `free_disk_space()` in `build/src/build_scripts/shared/setup.py` — no pre-installed Android SDK, .NET, GHCup, Swift to remove
- `install_dotnet()` — pre-installed on the server
- `install_oras()` in `shared/setup_oras.py` — pre-installed
- Unity license ORAS restore — license pre-activated on the server
- `unityci/editor` container images — Unity editor pre-installed natively
- ORAS cache round-trips for Library — local NVMe is the primary cache
- `actions/cache` for UPM packages — local directory persists
- The `/to_clean/*` volume mount hack for disk space

### Cleanup between jobs

- Remove build artifacts (`Builds/`, `Logs/`, `Temp/`) but preserve `Library/`
- Kill orphaned Unity processes
- Monitor disk space (alert at 80%)
- Weekly prune Library caches for branches deleted from remote
- Prune runner `_diag/` logs older than 30 days

### Dependencies

- **T111** (CI trigger policy) must be resolved first — determines how workflows are triggered on self-hosted
- **T112** (IaC tooling) must be resolved first — Ansible playbooks for dedicated server provisioning

## Key files

- `.github/workflows/build-unity.yml` — change `runs-on`, remove container config, simplify setup steps
- `.github/workflows/build-cesium-native.yml` — same changes
- `.github/actions/setup-uv/action.yml` — remove `astral-sh/setup-uv` (uv pre-installed)
- `build/src/build_scripts/shared/setup.py` — `free_disk_space()` and `install_dotnet()` become no-ops or conditional
- `build/src/build_scripts/shared/setup_oras.py` — `install_oras()` becomes no-op or conditional
- `build/src/build_scripts/shared/cache.py` — may switch from ORAS to local cache, or keep ORAS as fallback
- `build/src/build_scripts/shared/license_restore.py` — becomes no-op on self-hosted
- `build/src/build_scripts/placeframe/ci/build_unity.py` — simplified setup phase
- New: Ansible playbook for CI runner provisioning (Unity, .NET, ORAS, uv, runner agent)
- New: cleanup scripts (post-job, weekly prune)

## Approach

Not yet determined. Depends on T111 (trigger policy) and T112 (IaC tooling) decisions.

## Done when

- At least one Hetzner AX102 provisioned and configured via Ansible
- Runner agent installed, registered, running as systemd service
- All CI workflow jobs execute on self-hosted runners (both `build-unity.yml` and `build-cesium-native.yml`)
- Unity builds complete successfully with warm local Library caches
- Docker builds complete successfully on self-hosted
- Preflight checks complete successfully on self-hosted
- Setup overhead reduced from ~3 min to near-zero
- Cleanup between jobs implemented (post-job step + weekly prune)
- Build scripts gracefully handle both self-hosted and GitHub-hosted environments (conditional setup steps) during transition
- `commit-artifacts` job works on self-hosted (git push with appropriate credentials)

## Next step

Wait for T111 and T112 to be resolved, then plan the migration.
