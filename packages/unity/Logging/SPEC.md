# Logging Package

## What This Is

A shared Unity package (`packages/unity/Logging`) that extracts the Serilog + Grafana Loki logging infrastructure from `legacy/Outernet.Client/Assets/OuternetClient/Logging/` into a reusable package. The immediate consumer is `apps/AndroidMobile` (the capture tool), so its logs reach Grafana.

## Why a Unity Package (Not a NuGet Package)

The logging stack touches Unity APIs in most files:

- **Logger.cs** — intercepts `Debug.unityLogger.logHandler`, subscribes to `Application.logMessageReceived`, calls `Application.SetStackTraceLogType`, reads `SystemInfo.deviceName`.
- **UnityLoggerConfiguration.cs** — `ILogEventSink` that emits to `Debug.unityLogger.logHandler.LogFormat`.
- **Enricher.cs** — uses `Application.dataPath` for relative stack trace paths.
- **LokiLoggerConfiguration.cs** — uses `#if UNITY_EDITOR` / platform preprocessor directives for Loki labels.

Only `Log.cs`, `JTokenFromSerilogProperty.cs`, and `InnerFramesHiddenFromStackTraceAttribute.cs` are pure .NET. A NuGet package would require abstracting every Unity touchpoint behind interfaces (`IDeviceInfo`, `IPlatformSink`, etc.) — over-engineered given every consumer is a Unity app.

## Source Material

Seven files from `legacy/Outernet.Client/Assets/OuternetClient/Logging/`:

| File | Unity-dependent | Role |
|---|---|---|
| `Logger.cs` | Yes | Lifecycle: init Serilog, intercept Unity logs, hook UniTask/Task/R3 exceptions |
| `Log.cs` | No | Static API (`Log.Info(...)` etc.), `LogLevel` enum, `LogGroup` flags enum, `ILoggerFactory` adapter |
| `Enricher.cs` | Yes (`Application.dataPath`) | Serilog enricher: stack traces, device info, HTTP error details |
| `LokiLoggerConfiguration.cs` | Yes (preprocessor) | Serilog → Loki sink with authenticated HTTP client |
| `UnityLoggerConfiguration.cs` | Yes | Serilog → Unity console sink |
| `JTokenFromSerilogProperty.cs` | No | JSON serialization helper for Serilog properties |
| `InnerFramesHiddenFromStackTraceAttribute.cs` | No | Marker attribute for stack trace filtering |

**Not included:** `UnityMainThreadDispatcher` is defined in `LokiLoggerConfiguration.cs` but is only consumed by `App.cs` (not the logging system). It belongs in the app, not the package.

## Package Structure

Follows the same pattern as the existing Placeframe package (`packages/unity/Placeframe/Assets/Package/Core/`):

```
packages/unity/Logging/
├── SPEC.md
└── Assets/
    └── Package/
        ├── package.json          # org.outernet.logging, file-referenced from app manifests
        └── Runtime/
            ├── Outernet.Logging.asmdef
            ├── Log.cs
            ├── Logger.cs
            ├── Enricher.cs
            ├── LokiLoggerConfiguration.cs
            ├── UnityLoggerConfiguration.cs
            ├── JTokenFromSerilogProperty.cs
            └── InnerFramesHiddenFromStackTraceAttribute.cs
```

Apps reference via `manifest.json`:
```json
"org.outernet.logging": "file:../../../packages/unity/Logging/Assets/Package"
```

### NuGet Dependencies

NuGet packages are managed via **NuGetForUnity** (`packages.config` + `NuGet.config` per app). The logging package itself cannot declare NuGet dependencies — each consuming app must add the required NuGet packages to its own `packages.config`:

- `Serilog` (4.0.1)
- `Serilog.Sinks.Grafana.Loki` (8.3.0)
- `Newtonsoft.Json` (13.0.3) — likely already present
- `Microsoft.Extensions.Logging.Abstractions` (8.0.0)

The legacy Outernet.Client already has all of these. AndroidMobile currently has only `Newtonsoft.Json` — the others must be added.

The `package.json` should document the required NuGet dependencies so consumers know what to add.

## Design Decisions

### Generic log groups via type parameter

Each app defines its own `LogGroup` flags enum. The package makes this generic:

```csharp
public static class Log<TLogGroup> where TLogGroup : struct, Enum
```

The bitwise flags check (`(group & enabledLogGroups) == 0`) doesn't work directly on generic `Enum`. Use `Unsafe.As<TLogGroup, int>` for zero-alloc casting — works under IL2CPP.

Each app defines and passes its own enum:
```csharp
[Flags]
public enum LogGroup { None = 0, Default = 1 << 0, UncaughtException = 1 << 1, Capture = 1 << 2 }
```

### Color palette via attribute

Each app's `LogGroup` enum values carry their console color as an attribute:

```csharp
[AttributeUsage(AttributeTargets.Field)]
public class LogGroupColorAttribute : Attribute
{
    public string HexColor { get; }
    public LogGroupColorAttribute(string hexColor) => HexColor = hexColor;
}

// In the app:
[Flags]
public enum LogGroup
{
    None = 0,
    [LogGroupColor("#4E79A7")] Default = 1 << 0,
    [LogGroupColor("#E15759")] UncaughtException = 1 << 1,
    [LogGroupColor("#59A14F")] Capture = 1 << 2,
}
```

The `UnityDebugSink` reads these via reflection (cached once at startup).

### Log level configuration

No `UnityEnv` ScriptableObject. The package hardcodes the defaults that `UnityEnv` was providing:

- `logLevel` = `LogLevel.Info`
- `stackTraceLevel` = `LogLevel.Warn`
- `enabledLogGroups` = all groups enabled (`~0` / all bits set)

These are mutable static fields on `Log<TLogGroup>`, so apps can override them at startup if needed.

### Pluggable auth for Loki

The legacy code hardcodes `Auth.GetOrRefreshToken()` (Keycloak). The package accepts a `Func<Task<string>>` token provider instead:

```csharp
Logger<TLogGroup>.EnableLoki(domain, tokenProvider: () => Auth.GetOrRefreshToken());
```

### Pluggable Loki labels

Platform labels (`app`, `platform`) are currently hardcoded with preprocessor directives. The package accepts labels as a parameter to `EnableLoki()` so each app can supply its own.

### Benign error suppression

`Logger.cs` has a `SuppressBenignErrors` method that downgrades specific native errors (Magic Leap pose-not-found, ARCore GL_INVALID_ENUM, etc.). These are app-specific. The package accepts an optional `Func<LogType, string, LogType>` at initialization that apps can use to reclassify log messages:

```csharp
Logger<LogGroup>.Initialize(suppressErrors: (type, message) =>
{
    if (type == LogType.Error && message.Contains("GL_INVALID_ENUM"))
        return LogType.Log;
    return type;
});
```

If not provided, no suppression occurs.

### Enricher extensibility

Two app-specific references in the legacy Enricher must not leak into the package:

- **`ConnectionManager.RoomConnectionRequested`** (room context) — becomes an optional `Func<string?>` callback on the enricher, or omitted entirely.
- **`WebRequestException` / `ResponseDeserializationException`** (HTTP error details) — the enricher sniffs these for status codes and response bodies. Becomes an optional enrichment hook, e.g. `Action<Exception, IDictionary<string, object>>`.

### Static API surface

The full set of ~40 method overloads from the legacy `Log.cs` is preserved. Every combination of level × with/without group × with/without exception × with/without message template is included so call sites don't need to change their patterns.
