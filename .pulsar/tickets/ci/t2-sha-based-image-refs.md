---
id: T2
title: Replace .env.lock built-image digests with SHA-based image tags
status: in-progress
constraint: build/src/build_scripts/placeframe/ci/CLAUDE.md#ci-commit-free-invariant
violators:
  - build/src/build_scripts/placeframe/build_docker.py
  - build/src/build_scripts/placeframe/ci/commit_artifacts.py
  - build/src/build_scripts/placeframe/up.py
  - build/src/build_scripts/placeframe/down.py
  - .env.lock
  - compose.yml
  - compose.cuda.yml
  - compose.rocm.yml
  - compose.bake.yml
depends_on: []
plan: t2-plan.md
---

Built-image digests are stored in `.env.lock` and committed by `commit_artifacts.py`. Compose files reference built images via `${SERVICE_IMAGE:?err}` from `.env.lock`.

Should tag built images with `:<commit-sha>` in `compose.bake.yml`, reference as `ghcr.io/.../<service>:${GIT_SHA:?err}` in compose files (11 built services across 3 compose files), and pass `GIT_SHA` via `os.environ` in `up.py`/`down.py`. Local mode: `build_docker.py` writes `GIT_SHA=<sha>` to `.env.local.lock`; `up.py` reads it back as override when present. `.env.lock` reduced to base/third-party digests only.
