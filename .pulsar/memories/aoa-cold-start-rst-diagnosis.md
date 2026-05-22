---
updated: 2026-05-22
---

# AOA cold-start RST: recovery landed (bug A), root-cause corruption still reproduces (bug B) at phone→box offset ~161

## Goal

Capture Tool's "Captures" tab used to stay blank for ~60 s after login when the phone was wired to the ZED box over the AOA pipe. Diagnosis decomposed the failure into **two independent bugs**:

- **Bug A — recovery.** When Caddy tore down the upstream TCP socket for any reason, the phone's pooled h2c session desynced; OkHttp kept reusing the dead connection for 60 s (its `readTimeout`) before opening a new one. **Fixed** on this branch.
- **Bug B — root cause.** On the very first phone→box byte stream after entering accessory mode, the bytes at offset ~161 are garbage. Caddy reads a 9-byte frame header whose `Length` decodes to >1 MB, emits `GOAWAY ErrCode=FRAME_SIZE_ERROR`, and tears down — which is what triggers bug A. Mechanism still unknown. **Still reproducing.**

With bug A fixed, the user-visible symptom is no longer a 60 s blank tab — it's now "one extra AOA permission dialog on cold start, then the app works." Better but not invisible. Bug B is the thing left to chase.

This memory is targeted at `/diagnose`. The transport, repro path, logging, and prior-hypothesis-elimination are all in place; the next session executes the highest-information **byte-level** diagnostic step (deploy the `e03125e6` scaffolding, repro, diff hex dump against OkHttp `>>` writes to localize the corruption).

## State

### What landed since the prior memo

| Commit | Title | Role |
|---|---|---|
| `55885907` | Reset USB device on upstream tear-down so phone drops pooled h2c session | **Bug A fix.** `_reset_device(handle)` call in `_run_once()`'s `finally` block calls `handle.resetDevice()` (libusb port-reset). Phone observes accessory-FD invalidation, OkHttp drops the pooled h2c session, next request opens a fresh connection. Tolerates `LIBUSB_ERROR_NOT_FOUND` (device may already have vanished). Also reverts `NUM_IN_TRANSFERS` from 1 back to 4 — the serialization was a discriminator for the falsified parallel-USB hypothesis, not part of the fix. |
| `e03125e6` | TO BE DELETED: scaffolding hex dump of first IN bytes + logcat history | Two diagnostic-only additions for chasing bug B: (1) hex-dump of first ~512 bytes of phone→box IN traffic, emitted from `on_in_complete` once per session, to capture the corruption pattern at byte ~161. (2) `LogcatReader.java`: dropped `-T 1` so logcat reader picks up buffered history, since cold-start OkHttp frames otherwise predate the reader's start and never reach Loki. Marked TO BE DELETED in commit title — revert wholesale once bug B is rooted. |

### Latest repro after bug-A fix landed (2026-05-22 22:23 UTC window)

Same cold-start FRAME_SIZE_ERROR, exact same shape as the prior repro — bug A's fix doesn't address it:

```
22:23:57.642  Caddy: server connection from 127.0.0.1:42816
              SETTINGS+WINDOW_UPDATE exchange clean
              read HEADERS flags=END_STREAM|END_HEADERS stream=3 len=100  (GET /captures decoded fine)
22:23:57.689  Framer wrote GOAWAY LastStreamID=3 ErrCode=FRAME_SIZE_ERROR  ← 47 ms after HEADERS
22:23:58.690  GOAWAY close timer fired; closes TCP
22:23:58.???  aoa-bridge: upstream read error: [Errno 104] Connection reset by peer
22:23:59.???  aoa-bridge: _reset_device(handle) fires  ← bug-A fix kicks in
              libusb returns LIBUSB_ERROR_NOT_FOUND (device already vanished from libusb's POV) — handled gracefully
22:24:00.???  Clean re-handshake; phone re-enumerates → user sees second AOA dialog
              After dialog 2: fresh AOA enter, fresh OkHttp pool → no corruption → works
```

Bridge byte totals on the failed connection: 84 B → phone, 445 B ← phone. Of the 445 B from phone, the first ~161 B parsed fine (preface + SETTINGS + WINDOW_UPDATE + HEADERS for `/captures`). The corruption is in the next ~284 B — the frame header that should have followed HEADERS but decoded to a bogus `Length` > 1 MB.

### Why FRAME_SIZE_ERROR with no intervening `read frame` event

In Go's `x/net/http2`, `wrote GOAWAY ErrCode=FRAME_SIZE_ERROR` is emitted from exactly one place: `processFrameFromReader` when `Framer.ReadFrame()` returns `ErrFrameTooLarge`. That error fires when the framer reads a 9-byte frame header whose 24-bit `Length` field decodes to a value greater than `Framer.MaxReadFrameSize` (default 1 MB). **The framer errors before logging the frame**, which is exactly why the trace shows no `read frame X` line between the HEADERS read and the GOAWAY.

OkHttp can't write a frame > 16 KB — it `require`s `length ≤ INITIAL_MAX_FRAME_SIZE = 16384` before serializing. So the bytes were correct at the phone OkHttp boundary; corruption is downstream of OkHttp.

### The byte path

`phone OkHttp → JNI Execute() → AccessoryDescriptor.write() → USB BULK OUT to ZED → aoa-bridge USB BULK IN endpoint 0x81 → on_in_complete callback → upstream TCP socket sendall → Caddy framer`

### Hypothesis triage (current)

| # | Hypothesis | Status |
|---|---|---|
| 1 | Server-side stale-connection close on first real request after extended SETTINGS-only idle | Ruled out — TCP/h2 connection was 1 s old, not 76 s. |
| 2 | `SETTINGS_MAX_CONCURRENT_STREAMS=1` on the server | Ruled out — Caddy advertises `MAX_CONCURRENT_STREAMS=250`. |
| 3 | `SETTINGS` handshake race on cold start | Ruled out — proper SETTINGS+ACK exchange precedes stream 3. |
| 4 | aoa-bridge parallel-USB-IN completion-order race (`NUM_IN_TRANSFERS=4`) | Falsified by direct test at `NUM_IN_TRANSFERS=1`; same repro at both values. |
| 5 | TCP-direction concurrency in the bridge | Open — needs code re-read. |
| 6 | OkHttp client-side write interleaving across JNI | Open — discriminate by enabling phone-side OkHttpH2 frame log AND grabbing buffered logcat history (commit `e03125e6` does both). |
| 7 | Something else upstream of the bridge (libusb transfer recycling, kernel BULK-IN reassembly, ParcelFileDescriptor framing on the Android side, AOA accessory firmware) | Open — only worth pursuing if (5) and (6) are both eliminated. |

The hex dump in `e03125e6` is the discriminator across (5)/(6)/(7): the bytes at offset ~161 forensically identify *which side* of the bridge produced the bad frame header.

### Logging transport: now solid (Alloy + box-Loki + phone-relay)

The whole box→host log shipping refactor landed during the same diagnostic cycle (`696d7f47` "Add box-side log shipping: Alloy + Loki + phone relay to host Loki"). All 5 box services (`zed-capture`, `aoa-gateway`, `aoa-bridge`, `aoa-loki`, `aoa-alloy`) emit to a box-local Loki monolithic instance via Grafana Alloy on the docker socket. Phone polls box-Loki via Caddy `/loki/*` over AOA and pushes to host-Loki via Caddy `/loki/api/v1/push` with the existing Bearer token. 72 h retention on box-Loki. All listeners bind `127.0.0.1` on the box; AOA pipe is the sole route.

GODEBUG `http2debug=2` is still on for `aoa-gateway` for diagnosis. Caddy DEBUG level is still on. Both come off in the cleanup commit after bug B is rooted.

OkHttp h2 frame logging (`okhttp3.internal.http2.Http2` JUL logger → logcat tag `OkHttpH2` → LogcatRelay → LokiSink with `app=capture-tool`) is wired in `AoaAccessoryClient.java`'s static initializer and the `LogcatRelay.cs` whitelist. **Until commit `e03125e6`, the cold-start OkHttp frames were missed** because `LogcatReader.java` started with `-T 1` (only new lines from now), and OkHttp's first writes happened before that reader started. `e03125e6` drops `-T 1` so buffered history is included.

### Branch state

- Branch: `squash/zed-box-logging` (this is the post-squash branch; the original `fix/install-zed-aoa-gateway-and-pull-logging` was force-pushed to match)
- Tip: `e03125e6` (TO BE DELETED scaffolding) on top of `55885907` (the durable bug-A fix)
- Working tree: clean except for untracked `.claude/scheduled_tasks.lock` and `response.md` (both runtime artifacts, ignored)
- `docker/aoa-bridge/src/aoa_bridge/main.py:41` is committed as `NUM_IN_TRANSFERS = 4` (reverted alongside the bug-A fix).
- The `bded64f5 Add aoa-cold-start-rst-diagnosis memo` commit anchors this file in the squash; updates ride on top as separate prose commits per CLAUDE.md.

## Decisions

### Bug A vs bug B: fix recovery first, root-cause separately

The bug-A fix (`55885907`) is durable, narrow, and removes the user-visible 60 s hang. It does **not** prevent bug B; it makes the failure mode "phone reconnects in ~3 s with a second AOA dialog." This was an intentional split: the recovery mechanism (couple AOA-pipe lifetime to upstream-TCP lifetime via `resetDevice`) is the right fix regardless of what triggers the tear-down. Bug B continues to need root-causing, but the user impact is now bounded.

### Diagnostic strategy: stay Loki-native, no tcpdump

Originally considered tcpdump on the box's loopback as the strongest single move. User pushed back: "are you saying we cannot get this data via our current process of shipping loki logs through the android mobile app to the backend?" Loki-only is sufficient — Caddy GODEBUG already logs every frame read on the server side, OkHttp's JUL `Http2` frame logger gives the matching phone-side trace, and the `e03125e6` hex dump captures the bridge's byte stream directly. Diff the three streams to localize the corruption. tcpdump is a third-tier fallback only if all three Loki paths leave us blind.

### Scaffolding logs are scaffolding, not durable

The hex dump (`on_in_complete` first-512-byte log) and the `LogcatReader -T 1` removal both come off in the cleanup commit. Neither has steady-state operational signal — bridge first-IN bytes are once-per-session noise, OkHttp frame logs are high-volume per-request. The durable observability is what we already have: bridge lifecycle (`accessory ready`, `upstream connected`, `pipe done: to_phone=X from_phone=Y uptime=Z`, `state.fail(...)` reasons), Caddy access logs, and the box-Loki transport.

### `uv run install-zed --build` is the deploy path (not manual rebuild + ssh-load)

The `--build` flag exists on `up`/`install-zed`. Use it from the host. The sandbox cannot run `uv run install-zed --build` (it shells out to `nmcli`); user runs it. Manual `compile-unity` + `adb install` paths skip `pm grant android.permission.READ_LOGS`, which is why OkHttp frame logs are sometimes missing on freshly-installed APKs. See `.pulsar/memories/unity-build-install-surface-refactor.md` for the planned refactor of these install surfaces.

## Open questions

- **Where exactly does the offset-~161 corruption happen?** Bridge (between USB read and TCP write), phone (OkHttp's writes to the AOA file descriptor), or upstream of OkHttp (JNI marshaling, ParcelFileDescriptor, kernel USB driver, AOA accessory firmware)? The `e03125e6` scaffolding is designed to answer this. After deploy + repro:
  - If OkHttp wrote a frame with `Length > 1 MB` (per the buffered-history OkHttpH2 logs) → corruption is upstream of OkHttp (unlikely — OkHttp `require`s length ≤ 16 KB).
  - If OkHttp wrote sane frames and the bridge hex dump shows the same bytes Caddy choked on → corruption is on the wire between bridge and Caddy (loopback TCP — almost impossible).
  - If OkHttp wrote sane frames but the bridge hex dump shows the corrupted bytes → corruption is upstream of the bridge (USB driver, kernel BULK reassembly, ParcelFileDescriptor, AOA firmware).
  - If the bridge sees missing bytes between two valid frames → byte loss/duplication, not mutation. Different repair shape.
- **Is the OUT path symmetric?** Diagnosis is on phone→box (IN at the bridge, request bytes) because that's what trips Caddy. The bridge's OUT path (box→phone) might have a mirror race. Worth checking once IN is fixed, in case box→phone has latent corruption that just happens not to trip OkHttp's framer-strictness.

## Key files

- `docker/aoa-bridge/src/aoa_bridge/main.py` — bridge core. `NUM_IN_TRANSFERS = 4` at line ~41. `on_in_complete` is where the hex-dump scaffolding lives (`e03125e6`). `_run_once()`'s `finally` block calls `_reset_device(handle)` (bug-A fix). `_pump_upstream_to_usb` is the TCP recv side; `state.upstream.recv()` is called without `socket_lock` — audit for hypothesis 5.
- `apps/AndroidMobile/Assets/Plugins/Android/aoa-accessory-filter.androidlib/src/main/java/io/placeframe/android/AoaAccessoryClient.java` — OkHttp client config (`.readTimeout(60, TimeUnit.SECONDS)`, `ConnectionPool(1, 1, TimeUnit.DAYS)`) plus the JUL h2-frame-log static initializer.
- `apps/AndroidMobile/Assets/Plugins/Android/.../LogcatReader.java` — drops `-T 1` per `e03125e6` so cold-start OkHttp frames in the logcat buffer reach LokiSink.
- `apps/AndroidMobile/Assets/Scripts/Capture/ZedCaptureController.cs` — single LogDrain (post-refactor): queries box-Loki via Caddy `/loki/api/v1/query_range`, pushes to host-Loki via Caddy `/loki/api/v1/push` with Bearer token. Cursor is `logDrainCursorNs` (in-memory only).
- `apps/AndroidMobile/Assets/Scripts/AndroidAoaHttpHandler.cs` — `ExecuteOverAoa` synchronously calls `AoaJni.Execute` over JNI; cancellation isn't plumbed to OkHttp's `Call.cancel()`. The 60 s `readTimeout` wall lives here in spirit. With bug A fixed, the 60 s hang shouldn't recur, but the cancellation-plumbing gap remains as a pending thread.
- `docker/aoa-gateway/Caddyfile` — `handle /loki/*` reverse-proxy to local box-Loki at `127.0.0.1:3100`; `handle` block reverse-proxies to `127.0.0.1:9001` (zed-capture). Bind `127.0.0.1`. `log { level DEBUG output stdout format json }` still on for diagnosis. Comes off in cleanup.
- `docker/aoa-gateway/Dockerfile` + `compose.rig.yml` — plain `caddy run` (no more supervisor). `GODEBUG: http2debug=2` env on the aoa-gateway service; comes off in cleanup.
- `docker/aoa-loki/config.yaml` — monolithic, filesystem, 72 h retention, listens on `127.0.0.1:3100`.
- `docker/aoa-alloy/config.alloy` — `discovery.docker` on box's docker socket, `box_id = sys.env("ZED_BOX_ID")` external label, pushes to `http://127.0.0.1:3100/loki/api/v1/push`.
- `apps/AndroidMobile/CLAUDE.md` — explains why h2c-prior-knowledge is mandatory for the AOA pipe (concurrent requests on a single duplex stream).
- `.pulsar/memories/aoa-handshake-debug-wrong-track.md` — prior memo recording the stale-idle hypothesis being wrong; companion.
- `.pulsar/memories/unity-build-install-surface-refactor.md` — the broader refactor of `install`/`compile-unity` so `READ_LOGS` grant is automatic.

## Pending threads

1. **Deploy scaffolding (`e03125e6`) + repro + diff three streams.** This is the next move.
   - Host: `uv run install-zed --build` (bridge change deploys) + `uv run install --project CaptureTool` (LogcatReader change deploys). Or `uv run compile-unity && adb install -r` then `adb shell pm grant com.outernet.captureapp android.permission.READ_LOGS`.
   - Cold-start repro: unplug AOA cable, replug, accept dialog, open Captures tab.
   - Query Loki for the repro window:
     - `{service="aoa-bridge"} |~ "first_in_hex"` — bytes the bridge received from phone.
     - `{app="capture-tool"} | json | Tag="OkHttpH2"` — frames OkHttp wrote (`>>`) and read (`<<`).
     - `{service="aoa-gateway"}` — Caddy's `read frame` lines.
   - Cross-reference to identify which side mutated byte ~161.

2. **Once bug B root cause lands**:
   - Revert `e03125e6` wholesale (it's marked TO BE DELETED in the title for exactly this reason).
   - Land the durable bug-B fix in its own commit.
   - Same cleanup commit also removes `GODEBUG: http2debug=2` from `docker/zed-capture/compose.rig.yml`, reverts Caddy log level from `DEBUG` to default in `docker/aoa-gateway/Caddyfile` (keep `format json` and `handle /loki/*` reverse-proxy), and removes the `OkHttpH2:V` verbose whitelist from `LogcatRelay.cs` (keep the JUL→logcat wiring).

3. **JNI cancellation plumbing fix.** Independent of bugs A and B. `AndroidAoaHttpHandler.ExecuteOverAoa` currently consults `CancellationToken` only for the response body stream, not the synchronous `AoaJni.Execute` call. Plumb `Call.cancel()` over JNI so `requestCts.CancelAfter(2 s)` in `ZedCaptureController.HealthPollLoop` actually fires at 2 s. With bug A fixed, the 60 s hang shouldn't recur in practice, but this is still the principled fix and stays on the list.

4. **Optional: lower OkHttp `readTimeout`** in `AoaAccessoryClient.java` from 60 s to 3-5 s. Defense-in-depth so any future hang recovers fast. Trivial. Do after bug B is rooted, not before.

## Operational notes for the next session

- `uv run install-zed --build` cannot run inside the COI sandbox; it shells out to `nmcli`. User runs it on the physical host with ZED cabled. Everything else (`uv run up`, `uv run lock-python`, `uv run generate-clients`, `uv run compile-unity`, `adb install`) works inside the sandbox.
- Manual `compile-unity` + `adb install` paths skip the `pm grant READ_LOGS` step. Either run `uv run install --project CaptureTool` (cleanest), or after a manual install run `adb shell pm grant com.outernet.captureapp android.permission.READ_LOGS` before reproducing.
- Force-push to `fix/install-zed-aoa-gateway-and-pull-logging` is authorized. The branch was already force-pushed once during the squash (`squash/zed-box-logging` → `fix/...`); both should be at `e03125e6` now.
- Codegen commits must have message exactly `Run generate-clients`; no body, no rationale. Prose and code commit separately.
- `uv run loki-query '{service="aoa-gateway"}' --since 5m --limit 200` for queries. Pass `--raw` for box-side entries (the pretty-printer expects Unity/structlog shape).
- `service` and `service_name` are interchangeable in Loki LogQL — Loki auto-derives `service_name` from common label names including `service`.
- `uv run --no-sync preflight` tears down + re-brings-up `compose.postgres.yml`; interrupts a running stack.
- SSH access to the box is available (used during diagnosis to read the box-Caddy log directly when the loki-query CLI's formatter was hiding entries). Prefer Loki-native diagnostics; reach for SSH only when Loki gaps it.
- Host Loki occasionally logs `"negative structured metadata bytes received" size=0` on each push. Cosmetic — entries land regardless. Worth tracking down eventually (likely a stray empty `structuredMetadata` array in the phone-relay push payload), but not blocking.
