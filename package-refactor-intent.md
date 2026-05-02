# Placeframe .NET Package Refactor — Intent

> Execution and progress tracked in [`vps-redesign-plan.md`](vps-redesign-plan.md), Phase 2.

## Status

Design intent. Going-for-broke version: separate concerns cleanly so the Unity package is the thin Unity-specific shell over a body of cross-platform .NET libraries that do the actual work.

## Context

### Where the code lives now

All C# code in this repo lives under `packages/unity/Placeframe/Assets/Package/Core/`, compiled as the `Placeframe.Core` Unity assembly. That single assembly contains:

- Mathematical primitives (`Double4x4`, `LocationUtilities`, basis-change matrices).
- Domain types (`GeoPose`).
- Business logic (`Auth`, `VisualPositioningSystem` — including the localization HTTP request, response parsing, and Bayesian filter math added in VPS Phase 1).
- Unity-specific glue (MonoBehaviours, ARFoundation integration, R3 main-thread marshaling, the `Update()` slew loop).

Everything compiles as one Unity assembly with implicit dependencies on `UnityEngine`, `Unity.Mathematics`, `R3`, `UniTask`, `PlaceframeApiClient`, etc.

### Why this needs to change

The current monolith has three concrete problems:

- **Testability.** No tests exist for any of this code. Setting up Unity's test runner is feasible but high-friction (custom asmdef, NUnit references, iteration via Unity's editor). The math (especially Phase 1's SE(3) Log/Exp + Bayesian filter) is naturally pure-functional and trivially TDD-able outside Unity, but the current arrangement forces it into a test-hostile environment.
- **Coupling.** Code that doesn't need Unity (math, HTTP/auth, parsing) is mixed in with code that fundamentally does. A future non-Unity consumer (CLI tool, headless integration test harness, web client) cannot reuse the cross-platform parts.
- **Module clarity.** Reading the Unity package, it isn't obvious which files are about Unity-specific concerns vs general-purpose logic. A clean split makes the architecture self-documenting.

### Design goals

In priority order:

1. **Cross-platform math and business logic are testable in plain `dotnet test`.** No Unity install required; full TDD loop available.
2. **Cross-platform code is reusable.** Any .NET consumer can take a dependency on the math or business-logic packages without dragging in Unity.
3. **The Unity package is a thin shell.** It contains the things that *fundamentally* need Unity: MonoBehaviours, the `Update()` slew loop, ARFoundation glue, scene/prefab integration, R3-Unity main-thread marshaling.
4. **Distribution is automated long-term.** Initial ship via DLL-drop into Unity's `Plugins/` folder. Eventual ship as versioned NuGet packages published from CI, consumed by Unity via NuGetForUnity (matching the existing pattern for R3, Polly, etc.).

### Design non-goals

- **Removing Unity from the project.** Unity is the rendering and scene-integration layer. The whole point is a clean line between "Unity stuff" and "everything else," not removal of either side.
- **Shipping the .NET packages externally to third parties.** They're internal-use. The distribution-via-CI work is to make our own consumption smoother, not for public release.
- **Restructuring the Python side.** Out of scope — the Python services (`api`, `localizer`, etc.) are already cleanly separated from the C# side.

---

## Architectural overview

```
┌─────────────────────────────────────────────────────────┐
│ Unity package (Placeframe.Core asmdef)                  │
│                                                          │
│   MonoBehaviours: GeoPose, LocalizationMap, ...         │
│   VisualPositioningSystem (R3 marshaling, Update() slew)│
│   ARFoundation glue                                      │
│   Camera/capture providers                               │
│                                                          │
│   ▲ references                                           │
└───┼──────────────────────────────────────────────────────┘
    │
    ├──► Placeframe.Core.dll (cross-platform)
    │      Auth, HTTP-side localization, business logic
    │
    └──► Placeframe.Math.dll (cross-platform)
           SE(3) Log/Exp, BayesianAlignmentFilter,
           Double4x4, LocationUtilities
```

Both `.dll`s built from `packages/csharp/` projects. Unity consumes them as precompiled references (initially DLL-drop; eventually NuGet).

---

## Package boundaries

### `Placeframe.Math` (target: `netstandard2.1`)

**Dependencies**: `MathNet.Numerics`, `Unity.Mathematics`, BCL.

**Contains** (moved from Unity package):
- `Double4x4` static class (`FromTranslationRotation*`, `Decompose`, `Interpolate`).
- `LocationUtilities` — basis-change matrices, `UnityFromEcef` / `EcefFromUnity`.
- The math half of `ExtensionMethods` (`ToDouble3x3`, `ToQuaternion`, `ToFloats`, `Position`, `RotationQuaternion`, `RotationMatrix`).

**Contains** (new, written in VPS Phase 1 and migrated here):
- `Se3.Log(double4x4)` / `Se3.Exp(Vector<double>)`.
- 6×6 algebra (likely thin wrappers around `MathNet.Numerics.LinearAlgebra.Matrix<double>`).
- `BayesianAlignmentFilter` — pure-functional measurement processing (innovation gate, Bayesian update, snap-vs-slew decision).

### `Placeframe.Math.Tests` (target: `net8.0`)

**Dependencies**: `Placeframe.Math`, `NUnit`, `NUnit3TestAdapter`.

NUnit chosen for consistency with Unity's test runner — reduces the cognitive load if/when Unity-side integration tests get added.

### `Placeframe.Core` (target: `netstandard2.1`)

**Dependencies**: `PlaceframeApiClient` (generated), `System.Net.Http`, `Polly`, `R3` (core, not `R3.Unity`), `Placeframe.Math`, BCL.

**Contains** (moved from Unity package):
- `Auth` — JWT token acquisition, refresh, attachment to `HttpClient`.
- The HTTP-side of localization — request assembly, response parsing, basis transformation. Returns a strongly-typed result that the Unity layer feeds into the Bayesian filter.

**Excludes**: anything that needs `UnityEngine`, ARFoundation, `MonoBehaviour`, or the Unity-specific scheduling APIs (`UniTask.SwitchToMainThread`, R3-Unity providers).

### `Placeframe.Core.Tests` (target: `net8.0`)

NUnit. Covers Auth flows, HTTP handler shaping, parsing edge cases.

### Unity package (unchanged location, slimmed contents)

**Stays**:
- `VisualPositioningSystem` shell — subscribes to localization observable, marshals to main thread (R3-Unity), feeds measurements to `BayesianAlignmentFilter`, applies result to `_unityFromEcefTransform_*`, drives the slew loop in `Update()`, fires events.
- `GeoPose` MonoBehaviour.
- `LocalizationMap` / `LocalizationMapManager` — Unity rendering of map point clouds.
- `CaptureManager` and `ICameraProvider` implementations (`CameraProvider` for ARFoundation, `MagicLeapCameraProvider`).
- Inspectors, scene/prefab integration.
- The API-client conversion half of `ExtensionMethods` — `ToDouble3(Float3)`, `ToMathematicsQuaternion(Float4)`. These convert generated-client model types into Unity types and only matter in the Unity layer.

---

## Distribution

### Initial: DLL-drop

A new `uv run` script (e.g., `uv run build-dotnet-packages`) does:

1. `dotnet build` each project under `packages/csharp/`.
2. Copy the resulting `Placeframe.Math.dll`, `Placeframe.Core.dll`, and any direct dependencies (`MathNet.Numerics.dll`) into `packages/unity/Placeframe/Assets/Plugins/`.
3. Unity sees the precompiled DLLs and the asmdef references them via `precompiledReferences`.

Manual rebuild after C# changes. Acceptable while ergonomics aren't biting.

### Future: NuGet via CI

The repo already has a CI pipeline that pushes artifacts to NuGet. The end-state distribution:

1. `Placeframe.Math` and `Placeframe.Core` are versioned `.nupkg`s, published from CI on tagged releases.
2. Unity consumes them via NuGetForUnity (matching the R3 / Polly / SharpZipLib pattern already in `packages.config`).
3. No manual DLL copying; updates are just `packages.config` version bumps.

Migration trigger: when manual DLL-drop ergonomics start biting (e.g., multiple consumers of the packages, or coordination across collaborators). Probably soon after the refactor lands.

---

## Failure modes

| Condition | Behavior |
|---|---|
| `Placeframe.Math.dll` missing from `Plugins/` | Unity build fails loudly with unresolved type errors. Fix: run the build script. |
| Version mismatch between built DLL and Unity asmdef references | Same: build error at Unity import time. |
| MathNet's `Matrix<double>` allocation overhead becomes a perf issue | Address by introducing fixed-size struct types in `Placeframe.Math` later. Not expected at ~1Hz. |

---

## Risks and unknowns

- **Build-step ergonomics.** DLL-drop requires a manual rebuild after `dotnet build`. Easy to forget. Mitigation: integrate into the existing `uv run build` flow, or add a pre-commit hook. Move to NuGet/CI as soon as it bites.
- **Unity.Mathematics NuGet version drift.** The `Unity.Mathematics` NuGet package is published by Unity Technologies but may lag the version Unity itself ships. Mitigation: pin to a specific version in both `Placeframe.Math.csproj` and Unity's package manifest; update in lockstep when Unity is upgraded.
- **Namespace-change blast radius.** Moving types out of `Placeframe.Core` into `Placeframe.Math` / new `Placeframe.Core` (cross-platform) requires updating `using` statements across the Unity codebase. Mechanical but touches many files. Mitigation: do it once, atomically, in the refactor commit(s).
- **Test framework drift.** Unity's test runner uses NUnit; choosing NUnit for the standalone tests keeps skills aligned. Risk: if/when Unity adopts a different test framework, two test stacks would diverge. Low probability, easy to migrate.
