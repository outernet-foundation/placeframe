# ZED Capture — Session State & Next Steps

## What was accomplished this session

### 1. Litestar migration (complete)
Migrated `docker/zed-capture/` from FastAPI to Litestar + Scalar, matching the main API's framework:
- `docker/zed-capture/src/routers/captures.py` — Rewrote using Litestar Router, @get/@post/@delete, ClientException, Stream
- `docker/zed-capture/src/main.py` — Switched to `create_litestar_app` with OpenAPIConfig + ScalarRenderPlugin
- `docker/zed-capture/pyproject.toml` — Removed fastapi dependency
- Deleted `packages/python/common/src/common/fastapi.py` and `schemas.py` (no remaining consumers)
- Removed fastapi/starlette from `packages/python/common/pyproject.toml`
- Fixed `dump_openapi.py` to use Litestar's `app.openapi_schema.to_schema()`
- Regenerated all per-service lock files
- All CI checks pass (ruff, basedpyright, deptry)

### 2. Deploy-rig overhaul (complete)
Rewrote `scripts/src/scripts/deploy_rig.py` with several improvements:

**Layer-aware deploys via NAT internet sharing:**
- Instead of transferring full images, the script now enables IP forwarding + iptables MASQUERADE on the host, sets up a default route + DNS on the Jetson, and the Jetson pulls directly from ghcr.io
- Natively layer-aware — only changed layers download
- NAT is torn down via `atexit` after deploy completes

**ZED camera daemon management:**
- Step 5 runs `sudo systemctl enable --now nvargus-daemon zed_x_daemon` on the Jetson
- Required because the ZED SDK communicates with these host daemons via Unix sockets

**ZED SDK warm-up:**
- Step 7 runs `docker compose exec zed-capture python -c "import pyzed.sl as sl; c = sl.Camera(); p = sl.InitParameters(); c.open(p); c.close()"` while NAT is still up
- This lets the SDK download calibration files and AI models (NEURAL depth model) before internet is torn down
- Downloaded files persist via volume mounts in compose.rig.yml

**Other fixes:**
- Sudoers rule content-based checking (not just file existence)
- Single `sudo sh -c '...'` for host networking (avoids credential cache expiry)
- Hostname added to `/etc/hosts` on Jetson (suppresses sudo warnings)
- `--force-recreate` on `docker compose up` to ensure container always restarts

### 3. Compose.rig.yml updates (complete)
Added volume mounts for:
- `/usr/local/zed/settings` — calibration files
- `/usr/local/zed/resources` — AI models
- `/tmp/argus_socket` — nvargus-daemon socket
- `/tmp/nvscsock` — NVIDIA camera socket
- `/tmp/camsock` — camera socket
- Added `runtime: nvidia`

### 4. ZED X camera debugging (in progress)
Commented out `_meter_and_lock` in `zed.py` for testing — this function was written for ZED 2 (USB) and fails on ZED X (GMSL2) with `ZED Set Camera Settings ROI Error: FAILURE`. **This change has NOT been tested yet** because local builds can't currently be deployed (see next steps).

## Current branch state

Branch: `feature/zed-refactor-redux`

Key commits (oldest to newest):
- Litestar migration commits (captures.py, main.py, pyproject.toml, deleted fastapi/schemas)
- `6165880a` Fix dump_openapi.py to use Litestar openapi_schema API
- `2e6c3185` Regenerate per-service lock files
- `3c7222bd` Compare image digests in deploy-rig to detect stale transfers
- `7ae29c46` Use layer-aware registry transfer in deploy-rig, fix sudoers check
- `c7fd3d05` Replace skopeo/rsync with NAT-based internet sharing for layer-aware deploys
- `442156ba` Mount ZED daemon sockets and SDK cache dirs, warm up camera on deploy
- `94231e5c` Comment out _meter_and_lock for ZED X compatibility testing

Not pushed to remote yet. No PR created. `plan.md` is untracked.

## Blocker: No local ARM64 build → deploy workflow

The ZED Box is ARM64 (Jetson Orin NX). The deploy script pulls from `ghcr.io` which only has CI-built images. There is no way to iterate locally:

- `uv run build` builds x86 images on the host — useless for the Jetson
- CI builds ARM64 but requires pushing to the branch and waiting
- The `_meter_and_lock` comment-out hasn't been tested because of this

### Agreed approach: Local registry over USB

Run a local Docker registry on the host machine, cross-compile ARM64 images with `docker buildx --platform linux/arm64` (QEMU emulation), push to the local registry, and have the Jetson pull from it over the USB ethernet link (`192.168.55.100:5000`).

**What needs to happen:**

1. **One-time host setup:**
   ```
   docker run -d -p 5000:5000 --name registry --restart unless-stopped registry:2
   ```

2. **Configure Jetson Docker for insecure registry** (already have `systemctl` in sudoers):
   Add `"insecure-registries": ["192.168.55.100:5000"]` to `/etc/docker/daemon.json` on the Jetson, restart Docker. This should be done by deploy-rig as part of one-time setup.

3. **Build + push workflow:**
   ```
   docker buildx build --platform linux/arm64 \
     -t 192.168.55.100:5000/zed-capture:latest \
     --push .
   ```

4. **Deploy-rig `--local` flag:**
   - Skip NAT/internet sharing (not needed — registry is on the USB link)
   - Pull from `192.168.55.100:5000/zed-capture:latest` instead of ghcr
   - Everything else stays the same (daemons, warm-up, compose)

5. **Layer-aware by default** — Docker registry protocol is natively layer-aware. First push is slow (full image), subsequent pushes only transfer changed layers.

**Open questions:**
- Does the existing `compose.bake.yml` support `--platform` override easily, or do we need a separate build command?
- QEMU cross-compile speed — first build will be slow, but subsequent builds with only Python source changes should be fast (only top COPY layers rebuild)
- Should `--local` be the default when USB link is detected, or always explicit?

## Other known issues

### `zed_x_daemon` socket not found
The container logs still show `[ZED-X][Warning] Failed to connect to zed_x_daemon.` despite mounting the three sockets found in `/tmp`. The daemon is running on the host but may communicate via a different mechanism (shared memory, socket outside `/tmp`, etc.). This didn't prevent the camera from opening but may affect some features.

To investigate:
```
ssh user@192.168.55.1 "find / -name '*zed_x*' -o -name '*ZEDX*' 2>/dev/null"
ssh user@192.168.55.1 "ls /dev/shm/"
ssh user@192.168.55.1 "strace -e connect -p $(pgrep ZEDX_Daemon) 2>&1 | head -20"
```

### `_meter_and_lock` incompatible with ZED X
The `set_camera_settings_roi` call fails with `FAILURE` on ZED X. This function was written for ZED 2 (USB) where software-controlled auto-exposure metering was needed. The ZED X has a dedicated ISP that may handle this automatically. Currently commented out in `zed.py:206-210` — needs testing once local deploy workflow is working.

## Historical context (from previous session)

### USB gadget mode
The ZED Box connects to phones via USB gadget mode (micro USB port). The Jetson presents as a USB ethernet device at `192.168.55.1`. The host machine also connects at this IP for deployment. See the "ZED Box Port Layout" section in the git history of this file for detailed hardware notes.

### Key addresses
- ZED Box: `192.168.55.1` (USB gadget ethernet)
- Host USB IP: `192.168.55.100`
- ZED capture API: `http://192.168.55.1:9000`
- Scalar UI: `http://192.168.55.1:9000/schema`
- SSH: `user@192.168.55.1` (key-based auth, no password)
