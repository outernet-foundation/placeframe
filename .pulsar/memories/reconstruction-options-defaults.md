---
updated: 2026-05-20
---

# Make the C# `ReconstructionOptions` DTO self-describing for defaults, and fix the dialog NRE it exposed

## Goal

The capture-tool's Reconstruction Options dialog needs to (a) display real defaults for every field without duplicating them in client code, and (b) only send fields to the API that the user actually overrode. The shape the user wants, in their words: "the client knows what the defaults are for each field, so those can be displayed in the UI, but only bother passing values to the API if they actually differ from the defaults."

Half of this already exists in the generated `ReconstructionOptions.cs`: every property uses the `_flag<Name>` + `ShouldSerialize<Name>()` pattern, so Newtonsoft already omits anything the user hasn't assigned. The missing half is the *value*: the backing field is left at `default(T)` instead of the OpenAPI `default:` value, so the dialog shows 0/false instead of the real defaults. Tyler's `ReconstructionOptionsPersistence.cs` `BuildDefaults()` is a workaround that hardcodes the same numbers the server already declares.

Side effect of the same change: the dialog now NREs on open. Fixing that is part of this work, not a separate ticket — both fixes ship together.

## State

- `apps/AndroidMobile/Assets/Scripts/Capture/ReconstructionOptionsPersistence.cs` exists on disk (untracked). It loads/saves a phone-side JSON cache by reflecting over `[DataMember]` properties and diffing against `BuildDefaults()`. Once codegen emits real defaults, this whole persistence layer can collapse to plain `JsonConvert.SerializeObject(updated)` — Newtonsoft + `ShouldSerialize` already does the override-only behavior.
- Verified every value in current `BuildDefaults()` exactly matches the corresponding `default:` in `docker/api/openapi.json` (lines ~6200-6260). No semantic change for the user when the hardcoded list goes away — only deduplication.
- The Python generated client already emits `= Field(default=30.0, …)` from OpenAPI defaults. The C# template does not. That asymmetry is the gap to close.
- Existing C# template patches: `build/openapi-generator/templates-patches/csharp/000{1..6}-*.patch`. **`0002-csharp-models-required-only-constructors.patch` already patches `modelGeneric.mustache`** — the same mustache that drives the property/backing-field block. **Strong candidate: extend `0002` rather than add a new `0007`.** User explicitly asked us to consider that.
- Dialog blank-screen / NRE root cause **understood**: `AutomaticUI.cs:288`, in the non-nullable branch of `PrimitiveInspector`, passes `type = nullableUnderlyingType` into `PrimitiveControl`. `nullableUnderlyingType` is guaranteed `null` in that branch (immediately after `if (nullableUnderlyingType != null) { …; return; }`). `PrimitiveControl` then NREs at `props.type.IsEnum` on line 317. One-line fix: change line 288 to `type = type`.
- Why it stayed dormant for months and bit now: commit `4501bda3` ("Tune BA defaults, collapse deterministic_seed…") rewrote `packages/python/core/src/core/reconstruction_options.py` from `Optional[T] = None` to `T = <default>` for ~16 fields. OpenAPI lost `nullable: true`. The next `Run generate-clients` (`110c34f8`) emitted **non-nullable** C# types (`double` instead of `double?`), which routes through the buggy non-nullable branch instead of the working nullable branch. Before, every field was nullable → nullable branch → fine.
- Tyler has been opening this dialog successfully "for months"; the working path was the nullable branch, not because `AutomaticUI.cs:288` was ever correct.

## Decisions

- **Fix both the codegen template and `AutomaticUI.cs`.** The "no AutomaticUI changes" constraint Tyler floated can't coexist with non-nullable defaulted fields — the schema design wants concrete defaults, not nullables; the dialog needs to render those. One or the other has to give, and the right answer is "fix the latent bug in `AutomaticUI.cs` *and* make the DTO self-describing."
- **Codegen approach: backing-field initializer keyed off the OpenAPI `default:` value.** Result shape:
  ```cs
  private double _RotationThreshold = 30.0;   // schema-declared default
  private bool _flagRotationThreshold;        // still false until user assigns
  public double RotationThreshold { get { …; } set { …; _flagRotationThreshold = true; } }
  public bool ShouldSerializeRotationThreshold() => _flagRotationThreshold;
  ```
  `new ReconstructionOptions()` becomes the dialog's defaults baseline. `ShouldSerialize` omits any field the user didn't touch. Save collapses to a plain `JsonConvert.SerializeObject(updated)`. `BuildDefaults()` deletes. The diff-against-defaults loop in `ReconstructionOptionsPersistence.cs` deletes.
- **Prefer extending `0002-csharp-models-required-only-constructors.patch` over adding a new `0007-*.patch`.** Both edits touch the same `modelGeneric.mustache`. A new patch on top would be a second hunk in the same file; folding into `0002` keeps the property/constructor-shape changes in one logical patch. Open question is whether the diff is clean to merge or whether the layering is easier to review as a separate file — assess when writing the patch.
- **Rejected: option 1 (revert Pydantic to `Optional[T] = <default>`).** Weakens the API contract for every consumer just to satisfy the capture-tool dialog. Server-side behavior is equivalent (`model.field` is never `None` because of the default), but consumers reading the spec see "nullable with default" instead of "concrete value, always present" — that's a real downgrade.
- **Rejected: option 2 (new `/reconstructions/options/defaults` endpoint).** Adds a round-trip and a new endpoint when the spec already carries the data statically.
- **Rejected: original option 1 from earlier in the thread (drop defaults; dialog shows zeros).** Bad UX.
- **Rejected: C# template patch that wraps non-nullable value types as `T?`.** Avoids the `AutomaticUI.cs` fix but weakens the type story — the defaults are real values, not "absent."

## Open questions

- **`0007` vs. extend `0002`?** Read `0002-csharp-models-required-only-constructors.patch` and see what part of `modelGeneric.mustache` it touches. If the property-block region is already in `0002`, extend it. If `0002` is constructor-only and the property block is untouched, a new `0007` may read more cleanly. Either is acceptable; user wants the question considered, not pre-answered.
- **Where in `modelGeneric.mustache` does the per-property backing field appear, and what context variables expose the OpenAPI `default:`?** The mustache likely has `{{defaultValue}}` available per-property; confirm. Also confirm how it formats per-type (string quoting, `null` literal, enum names).
- **Nullable/absent default handling.** If a field has no OpenAPI `default:`, the initializer should be omitted (keep `default(T)`), not emit `= null` for a non-nullable type. Mustache-side: a `{{#defaultValue}}…{{/defaultValue}}` guard.
- **`deterministic_seed` is genuinely nullable** (`"nullable": true` retained in 4501bda3 for that one field) — confirm the patch handles `int?` defaults sensibly (likely no initializer needed; `default(int?)` is `null` which equals the OpenAPI default).
- After the template patch lands and `BuildDefaults()` is deleted, can `ReconstructionOptionsPersistence.cs` be deleted entirely (Save → `JsonConvert.SerializeObject`, Load → `JsonConvert.DeserializeObject` with try/catch fallback to `new ReconstructionOptions()`)? Probably yes; verify against current call sites in `CaptureRow.cs`.

## Key files

- `apps/AndroidMobile/Assets/Scripts/Capture/ReconstructionOptionsPersistence.cs` — untracked; `BuildDefaults()` is the duplication to delete. The whole file likely deletes once codegen carries defaults.
- `apps/AndroidMobile/Assets/Scripts/Capture/CaptureRow.cs` — call site for `ReconstructionOptionsPersistence.{Load,Save}`. Restore inline JsonConvert calls (or simpler) once persistence collapses.
- `apps/AndroidMobile/Assets/AutomaticUI.cs:288` — latent NRE. Change `type = nullableUnderlyingType` to `type = type`. Surrounding context: line 203 `PrimitiveInspector`, line 205 `Nullable.GetUnderlyingType`, line 206 `if (nullableUnderlyingType != null) { …; return; }`, line 272-295 non-nullable branch, line 315-317 `PrimitiveControl` dereferences `props.type.IsEnum`.
- `docker/api/openapi.json` (~lines 6200-6260) — authoritative `default:` values for `ReconstructionOptions`. Use as the verification target after running codegen.
- `build/openapi-generator/templates-patches/csharp/0002-csharp-models-required-only-constructors.patch` — read first to decide whether to extend or add `0007`.
- `build/openapi-generator/templates-generated/csharp/modelGeneric.mustache` — mustache template that emits the C# property + backing field + `ShouldSerialize` trio. The patch target.
- `packages/generated/csharp/api-client/src/PlaceframeApiClient/Model/ReconstructionOptions.cs` — current generated DTO; inspect to see the existing flag-and-`ShouldSerialize` shape and confirm what changes after codegen reruns.
- `packages/python/core/src/core/reconstruction_options.py` — source schema; the commit `4501bda3` that flipped `Optional[T] = None` → `T = <default>` lives here. Do not revert.
- `scripts/src/scripts/generate_clients.py` — pipeline that applies these patches. Sanity-check the patch lands during reruns.

## Pending threads

Resume order from a fresh session:

1. Read `0002-csharp-models-required-only-constructors.patch` and the surrounding `modelGeneric.mustache` to decide: extend `0002` vs. add `0007-csharp-model-default-initializers.patch`. Either is acceptable; user wants the question explicitly considered.
2. Author the patch. The mustache change initializes each non-nullable value-type backing field to its OpenAPI `default:` value when one is declared. Omit initializer for fields without a `default:`. Handle nullable types sensibly (likely no initializer).
3. Apply the one-line `AutomaticUI.cs:288` fix (`type = type`). This is a separate concern from the codegen patch but ships in the same conceptual change — both gate the dialog rendering correctly.
4. Run `uv run generate-clients --project docker/api` and verify `ReconstructionOptions.cs` now emits `private double _RotationThreshold = 30.0;`-style initializers for the nine fields with OpenAPI defaults.
5. Delete `BuildDefaults()` from `ReconstructionOptionsPersistence.cs`. Then decide: collapse the whole file to direct `JsonConvert` calls in `CaptureRow.cs`, or keep `Load`/`Save` as thin wrappers if there's a future-proofing reason. Lean toward full collapse.
6. Build & deploy: `uv run compile-unity --project CaptureTool --build android-mobile`, then `adb install -r apps/AndroidMobile/Build/Capture_Tool.apk`. Verify the dialog opens (no NRE) and shows real default values (30.0 etc., not 0).
7. Verify Loki for new NREs after the rebuild lands.
8. Commit hygiene: source-code change(s) and the codegen output go in separate commits per `CLAUDE.md`. The codegen commit's message must be exactly `Run generate-clients`. Prose commits separate from code commits per `CLAUDE.md` as well — but this work is code-only; the memory file itself is the only prose, and goes in its own commit (this `/memorize` commit).

## Context for the cold reader

This memory updates an earlier version that scoped the work to "delete the hardcoded `BuildDefaults` duplication via a codegen patch." That framing is preserved, but the scope has widened: the same root cause (commit `4501bda3` collapsing nullable fields to concrete-defaulted fields) also surfaced a latent NRE in `AutomaticUI.cs:288` that has to be fixed in the same change, because the codegen patch makes the dialog *finally render* — and rendering hits the latent bug.

The user has said both fixes are part of one change. A fresh session should plan both — pick the patch placement (extend `0002` vs. new `0007`), author the patch, apply the one-line `AutomaticUI.cs` fix, regenerate clients, delete `BuildDefaults`, redeploy, verify.
