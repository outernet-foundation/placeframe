# `apply_global_calibration` hard-codes `confidence_is_calibrated=True`

**Severity**: low — dead optionality in the response contract. No present consumer can distinguish calibrated from uncalibrated output.

**Location**: `packages/python/core/src/core/calibration.py:158-161` — the third tuple element returned by `apply_global_calibration` is the literal `True`. Consumer at `docker/localizer/src/build_metrics.py:81,99` forwards it into `LocalizationMetrics.confidence_is_calibrated`.

**Symptom**: `LocalizationMetrics.confidence_is_calibrated` is always `True` for any code path that goes through `apply_global_calibration`. Clients that branch on this flag (treating it as "trust the confidence numbers") get no signal — including for the placeholder-calibration path, which prints a stderr warning that values are not trustworthy yet still returns `confidence_is_calibrated=True`.

**Mechanism**: When the placeholder calibration was introduced (commit `06bff440 Drop client confidence gate and seed sigma_meas placeholders`), the optionality was preserved in the return shape but the runtime distinction was dropped. Nothing now sets the flag to `False`.

**Fix sketch**: Two options. (a) Remove the dead boolean: change the return to `tuple[float, float]` and drop `confidence_is_calibrated` from `LocalizationMetrics`, the OpenAPI schema, and generated clients. (b) Actually populate it: have `apply_global_calibration` accept the `CalibrationArtifact` it already has and return `pipeline_version != PLACEHOLDER_PIPELINE_VERSION` as the third element. (a) is the more honest fix — the flag has never been false, so removing it loses no information and prunes the schema. Either way, regenerate clients.

**Verification**: After (a): grep confirms zero references to `confidence_is_calibrated`. After (b): load a placeholder calibration, call `apply_global_calibration`, assert third element is `False`; load a real calibration, assert `True`.
