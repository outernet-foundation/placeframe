---
id: T102
title: CI preflight checks for linting, tests, and codegen staleness
status: in-review
depends_on: [T101]
---

# T102: CI preflight checks for linting, tests, and codegen staleness

## Goal

Extend CI with preflight checks that catch linting/formatting violations, type errors, test failures, and stale generated code before builds run. Resolve the open design question of whether preflight checks should gate all builds (including manual dispatches on feature branches) or only triggered builds on dev/main.

## Context

### What exists today

T101 established the preflight pattern: `lock-packages --check` runs before builds in both Docker and Unity CI. In the Docker workflow, it runs as a step in the build job (Python-only, instant). In the Unity workflow, it's a separate `check-locks` job. Both skip on `workflow_dispatch` — the rationale was that stale locks don't break builds (Unity/uv resolve on the fly), so feature branch iteration shouldn't be slowed.

The repo has linting and type-checking commands (`ruff check .`, `ruff format --check`, `basedpyright`, `deptry-check`) but none run in CI. There are a small number of tests: `scripts/tests/test_build_unity.py` (unit tests for build command assembly, 142 lines) and `docker/localizer/tests/test_build_metrics.py` (unit tests for inlier coverage, 41 lines). Empty test `__init__.py` files also exist in `docker/api/tests/` and `docker/localizer/tests/`. None of these run in CI.

T1 (linting CI) is `plan-needed` and covers the same scope as the linting portion of this ticket. T3 (snapshot tests for build.py) is `plan-needed`. T5 (API integration tests) is `design-needed`. T63 (basedpyright dev dependency) is `in-review`.

### Related existing tickets

- **T1** — "Add linting, formatting, and typechecking to CI" (`plan-needed`). Overlaps directly with the linting/formatting/typechecking portion of this ticket. Should be superseded by or merged into T102.
- **T3** — "Snapshot tests for build.py argument assembly" (`plan-needed`). The test infrastructure established by T102 would enable T3.
- **T5** — "Integration tests for API service" (`design-needed`). Heavier-weight testing that requires service containers. Out of scope for T102 but benefits from the CI test harness.
- **T63** — "Add basedpyright to dev dependencies" (`in-review`). Prerequisite for running basedpyright in CI — `uv run basedpyright` must work without a separate install step.

### The dispatch-gating question

T101 chose to skip lock-file checks on `workflow_dispatch` (feature branch manual triggers) because stale locks don't break builds. But several of the new checks have different characteristics:

- **Linting/formatting/type errors**: These DO break builds if the code has errors. But they also might be noise during rapid iteration on feature branches — an engineer might want to trigger a build to test something despite having a linting violation they haven't cleaned up yet.
- **Stale codegen**: If `generate-clients` or `generate-datamodels` output is stale, the build succeeds but ships incorrect API contracts. This is arguably worse than a lock file being stale — it's a correctness issue, not just a freshness issue. The instinct is that this should fail on ALL builds, not just dev/main triggers.
- **Tests**: If existing tests fail, that's a clear signal something is wrong regardless of branch.

This creates a tension: the T101 pattern was "feature branches get less friction" but some checks are about correctness, not freshness. The question is whether to:

1. **Gate everything on all dispatches** — simpler mental model, but adds friction to feature branch iteration. Engineers who want to skip checks can push directly and the checks only run in CI.
2. **Gate selectively** — lock file checks skip on dispatch (current), but codegen/lint/test checks always run. More complex YAML but matches the actual risk profile.
3. **Reconsider T101's skip-on-dispatch** — maybe lock file checks should also always run, and the "less friction" escape hatch is just `workflow_dispatch` without the checks at all (i.e., remove the skip entirely and don't add lock checks to dispatch).

### The codegen staleness problem

`generate-clients` can be checked statelessly — run the generator and diff output against committed files. It needs a running Litestar app to dump the OpenAPI spec, but the spec dump is a lightweight `python -m src.dump_openapi` invocation, not a full service startup.

`generate-datamodels` is harder. It introspects a **live PostgreSQL database** via `sqlacodegen`. The script connects to `postgresql+psycopg://placeframe_api_user:password@localhost:55432/placeframe`, reads the schema, and generates SQLAlchemy models + Pydantic DTOs. Running this in CI requires:

1. A PostgreSQL service container
2. Schema migrations applied (`migrate-database`)
3. The `sqlacodegen` + `datamodel-codegen` toolchain

This is substantially heavier than the other checks. It's closer to an integration test than a preflight check. The question is whether to:

- Include it in the same preflight job (with a postgres service container)
- Make it a separate job that runs in parallel
- Defer it entirely and only check `generate-clients` for now

### What checks to add

| Check | Command | Speed | Dependencies |
|-------|---------|-------|-------------|
| Lint | `uv run ruff check .` | <5s | None |
| Format | `uv run ruff format --check .` | <5s | None |
| Type check | `uv run basedpyright` | ~30s | T63 merged (basedpyright in dev deps) |
| Dep check | `uv run deptry-check` | <10s | None |
| Tests | `uv run pytest` | <10s (current suite is tiny) | None |
| Client codegen | `uv run generate-clients --config openapi-projects.json` + diff | ~30s | Litestar importable (may need pycolmap/pytorch for localizer spec) |
| Datamodel codegen | `uv run generate-datamodels` + diff | ~20s + postgres startup | PostgreSQL + migrations |

## Key files

- `.github/workflows/build-docker.yml` — Docker CI, would get lint/test/codegen steps
- `.github/workflows/build-unity.yml` — Unity CI, may get lint/test steps (already has lock check job)
- `scripts/pyproject.toml` — test deps, pytest config
- `scripts/tests/test_build_unity.py` — existing build command tests (142 lines)
- `docker/localizer/tests/test_build_metrics.py` — existing inlier coverage tests (41 lines)
- `docker/api/tests/__init__.py` — empty test package placeholder
- `scripts/src/scripts/generate_datamodels.py` — datamodel codegen (needs live postgres)
- `scripts/src/scripts/generate_clients.py` — client codegen (needs Litestar importable)
- `.pulsar/tickets/ci/t1-linting-ci.md` — existing ticket to supersede

## Design decisions

1. **Always gate.** All preflight checks run on every build — no skip-on-dispatch. Remove the `if: github.event_name != 'workflow_dispatch'` guards from T101's lock-packages checks too. If you trigger CI, you want the full picture. The escape hatch for rapid iteration is not triggering CI at all.
2. **Include datamodel codegen.** `generate-datamodels` staleness is checked in CI using a postgres service container + migrations. Both codegen commands (`generate-datamodels`, `generate-clients`) get `--check` flags that run the generator and diff output against committed files.
3. **Supersede T1.** T102 covers everything T1 does and more. Mark T1 as done.

## Approach

Implemented as a `preflight` job in both workflows:

**Docker workflow** (`build-docker.yml`): New `preflight` job with postgres service container (postgis/postgis:17-3.5) runs lint, format, typecheck, deptry, pytest, lock-packages --check --python-only, and codegen staleness checks (generate-datamodels via postgres + generate-clients --project docker/api). `build-and-lock` depends on `preflight`. Codegen staleness is detected via `git status --porcelain` after running generators.

**Unity workflow** (`build-unity.yml`): Renamed `check-locks` to `preflight`, removed dispatch-skip guard, added lint/format/typecheck/deptry/pytest steps before the lock-packages --check step. `build` job depends on `preflight` (no more skipped-is-ok condition).

No `--check` flags added to codegen commands — staleness is detected externally via git diff after running the generators. This avoids modifying the generator scripts.

## Done when

### Verifiable now
- `ruff check .`, `ruff format --check .`, `basedpyright`, `deptry-check` run in CI on all dispatches
- `uv run pytest` runs in CI and executes existing test suites
- CI fails on lint/format/type violations and test failures
- Generated client code staleness is detected (`generate-clients --check`, `generate-datamodels --check`)
- `generate-datamodels --check` runs against a postgres service container with migrations applied
- T101's `lock-packages --check` runs on all dispatches (skip-on-dispatch removed)
- T1 marked as done (superseded by T102)

### Requires manual verification
- CI preflight runs on all dispatch types (push, PR, workflow_dispatch)
- CI fails with clear output when any check detects a problem

## Next step

Push branch and verify CI passes on all dispatch types.
