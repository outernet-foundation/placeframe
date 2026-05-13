# Reconstructor `CAPTURE_SESSION_DIRECTORY` not cleaned between jobs

**Severity**: medium — disk fill over time; fine on CI ephemeral runners, will bite long-running workers.

**Location**: `docker/reconstructor/`'s per-job working directory setup.

**Symptom**: Each job unpacks its tar into the same `CAPTURE_SESSION_DIRECTORY`. Files from job N survive into job N+1's working tree. Side effects: (1) the worker fills its disk over time; (2) any pipeline step that globs the directory may pick up cross-job files; (3) failed-mid-pipeline jobs leave intermediates that confuse retry logic.

**Mechanism**: The directory is created (or reused) at startup and never reset between leases.

**Fix sketch**: At the start of each lease, recursively `rmtree` the working directory (or use a fresh `tempfile.mkdtemp` per lease and delete on success/failure). Keep the model cache directory separate so the GPU weights don't get cleared.

**Verification**: Run two consecutive jobs whose tars contain a same-named file with different bytes. Assert job 2 sees only its own bytes.
