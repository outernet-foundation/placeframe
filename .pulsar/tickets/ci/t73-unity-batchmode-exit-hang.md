---
id: T73
title: Unity hangs after successful batchmode player build
status: in-review
depends_on: []
---

# T73: Unity hangs after successful batchmode player build

## Goal

Make `uv run build-unity --target linux64` exit cleanly after a successful build, so it can be used reliably in CI without manual intervention.

## Context

Unity's `-buildLinux64Player` flag is supposed to auto-exit after building. The build completes (`Build Finished, Result: Success`, `Tundra build success`) and the player binary is written to disk, but the Unity process never exits. It stops producing log output after `TrimDiskCacheJob: Current cache size 0mb` and sits idle indefinitely.

Discovered during T69 (Cesium native Linux). A separate infinite-loop hang caused by `HandsSampleProjectValidation` was fixed by deleting the imported XR samples, but the post-build exit hang persists independently.

### What's still running after the build

From `ps aux` after build success:
- Unity editor (PID, 2.9 GB RSS, state `Rsl`)
- Unity.Licensing.Client (named pipe IPC)
- UnityPackageManager (IPC socket)
- Unity.ILPP.Runner
- UnityShaderCompiler

The licensing client and package manager are child processes that won't terminate until the editor does. The editor appears to be blocked in its shutdown path — possibly waiting on a network timeout (licensing, Unity Connect, analytics) or stuck in a delayed callback.

### Last log lines before hang

```
Asset Pipeline Refresh: Total: 0.059 seconds
[Licensing::Client] Successfully resolved entitlement details
[UnityConnectServicesConfig] config is NOT valid, switching to default
TrimDiskCacheJob: Current cache size 0mb
```

The `[UnityConnectServicesConfig] config is NOT valid` line suggests Unity Connect (analytics/cloud services) may be trying to connect and timing out without a network path.

## Approach

Root cause was simply that `-quit` was missing from the linux64 build command in `build_unity.py`. The android path already had it. Without `-quit`, Unity completes the build but enters its idle editor loop instead of exiting. The child processes, UnityConnect message, and lack of internet were all red herrings.

## Done when

- [x] `uv run build-unity --project Outernet.Client --target linux64` exits with code 0 after a successful build, without manual kill
- [ ] Solution is documented in CLAUDE.md environment notes if it involves flags or config

## Log

Clean implementation, no issues. The fix was a single flag addition — diagnosed from the asymmetry between the android path (has `-quit`) and the linux64 path (missing `-quit`).

## Observations

No pre-existing issues noticed.
