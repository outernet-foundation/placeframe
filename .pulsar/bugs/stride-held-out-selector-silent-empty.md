# `StrideHeldOutSelector` silently holds out every frame

**Severity**: medium — calibration runs on an empty test set; metrics are meaningless.

**Location**: `scripts/src/scripts/...` — `StrideHeldOutSelector`.

**Symptom**: When the selector is configured with `target_count >= len(timestamps)`, it holds out *every* frame. Calibration then runs on a zero-frame test set, the resulting metrics are computed against zero samples, and the calibration artifact is written with garbage statistics. The pipeline succeeds; the artifact is wrong.

**Mechanism**: The selector computes a stride such that `target_count` frames are picked. With `target_count >= len(timestamps)`, the math degenerates and every frame is selected. There is no guard rejecting that case.

**Fix sketch**: At the top of the selector, raise `ValueError` if `target_count >= len(timestamps)` (or, alternatively, clamp to `len(timestamps) - 1` and warn loudly). The right move depends on the caller's expectation; raising is safer.

**Verification**: Construct a selector with `target_count = len(timestamps)`; assert it raises before producing a held-out set. Add a test in `scripts/tests/`.
