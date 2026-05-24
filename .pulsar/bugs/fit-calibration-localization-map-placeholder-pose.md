# `fit_calibration` writes localization map with placeholder ECEF pose

**Severity**: low today, latent — silently incorrect if reconstructor's anchor behavior changes.

**Location**: `scripts/src/scripts/fit_calibration.py:303-315` (`_localize_and_persist` → `create_localization_map`).

**Symptom**: Every `LocalizationMap` created by the fit-calibration orchestration is persisted at position `(0, 0, 0)` with identity rotation `(0, 0, 0, 1)`. Consumers reading the map pose back from the API see a pose that bears no relation to the capture's real-world frame.

**Mechanism**: `_localize_and_persist` hard-codes `position_x/y/z=0.0` and `rotation_x/y/z=0.0, rotation_w=1.0` in the `LocalizationMapCreate` call. This is currently harmless because the reconstructor's single-anchor alignment places the rebuilt map in the capture's truth frame, making the stored ECEF pose immaterial to the fit math. If reconstructions ever begin placing maps at non-identity ECEF poses (multi-anchor alignment, true-georeferenced output), this script will silently overwrite that with zeros.

**Fix sketch**: Read the reconstruction's actual aligned pose (or the capture's anchor pose) and pass it to `LocalizationMapCreate`. Or, if the contract is "fit-calibration maps have no real pose," make the API enforce that explicitly so the placeholder is rejected, not silently accepted.

**Verification**: After fix, the persisted map's `position_*` / `rotation_*` fields should match either the reconstruction's alignment or be rejected at the API layer.
