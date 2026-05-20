# Plan: Swap Photon → LiveKit for MakeItSing networking

> **Status note.** This file is the original design rationale. The active operational breakdown lives in `livekit-plan/` and now spans seven phases (originally six). See `livekit-plan/README.md` for current per-phase status; below is a summary.
>
> | Phase (operational) | Status |
> |---|---|
> | 1 — LiveKit compose service | ✅ Done (commit `cb3f866d`) |
> | 2 — Ngrok routing for LiveKit | 🔜 Next — inserted after the dev-sandbox network model made LAN-direct unworkable for headsets on the user's WiFi |
> | 3 — ML2 + Android Mobile spike | 🟡 Partial — SDK pinned (`f77afe40`), smoke scaffold landed (`89c5a42c`), Magic Leap compile + APK verified, device round-trip blocked on Phase 2 URL |
> | 4 — Backend API (token-mint) | Not started |
> | 5 — Transport abstraction | Not started |
> | 6 — LiveKit transport implementation | Not started |
> | 7 — Cutover and Photon teardown | Not started |
>
> The phase numbers in the rest of this document (Phase 0 / Spike, Phase 1 / Backend infrastructure, etc.) reflect the original 5-phase rationale grouping and do **not** map 1:1 onto the operational phases above. When in doubt, defer to `livekit-plan/`.

## Context

MakeItSing currently uses Photon Realtime (5.1.9, bundled SDK at `Assets/ThirdParty/photon-unity-sdk_v5-1-9/`) for its multiplayer state replication. The integration is unusually clean: ~530 lines in `Assets/App/Managers/PhotonConnectionManager.cs` and a small custom binary codec, sitting on top of three Photon `OpRaiseEvent` channels (reliable-targeted, reliable-broadcast, unreliable-broadcast). The state-tree replication model above the transport (path-as-schema, `App.ExecuteTransaction`, `ISceneObjectViewComponent`, `PlayerIdHelper`'s ID slicing) is transport-agnostic.

This plan swaps Photon for self-hosted LiveKit. Reasons, in order:

- **Anti-vendor-lockin is the highest priority.** Photon is closed-source SaaS. LiveKit is Apache 2.0 self-hostable open source. The license-rug-pull risk on LiveKit (VC-backed company with paid Cloud product) is real but bounded — the transport abstraction this plan introduces makes any future swap a sibling implementation, not a rewrite.
- **Scale target is ~12 colocalized XR headsets** within six months (Magic Leap 2 + Android Mobile). Photon Cloud per-CCU pricing scales poorly at this size; self-hosted infrastructure on the existing docker compose stack does not.
- **Voice/audio optionality.** Colocalized XR experiences plausibly want spatial audio later. LiveKit gives that path for free as the same SFU; NATS/Mediasoup/raw WebRTC do not.
- **Master-handoff is currently broken** in the Photon code (per `apps/MakeItSing/SPEC.md` "Known issues" — `OnMasterClientSwitched` only logs). The rewrite is an opportunity to fix this, not a regression risk.

## Goals

1. Replace Photon Realtime with self-hosted LiveKit as the networking transport.
2. Introduce a thin `INetworkTransport` interface so the transport choice is reversible and testable.
3. Add LiveKit as a service to the existing docker compose stack with the codebase's pinning and healthcheck conventions.
4. Preserve all state-replication semantics (path-as-schema diff stream, ID-slicing, scene-baked negative IDs, master-client authority).
5. Fix the master-handoff bug as part of the swap.

## Non-goals

- **Not rewriting `PlayerIdHelper` or migrating to GUIDs.** The negative-int convention for scene-baked objects (`SceneViewManager.cs:28-34`, `InRoomManager.cs:104-108`) is load-bearing for zero-coordination consensus on baked-object IDs across clients. That refactor deserves its own PR with the original author. Out of scope here.
- **Not adding voice/audio.** Plumb the data channel only. Voice is a follow-up.
- **Not solving external (non-LAN) participant exposure.** Colocalized headsets on a shared network is the immediate target. Remote participants over ngrok-UDP is a separate problem deferred until needed.
- **Not adding raw P2P datachannel mesh.** LiveKit SFU-routed on the local network is the starting point. If measured latency proves insufficient for HF pose updates, the abstraction allows a parallel raw-WebRTC implementation later.

## Architecture

### Transport interface

Single C# interface, defined in `apps/MakeItSing/Assets/App/Networking/INetworkTransport.cs`:

```csharp
public enum DeliveryReliability { Reliable, Unreliable }

public interface INetworkTransport
{
    bool IsConnected { get; }
    bool IsMaster { get; }
    int LocalPlayerId { get; }
    IReadOnlyList<int> ConnectedPlayerIds { get; }

    UniTask ConnectAsync(string roomId, CancellationToken ct);
    UniTask DisconnectAsync();

    void Send(byte eventCode, byte[] payload, DeliveryReliability reliability, int? targetPlayerId = null);
    UniTask SendLargeAsync(byte eventCode, byte[] payload, int? targetPlayerId = null);

    event Action<int, byte, byte[]> OnDataReceived;
    event Action<int> OnPlayerJoined;
    event Action<int> OnPlayerLeft;
    event Action<int> OnMasterChanged;
    event Action OnDisconnected;
}
```

Two send methods: `Send` for single-packet payloads (under ~12 KiB after framing — covers incremental diffs and HF pose), `SendLargeAsync` for arbitrarily-sized payloads via the SDK's stream API (initial sync JSON). Implementations route appropriately.

### Service layout

LiveKit runs as a new docker compose service at `livekit:7880` (signaling) + `livekit:7881` (RTC TCP fallback) + `50000-50100/udp` (media). API service gains a `POST /livekit/token` endpoint that mints LiveKit JWTs for authenticated callers. The MakeItSing client fetches a token via the auto-generated C# API client, connects to LiveKit, and uses data channels for the existing three event codes.

---

## Phase 0 — Spike (half day)

**Goal**: verify the remaining unknowns before committing to the full implementation.

The original task 1 (Unity SDK API verification) was resolved from source inspection of `livekit/client-sdk-unity` v1.3.7 and `livekit/rust-sdks` rather than a Unity harness. Findings:

- `LocalParticipant.PublishData(byte[] data, IReadOnlyCollection<string> destination_identities = null, bool reliable = true, string topic = null)` preserves `topic` end-to-end (Participant.cs:108, Room.cs:501) and SFU-side filters delivery to `destination_identities` when set.
- LOSSY and RELIABLE are two distinct WebRTC data channels at the SCTP level (`rust-sdks` `rtc_session.rs:491-502`: `ordered: true` vs `ordered: false, max_retransmits: Some(0)`). HOL-blocking independence is a protocol guarantee, not an SDK behavior.
- Outgoing chunking is built-in (`CHUNK_SIZE = 15000`, `outgoing.rs:489`), receive validates `chunk_index` monotonically (`incoming.rs:300`), Unity exposes `RegisterByteStreamHandler` / `RegisterTextStreamHandler` + `reader.ReadAll()` returning a `ReadAllInstruction` yield instruction (ByteDataStream.cs:61, TextDataStream.cs:79).
- **`Participant.JoinedAt` is not publicly surfaced on the C# wrapper** despite existing in the proto (`Proto/Participant.cs:432`). Public members are `Sid / Identity / Name / Metadata / Attributes / ConnectionQuality`. See Phase 3.4 for the workaround.

### Tasks

1. **ML2 device validation.** The SDK ships `Runtime/Plugins/ffi-android-arm64/liblivekit_ffi.so`; ML2 is arm64 Android 10; the SDK has zero Unity-XR coupling. The risks are mechanical: does the native library load on Magic Leap 2, does ICE/STUN traversal pick a usable candidate, can the HF channel sustain its 16 Hz rate under XR rendering load? Build the SDK's `Samples~/Basic` sample to ML2 + Android Mobile and connect both to a localhost `livekit/livekit-server` over WiFi. ~30 minutes if it works first try.
2. **JoinedAt workaround prototype.** Implement option (1) from Phase 3.4 (self-set `joined_at_ms` participant attribute on connect, tiebreak by `Identity` lex order) on top of the Basic sample with 3 simulated participants. Verify the same total order emerges on all clients across rejoins. ~1 hour.
3. **Ngrok UDP path.** Check whether LiveKit's `rtc.tcp_port` fallback works end-to-end through the existing ngrok setup. Document the answer in `docker/SPEC.md` under a new "LiveKit external exposure" subsection. If TCP fallback works, the LAN-only constraint relaxes; if not, document the limit and move on (colocalized doesn't need this). May be skipped if the deployment is moving to a Tailscale funnel.

### Exit criteria

- Tasks 1 and 2 pass, or any failure has a documented workaround.
- Task 3 answered or formally deferred.
- No code committed; spike artifacts in `/tmp/` or a throwaway branch.

---

## Phase 1 — Backend infrastructure (half day)

**Goal**: LiveKit service running in `uv run up`, API endpoint mints JWTs, codegen produces a Unity-callable client method.

### 1.1 LiveKit compose service

Add to `/placeframe/compose.yml`:

```yaml
livekit:
  image: ${LIVEKIT_IMAGE:?err}
  environment:
    LIVEKIT_KEYS: "${LIVEKIT_API_KEY:?err}: ${LIVEKIT_API_SECRET:?err}"
    LIVEKIT_PORT: "7880"
    LIVEKIT_RTC_TCP_PORT: "7881"
    LIVEKIT_RTC_UDP_PORT_RANGE_START: "50000"
    LIVEKIT_RTC_UDP_PORT_RANGE_END: "50100"
  ports:
    - "7880:7880"
    - "7881:7881"
    - "50000-50100:50000-50100/udp"
  healthcheck:
    test: ["CMD", "wget", "-qO-", "http://localhost:7880/"]
    interval: 10s
    timeout: 3s
    retries: 5
  restart: unless-stopped
```

**Image pinning** (per the CLAUDE.md rule against `:latest`):
1. Pick a LiveKit release (latest stable at time of implementation).
2. Resolve its digest: `docker buildx imagetools inspect docker.io/livekit/livekit-server:v1.X.Y`.
3. Add `LIVEKIT_IMAGE=docker.io/livekit/livekit-server@sha256:...` to `.env.lock`.
4. If `scripts/src/scripts/context_sha.py` automates digest pinning, wire it through; otherwise pin manually with a comment pointing at the release notes.

**No Postgres, no Redis.** Single-node LiveKit holds room state in memory. Adequate for the 12-headset target.

### 1.2 Token-mint endpoint

New file `/placeframe/docker/api/src/routers/livekit.py` (mirrors the existing controller pattern from `routers/leases.py`):

```python
import time
from datetime import timedelta
from typing import Annotated

import jwt
from litestar import Controller, post
from litestar.params import Body
from pydantic import BaseModel

from ..settings import Settings

class LiveKitTokenRequest(BaseModel):
    room: str

class LiveKitTokenResponse(BaseModel):
    token: str
    url: str
    identity: str

class LiveKitController(Controller):
    path = "/livekit"

    @post("/token")
    async def mint_token(
        self,
        data: Annotated[LiveKitTokenRequest, Body()],
        settings: Settings,
        request_user: AuthenticatedUser,
    ) -> LiveKitTokenResponse:
        identity = request_user.subject
        now = int(time.time())
        claims = {
            "iss": settings.livekit_api_key,
            "sub": identity,
            "iat": now,
            "exp": now + int(timedelta(hours=6).total_seconds()),
            "video": {
                "room": data.room,
                "roomJoin": True,
                "canPublish": True,
                "canSubscribe": True,
                "canPublishData": True,
            },
        }
        token = jwt.encode(claims, settings.livekit_api_secret, algorithm="HS256")
        return LiveKitTokenResponse(token=token, url=settings.livekit_url, identity=identity)
```

Key design choice: **identity is server-derived from the Keycloak `sub` claim**, not client-supplied. The existing `AuthMiddleware` (`docker/api/src/auth.py:36-96`) validates the Keycloak token; the controller uses the validated subject as the LiveKit identity. This means MakeItSing players are identified by their Keycloak user, not by a random per-session UUID — relevant because the slot-claim layer in Phase 3.3 will need stable identities to map to playerIds.

Adjust `request_user: AuthenticatedUser` to whatever the existing convention is for accessing the authenticated subject in the Litestar handler — match what `leases.py` or `localization.py` does.

### 1.3 Settings additions

Add to `docker/api/src/settings.py`:

```python
livekit_api_key: str
livekit_api_secret: str
livekit_url: str  # "ws://livekit:7880" inside compose, "wss://${PUBLIC_DOMAIN}/livekit" externally if ngrok routes WS
```

### 1.4 Router registration

In `docker/api/src/main.py` around lines 82-98 (where other routers register), import and register `LiveKitController`.

### 1.5 Env scaffolding

Add to `.env.sample`:

```
LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=devsecretmustbeatleast32charslongforhmacsha256
LIVEKIT_URL=ws://livekit:7880
```

`.env` (real values, gitignored) gets the same keys with real secrets. For production, the API key/secret should be generated per environment, not shared.

### 1.6 Optional: gateway WebSocket route

If external (ngrok) access is needed even for signaling, add a Caddy route in `/placeframe/docker/gateway/entrypoint.sh` proxying `/livekit` → `ws://livekit:7880`. For LAN-only colocalized testing, skip this — clients connect directly to `ws://<host>:7880`.

### 1.7 Codegen

Run, in order:
```bash
uv run up                                          # bring up the stack, verify livekit healthcheck passes
uv run generate-clients --project docker/api       # regenerate API clients including the new endpoint
```

The new `PostLivekitToken` method appears automatically in `packages/generated/csharp/api-client/`. Commit codegen output in a separate `Run generate-clients` commit per the codegen hygiene rule in `CLAUDE.md`.

### Exit criteria

- `uv run up` brings up LiveKit alongside other services.
- `uv run --no-sync preflight` is green.
- Manual test: `curl -X POST http://localhost:8080/api/livekit/token -H "Authorization: Bearer $KEYCLOAK_TOKEN" -d '{"room":"test"}'` returns `{token, url, identity}`.
- A Python `livekit-server-sdk` script can connect to the LiveKit server using the minted token.

---

## Phase 2 — Transport abstraction (half day)

**Goal**: Photon code moved behind `INetworkTransport`. Zero behavior change.

### 2.1 Define the interface

Create `apps/MakeItSing/Assets/App/Networking/INetworkTransport.cs` with the interface from the Architecture section above.

### 2.2 Implement `PhotonTransport`

Move `Assets/App/Managers/PhotonConnectionManager.cs` → `Assets/App/Networking/PhotonTransport.cs`. Mechanical renames:

- `OpRaiseEvent(code, payload, options)` → `Send(code, payload, reliability, targetPlayerId)`.
- For payloads exceeding `OpRaiseEvent`'s practical size, route `SendLargeAsync` to the same `OpRaiseEvent` reliable path the existing code uses for initial sync. The chunking concern goes away in Phase 4 when Photon is deleted.
- Photon `OnEvent` → fire `OnDataReceived` event.
- `OnPlayerEnteredRoom` / `OnPlayerLeftRoom` → fire `OnPlayerJoined` / `OnPlayerLeft`.
- `OnMasterClientSwitched` → fire `OnMasterChanged`.
- `LocalPlayer.ActorNumber` → `LocalPlayerId`.

The state-diff stream code in `AppActions.cs` is unchanged — it now consumes `INetworkTransport` events instead of Photon-typed callbacks.

### 2.3 Dispatch in AppSetup

At `AppSetup.cs:325` (where `PhotonConnectionManager` is added today), replace with:

```csharp
INetworkTransport transport = UnityEnv.use_livekit
    ? gameObject.AddComponent<LiveKitTransport>()
    : gameObject.AddComponent<PhotonTransport>();
```

Add `use_livekit: bool` to `UnityEnv` (default `false`). The `LiveKitTransport` class in this phase is a stub that throws on `ConnectAsync`. It exists so the dispatch compiles.

### 2.4 Verify

- `uv run compile-unity --project MakeItSing --build android-mobile` succeeds.
- `PhotonSerializationTests.cs` still passes (codec is unchanged).
- Manual smoke test: with `use_livekit = false`, two clients (editor + device) join a Photon room, behavior identical to pre-refactor.

### Exit criteria

- No reference to `Photon.Realtime` types exists outside `PhotonTransport.cs`.
- All state-replication code consumes `INetworkTransport` events.
- The Photon flow works end-to-end exactly as before.

---

## Phase 3 — LiveKit transport (2-4 days)

**Goal**: `LiveKitTransport : INetworkTransport` is feature-complete. Setting `UnityEnv.use_livekit = true` produces equivalent behavior to Photon.

### 3.1 SDK install

Add the LiveKit Unity SDK to `apps/MakeItSing/Packages/manifest.json` (check whether the SDK ships via UPM, NuGet, or both for the project's Unity version — pick whichever matches the existing dependency pattern). Pin to a specific release. If the SDK has Android transitive native dependencies, they must compile for both Android Mobile (ARCore) and Magic Leap 2 (OpenXR + Android). Verify with `uv run compile-unity` for both build targets early.

### 3.2 Connection flow

`LiveKitTransport.ConnectAsync(roomId, ct)`:

1. Call the generated `PlaceframeApiClient.PostLivekitTokenAsync(new() { Room = roomId })`. The existing `AuthHttpHandler` (`packages/unity/Placeframe/Assets/Package/Core/Runtime/Auth.cs:10-21`) auto-attaches the Keycloak bearer token.
2. From the response, get `token`, `url`, `identity`.
3. `await _room.Connect(url, token)`.
4. Run the slot-claim handshake (3.3 below) to obtain `LocalPlayerId`.
5. Subscribe to `_room.ParticipantConnected`, `ParticipantDisconnected`, `DataReceived`, `Disconnected`, and register byte-stream handlers — map to `INetworkTransport` events.

### 3.3 Slot-claim for `playerId`

**Why this exists**: LiveKit gives string identities; `PlayerIdHelper`'s `playerId * 10000` math needs small ints. This is the impedance-mismatch layer. ~50 lines.

**Algorithm**: each participant claims a slot index (1, 2, 3...) and stores it as a LiveKit participant attribute (`slot`). On any participant join/leave:

1. Read everyone's `slot` attribute, including unset/in-progress.
2. Find the lowest unused slot in `[1, max_players]`.
3. If you don't have a slot yet, set yours to the lowest unused.
4. Update local `playerId` and `ConnectedPlayerIds` mapping.

**Race condition**: two joiners might claim the same slot simultaneously. Resolution: deterministic tiebreak by `Participant.JoinedAt` (earlier wins) — the loser re-claims the next lowest. Single retry loop, capped at `max_players` iterations.

**Stability**: a participant's slot is stable for their session lifetime. When a participant leaves, their slot is freed; new joiners can reclaim it. This matches the current Photon behavior closely enough that `PlayerIdHelper`'s assumptions hold.

Implementation goes in `LiveKitTransport.SlotClaim.cs` (separate file from the main transport to keep the dispatch logic readable).

### 3.4 Master election

**Constraint**: the C# `Participant` wrapper does not surface `JoinedAt` (see Phase 0 findings). The proto carries `joined_at_ms` but it is not exposed publicly. Workaround options, in order of preference:

1. **Self-set `joined_at_ms` attribute on connect.** Immediately after `_room.Connect()` completes, the local participant calls `SetAttributes(new() { ["joined_at_ms"] = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds().ToString() })`. Other clients read this attribute via `participant.Attributes`. Local clocks need not be synchronized — a total order with a stable tiebreaker (`Identity` lexicographic) is all the election needs. ~10 lines.
2. **Fork the SDK** and surface `JoinedAt => _info.JoinedAt` on `Participant` (~5 lines). Submittable upstream. Use only if (1) proves insufficient.
3. **Server-side webhook injection** — API service subscribes to LiveKit `participant_joined` webhooks and patches an authoritative `joined_at` into participant attributes via the server-side API. Heaviest; defer unless (1) and (2) both fail.

Start with (1). Phase 0 task 2 prototypes it.

Algorithm with workaround (1):
1. Read each participant's `joined_at_ms` attribute, defaulting to `long.MaxValue` for participants that haven't set theirs yet (treat as last-to-join).
2. Sort by `(joined_at_ms, Identity)` ascending.
3. The first is master.
4. Fire `OnMasterChanged(newMasterPlayerId)` if the identity at position 0 changed since last computation.

Re-run on `ParticipantConnected`, `ParticipantDisconnected`, and `ParticipantAttributesChanged` (the latter handles the brief window before a freshly-joined participant publishes their attribute).

**Debounce**: if join/leave is noisy, master can flip rapidly. Add a 500 ms stabilization window before honoring a master change — useful in flaky-WiFi demo conditions. Defer until observed in Phase 3.8 if it complicates initial implementation.

**This fixes the latent bug** documented in `apps/MakeItSing/SPEC.md` "Known issues" where `OnMasterClientSwitched` only logs. Call this out explicitly in the PR description.

### 3.5 Send mapping

The Unity SDK's `PublishData` takes `bool reliable` (no `DataPacketKind` enum on the send side; that enum exists only on the receive callback). For large payloads, `SendFile` takes a file path on disk (not byte arrays), so the right API for in-memory bytes is `StreamBytes` with explicit `Writer.Write` + `Writer.Close`.

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
        topic: eventCode.ToString());
}

public async UniTask SendLargeAsync(byte eventCode, byte[] payload, int? targetPlayerId = null)
{
    var options = new StreamByteOptions {
        Topic = eventCode.ToString(),
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

`.ToUniTask()` is the conventional UniTask wrapper for Unity yield instructions; if a project-wide helper doesn't already exist, write a small extension (`Cysharp.Threading.Tasks` ships `WaitForCompletion` patterns for `YieldInstruction`). LiveKit's data streams handle chunking automatically (`CHUNK_SIZE = 15000`, reliable SCTP channel — no manual chunk-and-reassemble layer needed). The initial-sync JSON (Code 1, can exceed 15 KiB on large scenes) goes through `SendLargeAsync`; incremental diffs (Code 2) and HF pose (Code 3) use `Send`.

### 3.6 Receive mapping

`Room.DataReceived` has signature `(byte[] data, Participant participant, DataPacketKind kind, string topic)` (Room.cs:125). The stream handler signature is `(ByteStreamReader reader, string participantIdentity)` (DataStream.cs:32). `ByteStreamReader.ReadAll()` returns a Unity `ReadAllInstruction` — yield it in a coroutine or wrap with `.ToUniTask()`; do not `await` it directly.

```csharp
_room.DataReceived += (data, participant, kind, topic) => {
    var eventCode = byte.Parse(topic);
    var senderId = PlayerIdForIdentity(participant.Identity);
    OnDataReceived?.Invoke(senderId, eventCode, data);
};

_room.RegisterByteStreamHandler("1", (reader, participantIdentity) => {
    HandleInitialSync(reader, participantIdentity).Forget();
});

private async UniTaskVoid HandleInitialSync(ByteStreamReader reader, string participantIdentity)
{
    var instruction = reader.ReadAll();
    await instruction.ToUniTask();
    var senderId = PlayerIdForIdentity(participantIdentity);
    OnDataReceived?.Invoke(senderId, 1, instruction.Bytes);
}
```

Two receive paths: `DataReceived` for single-packet `PublishData`, `RegisterByteStreamHandler` for stream-based large payloads. The eventCode-to-handler routing is consistent on both sides.

### 3.7 Tests

Add `apps/MakeItSing/Assets/App/Networking/Editor/Tests/LiveKitTransportTests.cs` covering pure logic (no live LiveKit):

- Slot-claim: deterministic resolution under contention. Given a participant list with simulated `JoinedAt` times and partial `slot` attributes, the algorithm picks the right slot. Race-condition cases: two participants claiming slot 1 simultaneously, resolution by `JoinedAt` tiebreak.
- Master election: earliest `JoinedAt` wins, flips correctly when master leaves.
- `IdentityForPlayerId` / `PlayerIdForIdentity` are inverses.

`PhotonSerializationTests.cs` is unchanged — the codec is generic, only the transport is new.

### 3.8 Integration testing on device

This is the time-eating part. Build for both targets and run on real devices:

```bash
uv run compile-unity --project MakeItSing --build android-mobile
uv run compile-unity --project MakeItSing --build magicleap
# adb install -r <printed-apk-path> on each device
```

Test scenarios:
1. Two clients (editor + Android device) join the same room. Avatar appears for each, transforms sync at 16 Hz, grabbing an `XRGrabbable` syncs ownership.
2. Three clients. Late joiner sees full state via initial sync. HF channel doesn't head-of-line-block the incremental diff stream.
3. Master disconnects mid-session. New master elected. State continues to converge. No state loss.
4. Network blip (toggle WiFi on one device). Reconnection works without state corruption.
5. Magic Leap 2 + Android Mobile + Editor — all three platforms in the same room.

Document any platform-specific quirks discovered. Surface them as separate small fix PRs if substantive.

### Exit criteria

- All three event channels work end-to-end on both build targets.
- Master-handoff fix is verified working.
- Slot-claim survives a soak test (10 joins/leaves, slot mapping always consistent across clients).
- `uv run --no-sync preflight` is green.

---

## Phase 4 — Cutover and teardown (half day)

**Goal**: LiveKit becomes the default; Photon is gone.

### 4.1 Flip the default

In `UnityEnv`, `use_livekit` defaults to `true`. Keep the flag for one release cycle as a rollback lever.

### 4.2 Demo

Run a real two-headset demo on LiveKit. Confirm parity with the prior Photon-based demo. If parity is achieved, proceed to 4.3.

### 4.3 Delete Photon

In a single dedicated commit:
- Delete `apps/MakeItSing/Assets/ThirdParty/photon-unity-sdk_v5-1-9/` and its `.meta` files.
- Delete `apps/MakeItSing/Assets/App/Networking/PhotonTransport.cs`.
- Delete the `use_livekit` flag and the dispatch ternary in `AppSetup.cs:325` — instantiate `LiveKitTransport` directly.
- Remove the `photon_project_id` reads from `SupabaseAPI.cs` and from any Supabase config rows (or leave dead in the config table — operational call).

### 4.4 Spec updates

In a separate commit (per the prose-and-code separation rule):

- `apps/MakeItSing/SPEC.md`: rewrite §Replicated scene-graph to reference LiveKit data channels and `INetworkTransport`. Update §Rationale "Raw Photon Realtime over Fusion/PUN" → "LiveKit transport behind `INetworkTransport`." Remove or update the Photon-specific Known Issues entries (master-handoff is fixed, orphan cleanup is still TODO).
- `apps/MakeItSing/CLAUDE.md`: update the "don't fix these" list. Point at the new networking layer path.
- `docker/SPEC.md`: add LiveKit to the service inventory. Document the API token-mint endpoint and the colocalized-LAN deployment model.

### 4.5 Codegen cleanup

If any generated client surface area referred specifically to Photon-related types or settings (unlikely but possible), run `uv run generate-clients` one more time and commit as `Run generate-clients`.

### Exit criteria

- Zero references to "Photon" or "Realtime" in `apps/MakeItSing/Assets/App/`.
- `uv run --no-sync preflight` is green.
- A real two-headset demo runs end-to-end on LiveKit.
- All three SPEC.md / CLAUDE.md files reflect the new state.

---

## Open design questions to resolve during implementation

1. **`SendLargeAsync` interface shape.** Two send methods on the interface vs. one with internal size routing. The two-method approach is clearer; the one-method approach is more uniform. Decide during Phase 2.
2. **Debounce on master flip.** Implement immediately in Phase 3.4, or add only after observing thrash in Phase 3.8 testing? Recommendation: defer until observed.
3. **Identity for guest/anonymous users.** The current plan ties LiveKit identity to Keycloak `sub`. If demos ever need anonymous/guest participation, the API endpoint needs a second path (e.g. generate a per-session UUID identity). Out of scope unless required.
4. **Reconnection state preservation.** When a client reconnects after a network blip, does it re-receive the full initial sync from the master, or does the master remember its state? Current Photon behavior is the former. LiveKit reconnection should match — verify in Phase 3.8.
5. **`SceneObjectId` / `HighFrequencyPrimitiveId` refactor (out of scope).** Whether these should be GUIDs instead of ints is a real question, but the negative-int convention for scene-baked objects is load-bearing for zero-coordination consensus. Refactoring deserves its own PR with Elliot Pjecha (the original author per SPEC.md) in the loop. Don't bundle it into this swap.

---

## Risks and mitigations

| Risk | Probability | Mitigation |
|---|---|---|
| LiveKit Unity SDK quirks on Magic Leap 2 (OpenXR + Android-but-not-quite-Android) | Medium | Phase 0 task 1 includes ML2 verification on the SDK's Basic sample. The SDK has zero Unity-XR coupling and ships an arm64 Android .so. If broken, fall back to building from raw `com.unity.webrtc` against LiveKit's protocol (more work but feasible). |
| SDK is "Developer Preview" per livekit/client-sdk-unity README. APIs may shift; bugs likely. | Medium | Pin to a tagged release in `manifest.json`; transport abstraction limits blast radius. Watch the release notes for breaking changes between Phase 0 and Phase 3. |
| LiveKit license rug-pull mid-implementation | Very low (1-week window) | `INetworkTransport` abstraction means the worst case is "swap implementation behind the same interface" — bounded work. |
| Master-election thrash on flaky WiFi | Low at first, possibly real at demo | Debounce on `OnMasterChanged` (defer until observed). |
| Slot-claim race condition | Low | Deterministic `JoinedAt` tiebreak + unit-tested. |
| Codegen flow breaks | Low | Preflight catches it. If it breaks, the API-side change is small and easily reverted. |
| Photon retains some hidden dependency we haven't found | Low | The audit was thorough, but Phase 2 will surface anything missed via compilation errors. |
| Initial-sync payload exceeds the stream API's practical limits | Very low | LiveKit's data streams have no documented upper bound. If observed, split scenes. |

---

## Timeline

| Phase | Effort | Cumulative |
|---|---|---|
| 0 — Spike | 0.5 day | 0.5 day |
| 1 — Backend infra | 0.5 day | 1 day |
| 2 — Transport abstraction | 0.5 day | 1.5 days |
| 3 — LiveKit transport | 2-4 days | 3.5-5.5 days |
| 4 — Cutover | 0.5 day | 4-6 days |

**Total: ~1 week of focused work, single engineer.** Phase 3 is the only one with real variance — bounded by how cooperative the LiveKit Unity SDK is on Magic Leap 2. If the SDK works first-try on ML2, the project lands at the low end. If there's a platform quirk to discover and work around, the high end.

Phases 1 and 2 can run in parallel if two engineers are available — Phase 1 doesn't touch Unity, Phase 2 doesn't touch docker.

## Commit hygiene

Per `CLAUDE.md` rules:
- Source code and prose changes go in separate commits.
- Codegen artifacts go in their own commit with message `Run generate-clients`.
- One commit per phase (or per logical sub-step within Phase 3), not one mega-commit at the end.
- No `Co-Authored-By` trailers.

## Open questions for the user before starting

1. Is anonymous/guest LiveKit access ever needed for demos? (Affects Phase 1.2 identity sourcing.)
2. Is voice/audio plumbing wanted in this PR or a follow-up? (Default: follow-up.)
3. Should the `use_livekit` flag survive past Phase 4, or be deleted immediately in 4.3? (Default: delete in 4.3 since rollback is `git revert`.)
4. Confirm the target deployment for the initial 12-headset demo: same-LAN colocalized, or some participants remote? (Affects whether ngrok-UDP work is needed.)
