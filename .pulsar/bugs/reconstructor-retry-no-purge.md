# Reconstructor retry doesn't purge prior MinIO outputs

**Severity**: medium — silent corruption: stale artifacts survive across attempts.

**Location**: `docker/api/`'s `retry_reconstruction` (`reconstructions.py:192`) and the reconstructor's upload path.

**Symptom**: A retry of a `failed` reconstruction reuses the same `dev-reconstructions/<reconstruction_id>/` prefix. Files written by the second attempt overwrite the first attempt's by key, but any files the first attempt wrote *under different keys* (e.g. `sfm_model/extra_model_2/` if multi-model emerged on retry but not original, or vice versa) survive. Downstream readers walk the prefix and may pick up half-and-half artifacts.

**Mechanism**: `retry_reconstruction` flips the row `failed` → `queued` and that's all. The MinIO prefix is untouched. The upload phase uses `_put_artifact` per file by exact key — same-key writes overwrite, but cross-attempt key set differences leak.

**Fix sketch**: Before flipping the row to `queued`, recursively delete `dev-reconstructions/<reconstruction_id>/` from MinIO. Do it inside the same transaction-equivalent as the row update so a half-purge doesn't corrupt state. Or, alternatively, rotate the on-disk prefix (`dev-reconstructions/<reconstruction_id>/attempt-N/`) and have readers consult a "current attempt" pointer.

**Verification**: Force a retry where the first attempt produced extra files (e.g. an `intermediate.h5`) that the second attempt does not. Assert no first-attempt files remain in MinIO after the retry completes.
