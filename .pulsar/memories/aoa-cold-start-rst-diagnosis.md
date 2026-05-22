---
updated: 2026-05-22
---

# AOA cold-start RST: captures tab blank ~60 s after login, root cause not yet wire-proven

## Goal

Diagnose why the Capture Tool's "Captures" tab stays blank for ~60 s after login when the phone is wired to the ZED box over the AOA pipe. User-visible symptom: tab does not populate despite the ZED being reachable. Actual failure: a TCP RST that Caddy sends to `aoa-bridge` on the first real HTTP/2 request after the connection has been idle on SETTINGS-only traffic, compounded by a 60 s OkHttp `readTimeout` that converts a sub-second failure into a minute-long freeze. Reproduced multiple times on `fix/install-zed-aoa-gateway-and-pull-logging`. Still don't know **which side first emits the kill frame** (GOAWAY from Caddy? RST_STREAM from Caddy? OkHttp tearing down locally?). The logging changes needed to settle that are partially committed but the box-side log transport is wrong (Alloy detour) and needs to be replaced before the next repro.

This memory is targeted at `/implement`: pick up by reverting the Alloy detour, switching the box-side log transport to the phone-relay `/logs` pattern with line-level `service` labels and a Python supervisor for Caddy's stderr, redeploying, and reading the cross-correlated wire trace.

## The signal (reproduced at 17:35:16 and again at 18:09:40 UTC, 2026-05-22)

From `service_name=capture-tool` + `docker logs placeframe-aoa-bridge-1` on the box, cross-correlated:

```
17:34:02.086  aoa-bridge: upstream connected; piping (in_ep=0x81, out_ep=0x01)
17:34:02 → 17:35:16   74 s idle. 71B to phone, 385B from phone — h2 preface + SETTINGS + maybe a PING. No real requests.
17:35:16.428  phone: GET /status fires (first real request after login)
17:35:16.439  phone: GET /captures fires concurrently (UpdateCaptureList one-shot when loggedIn && idle flips true)
17:35:16.442  aoa-bridge: upstream read error: [Errno 104] Connection reset by peer
17:35:16.524  phone OkHttp: ConnectionShutdownException on /captures
17:35:16.528  phone OkHttp: StreamResetException: REFUSED_STREAM on /status
17:35:17.495  aoa-bridge: accessory ready vid=18d1 pid=2d01; opening pipe (1 s later, new connection)
17:35:16 → +60.030 s  next /status hangs full OkHttp readTimeout=60s
+61.286 s     /status succeeds (20 ms)
+61.353 s     zedReachable flips True; captures polling timer starts
+61.518 s     EnumerateCaptures success count=1 — captures tab finally populates
```

Two bugs compounding:

1. **First real request after 74 s of SETTINGS-only idle triggers Caddy to abruptly RST the TCP socket to `aoa-bridge`.** OkHttp on the phone then reports `ConnectionShutdownException` / `REFUSED_STREAM` because the streams are in flight when the underlying TCP dies.
2. **`AndroidAoaHttpHandler.ExecuteOverAoa` calls `AoaJni.Execute(...)` synchronously over JNI** (`apps/AndroidMobile/Assets/Scripts/AndroidAoaHttpHandler.cs:112`). The C# `CancellationToken` (`requestCts.CancelAfter(2s)` in `ZedCaptureController.cs:251`) is plumbed into the handler but only consulted for the response body stream, not for the `Call.execute()` itself. So a stuck call waits the OkHttp `readTimeout`, which is `60 s` (`AoaAccessoryClient.java:248`) — the exact 60030 ms wall we see. While that one request hangs, `App.state.zedReachable` stays false, the polling-timer subscription stays disposed, and `UpdateCaptureList` never re-fires.

## Three hypotheses ordered by likelihood (none yet confirmed wire-side)

1. **Server-side stale-connection close on first real request after extended SETTINGS-only idle.** Caddy's Go HTTP/2 stack has detection paths that may close a connection that's been PING-only when an unexpected stream-open comes through. The 74 s idle gap + RST exactly on first real HEADERS frame fits. Default Go h2 doesn't have an obvious 74 s knob — would be Caddy-version-specific or kernel-level.
2. **`SETTINGS_MAX_CONCURRENT_STREAMS=1` on the server.** If Caddy advertises 1, h2 multiplexing is being used as HTTP/1.1-with-extra-framing — defeating the whole architectural reason for h2c-prior-knowledge on the AOA pipe. `apps/AndroidMobile/CLAUDE.md` is explicit that concurrent requests on the single-FD pipe is the whole point. Caddyfile doesn't set the limit explicitly; default needs to be verified from the actual SETTINGS frame.
3. **A `SETTINGS` handshake race on cold start**, where the client opens stream 3 before stream 1's response has settled the connection-state machine to "ready." Cure is server sends initial SETTINGS promptly, client honors it before opening multiple streams.

Effectively ruled out: TCP-layer half-closed from the bridge side (aoa-bridge would log a close, not see ECONNRESET from peer).

## Decisions (all resolved, no remaining open questions)

### Architecture: phone-relay extension, not Alloy

The committed Alloy approach (`84a16049`) is architecturally wrong and is being reverted. The placeframe deployment intent is that the ZED box's runtime data egress is exclusively through the phone app polling `zed-capture`'s `/logs` endpoint. The cable network (`100.64.0.0/24`) is for `install-zed` setup only (SSH + docker registry pulls), not runtime data. Alloy duplicated the existing transport, required a new unauthenticated gateway listener, and collided with the COI-sandbox netns boundary.

### Label location: in each line, not in the URL

The `service` label that drives Loki stream identity lives in each log line's JSON, mirroring the existing `box_id` pattern. The API's `push_zed_box_logs` will be changed to read `record.get("service")` per line (default `"unknown"`) and use that as the Loki stream label, instead of the current hard-coded `"service": "zed-capture"`.

### Endpoint shape: one per source

Four `/logs/<source>` endpoints on zed-capture, each a copy of today's handler pointed at a different file. Per-source cursor file. Rationale: each file rotates independently with its own `inode:offset` cursor; a single endpoint with a vector cursor would require inventing a cursor format. Three endpoints × one cursor each is mechanically simpler and an additive change:

| Endpoint                       | File                                                     | `service` label in lines  | Source                            |
|--------------------------------|----------------------------------------------------------|---------------------------|-----------------------------------|
| `GET /logs/app`                | `/var/log/zed-capture/app.jsonl`                         | `zed-capture`             | zed-capture's existing Python logging |
| `GET /logs/aoa-gateway`        | `/var/log/zed-capture/aoa-gateway.jsonl`                 | `aoa-gateway`             | Caddy's structured access/debug log, post-processed by the gateway supervisor |
| `GET /logs/aoa-gateway-h2debug`| `/var/log/zed-capture/aoa-gateway-h2debug.jsonl`         | `aoa-gateway-h2debug`     | Caddy process's raw stderr (GODEBUG=http2debug=2 frame trace), wrapped to JSON by the gateway supervisor |
| `GET /logs/aoa-bridge`         | `/var/log/zed-capture/aoa-bridge.jsonl`                  | `aoa-bridge`              | aoa-bridge's Python logging (replaces today's `print()`) |

The existing `/logs` route is **renamed** to `/logs/app` for consistency. Phone-side callers all go through generated client code, so the rename is a codegen + caller-update sweep, not a backward-compat concern. Cursor file for `app` stays at `cursor.json` for continuity; the new sources get `cursor-aoa-gateway.json`, `cursor-aoa-gateway-h2debug.json`, `cursor-aoa-bridge.json`.

### Rotation: Caddy native + extended reader

All four files rotate. Cap matches zed-capture's existing 50 MB × 5. aoa-bridge uses Python's `RotatingFileHandler` (same as zed-capture). aoa-gateway uses Caddy's native `roll_size 50mb / roll_keep 5 / roll_compress false`. The GODEBUG file is written by the supervisor through a Python `RotatingFileHandler`.

`roll_compress false` is required because Caddy's lumberjack-driven gzip wouldn't be decompressed by the reader. `roll_keep` is required to bound disk use.

`_ordered_log_files` in `docker/zed-capture/src/routers/logs.py` is extended to recognise both Python's numeric-suffix backups (`app.jsonl.1`, `.2`, …) and Caddy's lumberjack timestamp-suffix backups (`aoa-gateway-2026-05-22T14-05-45.000.jsonl`). Cleanest refactor: factor a `LogSource` struct that owns its own filename glob and backup-ordering key; `read_logs` takes one of those instead of the current `LOG_DIR` constant.

### GODEBUG transport: Python supervisor wraps Caddy's stderr (option ii)

`aoa-gateway`'s container `CMD` becomes a small Python supervisor (`docker/aoa-gateway/supervisor.py`, stdlib-only) that:

1. Spawns Caddy as a subprocess with `caddy run --config /etc/caddy/Caddyfile`. Caddy's Caddyfile is configured with `log default { level DEBUG output stdout format json }` and `log { output stdout format json }` — Caddy emits **all** its structured access + debug logs as JSON lines on **stdout**.
2. Reads Caddy's stdout in a thread. Each line is parsed as JSON. Adds `service: "aoa-gateway"` and `box_id: $ZED_BOX_ID` to the dict if missing. Preserves Caddy's own `ts` timestamp (Caddy's structured logs are already millisecond-accurate, do not overwrite). Re-serialises and writes via a `RotatingFileHandler` (50 MB × 5) to `/var/log/zed-capture/aoa-gateway.jsonl`.
3. Reads Caddy's stderr in another thread. Each line is raw text (GODEBUG `http2debug=2` frame trace, plus any Go-runtime panics). Wraps into `{"timestamp": <ISO-8601 utc now at line-read time, millisecond precision>, "service": "aoa-gateway-h2debug", "box_id": $ZED_BOX_ID, "level": "DEBUG", "message": <raw line>}`. Writes via a separate `RotatingFileHandler` (50 MB × 5) to `/var/log/zed-capture/aoa-gateway-h2debug.jsonl`.
4. Forwards SIGTERM / SIGINT to the Caddy subprocess; waits with a bounded join then `SIGKILL`s if it doesn't exit; propagates Caddy's exit code as its own.

Why option (ii) and not the simpler "label at the API edge" (option iii): every other source in the pipeline (zed-capture, aoa-bridge, Caddy stdout, phone-side OkHttp via Serilog) emits lines with millisecond-accurate `timestamp` fields baked in at emission time. GODEBUG raw stderr has no timestamp. In option (iii), the API would fall back to `datetime.now()` at relay-POST time, giving the GODEBUG stream a poll-cadence-dependent 0–5 s drift relative to every other stream. Option (ii) timestamps each GODEBUG line at supervisor-read time inside the container — submillisecond fidelity. For the cold-start RST diagnosis the alignment between Go's `wrote RST_STREAM` frame and OkHttp's `>> RST_STREAM` frame matters to ms, so (ii) is the correct choice. Cost is ~50 lines of Python and a Python interpreter in the aoa-gateway image (`python:3.13-slim`-derived base, or `apk add python3` on top of the current alpine-caddy base — TBD by reading the existing `docker/aoa-gateway/Dockerfile`).

The supervisor's verbose behavior is **not** env-gated for cleanup. Cleanup (a later, separate commit after diagnosis is settled) removes `GODEBUG=http2debug=2` from `compose.rig.yml` and reverts Caddy's log level from `DEBUG` to default. The supervisor remains — once you have a structured log pipeline that handles non-JSON stderr correctly, you keep it; removing it would re-introduce the wrong-transport problem the next time anyone reaches for a debug knob.

### zed-capture's existing logging: add `service=zed-capture` static field

`docker/zed-capture/src/logging_config.py` already has `JsonFormatter(..., static_fields={"box_id": BOX_ID})`. Add `"service": "zed-capture"` to that dict so the API's new per-line `service` extraction sees the right label on zed-capture's own lines.

### Defense-in-depth fix: still planned but not the first commit

The principled fix to the cold-start RST is to make the request burst actually succeed (whichever of the three hypotheses turns out to be the cause). Cheap fixes (lower OkHttp `readTimeout` from 60 s to 3 s, wire JNI cancellation to `Call.cancel()` over JNI) reduce recovery time of a failure mode that shouldn't exist. The JNI-cancellation plumbing fix is still worth doing as a separate, later commit — but only after the root-cause fix lands.

## State

**Logging changes (committed `84a16049`, partially correct, partially needs revert):**

| # | What | Where | Disposition |
|---|---|---|---|
| 1+2 | Caddy access logs + DEBUG level + JSON format | `docker/aoa-gateway/Caddyfile` | **Keep content; redirect output.** Change both log directives' `output stdout` → leave as `output stdout` (the supervisor reads stdout) and add `roll_size 50mb roll_keep 5 roll_compress false` once the supervisor exists. Actually simpler: Caddy emits to stdout, supervisor handles file write + rotation via Python's `RotatingFileHandler`. So Caddyfile keeps `output stdout`. |
| 3 | `GODEBUG=http2debug=2` env on aoa-gateway | `docker/zed-capture/compose.rig.yml` | **Keep.** Supervisor captures stderr to file. |
| 4+5 box | Alloy sidecar pushing to host gateway | `docker/aoa-alloy/Dockerfile`, `docker/aoa-alloy/config.alloy`, `compose.zed.bake.yml` (added `ALLOY_DIGEST` + `aoa-alloy` build), `docker/zed-capture/compose.rig.yml` (added `aoa-alloy` service), `scripts/src/scripts/install_zed/constants.py` (added to `ZED_SERVICES`) | **REVERT.** Replaced by per-source `/logs/...` routes + supervisor. |
| 4+5 host | Unauthenticated `/aoa-loki/push` route on new `:8084` listener restricted to `100.64.0.0/24` | `docker/gateway/entrypoint.sh` (Listener C block), `compose.yml` (added `"8084:8084"` port) | **REVERT.** Not needed once phone-relay carries the AOA logs. |
| 6 | OkHttp h2 frame logging via JUL `okhttp3.internal.http2.Http2` → logcat tag `OkHttpH2` → LogcatRelay → Loki | `apps/AndroidMobile/Assets/Plugins/Android/aoa-accessory-filter.androidlib/src/main/java/io/placeframe/android/AoaAccessoryClient.java` (static initializer), `apps/AndroidMobile/Assets/Scripts/LogcatRelay.cs` (added `OkHttpH2:V` to whitelist) | **Keep.** Frames already flowing in Loki under `service_name=capture-tool` Tag=`OkHttpH2`. Canonical pattern. |

**Repro status:** Cold-start RST reproduced again at 18:09:40 (phone-side OkHttp emits `>> RST_STREAM` on stream 3, then 678 ms later re-establishes a fresh stream 3 on a new connection). Bug is consistently reproducible by cold-starting the Capture Tool, logging in, watching the captures tab.

**Loki streams expected after the corrected transport ships:**
- `service=capture-tool` — phone-side: OkHttp exceptions, AOA req/res, `OkHttpH2` frame trace. *Already working today.*
- `service=zed-capture` — zed-capture container's Python logging via phone-relay. *Already working today; will need `service` field added to lines so the API's new per-line routing picks the right label.*
- `service=aoa-gateway` — Caddy access/debug JSON, structured, post-processed by gateway supervisor.
- `service=aoa-gateway-h2debug` — Go runtime stderr (GODEBUG frame trace), JSON-envelope-wrapped by gateway supervisor with millisecond-accurate timestamps.
- `service=aoa-bridge` — aoa-bridge container's Python logging.

## Open questions

None. All transport-architecture decisions are locked. Diagnostic questions (which hypothesis is right) are open by design and answerable once the corrected transport is deployed and the cold-start RST is reproduced once more.

## Pending threads (cookbook for the next implementation pass)

1. **Revert the Alloy detour.** One commit, code only:
   - `git rm -r docker/aoa-alloy/`
   - Revert `compose.zed.bake.yml` ALLOY_DIGEST x-base + aoa-alloy build target.
   - Revert `compose.yml` gateway `"8084:8084"` port.
   - Revert `docker/gateway/entrypoint.sh` Listener C block.
   - Revert `docker/zed-capture/compose.rig.yml` aoa-alloy service (other unrelated keeps in this file stay).
   - Revert `scripts/src/scripts/install_zed/constants.py` aoa-alloy ZED_SERVICES entry.
   - Run `uv run build --bake-file compose.zed.bake.yml --lock-only` to regenerate `.env.lock` without ALLOY_DIGEST; stage `.env.lock` in the same commit.

2. **Implement the corrected box-side transport.** One commit, code only:
   - `docker/zed-capture/compose.rig.yml`:
     - Add `volumes: [zed-logs:/var/log/zed-capture]` to `aoa-gateway` and `aoa-bridge`.
     - Add `environment: ZED_BOX_ID: ${ZED_BOX_ID:?err}` to `aoa-gateway` and `aoa-bridge`.
     - Keep existing `GODEBUG: http2debug=2` on `aoa-gateway`.
   - `docker/aoa-gateway/Dockerfile`: add Python 3 to the image; COPY `supervisor.py`; change `CMD` from `caddy run …` to `python3 /supervisor.py`.
   - `docker/aoa-gateway/supervisor.py` (new, stdlib-only): see "GODEBUG transport" decision above for behavior. Uses `subprocess.Popen`, two reader threads, two `logging.handlers.RotatingFileHandler` instances (50 MB × 5), `json.dumps` for stdout-passthrough lines (with `service`/`box_id` injection if missing, Caddy `ts` preserved) and for stderr wrap-into-envelope. Forwards SIGTERM/SIGINT; bounded join + SIGKILL fallback; propagates exit code.
   - `docker/aoa-gateway/Caddyfile`: keep `output stdout` for both log directives (supervisor reads stdout). No `roll_*` directives in the Caddyfile because the supervisor owns rotation.
   - `docker/aoa-bridge/src/aoa_bridge/main.py`: replace the module-level `def log(message: str): print(message, flush=True)` with `logging.getLogger(__name__).info(...)` callsites; configure logging at module-import time the same way zed-capture does — `JsonFormatter` with `static_fields={"box_id": ZED_BOX_ID, "service": "aoa-bridge"}`, `RotatingFileHandler` at `/var/log/zed-capture/aoa-bridge.jsonl` (50 MB × 5), `StreamHandler` to stdout (so `docker logs` still works for offline SSH). Pull `ZED_BOX_ID` from env, fail loudly if unset (match zed-capture's behavior).
   - `docker/zed-capture/src/logging_config.py`: add `"service": "zed-capture"` to the JsonFormatter's `static_fields` dict.
   - `docker/zed-capture/src/routers/logs.py`:
     - Factor a `LogSource` dataclass holding (filename, backup-glob, backup-sort-key, cursor-file-name). Four instances: `app` (existing `app.jsonl`, numeric suffix, `cursor.json`), `aoa-gateway` (`aoa-gateway.jsonl`, lumberjack timestamp suffix, `cursor-aoa-gateway.json`), `aoa-gateway-h2debug` (`aoa-gateway-h2debug.jsonl`, numeric suffix because supervisor uses Python's `RotatingFileHandler`, `cursor-aoa-gateway-h2debug.json`), `aoa-bridge` (`aoa-bridge.jsonl`, numeric suffix, `cursor-aoa-bridge.json`).
     - Extend `_ordered_log_files` to take a `LogSource` and use its glob + sort key. Add a regex-based path for lumberjack's `name-2006-01-02T15-04-05.000.jsonl` backups (sort by parsed timestamp, oldest first).
     - Register four route handlers: `GET /logs/app`, `GET /logs/aoa-gateway`, `GET /logs/aoa-gateway-h2debug`, `GET /logs/aoa-bridge`. The existing `GET /logs` route is **renamed** to `GET /logs/app`.
   - `docker/zed-capture/src/cursor_store.py`: parameterize `CursorStore` by cursor-file path. Instantiate one per `LogSource`. Existing top-level `cursor_store` becomes the `app` instance.
   - `docker/api/src/routers/zed_box_logs.py`: replace the hard-coded `"service": "zed-capture"` in the Loki stream label with `record.get("service")`, defaulting to `"unknown"` when missing or unparseable. Lines without `service` (e.g. mid-rollout from an older box image) land in the `unknown` stream — visible, not silent.

3. **Run `uv run generate-clients`.** Codegen-only commit. Message exactly `Run generate-clients`. The four new `/logs/...` route shapes appear as new methods on `PlaceframeZedCaptureClient` (replacing the existing `GetLogsAsync`).

4. **Phone-relay extension.** One commit, code only:
   - `apps/AndroidMobile/Assets/Scripts/Capture/ZedCaptureController.cs`:
     - Replace the single `logDrainTask` + `logDrainPendingAck` static pair with four `(TaskHandle, string)` pairs, one per source. Cleanest: factor a small `LogDrain` struct or static dict keyed by source name with `(GetAsync delegate, ackCursor)` pairs.
     - `EvaluateLogDrainState` cancels all four and restarts all four when `loggedIn && zedReachable`.
     - `LogDrainOnce` takes a `LogSource` parameter and calls the right generated client method.
     - `PushZedBoxLogsAsync` payload is unchanged; the API now reads `service` per line so the phone doesn't need to differentiate batches.

5. **Redeploy.**
   - `uv run lock-python && uv run generate-clients --config build/openapi-projects.json` (regenerates clients after route changes; lock first).
   - `uv run build --bake-file compose.zed.bake.yml --lock-only` (regenerate `.env.lock` after revert + new image hashes).
   - `uv run up --build --quiet-pull` (rebuilds host gateway without Listener C; brings up postgres etc.).
   - `uv run install-zed --build` (must run on the **physical host**, not in the COI sandbox — `nmcli` is unavailable in the sandbox; the install-zed `--build` path errors out with `FileNotFoundError: 'nmcli'` from inside the sandbox).
   - `uv run compile-unity --project CaptureTool --build android-mobile && adb install -r apps/AndroidMobile/Build/<ProductName>.apk` (path is printed by compile-unity).
   - Re-grant logcat permission post-install: `adb shell pm grant com.outernet.captureapp android.permission.READ_LOGS` (or use `uv run install --project CaptureTool` which auto-grants).

6. **Repro the cold-start RST one more time** and query the five Loki streams. Both the OkHttp `OkHttpH2` frame trace (`service=capture-tool` Tag=`OkHttpH2`) and the Caddy h2debug trace (`service=aoa-gateway-h2debug`) will be aligned to millisecond precision. Settle which of the three hypotheses is the cause:
   - Look for `<<` (received) GOAWAY / RST_STREAM frames in `service=capture-tool`. What error code?
   - Look for `wrote RST_STREAM` / `wrote GOAWAY` in `service=aoa-gateway-h2debug`. Which side initiated?
   - Look for the initial SETTINGS frame in either stream. What does `SETTINGS_MAX_CONCURRENT_STREAMS` advertise?
   - If hypothesis 1 (idle-stale), try a repro where login fires within 5 s of pipe-open and confirm no RST.

7. **Implement the actual code fix once hypothesis settled.** Default disposition: principled fix (whatever makes the cold-start request burst succeed at the protocol layer) is the first commit; JNI-cancellation plumbing fix (`Call.cancel()` on `CancellationToken`) is a second, independent commit.

8. **Cleanup after diagnosis.** Separate commit:
   - Remove `GODEBUG=http2debug=2` from `compose.rig.yml`.
   - Revert Caddy log level from `DEBUG` to default in `Caddyfile`.
   - Leave the supervisor, the per-source `/logs/...` routes, the line-level `service` field, and the extended reader — they are the durable transport, not diagnostic scaffolding.

## Key files

- `apps/AndroidMobile/Assets/Scripts/AndroidAoaHttpHandler.cs` — `ExecuteOverAoa` synchronously calls `AoaJni.Execute` over JNI; cancellation isn't plumbed to OkHttp's `Call.cancel()`. The 60 s `readTimeout` wall lives here in spirit.
- `apps/AndroidMobile/Assets/Scripts/Capture/ZedCaptureController.cs` — `HealthPollLoop` sets `requestCts.CancelAfter(2 s)`; that timeout is currently a lie because of the AndroidAoaHttpHandler issue. Also home of `LogDrainLoop` / `LogDrainOnce` which need to be extended to four sources.
- `apps/AndroidMobile/Assets/Plugins/Android/aoa-accessory-filter.androidlib/src/main/java/io/placeframe/android/AoaAccessoryClient.java` — OkHttp client config: `.readTimeout(60, TimeUnit.SECONDS)` is the 60030 ms wall; `ConnectionPool(1, 1, TimeUnit.DAYS)` is the single-FD pool. Static initializer at the top wires OkHttp's JUL logger to logcat tag `OkHttpH2`. **Keep.**
- `apps/AndroidMobile/Assets/Scripts/LogcatRelay.cs` — added `OkHttpH2:V` to the logcat tag whitelist. **Keep.**
- `apps/AndroidMobile/CLAUDE.md` — explains why h2c-prior-knowledge is mandatory for the AOA pipe (concurrent requests on a single duplex stream).
- `docker/aoa-gateway/Caddyfile` — Caddy config; has `log { level DEBUG }` + JSON access log. **Keep `output stdout`** so the supervisor (added by pending-thread #2) reads it.
- `docker/aoa-gateway/Dockerfile` — needs Python 3 added and CMD changed to invoke `supervisor.py` (pending-thread #2).
- `docker/aoa-gateway/supervisor.py` — **new file** (pending-thread #2). Behaviour spelled out in "GODEBUG transport" decision.
- `docker/aoa-bridge/src/aoa_bridge/main.py` — USB↔TCP shuttle. `log()` currently prints. Must switch to Python `logging` with file output via `RotatingFileHandler` (pending-thread #2).
- `docker/zed-capture/src/logging_config.py` — adds `"service": "zed-capture"` to JsonFormatter static_fields (pending-thread #2).
- `docker/zed-capture/src/routers/logs.py` — rename `/logs` → `/logs/app`; add three more endpoints; factor `LogSource`; extend `_ordered_log_files` for lumberjack timestamp backups (pending-thread #2).
- `docker/zed-capture/src/cursor_store.py` — parameterise by cursor-file path so each source gets its own (pending-thread #2).
- `docker/zed-capture/src/main.py` — already imports `logs_router`; no change.
- `docker/zed-capture/compose.rig.yml` — adds `zed-logs` volume mount + `ZED_BOX_ID` env to `aoa-gateway` and `aoa-bridge`; keeps `GODEBUG`; removes `aoa-alloy` service (pending-thread #1 and #2).
- `docker/api/src/routers/zed_box_logs.py` — replace hard-coded `"service": "zed-capture"` with `record.get("service")` per line, default `"unknown"` (pending-thread #2).
- `docker/aoa-alloy/` — **REVERT (delete)** (pending-thread #1).
- `docker/gateway/entrypoint.sh` — Listener C block. **REVERT** (pending-thread #1).
- `compose.yml` — gateway service `"8084:8084"` port mapping. **REVERT** (pending-thread #1).
- `compose.zed.bake.yml` — `ALLOY_DIGEST` base + `aoa-alloy` build target. **REVERT** (pending-thread #1).
- `scripts/src/scripts/install_zed/constants.py` — `aoa-alloy` entry in `ZED_SERVICES`. **REVERT** (pending-thread #1).
- `.env.lock` — `ALLOY_DIGEST` entry; regenerated via `uv run build --bake-file compose.zed.bake.yml --lock-only` after the revert (pending-thread #1).

## Operational notes for the next session

- `uv run install-zed --build` **cannot run inside the COI sandbox**; it shells out to `nmcli` which isn't present. The user runs that command on the physical host. Everything else (`uv run up`, `uv run lock-python`, `uv run generate-clients`, `uv run compile-unity`, `adb install`) works inside the sandbox.
- Force-push to `fix/install-zed-aoa-gateway-and-pull-logging` is **authorized**.
- Codegen commits must have message exactly `Run generate-clients`; no body, no rationale.
- Prose and code commit separately. The Alloy revert is all code; the corrected transport is all code; this memory update is prose. Don't mix.
- Use `uv run loki-query` for queries: `uv run loki-query '{service="aoa-gateway-h2debug"}' --since 5m --limit 200`.
- `service` and `service_name` are interchangeable in Loki LogQL — Loki auto-derives `service_name` from common label names including `service`.
