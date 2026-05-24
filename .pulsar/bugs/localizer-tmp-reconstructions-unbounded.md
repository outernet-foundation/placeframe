# Localizer `/tmp/reconstructions/` grows without bound

**Severity**: medium — disk leak; on container with constrained ephemeral storage, eventually fails `download_file` with ENOSPC.

**Location**: `docker/localizer/src/main.py:36` (`RECONSTRUCTIONS_DIR = Path("/tmp/reconstructions")`), `docker/localizer/src/map.py:42-67` (`load_map`).

**Symptom**: Every map ever loaded leaves its full artifact set (sfm_model directory, `features.h5`, `global_descriptors.h5`, OPQ matrix, PQ quantizer) under `/tmp/reconstructions/<id>/` for the lifetime of the container. With many distinct reconstructions, the tmpfs/overlay fills, and subsequent `s3.download_file` calls fail with `OSError: [Errno 28] No space left on device`.

**Mechanism**: `load_map` downloads every artifact from MinIO and writes it under `reconstructions_dir / str(id) /`. No cleanup path ever removes these directories — not on `_maps` eviction (there is no eviction; see `localizer-map-cache-unbounded.md`), not on shutdown, not on a TTL sweep.

**Fix sketch**: Couple disk cleanup to the cache eviction added by `localizer-map-cache-unbounded.md`: when an id is evicted from the LRU, `shutil.rmtree(RECONSTRUCTIONS_DIR / str(id), ignore_errors=True)`. Also gate the existing download path on `if local_path.exists(): continue` so a reload (same id, second container restart with persistent volume) doesn't re-pull — see `localizer-load-map-redownloads.md`.

**Verification**: Localize against N distinct reconstructions, evict the first, assert `(RECONSTRUCTIONS_DIR / str(first_id)).exists() is False`.
