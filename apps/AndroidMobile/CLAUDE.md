# apps/AndroidMobile

Unity 6 project for the phone-side Capture Tool. Talks to the ZED box over USB (ZED runs in USB gadget mode, Android sees it as `TRANSPORT_ETHERNET`).

## Invoking Unity from a `--with-adb` slot

Prefix Unity build invocations with `env -u ADB_SERVER_SOCKET`:

```
env -u ADB_SERVER_SOCKET /opt/unity/.../Unity -batchmode -nographics -quit \
  -projectPath apps/AndroidMobile -buildTarget Android -executeMethod ...
```

Unity's Android build module runs `adb kill-server` on teardown. With `ADB_SERVER_SOCKET` set (which `--with-adb` slots have by default), that kill message propagates through the slot and terminates the *host-side* adb server. Next `adb` call from the slot fails with `Connection refused` and the user has to restart the host server (`adb -a -P 5037 start-server` on the host). Unsetting the variable for the Unity subprocess confines Unity's adb dance to a local daemon inside the slot.

This applies to every Unity invocation that targets Android — production builds (`Placeframe.Client.Build.BuildForAndroidMobile`) and plain default-compile sanity checks.

## USB port contention when testing against the ZED box

The Pixel has one USB-C port. In end-to-end testing the ZED cable occupies it, which displaces the debug USB cable. Two ways to cope, in order of preference:

- **Serialize with deferred logcat** (cable-only). `adb logcat -G 4M` + `adb logcat -c` before the swap — the 4 MB ring buffer survives the offline window. Swap the cable back and drain with `adb logcat -d`. Reliable, no network dependency.
- **wifi-adb**. `adb tcpip 5555` + `adb connect <pixel-wifi-ip>:5555` before the swap. Only works when the host and Pixel are on the same wifi without AP client isolation. Office and guest networks often have client isolation — verify by attempting `adb connect` while the debug cable is still plugged; if it returns `No route to host`, don't rely on it.
- **USB-C hub does not work.** The Pixel can't simultaneously be a USB device (to the debug host) and a USB host (to the ZED gadget). These roles are mutually exclusive on a single USB-C port, regardless of what hub is in between. Don't buy one for this.

## Reading phone-side logs from Loki

Capture Tool pushes Unity logs directly to Loki via the gateway (`/loki/api/v1/push`, see `docker/gateway/entrypoint.sh`) with client-side label `app=capture-tool` set in `AuthManager.cs:EnableLoki(...)`. Loki auto-derives `service_name=capture-tool` from the `app` label, so either label works for queries. Quicker than swapping to the debug cable when the phone is plugged into the ZED.

```
docker exec placeframe-loki-1 wget -qO- \
  'http://localhost:3100/loki/api/v1/query_range?query=%7Bservice_name%3D%22capture-tool%22%7D&limit=200&direction=backward'
```

The relay only works while the backend is up (`uv run up`) and the phone has wifi (the relay POST goes over wifi, not USB-ethernet). For ZED-box-side logs see `docker/zed-capture/CLAUDE.md`.

## Slot preconditions for on-device work

Before starting any on-device testing, sanity check:

| Check | Expected |
|---|---|
| `echo "$ADB_SERVER_SOCKET"` | `tcp:<incusbr0-host-ip>:5037` |
| `adb version` | No `* daemon started successfully` line (would indicate a local daemon = wrong socket) |
| `adb devices` | Pixel listed as `device`, not `unauthorized` or empty |

If any check fails, the slot wasn't launched with `--with-adb` (or the host adb server isn't reachable). `forward_env` only fires at container creation — re-attaching a slot created without `--with-adb` won't pick up `ADB_SERVER_SOCKET`. Exit and relaunch with `uv run agent-shell --with-adb`.

If `ADB_SERVER_SOCKET` is set but the slot gets `connection refused` on `<incusbr0-host-ip>:5037` even after `adb -a -P 5037 start-server` on the host, suspect Unity Editor open on the host. Unity spawns its own adb daemon bound to `127.0.0.1:5037` whenever an Android-targeted project is open, which collides with the all-interface server and leaves the bridge IP unbound. Ask the user to close Unity, then re-run `adb -a -P 5037 start-server`.
