# Reconstructor `noqa: TID251` comments carry temporal "Phase T" markers

**Severity**: low — violates the project conventions on comments (no temporal language, no external-context pointers).

**Location**: Five `# noqa: TID251 -- Phase T piece 3 follow-up migration` markers — `run_reconstruction.py:30`, `run_reconstruction.py:138`, `colmap.py:26`, `metrics_builder.py:10`, `rig.py:6`.

**Symptom**: The comments anchor to a moment ("Phase T piece 3 follow-up") and a doc that isn't inlined. A reader who arrives after Phase T is complete cannot tell whether the suppression is still warranted; the comment fails the cold-reader test.

**Mechanism**: `TID251` is the banned-import rule. The suppression is for `from numpy.typing import NDArray`, which the codebase wants migrated to a typed wrapper. Until the migration completes the suppression is necessary, but the rationale should be self-contained (e.g. `# noqa: TID251 — NDArray import; typed wrapper migration pending`).

**Fix sketch**: Either (a) complete the migration and remove all five suppressions, or (b) rewrite the comments to drop "Phase T piece 3" and inline the constraint that justifies the suppression. (a) is the architecturally correct fix.

**Verification**: `grep -rn "Phase T" docker/reconstructor/` returns zero hits.
