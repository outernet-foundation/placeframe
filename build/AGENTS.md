# build/

## What this is

`build/` is a Python workspace member (`build-scripts`) that ships the placeframe-wide CLI commands invoked via `uv run <name>` from the repo root. It owns two cohorts of commands: codegen + workspace tooling (`generate-clients`, `generate-datamodels`, `deptry-check`, `preflight`) and the Cesium asset pipeline (`build-cesium`, `codegen-cesium`, `combine-cesium`). A third cohort under `placeframe/ci/` exists to be invoked from `.github/workflows/`; those commands are not intended for operator use locally. The Docker-stack lifecycle commands (`up`, `down`, `build`) and their helpers (`detect_gpu`, `modes`, `context_sha`) live in the standalone [`docker-devkit`](https://github.com/outernet-foundation/docker-devkit) repo, a PyPI dependency of this package (`docker-devkit>=0.1.0`); it depends on it for `compute_service_shas` / `run_build` in its CI commands. The Unity build commands (`compile-unity`, `lock-unity`, `test-unity`, `build-unity`, `unity-matrix`, license helpers) live in the standalone [`unity-devkit`](https://github.com/outernet-foundation/unity-devkit) repo — see its `AGENTS.md` — which this package depends on for `license_restore` in the Cesium pipeline. The CI runner floor (`ci_step`, runner setup, ORAS cache) lives in the standalone [`ci-devkit`](https://github.com/outernet-foundation/ci-devkit) repo, a PyPI dependency of this package (`ci-devkit>=0.1.0`); the CI commands and the Cesium pipeline import `ci_step` / `setup` / `setup_oras` / `cache` from it. The Python workspace-locking command (`lock-python`) and the Python check battery (`preflight`) live in the standalone [`python-devkit`](https://github.com/outernet-foundation/python-devkit) repo, PyPI dependencies of this package (`python-devkit>=0.1.0`); the group-export redirect for the neural-networks accelerator groups is configured in the root `pyproject.toml` under `[tool.python-devkit.lock-python]`, and the battery's toggles (sync args, deptry exclusions) under `[tool.python-devkit.preflight]`; `preflight` calls the battery in-process around its repo-specific blocks. The OpenAPI client-generation wrapper — spec 3.1→3.0 downgrade, the patched C# templates, the `openapi-generator-cli` invocation, and the Unity package metadata — lives in the standalone [`openapi-client-codegen`](https://github.com/outernet-foundation/openapi-client-codegen) repo; `generate-clients` is a `[project.scripts]` alias of its CLI (`openapi_client_codegen.cli:app`), and `build/openapi-projects.json` carries the repo identity (naming root, npm scope, license, repository URL, generated root) and the spec command (+ `spec_env`) as data — no wrapper module. The publish/release commands (`publish-stable`, `create-release`, `ensure-release-pr`, `fetch-ci-artifacts`, `mirror-images`) live in the standalone [`release-devkit`](https://github.com/outernet-foundation/release-devkit) repo; this repo declares its package identities, tag prefixes, and registry mappings in `build/publish-config.json`, and the workflows invoke the release-devkit entry points uvx-isolated (`uvx --from release-devkit==<version> … publish-stable --config build/publish-config.json`). The sibling `scripts/` package holds operator utilities (calibration, debug attach, capture-tool install, ZED Box deploy) — see `scripts/AGENTS.md` for that catalog.

## Shape

### Stack lifecycle (operator-facing)

`up`, `down`, and `build` now live in the external [`docker-devkit`](https://github.com/outernet-foundation/docker-devkit) repo — see its `AGENTS.md` for their flags and the native-vs-consumer-stack behavior.

### Codegen + workspace tooling (operator-facing)

Defined in `build/pyproject.toml`'s `[project.scripts]`. All commands accept `--help`.

| `uv run` command | Module | Notes |
|---|---|---|
| `generate-clients` | `openapi_client_codegen.cli:app` (alias) | Entry into [`openapi-client-codegen`](https://github.com/outernet-foundation/openapi-client-codegen)'s config-driven orchestrator: `openapi-projects.json` is the single source of identity (naming root `placeframe`, `org.outernet.placeframe.*` npm scope, Apache-2.0, repository URL, `packages/generated/` root) and of the spec command (`uv run --project . python -m src.dump_openapi` with `spec_env` `CODEGEN=1`), validated by the library's pydantic model. The verb produces each Litestar app's spec, downgrades it, skips on committed-spec equality, and syncs each client — C# clients stamped `0.0.0-local` with Unity x-wildcard dependency ranges. Needs Java 11+ on PATH (the lib runs `openapi-generator-cli`). Pass `--project docker/api` to skip the localizer (whose spec dump needs PyTorch / pycolmap in the venv). |
| `generate-datamodels` | `placeframe/generate_datamodels.py` | Runs `sqlacodegen` against live postgres → `packages/generated/python/datamodels/` (SQLAlchemy + Pydantic DTOs). Requires the stack to be up. |
| `preflight` | `placeframe/ci/preflight.py` | The exact command CI invokes — image-ref + version-coupling checks, database setup, python-devkit's preflight battery in-process (sync, lint, format, type check, deptry per workspace member, pytest, lock-file check, ruff drift — toggles in the root `[tool.python-devkit.preflight]` table), then datamodel + client codegen staleness guards, gated as a single pass/fail. Tears down + brings up `compose.postgres.yml`, so it interrupts a running stack. Invoke as `uv run --no-sync preflight`. |

`uv run lock-python` (workspace `uv.lock` + per-service `pylock.toml` regeneration, `--check` for staleness) is also on this package's command path, but its entry point and module live in the external [`python-devkit`](https://github.com/outernet-foundation/python-devkit) repo — see its `AGENTS.md` for the group-export redirect config. Must precede `generate-clients`; re-run after every `uv sync --all-packages` (which clobbers per-service locks).

### Cesium asset pipeline

| `uv run` command | Module | Notes |
|---|---|---|
| `build-cesium` | `cesium/build.py` | Build the Cesium 3D Tiles asset bundle. |
| `codegen-cesium` | `cesium/codegen.py` | Codegen for the Cesium pipeline. |
| `combine-cesium` | `cesium/combine.py` | Combine intermediate Cesium assets. |

### CI-only

`build-docker`, `protect-branches`, `publish-compose` live under `placeframe/ci/` and are wired up from `.github/workflows/`. They assume the CI environment (OCI cache registry, restored licenses, GitHub token) and are not intended to be invoked from a developer slot. The operator-facing `build` covers the local-use case. The publish/release commands (`publish-stable`, `create-release`, `ensure-release-pr`, `fetch-ci-artifacts`, `mirror-images`) come from the external [`release-devkit`](https://github.com/outernet-foundation/release-devkit) repo and read `build/publish-config.json`; `mirror-images` populates the org-level ghcr mirror namespace (`ghcr.io/outernet-foundation/mirror/<registry>/<upstream-path>`) with every mirror-prefixed image reference the repo scan finds, via `crane copy`, and runs before every build so a PR can never depend on an unpopulated mirror ref.

### Layout

    build/
      pyproject.toml                                  -- workspace member; declares entry points
      publish-config.json                             -- declarative publish identities (release-devkit reads this)
      src/build_scripts/
        placeframe/
        generate_datamodels.py
        protect_branches.py
          ci/
            preflight.py / build_docker.py            -- import compute_service_shas / run_build from docker-devkit
            publish_compose.py
        cesium/
          build.py / codegen.py / combine.py

    (external) outernet-foundation/docker-devkit    -- up / down / build + detect_gpu / modes / context_sha
    (external) outernet-foundation/ci-devkit       -- ci_step / setup / setup_oras / cache (the runner floor)
    (external) outernet-foundation/unity-devkit    -- license_restore (Cesium pipeline)
    (external) outernet-foundation/python-devkit   -- lock-python + preflight_runner (run_checks from preflight)
    (external) outernet-foundation/openapi-client-codegen  -- downgrade / regenerate_templates / generate_client / generate_projects orchestrator / naming
    (external) outernet-foundation/release-devkit             -- publish-stable / create-release / ensure-release-pr / fetch-ci-artifacts / mirror-images

## Constraints

**Why a separate `build-scripts` package, not part of `scripts/`?** The split is workspace-lifecycle (`build-scripts`) vs. operator utility (`scripts`). They have different dependency surfaces — `build-scripts` pulls in `sqlacodegen`, `datamodel-code-generator` for codegen; `scripts/` pulls in localizer-client, numpy, and the calibration stack. A CI runner that only needs `preflight` doesn't have to sync the calibration dependencies.

**Why `preflight` lives under `placeframe/ci/`, but is operator-facing.** It runs in CI, so it belongs with the CI cohort by ownership. But operators are expected to run it before claiming a change is CI-clean — individual checks (`ruff check` alone, `pytest` alone, `generate-clients` alone) don't catch failures in the others. Listing it in the operator table reflects intent of use, not module location.

## See also

- [`docker-devkit`](https://github.com/outernet-foundation/docker-devkit) — the standalone lifecycle package this one depends on for `compute_service_shas` / `run_build`.
- [`unity-devkit`](https://github.com/outernet-foundation/unity-devkit) — the Unity build toolkit this package depends on for `license_restore`; also home of the Unity entry points and their workflow contract.
- [`ci-devkit`](https://github.com/outernet-foundation/ci-devkit) — the CI runner floor this package depends on for `ci_step`, runner setup, the ORAS cache, and tag primitives.
- [`python-devkit`](https://github.com/outernet-foundation/python-devkit) — the Python repo-lifecycle devkit this package depends on for `lock-python` (workspace lock + per-service pylock exports) and the preflight check runner (`run_checks`).
- [`openapi-client-codegen`](https://github.com/outernet-foundation/openapi-client-codegen) — the OpenAPI client-generation package behind `generate-clients` (config-validated orchestration, spec dump + downgrade, committed-spec skip, patched C# templates, generator invocation, Unity package metadata).
- [`release-devkit`](https://github.com/outernet-foundation/release-devkit) — the publication machinery behind `publish-stable` / `create-release` / `ensure-release-pr` / `fetch-ci-artifacts` / `mirror-images` (tag ledger, path-diff detection, ephemeral version patching, per-registry feed adapters); `build/publish-config.json` is its declarative input.
