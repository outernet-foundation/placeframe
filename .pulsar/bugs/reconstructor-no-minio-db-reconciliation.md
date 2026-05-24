# Reconstructor lacks MinIO ↔ DB reconciliation after `succeed_lease` failure

**Severity**: medium — successful artifacts get marked `FAILED` 30 minutes later; no autorecovery from a transient API outage at the very last step.

**Location**: `docker/reconstructor/src/reconstructor/main.py:74-82` (succeed/fail both inside the outer try, no retry on the lease finalization itself).

**Symptom**: If `succeed_lease` raises after `sfm_model/` has fully uploaded to MinIO, the exception falls through to the broad `except` which calls `fail_lease`. The row eventually flips to `FAILED` (either via `fail_lease` or the 30-minute API-side reaper) despite a complete, valid artifact set sitting in MinIO. A subsequent `retry` re-runs the entire pipeline from scratch.

**Mechanism**: `succeed_lease` is not retried, and nothing scans MinIO post-hoc to recover. The DB is the sole source of truth; artifact presence in `dev-reconstructions/<id>/sfm_model/` doesn't influence status.

**Fix sketch**: Bounded retry around `succeed_lease` itself (same shape as the proposed fix in `reconstructor-fail-lease-cascade.md`). For belt-and-suspenders, a reconciler task in the API can promote `RECONSTRUCTING`/`FAILED` rows whose `sfm_model/` prefix is complete to `SUCCEEDED` instead of relying on retry.

**Verification**: Mock `succeed_lease` to fail; assert the row eventually reaches `SUCCEEDED` (via retry or reconciler), not `FAILED`.
