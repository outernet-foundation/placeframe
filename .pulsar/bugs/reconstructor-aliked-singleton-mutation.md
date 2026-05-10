# Reconstructor mutates ALIKED singleton between jobs

**Severity**: high — cross-job contamination of feature extraction.

**Location**: `docker/reconstructor/`'s feature-extraction phase. The mutation is `_aliked_model.dkd.n_limit = ...`.

**Symptom**: Job N+1 inherits the `n_limit` configured by job N. If job N requested a custom keypoint cap (via per-capture options) and job N+1 didn't, job N+1 silently runs with N's cap. Reconstructions look fine in isolation but degrade unpredictably under heterogeneous workloads.

**Mechanism**: `_aliked_model` is a process-singleton (loaded once at worker startup to amortize GPU cost). Each job mutates an attribute on the singleton's `dkd` submodule and never resets it. The pipeline assumes the singleton is config-immutable.

**Fix sketch**: Either (a) snapshot the original `n_limit` at startup and reset it in a `try/finally` at the end of each job, or (b) refactor ALIKED extraction to thread the limit through a per-call argument instead of mutating shared state. (b) is correct; (a) is the smallest diff.

**Verification**: Run two reconstructions back-to-back, the first with a non-default `n_limit`. Assert the second's keypoint counts match the default-config baseline.
