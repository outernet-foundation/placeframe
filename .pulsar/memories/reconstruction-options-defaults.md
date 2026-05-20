---
updated: 2026-05-20
---

# Eliminate hardcoded ReconstructionOptions defaults in the capture-tool client

## Goal

`ReconstructionOptionsPersistence.BuildDefaults()` in the AndroidMobile capture tool hardcodes the same defaults the server already declares in its OpenAPI spec. The duplication has rotted before (defaults drifted on the server while the phone kept stale values) and just caused a silent failure that masked a stale-cache bug. Delete the duplication by making the C# DTO's parameterless constructor initialize each field to the OpenAPI `default:` value, so `new ReconstructionOptions()` is itself the defaults. The user picked "option 3" — a codegen template patch — over the other two options on the table.

## State

- `apps/AndroidMobile/Assets/Scripts/Capture/ReconstructionOptionsPersistence.cs` exists on disk (untracked); it loads/saves a phone-side JSON cache by reflecting over `[DataMember]` properties and diffing against `BuildDefaults()`. The persistence layer itself stays — only the `BuildDefaults()` body becomes redundant once codegen handles defaults.
- Verified every value in current `BuildDefaults()` exactly matches the corresponding `default:` in `docker/api/openapi.json` (lines ~6200-6260). No semantic change for the user when the hardcoded list goes away — only deduplication.
- The Python generated client already emits `= Field(default=30.0, ...)` style initializers from OpenAPI defaults. The C# template does not. That asymmetry is the gap option 3 closes.
- Existing C# template patches live at `build/openapi-generator/templates-patches/csharp/000{1..6}-*.patch`. A new patch (e.g. `0007-csharp-model-default-initializers.patch`) is the right shape.
- Work is paused: user asked to memorize this before diverting to investigate a separate `AutomaticUI.cs` NRE that turned out to live on this branch (see Open questions).

## Decisions

- **Option 3 wins (codegen patch).** Rejected option 1 (drop defaults; dialog shows zeros) — bad UX. Rejected option 2 (fetch defaults from a new API endpoint on dialog open) — adds a round-trip and a new endpoint when the spec already carries the data statically.
- The fix is a template patch under `build/openapi-generator/templates-patches/csharp/`, not a post-codegen sed step and not a hand-edit of generated files (those regenerate every `generate-clients` run).
- Persistence's reflection-based override-diff approach (`Load`/`Save` in `ReconstructionOptionsPersistence.cs`) stays. Only the `BuildDefaults()` body — and ideally the method itself — is targeted for deletion once `new ReconstructionOptions()` carries the right defaults.

## Open questions

- Which C# template controls the model's parameterless constructor / field initializers — `modelGeneric.mustache` or one of the partials? Need to locate the right insertion point before drafting the patch.
- Does `openapi-generator` already expose the `default:` value on the model's vendor extensions / property context inside the template, or does the patch also need a `--additional-properties` plumb-through?
- Behavior for nullable vs non-nullable C# properties: if the OpenAPI default is `null` or absent, does the initializer become `= default` or get omitted entirely? Confirm against the Python client's pattern.
- Once `new ReconstructionOptions()` carries defaults, can `BuildDefaults()` be deleted outright and `Save()`'s diff target switch to `new ReconstructionOptions()`? Should not require any other changes, but verify.

## Key files

- `apps/AndroidMobile/Assets/Scripts/Capture/ReconstructionOptionsPersistence.cs` — `BuildDefaults()` is the duplication to delete; `Load`/`Save` are reflection-based and stay.
- `apps/AndroidMobile/Assets/Scripts/Capture/CaptureRow.cs` — call site for `ReconstructionOptionsPersistence.{Load,Save}`.
- `docker/api/openapi.json` (~lines 6200-6260) — authoritative `default:` values for `ReconstructionOptions`.
- `build/openapi-generator/templates-patches/csharp/` — existing patches numbered 0001-0006; add the new patch here.
- `packages/generated/csharp/api-client/src/PlaceframeApiClient/Model/ReconstructionOptions.cs` — current generated DTO; inspect to see what the constructor looks like today.
- `scripts/src/scripts/generate_clients.py` (or similar) — pipeline that applies these patches; sanity-check the patch lands.

## Pending threads

- After the `AutomaticUI.cs` NRE investigation (separate from this memory, but blocking before any capture-tool deploy is verified), resume here:
  1. Locate the relevant C# mustache template and where defaults appear in its context.
  2. Author `0007-csharp-model-default-initializers.patch`.
  3. Run `uv run generate-clients --project docker/api` and verify `ReconstructionOptions.cs` constructor now initializes the nine fields to their OpenAPI defaults.
  4. Delete `BuildDefaults()` from `ReconstructionOptionsPersistence.cs`; update `Load`/`Save` to use `new ReconstructionOptions()` as the defaults baseline.
  5. Codegen output goes in its own commit with message `Run generate-clients`; source change is a separate commit.
