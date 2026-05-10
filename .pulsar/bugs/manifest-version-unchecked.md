# `Manifest.model_validate` ignores `MANIFEST_VERSION`

**Severity**: medium — silent contract change on every manifest schema bump.

**Location**: `packages/python/core/src/core/...` — `Manifest` Pydantic model and `MANIFEST_VERSION` constant. Readers in `docker/api/routers/{leases,reconstructions}.py` parse manifests blindly.

**Symptom**: Bumping `MANIFEST_VERSION` (because a field was added, removed, or semantically reinterpreted) causes no failure on read. Old manifests in MinIO continue to validate as if they were the new version, and any reader that assumes the new semantics applies them to old data — or vice versa.

**Mechanism**: `Manifest.model_validate` accepts the JSON without checking a `version` field against `MANIFEST_VERSION`. Compare with `load_global_calibration`, which loudly enforces both `schema_version` and `pipeline_version`. The asymmetry is real and asymmetric: calibration is paranoid, manifest is naive.

**Fix sketch**: Add a required `version: int` field to `Manifest` and a `model_validator(mode="after")` that compares against `MANIFEST_VERSION`. Decide on read-side migration policy (reject? auto-migrate? forward-only?) and codify it. The minimal fix is the version check itself.

**Verification**: Write a manifest with `version: MANIFEST_VERSION - 1` and assert `Manifest.model_validate(...)` raises. Write one with `MANIFEST_VERSION` and assert it passes.
