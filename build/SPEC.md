# build/SPEC.md

## What this is

`build/` is a Python workspace member (`build-scripts`) that ships the placeframe-wide CLI commands invoked via `uv run <name>` from the repo root. It owns three cohorts of commands: the Docker-stack lifecycle (`up`, `down`, `build`, `generate-clients`, `generate-datamodels`, `lock-python`, `deptry-check`, `preflight`), the Unity-project build/test helpers (`compile-unity`, `lock-unity`, `test-unity`, `activate-unity-license`), and the Cesium asset pipeline (`build-cesium`, `codegen-cesium`, `combine-cesium`). A fourth cohort under `placeframe/ci/` exists to be invoked from `.github/workflows/`; those commands are not intended for operator use locally. The sibling `scripts/` package holds operator utilities (calibration, debug attach, capture-tool install, ZED Box deploy) — see `scripts/SPEC.md` for that catalog.

## Shape

### Stack lifecycle (operator-facing)

Defined in `build/pyproject.toml`'s `[project.scripts]`. All commands accept `--help`.

| `uv run` command | Module | Notes |
|---|---|---|
| `up` | `placeframe/up.py` | `docker compose up`. Auto-detects GPU. Flags: `--attached`/`-a` (foreground instead of detached), `--quiet-pull`/`-q` (pulls verbosely to `.placeframe/logs/up-pull-<utc-timestamp>.log` rather than the console), `--gpu auto\|cuda\|rocm\|none`. |
| `down` | `placeframe/down.py` | `docker compose down`. Flags: `--volumes`/`-v` also removes named volumes — wipes postgres / minio / keycloak / cloudbeaver state, full reset. |
| `build` | `placeframe/build_docker.py` | Builds the docker images for the local stack. Auto-detects CUDA / ROCm. |
| `generate-clients` | `placeframe/generate_clients.py` | Dumps OpenAPI from each Litestar app and runs `openapi-generator-cli` (Java 11+ on PATH). Writes `packages/generated/python/` and `packages/generated/csharp/`. Pass `--project docker/api` to skip the localizer (whose spec dump needs PyTorch / pycolmap in the venv). |
| `generate-datamodels` | `placeframe/generate_datamodels.py` | Runs `sqlacodegen` against live postgres → `packages/generated/python/datamodels/` (SQLAlchemy + Pydantic DTOs). Requires the stack to be up. |
| `lock-python` | `placeframe/lock_python.py` | Regenerates workspace `uv.lock` and per-service `pylock.toml`. Must precede `generate-clients`. Re-run after every `uv sync --all-packages` (which clobbers per-service locks). |
| `deptry-check` | `placeframe/deptry_check.py` | Dependency-vs-imports audit across all workspace packages. |
| `preflight` | `placeframe/ci/preflight.py` | The exact command CI invokes — bundles sync + ruff (check + format) + basedpyright + deptry + pytest + lock-file check + datamodel codegen + client codegen staleness, gated as a single pass/fail. Tears down + brings up `compose.postgres.yml`, so it interrupts a running stack. Invoke as `uv run --no-sync preflight`. |

### Unity (operator-facing)

| `uv run` command | Module | Notes |
|---|---|---|
| `compile-unity` | `placeframe/compile_unity.py` | Local Unity build (APK or platform binary, suitable for `adb install`). Required flags: `--project <name>` and `--build <target>`, matching `build/unity-projects.json`. Streams the editor log, prints output paths under `<project>/Build/`. |
| `lock-unity` | `placeframe/lock_unity.py` | Lock Unity package versions for reproducible builds. |
| `test-unity` | `placeframe/test_unity.py` | Run Unity editmode / playmode tests. |
| `activate-unity-license` | `shared/license.py` | Activate the local Unity Editor license. |

### Cesium asset pipeline

| `uv run` command | Module | Notes |
|---|---|---|
| `build-cesium` | `cesium/build.py` | Build the Cesium 3D Tiles asset bundle. |
| `codegen-cesium` | `cesium/codegen.py` | Codegen for the Cesium pipeline. |
| `combine-cesium` | `cesium/combine.py` | Combine intermediate Cesium assets. |

### CI-only

`build-docker`, `build-unity`, `create-release`, `ensure-release-pr`, `fetch-ci-artifacts`, `inject-unity-env`, `protect-branches`, `publish-packages`, `unity-license-tag`, `unity-matrix` live under `placeframe/ci/` and `shared/` and are wired up from `.github/workflows/`. They assume the CI environment (OCI cache registry, restored licenses, GitHub token) and are not intended to be invoked from a developer slot. Operator-facing equivalents (`build`, `compile-unity`) cover the local-use cases.

### Layout

    build/
      pyproject.toml                                  -- workspace member; declares entry points
      unity-projects.json                             -- project / build target catalog for compile-unity & build-unity
      src/build_scripts/
        placeframe/
          up.py / down.py / build_docker.py          -- stack lifecycle
          generate_clients.py / generate_datamodels.py / lock_python.py
          deptry_check.py
          compile_unity.py / lock_unity.py / test_unity.py
          context_sha.py                              -- per-service tree-hash → image tag
          downgrade_openapi_schema.py                 -- OpenAPI 3.1 → 3.0 fixup used during generate-clients
          protect_branches.py
          ci/
            preflight.py / build_docker.py / build_unity.py
            create_release.py / ensure_release_pr.py / fetch_ci_artifacts.py
            inject_unity_env.py / matrix.py / publish_packages.py
        cesium/
          build.py / codegen.py / combine.py
        shared/
          license.py / license_restore.py             -- Unity license activate / tag-and-store

## Constraints

**Why a separate `build-scripts` package, not part of `scripts/`?** The split is workspace-lifecycle (`build-scripts`) vs. operator utility (`scripts`). They have different dependency surfaces — `build-scripts` pulls in `sqlacodegen`, `datamodel-code-generator`, `pathspec`, `pyyaml` for codegen + image-context-hashing; `scripts/` pulls in localizer-client, numpy, and the calibration stack. A CI runner that only needs `preflight` doesn't have to sync the calibration dependencies.

**Why `--quiet-pull` writes verbose output to a log file rather than dropping it.** Compose's default per-layer progress output floods terminals (the CUDA images alone carry hundreds of layers), making the rest of the `up` lifecycle unreadable. But knowing exactly what crossed the wire is forensically useful — was a slow pull a real cache miss on a base layer, or just sequential manifest re-validation? The split resolves both: one console line per `up` invocation, full per-layer detail at `.placeframe/logs/up-pull-<timestamp>.log`. `tail -f` the file during a slow pull.

**Why `up` does GPU auto-detection.** `detect_gpu()` resolves to `cuda` / `rocm` / `none` based on host devices and selects the matching `compose.<gpu>.yml`. Override with `--gpu` only when reproducing a CI environment locally or testing the CPU-only path; the auto-detect is correct for ~all developer machines.

**Why `preflight` lives under `placeframe/ci/`, but is operator-facing.** It runs in CI, so it belongs with the CI cohort by ownership. But operators are expected to run it before claiming a change is CI-clean — individual checks (`ruff check` alone, `pytest` alone, `generate-clients` alone) don't catch failures in the others. Listing it in the operator table reflects intent of use, not module location.
