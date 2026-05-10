# Reconstructor `ReconstructionOptions` fields silently ignored

**Severity**: medium — caller-API contract gap; configuration looks effective but isn't.

**Location**: `docker/reconstructor/src/options_builder.py:72-73` (and adjacent).

**Symptom**: Three documented `ReconstructionOptions` fields round-trip through the API and manifest but the reconstructor worker never reads them: `single_threaded`, `bundle_adjustment_refine_additional_params`, and (effectively all of) `feature_matching_options`. Operators set them, see them in the manifest, and assume the pipeline honored them.

**Mechanism**:
- `single_threaded`: corresponding `num_threads = 1` lines are commented out in `options_builder.py:72-73`.
- `bundle_adjustment_refine_additional_params`: there is no `ba_refine_extra_params` assignment in the options builder; the field is read out of the request DTO and never plumbed.
- `feature_matching_options`: dead since LightGlue replaced COLMAP matching. The field is ingested but matching is now hard-coded.

**Fix sketch**: Pick per field. (1) Wire `single_threaded` through to a real `num_threads = 1` (or remove from the DTO and the manifest). (2) Plumb `bundle_adjustment_refine_additional_params` into the BA call (or remove). (3) Remove `feature_matching_options` from the DTO and update the manifest schema; do not silently accept fields the worker ignores. The "remove from DTO" path is preferred — caller-visible fields with no effect are worse than narrower DTOs.

**Verification**: Submit a reconstruction with each field set and observe pipeline behavior matches the request. Or, after the remove-path, assert the API rejects requests carrying the now-absent fields.
