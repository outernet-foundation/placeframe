---
updated: 2026-05-22
---

# AOA cold-start RST: bug A recovery landed, bug B root cause identified (double h2c preface from two OkHttp connections sharing one AOA FD)

## Goal

Capture Tool's "Captures" tab used to stay blank for ~60 s after login when the phone was wired to the ZED box over the AOA pipe. Diagnosis decomposed the failure into **two independent bugs**:

- **Bug A — recovery.** When Caddy tore down the upstream TCP socket for any reason, the phone's pooled h2c session desynced; OkHttp kept reusing the dead connection for 60 s (its `readTimeout`) before opening a new one. **Fixed** on this branch (commit `55885907`).
- **Bug B — root cause.** Cold-start FRAME_SIZE_ERROR. **Root-caused on 2026-05-22 from the `e03125e6` bridge hex dump**: the phone writes the h2c connection preface **twice** on a single AOA pipe. Two OkHttp h2c connections share one physical AOA `ParcelFileDescriptor` via `AoaSocketFactory`, and their writes interleave on the wire. Caddy reads the start of the *second* preface (`50 52 49 20 2a 20 48 54 54` — "PRI * HTT") as a 9-byte h2 frame header → `Length = 0x505249 ≈ 5 MB > MaxReadFrameSize` → `ErrFrameTooLarge` → `GOAWAY FRAME_SIZE_ERROR`. **Fix not yet implemented.**

With bug A fixed, the user-visible symptom is no longer a 60 s blank tab — it's "one extra AOA permission dialog on cold start, then the app works." The bug B fix will eliminate the extra dialog.

This memory is targeted at `/implement` next (fix Bug B). Diagnosis is complete; what remains is choosing and applying the right fix in `AoaSocketFactory.java` / `AoaAccessoryClient.java`.

## State

### What landed

| Commit | Title | Role |
|---|---|---|
| `55885907` | Reset USB device on upstream tear-down so phone drops pooled h2c session | **Bug A fix.** `_reset_device(handle)` call in `_run_once()`'s `finally` block calls `handle.resetDevice()` (libusb port-reset). Phone observes accessory-FD invalidation, OkHttp drops the pooled h2c session, next request opens a fresh connection. Tolerates `LIBUSB_ERROR_NOT_FOUND` (device may already have vanished). Also reverts `NUM_IN_TRANSFERS` from 1 back to 4 — the serialization was a discriminator for the falsified parallel-USB hypothesis, not part of the fix. |
| `e03125e6` | TO BE DELETED: scaffolding hex dump of first IN bytes + logcat history | Diagnostic-only additions: (1) `aoa-bridge` `on_in_complete` hex-dumps the first 512 bytes of phone→box IN traffic. (2) `LogcatReader.java` drops `-T 1` so the reader picks up buffered history (catches cold-start OkHttp frames). Marked TO BE DELETED in commit title — revert wholesale once bug B fix lands. **Successfully captured the corruption pattern on 2026-05-22** — see "Bug B root cause" below. |
| `11e80c1e` | Update aoa-cold-start-rst-diagnosis memo: bug A recovery landed, bug B still reproduces | Prior version of this memo. |

### Bug B root cause (confirmed 2026-05-22 from hex dump)

The bridge's first-512-byte hex dump of the phone→box stream on a failing cold start decodes to:

```
offset=0    len=24   505249202a20485454502f322e300d0a0d0a534d0d0a0d0a  PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n (h2c preface #1)
offset=24   len=15   000006040000000000000401000000                    SETTINGS Length=6 StreamID=0
offset=39   len=13   00000408000000000000ff0001                        WINDOW_UPDATE +0x00ff0001
offset=52   len=108  ...8204876083ad36d8...                            HEADERS stream=3 Length=99 (GET /captures)
offset=160  len=24   505249202a20485454502f322e300d0a0d0a534d0d0a0d0a  *** PREFACE #2 *** (root cause)
offset=184  len=15   000006040000000000000401000000                    SETTINGS again
offset=199  len=13   00000408000000000000ff0001                        WINDOW_UPDATE again
offset=212  len=9    000000040100000000                                SETTINGS ACK (conn #1 acking Caddy)
offset=221  len=17   0000080700000000000000000000000001                GOAWAY ErrorCode=PROTOCOL_ERROR (conn #1 reacting)
offset=238  len=13   00000403000000000300000001                        RST_STREAM stream=3 ErrorCode=PROTOCOL_ERROR
```

Caddy side (pulled via SSH `docker logs aoa-gateway --since 5m`) confirms: `wrote GOAWAY LastStreamID=3 ErrCode=FRAME_SIZE_ERROR` at 22:38:07.850, 45 ms after writing its own SETTINGS, immediately after reading the second `PRI` as a frame header. Caddy still returned `200` on `/captures` (113 B) because GOAWAY allows in-flight streams ≤ LastStreamID to finish.

**Mechanism:** the phone has one physical AOA pipe; `AoaSocketFactory` wraps the single accessory `ParcelFileDescriptor` in a `Socket`. OkHttp's connection pool decided it needed a *second* logical h2c connection (likely because the first looked busy / got tagged `noNewExchanges`, or a concurrent request raced through the pool gate). The factory handed out a Socket backed by the *same* FD, and connection #2 wrote its full preface into the shared wire — mid-stream of connection #1. This is hypothesis #6 from prior triage **confirmed at a specific mechanism: connection-pool level, not call level**.

### Observation history of the repro (2026-05-22 22:38 UTC window)

Cold-start sequence with `55885907` + `e03125e6` deployed:

```
22:25:31 – 22:26:06  PID 20556  healthy long-running h2c connection, streams 0x183 → 0x219
[12 min gap, app process restart]
22:38:07.850  Caddy: wrote GOAWAY LastStreamID=3 ErrCode=FRAME_SIZE_ERROR  (after reading 2nd PRI)
22:38:09.304  OkHttp: >> 0x00000003 4 RST_STREAM  (phone-initiated)
22:38:09.860  OkHttp: << 0x00000000 8 GOAWAY
[~5 s gap — _reset_device(handle) fires, phone re-enumerates, second AOA dialog]
22:38:15.100  OkHttp: << 0x00000000 0 SETTINGS ACK  (fresh TCP, fresh preface)
22:38:15.175  OkHttp: << 0x00000003 128 DATA  (Captures responded, traffic normal)
```

The 5 s recovery and second dialog is bug A's fix working as designed. The double-preface that triggered the tear-down is bug B, still present.

### Hypothesis triage (final)

| # | Hypothesis | Status |
|---|---|---|
| 1 | Server-side stale-connection close on first real request after extended SETTINGS-only idle | Ruled out — TCP/h2 connection was 1 s old, not 76 s. |
| 2 | `SETTINGS_MAX_CONCURRENT_STREAMS=1` on the server | Ruled out — Caddy advertises `MAX_CONCURRENT_STREAMS=250`. |
| 3 | `SETTINGS` handshake race on cold start | Ruled out — proper SETTINGS+ACK exchange precedes stream 3. |
| 4 | aoa-bridge parallel-USB-IN completion-order race (`NUM_IN_TRANSFERS=4`) | Falsified by direct test at `NUM_IN_TRANSFERS=1`; same repro at both values. |
| 5 | TCP-direction concurrency in the bridge | Ruled out — bridge hex dump shows the corrupted bytes arriving from the phone, so the bridge isn't the source. |
| 6 | OkHttp client-side write interleaving (two connections sharing one FD) | **Confirmed.** Specific mechanism: pool-level, not call-level. Second OkHttp h2c connection writes its preface mid-stream into the shared AOA FD. |
| 7 | Something else upstream of the bridge (libusb transfer recycling, kernel BULK-IN reassembly, ParcelFileDescriptor framing on the Android side, AOA accessory firmware) | Ruled out by (6) being confirmed — the bytes are correctly transported, just from two OkHttp connections muxed onto one FD. |

### Logging gotcha discovered this session

**LogDrain stops pulling box-Loki across app process restart.** During this session the Capture Tool app process restarted between 22:26 and 22:38; LogDrain never resumed, so host-Loki showed stale bridge data only up to 22:26. This made it briefly look like `aoa-bridge` hadn't been redeployed (no recent log lines in host-Loki for the post-22:37 timeframe), when in fact the bridge was running the new image and producing hex dumps — they were just sitting in box-Loki, never relayed. Workaround: SSH to the box and `docker logs aoa-bridge --since 5m` directly. Long-term fix: LogDrain should auto-resume on app start regardless of prior state. Separate ticket-shaped concern, not blocking bug B.

### Logging transport (otherwise solid)

The whole box→host log shipping refactor landed during the same diagnostic cycle (`696d7f47` "Add box-side log shipping: Alloy + Loki + phone relay to host Loki"). All 5 box services (`zed-capture`, `aoa-gateway`, `aoa-bridge`, `aoa-loki`, `aoa-alloy`) emit to a box-local Loki monolithic instance via Grafana Alloy on the docker socket. Phone polls box-Loki via Caddy `/loki/*` over AOA and pushes to host-Loki via Caddy `/loki/api/v1/push` with the existing Bearer token. 72 h retention on box-Loki. All listeners bind `127.0.0.1` on the box; AOA pipe is the sole route.

GODEBUG `http2debug=2` is still on for `aoa-gateway` for diagnosis (~5000 events per 2 min; queries age out quickly). Caddy DEBUG level is still on. Both come off in the cleanup commit after bug B fix lands.

OkHttp h2 frame logging (`okhttp3.internal.http2.Http2` JUL logger → logcat tag `OkHttpH2` → LogcatRelay → LokiSink with `app=capture-tool`) is wired in `AoaAccessoryClient.java`'s static initializer and the `LogcatRelay.cs` whitelist. The `LogcatReader.java -T 1` drop (`e03125e6`) is what made cold-start OkHttp frames reachable.

### Branch state

- Branch: `squash/zed-box-logging` (post-squash; the original `fix/install-zed-aoa-gateway-and-pull-logging` was force-pushed to match)
- Tip: `11e80c1e` (this memo's prior update) on top of `e03125e6` (TO BE DELETED scaffolding) on top of `55885907` (bug-A fix)
- Working tree at last check: clean except untracked `.claude/scheduled_tasks.lock` (runtime artifact, ignored)
- `docker/aoa-bridge/src/aoa_bridge/main.py:41` is `NUM_IN_TRANSFERS = 4` (reverted alongside bug-A fix)
- The `bded64f5 Add aoa-cold-start-rst-diagnosis memo` commit anchors this file in the squash; updates ride on top as separate prose commits per CLAUDE.md.

## Decisions

### Bug A vs bug B: fix recovery first, root-cause separately

The bug-A fix (`55885907`) is durable, narrow, and removes the 60 s hang. It does **not** prevent bug B; it makes the failure mode "phone reconnects in ~3-5 s with a second AOA dialog." This was an intentional split: the recovery mechanism (couple AOA-pipe lifetime to upstream-TCP lifetime via `resetDevice`) is the right fix regardless of what triggers the tear-down. The bug-A fix stays as defense-in-depth even after the bug-B fix lands — if anything else ever desyncs the pooled h2c session, recovery is automatic.

### Diagnostic strategy: stay Loki-native, no tcpdump (and it worked)

Caddy GODEBUG already logged every frame read on the server side; OkHttp's JUL `Http2` frame logger gave the matching phone-side trace; the `e03125e6` hex dump captured the bridge's byte stream directly. Diffing the three streams localized the corruption to "OkHttp is writing a second preface." No tcpdump was needed.

### Scaffolding logs are scaffolding, not durable

The hex dump (`on_in_complete` first-512-byte log) and the `LogcatReader -T 1` removal come off in the cleanup commit. Neither has steady-state operational signal. The durable observability is what we already have: bridge lifecycle (`accessory ready`, `upstream connected`, `pipe done: ...`), Caddy access logs, and the box-Loki transport.

### `uv run install-zed --build` is the deploy path

The `--build` flag exists on `up`/`install-zed`. Use it from the host. The sandbox cannot run `uv run install-zed --build` (shells out to `nmcli`); user runs it on the host with ZED cabled. Manual `compile-unity` + `adb install` paths skip `pm grant android.permission.READ_LOGS`, which is why OkHttp frame logs are sometimes missing on freshly-installed APKs. See `.pulsar/memories/unity-build-install-surface-refactor.md`.

## Open questions

- **Why did OkHttp's pool decide to open a second connection?** With `ConnectionPool(1, 1, TimeUnit.DAYS)` the pool should retain one h2c connection and serve all calls from it. Candidates:
  - The first connection was tagged `noNewExchanges` after a previous failed request (e.g. a read timeout or `Call.cancel()`), and the next request triggered a fresh-pool entry.
  - Concurrent requests raced through the pool's selection logic before the first connection was visible as available.
  - The pool sees the AOA socket-wrapped FD as already-pooled but a request still came in via a non-pool path.
- **What should `AoaSocketFactory.createSocket()` do on the second call?** Options:
  1. Hand back the *same* `Socket` instance (singleton) — but `Socket`s aren't really designed for re-use; OkHttp would call `connect()` again.
  2. Hand back a fresh `Socket` over the same FD, but reject `Socket.connect()` on the second instance — fail loud so OkHttp's pool gives up and reuses the first connection.
  3. Block the call until the first `Socket` is closed — wrong semantics for h2c (we *want* to multiplex on one connection, not serialize).
  4. Add a precondition higher up that prevents OkHttp from ever needing a second connection (e.g. ensure `noNewExchanges` is never set on the AOA-backed connection).
- **Is `Call.cancel()` over JNI plumbing related?** `AndroidAoaHttpHandler.ExecuteOverAoa` consults `CancellationToken` only for the response body stream, not the synchronous `AoaJni.Execute` call. If a UnityWebRequest is canceled, OkHttp may mark the connection `noNewExchanges`. Independent diagnostic thread but possibly the trigger for hypothesis (a).

## Key files

- `docker/aoa-bridge/src/aoa_bridge/main.py` — bridge core. `NUM_IN_TRANSFERS = 4` at line ~41. `on_in_complete` hosts the hex-dump scaffolding (`e03125e6`, `HEX_DUMP_BUDGET = 512`). `_run_once()`'s `finally` block calls `_reset_device(handle)` (bug-A fix).
- `apps/AndroidMobile/Assets/Plugins/Android/aoa-accessory-filter.androidlib/src/main/java/io/placeframe/android/AoaAccessoryClient.java` — OkHttp client config (`.readTimeout(60, TimeUnit.SECONDS)`, `ConnectionPool(1, 1, TimeUnit.DAYS)`) plus the JUL h2-frame-log static initializer. **The bug B fix likely lives here or in `AoaSocketFactory`.**
- `apps/AndroidMobile/Assets/Plugins/Android/aoa-accessory-filter.androidlib/src/main/java/io/placeframe/android/AoaSocketFactory.java` — wraps `ParcelFileDescriptor` in a `Socket`. Whether and how this enforces single-connection-per-FD is the question. **Read first when implementing the fix.**
- `apps/AndroidMobile/Assets/Plugins/Android/aoa-accessory-filter.androidlib/src/main/java/io/placeframe/android/LogcatReader.java` — drops `-T 1` per `e03125e6`.
- `apps/AndroidMobile/Assets/Scripts/Capture/ZedCaptureController.cs` — single LogDrain: queries box-Loki via Caddy `/loki/api/v1/query_range`, pushes to host-Loki via Caddy `/loki/api/v1/push`. Cursor `logDrainCursorNs` is in-memory only — explains the "LogDrain stops on app restart" gotcha.
- `apps/AndroidMobile/Assets/Scripts/AndroidAoaHttpHandler.cs` — `ExecuteOverAoa` synchronously calls `AoaJni.Execute` over JNI; `CancellationToken` only plumbed to the response body stream, not `Call.cancel()`. May be related to bug B trigger.
- `docker/aoa-gateway/Caddyfile` — `handle /loki/*` reverse-proxy to local box-Loki at `127.0.0.1:3100`; `handle` block reverse-proxies to `127.0.0.1:9001` (zed-capture). `protocols h1 h2c`, `log { level DEBUG output stdout format json }`. DEBUG and GODEBUG come off in cleanup.
- `docker/aoa-gateway/Dockerfile` + `compose.rig.yml` — plain `caddy run`. `GODEBUG: http2debug=2` env on the aoa-gateway service; comes off in cleanup.
- `docker/aoa-loki/config.yaml` — monolithic, filesystem, 72 h retention, listens on `127.0.0.1:3100`.
- `docker/aoa-alloy/config.alloy` — `discovery.docker` on box's docker socket, `box_id = sys.env("ZED_BOX_ID")` external label, pushes to `http://127.0.0.1:3100/loki/api/v1/push`.
- `apps/AndroidMobile/CLAUDE.md` — explains why h2c-prior-knowledge is mandatory for the AOA pipe (concurrent requests on a single duplex stream).
- `.pulsar/memories/aoa-handshake-debug-wrong-track.md` — prior memo recording the stale-idle hypothesis being wrong; companion.
- `.pulsar/memories/unity-build-install-surface-refactor.md` — the broader refactor of `install`/`compile-unity` so `READ_LOGS` grant is automatic.

## Pending threads

1. **Implement bug B fix.** Read `AoaSocketFactory.java` and `AoaAccessoryClient.java` first. The mechanism is "two OkHttp h2c connections sharing one AOA FD"; the fix prevents the second connection from ever being constructed (factory-level rejection or pool-level invariant). Yielded for direction after diagnosis — user decides between the four candidates listed in "Open questions."

2. **Investigate the OkHttp connection-pool trigger.** Independent of the factory fix: figure out why the pool wanted a second connection given `ConnectionPool(1, 1, TimeUnit.DAYS)`. Likely `noNewExchanges` got set on the first connection by a canceled call (see `AndroidAoaHttpHandler.ExecuteOverAoa` cancellation plumbing). Worth fixing the upstream cause even if the factory blocks the symptom.

3. **Cleanup commit after bug B fix lands:**
   - Revert `e03125e6` wholesale (TO BE DELETED).
   - Remove `GODEBUG: http2debug=2` from `docker/zed-capture/compose.rig.yml` (or wherever the aoa-gateway service env is set).
   - Revert Caddy log level from `DEBUG` to default in `docker/aoa-gateway/Caddyfile` (keep `format json` and `handle /loki/*` reverse-proxy).
   - Remove the `OkHttpH2:V` verbose whitelist from `LogcatRelay.cs` (keep the JUL→logcat wiring).

4. **JNI cancellation plumbing fix.** `AndroidAoaHttpHandler.ExecuteOverAoa` consults `CancellationToken` only for the response body stream, not the synchronous `AoaJni.Execute` call. Plumb `Call.cancel()` over JNI so `requestCts.CancelAfter(2 s)` actually fires at 2 s. May also be the trigger for bug B (a canceled call marking the OkHttp connection `noNewExchanges`).

5. **LogDrain resume on app restart.** Bridge logs stop reaching host-Loki when the Capture Tool app process restarts and LogDrain doesn't resume its box-Loki polling. Manifested in this session as misleading "bridge looks silent" data. `logDrainCursorNs` is in-memory only; on restart it presumably resets but the polling doesn't reinitiate. Worth a separate ticket — not blocking bug B but a real diagnostic-experience gap.

6. **Optional: lower OkHttp `readTimeout`** in `AoaAccessoryClient.java` from 60 s to 3-5 s. Defense-in-depth so any future hang recovers fast. Do after bug B fix lands.

## Operational notes for the next session

- `uv run install-zed --build` cannot run inside the COI sandbox (`nmcli`). User runs it on the physical host with ZED cabled. Everything else (`uv run up`, `uv run lock-python`, `uv run generate-clients`, `uv run compile-unity`, `adb install`) works inside the sandbox.
- Manual `compile-unity` + `adb install` paths skip the `pm grant READ_LOGS` step. Either run `uv run install --project CaptureTool` (cleanest, when a CI artifact is available for the branch), or after a manual install run `adb shell pm grant com.outernet.captureapp android.permission.READ_LOGS` before reproducing.
- **CI artifacts aren't built for `squash/zed-box-logging`** — `uv run install --project CaptureTool` will fail with "No artifact ... on branch ...". Use `compile-unity` + `adb install` + manual READ_LOGS grant.
- **When `aoa-bridge` looks silent in host-Loki**, check via SSH (`ssh user@100.64.0.1 'docker logs aoa-bridge --since 5m'`) before assuming the deployment failed. LogDrain may have stopped relaying after an app process restart.
- **GODEBUG http2debug=2 produces ~5000 events per 2 min on `aoa-gateway`** — Loki query windows age out fast. For Caddy frame-level diagnosis, prefer SSH + `docker logs aoa-gateway --since N` over `uv run loki-query`.
- Force-push to `fix/install-zed-aoa-gateway-and-pull-logging` is authorized. The branch was force-pushed during the squash (`squash/zed-box-logging` → `fix/...`).
- Codegen commits must have message exactly `Run generate-clients`; no body, no rationale. Prose and code commit separately.
- `uv run loki-query '{service="aoa-gateway"}' --since 5m --limit 200` for queries. Pass `--raw` for box-side entries (the pretty-printer expects Unity/structlog shape).
- `service` and `service_name` are interchangeable in Loki LogQL — Loki auto-derives `service_name` from common label names.
- `uv run --no-sync preflight` tears down + re-brings-up `compose.postgres.yml`; interrupts a running stack.
- Host Loki occasionally logs `"negative structured metadata bytes received" size=0` on each push. Cosmetic — entries land regardless. Tracked but not blocking.
