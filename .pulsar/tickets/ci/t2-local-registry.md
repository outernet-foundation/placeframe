---
id: T2
title: Local registry mode for build.py
status: plan-needed
depends_on: []
---

# T2: Local registry mode for build.py

See `ci-background.md` for shared CI context.

## Goal

Add a `--registry` option to `build.py` that pushes to a local Docker registry with registry-based caching, exactly mirroring CI caching behavior.

## Context

Local builds use `--load` with buildx's local cache. CI builds use `--push` with `cache-to`/`cache-from` type=registry to ghcr.io. These are fundamentally different caching strategies, so caching bugs in CI (especially with large PyTorch layers) can't be reproduced locally.

## Key files

- `scripts/src/scripts/build.py` — build orchestration (lines 176-185 are the cache/push logic)
- `compose.bake.yml` — `x-registry-cache: ghcr.io/outernet-foundation/placeframe/build-cache`, plus per-service tags all pointing at `ghcr.io/outernet-foundation/placeframe/<service>:latest`

## Approach

Add `--registry <host:port>` option. When set:
- Override `x-registry-cache` → `<host:port>/build-cache` for cache-to/cache-from
- Override image tags → `<host:port>/<service>:latest` for push destination
- Always use `--push` and registry caching (regardless of `--mode`)
- Write to `.env.local.lock`

## Usage pattern

```bash
docker run -d -p 5000:5000 --restart always --name registry registry:2
uv run build --registry localhost:5000 --gpu cuda
# run again to test cache hits
```

## Done when

**Requires hardware/infra (verify manually later):**
- `uv run build --registry localhost:5000 --gpu cuda` pushes to local registry
- Second run shows cache hits
