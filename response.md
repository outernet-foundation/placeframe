# Plan: Swap Photon → LiveKit

## Verdict shape

This is **four phases of work over ~2-3 focused weeks**, structured so each phase merges cleanly without breaking the existing Photon flow until the very end. The cutover is gated behind a single feature flag (`UnityEnv.use_livekit`) so the swap can be A/B-tested against the same demo scene before Photon is removed.

The key architectural commitment is **Phase 2's `INetworkTransport` interface**. Everything else falls out of it: LiveKit becomes one implementation, Photon stays as the working baseline, and any future swap (Nakama, raw WebRTC, NATS) becomes a sibling class rather than a rewrite.

---

## Phase 0 — Spike (1 day)

Before committing to the plan, verify the two unknowns the research couldn't resolve:

1. **LiveKit `client-sdk-unity` data-channel surface**. Open the Unity SDK, write a 50-line harness that connects two clients to a localhost LiveKit container and round-trips a `PublishData(payload, RELIABLE|LOSSY, destinationIdentities, topic)` call. Confirm: (a) topic field survives the round-trip cleanly, (b) `destinationIdentities` actually targets vs. broadcasts, (c) the LOSSY/UNRELIABLE channel is genuinely separate from the RELIABLE one (not head-of-line-blocking each other).
2. **Ngrok UDP story for media**. LiveKit signaling rides WebSocket (works through ngrok); media wants UDP (doesn't). Confirm whether LiveKit's `tcp_port` fallback works end-to-end through ngrok, or whether external deployments need a separate non-ngrok ingress. For LAN-only colocalized testing this doesn't matter; for any remote demo it does.

If either spike reveals a blocker, return to the architecture discussion. Otherwise proceed.

---

## Phase 1 — Backend infrastructure (3-4 days)

Goal: a running LiveKit service in `uv run up`, with a Placeframe-API endpoint that mints LiveKit JWTs for authenticated callers.

### 1.1 LiveKit container

**New service in `/placeframe/compose.yml`**:

```yaml
livekit:
  image: ${LIVEKIT_IMAGE:?err}  # pinned digest from .env.lock
  environment:
    LIVEKIT_KEYS: "${LIVEKIT_API_KEY:?err}: ${LIVEKIT_API_SECRET:?err}"
    LIVEKIT_PORT: "7880"
    LIVEKIT_RTC_TCP_PORT: "7881"
    LIVEKIT_RTC_UDP_PORT_RANGE_START: "50000"
    LIVEKIT_RTC_UDP_PORT_RANGE_END: "50100"
  ports:
    - "7880:7880"           # WebSocket signaling
    - "7881:7881"           # RTC TCP fallback
    - "50000-50100:50000-50100/udp"  # RTC media/data UDP range
  healthcheck:
    test: ["CMD", "wget", "-qO-", "http://localhost:7880/"]
    interval: 10s
    timeout: 3s
    retries: 5
  restart: unless-stopped
```

**Image pinning**: per `CLAUDE.md` rule, no `:latest`. Pick a current LiveKit release (e.g. `v1.7.x`), resolve its digest via `docker buildx imagetools inspect docker.io/livekit/livekit-server:v1.7.X`, write the `image@sha256:...` ref into `.env.lock` keyed on `LIVEKIT_IMAGE`. Update `scripts/src/scripts/context_sha.py` or wherever digests are tracked if there's an automated process.

**No Postgres tables needed.** Single-node LiveKit holds room state in memory. Multi-node would need Redis, but you're nowhere near that scale.

**No new gateway routes needed for local-only.** For external (ngrok) exposure: add a Caddy route in `/placeframe/docker/gateway/entrypoint.sh` proxying `wss://${PUBLIC_DOMAIN}/livekit` → `ws://livekit:7880`. Media stays on direct UDP and is only reachable on LAN — fine for the colocalized-headsets use case.

### 1.2 Token-mint endpoint

**New file `/placeframe/docker/api/src/routers/livekit.py`** (mirrors existing router pattern from `leases.py`, `localization.py`):

```python
from datetime import timedelta
from typing import Annotated

import jwt
from litestar import Controller, post
from litestar.params import Body
from pydantic import BaseModel

from ..settings import Settings

class LiveKitTokenRequest(BaseModel):
    room: str
    identity: str

class LiveKitTokenResponse(BaseModel):
    token: str
    url: str

class LiveKitController(Controller):
    path = "/livekit"

    @post("/token")
    async def mint_token(
        self,
        data: Annotated[LiveKitTokenRequest, Body()],
        settings: Settings,
    ) -> LiveKitTokenResponse:
        now = int(time.time())
        claims = {
            "iss": settings.livekit_api_key,
            "sub": data.identity,
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
        return LiveKitTokenResponse(token=token, url=settings.livekit_url)
```

Token validation is implicit: the existing `AuthMiddleware` (`docker/api/src/auth.py:36-96`) already gates this endpoint behind a valid Keycloak token. The `identity` claim should be sourced from the Keycloak `sub` rather than trusted from the request body — refactor accordingly during implementation. (Listed as an open question below.)

**Settings additions** in `docker/api/src/settings.py`:
```python
livekit_api_key: str
livekit_api_secret: str
livekit_url: str  # e.g. "ws://livekit:7880" inside compose, "wss://${PUBLIC_DOMAIN}/livekit" externally
```

**Wire it up** in `docker/api/src/main.py` alongside the other routers (around lines 82-98 per the audit).

### 1.3 Env scaffolding

Add to `.env.sample`:
```
LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=devsecretmustbeatleast32charslongforhmacsha256
LIVEKIT_URL=ws://livekit:7880
```

Add to `.env.lock` (populated by digest resolution):
```
LIVEKIT_IMAGE=docker.io/livekit/livekit-server@sha256:...
```

### 1.4 Codegen

After 1.1–1.3 land: `uv run generate-clients --project docker/api`. The new endpoint flows automatically into `packages/generated/csharp/api-client/` as `PostLivekitTokenAsync()` per the existing flow. Commit the codegen artifacts in a separate `Run generate-clients` commit per the repo's codegen hygiene rule.

### 1.5 Preflight check

`uv run --no-sync preflight` should pass with the new service running. If it doesn't, fix before continuing — don't accumulate broken CI debt across phases.

**Phase 1 exit criteria**:
- `uv run up` starts LiveKit alongside the other services.
- `curl -X POST http://localhost/api/livekit/token -H "Authorization: Bearer $KEYCLOAK_TOKEN" -d '{"room":"test","identity":"alice"}'` returns a valid JWT.
- `pnpm` test harness from Phase 0 (or a Python script using `livekit-server-sdk`) successfully connects to `ws://localhost:7880` with the minted token.

---

## Phase 2 — Transport abstraction (2-3 days)

Goal: a Unity-side `INetworkTransport` interface, with the existing Photon code refactored into a `PhotonTransport` implementation behind it. Zero behavior change — this is pure structural prep.

### 2.1 Interface design

**New file `apps/MakeItSing/Assets/App/Networking/INetworkTransport.cs`**:

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

    event Action<int, byte, byte[]> OnDataReceived;       // (senderId, eventCode, payload)
    event Action<int> OnPlayerJoined;
    event Action<int> OnPlayerLeft;
    event Action<int> OnMasterChanged;                    // new master's playerId
    event Action OnDisconnected;
}
```

This interface is the entire contract `AppActions.cs` and the sync streams need from the network layer. Anything Photon-specific that doesn't fit here (e.g. region selection, Photon-event-cache flags) is intentional dead weight that gets dropped.

### 2.2 `PhotonTransport` implementation

Move the contents of `Assets/App/Managers/PhotonConnectionManager.cs` into `Assets/App/Networking/PhotonTransport.cs`. Renames:

- `OpRaiseEvent(code, payload, options)` → `Send(code, payload, reliability, targetPlayerId)`.
- `OnEvent` callback → fires `OnDataReceived` event.
- `OnPlayerEnteredRoom` / `OnPlayerLeftRoom` → fire `OnPlayerJoined` / `OnPlayerLeft`.
- `OnMasterClientSwitched` → fire `OnMasterChanged`.
- `LocalPlayer.ActorNumber` → `LocalPlayerId`.

The state-diff stream, ID-slicing, JSON-initial-sync, and binary-codec logic in `AppActions.cs` does **not** change in this phase. They consume `INetworkTransport` events instead of Photon callbacks; that's it.

### 2.3 Wire it through `AppSetup`

`AppSetup.cs:325`-ish (where `PhotonConnectionManager` is added today): replace with a transport-provider dispatch:

```csharp
INetworkTransport transport = UnityEnv.use_livekit
    ? gameObject.AddComponent<LiveKitTransport>()  // stub in Phase 2; real impl in Phase 3
    : gameObject.AddComponent<PhotonTransport>();
```

`UnityEnv.use_livekit` defaults to `false`. The LiveKit transport in this phase is a no-op stub that throws on `ConnectAsync` — it exists so the dispatch compiles and the runtime guard is in place.

### 2.4 Verify

`uv run compile-unity --project MakeItSing --build android-mobile` succeeds. Manual smoke test: two clients in editor + on-device join a Photon room, behavior identical to pre-refactor.

**Phase 2 exit criteria**:
- Photon flow is 100% behind `INetworkTransport`.
- `PhotonSerializationTests.cs` still passes (codec unchanged).
- No reference to `PhotonConnectionManager` or `Photon.Realtime` types exists outside `PhotonTransport.cs`.

---

## Phase 3 — LiveKit transport implementation (4-6 days)

Goal: a working `LiveKitTransport : INetworkTransport`. Setting `UnityEnv.use_livekit = true` produces the same observable behavior as Photon.

### 3.1 SDK install

Add LiveKit Unity SDK to `apps/MakeItSing/Packages/manifest.json` (or NuGet equivalent — check whether LiveKit ships as UPM, NuGet, or both for the current Unity version). Pin a specific release.

### 3.2 Connection flow

`LiveKitTransport.ConnectAsync(roomId, ct)`:
1. Call the generated `PlaceframeApiClient.PostLivekitTokenAsync(new() { Room = roomId, Identity = $"player-{Guid.NewGuid()}" })`. The `AuthHttpHandler` (`packages/unity/Placeframe/Assets/Package/Core/Runtime/Auth.cs:10-21`) attaches the Keycloak token automatically.
2. From the response, get `token` and `url`.
3. `await _room.Connect(url, token)`.
4. On success, populate `LocalPlayerId` (see 3.3).
5. Subscribe to LiveKit room events; map them onto `INetworkTransport` events.

### 3.3 Player ID mapping

LiveKit identities are strings. The path-as-schema model needs stable small integers for the `playerId * 10000` slicing in `PlayerIdHelper`.

Strategy: deterministic mapping from sorted participant identities. On any participant join/leave:
1. Take all current participants (including self), sort by `joinedAt` (LiveKit exposes this on `Participant`).
2. The local player's index in that sorted list is `LocalPlayerId`.
3. Same logic for remote: `playerId(remote) = index in sorted list`.

Caveat: this means a participant's `playerId` can *change* mid-session when an earlier-joined participant leaves. The current Photon code assumes `playerId` is stable for the session lifetime. **Two options**:
- **(a) Sticky IDs**: on first join, each participant claims the lowest unused integer and broadcasts it as a custom participant-attribute. Stable across the participant's own session, freed on leave. More code, matches Photon semantics.
- **(b) Reassign-on-change**: accept that `playerId` can shift, and surface `OnPlayerIdChanged` events. The state tree's `ownerID` field gets remapped accordingly. Less code, more invariants to audit.

**Recommend (a)** — it matches the existing assumption, and a participant-attribute write is cheap. Flag this as a design call in the implementation PR.

### 3.4 Master election

On any participant join/leave, the participant with the earliest `joinedAt` is master. Fire `OnMasterChanged` when this flips. This is *better* than current Photon behavior (where `OnMasterClientSwitched` only logs, per SPEC.md "Known issues" line 13-15). Implementing master-handoff correctly here closes a known latent bug — call this out in the PR.

### 3.5 Send / receive mapping

```csharp
public void Send(byte eventCode, byte[] payload, DeliveryReliability reliability, int? targetPlayerId = null)
{
    var kind = reliability == DeliveryReliability.Reliable
        ? DataPacketKind.RELIABLE
        : DataPacketKind.LOSSY;

    string[] destinations = targetPlayerId.HasValue
        ? new[] { IdentityForPlayerId(targetPlayerId.Value) }
        : null;  // null = broadcast

    _room.LocalParticipant.PublishData(payload, kind, destinations, topic: eventCode.ToString());
}
```

Receive: subscribe to `_room.DataReceived`, parse `topic` back to byte, look up sender identity → playerId, fire `OnDataReceived(senderId, eventCode, payload)`.

### 3.6 Initial-sync chunking

The Code-1 initial-sync payload is `App.state.scene` serialized as JSON. LiveKit's reliable channel caps at ~15 KiB; the JSON for non-trivial scenes can exceed this. Add a chunking layer:

```
[sequenceNumber : u8][totalChunks : u8][chunkData : bytes]
```

The receiver buffers chunks by sender identity until `sequenceNumber + 1 == totalChunks`, then concatenates and dispatches as one `OnDataReceived(senderId, 1, fullPayload)` event. Chunk size ~12 KiB to leave headroom for LiveKit framing.

The Code-2 (incremental diff) and Code-3 (HF pose) payloads already fit in one packet — no chunking needed.

### 3.7 Tests

Add `apps/MakeItSing/Assets/App/Networking/Editor/Tests/LiveKitTransportTests.cs`:
- Identity-to-playerId mapping correctness (deterministic for any participant list).
- Master-election: earliest-joinedAt wins, flips correctly on leave.
- Initial-sync chunk reassembly.

These are unit tests; no live LiveKit needed. The `PhotonSerializationTests` continue to cover the binary codec.

### 3.8 Manual integration test

With `UnityEnv.use_livekit = true`:
1. Spin up `uv run up`.
2. Run two MakeItSing clients (editor + Android device, or two devices).
3. Join the same room. Confirm: avatar appears, moves smoothly (HF channel works), grabbing a `XRGrabbable` syncs (incremental channel works), late-joiners see existing state (initial-sync works).
4. Disconnect the master mid-session. Confirm: new master elected, state continues to converge.

**Phase 3 exit criteria**:
- `UnityEnv.use_livekit = true` produces feature-parity with Photon.
- Master-handoff actually works (improvement over current Photon).
- Manual two-client and three-client scenarios pass.

---

## Phase 4 — Cutover and teardown (1-2 days)

Goal: LiveKit becomes the default; Photon code and SDK are deleted.

### 4.1 Flip the default

`UnityEnv.use_livekit` defaults to `true`. Keep the flag for one or two release cycles in case rollback is needed.

### 4.2 Delete Photon

After a successful demo on LiveKit:
- Delete `apps/MakeItSing/Assets/ThirdParty/photon-unity-sdk_v5-1-9/`.
- Delete `PhotonTransport.cs`.
- Delete the `use_livekit` flag and the dispatch in `AppSetup.cs`.
- Remove `photon_project_id` from Supabase config rows (or leave dead — pick one).
- Rename `Assets/App/Serialization/PhotonSerialization.cs` → `BinarySerialization.cs`. Update `PhotonSerializationTests.cs` accordingly. (The codec is generic; only the name was Photon-flavored.)

### 4.3 Spec updates

Update `apps/MakeItSing/SPEC.md`:
- Rewrite §Replicated scene-graph to reference LiveKit data channels instead of Photon `OpRaiseEvent`.
- Update §Rationale "Raw Photon Realtime over Fusion/PUN" → "LiveKit transport behind `INetworkTransport`."
- Remove the Photon-specific "Known issues" entries (master-handoff, orphan cleanup) — these get fixed or re-filed as LiveKit-specific.

Update `docker/SPEC.md` to add LiveKit to the service inventory.

Update `apps/MakeItSing/CLAUDE.md` to point at the new networking layer.

Per `CLAUDE.md`'s prose-and-code-separately rule: spec and CLAUDE.md updates go in a separate commit from the code teardown.

**Phase 4 exit criteria**:
- Zero references to "Photon" in `apps/MakeItSing/Assets/App/`.
- `uv run --no-sync preflight` is green.
- A two-headset demo runs end-to-end on LiveKit.

---

## Open questions to resolve during implementation

1. **Token identity sourcing**: should the `/livekit-token` endpoint derive `identity` from the Keycloak `sub` claim (server-trusted) or accept it from the request body (client-trusted)? Recommend server-trusted; flag any flow that requires client-provided identity.
2. **Sticky vs. recomputed playerId** (Phase 3.3): probably (a) sticky. Decide in the PR review.
3. **External media exposure**: if remote (non-LAN) participants are needed before the colocalized use case ships, the ngrok-UDP problem needs a real answer. Options: dedicated host with static IP + direct UDP exposure, or a TURN server (coturn) alongside LiveKit. Defer until needed.
4. **Voice/audio roadmap**: if voice is in the next 6-12 months, plumb the LiveKit audio publish path now (it's ~50 lines) so the SFU stays warm. If not, leave it for later.
5. **Multi-node scaling**: not needed for 12 headsets. Single-node LiveKit handles thousands of participants. If you hit scale, add Redis + multi-node config; no app-side changes.

---

## Timeline

| Phase | Effort | Calendar |
|---|---|---|
| 0 — Spike | 1 day | Day 1 |
| 1 — Backend infra | 3-4 days | Days 2-5 |
| 2 — Transport abstraction | 2-3 days | Days 6-8 |
| 3 — LiveKit transport | 4-6 days | Days 9-14 |
| 4 — Cutover | 1-2 days | Days 15-16 |

**Total: ~2-3 weeks of focused engineering**, sequential, one engineer. The phases are independent enough that Phase 1 (backend) and Phase 2 (Unity refactor) could run in parallel if two engineers are available — Phase 1 doesn't touch Unity, Phase 2 doesn't touch docker.

## Risks

- **Phase 0 spike fails**: the SDK doesn't expose targeted send / topic round-trip cleanly. Fallback: implement targeting in user-space (broadcast with target-id header, drop on receive if not for us). Adds bandwidth waste but unblocks.
- **LiveKit license rug-pull mid-project**: low probability over 2-3 weeks but non-zero. The `INetworkTransport` interface is the insurance — swap implementation, keep the contract.
- **Master-election thrash**: if join/leave is noisy (e.g. flaky WiFi at a demo), the master can flip rapidly. Add a debounce (e.g. 500ms stabilization before honoring a master change). Defer until observed.
- **Initial-sync chunking edge cases**: if a chunk is dropped on the reliable channel (shouldn't happen, but…) the receiver hangs forever waiting for the rest. Add a timeout + retry-request protocol if observed in practice. Defer until needed.
