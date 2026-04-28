---
id: T71
title: Set up scoped UPM registry for Placeframe Unity packages
status: in-review
depends_on: []
branch: feature/upm-packages
plan: t71-plan.md
---

# T71: Set up scoped UPM registry for Placeframe Unity packages

## Goal

Host Placeframe UPM packages on a scoped registry so Unity projects can resolve them like any other package dependency, with proper transitive dependency resolution.

## Context

The Placeframe Unity projects consume custom packages. All were previously referenced via `file:` relative paths in each project's `Packages/manifest.json`. This means consuming projects must manually list every transitive dependency — the package manager can't resolve the dependency tree automatically. A proper registry fixes this.

## Key files

- `packages/unity/Placeframe/Assets/Package/*/package.json` — UPM package definitions
- `apps/*/Packages/manifest.json` — consumer project manifests
- `legacy/Outernet.Client/Packages/manifest.json` — same
- `.github/workflows/publish-upm.yml` — publish workflow

## Approach

Publish Placeframe packages to npmjs.org under the `org.outernet` scope. Authentication via OIDC trusted publishing (no long-lived tokens). See `.pulsar/plans/t71-plan.md` for original plan (note: package names changed from `com.placeframe.vps*` to `org.outernet.placeframe*` during implementation).

## Done when

- [x] Package.json metadata correct (license, repository, inter-package deps)
- [x] Publish workflow created (`.github/workflows/publish-upm.yml`)
- [x] ~~Manifest.json files updated with scoped registry entries and version refs~~ *(Reversed: manifests should use `file:` refs for monorepo packages — see T88)*
- [x] OIDC trusted publishing configured (replaces NPM_TOKEN)
- [x] Publish workflow triggered and all 3 packages live on npmjs.org
- [x] At least one Unity project opens and resolves all packages from registries
- [ ] *(Added post-review)* Monorepo app manifests reverted to `file:` references for in-repo packages (T88)

## Design decisions

- **npmjs.org as the registry.** GitHub Packages was considered but forces `@scope/` naming that's unproven with Unity UPM. npmjs.org is already used by the project (Magic Leap packages), and the rug-pull risk is negligible (too foundational to the npm ecosystem). No need for self-hosted Verdaccio.
- **`org.outernet` scope.** Packages renamed from `com.placeframe.vps*` to `org.outernet.placeframe*` to align with the Outernet Foundation identity across all FOSS projects.
- **OIDC trusted publishing over NPM_TOKEN.** npm's trusted publishing uses short-lived OIDC tokens from GitHub Actions — no secrets to manage or rotate. Requires Node 24+ (npm >=11.5.1) and `id-token: write` permission. The `setup-node` `registry-url` parameter must NOT be used as it writes a token placeholder that blocks OIDC.
- **~~Proper dependency resolution is the primary driver.~~** *(Reversed — see below.)* Decision changed: monorepo app manifests should use `file:` references for packages that live in the repo. Registry publishing is still useful for external consumers, but intra-monorepo references must be `file:` paths so local edits take effect immediately without a publish cycle. Transitive dependency listing is an acceptable cost. T88 tracks reverting the manifests.

## Log

- Initial implementation used `NPM_TOKEN` secret. First publish failed with 403 (token lacked 2FA bypass). Switched to OIDC trusted publishing instead.
- OIDC publish failed with 404 — `setup-node` with `registry-url` writes an `.npmrc` token placeholder that blocks OIDC. Fix: drop `registry-url`, use Node 24 (ships npm with native OIDC support).
- Package names changed from `com.placeframe.vps*` to `org.outernet.placeframe*` mid-implementation. Old packages on npmjs.org should be deprecated/unpublished.
- Repository URL in package.json was `plerion.git` (old repo name), fixed to `placeframe.git`.

## Observations

- `apps/MakeItSing/Packages/manifest.json` had hardcoded Windows absolute paths for Placeframe packages. Fixed by switching to registry references.
- `com.cysharp.r3` git dependency was unpinned across all 5 manifests. R3 1.3.0 introduced breaking API changes. Pinned to `#1.2.9` as a driveby fix.
- UnityNuGet packages (`org.nuget.placeframeapiclient`, `org.nuget.placeframezedclient`) resolve successfully from the UnityNuGet registry — confirmed in AndroidMobile package cache.
- `publish-upm.yml` has a `feature/upm-packages` branch trigger added for testing — remove it before merging to main (keep only `workflow_dispatch` + `v*` tags).
- Old `com.placeframe.vps*` packages on npmjs.org should be deprecated or unpublished.
