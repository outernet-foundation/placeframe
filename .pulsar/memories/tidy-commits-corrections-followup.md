---
updated: 2026-06-01
---

# Apply corrections to the misc-fixes tidy-commits result

## Goal

The `misc-fixes` branch was tidied from 124 commits down to 35 (HEAD `65613113`, before-tidy
`b9b45447` preserved on `misc-fixes-pretidy-safety`). The user reviewed the result and listed
specific corrections to apply. The session was interrupted (Claude over-reached on a comment-trim
pass and edited pre-existing-on-`dev` comments) and the working tree was reverted clean so the
corrections can be reapplied after `/clear` with the requested changes spelled out in this memory.

The user has also abandoned the 3-branch split: SPEC.md and miscellaneous-prose commits must be
**consolidated** (one of each per branch, not per section).

## State

- `misc-fixes` HEAD: `65613113` (35-commit tidy result).
- `misc-fixes-pretidy-safety`: `b9b45447` (pre-tidy HEAD; tree identical to `65613113`).
- `/placeframe/tidy-commits.json`: the current 35-commit tidy plan that produced HEAD.
- Working tree: clean. Untracked entries (`Make-it-Sing/`, `name-propagation-plan.md`,
  `response.md`) must be left alone.
- 20 numbered backup branches (`misc-fixes-backup-1`..`-20`) exist from prior tidy iterations.
  Leave them alone unless the user asks to clean up.

## Critical constraint: preserve pre-existing comments verbatim

Any comment or code that exists on `origin/dev` must be preserved unchanged. Only **new** content
added by this branch is eligible for trimming. Before editing a comment for verbosity, diff against
`origin/dev` to confirm it is new on this branch. The interrupting failure in the prior session was
trimming pre-existing comments — do not repeat it.

## Requested corrections (verbatim from user)

1. **`4d27ddc9` (Validate manifest and persist partial metrics)** — All rigs always have priors,
   so the `_validate_monocular_rigs_have_position_priors` check is no longer correct. Remove the
   function and its call site in `docker/api/src/routers/capture_sessions.py`. Squash into that
   commit (its final state must not include the validator).

2. **`ef0aae84` (Disambiguate queue labels on capture rows)** — two issues:
   - New verbose comments violate CLAUDE.md conventions (e.g. the AOA-bulk-endpoint multi-line
     block and the "Ordered list of captures waiting…" block in `CaptureController.cs`). Trim
     only NEW comments; leave any comment that exists on `origin/dev` alone.
   - The commit does a second thing: patching capture names through to API/ZED box
     (`OnCaptureNameChanged` rewrite, `PatchApiName`, `PatchBoxName`, and the name-display
     fallback in `UpdateCaptureList`). Split that into a **separate commit**.

3. **SPEC / prose consolidation (structural reorg)** — the 3-branch split is abandoned, so:
   - **One** SPEC.md commit at the **beginning** of the branch covering all SPEC changes.
     Drop the per-section SPEC commits currently at positions 2, 15, 26.
   - **One** miscellaneous-prose commit at the **end** covering everything non-CLAUDE.md
     non-SPEC.md (memories, notes, bug reports). Drop the per-section prose commits at positions
     14, 25, 35.
   - CLAUDE.md commit stays at position 1 (or wherever fits the new linear structure).

4. **`54978fe5` (currently titled "Speed up verify-geometry poll and fix zed recorded_at")** —
   commit message does not match the diff. The diff is entirely in
   `docker/zed-capture/src/routers/capture_sessions.py` and is about restructuring meta storage
   to include `recorded_at` from `frames.csv` (plus dropping the legacy migration path). No
   verify-geometry-poll content. Rewrite the message to reflect what the commit actually does.

5. **`28dbc4f3` (Drive priors-off and stereo-pin from rig structure)** — three issues:
   - The NEW comments in `options_builder.py` are too verbose; remove them.
   - The boolean constants in `options_builder.py`
     (`BUNDLE_ADJUSTMENT_INCREMENTAL_REFINE_SENSOR_FROM_RIG`,
     `BUNDLE_ADJUSTMENT_REFINE_FOCAL_LENGTH`, etc.) should be **inlined** at their call sites.
   - This commit owns `packages/python/core/src/core/image_preprocess.py`, which contains the
     `tile_image` removal — the actual tiling-drop core. That file belongs in commit 30
     (`8d5a6b7f` Unify image-retrieval similarity + drop tiling), not here. Move it.

6. **`75b4a841` (Rewrite reconstruction pipeline)** — two issues:
   - The NEW comments in `colmap.py` and `run_reconstruction.py` are too long and some may not
     be necessary. Trim only NEW comments; preserve `origin/dev`-existing comments verbatim.
   - **Commit message is wrong**: the hand-rolled two-stage geometric verification is no longer
     a thing — it got squashed away. Rewrite the message to reflect what actually survives in
     the final code, not what was tried-and-removed. Inspect the final state of
     `docker/reconstructor/src/reconstructor/colmap.py` and surrounding pipeline files to derive
     the accurate description.

7. **`3269d2c3` (currently titled "Update reconstructor pyproject deps add httpx, drop
   pybind11-stubgen")** — commit message is wrong (pybind11-stubgen was actually dropped in
   `e762080a` "Drop project pycolmap typings"). The commit also bundles unrelated things;
   redistribute and **drop the commit entirely**:
   - `httpx` addition to `docker/reconstructor/pyproject.toml` → fold into pipeline-rewrite
     commit (`75b4a841`); httpx is for the verify-poll child process.
   - `scripts/pyproject.toml` new diagnostic-script entries (displacement-check,
     sweep-postprocess, two-view-diagnostic) → fold into the diagnostic-scripts commit
     (`df773cca` / commit 33).
   - `scripts/src/scripts/tune_reconstruction.py` small change → fold into the diagnostic-scripts
     commit (or wherever the tune options were last touched).

## Decisions

- Reapply the corrections by rewriting `/placeframe/tidy-commits.json` and re-running
  `uv run --project /workspace tidy-commits-wrapper --base origin/dev`. The wrapper handles
  backup, invariance check, rollback.
- Codegen still lands once at the end (immediately before the consolidated prose commit), not
  per section — the section split is abandoned.
- `misc-fixes-pretidy-safety` (= `b9b45447`) remains the canonical pre-tidy reference. The new
  rewrite's final tree must match it (invariance check enforces this).
- Comment trimming: diff each target file against `origin/dev` before editing; only touch hunks
  this branch introduced.

## Key files

- `/placeframe/tidy-commits.json` — current 35-commit plan; rewrite this with consolidated
  SPEC/prose structure and the corrections above.
- `/workspace/.claude/skills/tidy-commits/SKILL.md` — wrapper invocation and JSON schema.
- `docker/api/src/routers/capture_sessions.py` — remove
  `_validate_monocular_rigs_have_position_priors` and its call site (correction 1).
- `apps/AndroidMobile/.../CaptureController.cs` — trim NEW verbose comments; split capture-name
  patching out (correction 2).
- `docker/zed-capture/src/routers/capture_sessions.py` — sole file in commit `54978fe5`; basis
  for rewriting its message (correction 4).
- `docker/reconstructor/src/reconstructor/options_builder.py` — remove new verbose comments and
  inline boolean constants (correction 5).
- `packages/python/core/src/core/image_preprocess.py` — move from commit 28 to commit 30
  (correction 5).
- `docker/reconstructor/src/reconstructor/colmap.py` — trim NEW comments; basis for rewriting
  the `75b4a841` commit message to reflect what survives (correction 6).
- `docker/reconstructor/src/reconstructor/run_reconstruction.py` — trim NEW comments
  (correction 6).
- `docker/reconstructor/pyproject.toml`, `scripts/pyproject.toml`,
  `scripts/src/scripts/tune_reconstruction.py` — redistribute the three pieces of `3269d2c3`
  into other commits and drop `3269d2c3` (correction 7).

## Pending threads

1. Inspect `docker/reconstructor/src/reconstructor/colmap.py` at HEAD to determine what
   geometric-verification shape actually survives there, so commit `75b4a841` can be given an
   accurate title and body. The current title ("hand-rolled two-phase geometric verification
   with rig pass") describes a tried-and-removed approach.
2. Rewrite `tidy-commits.json`:
   - Single SPEC commit at position 1 (or 2, behind CLAUDE.md) covering all three sections'
     SPEC changes.
   - Single prose commit at the very end covering all memories/notes/bugs.
   - Drop commit `3269d2c3`; redistribute its files into `75b4a841` and `df773cca`.
   - Move `image_preprocess.py` from commit 28 (`28dbc4f3`) to commit 30 (`8d5a6b7f`).
   - Apply correction 2's split (queue-label disambiguation vs. capture-name patching) as two
     separate commits.
3. After rewriting the plan, apply the in-place file edits (correction 1's validator removal,
   correction 2's comment trims, correction 5's comment removal + boolean inlining, correction 6's
   comment trims) — these require source edits the wrapper cannot derive from cherry-picks; use
   the `content` / `checkout_ref` mechanism or apply edits on top after the wrapper completes.
4. Rerun the wrapper, verify tree invariance against `misc-fixes-pretidy-safety`.
5. `/commit` the cleaned-up prose memory file once corrections are in.
