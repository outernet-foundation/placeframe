# `Auth` log fallback to `Console.WriteLine` is `/dev/null` on Android

**Severity**: low — silently lost auth diagnostics in production.

**Location**: `packages/unity/Placeframe/Assets/Package/Core/Runtime/Auth.cs:54-58` — `Info`, `Warn`, `Error` each fall back to `Console.WriteLine` when their respective log callback is null.

**Symptom**: A consumer that constructs `Auth` (directly or via `VisualPositioningSystem.Initialize`) without supplying log callbacks gets `Console.WriteLine` for every auth diagnostic — token refresh failures, expiry stamps, 401 responses. On Android (the primary deployment target) `Console.WriteLine` is not wired to `adb logcat` or Unity's log handler — it's effectively `/dev/null`. The auth path failures appear as silent login hangs.

**Mechanism**: `private static void Info(string message) => (LogInfo ?? Console.WriteLine).Invoke(message);` (lines 54, 56, 58). The null-fallback is a compile-time convenience that hides the contract requirement.

**Fix sketch**: Either (a) make the log-callback parameters required (throw if null in `Initialize`) so callers cannot accidentally drop logs, or (b) fall back to `UnityEngine.Debug.Log` / `Debug.LogWarning` / `Debug.LogError`, which on Android route through `logcat`. Option (b) preserves the convenience but produces output the operator can actually see.

**Verification**: Build the package into a consumer that omits log callbacks; trigger a token refresh failure on Android; assert the error appears in `adb logcat`.
