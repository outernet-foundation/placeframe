---
id: T99
title: Burst-compiled native plugin missing from Android APK
status: done
depends_on: []
---

# T99: Burst-compiled native plugin missing from Android APK

## Goal

Diagnose and fix why Burst AOT-compiled native code (`_burst_0_0`) is not present in the Android APK built by CI.

## Symptom

ADB logs from an Android device (2026-03-12) show:

```
D nativeloader: Load liblib_burst_0_0.so ... dlopen failed: library "liblib_burst_0_0.so" not found
D Unity   : Failed to load native plugin: Unable to lookup library path for '_burst_0_0'.
D nativeloader: Load lib_burst_0_0.so ... dlopen failed: library "lib_burst_0_0.so" not found
```

Unity tries both `liblib_burst_0_0.so` and `lib_burst_0_0.so` — neither exists in the APK. The main Burst runtime (`lib_burst_generated.so`) loads successfully, but the individual Burst-compiled job libraries are missing.

## Resolution: not a bug

The `_burst_0_0` split-library naming pattern is from older Burst versions. In Unity 6000.0, Burst compiles all jobs into a single `lib_burst_generated.so`, which loads successfully (ADB log line 2866: `ok`). Unity tries the legacy naming convention as a fallback, fails at **Debug** level (`D`, not `E`), and moves on gracefully.

This is the same benign pattern as the MagicLeap plugin failures (`ml_ycbcr_renderer`, `ml_unity_native_logging`, `ml_systrace_plugin`) — Debug-level messages for plugins that don't exist on the target device. These messages have likely always been present in ADB output; they were only noticed now because the Cesium `NotImplementedException` crash (fixed by T97) was no longer dominating the logs.

Evidence:
- `lib_burst_generated.so` loads OK → Burst AOT code is present and working
- `BurstAotSettings_Android.json` has `EnableBurstCompilation: true`
- Log level is `D` (Debug), not `E` (Error) — same as other benign plugin failures
- No downstream errors attributable to missing Burst code

## Log

Clean investigation, no issues. Initial ticket was created before diagnosis.

## Observations

No pre-existing issues noticed.
