# Unity logging `LogType` mapping inconsistent between two paths

**Severity**: low/medium — log levels diverge depending on which path the message takes.

**Location**: `packages/unity/Logging/.../SerilogLogHandler.LogFormat` vs `Application.logMessageReceived` handler.

**Symptom**: A `Debug.Log(...)` call routed through `SerilogLogHandler.LogFormat` lands at one Serilog level. The same `Debug.Log(...)` observed via `Application.logMessageReceived` (e.g. for an exception that bypasses the handler) lands at a *different* level. Filters and dashboards based on `level` show different counts depending on which side you query.

**Mechanism**: Each path translates `UnityEngine.LogType` to Serilog's `LogEventLevel` independently. The two translation tables disagree on `LogType.Log` (one maps to `Information`, the other maps to `Debug`) and `LogType.Warning` (one normalizes, the other doesn't).

**Fix sketch**: Extract a single `static LogEventLevel ToSerilogLevel(LogType)` helper and have both paths call it. Pin the choice — `LogType.Log` → `Information` and `LogType.Warning` → `Warning` is the conventional mapping.

**Verification**: Emit one of each `LogType`; query Loki for the resulting level; assert each `LogType` produces exactly one level regardless of path.
