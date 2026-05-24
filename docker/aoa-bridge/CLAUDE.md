# AOA Bridge Service

USB-host daemon that handshakes a connected Android phone into accessory mode and forwards the bulk-endpoint bytes to `zed-capture`'s HTTP server at `127.0.0.1:9000`. The phone app speaks HTTP/2 cleartext (h2c, prior-knowledge) directly to the accessory FD with no IP layer between them. The bridge itself is protocol-agnostic — it's a transparent byte pipe and never inspects framing.

## Service shape

Standard placeframe Python workspace member — `src/aoa_bridge/` package, `pyproject.toml` declaring `pyusb`, hatchling build backend, `pylock.toml` for transitive pins, `[project.scripts] aoa-bridge = "aoa_bridge.main:main"` exposing the entry point.

The Dockerfile bakes deps in at build time (`libusb-1.0-0` via apt, `pyusb` via uv from `pylock.toml`) — no internet needed at container start. Built via `compose.zed.bake.yml` alongside `zed-capture` and shipped to the box via the same local-registry path `install-zed --build` uses.

## Protocol (`src/aoa_bridge/main.py`)

1. Find any non-Google USB device on the bus.
2. Issue `GET_PROTOCOL` (vendor request 51). Anything ≥1 supports AOA.
3. Send identification strings (`SEND_STRING`, request 52). Manufacturer/model/version must match the phone-side `accessory_filter.xml`:
   - manufacturer = `Placeframe`
   - model = `ZED-Box`
   - version = `1`
4. Send `START` (request 53). Phone re-enumerates with Google's accessory vid/pid (`0x18d1` / `0x2d00`+).
5. Open interface 0, find bulk IN/OUT endpoints, forward bytes to/from a TCP socket on `127.0.0.1:9000`.

When the cable is unplugged the USB read errors out, the upstream socket is closed, and the loop returns to polling for new accessories. The phone-side `AoaAccessoryClient.java` is the counterpart: it opens the `UsbAccessory` via `UsbManager.openAccessory()`, then OkHttp speaks HTTP/2 (prior-knowledge) against the FD via a custom `SocketFactory`.

## App dispatch (auto-launch the Capture Tool)

Android matches the AOA handshake strings against every installed app's `accessory_filter.xml` and launches the unique match via `USB_ACCESSORY_ATTACHED`. The Capture Tool's manifest declares:

```xml
<intent-filter>
    <action android:name="android.hardware.usb.action.USB_ACCESSORY_ATTACHED" />
</intent-filter>
<meta-data android:name="android.hardware.usb.action.USB_ACCESSORY_ATTACHED"
           android:resource="@xml/accessory_filter" />
```

with `accessory_filter.xml` matching the strings above. Intent-launch carries implicit USB permission for the accessory in the intent. Manually opening the app with an accessory already attached takes the explicit-permission path: `AoaAccessoryClient` calls `UsbManager.requestPermission` with a `PendingIntent`; the system shows a one-time dialog.

## Reading bridge logs

`docker logs -f $(docker ps -q --filter name=aoa-bridge)` on the box shows handshake + pipe lifecycle.

## Debugging gotchas

- **Do not unbind/rebind the `tegra-xusb` driver.** `echo 3610000.usb | sudo tee /sys/bus/platform/drivers/tegra-xusb/unbind` (and its rebind) crashes the xHCI controller with `Falcon state: 0xffffffff, failed to load firmware: -5` and requires a physical reboot of the box to recover. Use `journalctl -k` + a physical cable reseat to observe enumeration events instead.
- **Ignore FUSB301 / `usb-role-switch` / OTG diagnostics on the box.** The phone is wired into the box's USB-A 3.0 port, which is always-host (no role switching). FUSB301 probe failures and `usb2-0-role-switch role=none` log lines come from the unused Micro-USB-B OTG port and are irrelevant to this pipeline.
- **Kernel traces over SSH: non-sudo `journalctl -k` works.** Run `ssh user@100.64.0.1 'journalctl -kf -n 0 --since now' | grep -iE "usb|xhci|hub |port|connect|enum|tegra"` (or pipe through the Monitor tool) to stream plug events live. `sudo journalctl` over SSH needs a TTY/password and fails silently inside non-interactive commands.
- **Handshake cycles every ~20 s when something is wrong.** Sampling `lsusb` once can land in the disconnected window of the cycle and look like "phone isn't enumerating" when it is. Use the streaming `journalctl` command above instead.
