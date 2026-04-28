# Unity Hub Segfault in COI Build Container

Research conducted 2026-03-03. Context: T62 Unity headless batch builds — Unity Hub (Electron app) segfaults during `coi build custom` image creation.

## The question

Why does `unityhub --no-sandbox --headless install-path --set /opt/unity` segfault (exit 139) inside the COI build container, even with `ELECTRON_DISABLE_CRASHPAD=1`? What are the viable fixes — either making Hub work in the build container, or bypassing Hub entirely with direct downloads?

## Timeline

1. Initial attempt: `unityhub --headless` without display → needed `xvfb-run`
2. Reopened (1): `xvfb-run` itself failed to start in build container → dropped `xvfb-run`, relied on `--headless` alone
3. Reopened (2): segfault (exit 139) with crashpad error `elf_dynamic_array_reader.h:64: tag not found` → added `ELECTRON_DISABLE_CRASHPAD=1`
4. Reopened (3): `ELECTRON_DISABLE_CRASHPAD=1` did not prevent the segfault

Note: the same commands work in a fully launched COI container. The failure is specific to the temporary build container created by `coi build custom`.

## Root cause analysis

### What the COI build container does

From `github.com/mensfeld/code-on-incus` source (`internal/container/commands.go`, `internal/image/builder.go`):

1. `incus init <base-image> coi-build` (persistent, unprivileged)
2. `EnableDockerSupport()` sets three config keys before boot:
   - `security.nesting=true`
   - `security.syscalls.intercept.mknod=true`
   - `security.syscalls.intercept.setxattr=true`
3. `incus start coi-build`
4. Build script runs via `incus exec`
5. Container is stopped, published as image, deleted

The build container and running containers use **identical security configurations**. There is no difference in privilege level, seccomp profile, or mount configuration between them. If Hub works in a running container, the failure may be caused by a race condition during early container boot, or by the build script running before all services (dbus, udev, etc.) are fully initialized.

### Why Electron segfaults

The crash chain is:

1. Unity Hub (Electron) starts and tries to initialize a GPU process
2. In a container with no GPU and no display, the GPU process crashes
3. Crashpad (Chromium's crash reporter) tries to generate a crash snapshot
4. Crashpad's ptrace broker calls `ptrace()` to read thread state from `/proc/<pid>/task`
5. With `kernel.yama.ptrace_scope=1` (Ubuntu default), the broker needs `PR_SET_PTRACER` to succeed — this can fail in a container's PID namespace
6. The broker reads invalid memory → `elf_dynamic_array_reader.h:64: tag not found` → secondary segfault

The `ELECTRON_DISABLE_CRASHPAD=1` environment variable is **not officially documented** in Electron's public API. It's used in the wild but may not be respected by all Electron versions (Unity Hub 3.16.3 bundles its own Electron).

### Key missing flags

The build script uses `--no-sandbox` and `ELECTRON_DISABLE_CRASHPAD=1`, but does NOT use:
- `--disable-gpu` — prevents the GPU process from starting at all (avoids the initial crash that triggers the cascade)
- `--disable-dev-shm-usage` — forces `/tmp` instead of `/dev/shm` for shared memory

## Approach A: Fix Electron flags (quick fix attempt)

Add `--disable-gpu` to Unity Hub CLI calls. This prevents the GPU process crash that triggers the Crashpad cascade in the first place.

```bash
ELECTRON_DISABLE_CRASHPAD=1 unityhub --no-sandbox --headless --disable-gpu install-path --set /opt/unity
```

**Risk**: Unity Hub may not pass `--disable-gpu` through to its internal Chromium. Electron apps sometimes strip unknown CLI flags. Worth trying since it's a one-line change, but not reliable.

## Approach B: Direct download (recommended)

Bypass Unity Hub entirely. Download the editor and modules via direct URLs from Unity's CDN.

### URL discovery

Unity publishes a per-version `.ini` manifest at a predictable URL:

```
https://download.unity3d.com/download_unity/{changeset}/unity-{version}-linux.ini
```

For 6000.0.66f1: `https://download.unity3d.com/download_unity/e7adf66625be/unity-6000.0.66f1-linux.ini`

This `.ini` lists every downloadable component with relative URLs, MD5 checksums, and sizes. The same data is available as JSON from the Unity Releases API:

```
https://services.api.unity.com/unity/editor/release/v1/releases?limit=1&version=6000.0.66f1
```

### Verified download URLs for 6000.0.66f1

| Component | URL (relative to `https://download.unity3d.com/download_unity/e7adf66625be/`) | Size | Format |
|---|---|---|---|
| Editor | `LinuxEditorInstaller/Unity.tar.xz` | 4.5 GB | tar.xz |
| Linux IL2CPP | `LinuxEditorTargetInstaller/UnitySetup-Linux-IL2CPP-Support-for-Editor-6000.0.66f1.tar.xz` | 66 MB | tar.xz |
| Android support | `MacEditorTargetInstaller/UnitySetup-Android-Support-for-Editor-6000.0.66f1.pkg` | 675 MB | pkg (xar) |
| OpenJDK 17.0.9 | `open-jdk/open-jdk-linux-x64/jdk17.0.9-9_...f12c2989...63e.zip` | 122 MB | zip |
| Android NDK r27c | `https://dl.google.com/android/repository/android-ndk-r27c-linux.zip` | 664 MB | zip |
| SDK Build Tools 36 | `https://dl.google.com/android/repository/build-tools_r36_linux.zip` | 64 MB | zip |
| SDK Platform Tools 36 | `https://dl.google.com/android/repository/platform-tools_r36.0.0-linux.zip` | 8 MB | zip |
| SDK Command Line Tools | `https://dl.google.com/android/repository/commandlinetools-linux-12266719_latest.zip` | 166 MB | zip |

**Verified** (HTTP HEAD returns 200): Editor tar.xz, Linux IL2CPP tar.xz, Android support .pkg. The `LinuxEditorTargetInstaller/UnitySetup-Android-Support-for-Editor-6000.0.66f1.tar.xz` does **not** exist (404) — the Android module uses the Mac `.pkg` on all platforms.

### Installation steps

```bash
CHANGESET=e7adf66625be
VERSION=6000.0.66f1
BASE=https://download.unity3d.com/download_unity/$CHANGESET
INSTALL=/opt/unity/6000.0.66f1

# 1. Editor
mkdir -p "$INSTALL"
curl -fSL "$BASE/LinuxEditorInstaller/Unity.tar.xz" | tar xJ -C "$INSTALL" --strip-components=1

# 2. Linux IL2CPP module
curl -fSL "$BASE/LinuxEditorTargetInstaller/UnitySetup-Linux-IL2CPP-Support-for-Editor-$VERSION.tar.xz" \
  | tar xJ -C "$INSTALL" --strip-components=1

# 3. Android support module (.pkg extraction)
apt-get install -y p7zip-full cpio
curl -fSL "$BASE/MacEditorTargetInstaller/UnitySetup-Android-Support-for-Editor-$VERSION.pkg" -o /tmp/android.pkg
cd /tmp && 7z x -y android.pkg
# .pkg contains Payload files that need cpio extraction
cat Payload | gunzip -dc | cpio -i -d
# Move the PlaybackEngines directory into the editor install
cp -r ./Editor/Data/PlaybackEngines/AndroidPlayer "$INSTALL/Editor/Data/PlaybackEngines/"
rm -rf /tmp/android.pkg /tmp/Payload /tmp/Editor

# 4. Android SDK/NDK/JDK (placed where Unity expects them)
ANDROID_DIR="$INSTALL/Editor/Data/PlaybackEngines/AndroidPlayer"
# OpenJDK
curl -fSL "$BASE/open-jdk/open-jdk-linux-x64/jdk17.0.9-9_8d1cbcce56285f3146cf7761353a643fe573b39e45bd94f35590dca39277f667.zip" \
  -o /tmp/jdk.zip && unzip -q /tmp/jdk.zip -d "$ANDROID_DIR/OpenJDK" && rm /tmp/jdk.zip
# NDK
curl -fSL "https://dl.google.com/android/repository/android-ndk-r27c-linux.zip" \
  -o /tmp/ndk.zip && unzip -q /tmp/ndk.zip -d "$ANDROID_DIR/NDK" && rm /tmp/ndk.zip
# SDK tools (build-tools, platform-tools, cmdline-tools, platforms)
# These go under $ANDROID_DIR/SDK/ — each in its own subdirectory
```

### Unknowns

- **`.pkg` extraction**: The `.pkg` file is an Apple xar archive. The exact internal structure (whether Payload is gzipped cpio, or bom-based) needs to be verified by downloading a small test. The `7z` + `cpio` approach works for most Unity .pkg files, but the exact commands may need adjustment.
- **modules.json**: Unity Hub creates a `modules.json` file that tells the editor which modules are installed. Without this file, the editor may not discover installed modules. This file would need to be created manually. GameCI extracts it from the Hub installation; for direct downloads, a minimal version would need to be constructed.
- **Android SDK license acceptance**: `sdkmanager --licenses` normally needs to be run. Without Unity Hub handling this, the license acceptance files would need to be created manually.

## Approach C: Fix Xvfb in build container

Revisit using `xvfb-run` (which failed in Reopened 1). The failure message was `Xvfb failed to start` — this could be caused by missing pseudo-filesystems in the build container. If Xvfb can be made to work, the original `xvfb-run unityhub --headless` approach would succeed.

However, this has the same root problem as Approach A: depending on an Electron app in a restricted container is fragile, and future Unity Hub updates could break again.

## Recommendation

**Approach B (direct download)** is the most robust solution. It:

- Eliminates the Electron dependency entirely (no Hub process, no Chromium, no crashpad)
- Is deterministic and reproducible (explicit URLs with checksums from the .ini manifest)
- Is faster at build time (no Hub startup overhead, parallel downloads possible)
- Is the same pattern used by legacy CI systems that predate Unity Hub
- Makes version pinning explicit (URLs contain the exact changeset)

The main cost is implementation complexity for Android module extraction (`.pkg` → `7z` → `cpio`), but this is a one-time investment. The `.ini` manifest URL pattern is stable and has been available since at least Unity 2017.

**If quick iteration is needed first**, try Approach A (`--disable-gpu` flag) as a one-line experiment. If that works, it buys time to implement Approach B properly.

## Sources

- Unity Releases API: `https://services.api.unity.com/unity/editor/release/v1/releases`
- Unity download manifest (.ini): `https://download.unity3d.com/download_unity/{changeset}/unity-{version}-{platform}.ini`
- [GameCI Docker images](https://github.com/game-ci/docker) — uses Hub with `xvfb-run` in a full Docker container
- [COI source - commands.go](https://github.com/mensfeld/code-on-incus/blob/master/internal/container/commands.go) — build container creation
- [COI source - builder.go](https://github.com/mensfeld/code-on-incus/blob/master/internal/image/builder.go) — image build process
- [Chromium Crashpad design](https://chromium.googlesource.com/crashpad/crashpad/+/HEAD/doc/overview_design.md)
- [Crashpad ELF reader source](https://chromium.googlesource.com/crashpad/crashpad/+/3e748e9c4e0deccf2f95fe3c0ca6ea58b46632b0/snapshot/elf/elf_dynamic_array_reader.cc)
- [dang-gun/UnityHub_ModulesJson](https://github.com/dang-gun/UnityHub_ModulesJson) — modules.json structure examples
- [Unity Forum: Installing on Linux CI/CD](https://discussions.unity.com/t/installing-unity-on-linux-ci-cd-machine-how-to-handle-pkg-files/1615551)
- [Electron environment variables](https://www.electronjs.org/docs/latest/api/environment-variables)
