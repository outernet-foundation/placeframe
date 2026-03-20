## Implementation Plan: T3 — Split CI and Release into Separate Workflows

### Context

The current `placeframe.yml` workflow runs the entire CI pipeline (build + release) on every push to main, wasting CI minutes since the dev-to-main merge is a fast-forward with an identical SHA. Splitting into two workflows lets CI run only on dev/PRs while release runs only on main, reusing CI artifacts by SHA lookup.

### Approach

This plan assumes T1 (tag-based versioning, eliminating `versions.json`/`package.json` commits) and T2 (SHA-based image refs, eliminating `.env.lock` commits) are already implemented. After those changes, no workflow job creates commits, making the dev-to-main fast-forward SHA-identical.

#### Step 1: Create `.github/workflows/ci.yml` (renamed from `placeframe.yml`)

Take the existing `placeframe.yml` and transform it:

- **Rename** the file from `placeframe.yml` to `ci.yml` and change `name:` to `CI`.
- **Change triggers**: Replace `push: branches: [main]` with `push: branches: [dev]`. Keep `pull_request: branches: [main, dev]` and `workflow_dispatch`.
- **Remove `paths-ignore`** entirely. After T1 and T2, no CI job commits files, so there are no bot-authored pushes to ignore. The `paths-ignore` for `.env.lock`, `versions.json`, and `package.json` files becomes unnecessary.
- **Keep jobs**: `preflight`, `activate-license`, `matrix`, `build-docker`, `build-unity` -- unchanged.
- **Remove jobs**: `publish`, `commit`, `release` -- all three are deleted from this workflow.
- **Add `ensure-release-pr` job**: This replaces the standalone `placeframe-release-pr.yml` workflow. It depends on `[build-docker, build-unity]` and runs only on dev push (`if: github.event_name == 'push' && github.ref == 'refs/heads/dev'`). Steps:
  1. Generate app token (same pattern as current `commit` job uses)
  2. Checkout with `actions/checkout@v5`
  3. Setup uv with `./.github/actions/setup-uv`
  4. Run `uv run --no-sync ensure-release-pr` with `GH_TOKEN` set to the app token

- **Keep concurrency** as-is: `group: ${{ github.workflow }}-${{ github.event.pull_request.number || github.ref }}` with `cancel-in-progress: true`.

**Rationale for `ensure-release-pr` placement**: By making it depend on all build jobs, the release PR only exists/updates when CI is green. This is strictly better than the current `placeframe-release-pr.yml` which fires on every dev push regardless of CI status.

#### Step 2: Create `build/src/build_scripts/placeframe/ci/fetch_ci_artifacts.py`

Create a new Python script that replaces the inline shell logic for finding the successful CI run and downloading its artifacts.

**Script design** (follows the same patterns as `create_release.py`, `publish_packages.py`, etc.):

- **Typer app** with `add_completion=False, pretty_exceptions_show_locals=False`.
- **Pydantic Settings** class for environment variables:
  - `github_sha: str` -- the commit SHA to look up (from `GITHUB_SHA`)
  - `github_repository: str` -- the repo slug (from `GITHUB_REPOSITORY`)
  - `github_output: str | None = None` -- path to `GITHUB_OUTPUT` file for passing outputs to subsequent steps
- **Uses `ci_step` context manager** for GitHub Actions grouping and summary table.
- **Uses `bash_output` from `common.bash`** to invoke `gh api` commands.

**Logic (two ci_steps)**:

1. `ci_step("Find successful CI run")`:
   - Calls `bash_output(f'gh api "/repos/{repo}/actions/workflows/ci.yml/runs?head_sha={sha}&status=success" --jq ".workflow_runs[0].id // empty"')`.
   - Strips the result. If empty, prints `::error::No successful CI run found for SHA {sha}. Cannot release untested code.` and raises `typer.Exit(code=1)`.
   - Otherwise, stores the `run_id` as a string.
   - Writes `run_id={run_id}` to `GITHUB_OUTPUT` (same pattern as `publish_packages.py` line 217-218: open the `github_output` path in append mode and write the key-value pair).

2. `ci_step("Download artifacts")`:
   - Calls `bash_output(f'gh api "/repos/{repo}/actions/runs/{run_id}/artifacts" --paginate --jq ".artifacts[] | [.id, .name] | @tsv"')` to get all artifact IDs and names as tab-separated lines.
   - Defines the same skip logic as `create_release.py`: `SKIP_PREFIXES = ("env-lock-", "versions")` and `SKIP_SUFFIXES = ("-build-report",)`.
   - Creates `/tmp/release-artifacts/` directory via `Path.mkdir(parents=True, exist_ok=True)`.
   - Iterates over each artifact line, skipping those matching the prefix/suffix patterns.
   - For each kept artifact: downloads via `bash(f'gh api "/repos/{repo}/actions/runs/{run_id}/artifacts/{artifact_id}/zip" > /tmp/release-artifacts/{name}.zip"')`, then uses `zipfile.ZipFile` to extract to `/tmp/release-artifacts/{name}/`, then removes the zip file.
   - Prints a summary of how many artifacts were downloaded.

**Registration in `build/pyproject.toml`**:

Add this entry to `[project.scripts]`:
```
fetch-ci-artifacts = "build_scripts.placeframe.ci.fetch_ci_artifacts:app"
```

#### Step 3: Create `.github/workflows/release.yml`

New workflow triggered on `push: branches: [main]` only. Single `release` job.

**Concurrency**:
```yaml
concurrency:
  group: release
  cancel-in-progress: false
```

**Permissions**: `contents: write`, `packages: write`, `id-token: write`, `actions: read` (needed for artifact API lookup).

**Job steps**:

1. **Generate app token** -- same pattern as existing `release` job, using `PLACEFRAME_CI_APP_ID` / `PLACEFRAME_CI_PRIVATE_KEY` secrets.

2. **Checkout main** with the app token (needed for `git push` of the release tag in `create-release`).

3. **Setup uv** via `./.github/actions/setup-uv`.

4. **Fetch CI artifacts** -- A single workflow step that invokes the new Python script:
   ```yaml
   - name: Fetch CI artifacts
     id: fetch-ci-artifacts
     run: uv run --no-sync fetch-ci-artifacts
     env:
       GH_TOKEN: ${{ github.token }}
   ```
   The script reads `GITHUB_SHA` and `GITHUB_REPOSITORY` from the environment (automatically set by GitHub Actions), finds the successful CI run, downloads all release artifacts to `/tmp/release-artifacts/`, and writes `run_id=<id>` to `$GITHUB_OUTPUT`.

5. **Publish packages** -- Run `uv run --no-sync publish-packages` with `NUGET_API_KEY` and `NODE_AUTH_TOKEN` secrets, same as the current `publish` job.

6. **Create GitHub Release** -- Run `uv run --no-sync create-release --run-number ${{ github.run_number }}` with `GH_TOKEN` set to the app token, same as the current `release` job.

#### Step 4: Delete `.github/workflows/placeframe-release-pr.yml`

This workflow is fully absorbed into the `ensure-release-pr` job in `ci.yml`.

#### Step 5: Remove the `env-lock-*` artifact upload from `build-docker`

After T2 (SHA-based image refs), Docker builds no longer produce `.env.lock` files that need committing. The `Upload .env.lock` step in `build-docker` and the corresponding `env-lock-*` artifact pattern can be removed from `ci.yml`. However, if T2 is not yet merged, keep this step -- it is harmless and the release workflow already skips `env-lock-*` artifacts.

#### Step 6: Verify `create_release.py` compatibility

The existing `create_release.py` at `/placeframe/build/src/build_scripts/placeframe/ci/create_release.py`:
- Reads artifacts from `ARTIFACT_DIR = Path("/tmp/release-artifacts")`
- Skips directories matching `SKIP_PREFIXES = ("env-lock-", "versions")` and `SKIP_SUFFIXES = ("-build-report",)`
- Creates a git commit for the version bump, tags, and pushes

This script works as-is with the new workflow, provided artifacts are placed in the expected directory structure (handled by `fetch-ci-artifacts`). No changes needed to this file.

#### Step 7: Clean up `commit_artifacts.py` references (optional, post-T1/T2)

After T1 and T2 land, the `commit-artifacts` script in `build/pyproject.toml` becomes dead code. It can be removed from `pyproject.toml` and its source file `build/src/build_scripts/placeframe/ci/commit_artifacts.py` deleted. This is a cleanup step and not strictly required for T3.

### Key files

**Create:**
- `.github/workflows/release.yml` -- New release workflow with single `uv run` commands, no inline shell logic
- `build/src/build_scripts/placeframe/ci/fetch_ci_artifacts.py` -- Python script that finds the CI run by SHA and downloads artifacts to `/tmp/release-artifacts/`

**Modify:**
- `.github/workflows/placeframe.yml` -- Rename to `.github/workflows/ci.yml`, change push trigger to `[dev]`, remove `publish`/`commit`/`release` jobs, add `ensure-release-pr` job, remove `paths-ignore`
- `build/pyproject.toml` -- Register `fetch-ci-artifacts` script entry point

**Delete:**
- `.github/workflows/placeframe-release-pr.yml` -- Absorbed into `ci.yml`

**No changes (used by release.yml):**
- `build/src/build_scripts/placeframe/ci/publish_packages.py` -- Called by release workflow
- `build/src/build_scripts/placeframe/ci/create_release.py` -- Called by release workflow, expects `/tmp/release-artifacts/` directory structure
- `build/src/build_scripts/placeframe/ci/ensure_release_pr.py` -- Called by `ensure-release-pr` job in `ci.yml`

### Verification

**Static checks (verifiable from the files):**
- `ci.yml` triggers on `push: [dev]` and `pull_request: [main, dev]`, NOT `push: [main]`
- `ci.yml` contains jobs: `preflight`, `activate-license`, `matrix`, `build-docker`, `build-unity`, `ensure-release-pr`
- `ci.yml` does NOT contain jobs: `publish`, `commit`, `release`
- `ci.yml` `ensure-release-pr` job has `needs: [build-docker, build-unity]` and condition `github.event_name == 'push' && github.ref == 'refs/heads/dev'`
- `release.yml` triggers on `push: [main]` only
- `release.yml` uses `cancel-in-progress: false`
- `release.yml` contains no inline shell logic with conditionals or loops -- all logic is in Python scripts invoked via `uv run`
- `release.yml` calls `fetch-ci-artifacts`, `publish-packages`, and `create-release` as separate steps
- `fetch_ci_artifacts.py` uses `typer.Typer`, `ci_step`, `bash_output`, and `pydantic_settings.BaseSettings` -- same patterns as all other CI scripts
- `fetch_ci_artifacts.py` writes `run_id` to `GITHUB_OUTPUT` using the same file-append pattern as `publish_packages.py`
- `fetch_ci_artifacts.py` downloads artifacts to `/tmp/release-artifacts/<name>/` matching `create_release.py`'s expectation
- `fetch-ci-artifacts` is registered in `build/pyproject.toml` under `[project.scripts]`
- `placeframe-release-pr.yml` no longer exists
- No job in either workflow creates a git commit (except `create-release` which tags the release)

**Runtime checks (manual verification after merge):**
- Push to dev triggers only `ci.yml`
- Push to main (via release PR merge) triggers only `release.yml`
- PR to dev triggers `ci.yml` build jobs but not `ensure-release-pr`
- `release.yml` successfully finds CI artifacts by SHA and creates a GitHub Release
- `release.yml` fails cleanly with `::error::` annotation when no successful CI run exists for the SHA
- `ensure-release-pr` only runs after all build jobs succeed
