---
id: T96
title: Cesium for Unity — build all platforms from source instead of augmenting official tgz
status: in-progress
depends_on: []
---

# T96: Cesium for Unity — build all platforms from source

## Goal

Replace the "augment official tgz" approach (T95) with a full from-source build that mirrors Cesium's own CI. Build native libraries and run Reinterop codegen for every target platform, then combine into a single UPM package. Eliminates fragile file-mapping between our codegen output and the official package's internal layout.

## Context

T95 downloads the official `com.cesium.unity` tgz and splices Linux artifacts into it. This hit a wall: the official package's `generated/` directory contains multi-platform `#if`-guarded C# from Cesium's Combine step. Adding Linux codegen in parallel directories (`generated-linux-editor/`, `generated-linux-standalone/`) causes Unity's MonoScriptInfoGenerator to produce duplicate `UnitySourceGeneratedAssemblyMonoScriptTypes_v1` registrations (CS0101). Appending to existing files requires reverse-engineering the official package's directory layout and matching by basename — fragile and version-coupled.

Cesium's own CI avoids this entirely: each platform builds from source, then a Combine job concatenates all `#if`-guarded C# into the same files. No grafting, no layout assumptions. We need Android and will soon need Windows, so we'd be grafting onto an increasingly complex official package. Building from source scales linearly — each platform is the same pattern.

See also:
- T70 — original single-codegen pipeline, proved hash mismatch is real
- T95 — augment approach, design decisions on per-platform codegen still apply
- `response.md` (repo root) — full analysis of Cesium's CI vs our approach

## Architecture

Four-phase workflow in `build-cesium.yml`. All codegen runs on Linux via GameCI containers — no platform-native runners needed for codegen.

### Phase 0 — Activate Unity license

Single job activates a Unity license and pushes the ULF file to ORAS cache. All codegen and combine jobs restore this cached ULF instead of activating independently — avoids a token race where parallel activations invalidate each other's access tokens (all GameCI containers share the same machine-id).

### Phase 1 — Codegen (all parallel, all Linux containers)

Each job runs Reinterop in a platform-specific Unity container, producing a matched pair of C# wrappers + C++ headers. Per-platform codegen is mandatory because Reinterop embeds a function-count hash in both the C# and C++ output. `ConfigureReinterop.cs` uses `#if UNITY_EDITOR` and potentially other platform-specific conditionals that change the function count (T70 proved editor=1513 vs standalone=1487 functions). If the hash in the native binary doesn't match the C# at runtime → `NotImplementedException: The native library is out of sync`.

| Job | GameCI image | Trigger | Guard |
|---|---|---|---|
| codegen-editor-linux | `linux-il2cpp` | `CompileForEditorAndExit` | `UNITY_EDITOR_LINUX` |
| codegen-editor-windows | `windows-mono` | `CompileForEditorAndExit` | `UNITY_EDITOR_WIN` |
| codegen-standalone-linux | `linux-il2cpp` | `-buildLinux64Player` | `UNITY_STANDALONE_LINUX` |
| codegen-standalone-windows | `windows-mono` | `-buildWindows64Player` | `UNITY_STANDALONE_WIN` |
| codegen-standalone-android | `android` | `-buildTarget Android -executeMethod CesiumForUnity.BuildCesiumForUnity.CompileForAndroidAndExit` | `UNITY_ANDROID` |

Cross-platform codegen from Linux is supported by GameCI for Mono-backend builds. The codegen script uses `check_command` (tolerates player link failure) — we only need the Reinterop source generator output, not a working player binary.

Codegen is decomposed into orthogonal `Mode` (editor/standalone) × `Platform` (linux/windows/android) axes. `codegen-cesium.yml` is a reusable workflow accepting `mode`, `platform`, `container-image`, and `cache-tag` inputs.

### Phase 2 — Native build (all parallel, depend on phase 1)

Each job compiles Cesium's C++ source using the C++ headers from its platform's codegen. The hash in the resulting binary matches the C# from the same codegen pass.

| Job | Runner | Compiler | Consumes codegen from |
|---|---|---|---|
| build-native-linux | Linux container (gcc) | gcc | editor-linux + standalone-linux |
| build-native-windows | `windows-latest` (MSVC) | cl.exe | editor-windows + standalone-windows |
| build-native-android | Linux container (NDK) | NDK cross-compile | android |

Windows native build does NOT depend on T75's self-hosted runner — `windows-latest` has MSVC pre-installed and no Unity license is needed for CMake compilation. Android NDK cross-compilation runs on Linux.

`build_cesium_native.py` accepts `--platform` (linux/windows/android) and `--build-directory`. Platform config (vcpkg triplet, cmake args, output names, strip) is in a `PlatformConfig` dataclass. Build steps are shared via the `build-cesium-native` composite action.

#### Android native build details

Android cross-compilation uses the GameCI `android` image, which bundles NDK r27c at `/opt/unity/Editor/Data/PlaybackEngines/AndroidPlayer/NDK`. No separate NDK install needed.

Cesium ships its own triplets and toolchain file in the cloned repo:
- Triplets: `native~/vcpkg/triplets/arm64-android-unity.cmake` (devices) and `x64-android-unity.cmake` (emulators) — use these directly, no need to define our own
- Toolchain: `native~/extern/android-toolchain.cmake` — sets `CMAKE_SYSTEM_NAME=Android`, `CMAKE_ANDROID_NDK=$ANDROID_NDK_ROOT`
- CMake needs `-DCMAKE_TOOLCHAIN_FILE=extern/android-toolchain.cmake -DCMAKE_ANDROID_ARCH_ABI=arm64-v8a`
- Output: `libCesiumForUnityNative-Runtime.so` only (no Editor variant — Editor only runs on desktop)
- Output directory: `Plugins/Android/arm64/` (and `Plugins/Android/x64/` if we build for emulators)
- Initially build arm64 only; x86_64 emulator support can be added later
- `ANDROID_NDK_ROOT` env var must be set explicitly — GameCI sets `ANDROID_NDK_HOME` (different name) only in `~/.bashrc` (which GHA doesn't source), and Cesium's `android-toolchain.cmake` reads `ANDROID_NDK_ROOT`

### Phase 3 — Combine + publish (single Linux container job)

Depends on all phase 1 and phase 2 jobs. Runs in the existing `linux-il2cpp` container.

1. Restore all 5 codegen C# outputs
2. Download all 3 sets of native binaries
3. Combine C# into `generated/` directories with per-platform `#if` guards
4. Generate `.meta` files for all native plugins via Unity batchmode (`ConfigureNativePlugins.cs`)
5. Patch asmdef, publish to npmjs

Unity's `PluginImporter` API knows all `BuildTarget` values regardless of host OS, so `.meta` generation for Windows/Android plugins works from the Linux editor.

### Artifact passing — ORAS everywhere

Use ORAS caching for all artifact passing (codegen → native build, native build → combine). Cross-run caching avoids rebuilding when `CACHE_TAG` hasn't changed.

The `save_cache.py` and `restore_cache.py` scripts need minor cross-platform fixes for the `windows-latest` runner:
- Replace hardcoded `/tmp/` with `tempfile.gettempdir()` (~3 lines)
- Handle `tar --zstd` on Windows (pipe through `zstd` binary instead of GNU tar flag)
- Install ORAS + zstd on Windows (`choco install`)

### Key files

- `.github/workflows/build-cesium.yml` — orchestrator: Phase 0 license → 5 codegen → 3 native → 1 combine
- `.github/workflows/codegen-cesium.yml` — reusable workflow for codegen jobs
- `.github/actions/setup-job/action.yml` — composite action: CI preamble (disk cleanup, ORAS, ghcr login, UV) for Linux and Windows
- `.github/actions/build-cesium-native/action.yml` — composite action: native build steps (deps, clone, cache, build, save)
- `.github/actions/set-cesium-build-paths/action.yml` — composite action: sets BUILD_DIR/PACKAGE_DIR env vars
- `.github/actions/activate-unity-license/action.yml` — composite action: activate license, optionally push ULF to ORAS
- `.github/actions/restore-unity-license/action.yml` — composite action: restore cached ULF + setup .NET
- `build/src/build_scripts/codegen_cesium_native.py` — codegen script (Mode × Platform decomposition)
- `build/src/build_scripts/build_cesium_native.py` — native build script (`--platform`, `--build-directory`)
- `build/src/build_scripts/clone_cesium_native.py` — repo clone (`--build-directory`)
- `build/src/build_scripts/combine_cesium_package.py` — combine + package (5-platform codegen guards)
- `build/src/build_scripts/data/ConfigureNativePlugins.cs` — Unity plugin metadata (all platforms)
- `build/src/build_scripts/tar_zstd.py` — cross-platform tar+zstd (shared by save/restore cache)
- `build/src/build_scripts/save_cache.py`, `restore_cache.py` — ORAS cache scripts (cross-platform)

## Done when

- [x] Linux Editor + Standalone: codegen, native build, and combine all pass in CI
- [ ] Windows Editor + Standalone: codegen, native build, and combine pass in CI
- [ ] Android: codegen, native build, and combine pass in CI
- [ ] Published package installs and runs in Unity Editor on Linux
- [ ] Published package installs and runs in Unity Editor on Windows
- [x] Android device verified: no `NotImplementedException: The native library is out of sync`
- [ ] Linux Standalone player verified: no Reinterop hash mismatch at runtime
- [ ] Win64 Standalone player verified: no Reinterop hash mismatch at runtime
- [x] Cache scripts (`save_cache.py`, `restore_cache.py`) work on `windows-latest`
- [x] T95's `assemble_cesium_package.py` removed
- [ ] Rename `build-cesium-native.yml` → `build-cesium.yml` before merging (reverted due to GitHub dispatch limitation on non-default branches)

## Progress

- Combine script path issues resolved: `-generatedfilesout` uses `{Assembly}/{GeneratorAssemblyName}/{GeneratorTypeName}/` hierarchy (e.g. `Runtime/Reinterop/Reinterop.RoslynSourceGenerator/`)
- Cesium Native build passes in CI — Linux codegen + native build + combine + publish all work
- Unity builds pass for Linux and Android platforms
- `restore_cache.py` hardened against corrupt cache blobs
- Multi-platform implementation complete: all Python scripts parameterized, workflows refactored with composite actions, codegen decomposed into Mode × Platform axes
- Cache tag bumped to "12" (now a `workflow_dispatch` input), manifests and lock files updated to `1.15.3-12`
- CI actions refactored: `container-job-setup` + `setup-oras` replaced by `setup-job` (supports Linux + Windows), `cesium-native-build` → `build-cesium-native` (slimmed), `set-cesium-build-paths` extracted, consistent verb-object naming
- Phase 0 license activation added: single activation → ORAS cache → restore in downstream jobs, eliminates token race from parallel activations
- Android codegen sentinel path fixed: `generated-Android/` not `generated-Standalone/` (Cesium's `BuildTargetGroup.Android.ToString()`)
- Codegen config consolidated into `get_config()` function with `Config` dataclass
- `setup-job` uses `github.token` context directly, no `github-token` input needed
- Open: volumes list duplicated across container jobs — inherent to GitHub Actions `container:` being job-level

## Design rationale

- **Per-platform codegen is mandatory** — T70 proved that editor/standalone hash mismatch causes runtime crashes. The same risk applies across platforms: `#if UNITY_EDITOR_WIN` vs `#if UNITY_EDITOR_LINUX` could produce different function counts. We cannot reuse one platform's codegen for another.
- **Cross-platform codegen from Linux is feasible** — GameCI provides Ubuntu images with each platform's build module (`windows-mono`, `android`). Codegen only needs the C# compilation phase (Roslyn source generators run during compilation), not a working player binary. The existing `check_command` pattern tolerates player link failures.
- **Cesium's own CI uses native runners per platform** — we diverge by using GameCI cross-compilation from Linux, which is simpler (no Windows/macOS runners for codegen) and supported by GameCI for Mono-backend builds.
- **T75 is NOT a dependency for T96** — the only platform that needs a non-Linux runner is the Windows native build (CMake + MSVC), which runs on `windows-latest` GitHub-hosted. No Unity license needed for CMake. T75 is only needed for IL2CPP player builds.
- **ORAS over `actions/upload-artifact`** — the workflow runs infrequently (`workflow_dispatch`) but native builds are slow (15-30 min). ORAS cross-run caching avoids rebuilding when the version hasn't changed. The cross-platform fix to the cache scripts is trivial (~6 lines).

## Related tickets

- T93 — Win64 Mono builds (cross-compiled from Linux, no Windows runner needed) — status: ready
- T75 — Win64 IL2CPP builds (requires Windows runner + MSVC) — status: design-needed. T96 does NOT depend on T75 — see design rationale.
