# T70: Automate Cesium native Linux build and publish to UPM registry

## Context

T69 manually built the Cesium for Unity Linux native plugin and committed the binaries (~100-150 MB) directly to the repo as a temporary measure. T71 set up the `org.outernet` scoped registry on npmjs.org with OIDC trusted publishing. T70 closes the loop: automate the build in CI, publish to the registry, and remove the committed binaries from the repo.

## Approach

### 1. Convert shell script to Python

Convert `scripts/build-cesium-native-linux.sh` to `scripts/src/scripts/build_cesium_native_linux.py`. Follow the established pattern (T7's `build_unity.py`, `migrate_database.py`): Typer CLI, `common.run_command`/`check_command`, registered as `uv run build-cesium-native-linux`.

CLI options:
- `--build-dir` (default `/tmp/cesium-build`)
- `--cesium-version` (default `v1.15.3`)
- `--unity-editor` (default from `UNITY_EDITOR` env var, fallback to `/opt/unity/6000.0.66f1/Editor/Unity`)

The script is a direct port — same steps, same idempotency, same structure. Use `run_command` with `stream_log=True` for cmake builds (long-running). Use `check_command` for idempotency checks (e.g., `command -v cmake`). Write the vcpkg triplet file using Python's `Path.write_text()` instead of heredoc.

### 2. Register the command

Add to `scripts/pyproject.toml`:
```toml
build-cesium-native-linux = "scripts.build_cesium_native_linux:main"
```

### 3. Rename package for registry

Update `packages/unity/com.cesium.unity/package.json`:
- Change `name` from `com.cesium.unity` to `org.outernet.cesium-unity`
- Keep version `1.15.3-linux.1`
- Add `repository` field (matching Placeframe package pattern)

This package stays in the repo temporarily as the "source of truth" for what gets published. The CI workflow will eventually build fresh and publish, but until that workflow is proven, keeping the package ensures nothing breaks.

### 4. Create CI workflow: `build-cesium-native.yml`

Separate workflow (not extending `publish-upm.yml` — fundamentally different job: 30-60 min cmake build vs quick npm publish).

**Trigger**: `workflow_dispatch` only (manual). Cesium version bumps are rare. Add input for `cesium-version` (default `v1.15.3`).

**Runner**: `ubuntu-latest` with `unityci/editor:6000.0.66f1-linux-il2cpp-3` container (same pattern as `build-unity.yml`).

**Steps**:
1. Free disk space (same volume-mount trick as `build-unity.yml`)
2. Checkout
3. Activate Unity license (serial-based, same pattern as T7/T79 — no error swallowing)
4. Install build deps (`apt-get`: cmake, ninja-build, nasm, g++, zip, unzip, pkg-config)
5. Setup .NET SDK 8.0 (`actions/setup-dotnet@v4`)
6. Setup UV (`astral-sh/setup-uv@v5`)
7. Run `uv run build-cesium-native-linux --cesium-version ${{ inputs.cesium-version }}`
8. Prepare package: copy built `.so` files into `packages/unity/com.cesium.unity/` (the fork directory with C# source + package.json)
9. Setup Node.js 24 (for npm OIDC publish)
10. Publish to npmjs.org with `--access public --provenance` (same pattern as `publish-upm.yml` — check if version already exists, skip if so)
11. Return Unity license (`always()`, best-effort)

**Permissions**: `contents: read`, `id-token: write` (OIDC)

**Caching**: The vcpkg/cmake build is the expensive part (30-60 min first run). Cache the vcpkg binary cache (`~/.cache/vcpkg`) and cmake build directories via ORAS/GHCR (same pattern as T78's Library caching). Steps:
- After build: tar + zstd the vcpkg cache, push to `ghcr.io/<repo>/cache/cesium-vcpkg:latest`
- Before build: pull and restore if available
- This turns subsequent builds from 30-60 min to ~5-10 min (only relinks, no recompilation)
- Requires `packages: write` permission (already needed for ORAS push)

### 5. Update consumer manifests

Update both manifests to reference the registry package:

`apps/MapRegistrationTool/Packages/manifest.json`:
- Remove: `"com.cesium.unity": "file:../../../packages/unity/com.cesium.unity"`
- Add: `"org.outernet.cesium-unity": "1.15.3-linux.1"`

`legacy/Outernet.Client/Packages/manifest.json`:
- Same change

Both manifests already have the `org.outernet` scope in their `scopedRegistries` config (from T71). No scoped registry changes needed.

### 6. Regenerate packages-lock.json files

After changing the manifests, open each Unity project in batchmode to regenerate `packages-lock.json` with the updated package references. Unity is installed and licensed in this container:
```bash
xvfb-run /opt/unity/6000.0.66f1/Editor/Unity -batchmode -nographics -quit \
  -projectPath apps/MapRegistrationTool -logFile /dev/stdout
```
Same for `legacy/Outernet.Client`. This ensures the lock files reflect actual package resolution rather than manual edits.

### 7. Remove committed binary (deferred)

The ticket says to remove `packages/unity/com.cesium.unity/` from the repo. However, this should only happen AFTER:
1. The CI workflow is proven to work (successfully builds and publishes)
2. Consumer manifests are verified to resolve from the registry

Since we can't run the CI workflow from this environment (read-only GitHub token), removal should be a follow-up step after the first successful CI run. Document this in the ticket's Next step.

**Alternative**: Remove now and accept that the package only exists on the registry. This is cleaner but riskier — if the CI workflow has issues, there's no fallback.

Recommend: Keep the directory but update the package.json name. Remove after first successful CI publish.

### 8. Document rebuild triggers

Add a section to the workflow file (as YAML comments) or to the ticket documenting when to re-trigger:
- Cesium version bump (change `cesium-version` input)
- Unity version bump (update container image tag)
- Linux platform fixes in Cesium upstream

## Key files

| File | Action |
|------|--------|
| `scripts/build-cesium-native-linux.sh` | Read (reference for conversion) |
| `scripts/src/scripts/build_cesium_native_linux.py` | Create (new Python script) |
| `scripts/pyproject.toml` | Modify (add entry point) |
| `.github/workflows/build-cesium-native.yml` | Create (new CI workflow) |
| `packages/unity/com.cesium.unity/package.json` | Modify (rename to `org.outernet.cesium-unity`) |
| `apps/MapRegistrationTool/Packages/manifest.json` | Modify (registry reference) |
| `legacy/Outernet.Client/Packages/manifest.json` | Modify (registry reference) |
| `apps/MapRegistrationTool/Packages/packages-lock.json` | Modify (update package reference) |
| `legacy/Outernet.Client/Packages/packages-lock.json` | Modify (update package reference) |

## Verification

- `uv run ruff check .` and `uv run ruff format --check .` pass on new Python script
- `uv run basedpyright` passes on new Python script
- `uv run build-cesium-native-linux --help` works (CLI registered correctly)
- CI workflow YAML is valid (can lint with `actionlint` if available)
- Consumer manifests have correct JSON syntax
- Package.json has valid npm package name (`org.outernet.cesium-unity`)
- After first manual CI run: verify package appears on npmjs.org, Unity projects resolve it from registry
