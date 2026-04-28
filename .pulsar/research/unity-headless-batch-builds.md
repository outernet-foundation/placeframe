# Unity Headless Batch Builds in Incus Containers

Research conducted 2026-03-03. Context: enabling Claude Code to verify Unity project compilation inside the COI (Code on Incus) sandbox.

## The question

How can we run Unity CLI batch builds inside an Incus system container (Linux, no GPU) to verify that four Unity projects compile for Android and Linux Standalone targets — using a Personal license, with minimal cost and no cloud vendor lock-in?

Constraints:
- Two editor versions: Unity 2022.3 LTS (three apps projects) and Unity 6 LTS 6000.0.66f1 (legacy/Outernet.Client)
- Build targets: Android and Linux Standalone
- Primary goal is compilation verification, not producing shippable artifacts
- Personal license preferred; willing to upgrade if no viable alternative
- FOSS tooling only; Unity Build Automation (cloud) is excluded
- GameCI pipeline integration is planned separately — this research covers the container-level setup

## Findings

### 1. Compilation verification without a full player build

The fastest way to verify scripts compile is to open the project in batch mode and quit:

```bash
Unity -batchmode -nographics -quit -logFile /dev/stdout -projectPath /path/to/project
```

Unity compiles all scripts during "Initial Script Refresh" on project open. If compilation fails, it exits with **return code 1**. If it succeeds, `-quit` causes a clean exit with **return code 0**. No player build, no output artifacts — just "does it compile?".

This is slower than a pure C# compiler invocation (Unity loads its full runtime, imports assets, resolves packages) but it's the only reliable method — Unity projects depend on Unity-specific assemblies, define symbols, and asmdef references that a standalone `dotnet build` cannot resolve.

For a more thorough check that also validates per-platform settings, add `-buildTarget`:

```bash
# Verify compilation with Android as the active platform
Unity -batchmode -nographics -quit -logFile /dev/stdout \
  -projectPath /path/to/project -buildTarget android

# Verify with Linux Standalone
Unity -batchmode -nographics -quit -logFile /dev/stdout \
  -projectPath /path/to/project -buildTarget linux64
```

This catches platform-conditional compilation issues (`#if UNITY_ANDROID`, etc.) without producing a build.

### 2. License activation — the central problem

**Unity Personal cannot be officially activated via CLI.** The Unity 6 docs explicitly state: "The following procedures don't apply to Unity Personal. To activate a license for Unity Personal, log in to the Unity Hub." The old manual activation portal (`license.unity3d.com/manual`) was shut down for Personal tier in August 2023.

The `-serial` flag only works with Pro/Enterprise serial keys.

#### Workaround: copy the .ulf file

The established CI workaround (used by GameCI and others):

1. Activate a Personal license on a machine with a GUI (Unity Hub → Preferences → Licenses)
2. Copy the generated `.ulf` file from `~/.local/share/unity3d/Unity/Unity_lic.ulf` (Linux)
3. Place the `.ulf` at the same path inside the container
4. Unity reads it on startup — no `-serial` activation needed

This works reliably. The license file is tied to a machine fingerprint, but in practice Unity is lenient about this in batch mode — the same `.ulf` file works across CI machines. If it stops working, re-activate locally and copy the new file.

**Risk**: Unity could tighten enforcement at any time. This is a tolerated workaround, not a documented feature. However, GameCI has relied on variants of this approach for years across thousands of CI pipelines, which provides practical stability evidence.

#### Upgrade path: Unity Pro

If the workaround becomes untenable:
- **Unity Pro**: $2,200/seat/year. Provides a serial key for clean `-serial` activation.
- **Unity Build Server license**: requires Pro as a prerequisite. Provides floating licenses for build machines. Pricing requires contacting sales. Not available for Personal tier at all.

For a single developer doing compilation checks, the `.ulf` copy approach is the pragmatic choice.

### 3. Installation in the container

#### Option A: Unity Hub CLI (recommended)

Install Unity Hub and use it to manage editor versions and modules:

```bash
# Install Hub
sudo install -d /etc/apt/keyrings
curl -fsSL https://hub.unity3d.com/linux/keys/public | sudo gpg --dearmor -o /etc/apt/keyrings/unityhub.gpg
echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/unityhub.gpg] https://hub.unity3d.com/linux/repos/deb stable main" \
  | sudo tee /etc/apt/sources.list.d/unityhub.list
sudo apt update && sudo apt install -y unityhub

# Install editors with modules (Hub CLI requires xvfb even in headless mode)
xvfb-run unityhub --headless install \
  --version 2022.3.XXf1 --changeset XXXXX \
  --module android android-sdk-ndk-tools android-open-jdk linux-il2cpp \
  --childModules

xvfb-run unityhub --headless install \
  --version 6000.0.66f1 --changeset XXXXX \
  --module android android-sdk-ndk-tools android-open-jdk linux-il2cpp \
  --childModules
```

Advantages: manages multiple versions cleanly, handles module dependencies, official tool.
Disadvantages: Hub itself requires xvfb, adds ~500MB, has had bugs with Android SDK installation on Linux.

#### Option B: Direct tar.xz download

Download from Unity's CDN without Hub:

```
https://download.unity3d.com/download_unity/{changeset}/LinuxEditorInstaller/Unity-{version}.tar.xz
```

Advantages: no Hub dependency, deterministic.
Disadvantages: must manually manage Android SDK/NDK/JDK, no module installer.

**Recommendation**: Use Hub for initial setup (it handles the Android SDK/NDK complexity), but the direct download is a viable fallback.

#### System dependencies

Even with `-nographics`, Unity links against X11/Mesa libraries at load time. Required packages:

```bash
sudo apt install -y \
  xvfb \
  libgtk2.0-0 libglib2.0-0 \
  libxinerama1 libxcursor1 libxrandr2 libxext6 libxrender1 libxi6 libx11-6 \
  libglu1-mesa libgl1-mesa-dev mesa-common-dev \
  libasound2 libpulse0 libnss3 libgconf-2-4 \
  libcap2 libnotify4 libunwind-dev
```

For IL2CPP builds (Linux Standalone): add `build-essential clang lld`.

#### Disk space

| Component | Approximate size |
|---|---|
| Unity 2022.3 LTS editor (base) | ~5 GB |
| Unity 6 LTS editor (base) | ~5 GB |
| Android modules (SDK/NDK/JDK) per version | ~3-5 GB |
| Linux IL2CPP module per version | ~500 MB |
| System dependencies | ~500 MB |
| **Total for two editors + Android + Linux** | **~15-20 GB** |

This is significant for a container image. Consider whether the editor installs should live in the image itself (slow rebuild, fast container launch) or be installed into a persistent volume (fast image rebuild, first-launch install delay).

### 4. Android SDK/NDK details

Unity bundles the correct SDK/NDK/JDK when installed via Hub with the `android-sdk-ndk-tools` and `android-open-jdk` modules. The bundled versions differ by editor:

| Component | Unity 2022.3 LTS | Unity 6 (6000.0) |
|---|---|---|
| NDK | r23b | r27c |
| JDK | OpenJDK 11 | OpenJDK 17 |
| SDK Build Tools | 34.0.0 | 36.0.0 |
| Target API | 33+ | 35+ |

Known issue: Unity Hub on Linux sometimes installs Android SDK executables without execute permissions or puts the NDK in the wrong directory. GameCI's Dockerfiles include post-install fixup scripts for this. If we hit this, we'll need similar workarounds.

### 5. GameCI — reference implementation

**Status**: MIT license, community-governed (no corporate backing), funded via OpenCollective donations. Latest release v3.2.1 (December 2025). 460 stars, active maintenance. Passes the FOSS governance check.

GameCI provides three Docker image layers:
1. `unityci/base` — Ubuntu with system deps
2. `unityci/hub` — adds Unity Hub
3. `unityci/editor` — full editor with target modules

Tag format: `unityci/editor:ubuntu-{version}-{target}-{gameci_version}`
Example: `unityci/editor:ubuntu-2022.3.8f1-android-3`

**We should not use GameCI images directly** (that would mean Docker-in-Incus), but their Dockerfiles are an excellent reference for:
- Exact system dependency lists per Unity version
- The `xvfb-run` wrapper pattern for headless execution
- Android SDK post-install fixups
- License activation scripting
- Version-specific workarounds

### 6. Incus/LXC-specific considerations

**No known issues** for headless Unity builds in Incus system containers. Key points:

- **No GPU passthrough needed.** `-nographics` means no graphics device initialization. Do not add a GPU device to the container.
- **xvfb is sufficient.** Unity and Unity Hub need an X11 display even in batch mode. `xvfb-run` provides a virtual framebuffer. This works identically in LXC as it does in Docker.
- **System container advantage.** Incus system containers run a full init system (unlike Docker application containers). This is actually a plus — Unity expects a normal Linux userspace with `/tmp`, `/dev/shm`, dbus, etc.
- **File descriptor limits.** Unity may need `ulimit -n 4096`. Set in the container profile.
- **No special kernel features needed.** Standard unprivileged container is fine.

## Recommendation

### Approach: direct install in the COI container image

1. **Extend `coi-placeframe-build.sh`** to install Unity Hub, xvfb, system dependencies, and both editor versions with Android + Linux IL2CPP modules.

2. **License activation**: activate Personal license locally, copy the `.ulf` file into the container at build time or mount it at runtime. This is the pragmatic choice — it's what the entire GameCI ecosystem relies on.

3. **Compilation check wrapper**: add a script (or integrate into the skills system) that runs:
   ```bash
   xvfb-run /path/to/Unity -batchmode -nographics -quit \
     -logFile /dev/stdout -projectPath /path/to/project \
     -buildTarget <android|linux64>
   ```
   Check exit code. Parse log for `Compilation failed` / `error CS` lines.

4. **Disk budget**: ~15-20 GB for both editors with modules. The COI image will be significantly larger. Consider using a separate Incus image profile or a persistent volume for the Unity installations to avoid rebuilding the full image on Unity version bumps.

5. **No Pro license needed** for now. The `.ulf` workaround is well-established. Revisit if Unity tightens enforcement or if the GameCI pipeline integration (future work) requires cleaner activation.

### What this does NOT solve

- **Runtime testing**: compilation checks don't catch runtime errors, missing asset references, or broken prefab connections.
- **Unity MCP integration**: the research question excluded this, but it's the natural next step for deeper Claude-Unity integration.
- **Build artifact production**: compilation checks are fast (~1-3 min). Full player builds (APK, Linux binary) would take significantly longer and require more disk space for output.

## Sources

- [Unity 6 Command Line Arguments](https://docs.unity3d.com/6000.0/Documentation/Manual/EditorCommandLineArguments.html)
- [Unity 6 License Management](https://docs.unity3d.com/6000.0/Documentation/Manual/ManagingYourUnityLicense.html)
- [Unity Hub CLI Reference](https://docs.unity3d.com/hub/manual/HubCLI.html)
- [Unity Hub Linux Installation](https://docs.unity3d.com/hub/manual/install-hub-linux.html)
- [Unity Android Dependency Versions](https://docs.unity3d.com/6000.3/Documentation/Manual/android-supported-dependency-versions.html)
- [Unity Build Server](https://unity.com/products/unity-build-server)
- [Unity Pricing Updates (2024)](https://unity.com/products/pricing-updates)
- [GameCI Docker Images](https://game.ci/docs/docker/docker-images/)
- [GameCI GitHub Repository](https://github.com/game-ci/docker) — MIT license, v3.2.1 (Dec 2025)
- [GameCI Activation Docs (GitHub)](https://game.ci/docs/github/activation/)
- [GameCI Activation Docs (GitLab)](https://game.ci/docs/gitlab/activation/)
- [GameCI Documentation Issue #408 — Personal license manual activation removed](https://github.com/game-ci/documentation/issues/408)
- [mob-sakai/unity-activate](https://github.com/mob-sakai/unity-activate) — Puppeteer-based activation tool
- [Unity Personal License Workaround (dev.to)](https://dev.to/ankursheel/workaround-for-unity-personal-license-manual-activation-not-supported-49j2)
- [Unity Script Compilation from CLI (Andrew Fray)](https://andrewfray.wordpress.com/2013/08/28/how-to-build-unity3d-scripts-from-the-command-line/)
- [Unity Forums — Manual Activation Removed](https://discussions.unity.com/t/unity-no-longer-supports-manual-activation-of-personal-licenses/926760)
- [Incus GPU Passthrough Issues](https://github.com/lxc/incus/issues/946)
