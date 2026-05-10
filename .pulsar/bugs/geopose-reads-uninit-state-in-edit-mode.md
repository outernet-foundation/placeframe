# `GeoPose` reads uninitialized `_state` in edit mode

**Severity**: low — works today by struct-default-zero accident; latent against any change to `FilterState` defaults.

**Location**: `packages/unity/Placeframe/.../VisualPositioningSystem.cs` (`_state` field) read by `GeoPose`.

**Symptom**: In edit mode, `Initialize` is never called, so `_state` is the default-constructed `FilterState`. `GeoPose` reads `_state.AlignmentCurrent` and computes an ECEF-from-Unity transform from it. Today this happens to produce the correct answer because `default(FilterState).AlignmentCurrent` is `quaternion.identity`, which under the diag(1, -1, 1) basis yields the ECEF-origin pose. Any future change to `FilterState`'s default — adding a non-identity default, switching to a class, initializing in the constructor — silently breaks edit-mode `GeoPose`.

**Mechanism**: There is no edit-mode initialization path for `_state`. The code relies on the default-struct semantics of `quaternion`, `float3`, etc., to align with the math of `GeoPose`'s formula. The coupling is invisible.

**Fix sketch**: In edit mode (or when `_state` is the default), make `GeoPose` either return a documented sentinel (e.g. `GeoPose.Origin`) or assert and throw. The intent should be explicit so a default-struct change can't silently shift the answer. Smallest version: a comment + `Assert(_state.AlignmentCurrent.value == quaternion.identity.value)` at the read point, so a future drift fires a clear assertion rather than miscomputing.

**Verification**: Mutate `FilterState`'s default `AlignmentCurrent` to a non-identity quaternion, run `GeoPose` in edit mode, assert it now fails loudly rather than silently miscomputing.
