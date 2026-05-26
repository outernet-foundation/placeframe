# `tune_reconstruction.py` has no reconstruction reuse and no polling timeout

**Severity**: medium — re-running the sweep doubles DB row count and can hang indefinitely on a stuck cell.

**Location**: `scripts/src/scripts/tune_reconstruction.py` — `_run_cell` (lines 100-147) and its polling loop (lines 111-124).

**Symptom**: (1) Re-running the sweep against the same capture-ids creates a fresh `Reconstruction` for every cell every time, regardless of whether an identical-options reconstruction already exists. The reconstructions table grows without bound across iterations. (2) The polling `while True: await sleep(POLL_INTERVAL_S)` loop has no upper bound — a reconstruction stuck in `IN_PROGRESS` blocks the sweep forever, with no log indicating which cell is the culprit.

**Mechanism**: Contrast `fit_calibration.match_or_create_reconstruction` (`fit_calibration.py:216`), which queries existing reconstructions for the same `(capture_id, options)` tuple and reuses on hit, and tracks `RECONSTRUCTION_TIMEOUT_S = 1800` (line 81) to bound the polling loop. `tune_reconstruction.py` ships neither.

**Fix sketch**: Factor `match_or_create_reconstruction` and the bounded polling helper out of `fit_calibration.py` into a shared module (e.g. `scripts/src/scripts/_reconstruction_lifecycle.py`), and have both scripts consume it. Drop-in reuse keeps the two callers in lockstep when either grows new options.

**Verification**: Re-run `uv run tune-reconstruction --captures <id>` twice; the second run should not create new reconstruction rows for cells whose options already succeeded. Stop a reconstructor mid-run; the sweep should surface a `RuntimeError` naming the stuck cell within `RECONSTRUCTION_TIMEOUT_S`.
