# Plan: Split CI/CD Pipeline — Build Once on Dev, Release from Main

## Context

When the dev→main release gate PR merges (fast-forward), the `push: [main]` trigger re-runs the entire build pipeline — preflight, Docker builds (3 variants), Unity builds (matrix). Since commit SHAs are identical (fast-forward), every artifact is deterministically the same. This wastes CI minutes and delays releases.

Additionally:
- The release gate PR (`ensure-release-pr`) fires on every dev push regardless of CI status
- The `commit` job pushes bot commits to PR branches (including the release gate PR's dev branch)
- `commit` and `release` are separate jobs that each push a commit to main

The fix: split into two workflows. CI builds on dev. Release on main reuses CI artifacts via the GitHub REST API.

## Files to Change

| File | Action |
|---|---|
| `.github/workflows/placeframe.yml` | Refactor triggers and jobs (keep name) |
| `.github/workflows/placeframe-release-pr.yml` | Delete (absorbed into `placeframe.yml`) |
| `.github/workflows/placeframe-release.yml` | Create new |
| `build/src/build_scripts/placeframe/ci/download_ci_artifacts.py` | Create new — downloads artifacts from a CI run via REST API |
| `build/pyproject.toml` | Register `download-ci-artifacts` entry point |
| `build/src/build_scripts/placeframe/ci/commit_artifacts.py` | No changes |
| `build/src/build_scripts/placeframe/ci/create_release.py` | No changes |
| `build/src/build_scripts/placeframe/ci/ensure_release_pr.py` | No changes |
| `build/src/build_scripts/placeframe/ci/publish_packages.py` | No changes |

## Step 1: Refactor `placeframe.yml`

**Trigger changes:**
```yaml
# Before
on:
  push:
    branches: [main]
    paths-ignore: [...]
  pull_request:
    branches: [main, dev]
    paths-ignore: [...]
  workflow_dispatch:

# After
on:
  push:
    branches: [dev]
    paths-ignore: [...]     # same list — prevents re-trigger from bot commits on dev
  pull_request:
    branches: [main, dev]
    paths-ignore: [...]     # unchanged
  workflow_dispatch:
```

**Job changes:**

- `preflight` — unchanged
- `activate-license` — unchanged
- `matrix` — unchanged
- `build-docker` — unchanged (images push to GHCR, env-lock uploaded as artifact)
- `build-unity` — unchanged (artifacts uploaded)
- `publish` — **remove entirely** (moves to `placeframe-release.yml`)
- `commit` — refactor:
  - Condition: `github.ref == 'refs/heads/dev'` only (no more PR-branch commits)
  - Remove dependency on `publish` (publish no longer in this workflow)
  - Keeps dependency on `build-docker`
  - Still merges env-lock artifacts and commits `.env.lock` to dev
  - Does NOT commit `versions.json` or `package.json` (those are publish concerns now)
- `release` — **remove entirely** (moves to `placeframe-release.yml`)
- **New `ensure-release-pr` job** — runs after `commit` succeeds on dev:
  ```yaml
  ensure-release-pr:
    needs: [preflight, build-docker, build-unity, commit]
    if: github.ref == 'refs/heads/dev' && github.event_name == 'push'
    runs-on: ubuntu-latest
    steps:
      - name: Generate app token
        id: app-token
        uses: actions/create-github-app-token@v2
        with:
          app-id: ${{ secrets.PLACEFRAME_CI_APP_ID }}
          private-key: ${{ secrets.PLACEFRAME_CI_PRIVATE_KEY }}
      - uses: actions/checkout@v5
      - uses: ./.github/actions/setup-uv
      - name: Ensure release PR exists
        env:
          GH_TOKEN: ${{ steps.app-token.outputs.token }}
        run: uv run --no-sync ensure-release-pr
  ```

**Revised `commit` job condition:**
```yaml
commit:
  needs: [build-docker]
  if: >-
    github.ref == 'refs/heads/dev'
    && github.event_name == 'push'
    && !cancelled()
    && needs.build-docker.result == 'success'
```

**`commit_artifacts.py` impact**: The script commits `.env.lock`, `build/versions.json`, and `package.json` files. Since `publish` no longer runs in placeframe.yml, `versions.json` and `package.json` won't have changed — the `git add` will be a no-op for those files, and `git diff --cached --quiet` handles it. No script change needed.

## Step 2: Create `download_ci_artifacts.py`

New Python script at `build/src/build_scripts/placeframe/ci/download_ci_artifacts.py`, registered as `download-ci-artifacts` in `build/pyproject.toml`.

**Purpose**: Given a commit SHA, find the successful `placeframe.yml` CI workflow run for that SHA and download its artifacts to the expected directories (`/tmp/env-locks/` and `/tmp/release-artifacts/`).

**Interface:**
```
uv run --no-sync download-ci-artifacts --sha <commit-sha>
```

**Behavior:**
1. Use `gh api` to query `/repos/{owner}/{repo}/actions/workflows/placeframe.yml/runs?head_sha={sha}&status=success`
2. Extract the first (most recent) run ID. Fail with a clear error if no successful run exists.
3. List artifacts for that run via `/repos/{owner}/{repo}/actions/runs/{run_id}/artifacts`
4. For each artifact:
   - `env-lock-*` → download and extract to `/tmp/env-locks/{name}/`
   - Skip `versions` and `*-build-report` artifacts
   - Everything else (Unity builds) → download and extract to `/tmp/release-artifacts/{name}/`
5. Download uses `gh api .../artifacts/{id}/zip` and extracts with `zipfile`

**Implementation details:**
- Uses `common.bash.bash_output` for `gh api` calls (consistent with other scripts)
- Uses Python `zipfile` for extraction (no shell dependency on `unzip`)
- Uses `ci_step` context manager for GitHub Actions group logging
- Reads `GITHUB_REPOSITORY` from environment via pydantic-settings

## Step 3: Create `placeframe-release.yml`

New workflow with a single `release` job that does everything: download CI artifacts → publish packages → commit all artifacts → tag → create GitHub Release.

```yaml
name: Placeframe Release

on:
  push:
    branches: [main]
    paths-ignore:
      - ".env.lock"
      - "build/versions.json"
      - "packages/unity/Placeframe/Assets/Package/Core/package.json"
      - "packages/unity/Placeframe/Assets/Package/ARFoundation/package.json"
      - "packages/unity/Placeframe/Assets/Package/MagicLeap/package.json"

concurrency:
  group: release
  cancel-in-progress: false

jobs:
  release:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      packages: read
      actions: read
      id-token: write    # npm provenance
    steps:
      - name: Generate app token
        id: app-token
        uses: actions/create-github-app-token@v2
        with:
          app-id: ${{ secrets.PLACEFRAME_CI_APP_ID }}
          private-key: ${{ secrets.PLACEFRAME_CI_PRIVATE_KEY }}

      - uses: actions/checkout@v5
        with:
          ref: main
          token: ${{ steps.app-token.outputs.token }}

      - uses: ./.github/actions/setup-uv

      - name: Download CI artifacts
        env:
          GH_TOKEN: ${{ github.token }}
        run: uv run --no-sync download-ci-artifacts --sha ${{ github.sha }}

      - name: Publish packages
        env:
          NUGET_API_KEY: ${{ secrets.NUGET_API_KEY }}
          NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
        run: uv run --no-sync publish-packages

      - name: Commit artifacts
        run: uv run --no-sync commit-artifacts

      - name: Create GitHub Release
        env:
          GH_TOKEN: ${{ steps.app-token.outputs.token }}
        run: uv run --no-sync create-release --run-number ${{ github.run_number }}
```

**Key design decisions:**
- `github.token` for reading CI artifacts (needs `actions:read`), app token for pushing commits/tags
- `download-ci-artifacts` populates `/tmp/env-locks/` and `/tmp/release-artifacts/` — the same paths `commit_artifacts.py` and `create_release.py` expect
- `commit-artifacts` runs between `publish-packages` and `create-release`, same as current ordering
- `cancel-in-progress: false` — never abort a release mid-publish

## Step 4: Delete `placeframe-release-pr.yml`

The `ensure-release-pr` job in `placeframe.yml` replaces this entirely. The new version only runs after all builds succeed, so the release PR only reflects green commits.

## Consideration: Main/Dev Divergence

After `placeframe-release.yml` runs, main has commits that dev doesn't (env.lock merge, version bumps, release tag commit). The next dev→main merge can't be a strict fast-forward. This matches current behavior — the existing `commit` + `release` jobs also create main-only commits.

Options to address (out of scope for this PR, but worth noting):
- After release, auto-merge main back into dev
- Accept merge commits for the release PR
- Keep current behavior (this is what happens today)

## Verification

1. **Push to dev**: placeframe.yml triggers → preflight, build-docker, build-unity all run → commit job merges env.lock on dev → ensure-release-pr creates/updates the gate PR
2. **Open PR to dev**: placeframe.yml triggers on `pull_request` → builds run, no commit/publish/release
3. **Merge release PR (dev→main)**: placeframe-release.yml triggers → `download-ci-artifacts` finds CI run for SHA → downloads env-lock + Unity artifacts → publishes packages → commits artifacts → creates GH Release with tag and Unity binaries
4. **Push to main with no CI run**: placeframe-release.yml triggers → `download-ci-artifacts` fails with clear error ("No successful CI run found")
5. **Verify no workflow runs on main besides placeframe-release.yml**: placeframe.yml should NOT trigger on main pushes
