# Reconstructor SIGTERM cannot stop in-flight pipeline

**Severity**: medium — graceful shutdown can leak leases; combined with `fail_lease` cascade, leases are lost until reaper.

**Location**: `docker/reconstructor/`'s signal handler and the `run_in_executor` call dispatching the pipeline.

**Symptom**: Sending SIGTERM to a busy reconstructor cancels the asyncio wait but does not stop the pipeline thread. The container takes the full pipeline duration (minutes) to exit. If shutdown also racing with `fail_lease`, the lease is dropped without ever being marked terminal — the 30-min API reaper is the only safety net.

**Mechanism**: The signal handler raises `CancelledError` in the event loop. The pipeline runs on a thread pool via `loop.run_in_executor(...)`. Threads are not cancellable in Python — `CancelledError` only unblocks the await on the future, not the work itself. The pipeline continues to completion (or crash) and the lease state machine doesn't get a definitive transition.

**Fix sketch**: Two layers. (1) Inside the pipeline, sprinkle cooperative cancellation checkpoints at phase boundaries (after extract, after match, after train, etc.) that read a shared `threading.Event`. The signal handler sets the event before raising. (2) Wrap the executor call with a watchdog that, on cancel, attempts a best-effort `fail_lease(reason="shutdown")` even if the pipeline is still grinding.

**Verification**: SIGTERM mid-pipeline; assert the lease ends in `failed` (not stuck in `running`/`uploading`) within seconds, not minutes.
