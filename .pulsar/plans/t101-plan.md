# T101: Consolidated lock-packages command — Implementation Plan

## Context

Lock file management is fragmented: `uv.lock` is manual, per-service pylock exports have a script but only do the export step, and Unity `packages-lock.json` files have no tooling. There's no CI validation. T101 consolidates all lock management into a single `lock-packages` command with a `--check` flag for CI preflight.

## Files to create/modify

| File | Action |
|------|--------|
| `scripts/src/scripts/lock_packages.py` | **Create** — new typer-based command |
| `scripts/src/scripts/generate_lock_files.py` | **Delete** — superseded |
| `scripts/pyproject.toml` | **Edit** — swap entry point |
| `.github/workflows/build-docker.yml` | **Edit** — add Python preflight step |
| `.github/workflows/build-unity.yml` | **Edit** — add lock check preflight job |
| `CLAUDE.md` | **Edit** — update command table |
| `.pulsar/tickets/ci/t101-lock-packages-command.md` | **Edit** — update status |

## Script design: `lock_packages.py`

### CLI interface (typer)

```
uv run lock-packages [--check] [--python-only] [--unity-only] [--project NAME]
```

- `--check`: validate without writing; exit 1 if any lock is stale
- `--python-only`: skip Unity phase
- `--unity-only`: skip Python phases
- `--project NAME`: limit Unity to one project (enum: Outernet.Client, MapRegistrationTool, AndroidMobile, MakeItSing, Placeframe)

Entry point: `lock-packages = "scripts.lock_packages:app"` (typer pattern per CLAUDE.md convention).

### Structure

```
app = typer.Typer(add_completion=False, pretty_exceptions_show_locals=False)

@app.command()
def lock_packages(check, python_only, unity_only, project):
    stale = False
    if not unity_only:
        stale |= _lock_python(check)
    if not python_only:
        stale |= _lock_unity(check, project)
    if check and stale:
        raise SystemExit(1)
```

### Phase 1 — Python workspace lock

- **Normal mode**: `run_command("uv lock", log=True)`
- **Check mode**: `check_command("uv lock --check")` — instant, no network. If fails, print "uv.lock is stale" and set stale flag.

### Phase 2 — Per-service pylock exports

Reuse discovery logic from current `generate_lock_files.py`: read workspace members from root `pyproject.toml`, filter to members with a Dockerfile, iterate dependency groups (skip `dev`).

- **Normal mode**: `uv export --frozen --output-file <path>` (same as current script), then normalize line endings.
- **Check mode**: `uv export --frozen` (capture stdout), compare with committed file content. No writes. Report any differences.

Comparison normalizes line endings on both sides to avoid false positives.

### Phase 3 — Unity batchmode

Project map (hardcoded, matches the 5 projects in the repo):

| Name | Path |
|------|------|
| Outernet.Client | `legacy/Outernet.Client` |
| MapRegistrationTool | `apps/MapRegistrationTool` |
| AndroidMobile | `apps/AndroidMobile` |
| MakeItSing | `apps/MakeItSing` |
| Placeframe | `packages/unity/Placeframe` |

For each project (or just `--project` if specified):

- **Normal mode**: Run `xvfb-run unity-editor -batchmode -nographics -quit -projectPath <abs_path> -logFile /dev/stdout`. This triggers package resolution, updating `packages-lock.json` in place.
- **Check mode**: Read lock file content before batchmode, run batchmode, read after, compare. If different, restore the original content and report stale. This briefly modifies the working tree but immediately restores it.

Unity batchmode may exit non-zero due to compile errors even though package resolution succeeded. The script checks the lock file diff regardless of exit code, but prints a warning if Unity exited non-zero.

### Reused utilities

- `common.run_command.run_command` — run subprocess, raise on failure (`/placeframe/packages/python/common/src/common/run_command.py`)
- `common.run_command.check_command` — run subprocess, return bool

## CI integration

### Docker CI (`build-docker.yml`)

Add a step early in the `build-and-lock` job (after uv setup, before Docker build):

```yaml
- name: Check Python lock files
  if: github.event_name != 'workflow_dispatch'
  run: uv run lock-packages --check --python-only
```

This is a single step, not a separate job. It's instant (`uv lock --check` + in-memory diffs of pylock exports). Placed after `Setup UV` and before `Set up Docker Buildx`.

### Unity CI (`build-unity.yml`)

Add a new `check-locks` job:

```yaml
check-locks:
  if: github.event_name != 'workflow_dispatch'
  needs: [activate-license]
  runs-on: ubuntu-latest
  container:
    image: unityci/editor:6000.0.66f1-linux-il2cpp-3
  steps:
    - uses: actions/checkout@v5
    - uses: ./.github/actions/setup-job
    - uses: ./.github/actions/restore-unity-license
    - name: Check all lock files
      run: uv run lock-packages --check
```

Update the `build` job's `needs` and `if` to handle the skipped preflight on `workflow_dispatch`:

```yaml
build:
  needs: [activate-license, check-locks]
  if: >-
    !cancelled()
    && needs.activate-license.result == 'success'
    && (needs.check-locks.result == 'success' || needs.check-locks.result == 'skipped')
```

The full check (Python + Unity) runs here because the container already has Unity. Checking all 5 projects sequentially should take ~5-10 minutes (package resolution only, no build).

## CLAUDE.md update

Replace `generate-lock-files` row in the command table:

```
| `uv run lock-packages` | Regenerate all lock files (Python + Unity). `--check` for CI validation. |
```

Remove the `generate-lock-files` row from the Generation Pipeline section and add `lock-packages` there instead.

## Verification

1. `uv run lock-packages --python-only` — should regenerate uv.lock and all pylock files
2. `uv run lock-packages --check --python-only` — should exit 0 (locks just regenerated)
3. Manually edit a pylock file, run `--check --python-only` — should exit 1 with message
4. `uv run lock-packages --unity-only --project Placeframe` — should run Unity batchmode for one project
5. `uv run lock-packages --check --unity-only --project Placeframe` — should exit 0 after regeneration
6. Full `uv run lock-packages` — all phases run
7. Verify old `generate-lock-files` entry point is gone: `uv run generate-lock-files` should fail

Note: Unity validation (steps 4-5) requires Unity to be available. Steps 1-3 can be tested without Unity using `--python-only`.
