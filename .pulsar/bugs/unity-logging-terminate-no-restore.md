# Unity logging `Terminate` doesn't restore Unity log handler

**Severity**: low/medium — leaves Unity in a half-broken state on cleanup.

**Location**: `packages/unity/Logging/.../*.cs` — the `Terminate` path.

**Symptom**: After `Terminate`, `Debug.unityLogger.logHandler` is still the `SerilogLogHandler`, but the Serilog sink (the Loki sink, the unbounded queue) has been disposed. Subsequent Unity log calls flow into the dead handler and either drop silently or throw `ObjectDisposedException` depending on which Serilog component the call hits first.

**Mechanism**: `Initialize` saves the original handler; `Terminate` does not assign it back. The handler chain remains rooted at the dead `SerilogLogHandler`.

**Fix sketch**: In `Terminate`, before disposing Serilog, set `Debug.unityLogger.logHandler = _savedOriginalHandler`. Pair with the idempotence-on-Initialize fix so the saved handler is the truly-original one, not a chain of `SerilogLogHandler`s.

**Verification**: Call `Initialize` then `Terminate`; assert `Debug.unityLogger.logHandler` is the same instance as before `Initialize`. Call `Debug.Log("test")` after `Terminate`; assert no exception, line goes to the original handler.
