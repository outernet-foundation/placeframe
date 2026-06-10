# ZED Capture Service

## Hardware constraints

- **No WiFi. Ever.** WiFi is fundamentally less reliable than physical wires. All connectivity is wired — no exceptions.
- The ZED Box Mini is a Jetson Orin-based device (Orin Nano or Orin NX depending on SKU) with: 2x GMSL2 FAKRA-Z (camera), 1x Gigabit Ethernet (RJ45), 1x USB 3.0 Type-A, 1x Micro USB 2.0 Type-B (flashing/OTG), 1x HDMI. The ZED X camera connects via GMSL2, not USB.

## ZED Box networking

The Jetson is the **USB host** for the phone-as-accessory link, and uses its RJ-45 wired ethernet for laptop SSH access (deploys, debugging) and for outbound internet (image pulls, ZED SDK warmup).

**Two connectivity paths:**

1. **Laptop → wired ethernet**: For deploying containers (`install-zed`), hitting the API from a browser, etc. SSH over standard TCP/IP on the box's RJ-45 address. The expected topology is a direct ethernet cable between the host machine and the box, so `install-zed` defaults to `--host user@100.64.0.1` (with the host's cable-side end at `100.64.0.2`). The subnet sits in RFC 6598 (`100.64.0.0/10`, the same range Tailscale uses) rather than RFC1918 so sandboxed agent containers on the host can reach the box without tripping RFC1918-block rules. `install-zed` owns the host's `zedbox` NetworkManager connection, `ip_forward`, and firewalld trusted-zone source / masquerade — a fresh-Ubuntu host can run `install-zed` and get a fully working box→internet path. Override with `--host user@<ip>` for a shared-LAN setup (skips the host-side ownership).
2. **Android phone → USB-C OTG (AOA)**: For the CaptureTool app hitting the REST API in the field. The ZED is the USB host; the phone is a USB accessory. See `docker/aoa-bridge/CLAUDE.md` for the bridge service that drives the [Android Open Accessory](https://source.android.com/docs/core/interaction/accessories/aoa) handshake and forwards the accessory's bulk endpoints to `127.0.0.1:9000`.

NVIDIA's stock `nv-l4t-usb-device-mode.service` is disabled by `install-zed` because it pins the USB-C port as a peripheral (CDC ethernet + mass-storage gadget), preventing the host-mode role the AOA bridge requires.

## `frames.csv` schema

ZED captures write `timestamp_ms,tx,ty,tz,gx,gy,gz`. `(tx, ty, tz)` is the SDK's `world_from_rig` translation (the camera0 center in the SDK's gravity-aligned world); `(gx, gy, gz)` is the unit down vector in the frame's rig-local coordinates, derived from the SDK's `world_from_rig` rotation and the IMAGE/OpenCV world's `+Y` down convention. Camera0 is the ref sensor with identity rig↔camera0, so it's also gravity-in-camera0. The reconstructor consumes the position as a pair-generation signal (spatial-neighbor source) and the gravity as a map-frame alignment signal — see `docker/reconstructor/SPEC.md` "Map-frame alignment via per-frame gravity + first-frame origin" and "Pair generation".

## Reading box-side logs from Loki

Box containers log via OTLP (gRPC) to `OTEL_EXPORTER_OTLP_ENDPOINT` (`http://127.0.0.1:4317`, the box-side Alloy `aoa-alloy`), which forwards to the box-side Loki `aoa-loki` (`127.0.0.1:3100`). The OTLP pipeline maps each service's `service.name` resource attribute to the `service_name` Loki label, so box logs land under `service_name="zed-capture"`; the box's hardware serial rides as the `instance` label (from `ZED_BOX_ID`, set by `install-zed`).

The phone forwards box logs to the backend Loki via `LogDrainController` (`apps/CaptureTool/Assets/Scripts/Capture/LogDrainController.cs`). While logged in, it queries `aoa-loki` over the AOA pipe (`GET /loki/api/v1/query_range?query={service_name=~".+"}`, cursor-based on nanosecond timestamps, 1h max lookback) and pushes the returned streams to `{apiUrl}/loki/api/v1/push` (through host-Caddy, authed by the shared backend handler). Timestamps are restamped to phone wall-time at drain — the box boots at 1970 with no RTC, so the offset is `phone_now` minus the box clock read from the query response `Date` header — but labels are untouched, so box-Alloy's `service_name="zed-capture"` stream survives the hop into the backend Loki and is read with the standard tool:

```
uv run loki-query '{service_name="zed-capture"}'
```

The stream is empty when the phone isn't draining: no AOA link, not logged in, or `aoa-loki` has nothing newer than the drain cursor. To read box logs on the box itself, query `aoa-loki` directly (`wget -qO- 'http://127.0.0.1:3100/loki/api/v1/query_range?query=%7Bservice_name%3D~%22.%2B%22%7D'`) or tail `sudo docker logs -f $(sudo docker ps -q --filter name=zed-capture)`.

**On-box logging config.** `src/logging_config.py` (imported first by `src/__init__.py`, before Litestar acquires any logger) calls `common.configure_logging("zed-capture", instance_id=ZED_BOX_ID, log_file_path=/var/log/zed-capture/app.jsonl, uvicorn_logger_handlers=True)`. That installs three handlers on the root and `uvicorn`/`uvicorn.access`/`uvicorn.error` loggers: a stderr `StreamHandler` (→ `docker logs`), an OTLP handler (→ `aoa-alloy`, the Loki path above, active whenever `OTEL_EXPORTER_OTLP_ENDPOINT` is set), and a `RotatingFileHandler` writing `/var/log/zed-capture/app.jsonl` — a local on-box copy, independent of the OTLP path. `print()` calls and native ZED SDK stderr (e.g. `NvVideo:` lines) bypass `logging` entirely and reach only `docker logs`.

Important: `main.py` passes `logging_config=None` to `create_litestar_app(...)`. **Do not remove that argument, and do not pass `--log-config` to uvicorn.** Litestar's default `LoggingConfig` (used when `logging_config` is `Empty`) calls `dictConfig` at app construction time and replaces the root logger's handlers with a single `QueueHandler` whose listener has its own pretty-print stream handler — no file output, no OTLP export. That clobbers what `logging_config.py` set up. We landed here once already (the bug surfaced as `Capturing frame` and other `src.zed.zed` log calls landing in `docker logs` but not in `app.jsonl`); the parent walk in a thread-side probe was the smoking gun (root having only `[<QueueHandler (DEBUG)>]`). A `--log-config` flag would just add a second config-application step that Litestar then overwrites anyway; the only durable fix is to own the config in Python and tell Litestar to do nothing.
