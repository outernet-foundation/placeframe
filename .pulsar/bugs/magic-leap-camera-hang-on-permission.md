# MagicLeap `MagicLeapCamera.Start` hangs on permission denial

**Severity**: medium — unrecoverable hang; user-visible as "app frozen at startup."

**Location**: `packages/unity/Placeframe/.../MagicLeapCamera.cs` (or the equivalent in MakeItSing's `Plerion-MagicLeap`).

**Symptom**: If the camera permission is denied (user dismissed the prompt, or permission was previously revoked in OS settings), `MagicLeapCamera.Start` does not return. The app sits at whatever loading state called it. There is no error, no log, no fallback.

**Mechanism**: The permission request is fire-and-forget; the start path awaits the camera-ready callback unconditionally. Permission denial does not raise the callback, so the await never completes.

**Fix sketch**: Pair the permission request with a timeout (e.g. `WhenAny(cameraReady, Task.Delay(5000))`). On timeout or explicit denial, raise a typed `PermissionDeniedException` and surface it to the UI. Better still, request permission *before* starting the camera and bail early if denied.

**Verification**: On an ML2 with camera permission revoked, launch the app; assert the path exits within ~5s with a typed error rather than hanging.
