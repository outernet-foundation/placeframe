---
id: T76
title: Shared Unity build helpers package
status: design-needed
depends_on: [T7]
---

# T76: Shared Unity build helpers package

## Goal

Extract duplicated build report serialization and build execution helpers from per-project `BuildScript.cs` files into a shared Editor assembly in `packages/unity/Placeframe/`, so each project's BuildScript only contains project-specific configuration.

## Context

T7 introduced `apps/AndroidMobile/Assets/Editor/BuildScript.cs`, which duplicates ~60 lines of build report serialization code from `legacy/Outernet.Client/Assets/OuternetClient/Editor/BuildScript.cs` (`SerializableBuildReport`, `Step`, `Message` classes and `BuildStepTree()` method). As more Unity projects gain CI builds, this duplication will grow.

The Placeframe UPM package (`packages/unity/Placeframe/`) already has Editor assemblies (`Plerion.VPS.Editor`). A new Editor assembly for build tooling could live alongside these, or in a separate assembly to avoid coupling build infrastructure to the SDK.

## Key files

- `legacy/Outernet.Client/Assets/OuternetClient/Editor/BuildScript.cs` — existing build script with report serialization
- `apps/AndroidMobile/Assets/Editor/BuildScript.cs` — new build script with same report serialization
- `packages/unity/Placeframe/Assets/Package/Core/Editor/` — existing Editor assembly location in Placeframe package

## Done when

- Shared Editor assembly exists with build report serialization and a `RunBuild()` helper
- Both existing BuildScript.cs files use the shared helpers
- No duplicated build report code remains across projects
