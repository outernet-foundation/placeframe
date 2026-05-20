# LiveKit swap — phase breakdown

This directory breaks the original `../livekit-plan.md` into seven sequential phases sized for Claude Code one-shot delivery. Each file is self-contained: hand it to a fresh Claude Code session along with `apps/MakeItSing/CLAUDE.md`, `apps/MakeItSing/SPEC.md`, and the top-level `CLAUDE.md`, and it should be executable end-to-end without referencing the sibling files.

See `../livekit-plan.md` for full design rationale (anti-vendor-lockin reasoning, architectural choices, risks table). The phase files here are the concrete work; the master plan is the "why."

## Phases

| # | File | Goal | Status |
|---|---|---|---|
| 1 | `01-compose-service.md` | LiveKit server in compose, env keys, digest pin. The minimum infra to run the Phase 3 spike. | ✅ Done (commit `cb3f866d`) |
| 2 | `02-ngrok-routing.md` | Route LiveKit signaling through Caddy + ngrok; confirm media plane reachability and pick a fallback (TCP tunnel / TURN / same-LAN) if needed. | 🔜 Next |
| 3 | `03-ml2-spike.md` | Validate the LiveKit Unity SDK loads and connects on Magic Leap 2 + Android Mobile. Throwaway smoke scene. | 🟡 Partial — SDK pinned (`f77afe40`), smoke scaffold landed (`89c5a42c`), Magic Leap compile + APK verified, device round-trip blocked on Phase 2 URL |
| 4 | `04-backend-api.md` | `POST /livekit/token` endpoint, settings, codegen. Picks up where Phase 1 left off. | Not started |
| 5 | `05-transport-abstraction.md` | `INetworkTransport` interface; move `PhotonConnectionManager` behind it as `PhotonTransport`; stub `LiveKitTransport`. Pure Unity refactor, zero behavior change. | Not started |
| 6 | `06-livekit-transport.md` | Real `LiveKitTransport`: SDK plumbing, slot-claim, master election, send/receive, unit tests. | Not started |
| 7 | `07-cutover.md` | Flip default, delete Photon, update SPECs. | Not started |

Phases 3 and 5–7 are durable (land on mainline). Phase 2's signaling/Caddy work is durable; any TURN/TCP-tunnel choice it makes is durable infra. Phase 3 is the only mostly-throwaway phase — the smoke scene and its build-config edits get deleted at the end; only the SDK pin survives.

## Dependency graph

```
1 ─→ 2 ─→ 3 ─→ 4 ─┐
              └─→ 5 ─→ 6 ─→ 7
```

- **Phase 2** unblocks the device side of Phase 3. Without an externally-reachable LiveKit URL the smoke spike can't actually round-trip a byte from the ML2.
- **Phase 3** strictly blocks everything downstream — if the SDK doesn't work on ML2, the whole approach is up for re-evaluation.
- **Phase 4** and **Phase 5** are independent of each other after Phase 3 passes. Different parts of the repo, no shared files. May run in either order or in parallel.
- **Phase 5** has no technical dependency on Phases 1–4 (the refactor only touches existing Photon code and adds a `LiveKitTransport` stub that throws), but pragmatically nobody does the refactor work until Phase 3 has confirmed the swap is viable.
- **Phase 6** needs Phase 4's generated C# client and Phase 5's `INetworkTransport` stub.
- **Phase 7** is gated on real-device validation of Phase 6's work — the user has to confirm before any Photon deletion happens.

## Decisions baked in along the way

A few things resolved during the planning process worth knowing:

- **Identity comes from Keycloak `sub`.** Phase 4's token endpoint derives LiveKit identity from the validated Keycloak claim, not from client input. This gives Phase 6's slot-claim layer stable identities to map to playerIds. Anonymous/guest paths are out of scope unless explicitly added.
- **`Participant.JoinedAt` is not public on the C# wrapper.** Phase 6's master election works around this by having each participant self-set a `joined_at_ms` attribute on connect. Identity lex order is the tiebreak. Local clocks need not be synchronized — only a stable total order matters.
- **Two send methods on the transport interface.** `Send` for single-packet (under ~12 KiB), `SendLargeAsync` for chunked streams. LiveKit handles chunking automatically at `CHUNK_SIZE = 15000` bytes.
- **`PhotonSerialization.cs` is transport-agnostic.** Don't rename it. It serializes the diff format; the transport carries the bytes. Renaming is a cosmetic concern out of scope here.
- **No voice/audio.** Data channels only. The `video` grant name in the JWT claim is canonical LiveKit even for data-only use; nothing extra needed.
- **External LiveKit goes through ngrok + Caddy, not LAN-direct.** The original plan deferred this with "LAN-only colocalized is fine"; the dev sandbox's network model meant LAN-direct wasn't actually available, so Phase 2 was inserted to make the ngrok path work properly. WebRTC media plane reachability is the open question that phase resolves.

## Open questions still pending

Carried over from `../livekit-plan.md`. None of these block Phases 1, 2, or 3.

1. Anonymous/guest LiveKit access ever needed for demos? (Affects Phase 4 identity sourcing.)
2. Voice/audio plumbing in this PR or follow-up? (Default: follow-up.)
3. `use_livekit` flag survives past Phase 7 or deleted immediately? (Default: delete in Phase 7.)
4. Target deployment for the initial 12-headset demo: same-LAN colocalized, or some participants remote? (Phase 2 makes the remote case viable; Phase 4 still uses the same token-mint endpoint regardless.)
