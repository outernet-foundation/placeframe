# Reconstructor discards extra COLMAP models without surfacing to metrics

**Severity**: low — operators can't tell when a reconstruction split into multiple disconnected components; the largest is silently kept.

**Location**: `docker/reconstructor/src/reconstructor/colmap.py:153` and surrounding `incremental_mapping` result handling (carries a `# TODO: Write information to metrics about this for visibility`).

**Symptom**: When `incremental_mapping` returns multiple reconstructions (the scene split into disconnected components), the worker picks the largest and discards the rest. The API and operators never learn this happened. Diagnosing "why did only half the captured area register?" requires re-running with logging hooks.

**Mechanism**: The discard is inline; only the chosen model's stats flow into `ReconstructionMetrics`. There is no field for "number of models returned" or "discarded model image counts".

**Fix sketch**: Add `additional_models: list[ModelSummary]` (image count, point count) to `ReconstructionMetrics`. Populate at the discard site. Surface in the API response so the capture UI can flag multi-model outcomes.

**Verification**: Construct a deliberately split capture; assert the metrics record both models and the API exposes the discarded one's stats.
