# Localizer bare `raise` outside any `except`

**Severity**: medium — latent crash gated on a CODEGEN escape.

**Location**: `docker/localizer/src/main.py:81`.

**Symptom**: `RuntimeError: No active exception to re-raise` if the bare `raise` ever executes — which happens if `CODEGEN=1` is set in any environment that *isn't* a one-shot OpenAPI dump and the calibration check triggers the path.

**Mechanism**: A bare `raise` statement sits outside an `except` block. Python re-raise semantics require an active exception in the current scope; without one, Python raises `RuntimeError`. Today, the surrounding control flow keeps the line unreachable in normal containers, but `CODEGEN` is set per-process and the assertion four lines later (`assert calibration is not None`) would have been the right guard if the bare `raise` had been deleted.

**Fix sketch**: Delete the bare `raise`. The `assert calibration is not None` immediately after handles the only failure mode the line was probably trying to express.

**Verification**: `grep -n "^[[:space:]]*raise[[:space:]]*$" docker/localizer/src/` returns zero matches after the fix.
