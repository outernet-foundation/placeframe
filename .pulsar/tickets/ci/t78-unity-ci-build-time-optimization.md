---
id: T78
title: Investigate and reduce Unity CI build times
status: in-review
depends_on: [T7]
plan: t78-plan.md
---

# T78: Investigate and reduce Unity CI build times

## Goal

Reduce wall-clock time for Unity CI builds. Current warm-cache times range from ~8 min (smaller projects) to 27+ min (Outernet.Client linux64/magicleap). Identify bottlenecks and optimize.

## Context

T7 established the Unity CI workflow with Library caching. First-run (cold cache) results:

| Build | Cold | Warm |
|---|---|---|
| AndroidMobile (android) | 31m42s | 7m48s |
| Outernet.Client (android) | 39m42s | 9m35s |
| MapRegistrationTool (linux64) | 45m2s | 8m27s |
| Outernet.Client (magicleap) | 41m7s | ~27m+ |
| Outernet.Client (linux64) | 50m+ | ~27m+ |

Caching cut smaller builds by 4-5x. The two large Outernet.Client builds still take a long time even with warm caches — likely dominated by IL2CPP C++ compilation (linux64) and shader compilation (magicleap).

## Root cause (identified)

The cache key in `build-unity.yml` is **per-project but not per-platform**:

```yaml
key: unity-library-${{ matrix.project-name }}-${{ hashFiles(...) }}
```

All three Outernet.Client builds (linux64, android-mobile, magicleap) share **one cache entry**. Whichever platform finishes first on a cold run saves its Library — in practice, android-mobile wins the race. The linux64 and magicleap builds then restore an android-flavored Library that contains platform-specific artifacts (Bee build graph, shader cache, player data cache) for the wrong platform.

CI logs confirm this. Most recent run (2026-03-04):

| Build | Cache status | Shader cache hits | Build time |
|---|---|---|---|
| Outernet.Client (android) | HIT (exact key) | All local hits | 8m 41s |
| Outernet.Client (magicleap) | HIT (exact key) | 0 local hits | 34m 29s |
| Outernet.Client (linux64) | HIT (exact key) | 0 local hits | 58m 40s |
| AndroidMobile (android) | HIT (exact key) | All local hits | 7m 23s |
| MapRegistrationTool (linux64) | HIT (exact key) | All local hits | 6m 24s |

The fix is to add `${{ matrix.platform }}` to the cache key. But this creates a cache budget problem.

## Cache budget constraint

GitHub Actions cache has a **10 GB per-repo limit** (free tier). Current usage:

| Cache | Size |
|---|---|
| unity-library-Outernet.Client | 3.71 GiB |
| unity-library-AndroidMobile | 2.84 GiB |
| unity-library-MapRegistrationTool | 2.29 GiB |
| Total | ~8.84 GiB |

With per-platform keys, Outernet.Client would need 3 separate caches (~3.7 GiB each), pushing total to ~16 GiB — well over the 10 GiB limit. LRU eviction would kick in, causing periodic cold-cache builds (unacceptable).

As of Nov 2025, GitHub allows exceeding 10 GB with a paid plan (Pro/Team/Enterprise). Pricing is ~$0.07/GB/month. The project is FOSS/non-profit and wants to avoid paying.

## Areas to investigate (revised)

The original list was mostly wrong — `Library/Bee/`, shader cache, etc. are all inside `Library/` and already cached. The real issues are:

1. **Per-platform cache keys** — the primary fix. Requires solving the budget problem.
2. **Trimming cached content** — exclude `Library/PackageCache/` (~1.6 GiB per project, re-downloaded from UPM registry on each run in ~1-2 min) to free budget for per-platform keys. Estimated total with trimming: ~8.2 GiB (fits in 10 GiB, but tight).
3. **Machine-level Bee cache** (`BEE_CACHE_DIRECTORY` at `~/.cache/unity3d/bee`) — separate from `Library/Bee/`. Currently not cached in CI. Unclear whether it provides value beyond what `Library/Bee/` already provides when the project-local cache is warm. Needs empirical testing.
4. **Minor Docker CI gaps** — no Go module cache mount in `database-migrator` Dockerfile, no NuGet cache mount in `state-sync` Dockerfile. Small impact but easy wins.

## Research: Unity Library internals

The Library directory for MapRegistrationTool (4.8 GiB total):

| Directory | Size | Content-addressed? | Platform-specific? |
|---|---|---|---|
| `Bee/` | 2.9 GiB | Partially (CachedNodeOutput is MD5-keyed) | Yes — build artifacts are platform-specific |
| `PackageCache/` | 1.6 GiB | No (name@registry-hash) | No — packages are platform-independent |
| `Artifacts/` | 126 MB | Yes (hash-bucketed `00/`-`ff/`) | Yes — platform is part of the hash |
| `BurstCache/` | 144 MB | No | Yes |
| `ShaderCache/` | 36 MB | No (name-based directories) | Yes |
| `ScriptAssemblies/` | 34 MB | No | Partially |

Unity has two built-in cross-project deduplication mechanisms:
- **`BEE_CACHE_DIRECTORY`** (`~/.cache/unity3d/bee`) — machine-wide Bee cache for reusable build components (libIL2CPP, non-embedded package compilations)
- **Global UPM cache** (`~/.cache/Unity/upm/`) — shared package tarballs, configurable via `UPM_CACHE_PATH`

Unity Accelerator (network-level import cache) exists but is **proprietary** — violates FOSS-only principle.

## Research: Docker CI caching (already good)

The Docker build pipeline is well-optimized:
- Registry-based layer cache (`mode=max`) to `ghcr.io/.../build-cache` — no size limit
- BuildKit `--mount=type=cache,id=uvcache` — all Dockerfiles share one uv download cache
- Lock-file-before-source pattern in every Dockerfile
- `setup-uv` with `enable-cache: true` for host-side uv cache

## Approach

**Phase 1: Understand Unity's Bee build system.** Research Bee internals (web + local inspection + empirical build), understand the structural relationship between project-local `Library/Bee/` and machine-level `~/.cache/unity3d/bee`, record findings in `.pulsar/research/unity-bee-cache-internals.md`. (**Done.**)

**Phase 2: CI workflow changes.**
1. Add `${{ matrix.platform }}` to the cache key so each platform gets its own Library cache.
2. Add a shared UPM cache step (`~/.cache/Unity/upm/`, ~113 MB) that serves all builds — analogous to the shared uv download cache in Docker builds.
3. Trim `Library/PackageCache/` (~1.6 GiB/project) from per-project caches. With the UPM cache warm, PackageCache repopulation is a fast local extraction (verified: 56s total build including extraction, no measurable penalty).

This deduplicates ~8 GiB of per-project PackageCache into a single ~113 MB shared entry, freeing budget for per-platform Library caches.

Docker CI cache gaps (Go module cache in database-migrator, NuGet cache in state-sync) are covered by T81.

## Design decisions

- Bee cache experiment runs locally in the COI container (Unity is licensed here), not in CI.
- Bee experiment happens before the cache key fix — results inform the cache budget.
- Docker cache gaps excluded from this ticket (T81).
- Machine-level Bee cache (`~/.cache/unity3d/bee`) is NOT worth caching in CI — only 37 MB after a full build, max 256 MB with auto-cleanup. See `.pulsar/research/unity-bee-cache-internals.md`.
- PackageCache trimming requires a shared UPM cache to avoid network re-downloads. The global UPM cache (`~/.cache/Unity/upm/`) is the UPM equivalent of uv's download cache — stores compressed tarballs (~113 MB), shared across all projects/platforms. Verified locally: with UPM cache warm, PackageCache repopulation adds negligible time (56s total build including extraction from tarballs).
- **ORAS/GHCR is the permanent Library caching strategy**, not `actions/cache`. The 10 GB `actions/cache` budget will inevitably be exceeded as projects and platforms grow. ORAS pushes to GHCR have no size limit. The tradeoff (slower network transfer vs `actions/cache`'s internal blob storage) is mitigated by zstd compression and conditional save (only on cache miss).

## Key files

- `.github/workflows/unity.yml` — cache configuration (the main target)
- `scripts/src/scripts/build_unity.py` — build output paths

## Done when

- Root causes of slow warm-cache builds identified (**done** — cross-platform cache sharing)
- At least one optimization implemented that measurably reduces the slowest build time (**done** — per-platform ORAS cache keys + PackageCache trimming + UPM shared cache + volume-mount disk cleanup; Outernet.Client magicleap 27m+ → 11m, linux64 27m+ → 10m)

## Research: UPM cache architecture

The global UPM cache (`~/.cache/Unity/upm/`) stores downloaded package tarballs, content-addressed by sha512. Conceptually identical to uv's download cache or npm's global cache — a shared download layer that deduplicates network fetches across projects.

| Layer | Size (MapRegistrationTool) | Content | Platform-specific? | Per-project? |
|---|---|---|---|---|
| Global UPM cache (`~/.cache/Unity/upm/`) | 113 MB | Compressed tarballs (149 entries) | No | No — shared |
| `Library/PackageCache/` | 1.6 GiB | Extracted package source | No | Yes — per project |

When `Library/PackageCache/` is missing but the UPM cache is warm, Unity extracts packages from local tarballs during project open. Verified: full build with warm UPM cache + deleted PackageCache completed in 56s (no measurable penalty vs having PackageCache pre-populated).

## Log

Phase 1 (Bee cache research) completed cleanly. Web research + local inspection + empirical build confirmed:
- Machine-level Bee cache (`~/.cache/unity3d/bee`) produced only 37 MB after a full MapRegistrationTool linux64 build (95 content-addressed entries of package/libIL2CPP compilations)
- Unity auto-cleans this cache to 256 MB max via LRU eviction
- Not worth caching in CI — negligible compared to multi-GiB Library caches
- Full findings in `.pulsar/research/unity-bee-cache-internals.md`

Phase 2 (workflow changes) in progress. Three CI failures encountered and fixed:
- `${tag,,}` bashism fails in GameCI containers (default shell is `sh`, not `bash`) → replaced with `tr '[:upper:]' '[:lower:]'`
- `tar --zstd` shells out to `zstd` binary which isn't installed (only `libzstd1` present) → switched to `tar -czf` (gzip)
- ORAS rejects absolute file paths (`/tmp/library.tar.gz`) to prevent path traversal → switched to relative paths in cwd
- Outernet.Client magicleap cold build hit "no space left on device" → added `jlumbroso/free-disk-space` step
- `jlumbroso/free-disk-space` does nothing inside `container:` jobs — composite actions run inside the container, not on the host, so `rm -rf /usr/share/dotnet` etc. target container paths that don't exist. All 5 jobs showed 0-second completion for that step. AndroidMobile (android-mobile) hung during IL2CPP compilation (1.5+ hours, no logs) — likely disk exhaustion. Fix: replace the action with `container.volumes` bind mounts from host paths + `rm -rf` inside the container. See `.pulsar/research/gha-container-disk-space.md`.
- Volume-mount disk cleanup confirmed working (30-90s per job instead of 0s). But ORAS save/restore now dominates build time — save step alone was 4-7 min per job with gzip, longer than the actual build for 2 of 3 completed jobs. Fix: switch from gzip to zstd compression (install `zstd` CLI in container), and skip save entirely on cache hit (only save on cold-cache runs).

Also renamed workflow files: `build.yml` → `build-docker.yml`, `unity.yml` → `build-unity.yml`.

Phase 2 verification complete. Cold-cache run (all 5 jobs success): zstd ORAS push succeeded for all platforms, UPM cache populated. Warm-cache run (all 5 jobs success): all ORAS cache hits, save correctly skipped, UPM cache hit. Final warm-cache results:

| Build | Old warm | New warm | Speedup |
|---|---|---|---|
| MapRegistrationTool (linux64) | 8m 27s | 7m 12s | 1.2x |
| AndroidMobile (android-mobile) | 7m 48s | 8m 29s | ~same |
| Outernet.Client (android-mobile) | 9m 35s | 10m 37s | ~same |
| Outernet.Client (magicleap) | ~27m+ | 11m 42s | 2.3x |
| Outernet.Client (linux64) | ~27m+ | 10m 55s | 2.5x |

## Observations

- GameCI containers (`unityci/editor:*`) default to `sh`, not `bash`. Avoid bashisms in workflow `run:` steps.
- `libzstd1` is installed but `zstd` CLI is not. `tar --zstd` requires the CLI binary.
- `jlumbroso/free-disk-space` (and all composite actions that use `sudo rm`) are incompatible with `container:` jobs. Use `container.volumes` to bind-mount host paths and `rm -rf` them from inside the container instead.
