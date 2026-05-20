# Phase 5 — Transport abstraction

## Context

The MakeItSing Unity app currently uses Photon Realtime via `Assets/App/Managers/PhotonConnectionManager.cs` (~530 lines) for multiplayer state replication. We are eventually swapping Photon for LiveKit. **This phase does not introduce LiveKit.** It only:

1. Introduces a thin `INetworkTransport` C# interface.
2. Moves the existing Photon code behind that interface as `PhotonTransport`.
3. Adds a `LiveKitTransport` stub that throws on `ConnectAsync` (so the dispatch logic compiles).
4. Adds a `UnityEnv.use_livekit` flag (default `false`) that selects which implementation `AppSetup` instantiates.

Zero behavior change. With `use_livekit = false`, the app must behave identically to its pre-refactor state.

Read `/placeframe/CLAUDE.md` and `/placeframe/apps/MakeItSing/CLAUDE.md` before starting. Especially:
- **Don't fix these list** in `apps/MakeItSing/CLAUDE.md` — some "obvious" issues are intentional load-bearing absences. Respect them.
- **MakeItSing is co-authored with Elliot Pjecha.** Non-trivial structural changes need coordination. This phase is a mechanical refactor (renames and event re-wiring) — that's in-scope. Anything beyond that is not.
- **UniTask, not `Task.Run`.** This codebase uses `Cysharp.Threading.Tasks` everywhere.
- **Serilog message templates, not interpolated strings.** Every log call uses `{PascalCase}` placeholders and separate args.
- **No docstrings, no inline imports, no temporal language in comments.**

Phase 5 has no strict technical dependency on Phases 1–4 — the refactor only touches existing Photon code and adds a `LiveKitTransport` stub that throws. Pragmatically, you wouldn't spend the refactor effort if the Phase 3 spike hadn't passed, but the file changes themselves are LiveKit-independent. Phase 6 will invoke the generated `PostLivekitToken` client method (produced in Phase 4), but this phase only wires up the dispatch so Phase 6 can drop the real implementation in without touching `AppSetup`.

## Goal

After this phase:
- `apps/MakeItSing/Assets/App/Networking/INetworkTransport.cs` defines the transport contract.
- `apps/MakeItSing/Assets/App/Networking/PhotonTransport.cs` is the moved/renamed `PhotonConnectionManager` implementing `INetworkTransport`.
- `apps/MakeItSing/Assets/App/Networking/LiveKitTransport.cs` is a stub MonoBehaviour implementing `INetworkTransport` that throws `NotImplementedException` on `ConnectAsync`.
- `AppSetup.cs` instantiates one or the other based on `UnityEnv.use_livekit`.
- `UnityEnv.use_livekit` exists and defaults to `false`.
- All state-replication code (`AppActions.cs` and friends) consumes `INetworkTransport` events instead of Photon-typed callbacks.
- No reference to `Photon.Realtime` types exists outside `PhotonTransport.cs`.
- `uv run compile-unity --project MakeItSing --build android-mobile` succeeds.
- The Photon flow still works end-to-end exactly as before (the user will verify this on devices; you cannot verify it from a Claude Code session).

## The interface

Create `apps/MakeItSing/Assets/App/Networking/INetworkTransport.cs`:

```csharp
namespace App.Networking;

public enum DeliveryReliability
{
    Reliable,
    Unreliable,
}

public interface INetworkTransport
{
    bool IsConnected { get; }
    bool IsMaster { get; }
    int LocalPlayerId { get; }
    IReadOnlyList<int> ConnectedPlayerIds { get; }

    UniTask ConnectAsync(string roomId, CancellationToken cancellationToken);
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

Adjust the namespace to match the project's convention if it isn't file-scoped namespaces elsewhere. Match the `using` style used in adjacent `Assets/App/` files. `byte[]` here is the canonical type Photon already uses; don't switch to `ReadOnlyMemory<byte>` mid-refactor.

Rationale for **two send methods**:
- `Send` carries single-packet payloads — under ~12 KiB after framing. Covers incremental diffs and HF pose updates.
- `SendLargeAsync` carries arbitrarily-sized payloads. In `PhotonTransport`, route this through the same `OpRaiseEvent` reliable path Photon already uses for initial sync — Photon's max payload size is per-event-buffer-tuned and the existing code handles it. In `LiveKitTransport` (Phase 6), this becomes a chunked stream via LiveKit's `StreamBytes` API. The chunking concern goes away in Phase 7 when Photon is deleted.

## Move PhotonConnectionManager → PhotonTransport

`apps/MakeItSing/Assets/App/Managers/PhotonConnectionManager.cs` → `apps/MakeItSing/Assets/App/Networking/PhotonTransport.cs`. Also move its `.meta` file so Unity GUIDs survive. Rename the class to `PhotonTransport`. Mechanical mappings:

| Photon API | Interface |
|---|---|
| `OpRaiseEvent(code, payload, options)` | `Send(code, payload, reliability, targetPlayerId)` — bool/enum maps onto the `RaiseEventOptions.Receivers` + `SendOptions.Reliability` Photon parameters |
| `OpRaiseEvent` (initial-sync-large path) | `SendLargeAsync(code, payload, targetPlayerId)` — same Photon path, just exposed under a UniTask return |
| `OnEvent` callback | fire `OnDataReceived(senderId, code, payload)` |
| `OnPlayerEnteredRoom` | fire `OnPlayerJoined(playerId)` |
| `OnPlayerLeftRoom` | fire `OnPlayerLeft(playerId)` |
| `OnMasterClientSwitched` | fire `OnMasterChanged(newMasterPlayerId)` (still buggy in Photon — known issue per `apps/MakeItSing/SPEC.md`; do not attempt to fix here, fix lives in Phase 6's master election) |
| `LocalPlayer.ActorNumber` | `LocalPlayerId` |
| `CurrentRoom.Players.Keys` | `ConnectedPlayerIds` |
| `PhotonNetwork.IsConnected` | `IsConnected` |
| `PhotonNetwork.IsMasterClient` | `IsMaster` |

`PhotonTransport` stays a `MonoBehaviour` (Photon's callback interface registration is gameObject-component-based). The interface doesn't mandate `MonoBehaviour`, but both implementations will be `MonoBehaviour` for AppSetup's `AddComponent` pattern — leave that as-is.

`OpRaiseEvent`'s `targetActors` array maps directly from `targetPlayerId.HasValue ? new[] { targetPlayerId.Value } : null`. For broadcast (`targetPlayerId == null`), use Photon's `ReceiverGroup.All` (or whichever the existing code uses — match exactly).

The state-diff stream code in `AppActions.cs` (and anywhere else that subscribes to `PhotonConnectionManager`'s events) must now subscribe to the `INetworkTransport` events instead. The signatures should already match (Photon callbacks already pass `(int senderId, byte eventCode, byte[] payload)` after the existing wrapper code unpacks the `EventData`). If there's incidental impedance, write minimum-touch adapter code on the consumer side, not on the `INetworkTransport` side — the interface shape is the contract.

`PhotonSerialization.cs` is a transport-agnostic binary codec (despite the name). **Do not touch it.** It serializes the diff format; the transport carries the serialized bytes. The name will keep the `Photon` prefix; renaming it is a cosmetic separate concern.

## LiveKitTransport stub

Create `apps/MakeItSing/Assets/App/Networking/LiveKitTransport.cs`:

```csharp
using System;
using System.Collections.Generic;
using System.Threading;
using Cysharp.Threading.Tasks;
using UnityEngine;

namespace App.Networking;

public class LiveKitTransport : MonoBehaviour, INetworkTransport
{
    public bool IsConnected => false;
    public bool IsMaster => false;
    public int LocalPlayerId => 0;
    public IReadOnlyList<int> ConnectedPlayerIds { get; } = Array.Empty<int>();

    public event Action<int, byte, byte[]>? OnDataReceived;
    public event Action<int>? OnPlayerJoined;
    public event Action<int>? OnPlayerLeft;
    public event Action<int>? OnMasterChanged;
    public event Action? OnDisconnected;

    public UniTask ConnectAsync(string roomId, CancellationToken cancellationToken) =>
        throw new NotImplementedException("LiveKitTransport is implemented in Phase 6.");

    public UniTask DisconnectAsync() => UniTask.CompletedTask;

    public void Send(byte eventCode, byte[] payload, DeliveryReliability reliability, int? targetPlayerId = null) =>
        throw new NotImplementedException("LiveKitTransport is implemented in Phase 6.");

    public UniTask SendLargeAsync(byte eventCode, byte[] payload, int? targetPlayerId = null) =>
        throw new NotImplementedException("LiveKitTransport is implemented in Phase 6.");
}
```

The unused-event warnings (`OnDataReceived` etc. never raised) are intentional — Phase 6 fills them in. If the project's nullable-event style differs (some C# codebases use `event ... = delegate { }` to avoid null-check), match the surrounding code.

## Dispatch in AppSetup

At `apps/MakeItSing/Assets/App/AppSetup.cs:325` (where `PhotonConnectionManager` is added today — grep `gameObject.AddComponent<PhotonConnectionManager>` or similar to confirm the exact line), replace:

```csharp
INetworkTransport transport = UnityEnv.use_livekit
    ? gameObject.AddComponent<LiveKitTransport>()
    : gameObject.AddComponent<PhotonTransport>();
```

Match the existing variable name / field-assignment pattern around that line. If the surrounding code stores the manager in a field like `_photonManager`, rename that field to `_transport` (typed as `INetworkTransport`) and update every reference. Don't leave both names around for "compatibility" — that violates the "no backwards-compat shims" rule in CLAUDE.md.

## UnityEnv flag

Add `use_livekit: bool` (default `false`) to wherever `UnityEnv` lives. Grep for it (`grep -r "UnityEnv\." apps/MakeItSing/Assets/`) to find the declaration and match the existing flag conventions. If other flags are in an `.env`-style file rather than C# source, follow that pattern.

## Verify

```bash
uv run compile-unity --project MakeItSing --build android-mobile
```

Must succeed. The dispatch ternary compiles, `PhotonTransport` is wired up, the codec is unchanged.

`PhotonSerializationTests.cs` should still pass (the codec wasn't touched). Run via whatever test runner the project uses — `uv run compile-unity` won't run editor tests; if a separate test entry point exists, invoke it. If there isn't one, note this in the PR description as "tests will be re-run with Phase 6's additions."

**Behavioral verification cannot happen from a Claude Code session.** State in the PR description that the user must smoke-test on two clients (editor + device) with `use_livekit = false` and confirm Photon behavior is identical to pre-refactor. Do not claim "verified working" — claim "compiles, awaiting device verification."

## Commit hygiene

Code-only changes here; no prose changes expected. One commit covering:
- The new `INetworkTransport.cs`
- The renamed/moved `PhotonTransport.cs` (+ its `.meta`)
- The stub `LiveKitTransport.cs` (+ `.meta`)
- The `AppSetup.cs` dispatch change
- Any consumer-side event-subscription updates in `AppActions.cs` and elsewhere
- The `UnityEnv` flag addition

If the project keeps separate `.asmdef` files and adding a new `Networking/` folder requires an `Assets/App/Networking/Networking.asmdef`, include that in the same commit — it's structurally tied to the new folder.

No prose updates in this phase. `apps/MakeItSing/SPEC.md` updates land in Phase 7 (the "Known issues" master-handoff entry isn't resolved yet, so updating the spec now would mislead readers).

No `Co-Authored-By` trailers. No `--no-verify`. No codegen runs here — this phase doesn't touch the OpenAPI spec.

## Exit criteria

- `apps/MakeItSing/Assets/App/Networking/` contains `INetworkTransport.cs`, `PhotonTransport.cs`, `LiveKitTransport.cs` (+ `.meta`).
- `apps/MakeItSing/Assets/App/Managers/PhotonConnectionManager.cs` no longer exists.
- `grep -r "Photon\.Realtime" apps/MakeItSing/Assets/App/ | grep -v "Networking/PhotonTransport.cs"` returns nothing. (Photon SDK files under `Assets/ThirdParty/` are not part of `App/` and are out of scope until Phase 7.)
- `uv run compile-unity --project MakeItSing --build android-mobile` succeeds.
- The state-replication code subscribes to `INetworkTransport` events.
- `UnityEnv.use_livekit` exists and defaults to `false`.
- Single source-code commit. No prose changes. No codegen.

## Out of scope

- Anything LiveKit-actual (real SDK integration, slot-claim, master election, send/receive mappings) — Phase 6.
- Renaming `PhotonSerialization.cs` — kept as-is.
- Fixing the master-handoff bug — fix lives in Phase 6's master election.
- Deleting Photon SDK or `PhotonTransport.cs` — Phase 7.
- SPEC/CLAUDE.md prose updates — Phase 7.
