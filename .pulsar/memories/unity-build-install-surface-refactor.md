---
updated: 2026-05-22
---

# Unity build/install command surface: `install --build` flag and follow-up cleanups

## Goal

Eliminate the trap that caused `READ_LOGS` (and other `grant_permissions` entries in `build/unity-projects.json`) to be silently skipped when an assistant followed root `CLAUDE.md` note #10 — which documents `uv run compile-unity --project <p> --build <target>` + manual `adb install -r` as the default "build and install" path. That path bypasses `scripts/install.py`'s post-install permission-grant step entirely. The user reproduced the consequence: an OkHttpH2 frame trace that should have shipped to Loki via `LogcatRelay` was missing because `READ_LOGS` was never granted on the manually-installed APK.

The fix is to make a single command — `uv run install` — cover both the "pull latest CI artifact" path and the "build from current working tree" path, so the post-install grant step is always reached.

## State

- Diagnosis confirmed: `uv run install --project CaptureTool` already exists at `scripts/src/scripts/install.py:80-141`. `build/unity-projects.json:36` still lists `"grant_permissions": ["android.permission.READ_LOGS"]`. Nothing was lost in a rebase — the trap is purely the root `CLAUDE.md` guidance pointing at the wrong default.
- Confirmed `uv run install --project CaptureTool` downloads the **latest successful CI artifact for the current branch**; it does not build locally. So a local-changes workflow currently requires `compile-unity` + `adb install -r` + manual `pm grant`, which is exactly the trap.
- Discussion produced a tiered plan (below). User approved exploring this and asked for an opinion before any code change. No code change has been made on this thread for the refactor itself.

## Decisions

- **Add `--build` to `uv run install`.** When set, `install` invokes the `compile-unity` build path locally, then funnels the produced APK into the existing `adb install` + `grant_permissions` code path at `scripts/install.py:120-141`. Single command, single set of post-install steps, trap closed.
- **No new "install cache" concept.** The current install cache is GitHub Actions artifacts keyed by branch+target. A "compile-unity populates the install cache" side channel would add stateful complexity for no real win — `install --build` calling into `compile-unity`'s build output directly is cleaner.
- **Do not rename `install`.** It is broad enough to cover both CI-pull and local-build modes.
- **Do not touch `build-unity`.** That is the CI entry point and is a separate concern.

## Open questions

- None blocking the minimal fix. The user has not yet picked between "ship just `--build`" and "ship `--build` plus the surface-area cleanup as separate follow-up commits." Default assumption: ship `--build` first as a focused commit, then file follow-ups for items in **Pending threads**.

## Key files

- `/placeframe/scripts/src/scripts/install.py` — current install pipeline; line 80-141 is the install + grant_permissions block that `--build` must funnel into.
- `/placeframe/build/src/build_scripts/placeframe/compile_unity.py` — the build path `install --build` will invoke.
- `/placeframe/build/unity-projects.json` — per-project metadata including `grant_permissions`. `CaptureTool` at line 36 lists `READ_LOGS`.
- `/placeframe/CLAUDE.md` — root environment note #10 currently steers toward the trap path. Needs updating in lockstep with the code change (separate prose commit per repo convention: prose and code never share a commit).
- `/placeframe/apps/AndroidMobile/CLAUDE.md` — "Build + install on the host-attached phone" snippet around line 11-14 also documents the trap path; smaller edit, same direction. Line 34 already mentions `uv run install`; the two halves currently contradict each other.
- `/placeframe/apps/AndroidMobile/SPEC.md` — verify whether it mirrors the same guidance and needs the same update.

## Pending threads

1. **Implement `uv run install --build`** (single focused commit on code, plus a separate prose commit updating root + AndroidMobile `CLAUDE.md`).
2. **Follow-up: unify flag names.** `compile-unity --build <target>` and `install --target <target>` mean the same thing. After `install --build` lands (as a boolean flag), `compile-unity`'s `--build` becomes immediately confusing. Rename `compile-unity --build` to `--target` for consistency. Separate commit.
3. **Follow-up: make `--project` positional.** `uv run install CaptureTool` reads better than `uv run install --project CaptureTool`. Project name is the dominant argument; everything else is a modifier. Apply to both `install` and `compile-unity`. Separate commit.
4. **Follow-up: consider whether `compile-unity` should be a hidden helper.** Once `install --build` exists, the only remaining standalone use for `compile-unity` is the "did this `.cs` change compile?" sanity check. Either keep it (and possibly rename for clarity, e.g. `unity-typecheck`) or fold it into `install --build --no-install`. Low urgency.
5. **Explicitly skipped: a multi-tier install cache.** Mentioned only to record that it was considered and rejected.
