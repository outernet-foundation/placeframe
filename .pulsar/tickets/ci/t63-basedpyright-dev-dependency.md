---
id: T63
title: Add basedpyright to dev dependencies
status: in-review
depends_on: []
---

# T63: Add basedpyright to dev dependencies

## Goal

Make `uv run basedpyright` work inside the COI sandbox.

## Context

`basedpyright` is configured in the root `pyproject.toml` (`[tool.basedpyright]` section) but is not listed in the `[dependency-groups] dev` list. Running `uv run basedpyright` fails with "No such file or directory". The package is available on PyPI and bundles its own Node binary.

## Key files

- `pyproject.toml` — add `basedpyright>=1.28.0` to the dev dependency group (line 9)

## Approach

Add `basedpyright` to the dev dependency group. Run `uv sync --all-packages` to install. Verify `uv run basedpyright` runs.

## Done when

- [ ] `basedpyright` listed in dev dependencies in `pyproject.toml`
- [ ] `uv run basedpyright` succeeds (may report type errors, but the command itself runs)

## Log

Clean implementation, no issues.

## Observations

No pre-existing issues noticed.
