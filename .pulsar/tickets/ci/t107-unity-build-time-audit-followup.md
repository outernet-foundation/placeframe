---
id: T107
title: Implement Unity CI build time audit recommendations
status: ready
depends_on: [T104]
---

# T107: Implement Unity CI build time audit recommendations

## Goal

Act on findings from the CI audit of run 23084448524 (2026-03-14). The magicleap build took 30m 18s due to a Library cache miss and cold IL2CPP compilation. Several structural improvements can prevent this from recurring and improve build observability.

## Context

### Audit findings (run 23084448524)

The Outernet.Client (magicleap) build was the only one with a Library cache miss. All other builds (6 of 7) had warm caches and completed in 2-7 minutes. Magicleap took 30m 18s, dominated by cold IL2CPP C++ compilation (20.8 min, 2558 object files) and cold asset packaging (2.8 min).

**There was no post-build hang.** Unity exited cleanly in 29 seconds after build completion. The perceived "hanging" was the IL2CPP C++ compilation phase, which produces very sparse log output (~1 progress line per minute with gaps up to 76 seconds of silence).

### Why the cache missed

The Library cache key is `unity-library:{project}-{platform}-{manifest-hash[:8]}`. Commit c91689c9 ("Regenerate Unity lock files after UPM package rename") changed `manifest.json`, invalidating all Library caches. In subsequent CI runs:

- android-mobile succeeded in run 23083359004 → saved its cache with the new hash
- magicleap **failed** in that run → never reached "Save Library cache"
- magicleap was **cancelled** in run 23082858701 → also never saved

Since the cache only saves after a successful Build step, magicleap's cache was never populated for the new manifest hash. This is a structural vulnerability: if a build fails after a cache-invalidating change, it stays cold until it succeeds, and cold builds are more likely to timeout.

### Build report comparison (same project, same codebase)

| Phase | magicleap (cold) | android-mobile (warm) | Ratio |
|---|---|---|---|
| Total Build player | 1609s (26.8min) | 288s (4.8min) | 5.6x |
| Compile scripts | 37.0s | 7.3s | 5.1x |
| Writing asset files | 170.5s | 2.7s | 63x |
| IL2CPP incremental build | 1247.8s (20.8min) | 165.9s (2.8min) | 7.5x |
| Gradle build | 68.3s | 69.3s | 1.0x (constant) |

### Errors and warnings in the build

- **18 cesium-unity `.meta` file errors** — `Packages/org.outernet.cesium-unity/Plugins/Android/x86_64` and its `.so` have no `.meta` files, repeated across Preprocess, Prebuild, Prepare assets (3x), and Postprocess (3x). Each triggers a package rescan.
- **1 cmake exception** — cesium-unity tries `cmake` during "Build scripts DLLs", not installed in CI container. Expected (uses pre-built `.so`) but noisy. Appears in all builds.
- **3 missing script warnings** — LocalUser, RemoteUser, SettingsPanel prefabs have missing script references. Likely a real codebase bug.
- **10 16KB-alignment warnings** — Magic Leap SDK `.so` plugins not 16KB-aligned, will break on Android 15+ devices.
- **8 GUID parse warnings** — `com.magicleap.unitysdk/Runtime/OpenXR/Common/ReferenceSpaces.cs.meta` has a malformed GUID. ML SDK bug.

## Key files

- `.github/workflows/build-unity.yml` — unified CI workflow (on `feature/ci-cd`); build-unity job starts at line 259, cache restore at line 293, cache save at line 306
- `build/src/build_scripts/build_unity.py` — Unity batchmode invocation; `PLATFORM_CONFIGS` dict at line 19
- `build/src/build_scripts/restore_cache.py` — ORAS cache restore logic
- `build/src/build_scripts/save_cache.py` — ORAS cache save logic (currently only saves on cache miss)
- `build/src/build_scripts/unity_ci_matrix.py` — generates build matrix with cache keys (line 24: `"cache-key": name.lower()`)
- `legacy/Outernet.Client/Packages/manifest.json` — UPM manifest whose hash is part of the cache key

## Approach

### 1. Add `timeout-minutes` to build-unity jobs

Currently no timeout on the build-unity job. A truly hung build would consume the full workflow timeout (6 hours on GitHub Actions). Add `timeout-minutes: 45` to the job (generous enough for cold builds, catches genuine hangs).

### 2. Implement Library cache fallback on miss

When the exact cache key misses (e.g. `outernet.client-magicleap-55b4a0e8`), fall back to the most recent tag matching `outernet.client-magicleap-*`. A stale Library cache is vastly faster than no cache — Unity's incremental import updates only changed assets. This breaks the cascade vulnerability where failed cold builds prevent cache population.

Implementation: in `restore_cache.py`, if the exact tag lookup fails, use `oras repo tags` to find the most recent matching prefix and pull that instead. Log clearly that it's a fallback hit, not an exact hit. Always save with the exact tag on success (overwriting the stale entry).

### 3. Consider IL2CPP "Faster builds" for CI

Unity's `IL2CPP Code Generation` setting has a "Faster (smaller) builds" option that reduces C++ optimization level. This trades runtime performance for build speed. For CI validation builds that won't be deployed, this could cut IL2CPP time significantly.

Implementation: set `EditorUserBuildSettings.il2CppCodeGeneration = Il2CppCodeGeneration.OptimizeSize` in the C# build methods (`BuildForMagicLeap`, `BuildForAndroidMobile`), gated by a `CI` environment variable or a build script flag.

Needs measurement: run one build with this setting and compare IL2CPP step duration against the current 165.9s (warm) / 1247.8s (cold).

### 4. Address cesium-unity `.meta` file errors

The 18 error messages about `Packages/org.outernet.cesium-unity/Plugins/Android/x86_64` having no `.meta` file indicate a packaging issue in the cesium-unity fork. Each occurrence triggers Unity to rescan the immutable package. Fix by adding the missing `.meta` files to the cesium-unity package, or by excluding the x86_64 directory if it's not needed for the target platforms.

## Done when

- [ ] `timeout-minutes` set on the build-unity job
- [ ] Library cache fallback implemented (ORAS prefix tag lookup on exact miss)
- [ ] IL2CPP "Faster builds" evaluated for CI (with before/after timing)
- [ ] cesium-unity `.meta` file errors addressed or triaged to a separate ticket
- [ ] Next CI run after T104 merge confirms magicleap cache is warm and builds in <10 minutes

## Next step

T104 must merge first (it introduces the unified `ci.yml` where these changes will land). After merge, verify magicleap cache warmth on the first `main` branch run, then implement items 1-4 in order of impact.
