---
updated: 2026-05-21
---

# AOA pipeline carries no traffic end-to-end; prior debug went down wrong tracks

## Goal

Find out **what is actually preventing the AOA pipeline from carrying traffic end-to-end** between the ZED box (USB host, `aoa-bridge` + `aoa-gateway` + `zed-capture`) and the Capture Tool phone app (USB accessory). The prior session chased several wrong theories and broke things along the way; the user explicitly stated the real cause was never addressed and reverted the cosmetic/diagnostics changes that ended up landing.

This memory is targeted at `/diagnose` — restart investigation from the actual signal, not the closed theories below.

## The real signal (re-confirmed at end of session)

Both ends were behaving roughly as designed at the handshake level. The failure is post-handshake, in the pipe.

- **Box side** (`docker logs placeframe-aoa-bridge-1` while phone plugged into the box's USB-A port):
  ```
  aoa-bridge starting; upstream=127.0.0.1:9000
  handshaking candidate vid=18d1 pid=4ee7        # phone in normal Pixel mode
  device supports AOA protocol v2
  accessory ready vid=18d1 pid=2d01              # re-enumerated as AOA + ADB
  upstream connected; piping (in_ep=0x81, out_ep=0x01)
  IN transfer status=5                           # LIBUSB_TRANSFER_NO_DEVICE
  pipe done: to_phone=0B from_phone=0B           # zero bytes either direction
  ```
  Cycle repeats roughly every ~20s. `lsusb` during the connected window shows `Bus 002 Device N: ID 18d1:2d01 Google Inc. Android Open Accessory device (accessory + ADB)` — handshake genuinely completes.

- **Phone side** (Loki, `{app="capture-tool"}`): repeated `java.io.IOException: AOA accessory not ready (accessoryList=empty)` from a `health poll` loop. `UsbManager.getAccessoryList()` returns empty even though the box has the phone re-enumerated as an AOA accessory.

So: bridge thinks it has an AOA accessory and opens the bulk pipe; phone-side `UsbManager` doesn't see any accessory; no bytes flow; phone vanishes a couple seconds later; bridge loop restarts.

## Wrong tracks already chased (do not re-walk)

1. **"The phone isn't enumerating on the box."** False. `lsusb` showed nothing only because it was sampled during the disconnected window of the ~20s handshake/retry cycle. The phone was always being seen — we just didn't realize the cycle was happening.
2. **USB-C / Type-C / FUSB301 / `usb_role` / OTG.** The phone is plugged into the box's **USB 3.0 Type-A port** (always-host, no role-switching). The `usb2-0-role-switch role=none`, `nv-l4t-usb-device-mode.service` absent, FUSB301 probe failures (`failed to read device id, err: 0xffffff87`), etc. are all about the unused Micro-USB-B OTG port. Irrelevant to this pipeline.
3. **"Cable is charge-only / cable is bad / port is bad."** User had already confirmed cable and port were fine; this was a lazy reach the user pushed back on hard.
4. **Root-hub `autosuspend_delay_ms=0`.** That's the kernel default for root hubs (they have no children to wake on), not a bug we injected. `grep -rn "autosuspend\|power/control\|usbcore" /placeframe/` returns nothing — install_zed never writes to it.
5. **`install_zed` is misconfiguring the box.** Reviewed `orchestrator.py`, `box_install.py`, `host_setup.py`, `constants.py`. It only does package installs, `systemctl disable --now nv-l4t-usb-device-mode.service` (no-op on this box), `/etc/hosts`, `nmcli`, image pulls, `docker compose up`. Nothing touches `/sys/class/usb*` or `/sys/bus/usb/devices/*/power/*`. Not the cause. (One unrelated latent issue noted there: the disable swallows "unit not found" silently, but that's cosmetic.)
6. **`tegra-xusb` driver unbind/rebind probe.** I tried `echo 3610000.usb | sudo tee /sys/bus/platform/drivers/tegra-xusb/unbind` then bind, which **crashed the controller** (`Falcon state: 0xffffffff, failed to load firmware: -5`) and forced a reboot of the box to recover. Do not repeat. Use Monitor on `journalctl -kf` + a physical reseat to observe plug events instead.

## Working theory at point of abort (unverified)

The closing theory — also unverified — is that the bridge advertises identification strings via AOA `SEND_STRING` (manufacturer="Placeframe", model="ZED-Box", version="1" — see `docker/aoa-bridge/src/aoa_bridge/main.py:20-25`), and Android matches those exactly against `accessory_filter.xml` to populate `getAccessoryList()` and dispatch the `USB_ACCESSORY_ATTACHED` intent. A mismatch would explain `accessoryList=empty`.

**But: I already grepped this.** The two strings ARE in sync right now:

- `docker/aoa-bridge/src/aoa_bridge/main.py:20-25` → manufacturer `Placeframe`, model `ZED-Box`, version `1`
- `apps/AndroidMobile/Assets/Plugins/Android/aoa-accessory-filter.androidlib/res/xml/accessory_filter.xml` → `<usb-accessory manufacturer="Placeframe" model="ZED-Box" version="1" />`
- `docker/aoa-bridge/CLAUDE.md` confirms these are the canonical strings.

So the obvious accessory-filter-drift hypothesis is already disproved by inspection. The real cause is somewhere else.

## Open questions (start here)

1. **Why does `UsbManager.getAccessoryList()` return empty when `lsusb` shows the phone as `18d1:2d01` AOA + ADB?** Possibilities to actually probe (not assume away):
   - Is the Capture Tool process even running / foregrounded when the handshake completes? The bridge cycles every ~20s; if the app is killed/backgrounded and Android isn't dispatching the intent (because no manifest match for this user/profile), `getAccessoryList()` from a freshly launched app may legitimately be empty.
   - Is the system delivering `USB_ACCESSORY_ATTACHED` to the app at all? `adb logcat -d` filtered to `UsbHostManager`, `UsbDeviceManager`, `UsbAccessory` will say whether Android matched the accessory against `accessory_filter.xml` and tried to dispatch.
   - The accessory `vid:pid` reported by the bridge log was `18d1:2d01` ("accessory + ADB"). The Android docs distinguish `2d00`/`2d01`/`2d04`/`2d05` for accessory-only / accessory+ADB / accessory+audio / accessory+ADB+audio. ADB-on means the phone has USB-debugging enabled — does the install_zed setup expect a specific mode? Could the `+ADB` variant be hitting a permission edge case?
   - The bridge sees `LIBUSB_TRANSFER_NO_DEVICE` (`status=5`) almost immediately after `upstream connected`. That's the kernel telling libusb the device went away. Why does the phone disconnect itself ~2s after a successful AOA START? Hypotheses worth checking:
     - Phone-side app has a watchdog that closes the `ParcelFileDescriptor` on health-check failure, which triggers a USB re-enumeration.
     - `aoa-bridge` is claiming interface 0 in a way that races with the system-side accessory dispatch (system holds the accessory FD; libusb wresting the bulk endpoints kicks the system off, which kicks the phone into re-enumeration).
     - There's a permission dialog blocking on the phone that we can't see because the screen is off / the app isn't foregrounded.
2. **`aoa-bridge` log is suspiciously sparse.** Only `aoa-bridge starting; upstream=127.0.0.1:9000` then the cycle. Confirm logging level isn't dropping useful information about the failure mode.
3. **`aoa-gateway` (Caddy h2c sidecar in front of `zed-capture`) logs were never inspected end-to-end.** `docker logs placeframe-aoa-gateway-1` only showed Caddy startup. With zero bytes flowing through the bridge, gateway should see nothing — but if it sees connection attempts that fail, that's a separate signal.

## Diagnostic moves that worked (re-usable)

- SSH to the box: `ssh user@100.64.0.1` (no host-side cable required; user→box link is over ethernet, the host laptop has nothing USB-attached).
- Box uses Tegra `tegra-xusb` xHCI. `lsusb` + `lsusb -t` + `journalctl -k -b 0` is the right toolkit.
- `Monitor` tool with `ssh user@100.64.0.1 'journalctl -kf -n 0 --since now' </dev/null | grep --line-buffered -iE "usb|xhci|hub |port|connect|enum|tegra"` works without sudo and streams kernel events. **Use this** to confirm plug events while the user physically reseats — it's how we finally caught the ~20s cycle.
- `sudo journalctl` from SSH needs a TTY/password and will fail silently in a Monitor command — don't try it; non-sudo `journalctl -k` works fine on this box.
- Phone-side: query Loki for `{service_name="capture-tool"}` to see Unity-side AOA exceptions without swapping cables.

## Key files

- `docker/aoa-bridge/src/aoa_bridge/main.py` — bridge handshake + bulk-pipe loop. The `status=5` and `pipe done: to_phone=0B from_phone=0B` log lines come from here.
- `docker/aoa-bridge/CLAUDE.md` — protocol summary; manufacturer/model/version strings on lines 17-18.
- `docker/aoa-gateway/` (Caddy h2c sidecar) — sits between bridge's TCP socket on `127.0.0.1:9000` and `zed-capture`'s HTTP server.
- `apps/AndroidMobile/Assets/Plugins/Android/aoa-accessory-filter.androidlib/res/xml/accessory_filter.xml` — phone-side accessory match.
- `apps/AndroidMobile/Assets/Plugins/Android/AoaAccessoryClient.java` — phone-side JNI that opens the `UsbAccessory` and wraps it in OkHttp + vendored HTTP/2.
- `apps/AndroidMobile/Assets/Scripts/AndroidAoaHttpHandler.cs` — `HttpMessageHandler` marshalling requests to the Java side.
- `apps/AndroidMobile/CLAUDE.md` — explains the AOA topology, why h2c, and the "health poll" loop the IOException comes from.
- `scripts/src/scripts/install_zed/{orchestrator,box_install,host_setup,constants}.py` — already reviewed; not the cause but useful reference for what the box install actually does.

## Pending threads

- Re-investigate from the phone side first: `adb logcat -G 4M`, plug into ZED box, let one full handshake cycle happen, swap cable back, `adb logcat -d | grep -iE "usb|accessory|aoa|Placeframe|CaptureTool"`. The first question to answer is "did Android receive `USB_ACCESSORY_ATTACHED` and try to deliver it?"
- Confirm the Capture Tool's AndroidManifest still declares the `USB_ACCESSORY_ATTACHED` intent-filter + meta-data pointing at the filter XML (CLAUDE.md says it does, but verify in the built APK manifest — the resource id has to actually resolve in the merged manifest, not just in the `aoa-accessory-filter.androidlib` library).
- If the manifest is fine and Android still doesn't dispatch, check whether the `accessory + ADB` (`pid=0x2d01`) variant is the issue — try forcing the bridge to handshake without ADB (`accessory` only, `pid=0x2d00`) by toggling USB debugging on the phone, and see whether dispatch starts working.
- Treat the bridge cycling as an effect, not a cause, until proven otherwise. The bridge sees `NO_DEVICE` because something on the phone-side is releasing the FD; figure out what releases it.
- The user reverted the cosmetic toggle/log additions that landed in commits `06953199`, `0c46d860`, `0e2d56af` because they didn't address this; do not re-add them as a means of debugging this issue. Use logcat + journalctl + Loki, not more in-app toggles.
