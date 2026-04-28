---
id: T7
title: Unity CI workflow
status: in-review
depends_on: [T4]
plan: t7-plan.md
---

# T7: Unity CI workflow

See `ci-background.md` for shared CI context.

## Goal

Automated Unity builds in CI for the full build matrix, running on every push to `main` and `dev` and on PRs targeting those branches.

## Context

Placeframe includes three active Unity projects targeting multiple platforms. All use Unity 6 LTS (6000.0.66f1).

Foundation work is complete:
- **T62** established `uv run build-unity`, direct Unity CDN installation, and serial-based license activation in the COI sandbox.
- **T69** built the Cesium native Linux plugin (committed at `packages/unity/com.cesium.unity/`).
- **T73** fixed `-quit` so batchmode builds exit cleanly.

### Build matrix

| Project | android-mobile | magicleap | linux64 | win64 |
|---|---|---|---|---|
| **Outernet.Client** | yes | yes | yes | T75 |
| **MapRegistrationTool** | - | - | yes | T75 |
| **AndroidMobile** | yes | - | - | - |

5 active builds (win64 disabled pending T75).

## Key files

- `scripts/src/scripts/build_unity.py` — build script (needs platform enum, `-executeMethod` support, Windows)
- `legacy/Outernet.Client/Assets/OuternetClient/Editor/BuildScript.cs` — Android/ML2 configure+build methods
- `apps/AndroidMobile/` — needs a `BuildScript.cs` added (currently has none)
- `.pulsar/coi-placeframe-build.sh` — Unity installation reference
- `.github/workflows/build.yml` — existing Docker build workflow (patterns)
- `packages/generated/csharp/` — generated C# API client consumed by Unity

## Design decisions

1. **GameCI hybrid approach.** Use GameCI's Docker images (`unityci/editor`) for the pre-built Unity environment. Use GameCI's activation action (`game-ci/unity-activate`) for license management. Call `uv run build-unity` for actual build logic (keeps it in Python, portable, tested locally). Don't use `game-ci/unity-builder` — our build script handles the Unity CLI.
2. **License: serial-based activation** via GameCI's activation action, credentials in GitHub Secrets. ULF copy doesn't work with Unity 6 headless (learned in T62).
3. **C# API client: assume committed is current.** Enforces that developers regenerate before pushing. No need to run the API service in Unity CI.
4. **Trigger strategy: pushes to `main` and `dev`, PRs targeting both.** T4 establishes the multi-branch CI pattern.
5. **Platform enum in `build_unity.py`.** The script defines a flat enumeration of platforms: `android-mobile`, `magicleap`, `linux64`, `win64`. The `--platform` parameter is the only input — the script does the right thing for each platform (CLI flags for standalone, `-executeMethod` for Android sub-platforms). No separate `--target` / `--variant` split.
6. **`-executeMethod` for Android sub-platforms.** Android Mobile and Magic Leap 2 are both `BuildTarget.Android` but need different XR loaders, graphics APIs, architectures, texture compression, and scripting defines. The existing C# `BuildScript.cs` methods (`ConfigureForMagicLeap()` + `BuildForMagicLeap()`, etc.) handle this. The Python script calls them via `-executeMethod`. A `BuildScript.cs` must be added to the AndroidMobile app (currently has none).
7. **Standalone builds use `AUTHORING_TOOLS_ENABLED`.** Already set in Outernet.Client's `ProjectSettings.asset` for Standalone. MapRegistrationTool will need the same.
8. **Win64 cross-compiles from Linux.** Uses GameCI's `windows-mono` module on `ubuntu-latest` rather than dedicated Windows runners. Simpler (all 7 builds use the same container approach) but limited to Mono backend. T75 tracks switching to Windows runners for IL2CPP support.
9. **One job per build, fully parallel.** All 7 builds run as separate parallel jobs. Each job restores its Library cache independently. This gives the best wall-clock time and per-build status granularity. Library cache keys are scoped per project (the cache is platform-independent — it's asset import results).

## Approach

Rewrite `build_unity.py` with a full platform enum (`android-mobile`, `magicleap`, `linux64`, `win64`) and an execute-method dispatch table that maps (project, platform) to the fully qualified C# build method. All 7 builds run on Linux using GameCI Docker containers — win64 cross-compiles via the `windows-mono` module (T75 tracks switching to dedicated Windows runners later). License activation uses direct Unity CLI serial activation inside the container, not the `game-ci/unity-activate` action. A new `BuildScript.cs` for AndroidMobile follows the legacy Outernet.Client pattern.

## Depends on

T4 (branch-based builds) — establishes multi-branch triggers and `.env.lock` commit strategy that T7's workflow must follow.

## Done when

**Verifiable now (no special infra):**
- Workflow file `.github/workflows/unity.yml` exists and is syntactically valid
- `build_unity.py` supports the full platform enum (`android-mobile`, `magicleap`, `linux64`, `win64`)
- `BuildScript.cs` exists in AndroidMobile app

**Requires GitHub Actions (verify manually):**
- Full build matrix passes on push to `main`
- License activation works reliably
- Library cache reduces subsequent build times

## CI iteration

Implementation is code-complete. All "verifiable now" criteria pass locally. Remaining work is iterating on the GitHub Actions workflow until all 7 builds pass.

**Iteration loop** (Claude Code has read-only GitHub access, no repo write):
1. User pushes `dev` branch from the host
2. User tells the session "pushed" or pastes the workflow run URL
3. Session checks logs: `gh run list --workflow=unity.yml --limit=1` then `gh run view <id> --log-failed`
4. Session fixes failures, commits to the branch
5. User pushes again, repeat until green

**GitHub setup (already done):**
- Secrets configured: `UNITY_EMAIL`, `UNITY_PASSWORD`, `UNITY_SERIAL`
- Read-only PAT with Actions:read in container via `GITHUB_TOKEN` env var

**Likely first-run failure points:**
- `unity-editor` wrapper path inside GameCI containers (may need `UNITY_EDITOR` env var set in workflow)
- `xvfb-run` availability in GameCI images
- `uv sync` inside container (the workspace `pyproject.toml` may have dependencies not installable in the GameCI image)
- Container image pull — tags verified as `6000.0.66f1-{module}-3` on Docker Hub

**Key files for iteration:**
- `.github/workflows/unity.yml` — workflow definition
- `scripts/src/scripts/build_unity.py` — build logic (UNITY_EDITOR env var, command construction)

## Log

Clean implementation, no issues. The plan mapped directly to the code. One deviation from design decision 8: win64 builds cross-compile from Linux via GameCI's `windows-mono` module instead of using Windows runners (T75 tracks the switch). License activation uses direct Unity CLI (`unity-editor -serial ...`) instead of `game-ci/unity-activate` action (which doesn't work inside container jobs).

GameCI image tags corrected from `ubuntu-6000.0.66f1-{module}-3.1.0` to `6000.0.66f1-{module}-3` after verifying against Docker Hub API.

CI iteration (runs 22644797672–22647576309):
- `UNITY_EDITOR` env var semantics changed from base-directory to direct command path; set to `unity-editor` in workflow
- NuGet restore added via `NuGetForUnity.Cli` dotnet local tool manifest (`.config/dotnet-tools.json` already existed for CSharpier)
- MapRegistrationTool Cesium manifest fixed — was still on registry, not local fork (T69 reopened)
- Unity build noise gitignored (PerformanceTestRunInfo, XR sim settings, native~ dirs)
- AndroidMobile `BuildScript.cs` missing `using UnityEditor.Build` and `using UnityEngine.Rendering` — caught by CI, not locally (no C# static analysis without Unity project open; workon skill updated to include Unity batchmode compilation check)
- Win64 builds fail with "IL2CPP not installed" — expected, GameCI linux containers only have Mono. Win64 matrix entries commented out pending T75.
- Remaining 5 builds (3 android, 1 magicleap, 2 linux64) pending verification on next push.

## Observations

- `scripts/src/scripts/build.py` and `scripts/src/scripts/generate_datamodels.py` have pre-existing formatting violations (`ruff format --check` flags them) — not introduced by this branch.
- Pre-existing lint errors in `packages/generated/python/` (import sorting, unused imports) — auto-generated code, expected.
