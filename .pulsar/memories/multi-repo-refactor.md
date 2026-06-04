---
updated: 2026-06-02
---

# Multi-repo refactor: extract Capture Tool and LiveKit-only services out of placeframe

## Goal

Two coordinated extractions that share the same prep work.

1. **Capture Tool** (Unity `apps/AndroidMobile/` plus `docker/zed-capture/`) into a standalone repo `placeframe-capture-tool`. Today it lives inside placeframe as a workspace member and consumes generated C# clients via `file:` refs. Post-split, capture-tool consumes placeframe via versioned references (git URLs initially; packages later) rather than filesystem paths.

2. **LiveKit-only services** out of placeframe entirely, into Make-it-Sing. Placeframe is "relocalization as a service" — LiveKit is a multiplayer-XR concern that belongs in the consuming app's compose stack. The vehicle is Docker Compose `include:` — Make-it-Sing's `compose.yml` `include:`s placeframe's base compose and adds the LiveKit services on top. Placeframe's tree stops shipping LiveKit at all.

Make-it-Sing already exists as a separate repo (operational, already consumes placeframe via OpenUPM and git URLs); it is the proof of the consumer pattern for both extractions.

## State

- No code has moved. This is still planning.
- The capture-tool plan has been compressed from 6 stages to 3 (logging-package extraction dropped, cross-repo consumption defaults to git URLs — see Decisions).
- `Make-it-Sing/` exists as an untracked sibling checkout in the working tree (separate repo, operational).
- `response.md` and `name-propagation-plan.md` are untracked working notes from the planning session.

## In-repo prep work (no cross-repo coordination needed) — DO THIS FIRST

All of the work below can land in placeframe before any repo split. Each piece reduces the cross-repo blast radius later AND is independently valuable. Order: cleanup → compose LiveKit overlay → `build/` carve. (2) and (3) can run in parallel — they touch different files.

1. **Cleanup pass** (originally "Stage 1" of the capture-tool plan). Delete `legacy/`, delete `state-sync` (server), delete `packages/generated/csharp/zed-client/` (the OLD dead `placeframe-zed-client`, NOT the live `placeframe-zed-capture-client`). Remove matching entries from `build/src/build_scripts/placeframe/ci/publish_packages.py` and `create_release.py`. Audit for orphan compose entries. Pure grep-and-delete plus a `preflight` pass. Lowest risk; unblocks nothing but shrinks the surface for everything that follows.

2. **Peel LiveKit into its own compose overlay.** Today the `livekit` server, the `livekit-token` sidecar, and the `LIVEKIT_*` env vars live inline in `compose.yml` / `.env.sample`. Move them into `compose.livekit.yml` (precedent: `compose.cuda.yml`, `compose.rocm.yml`, `compose.postgres.yml`) plus a `.env.livekit.sample` (or analogous). Wire `up`/`down` to opt into the overlay via flag or profile, and confirm no non-LiveKit placeframe service has a `depends_on` edge into `livekit` or `livekit-token`. After this lands in placeframe, the eventual cross-repo move is mechanical: Make-it-Sing's compose copies the overlay file (or references it via `include:`), placeframe's tree drops it. Until then, the overlay still ships in placeframe — it's just cleanly bounded.

3. **Carve `build/` along the project-agnostic / placeframe-specific seam** (originally "Stage 2"). Inside `build/src/build_scripts/placeframe/`, separate the generic tooling (`compile-unity`, `generate-clients`, `generate-datamodels`, `lock-python`, `up`, `down`, `lock-unity`) from placeframe-specific CI glue (`preflight`, `publish-packages`, `create-release`, `ensure-release-pr`). Even before the split, the generic side becomes its own workspace package (proposed `placeframe-build`); the CI glue depends on it. The capture-tool repo later depends on the same package via git URL. Spec-first: the three boundary audits (`compile-unity` `Path.cwd()` assumptions, `generate-clients` project-list assumptions, `up`/`down` per-repo compose configurability) are all in-repo grep jobs and gate how clean Stage 2 actually is.

After (1)–(3), the remaining cross-repo work is just file moves against a much smaller, cleanly-bounded surface.

### Auxiliary in-repo audit: `livekit-token`'s coupling to placeframe

Before the LiveKit overlay can move to Make-it-Sing in earnest, we need to know what `docker/livekit-token/` actually consumes from placeframe. Two shapes:

- If it only signs JWTs with `LIVEKIT_API_SECRET` and validates identity statelessly (e.g. trusts a Keycloak bearer it can verify via JWKS, or accepts an anonymous-identity header in `AUTH_MODE=disabled`), it moves cleanly with the overlay — JWKS verification works the same from either repo.
- If it actually calls placeframe internals (DB, internal API), the boundary needs explicit redesign before the move.

This audit is an in-repo grep — surface the answer now so the overlay design in step (2) can reflect it.

## Cross-repo work (deferred — requires the other repos)

- **Extract capture-tool** (originally "Stage 3"). Move `docker/zed-capture/`, `apps/AndroidMobile/`, `packages/generated/csharp/zed-capture-client/`. New repo's uv workspace contains `docker/zed-capture/` and its locally-regenerated csharp client. Consumes placeframe artifacts (`placeframe-common`, `placeframe-core`, `org.nuget.placeframeapiclient`, `org.outernet.placeframe`, `org.outernet.logging`) via git URLs.
- **Relocate the LiveKit overlay to Make-it-Sing.** Make-it-Sing's compose either copies `compose.livekit.yml` outright or `include:`s a pinned placeframe checkout's base `compose.yml` and adds the LiveKit services on top. Placeframe's tree no longer contains LiveKit.

## Repo layout that falls out

- **placeframe** — server services (no LiveKit), MapRegistrationTool, Unity Placeframe packages (Core + ARFoundation), the API client (generated from `docker/api`). Python utilities (`common`, `core`) stay here.
- **placeframe-capture-tool** — `docker/zed-capture/` + `apps/AndroidMobile/` + a locally-regenerated `zed-capture-client`. Owns its own OpenAPI spec.
- **Make-it-Sing** — already a separate repo. Owns LiveKit services and the `livekit-token` sidecar. Consumes placeframe via `org.outernet.placeframe@1.0.5` (OpenUPM), `org.nuget.placeframeapiclient` via git URL, and `compose.yml` via `include:`.

## Coupling facts confirmed during planning

- CaptureTool's C# (`AppState.cs`, `AppUI.cs`, `CaptureRow.cs`, `ZedCaptureController.cs`) imports `PlaceframeApiClient.Model` / `PlaceframeApiClient.Client` directly — needs a direct dep on the api-client, not just the `org.outernet.placeframe` wrapper.
- CaptureTool consumes **zero** Python from placeframe. `common`/`core`/`datamodels`/api-client-py are server-side only.
- CaptureTool has **no** compile/config/install-time coupling to a placeframe deployment URL. `LoginUI.cs:38-44` accepts the API domain at runtime from `App.state.settings.domain`. `LogDrainController.cs:194-195` uses the same. The only hardcoded address (`http://zed-box` in `ZedCaptureController.cs:86`) is a Host header placeholder for the ZED hardware on LAN, unrelated to the placeframe API. So "how do capture-tool devs get a placeframe API" is a non-issue — they type in a domain.
- `placeframe-zed-client` (in `packages/generated/csharp/zed-client/`) is **dead code** — leftover from a renamed `docker/zed/` service that no longer exists. Not in `build/openapi-projects.json`, no consumers anywhere. Goes in step (1).
- `placeframe-zed-capture-client` (live, generated from `docker/zed-capture`) is consumed only by `apps/AndroidMobile/` via `file:` ref. After extraction both producer and consumer live in capture-tool's repo, so it stays a relative `file:` ref there. No publish needed.
- `publish_packages.py` already publishes `placeframe-api-client` to NuGet and `placeframe-core` / `placeframe-arfoundation` / `placeframe-magicleap` to OpenUPM with per-package git-tag detection, patch bumps, and dependency-cascade re-bumps. The "publish on tag" infrastructure already exists — Stage 4 of the older plan is unnecessary.
- LiveKit-side: no placeframe service consumes the `livekit` server. `livekit-token` is the only adjacent thing, and its coupling is the open audit above.

## Decisions

- **Punt on extracting Logging.** The `org.outernet.logging` Unity package stays inside placeframe; Make-it-Sing already consumes it via git URL and capture-tool will do the same. Don't add it to `PACKAGES` in `publish_packages.py`. Revisit only if an external consumer materializes.
- **Use git URLs everywhere for cross-repo consumption (stopgap).** Mirrors what Make-it-Sing already does, avoids building new publish infrastructure for Python packages, and works for both Unity (`?path=...` in `manifest.json`) and Python (`uv`'s `{ git = ..., subdirectory = ..., tag = ... }`). Migrate to proper PyPI/NuGet publish later when there's a third consumer or external need. The user has stated they intend to move to packages "sooner rather than later" but git URLs are the current target for this work.
- **Keep `common`/`core` in placeframe as workspace members.** Don't split into their own utility repo — capture-tool consumes them via git URL. Splitting source creates 6-repo lockstep-update hell for negative gain.
- **Spec-first on the build refactor.** The deepest unknown is how much hidden monorepo-shape is baked into `build/` entry points; that determines whether step (3) is a day or a week.
- **LiveKit is a Make-it-Sing concern, not a placeframe concern.** Placeframe's role is relocalization. LiveKit is the multiplayer transport for one app that happens to consume placeframe. Keeping it in placeframe's compose conflates platform with app concern; future placeframe consumers that don't need multiplayer XR (capture tool, MapRegistrationTool) shouldn't pull in a media server.
- **Use Docker Compose `include:` for the cross-repo compose composition.** Native compose feature (no external orchestration), matches the "consume placeframe via versioned references" theme of the rest of the plan.

## Open questions

- **The `build/` refactor boundary.** Three judgement calls inside `build/src/build_scripts/placeframe/`:
  - Does `compile-unity` already accept any project path (it reads `unity-projects.json`), or are there `Path.cwd() / "apps" / ...` style assumptions baked in?
  - Does `generate-clients` correctly handle a consumer-supplied `openapi-projects.json`, or does it bake in placeframe's project list anywhere?
  - Does `up`/`down` need per-repo compose-file configuration to be reusable, or does capture-tool just pass a different compose file in?
  - If 80%+ of the CI machinery is placeframe-specific, the "shared CI runner" abstraction isn't worth pursuing and we publish only the project-agnostic Unity/Docker tooling.
- **Why does Make-it-Sing prefer git URL for `org.nuget.placeframeapiclient` when it's actively published to NuGet?** Three possibilities: predates the publish step, the NuGet publish doesn't actually fire in CI, or Make-it-Sing intentionally wants HEAD tracking. Resolve before pointing capture-tool at NuGet for the same package — if there's a real reason, capture-tool should match.
- **Versioning policy for cross-repo consumption of placeframe artifacts.** Tag-pinned vs commit-pinned vs branch-tracking. Make-it-Sing currently uses a mix (some pinned to `1.0.5`, some pulling main with no ref). For capture-tool the default should be stricter than what Make-it-Sing does now. Applies equally to the eventual `compose.yml` `include:` target — the include reference needs a version policy too.
- **Does `livekit-token` actually need anything placeframe-specific?** If yes (e.g. validates a Keycloak-issued bearer before minting a LiveKit JWT), the boundary needs explicit design (JWKS publication, or anonymous-identity header replay) before moving the service. If no, the move is mechanical. See the in-repo audit above.
- **Does the gateway route `/livekit/*`?** If yes, that route belongs in Make-it-Sing's gateway (or Make-it-Sing runs its own gateway in front of placeframe's). If no (LiveKit signaling goes direct), the overlay move is trivial. In-repo grep against `docker/gateway/`.
- **What identifies "the placeframe compose" for Make-it-Sing's `include:`?** Git submodule of placeframe at a pinned ref, a small `placeframe-compose` published artifact, or an explicit checkout-path with a documented version pin. Same shape as the versioning question above.

## Key files

- `apps/AndroidMobile/Packages/manifest.json` — capture-tool's full external dep surface (5 packages).
- `build/src/build_scripts/placeframe/ci/publish_packages.py` — existing publish-on-tag pipeline; `PACKAGES` list defines what's already published. Has the `placeframe-zed-client` (dead) entry that step (1) deletes.
- `build/src/build_scripts/placeframe/ci/create_release.py` — companion to publish_packages; also references the dead zed-client.
- `build/src/build_scripts/placeframe/ci/CLAUDE.md` — the CI commit-free invariant (publish flow patches `package.json` ephemerally, never commits).
- `build/openapi-projects.json` — the config that drives `generate-clients`; confirms the live client set.
- `build/unity-projects.json` — config that drives `compile-unity`.
- `docker/zed-capture/` — the service that moves with capture-tool.
- `apps/AndroidMobile/` — the Unity app that moves with capture-tool.
- `packages/generated/csharp/zed-client/` — dead code; step (1) deletes.
- `packages/generated/csharp/zed-capture-client/` — live, moves with capture-tool.
- `apps/AndroidMobile/Assets/Scripts/Capture/LoginUI.cs` — proof capture-tool takes the placeframe domain at runtime, not compile time.
- `docker/livekit-token/` — the LiveKit-related service to peel into the overlay (and ultimately into Make-it-Sing).
- `compose.yml` — `livekit` and `livekit-token` service entries; the unit to split into `compose.livekit.yml` in step (2).
- `.env.sample` — `LIVEKIT_*` vars (LIVEKIT_API_KEY, LIVEKIT_API_SECRET, LIVEKIT_SIGNALING_DOMAIN/PORT, LIVEKIT_RTC_DOMAIN/PORT); move to the overlay's sample in step (2).
- `docker/gateway/entrypoint.sh` — check for `/livekit/*` route handling during the audit.
- `/placeframe/response.md` — accumulated planning notes for this work (untracked, may be relevant to revisit).
- `/placeframe/name-propagation-plan.md` — sibling planning artifact (untracked).
- `/placeframe/Make-it-Sing/` — sibling repo checkout used as the reference consumer pattern.
- `.pulsar/memories/livekit-phase-2-networking.md` — NOT superseded by this memory. That one is about media-plane transport (LAN IP advertisement, coturn overlay) and applies regardless of which repo owns the compose definition.

## Pending threads

- **Start with in-repo prep.** All three numbered pieces above are doable on a single feature branch in placeframe without touching Make-it-Sing or creating capture-tool's repo. Order: (1) cleanup pass, then (2) and (3) in parallel.
- **Run the `livekit-token` coupling audit** before designing the overlay split in step (2) — it determines whether the eventual cross-repo move is mechanical or requires boundary redesign.
- **Answer the `build/` refactor boundary questions** before doing step (3) (10-minute grep job per the original planning session).
- **Cross-repo work stays deferred.** Capture-tool extraction and the LiveKit overlay → Make-it-Sing move don't start until the in-repo prep is done.
- **Resolve the Make-it-Sing-bypasses-NuGet mystery and pick a versioning policy** stricter than Make-it-Sing's current mix — needed before either cross-repo move.
