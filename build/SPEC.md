# build/SPEC.md

## What this is

`build/` is a Python workspace member (`build-scripts`) that ships the placeframe-wide CLI commands invoked via `uv run <name>` from the repo root. It owns two cohorts of commands: the Docker-stack lifecycle (`up`, `down`, `build`, `generate-clients`, `generate-datamodels`, `lock-python`, `deptry-check`, `preflight`) and the Cesium asset pipeline (`build-cesium`, `codegen-cesium`, `combine-cesium`). A third cohort under `placeframe/ci/` exists to be invoked from `.github/workflows/`; those commands are not intended for operator use locally. The Unity build commands (`compile-unity`, `lock-unity`, `test-unity`, `build-unity`, `unity-matrix`, license helpers) live in the standalone `placeframe-unity` package — see `packages/python/placeframe-unity/SPEC.md` — which this package depends on for its shared CI helpers (`ci_step`, ORAS cache, runner setup). The sibling `scripts/` package holds operator utilities (calibration, debug attach, capture-tool install, ZED Box deploy) — see `scripts/SPEC.md` for that catalog.

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
          up.py / down.py / build_docker.py          -- stack lifecycle
          generate_clients.py / generate_datamodels.py / lock_python.py
          deptry_check.py
          context_sha.py                              -- per-service tree-hash → image tag
          downgrade_openapi_schema.py                 -- OpenAPI 3.1 → 3.0 fixup used during generate-clients
          protect_branches.py
          ci/
            preflight.py / build_docker.py
            create_release.py / ensure_release_pr.py / fetch_ci_artifacts.py
            publish_packages.py / git_tags.py         -- release tagging (name → tag-prefix map)
        cesium/
          build.py / codegen.py / combine.py

## Constraints

**Why a separate `build-scripts` package, not part of `scripts/`?** The split is workspace-lifecycle (`build-scripts`) vs. operator utility (`scripts`). They have different dependency surfaces — `build-scripts` pulls in `sqlacodegen`, `datamodel-code-generator`, `pathspec`, `pyyaml` for codegen + image-context-hashing; `scripts/` pulls in localizer-client, numpy, and the calibration stack. A CI runner that only needs `preflight` doesn't have to sync the calibration dependencies.

**Why `--quiet-pull` writes verbose output to a log file rather than dropping it.** Compose's default per-layer progress output floods terminals (the CUDA images alone carry hundreds of layers), making the rest of the `up` lifecycle unreadable. But knowing exactly what crossed the wire is forensically useful — was a slow pull a real cache miss on a base layer, or just sequential manifest re-validation? The split resolves both: one console line per `up` invocation, full per-layer detail at `.placeframe/logs/up-pull-<timestamp>.log`. `tail -f` the file during a slow pull.

**Why `up` does GPU auto-detection.** `detect_gpu()` resolves to `cuda` / `rocm` / `none` based on host devices and selects the matching `compose.<gpu>.yml`. Override with `--gpu` only when reproducing a CI environment locally or testing the CPU-only path; the auto-detect is correct for ~all developer machines.

**Why `preflight` lives under `placeframe/ci/`, but is operator-facing.** It runs in CI, so it belongs with the CI cohort by ownership. But operators are expected to run it before claiming a change is CI-clean — individual checks (`ruff check` alone, `pytest` alone, `generate-clients` alone) don't catch failures in the others. Listing it in the operator table reflects intent of use, not module location.

**`build` emits two env files, partitioning image references by who builds the image.** `.env.lock` (committed) carries third-party and base-image digests — images placeframe *pulls*. `.env.shas` (gitignored) carries the `tree-<hash>` tags of images placeframe *builds* from its own Dockerfiles, where the hash is a `git write-tree` over the `.dockerignore`-allowlisted context (`context_sha.py`). The split is mandated by a CI invariant — `.env.lock` must never contain built-image digests — and by churn: `.env.shas` changes on every source edit, so it stays out of version control. `uv run up` injects the `${*_SHA}` values into the environment directly and reads neither file; `.env.shas` exists so a consumer running placeframe's compose files through raw `docker compose` (without the `uv run up` wrapper) can resolve those holes via `--env-file .env.shas`.

## See also

- `packages/python/placeframe-unity/SPEC.md` — the Unity build toolkit this package depends on for `ci_step`, the ORAS cache, and runner setup; also home of the Unity entry points and their workflow contract.
