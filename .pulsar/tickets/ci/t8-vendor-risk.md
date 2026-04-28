---
id: T8
title: GitHub Actions vendor risk mitigation
status: design-needed
depends_on: []
---

# T8: GitHub Actions vendor risk mitigation

See `ci-background.md` for shared CI context.

## Goal

Ensure all CI logic is portable and not locked into GitHub Actions.

## Context

GitHub Actions is ubiquitous but Microsoft's moves toward monetizing free-tier features are concerning. A full rug pull is unlikely given entrenchment, but cost increases and feature restrictions are plausible.

## Current exposure

- `.github/workflows/build.yml` — the workflow YAML itself (low-value, easy to rewrite)
- `actions/checkout@v4` — trivially replaced by `git clone`
- `astral-sh/setup-uv@v5` — replaced by `curl | sh`
- `docker/setup-buildx-action@v3` — replaced by `docker buildx create`
- `docker/login-action@v3` — replaced by `docker login`
- `jlumbroso/free-disk-space@v1.3.1` — GitHub-runner-specific, would need equivalent on other platforms
- `peter-evans/create-pull-request@v6` — GitHub API-specific, would need `gh` CLI or API calls on other platforms

## Assessment

The exposure is already low because the real logic is in `build.py`. The riskiest dependency is on GitHub-hosted runners themselves (free compute). If GitHub makes runners expensive, alternatives include:
- **Buildkite** — hybrid model, agents run on your own infra, orchestration in cloud. Used by Uber and Shopify.
- **GitLab CI** — fully self-hostable, generous free tier
- **Self-hosted runners** — GitHub Actions compatible but running on your own machines
- **Forgejo/Gitea Actions** — open-source GitHub Actions compatible runners

## Action items

- Keep all logic in `scripts/` (already the case)
- Avoid deep dependencies on GitHub-specific features (environments, OIDC, branch protection rules for CI)
- Document the thin translation layer needed for each alternative CI system
- Monitor GitHub pricing changes

This ticket is primarily a documentation/audit exercise, not an implementation task.

## Done when

- Portability document exists listing translation layer for 2+ alternative CI systems
