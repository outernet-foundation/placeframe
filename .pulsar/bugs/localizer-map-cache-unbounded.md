# Localizer `_maps` in-memory cache has no eviction

**Severity**: medium — slow leak; eventually OOMs a long-lived container that has serviced many distinct reconstructions.

**Location**: `docker/localizer/src/main.py:44` (`_maps: dict[UUID, Map]`).

**Symptom**: Memory grows linearly with the number of distinct `reconstruction_id`s the process has ever localized against. Each `Map` holds a full pycolmap `Reconstruction` (points3D, images), keypoints, PQ codes, padded tile descriptors, OPQ matrix, and PQ quantizer — easily hundreds of MB for a non-trivial map. A localizer serving many tenants over its lifetime eventually OOMs and is restarted by Docker, dropping warm caches for *everyone*.

**Mechanism**: `localize_image` does `if id not in _maps: _maps[id] = load_map(...)` and never removes entries. There is no LRU, no TTL, no max-size cap.

**Fix sketch**: Replace the bare `dict` with an LRU-bounded cache (e.g. `cachetools.LRUCache(maxsize=N)`) keyed by `reconstruction_id`. Eviction should also remove the corresponding `/tmp/reconstructions/<id>/` directory to bound disk usage (see companion bug `localizer-tmp-reconstructions-unbounded.md`). Size N picked from per-map memory footprint and the container's memory limit.

**Verification**: Loop test that localizes against N+5 distinct reconstruction ids; assert `len(_maps) == N` and that the earliest-loaded id is no longer present.
