# Localizer concurrent map-load race (non-reentrant)

**Severity**: medium — first-query-after-startup races; harder to hit once a map is cached.

**Location**: `docker/localizer/src/`'s map-load path (the function gated by `_load_lock` / `_load_state` in the dangling executor scaffolding).

**Symptom**: Two simultaneous `localize_image` requests for the same `reconstruction_id`, before that map is in `_maps`, both enter the load path. They independently download from MinIO, parse `features.h5` / `global_descriptors.h5` / OPQ / PQ, and one of them clobbers the other's entry in `_maps`. Worst case: one request gets a half-loaded map and a `KeyError` or wrong-key match.

**Mechanism**: The load path checks `_maps[id]`, misses, runs the load, and stores. There is no `asyncio.Lock` (or per-id lock) gating the *load itself*, so two coroutines can be in flight simultaneously. The vestigial `_load_lock` and `LoadState` scaffolding exist but aren't wired into the read path that matters.

**Fix sketch**: Add `dict[str, asyncio.Lock]` keyed by `reconstruction_id`. On miss, acquire the per-id lock, re-check `_maps`, then load and store. Or use `asyncio.Future` per id so concurrent waiters share the in-flight load.

**Verification**: Cold-cache load test that fires N concurrent `localize_image` for the same `reconstruction_id`; assert MinIO get-count is exactly 1 per artifact.
