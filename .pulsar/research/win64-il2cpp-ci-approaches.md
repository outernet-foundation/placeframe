# Win64 IL2CPP CI: Approach Feasibility

Research conducted 2026-03-04. Context: T75 needs Windows IL2CPP builds in CI. This doc covers cross-compilation feasibility, the Windows CI tooling landscape, and trade-offs of each approach.

See also: `.pulsar/research/unity-ci-licensing.md` for licensing/seat analysis.

## Cross-compilation is not possible

Unity does not support cross-compiling IL2CPP for Windows from Linux. This is definitively confirmed by Unity docs, GameCI maintainers, and community experience.

The cross-compilation support matrix for IL2CPP desktop builds:

| Build target | From Windows | From macOS | From Linux |
|---|---|---|---|
| Linux IL2CPP | Supported (via toolchain package) | Supported (via toolchain package) | Native |
| Windows IL2CPP | Native | **Not supported** | **Not supported** |
| macOS IL2CPP | Not supported | Native | Not supported |

Mobile IL2CPP (Android, iOS) can be built from any host. The restriction is desktop-only.

There is no `windows-il2cpp` module for the Linux Unity editor. The only Windows build module available on Linux is `windows-mono`, which uses the Mono scripting backend — not IL2CPP. The existing commented-out entries in `unity.yml` used `windows-mono` and were disabled because the projects require IL2CPP.

Unity 6 has not changed this. No new cross-compilation targets were added.

Sources:
- [Unity Manual: Linux IL2CPP cross-compiler](https://docs.unity3d.com/6000.3/Documentation/Manual/linux-il2cpp-crosscompiler.html) (only Linux-as-target is documented)
- [Unity Manual: IL2CPP scripting back end](https://docs.unity3d.com/6000.3/Documentation/Manual/scripting-backends-il2cpp.html)
- [Unity Discussions: "Why is there no Windows IL2CPP build module for macOS?"](https://discussions.unity.com/t/why-is-there-no-windows-il2cpp-build-module-for-macos-installations-of-unity/919172)
- [GameCI issue #82](https://github.com/game-ci/unity-builder/issues/82): maintainer confirms "not possible to create windows builds with IL2CPP support using Unity running on Linux"
- [GameCI issue #610](https://github.com/game-ci/unity-builder/issues/610): "You can only build Desktop IL2CPP for that platform that you're on"

## IL2CPP requires MSVC on Windows

IL2CPP converts C# to C++, then compiles the C++ to native code. On Windows, Unity requires Microsoft's MSVC compiler (`cl.exe` from Visual Studio Build Tools). MinGW, Clang, and other compilers are not supported. This is Unity-specific, not a universal Windows constraint.

Visual Studio Build Tools cannot be *publicly* redistributed inside Docker images (Microsoft licensing). Building private images with VS Build Tools installed is explicitly supported and documented by Microsoft ([Install VS Build Tools into a container](https://learn.microsoft.com/en-us/visualstudio/install/build-tools-container?view=vs-2022)). GameCI's images are public, so they can't include them — they must be mounted from the host at runtime, which is documented as fragile (path coupling, VS version drift). A private image (e.g. on GHCR) with VS Build Tools baked in avoids both the licensing issue and the mount fragility.

## What we use from GameCI today

Our `unity.yml` workflow uses **only GameCI's Docker images** (`unityci/editor:6000.0.66f1-<module>-3`). We do NOT use any GameCI GitHub Actions — activation, build, and license return are all done manually via `unity-editor` CLI and `uv run build-unity`. GameCI's value to us is purely "Ubuntu container with Unity pre-installed."

## Windows CI approaches evaluated

### 1. Serialize + native install on `windows-latest`

Install Unity on the bare runner each time (via Unity Hub CLI or Buildalon's `unity-setup` action), build, return license, then start the next build.

- **Install overhead**: ~10-20 min cold, ~3-8 min with `actions/cache` restore (Unity is 5-7 GB)
- **Cache budget**: GitHub allows 10 GB per repo. Unity installation would consume most of it, competing with Library folder caches for all 7 builds.
- **I/O performance**: `windows-latest` C: drive is remote blob storage (136-4,262 IOPS vs 8,247-83,588 IOPS on the temp D: drive). Unity installs to C: by default. ([Source](https://chadgolden.com/blog/github-actions-hosted-windows-runners-slower-than-expected-ci-and-you))
- **Licensing**: Serialization stays within the 2-seat limit (1 dev machine + 1 CI at a time). Must serialize with Linux builds too — all of CI shares the remaining seat.
- **Cross-workflow concern**: If two workflows run simultaneously (push to main + dev), a GitHub `concurrency` group on the Unity activation step would be needed to prevent both from activating at the same time.
- **Seat wedging risk**: If a runner crashes mid-build, the license isn't returned. Recoverable via Unity ID portal but requires manual intervention.
- **Verdict**: Free, reliable, but slow. The install overhead is the main pain point.

### 2. Windows Docker container on `windows-latest`

Use a Windows Docker image with Unity pre-installed (GameCI's or our own), running on `windows-latest` via process isolation. Mount VS Build Tools from the host.

- **No install overhead**: Unity is baked into the image.
- **VS Build Tools mount**: `windows-latest` has VS 2022 pre-installed. Mount `C:\Program Files\Microsoft Visual Studio\` and Windows SDK paths into the container. Paths must match exactly.
- **Fragility**: Host VS version can change when GitHub updates runner images. Mount paths break silently. GameCI docs describe this approach but note it is fragile.
- **Machine identity**: GameCI Windows images don't hardcode machine-id. A custom image could hardcode writable signals (registry values) but not SMBIOS values (set by hypervisor). Effectiveness depends on which signals Unity checks.
- **Known issues**: DNS failures reaching Unity licensing server ([#669](https://github.com/game-ci/unity-builder/issues/669)), IPC/token caching failures ([#569](https://github.com/game-ci/unity-builder/issues/569)).
- **Verdict**: Mirrors the Linux pattern but the VS mount coupling is a maintenance liability. The machine identity question adds uncertainty.

### 3. Self-hosted Windows runner

A Windows machine (physical or VM) with Unity + VS pre-installed, registered as a GitHub Actions runner. Unity stays installed permanently.

- **No install overhead**: Unity is always there.
- **No VS mount**: VS is installed natively.
- **Licensing**: Consistent machine identity (it's literally the same machine every time). 1 seat consumed.
- **Maintenance**: Must keep runner online, patched, and updated. Hardware/VM cost.
- **Verdict**: Free (if hardware exists), fast, reliable. But adds an operational burden.

### 4. Paid managed runners

Buildalon ($40-180/mo) or GitHub larger runners with custom images (requires Team/Enterprise plan).

- **Buildalon**: Persistent Windows VMs with Unity pre-installed. Incremental builds. Single-person project — governance risk per CLAUDE.md FOSS principles.
- **GitHub custom images**: Available on larger runners (public preview since Oct 2025). Requires paid plan. You build a custom VM image with Unity baked in.
- **Verdict**: Solves everything but costs money and/or adds vendor dependency.

### 5. Skip win64 CI

Accept that Windows builds are only tested locally on developer machines.

- **Verdict**: Honest about the cost/complexity trade-off. No CI coverage for the win64 platform.

## The Buildalon ecosystem

[Buildalon](https://github.com/buildalon) is a set of GitHub Actions by RageAgainstThePixel (Adam Gale). Open-source actions: `unity-setup` (install + cache Unity), `activate-unity-license`, `unity-action` (run Unity commands). Also sells managed runners with Unity pre-installed.

Governance concern: single-person project. Predecessor (`kuler90/setup-unity`) was archived January 2026. The actions are thin wrappers around Unity Hub CLI, so the logic is straightforward to replicate if abandoned.

## GitHub-hosted runner constraints

- **Cache size**: 10 GB per repo (default). Can exceed via pay-as-you-go on enterprise plans. Entries evicted after 7 days of no access.
- **Custom VM images**: Only available on "larger runners" (GitHub Team/Enterprise plan, public preview Oct 2025). Standard runners (`windows-latest`) cannot use custom images.
- **Windows containers**: `windows-latest` supports Windows containers (process isolation). No Hyper-V isolation on GitHub-hosted runners.
