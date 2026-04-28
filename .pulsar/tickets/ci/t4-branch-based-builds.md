---
id: T4
title: Branch-based builds and .env.lock strategy
status: in-review
depends_on: []
---

# T4: Branch-Based Builds and .env.lock Strategy

## Context

CI builds only trigger on push to `main`. The `.env.lock` file (pinned image digests) is updated via a bot-created PR (`peter-evans/create-pull-request`), introducing a delay between code landing and the lock file being correct. We need to support multiple long-running branches (`main`, `dev`, and potentially others like `alpha`, `beta`, customer-specific) where every commit at the tip of each branch has a `.env.lock` that exactly matches the code.

The core mechanism: **branch protection's "require branches to be up to date before merging"** provides merge-queue-like serialization. PRs must be rebased onto the target before merging, so CI builds from the rebased code and commits `.env.lock` to the PR branch. When the PR merges, the lock file is already correct — no post-merge rebuild needed on the target branch.

## Design Decisions

1. **No branch-specific image tags.** All branches push to `:latest`. Lock files pin by `@sha256:` digest, which is immutable regardless of tags.
2. **CI commits `.env.lock` directly** to the branch, replacing the lock PR approach.
3. **Feature branches build images** when a PR is opened against a long-running branch.
4. **GITHUB_TOKEN loop prevention.** Pushes made with `GITHUB_TOKEN` do not trigger new workflow runs (GitHub's built-in behavior). No `[skip ci]` or bot-detection needed.
5. **`.gitattributes merge=ours`** as a safety net for local command-line merges (branch protection is the primary mechanism — "require up to date" ensures fast-forward merges where no merge driver is invoked).

## Files to Change

### 1. `.github/workflows/build.yml`

**Triggers** — add `pull_request` trigger and `dev` to branch lists:
```yaml
on:
  push:
    branches: [main, dev]
    paths-ignore: [".env.lock"]
  pull_request:
    branches: [main, dev]
    paths-ignore: [".env.lock"]
```

`paths-ignore` on `push`: skips if the push ONLY touches `.env.lock` (prevents loops for the rare case of manual lock file edits). On `pull_request`: skips if the entire PR diff only touches `.env.lock` (PRs with code changes always run).

**Concurrency** — separate groups for PRs vs branch pushes:
```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: true
```

**Checkout** — check out the actual branch, not the merge ref:
```yaml
- uses: actions/checkout@v4
  with:
    ref: ${{ github.head_ref || github.ref_name }}
    token: ${{ secrets.GITHUB_TOKEN }}
```

On `pull_request`: `github.head_ref` is the PR source branch (e.g., `feature/my-change`).
On `push`: `github.head_ref` is empty, falls back to `github.ref_name` (e.g., `main`, `dev`).

**Permissions** — remove `pull-requests: write` (no longer creating PRs):
```yaml
permissions:
  contents: write
  packages: write
```

**Remove** the entire `Create/Update Lockfile PR` step (lines 76-87).

**Add** commit-and-push step after the Build step:
```yaml
- name: Commit and push .env.lock
  if: github.event_name == 'push' || !contains(fromJSON('["main","dev"]'), github.head_ref)
  run: |
    if git diff --quiet .env.lock; then
      echo "No changes to .env.lock, skipping commit."
      exit 0
    fi
    git config user.name "github-actions[bot]"
    git config user.email "github-actions[bot]@users.noreply.github.com"
    git add .env.lock
    git commit -m "Update .env.lock"
    git push
```

The `if` condition: **skip** the commit step when the PR source is itself a long-running branch (e.g., `dev → main` PR). Those branches are protected (CI can't push to them) and already have correct lock files from their own CI. For `feature → dev` PRs, the condition evaluates to true and the step runs normally.

### 2. `.gitattributes`

Add one line:
```
.env.lock merge=ours
```

Requires one-time per-clone developer setup: `git config merge.ours.driver true`. This defines the `ours` merge driver as `true` (exit 0 = keep current branch's version). Without this, Git doesn't know how to execute the driver and merges involving `.env.lock` will error (a clear signal to run the config command).

Note: this is a safety net. With "require up to date" branch protection, all PR merges are fast-forwards (or `--no-ff` commits with no file-level conflicts), so the merge driver is never invoked during normal workflow. It only matters for local command-line merges.

### 3. `CLAUDE.md`

Add a CI/CD section documenting:
- Build triggers: pushes to long-running branches + PRs targeting them
- Lock file flow: CI builds → commits `.env.lock` directly to branch
- Branch protection requirements: require PRs, require status checks, require up to date
- Developer setup: `git config merge.ours.driver true`
- Adding new long-running branches: update `branches` lists in `build.yml` (3 places: `push.branches`, `pull_request.branches`, and the `contains()` check in the commit step)

### 4. GitHub Repository Settings (manual, post-merge)

Configure branch protection for `main` and `dev`:
- Require a pull request before merging
- Require status checks to pass (`build-and-lock`)
- **Require branches to be up to date before merging** (this is the key mechanism)

## No Changes Needed

- `scripts/src/scripts/build.py` — existing `--mode ci` does exactly what we need
- `compose.bake.yml` — image tags stay as `:latest`
- `scripts/src/scripts/up.py` — no changes

## Implementation Order

1. Update `.gitattributes` (safe, no effect until branches diverge)
2. Update `build.yml` (core change)
3. Update `CLAUDE.md` (documentation)
4. Commit and merge to `main`
5. Create `dev` branch from `main` (if it doesn't exist)
6. Configure branch protection in GitHub settings (manual)
7. Delete `bot/update-lock` remote branch: `git push origin --delete bot/update-lock`

## Verification

After merging to `main`:
1. Push a change to `main` → verify CI builds and commits `.env.lock` directly (no lock PR created)
2. Create `dev` branch, open a PR with a code change against `dev` → verify CI builds and commits `.env.lock` to the feature branch
3. Merge the PR → verify `dev` has correct `.env.lock` at the merge commit
4. Open a PR from `dev → main` → verify CI runs the build but does NOT attempt to push to `dev`

## Done when

- `.github/workflows/build.yml` updated with PR triggers, concurrency, and direct commit step
- `.gitattributes` created with `merge=ours` for `.env.lock`
- CI commits `.env.lock` directly on push to `main`
- Branch protection configured (manual step documented)

## Log

Clean implementation, no issues. The ticket had exact code snippets for every change — implementation was a direct transcription.

Post-merge manual steps remain:
1. Create `dev` branch from `main` (if it doesn't exist)
2. Configure branch protection for `main` and `dev` in GitHub repo settings
3. Delete `bot/update-lock` remote branch: `git push origin --delete bot/update-lock`

## Observations

No pre-existing issues noticed.
