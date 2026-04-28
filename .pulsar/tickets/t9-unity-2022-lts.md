---
id: T9
title: Unity 2022.3 LTS compatibility
status: ready
depends_on: []
---

# Unity 2022.3 LTS Compatibility for Placeframe Packages + AndroidMobile

## Context

The three Placeframe Unity packages and the AndroidMobile capture app currently target Unity 6 exclusively. The packages need to support Unity 2022.3 LTS to broaden their audience. Everything will be downgraded to 2022.3 — the packages set `"unity": "2022.3"` as the minimum (they'll still work in Unity 6 via `#if` preprocessor gates), and all Unity projects (AndroidMobile, package dev project) run on 2022.3.

Other apps (MapRegistrationTool, MakeItSing) are unaffected.

Future CI can compile-test the packages against multiple Unity versions (2022.3, Unity 6) using throwaway test projects — the `#if UNITY_6000_0_OR_NEWER` branch activates automatically when compiled by Unity 6.

## Assessment

**This is low effort.** The C# code is already fully C# 9 compatible — zero language issues. The only actual code change is one preprocessor gate around a single method. Everything else is version numbers in JSON files.

---

## Part 1: Package Changes

### 1. Lower `"unity"` minimum in all three `package.json` files

| File | Change |
|---|---|
| `packages/unity/Placeframe/Assets/Package/Core/package.json` | `"unity": "6000.0"` -> `"unity": "2022.3"` |
| `packages/unity/Placeframe/Assets/Package/ARFoundation/package.json` | `"unity": "6000.0"` -> `"unity": "2022.3"` |
| `packages/unity/Placeframe/Assets/Package/MagicLeap/package.json` | `"unity": "6000.0"` -> `"unity": "2022.3"` |

### 2. Fix ARFoundation version dependencies

**Core package** — Remove `"com.unity.xr.arfoundation": "6.0.6"` entirely. The Core asmdef (`Plerion.VPS.asmdef`) doesn't reference ARFoundation assemblies, and none of the 10 C# files in `Core/Runtime/` import ARFoundation types. This dependency is unnecessary.

**ARFoundation package** — Change `"com.unity.xr.arfoundation": "6.0.6"` to `"com.unity.xr.arfoundation": "5.1.0"`. Sets the floor at 5.1; Unity 6 projects will still resolve to 6.x.

| File | Change |
|---|---|
| `packages/unity/Placeframe/Assets/Package/Core/package.json` | Remove ARFoundation dependency line |
| `packages/unity/Placeframe/Assets/Package/ARFoundation/package.json` | `"6.0.6"` -> `"5.1.0"` |

### 3. Preprocessor gate in `CameraProvider.cs` (the only code change in all packages)

**File**: `packages/unity/Placeframe/Assets/Package/ARFoundation/Runtime/CameraProvider.cs`, lines 149-164

`ARAnchorManager.TryAddAnchorAsync(Pose)` is ARFoundation 6.x only. In 5.x, the equivalent is `AddAnchor(Pose)` — synchronous, returns `ARAnchor` directly.

Replace the `PrepareAnchor` method with:

```csharp
private async UniTask<ARAnchor> PrepareAnchor(CancellationToken cancellationToken)
{
    await UniTask.WaitUntil(
        () => ARSession.state == ARSessionState.SessionTracking,
        cancellationToken: cancellationToken
    );

    var pose = new Pose(
        _cameraManager.transform.position,
        Quaternion.Euler(0f, _cameraManager.transform.eulerAngles.y, 0f)
    );

#if UNITY_6000_0_OR_NEWER
    var result = await _anchorManager.TryAddAnchorAsync(pose);
    return result.value;
#else
    var anchor = _anchorManager.AddAnchor(pose);
    if (anchor == null)
        throw new Exception("Failed to add anchor");
    return anchor;
#endif
}
```

Everything else in `CameraProvider.cs` — `XRCpuImage`, `TryAcquireLatestCpuImage`, `ConvertAsync`, `FormatSupported`, `ARCameraManager.frameReceived` — has identical signatures in both ARFoundation 5.x and 6.x.

---

## Part 2: Downgrade Package Dev Project to Unity 2022.3

**Project**: `packages/unity/Placeframe/`

### 1. Update `ProjectSettings/ProjectVersion.txt`

Change to target 2022.3 patch version (e.g., `2022.3.56f1` or latest).

### 2. Update `Packages/manifest.json`

Downgrade Unity-version-locked packages to 2022.3-compatible equivalents. Third-party packages (UniTask, R3) pulled from Git URLs should work as-is.

### 3. Update `ProjectSettings/ProjectSettings.asset`

- `apiCompatibilityLevel`: change from level 6 (`.NET 6+`) to level 3 (`.NET Standard 2.1`)

### 4. Open in Unity 2022.3

- Delete `Packages/packages-lock.json` (will be regenerated)
- Open in Unity 2022.3 editor, let it re-import
- Resolve any remaining package version warnings

---

## Part 3: Downgrade AndroidMobile to Unity 2022.3

### 1. Update `Packages/manifest.json`

Key version changes:

| Package | Current (Unity 6) | Target (2022.3) |
|---|---|---|
| `com.unity.render-pipelines.universal` | 17.0.4 | 14.0.11 |
| `com.unity.xr.arfoundation` | 6.0.6 | 5.1.5 |
| `com.unity.xr.arcore` | 6.0.6 | 5.1.5 |
| `com.unity.ugui` | 2.0.0 | 1.0.0 |
| `com.unity.test-framework` | 1.6.0 | 1.4.5 |
| `com.unity.multiplayer.center` | 1.0.0 | Remove (doesn't exist in 2022.3) |

Third-party packages (UniTask, R3, StatefulUnity, ObserveThing, Nessle, NuGetForUnity) are pulled from Git URLs and should work as-is — they all support 2022.3.

Local Placeframe packages (`file:../../../packages/...`) will work because of Part 1 changes.

### 2. Update `ProjectSettings/ProjectVersion.txt`

Change to the target 2022.3 patch version (e.g., `2022.3.56f1` or latest).

### 3. Update `ProjectSettings/ProjectSettings.asset`

- `apiCompatibilityLevel`: change from level 6 (`.NET 6+`) to level 3 (`.NET Standard 2.1`)
- Other settings (IL2CPP, ARM64, min SDK 24) should be fine as-is

### 4. Open in Unity 2022.3

- Delete `Packages/packages-lock.json` (will be regenerated)
- Open project in Unity 2022.3 editor
- Let it re-import assets and regenerate URP pipeline configuration
- URP pipeline assets may need re-creation if serialization format changed between URP 14 and 17
- Resolve any remaining package version warnings

### 5. App C# code: no changes expected

The app's scripts (`CaptureController`, `AuthManager`, `CameraProvider` usage, etc.) don't call version-sensitive ARFoundation APIs directly — they go through the Placeframe `CameraProvider`, which handles the version differences via `#if`.

---

## Verification

### Packages
1. Open `packages/unity/Placeframe/` in Unity 2022.3 — verify no compilation errors
2. Verify the `#else` branch of `CameraProvider.cs` compiles (the default path on 2022.3)

### AndroidMobile App
1. Open in Unity 2022.3 — verify all packages resolve and project compiles
2. Build APK for Android
3. Deploy and test capture flow (exercises `CameraProvider.PrepareAnchor` via ARFoundation 5.x `AddAnchor` path)
4. Test localization flow

### Risk: `ARAnchorManager.AddAnchor(Pose)` deprecation
In late ARFoundation 5.x, `AddAnchor` may be `[Obsolete]` (warning, not error). If it was removed (unlikely), fallback is instantiating a `GameObject` with `ARAnchor` component at the desired pose. Verify at runtime.

## Done when

**Verifiable now (no special infra):**
- `#if` gate compiles under basedpyright (no Python changes break)

**Requires Unity (verify manually later):**
- Project opens in 2022.3 without errors
- APK builds
