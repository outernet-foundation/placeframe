# Cesium for Unity: Native Plugin for Linux

Research conducted 2026-03-03. Context: Outernet.Client uses `com.cesium.unity` v1.15.4 which fails to compile on Linux because no native library is shipped for that platform.

## The question

How to build CesiumForUnityNative from source for Linux, package it so it works with or replaces the existing `com.cesium.unity` UPM package, and host it in a registry. The bar is Play Mode in the editor, not just compilation.

Constraints: FOSS-only tooling, self-hosted, Outernet.Client only.

## Current state

Outernet.Client pins `com.cesium.unity` **v1.15.4** from the Cesium scoped registry (`https://unity.pkg.cesium.com`). The cached package lives at `Library/PackageCache/com.cesium.unity@AC303E3B95B5/`.

## Why it fails on Linux

The Cesium package uses a Roslyn source generator called **Reinterop** that generates C#↔C++ interop code. All generated C# files are wrapped in platform preprocessor guards:

```csharp
#if UNITY_EDITOR_OSX
// ...
#endif
#if UNITY_EDITOR_WIN
// ...
#endif
```

There is **no `#if UNITY_EDITOR_LINUX` block**. The entire interop layer compiles out on Linux, so the `[ReinteropNativeImplementation]` attribute doesn't exist, and every class annotated with it produces CS0246 errors.

## Official Linux support

**There is none.** v1.15.4 ships binaries for Windows x64, macOS (x64 + arm64), Android (arm64 + x86_64), iOS, and UWP. Linux is absent. GitHub issue [#513](https://github.com/CesiumGS/cesium-unity/issues/513) tracks the request. There is no indication it's on the roadmap.

## Build process

Two-phase build:

### Phase 1: Reinterop (C# source generator)

```bash
cd cesium-unity
dotnet publish Reinterop~ -o .
```

Produces `Reinterop.dll`, a Roslyn source generator that runs inside the C# compiler.

### Phase 2: Native C++ library

```bash
cd native~
cmake -B build-Standalone -S . \
  -DCMAKE_BUILD_TYPE=RelWithDebInfo \
  -DVCPKG_TRIPLET=x64-linux-unity \
  -DVCPKG_OVERLAY_TRIPLETS=$(pwd)/vcpkg/triplets \
  -DEDITOR=OFF
cmake --build build-Standalone --target install --parallel $(nproc)
```

Two variants needed:
- **Editor** (`-DEDITOR=ON`): produces `libCesiumForUnityNative-Editor.so` → installed to `Editor/`
- **Runtime** (`-DEDITOR=OFF`): produces `libCesiumForUnityNative-Runtime.so` → installed to `Plugins/Standalone/`

### Build dependencies

- CMake 3.18+
- .NET SDK 6.0+
- NASM assembler
- C++ compiler with C++20 support
- Ninja build system
- vcpkg (bundled as submodule in `native~/extern/`)

All native dependencies (OpenSSL, libcurl, libjpeg-turbo, draco, KTX, etc.) are resolved via vcpkg and **statically linked** into the single `.so` using the `x64-linux-unity` triplet. The resulting `.so` should only depend on libc, libstdc++, libm, libpthread, libdl.

### Additional steps for Linux

Per the [JOHNI1/CesiumSetupLinuxGuide](https://github.com/JOHNI1/CesiumSetupLinuxGuide) (covers v1.15.3):
- Open in Unity Editor on Linux to trigger Reinterop source generation (produces generated C# and C++ interop code with Linux guards)
- Patch `TilesetJsonLoader.cpp` for Linux compilation issues
- Update `CesiumRuntime.asmdef` to add `"LinuxStandalone64"` to `includePlatforms`

## What the build produces

A modified UPM package that adds alongside existing binaries:
- `Editor/libCesiumForUnityNative-Editor.so` + `.meta`
- `Plugins/Standalone/libCesiumForUnityNative-Runtime.so` + `.meta`
- Generated C# files with `#if UNITY_EDITOR_LINUX` / `#if UNITY_STANDALONE_LINUX` blocks appended to existing platform guards
- Updated `CesiumRuntime.asmdef` with Linux platform

This **augments** the existing package — the Windows/macOS/Android/iOS binaries remain. The result is a superset of the official package with Linux added.

## Packaging options

The official package bundles all native binaries in the UPM tarball. Options for distributing a Linux-augmented version:

| Option | Complexity | Maintenance | Notes |
|---|---|---|---|
| **Local file path** (`"file:path/to/package"`) | Low | Manual | Simplest, no infra needed. Package dir lives in repo or alongside it. |
| **Git URL** (`"https://...cesium-unity-linux.git"`) | Low | Manual | Unity supports git-based UPM packages natively. Fork repo, add Linux binaries. |
| **Local tarball** (`"file:../path/to.tgz"`) | Low | Manual | Same as file path but compressed. |
| **Verdaccio registry** | Medium | Automated | MIT license, independent community, self-hosted. Unity scoped registries speak npm protocol, so Verdaccio works natively. Publish with `npm publish`. |
| **OpenUPM** | N/A | N/A | Hosted service, auto-builds from GitHub tags. Not suitable for a custom fork. |

For a single custom package, **git URL** or **local file path** is simplest. **Verdaccio** makes sense if more custom packages are needed later (it could also serve the Placeframe UPM packages).

## Play Mode in headless container

**Yes, Unity can enter Play Mode in batchmode.** The approach:

1. Create an Editor script with a static method calling `EditorApplication.EnterPlaymode()`
2. Launch with `-batchmode -nographics -executeMethod YourClass.EnterPlayMode` (no `-quit`)
3. In-game code detects `Application.isBatchMode` and calls `EditorApplication.ExitPlaymode()` + `EditorApplication.Exit(0)` when done

With `-nographics`, Unity uses the **Null Graphics Device** — no GPU needed, no display needed. Physics, scripting, and game logic execute normally. Rendering is stubbed out.

## Runtime feasibility without GPU

**Likely works for data operations.** Cesium-native is a data processing library — it handles tile selection, HTTP fetching, decoding, and coordinate transforms. It has **no dependency on OpenGL, Vulkan, or any graphics API**. The rendering is handled by Unity's pipeline, which is stubbed by the Null Graphics Device.

Caveats:
- KTX GPU-compressed texture decompression may fail or be skipped
- MonoBehaviour code in Cesium that touches the rendering pipeline (materials, meshes) might not gracefully handle the Null device
- Cesium's credit system UI rendering would need suppression

For a "does it load and run without crashing" test, this is probably fine.

## Sources

- [Cesium for Unity Developer Setup](https://cesium.com/learn/cesium-unity/ref-doc/developer-setup.html)
- [cesium-unity GitHub](https://github.com/CesiumGS/cesium-unity)
- [Add support for Linux — Issue #513](https://github.com/CesiumGS/cesium-unity/issues/513)
- [JOHNI1/CesiumSetupLinuxGuide](https://github.com/JOHNI1/CesiumSetupLinuxGuide) — community guide for v1.15.3
- [Building plugin on Linux — Cesium Community](https://community.cesium.com/t/building-plugin-on-linux/22551)
- [cesium-unity build.yml (GitHub Actions)](https://github.com/CesiumGS/cesium-unity/blob/main/.github/workflows/build.yml)
- [C++ and C# Interop in Cesium for Unity (Blog)](https://cesium.com/blog/2023/01/26/developing-for-unity/)
- [cesium-native Dependencies](https://cesium.com/learn/cesium-native/ref-doc/md_topics_2dependencies.html)
- [Unity Desktop Headless Mode](https://docs.unity3d.com/6000.3/Documentation/Manual/desktop-headless-mode.html)
- [Headless automation in Unity](https://partiallydisassembled.net/posts/unity-headless.html)
- [Verdaccio](https://verdaccio.org/) — MIT license, self-hosted npm registry
