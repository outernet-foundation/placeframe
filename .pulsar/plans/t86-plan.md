# T86 Plan: Content-hash versioning and automated publishing

## Context

Package versions are bumped manually. If source changes but the version isn't bumped, CI skips publishing and the registry stays stale. This already caused a production issue (NuGet `PlaceframeApiClient@0.1.3` missing `LocalizationMetrics` fields). This plan automates the entire pipeline: detect source changes via content hashing, auto-bump patch versions, publish to npm/NuGet, cascade dependency updates, and commit state back to the repo.

## Approach

### 1. Create `publish-state.json` (repo root)

Seed with current published versions and empty hashes. First CI run will see hash mismatch, bump all versions by one patch, publish everything, and commit real hashes.

```json
{
  "nuget": { "version": "0.1.4", "hash": "" },
  "core": { "version": "1.0.1", "hash": "" },
  "arfoundation": { "version": "1.0.1", "hash": "" },
  "magicleap": { "version": "1.0.1", "hash": "" }
}
```

### 2. Add `publish-state.json merge=ours` to `.gitattributes`

One line, follows existing `.env.lock` pattern.

### 3. Add `org.nuget.placeframeapiclient` dependency to Core's `package.json`

Add `"org.nuget.placeframeapiclient": "0.1.4"` to the dependencies object. This makes the API client a transitive dependency for external consumers who install Core from npm. Local dev continues using `file:` references.

### 4. Fix stale dependency pins

- ARFoundation: `"org.outernet.placeframe": "1.0.0"` → `"1.0.1"`
- MagicLeap: `"org.outernet.placeframe": "1.0.0"` → `"1.0.1"`

### 5. Rewrite `.github/workflows/publish-upm.yml`

**Triggers:** Push to `main` only (+ `workflow_dispatch`). `paths-ignore` for `publish-state.json` and the 3 UPM `package.json` files (all CI-written, prevents re-trigger loop).

```yaml
on:
  push:
    branches: [main]
    paths-ignore:
      - "publish-state.json"
      - "packages/unity/Placeframe/Assets/Package/Core/package.json"
      - "packages/unity/Placeframe/Assets/Package/ARFoundation/package.json"
      - "packages/unity/Placeframe/Assets/Package/MagicLeap/package.json"
  workflow_dispatch:
```

**Permissions:** `contents: write` (for commit-back), `id-token: write` (for OIDC).

**Tool setup:** Node 24 (npm), .NET SDK 8.0 (dotnet pack/push), `NuGet/login@v1` (OIDC token exchange → short-lived API key).

**Workflow steps (sequential within single job):**

1. **Checkout** with `token: ${{ secrets.GITHUB_TOKEN }}` for push access
2. **Setup** Node 24, .NET 8.0, NuGet OIDC login
3. **Compute hashes** for all 4 packages:
   - NuGet: `find ... -name '*.cs' -not -path '*/bin/*' -not -path '*/obj/*' | sort | xargs sha256sum | sha256sum`
   - UPM: `find <dir> -type f -not -name 'package.json' | sort | xargs sha256sum | sha256sum`
4. **Compare** each hash against `publish-state.json`. Determine publish set with cascade:
   - NuGet hash changed → publish NuGet, force-bump Core
   - Core hash changed OR cascaded → publish Core, force-bump ARFoundation + MagicLeap
   - ARFoundation/MagicLeap hash changed OR cascaded → publish each
   - Version bump = increment patch (read from state file)
5. **Publish NuGet** (if needed): `dotnet pack -p:Version=X.Y.Z`, `dotnet nuget push --api-key <OIDC key>`
6. **Update Core package.json**: write new version, update NuGet dep version if cascaded
7. **Publish Core** (if needed): `npm publish --access public --provenance`
8. **Update ARFoundation/MagicLeap package.json**: write new version, update Core dep version if cascaded
9. **Publish ARFoundation/MagicLeap** (if needed)
10. **Update `publish-state.json`**: write new versions + current hashes for ALL packages
11. **Commit and push**: `git add publish-state.json packages/unity/Placeframe/Assets/Package/*/package.json`, commit, push. Mirrors `build-docker.yml` commit-back pattern. No-op if nothing changed.

**Cascade dependency graph:**
```
NuGet → Core → ARFoundation
                MagicLeap
```

### Hash design notes

- **package.json excluded** from UPM hash (contains CI-written version field). Trade-off: manual dependency additions to package.json won't trigger publish. Acceptable — extremely rare, can use `workflow_dispatch`.
- **.meta files included** in UPM hash (contain Unity import settings that affect behavior).
- **.csproj excluded** from NuGet hash (implicitly, by only hashing `*.cs` files). Regenerated with fixed `0.1.0` version.
- **Deterministic**: `find | sort | xargs sha256sum | sha256sum` — sorted paths, individual file hashes, combined into one.

## Key files

| File | Action |
|---|---|
| `.github/workflows/publish-upm.yml` | Rewrite (content-hash logic, NuGet publish, cascade, commit-back) |
| `publish-state.json` | Create (seed with current versions, empty hashes) |
| `.gitattributes` | Add `publish-state.json merge=ours` |
| `packages/unity/Placeframe/Assets/Package/Core/package.json` | Add NuGet dep |
| `packages/unity/Placeframe/Assets/Package/ARFoundation/package.json` | Fix Core dep pin |
| `packages/unity/Placeframe/Assets/Package/MagicLeap/package.json` | Fix Core dep pin |

Reference (read-only):
- `.github/workflows/build-docker.yml` — commit-back pattern template
- `packages/generated/csharp/api-client/src/PlaceframeApiClient/PlaceframeApiClient.csproj` — NuGet package metadata
- `scripts/openapi-generator/configs/csharp.json` — hardcoded version `0.1.0`

## Manual setup (user actions, not code)

1. Configure NuGet OIDC trusted publishing policy on nuget.org for `PlaceframeApiClient` (repo: `outernet-foundation/placeframe`, workflow: `publish-upm.yml`)
2. Add `NUGET_USER` repository secret (nuget.org username)

## Verification

1. Merge to main → first run publishes all 4 packages (sentinel hash mismatch)
2. Commit-back push should NOT re-trigger (all modified files in `paths-ignore`)
3. Second push with no source changes → workflow triggers but skips all publishes
4. Change only one NuGet `.cs` file → all 4 packages publish (full cascade)
5. Change only an ARFoundation `.cs` file → only ARFoundation publishes (no cascade)
6. `npm view org.outernet.placeframe@<version>` confirms npm publish
7. NuGet.org shows new `PlaceframeApiClient` version
