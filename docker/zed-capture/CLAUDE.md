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
