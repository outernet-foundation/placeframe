# T78 Plan: Unity CI Build Time Optimization

## Context

Unity CI builds for Outernet.Client (linux64, magicleap) take 30-60 min even with warm caches because the cache key is per-project but not per-platform — all three Outernet.Client builds share one android-flavored Library cache. Fixing this requires per-platform cache keys, but the resulting cache size (~16 GiB) would exceed GitHub's 10 GiB free-tier limit. Before committing to a cache strategy, we need to understand Unity's Bee build system well enough to make informed decisions.

## Approach

### Phase 1: Understand Unity's Bee build system

**Goal**: Develop a structural understanding of how Bee caching works — not just sizes, but mechanics. Record this as durable context.

#### 1a. Web research

Research Unity's Bee build system internals:
- What is Bee? (Unity's build backend — replaced the old editor pipeline)
- How does `Library/Bee/` work? What's the content-addressing scheme? What's in `CachedNodeOutput/` vs other subdirectories?
- What is `BEE_CACHE_DIRECTORY` (`~/.cache/unity3d/bee`)? How does it relate to `Library/Bee/`?
- How do cache lookups flow? Does Unity check machine-level first, then project-local? Or vice versa?
- Are there environment variables or settings that control Bee cache behavior?
- What's platform-specific vs shared in the Bee cache?

Sources: Unity forums, Unity documentation, blog posts, GitHub issues on GameCI/unity-builder.

#### 1b. Local inspection (guided by research)

With the research context, inspect MapRegistrationTool's existing `Library/Bee/` (2.9 GiB):
- Map the directory structure to what the research says
- Understand the content-addressing scheme (MD5-keyed `CachedNodeOutput/`)
- Identify what's platform-specific vs potentially shared across projects/platforms
- Check for any Bee config files or logs that reveal cache behavior

#### 1c. Empirical observation (guided by understanding)

Run a MapRegistrationTool linux64 build locally and observe:
- What files are written to `~/.cache/unity3d/bee`? Do they overlap with `Library/Bee/`?
- What does Unity log about Bee cache hits/misses? (parse build log output)
- Are there keys or hashes that reveal how cache entries are addressed?
- What's the relationship — does one level feed the other?

The research phase may reveal environment variables, log verbosity flags, or other controls that change what we should observe during the build.

#### 1d. Write up findings

Record the structural understanding in `.pulsar/research/unity-bee-cache-internals.md`. This is not just measurements — it's an explanation of how the system works, what we observed, and how it informs CI caching decisions. Update the ticket with a summary and link to the research file.

### Phase 2: Cache key fix + PackageCache trimming (unity.yml changes)

Informed by Phase 1 findings, implement the CI workflow changes.

**Change 1: Per-platform cache key** — Add `${{ matrix.platform }}` to the cache key.

In `.github/workflows/unity.yml`, change:
```yaml
key: unity-library-${{ matrix.project-name }}-${{ hashFiles(...) }}
restore-keys: |
  unity-library-${{ matrix.project-name }}-
```
To:
```yaml
key: unity-library-${{ matrix.project-name }}-${{ matrix.platform }}-${{ hashFiles(...) }}
restore-keys: |
  unity-library-${{ matrix.project-name }}-${{ matrix.platform }}-
```

**Change 2: Exclude PackageCache from cache** — Add a step after the build that deletes `Library/PackageCache/` before the post-job cache save runs. `actions/cache@v4` saves at post-job on cache miss; deleting PackageCache after the build means it won't be archived. It's re-downloaded from UPM registry on each run (~1-2 min).

```yaml
- name: Trim Library cache
  if: always()
  run: rm -rf ${{ matrix.project }}/Library/PackageCache
```

**Change 3 (conditional on Phase 1)**: If the Bee cache experiment reveals that the machine-level cache provides value, add a separate cache step for `~/.cache/unity3d/bee`. If it doesn't, skip this.

**Budget estimate after changes:**
- Per-platform Outernet.Client without PackageCache: ~2.1 GiB × 3 = ~6.3 GiB
- AndroidMobile without PackageCache: ~1.2 GiB
- MapRegistrationTool without PackageCache: ~0.7 GiB
- **Estimated total: ~8.2 GiB** (fits within 10 GiB)

## Key files

| File | Changes |
|---|---|
| `.github/workflows/unity.yml` | Add platform to cache key, add PackageCache trim step, potentially add Bee cache step |
| `.pulsar/research/unity-bee-cache-internals.md` | New — research findings on Bee build system |
| `.pulsar/tickets/ci/t78-unity-ci-build-time-optimization.md` | Record findings, update status |

## Verification

**Phase 1 (local)**:
- Research file written with structural understanding
- Build completes successfully
- Bee cache behavior observed and documented

**Phase 2 (CI)**:
- Push unity.yml changes to `dev` branch
- Monitor CI run: each platform gets its own cache entry, PackageCache excluded, cache sizes smaller
- Outernet.Client linux64/magicleap builds should be significantly faster with correct platform-specific caches
- Total cache usage stays under 10 GiB
