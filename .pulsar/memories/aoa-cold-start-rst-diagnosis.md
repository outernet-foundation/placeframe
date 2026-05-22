---
updated: 2026-05-22
---

# AOA cold-start RST: GOAWAY FRAME_SIZE_ERROR, byte corruption on the wire, aoa-bridge's parallel USB IN transfers are prime suspect

## Goal

Diagnose why the Capture Tool's "Captures" tab stays blank for ~60 s after login when the phone is wired to the ZED box over the AOA pipe. After two prior sessions of detour and a transport refactor that finally landed cross-side wire-level visibility into Loki, the **root cause is now known**: Caddy sends `GOAWAY ErrCode=FRAME_SIZE_ERROR` ~48 ms after reading the first HEADERS frame on a fresh TCP connection, because some frame header arriving over the AOA pipe decodes to a `Length` > 1 MB (Caddy's `MaxReadFrameSize` default). OkHttp on the phone cannot produce that — it `require`s `length ≤ INITIAL_MAX_FRAME_SIZE = 16384` before serializing each frame — so the bytes are being **corrupted on the wire** between phone OkHttp and Caddy. Prime suspect: aoa-bridge's `NUM_IN_TRANSFERS=4` parallel USB BULK IN transfers, whose libusb completion order is not guaranteed to match submission order, and whose `on_in_complete` callbacks each `sendall` independently to the upstream TCP socket — interleaving h2 frame fragments out of order.

This memory is targeted at `/diagnose` (extra confirmation) then `/implement` (fix). The transport, repro path, and instrumentation are all in place; the next session reads aoa-bridge's USB-to-TCP loop and either confirms the parallel-completions theory and fixes it (e.g. serialize completions through a single writer task) or rules it out and looks at the next byte-corruption candidate.

## State

### What the wire actually shows (2026-05-22 21:00:03 → 21:01:19 UTC repro)

Cross-correlated trace from `service=aoa-bridge`, `service=aoa-gateway` (Caddy structured + GODEBUG `http2debug=2` stderr), and `service=capture-tool` (OkHttp h2 frame log under Tag=`OkHttpH2`):

```
21:00:03.098  aoa-bridge: upstream connected; piping (in_ep=0x81, out_ep=0x01)  ← TCP accept
              [75s blocked: Caddy reading h2c preface; bytes don't flow yet]
+78.848 ms*   Caddy: http2: server connection from 127.0.0.1:36678               ← preface arrives
+78.848       Caddy: wrote SETTINGS MAX_FRAME_SIZE=1048576, MAX_CONCURRENT_STREAMS=250
+78.848       Caddy: read SETTINGS INITIAL_WINDOW_SIZE=16777216 (from client)
+78.849       Caddy: wrote SETTINGS flags=ACK
+78.850       Caddy: read HEADERS stream=3 (GET /captures)                       ← 1 ms after handshake
+78.898       Caddy: wrote GOAWAY LastStreamID=3 ErrCode=FRAME_SIZE_ERROR        ← 48 ms gap, no intervening frame
+79.028       Caddy: /captures upstream completes 200                            ← in-flight stream finishes
+79.899       Caddy: GOAWAY close timer fires; closing conn
21:01:19.899  aoa-bridge: upstream read error: [Errno 104] Connection reset by peer
21:01:19.951  aoa-bridge: pipe done uptime=76s
21:01:20.954  aoa-bridge: accessory ready vid=18d1 pid=2d01; opening pipe (re-handshake)
```

(* The bridge says `uptime=76s` because that's how long the AOA pipe was open. The TCP/h2 connection itself was 1 second long — Caddy logs `http2: server connection from ...` when it reads the h2c preface, not at TCP accept. The 75 s gap is Caddy blocked on `Read` waiting for the preface bytes to arrive over USB.)

### Why FRAME_SIZE_ERROR with no intervening `read frame` event

In Go's `x/net/http2`, `wrote GOAWAY ErrCode=FRAME_SIZE_ERROR` is emitted from exactly one place: `processFrameFromReader` when `Framer.ReadFrame()` returns `ErrFrameTooLarge`. That error fires when the framer reads a 9-byte frame header whose 24-bit `Length` field decodes to a value greater than `Framer.MaxReadFrameSize` (default 1 MB). **The framer errors before logging the frame**, which is exactly why the GODEBUG trace shows a 48 ms gap between the HEADERS read at `+0850 ms` and the GOAWAY at `+0898 ms` with no `read frame X` line in between.

So between those two events, Caddy received bytes whose first three bytes decoded to a `Length` field > 1 048 576. The bytes were correct on the phone; they were corrupted somewhere on the wire.

### The byte path

`phone OkHttp → JNI Execute() → AccessoryDescriptor.write() → USB BULK OUT to ZED → aoa-bridge USB BULK IN endpoint 0x81 → on_in_complete callback → upstream TCP socket sendall → Caddy framer`

### Why aoa-bridge's 4 parallel IN transfers are the prime suspect

`docker/aoa-bridge/src/aoa_bridge/main.py:43` declares `NUM_IN_TRANSFERS = 4`. The submission loop at lines 351-355 submits four 256 KB BULK IN transfers to endpoint 0x81 simultaneously. As each transfer completes asynchronously on libusb's event thread, `on_in_complete` (line 120) `sendall`s the buffer contents to the upstream TCP socket (line 136) **in completion order, not submission order**. libusb only guarantees ordering at submission; completion ordering is "the order the kernel signals completion," which for BULK transfers is not contractually serial across pending submissions on the same endpoint.

If a single h2 HEADERS frame (or the 9-byte frame header alone) straddles two USB transfers, and those two transfers complete out-of-order, the bytes get reassembled in the wrong sequence — corrupting the frame header's `Length` field. Three random middle bytes presented as the `Length` field of a 9-byte header will, on average, decode to a value > 1 MB ~94% of the time (anything ≥ `0x100000`), perfectly matching the `FRAME_SIZE_ERROR` signature.

This also explains why the failure is **cold-start specific and intermittent**: when traffic is steady, h2 frames have settled into stable ordering relative to USB transfer boundaries; on cold start, the SETTINGS-handshake burst plus the immediate login-time concurrent request burst hits the rate at which transfer-completion races can scramble frame boundaries.

### Three hypotheses, now triaged

| # | Hypothesis | Status |
|---|---|---|
| 1 | Server-side stale-connection close on first real request after extended SETTINGS-only idle | **Ruled out.** The TCP/h2 connection was 1 s old when the GOAWAY fired, not 74 s. The 74 s "idle" in the prior memo was the AOA-pipe-open-to-TCP-accept gap (USB enumerated, Caddy hadn't yet read a preface byte). |
| 2 | `SETTINGS_MAX_CONCURRENT_STREAMS=1` on the server | **Ruled out.** Caddy GODEBUG shows `wrote SETTINGS MAX_FRAME_SIZE=1048576, MAX_CONCURRENT_STREAMS=250`. |
| 3 | `SETTINGS` handshake race on cold start | **Ruled out.** Trace shows proper SETTINGS exchange + ACK before stream 3 opened. |
| **4 (new)** | **Byte corruption on the wire — aoa-bridge's parallel USB IN transfer completion-order race** | **Prime suspect.** Matches `FRAME_SIZE_ERROR` + 48 ms framer-failure gap + 1 MB `MaxReadFrameSize` ceiling exactly. |

### Logging transport: corrected shape landed and proven

The Alloy detour from the prior memo was reverted and replaced. Final shape (committed in `696d7f47`, then squashed and force-pushed to `fix/install-zed-aoa-gateway-and-pull-logging`):

- **box-Loki** (`aoa-loki` service, monolithic filesystem, 72 h retention, bound `127.0.0.1:3100`)
- **box-Alloy** (`aoa-alloy` service, `discovery.docker` scrape over box's own docker socket, sets `box_id` external label from `ZED_BOX_ID`, bound `127.0.0.1:12345`)
- **Caddy `/loki/*` reverse-proxy handle** on `aoa-gateway` so the phone reaches box-Loki through the AOA pipe with no extra listener
- **Phone-side**: `ZedCaptureController.cs` LogDrain collapsed from four bespoke `/logs/<source>` polls to a single `query_range` against box-Loki + a `/loki/api/v1/push` to host-Caddy with the existing Bearer token
- **Removed entirely**: `docker/api/src/routers/zed_box_logs.py`, `docker/zed-capture/src/routers/logs.py`, `docker/zed-capture/src/cursor_store.py`, the aoa-gateway Python supervisor idea, the per-line `service` field plumbing, the bespoke `/logs/aoa-gateway-h2debug` endpoint

`alloy validate`, `caddy validate`, `loki -verify-config`, and `uv run --no-sync preflight` all pass.

### End-to-end pipeline verified

After deploying the new transport and reproducing the cold-start failure, all five box services (`zed-capture`, `aoa-gateway`, `aoa-bridge`, `aoa-loki`, `aoa-alloy`) are visible in box-Loki with `box_id=1420825014984` external label, the phone-side LogDrain returns 135 KB query responses over AOA, the host-Caddy push returns 204, and host-Loki has all streams intact. `aoa-bridge` and `aoa-alloy` are quiet but discoverable — they only log on events. Cosmetic warning in host Loki: `"negative structured metadata bytes received" size=0` on every push — entries are ingested regardless.

The OkHttp h2 frame log instrumentation (`service=capture-tool` Tag=`OkHttpH2`, JUL `okhttp3.internal.http2.Http2` → logcat → LokiSink) is the canonical pattern and is **kept**.

### Branch state

- Current branch: `squash/zed-box-logging` (HEAD `e92e588c`)
- `fix/install-zed-aoa-gateway-and-pull-logging` force-pushed authorized; tip was byte-identical to `squash/zed-box-logging` through `bded64f5`, has since advanced with prose-only commits (`028e5c99` updating this memo, `e92e588c` adding `unity-build-install-surface-refactor.md`)
- Commits since squash base: `696d7f47` (fat code), `c61c177f` (forbid `typing.cast`), `baf328ea` (CODEGEN env in generate-clients), `94de9bbc` (ruff format on pre-existing debt), `bded64f5` (this memory v1), `028e5c99` (this memory v2 with FRAME_SIZE_ERROR root cause), `e92e588c` (`unity-build-install-surface-refactor.md`)
- Three superseded memos dropped in the squash: `aoa-gateway-caddy-field-injection.md`, `box-loki-log-shipping-refactor.md`, plus one other detour memo
- Working tree has `docker/aoa-bridge/src/aoa_bridge/main.py` modified (`NUM_IN_TRANSFERS = 1` for path-B diagnostic — see pending threads), `.claude/scheduled_tasks.lock` (runtime), `response.md` (scratch); user's stash@{0} preserves a pre-autosquash conflict on `config/calibration/global.json` for them to re-pop later

## Decisions

### Diagnostic transport architecture: direct phone↔box-Loki + direct phone↔host-Loki

Resolved during the in-session refactor (memo Q1, Q2, Q3, Q4):

- **Phone → box-Loki**: direct via box-Caddy `/loki/*`. zed-capture is a ZED-camera-capture service; routing log queries through it conflates concerns.
- **Phone → host-Loki**: direct via host-Caddy `/loki/api/v1/push` with the existing Bearer token from `Auth.GetOrRefreshToken()`. The API surface is for captures/sessions/auth; log shipping isn't its concern.
- **Retention**: 72 h on box-Loki.
- **Security**: Caddy, Loki, and Alloy all bind `127.0.0.1` on the box. The AOA pipe is the sole route the phone reaches box-Loki through; the wired-ethernet exposure considered earlier (Listener C on `:8084`) is gone.
- **Image pinning**: upstream Loki/Alloy digests in `compose.zed.bake.yml` + bind-mounted configs. No `docker/aoa-loki/Dockerfile` or `docker/aoa-alloy/Dockerfile`.

### `GODEBUG=http2debug=2` and Caddy DEBUG: kept past diagnosis for now

Both are still on in the deployed `compose.rig.yml`. Decision deferred until the fix lands and the failure no longer reproduces. Cleanup (env-gating or reverting Caddy to default log level) is a later, separate commit.

### Phone-side: OkHttp h2 frame logging stays

The `JUL → logcat → LokiSink` wiring in `AoaAccessoryClient.java` (static initializer) plus the `OkHttpH2:V` whitelist in `LogcatRelay.cs` is the canonical pattern and stays past diagnosis.

### Cheap fixes are not the first fix

Lowering OkHttp's `readTimeout` from 60 s and plumbing the C# `CancellationToken` through JNI to `Call.cancel()` are both worth doing — but they reduce the recovery time of a failure mode that shouldn't exist. The principled fix is to stop the byte corruption. JNI cancellation plumbing is a second, independent commit after the root-cause fix lands.

## Open questions

- **Does serializing aoa-bridge's USB IN completions actually fix it?** Hypothesis is strong but unconfirmed at the byte level. Two ways to confirm: (a) drop `NUM_IN_TRANSFERS` from 4 to 1, repro, see if `FRAME_SIZE_ERROR` disappears; (b) add a single-writer `asyncio.Queue` between `on_in_complete` and `sendall` so completions are reordered by submission-index before egress, repro. (a) is the cheap diagnostic; (b) is the durable fix shape.
- **Is the OUT path symmetric?** The diagnosis is on the phone→box (IN at the bridge, request bytes) direction because that's what triggers the FRAME_SIZE_ERROR. The bridge's OUT path (box→phone) might have the same race in mirror; worth checking once IN is fixed, in case the box→phone direction has a latent corruption that just happens not to trip OkHttp's framer-strictness.

## Key files

- `docker/aoa-bridge/src/aoa_bridge/main.py:43` — `NUM_IN_TRANSFERS = 4` declaration.
- `docker/aoa-bridge/src/aoa_bridge/main.py:120` — `on_in_complete` callback. `sendall(bytes(transfer.getBuffer()[:length]))` at line 136 is where the completion-order TCP write happens.
- `docker/aoa-bridge/src/aoa_bridge/main.py:351-355` — the submission loop that submits all four IN transfers simultaneously.
- `apps/AndroidMobile/Assets/Plugins/Android/aoa-accessory-filter.androidlib/src/main/java/io/placeframe/android/AoaAccessoryClient.java` — OkHttp client config (`.readTimeout(60, TimeUnit.SECONDS)`, `ConnectionPool(1, 1, TimeUnit.DAYS)`) plus the JUL h2-frame-log static initializer. **Keep.**
- `apps/AndroidMobile/Assets/Scripts/Capture/ZedCaptureController.cs` — single Loki query/push LogDrain loop after the 696d7f47 collapse. `HealthPollLoop` sets `requestCts.CancelAfter(2 s)` which is still a lie because of the JNI cancellation issue.
- `apps/AndroidMobile/Assets/Scripts/AndroidAoaHttpHandler.cs` — `ExecuteOverAoa` synchronously calls `AoaJni.Execute` over JNI; cancellation isn't plumbed to OkHttp's `Call.cancel()`. The 60 s `readTimeout` wall lives here in spirit.
- `apps/AndroidMobile/CLAUDE.md` — explains why h2c-prior-knowledge is mandatory for the AOA pipe (concurrent requests on a single duplex stream).
- `docker/aoa-gateway/Caddyfile` — `/loki/*` reverse-proxy handle, bind to `127.0.0.1:9000`, `log { level DEBUG output stdout format json }` still on for diagnosis.
- `docker/zed-capture/compose.rig.yml` — `aoa-loki` and `aoa-alloy` services; `GODEBUG: http2debug=2` still on for diagnosis.
- `docker/aoa-loki/config.yaml` — monolithic, filesystem, 72h retention, `127.0.0.1:3100`.
- `docker/aoa-alloy/config.alloy` — `discovery.docker` on box's docker socket, `ZED_BOX_ID` external label.
- `.pulsar/memories/aoa-handshake-debug-wrong-track.md` — prior memo that recorded the stale-idle hypothesis being wrong; companion to this one.

## Pending threads

1. **Confirm the parallel-completions hypothesis cheaply — path B initiated, awaiting host-side deploy + repro.** Edit applied in the working tree: `docker/aoa-bridge/src/aoa_bridge/main.py:41` now reads `NUM_IN_TRANSFERS = 1` (was `4`, and the two-line comment above it about "multiple in-flight transfers" was removed by the same edit since it no longer described the code). User chose path B over path A (grant `READ_LOGS` + OkHttpH2 frame trace) when surfaced as a discriminator. Next: rebuild aoa-bridge, `uv run install-zed --build` from the physical host (this command cannot run inside the COI sandbox; user runs it), repro cold start. Expected result: no `FRAME_SIZE_ERROR` in `service=aoa-gateway` GODEBUG, no `>> RST_STREAM`/`ConnectionShutdownException` in `service=capture-tool`, captures tab populates immediately. This is a diagnostic, not the durable fix — single-in-flight cripples throughput.

2. **If (1) confirms: write the durable fix.** Two shapes worth considering:
   - **(a) Single writer task with submission-indexed reorder buffer.** Each transfer gets a monotonic submission index at submit time; `on_in_complete` enqueues `(index, bytes)` onto an `asyncio.Queue`; a single consumer task pops in index order (using a small priority-heap / dict-of-waiters) and `sendall`s. Preserves the parallel-IN throughput benefit. ~30 lines.
   - **(b) Lock around `sendall` and rely on libusb's documented "completion order matches submission order on a single endpoint for bulk transfers under linear demand" (verify this claim — it may not actually hold).** Cheaper but rests on a fragile assumption about kernel scheduling.

   (a) is the principled answer. (b) might be enough if libusb's docs actually guarantee what we'd need.

3. **Check OUT path symmetry.** Once IN is fixed, examine `docker/aoa-bridge/src/aoa_bridge/main.py` for the OUT-side write loop. If it also uses parallel transfers with `on_out_complete`-driven egress, apply the same single-writer pattern. If it's already serial, no action needed.

4. **JNI cancellation plumbing fix.** Independent of the root-cause fix. `AndroidAoaHttpHandler.ExecuteOverAoa` currently consults `CancellationToken` only for the response body stream, not the synchronous `AoaJni.Execute` call. Plumb `Call.cancel()` over JNI so `requestCts.CancelAfter(2 s)` in `ZedCaptureController.HealthPollLoop` actually fires at 2 s instead of waiting the full OkHttp `readTimeout`. Second, separate commit after pending-thread #2.

5. **Cleanup commit.** Once the cold-start RST no longer reproduces:
   - Remove `GODEBUG: http2debug=2` from `docker/zed-capture/compose.rig.yml`.
   - Revert Caddy log level from `DEBUG` to default in `docker/aoa-gateway/Caddyfile` (keep the `format json` and the `/loki/*` reverse-proxy handle).
   - Keep the box-Alloy + box-Loki + phone-Loki-relay transport — it's durable infrastructure.
   - Keep the OkHttp JUL→logcat→Loki wiring and the `OkHttpH2:V` whitelist entry.

6. **Optional: lower OkHttp `readTimeout` in `AoaAccessoryClient.java`.** From 60 s to 3-5 s. Defense-in-depth so that if any future failure mode leaves a stream hanging, recovery is fast. Trivial commit. Do this after the root-cause fix has been verified to actually fix the cold-start path — not before, or we'd be masking the bug.

## Operational notes for the next session

- `uv run install-zed --build` cannot run inside the COI sandbox; it shells out to `nmcli` which isn't present. The user runs that command on the physical host with the ZED cabled. Everything else (`uv run up`, `uv run lock-python`, `uv run generate-clients`, `uv run compile-unity`, `adb install`) works inside the sandbox.
- Force-push to `fix/install-zed-aoa-gateway-and-pull-logging` is authorized.
- Codegen commits must have message exactly `Run generate-clients`; no body, no rationale. Prose and code commit separately.
- `uv run loki-query '{service="aoa-gateway"}' --since 5m --limit 200` for queries. The `loki-query` pretty-printer shows `[?]` for box-side entries because it expects Unity/structlog shape — pass `--raw` for now, or fix later.
- `service` and `service_name` are interchangeable in Loki LogQL — Loki auto-derives `service_name` from common label names including `service`.
- `uv run --no-sync preflight` tears down + re-brings-up `compose.postgres.yml`; interrupts a running stack.
