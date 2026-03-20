## Implementation Plan: Replace `versions.json` with Per-Package Git Tags

### Context

The `versions.json` file and `package.json` version patches are committed to `main` during CI release, creating main-only commits that prevent fast-forward merges from `dev` to `main`. Replacing these with git tags (which are not commits) eliminates this divergence source, a prerequisite for the broader CI simplification tracked in T3.

### Approach

#### Step 1: Add git tag helper functions to `publish_packages.py`

Add two utility functions at the top of the module:

- `get_latest_tag_version(prefix: str) -> str | None` -- Runs `git tag --list "{prefix}*" --sort=-v:refname` and parses the latest tag to extract the version string. Returns `None` if no tags match. Use `bash_output` to capture the output and split on newlines, taking the first result. The `--sort=-v:refname` flag performs version-aware sorting natively in git, which correctly handles semver without needing a Python semver library.

- `has_changes_since_tag(tag: str, path: Path) -> bool` -- Runs `git diff --quiet {tag} HEAD -- {path}` via `bash_check` (which returns `True` if exit code is 0). Returns the negation (changes exist when diff is NOT quiet). If the tag is `None` (no prior tag), return `True` unconditionally (first-publish case).

**Rationale for `--sort=-v:refname`**: This is a git built-in that handles `v0.1.5` vs `v0.1.10` correctly. It avoids pulling in a Python semver library.

#### Step 2: Refactor the "Compute publish plan" section of `publish_packages.py`

Replace the hash-based change detection loop (lines 89-117) with:

```python
publish: dict[str, bool] = {}
versions: dict[str, str] = {}
for name, config in PACKAGES.items():
    last_version = get_latest_tag_version(f"{name}-v")
    changed = has_changes_since_tag(f"{name}-v{last_version}" if last_version else None, config.path)
    # Preserve dependency cascading
    if config.depends_on and publish.get(config.depends_on, False):
        changed = True
    publish[name] = changed
    if changed:
        if last_version:
            major, minor, patch = last_version.split(".")
            versions[name] = f"{major}.{minor}.{int(patch) + 1}"
        else:
            versions[name] = "0.1.0"  # first publish default
    else:
        versions[name] = last_version or "0.0.0"
```

Remove the `STATE_FILE` constant, the `hashes` dict, and the `hashlib` import. Remove the `hash_glob` and `hash_exclude` fields from `PackageConfig` since they are no longer needed.

#### Step 3: Replace "Save publish state" with tag creation in `publish_packages.py`

Replace the "Save publish state" step (lines 209-218) with a new step that creates git tags for each published package:

```python
with ci_step("Create version tags"):
    for name in PACKAGES:
        if publish[name]:
            tag = f"{name}-v{versions[name]}"
            bash(f"git tag {tag}")
            bash(f"git push origin {tag}")
            print(f"  Tagged: {tag}")
```

Keep the `github_output` write (`published=true`) so the workflow can still gate downstream jobs.

#### Step 4: Make `package.json` patching ephemeral

Currently `patch_package_json` writes to disk and the files get committed by `commit_artifacts.py`. Instead, the patch should be ephemeral -- patch before `npm publish`, then restore immediately after. Add a context manager or use a try/finally around each npm publish call:

```python
import shutil

def ephemeral_patch(package_path: Path, version: str, dependency_updates: dict[str, str] | None = None):
    """Context manager that patches package.json, yields, then restores the original."""
    package_json = package_path / "package.json"
    original = package_json.read_text()
    try:
        patch_package_json(package_path, version, dependency_updates)
        yield
    finally:
        package_json.write_text(original)
```

Wrap each npm publish call with this context manager. This way the working tree stays clean.

#### Step 5: Handle app versions

The "Compute app versions" section (lines 174-207) currently stores app hashes/versions in `versions.json`. Since app versions are used by the Unity build system (via `--run-number`), they need tag-based tracking too. Add app tag patterns: `outernet-client-v*`, `mapregistrationtool-v*`, `androidmobile-v*`.

Replace the app hash computation with `has_changes_since_tag` using the project path. Create tags for apps after version computation, same as packages.

**Important**: The app names in `versions.json` use PascalCase (`Outernet.Client`, `MapRegistrationTool`, `AndroidMobile`). The tag prefixes should use lowercase-kebab-case to match the package tag convention. Add a mapping dict:

```python
APP_TAG_PREFIXES = {
    "Outernet.Client": "outernet-client",
    "MapRegistrationTool": "mapregistrationtool",
    "AndroidMobile": "androidmobile",
}
```

#### Step 6: Refactor `create_release.py`

Replace `STATE_FILE` read (line 73) with:

```python
current_version = get_latest_tag_version("release-v")
if current_version is None:
    current_version = "0.0.0"
```

Remove the `STATE_FILE` write and git commit (lines 81-90). Replace with just tag creation and push:

```python
with ci_step("Create release tag"):
    tag = f"v{new_version}"
    bash(f"git tag {tag}")
    bash(f"git push origin {tag}")
    # Also create the release-v tag for tracking
    release_tag = f"release-v{new_version}"
    bash(f"git tag {release_tag}")
    bash(f"git push origin {release_tag}")
```

Remove the `json` import and `STATE_FILE` constant. Keep the existing `_bump_patch` helper. Remove the `git add`, `git commit`, and first `git push` (the one that pushes the branch) -- only push tags.

**Important**: The existing code creates a `v{version}` tag for the GitHub Release. Keep this tag. Additionally create a `release-v{version}` tag for the version-tracking system to find via `get_latest_tag_version("release-v")`. Alternatively, use `v` as the prefix for `get_latest_tag_version` since the existing release tags already use `v{version}`. Given that the only existing tag is `v0.1.0-alpha.2`, using `release-v` as a separate namespace is cleaner and avoids confusion.

#### Step 7: Simplify `commit_artifacts.py`

Remove `build/versions.json` and `packages/unity/Placeframe/Assets/Package/*/package.json` from the `git add` line (line 38). The line becomes:

```python
bash("git add .env.lock")
```

This file may be deleted entirely in T2 once `.env.lock` commits are also eliminated, but for now it remains.

#### Step 8: Update `.github/workflows/placeframe.yml`

1. **Remove `build/versions.json` from `paths-ignore`** (lines 9, 17) -- this file will no longer exist.

2. **Remove the three `package.json` entries from `paths-ignore`** (lines 10-12, 18-20) -- these files will have static `0.0.0-local` versions and will not be modified by CI.

3. **Remove the "Upload publish artifacts" step** (lines 202-208) in the `publish` job -- no more `versions.json` or `package.json` artifacts to pass.

4. **Remove the "Download publish artifacts" step** (lines 239-243) in the `commit` job -- nothing to download.

5. **Add `contents: write` permission** to the `publish` job (currently only has `contents: read`) so it can push tags. Alternatively, the tag push could happen in the `release` job, but doing it in `publish` is more natural since that is where versions are determined.

#### Step 9: Set `package.json` versions to `0.0.0-local`

Set the `version` field in all three `package.json` files to `"0.0.0-local"`. Also update the cross-package dependency versions: in `ARFoundation/package.json` and `MagicLeap/package.json`, set `"org.outernet.placeframe"` dependency to `"file:../Core"` or keep the current version string (since Unity resolves via `file:` references anyway). Actually, checking the ticket again -- the version fields in dependencies are also only relevant for npm publish, so they can stay as-is since the ephemeral patch will set them correctly at publish time. Just set the top-level `"version"` to `"0.0.0-local"` in each.

#### Step 10: Delete `build/versions.json`

Remove the file from the repository.

#### Step 11: Bootstrap tags from current versions

Before merging, create the initial tags matching current `versions.json` values on `main`:

```
git tag api-client-v0.1.5
git tag core-v1.0.3
git tag arfoundation-v1.0.3
git tag magicleap-v1.0.3
git tag release-v0.2.0
git tag outernet-client-v0.1.9
git tag mapregistrationtool-v1.0.0
git tag androidmobile-v0.1.0
```

This must be done as part of the merge/deploy process so the new code can find its starting versions.

#### Step 12: Extract shared tag utilities

Since both `publish_packages.py` and `create_release.py` need `get_latest_tag_version`, create a small shared module at `build/src/build_scripts/placeframe/ci/git_tags.py` containing:

- `get_latest_tag_version(prefix: str) -> str | None`
- `has_changes_since_tag(tag: str | None, path: Path) -> bool`
- `create_and_push_tag(tag: str) -> None`

Both scripts import from this shared module.

### Key Files

**Create:**
- `build/src/build_scripts/placeframe/ci/git_tags.py` -- Shared git tag utility functions (get latest version from tags, check for changes, create+push tags)

**Modify:**
- `build/src/build_scripts/placeframe/ci/publish_packages.py` -- Replace hash-based detection with `git diff`, replace `versions.json` reads/writes with tag queries/creation, make `package.json` patching ephemeral, remove `hashlib`/`PackageConfig.hash_glob`/`hash_exclude`
- `build/src/build_scripts/placeframe/ci/create_release.py` -- Read release version from `release-v*` tags, remove `versions.json` write and git commit, only create+push tags
- `build/src/build_scripts/placeframe/ci/commit_artifacts.py` -- Remove `versions.json` and `package.json` from `git add` line
- `.github/workflows/placeframe.yml` -- Remove `versions.json` and `package.json` from `paths-ignore`, remove publish artifact upload/download steps, add `contents: write` to `publish` job permissions
- `packages/unity/Placeframe/Assets/Package/Core/package.json` -- Set version to `0.0.0-local`
- `packages/unity/Placeframe/Assets/Package/ARFoundation/package.json` -- Set version to `0.0.0-local`
- `packages/unity/Placeframe/Assets/Package/MagicLeap/package.json` -- Set version to `0.0.0-local`

**Delete:**
- `build/versions.json`

### Verification

1. **Static checks**: `uv run ruff check .` and `uv run basedpyright` pass with no new errors.

2. **Unit-testable logic**: The `get_latest_tag_version` function can be tested by mocking `bash_output` to return various tag list outputs (empty, single tag, multiple tags with semver ordering). The `has_changes_since_tag` function can be tested by mocking `bash_check`.

3. **Bootstrap tag verification**: After creating bootstrap tags, run `git tag --list "*-v*" --sort=-v:refname` and confirm all expected tags exist with correct versions matching the current `versions.json`.

4. **No-change publish**: Run `publish-packages --dry-run` on a branch where no package paths have changed since the bootstrap tags. Verify it reports "Nothing to publish."

5. **Change detection**: Modify a file under `packages/unity/Placeframe/Assets/Package/Core/`, run `publish-packages --dry-run`, and confirm `core`, `arfoundation`, and `magicleap` are all marked for publish (dependency cascade).

6. **Ephemeral patching**: After a dry run or real publish, confirm `git status` shows no changes to `package.json` files.

7. **Workflow correctness**: Verify the workflow YAML is valid (e.g., `python -c "import yaml; yaml.safe_load(open('.github/workflows/placeframe.yml'))"` or use `actionlint`).

8. **End-to-end CI run**: Trigger the workflow on a test branch merged to `main`. Confirm: tags are created after publish, no commits are made to `main` by the publish or release jobs (only `.env.lock` commit from `commit_artifacts` remains), and the GitHub Release is created with the correct `v{version}` tag.
