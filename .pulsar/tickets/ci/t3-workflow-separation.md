---
id: T3
title: Split CI and release into separate workflows
status: plan-needed
constraint: .github/workflows/CLAUDE.md#ci-release-workflow-separation
violators:
  - .github/workflows/placeframe.yml
  - .github/workflows/placeframe-release-pr.yml
depends_on: [T1, T2]
plan: t3-plan.md
---

Single `placeframe.yml` contains both CI and release jobs. `push: [main]` re-runs entire pipeline after fast-forward merge, wasting CI minutes. `commit` job pushes bot commits to PR branches. `ensure-release-pr` fires as separate workflow regardless of CI status.

Rename `placeframe.yml` to `ci.yml` (trigger on `push: [dev]`), remove `publish`/`commit`/`release` jobs, absorb `placeframe-release-pr.yml` as `ensure-release-pr` job gated on builds. Create `release.yml` (trigger on `push: [main]`) with single job: new `fetch_ci_artifacts.py` script (Typer app using `gh api` to find CI run by SHA and download artifacts to `/tmp/release-artifacts/`) → `publish-packages` → `create-release`.
