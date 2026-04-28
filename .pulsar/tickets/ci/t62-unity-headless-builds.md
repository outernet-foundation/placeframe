---
id: T62
title: Unity headless batch builds in COI container
status: in-review
depends_on: []
plan: t62-plan.md
---

# T62: Unity headless batch builds in COI container

## Goal

Enable compilation verification for the four Unity projects (AndroidMobile, MapRegistrationTool, MakeItSing, Outernet.Client) inside the COI sandbox, targeting Android and Linux Standalone.

## Context

Research reports:
- `.pulsar/research/unity-headless-batch-builds.md` (original feasibility research)
- `.pulsar/research/unity-hub-segfault-in-coi-build.md` (segfault root cause + direct download approach)

Claude Code currently cannot verify that Unity C# code compiles. When editing generated API clients or Placeframe packages consumed by the Unity projects, there is no feedback loop — breakage is only discovered when a human opens the project in the Unity Editor.

All four projects currently use **Unity 6 LTS (6000.0.66f1)**. The planned downgrade to Unity 2022.3 LTS has not happened.

## Design decisions

1. **Image vs volume** → bake into image. Install editors in `coi-placeframe-build.sh` (~15-20 GB). Slower image rebuild on Unity version bumps, but fast container launch and no first-run surprises.
2. **License management** → serial-based activation at container startup. Unity 6 changed the licensing system: the old ULF copy approach no longer provides the `com.unity.editor.headless` entitlement needed for batchmode. Instead, `agent_shell.py` reads credentials from a host-side file (`~/.config/unity3d/unity-credentials`) and runs `-serial -username -password` activation via `incus exec` after the container reaches RUNNING state. The credentials file is never mounted into the container — Claude Code cannot see it. The serial is extracted from the ULF's `DeveloperData` field. Same pattern as GameCI's approach (see issue #74 on game-ci/unity-orb).
3. **Compilation wrapper** → `uv run` command (e.g. `uv run build-unity`). Follows existing pattern (`uv run up`, `uv run build`, etc.). Runnable from repo root, no Claude Code dependency.

## Key risks

- **Serial activation limits**: Unity limits concurrent serial activations (typically 2 for Personal). If a container is destroyed without returning the license, the activation slot is consumed until Unity's server-side timeout. Can be manually returned via Unity Hub on the host machine, or by running `Unity -batchmode -quit -returnlicense` in the container before destruction.

## Approach

**Revised**: bypass Unity Hub in the build script entirely. Download the editor and modules via direct URLs from Unity's CDN, avoiding the Electron dependency that segfaults in the COI build container. Unity publishes a per-version `.ini` manifest at `https://download.unity3d.com/download_unity/{changeset}/unity-{version}-linux.ini` with all download URLs and checksums.

Key downloads for 6000.0.66f1 (changeset `e7adf66625be`):
- Editor: `LinuxEditorInstaller/Unity.tar.xz` (4.5 GB, tar.xz)
- Linux IL2CPP: `LinuxEditorTargetInstaller/UnitySetup-Linux-IL2CPP-Support-for-Editor-6000.0.66f1.tar.xz` (66 MB, tar.xz)
- Android support: `MacEditorTargetInstaller/UnitySetup-Android-Support-for-Editor-6000.0.66f1.pkg` (675 MB, needs `7z`/`cpio` extraction — no Linux-native `.tar.xz` available)
- Android SDK/NDK/JDK: individual downloads from Google + Unity CDN (see research report)

License activation is handled by `agent_shell.py` at container startup using serial-based activation (credentials read from host-side file, passed via `incus exec`). Provide `uv run build-unity` to run compilation checks. See `.pulsar/plans/t62-plan.md` for original plan; approach updated per `.pulsar/research/unity-hub-segfault-in-coi-build.md`.

## Done when

- [ ] Both Unity editors installed and launchable in batchmode inside COI container
- [ ] License activation works (serial-based activation at container startup)
- [ ] All four projects pass compilation check for Android target
- [ ] All four projects pass compilation check for Linux Standalone target
- [ ] Compilation check is runnable as a command from repo root

## Log

Clean implementation, no issues. Basedpyright not available in sandbox (tracked as T63), so type checking was done via `npx basedpyright` — all errors are pre-existing import resolution failures, not new issues.

**Reopened (1)** — `xvfb-run: error: Xvfb failed to start` during `coi build custom` (image build). Fixed by dropping `xvfb-run` and relying on `--headless` alone (750fcc92).

**Reopened (2)** — `unityhub --no-sandbox --headless install-path --set /opt/unity` segfaults (exit 139) during `coi build custom`. Crashpad error precedes: `elf_dynamic_array_reader.h:64: tag not found`. The same commands worked when run interactively in a fully launched COI container — the difference is the COI build container, which is a temporary container with likely more restricted environment (missing `/dev/shm`, tighter seccomp/AppArmor, missing pseudo-filesystems that Electron/Chromium needs). Unity Hub is an Electron app, so it's sensitive to these restrictions even in `--headless --no-sandbox` mode.

**Reopened (3)** — `ELECTRON_DISABLE_CRASHPAD=1` fix (fc511baf) did not resolve the segfault. Research (`.pulsar/research/unity-hub-segfault-in-coi-build.md`) identified the root cause: Chromium's GPU process crashes in the containerized environment, Crashpad's ptrace broker tries to snapshot the crash but fails due to Yama ptrace_scope restrictions in the container's PID namespace, producing a secondary segfault. The `ELECTRON_DISABLE_CRASHPAD=1` env var is undocumented and may not be respected by Unity Hub 3.16.3's Electron build. COI source code review confirmed the build container and running container have **identical security configs** — the "works in running container" observation suggests the issue is timing (services not fully initialized) rather than missing capabilities. **Decision: abandon Unity Hub in the build script. Switch to direct downloads from Unity's CDN.** The `.ini` manifest at `download.unity3d.com` provides all URLs and checksums. Editor and Linux modules are `.tar.xz`; Android module requires `.pkg` extraction via `7z`/`cpio`.

**Reopened (3) fix** — Rewrote `coi-placeframe-build.sh` to use direct downloads from Unity's CDN. Tested `.pkg` extraction in-container: the Apple xar archive contains a plain cpio `Payload~` (not gzipped), which extracts flat to the `AndroidPlayer/` level. Editor and Linux IL2CPP are straightforward `tar xJ` extractions. Android SDK/NDK/JDK downloaded individually from Google/Unity CDN with directory renames to match Unity's expected layout. Skipped `modules.json` creation — will add if Unity can't auto-discover modules during compilation checks.

**Reopened (4)** — `curl: (22) The requested URL returned error: 404` during OpenJDK download in `coi-placeframe-build.sh`. The build script constructs the URL as `$CDN/open-jdk/open-jdk-linux-x64/jdk17.0.9-9_...zip` where `CDN=https://download.unity3d.com/download_unity/$CHANGESET`. This expands to `download_unity/e7adf66625be/open-jdk/...` — but Unity hosts OpenJDK at a **version-independent** path without the changeset prefix: `download_unity/open-jdk/open-jdk-linux-x64/...`. Confirmed via HEAD requests: the changeset-prefixed URL returns 404, the root-level URL returns 200. The Unity release API (`services.api.unity.com/unity/editor/release/v1/releases`) confirms the correct URL has no changeset prefix. **Fix:** use the absolute URL `https://download.unity3d.com/download_unity/open-jdk/open-jdk-linux-x64/jdk17.0.9-9_8d1cbcce56285f3146cf7761353a643fe573b39e45bd94f35590dca39277f667.zip` instead of `$CDN/open-jdk/...`. The `.ini` manifest doesn't list the JDK at all — it's only discoverable via the release API.

**Reopened (5)** — `mv: cannot stat '.../SDK/cmake/cmake': No such file or directory` during `coi build custom`. The `cmake-3.22.1-linux.zip` from Google extracts flat (`bin/`, `share/`) with no parent directory. The build script assumed it extracted into a `cmake/` subdirectory and tried to rename that to `3.22.1`. **Fix:** extract directly into the `3.22.1` target directory, eliminating the rename.

**Build complete** — `coi build custom` succeeded. Unity 6000.0.66f1 editor and all modules (Linux IL2CPP, Android support, OpenJDK 17, NDK r27c, SDK build-tools/platform-tools/platforms/cmdline-tools/CMake) verified present at `/opt/unity/6000.0.66f1/`. Five reopens to get here (xvfb, Hub segfault, Hub segfault redux, OpenJDK URL, CMake extraction). Next blocker: ULF license file not mounted — `setup_agent_sandbox.py` adds the Incus profile disk device, but the host needs `~/.local/share/unity3d/Unity/Unity_lic.ulf` present and `uv run setup-agent-sandbox` re-run. After that: smoke-test batchmode compilation, implement `uv run build-unity`, and add Unity 2022.3 LTS.

**ULF not found** — `setup_agent_sandbox.py` checked all three candidate paths and found nothing, despite Unity Hub on the host showing an activated Personal license. Unity Hub can show an activated license without writing the `.ulf` file to disk. Fix: Hub → Manage Licenses → Add → "Get a free personal license" forces the file to be created. Added a hint about this quirk to the error message in `setup_agent_sandbox.py` (9875d0a2).

**GTK3 missing** — `uv run build-unity` failed with `libgtk-3.so.0: cannot open shared object file`. The build script installed `libgtk2.0-0` (GTK2) but Unity 6 requires GTK3 even in batchmode. **Fix:** added `libgtk-3-0` to the apt-get install list in `coi-placeframe-build.sh`. Verified in-container: `ldd` shows no missing libraries after install.

**ULF licensing fails with Unity 6** — With GTK3 fixed, Unity launches, loads the project, and completes assembly reload, but rejects the license: `[Licensing::Module] Error: 'com.unity.editor.headless' was not found.` followed by `No valid Unity Editor license found.` Unity 6 changed the licensing system to require an online entitlement check for `com.unity.editor.headless`, which the ULF copy approach doesn't satisfy. This is the same issue documented in [GameCI unity-orb #74](https://github.com/game-ci/unity-orb/issues/74). The `enableEntitlementLicensing: false` workaround in `services-config.json` was attempted but the licensing client ignores it (it's a Licensing Server setting, not an editor setting).

**Switched to serial activation** — Following GameCI's approach (PR #83): extract serial from ULF `DeveloperData` field, activate with `-serial -username -password` at runtime. Credentials stored in `~/.config/unity3d/unity-credentials` on the host, read by `agent_shell.py`, passed via `incus exec` (host PID namespace — invisible to Claude Code inside the container). `setup_agent_sandbox.py` auto-extracts serial from ULF and validates the credentials file. Old `unity-license` profile device removed. Pending: smoke-test of the actual serial activation (requires host-side re-run of `setup-agent-sandbox` and `agent-shell`).

**Basedpyright fix** — `_parse_unity_credentials` used private prefix but was imported cross-module by `agent_shell.py`. Renamed to `parse_unity_credentials`. All three T62 files now pass basedpyright with 0 errors.

**Activation never runs from main repo** — `agent_shell.py` validated credentials at the top (blocking entry if missing), but the actual `ensure_unity_activated()` call was only reachable from the worktree code path. When `.git` is a directory (not a worktree file), `main_git_path` is `None` and `exec_command(SHELL_COMMAND)` replaced the process before reaching any activation code. The two worktree paths (existing container, new container) both called `ensure_unity_activated`, but the non-worktree path short-circuited. **Fix:** changed the early `exec_command` guard from `main_git_path is None` to `main_git_path is None and credentials is None` — only skip configuration when there's truly nothing to do. The container-exists and new-container branches now conditionally handle git mount and activation independently.

## Observations

- `basedpyright` is not in the dev dependency group, so `uv run basedpyright` fails in the sandbox. Tracked as T63.
- Unity's `services-config.json` lives at `/usr/share/unity3d/config/services-config.json` on Linux (confirmed via strace). The `enableEntitlementLicensing` key is a Licensing Server setting — the editor's licensing client reads the file but ignores that key. Not a viable workaround for the headless entitlement issue.
- `uv run build-unity` with linux64 target causes Unity to auto-add `com.unity.toolchain.linux-x86_64` to project manifests and lock files. This is a Unity side effect, not a bug — the changes are additive and should be committed.
- Pre-existing format drift in `packages/python/common/src/common/run_command.py`, `packages/python/common/src/common/stream_tar.py`, `scripts/src/scripts/build.py`, `scripts/src/scripts/generate_datamodels.py` — all flagged by `ruff format --check` but not introduced by this branch.
