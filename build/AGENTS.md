# build/

## What this is

`build/` is a Python workspace member (`build-scripts`) that ships the placeframe-wide CLI commands invoked via `uv run <name>` from the repo root. It owns two cohorts of commands: codegen + workspace tooling (`generate-clients`, `generate-datamodels`, `lock-python`, `deptry-check`, `preflight`) and the Cesium asset pipeline (`build-cesium`, `codegen-cesium`, `combine-cesium`). A third cohort under `placeframe/ci/` exists to be invoked from `.github/workflows/`; those commands are not intended for operator use locally. The Docker-stack lifecycle commands (`up`, `down`, `build`) and their helpers (`detect_gpu`, `modes`, `context_sha`) live in the standalone `placeframe-stack` package — see `packages/python/placeframe-stack/AGENTS.md` — which this package depends on for `compute_service_shas` / `run_build` in its CI commands. The Unity build commands (`compile-unity`, `lock-unity`, `test-unity`, `build-unity`, `unity-matrix`, license helpers) live in the standalone `placeframe-unity` package — see `packages/python/placeframe-unity/AGENTS.md` — which this package depends on for its shared CI helpers (`ci_step`, ORAS cache, runner setup). The sibling `scripts/` package holds operator utilities (calibration, debug attach, capture-tool install, ZED Box deploy) — see `scripts/AGENTS.md` for that catalog.

## Shape

### Stack lifecycle (operator-facing)

`up`, `down`, and `build` now live in the `placeframe-stack` package — see `packages/python/placeframe-stack/AGENTS.md` for their flags and the native-vs-consumer-stack behavior.

### Codegen + workspace tooling (operator-facing)

Defined in `build/pyproject.toml`'s `[project.scripts]`. All commands accept `--help`.

| `uv run` command | Module | Notes |
|---|---|---|
| `generate-clients` | `placeframe/generate_clients.py` | Dumps OpenAPI from each Litestar app and runs `openapi-generator-cli` (Java 11+ on PATH). Writes `packages/generated/python/` and `packages/generated/csharp/`. Pass `--project docker/api` to skip the localizer (whose spec dump needs PyTorch / pycolmap in the venv). |
| `generate-datamodels` | `placeframe/generate_datamodels.py` | Runs `sqlacodegen` against live postgres → `packages/generated/python/datamodels/` (SQLAlchemy + Pydantic DTOs). Requires the stack to be up. |
| `lock-python` | `placeframe/lock_python.py` | Regenerates workspace `uv.lock` and per-service `pylock.toml`. Must precede `generate-clients`. Re-run after every `uv sync --all-packages` (which clobbers per-service locks). |
| `deptry-check` | `placeframe/deptry_check.py` | Dependency-vs-imports audit across all workspace packages. |
| `preflight` | `placeframe/ci/preflight.py` | The exact command CI invokes — bundles sync + ruff (check + format) + basedpyright + deptry + pytest + lock-file check + datamodel codegen + client codegen staleness, gated as a single pass/fail. Tears down + brings up `compose.postgres.yml`, so it interrupts a running stack. Invoke as `uv run --no-sync preflight`. |

### Cesium asset pipeline

| `uv run` command | Module | Notes |
|---|---|---|
| `build-cesium` | `cesium/build.py` | Build the Cesium 3D Tiles asset bundle. |
| `codegen-cesium` | `cesium/codegen.py` | Codegen for the Cesium pipeline. |
| `combine-cesium` | `cesium/combine.py` | Combine intermediate Cesium assets. |

### CI-only

`build-docker`, `create-release`, `ensure-release-pr`, `fetch-ci-artifacts`, `protect-branches`, `publish-packages` live under `placeframe/ci/` and are wired up from `.github/workflows/`. They assume the CI environment (OCI cache registry, restored licenses, GitHub token) and are not intended to be invoked from a developer slot. The operator-facing `build` covers the local-use case.

### Layout

    build/
      pyproject.toml                                  -- workspace member; declares entry points
      src/build_scripts/
        placeframe/
          generate_clients.py / generate_datamodels.py / lock_python.py
          deptry_check.py
          downgrade_openapi_schema.py                 -- OpenAPI 3.1 → 3.0 fixup used during generate-clients
          protect_branches.py
          ci/
            preflight.py / build_docker.py            -- import compute_service_shas / run_build from placeframe-stack
            create_release.py / ensure_release_pr.py / fetch_ci_artifacts.py
            publish_packages.py / git_tags.py         -- release tagging (name → tag-prefix map)
        cesium/
          build.py / codegen.py / combine.py

    packages/python/placeframe-stack/                 -- up / down / build + detect_gpu / modes / context_sha

## Constraints

**Why a separate `build-scripts` package, not part of `scripts/`?** The split is workspace-lifecycle (`build-scripts`) vs. operator utility (`scripts`). They have different dependency surfaces — `build-scripts` pulls in `sqlacodegen`, `datamodel-code-generator` for codegen; `scripts/` pulls in localizer-client, numpy, and the calibration stack. A CI runner that only needs `preflight` doesn't have to sync the calibration dependencies.

**Why `preflight` lives under `placeframe/ci/`, but is operator-facing.** It runs in CI, so it belongs with the CI cohort by ownership. But operators are expected to run it before claiming a change is CI-clean — individual checks (`ruff check` alone, `pytest` alone, `generate-clients` alone) don't catch failures in the others. Listing it in the operator table reflects intent of use, not module location.

## See also

- `packages/python/placeframe-stack/AGENTS.md` — the stack-lifecycle (`up`/`down`/`build`) package this one depends on for `compute_service_shas` / `run_build`.
- `packages/python/placeframe-unity/AGENTS.md` — the Unity build toolkit this package depends on for `ci_step`, the ORAS cache, and runner setup; also home of the Unity entry points and their workflow contract.
