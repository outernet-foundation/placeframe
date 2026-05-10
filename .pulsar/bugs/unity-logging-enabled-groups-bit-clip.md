# Unity logging `enabledLogGroups = ~0` clips for non-int enums

**Severity**: low — works today by accident; breaks the moment the enum widens.

**Location**: `packages/unity/Logging/.../*.cs` — the `enabledLogGroups = ~0` initialization.

**Symptom**: Today the `LogGroups` enum fits in 32 bits and `~0` (signed-int all-ones) covers every value. The moment a future contributor adds a 33rd flag, or marks the enum as `: long`, `~0` will silently clip the high bits and that group won't be enabled by default. The miss is invisible — no compile error, just "logs from group X are missing."

**Mechanism**: `~0` is `int.MaxValue.Negate()`-style — a 32-bit pattern. C# converts it to the enum's underlying type via implicit cast; for `long`-backed enums, the high 32 bits become zero.

**Fix sketch**: Use `enabledLogGroups = (LogGroups)(~0L)` if the underlying type is `long`, or better, `enabledLogGroups = (LogGroups)~0` cast through the actual underlying type via `Enum.GetUnderlyingType` — but the simplest fix is `enabledLogGroups = (LogGroups)(-1)` and ensure the enum is `[Flags]` with the right backing.

**Verification**: Add a hypothetical 33rd flag (in a test) and assert it's enabled by default with the chosen pattern.
