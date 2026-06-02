---
updated: 2026-06-02
---

# Split Capture Tool out of placeframe into its own repo (`placeframe-capture-tool`)

## Goal

Extract the Capture Tool (Unity `apps/AndroidMobile/` plus the `docker/zed-capture/` service that backs it) into a standalone repo. Today it lives inside the placeframe monorepo as a workspace member and consumes the generated C# clients via `file:` refs. After the split, capture-tool should consume everything from placeframe via versioned references rather than filesystem paths, so that a third Unity app (Make-it-Sing already exists as that proof) can adopt the same pattern.

## State

- The plan has been compressed from a 6-stage to a 3-stage shape after two decisions (see Decisions): logging-package extraction is dropped, and cross-repo consumption defaults to git URLs.
- No code has moved. This is still planning.
- `Make-it-Sing/` exists as an untracked sibling checkout in the working tree (separate repo, already operational). It is a working reference for the "consume placeframe via published packages + git URLs" pattern.
- `response.md` and `name-propagation-plan.md` are untracked working notes that accumulated during the planning session.

### Three-stage plan

1. **Cleanup pass in placeframe.** Delete `legacy/`, delete `state-sync` (server), delete `packages/generated/csharp/zed-client/` (the *old* dead `placeframe-zed-client`, not to be confused with the live `placeframe-zed-capture-client`), and remove the matching entries from `build/src/build_scripts/placeframe/ci/publish_packages.py` and `create_release.py`. Audit for orphan compose entries.
2. **Refactor `build/`** — split project-agnostic tooling (`compile-unity`, `generate-clients`, `generate-datamodels`, `lock-python`, `up`, `down`, `lock-unity`) from placeframe-specific CI glue (`preflight`, `publish-packages`, `create-release`, `ensure-release-pr`). Package the general part (proposed name `placeframe-build`) so capture-tool's repo can depend on it.
3. **Extract capture-tool.** Move `docker/zed-capture/`, `apps/AndroidMobile/`, `packages/generated/csharp/zed-capture-client/`. New repo's uv workspace contains `docker/zed-capture/` and its locally-regenerated csharp client. Consumes placeframe artifacts (`placeframe-common`, `placeframe-core`, `org.nuget.placeframeapiclient`, `org.outernet.placeframe`, `org.outernet.logging`) via git URLs.

### Repo layout that falls out

- **placeframe** — server services, MapRegistrationTool, Unity Placeframe packages (Core + ARFoundation), the API client (generated from `docker/api`). Python utilities (`common`, `core`) stay here.
- **placeframe-capture-tool** — `docker/zed-capture/` + `apps/AndroidMobile/` + a locally-regenerated `zed-capture-client`. Owns its own OpenAPI spec.
- **Make-it-Sing** — already a separate repo, already consuming `org.outernet.placeframe@1.0.5` (OpenUPM) and `org.nuget.placeframeapiclient` via git URL.

### Coupling facts confirmed during planning

- CaptureTool's C# (`AppState.cs`, `AppUI.cs`, `CaptureRow.cs`, `ZedCaptureController.cs`) imports `PlaceframeApiClient.Model` / `PlaceframeApiClient.Client` directly — needs a direct dep on the api-client, not just the `org.outernet.placeframe` wrapper.
- CaptureTool consumes **zero** Python from placeframe. `common`/`core`/`datamodels`/api-client-py are server-side only.
- CaptureTool has **no** compile/config/install-time coupling to a placeframe deployment URL. `LoginUI.cs:38-44` accepts the API domain at runtime from `App.state.settings.domain`. `LogDrainController.cs:194-195` uses the same. The only hardcoded address (`http://zed-box` in `ZedCaptureController.cs:86`) is a Host header placeholder for the ZED hardware on LAN, unrelated to the placeframe API. So "how do capture-tool devs get a placeframe API" is a non-issue — they type in a domain.
- `placeframe-zed-client` (in `packages/generated/csharp/zed-client/`) is **dead code** — leftover from a renamed `docker/zed/` service that no longer exists. Not in `build/openapi-projects.json`, no consumers anywhere. Goes in Stage 1.
- `placeframe-zed-capture-client` (live, generated from `docker/zed-capture`) is consumed only by `apps/AndroidMobile/` via `file:` ref. After extraction both producer and consumer live in capture-tool's repo, so it stays a relative `file:` ref there. No publish needed.
- `publish_packages.py` already publishes `placeframe-api-client` to NuGet and `placeframe-core` / `placeframe-arfoundation` / `placeframe-magicleap` to OpenUPM with per-package git-tag detection, patch bumps, and dependency-cascade re-bumps. The "publish on tag" infrastructure already exists — Stage 4 of the older plan is unnecessary.

## Decisions

- **Punt on extracting Logging.** The `org.outernet.logging` Unity package stays inside placeframe; Make-it-Sing already consumes it via git URL and capture-tool will do the same. Don't add it to `PACKAGES` in `publish_packages.py`. Revisit only if an external consumer materializes.
- **Use git URLs everywhere for cross-repo consumption (stopgap).** Mirrors what Make-it-Sing already does, avoids building new publish infrastructure for Python packages, and works for both Unity (`?path=...` in `manifest.json`) and Python (`uv`'s `{ git = ..., subdirectory = ..., tag = ... }`). Migrate to proper PyPI/NuGet publish later when there's a third consumer or external need. The user has stated they intend to move to packages "sooner rather than later" but git URLs are the current target for this work.
- **Keep `common`/`core` in placeframe as workspace members.** Don't split into their own utility repo — capture-tool consumes them via git URL. Splitting source creates 6-repo lockstep-update hell for negative gain.
- **Spec-first on the build refactor.** The deepest unknown is how much hidden monorepo-shape is baked into `build/` entry points; that determines whether Stage 2 is a day or a week.

## Open questions

- **The `build/` refactor boundary.** Three judgement calls inside `build/src/build_scripts/placeframe/`:
  - Does `compile-unity` already accept any project path (it reads `unity-projects.json`), or are there `Path.cwd() / "apps" / ...` style assumptions baked in?
  - Does `generate-clients` correctly handle a consumer-supplied `openapi-projects.json`, or does it bake in placeframe's project list anywhere?
  - Does `up`/`down` need per-repo compose-file configuration to be reusable, or does capture-tool just pass a different compose file in?
  - If 80%+ of the CI machinery is placeframe-specific, the "shared CI runner" abstraction isn't worth pursuing and we publish only the project-agnostic Unity/Docker tooling.
- **Why does Make-it-Sing prefer git URL for `org.nuget.placeframeapiclient` when it's actively published to NuGet?** Three possibilities: predates the publish step, the NuGet publish doesn't actually fire in CI, or Make-it-Sing intentionally wants HEAD tracking. Resolve before pointing capture-tool at NuGet for the same package — if there's a real reason, capture-tool should match.
- **Versioning policy for capture-tool's consumption of placeframe artifacts.** Tag-pinned vs commit-pinned vs branch-tracking. Make-it-Sing currently uses a mix (some pinned to `1.0.5`, some pulling main with no ref). For capture-tool the default should be stricter than what Make-it-Sing does now.

## Key files

- `apps/AndroidMobile/Packages/manifest.json` — capture-tool's full external dep surface (5 packages).
- `build/src/build_scripts/placeframe/ci/publish_packages.py` — existing publish-on-tag pipeline; `PACKAGES` list defines what's already published. Has the `placeframe-zed-client` (dead) entry that Stage 1 deletes.
- `build/src/build_scripts/placeframe/ci/create_release.py` — companion to publish_packages; also references the dead zed-client.
- `build/src/build_scripts/placeframe/ci/CLAUDE.md` — the CI commit-free invariant (publish flow patches `package.json` ephemerally, never commits).
- `build/openapi-projects.json` — the config that drives `generate-clients`; confirms the live client set.
- `build/unity-projects.json` — config that drives `compile-unity`.
- `docker/zed-capture/` — the service that moves in Stage 3.
- `apps/AndroidMobile/` — the Unity app that moves in Stage 3.
- `packages/generated/csharp/zed-client/` — dead code; Stage 1 deletes.
- `packages/generated/csharp/zed-capture-client/` — live, moves with capture-tool in Stage 3.
- `apps/AndroidMobile/Assets/Scripts/Capture/LoginUI.cs` — proof capture-tool takes the placeframe domain at runtime, not compile time.
- `/placeframe/response.md` — accumulated planning notes for this work (untracked, may be relevant to revisit).
- `/placeframe/name-propagation-plan.md` — sibling planning artifact (untracked).
- `/placeframe/Make-it-Sing/` — sibling repo checkout used as the reference consumer pattern.

## Pending threads

- Resume on Stage 1 (cleanup pass) — it's the lowest-risk and unblocks nothing. Grep-and-delete plus a preflight pass.
- Before Stage 2, answer the build/ refactor boundary questions above (10-minute grep job per the planning session).
- Before Stage 3, resolve the Make-it-Sing-bypasses-NuGet mystery and pick a versioning policy stricter than Make-it-Sing's current mix.
