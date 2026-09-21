# build/

## What this is

`build/` is a Python workspace member (`build-scripts`) that ships the placeframe-wide CLI commands invoked via `uv run <name>` from the repo root. It owns two cohorts of commands: codegen + workspace tooling (`generate-clients`, `generate-datamodels`, `lock-python`, `deptry-check`, `preflight`) and the Cesium asset pipeline (`build-cesium`, `codegen-cesium`, `combine-cesium`). A third cohort under `placeframe/ci/` exists to be invoked from `.github/workflows/`; those commands are not intended for operator use locally. The Docker-stack lifecycle commands (`up`, `down`, `build`) and their helpers (`detect_gpu`, `modes`, `context_sha`) live in the standalone [`stack-toolkit`](https://github.com/outernet-foundation/stack-toolkit) repo, a PyPI dependency of this package (`stack-toolkit>=0.1.0`); it depends on it for `compute_service_shas` / `run_build` in its CI commands. The Unity build commands (`compile-unity`, `lock-unity`, `test-unity`, `build-unity`, `unity-matrix`, license helpers) live in the standalone [`unity-buildkit`](https://github.com/outernet-foundation/unity-buildkit) repo — see its `AGENTS.md` — which this package depends on for its shared CI helpers (`ci_step`, ORAS cache, runner setup). The OpenAPI client-generation wrapper — spec 3.1→3.0 downgrade, the patched C# templates, the `openapi-generator-cli` invocation, and the Unity package metadata — lives in the standalone [`openapi-client-codegen`](https://github.com/outernet-foundation/openapi-client-codegen) repo; `generate-clients` is a thin orchestrator over it. The publish/release commands (`publish-packages`, `create-release`, `ensure-release-pr`, `fetch-ci-artifacts`, `mirror-images`) live in the standalone [`release-kit`](https://github.com/outernet-foundation/release-kit) repo; this repo declares its package identities, tag prefixes, and registry mappings in `build/publish-config.json`, and the workflows invoke the release-kit entry points uvx-isolated (`uvx --from release-kit==<version> … publish-packages --config build/publish-config.json`). The sibling `scripts/` package holds operator utilities (calibration, debug attach, capture-tool install, ZED Box deploy) — see `scripts/AGENTS.md` for that catalog.

## Shape

### Stack lifecycle (operator-facing)

`up`, `down`, and `build` now live in the external [`stack-toolkit`](https://github.com/outernet-foundation/stack-toolkit) repo — see its `AGENTS.md` for their flags and the native-vs-consumer-stack behavior.

### Codegen + workspace tooling (operator-facing)

Defined in `build/pyproject.toml`'s `[project.scripts]`. All commands accept `--help`.

| `uv run` command | Module | Notes |
|---|---|---|
| `generate-clients` | `placeframe/generate_clients.py` | Thin orchestrator over the [`openapi-client-codegen`](https://github.com/outernet-foundation/openapi-client-codegen) package: per `openapi-projects.json` entry it dumps the Litestar app's spec (with `CODEGEN=1`) and calls the lib to downgrade, generate, and sync each client. C# clients are stamped with the `org.outernet.placeframe.*` npm identity, `0.0.0-local` version, and Unity x-wildcard dependency ranges (identity constants live in `generate_clients.py`). Needs Java 11+ on PATH (the lib runs `openapi-generator-cli`). Writes `packages/generated/python/` and `packages/generated/csharp/`. Pass `--project docker/api` to skip the localizer (whose spec dump needs PyTorch / pycolmap in the venv). |
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

`build-docker`, `protect-branches`, `publish-compose` live under `placeframe/ci/` and are wired up from `.github/workflows/`. They assume the CI environment (OCI cache registry, restored licenses, GitHub token) and are not intended to be invoked from a developer slot. The operator-facing `build` covers the local-use case. The publish/release commands (`publish-packages`, `create-release`, `ensure-release-pr`, `fetch-ci-artifacts`, `mirror-images`) come from the external [`release-kit`](https://github.com/outernet-foundation/release-kit) repo and read `build/publish-config.json`; `mirror-images` populates the org-level ghcr mirror namespace (`ghcr.io/outernet-foundation/mirror/<registry>/<upstream-path>`) with every mirror-prefixed image reference the repo scan finds, via `crane copy`, and runs before every build so a PR can never depend on an unpopulated mirror ref.

### Layout

    build/
      pyproject.toml                                  -- workspace member; declares entry points
      publish-config.json                             -- declarative publish identities (release-kit reads this)
      src/build_scripts/
        placeframe/
          generate_clients.py / generate_datamodels.py / lock_python.py
          deptry_check.py
          protect_branches.py
          ci/
            preflight.py / build_docker.py            -- import compute_service_shas / run_build from stack-toolkit
            publish_compose.py
        cesium/
          build.py / codegen.py / combine.py

    (external) outernet-foundation/stack-toolkit    -- up / down / build + detect_gpu / modes / context_sha
    (external) outernet-foundation/unity-buildkit     -- ci_step / cache / license_restore / setup / setup_oras
    (external) outernet-foundation/openapi-client-codegen  -- downgrade / regenerate_templates / generate_client / naming
    (external) outernet-foundation/release-kit             -- publish-packages / create-release / ensure-release-pr / fetch-ci-artifacts / mirror-images

## Constraints

**Why a separate `build-scripts` package, not part of `scripts/`?** The split is workspace-lifecycle (`build-scripts`) vs. operator utility (`scripts`). They have different dependency surfaces — `build-scripts` pulls in `sqlacodegen`, `datamodel-code-generator` for codegen; `scripts/` pulls in localizer-client, numpy, and the calibration stack. A CI runner that only needs `preflight` doesn't have to sync the calibration dependencies.

**Why `preflight` lives under `placeframe/ci/`, but is operator-facing.** It runs in CI, so it belongs with the CI cohort by ownership. But operators are expected to run it before claiming a change is CI-clean — individual checks (`ruff check` alone, `pytest` alone, `generate-clients` alone) don't catch failures in the others. Listing it in the operator table reflects intent of use, not module location.

## See also

- [`stack-toolkit`](https://github.com/outernet-foundation/stack-toolkit) — the standalone lifecycle package this one depends on for `compute_service_shas` / `run_build`.
- [`unity-buildkit`](https://github.com/outernet-foundation/unity-buildkit) — the Unity build toolkit this package depends on for `ci_step`, the ORAS cache, and runner setup; also home of the Unity entry points and their workflow contract.
- [`openapi-client-codegen`](https://github.com/outernet-foundation/openapi-client-codegen) — the OpenAPI client-generation wrapper `generate-clients` orchestrates (spec downgrade, patched C# templates, generator invocation, Unity package metadata).
- [`release-kit`](https://github.com/outernet-foundation/release-kit) — the publication machinery behind `publish-packages` / `create-release` / `ensure-release-pr` / `fetch-ci-artifacts` / `mirror-images` (tag ledger, path-diff detection, ephemeral version patching, per-registry feed adapters); `build/publish-config.json` is its declarative input.
