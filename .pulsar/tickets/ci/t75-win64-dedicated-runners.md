---
id: T75
title: "Win64 CI: enable IL2CPP builds"
status: design-needed
depends_on: [T7]
---

# T75: Win64 CI: enable IL2CPP builds

## Goal

Enable the two commented-out win64 builds (Outernet.Client, MapRegistrationTool) in `build-unity.yml` using IL2CPP scripting backend.

## Context

T7 implements the Unity CI workflow with all 7 builds running on Linux using GameCI Docker images. The two win64 builds are commented out because IL2CPP for Windows cannot be cross-compiled from Linux — there is no `windows-il2cpp` module for the Linux Unity editor. Only `windows-mono` exists, and the projects require IL2CPP. A Windows environment is strictly required.

Additionally, IL2CPP on Windows requires MSVC (`cl.exe` from Visual Studio Build Tools). This is a Unity-specific requirement — other C++ compilers (MinGW, Clang) are not supported. Microsoft's licensing prohibits *publicly* redistributing VS Build Tools inside Docker images — but building private images with VS Build Tools installed is explicitly supported and documented by Microsoft ([Install VS Build Tools into a container](https://learn.microsoft.com/en-us/visualstudio/install/build-tools-container?view=vs-2022)). This is why GameCI can't include them in their public images, but we can build our own private image.

Our current workflow uses only GameCI's Docker images (not their GitHub Actions). Activation, build, and license return are handled directly via `unity-editor` CLI and `uv run build-unity`.

## Key files

- `.github/workflows/unity.yml` — add win64 builds
- `scripts/src/scripts/build_unity.py` — may need path adjustments for Windows Unity install location

## Research

- `.pulsar/research/unity-ci-licensing.md` — licensing seat analysis: why Linux parallel builds work (hardcoded `machine-id`), why Windows is different, machine fingerprinting on Windows, HardwareId test proposal
- `.pulsar/research/win64-il2cpp-ci-approaches.md` — cross-compilation infeasibility, MSVC requirement, evaluation of all approaches (serialize + native install, Windows Docker, self-hosted runner, managed runners, skip)
- `.pulsar/research/win64-container-feasibility.md` — hosted vs self-hosted runners for Windows containers, GameCI Windows image architecture, VS Build Tools in containers, vswhere discovery risk, hosting cost comparison
- `.pulsar/research/win64-container-machine-identity.md` — Unity licensing bindings on Windows, registry hive isolation in containers, fixed-MAC approach (the Windows equivalent of Linux's hardcoded `machine-id`), empirical test protocol, ~75% confidence assessment

### Licensing situation

Unity Personal allows 2 activation seats. Current usage: 1 seat for the dev machine, 1 seat for all Linux CI (GameCI containers share a hardcoded `/etc/machine-id`, so Unity sees them as one machine). Windows builds must share the remaining seat, which means all of CI (Linux + Windows) shares 1 seat. Windows builds must run after Linux builds finish, not just after each other. Concurrent workflows (push to main + dev simultaneously) also need coordination — a GitHub `concurrency` group would queue Windows activation across workflows.

If a runner crashes mid-build, the license isn't returned (recoverable via Unity ID portal, but manual).

### Approaches evaluated

| Approach | Install overhead | Licensing | Cost | Risk |
|---|---|---|---|---|
| **Serialize + native install** | 10-20 min cold, 3-8 min cached (5-7 GB eats most of 10 GB cache budget) | Serialize all Windows after Linux + concurrency group across workflows | $0 | Low — slow but reliable |
| ~~**Windows Docker + VS mount**~~ | None (Unity in image) | Custom image could hardcode identity (partial — registry yes, SMBIOS no) | $0 | High — VS mount fragile, DNS/IPC issues reported |
| **Private Windows Docker image (Unity + VS Build Tools baked in)** | None (everything in image) | Custom image can hardcode registry-based identity; SMBIOS still uncontrolled | $0 | Medium — needs research on Windows container support on `windows-latest` |
| **Self-hosted runner** | None (permanent install) | 1 consistent seat | $0 + hardware | Medium — maintenance burden |
| **Managed runners (Buildalon)** | None (persistent VMs) | Handled | $40-180/mo | Medium — single-person project, governance risk |
| **GitHub custom images** | None (baked in) | Depends on approach | Requires Team/Enterprise plan | Low-Medium |
| **Mono backend for win64** | None (cross-compiles from Linux GameCI) | Same as Linux (shared `machine-id`) | $0 | Low — no documented Mono issues for win64; projects just have IL2CPP set in PlayerSettings |
| **Skip win64 CI** | N/A | N/A | $0 | Accept the gap |

### Untested assumption: shared HardwareId on `windows-latest`

If GitHub's hosted Windows runners share the same machine identity signals that Unity licensing checks (likely the Windows Product ID), then native-runner activation would consume only 1 seat — the same trick that works on Linux, but via Azure's VM provisioning rather than a hardcoded container ID. This would make serialization simpler (no cross-workflow seat conflicts, parallel Windows builds safe). A test workflow dumping WMI values across parallel jobs would confirm or rule this out. See licensing research doc section 5 for the proposed test.

## Approach

Self-hosted Windows runner (office desktop) running a private Docker image (GameCI Windows base + VS Build Tools, pushed to GHCR). Two go/no-go tests gate the approach. Fallback decision tree:

1. **Primary**: Self-hosted runner + private Docker image with fixed-MAC licensing
2. **If fixed-MAC licensing fails** (go/no-go test 1): Same self-hosted runner, but native Unity install (no containers). Consistent machine identity by definition. Simpler but less reproducible.
3. **If IL2CPP-in-container fails** (go/no-go test 2): Same fallback — native install on the self-hosted runner.
4. **If self-hosted proves too burdensome operationally**: Native Unity install + `actions/cache` on GitHub-hosted `windows-latest`. Slower (3-8 min cached install, 2 vCPUs) but zero infrastructure.

All fallbacks produce working win64 IL2CPP builds. The decision tree trades reproducibility and speed for simplicity at each step.

## Design decisions

1. **Two separate jobs** (not conditional matrix). The `build-linux` job uses GameCI Linux containers; `build-windows` uses a self-hosted Windows runner. Clean separation, no conditional YAML.
2. ~~**GameCI `windows-il2cpp` containers**~~ — Withdrawn as a standalone approach. GameCI Windows Docker containers require mounting VS Build Tools from the host (fragile path coupling) and don't hardcode machine-id. However, GameCI's Windows images are still useful as a **base layer** — they have Unity pre-installed with the Server Core DLL fixes. Our private image builds on top of them.
3. **VS Build Tools licensing is not a blocker for private images.** Microsoft's restriction is on *public redistribution* only. Building a private Docker image with VS Build Tools baked in for your own CI is explicitly supported ([MS docs](https://learn.microsoft.com/en-us/visualstudio/install/build-tools-container?view=vs-2022)). This reopens the containerized Windows build approach — build our own image with Unity + VS Build Tools, push to a private registry (GHCR).
4. **Self-hosted runner + private Docker image.** GitHub-hosted `windows-latest` is not viable for containerized builds: no persistent Docker layer cache (25-40 min pull every run), only 33 GB disk (WS2025), and 2 vCPUs (too slow for IL2CPP compilation). A self-hosted Windows runner solves all three: Docker cache persists between runs, disk/CPU are user-controlled. The private image (Unity + VS Build Tools baked in) on GHCR gives the same container reproducibility as the Linux GameCI approach.
5. **Hosted runners rejected for containers, not for native install.** The research showed that native Unity install + `actions/cache` on `windows-latest` (Option B) is viable as a fallback if self-hosted proves too burdensome. But containers on hosted runners are economically backwards — pull time exceeds native install time.
6. **Public repo = no GitHub platform fee.** Self-hosted runner usage on public repos remains free (no $0.002/min orchestration charge introduced March 2026).
7. **Licensing via fixed MAC address (not acquire/return).** Windows containers from the same image already share a fixed Product ID (Unity binding 1) via the base registry hive. The variable element is the MAC address (binding 5) — Docker assigns a random MAC each run. Fix with `docker run --mac-address=XX:XX:XX:XX:XX:XX`. This is the Windows equivalent of GameCI's Linux `machine-id` hardcoding. Untested by the community but technically sound. Fallback if this doesn't work: native install on the self-hosted runner (no containers), which has a consistent machine identity by definition.
8. **Layer on GameCI's Windows image.** Start `FROM unityci/editor:windows-...-windows-il2cpp-...`, add VS Build Tools via Chocolatey. Reuses their proven Unity installation and DLL fixes. Exact image tag needs verification.

## Next step

**Two go/no-go tests on the office desktop (dual-boot Windows), then plan.** The entire self-hosted container approach hinges on two empirical tests. If either fails, fall back to native install on the self-hosted runner (no containers). Everything else is implementation work with known solutions.

**Go/no-go test 1: Fixed-MAC licensing (~10 min).** Pull a GameCI Windows image, activate Unity inside a container with `--mac-address=02:42:ac:11:00:02`, stop the container, start a new container with the same MAC, check if the license is still valid without re-activation. Confirms or kills design decision 7.

**Go/no-go test 2: IL2CPP build end-to-end in a container (~1-2 hrs first time).** Build a private image (GameCI Windows base + VS Build Tools via Chocolatey), run a win64 IL2CPP build for Outernet.Client inside it. This confirms Unity finds MSVC (`cl.exe`) via vswhere and that IL2CPP compilation works under process isolation. Implicitly tests vswhere discovery — if the build succeeds, Unity found the compiler.

Prep steps before test 2:
1. Verify GameCI Windows image tag on Docker Hub for Unity 6000.0.66f1
2. Write Dockerfile layering VS Build Tools on GameCI's image, build locally, push to GHCR

After both tests pass, plan the runner provisioning and workflow changes.

## Scope note

**T93 provides interim win64 CI coverage using Mono cross-compilation from Linux.** This ticket (T75) remains for IL2CPP builds, which require a Windows environment with MSVC. T93's Mono builds catch C# compilation and reference errors but not IL2CPP-specific issues (AOT failures, stripping).

**T96 (Cesium native builds) no longer depends on this ticket.** T96's Windows native build (CMake + MSVC) runs on `windows-latest` GitHub-hosted — no Unity license needed for CMake compilation, no self-hosted runner needed. Windows codegen runs from Linux via GameCI's `windows-mono` container image. This ticket is only needed for IL2CPP Unity player builds.

## Done when

- win64 matrix entries build successfully with IL2CPP scripting backend
- Windows builds run on a Windows environment (runner or container)
- All other builds remain unchanged on Linux/GameCI
