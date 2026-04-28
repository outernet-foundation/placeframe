# T10: ZED Capture Docker Images

## Context

The ZED camera capture service (`zed/`) deploys via SSH/tarball to bare-metal Jetsons. This ticket containerizes it with Docker images built in CI and pushed to GHCR, cross-compiled for aarch64 via QEMU.

## Approach

### 1. Remove vendored pyzed wheels and dependencies

Delete `zed/third-party/pyzed/` entirely. In `zed/pyproject.toml`:
- Remove `"pyzed"` from `[project] dependencies`
- Remove all three `[[tool.uv.sources.pyzed]]` entries (win_amd64, linux_aarch64, linux_x86_64)
- Add this comment above the dependencies list:
  ```
  # pyzed (Stereolabs ZED SDK Python bindings) is NOT listed here. The "pyzed" package
  # on PyPI is an unrelated project. The real pyzed can only be obtained by running
  # get_python_api.py from a ZED SDK installation, which generates a platform-specific
  # wheel matching the installed SDK version. It is installed at Docker build time inside
  # the Stereolabs base image — see zed/Dockerfile.
  ```
- Add `"pyzed"` to the existing `[tool.deptry.per_rule_ignores]` section under `DEP002` (missing dependency — pyzed is imported but not declared). The section already has `DEP002 = ["uvicorn"]`, so extend it to `DEP002 = ["uvicorn", "pyzed"]`.

Run `uv lock` to regenerate the workspace lock file. This will produce a significant diff in `uv.lock` since all pyzed resolution entries (4 variants: PyPI 1.3.0 + 3 vendored wheels) will be removed.

### 2. Create `zed/Dockerfile`

Place at `zed/Dockerfile` so `lock_python.py` discovers it for pylock export (it checks for `Dockerfile` in workspace member dirs).

```dockerfile
ARG ZED_BASE_IMAGE
FROM ${ZED_BASE_IMAGE}

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app/zed

ENV \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_NO_INSTALLER_METADATA=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/uv/venv \
    VIRTUAL_ENV=/opt/uv/venv

# Stereolabs base images don't include Python 3.13
RUN uv python install 3.13

RUN uv venv $UV_PROJECT_ENVIRONMENT

# Generate pyzed wheel matching the installed ZED SDK version.
# get_python_api.py ships inside the SDK and outputs a wheel to /usr/local/zed/.
# Running under QEMU on aarch64 ensures the correct platform wheel is produced.
RUN uv run --python 3.13 /usr/local/zed/get_python_api.py
RUN --mount=type=cache,id=uvcache,sharing=locked,target=/root/.cache/uv \
    uv pip install /usr/local/zed/pyzed*.whl

# Install remaining dependencies from lock file
COPY zed/pylock.toml ./pylock.toml
RUN --mount=type=cache,id=uvcache,sharing=locked,target=/root/.cache/uv \
    uv pip install -r pylock.toml

# Install source packages
COPY packages/python/common /app/packages/python/common
COPY packages/python/core /app/packages/python/core
COPY zed /app/zed
RUN uv pip install --no-deps --no-sources \
    /app/packages/python/common \
    /app/packages/python/core \
    /app/zed

RUN uv pip check

COPY --chmod=0755 zed/entrypoint.sh /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
```

**Notes on the Dockerfile:**
- No ARG defaults — `ZED_BASE_IMAGE` is always passed explicitly by the bake target.
- The `get_python_api.py` output path (`/usr/local/zed/pyzed*.whl`) may vary by SDK version. If it outputs elsewhere (e.g. `/tmp/`), adjust the glob. Check by inspecting the Stereolabs base image if the build fails.
- `uv pip check` will verify pyzed is installed (it's a runtime import) even though it's not in pyproject.toml dependencies. Wait — actually `uv pip check` only checks declared metadata deps, so it won't flag the missing declaration. It WILL verify that pyzed's own declared deps (cython, numpy) are satisfied.

### 3. Create `zed/entrypoint.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

cd /app/zed

echo "Starting ZED Capture"

exec uv run --no-sync uvicorn src.main:app --host 0.0.0.0 --port 9000
```

### 4. Add bake targets to `compose.bake.yml`

Append after the existing `localizer-rocm` service:

```yaml
  zed-capture-jp62:
    build:
      context: .
      dockerfile: zed/Dockerfile
      platforms: ["linux/arm64"]
      args:
        ZED_BASE_IMAGE: "stereolabs/zed:5.0-runtime-jetson-jp6.2"
      tags: ["ghcr.io/outernet-foundation/placeframe/zed-capture-jp62:latest"]

  zed-capture-jp51:
    build:
      context: .
      dockerfile: zed/Dockerfile
      platforms: ["linux/arm64"]
      args:
        ZED_BASE_IMAGE: "stereolabs/zed:4.2-runtime-jetson-jp5.1.2"
      tags: ["ghcr.io/outernet-foundation/placeframe/zed-capture-jp51:latest"]
```

Do NOT use `*base-args` — these use a completely different base image chain (Stereolabs L4T, not UV/Python bookworm).

### 5. Filter JetPack targets from default local builds

In `build/src/build_scripts/placeframe/build_docker.py`:

Add near the top (after the existing imports that reference `GPU_TYPES`):
```python
JETPACK_SUFFIXES = ("jp62", "jp51")
```

Modify the target filter (line ~179-183) from:
```python
targets = [
    service
    for service in bake_data["services"]
    if not any(service.endswith(f"-{g}") for g in GPU_TYPES) or service.endswith(f"-{gpu}")
]
```
to:
```python
targets = [
    service
    for service in bake_data["services"]
    if (not any(service.endswith(f"-{g}") for g in GPU_TYPES) or service.endswith(f"-{gpu}"))
    and not any(service.endswith(f"-{s}") for s in JETPACK_SUFFIXES)
]
```

This ensures JetPack targets are never auto-included. They can still be built via `uv run build --targets zed-capture-jp62`.

### 6. Add dedicated `build-zed` CI job

In `.github/workflows/build-unity.yml`, add a standalone `build-zed` job. This does NOT use the CI wrapper (`ci/build_docker.py` / `build-docker` command) because that has a `Variant` type and hardcoded target lists. Instead, it calls the main `build` command directly:

```yaml
  build-zed:
    needs: [preflight]
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    name: build-zed
    steps:
      - name: Checkout Code
        uses: actions/checkout@v5
        with:
          ref: ${{ github.head_ref || github.ref_name }}

      - uses: ./.github/actions/setup-uv

      - name: Set up QEMU
        uses: docker/setup-qemu-action@v3
        with:
          platforms: arm64

      - name: Create builder and login
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          docker buildx create --use --driver docker-container
          echo "$GITHUB_TOKEN" | docker login ghcr.io -u ${{ github.actor }} --password-stdin

      - name: Build
        run: uv run build --mode ci --gpu none --targets zed-capture-jp62 --targets zed-capture-jp51

      - name: Upload .env.lock
        uses: actions/upload-artifact@v6
        with:
          name: env-lock-zed
          path: .env.lock
          include-hidden-files: true
```

**Key details:**
- Uses `uv run build` (the main `build_docker.py` entry point), NOT `uv run build-docker` (the CI wrapper). The main entry point handles digest resolution, bake invocation, and `.env.lock` writing.
- `--gpu none` — the value doesn't matter since targets are explicit, but the flag is required in CI mode validation. Actually, check: the main `build` command uses `--gpu auto` by default locally and doesn't require it. But `--mode ci` with `--gpu auto` raises a `BadParameter`. So pass `--gpu none` or `--gpu cuda` (either works since targets are explicit).
- The `.env.lock` artifact is uploaded with name `env-lock-zed` to avoid collision with the existing `env-lock-{variant}` artifacts.

### 7. Generate `zed/pylock.toml`

Run `uv run lock-python` after the Dockerfile exists. With pyzed removed from dependencies, the pylock export is clean — no path resolution issues, no pyzed entries.

## Key files

| File | Action | Notes |
|---|---|---|
| `zed/Dockerfile` | Create | ZED_BASE_IMAGE arg, get_python_api.py at build time |
| `zed/entrypoint.sh` | Create | uvicorn startup script |
| `zed/pyproject.toml` | Modify | Remove pyzed dependency and sources, add comments, update deptry |
| `zed/third-party/pyzed/` | Delete | Vendored wheels no longer needed |
| `compose.bake.yml` | Modify | Add zed-capture-jp62 and zed-capture-jp51 targets |
| `build/src/build_scripts/placeframe/build_docker.py` | Modify | Add JETPACK_SUFFIXES filtering |
| `.github/workflows/build-unity.yml` | Modify | Add build-zed job with QEMU |
| `zed/pylock.toml` | Generate | Via `uv run lock-python` |
| `uv.lock` | Regenerate | Via `uv lock` after removing pyzed |

## Verification

- `docker buildx bake -f compose.bake.yml zed-capture-jp62 --print` exits 0
- `docker buildx bake -f compose.bake.yml zed-capture-jp51 --print` exits 0
- `build-zed` job present in `build-unity.yml`
- `uv run ruff check .` and `uv run basedpyright` pass on modified Python files
- `uv lock --check` passes
- `uv run lock-python --check` passes
