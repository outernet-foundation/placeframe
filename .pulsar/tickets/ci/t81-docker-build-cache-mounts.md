---
id: T81
title: Add missing BuildKit cache mounts to database-migrator and state-sync Dockerfiles
status: ready
depends_on: []
---

# T81: Add missing BuildKit cache mounts to database-migrator and state-sync Dockerfiles

## Goal

Add BuildKit `--mount=type=cache` directives to the two Dockerfiles that are missing them, so dependency downloads are cached across builds.

## Context

Discovered during T78 research. All Python-based Dockerfiles already use `--mount=type=cache,id=uvcache` for the uv download cache. Two non-Python Dockerfiles are missing equivalent cache mounts:

- `docker/database-migrator/Dockerfile` — runs `go install` without Go module or build caches
- `docker/state-sync/Dockerfile` — runs `dotnet restore` without NuGet package cache

These are small, fast images so the impact is minor, but the fix is trivial.

## Key files

- `docker/database-migrator/Dockerfile` — add Go module + build cache mounts
- `docker/state-sync/Dockerfile` — add NuGet package cache mount

## Approach

Add cache mounts to the `RUN` instructions:

**database-migrator:**
```dockerfile
RUN --mount=type=cache,target=/root/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    apk add --no-cache git \
    && go install ...
```

**state-sync:**
```dockerfile
RUN --mount=type=cache,target=/root/.nuget/packages \
    dotnet restore ...
```

## Done when

- Both Dockerfiles have cache mounts on their dependency-install steps
- `uv run build` still succeeds locally (with `--gpu none`)
