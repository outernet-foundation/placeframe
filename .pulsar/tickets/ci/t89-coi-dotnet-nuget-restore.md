---
id: T89
title: Add dotnet SDK and NuGet restore to COI sandbox setup
status: plan-needed
depends_on: []
---

# T89: Add dotnet SDK and NuGet restore to COI sandbox setup

## Goal

Unity projects that use NuGetForUnity fail to compile on cold opens in the COI sandbox because the dotnet SDK is not installed and NuGet packages are not restored before Unity batchmode runs.

## Context

NuGetForUnity restores packages via an `[InitializeOnLoad]` editor script, but Unity aborts batchmode before editor scripts run if there are compilation errors. This creates a chicken-and-egg: R3.Unity needs R3.dll (from NuGet) to compile, but NuGetForUnity can't run until compilation succeeds.

CI solves this with an explicit pre-Unity step: `dotnet tool restore && dotnet nugetforunity restore <project>` (see `build-unity.yml` lines 136-139). The COI sandbox image (`.pulsar/coi-placeframe-build.sh`) installs Unity but not the dotnet SDK, so this step can't be replicated locally.

Discovered during T88 when `packages-lock.json` regeneration required manual dotnet installation.

## Key files

- `.pulsar/coi-placeframe-build.sh` — COI image build script, needs dotnet SDK install step
- `scripts/src/scripts/build_unity.py` — Unity build script, may need a NuGet restore pre-step for local runs

## Approach

Install dotnet SDK 8.0 in the COI image build script. Add a NuGet restore step (using `dotnet nugetforunity restore`) that runs before Unity batchmode in the build-unity script or as sandbox documentation.

## Done when

- `.pulsar/coi-placeframe-build.sh` installs dotnet SDK 8.0
- Cold Unity batchmode opens succeed in a fresh COI container without manual intervention
- `dotnet tool restore && dotnet nugetforunity restore <project>` works out of the box
