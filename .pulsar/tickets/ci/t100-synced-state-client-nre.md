---
id: T100
title: SyncedStateClient NullReferenceException on startup
status: in-progress
depends_on: []
---

# T100: SyncedStateClient NullReferenceException on startup

## Goal

Diagnose and fix the NullReferenceException in `SyncedStateClient` that fires repeatedly on app startup, producing a wall of red error logs.

## Symptom

ADB logs from an Android device (2026-03-12) show a repeating pattern every frame:

```
E Unity : [SyncedStateClient] Object reference not set to an instance of an object.
E Unity : [UncaughtException] Unity exception
```

The full stack trace passes through `Serilog.Core.Logger.Write` → `Outernet.Client.Logger.Serilog` → `Outernet.Client.Enricher.SerilogStackTrace` → `Outernet.Client.Enricher.Enrich`. The NRE originates in `SyncedStateClient` and the Serilog enricher logs it, then the enricher itself throws again (recursive error logging).

## Context

This was likely masked previously by the Cesium `NotImplementedException` crash (T97) — the app crashed on startup before reaching `SyncedStateClient` initialization. Now that Cesium loads correctly, the app gets further and hits this pre-existing bug.

## Diagnosis so far

### Root cause: enricher NRE in `SerilogStackTrace` on every log call

The Serilog enricher crashes on **every** log call, not just SyncedStateClient logs. The "SyncedStateClient" and "UncaughtException" errors in ADB are downstream symptoms — the enricher NRE kills the original log message, then the exception logging for the enricher failure also crashes in the enricher, cascading into the wall of red.

### Enricher fixes applied so far

1. **`GetFrames()` null on IL2CPP** (commit `696d5fad`): `stackTrace.GetFrames()` returns null on Android IL2CPP. Fixed with null-coalesce to `Array.Empty<StackFrame>()`.

2. **`ConnectionManager.RoomConnectionRequested` null before init** (commit `62cfa6fb`): The enricher accesses `ConnectionManager.RoomConnectionRequested.Value` at line 52, but `ConnectionManager.Initialize()` doesn't run until `PostLoginSetup()`. Fixed with `?.` null-conditional.

3. **`Log.Info("Build ...")` ordering** (commit `a081f695`): `Log.logLevel` and `Log.enabledLogGroups` both default to `None`, which filters out ALL log messages. The `Log.Info("Build ...")` call was placed before config initialization, so it was silently discarded. Moved after config load — now appears in ADB.

### Build identification (commit `7b9d63ea`)

- `BuildInfo.generated.cs` injects git commit SHA at build time (via `build_unity.py --commit-sha`)
- `PlayerSettings.bundleVersion` is suffixed with SHA — visible in Android Settings > Apps
- `Debug.Log("[BuildInfo] ...")` fires before `Logger.Initialize()` — bypasses Serilog entirely

### Diagnostic instrumentation (commits `a081f695`, `9bca86c9`)

Added `[EnricherDiag]` logging throughout `SerilogStackTrace`, `BuildMethodName`, and `BuildTypeName` using `Logger.defaultUnityLogHandler` (bypasses Serilog to avoid recursion). Prints every nullable value before each dereference.

**Key finding from build `a081f695`:** The FIRST call to `SerilogStackTrace` completes successfully — all 15 stack frames processed, every value non-null. The SECOND call crashes (no diagnostics ran because `_diagDone` was already set).

Updated instrumentation in `9bca86c9` to run diagnostics on the first 3 calls instead of just the first, so the crashing second call will have diagnostics.

### Recursive call chain identified

The second `SerilogStackTrace` call is triggered by a recursive path:

1. `Log.Info("Build ...")` → Serilog → enricher → `SerilogStackTrace()` (first call, succeeds)
2. Unity sink writes via `defaultUnityLogHandler.LogFormat(LogType.Log, ...)`
3. `Application.logMessageReceived` fires → `UnityLogMessageReceived`
4. `UnityLogMessageReceived` maps `LogType.Log` → `Log.Warn(condition)` (re-enters Serilog)
5. Serilog enricher runs again → `SerilogStackTrace()` (second call, crashes)

The second call has a different stack trace (going through `UnityLogMessageReceived` → `Log.Warn`), which may contain frames that hit a null reflection value the first call's frames didn't.

## Next step

Deploy build from `9bca86c9` and check ADB for `[EnricherDiag]` output from the second `SerilogStackTrace` call. The last diagnostic line printed before the crash pinpoints the null value. Then apply the targeted fix.

## Key files

- `legacy/Outernet.Client/Assets/OuternetClient/Logging/Enricher.cs` — diagnostic instrumentation, two NRE fixes applied
- `legacy/Outernet.Client/Assets/OuternetClient/Logging/Logger.cs` — `UnityLogMessageReceived` recursive path
- `legacy/Outernet.Client/Assets/OuternetClient/Logging/UnityLoggerConfiguration.cs` — Unity sink (uses `defaultUnityLogHandler`, not `Debug.Log`)
- `legacy/Outernet.Client/Assets/OuternetClient/Logging/Log.cs` — `logLevel`/`stackTraceLevel` defaults to `None`
- `legacy/Outernet.Client/Assets/OuternetClient/AppSetup.cs` — build info logging, config init order

## Related tickets

- T99 — Burst native plugin missing (closed, benign debug logging)
- T96 — Cesium from-source (the fix that unblocked this error from surfacing)
