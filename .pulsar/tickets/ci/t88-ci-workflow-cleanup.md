---
id: T88
title: CI workflow cleanup on feature/ci-improvements-3
status: in-review
depends_on: []
---

# T88: CI workflow cleanup on feature/ci-improvements-3

## Goal

Fix issues discovered during review of the `feature/ci-improvements-3` branch, before merging CI work to main. Includes redundant workflow lines, a dead script, and incorrect manifest references.

## Context

During review of the `feature/ci-improvements-3` branch, several issues were found: redundancies in the Docker build workflow, an obsolete shell script, and app manifests incorrectly using registry versions instead of `file:` references for monorepo packages. The registry switch was part of T71 but the decision was later reversed — monorepo apps should use `file:` paths so local edits take effect without a publish cycle.

## Key files

- `.github/workflows/build-docker.yml`
- `scripts/build-cesium-native-linux.sh`
- `apps/AndroidMobile/Packages/manifest.json`
- `apps/MakeItSing/Packages/manifest.json`
- `apps/MapRegistrationTool/Packages/manifest.json`
- `legacy/Outernet.Client/Packages/manifest.json`

## Approach

Six changes:

1. **Remove `token` from checkout step** (line 27). `token: ${{ secrets.GITHUB_TOKEN }}` is the default for `actions/checkout@v4` — specifying it is redundant. The `ref` override on line 26 is still needed for the `.env.lock` commit-and-push step.

2. **Simplify `if` condition on lock-commit step** (line 80). The `github.event_name == 'push'` half is redundant because on push events `github.head_ref` is empty, so `!contains(["main","dev"], "")` is already true. Simplify from:
   ```
   if: github.event_name == 'push' || !contains(fromJSON('["main","dev"]'), github.head_ref)
   ```
   to:
   ```
   if: "!contains(fromJSON('[\"main\",\"dev\"]'), github.head_ref)"
   ```

3. **Delete `scripts/build-cesium-native-linux.sh`**. Obsolete shell script from T69, replaced by `scripts/src/scripts/build_cesium_native_linux.py` in T70. The CI workflow calls the Python version via `uv run build-cesium-native-linux`.

4. **Fold content-hash publish commit into UPM publishing commit.** The "Content-hash publish pipeline" commit (`.gitattributes` merge=ours for publish-state.json, `publish-state.json` initial state) is orphaned — both files are part of the publish-upm pipeline and belong in the same commit that creates `publish-upm.yml`. Merge them during the next `/tidy-commits`.

5. **Revert app manifests to `file:` references for monorepo packages.** T71 switched all Placeframe package references from `file:` paths to registry versions (`org.outernet.placeframe: 1.0.1`). That decision was reversed — monorepo apps should use `file:` paths for packages that live in the repo. Revert the Placeframe and generated client references in all four app manifests back to `file:` relative paths. The scoped registry entries for `org.outernet` and the Cesium fork (`org.outernet.cesium-unity`) should remain since those packages are NOT in the monorepo. Origin/main has the correct `file:` path patterns to reference:
   - `org.outernet.placeframe` → `file:` path to `packages/unity/Placeframe/Assets/Package/Core`
   - `org.outernet.placeframe.arfoundation` → `file:` path to `packages/unity/Placeframe/Assets/Package/ARFoundation`
   - `org.outernet.placeframe.magicleap` → `file:` path to `packages/unity/Placeframe/Assets/Package/MagicLeap`
   - `org.nuget.placeframeapiclient` → `file:` path to `packages/generated/csharp/api-client/src/PlaceframeApiClient`
   - `org.nuget.placeframezedclient` → `file:` path to `packages/generated/csharp/zed-client/src/PlaceframeZedClient`

   Note: the package *names* changed (`com.placeframe.vps` → `org.outernet.placeframe`, etc.) so the `file:` entries use the new names, not the origin/main names. The relative paths stay the same.

6. **Regenerate `packages-lock.json` via Unity batchmode.** After all manifest changes (items 4-5), run Unity batchmode on each project to regenerate lock files. Never hand-edit these — Unity generates them during package resolution. Add the regenerated files in a dedicated commit after the other CI code commits. Projects to regenerate: `apps/AndroidMobile`, `apps/MakeItSing`, `apps/MapRegistrationTool`, `legacy/Outernet.Client`. Requires Unity installed in the sandbox (`/opt/unity/6000.0.66f1/Editor/Unity` via `xvfb-run`).

## Done when

- `token:` line removed from the Checkout step
- `if:` condition on lock-commit step simplified to only the `!contains(...)` guard
- `scripts/build-cesium-native-linux.sh` deleted
- App manifests use `file:` references for all packages that live in the monorepo
- Registry references retained only for external packages (Cesium fork, Magic Leap)
- Content-hash commit folded into UPM publishing commit
- Regenerated `packages-lock.json` files in a dedicated commit after CI code commits

## Log

- Generated C# packages (`com.placeframe.api-client`, `com.placeframe.zed-client`) still use old names in their `package.json`. Initial manifest commit used `org.nuget.*` keys which Unity rejected — `file:` paths require the manifest key to match the package's own `name` field. Fixed in a follow-up commit using the original `com.placeframe.*` names.
- Unity batchmode failed on cold project open: R3.Unity compilation errors because NuGetForUnity couldn't restore R3.dll before compilation. Root cause: dotnet SDK not installed in COI sandbox, so `dotnet nugetforunity restore` (used by CI in `build-unity.yml`) wasn't available. Installed dotnet 8.0 manually, ran NuGet restore, then Unity compiled clean. Filed T89 to add dotnet to the COI image.
- Item 4 (fold content-hash commit into UPM publishing commit) is deferred to `/tidy-commits` as specified in the ticket.

## Observations

- `apps/AndroidMobile/Assets/packages.config` specifies R3 NuGet version 1.3.0, but the manifest pins R3.Unity at `#1.2.9`. This version mismatch exists on main and predates this branch. Should be 1.2.9 in packages.config to match.
