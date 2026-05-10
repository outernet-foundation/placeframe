# Localizer ConvexHull bare-`Exception` swallow

**Severity**: low/medium — silent failure mask; metrics under-report failures.

**Location**: `docker/localizer/src/` ConvexHull computation path.

**Symptom**: A `ConvexHull` failure (degenerate point set, scipy import error, numeric collapse) is caught and silently downgraded. The query proceeds but with a wrong / null hull, and any metric or filter downstream of the hull is computed against bad data. No log, no metric increment.

**Mechanism**: `except Exception:` block (rather than the specific `scipy.spatial.qhull.QhullError` or `ValueError`) swallows everything, including programmer errors (`AttributeError`, `KeyError`) that would otherwise surface as 500s.

**Fix sketch**: Narrow the catch to `QhullError` (and possibly `ValueError`). On catch, log at WARNING with `reconstruction_id` and the input point count, and either return early with a typed "hull-not-computed" response or fall through with an explicit sentinel that downstream code checks.

**Verification**: Inject a degenerate-input test (3 collinear points) and assert (a) the log line fires, (b) the response carries a typed indicator, (c) `AttributeError` from the same code block is no longer swallowed.
