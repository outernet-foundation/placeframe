---
id: T97
title: Speed up Android codegen by downgrading to Unity 2022.3
status: in-progress
depends_on: [T96]
---

# T97: Speed up Android codegen by downgrading to Unity 2022.3

## Goal

Reduce Android codegen time from ~46 minutes to something comparable to the other platforms (~1-4 minutes). Currently Android codegen is an order of magnitude slower because Unity 6 forces IL2CPP as the only Android scripting backend, triggering the full IL2CPP + Gradle pipeline.

## Context

All five codegen jobs in T96's Cesium build pipeline exist to trigger the Reinterop source generator — they compile C# with platform-specific defines active, producing matched C#/C++ output. Only the C# compilation step matters; the actual player build always fails (tolerated via `check_command`).

Linux and Windows standalone codegen use `-buildLinux64Player`/`-buildWindows64Player`, which attempt a Mono-backend player build. These fail fast at the link step (~1 min total) because the native library hasn't been built yet.

Android standalone codegen uses `-buildTarget Android -executeMethod CesiumForUnity.BuildCesiumForUnity.CompileForAndroidAndExit`, which is Cesium's own method. It does:
```csharp
PlayerSettings.SetScriptingBackend(BuildTargetGroup.Android, ScriptingImplementation.IL2CPP);
PlayerSettings.Android.targetArchitectures = ARM64 | X86_64;
BuildPlayer(BuildTargetGroup.Android, BuildTarget.Android, ...);
```

The IL2CPP scripting backend triggers the full IL2CPP conversion and Gradle project setup — dramatically heavier than Mono compilation. `ExitAfterCompile = true` stops Reinterop after generating output, but Unity still sets up the IL2CPP pipeline before C# compilation even begins.

In the CI run on 2026-03-12, codegen timings were:
- editor-linux: cache hit (0s)
- standalone-linux: cache hit (0s)
- editor-windows: cache hit (0s)
- standalone-windows: cache hit (0s)
- standalone-android: **46 min** (cold, no cache)

## Design decisions

All three approaches originally proposed are infeasible on Unity 6:
- Approach 1 (Mono-backend BuildPlayer): Unity 6 dropped Mono for Android entirely
- Approach 2 (Editor compile with buildTarget): `UNITY_EDITOR` always defined in batchmode
- Approach 3 (Bare project open + quit): Same `UNITY_EDITOR` problem

**Solution: downgrade all codegen jobs to Unity 2022.3.42f1.** This version still supports Mono on Android. A custom `CompileForAndroidMono.cs` executeMethod replaces Cesium's `CompileForAndroidAndExit`, setting `ScriptingImplementation.Mono2x` instead of IL2CPP. The pre-generated C# is platform-guarded and Unity-version-independent, so downgrading codegen doesn't affect the consuming Unity 6 apps.

2022.3.42f1 chosen over .41f1 to avoid a known mono-boehm bug. Matches Cesium's own CI which uses 2022.3.41f1.

### Issues found during CI runs

- **`CompileCesiumForUnityNative` is `internal`** to the Cesium package assembly. Our script in `Assets/Editor/` (Assembly-CSharp-Editor) cannot access it. Not needed: `ExitAfterCompile` is checked in `OnPostBuildPlayerScriptDLLs`, which runs after C# compilation — Reinterop output is already on disk by then.
- **`AndroidArchitecture.ARM64` is IL2CPP-only** on Unity 2022.3 Mono. Setting it silently fails (target becomes None), causing `UnityException: Target architecture not specified`. Fix: use `ARMv7` instead — architecture doesn't affect codegen output.
- **`TypeInitializationException` during `OnBuildPreProcess` is non-fatal.** When `BuildPlayer` starts, Cesium's build callbacks try to P/Invoke into the native library (which doesn't exist during codegen). Unity logs the error and continues — the build proceeds to player compilation where Reinterop generates output.
- **Android Mono build doesn't fail fast like Linux/Windows.** Linux/Windows standalone builds fail at the native library link step (~1 min). Android Mono gets past linking (placeholder `.so` files satisfy it) and continues into shader compilation (~10+ min of wasted work). Fix: add an `IPostBuildPlayerScriptDLLs` callback that exits Unity right after C# compilation, before shaders.

## Approach

1. Replace all `unityci/editor:6000.0.66f1-*` container images with `2022.3.42f1` equivalents in `build-cesium-native.yml`
2. Create `CompileForAndroidMono.cs` — identical to Cesium's method but sets Mono backend
3. Inject the script into the Unity project at codegen time (Android only)
4. Update codegen script to call our method instead of Cesium's

## Key files

- `.github/workflows/build-cesium-native.yml` — container image references (9 changes)
- `.github/workflows/codegen-cesium.yml` — example in description
- `build/src/build_scripts/codegen_cesium_native.py` — Android build flags + script injection
- `build/src/build_scripts/data/CompileForAndroidMono.cs` — custom executeMethod

## Done when

- Android codegen completes in under 5 minutes (comparable to other platforms)
- Reinterop function count matches between codegen and native build (no hash mismatch at runtime)
- CI run demonstrates all four phases passing end-to-end

## Pre-existing bug: REINTEROP_GENERATED_DIRECTORY not set for standalone builds

**Discovered 2026-03-12 via ADB logs from device.** The on-device error is `NotImplementedException: The native library is out of sync with the managed one` — the Reinterop hash check fails at app startup.

### Root cause

The cesium-unity `native~/CMakeLists.txt` line 24 sets:
```cmake
set(REINTEROP_GENERATED_DIRECTORY "generated-Editor" CACHE STRING ...)
```

`build_cesium_native.py` never overrides this for standalone builds. Every platform's **Runtime** native library is compiled from `generated-Editor/` C++ (editor function table: 1513 functions, hash `4378356952313487757`), but the C# at runtime uses the platform-specific standalone section (1487 functions, hash `7031067308632330464`). The 26-function mismatch triggers the error.

Verified in CI logs for **both** build-number 12 (Unity 6, pre-T97) and build-number 13 (Unity 2022.3, post-T97) — both compile `CesiumForUnityNative-Runtime` from `generated-Editor/src/`. This is not a T97 regression; it's a pre-existing bug in the native build script.

### Evidence

- Published package `ReinteropInitializer.cs` contains per-platform hashes:
  - Editor sections (UNITY_EDITOR_LINUX, UNITY_EDITOR_WIN): hash=`4378356952313487757`, count=`1513`
  - Standalone sections (UNITY_STANDALONE_LINUX, UNITY_STANDALONE_WIN, UNITY_ANDROID): hash=`7031067308632330464`, count=`1487`
- Android native build log (`build-native-android` job 66746085949): every `Building CXX` line shows `generated-Editor/src/`
- Same for Linux native build (`build-native-linux` job 66745891747): Runtime target uses `generated-Editor/src/`
- `ConfigureReinterop.cs` in cesium-unity maps `CppOutputPath` by platform guards:
  - `UNITY_EDITOR` → `generated-Editor`, `UNITY_ANDROID` → `generated-Android`, `UNITY_64` → `generated-Standalone`

### Fix

`build_cesium_native.py` must pass `-DREINTEROP_GENERATED_DIRECTORY=generated-{suffix}` to CMake for standalone builds. The suffix mapping matches `codegen_cesium_native.py`'s `STANDALONE_GENERATED_SUFFIXES`: Linux/Windows → `Standalone`, Android → `Android`. Editor builds keep the default `generated-Editor`.

## Verified on device (2026-03-12)

The `REINTEROP_GENERATED_DIRECTORY` fix (commit `9d05bf8c`) is confirmed working. ADB logs from an Android device show:
- `libCesiumForUnityNative-Runtime.so` loads successfully (no dlopen failure)
- No `NotImplementedException`, no `out of sync`, no Reinterop hash mismatch
- Cesium shaders compile and upload normally

The previous `NotImplementedException: The native library is out of sync` error is gone.
