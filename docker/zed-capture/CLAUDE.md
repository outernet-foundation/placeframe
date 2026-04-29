# ZED Capture Service

## Hardware constraints

- **No WiFi. Ever.** WiFi is fundamentally less reliable than physical wires. All connectivity is wired — no exceptions.
- The ZED Box Mini is a Jetson Orin-based device (Orin Nano or Orin NX depending on SKU) with: 2x GMSL2 FAKRA-Z (camera), 1x Gigabit Ethernet (RJ45), 1x USB 3.0 Type-A, 1x Micro USB 2.0 Type-B (flashing/OTG), 1x HDMI. The ZED X camera connects via GMSL2, not USB.

## ZED Box networking

The Jetson runs in **USB gadget mode**. The Micro USB OTG port presents the Jetson as a USB Ethernet device to whatever USB host is plugged into it.

**Two connectivity scenarios (never simultaneous):**

1. **Dev computer → OTG port**: For deploying containers (`install-zed`), hitting the API from a browser, etc. The computer is the USB host, the Jetson is the gadget. Disconnect when done.
2. **Android phone → OTG port**: For the CaptureTool app hitting the REST API in the field. The phone acts as USB host via USB-C OTG. Requires a USB-C to Micro USB cable/adapter.

The Ethernet port is available as an alternative, but the OTG gadget link is the primary connectivity method.

## Captive-portal spoof (Android-as-host only)

Android's `NetworkMonitor` runs internet-validation probes on every new network. The USB-ethernet link has no internet, so probes fail; on failure, AOSP's `EthernetNetworkFactory` restarts `IpClient` on the interface, which removes the IP and kernel-destroys every live TCP socket at `192.168.55.100`. Sub-second requests slip through between restart cycles; multi-second ones (camera init during `StartCapture`) get caught and die mid-flight with `Software caused connection abort`. There is no phone-side workaround for non-system apps — `setAcceptUnvalidated` requires `NETWORK_SETTINGS` (signature permission), and `removeCapability(NET_CAPABILITY_INTERNET)` doesn't help because validation is decided by the NetworkAgent's caps, not the request's.

The fix is to make the probe pass. Two pieces:

- **DHCP option** injected into `/opt/nvidia/l4t-usb-device-mode/nv-l4t-usb-device-mode-runtime-start.sh` by `install-zed`. NVIDIA's runtime-start script regenerates `dhcpd.conf` from an inline heredoc on every cable connect (and the stock heredoc does NOT include a `domain-name-servers` option), so editing `dhcpd.conf` directly is silently overwritten on the next plug. The deploy step instead adds `option domain-name-servers 192.168.55.1;` inside the heredoc itself — every regeneration then includes it. An idempotency marker (`# placeframe-captive-portal-fix`) makes re-runs of install-zed a no-op. ISC dhcpd does not reread its config on `SIGHUP`, so install-zed restarts `nv-l4t-usb-device-mode-runtime.service` to force regeneration (cable must be plugged in: `l4tbr0` only exists once udev fires on cable connect).
- **`captive-portal-responder` service in `compose.rig.yml`**: a single `python:3.13-alpine` container running `captive_portal.py` (referenced via compose `configs.file`, scp'd to the box alongside the compose file by `install-zed`) that binds DNS on `192.168.55.1:53` (responds to A queries with `192.168.55.1`, empty answer to others) and HTTP on `192.168.55.1:80` (returns `204 No Content` for any GET). Binds specifically to the gadget IP rather than `0.0.0.0` to sidestep conflicts with anything bound to `127.0.0.1:53`. Retries the bind on startup so it survives starting before the cable is plugged in (`l4tbr0` only exists once udev fires on cable connect).

Android's HTTPS probe still fails (we'd need a custom CA on the phone to spoof it), but Android marks the network validated if any single probe succeeds, and the HTTP probe is enough. We deliberately do NOT add `option routers 192.168.55.1;` to the heredoc — without a default gateway on the ethernet network, Android can't accidentally route internet-bound traffic through the cable even after validation passes.

**DHCP lease time** is the second heredoc patch `_setup_captive_portal_dhcp` lands. NVIDIA's stock heredoc parameterises both `default-lease-time` and `max-lease-time` with `${net_dhcp_lease_time}`, which on the boxes we've seen resolves to 15 seconds. That's too short for Android's `DhcpClient`: it schedules renewal at ~30 s (its internal minimum), so the lease expires first. When the lease expires the kernel removes 192.168.55.100 from `usb0`, `EthernetNetworkFactory` restarts `IpClient`, and every live TCP socket on the gadget IP dies mid-flight with `java.net.SocketException: Software caused connection abort` — the same socket-abort symptom as the captive-portal flap, just from a different root cause. `install-zed` overrides both directives to `3600` in the heredoc.

**L4T assumptions baked into install-zed:** the runtime-start script path (`/opt/nvidia/l4t-usb-device-mode/nv-l4t-usb-device-mode-runtime-start.sh`) and the runtime service name (`nv-l4t-usb-device-mode-runtime.service`) are NVIDIA-shipped, stable across L4T R32–R36+, but Jetson-specific. The two `replace()` anchors inside `_setup_captive_portal_dhcp` (captive-portal DNS option and lease-time directives) match the heredoc shape on L4T R36 (June 2025); if a future release tweaks the heredoc indentation or variable names, neither replace finds its anchor and `install-zed` fails loudly with an actionable pointer to update. If a future release moves the script entirely (or a custom Jetson image replaces L4T USB device mode with NetworkManager/systemd-networkd), the `test -f` check fires loudly with the same pattern.

This whole section only matters when the phone is the USB host. Dev-computer-as-host doesn't care because Linux/macOS/Windows don't run gstatic probes.

## Reading box-side logs from Loki

The ZED box's container logs are pulled by the phone via `GET /logs` (cursor-based) and forwarded to the api at `POST /zed-boxes/logs` (see `docker/api/src/routers/zed_box_logs.py`). The api tags the relayed lines with stream label `service="zed-capture"` and `box_id=<box hardware serial>` in Loki. Each log record carries its own `box_id` field, stamped by `logging_config.py` from the `ZED_BOX_ID` env var (set by `install-zed` from the box's hardware serial). The api groups entries by `box_id` and emits one Loki stream per id.

**Source of truth on the box** is `/var/log/zed-capture/app.jsonl`. Logging is configured in Python by `src/logging_config.py` calling `logging.config.dictConfig(...)` at module import time, triggered from `src/__init__.py`. The dictConfig points root and the `uvicorn`/`uvicorn.access`/`uvicorn.error` loggers at the same `RotatingFileHandler` + `StreamHandler` pair, both formatted with `pythonjsonlogger.json.JsonFormatter`. The `GET /logs` router reads back the same file via the `LOG_DIR` / `LOG_FILE_NAME` constants from the same module — single source of truth.

Important: `main.py` passes `logging_config=None` to `create_litestar_app(...)`. **Do not remove that argument.** Litestar's default `LoggingConfig` (used when `logging_config` is `Empty`) calls `dictConfig` at app construction time and replaces the root logger's handlers with a single `QueueHandler` whose listener has its own pretty-print stream handler — no file output, JSON formatter ignored. That clobbers what `logging_config.py` set up. We landed here once already (the bug surfaced as `Capturing frame` and other `src.zed.zed` log calls landing in `docker logs` but not in `app.jsonl`); the parent walk in a thread-side probe was the smoking gun (root having only `[<QueueHandler (DEBUG)>]`). For the same reason, **do not** pass `--log-config` to uvicorn — that just adds a second config-application step that is then itself overwritten by Litestar; the only durable fix is to own the config in Python and tell Litestar to do nothing.

Anything written via Python's `logging` framework lands in the relay; **`print()` calls bypass it** and only appear in `docker logs`. Native ZED SDK stderr (e.g. `NvVideo:` lines) also bypasses it — that would need an explicit stderr-to-logger bridge to capture.

```
docker exec placeframe-loki-1 wget -qO- \
  'http://localhost:3100/loki/api/v1/query_range?query=%7Bservice%3D%22zed-capture%22%7D&limit=200&direction=backward'
```

The stream is empty when the phone isn't actively draining (no relay traffic). Direct alternative when SSH'd into the ZED: `docker logs -f $(docker ps -q --filter name=zed-capture)`.
