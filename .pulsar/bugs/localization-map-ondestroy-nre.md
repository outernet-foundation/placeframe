# `LocalizationMap.OnDestroy` NRE when destroyed before `Load`

**Severity**: low/medium — NRE in the editor, depending on platform may surface as a crash on device.

**Location**: `packages/unity/Placeframe/.../LocalizationMap.cs` — `OnDestroy`.

**Symptom**: A `LocalizationMap` Unity object that is destroyed before `Load` has been called throws `NullReferenceException` from `OnDestroy`. Triggering scenarios: scene unload during loading, destroying the GameObject in the editor before play mode, an early-failure path that destroys the map without ever loading it.

**Mechanism**: `OnDestroy` accesses fields populated only by `Load` (e.g. native handles, FAISS indices, or HDF5 readers) without null-checking them. Unity's lifecycle calls `OnDestroy` regardless of whether `Load` ever ran.

**Fix sketch**: Null-check each managed/native resource in `OnDestroy` before disposing. Or guard with a `_loaded` flag set at the end of `Load` and short-circuit `OnDestroy` if `!_loaded`.

**Verification**: Add a `LocalizationMap` GameObject to a scene, enter play mode, then exit immediately (before `Load` would have completed). Assert no NRE in the console.
