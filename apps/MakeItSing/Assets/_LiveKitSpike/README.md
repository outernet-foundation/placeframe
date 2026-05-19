# LiveKit ML2 + Android Mobile smoke spike

Throwaway scene that validates the LiveKit Unity SDK loads and a byte can round-trip on Magic Leap 2 and Android Mobile. Deleted entirely after the spike passes; only the SDK pin in `apps/MakeItSing/Packages/manifest.json` survives.

## Scene setup (manual editor step)

1. In Unity, `File > New Scene > Empty`.
2. Create an empty GameObject, name it `Spike`.
3. Add the `SmokeScene` component (search for it in `Add Component`).
4. (Optional) Set `Default Url` to your dev host's LAN IP, e.g. `ws://192.168.x.y:7880`.
5. `File > Save As > apps/MakeItSing/Assets/_LiveKitSpike/SmokeScene.unity`.
6. `File > Build Profiles`, remove the existing scene list and add `SmokeScene` at index 0.

**Do not commit the Build Profiles change.** It reverts after cleanup.

## Mint tokens

`mint_tokens.py` (uncommitted helper) prints three JWTs — one for ML2, one for Android Mobile, one for the optional Python echo bot. Run with `uv run --no-sync python apps/MakeItSing/Assets/_LiveKitSpike/mint_tokens.py` after setting `LIVEKIT_API_KEY` / `LIVEKIT_API_SECRET` to match your `.env`.

## Build

```bash
uv run compile-unity --project MakeItSing --build android-mobile
uv run compile-unity --project MakeItSing --build magicleap
```

Both must succeed. The Magic Leap target loads the native `liblivekit_ffi.so` at runtime — that's where the highest-odds failure lives.

## Deploy and observe

```bash
adb logcat -c
adb logcat -s Unity:* libc:F
adb install -r <printed-apk-path>
```

Launch, paste URL + token, press **Connect**. Expected logcat lines:

```
[Spike] Connecting url=ws://<lan-ip>:7880
[Spike] Connect returned. identity=ml2
[Spike] SEND 01-02-03 topic=smoke
[Spike] RECV from=bot topic=smoke 01-02-03   # or from the other device
```

A successful round-trip on both devices = spike pass. Failure-mode triage table is in `/placeframe/livekit-plan/02-ml2-spike.md` §7.

## Cleanup after pass

1. `rm -r apps/MakeItSing/Assets/_LiveKitSpike apps/MakeItSing/Assets/_LiveKitSpike.meta`
2. Revert any `ProjectSettings/EditorBuildSettings.asset` change.
3. The LiveKit Unity SDK pin in `manifest.json` stays — Phase 5 consumes it.
