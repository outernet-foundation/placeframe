# Phase 6 — LiveKit transport implementation

## Context

Phases 1 and 4 added the LiveKit compose service and the `POST /livekit/token` endpoint. Phase 3 validated that the LiveKit Unity SDK loads and operates on Magic Leap 2 + Android Mobile. Phase 5 introduced `INetworkTransport` and a stubbed `LiveKitTransport` that throws on `ConnectAsync`. This phase implements `LiveKitTransport` for real, so setting `UnityEnv.use_livekit = true` produces behavior equivalent to the existing Photon transport.

Read before starting:
- `/placeframe/CLAUDE.md` — especially UniTask-not-Task.Run, Serilog message templates, no docstrings, no inline imports, no temporal language in comments, no nested try blocks, callers-before-callees, classes-at-the-top.
- `/placeframe/apps/MakeItSing/CLAUDE.md` — the "don't fix these" list, the co-authorship reminder for Elliot Pjecha (this phase is mostly greenfield additions in `Assets/App/Networking/`, which is safer than touching shared replication logic).
- `/placeframe/apps/MakeItSing/SPEC.md` — the "Known issues" section documents the master-handoff bug this phase fixes.

## SDK facts already established (from source inspection)

These were verified by reading `livekit/client-sdk-unity` v1.3.7 and `livekit/rust-sdks` source. **Do not re-verify; trust and use.**

- `LocalParticipant.PublishData(byte[] data, IReadOnlyCollection<string> destination_identities = null, bool reliable = true, string topic = null)` is the actual signature. There is no `DataPacketKind` enum on the send side — that enum exists only on the receive callback. The `topic` parameter is preserved end-to-end and used for receive-side routing.
- LOSSY and RELIABLE are two distinct WebRTC data channels at the SCTP level (`ordered: true` vs `ordered: false, max_retransmits: Some(0)`). HOL-blocking independence between channels is an SCTP protocol guarantee.
- Outgoing chunking for streams is built-in: `CHUNK_SIZE = 15000` bytes, header → indexed chunks → trailer. Receive validates `chunk_index` monotonically. The Unity API exposes `RegisterByteStreamHandler` / `RegisterTextStreamHandler` and `ByteStreamReader.ReadAll()` returning a `ReadAllInstruction` (a Unity `YieldInstruction`, **not** a `Task` — wrap with `.ToUniTask()` or yield in a coroutine, never `await` directly).
- `Participant.JoinedAt` exists in the proto (`Proto/Participant.cs`) but is **not** publicly exposed on the C# `Participant` wrapper. Public members: `Sid / Identity / Name / Metadata / Attributes / ConnectionQuality`. See "Master election" below for the workaround.
- The Unity SDK is "Developer Preview" per its README. Pin to a tagged release. Treat API surface as potentially-shifting between SDK revisions.

## ML2 validation: already done in Phase 3

Phase 3's smoke spike confirmed the SDK's native `liblivekit_ffi.so` loads on ML2, ICE traversal works on the local WiFi, and `Room.Connect` + `PublishData` round-trips succeed. This phase proceeds on that basis. If Phase 3 surfaced platform-specific quirks (an `AndroidManifest.xml` permission, a `LIVEKIT_RTC_TCP_PORT` fallback requirement, a custom WebRTC config tweak), carry them forward into the real `LiveKitTransport` here.

## Goal

After this phase:
- The LiveKit Unity SDK is added to `apps/MakeItSing/Packages/manifest.json`, pinned to a specific release tag.
- `apps/MakeItSing/Assets/App/Networking/LiveKitTransport.cs` is a feature-complete `INetworkTransport` implementation.
- Slot-claim (LiveKit string identity → small-int `playerId`) and master election (using a self-set `joined_at_ms` participant attribute, since `JoinedAt` isn't exposed) both work correctly.
- Unit tests cover the pure-logic pieces (slot-claim resolution, master election ordering, identity/playerId inverse mapping).
- `uv run compile-unity --project MakeItSing --build android-mobile` and `uv run compile-unity --project MakeItSing --build magicleap` both succeed.
- The PR description hands off device validation steps to the user.

## Work

### 1. SDK install (already pinned in Phase 3)

The LiveKit Unity SDK pin landed in `apps/MakeItSing/Packages/manifest.json` during Phase 3. Confirm it's still there and matches the version that passed the smoke spike. If a newer release has shipped since Phase 3 and you want to bump, do that as an explicit decision — not a passive upgrade. The Phase 3 validation result only covers the validated version.

If Phase 3 added an `AndroidManifest.xml` INTERNET permission, confirm it's still present. Don't add RECORD_AUDIO or CAMERA — voice/audio is explicitly out of scope.

### 2. LiveKitTransport.cs structure

Replace the stub with the real implementation. Suggested file layout (per CLAUDE.md "classes at the top", "callers before callees"):

```
LiveKitTransport.cs               main MonoBehaviour, public surface, connection lifecycle, event dispatch
LiveKitTransport.SlotClaim.cs     partial class — slot-claim algorithm
LiveKitTransport.MasterElection.cs   partial class — master election with joined_at_ms attribute
LiveKitTransport.Send.cs          partial class — Send / SendLargeAsync mappings
LiveKitTransport.Receive.cs       partial class — DataReceived + byte-stream handlers
```

Split into partial-class files only if the total exceeds ~250 lines; otherwise keep it all in one file. Match the existing project's file-splitting taste (look at how `AppActions.cs` and similar are organized).

### 3. Connection flow

`ConnectAsync(string roomId, CancellationToken cancellationToken)`:

1. Call the generated `PlaceframeApiClient.PostLivekitTokenAsync(new() { Room = roomId })`. The existing `AuthHttpHandler` at `packages/unity/Placeframe/Assets/Package/Core/Runtime/Auth.cs` auto-attaches the Keycloak bearer token — no manual auth wiring.
2. From the response, extract `token`, `url`, `identity`. Cache the local `identity` — it's used to map back to the local participant in event handlers.
3. `await _room.Connect(url, token)` (wrap with `.ToUniTask()` if `Connect` returns a `YieldInstruction`; check the SDK signature).
4. Run the slot-claim handshake (§4) to obtain `LocalPlayerId`.
5. Set the local participant's `joined_at_ms` attribute (§5) so other clients can compute master election.
6. Subscribe to room events: `_room.ParticipantConnected`, `ParticipantDisconnected`, `DataReceived`, `Disconnected`, `ParticipantAttributesChanged`. Register byte-stream handlers via `_room.RegisterByteStreamHandler(...)`. Map all of these to the `INetworkTransport` events.

Threading note from source inspection: room-level events fire on the Unity main thread; data-stream chunk events fire on the FFI background thread. If a handler that originates from `RegisterByteStreamHandler` needs to touch Unity-thread-only state (`Transform`, `GameObject`, etc.), marshal back via `UniTask.SwitchToMainThread()`. The state replication code is already main-thread-bound — make sure dispatched events end up there.

### 4. Slot-claim for `playerId`

**Why this exists.** LiveKit identifies participants by string identity. The existing replication code (specifically `PlayerIdHelper`'s `playerId * 10000` ID-slicing math) needs small ints. Slot-claim is the impedance-matching layer. Target: ~50 lines.

**Algorithm.** Each participant claims a slot index in `[1, MaxPlayers]` and stores it as a LiveKit participant attribute named `slot`. On any participant join/leave, every client runs:

```
1. Read everyone's `slot` attribute (including local).
2. Find the lowest unused slot in [1, MaxPlayers].
3. If local doesn't have a slot yet, set local's attribute to the lowest unused.
4. Recompute `ConnectedPlayerIds` from the (identity → slot) mapping.
```

**Race resolution.** Two joiners might pick the same slot simultaneously. Resolve by deterministic tiebreak: `joined_at_ms` ascending (lowest wins; ties broken by `Identity` lex order). The loser releases its claim and re-runs the algorithm. Cap retries at `MaxPlayers` to avoid pathological loops.

**Stability.** A participant's slot is stable for their session. When a participant leaves, their slot is freed; new joiners can reclaim it. This matches the current Photon `ActorNumber` behavior closely enough that `PlayerIdHelper`'s assumptions hold.

`MaxPlayers` should be sourced from the existing config that Photon uses (grep for it — there's a room-size constant somewhere). Default to 12 if no existing config is found.

### 5. Master election (with `joined_at_ms` attribute)

Because `Participant.JoinedAt` isn't surfaced on the public C# wrapper, every client self-publishes a `joined_at_ms` attribute immediately after `_room.Connect()` completes:

```csharp
var joinedAt = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();
await _room.LocalParticipant.SetAttributes(new Dictionary<string, string> {
    ["joined_at_ms"] = joinedAt.ToString(CultureInfo.InvariantCulture),
}).ToUniTask();
```

Local clocks don't need to be synchronized — the election only needs a stable total order. Tiebreak by `Identity` lex order for the (rare) case of identical timestamps or unset attributes.

**Algorithm.** On each of `ParticipantConnected` / `ParticipantDisconnected` / `ParticipantAttributesChanged`:

```
1. Build the list of (identity, joined_at_ms, Identity) for all participants including local.
2. For any participant whose `joined_at_ms` attribute is unset or unparseable, use `long.MaxValue` (treat as last-to-join).
3. Sort by (joined_at_ms ascending, Identity ascending).
4. The first entry is master.
5. If the master identity changed since the last computation, fire `OnMasterChanged(playerIdForIdentity(newMaster))`.
```

`IsMaster` returns `localIdentity == currentMasterIdentity`.

**This fixes the latent bug** documented in `apps/MakeItSing/SPEC.md` "Known issues" where Photon's `OnMasterClientSwitched` only logs. Call this out in the PR description.

**Debounce — defer.** Master flips can be noisy on flaky WiFi. The original plan suggests a 500 ms stabilization window. **Do not add this here.** If master-flip thrash is observed during device testing, add it as a follow-up. Defer-until-observed avoids speculative complexity.

### 6. Send mapping

Single-packet sends use `LocalParticipant.PublishData`:

```csharp
public void Send(byte eventCode, byte[] payload, DeliveryReliability reliability, int? targetPlayerId = null)
{
    var destinations = targetPlayerId.HasValue
        ? new[] { IdentityForPlayerId(targetPlayerId.Value) }
        : null;

    _room.LocalParticipant.PublishData(
        payload,
        destination_identities: destinations,
        reliable: reliability == DeliveryReliability.Reliable,
        topic: eventCode.ToString(CultureInfo.InvariantCulture));
}
```

The `topic` parameter carries `eventCode` end-to-end. Receive-side parses `byte.Parse(topic)` to recover it.

Large sends use `StreamBytes` (not `SendFile` — `SendFile` takes a file path on disk, not bytes):

```csharp
public async UniTask SendLargeAsync(byte eventCode, byte[] payload, int? targetPlayerId = null)
{
    var options = new StreamByteOptions
    {
        Topic = eventCode.ToString(CultureInfo.InvariantCulture),
        DestinationIdentities = targetPlayerId.HasValue
            ? new List<string> { IdentityForPlayerId(targetPlayerId.Value) }
            : new List<string>(),
    };

    var openInstruction = _room.LocalParticipant.StreamBytes(options);
    await openInstruction.ToUniTask();
    var writer = openInstruction.Writer;

    await writer.Write(payload).ToUniTask();
    await writer.Close().ToUniTask();
}
```

If `.ToUniTask()` isn't already an extension method registered for `YieldInstruction` in the project, write a small extension in the `Networking/` folder. `Cysharp.Threading.Tasks` ships patterns for this; one common form:

```csharp
public static class YieldInstructionExtensions
{
    public static UniTask ToUniTask(this YieldInstruction yieldInstruction)
        => UniTask.Create(async () => { await yieldInstruction; });
}
```

If `await yieldInstruction` itself doesn't work in the target Unity version, fall back to wrapping in a coroutine. Check the surrounding code for the existing pattern.

LiveKit's data streams handle chunking automatically (`CHUNK_SIZE = 15000`, reliable SCTP channel) — no manual chunk-and-reassemble layer is needed. The initial-sync JSON (eventCode 1) goes through `SendLargeAsync`; incremental diffs (eventCode 2) and HF pose (eventCode 3) use `Send`. Confirm the eventCode constants by grepping the existing Photon code — match exactly.

### 7. Receive mapping

Two receive paths:

```csharp
_room.DataReceived += (data, participant, kind, topic) =>
{
    if (!byte.TryParse(topic, NumberStyles.Integer, CultureInfo.InvariantCulture, out var eventCode))
    {
        Log.Warning(LogGroup.Networking, "DataReceived with unparseable topic {Topic} from {Identity}",
            topic, participant.Identity);
        return;
    }
    var senderId = PlayerIdForIdentity(participant.Identity);
    OnDataReceived?.Invoke(senderId, eventCode, data);
};

_room.RegisterByteStreamHandler("1", (reader, participantIdentity) =>
{
    HandleInitialSync(reader, participantIdentity).Forget();
});

private async UniTaskVoid HandleInitialSync(ByteStreamReader reader, string participantIdentity)
{
    var instruction = reader.ReadAll();
    await instruction.ToUniTask();
    var senderId = PlayerIdForIdentity(participantIdentity);
    OnDataReceived?.Invoke(senderId, eventCode: 1, instruction.Bytes);
}
```

Match the actual `LogGroup` enum/category that the rest of the MakeItSing codebase uses for networking logs (grep `LogGroup`). If there isn't a `Networking` category yet, add one or reuse the closest existing one — don't invent a new log subsystem just for this.

The handler registration string `"1"` must match the eventCode the sender uses for large initial-sync payloads. Confirm by greping the existing Photon code for the eventCode constants and use the same numeric value.

The eventCode-to-handler routing is consistent on both sides (sender uses `topic = eventCode.ToString()`, receiver registers a handler keyed on `eventCode.ToString()`).

### 8. Identity ↔ playerId mapping

`IdentityForPlayerId(int)` and `PlayerIdForIdentity(string)` are inverses derived from the slot-claim state. The internal mapping is built from participant attributes:

```
identity → slot (from `slot` attribute, populated by §4)
```

Both lookups need to be O(1) — cache the bidirectional map. Rebuild it whenever the slot-claim algorithm updates.

For the local participant during the window between `_room.Connect()` returning and slot-claim completing, return `0` for `LocalPlayerId` and treat the participant as not-yet-joined for emission purposes (don't fire `OnPlayerJoined` for local self).

### 9. Unit tests

Add `apps/MakeItSing/Assets/App/Networking/Editor/Tests/LiveKitTransportTests.cs` covering pure logic (no live LiveKit dependency). Match the test framework the project already uses (NUnit via Unity Test Framework most likely — check `PhotonSerializationTests.cs` for the pattern).

Test cases:
- **Slot-claim, simple.** Given a participant list with three participants and `slot` attributes `{1, 2, 3}`, the algorithm picks `4` for a fourth joiner.
- **Slot-claim, gap.** Given `slot` attributes `{1, 3}`, the algorithm picks `2`.
- **Slot-claim, race.** Two participants simultaneously claim `slot = 1`. The one with the lower `joined_at_ms` wins; the loser re-runs and claims `2`.
- **Slot-claim, race tiebreak by identity.** Identical `joined_at_ms` — lexicographically smaller `Identity` wins.
- **Master election, simple.** Three participants with `joined_at_ms` `{100, 200, 300}` — master is the one at 100.
- **Master election, leave.** Master leaves; the next-earliest becomes master.
- **Master election, attribute missing.** A participant with no `joined_at_ms` attribute sorts last.
- **Master election, identical timestamps.** Tiebreak by `Identity` lex order.
- **Identity/playerId inverse.** `PlayerIdForIdentity(IdentityForPlayerId(n)) == n` for any `n` in the slot map.

Mock the participant list with a simple test double — don't try to spin up a real LiveKit room from unit tests. The algorithms should be pure functions over a participant-snapshot input; extract them as testable statics if they aren't naturally so.

### 10. Verify

```bash
uv run compile-unity --project MakeItSing --build android-mobile
uv run compile-unity --project MakeItSing --build magicleap
```

Both must succeed. The Magic Leap target's native-`.so` runtime risk was already retired in Phase 3; compile failures here would point at integration mistakes (missing UniTask wrappers, `using` directives, asmdef references), not SDK-level platform issues.

Unit tests must pass.

`uv run --no-sync preflight` must be green.

## Device-validation handoff (user-driven, post-PR)

Claude Code cannot run on-device validation. State explicitly in the PR description that the following must pass before Phase 7 begins:

1. Two clients (editor + Android Mobile device, both with `use_livekit = true`) join the same room. Avatar appears for each, transforms sync at 16 Hz, grabbing an `XRGrabbable` syncs ownership.
2. Three clients including one Magic Leap 2. Late joiner sees full state via initial sync. The HF channel doesn't head-of-line-block the incremental diff stream.
3. Master disconnects mid-session. New master is elected (verifies the bug fix). State continues to converge. No state loss.
4. Network blip (toggle WiFi on one device). Reconnection works without state corruption.
5. Magic Leap 2 + Android Mobile + Editor all three in the same room.

If any of these fail, document the failure mode and the workaround/fix. Real failures here are the most likely place for SDK quirks (especially on ML2) to surface; don't pretend they didn't happen.

## Commit hygiene

Code changes only in this phase. Single commit covering the full `LiveKitTransport` implementation plus unit tests. The `manifest.json` SDK pin already landed in Phase 3 — don't re-touch it unless deliberately bumping the version.

No `.asmdef` cross-folder edits should be needed — `Networking/` was set up in Phase 5.

No prose updates in this phase — those land in Phase 7 once devices verify the swap works. No `Co-Authored-By`. No `--no-verify`.

No codegen runs in this phase (the API endpoint already exists from Phase 4).

## Exit criteria

- LiveKit Unity SDK pinned in `manifest.json` at a specific release.
- `apps/MakeItSing/Assets/App/Networking/LiveKitTransport.cs` is feature-complete: `ConnectAsync`, `DisconnectAsync`, `Send`, `SendLargeAsync`, slot-claim, master election, all `INetworkTransport` events wired.
- `LiveKitTransportTests.cs` covers slot-claim and master election logic.
- `uv run compile-unity --project MakeItSing --build android-mobile` passes.
- `uv run compile-unity --project MakeItSing --build magicleap` passes.
- `uv run --no-sync preflight` is green.
- PR description hands off the on-device test plan to the user.

## Out of scope

- Flipping `UnityEnv.use_livekit` to `true` by default — Phase 7.
- Deleting `PhotonTransport.cs` and the Photon SDK — Phase 7.
- SPEC.md / CLAUDE.md prose updates — Phase 7.
- Master-flip debounce — defer until observed.
- Voice/audio.
- Anonymous/guest identity paths.
- Server-side webhook injection of `joined_at_ms` (workaround option 3 from the master plan — only needed if the self-set attribute approach fails on device).
