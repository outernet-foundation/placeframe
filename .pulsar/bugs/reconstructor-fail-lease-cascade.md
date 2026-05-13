# Reconstructor `fail_lease` failure cascades to broad except

**Severity**: medium — leases stuck in non-terminal state; reaper is the only recovery.

**Location**: `docker/reconstructor/`'s outer exception handler around the per-lease loop.

**Symptom**: When the pipeline fails for any reason, the worker tries `fail_lease`. If `fail_lease` *itself* fails (network blip, JWKS retry, API restart, 5xx), the failure is caught by the surrounding `except Exception:` and silently swallowed. The lease stays in whatever non-terminal state it had (`running`, `uploading`, etc.) until the API's 30-minute reaper flips it to `failed`.

**Mechanism**: `fail_lease` is wrapped in the same broad `except` that catches the original pipeline error. Any exception raised by `fail_lease` itself goes to the same handler; the worker logs and moves on. There's no retry, no escalation, no out-of-band signal.

**Fix sketch**: Separate the `fail_lease` call into its own try-block with bounded retries (e.g. exponential backoff, 3 attempts, total budget ~30s) before giving up. On final failure, log at ERROR with a `lease_id` and a "reaper will recover" note. Optionally write to a local on-disk retry queue that the worker drains on startup, but that's a bigger lift — bounded retries cover the common case.

**Verification**: Mock `fail_lease` to fail twice then succeed; assert the lease ends in `failed`. Mock to fail unconditionally; assert the worker logs ERROR and falls back to reaper-recovery.
