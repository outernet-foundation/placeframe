---
id: T83
title: Consolidate CI free-disk-space approach across workflows
status: design-needed
depends_on: []
---

# T83: Consolidate CI free-disk-space approach across workflows

## Goal

Replace the third-party `jlumbroso/free-disk-space` action in `build-docker.yml` with inline `rm -rf` commands, matching the pattern used in `build-unity.yml` and `build-cesium-native.yml`. One consistent approach to freeing disk space across all workflows.

## Context

Three workflows currently free disk space before heavy builds:

- `build-docker.yml` — uses `jlumbroso/free-disk-space@v1.3.1` action (runs on host, no container)
- `build-unity.yml` — volume-mounts host paths into container and `rm -rf` them (runs in container)
- `build-cesium-native.yml` — same volume-mount approach (runs in container)

The `jlumbroso` action is a thin wrapper around `rm -rf` plus `apt-get remove` for large packages and `swapoff`/`rm` for swap. Replacing it with inline commands drops a third-party dependency and makes all workflows consistent. The container-based workflows will keep their bind-mount approach since they can't run host commands directly.

The design question is: exactly which paths should we delete? The action cleans Android SDK, .NET, Haskell, tool cache, large apt packages, Docker images, and swap. Not all of these may be necessary or desirable for every workflow. We should audit what actually saves meaningful space and what's already gone by the time the step runs.

## Key files

- `.github/workflows/build-docker.yml` — switch from action to inline commands
- `.github/workflows/build-unity.yml` — reference for current inline approach
- `.github/workflows/build-cesium-native.yml` — reference for current inline approach

## Done when

- [ ] `build-docker.yml` no longer uses `jlumbroso/free-disk-space`
- [ ] All three workflows use a consistent set of paths to clean (accounting for host vs container differences)
- [ ] No regressions in available disk space during builds

## Next step

Audit what `jlumbroso/free-disk-space` actually deletes vs what the Unity workflows delete, and decide on the right set of paths for host-based workflows.
