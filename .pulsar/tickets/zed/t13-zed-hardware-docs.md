---
id: T13
title: ZED refactor wrap-up — hardware validation and README
status: plan-needed
---

The `feature/zed-refactor` branch containerized the ZED capture service (Dockerfile, bake target, pyzed stubs), replaced per-frame JPEG writes with SVO hardware-encoded recording, and added a zero-internet `deploy-rig` script. All code changes pass static analysis (`basedpyright`, `ruff`). No regressions from the rebase onto main.

What remains is hardware validation and documentation:

1. **Validate on ZED hardware** — SVO recording produces `video.svo2`, frame extraction writes JPEGs to `camera0/`/`camera1/`, `deploy-rig` transfers and starts the container on the ZED Box.
2. **Verify CI `build-zed` job** — confirm the aarch64 QEMU cross-compilation job passes in GitHub Actions (requires pushing the branch).
3. **Rewrite `docker/zed-capture/README.md`** — replace the developer-facing JetPack setup guide with a user-facing hardware quickstart: BOM, cable connections, one-command `uv run deploy-rig` workflow.

Completed work (T10, T11, T12 — now deleted):
- `docker/zed-capture/Dockerfile` + `docker/zed-capture/entrypoint.sh` — containerized ZED capture for JetPack 6.2
- `docker/zed-capture/compose.rig.yml` — minimal compose for the ZED Box
- `typings/pydocker/zed-capture/sl.pyi` — vendored type stubs (pyzed removed from uv deps)
- `docker/zed-capture/src/docker/zed-capture/zed.py` — SVO recording in `_start`, stripped image writes from `_capture_frame`, added `_extract_frames_from_svo` in `_stop`
- `docker/zed-capture/src/docker/zed-capture/zed_wrapper.py` — `enable_recording`, `disable_recording`, `set_from_svo_file` wrappers
- `scripts/src/scripts/deploy_rig.py` — zero-internet deploy over USB gadget link
- `docker/zed-capture/install.py` deleted, `docker/zed-capture/third-party/pydocker/zed-capture/` deleted
