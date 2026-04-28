---
id: T3
title: Snapshot tests for build.py argument assembly
status: plan-needed
depends_on: [T2]
---

# T3: Snapshot tests for build.py argument assembly

See `ci-background.md` for shared CI context.

## Goal

Automated tests that verify `build.py` produces the correct `docker buildx bake` command arguments for each mode/gpu/registry combination, without running actual Docker builds.

## Context

`build.py` is untested. The interesting logic is argument assembly — which targets, which cache refs, which tags, `--load` vs `--push`. `docker buildx bake --print` outputs the resolved build plan as JSON without building. We can use this to snapshot-test the orchestration logic.

## Key files

- `scripts/src/scripts/build.py`
- `compose.bake.yml`
- `compose.yml`

## Approach options (decide during implementation)

- **Option A:** Refactor `build.py` to separate argument assembly from execution, then unit test the assembly function directly against expected argument lists.
- **Option B:** Use `--print` flag on `docker buildx bake` to capture the resolved plan as JSON, then snapshot-test that output for each mode. Requires Docker installed but not running builds.

Option A is cleaner and faster to run. Option B tests closer to reality but has a Docker dependency.

## Depends on

T2 (the `--registry` option adds new argument paths that should be tested).

## Done when

- `uv run pytest` passes snapshot tests for all mode/gpu/registry combinations
