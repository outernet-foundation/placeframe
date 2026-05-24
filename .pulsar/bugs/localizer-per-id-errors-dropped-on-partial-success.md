# Localizer drops per-id error reasons on partial-success responses

**Severity**: low/medium — silent observability gap; caller cannot tell *why* a specific reconstruction failed unless *every* requested id failed.

**Location**: `docker/localizer/src/main.py:88-115`.

**Symptom**: When a multi-id `/localization` request has at least one successful reconstruction, the response is `list[Localization]` containing only successes; the per-id error strings collected in `errors` are silently discarded. The caller can count the response and infer that some ids failed, but has no way to recover which ids failed or why. Only when *every* id fails does the 422 detail surface the joined error strings.

**Mechanism**: The handler appends `LocalizationError` messages to a local `errors: list[str]` but only returns it (joined) in the 422 path. On any partial success, `errors` is dropped on the floor.

**Fix sketch**: Change the success response shape to include per-id errors — either `BaseModel { localizations: list[Localization], errors: dict[UUID, str] }`, or include a `LocalizationError` variant in the response list. The Localization response type and the API client both regenerate from the OpenAPI spec, so the API and Unity client pick up the new shape automatically after `generate-clients`.

**Verification**: Two-id request where one id has a fabricated `LocalizationError`; assert the success response includes the error message for the failing id.
