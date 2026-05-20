Three direct answers.

## 3.3 — Why is this different from Photon?

**Photon Realtime hands you a stable monotonic integer per player** (`Player.ActorNumber`) as a first-class part of the product. Photon's worldview is "you have N players in a room, numbered 1..N, the numbers are mine to assign." That's exactly the shape `PlayerIdHelper`'s `playerId * 10000` ID-slicing needs, and that's why MakeItSing has no code to *make* a small int — Photon makes it.

**LiveKit's worldview is different.** A participant has `Participant.Identity`, an opaque string. LiveKit assumes the *application* owns identity (because it's primarily a WebRTC stack for arbitrary call/conference apps, where identity comes from the caller's auth provider). LiveKit deliberately doesn't make up integer IDs.

So the "extra step" is the impedance mismatch between those two worldviews. You need *some* mapping from identity-strings to small ints so `PlayerIdHelper`'s arithmetic still works. The mapping is small (one participant attribute storing the claimed slot) but it has to exist somewhere. Photon hides this from you for free; LiveKit hands you the lower-level primitive.

It's not technically hard — probably ~50 lines for slot-claiming via participant attributes — it's just net-new code that didn't exist before because Photon did it under the hood. Calling it out in the plan so it didn't get hand-waved.

## 3.6 — I was wrong, LiveKit ships this

Researched. LiveKit added **data streams** as a first-class feature: `SendText`, `StreamText`, `SendFile`, `StreamBytes`, plus `RegisterTextStreamHandler` / `RegisterByteStreamHandler` on the receive side. From [LiveKit's own docs](https://docs.livekit.io/home/client/data/text-streams/): "the input string is automatically chunked and streamed so there is no limit on string size." Chunks are typically ≤15 KB, reassembly is guaranteed complete and in-order, and the Unity SDK has the full API surface ([livekit/client-sdk-unity](https://github.com/livekit/client-sdk-unity)).

**So 3.6 collapses.** No manual chunking layer. Initial sync becomes:

```csharp
// send (master → joiner)
await _room.LocalParticipant.SendText(initialSyncJson, new SendTextOptions {
    Topic = "init", DestinationIdentities = new[] { joinerIdentity },
});

// receive (joiner)
_room.RegisterTextStreamHandler("init", async (reader, participant) => {
    var fullJson = await reader.ReadAll();
    ApplyInitialSync(fullJson);
});
```

For Code-2 incremental diffs and Code-3 HF pose, both stay on `PublishData` (single-packet, low-overhead) — the streams API is for the cases where you'd otherwise hit the 15 KiB cap. Section 3.6 in the plan should be a one-paragraph "use SendText for initial sync, PublishData for everything else" rather than its own chunking subsystem.

This actually also implies a small simplification to 2.1 — the `INetworkTransport` interface might want a separate `SendLarge(eventCode, payload, targetPlayerId)` method that maps to `SendText`/`SendFile` under the hood, since the wire encoding genuinely differs. Or it stays one `Send` method and the implementation routes based on payload size. Implementation-detail call, decide during the actual coding.

## Timeline — agree, I overestimated

Honest answer: **agree, the timeline was ~2x too long.** I was pricing this in pre-Claude-Code engineering-hours. With Claude Code the boilerplate-rate isn't the bottleneck; what actually consumes time is:

- **Running on hardware**: Magic Leap 2 + Android device pairs, observing real network behavior. Claude Code doesn't speed this up — it's wall-clock for build + deploy + reproduce.
- **SDK discovery**: undocumented LiveKit Unity quirks. Coroutines vs. async/await, threading model around `Room` events, what happens during reconnect. Some of this only surfaces in integration testing.
- **Codegen iteration loop**: `uv run generate-clients` is a few minutes per cycle; that's a real tax if you're tweaking endpoint shape.

Subtracting the LOC-bottlenecked time, revised:

| Phase | Original | Revised | Why |
|---|---|---|---|
| 0 — Spike | 1 day | half day | Two narrow questions, easy to answer with a localhost harness |
| 1 — Backend infra | 3-4 days | half day | Mechanical: compose service + router file + settings + codegen. Claude Code excels here. |
| 2 — Transport abstraction | 2-3 days | half day | Pure refactor, no semantic change, type system catches mistakes |
| 3 — LiveKit transport | 4-6 days | 2-4 days | Device-bound. Identity mapping + master election are quick; the long tail is reality. |
| 4 — Cutover | 1-2 days | half day | Delete + spec rewrite |

**Revised total: 4-6 days**, of which Phase 3 is genuinely the only one with real uncertainty. With 3.6 collapsing to a non-issue, Phase 3 trims further — maybe 1.5-3 days.

The honest framing: **everything except Phase 3 is a 1-day day-of-work, and Phase 3 is bounded by how cooperative the LiveKit Unity SDK is on Magic Leap 2.** If the SDK works first try on ML2, the whole project is a week. If there's a platform issue (ML2 is OpenXR + Android with quirks), Phase 3 stretches to discover and work around it. That's the actual risk — not engineering volume, but platform integration unknowns.

## Sources
- [LiveKit text streams docs](https://docs.livekit.io/home/client/data/text-streams/)
- [LiveKit byte streams docs](https://docs.livekit.io/home/client/data/byte-streams/)
- [LiveKit blog — data tracks announcement](https://livekit.com/blog/livekit-data-tracks-realtime-streaming)
- [LiveKit Unity SDK README](https://github.com/livekit/client-sdk-unity)
