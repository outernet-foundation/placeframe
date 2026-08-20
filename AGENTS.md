# Placeframe

This file is placeframe-specific guidance: what the project is and how to operate it.

## What This Project Is

**Placeframe** is a self-hosted XR spatial localization system ("relocalization as a service"). It determines an XR device's position and rotation relative to a canonical reference frame for a physical space — an open-source alternative to Apple Shared World Anchors, Google ARCore Cloud Anchors, etc.

The repo also hosts a Unity app that consumes Placeframe: `apps/CaptureTool/`. It has its own agent doc for app-specific guidance.

## Linear

The `linear` CLI (from the [`linear-cli`](https://github.com/outernet-foundation/linear-cli) repo, installed globally via `uv tool install`) is placeframe's Linear write path; see `AGENTS-SHARED.md` (Trackable work) for the workflow. **Before creating or editing any Linear ticket or project, read [linear-cli's `AGENTS.md`](https://github.com/outernet-foundation/linear-cli/blob/main/AGENTS.md)** — it holds the team/label taxonomy (team PLE; the `repo` and `type` label groups) and the ticket-authoring conventions (declarative outcome-tickets, imperative titles, `blocks`-for-sequence, just-in-time sub-issues, no file lists in tickets).

## Commands

Top-level commands are `uv run <name>` from the repo root. See [`stack-lifecycle`'s `AGENTS.md`](https://github.com/outernet-foundation/stack-lifecycle/blob/main/AGENTS.md) for the stack-lifecycle catalog (`up`, `down`, `build`), `build/AGENTS.md` for the codegen / Cesium catalog (`generate-clients`, `generate-datamodels`, `lock-python`, `deptry-check`, `preflight`, …), and [`unity-buildkit`'s `AGENTS.md`](https://github.com/outernet-foundation/unity-buildkit/blob/main/AGENTS.md) for the Unity catalog (`compile-unity`, `lock-unity`, `test-unity`, …), including per-command flags. See `scripts/AGENTS.md` for operator utilities (`install`, `install-zed`, `fit-calibration`, debug-attach helpers). Every command accepts `--help`.

**Linting and type checking** (from repo root):

```bash
uv run ruff check .          # Lint
uv run ruff format .         # Format
uv run basedpyright          # Type check (strict mode)
```

**Tests**: `uv run pytest` from repo root. Tests live alongside each service (e.g. `docker/localizer/tests/`).

**Full preflight**: `uv run --no-sync preflight` from the repo root. This is the exact command CI invokes — it bundles sync, lint, format check, type check, deptry, pytest, lock-file check, datamodel codegen, and client codegen staleness, all gated as a single pass/fail. Run it before claiming a change is CI-clean; running individual checks (just `ruff check`, just `pytest`, just the codegen check) won't catch failures in the others. Note: preflight tears down and re-brings-up `compose.postgres.yml`, so it interrupts a running stack.

## Server stack

The server stack (API, localizer, reconstructor, Keycloak, MinIO, Postgres, Loki/Alloy/Grafana) is a set of Docker microservices under `docker/`. The reconstructor pulls work via API lease endpoints — there is no separate orchestrator service. See `docker/AGENTS.md` for service inventory, data flow, and authentication model. For debugging — querying Loki, inspecting MinIO buckets, hitting Postgres directly — see the Debugging section in `docker/AGENTS.md` (and `scripts/AGENTS.md` for zed-box SSH access).

## Python Workspace

The repo is a `uv` monorepo. Shared Python code lives in `packages/python/`:

- **`common`** — utilities for boto/MinIO, Docker SDK, Litestar, JWT
- **`core`** — domain logic: camera configs, coordinate transforms, metrics
- **`neural-networks`** — PyTorch models with conditional extras (`cpu`, `cuda`, `rocm`)
- **`datamodels`** — auto-generated Pydantic models from the OpenAPI schema
- **`api-client` / `localizer-client`** — auto-generated async API clients

Auto-generated packages in `packages/generated/` should not be edited directly — regenerate them with the commands above.

**Generation pipeline**: Code in `packages/generated/` is produced by two scripts that must be run after certain changes:

- **`uv run generate-datamodels`** — Introspects the **live PostgreSQL database** (via `sqlacodegen`) to produce `packages/generated/python/datamodels/` (SQLAlchemy table models + Pydantic DTOs). Must be run after any changes to `database/*.sql` schema files. **Requires Docker + postgres to be running**; `uv run up` brings up postgres and applies migrations automatically.
- **`uv run lock-python`** — Regenerates the workspace `uv.lock` and per-service `pylock.toml` files (for services with a `Dockerfile`). Must be run before `generate-clients` (which uses `uv run --no_workspace` per-service and needs the lock files). Also re-run after `uv sync --all-packages` since that overwrites per-service locks.
- **`uv run generate-clients --config build/openapi-projects.json`** — Dumps the OpenAPI spec from each Litestar app and calls the standalone [`openapi-clientgen`](https://github.com/outernet-foundation/openapi-clientgen) package (which runs `openapi-generator-cli` via `uvx`) to produce typed API clients in `packages/generated/python/` and `packages/generated/csharp/`. Must be run after any changes to API route signatures (new query params, new response fields, etc.). Requires Java (JDK 11+) on PATH. The localizer spec dump requires PyTorch/pycolmap in the workspace venv — sync with the appropriate extra first (see "Syncing PyTorch into the workspace venv" below). To skip the localizer and regenerate only the API/zed-capture clients, pass `--project docker/api`.

**When changing both schema and API routes**, run in this order:
1. `uv run generate-datamodels` (updates Pydantic models the API imports; needs live postgres)
2. `uv sync --all-packages` then `uv run lock-python` (sync first if any `pyproject.toml` changed; lock files must precede generate-clients)
3. `uv run generate-clients --config build/openapi-projects.json` (dumps updated OpenAPI spec, generates clients)

All three scripts live in `build/src/build_scripts/placeframe/` — see `build/AGENTS.md` for per-command flag details.

**Codegen commit hygiene**: Regenerated artifacts under `packages/generated/` always live in their own dedicated commit, separate from any source change. The codegen commit's message must be exactly `Run generate-clients`, `Run generate-datamodels`, or `Run generate-clients and generate-datamodels` — no body, no rationale, no reference to the source change or repo state. The reason: codegen output is not reviewed; reviewers must be able to spot and skip these commits at a glance, which only works if they're (a) always separate and (b) always have the same canonical message. A single codegen commit may cover multiple preceding source commits — there is no requirement of a 1:1 source↔codegen pairing. The only constraint is that the codegen commit's contents must reflect the cumulative source state at its position (i.e. running `generate-clients` / `generate-datamodels` against that tree must produce a no-op diff).

## Initial Setup

1. Copy `.env.sample` to `.env` and fill in `PUBLIC_URL` — see `README.md` for ngrok or air-gap LAN setup.
2. Run `uv run up` to start all services.
3. Visit `${PUBLIC_URL}` to access the OpenAPI UI.

## Claude Code Environment Notes

When running in a containerized Claude Code environment (COI sandbox):

1. **Install prerequisites**: `uv` may not be pre-installed. Install with `curl -LsSf https://astral.sh/uv/install.sh | sh` and ensure `~/.local/bin` is on PATH. Java (JDK 11+) is required for `generate-clients` — install with `sudo apt-get install -y default-jre-headless`.
2. **`.env` is pre-configured**: The `.env` file is mounted from the host with real credentials. Do not overwrite it.
3. **Host repos are bind-mounted at `/<project-name>/`**: Every project in the pulsar sandbox config is bind-mounted at `/<project-name>/` inside the container — currently `/placeframe`, `/linear-cli`, `/bashrun`, `/stack-lifecycle`, `/unity-buildkit`, `/infra`, `/make-it-sing`, and `/pulsar` (also aliased at `/workspace`; both are bind mounts of the same host directory). Edits inside these paths are visible on the host live. **Never `git clone` an `outernet-foundation` repo from scratch** — check `/<repo-name>/` first; the mount is where changes belong. Cloning into `/workspace` (or `/pulsar`) instead pollutes the pulsar checkout on the host.
4. **GPU is available**: This environment has GPU passthrough. `uv run up` auto-detects CUDA and includes the GPU compose file. The first run may take several minutes to pull CUDA images (~5GB). **Always use `uv run up --quiet-pull`** — the default pull progress output floods the terminal. Always use `timeout: 600000` (10 minutes) on these Bash calls.
5. **Docker registry auth**: Docker must be authenticated to `ghcr.io` to pull private placeframe images. The COI `agent-shell` script configures this automatically via `GITHUB_TOKEN`. If pulls hang silently, check `~/.docker/config.json` exists and contains `ghcr.io` credentials.
6. **`GITHUB_TOKEN` has read scope only — no `git push`**: The sandbox `GITHUB_TOKEN` authenticates `ghcr.io` pulls and `git clone` from private `outernet-foundation` repos, but `git push` is denied (403 `Permission to ... denied to tylershatch`). SSH is also unavailable — no key is provisioned. When a change to any git-referenced external repo (`bashrun`, `stack-lifecycle`, `unity-buildkit`, `openapi-clientgen`, and future extractions) needs pushing, commit locally at the appropriate `/<project-name>/` bind mount (see item 3) and hand the branch name + HEAD SHA to the operator to push from the host. Do not attempt the push yourself and do not silently work around it.
7. **Migrations run automatically**: `uv run up` starts a `database-migrator` container that has `pg-schema-diff` installed and runs migrations inside Docker. You do NOT need to install `pg-schema-diff` locally — just `uv run up` and wait for the migrator container to finish.
8. **Never run bare `docker compose` commands**: The compose setup requires multiple `--env-file` flags (`.env` + `.env.lock`) and GPU-specific compose files. Always use the `uv run` wrapper scripts (`uv run up`, `uv run down`, etc.) which assemble the correct command. Running `docker compose` directly will fail with missing variable errors.
9. **Generation pipeline in the sandbox**: follow the ordering under "Python Workspace → Generation pipeline" above. Two sandbox specifics: start postgres first with `uv run up --quiet-pull` (it also runs migrations), and pass `--extra cuda` to the `uv sync` step (this host has GPU passthrough) so the localizer OpenAPI spec can be dumped.
10. **Don't `uv sync` inside a service directory**: Running `uv sync` in e.g. `docker/api/` clobbers the workspace venv. Always sync from the repo root with `uv sync --all-packages`, then re-run `uv run lock-python`.
11. **Syncing PyTorch into the workspace venv**: The `neural-networks` package declares `torch`/`torchvision` behind conflicting `cpu`/`cuda`/`rocm` extras (one per accelerator), so a plain `uv sync --all-packages` does not install them. To get PyTorch (and pycolmap, which neural-networks pulls transitively) into the workspace venv — needed for `docker/localizer/tests/`, `dirtorch/test_dir.py`, and `dump_openapi` for the localizer's OpenAPI spec — pass the matching extra: `uv sync --all-packages --extra cuda` (or `cpu` / `rocm`). This Claude Code environment has GPU passthrough, so use `--extra cuda`.
12. **Unity Editor is installed and licensed**: The editor binary is at `/opt/unity/<version>/Editor/Unity`, where `<version>` matches `m_EditorVersion` in each project's `ProjectSettings/ProjectVersion.txt`. License is pre-activated (`~/.local/share/unity3d/Unity/Unity_lic.ulf`). `/opt/unity/slot-env.sh` is auto-sourced by login, interactive, and non-interactive bash shells, so `ANDROID_SDK_ROOT` and the Android `platform-tools` are already on PATH — no manual sourcing needed. To build a Unity project locally (full APK or platform binary, suitable for `adb install` afterward), run `uv run compile-unity --project <ProjectName> --build <BuildTarget>` from the repo root — projects are Unity project directories containing a `unity-build.json` manifest (discovered by scanning from the repo root; the project name is the directory name), and build targets match the manifest's `builds` entries (e.g. `--project CaptureTool --build android-mobile`, `--project MapRegistrationTool --build linux64`). Both flags are required; there is no default. The command preps the project (`dotnet tool restore`, `nugetforunity restore`), runs Unity in batchmode with the project's registered `executeMethod`, streams the log, exits non-zero on failure, and prints the path to each produced APK/EXE under `<project>/Build/`. Use this for "did this `.cs` change compile?" sanity checks (Unity bails fast on `error CS####` before the platform build starts). For a full local deploy prefer `uv run install --build --project <ProjectName>`, which builds then installs in one step and applies the post-install `pm grant` — avoiding the manual `compile-unity` + `adb install -r` + `pm grant` dance (see `apps/CaptureTool`'s agent doc). Never invoke `/opt/unity/.../Unity` directly: `unity_batchmode_command` strips `ADB_SERVER_SOCKET` from the subprocess to prevent Unity's `adb kill-server` teardown from terminating the host adb daemon, and a direct invocation bypasses that guard. The CI-side `uv run build-unity` is a different entry point (cache restore, license restore, OCI registry, version tags) and is not usable from a slot — do not reach for it.
