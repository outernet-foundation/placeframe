---
id: T70
title: Cesium native CI — build Linux + Android from source, publish to UPM registry
status: done
depends_on: [T69, T71]
---

# T70: Cesium native CI — build Linux + Android from source, publish to UPM registry

## Goal

Build the Cesium for Unity native plugin for all platforms we target (Linux, Android) from source in CI and publish as a multi-platform UPM package to the scoped registry. Remove the committed binary from the repo.

## Context

T69 commits a manually-built forked `com.cesium.unity` package with Linux-only binaries directly to the repo as a temporary measure. This ticket replaces that with an automated build that publishes to the same scoped registry set up in T71 (npmjs.org with OIDC trusted publishing).

The upstream Cesium for Unity package (`com.cesium.unity`) ships pre-generated C# (with per-platform `#if` guards) and native binaries for Windows, macOS, Android, and iOS — but not Linux. Our fork exists to add Linux support. ~~We also build Android from source to guarantee hash consistency from a single codegen run~~ — this approach was wrong; each platform needs its own codegen run (see design decisions). The correct approach is to borrow the official package's non-Linux artifacts and only build Linux ourselves.

## Key files

- `scripts/src/scripts/build_cesium_native.py` — build script (phases: clone, codegen, native-linux, native-android, list-cache-files)
- `.github/workflows/build-cesium-native.yml` — CI workflow
- `.github/actions/setup-cesium-build/action.yml` — composite action (ORAS, ghcr login, UV, clone)
- `apps/MapRegistrationTool/Packages/manifest.json` — consumer manifest
- `legacy/Outernet.Client/Packages/manifest.json` — consumer manifest (`org.outernet.cesium-unity: 1.15.3-7`)

### Upstream Cesium files (analyzed from `github.com/CesiumGS/cesium-unity` v1.15.3)

- `Build~/Package.cs` — the build orchestrator. Runs Unity per-platform, captures generated C# via `-generatedfilesout`, wraps in `#if` guards, builds native via cmake, strips build machinery from published package.
- `Build~/Package.cs:AddGeneratedFiles()` (line 314) — wraps generated C# in `#if <condition> ... #endif` and appends to output files. Conditions: `UNITY_EDITOR_WIN`, `!UNITY_EDITOR && UNITY_ANDROID`, `!UNITY_EDITOR && UNITY_STANDALONE_WIN`, etc.
- `Build~/Package.cs:CopyPackageContents()` (line 374) — copies package files but **deletes** `ConfigureReinterop.cs`, `csc.rsp`, and build scripts from the published package. `Reinterop.dll` is not in the copy list so also excluded.
- `Runtime/ConfigureReinterop.cs` — contains `[Reinterop]`-annotated `ExposeToCPP()` method. Lines 28-40: `CppOutputPath` varies per platform (`generated-Editor`, `generated-Android`, `generated-Standalone`, etc.). Lines 908-919: `#if UNITY_EDITOR` block adds `SceneView`, `EditorApplication`, `EditorUtility` — this is what causes the hash to differ between Editor and non-Editor platforms.
- `Editor/ConfigureReinterop.cs` — separate `[Reinterop]` config for the Editor assembly (separate hash, separate native library).
- `.github/workflows/build.yml` — upstream CI. Windows job builds Win64+UWP+Android. macOS job builds macOS+iOS. Combine job merges via overlay + C# concatenation.
- `native~/Runtime/.gitignore` — excludes `generated/` and `generated-*/` — generated C++ is never committed.

## Done when

- [x] Build script converted from shell to Python (`uv run build-cesium-native`)
- [x] CI workflow builds CesiumForUnityNative for Linux from source
- [x] CI workflow builds CesiumForUnityNative for Android from source (cross-compile via Android NDK)
- [x] ~~All native binaries built from the same Reinterop codegen run (single hash across all platforms)~~ — **invalidated**: see "Single-codegen approach is fundamentally broken" below. Each platform needs its own codegen.
- [x] Combined package published to npmjs.org under `org.outernet` scope via OIDC trusted publishing
- [x] Consumer manifests point at registry instead of `file:` path
- [x] Committed binary (`packages/unity/com.cesium.unity/`) removed from repo
- [x] Rebuild triggers documented (manual or on Cesium version bump)
- [ ] Android device verified: no `NotImplementedException: The native library is out of sync` — **FAILED**: see #14 below
- [ ] Linux Standalone player verified: no Reinterop hash mismatch at runtime (same root cause as Android, untested)

## Approach

**Current approach (1.15.3-7, broken):** Build all target platform native binaries from source using a single Reinterop codegen run (Editor mode), assuming one consistent hash across all platforms. This is fundamentally wrong — see "Single-codegen approach is fundamentally broken" in design decisions.

**Proposed new approach:** Adopt the same architecture as upstream Cesium: per-platform codegen producing pre-generated C# files with `#if` guards, per-platform native binaries, no source generator in the published package. For non-Linux platforms, borrow the official package's pre-generated C# and native binaries. For Linux (Editor + Standalone), run our own per-platform codegen and native builds.

**Current CI architecture (to be replaced):**

1. **Codegen job** — runs in `unityci/editor:6000.0.66f1` container (matches our app Unity version). Clones repos, runs Reinterop, caches codegen output via ORAS. Unity serial license activation.
2. **Linux native job** — ubuntu-22.04 runner, no Unity. Pulls codegen cache, builds Editor + Standalone `.so` via cmake/g++. Runs in parallel with Android job.
3. **Android native job** — bare ubuntu runner, no Unity. Pulls codegen cache, cross-compiles `libCesiumForUnityNative-Runtime.so` for `arm64-v8a` via cmake + Android NDK (uses runner's pre-installed NDK). Runs in parallel with Linux job.
4. **Package + publish job** — runs in `unityci/editor` container. Collects all native binaries, places them in the package directory, runs Unity batchmode to import them (generating correct `.meta` files via `PluginImporter`), assembles UPM package, publishes to npmjs.org via OIDC trusted publishing.

Windows native binaries require MSVC and cannot be cross-compiled from Linux — deferred to T75.

## Design decisions

- Package renamed from `com.cesium.unity` to `org.outernet.cesium-unity` to fit the `org.outernet` scoped registry
- Separate workflow from `publish-upm.yml` — fundamentally different job (30-60 min cmake build vs quick npm publish)
- `workflow_dispatch` only (manual trigger) — Cesium version bumps are rare
- vcpkg/cmake caching via ORAS/GHCR to avoid 30-60 min rebuilds
- `GIT_LFS_SKIP_SMUDGE=1` required in CI — `unityci/editor` has git-lfs installed, which breaks vcpkg's KTX port (LFS smudge filter fails in temp clone). COI sandbox lacks git-lfs so it works locally.
- Apache-2.0 redistribution: fork is compliant as long as LICENSE is included in published package and package name doesn't imply official Cesium endorsement
- Codegen output cache replaces Unity Library cache — the Library cache caused Reinterop to never fire on warm runs (Unity skipped recompilation, so code generation never ran). Caching just the outputs (Reinterop.dll + generated C++ headers) lets phase_codegen skip Unity entirely via idempotency checks, which is both faster and correct.
- Windows excluded — T75 blocks win64 builds (no Windows runner yet). T75 updated to include building Windows Cesium native binaries once a runner is available.
- **Reinterop sync mechanism** — Reinterop (Cesium's C#↔native interop layer) embeds a sync check: an MD5 hash of all interop function signatures (name + type), truncated to 64-bit. Both the generated C# and C++ contain hardcoded hash + function count literals. If the C# doesn't match the native library, the app throws `NotImplementedException: The native library is out of sync with the managed one` at `ReinteropInitializer..cctor`. Cache keys include `UNITY_VERSION` to prevent stale codegen across version changes.
- **~~Reinterop hash mismatch: repackaging official binaries is not viable~~ — MISDIAGNOSIS, SUPERSEDED** — The original analysis was: run Reinterop ourselves to generate C# + C++ code, build Linux native `.so`, then download the official Cesium release and copy in their pre-built Android/Windows binaries. This fails because even after matching the exact Unity version (2022.3.41f1), the hashes still differ — "something about running Reinterop on Linux vs Windows/Mac produces different output." **This diagnosis was wrong.** The actual cause was the `#if UNITY_EDITOR` block in `Runtime/ConfigureReinterop.cs` (see next decision). Our codegen ran in Editor mode (hash Y, 1513 functions), and we compared that against official Android native binaries which were compiled from Android codegen (hash X, fewer functions). The mismatch was Editor-vs-Android, not Linux-vs-Windows. Reinterop output is deterministic for a given set of platform defines. The repackaging approach is viable — see "Single-codegen approach is fundamentally broken" below.
- **Single-codegen approach is fundamentally broken** — The entire premise of T70 — "build all platform native binaries from a single Reinterop codegen run, ensuring a consistent hash across all platforms" — is wrong. **Each target platform produces a different Reinterop hash because the `ExposeToCPP` method in `Runtime/ConfigureReinterop.cs` contains `#if UNITY_EDITOR` blocks** (lines 908-919) that add `SceneView`, `EditorApplication`, and `EditorUtility` to the interop function list. When compiled in Editor mode: 1513 functions, hash `4378356952313487757`. When compiled for Android (`UNITY_ANDROID`, no `UNITY_EDITOR`): fewer functions, different hash. The `CppOutputPath` constant also varies per platform via `#if` (`generated-Editor`, `generated-Android`, `generated-Standalone`, etc.), confirming upstream expects separate codegen per platform. Our pipeline runs codegen once in Editor mode and builds ALL native binaries (Editor, Standalone, Android) from that single `generated-Editor` output. This means ALL non-Editor native binaries have the Editor hash, but at runtime the C# source generator produces the platform-specific hash → mismatch. **This affects both Android AND Linux Standalone** (untested but same root cause). Only Linux Editor works because that's the one context where our codegen matches.
- **How upstream Cesium actually builds and packages (analysis of `Build~/Package.cs` and `build.yml`)** — Cesium's CI is fundamentally different from what we assumed:
  1. **Two platform CI jobs**: Windows (builds Win64, UWP, Android native + codegen) and macOS (builds macOS, iOS native + codegen). Each job runs `dotnet run --project Build~`.
  2. **`Build~` runs Unity compilation separately for each target platform**: Editor (`CompileForEditorAndExit`), then each player platform via `-buildTarget <platform> -executeMethod CompileFor<Platform>AndExit`. Each Unity invocation triggers Reinterop codegen with the correct platform defines.
  3. **Generated C# is captured to disk** via `-generatedfilesout` in `csc.rsp`, then **wrapped in per-platform `#if` guards** and **concatenated** into files in `Runtime/generated/` and `Editor/generated/`. Example: Android codegen gets `#if !UNITY_EDITOR && UNITY_ANDROID ... #endif`, Windows Editor gets `#if UNITY_EDITOR_WIN ... #endif`.
  4. **Generated C++ is written to platform-specific directories**: `native~/Runtime/generated-Editor/`, `native~/Runtime/generated-Android/`, `native~/Runtime/generated-Standalone/`, etc. Each platform's native library is built from its own generated C++.
  5. **A Combine job** merges the Windows and macOS package artifacts by overlaying files and concatenating generated C# (appending with `#if` guards).
  6. **The published package strips the build machinery**: `ConfigureReinterop.cs` (both Editor and Runtime), `csc.rsp`, `Reinterop.dll`, `CompileCesiumForUnityNative.cs`, `BuildCesiumForUnity.cs` are all **deleted** from the published package. The package ships NO source generator and NO codegen configuration.
  7. **The published package contains**: pre-generated C# files with per-platform `#if` guards (in `Runtime/generated/` and `Editor/generated/`), pre-built native binaries per platform (in `Plugins/` and `Editor/`), and the Cesium C# source code (minus build infrastructure). At compile time in the consuming project, the `#if` guards select the correct platform variant — no Reinterop runs.
  8. **Our fork does the opposite**: ships `Reinterop.dll` (source generator) + `ConfigureReinterop.cs` + `csc.rsp`, expects Reinterop to run at compile time in the consumer. This is why the hash mismatch occurs — the source generator produces a hash based on the consumer's compilation context (platform defines), but all native binaries were built from a single Editor-mode codegen.
- **Repackaging official binaries IS viable (revised)** — Since the hash mismatch was caused by Editor-vs-platform defines (not Linux-vs-Windows non-determinism), we can borrow the official package's pre-generated C# and native binaries for non-Linux platforms. The official Android `.so` has hash X (Android codegen). The official package's pre-generated C# for Android (wrapped in `#if !UNITY_EDITOR && UNITY_ANDROID`) also has hash X. They match. We only need to build Linux (Editor + Standalone) ourselves and add our generated C# with appropriate `#if` guards (`UNITY_EDITOR_LINUX` for Editor, `!UNITY_EDITOR && UNITY_STANDALONE_LINUX` for Standalone). The official Cesium package works across Unity versions (millions of users), so Reinterop output is stable across Roslyn versions for a given set of platform defines.
- **Unity version matches our apps, not Cesium's CI** — ~~The repackaging approach required matching Cesium's Unity version.~~ No longer relevant if we adopt the pre-generated C# approach. The pre-generated C# is platform-guarded and doesn't depend on the consumer's Unity version. Use 6000.0.66f1 for our Linux codegen.
- **Fan-out CI for disk space and parallelism** — Free GitHub runners have ~20 GB usable disk. A single job building codegen + linux native + android native (with NDK) risks exceeding that. Splitting into parallel jobs gives each job a fresh ~40 GB (after cleanup) and cuts wall clock time. The codegen ORAS cache makes artifact transfer between jobs nearly free.
- **Android cross-compilation uses cmake directly** — Cesium's CI triggers cmake from inside Unity's build pipeline (via `IPostBuildPlayerScriptDLLs` hook), but the cmake invocation itself is standalone. We call cmake directly with the same flags: `-DCMAKE_TOOLCHAIN_FILE=extern/android-toolchain.cmake -DCMAKE_ANDROID_ARCH_ABI=arm64-v8a`. No Unity needed for native compilation.
- **NDK version: use whatever is on the runner** — Cesium's CI uses Unity's bundled NDK (r23b for 2022.3) by convention, not requirement. The NDK version affects the clang version, not the Reinterop hash. Any NDK that supports API level 21 and arm64-v8a works.
- **Native plugin `.meta` files must be in the published package** — Unity ignores `.so`/`.dll` files in immutable (downloaded) package folders if they lack `.meta` files. Without `.meta` files, the `PluginImporter` never runs, the native libraries aren't loaded, `Reinterop.ReinteropInitializer` throws `DllNotFoundException`, and the entire `CesiumForUnity` assembly becomes unavailable (cascading `CS0246` errors in consumer code).
- **`.meta` generation via `-executeMethod` script in package-publish job** — Three approaches tried:
  - *1.15.3-3/4 (codegen job, placeholder files):* Custom `GenerateNativePluginMeta.cs` used `AssetDatabase.ImportAsset()` + `PluginImporter` on placeholder text files. Standalone targeting broke (`enabled: 0` for all platforms) — likely because `SetCompatibleWithPlatform("StandaloneLinux64", true)` used a string name instead of the `BuildTarget` enum.
  - *1.15.3-5 (package-publish job, passive import):* Deleted the C# script, placed real `.so` files, ran Unity batchmode with just `-quit` hoping auto-import would generate `.meta` files. Failed: Unity generated zero `.meta` files for the `.so` files. Root cause: the upstream Cesium `.gitignore` excludes `Plugins/`, `libCesiumForUnityNative-*.so`, and their `.meta` files — Unity's asset database appears to skip git-ignored files in embedded packages during passive cold-start import.
  - *1.15.3-6 (package-publish job, `-executeMethod`):* Bring back a C# script using `AssetDatabase.ImportAsset()` + `PluginImporter`, but run against real `.so` files in the package-publish job. Use `BuildTarget` enum values (matching Cesium's own `CompileCesiumForUnityNative.ConfigurePlugin()`) instead of string platform names. `.meta` generation succeeded, but Unity builds still failed with `CS0246` — the `CesiumRuntime.asmdef` `LinuxStandalone64` patch was only applied in `phase_codegen` and not persisted in the codegen cache, so the published package's asmdef excluded Linux from its platform include list.
  - *1.15.3-7:* Moved the `CesiumRuntime.asmdef` `LinuxStandalone64` patch into `phase_generate_meta` so it runs in the package-publish job and is included in the published package. All 5 Unity build jobs pass.
- **Linux native binaries must be built on ubuntu-22.04, not ubuntu-latest** — The `unityci/editor` containers are based on older Ubuntu with glibc < 2.38. `ubuntu-latest` (24.04) produces `.so` files requiring GLIBC_2.38 and GLIBCXX_3.4.32, which fail to load in the container (`DllNotFoundException`). Pinning to `ubuntu-22.04` (Jammy, glibc 2.35) ensures compatibility. The native-linux ORAS cache tag includes a `-jammy` suffix to distinguish from binaries built on other runners. If the unityci base image is upgraded in the future, this constraint may be relaxed.

## Remaining

1. ~~**Clean repackaging cruft** from workflow~~ — done.
2. ~~**Restructure workflow** into fan-out shape~~ — done: codegen → parallel linux/android native → package+publish.
3. ~~**Add Android native build** job~~ — done: cmake cross-compilation with android-toolchain.cmake.
4. ~~**`packages-lock.json` regeneration**~~ — done: manifests + lock files updated to `1.15.3`.
5. **Verify on Android device** — confirm absence of Reinterop hash mismatch. Blocked by #8.
6. ~~**Run workflow** — trigger dispatch and verify all 4 jobs succeed.~~ — done: run 22837763895, all 4 jobs green (codegen 7m, linux 30m, android 22m, publish 42s). Package `org.outernet.cesium-unity@1.15.3` published with Linux + Android binaries.
7. ~~**Generate `.meta` files for native binaries in codegen job**~~ — done: placeholder trick implemented in `generate_native_plugin_meta()`. C# editor script creates placeholders, calls `AssetDatabase.ImportAsset()` + `PluginImporter` to set platform targeting, `.meta` files included in ORAS codegen cache (tag bumped to `-f3`). Initial implementation was broken (CesiumForUnitySamples compile errors blocked executeMethod, `check_command` swallowed the failure, bare-GUID `.meta` files passed existence-only check). Fixed: remove samples before meta-gen, use `run_command`, validate `.meta` content contains `PluginImporter`.
8. ~~**Republish with `.meta` files**~~ — done: `1.15.3-3` published with correct PluginImporter `.meta` files (581 bytes, verified). Codegen cache format bumped to `-f3`.
9. ~~**Fix glibc mismatch**~~ — done: native-linux job pinned to `ubuntu-22.04`. `ubuntu-latest` (24.04) produced `.so` requiring GLIBC_2.38, incompatible with unityci container.
10. ~~**Publish `1.15.3-4` and verify Unity builds**~~ — `1.15.3-4` published (run `22863476835`, all 4 cesium-native jobs green). Unity build workflow (`22865672845`) failed: linux64 jobs hit `CS0246` (CesiumForUnity namespace not found during player build). Root cause: `Plugins/Standalone/libCesiumForUnityNative-Runtime.so.meta` had all platforms `enabled: 0` — the custom `GenerateNativePluginMeta.cs` script didn't correctly configure `StandaloneLinux64` targeting. Android jobs TBD (were still running when diagnosed).
11. ~~**Move `.meta` generation to package-publish job**~~ — done: deleted `GenerateNativePluginMeta.cs`, added `phase_generate_meta()` that validates real `.so` files and runs Unity batchmode import. Package-publish job now runs in `unityci/editor` container with license activation. Codegen cache format bumped to `4` (`.meta` files no longer cached). `1.15.3-5` ready to publish.
12. ~~**Fix `.meta` generation: restore `-executeMethod` approach**~~ — done. `1.15.3-5` passive import failed (run `22870958444`): Unity skips git-ignored `.so` files during cold-start import. `1.15.3-6` brought back `-executeMethod` with `ConfigureNativePlugins.cs` using `BuildTarget` enum values + `AssetDatabase.ImportAsset(ForceUpdate)`. `.meta` generation succeeded (run `22873267101`, all 4 jobs green). Unity builds still failed with `CS0246` — root cause: `CesiumRuntime.asmdef` `LinuxStandalone64` patch was only in `phase_codegen` (not persisted in codegen cache), so published package excluded Linux from the assembly platform list. Fixed in `1.15.3-7`: moved asmdef patch to `phase_generate_meta`.
13. ~~**Verify Unity builds pass**~~ — done. `1.15.3-7` (run `22874301772` cesium-native, run `22874813186` Unity). All 5 Unity build jobs passed: no `DllNotFoundException`, no `CS0246`.
14. **Verify on Android device** — **FAILED**. Tested `1.15.3-7` on Pixel 9 (Outernet.Client, `com.Ogment.OuternetNYC.Beta`). The native library loads successfully (`libCesiumForUnityNative-Runtime.so` via `nativeloader: ok`), but `ReinteropInitializer..cctor` throws `NotImplementedException: The native library is out of sync with the managed one` 7 times starting at `CesiumCreditSystem.HasLoadingImages()`. Root cause: `Runtime/ConfigureReinterop.cs:908-919` has `#if UNITY_EDITOR` block in `ExposeToCPP` adding `SceneView`, `EditorApplication`, `EditorUtility` to the function list. Codegen ran in Editor mode (1513 functions, hash `4378356952313487757`), Android runtime compiled without `UNITY_EDITOR` (fewer functions, different hash). Native `.so` has Editor hash, C# has Android hash → mismatch. This is not a cache or CI issue — the single-codegen approach is architecturally wrong. See "Single-codegen approach is fundamentally broken" in design decisions. Same issue affects Linux Standalone (untested). Note: the brief said to test `AndroidMobile-android-mobile` artifact, but AndroidMobile doesn't reference cesium-unity — the correct test artifact is `Outernet.Client-android-mobile`. Logs in `adb.log` at repo root.
15. **Redesign package build to match upstream architecture** — adopt Cesium's per-platform codegen + pre-generated C# with `#if` guards approach. For non-Linux platforms, borrow from official `com.cesium.unity` package. For Linux (Editor + Standalone), run our own per-platform codegen. Strip `Reinterop.dll`, `ConfigureReinterop.cs`, and `csc.rsp` from published package. See design decisions for full analysis.

## Closure

T70 is closed. The single-codegen pipeline it built (1.15.3-1 through 1.15.3-7) successfully automated the build and achieved CI green across all Unity build jobs, but the architectural approach was wrong — each platform needs its own codegen run, not a single shared one. The remaining work (#15: redesign pipeline to augment the official package with Linux support) has moved to **T95**.
