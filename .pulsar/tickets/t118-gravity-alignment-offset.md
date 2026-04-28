---
id: T118
title: Investigate gravity alignment as source of consistent point cloud offset
status: design-needed
depends_on: []
---

# T118: Investigate gravity alignment as source of consistent point cloud offset

## Goal

Determine whether the gravity alignment in `VisualPositioningSystem.Localize` causes a consistent fixed translation offset in the point cloud visualization during relocalization, and fix it if confirmed.

## Context

When testing relocalization on both the AndroidMobile app and the Outernet.Client app, the point cloud visualization lines up with the real world in terms of shape and orientation, but is consistently shifted by a fixed amount in the same direction. The offset is the same magnitude and direction across sessions and across both apps, which rules out app-specific bugs and points to the shared `VisualPositioningSystem` package or the backend.

The leading hypothesis is the **gravity alignment block** in `Localize()` (lines 230–233 of `VisualPositioningSystem.cs`). This block strips pitch and roll from `rotationUnityFromMap` by projecting it onto the gravity plane, but the translation (`translationUnityFromMap`, line 235–236) is computed from the **exact** (non-gravity-aligned) `rotationUnityWorldFromCamera`. The gravity-aligned rotation is then paired with the exact translation to form `transformUnityFromMap` (line 238–241), which propagates into `_unityFromEcefTransform`.

The result: the reconstruction origin is placed at the correct world position (translation is right), but the reconstruction's local axes are mapped to world axes with a small rotation error (the pitch/roll correction). Points in the point cloud are rendered relative to the `LocalizationMap` transform, so a rotation error at the origin shifts all points. If the phone has 5° of pitch during localization, points 5m from the reconstruction origin shift by ~0.4m — and since the cloud typically extends in one direction from the origin, this looks like a uniform translation offset.

A full code review of the localization pipeline (backend PnP, axis convention transforms, Sim3d alignment, Anchor repositioning, ECEF round-trips) found no other systematic error. The math at every other step checks out. The gravity alignment is the only place where the rotation used for positioning diverges from the rotation used for the translation computation.

Other hypotheses not yet ruled out:
- The reconstruction's Sim3d alignment introduces a systematic offset for this specific capture.
- An error in the coordinate transform chain that the code review missed.

## Key files

- `packages/unity/Placeframe/Assets/Package/Core/Runtime/VisualPositioningSystem.cs` — `Localize()` method, lines 169–264. The gravity alignment block is lines 230–233. The translation computation is lines 235–236. The `_unityFromEcefTransform` is computed at lines 245–248.
- `packages/unity/Placeframe/Assets/Package/Core/Runtime/Anchor.cs` — Repositions `LocalizationMap` when the ECEF-to-Unity transform updates. Subscribes to `OnEcefToUnityWorldTransformUpdated`.
- `packages/unity/Placeframe/Assets/Package/Core/Runtime/LocalizationMap.cs` — `DownloadMapAndLoad()` positions the map using `EcefToUnityWorld` and loads the point cloud as local-space particles.
- `packages/unity/Placeframe/Assets/Package/Core/Runtime/MathUtil.cs` — `LocationUtilities` basis change functions (`ChangeBasisUnityFromEcef`, etc.) and `UnityFromEcef`/`EcefFromUnity` transform helpers.
- `docker/localizer/src/localize.py` — PnP pose estimation, returns `cam_from_world` with optional Unity basis change.
- `packages/python/core/src/core/axis_convention.py` — Backend basis change matrices and transform functions.
- `docker/reconstructor/src/reconstructor/colmap.py` — Sim3d alignment of reconstruction to anchor frame prior pose.

## Approach

1. **Quick verification**: temporarily comment out the gravity alignment (lines 230–233) and test relocalization. If the offset disappears (but the cloud wobbles with phone tilt), the hypothesis is confirmed.
2. If confirmed, fix the mismatch by applying gravity alignment consistently to the full `unityFromMap` transform — either gravity-align both the rotation AND the translation, or remove gravity alignment entirely and accept the tilt.
3. If the hypothesis is wrong (offset persists without gravity alignment), investigate further: add debug logging to print `translationUnityFromMap`, `rotationUnityFromMap`, and the camera pose per localization to identify where the offset enters.

## Done when

**Verifiable now:**
- The gravity alignment hypothesis is confirmed or rejected with test evidence

**Requires manual verification:**
- Point cloud visualization aligns with the physical world without a consistent offset in both AndroidMobile and Outernet.Client apps

## Next step

Test the hypothesis: comment out lines 230–233 of `VisualPositioningSystem.cs`, build, and relocalize. Compare the point cloud alignment with and without gravity alignment to confirm or reject the hypothesis.
