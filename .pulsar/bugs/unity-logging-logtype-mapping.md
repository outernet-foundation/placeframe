# Unity logging `LogType` mapping inconsistent between two paths

**Severity**: low/medium — log levels diverge depending on which path the message takes.

**Location**: `packages/unity/Logging/Assets/Package/Runtime/Logger.cs` — `SerilogLogHandler.LogFormat` at lines 178-180 vs `UnityLogMessageReceived` (subscribed to `Application.logMessageReceived`) at lines 152-155.

**Symptom**: A `Debug.Log(...)` call routed through `SerilogLogHandler.LogFormat` lands at `Info`. The same `Debug.Log(...)` observed via `Application.logMessageReceived` (e.g. for an exception that bypasses the handler, or any log emitted when `emittingToUnity` was true and the SerilogLogHandler short-circuited) lands at `Warn`. Filters and dashboards based on `level` show different counts depending on which side observed the message.

**Mechanism**: Each path translates `UnityEngine.LogType` to a `Log<TLogGroup>` level call independently. `SerilogLogHandler.LogFormat` maps `LogType.Log → Info` (line 178-179). `UnityLogMessageReceived` collapses `LogType.Warning` and `LogType.Log` into the same `Warn` case (lines 152-154), so `LogType.Log → Warn` on this side.

**Fix sketch**: Extract a single `static void EmitToSerilog(LogType, string)` (or a `LogType → Log<>` level mapping helper) and have both paths call it. Pin the choice — `LogType.Log → Info` is the conventional mapping; the `logMessageReceived` collapse of Warning+Log into Warn is the side that needs to change.

**Verification**: Emit one of each `LogType`; query Loki for the resulting level; assert each `LogType` produces exactly one level regardless of path.
