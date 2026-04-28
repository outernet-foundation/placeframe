---
id: T95
title: Cesium for Unity — augment official package with Linux support
status: wont-do
depends_on: [T71]
---

# T95: Cesium for Unity — augment official package with Linux support

## Goal

Publish a `org.outernet.cesium-unity` UPM package that is the official `com.cesium.unity` v1.15.3 release augmented with Linux Editor and Linux Standalone support. Replace the broken single-codegen pipeline from T70.

## Context

T70 built a pipeline using a single Reinterop codegen run (Editor mode) for all platforms. This is architecturally wrong: `Runtime/ConfigureReinterop.cs` has `#if UNITY_EDITOR` blocks that make the Editor codegen hash differ from Standalone/Android. See T70 #14 and its "Single-codegen approach is fundamentally broken" design decision for the full diagnosis.

The official Cesium package ships pre-generated C# with per-platform `#if` guards and native binaries for Windows, macOS, Android, iOS, and UWP — but not Linux. We take it as a base and add Linux on top.

### What we add to the official package

- `Editor/libCesiumForUnityNative-Editor.so` + `.meta` — Linux Editor native (editor-only code: inspectors, scene view helpers)
- `Editor/libCesiumForUnityNative-Runtime.so` + `.meta` — Linux Runtime native loaded inside the Editor (tile engine used in Editor context)
- `Plugins/Standalone/libCesiumForUnityNative-Runtime.so` + `.meta` — Linux Standalone Runtime native (tile engine for built players)
- `#if UNITY_EDITOR_LINUX` C# blocks in `Runtime/generated-linux-editor/` and `Editor/generated-linux-editor/`
- `#if !UNITY_EDITOR && UNITY_STANDALONE_LINUX` C# blocks in `Runtime/generated-linux-standalone/`
- `LinuxStandalone64` added to `CesiumRuntime.asmdef` `includePlatforms`

## Key files

### Workflow and CI (DONE)

- `.github/workflows/build-cesium-native.yml` — main workflow (3 jobs: codegen-editor, codegen-standalone, build-and-publish)
- `.github/workflows/cesium-codegen.yml` — reusable workflow for codegen (called twice with `mode: editor|standalone`)
- `.github/actions/unity-job-setup/action.yml` — composite action (disk cleanup, checkout, Unity license, .NET, ORAS, UV)

### Python scripts (DONE)

- `build/src/build_scripts/clone_cesium_native.py` — clone cesium-unity into empty project structure
- `build/src/build_scripts/codegen_cesium_native.py` — run Reinterop codegen (editor or standalone mode)
- `build/src/build_scripts/build_cesium_native.py` — cmake native build (Editor + Standalone variants)
- `build/src/build_scripts/assemble_cesium_package.py` — assemble package from official tgz + Linux artifacts, generate .meta files
- `build/src/build_scripts/save_cesium_cache.py` — tar + ORAS push of build artifacts
- `build/src/build_scripts/restore_cesium_cache.py` — ORAS pull + extract of build artifacts
- `build/src/build_scripts/patch_cesium_package.py` — rewrite package.json for fork
- `build/src/build_scripts/publish_cesium_package.py` — check if version exists, npm publish

### Other

- `build/src/build_scripts/data/ConfigureNativePlugins.cs` — injected C# for .meta generation
- `legacy/Outernet.Client/Packages/manifest.json` — consumer manifest (update version after publish)
- T70 ticket — historical context, design decisions that still apply

## Approach

### Architecture

Three-job CI workflow. Each job calls one or more Python scripts via `uv run`. ORAS caching wraps expensive steps (codegen, native build) so repeat runs skip them. The two codegen jobs run in parallel in separate Unity containers, eliminating Bee cache and output-path collision issues by construction. The build-and-publish job runs after both complete.

```
codegen-editor ──────┐
                     ├──► build-and-publish
codegen-standalone ──┘
```

All constants are hardcoded: Cesium version `v1.15.3`, Unity version `6000.0.66f1`, cache tag `8`. The npm package version is `${CESIUM_VERSION}-${CACHE_TAG}` (e.g. `1.15.3-8`). To publish a new version, bump `CACHE_TAG` in both workflow files.

### Script responsibilities

**`clone_cesium_native.py`** — Clones cesium-unity at tag v1.15.3 into an empty project structure at `/tmp/cesium-build/CesiumForUnityBuildProject/Packages/com.cesium.unity/`. This mirrors Cesium's own CI approach — they create an empty Unity project and drop the package into `Packages/`, rather than using cesium-unity-samples. No LFS, no sample scripts, no VR script cleanup needed.

**`codegen_cesium_native.py`** — Takes `--mode editor|standalone` (enum-validated by typer). Builds Reinterop.dll, patches CesiumRuntime.asmdef with LinuxStandalone64, appends `-generatedfilesout` to existing csc.rsp files, then runs Unity. Editor mode uses `-quit`, standalone uses `-buildLinux64Player` to compile without `UNITY_EDITOR`. Validates sentinel C++ header and C# output exist. Cache skip logic lives in the workflow (`if: steps.cache.outputs.cache-hit != 'true'`), not in the script.

**`build_cesium_native.py`** — cmake builds for Editor (`-DEDITOR=ON`) and Standalone (`-DEDITOR=OFF`) via a shared `cmake_build()` helper. Writes a vcpkg triplet for Linux x64 static linking. Strips debug symbols. Cache skip logic lives in the workflow.

**`assemble_cesium_package.py`** — Downloads official npm tgz, extracts it, grafts in Linux .so files and `#if`-guarded codegen C#, patches asmdef, removes dev artifacts (Reinterop.dll, ConfigureReinterop.cs, csc.rsp), replaces the cloned source with the assembled package, then runs Unity to generate PluginImporter .meta files for the 3 .so files via an injected ConfigureNativePlugins.cs script. Always runs (not cacheable).

### Cesium's own Build~ tool

Cesium's repo contains a `Build~` C# CLI tool that orchestrates their entire build — codegen for each platform, `#if` guard wrapping, cmake, and package assembly. Linux is in their `SupportedPlatforms` list but they don't build it in CI (Windows/macOS runners only). We can't use `Build~` because it expects Unity Hub + private license server. Our pipeline does the same thing via Python scripts in containerized Unity.

## Design decisions

- **Why two codegen passes are necessary** — `Runtime/ConfigureReinterop.cs` has `#if UNITY_EDITOR` blocks (lines 908-919) that add `SceneView`, `EditorApplication`, `EditorUtility` to the interop function list. Editor codegen produces hash `4378356952313487757` (1513 functions, 379 C++ files). Standalone codegen (without `UNITY_EDITOR`) produces hash `7031067308632330464` (1487 functions, 371 C++ files). 26 extra functions in Editor mode. Each native binary must be built from its own platform's C++ headers, and the pre-generated C# `#if` blocks must contain the matching hash. Single codegen cannot work. **Validated locally 2026-03-10.**
- **Why a player build is needed for Standalone codegen** — When Unity runs in batchmode (even with `-buildTarget StandaloneLinux64`), the initial script compilation always has `UNITY_EDITOR` defined because the Editor is running. Switching the build target does NOT remove `UNITY_EDITOR` from the compilation. The only way to compile C# without `UNITY_EDITOR` is to trigger an actual player build via `BuildPipeline.BuildPlayer()`, which recompiles runtime assemblies for the target platform with different defines.
- **Standalone codegen trigger: `-buildLinux64Player` wins** — Validated locally. `-buildLinux64Player /tmp/throwaway` triggers a player build that compiles CesiumRuntime without `UNITY_EDITOR`, producing Standalone C++ headers (371 files) and C# (30 files) with hash `7031067308632330464` / 1487 functions. The cmake callback (`OnPostBuildPlayerScriptDLLs`) fires and fails harmlessly (cmake not installed) — codegen output is already on disk. Exit code is still 0. No injected script needed.
- **Split codegen into separate jobs to avoid Bee cache and output-path issues** — Running both passes in one job requires clearing `~/.cache/unity3d/bee/` between passes (Bee caches compilation, preventing Reinterop from re-running) and using separate `-generatedfilesout` paths per assembly (Reinterop generates identically-named files like `ReinteropInitializer.cs` that collide). Separate jobs eliminate both problems by construction — each job gets a clean runner.
- **Empty project instead of cesium-unity-samples** — Cesium's own CI creates an empty Unity project and drops the package into `Packages/`. We do the same. This avoids cloning a large samples repo, avoids LFS objects, and eliminates the need to remove VR sample scripts that reference XR Interaction Toolkit types not present in our Unity version.
- **cesium-unity must be cloned from source, not extracted from npm tgz** — The npm tgz may have auto-generated `.meta` files with wrong GUIDs. The source repo has the correct GUIDs (e.g. `CesiumRuntime.asmdef.meta` GUID `63cab5ddbd23cf34ca160a9b3d74438d`). CesiumEditor.asmdef references CesiumRuntime by this GUID — wrong GUIDs cause the Editor assembly to fail with CS0246 errors for all Runtime types.
- **Separate build and assembly scripts** — `build_cesium_native.py` (cmake) is cacheable and skipped on cache hit via workflow `if:`. `assemble_cesium_package.py` (tgz assembly + .meta generation) always runs. Splitting them allows the workflow to skip the expensive cmake build without conditional logic inside the script.

## Done when

- [x] Codegen runs two passes (Editor + Standalone), capturing generated C# via `-generatedfilesout` — validated 2026-03-10
- [x] Standalone codegen triggers a player build to compile without `UNITY_EDITOR` — `-buildLinux64Player` validated 2026-03-10
- [x] CI workflow and reusable codegen workflow written
- [x] Composite action for shared job preamble written
- [x] Cache save/restore, patch, and publish Python scripts written
- [x] `clone_cesium_native.py` implemented
- [x] `codegen_cesium_native.py` implemented
- [x] `build_cesium_native.py` implemented
- [x] `assemble_cesium_package.py` implemented
- [ ] All 3 CI jobs pass (codegen-editor, codegen-standalone, build-and-publish)
- [ ] Android device verified: no `NotImplementedException: The native library is out of sync`
- [ ] Linux Standalone player verified: no Reinterop hash mismatch at runtime
