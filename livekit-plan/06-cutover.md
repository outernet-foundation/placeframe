# Phase 6 — Cutover and Photon teardown

## Context

Phases 1–5 added the LiveKit backend, the `INetworkTransport` abstraction with Photon behind it, and the real `LiveKitTransport` implementation. After Phase 5, the user has verified on real devices (Android Mobile + Magic Leap 2 + Editor) that `UnityEnv.use_livekit = true` produces equivalent behavior to the Photon path.

**This phase is gated on that device verification.** Do not start it until the user confirms the two-headset (or three-client) demo passed end-to-end on LiveKit. If they haven't confirmed, ask explicitly — don't assume.

After this phase:
- LiveKit is the default and only transport.
- Photon SDK, `PhotonTransport.cs`, and the `use_livekit` flag are deleted.
- SPEC.md, CLAUDE.md, and `docker/SPEC.md` reflect the new state.
- Master-handoff is documented as fixed.

Read `/placeframe/CLAUDE.md` and `/placeframe/apps/MakeItSing/CLAUDE.md` before starting. Especially the prose-and-code commit-separation rule (Markdown and source code never share a commit, even when changed in the same session) and the codegen commit message conventions.

## Pre-flight check

Before any edits, confirm with the user:

> Phase 5's on-device validation passed for all five scenarios (two-client basic, three-client late-join, master-disconnect recovery, network-blip recovery, all-three-platforms). Any failures have separate follow-up fixes merged, or are documented as known-acceptable. Confirm and I'll proceed.

If they confirm, proceed. If anything is outstanding, surface it and stop — don't delete Photon while LiveKit has open bugs that might force a rollback.

## Work

### 1. Flip the default

In `UnityEnv` (whatever file holds it; grep `use_livekit` to locate), change the default from `false` to `true`.

This is a one-line change. Keep the flag itself for now — it's deleted in §2 in the same source commit, but doing the flip first as a logical step keeps the commit readable. (You can squash if it improves clarity; the flip + delete can be one commit.)

### 2. Delete Photon

In the **same source-code commit** as §1 (or a closely-following one — both are pure code, no prose, can share a commit if size permits):

- Delete `apps/MakeItSing/Assets/ThirdParty/photon-unity-sdk_v5-1-9/` recursively. Make sure to delete the corresponding `.meta` files (including the folder's own `.meta`). Unity reacts badly to dangling `.meta` files; grep for any remaining references after the delete and clean them up.
- Delete `apps/MakeItSing/Assets/App/Networking/PhotonTransport.cs` (+ `.meta`).
- Delete the `use_livekit` flag from `UnityEnv` and the dispatch ternary in `AppSetup.cs`. Instantiate `LiveKitTransport` directly:
  ```csharp
  INetworkTransport transport = gameObject.AddComponent<LiveKitTransport>();
  ```
- Remove any `photon_project_id` reads from `apps/MakeItSing/Assets/App/SupabaseAPI.cs` (or wherever Supabase config is read). Whether to delete the corresponding row from the Supabase config table is an operational call — leave the row in place (dead but harmless) unless you can confirm with the user that they want it cleaned up. Note the orphaned config row in the PR description.
- If the `.csproj`-generated Unity project still references Photon assemblies via an `.asmdef` `references` list, remove those entries.

Sanity check:
```bash
grep -ri "photon\|realtime" apps/MakeItSing/Assets/App/
grep -ri "photon" apps/MakeItSing/Packages/
```
Both should be empty (modulo any deliberate residual references — there shouldn't be any).

**Do not rename `PhotonSerialization.cs`.** The codec is transport-agnostic but keeps its existing name. Renaming it is a separate cosmetic concern that requires GUID migration and isn't worth the diff noise here.

### 3. Compile + (optional) codegen

```bash
uv run compile-unity --project MakeItSing --build android-mobile
uv run compile-unity --project MakeItSing --build magicleap
```

Both must succeed. The Photon delete should not affect compilation if Phase 4's refactor was clean — there should be no straggling `Photon.Realtime` references.

It is unlikely the API client surface changed, but if it did (extremely unlikely — this phase is delete-only on the Unity side), regenerate:

```bash
uv run generate-clients --project docker/api
```

If this produces a diff, commit it separately with the message exactly `Run generate-clients`. If no diff, skip.

### 4. SPEC updates (separate commit)

In a **separate commit** from the code changes (prose-and-code separation rule):

#### `apps/MakeItSing/SPEC.md`

- Rewrite §Replicated scene-graph (or whichever section describes the networking model) to reference LiveKit data channels and `INetworkTransport` instead of Photon `OpRaiseEvent`. Match the SPEC-STYLE-GUIDE.md conventions (`/SPEC-STYLE-GUIDE.md`) — read that file first if you haven't recently. Keep the narrative durable; don't reference "the swap" or "the migration" — describe the current state.
- Update §Rationale: replace "Raw Photon Realtime over Fusion/PUN" (or equivalent existing reasoning) with the LiveKit decision and the `INetworkTransport` abstraction rationale.
- Update §Known Issues:
  - Remove or amend the entry about `OnMasterClientSwitched` only logging — the LiveKit master election in Phase 5 fixes this. Document it as resolved (or remove the entry entirely if the spec convention is to delete-when-fixed; check how other known-issue resolutions were handled historically with `git log -p apps/MakeItSing/SPEC.md | head -200`).
  - Leave the orphan-cleanup TODO (and any other still-unresolved issues) alone unless they're affected by this swap.

Cold-reader test: after the edits, the SPEC.md should read as if LiveKit had always been the transport — no temporal markers like "previously", "was Photon", "after the migration".

#### `apps/MakeItSing/CLAUDE.md`

- Update the "don't fix these" list. Specifically: any guidance that referenced Photon-specific behavior to leave alone (e.g. "don't fix the master-client switch") should be removed if that issue is now fixed.
- If the file points at networking implementation paths, update them to point at `Assets/App/Networking/LiveKitTransport.cs` instead of `Assets/App/Managers/PhotonConnectionManager.cs`.

#### `docker/SPEC.md`

- Add LiveKit to the service inventory. Include the role (data-channel SFU for MakeItSing), the ports (7880 signaling, 7881 RTC TCP, 50000–50100/udp media), the in-memory state model, and the no-Postgres/no-Redis note.
- Document the API token-mint endpoint (`POST /livekit/token`, identity from Keycloak `sub`).
- Document the colocalized-LAN deployment model and the (deferred) ngrok-UDP question.
- If Phase 1 or Phase 3 already added a LiveKit entry to `docker/SPEC.md`, **edit it** rather than duplicating. Check `git log -p docker/SPEC.md` for recent LiveKit additions.

### 5. Final commit hygiene check

Commit ordering for this phase:

1. **Code commit.** All deletions (Photon SDK, `PhotonTransport.cs`, `use_livekit` flag, dispatch ternary, `photon_project_id` reads) + the default-flip (which is implicit in deleting the flag). Single commit.
2. **(If generated) Codegen commit.** Message: exactly `Run generate-clients`. Skip if no diff.
3. **Prose commit.** All three of `apps/MakeItSing/SPEC.md`, `apps/MakeItSing/CLAUDE.md`, `docker/SPEC.md`. Single commit. Conventional commit-style message (e.g. `apps/MakeItSing: update spec and CLAUDE for LiveKit transport`).

No `Co-Authored-By` trailers on any commit. No `--no-verify`. If pre-commit hooks fail, fix the underlying issue and make a new commit — never `--amend` over a hook failure.

## Exit criteria

- `grep -ri "Photon\|Realtime" apps/MakeItSing/Assets/App/` returns nothing.
- `grep -ri "photon" apps/MakeItSing/Packages/` returns nothing.
- `apps/MakeItSing/Assets/ThirdParty/photon-unity-sdk_v5-1-9/` no longer exists.
- `UnityEnv.use_livekit` no longer exists.
- `uv run compile-unity --project MakeItSing --build android-mobile` passes.
- `uv run compile-unity --project MakeItSing --build magicleap` passes.
- `uv run --no-sync preflight` is green.
- `apps/MakeItSing/SPEC.md`, `apps/MakeItSing/CLAUDE.md`, and `docker/SPEC.md` reflect the post-swap state with no temporal markers.
- A real two-headset demo on LiveKit has been run end-to-end (this is the user's responsibility; confirm before merging).
- Code, codegen (if any), and prose are in separate commits.

## Out of scope

- Voice/audio plumbing.
- Multi-node LiveKit deployment.
- Anonymous/guest token paths.
- Photon-config-row cleanup in Supabase (operational, not code).
- Renaming `PhotonSerialization.cs`.
- Cleaning up the unrelated TODOs in `SPEC.md` "Known Issues" (e.g. orphan cleanup).
