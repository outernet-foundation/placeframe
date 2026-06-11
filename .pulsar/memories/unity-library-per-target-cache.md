---
updated: 2026-06-10
---

# Per-build-target Unity Library cache for placeframe-unity

## Goal

Avoid the slow Unity "Switch Platform" reimport that happens every time a
developer alternates between build targets for the same project. Today, building
e.g. MakeItSing's `android-mobile` slot, then `magicleap`, then back to
`android-mobile` forces Unity to reimport changed assets each switch — the
Library cache only holds artifacts for whichever target was built last. The
proposal is a gitignored per-target Library cache that `compile_unity` swaps in
before invoking Unity, so each target's reimport state survives across switches.

## Decisions

- Scope: a change to `placeframe-unity` (the Python toolkit), not to any Unity
  project. The swap is universal across every project `compile_unity` drives.
- Mechanism: rename-based swap (`os.rename` / `Path.rename`). Not symlinks
  (Unity has historically been fragile against them, and the indirection
  complicates Windows behavior). Not clones (defeats the speed goal).
- Slot layout: per-target slots live next to `Library/` as `Library.<target>/`
  (e.g. `Library.android-mobile/`, `Library.magicleap/`). Gitignore them.
- Sentinel: write `Library/.placeframe-last-build-target` at the end of every
  successful build. On the next build, read it to know which slot to rename the
  *current* `Library/` into before renaming the requested target's slot into
  `Library/`.
- Always-on, no flag. A single-target workflow just produces one slot and a
  no-op swap; rename is O(1) on the same filesystem so the overhead is
  negligible.
- Seam: insert the swap immediately before `prepare_unity_project(project_path)`
  in `compile_unity.build_unity_project`. That's the earliest point where the
  build target is known and `Library/` has not yet been touched by Unity.
- Disk cost is acceptable: one Library tree per cached target. Inodes only, no
  bandwidth. Renames are intra-filesystem so they're free.
- Failure mode is bounded: if the sentinel and the actual `Library/` contents
  disagree (e.g. crash mid-swap), Unity does a Switch Platform reimport — which
  is the current behavior. Degrades to status quo, never breaks.

## Open questions

- Trust the sentinel alone, or defensively cross-check `Library/PlayerDataCache/`
  contents to detect a desync and fall back to a clean reimport? Lean: trust
  the sentinel first; add the defensive check only after a real desync is
  observed.
- Should we also swap the BurstCache (`Library/Bee/...`)? Currently the whole
  `Library/` swaps as one unit, which is the simplest answer and probably
  correct.

## Key files

- `/placeframe/packages/python/placeframe-unity/src/placeframe_unity/compile_unity.py` —
  `build_unity_project` calls `prepare_unity_project(project_path)` at line 15;
  the swap goes immediately before that call.
- `/placeframe/packages/python/placeframe-unity/src/placeframe_unity/unity.py` —
  hosts `prepare_unity_project`, `PLATFORM_CONFIGS` (the valid `<target>` set:
  `android-mobile`, `magicleap`, `linux64`, `win64`), and is the natural home
  for a new helper like `swap_library_for_target(project_path, build)`.
- `/placeframe/packages/python/placeframe-unity/src/placeframe_unity/projects.py` —
  `UnityProject` / `load_unity_projects` give the project root path that anchors
  `Library/` and `Library.<target>/`.

## Pending threads

- Awaiting user go-ahead to implement. The last assistant turn before this memory
  was "Want me to implement it?" — no green light yet.
- When implementing: add `Library.*/` to each Unity project's `.gitignore` (or
  add a single rule to placeframe's top-level `.gitignore` if it already covers
  `Library/`).
- When implementing: write a unit/integration test that exercises the
  rename-swap path with two synthetic targets to lock the sentinel logic.
- After implementation, callers in `make-it-sing` and `apps/CaptureTool` need
  nothing — they pick up the behavior by bumping placeframe's pinned SHA.

## Related prior work in this session

This came up while debugging a separate placeframe-unity bug: `snapshot_artifacts`
in `compile_unity.py` was non-recursive (`iterdir()`), so it missed MakeItSing's
`Build/AndroidMobile/OgmentUnity.apk` and emitted a misleading "stale incremental
build" error even when Unity reported success. Fixed in this session by switching
to `rglob`. That fix is in flight or already committed; the per-target Library
cache work is independent.
