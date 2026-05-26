# `CaptureManager` hardcodes `DeviceType.ARFoundation` for ML2 captures

**Severity**: medium — captures from ML2 are mislabeled; downstream consumers that key on `device_type` get wrong data.

**Location**: `packages/unity/Placeframe/Assets/Package/Core/Runtime/CaptureManager.cs:98` — the `LocalCapture` constructor invocation inside `GetCaptures`'s `.Select(...)` projection.

**Symptom**: A capture session enumerated on a Magic Leap 2 device exposes `device_type = ARFoundation` instead of `MagicLeap2`. Reconstructions, calibration analytics, and any per-device branching downstream silently treat the data as if it came from a phone.

**Mechanism**: `GetCaptures` projects each on-disk capture id into `new LocalCapture(id, ..., DeviceType.ARFoundation, ...)` with a literal `DeviceType.ARFoundation`. No conditional picks the platform-specific value — the `#if PLERION_MAGIC_LEAP` / `#elif PLERION_ANDROID_MOBILE` guard used elsewhere in the project is absent at this call site.

**Fix sketch**: Wrap the `DeviceType.ARFoundation` argument with the same `#if PLERION_MAGIC_LEAP` / `#elif PLERION_ANDROID_MOBILE` block used elsewhere in the project, mapping ML2 to its dedicated enum value. If the enum doesn't have an ML2 variant, add it (server-side too). Audit the rest of the file for any other literal `DeviceType.ARFoundation` writes — `StartCapture` and the per-frame recording path appear to read the platform indirectly, but the same fix should be applied anywhere the enum is constructed.

**Verification**: Capture on ML2 and inspect the manifest's `device_type` field; assert it reflects the platform.
