---
updated: 2026-05-22
---

# AOA cold-start RST: parallel-USB hypothesis falsified; corruption is somewhere else on the byte path

## Goal

Diagnose why the Capture Tool's "Captures" tab stays blank for ~60 s after login when the phone is wired to the ZED box over the AOA pipe. Three prior sessions narrowed the failure to **byte corruption on the wire**: Caddy on the box sends `GOAWAY ErrCode=FRAME_SIZE_ERROR` within a few ms of reading the first HEADERS frame on a fresh TCP connection, because a frame header arriving over the AOA pipe decodes to a `Length` > 1 MB (Caddy's default `MaxReadFrameSize`). The previous prime suspect — aoa-bridge's `NUM_IN_TRANSFERS=4` parallel USB BULK IN transfers completing out of submission order — has now been **falsified by direct test**. The corruption mechanism is elsewhere.

This memory is targeted at `/diagnose`. The transport, repro path, logging, and prior-hypothesis-elimination are all in place; the next session executes the highest-information **Loki-native** diagnostic step (grant `READ_LOGS` on the phone so OkHttp h2 frame writes flow into Loki, repro, diff OkHttp `>>` writes against Caddy `read` frames). No host-side tcpdump needed.

## State

### What the wire actually shows (latest repro, 2026-05-22 21:45:41 UTC)

Cross-correlated trace from `service=aoa-bridge`, `service=aoa-gateway` (Caddy structured + GODEBUG `http2debug=2` stderr), and `service=capture-tool` (OkHttp h2 frame log under Tag=`OkHttpH2`):

```
21:45:26      aoa-bridge container started with NUM_IN_TRANSFERS = 1 (verified via SSH `docker inspect`)
21:45:31      aoa-bridge: upstream connected; piping (in_ep=0x81, out_ep=0x01)
              [10 s gap: Caddy blocked on Read waiting for h2c preface bytes over USB]
21:45:41.205  Caddy: http2: server connection from 127.0.0.1:<port>
              Caddy: wrote SETTINGS MAX_FRAME_SIZE=1048576, MAX_CONCURRENT_STREAMS=250
              Caddy: read SETTINGS, ACK exchange
              Caddy: read WINDOW_UPDATE, read HEADERS stream=3 (GET /captures, 99 bytes, 8 HPACK fields all decoded cleanly)
21:45:41.207  Caddy: http2: Framer wrote GOAWAY len=8 LastStreamID=3 ErrCode=FRAME_SIZE_ERROR  ← 2 ms after HEADERS
21:45:41.336  Caddy: stream 3 completes 200 (already in-flight, within LastStreamID)
21:45:42.208  Caddy: GOAWAY close timer fires; closes TCP
21:45:42.605  Phone OkHttp: StreamResetException REFUSED_STREAM on streams 5, 7, 9
```

Bridge moved only **444 bytes phone→TCP** across the entire 11-second TCP lifetime. The first ~160 bytes (preface + SETTINGS + WINDOW_UPDATE + HEADERS for `/captures`) parsed fine. The corruption is in the next ~284 bytes — the frame header that should have followed HEADERS but decoded to a bogus `Length` > 1 MB.

### REFUSED_STREAM vs FRAME_SIZE_ERROR: same bug, different vantage

The phone-side `StreamResetException: REFUSED_STREAM` is the downstream symptom of the box-side FRAME_SIZE_ERROR GOAWAY. Sequence: Caddy emits `GOAWAY LastStreamID=3`, then closes; phone's in-flight streams 5/7/9 (sent after the GOAWAY) exceed LastStreamID, so Caddy refuses them with RST_STREAM REFUSED_STREAM. Go's framer error code (FRAME_SIZE_ERROR) only appears on the GOAWAY itself; client-side OkHttp just sees its concurrent streams getting RST'd. Same root cause as the prior FRAME_SIZE_ERROR-on-cold-start memo.

### Why FRAME_SIZE_ERROR with no intervening `read frame` event

In Go's `x/net/http2`, `wrote GOAWAY ErrCode=FRAME_SIZE_ERROR` is emitted from exactly one place: `processFrameFromReader` when `Framer.ReadFrame()` returns `ErrFrameTooLarge`. That error fires when the framer reads a 9-byte frame header whose 24-bit `Length` field decodes to a value greater than `Framer.MaxReadFrameSize` (default 1 MB). **The framer errors before logging the frame**, which is exactly why the trace shows no `read frame X` line between the HEADERS read and the GOAWAY.

### The byte path

`phone OkHttp → JNI Execute() → AccessoryDescriptor.write() → USB BULK OUT to ZED → aoa-bridge USB BULK IN endpoint 0x81 → on_in_complete callback → upstream TCP socket sendall → Caddy framer`

### Falsified hypothesis: parallel USB IN transfer completion-order race

`docker/aoa-bridge/src/aoa_bridge/main.py:41` was changed from `NUM_IN_TRANSFERS = 4` to `NUM_IN_TRANSFERS = 1` (path B). The image was rebuilt and deployed via `uv run install-zed --build` on the host. SSH verification on the box at repro time confirmed `placeframe-aoa-bridge-1` was running the new code (container started 21:45:26, code change present). The cold-start FRAME_SIZE_ERROR **still reproduced** at 21:45:41.207. Hypothesis is **falsified at the byte level** — parallel USB completion ordering is not the corruption source.

### Hypothesis triage (current)

| # | Hypothesis | Status |
|---|---|---|
| 1 | Server-side stale-connection close on first real request after extended SETTINGS-only idle | Ruled out — TCP/h2 connection was seconds old, not idle for 74 s. |
| 2 | `SETTINGS_MAX_CONCURRENT_STREAMS=1` on the server | Ruled out — Caddy advertises `MAX_CONCURRENT_STREAMS=250`. |
| 3 | `SETTINGS` handshake race on cold start | Ruled out — proper SETTINGS+ACK exchange precedes stream 3. |
| 4 | aoa-bridge parallel-USB-IN completion-order race (`NUM_IN_TRANSFERS=4`) | **Falsified by direct test at `NUM_IN_TRANSFERS=1`.** |
| **5 (new)** | **TCP-direction concurrency in the bridge.** `_pump_upstream_to_usb` calls `state.upstream.recv()` without `socket_lock`; `on_in_complete` calls `state.upstream.sendall()` with it. Read and write are independent at TCP layer, but there may be shared mutable state on the libusb transfer or buffer side. | Open — needs code re-read. |
| **6 (new)** | **OkHttp client-side write interleaving across JNI.** UI fires `/status` and `/captures` near-simultaneously. OkHttp's `Http2Writer` should serialize, but the JNI boundary to `AoaAccessoryClient.java` might interleave writes to the ParcelFileDescriptor. | Open — discriminated by enabling phone-side OkHttpH2 frame log. |
| **7 (new)** | **Something else upstream of the bridge** (libusb transfer recycling, kernel BULK-IN reassembly, ParcelFileDescriptor framing on the Android side). | Open — only worth pursuing if (5) and (6) are both eliminated. |

### Logging transport: stable

Box-Loki + box-Alloy + phone LogDrain + host-Caddy push are all working. Five box services (`zed-capture`, `aoa-gateway`, `aoa-bridge`, `aoa-loki`, `aoa-alloy`) visible in box-Loki with `box_id=1420825014984` external label. Phone-side LogDrain returns Loki query responses over AOA, host-Caddy push returns 204. Host-Loki has all streams. GODEBUG `http2debug=2` and Caddy DEBUG remain enabled for diagnosis. The OkHttp h2 frame log instrumentation (`service=capture-tool` Tag=`OkHttpH2`, JUL `okhttp3.internal.http2.Http2` → logcat → LokiSink) is wired and **proven** — two stray `OkHttpH2` lines did make it into Loki during the latest repro, but only two, because `READ_LOGS` was never granted on the manually-installed APK (see "Pending threads" #1).

### Branch state

- Current branch: `fix/install-zed-aoa-gateway-and-pull-logging`
- Working tree: `apps/AndroidMobile/Assets/Scripts/Capture/CaptureController.cs` and `ZedCaptureController.cs` modified (UI diagnostics); `.claude/scheduled_tasks.lock` present (runtime artifact, ignored).
- `docker/aoa-bridge/src/aoa_bridge/main.py:41` is committed as `NUM_IN_TRANSFERS = 1` and deployed to the box. **Do not revert this in code yet** — keeping the diagnostic constraint narrows hypothesis space. Revert as part of the cleanup commit only after the actual root cause lands.

## Decisions

### Diagnostic strategy: stay Loki-native, no tcpdump

Originally considered tcpdump on the box's loopback as the strongest single move (ground truth at Caddy's vantage). User pushed back: "are you saying we cannot get this data via our current process of shipping loki logs through the android mobile app to the backend?" Re-evaluated and confirmed Loki-only is sufficient — Caddy GODEBUG already logs every frame read on the server side, and OkHttp's JUL `Http2` frame logger gives the matching phone-side trace. Diff the two streams to localize the corruption. tcpdump is a third-tier fallback only if both Loki paths leave us blind.

### Diagnostic transport architecture: direct phone↔box-Loki + direct phone↔host-Loki

(Unchanged from prior version.) Phone reaches box-Loki via box-Caddy `/loki/*`. Phone pushes to host-Loki via host-Caddy `/loki/api/v1/push` with the existing Bearer token. 72 h retention on box-Loki. Caddy/Loki/Alloy bind `127.0.0.1` on the box. AOA pipe is the sole route.

### `GODEBUG=http2debug=2` and Caddy DEBUG: kept past diagnosis

Both still on in deployed `compose.rig.yml`. Cleanup is a later, separate commit after root cause lands.

### Phone-side: OkHttp h2 frame logging stays

The `JUL → logcat → LokiSink` wiring in `AoaAccessoryClient.java` (static initializer) plus the `OkHttpH2:V` whitelist in `LogcatRelay.cs` is canonical and kept past diagnosis.

### Cheap fixes are not the first fix

Lowering OkHttp's `readTimeout` from 60 s and plumbing the C# `CancellationToken` through JNI to `Call.cancel()` reduce recovery time of a failure mode that shouldn't exist. The principled fix is to stop the byte corruption. JNI cancellation plumbing is a separate, later commit.

### `uv run install-zed --build` is the deploy path (not manual rebuild + ssh-load)

The `--build` flag was just added to `up`/`install-zed` (commit `747950f1`). Use it from the host. The sandbox cannot run `uv run install-zed --build` (it shells out to `nmcli`); user runs it. Manual `compile-unity` + `adb install` paths skip `pm grant android.permission.READ_LOGS`, which is why OkHttp frame logs are missing. See `.pulsar/memories/unity-build-install-surface-refactor.md` for the planned refactor of these install surfaces.

## Open questions

- **Where exactly is the corruption?** Bridge (between USB read and TCP write), phone (OkHttp's writes to the AOA file descriptor), or upstream of OkHttp (JNI marshaling, ParcelFileDescriptor, kernel USB driver, AOA accessory firmware)? Pending-thread #1 is the next diagnostic that narrows this.
- **Is the OUT path symmetric?** The diagnosis is on phone→box (IN at the bridge, request bytes) because that's what trips Caddy. The bridge's OUT path (box→phone) might have a mirror race. Worth checking once IN is fixed, in case the box→phone direction has latent corruption that just happens not to trip OkHttp's framer-strictness.

## Key files

- `docker/aoa-bridge/src/aoa_bridge/main.py:41` — `NUM_IN_TRANSFERS = 1` (was `4` until the falsification test).
- `docker/aoa-bridge/src/aoa_bridge/main.py:120` — `on_in_complete` callback. `sendall(bytes(transfer.getBuffer()[:length]))` is where USB-IN bytes hit the TCP socket. Hex-dump instrumentation, if needed (pending-thread #2), goes here.
- `docker/aoa-bridge/src/aoa_bridge/main.py` `_pump_upstream_to_usb` — TCP recv side; `state.upstream.recv()` is called without `socket_lock`. Audit for shared mutable state with the IN side (hypothesis 5).
- `apps/AndroidMobile/Assets/Plugins/Android/aoa-accessory-filter.androidlib/src/main/java/io/placeframe/android/AoaAccessoryClient.java` — OkHttp client config (`.readTimeout(60, TimeUnit.SECONDS)`, `ConnectionPool(1, 1, TimeUnit.DAYS)`) plus the JUL h2-frame-log static initializer. **Keep.**
- `apps/AndroidMobile/Assets/Scripts/Capture/ZedCaptureController.cs` — single Loki query/push LogDrain loop. `HealthPollLoop` sets `requestCts.CancelAfter(2 s)` which is still a lie until JNI cancellation is plumbed.
- `apps/AndroidMobile/Assets/Scripts/AndroidAoaHttpHandler.cs` — `ExecuteOverAoa` synchronously calls `AoaJni.Execute` over JNI; cancellation isn't plumbed to OkHttp's `Call.cancel()`. The 60 s `readTimeout` wall lives here in spirit.
- `apps/AndroidMobile/CLAUDE.md` — explains why h2c-prior-knowledge is mandatory for the AOA pipe (concurrent requests on a single duplex stream).
- `docker/aoa-gateway/Caddyfile` — `/loki/*` reverse-proxy handle, bind to `127.0.0.1:9000`, `log { level DEBUG output stdout format json }` still on for diagnosis.
- `docker/zed-capture/compose.rig.yml` — `aoa-loki` and `aoa-alloy` services; `GODEBUG: http2debug=2` still on for diagnosis.
- `docker/aoa-loki/config.yaml` — monolithic, filesystem, 72h retention, `127.0.0.1:3100`.
- `docker/aoa-alloy/config.alloy` — `discovery.docker` on box's docker socket, `ZED_BOX_ID` external label.
- `scripts/install_zed.py` (or wherever `install-zed` lives) — should `pm grant android.permission.READ_LOGS` as part of the install flow. See `.pulsar/memories/unity-build-install-surface-refactor.md`.
- `.pulsar/memories/aoa-handshake-debug-wrong-track.md` — prior memo that recorded the stale-idle hypothesis being wrong; companion.
- `.pulsar/memories/unity-build-install-surface-refactor.md` — captures the broader refactor of `install`/`compile-unity` so READ_LOGS grant is automatic.

## Pending threads

1. **Grant `READ_LOGS` on the phone, repro, diff OkHttp writes against Caddy reads in Loki.** This is the next move.
   - One command, no rebuild: `adb shell pm grant com.outernet.captureapp android.permission.READ_LOGS`
   - Repro cold start (close app, replug AOA cable or `adb shell am force-stop com.outernet.captureapp` then open Capture Tool, hit Captures tab).
   - Query Loki: `{app="capture-tool"} | json | Tag="OkHttpH2"` over the repro window — every frame OkHttp wrote (`>>`) and read (`<<`), hex-prefixed by stream/length/type.
   - Cross-reference against `{service="aoa-gateway"}` `read frame` lines from the box.
   - **Expected discrimination**:
     - If OkHttp wrote a frame with `Length > 1 MB` → corruption is upstream of OkHttp (bug in client h2 layer, unlikely) or the test apparatus is lying.
     - If OkHttp wrote sane frames and Caddy read garbage → corruption is on the wire (bridge or below). Move to thread #2.
     - If Caddy's last successfully-read frame was followed by N missing bytes, then bogus → byte loss/duplication, not byte mutation. Different repair shape.

2. **If thread #1 confirms bridge-or-below corruption: add ECONNRESET-triggered hex dump in the bridge.** Patch `on_in_complete` (or the TCP-fail handler) to log the last ~1 KB of bytes-written-to-TCP whenever `sendall` raises or upstream resets. Loki-native — same redeploy cycle. Identifies the exact corrupted bytes for forensic comparison.

3. **If threads #1 and #2 still leave us blind**: tcpdump on the box's loopback at port 9001 during repro. Third-tier fallback. Carries the box-touching cost.

4. **Once root cause lands**: revert `NUM_IN_TRANSFERS` back to a sensible parallelism (likely 4) in the same commit as the durable fix, since the serialization was a discriminator, not a fix.

5. **JNI cancellation plumbing fix.** Independent of root cause. `AndroidAoaHttpHandler.ExecuteOverAoa` currently consults `CancellationToken` only for the response body stream, not the synchronous `AoaJni.Execute` call. Plumb `Call.cancel()` over JNI so `requestCts.CancelAfter(2 s)` in `ZedCaptureController.HealthPollLoop` actually fires at 2 s. Separate commit.

6. **Cleanup commit.** Once cold-start RST no longer reproduces:
   - Remove `GODEBUG: http2debug=2` from `docker/zed-capture/compose.rig.yml`.
   - Revert Caddy log level from `DEBUG` to default in `docker/aoa-gateway/Caddyfile` (keep `format json` and `/loki/*` reverse-proxy handle).
   - Keep box-Alloy + box-Loki + phone-Loki-relay transport — durable infrastructure.
   - Keep OkHttp JUL→logcat→Loki wiring and `OkHttpH2:V` whitelist entry.

7. **Optional: lower OkHttp `readTimeout`** in `AoaAccessoryClient.java` from 60 s to 3–5 s. Defense-in-depth so any future hang recovers fast. Trivial. Do this **after** the root-cause fix is verified — not before, or we'd mask the bug.

## Operational notes for the next session

- `uv run install-zed --build` cannot run inside the COI sandbox; it shells out to `nmcli`. User runs it on the physical host with ZED cabled. Everything else (`uv run up`, `uv run lock-python`, `uv run generate-clients`, `uv run compile-unity`, `adb install`) works inside the sandbox.
- Manual `compile-unity` + `adb install` paths skip the `pm grant READ_LOGS` step. Either run `uv run install-zed --build` from the host (cleanest), or after a manual install run `adb shell pm grant com.outernet.captureapp android.permission.READ_LOGS` before reproducing.
- Force-push to `fix/install-zed-aoa-gateway-and-pull-logging` is authorized.
- Codegen commits must have message exactly `Run generate-clients`; no body, no rationale. Prose and code commit separately.
- `uv run loki-query '{service="aoa-gateway"}' --since 5m --limit 200` for queries. Pass `--raw` for box-side entries (the pretty-printer expects Unity/structlog shape).
- `service` and `service_name` are interchangeable in Loki LogQL — Loki auto-derives `service_name` from common label names including `service`.
- `uv run --no-sync preflight` tears down + re-brings-up `compose.postgres.yml`; interrupts a running stack.
- SSH access to the box is available (used during the latest repro to read the box-Caddy log and verify the deployed `NUM_IN_TRANSFERS` value). Prefer Loki-native diagnostics; reach for SSH only when Loki gaps it.
