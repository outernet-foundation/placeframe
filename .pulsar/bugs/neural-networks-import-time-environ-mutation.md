# `neural-networks` mutates `os.environ` at import time

**Severity**: low/medium — surprising side effect; bites any process that imports neural-networks for unrelated reasons.

**Location**: `packages/python/neural-networks/src/neural_networks/...` — the `environ["DB_ROOT"] = ""` assignment at module top.

**Symptom**: Importing anything from `neural-networks` unconditionally sets `DB_ROOT=""` in the process environment. Any sibling code or library that reads `DB_ROOT` after the import sees the empty string instead of whatever the operator set. In a test harness that imports `neural-networks` for one suite and another package for an adjacent suite, results diverge based on import order.

**Mechanism**: Module-level `import` runs the assignment unconditionally as a side effect of resolving the import graph. There is no guard checking whether `DB_ROOT` is already set.

**Fix sketch**: Either (a) wrap the assignment in `os.environ.setdefault("DB_ROOT", "")` so it only fires when nothing has set it, or (b) move the assignment into the dirtorch import path (lazy, inside the function that actually needs it), or (c) refactor dirtorch to take `db_root` as a parameter rather than reading the env. (a) is the smallest fix.

**Verification**: Set `DB_ROOT=foo` before import; import `neural_networks`; assert `os.environ["DB_ROOT"] == "foo"`.
