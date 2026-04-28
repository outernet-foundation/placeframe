---
id: T103
title: Make localizer build_metrics test runnable from root pytest
status: plan-needed
depends_on: []
---

# T103: Make localizer build_metrics test runnable from root pytest

## Goal

Make `docker/localizer/tests/test_build_metrics.py` collectible and passing when running `uv run pytest` from the repo root, and add its path to `testpaths` in `pyproject.toml`.

## Context

The test file tests `_compute_inlier_coverage`, a pure-math function that only uses numpy and scipy (both available in the root workspace venv). However, it can't be collected from root for two reasons:

1. **Wrong import path** — the test imports `from build_metrics import _compute_inlier_coverage` but the module is `localize.build_metrics` (part of the `placeframe-localizer` package at `docker/localizer/src/localize/build_metrics.py`). This was partially fixed on the `feature/ci-cd` branch to `from localize.build_metrics import ...`, but that still fails because:

2. **Package not installed** — the `placeframe-localizer` package is not installed in the workspace root venv (it has heavy deps like torch and pycolmap). Even though numpy/scipy are available, `import localize` fails because the package itself isn't importable.

3. **Module-level imports block collection** — even if the package were importable, `build_metrics.py` imports `pycolmap` and `core.localization_metrics` at module level. The tested function doesn't use these, but Python evaluates all module-level imports on collection.

The likely fix is to extract `_compute_inlier_coverage` into a small module with only numpy/scipy imports, or use lazy imports for the heavy dependencies in `build_metrics.py`.

## Key files

- `docker/localizer/src/localize/build_metrics.py` — contains `_compute_inlier_coverage` and heavy module-level imports
- `docker/localizer/tests/test_build_metrics.py` — the test file (import path needs fixing)
- `pyproject.toml` — `testpaths` needs `docker/localizer/tests` added

## Approach

Extract `_compute_inlier_coverage` into a separate module (e.g. `inlier_coverage.py`) with only numpy/scipy deps. Update the test import and the call site in `build_metrics.py`. Add the test path to root `testpaths`.

## Done when

- `uv run pytest` from repo root collects and passes `test_build_metrics.py`
- `docker/localizer/tests` is listed in `testpaths` in `pyproject.toml`
- No new dependencies added to the root dev group

## Next step

Decide whether to extract the function into a new module or restructure imports in `build_metrics.py` to defer the heavy deps.
