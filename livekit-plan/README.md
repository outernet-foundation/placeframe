# LiveKit swap — phase breakdown

This directory breaks the original `../livekit-plan.md` into six sequential phases sized for Claude Code one-shot delivery. Each file is self-contained: hand it to a fresh Claude Code session along with `apps/MakeItSing/CLAUDE.md`, `apps/MakeItSing/SPEC.md`, and the top-level `CLAUDE.md`, and it should be executable end-to-end without referencing the sibling files.

See `../livekit-plan.md` for full design rationale (anti-vendor-lockin reasoning, architectural choices, risks table). The phase files here are the concrete work; the master plan is the "why."

## Phases

| # | File | Goal | Throwaway? |
|---|---|---|---|
| 1 | `01-compose-service.md` | LiveKit server in compose, env keys, digest pin. The minimum infra to run the Phase 2 spike. | No — lands on mainline |
| 2 | `02-ml2-spike.md` | Validate the LiveKit Unity SDK loads and connects on Magic Leap 2 + Android Mobile. Throwaway smoke scene. | Mostly — SDK pin in `manifest.json` survives; smoke scene deleted |
| 3 | `03-backend-api.md` | `POST /livekit/token` endpoint, settings, codegen. Picks up where Phase 1 left off. | No |
| 4 | `04-transport-abstraction.md` | `INetworkTransport` interface; move `PhotonConnectionManager` behind it as `PhotonTransport`; stub `LiveKitTransport`. Pure Unity refactor, zero behavior change. | No |
| 5 | `05-livekit-transport.md` | Real `LiveKitTransport`: SDK plumbing, slot-claim, master election, send/receive, unit tests. | No |
| 6 | `06-cutover.md` | Flip default, delete Photon, update SPECs. | No |

## Dependency graph

```
1 ─→ 2 ─→ 3 ─┐
         └─→ 4 ─→ 5 ─→ 6
```

- **Phase 2** strictly blocks everything downstream — if the SDK doesn't work on ML2, the whole approach is up for re-evaluation.
- **Phase 3** and **Phase 4** are independent of each other after Phase 2 passes. Different parts of the repo, no shared files. May run in either order or in parallel.
- **Phase 4** has no technical dependency on Phases 1–3 (the refactor only touches existing Photon code and adds a `LiveKitTransport` stub that throws), but pragmatically nobody does the refactor work until Phase 2 has confirmed the swap is viable.
- **Phase 5** needs Phase 3's generated C# client and Phase 4's `INetworkTransport` stub.
- **Phase 6** is gated on real-device validation of Phase 5's work — the user has to confirm before any Photon deletion happens.

## Decisions baked in along the way

A few things resolved during the planning process worth knowing:

- **Identity comes from Keycloak `sub`.** Phase 3's token endpoint derives LiveKit identity from the validated Keycloak claim, not from client input. This gives Phase 5's slot-claim layer stable identities to map to playerIds. Anonymous/guest paths are out of scope unless explicitly added.
- **`Participant.JoinedAt` is not public on the C# wrapper.** Phase 5's master election works around this by having each participant self-set a `joined_at_ms` attribute on connect. Identity lex order is the tiebreak. Local clocks need not be synchronized — only a stable total order matters.
- **Two send methods on the transport interface.** `Send` for single-packet (under ~12 KiB), `SendLargeAsync` for chunked streams. LiveKit handles chunking automatically at `CHUNK_SIZE = 15000` bytes.
- **`PhotonSerialization.cs` is transport-agnostic.** Don't rename it. It serializes the diff format; the transport carries the bytes. Renaming is a cosmetic concern out of scope here.
- **No voice/audio.** Data channels only. The `video` grant name in the JWT claim is canonical LiveKit even for data-only use; nothing extra needed.

## Open questions still pending

Carried over from `../livekit-plan.md`. None of these block Phases 1 or 2.

1. Anonymous/guest LiveKit access ever needed for demos? (Affects Phase 3 identity sourcing.)
2. Voice/audio plumbing in this PR or follow-up? (Default: follow-up.)
3. `use_livekit` flag survives past Phase 6 or deleted immediately? (Default: delete in Phase 6.)
4. Target deployment for the initial 12-headset demo: same-LAN colocalized, or some participants remote? (Affects whether Phase 3's optional Caddy/ngrok route is needed.)
