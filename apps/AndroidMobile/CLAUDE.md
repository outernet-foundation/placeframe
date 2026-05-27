# apps/AndroidMobile

Unity 6 project for the phone-side Capture Tool. Talks to the ZED box over USB via the [Android Open Accessory (AOA) protocol](https://source.android.com/docs/core/interaction/accessories/aoa): the ZED is the USB host, the phone is a USB accessory, and the app speaks HTTP/2 cleartext (h2c, prior-knowledge) directly to the accessory file descriptor with no IP layer. HTTP/2 is required because the single duplex byte stream over the accessory FD permits only one in-flight HTTP/1.1 request — a concurrent request corrupts framing and tears the pipe down. HTTP/2 frames multiple logical streams over the one transport, which is exactly the property the medium is missing; `h2c` (prior-knowledge, no ALPN, no TLS) is the correct flavour for a fixed-topology USB link with no IP identity. The HTTP path is a Java+OkHttp hybrid: `Assets/Scripts/AndroidAoaHttpHandler.cs` is the `HttpMessageHandler` shim that marshals requests via JNI into `Assets/Plugins/Android/AoaAccessoryClient.java`, which holds a vendored-OkHttp client (`Protocol.H2_PRIOR_KNOWLEDGE`) wired to `AoaSocketFactory` (`AoaSocket.connect()` is a no-op so OkHttp writes straight into the `UsbAccessory` `ParcelFileDescriptor`). OkHttp still resolves URL hostnames before consulting the SocketFactory, so the client installs a synthetic `Dns` that returns `127.0.0.1` for any hostname — the address is never dialled. The ZED-side bridge is in `docker/aoa-bridge/src/aoa_bridge/main.py`. Internet-bound HTTP (placeframe API, Loki push) uses .NET's default `HttpClientHandler` — there is no per-network binding because AOA isn't a Network from Android's point of view, so default routing can't accidentally use the USB cable.

## Invoking Unity from a Pulsar slot

Use `uv run compile-unity` for every Unity invocation; never call `/opt/unity/.../Unity` directly.

**Build + install on the host-attached phone:**

```
uv run compile-unity --project CaptureTool --build android-mobile
adb install -r apps/AndroidMobile/Build/<ProductName>.apk   # path is printed at end of build
```

Both `--project` and `--build` are required (no defaults). `--project` keys live in `build/unity-projects.json`; `--build` keys are the project's entries under `builds`. The command preps NuGet/dotnet tools, builds Unity in batchmode via the project's registered `executeMethod`, streams the log, and prints the produced APK path on success. Use the same command for a "did this `.cs` change compile?" sanity check — Unity bails fast on `error CS####` before the Android build starts.

The CI-side `uv run build-unity` is a different entry point (cache, license, OCI registry, version tags) and is not usable from a slot. Don't reach for it.

`compile-unity` goes through `unity_batchmode_command`, which prefixes `env -u ADB_SERVER_SOCKET` on non-Windows. Background: Unity's Android build module runs `adb kill-server` on teardown. Since every slot has `ADB_SERVER_SOCKET` forwarded to the host adb daemon (set unconditionally by `uv run agent-shell`), an unscrubbed kill propagates through the socket and terminates the *host-side* server — next `adb` call from the slot then fails with `Connection refused` until the host runs `adb -a -P 5037 start-server` again. The `env -u` strip in `unity_batchmode_command` confines Unity's adb dance to a local daemon inside the slot. Direct `/opt/unity/.../Unity` invocations bypass that guard, which is why the rule is "always `uv run compile-unity`."

## USB port contention when testing against the ZED box

The Pixel has one USB-C port. In end-to-end testing the ZED cable occupies it, which displaces the debug USB cable. Two ways to cope, in order of preference:

- **Serialize with deferred logcat** (cable-only). `adb logcat -G 4M` + `adb logcat -c` before the swap — the 4 MB ring buffer survives the offline window. Swap the cable back and drain with `adb logcat -d`. Reliable, no network dependency.
- **wifi-adb**. `adb tcpip 5555` + `adb connect <pixel-wifi-ip>:5555` before the swap. Only works when the host and Pixel are on the same wifi without AP client isolation. Office and guest networks often have client isolation — verify by attempting `adb connect` while the debug cable is still plugged; if it returns `No route to host`, don't rely on it.
- **USB-C hub does not work.** The Pixel can't simultaneously be a USB device (to the debug host) and a USB host (to the ZED gadget). These roles are mutually exclusive on a single USB-C port, regardless of what hub is in between. Don't buy one for this.

## Granting READ_LOGS for the logcat -> Loki relay

`LogcatRelay` (`Assets/Scripts/LogcatRelay.cs`) tails Android's logcat in a background thread and forwards filtered lines (USB / accessory framework tags) through Serilog into the existing Loki sink, so phone-side diagnosis of `UsbHostManager` / `UsbDeviceManager` decisions does not require swapping the debug cable. The reader runs unconditionally, but the kernel only exposes other processes' lines to apps holding `android.permission.READ_LOGS`. That permission is `signature|privileged|development`, so install-time grant is impossible; the `development` flag is what lets `pm grant` satisfy it at runtime.

After every fresh install of the Capture Tool, the grant has to be re-applied — it persists across reboots and app launches but is lost on uninstall. `uv run install --project CaptureTool` does this automatically: the project's `grant_permissions: ["android.permission.READ_LOGS"]` entry in `build/unity-projects.json` drives a post-install `adb shell pm grant` call. Pass `--no-grant-permissions` to opt out for a specific install (rare; the grant is harmless when LogcatRelay isn't actively used).

For a hand-built APK from `uv run compile-unity` + `adb install`, the grant has to be applied manually:

```
adb shell pm grant com.outernet.captureapp android.permission.READ_LOGS
``` Without it, the relay still runs but its Loki output is limited to this app's own log lines (which Serilog already captures by other means, so the practical signal is zero). To verify after a session, query Loki for `{app="capture-tool"} | json | logGroup="Android"` — non-empty (and showing `Pid` values that aren't the app's own) means the grant is in place and framework events are flowing through.

The tag whitelist lives in `LogcatRelay.TagFilters`; extend it (or relax to `*:V`) only when a specific debugging session needs more — raw `*:V` is much chattier than Loki's per-tenant ingestion burst comfortably handles.

## Reading phone-side logs from Loki

Capture Tool pushes Unity logs directly to Loki via the gateway (`/loki/api/v1/push`, see `docker/gateway/entrypoint.sh`) with client-side label `app=capture-tool` set in `AuthManager.cs:EnableLoki(...)`. Loki auto-derives `service_name=capture-tool` from the `app` label, so either label works for queries. Quicker than swapping to the debug cable when the phone is plugged into the ZED.

Use `uv run loki-query` from the slot — it handles URL encoding and prints one-line summaries (timestamp, level, log group, message, exception chain). Single-quote the LogQL so the shell doesn't expand `{}` or `|`:

```
uv run loki-query '{app="capture-tool"} | json | logGroup="Android"'
uv run loki-query '{app="capture-tool"} | json | logGroup="Zed"' --since 5m
uv run loki-query '{app="capture-tool"} | json | logGroup="Android" | Tag="UsbHostManager"' --limit 200
uv run loki-query '{app="capture-tool"}' --raw       # full Loki JSON, for ad-hoc jq
```

Default range is 30m, default limit 50, newest first. Pass `--raw` when you need the full JSON instead of the formatted summaries.

Prefer the structured `| json | <field>="<value>"` form over `|= "<substring>"` substring filters — fewer escape-quoting traps. If a fresh query returns zero entries, wait ~3s and retry: `LokiSink` batches every ~2s when idle, so very recent emissions may not be flushed yet. The relay only works while the backend is up (`uv run up`) and the phone has wifi (the relay POST goes over wifi, not USB-ethernet). For ZED-box-side logs see `docker/zed-capture/CLAUDE.md`.

## Slot preconditions for on-device work

Before starting any on-device testing, sanity check:

| Check | Expected |
|---|---|
| `echo "$ADB_SERVER_SOCKET"` | `tcp:<incusbr0-host-ip>:5037` |
| `adb version` | No `* daemon started successfully` line (would indicate a local daemon = wrong socket) |
| `adb devices` | Pixel listed as `device`, not `unauthorized` or empty |

If any check fails, the host adb server isn't reachable or the slot was created before adb forwarding became unconditional. `forward_env` only fires at container creation, so an older slot may have a stale or absent `ADB_SERVER_SOCKET`. Destroy the slot and relaunch with `uv run agent-shell` to pick up the current value.

If `ADB_SERVER_SOCKET` is set but the slot gets `connection refused` on `<incusbr0-host-ip>:5037` even after `adb -a -P 5037 start-server` on the host, suspect Unity Editor open on the host. Unity spawns its own adb daemon bound to `127.0.0.1:5037` whenever an Android-targeted project is open, which collides with the all-interface server and leaves the bridge IP unbound. Ask the user to close Unity, then re-run `adb -a -P 5037 start-server`.
