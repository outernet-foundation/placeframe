# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Is

**Placeframe** is a self-hosted XR spatial localization system ("relocalization as a service"). It determines an XR device's position and rotation relative to a canonical reference frame for a physical space — an open-source alternative to Apple Shared World Anchors, Google ARCore Cloud Anchors, etc.

## Commands

All top-level commands are run via `uv run <command>` from the repo root. These are defined in `scripts/src/scripts/` and registered in `scripts/pyproject.toml`.

| Command | Purpose |
|---|---|
| `uv run up` | Start all Docker services (detached). Pass `--attached` for streaming logs. |
| `uv run down` | Stop all Docker services |
| `uv run build` | Build Docker images (auto-detects CUDA/ROCm) |
| `uv run migrate-database` | Run PostgreSQL schema migrations |
| `uv run generate-clients` | Regenerate OpenAPI client packages |
| `uv run generate-datamodels` | Regenerate Pydantic data models |
| `uv run lock-python` | Regenerate workspace `uv.lock` and per-service `pylock.toml` files |
| `uv run deptry-check` | Check for dependency issues across all packages |

**Linting and type checking** (run from repo root):
```bash
uv run ruff check .          # Lint
uv run ruff format .         # Format
uv run basedpyright          # Type check (strict mode)
```

**Tests**: `uv run pytest` from repo root. Tests live alongside each service (e.g. `docker/localizer/tests/`).

**Full preflight**: `uv run --no-sync preflight` from the repo root. This is the exact command CI invokes — it bundles sync, lint, format check, type check, deptry, pytest, lock-file check, datamodel codegen, and client codegen staleness, all gated as a single pass/fail. Run it before claiming a change is CI-clean; running individual checks (just `ruff check`, just `pytest`, just the codegen check) won't catch failures in the others. Note: preflight tears down and re-brings-up `compose.postgres.yml`, so it interrupts a running stack.

## Architecture

The system runs as a set of Docker microservices defined in `compose.yml`, with GPU overrides in `compose.cuda.yml` and `compose.rocm.yml`.

### Core Services

| Service | Path | Technology | Role |
|---|---|---|---|
| `api` | `docker/api/` | Litestar (ASGI) | Main REST API: manages users, places, captures, maps |
| `localizer` | `docker/localizer/` | Litestar (ASGI) | Runs image-to-map localization (LightGlue feature matching + RANSAC) |
| `reconstructor` | `docker/reconstructor/` | Python + pycolmap | Builds 3D maps from capture sessions |
| `state-sync` | `docker/orchestrator/` | Python worker | Polls the database and orchestrates async jobs between services |
| `database-manager` | `docker/database-manager/` | Python | Runs SQL migrations at startup |
| `auth-initializer` | `docker/auth-initializer/` | Python | Configures Keycloak realm on startup |
| `gateway` | `docker/gateway/` | ngrok | Public HTTPS tunnel |
| `keycloak` | `docker/keycloak/` | Keycloak 26 | OpenID Connect / OAuth2 identity provider |

**Backing services**: PostgreSQL 16, MinIO (S3-compatible object storage), CloudBeaver (database UI).

### Python Workspace

The repo is a `uv` monorepo. Shared Python code lives in `packages/python/`:

- **`common`** — utilities for boto/MinIO, Docker SDK, Litestar, JWT
- **`core`** — domain logic: camera configs, coordinate transforms, metrics
- **`neural-networks`** — PyTorch models with conditional extras (`cpu`, `cuda`, `rocm`)
- **`datamodels`** — auto-generated Pydantic models from the OpenAPI schema
- **`api-client` / `localizer-client`** — auto-generated async API clients

Auto-generated packages in `packages/generated/` should not be edited directly — regenerate them with the commands above.

**Generation pipeline**: Code in `packages/generated/` is produced by two scripts that must be run after certain changes:

- **`uv run generate-datamodels`** — Introspects the **live PostgreSQL database** (via `sqlacodegen`) to produce `packages/generated/python/datamodels/` (SQLAlchemy table models + Pydantic DTOs). Must be run after any changes to `database/*.sql` schema files. **Requires Docker + postgres to be running** (`uv run up`, then `uv run migrate-database` to apply schema changes).
- **`uv run lock-python`** — Regenerates the workspace `uv.lock` and per-service `pylock.toml` files (for services with a `Dockerfile`). Must be run before `generate-clients` (which uses `uv run --no_workspace` per-service and needs the lock files). Also re-run after `uv sync --all-packages` since that overwrites per-service locks.
- **`uv run generate-clients --config openapi-projects.json`** — Dumps the OpenAPI spec from each Litestar app and runs `openapi-generator-cli` (via `uvx`) to produce typed API clients in `packages/generated/python/` and `packages/generated/csharp/`. Must be run after any changes to API route signatures (new query params, new response fields, etc.). Requires Java (JDK 11+) on PATH. Use `--project docker/api` to generate only the API client (the localizer requires PyTorch/pycolmap to dump its spec).

**When changing both schema and API routes**, run in this order:
1. `uv run generate-datamodels` (updates Pydantic models the API imports; needs live postgres)
2. `uv sync --all-packages` then `uv run lock-python` (sync first if any `pyproject.toml` changed; lock files must precede generate-clients)
3. `uv run generate-clients --config openapi-projects.json` (dumps updated OpenAPI spec, generates clients)

All three scripts live in `scripts/src/scripts/`.

**Codegen commit hygiene**: Regenerated artifacts under `packages/generated/` always live in their own dedicated commit, separate from any source change. The codegen commit's message must be exactly `Run generate-clients`, `Run generate-datamodels`, or `Run generate-clients and generate-datamodels` — no body, no rationale, no reference to the source change or repo state. The reason: codegen output is not reviewed; reviewers must be able to spot and skip these commits at a glance, which only works if they're (a) always separate and (b) always have the same canonical message. A single codegen commit may cover multiple preceding source commits — there is no requirement of a 1:1 source↔codegen pairing. The only constraint is that the codegen commit's contents must reflect the cumulative source state at its position (i.e. running `generate-clients` / `generate-datamodels` against that tree must produce a no-op diff).

### Data Flow

1. **Capture**: Unity mobile app (ARFoundation, C#) records images + sensor data and POSTs to the API.
2. **Reconstruction**: The `state-sync` worker triggers the `reconstructor`, which uses pycolmap to build a sparse 3D map (point cloud + camera poses). The result is stored in MinIO.
3. **Localization**: A Unity client sends a query image to the `localizer`, which matches it against a stored map using LightGlue feature matching, then estimates 6-DOF pose via RANSAC/PnP.
4. **Georeferencing**: The Map Registration Tool (Unity standalone) can visually align point clouds against Cesium tilesets (OSM / Google Photorealistic Tiles).

### Authentication

All API endpoints require an OAuth2 Bearer token from Keycloak. The default dev credentials are `user` / `password` (configured in `docker/keycloak/realm-export/placeframe.json`). The `state-sync` worker uses client credentials to authenticate service-to-service calls.

## Code Conventions

- **Python 3.13+**, line length 120, Ruff for linting/formatting, BasedPyright in strict mode.
- **C# (Unity)**: CSharpier formatter, 120 char width (`.csharpierrc.json`).
- All Python packages use `src/<package>/` layout with `py.typed` marker.
- Pydantic v2 for data validation everywhere; async/await throughout all services.
- The `deptry-check` command enforces that all imports match declared dependencies. Per-rule exceptions for platform-specific packages (CUDA/ROCm) are documented in each `pyproject.toml`.
- **No shell scripts.** All scripting is Python. CI workflow steps should be one command (two at most). If there's a condition, a loop, or any real logic, it belongs in a Python script invoked via `uv run`, not inline shell in a workflow YAML.
- **No docstrings.** Do not add docstrings to any function, class, or module — including new files. Comments are allowed only where the logic isn't self-evident.
- **No temporal language in comments.** Don't write "Phase N", "currently", "for now", "until X lands", or other tense markers anchored to a moment. A comment should describe what the code does now; temporary scaffolding gets tracked in a per-initiative plan file, not inline. Comments that survive into a different temporal context become misleading.
- **Comments must be self-contained.** A comment shouldn't require a reader to chase a specific design doc, ticket, or chat history to make sense. "See TDD" / "as discussed in spec" pointers are reference-bait — they imply context but don't deliver it, and orphan when the referenced doc is archived. Inline the full rationale or omit the comment. Cold-reader test: if every external doc were deleted, would this comment still make complete sense?
- **No inline imports.** All imports at module level. No `from x import y` inside functions or methods.
- **Callers before callees.** When one function in a file calls another defined in the same file, the caller's definition appears earlier (closer to the top). Module entry points / public API live near the top; leaf helpers live at the bottom. Among sibling callees called by the same parent, order them by their first call site within that parent's body. A reader scanning the file top-to-bottom encounters the high-level structure first and progressively descends into details.
- **Prefer declarative over imperative.** R3/LINQ operator chains over while loops with multi-predicate exit conditions; joins over dict-mutate-in-foreach; pre-computed view records over inline ternaries in copy lambdas. Reach for imperative only when the declarative version genuinely loses a behavioral guarantee — verify by auditing the code, not by assuming. The default answer to "is the declarative rewrite worth it?" is yes.
- **No lint suppression changes without asking.** Never add, remove, or modify `noqa`, `type: ignore`, file-level lint directives, or any equivalent suppression without explicit user approval.
- **Pin everything.** Never use `:latest` image tags, unpinned package versions, or any mutable version reference. All images use content-addressed SHA tags (e.g. `zed-capture:${ZED_CAPTURE_SHA}`). All base images in `compose.bake.yml` use digest-pinned references. If a SHA tag doesn't exist in the registry yet, surface a clear error — don't fall back to `:latest`.
- **Use `common.bash` for shell calls, not `subprocess`.** All shell-out from Python code goes through `bash()` / `bash_output()` / `bash_check()` / `bash_pipe()` / `bash_handoff()` in `common.bash`. Don't reach for `subprocess.run` / `subprocess.check_output` / `subprocess.Popen` — those bypass the project's logging, error-handling, and shell-operator guards.
- **`bash()` / `bash_output()` reject shell operators.** The `_check_no_pipe` guard in `common.bash` strips quoted strings and rejects any `|` — this catches both pipes (`|`) and logical OR (`||`). Don't use shell fallback patterns like `cmd || echo default`. Instead, use `bash_check()` to test success, then `bash_output()` for the value. `bash_pipe()` is only for actual pipelines (`cmd1 | cmd2`).

## NuGet Packages in Unity Projects

Unity projects use [NuGetForUnity](https://github.com/GlitchEnzo/NuGetForUnity) with `packages.config` files. The NuGetForUnity CLI (`dotnet nugetforunity restore`) only downloads packages already listed — it does **not** resolve transitive dependencies. Dependency resolution only happens through the NuGetForUnity editor UI inside Unity.

**When adding a NuGet package to `packages.config`**, you must also add its transitive dependencies manually. Check the package's **.NET Standard 2.0** dependency list on nuget.org (e.g. `https://www.nuget.org/packages/Serilog/4.0.1`). Skip low-level BCL packages that Unity's runtime already provides (e.g. `System.Buffers`, `System.Memory`, `System.Numerics.Vectors`, `System.Threading.Tasks.Extensions`). Add higher-level transitive deps like `System.Text.Json`, `System.Diagnostics.DiagnosticSource`, etc. When in doubt, check `legacy/Outernet.Client/Assets/packages.config` as a working reference — if the legacy project works without listing a dep, AndroidMobile doesn't need it either. Missing transitive deps won't cause compile errors locally in the editor (NuGetForUnity resolves them there), but they **will** fail in CI where only `restore` runs.

## Docker Build Context

- **`.dockerignore` is an allowlist.** It uses `*` (ignore everything) then `!` entries to whitelist paths Docker can see. This file is the single source of truth for which files affect Docker image builds and for the `CONTEXT_SHA` image tag. Adding a COPY for a path not in the allowlist fails the build loudly (self-correcting). Extra entries cause unnecessary rebuilds (safe failure mode). When adding a new directory that a Dockerfile COPYs, add a `!` entry to `.dockerignore`.
- **BuildKit does not expose which context files a build uses.** Despite computing this internally (`FollowPaths` in the LLB solver), there is no API or CLI to query it ([moby/buildkit#1181](https://github.com/moby/buildkit/issues/1181), open since 2019). This is why we use the `.dockerignore` allowlist approach rather than inferring build inputs from Docker.

## Initial Setup

1. Copy `.env.sample` to `.env` and fill in `PUBLIC_DOMAIN` (ngrok static domain) and `NGROK_AUTHTOKEN`.
2. Run `uv run up` to start all services.
3. Visit your ngrok domain to access the OpenAPI UI.

## Claude Code Environment Notes

When running in a containerized Claude Code environment (COI sandbox):

1. **Install prerequisites**: `uv` may not be pre-installed. Install with `curl -LsSf https://astral.sh/uv/install.sh | sh` and ensure `~/.local/bin` is on PATH. Java (JDK 11+) is required for `generate-clients` — install with `sudo apt-get install -y default-jre-headless`.
2. **`.env` is pre-configured**: The `.env` file is mounted from the host with real credentials (ngrok authtoken, etc.). Do not overwrite it.
3. **GPU is available**: This environment has GPU passthrough. `uv run up` auto-detects CUDA and includes the GPU compose file. The first run may take several minutes to pull CUDA images (~5GB). **Always use `uv run up --quiet-pull`** — the default pull progress output floods the terminal. Always use `timeout: 600000` (10 minutes) on these Bash calls.
4. **Docker registry auth**: Docker must be authenticated to `ghcr.io` to pull private placeframe images. The COI `agent-shell` script configures this automatically via `GITHUB_TOKEN`. If pulls hang silently, check `~/.docker/config.json` exists and contains `ghcr.io` credentials.
5. **Migrations run automatically**: `uv run up` starts a `migrate-database` container that has `pg-schema-diff` installed and runs migrations inside Docker. You do NOT need to install `pg-schema-diff` locally or run `uv run migrate-database` separately — just `uv run up` and wait for the migrator container to finish.
6. **Never run bare `docker compose` commands**: The compose setup requires multiple `--env-file` flags (`.env` + `.env.lock`) and GPU-specific compose files. Always use the `uv run` wrapper scripts (`uv run up`, `uv run down`, etc.) which assemble the correct command. Running `docker compose` directly will fail with missing variable errors.
7. **Full generation pipeline order** (after schema or API route changes):
   - `uv run up --quiet-pull` (starts postgres, runs migrations automatically)
   - `uv run generate-datamodels` (needs live postgres)
   - `uv sync --all-packages` (required if any `pyproject.toml` changed; slow but necessary)
   - `uv run lock-python` (must precede generate-clients)
   - `uv run generate-clients --config openapi-projects.json --project docker/api` (localizer can't dump spec without GPU/PyTorch)
8. **Don't `uv sync` inside a service directory**: Running `uv sync` in e.g. `docker/api/` clobbers the workspace venv. Always sync from the repo root with `uv sync --all-packages`, then re-run `uv run lock-python`.
9. **Tests**: `uv run pytest` from repo root. Collection errors for `docker/localizer/tests/` and `dirtorch/test_dir.py` may occur if PyTorch is not installed in the workspace venv (it's only in the Docker images).
10. **Unity Editor is installed and licensed**: The editor binary is at `/opt/unity/<version>/Editor/Unity`, where `<version>` matches `m_EditorVersion` in `packages/unity/Placeframe/ProjectSettings/ProjectVersion.txt`. License is pre-activated (`~/.local/share/unity3d/Unity/Unity_lic.ulf`). Source `/opt/unity/slot-env.sh` to add Unity's bundled Android SDK to PATH and set `ANDROID_SDK_ROOT`. To verify the Unity project compiles after a C# change, run headlessly:
    ```bash
    /opt/unity/$(awk '/^m_EditorVersion:/{print $2}' packages/unity/Placeframe/ProjectSettings/ProjectVersion.txt)/Editor/Unity \
      -batchmode -nographics -quit \
      -projectPath packages/unity/Placeframe \
      -logFile - 2>&1 | grep -E "error CS|Compilation"
    ```
    Compile errors appear as `error CS####`. Use this whenever you change `.cs` files in `packages/unity/` — `dotnet build` of standalone .NET projects does not catch Unity-side asmdef issues.
