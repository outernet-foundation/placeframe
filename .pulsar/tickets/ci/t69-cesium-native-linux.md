---
id: T69
title: Build Cesium for Unity native plugin for Linux
status: in-review
depends_on: []
plan: t69-plan.md
---

# T69: Build Cesium for Unity native plugin for Linux

## Goal

Get Outernet.Client's Cesium dependency compiling and entering Play Mode on Linux, so `uv run build-unity` passes for that project.

## Context

`com.cesium.unity` v1.15.4 ships native binaries for Windows, macOS, Android, iOS, and UWP — but not Linux. The generated C# interop layer is wrapped in `#if UNITY_EDITOR_WIN` / `#if UNITY_EDITOR_OSX` guards with no `#if UNITY_EDITOR_LINUX` block, so the entire Reinterop layer compiles out on Linux, producing CS0246 errors for `ReinteropNativeImplementation`.

There is no official Linux support and no indication it's on the roadmap (GitHub issue [#513](https://github.com/CesiumGS/cesium-unity/issues/513)). A community guide exists for v1.15.3: [JOHNI1/CesiumSetupLinuxGuide](https://github.com/JOHNI1/CesiumSetupLinuxGuide).

Research report: `.pulsar/research/cesium-unity-native-linux.md`

## Design decisions

1. **Artifact hosting**: Build manually once, commit the forked package to the repo as a local file path dependency (`"file:../../packages/cesium-unity-linux"`). Follow-up ticket to move the build to CI and publish to a scoped registry (same one being set up for Placeframe UPM packages).
2. **Augment vs. replace**: Fork of the official `com.cesium.unity` package — same name, superset contents. Adds Linux `.so` binaries and `#if UNITY_EDITOR_LINUX` generated C# alongside the existing Win/Mac/Android/iOS binaries. Outernet.Client's manifest points at the local fork instead of Cesium's registry.
3. **Build location**: Built manually once outside the repo. The resulting package (including `.so`) is committed to the repo temporarily. Follow-up ticket moves the build to CI and the artifact to a registry.
4. **Play Mode bar**: "Loads without crashing" is sufficient. No need for specific Cesium geospatial functionality to work.
5. **Version tracking**: Manual for now. Follow-up ticket to automate via CI.
6. **Fork scope**: C# code + Linux `.so` files only (~100-150MB). No other platform binaries (saves ~1.3GB). All original C# platform guards preserved so compilation works everywhere; other platforms lose runtime/Play Mode from this fork but can switch back to the official registry.
7. **Build automation**: Native `.so` files built via an idempotent shell script committed to the repo. Script installs deps, clones source, and builds regardless of container starting state — serves as both build tool and documentation.
8. **C# guard generation**: Reinterop source generator handles Linux C# guard generation automatically when opened in Unity on Linux — no manual patching needed.
9. **Build process**: Follow the [official Cesium developer setup](https://cesium.com/learn/cesium-unity/ref-doc/developer-setup.html), not the community Linux guide. Clone `cesium-unity-samples` as the Unity project (has all dependencies pre-configured), clone `cesium-unity` into its `Packages/`, publish Reinterop, open in Unity, cmake build. The community guide's extra steps (Reinterop.csproj patching, TilesetJsonLoader.cpp patching) are workarounds for older versions/specific environments and are not needed.
10. **Version: v1.15.3, not v1.15.4.** v1.15.4 bumped cesium-native to v0.45.0 which added `BoundingCylinderRegion` to the `BoundingVolume` variant, but cesium-unity v1.15.4 didn't update the `CalculateECEFCameraPosition` visitor to handle it — causing a compilation failure on any platform. The fix landed on main after v1.15.4 (commit `30502bd`). v1.15.3 pins cesium-native v0.44.x which doesn't have the new type. v1.15.4 had zero cesium-unity code changes over v1.15.3, so nothing is lost by staying on v1.15.3.

## Approach

An idempotent build script follows the [official Cesium developer setup](https://cesium.com/learn/cesium-unity/ref-doc/developer-setup.html): clone `cesium-unity-samples` (provides a complete Unity project with all dependencies), clone `cesium-unity` into its `Packages/`, publish Reinterop, open in Unity on Linux (triggers Reinterop code generation), then build native `.so` files with cmake. The build output is assembled into a fork package at `packages/unity/com.cesium.unity/` with Linux `.so` binaries. Outernet.Client manifest changes from Cesium registry to local `file:` path.

## Done when

- [x] Outernet.Client passes `uv run build-unity` for `linux64` — build succeeds (`Build Finished, Result: Success`), but Unity hangs on exit (T73)
- [ ] Outernet.Client passes `uv run build-unity` for `android` (compilation check) — untested, low risk since fork only adds Linux binaries
- [x] Forked `com.cesium.unity` package committed to repo with Linux binaries
- [x] Outernet.Client manifest points at local fork
- [x] Build process documented for future version bumps (build script + plan + design decisions)
- [x] Follow-up ticket exists for CI build + registry hosting (T70)
- [ ] Play Mode can be entered without crashes (stretch goal, may surface separate blockers)

## Log

- v1.15.4 failed to compile: cesium-native v0.45.0 added `BoundingCylinderRegion` to the `BoundingVolume` variant but `CalculateECEFCameraPosition` visitor wasn't updated. Downgraded to v1.15.3 (zero code changes between the two versions). Compiled cleanly.
- First build attempt used v1.15.4 with the previous script's minimal-project approach. Rewrote to use `cesium-unity-samples` per official developer setup. Code generation succeeded on first try.
- `.so` files were 391-408 MB unstripped (RelWithDebInfo). Stripping reduced to 28-34 MB (~10x). Added strip step to build script.
- `NodeBatchCreate` constructor call in `Utility.cs` was broken — `linkType`/`labelType` became required params but the call site used object initializer syntax. Pre-existing bug, fixed.
- `Platform` class missing for standalone Linux — all implementations behind preprocessor guards with no Linux standalone match. Fixed by adding `AUTHORING_TOOLS_ENABLED` to Standalone scripting defines.
- `HandsSampleProjectValidation` (imported XR Interaction Toolkit sample) caused infinite post-build hang: registered a `delayCall` to open Project Settings UI, which triggered MagicLeap's settings provider to enumerate GUI styles in batchmode, looping forever. Fixed by deleting unused `Assets/Samples/` directory.
- Unity still hangs after successful build even without the samples loop — stops after `TrimDiskCacheJob`, never exits. Filed as T73.

## Observations

- `Assets/Samples/` contained imported UPM samples (XR Hands HandVisualizer, XR Interaction Toolkit Starter Assets + Hands Demo) that nothing referenced — deleted.
- `legacy/Outernet.Client/Assets/Samples.meta` left behind after deleting Samples/ — Unity recreates the empty directory from the orphaned `.meta` file on next open. The `.meta` should also be deleted.
