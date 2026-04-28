# Freeing host disk space from GitHub Actions container jobs

Research conducted 2026-03-04. Context: Unity CI Android builds hanging due to disk exhaustion; the `jlumbroso/free-disk-space` action silently does nothing inside `container:` jobs.

## The question

Is mounting the host filesystem into a GitHub Actions `container:` job via volume mounts a viable, robust way to free host disk space from inside the container? What are the gotchas, and what's the recommended implementation?

## Background: why composite actions fail in container jobs

When a job specifies `container:`, all steps — including composite actions — run inside the container. The `jlumbroso/free-disk-space` action uses `sudo rm -rf`, `sudo apt-get remove`, and `sudo docker image prune`, all of which target the container's filesystem, not the host's. The action completes in 0 seconds, frees 0 bytes, and reports success.

GitHub staff confirmed in [community discussion #13718](https://github.com/orgs/community/discussions/13718) that there is no way to make composite actions run on the host when a job specifies a container. [actions/runner issue #812](https://github.com/actions/runner/issues/812) requested pre-container steps and was closed without implementation.

The action's own issue tracker confirms the problem: [jlumbroso/free-disk-space #21](https://github.com/jlumbroso/free-disk-space/issues/21).

## The volume-mount approach

GitHub Actions provides a first-class `volumes:` key under `jobs.<job_id>.container` for bind mounts from the host. No documented restriction on which host paths can be mounted. The syntax:

```yaml
container:
  image: my-image
  volumes:
    - /host/path:/container/path
```

By mounting host directories containing pre-installed bloat, a step running inside the container can `rm -rf` those contents, freeing actual host disk space (which is the same disk backing the container's overlay filesystem).

## Real-world usage

Multiple major open-source projects use this pattern in production:

**Selective mounts (recommended)**:
- [kedacore/keda](https://github.com/kedacore/keda) — mounts `/usr:/host/usr` and `/opt:/host/opt`, then `rm -rf /host/usr/local/lib/android /host/usr/share/dotnet /host/opt/ghc`
- [obsproject/obs-studio](https://github.com/obsproject/obs-studio) — mounts each target path individually under `/to_clean/`, e.g. `/usr/local/lib/android:/to_clean/android`
- [OrcaSlicer](https://github.com/OrcaSlicer/OrcaSlicer) — similar to OBS, with renamed mount points to avoid collisions
- [apache/kvrocks](https://github.com/apache/kvrocks) — mounts `/usr/local/lib/android:/usr-local-lib-android`

**Full host root mount (works but broader attack surface)**:
- [dragonflydb/dragonfly](https://github.com/dragonflydb/dragonfly) — mounts `/:/hostroot`, then `rm -rf /hostroot/usr/share/dotnet` etc.

## What to clean and how much space each path holds

| Path | Contents | Approx. Size |
|------|----------|-------------|
| `/usr/local/lib/android` | Android SDK + NDK | 6-10 GB |
| `/opt/hostedtoolcache` | Node, Go, Python, Ruby, CodeQL | 8-11 GB |
| `/usr/local/.ghcup` | Haskell (GHC, Cabal, Stack) | 3-6 GB |
| `/usr/share/swift` | Swift toolchain | 2.5 GB |
| `/usr/share/dotnet` | .NET SDKs/runtimes | 1.5-2 GB |
| `/usr/local/share/chromium` | Chromium browser | 1.5 GB |
| `/usr/lib/jvm` | Java JDKs | 1.5 GB |
| `/opt/google` | Chrome + Google Cloud CLI | 1 GB |
| `/usr/local/share/powershell` | PowerShell | 800 MB |
| `/opt/microsoft` | Edge browser | 500 MB |
| `/usr/local/share/boost` | Boost C++ libraries | 500 MB |

Total recoverable via volume mounts: ~25-35 GB.

**Cannot clean from inside a container**: Docker images (requires host Docker daemon), swap file (requires `swapoff`), APT packages (requires host's `apt-get`). These are less impactful — the `rm -rf` targets above cover the vast majority of reclaimable space.

## Gotchas

1. **Path collisions.** If the container image has files at the mount destination (e.g., mounting host `/usr/local/lib/android` to container `/usr/local/lib/android`), the container's content at that path is hidden by the bind mount. Use different mount points (e.g., `/to_clean/android`) to avoid this. This is particularly relevant for the `android` module images which have their own Android SDK inside the container.

2. **Runner image path changes.** `ubuntu-latest` now points to Ubuntu 24.04 (changed January 2025). Core paths (`/usr/local/lib/android`, `/usr/share/dotnet`, `/opt/hostedtoolcache`) have been stable across 22.04 and 24.04. Using `rm -rf` on directory paths is more resilient than `apt-get remove` (which broke when `google-cloud-sdk` was renamed to `google-cloud-cli`).

3. **Permission issues.** Container jobs typically run as root. Files created via mounted volumes will be owned by root, which can cause cleanup issues in later steps. Not a concern for delete-only mounts.

4. **`--network` and `--entrypoint` are blocked** in `container.options`. Other docker create flags appear to pass through. Volume mounts via the `volumes:` key are fully supported.

## Recommended implementation for this project

```yaml
container:
  image: unityci/editor:6000.0.66f1-${{ matrix.module }}-3
  volumes:
    - /usr/local/lib/android:/to_clean/android
    - /usr/share/dotnet:/to_clean/dotnet
    - /opt/hostedtoolcache:/to_clean/toolcache
    - /usr/local/.ghcup:/to_clean/ghcup
    - /usr/share/swift:/to_clean/swift

steps:
  - name: Free Disk Space
    run: |
      rm -rf /to_clean/android/* /to_clean/dotnet/* /to_clean/toolcache/* /to_clean/ghcup/* /to_clean/swift/*
      df -h
```

Note: the host's Android SDK (`/usr/local/lib/android`) is safe to delete even for Android builds — the NDK and SDK needed for Unity Android builds are inside the container image, not on the host. The host copy is a GitHub runner pre-install that's pure bloat for containerized builds. Mounting it to `/to_clean/android` (not `/usr/local/lib/android`) avoids shadowing the container's own Android tools.

## Sources

- [GitHub Docs: Running jobs in a container](https://docs.github.com/en/actions/how-tos/write-workflows/choose-where-workflows-run/run-jobs-in-a-container) — `container.volumes` syntax
- [jlumbroso/free-disk-space #21](https://github.com/jlumbroso/free-disk-space/issues/21) — confirms action broken in container jobs
- [GitHub community #13718](https://github.com/orgs/community/discussions/13718) — composite actions can't run on host in container jobs
- [actions/runner #812](https://github.com/actions/runner/issues/812) — pre-container steps not supported (closed)
- [obsproject/obs-studio workflow](https://github.com/obsproject/obs-studio) — selective mount pattern
- [kedacore/keda workflow](https://github.com/kedacore/keda) — `/usr` and `/opt` mount pattern
- [dragonflydb/dragonfly workflow](https://github.com/dragonflydb/dragonfly) — full host root mount
- [OrcaSlicer workflow](https://github.com/OrcaSlicer/OrcaSlicer) — selective mount with renamed paths
- [apache/kvrocks workflow](https://github.com/apache/kvrocks) — selective mount
- [Matej Lednicky: Squeezing Disk Space from GitHub Actions Runners](https://dev.to/mathio/squeezing-disk-space-from-github-actions-runners-an-engineers-guide-3pjg) — disk space analysis
- [actions/runner-images Ubuntu 24.04 Readme](https://github.com/actions/runner-images/blob/main/images/ubuntu/Ubuntu2404-Readme.md) — installed software paths
