---
id: T110
title: Migrate all Python packages from relative to absolute imports
status: plan-needed
depends_on: []
---

# T110: Migrate all Python packages from relative to absolute imports

## Goal

Replace all relative imports (`from ..module import ...`, `from ...shared.cache import ...`) with absolute imports (`from build_scripts.shared.cache import ...`) across every Python package in the repo, and update the CLAUDE.md convention to mandate absolute imports going forward.

## Context

The codebase convention (CLAUDE.md line 77) currently mandates relative imports for intra-package use. This worked when packages were shallow, but several packages now have 3+ levels of nesting (e.g. `build_scripts/placeframe/ci/`), producing hard-to-read triple-dot imports like `from ...shared.cache import restore`. As packages grow deeper, this will only get worse.

Absolute imports read the same regardless of nesting depth, are used by the Python standard library and every major framework, and the "what if the package is renamed" argument doesn't apply to application code (or even to redistributable packages in practice).

Current scope: 51 relative imports across 20 files in two main areas:
- `build/src/build_scripts/` — CI/build tooling (heaviest nesting, triple-dot imports)
- `docker/api/src/routers/` — API service (double-dot imports)

This is a mechanical change but highly invasive — it touches every Python package and requires careful validation that nothing breaks.

## Key files

- `CLAUDE.md` — convention change (line 77: relative → absolute)
- `build/src/build_scripts/placeframe/ci/*.py` — heaviest concentration (8 files, triple-dot imports)
- `build/src/build_scripts/cesium/*.py` — 3 files with double/triple-dot imports
- `build/src/build_scripts/placeframe/lock_unity.py` — 1 file
- `docker/api/src/routers/*.py` — 8 files with double-dot imports
- All other `packages/python/*/src/` directories — audit for relative imports

## Approach

Mechanical find-and-replace per package: resolve each relative import to its absolute form based on the package's top-level name. Validate with `uv run ruff check .` and `uv run basedpyright` after each package is converted. Update CLAUDE.md convention last.

## Done when

### Verifiable now
- Zero relative imports in the codebase (`grep -r "from \.\." --include="*.py"` returns nothing)
- `uv run ruff check .` passes
- `uv run basedpyright` passes
- CLAUDE.md line 77 updated to mandate absolute imports

### Requires manual verification
- CI passes on the migration branch
- No runtime import errors in Docker services

## Next step

Enter plan mode to decide the migration order (per-package or all-at-once) and whether to use an automated rewriting tool (e.g. `absolufy-imports`) or do it manually.
