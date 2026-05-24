# Localizer `load_map` re-downloads every file on every call

**Severity**: low/medium — wasted bandwidth + latency; harmless when cache is warm, painful on container restart with a persistent volume.

**Location**: `docker/localizer/src/map.py:49-67`.

**Symptom**: Every call to `load_map` runs `s3.download_file` for every artifact under the reconstruction's prefix, even when the local file already exists on disk. In practice this only matters when the in-memory cache misses but the on-disk artifacts are still present — e.g. after a process restart with a persistent `/tmp/reconstructions/` volume, or after an eviction-with-disk-retention policy. Today it amplifies cold-start latency on container restart.

**Mechanism**: The download loop in `load_map` unconditionally calls `s3_client.download_file(...)` for each matching key. There is no `if local_path.exists(): continue` short-circuit. The on-disk artifacts are effectively a write-only cache.

**Fix sketch**: Before `s3_client.download_file(...)`, check `if local_path.exists() and local_path.stat().st_size > 0: continue`. Optionally compare ETag/size against the S3 object metadata if integrity matters.

**Verification**: Call `load_map` twice for the same id with a clean S3 mock; assert `download_file` is invoked once per artifact across both calls.
