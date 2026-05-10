# `CaptureManager` hardcodes `DeviceType.ARFoundation` for ML2 captures

**Severity**: medium — captures from ML2 are mislabeled; downstream consumers that key on `device_type` get wrong data.

**Location**: `packages/unity/Placeframe/.../CaptureManager.cs`.

**Symptom**: A capture session recorded on a Magic Leap 2 device tags its uploads with `device_type = ARFoundation` instead of `MagicLeap2`. Reconstructions, calibration analytics, and any per-device branching downstream silently treat the data as if it came from a phone.

**Mechanism**: The `CaptureManager.StartCapture` (or equivalent) path constructs the capture metadata with a literal `DeviceType.ARFoundation`. The conditional that should pick the platform-specific value (`PLERION_MAGIC_LEAP` define guard) is absent.

**Fix sketch**: Wrap the `DeviceType` assignment with the same `#if PLERION_MAGIC_LEAP` / `#elif PLERION_ANDROID_MOBILE` block used elsewhere in the project, mapping ML2 to its dedicated enum value. If the enum doesn't have an ML2 variant, add it (server-side too).

**Verification**: Capture on ML2 and inspect the manifest's `device_type` field; assert it reflects the platform.
