# T69 Plan: Build Cesium for Unity Native Plugin for Linux

## Context

`com.cesium.unity` v1.15.3 ships no Linux native binaries and all generated C# interop code is wrapped in `#if UNITY_EDITOR_WIN` / `#if UNITY_EDITOR_OSX` guards (no Linux equivalent). On Linux, the interop layer compiles out entirely, causing CS0246 errors that make `uv run build-unity` fail. Additionally, `CesiumRuntime.asmdef` has `includePlatforms` without `LinuxStandalone64`, excluding the assembly from standalone Linux builds.

## Approach

Follow the [official Cesium developer setup](https://cesium.com/learn/cesium-unity/ref-doc/developer-setup.html) rather than the community Linux guide. The official path uses `cesium-unity-samples` as the Unity project, which has all dependencies pre-configured. This avoids the incomplete code generation caused by a minimal Unity project missing required modules.

The [community Linux guide](https://github.com/JOHNI1/CesiumSetupLinuxGuide) (v1.15.3, Unity 2022.3) adds extra steps — Reinterop.csproj patching, TilesetJsonLoader.cpp patching — that are workarounds for older versions and specific environments. These are not needed when following the official developer setup with v1.15.3 and Unity 6.

**Version: v1.15.3, not v1.15.3.** v1.15.3 bumped cesium-native to v0.45.0 which added `BoundingCylinderRegion` to the `BoundingVolume` variant, but the cesium-unity visitor (`CalculateECEFCameraPosition` in `Cesium3DTilesetImpl.cpp`) was not updated — compilation fails in the Runtime target. The fix landed on `main` after the tag (commit `30502bd`, PR #558). v1.15.3 had zero C#/C++ code changes over v1.15.3 (just the submodule bump), so v1.15.3 is functionally identical and compiles cleanly.

### Step 1: Rewrite the build script

**File**: `scripts/build-cesium-native-linux.sh`

Rewrite to follow the official developer setup:

1. Install build dependencies (cmake, ninja, nasm, g++, dotnet-sdk-8.0, pkg-config)
2. Clone `cesium-unity-samples` as the Unity project (has all deps configured)
3. Clone `cesium-unity` v1.15.3 into `Packages/com.cesium.unity/`
4. Add `LinuxStandalone64` to `CesiumRuntime.asmdef`
5. `dotnet publish Reinterop~ -o .` (build the Roslyn source generator)
6. Open Unity to trigger Reinterop code generation (produces C++ interop headers)
7. `cmake -B build -S . -DCMAKE_BUILD_TYPE=RelWithDebInfo` then `cmake --build build --target install` from `native~/`

The official guide does not specify a vcpkg triplet — the CMakeLists.txt may auto-detect. If Linux auto-detection fails, create `native~/vcpkg/triplets/x64-linux-unity.cmake` as a fallback.

### Step 2: Assemble the fork package

After the build script completes, assemble the fork package at `packages/unity/com.cesium.unity/`:

- Copy the C# source, .meta files, .asmdef, package.json from the build clone
- Copy the Linux `.so` files from the build output
- Include the built `Reinterop.dll` (source generator, generates platform-specific C# at compile time)
- Update `CesiumRuntime.asmdef` to include `LinuxStandalone64`
- Update `package.json` version to `1.15.3-linux.1`
- No other platform native binaries (saves ~1.3GB)

### Step 3: Update Outernet.Client manifest

In `legacy/Outernet.Client/Packages/manifest.json`:
- Change `"com.cesium.unity": "1.15.4"` to `"com.cesium.unity": "file:../../../packages/unity/com.cesium.unity"`
- Keep the Cesium scoped registry entry (harmless, makes reverting easier)

### Step 4: Add .gitattributes entry

Add `packages/unity/com.cesium.unity/**/*.so binary` to `.gitattributes` to prevent line-ending conversion. (Already done.)

## Key files

| File | Action |
|---|---|
| `scripts/build-cesium-native-linux.sh` | Rewrite (follow official dev setup with cesium-unity-samples) |
| `packages/unity/com.cesium.unity/` | Create (fork directory: C# + Linux .so from build) |
| `packages/unity/com.cesium.unity/Runtime/CesiumRuntime.asmdef` | Modify (add LinuxStandalone64) |
| `packages/unity/com.cesium.unity/package.json` | Modify (version + displayName) |
| `legacy/Outernet.Client/Packages/manifest.json` | Modify (file: path) |
| `.gitattributes` | Modify (binary marker for .so) — already done |

## Risks

1. **vcpkg triplet auto-detection** — The official guide doesn't specify a triplet. If cmake fails to auto-detect Linux, we need to create the `x64-linux-unity.cmake` triplet. Keep it as a fallback step in the script.
2. **vcpkg build time** — First run: 30-60 minutes for dependency compilation. Script is idempotent so subsequent runs are fast.
3. **Binary size** — Linux .so files ~50-65MB. Committed temporarily; T70 moves to CI + registry.

## Previous blocker (resolved)

The original build script used a minimal empty Unity project. This caused incomplete Reinterop code generation because cesium-unity's dependencies (`com.unity.modules.unitywebrequest`, etc.) couldn't resolve. Adding the missing modules to the manifest fixed code generation, but the root fix is to use `cesium-unity-samples` which has everything pre-configured — matching both the official docs and the user's successful manual build experience.

## Verification

1. `uv run build-unity --project Outernet.Client --target linux64` — must pass (standalone player build)
2. `uv run build-unity --project Outernet.Client --target android` — must still pass (compilation check)
3. Verify fork package has Linux .so files at expected paths
4. Spot-check generated C# for `#if UNITY_EDITOR_LINUX` guards (produced by Reinterop at compile time)
