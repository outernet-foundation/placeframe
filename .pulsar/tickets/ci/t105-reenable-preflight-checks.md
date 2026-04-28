---
id: T105
title: Re-enable preflight checks disabled by T104
status: plan-needed
depends_on: [T104]
---

# T105: Re-enable preflight checks disabled by T104

## Goal

Re-enable basedpyright, deptry-check, and pytest in the preflight-checks action. These were disabled in T104 because torch and lightglue aren't available on the bare CI runner.

## Context

T104 unified CI into a single workflow (`ci.yml`) but disabled three preflight checks that fail without torch:

1. **basedpyright** — type checking fails because torch type stubs aren't installed on the bare runner.
2. **deptry-check** — dependency checking fails because torch and lightglue aren't importable.
3. **pytest** — disabled because there are currently no bare-runner-compatible tests.

The root cause is the same for all three: `uv sync --all-packages` on the bare runner doesn't install GPU extras (torch, lightglue), so any code that imports these packages fails at analysis time.

## Key files

- `.github/actions/preflight-checks/action.yml` — the composite action where these checks are disabled
- `scripts/src/scripts/deptry_check.py` — deptry wrapper
- Per-service `pyproject.toml` files — dependency declarations and deptry config

## Design decisions

1. **Install CPU torch on the preflight runner.** No viable type stubs package exists (`types-torch` is v0.1.1, stale). PyTorch ships inline type annotations via `py.typed`, so the real package is needed. CPU-only torch (~200MB) is sufficient for type checking, dependency validation, and tests. `setup-uv` already caches `~/.cache/uv` via GitHub Actions cache, so torch is only downloaded on cache miss.

## Approach

Not yet determined — needs planning.

## Done when

### Verifiable now
- basedpyright runs in preflight and passes
- deptry-check runs in preflight and passes
- pytest runs in preflight and passes (even if no tests exist yet — the runner should not skip it)

### Requires manual verification
- CI run completes with all three checks enabled and green
