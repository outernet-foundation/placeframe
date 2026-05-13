# `tune_reconstruction.py` `PB_FACTORS`/`PB_SEED` length-coupling unchecked

**Severity**: medium — adding an 11th option silently truncates; future contributor adds a knob and it does nothing.

**Location**: `scripts/src/scripts/tune_reconstruction.py` — the `PB_FACTORS` and `PB_SEED` arrays.

**Symptom**: The arrays are coupled by index (option N uses `PB_FACTORS[N]` and `PB_SEED[N]`), but their lengths are independent. Adding an 11th `PB_FACTOR` without an 11th `PB_SEED` truncates silently — the eleventh tuning run uses an out-of-range index, which Python returns as `IndexError` *only if* the loop bound was set from `len(PB_FACTORS)`. If the loop bound is set from `len(PB_SEED)`, the eleventh `PB_FACTOR` is never used. Either way it's a silent contract violation.

**Mechanism**: Two parallel lists, no `assert len(PB_FACTORS) == len(PB_SEED)` at module load, no `zip()` strictness check.

**Fix sketch**: Replace the parallel lists with a single `list[tuple[float, int]]` (or a dataclass per option). Or, minimally, assert `len(PB_FACTORS) == len(PB_SEED)` at module top.

**Verification**: Mismatch the lengths; the script should fail at load time, not silently truncate.
