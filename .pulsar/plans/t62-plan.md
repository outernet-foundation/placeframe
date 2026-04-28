# T62: Unity Headless Batch Builds in COI Container

## Context

Claude Code cannot verify that Unity C# code compiles. When editing generated API clients or Placeframe packages, breakage is only discovered when a human opens the project. This adds Unity to the COI container image and provides a `uv run build-unity` command to verify compilation.

All four Unity projects currently use Unity 6000.0.66f1 (changeset `e7adf66625be`). The script reads each project's `ProjectVersion.txt` at runtime, so when the three apps are later downgraded to 2022.3 LTS, only the image needs a second editor install — the command adapts automatically.

## Approach

### Step 1: Extend `.pulsar/coi-placeframe-build.sh`

Add three blocks after the Playwright install:

1. **System dependencies** — xvfb, X11/Mesa libs, IL2CPP toolchain (`build-essential clang lld`). Handle `libasound2` vs `libasound2t64` with `|| true` fallback (Ubuntu version varies by COI base).
2. **Unity Hub** — install via apt (official repo + GPG key).
3. **Editor install** — `xvfb-run unityhub --headless install` for 6000.0.66f1 with modules `android android-sdk-ndk-tools android-open-jdk linux-il2cpp --childModules`. Set install path to `/opt/unity`.

~25 lines of bash.

### Step 2: Modify `scripts/src/scripts/setup_agent_sandbox.py`

After the `UV_PROJECT_ENVIRONMENT` profile line (line 177), add a Unity license section:

- Check if `~/.local/share/unity3d/Unity/Unity_lic.ulf` exists on the host.
- If not found: **fatal error** with a clear message ("Unity license not found at <path>. Activate Unity Personal locally via Unity Hub, then re-run.") and `sys.exit(1)`. The COI image now includes Unity, so a license is required.
- If found: add Incus profile disk device `unity-license` mounting it read-only to `/root/.local/share/unity3d/Unity/Unity_lic.ulf`. Use `check_command` for idempotency (skip if device already exists).

~12 lines of Python.

### Step 3: Create `scripts/src/scripts/build_unity.py`

New Typer command following the `up.py`/`build.py` pattern:

- Constants: `UNITY_PROJECTS` (four `Path` entries), `BUILD_TARGETS` (`["android", "linux64"]`), `UNITY_INSTALL_PATH` (`/opt/unity`), `LICENSE_PATH`.
- `read_editor_version(project_path)` — parse `ProjectSettings/ProjectVersion.txt` for `m_EditorVersion`.
- `find_unity_editor(version)` — resolve `/opt/unity/<version>/Editor/Unity`, error if missing.
- `check_compilation(project_path, target)` — run `xvfb-run Unity -batchmode -nographics -quit -projectPath <path> -buildTarget <target> -logFile /dev/stdout` via `run_command(stream_log=True)`. Catch `CalledProcessError`, return bool.
- `build_unity()` command — options `--project`/`-p` and `--target`/`-t` for filtering. Defaults to all projects × all targets. Early exit if license not found. Print summary table, exit 1 if any fail.

~85 lines of Python.

### Step 4: Register in `scripts/pyproject.toml`

Add `build-unity = "scripts.build_unity:main"` to `[project.scripts]`.

## Key files

| File | Action | Notes |
|---|---|---|
| `.pulsar/coi-placeframe-build.sh` | modify | Add Unity Hub, system deps, editor install |
| `scripts/src/scripts/setup_agent_sandbox.py` | modify | Add `.ulf` profile mount after line 177 |
| `scripts/src/scripts/build_unity.py` | create | `uv run build-unity` command |
| `scripts/pyproject.toml` | modify | Entry point registration |

Existing utilities to reuse:
- `common.run_command.run_command` and `check_command` (`/workspace/packages/python/common/src/common/run_command.py`)
- Typer patterns from `setup_agent_sandbox.py`, `build.py`

## Verification

### Verifiable now (in sandbox)

- `uv run ruff check scripts/src/scripts/build_unity.py`
- `uv run ruff format --check scripts/src/scripts/build_unity.py`
- `uv run basedpyright scripts/src/scripts/build_unity.py`
- `uv run build-unity --help` (registers and prints usage)
- `bash -n .pulsar/coi-placeframe-build.sh` (syntax check)

### Requires manual verification (host rebuild)

- `uv run setup-agent-sandbox --rebuild` installs Unity in the image
- `.ulf` is mounted at `/root/.local/share/unity3d/Unity/Unity_lic.ulf`
- `uv run build-unity` — all four projects pass for both targets
- `uv run build-unity --project AndroidMobile --target android` — single check works

## Known pitfalls

- **Android SDK permissions**: Unity Hub on Linux may install SDK executables without +x. If Android checks fail, add post-install `chmod -R +x` on the SDK directory.
- **`libgconf-2-4`**: deprecated on Ubuntu 24.04. May need to drop from the deps list if the COI base is 24.04+.
- **Disk space**: single editor with Android + IL2CPP is ~8-10 GB. Incus storage pool is 50 GiB, should be fine.
