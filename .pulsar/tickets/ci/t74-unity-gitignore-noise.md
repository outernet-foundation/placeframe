---
id: T74
title: Gitignore rules for Unity batchmode artifacts
status: plan-needed
depends_on: []
---

# T74: Gitignore rules for Unity batchmode artifacts

## Goal

Prevent Unity batchmode runs (`uv run build-unity`) from polluting the working tree with untracked and modified files that create git noise.

## Context

Unity modifies tracked files as a side effect of opening projects — both in batchmode (`uv run build-unity`) and when switching platforms. This creates persistent git noise that must be manually discarded after every build or platform switch. Some of the current dirty files may also be residue from prior tasks (T62, T69) that was never cleaned up properly.

### Two categories of noise

**Untracked files** (can be gitignored):
- `Temp/` directories in project roots
- `native~/` (Cesium build artifacts — `~` suffix means Unity ignores it, but git doesn't)
- Auto-generated `.meta` files for native plugins added outside Unity (e.g. `*.so.meta`)

**Tracked files that Unity re-serializes on open** (cannot be gitignored):
- `ProjectSettings.asset` — Unity tidies its own serialization, removes whitespace, reorders fields
- `packages-lock.json` — Unity resolves package versions, may change hashes
- `.mat` files — Unity upgrades shader references on import
- XR settings `.asset.meta` files — GUID or import setting drift
- Platform-specific settings that change when switching build targets (scripting defines, graphics API, XR loader config)

The second category is the harder problem. These files are tracked because they *must* be — they contain real project configuration. But Unity also touches them as a side effect, producing diffs that have no semantic meaning.

## Approach

Two complementary pieces (may split into separate tickets later):

1. **Improve `.gitignore`** — cover `Temp/`, `native~/`, and any other clearly-untracked noise. Low effort, immediate value.

2. **Post-build cleanup script** — after `uv run build-unity` completes, automatically restore tracked files that Unity dirtied as a side effect. Could be a `--clean` flag on `build_unity.py`, or a separate `uv run` command. Needs a manifest of known-noisy paths per project, or a heuristic (restore all modified files that aren't in a whitelist of expected changes). This is the high-value item — it's what makes `git status` clean after a build.

## Done when

- `uv run build-unity` leaves a clean `git status` (or close to it)
- Solution documented so future sessions know the pattern
