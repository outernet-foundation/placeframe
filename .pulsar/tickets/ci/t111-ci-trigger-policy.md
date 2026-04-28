---
id: T111
title: CI trigger policy for all-self-hosted compute on a public repo
status: design-needed
depends_on: []
---

# T111: CI trigger policy for all-self-hosted compute on a public repo

## Goal

Design and implement the workflow trigger architecture that controls who can trigger CI runs, when, and how — given that all compute (not just Unity builds) will run on self-hosted Hetzner runners and the repository is public.

## Context

T109 research (`.pulsar/research/hetzner-infrastructure.md`) established that all CI compute should move to self-hosted Hetzner infrastructure. This creates two problems that don't exist with GitHub-hosted runners:

1. **Security.** Anyone can fork a public repo, add a workflow targeting `self-hosted` runners, and open a PR. GitHub's own docs warn: "Self-hosted runners should almost never be used for public repositories." The Shai-Hulud worm (November 2025) demonstrated this at scale — turning self-hosted runners into persistent C2 nodes. There is no process isolation between jobs on persistent runners (same OS user, shared filesystem).

2. **Cost.** Every workflow run consumes compute on hardware we pay for. Without gating, any GitHub user can trigger arbitrarily many CI runs by opening PRs or pushing to fork branches.

Both problems apply to ALL jobs, not just Unity builds — preflight, Docker builds, matrix generation, license activation, everything.

### Trigger mechanisms available

- **GitHub fork approval settings**: "Require approval for all outside collaborators" — every push to a fork PR needs maintainer approval before workflows run. UX is clunky (buried in Actions tab).
- **Label-gated CI (`ok-to-test`)**: Workflow has `if: contains(github.event.pull_request.labels.*, 'ok-to-test')`. Maintainer reviews PR, adds label, CI runs. Can auto-label for org members.
- **Comment-triggered CI (`/test`)**: Workflow triggers on `issue_comment`, checks commenter has write access. Used by Kubernetes (Prow). More complex workflow logic, different checkout behavior.
- **Two-phase CI**: Lightweight checks run automatically (or not at all), heavyweight jobs require explicit approval. Branch protection requires both.
- **`push`-only triggers**: Self-hosted jobs only run on push to main/dev, never on `pull_request`. PRs get no pre-merge feedback from self-hosted jobs.

### Current workflow structure

The CI workflow (`.github/workflows/build-unity.yml`) triggers on both `push` and `pull_request` to `main`/`dev`. All jobs currently run on `ubuntu-latest` (GitHub-hosted) or in `unityci/editor` containers on GitHub-hosted runners. The workflow logic is almost entirely in Python scripts invoked via `uv run` — the YAML is a thin dispatch layer.

GitHub-specific coupling points that matter for this ticket:
- `actions/upload-artifact` / `download-artifact` for passing data between jobs (env-lock files, build artifacts, version files)
- `actions/cache` for UPM packages
- `${{ github.token }}` for GHCR authentication (ORAS cache)
- `${{ secrets.* }}` for credentials

### Requirement

PRs must get pre-merge CI feedback (including Unity builds) — CI success is a prerequisite for considering a PR mergeable. But untrusted users must not be able to trigger CI runs freely.

## Key files

- `.github/workflows/build-unity.yml` — main CI workflow
- `.github/workflows/build-cesium-native.yml` — Cesium build workflow
- `.github/actions/setup-uv/action.yml` — composite action for uv setup

## Approach

Not yet determined. Key decisions:

1. Which gating mechanism (label, comment, fork approval, or hybrid)?
2. Should org members get automatic CI, with gating only for outside contributors?
3. How does artifact passing between jobs work without `actions/upload-artifact`? Shared filesystem on same machine? Separate artifact store?
4. What replaces GHCR as the ORAS cache registry? Self-hosted OCI registry, Hetzner Object Storage, or local disk only?

## Done when

- Trigger policy documented: who can trigger CI, via what mechanism, for each job type
- Artifact passing strategy decided: how data flows between jobs without GitHub-hosted primitives
- Cache strategy decided: what replaces GHCR for ORAS caches and UPM package caches
- Workflow YAML updated to implement the chosen policy
- Branch protection rules updated to match
- Security hardening documented: runner user permissions, process monitoring, cleanup between jobs

## Next step

Decide on the gating mechanism. The label-gated approach (`ok-to-test`) with auto-labeling for org members seems simplest. Evaluate whether this integrates cleanly with branch protection required status checks (a skipped check vs a missing check behave differently).
