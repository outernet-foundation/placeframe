# Phase 2 — ML2 + Android Mobile SDK smoke spike

## Context

Phase 1 stood up the LiveKit server in compose. This phase verifies that the LiveKit Unity SDK actually works on **Magic Leap 2** at runtime before we commit to the rest of the swap. ML2 is the riskiest platform: arm64 Android 10 with a stripped-down AOSP runtime, OpenXR-backed XR rendering, and possible network-stack quirks XR devices sometimes ship with.

**This is the only throwaway phase.** Most artifacts produced here are deleted after the spike passes. The exception is the LiveKit Unity SDK pin in `apps/MakeItSing/Packages/manifest.json` — that's small, useful, and carries forward to Phase 5.

Calibrated odds the spike kills the LiveKit approach:
- `.so` loading on ML2: ~15-20%. ML2's AOSP-derived runtime is mostly standard, but stripped builds sometimes drop libraries the SDK assumes.
- ICE traversal on ML2: ~5-10%. Should work over LAN with no NAT, but XR devices occasionally ship hardened network policies that block raw UDP.
- Data-channel under XR rendering load: <2%. WebRTC offloads to FFI worker threads; ~16 events/sec of a few hundred bytes is negligible. Included for completeness only.

Composite odds: ~20-25% the spike fails. ~10% it fails in a way we can't trivially work around.

What "validation" means concretely: deploy a Unity scene with one button that calls `Room.Connect(url, token)`, sends one byte, receives one byte back, and logs both events. Run on ML2 and Android Mobile against the Phase 1 LiveKit server. Read `adb logcat` to confirm.

Read `/placeframe/CLAUDE.md` and `/placeframe/apps/MakeItSing/CLAUDE.md` before starting. Especially the **"don't fix these" list** in `apps/MakeItSing/CLAUDE.md` — some "obvious" issues are intentional load-bearing absences. The spike scene is a self-contained throwaway under `Assets/_LiveKitSpike/` and touches none of the existing networking code.

## Goal

After this phase, you have a binary answer to:
- Does the LiveKit Unity SDK's native `.so` load and initialize on Magic Leap 2 at runtime?
- Can a `Room.Connect()` against the Phase 1 LiveKit server complete on ML2 over the local WiFi?
- Can a byte round-trip ML2 → server → ML2 (echoed by an Android-Mobile counterparty or a Python echo bot)?

Pass: proceed to Phase 3 (the rest of the backend) and Phase 4 (the abstraction layer) in either order. Fail: stop, document the failure mode and logcat, and re-evaluate the LiveKit decision before doing more work.

## Work

### 1. Pin the LiveKit Unity SDK in MakeItSing's manifest

Check whether the SDK ships via UPM Git URL, OpenUPM, or NuGet for the project's Unity version. Look at `apps/MakeItSing/Packages/manifest.json` and `apps/MakeItSing/Assets/packages.config` to see which dependency style is preferred for new additions. Match it.

Pin to a specific release tag from <https://github.com/livekit/client-sdk-unity/releases>. The SDK is "Developer Preview" — an unpinned ref is unsafe.

**This pin is committed.** It carries forward to Phase 5. The rest of Phase 2's artifacts are uncommitted/throwaway.

### 2. Smoke scene

Create `apps/MakeItSing/Assets/_LiveKitSpike/` (the underscore prefix sorts to top and clearly marks it throwaway). Add:

- `SmokeScene.unity` — a scene asset with a single Canvas + Button + Text component.
- `SmokeScene.cs` — the MonoBehaviour wiring. ~50–80 lines.

The scene's logic, end-to-end:

```
On Awake:
  Read LIVEKIT_URL and LIVEKIT_TOKEN from hardcoded constants (or a JSON Resources file).
  Display them on the UI Text for diagnostic confirmation.

On Button.Click:
  Create a new Room.
  Subscribe to room.DataReceived: append "RECV: <bytes>" to UI Text.
  Subscribe to room.Disconnected: append "DISCONNECTED" to UI Text.
  await room.Connect(url, token).ToUniTask() — append "CONNECTED <identity>".
  Wait 250ms (let SFU register subscription).
  room.LocalParticipant.PublishData(bytes: [0x01, 0x02, 0x03], reliable: true, topic: "smoke").
  Log every step with Serilog message templates (constant template + {Named} placeholders, never $-interpolation).
```

Important details:

- Use `UniTask` everywhere (`Cysharp.Threading.Tasks`); never `Task.Run`. Wrap LiveKit SDK `YieldInstruction` returns with `.ToUniTask()`.
- Log with Serilog using a NetworkSpike or similar `LogGroup`. Use constant templates with `{PascalCase}` placeholders.
- The scene must be added to `Build Settings` (or `ProjectSettings/EditorBuildSettings.asset`) as the active build scene, so a smoke APK boots into it. **Do this on a separate uncommitted branch state** — don't ship a build settings change into mainline.

The two hardcoded values per device are:
- `LIVEKIT_URL = "ws://<lan-ip>:7880"` — your LAN IP, identified at run time.
- `LIVEKIT_TOKEN = "<JWT>"` — pre-minted, see §3.

Two separate APKs get built (one for each device) with distinct hardcoded identities baked into the tokens. Alternative: a single APK with a text input for the URL+token. Hardcoding is simpler for a throwaway.

### 3. Mint JWTs

Tokens are minted out-of-band with a tiny Python script (not the API endpoint — that's Phase 3's work, not needed here). Use `PyJWT` directly:

```python
import jwt
import time

API_KEY = "devkey"  # match LIVEKIT_API_KEY in .env
API_SECRET = "devsecretmustbeatleast32charslongforhmacsha256"  # match .env

def mint(identity: str, room: str = "smoke") -> str:
    now = int(time.time())
    return jwt.encode(
        {
            "iss": API_KEY,
            "sub": identity,
            "iat": now,
            "exp": now + 24 * 3600,
            "video": {
                "room": room,
                "roomJoin": True,
                "canPublish": True,
                "canSubscribe": True,
                "canPublishData": True,
            },
        },
        API_SECRET,
        algorithm="HS256",
    )

print("ML2:    ", mint("ml2"))
print("MOBILE: ", mint("mobile"))
print("BOT:    ", mint("bot"))
```

Stash this script at `apps/MakeItSing/Assets/_LiveKitSpike/mint_tokens.py` or `/tmp/`. It is **not** committed. PyJWT is already in the workspace (or available via `uv add`); if not, install ephemerally with `uv pip install pyjwt`.

### 4. Counterparty: Python echo bot (optional but recommended)

To avoid needing two devices live at once, run a Python echo bot that connects to the same room and replies to any byte it receives. Skip if you have both devices ready and want a true round-trip.

Use `livekit-server-sdk` (Python) or the matching client SDK. Sketch:

```python
import asyncio
from livekit import rtc

async def main():
    room = rtc.Room()
    room.on("data_received", lambda data, participant, kind, topic:
        asyncio.create_task(room.local_participant.publish_data(data, reliable=True, topic=topic)))
    await room.connect("ws://<lan-ip>:7880", "<BOT_JWT>")
    print("Echo bot connected. Ctrl-C to exit.")
    await asyncio.Event().wait()

asyncio.run(main())
```

Stash at `apps/MakeItSing/Assets/_LiveKitSpike/echo_bot.py`. Not committed.

### 5. Build

```bash
uv run compile-unity --project MakeItSing --build android-mobile
uv run compile-unity --project MakeItSing --build magicleap
```

Both must succeed. The Magic Leap target is the riskier — that's where the native `.so` actually has to load. If compile fails on either target with `_LiveKitSpike` present, that itself is the spike result: SDK doesn't fit the project.

The command prints the produced APK paths. Note them.

### 6. Deploy and observe (user-driven)

This step is yours — Claude Code can't drive physical devices.

For each device, in a separate terminal:

```bash
# Filter logcat to Unity tag + livekit-related output
adb logcat -s Unity:* livekit:* libc:F
```

Install:

```bash
adb install -r <path-to-android-mobile.apk>   # against Android Mobile
adb install -r <path-to-magicleap.apk>        # against ML2
```

(ML2's deploy flow is `adb install -r` — ML2 is Android underneath.)

Launch the app on each device, press the button, observe:
- ML2 logcat shows `CONNECTED ml2` followed by `RECV: 01 02 03` (or whatever the echo bot / Android-Mobile peer sent back).
- Android Mobile logcat shows the same shape with `mobile` identity.

Successful round-trip on both devices = pass.

### 7. Failure-mode triage

If anything goes wrong, paste the logcat into the conversation. Common signatures:

- **`UnsatisfiedLinkError: dlopen failed: cannot locate symbol "..."`** — the .so loaded but a runtime dep is missing on ML2's stripped AOSP. Hard failure. Options: rebuild SDK from `com.unity.webrtc` against LiveKit's protocol (substantial), switch SFU (Mediasoup/Janus), ship Android-Mobile-only and skip ML2 for now.
- **`Failed to load library "livekit_ffi"`** — the .so didn't load at all. Could be missing dep, ABI mismatch, or ML2 sandboxing. Same options as above.
- **`Room.Connect` hangs in "Connecting" state forever** — ICE traversal failure. Check: is the LAN IP reachable from ML2 (`adb shell ping <lan-ip>`)? Is UDP egress blocked? Does ML2 have a non-default network interface? Workaround: enable LiveKit's TCP fallback (`LIVEKIT_RTC_TCP_PORT`, already set in Phase 1's compose).
- **Connects but `DataReceived` never fires** — SCTP / data-channel issue. Less likely; check the SFU side.
- **Connects fine but frame-rate tanks under XR rendering** — unlikely. If observed, profile with Unity's profiler attached.

## Cleanup

After the spike passes, before starting Phase 3:

1. The SDK pin in `apps/MakeItSing/Packages/manifest.json` stays committed. It's the only durable Phase 2 artifact.
2. Delete `apps/MakeItSing/Assets/_LiveKitSpike/` (and its `.meta`).
3. Revert the `EditorBuildSettings.asset` change that added the smoke scene to the build list.
4. Discard the local `mint_tokens.py`, `echo_bot.py`, and any token strings (they're hardcoded in the throwaway scene anyway).
5. Confirm `uv run compile-unity --project MakeItSing --build android-mobile` still passes against the original MakeItSing entry scene.

The working branch state after cleanup: Phase 1's compose-service commit, plus a small SDK-pin commit. Phase 3 starts from there.

## Commit hygiene

Two commits, sequenced:

1. **SDK pin commit** (one-line `manifest.json` change). Lands on the working branch and survives the cleanup. Message style: match how other Unity package additions are committed (`git log -- apps/MakeItSing/Packages/manifest.json`).
2. **(Optional) Smoke artifacts commit** — only if you want a checkpoint while iterating on the scene. Otherwise leave `_LiveKitSpike/` uncommitted. If you do commit, the next commit after the spike passes is the deletion of that folder.

No `Co-Authored-By`. No `--no-verify`. No prose updates in this phase.

## Exit criteria

- The LiveKit Unity SDK is pinned in `manifest.json`.
- The smoke scene compiled for both `android-mobile` and `magicleap` targets.
- The smoke scene deployed and ran on a real ML2 device.
- A `Room.Connect()` against the Phase 1 LiveKit server succeeded from ML2.
- A byte round-trip (ML2 ↔ counterparty) succeeded.
- `_LiveKitSpike/` is deleted, `EditorBuildSettings.asset` reverted.
- One small commit (SDK pin) remains on the working branch.

If any of these fail, the gate is failed. Stop and re-evaluate before proceeding to Phase 3.

## Out of scope

- The full `LiveKitTransport` — Phase 5.
- `INetworkTransport` abstraction — Phase 4.
- Token-mint API endpoint — Phase 3.
- Slot-claim, master election, send/receive mapping — Phase 5.
- Voice/audio.
