---
id: T1
title: Add linting, formatting, and typechecking to CI
status: done
depends_on: []
---

# T1: Add linting, formatting, and typechecking to CI

See `ci-background.md` for shared CI context.

## Goal

Run `ruff check`, `ruff format --check`, `basedpyright`, and `deptry-check` on every push and PR.

## Context

These tools are already configured in the root `pyproject.toml` and run locally. They just aren't in CI yet.

## Key files

- `pyproject.toml` — tool configs (ruff, basedpyright, deptry)
- `scripts/src/scripts/deptry_check.py` — custom deptry wrapper
- `.github/workflows/build.yml` — existing workflow

## Approach

Create a new `.github/workflows/ci.yml` workflow (separate from `build.yml`) that runs on push to `main` and on PRs. Two parallel jobs: `lint-and-typecheck` (ruff, basedpyright, deptry) and `test`. Both need `uv sync --all-packages` first. Use `astral-sh/setup-uv@v5`.

**Decision:** Keep this as a separate workflow from `build.yml`. Linting should run on PRs (fast feedback); image builds only run on `main` (expensive). Don't combine them.

## Notes

- `docker/localizer/tests/` and `dirtorch/test_dir.py` require PyTorch — must be excluded from the test job with `--ignore` flags
- `basedpyright` runs in strict mode across the whole workspace — may take 2-5 minutes

## Done when

- CI workflow file `.github/workflows/ci.yml` exists
- Workflow passes `ruff check`, `ruff format --check`, `basedpyright`, and `deptry-check` in a real GitHub Actions run on a test PR

## Log

Superseded by T102, which covers linting/formatting/typechecking plus tests and codegen staleness checks in a unified CI preflight design.
