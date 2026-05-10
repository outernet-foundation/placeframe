# Unity logging `Initialize` is implicitly single-shot

**Severity**: medium — re-init creates a Serilog→Unity→Serilog feedback loop.

**Location**: `packages/unity/Logging/.../*.cs` — the `Initialize` and `SerilogLogHandler` paths.

**Symptom**: Calling `Initialize` a second time (e.g. on scene reload, on re-login, on test setup) wires the previously-installed Serilog handler back into Unity's `Debug.unityLogger.logHandler`, which is already pointing at Serilog. Each Unity log message then ping-pongs between the two until stack overflow or queue saturation. Symptom in production is a sudden flood of identical log lines and an eventual crash.

**Mechanism**: `Initialize` saves the current `unityLogger.logHandler` and replaces it with a `SerilogLogHandler` that forwards to the saved handler in addition to Serilog. On re-init, the "saved" handler captured is the *previously-installed `SerilogLogHandler`*. The new handler forwards to that handler, which forwards to Serilog, which forwards back to Unity through the new top-level handler — infinite cycle (kept under control today only by the `[ThreadStatic] emittingToUnity` guard, which catches the immediate re-entry but not the deferred-via-task-scheduler version).

**Fix sketch**: Guard `Initialize` with an idempotence check: if a `SerilogLogHandler` is already installed, no-op (or log a warning and skip). Symmetric `Terminate` should restore the *original* (pre-first-Initialize) handler, not just the most recently saved one.

**Verification**: Call `Initialize` twice in the editor; assert `Debug.unityLogger.logHandler` is still a `SerilogLogHandler` pointing at the original Unity handler, not at another `SerilogLogHandler`.
