---
id: T92
title: Integrate AltTester for Unity end-to-end testing
status: design-needed
depends_on: []
---

# T92: Integrate AltTester for Unity end-to-end testing

## Goal

Add AltTester to the Unity projects so that automated end-to-end tests can drive a running build over the network — verifying UI flows, localization triggers, and scene transitions without manual QA.

## Context

The repo has four Unity projects (Placeframe package, Outernet.Client, AndroidMobile, MapRegistrationTool) all on Unity 6000.0.66f1. The Unity Test Framework (`com.unity.test-framework` 1.6.0) is installed in every project but no tests exist — no test assemblies, no test scripts.

AltTester is an open-source (LGPL-2.1) UI-driven test automation tool for Unity. It instruments a build via an embedded SDK (the "AltTester Unity Package"), then an external driver (Python, C#, or Java) connects over WebSocket to send commands (find object, tap, swipe, wait-for, assert). This decoupled architecture means tests run against a real build, not inside the editor — closer to what users actually experience. It's the closest thing to Playwright that exists for Unity.

Key architectural decisions to make:
- **Which project(s) to instrument first.** The Placeframe package is shared code; the apps are where user-facing flows live. Starting with one app (likely Outernet.Client since it has the most platforms and complexity) is pragmatic.
- **Test driver language.** Python (via `alttester` pip package) fits the existing repo tooling (uv, pytest). C# via NUnit is also an option but adds a separate test project outside the Unity editor.
- **Instrumentation toggle.** AltTester's SDK must be stripped from release builds (it opens a WebSocket server). Need a scripting define or build configuration to include it only in test builds.
- **CI execution.** Running AltTester tests in CI requires a headed or virtual-display Unity build plus the test driver. The existing `build-unity.yml` workflow (T7) runs in GameCI containers with `xvfb` — need to determine if a built player can run under xvfb in the same container, or if a separate test job is needed.

## Key files

- `packages/unity/Placeframe/Packages/manifest.json` — package dependencies for the Placeframe Unity project
- `legacy/Outernet.Client/Packages/manifest.json` — package dependencies for Outernet.Client
- `apps/AndroidMobile/Packages/manifest.json` — package dependencies for AndroidMobile
- `apps/MapRegistrationTool/Packages/manifest.json` — package dependencies for MapRegistrationTool
- `.github/workflows/build-unity.yml` — existing Unity CI workflow (T7)
- `scripts/src/scripts/build_unity.py` — Unity build script
- `packages/unity/Placeframe/Assets/Package/Core/Runtime/Plerion.VPS.asmdef` — core runtime assembly definition

## Approach

TBD — pending design decisions above.

## Done when

**Verifiable now:**
- AltTester Unity package is added to at least one project's `manifest.json`
- A test assembly definition exists with AltTester references
- At least one smoke test exists (Python or C#) that connects to an instrumented build, finds a GameObject, and asserts on it
- Instrumentation is gated behind a scripting define so it can be stripped from release builds

**Requires manual verification:**
- An instrumented build launches and accepts AltTester driver connections
- The smoke test passes against the running build
- A non-instrumented (release) build does not include the AltTester SDK

## Next step

Decide on: (1) which Unity project to instrument first, (2) Python vs C# for the test driver, (3) how to gate instrumentation (scripting define vs build config), and (4) whether CI tests run in the same job as builds or a separate job. A `/research` pass on AltTester's Unity 6 compatibility and UPM installation method would be valuable — the docs may have changed since the 2.x release.
