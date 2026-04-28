# T71 Plan: Publish UPM packages to npmjs.org

## Context

Placeframe UPM packages are currently consumed via `file:` relative paths, which means transitive dependencies don't resolve — every consumer must manually list the full dependency tree. Publishing to npmjs.org (the public npm registry) gives proper dependency resolution, external accessibility, and follows the same pattern already used for Magic Leap packages in this project. The generated C# clients (api-client, zed-client) are already published to NuGet and available via the UnityNuGet registry.

## Registries

| Registry | URL | Scope | Packages |
|---|---|---|---|
| npmjs.org | `https://registry.npmjs.org` | `com.placeframe` | vps, vps.arfoundation, vps.magicleap |
| UnityNuGet (OpenUPM) | `https://unitynuget-registry.openupm.com` | `org.nuget` | placeframeapiclient, placeframezedclient |

## Approach

### Phase 1: Package metadata fixes + publish workflow (this session)

1. **Fix package.json files** (3 files). Add `license` (Apache-2.0), `repository` fields. Add missing inter-package dependency: ARFoundation and MagicLeap both depend on Core (`com.placeframe.vps`) via their `.asmdef` references but don't declare it in `package.json` dependencies.

2. **Create `.github/workflows/publish-upm.yml`**. Trigger: `workflow_dispatch` + push tags matching `v*`. Uses `actions/setup-node@v4` with `registry-url: https://registry.npmjs.org`. Publishes each package with `npm publish --access public`. Each step checks if the version already exists (idempotent). Requires `NPM_TOKEN` repository secret.

3. **Update manifest.json files** (4 projects). Two scoped registry entries needed per project:
   - npmjs.org with scope `com.placeframe` (can merge with existing Magic Leap entry since same URL)
   - UnityNuGet with scope `org.nuget`

   Switch all Placeframe package refs from `file:` paths to registry versions:
   - `com.placeframe.vps`: `"1.0.0"` (from npmjs.org)
   - `com.placeframe.vps.arfoundation`: `"1.0.0"` (from npmjs.org)
   - `com.placeframe.vps.magicleap`: `"1.0.0"` (from npmjs.org)
   - `com.placeframe.api-client` → `org.nuget.placeframeapiclient`: `"0.1.3"` (from UnityNuGet)
   - `com.placeframe.zed-client` → `org.nuget.placeframezedclient`: `"0.1.3"` (from UnityNuGet)

   **Note:** The vps packages won't resolve until after the first npm publish. The NuGet packages should resolve immediately since they're already published.

4. **Fix MakeItSing absolute Windows paths** (pre-existing issue, opportunistic).

### Manual steps (user)

- Create an npm account (if needed) and generate a granular access token scoped to `com.placeframe.*`
- Add `NPM_TOKEN` as a repository secret in GitHub
- Trigger the first publish via workflow_dispatch
- Verify packages are resolvable: `npm view com.placeframe.vps`

## Key files

**Modify:**
- `packages/unity/Placeframe/Assets/Package/Core/package.json` — add `license`, `repository`
- `packages/unity/Placeframe/Assets/Package/ARFoundation/package.json` — add `license`, `repository`, add `com.placeframe.vps` dependency
- `packages/unity/Placeframe/Assets/Package/MagicLeap/package.json` — add `license`, `repository`, add `com.placeframe.vps` dependency
- `apps/AndroidMobile/Packages/manifest.json` — add scoped registries, switch to version refs
- `apps/MapRegistrationTool/Packages/manifest.json` — add scoped registries, switch to version refs
- `apps/MakeItSing/Packages/manifest.json` — add scoped registries, switch to version refs, fix absolute Windows paths
- `legacy/Outernet.Client/Packages/manifest.json` — add scoped registries, switch to version refs

**Create:**
- `.github/workflows/publish-upm.yml` — publish workflow

## Design notes

- **Cysharp dependencies (unitask, r3) are git-URL sourced by consumers.** The version strings in package.json (`"2.5.10"`) may cause UPM warnings if the git-sourced version doesn't exactly match. This is pre-existing behavior, not introduced by this change.
- **No `.npmignore` needed.** Package directories contain only files Unity needs (`.cs`, `.asmdef`, `.meta`, assets). No test directories, no build artifacts.
- **api-client/zed-client name change.** Consumers switch from `com.placeframe.api-client` to `org.nuget.placeframeapiclient`. Assembly names (`PlaceframeApiClient`) stay the same, so `.asmdef` references continue to work.

## Verification

- `npm pack --dry-run` in each package directory to see what would be published
- After publish: `npm view com.placeframe.vps` returns package metadata
- After manifest update: Unity projects resolve all packages from registries (requires Unity — manual verification)
