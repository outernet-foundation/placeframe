# `VisualPositioningSystem.Localize` setup failures routed through `LogDebug`

**Severity**: low/medium — operator-debuggability defect; "why isn't localization running?" with no error to grep for.

**Location**: `packages/unity/Placeframe/Assets/Package/Core/Runtime/VisualPositioningSystem.cs:218` — the `SelectMany` over camera frames installs `onErrorResume: exception => LogDebug(exception.Message)`.

**Symptom**: A setup-time failure inside `Localize` (e.g. "no localization maps loaded", auth not yet established, server-returned empty result on the very first call) is reported at `Debug` level, indistinguishable from the per-frame transient skips that are also routed through the same handler at 30 Hz. An operator looking at Loki for "why is this client not localizing?" sees nothing at Info or above and has to enable Debug-level capture to find the cause.

**Mechanism**: A single `onErrorResume` callback fan-ins both classes of failure (transient per-frame and structural-setup) and emits them all at the same level. The comment at lines 215-216 acknowledges the conflation but does not split the levels.

**Fix sketch**: Type-discriminate inside the handler — known transient classes (e.g. `LocalizeImageEmptyResponseException`, request-in-flight cancellations) stay at Debug, everything else escalates to Error (or Warn). Alternatively, classify at the throw site and let the handler trust the classification.

**Verification**: Trigger a setup failure (call `StartLocalizing` with no maps loaded) and assert an `Error`-level log line appears in Loki. Trigger a per-frame transient (briefly drop the server) and assert it stays at Debug.
