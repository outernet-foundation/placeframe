# Unity Bee Build System: Cache Internals

Research for T78 (Unity CI build time optimization). Produced 2026-03-04.

## What is Bee?

Bee ("Build Everything Engine") is Unity's incremental build backend, managing the full player build pipeline: script compilation, IL2CPP conversion, C++ compilation, code stripping (UnityLinker), Burst compilation, and packaging.

**Architecture**: Two-program design.
1. **Build Program** — .NET application that reads source/config files and generates a build graph (DAG of nodes, commands, and dependencies), serialized to `.dag.json`.
2. **`bee_backend`** — execution engine based on the [Tundra](https://github.com/deplinenoise/tundra) build system (archived Jan 2025, moved to Unity's internal Bee repo). Reads the DAG, detects changed inputs via content hashing, and rebuilds only necessary nodes in parallel.

**History**: Originated from a 2016 hackweek. Rolled out incrementally: Unity 2021.1 (script compilation), 2021.2 (desktop/Android), 2022.1 (iOS/Xbox), 2022.2 (all platforms + Burst). `Library/Bee/` first appeared when upgrading from Unity 2020 to 2021.

**Sources**: [Aras Pranckevičius blog](https://aras-p.info/blog/2019/06/21/Replacing-a-live-system-is-really-hard/), [Unity blog](https://unity.com/blog/engine-platform/accelerating-player-builds-with-incremental-build-pipeline), [Unity manual](https://docs.unity3d.com/6000.1/Documentation/Manual/incremental-build-pipeline.html).

## Two cache levels

### Project-local: `Library/Bee/`

The primary cache. Contains the complete state of the most recent build for this project.

**Observed structure** (MapRegistrationTool, linux64 build, 2.9 GiB total):

| Path | Size | Content |
|---|---|---|
| `*.dag`, `*.dag.json`, `*-inputdata.json` | ~100 MB | Build graphs (DAGs). Hex prefix like `2400b0aE` is an internal identifier, not a content hash. Multiple DAGs: editor scripts (`E` suffix), player scripts (`P`), player build (`Player*`). |
| `artifacts/LinuxPlayerBuildProgram/zbz95/` | 1.5 GiB | Compiled `.o` files (504 total) from IL2CPP C++ compilation. **Project-specific, platform-specific.** These are the expensive outputs. |
| `artifacts/LinuxPlayerBuildProgram/il2cppOutput/cpp/` | 1.1 GiB | Generated C++ source files (699 total) from IL2CPP conversion of managed assemblies. **Project-specific.** Input to the C++ compilation step. |
| `artifacts/LinuxPlayerBuildProgram/fregp/` | 81 MB | Contains `il2cpp.a` (43 MB static library) + compiled `.o` files. This is the **libIL2CPP runtime** — project-independent but platform-specific. The machine-level cache is designed to share this. |
| `artifacts/LinuxPlayerBuildProgram/ManagedStripped/` | 27 MB | Post-UnityLinker stripped assemblies. Project-specific. |
| `artifacts/2400b0aE.dag/` | 83 MB | Compiled C# script assemblies (`.dll`, `.pdb`). Largely platform-independent. |
| `artifacts/2400b0aP.dag/` | 40 MB | Player script assemblies. |
| `CachedNodeOutput/` | 460 KB | 372 files, **all 0 bytes**. MD5-keyed marker files tracking which nodes have cached outputs. Actual content lives in `artifacts/`. |
| `tundra.digestcache` | 1.6 MB | Signature database: file path → content hash mappings for change detection. |
| `tundra.scancache` | 234 KB | Header/include dependency scan cache. |
| `TundraBuildState.state.map` | 840 KB | Build state tracking. |
| `backend*.traceevents` | ~660 KB | Chrome Trace profiling data. |

**Change detection**: Bee/Tundra uses a `DigestCache` (memory-mapped file) that maps file paths to content hashes. Original Tundra supported SHA-1 and xxHash; Unity's fork likely uses one or both. On rebuild, Tundra checks if input file content hashes match the cached hashes — if unchanged, the node's outputs are reused.

### Machine-level: `BEE_CACHE_DIRECTORY`

A supplementary cache for **cross-project artifact reuse**. Only stores project-independent build outputs.

**Default locations**:
- Linux: `~/.cache/unity3d/bee`
- macOS: `~/Library/Unity/cache/bee`
- Windows: `%USERPROFILE%\AppData\Local\Unity\Caches\bee`

**Observed after a MapRegistrationTool linux64 build**: 37 MB total, 95 content-addressed entries. Each entry is a directory named `{32-char-hex}{32-zeros-with-suffix-04}`, containing 3-4 hash-named files (one typically 0 bytes as a marker, others are compiled artifacts up to ~1.8 MB).

**Auto-cleanup**: Unity's `RunCleanBeeCache` method (in `UnityBeeDriver.cs`) enforces a **256 MB target size** via LRU eviction — sorts by modification time, deletes oldest entries until under threshold.

**What it stores** (per Unity documentation): "non-embedded packages and libIL2CPP artifacts." These are compilations that depend only on the Unity installation and package versions, not on project-specific code.

**What it does NOT store**: Project-specific IL2CPP C++ compilation outputs (the 1.5 GiB of `.o` files in `zbz95/`), generated C++ (the 1.1 GiB in `il2cppOutput/`), stripped assemblies, or any content-building outputs.

## Cache lookup flow

1. `bee_backend` reads the `.dag.json` build graph.
2. For each node, checks `tundra.digestcache` to see if input files have changed since last build.
3. If unchanged, reuses outputs from `Library/Bee/artifacts/` directly (zero work).
4. If changed, checks `BEE_CACHE_DIRECTORY` for matching cross-project artifacts (libIL2CPP, package compilations).
5. If no cache hit at either level, executes the node's build commands.

The project-local cache is checked first (it's the authoritative build state). The machine-level cache is only consulted for specific node types that are known to be project-independent.

## Environment variables

| Variable | Purpose | Default |
|---|---|---|
| `BEE_CACHE_DIRECTORY` | Override machine-level cache location | OS-specific (see above) |
| `BEE_CACHE_BEHAVIOUR` | Control cache mode: `"_"` (off), `"R"` (read-only), `"W"` (write-only), `"RW"` (read+write) | `"RW"` |

No documented verbosity/debug flags for Bee cache behavior.

**Source**: [UnityCsReference — UnityBeeDriver.cs](https://github.com/Unity-Technologies/UnityCsReference/blob/master/Editor/Mono/Scripting/ScriptCompilation/BeeDriver/UnityBeeDriver.cs), [Unity Issue Tracker UUM-77620](https://issuetracker.unity3d.com/issues/bee-cache-documentation).

## CI implications

**The machine-level Bee cache is not worth caching in CI.** At 37 MB (max 256 MB), it's negligible compared to the multi-GiB `Library/Bee/` caches. The expensive work — IL2CPP C++ compilation (~7.5 min for MapRegistrationTool, producing 1.5 GiB of `.o` files) — is project-specific and only cached in `Library/Bee/artifacts/`. The machine-level cache's cross-project savings (libIL2CPP runtime + package compilations) would shave seconds at most.

**The critical fix is per-platform cache keys.** The dominant cost in slow builds is IL2CPP C++ compilation and shader compilation, both of which produce platform-specific artifacts in `Library/Bee/artifacts/{Platform}PlayerBuildProgram/`. When platforms share a cache entry, these artifacts are for the wrong platform and must be recompiled from scratch.

**`Library/PackageCache/` is safe to exclude from per-project CI caches** when paired with a shared UPM cache. See below.

## Global UPM cache (`~/.cache/Unity/upm/`)

The global UPM cache is Unity's package download cache — conceptually identical to uv's download cache or npm's global cache. It stores compressed package tarballs, content-addressed by sha512, shared across all projects on the machine.

**Observed after a MapRegistrationTool build**: 113 MB total, 149 files in `db/content-v2/` (sha1 and sha512 hash-bucketed directories). This corresponds to the 1.6 GiB of extracted content in `Library/PackageCache/` — roughly 14x compression ratio.

**Relationship to `Library/PackageCache/`**: When Unity opens a project and resolves `Packages/manifest.json`, it checks the global UPM cache for each required package. If the tarball is present, it extracts locally. If not, it downloads from the registry and caches the tarball.

**CI strategy**: Cache `~/.cache/Unity/upm/` as a single shared entry across all builds (~113 MB). Trim `Library/PackageCache/` from per-project Library caches (~1.6 GiB each). On cache restore, Unity repopulates PackageCache from local tarballs — verified to add negligible time (56s total build including extraction, no measurable penalty vs pre-populated PackageCache).

**Budget impact**: Replaces ~1.6 GiB × N projects of per-project PackageCache with a single ~113 MB shared entry. For the current 5-build matrix (3 distinct projects), this saves ~4.8 GiB of cache budget.
