# Win64 Container Feasibility: Hosted vs Self-Hosted Runners

Research conducted 2026-03-04. Context: T75 evaluating private Windows Docker image (Unity + VS Build Tools) for IL2CPP CI builds.

## Windows containers on GitHub-hosted runners

### Pull time is prohibitive

Windows container base images start at ~4 GB compressed (Server Core). Add Unity (~5-7 GB) and VS Build Tools (~5 GB) and the total image is 12-16 GB compressed, 18-25 GB extracted. GitHub-hosted runners have no persistent Docker layer cache between runs. Every CI run pulls the full image.

Documented real-world case: 11 GB compressed Windows image on a hosted runner took 15-25 minutes just for pull + extraction. Extraction time dominates over download time. For a 15-20 GB image, expect 25-40+ minutes per run.

This is worse than native Unity install with `actions/cache` (3-8 min warm).

### Disk space on `windows-latest` (WS2025) is ~33 GB

`windows-latest` migrated from WS2022 to WS2025 in September 2025. The D: drive was removed (confirmed, intentional, GitHub closed the issue as "not planned"). Only ~33 GB free on C:. GitHub's guaranteed minimum is 14 GB.

A 15-20 GB image extraction plus build artifacts would be very tight. `windows-2022` still has ~93 GB free but will eventually be deprecated.

### `container:` job syntax is Linux-only

GitHub Actions `container:` key (native container integration) only works on Linux runners. On Windows, you must use explicit `docker pull` + `docker run` in `run:` steps. This works but is less integrated.

### 2 vCPUs on standard hosted runners

IL2CPP compilation is CPU-intensive (MSVC compiling generated C++). 2 vCPUs on `windows-latest` is very slow for this workload.

### Process isolation only

GitHub-hosted runners don't support Hyper-V isolation (no nested virtualization). Process isolation requires container OS version to match host OS version. ltsc2022 containers are forward-compatible to WS2025 hosts, so this isn't a practical issue.

## Self-hosted runner eliminates all hosted-runner blockers

| Blocker on hosted runners | Self-hosted |
|---|---|
| 25-40 min image pull every run | Docker layer cache persists. First pull only. |
| 33 GB disk on WS2025 | User-controlled disk size. |
| 2 vCPUs | User-controlled CPU. |
| No `container:` syntax | Same — use `docker run` in `run:` steps. |

### Hosting options

| Option | Cost | Notes |
|---|---|---|
| Spare Windows machine | ~$0/mo (public repo) | Zero infra cost if available. Best for starting. |
| Hetzner AX41 + WS2022 license | ~€65-70/mo | 6-core Ryzen, 64 GB RAM, NVMe. Best value for dedicated. |
| Azure D4s_v5 | ~$280/mo | Only makes sense with reserved instances. |

### Security

Self-hosted runners on public repos: any fork PR can execute arbitrary code. Mitigate by requiring approval for outside contributor PRs (repo settings → Actions → Fork pull request workflows). For a small public project with controlled contributors, a persistent runner with this setting is acceptable.

### GitHub platform fee (March 2026)

$0.002/min for self-hosted runners on private repos. Public repos remain free.

## GameCI Windows images

GameCI has production Windows Docker images (`unityci/editor:windows-*`) that solve the Server Core compatibility problem. Their approach:

1. Base image: `mcr.microsoft.com/dotnet/framework/sdk:4.8-windowsservercore-ltsc2022`
2. Multi-stage build copies ~8 DLLs from `mcr.microsoft.com/windows/server:ltsc2022` into Server Core:
   - `opengl32.dll`, `glu32.dll` (OpenGL — needed by Unity Hub's Electron/Chromium)
   - `dxva2.dll` (DirectX Video Acceleration)
   - `mf.dll`, `mfplat.dll`, `mfreadwrite.dll` (Media Foundation)
   - `BluetoothApis.dll`, `bthprops.cpl` (Bluetooth)
3. Install Unity Hub via Chocolatey, then Unity Editor via Hub CLI headless
4. Configure Windows services (`nlasvc`, `netprofm`) needed by Unity's networking internals

Without these DLLs, Unity Hub crashes and Unity Editor batchmode fails silently.

GameCI's Windows images do NOT include VS Build Tools (Microsoft licensing prohibits public redistribution). For IL2CPP, they document bind-mounting VS from the host — fragile due to path coupling and VS version drift.

## VS Build Tools in containers

Microsoft's official Dockerfile pattern (`learn.microsoft.com/en-us/visualstudio/install/build-tools-container`):

```dockerfile
RUN curl -SL --output vs_buildtools.exe https://aka.ms/vs/17/release/vs_buildtools.exe \
    && (start /w vs_buildtools.exe --quiet --wait --norestart --nocache \
        --installPath "%ProgramFiles(x86)%\Microsoft Visual Studio\2022\BuildTools" \
        --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended \
        || IF "%ERRORLEVEL%"=="3010" EXIT 0) \
    && del /q vs_buildtools.exe
```

- Minimal workload: `VCTools --includeRecommended` (~15 GB, includes MSVC cl.exe + Windows SDK)
- Exit code 3010 = "success, reboot required" — treat as success in containers
- Private images with VS Build Tools are explicitly supported by Microsoft

### vswhere discovery risk

Unity uses `vswhere.exe` to locate VS installations. By default, vswhere only searches Community/Professional/Enterprise — it excludes Build Tools unless called with `-products *` or `-products Microsoft.VisualStudio.Product.BuildTools`. Whether Unity 6 passes this flag is unknown. Workarounds if it doesn't: install VS Community instead, set environment variables, or create registry shims.

## Conclusion

Containers on hosted runners are economically backwards for large Windows images — pull time exceeds native install time. Self-hosted runners eliminate this by persisting the Docker cache. The private image strategy (GameCI base + VS Build Tools) is viable on self-hosted, pending empirical confirmation of IL2CPP compilation inside the container.

## Sources

- [Windows container version compatibility — Microsoft Learn](https://learn.microsoft.com/en-us/virtualization/windowscontainers/deploy-containers/version-compatibility)
- [Isolation modes — Microsoft Learn](https://learn.microsoft.com/en-us/virtualization/windowscontainers/manage-containers/hyperv-container)
- [Install VS Build Tools into a container — Microsoft Learn](https://learn.microsoft.com/en-us/visualstudio/install/build-tools-container)
- [VS Build Tools Workload Component IDs — Microsoft Learn](https://learn.microsoft.com/en-us/visualstudio/install/workload-component-id-vs-build-tools)
- [GameCI Windows Docker Images](https://game.ci/docs/docker/windows-docker-images/)
- [game-ci/docker GitHub repository](https://github.com/game-ci/docker)
- [Windows Server 2025 disk space — runner-images #12609](https://github.com/actions/runner-images/issues/12609)
- [windows-latest migration to WS2025 — runner-images #12677](https://github.com/actions/runner-images/issues/12677)
- [GitHub Actions Windows containers — community #25491](https://github.com/orgs/community/discussions/25491)
- [vswhere excludes Build Tools by default — vswhere #320](https://github.com/microsoft/vswhere/issues/320)
- [Using MSVC in a Docker Container — C++ Team Blog](https://devblogs.microsoft.com/cppblog/using-msvc-in-a-docker-container-for-your-c-projects/)
