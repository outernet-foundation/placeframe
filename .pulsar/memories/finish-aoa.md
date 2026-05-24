---
updated: 2026-05-24
---

# Finish AOA — post-cold-start-fix follow-ups

## Goal

Close out the four hygiene/correctness items that were opened during
the AOA cold-start (Bug B) diagnosis and not addressed when the
primary fix landed. Three are debug-instrumentation leftovers; one is
a JNI cancellation gap; one is a defense-in-depth timeout; one is a
LogDrain cursor-persistence gap on process restart. They all touch
the same subsystem and read naturally as a single sweep.

## State

The cold-start fix itself (connection reset in `_run_once`'s `finally`
block during tear-down) has landed and is in production. None of the
four follow-ups below have been touched.

## Decisions

- **Single memo, not four bug files.** Same subsystem, same person
  picks them up together when they next touch AOA.
- **LogDrain belongs in this file** even though it is not strictly
  "AOA." The log-drain is the AOA-pipe log relay; whoever returns to
  AOA touches it as part of the same pass.

## Follow-up 1: AOA debug-logging cleanup

Three debug-firehose flags turned on during the cold-start diagnosis
are still on in production. None are needed now.

- **`GODEBUG: http2debug=2`** at
  `docker/zed-capture/compose.rig.yml:31`. Floods `aoa-gateway` with
  ~5000 HTTP/2 protocol events per 2 minutes, ageing Loki queries out
  fast. Remove the env line.
- **Caddy `level DEBUG`** at `docker/aoa-gateway/Caddyfile:4`. Verbose
  per-request logging. Keep `format json` and the `/loki/*`
  reverse-proxy block — drop only the DEBUG level back to INFO.
- **`"OkHttpH2:V"`** at `apps/AndroidMobile/Assets/Scripts/LogcatRelay.cs:30`.
  Verbose OkHttp h2 frame logging on the phone. Keep the JUL→logcat
  wiring (architectural); remove the `OkHttpH2:V` entry from the
  whitelist.

## Follow-up 2: JNI cancellation plumbing for AOA requests

In `AndroidAoaHttpHandler.ExecuteOverAoa`, the `CancellationToken` is
consulted only for the response-body stream. The synchronous
`AoaJni.Execute` call that issues the request does not respond to
cancellation. An upstream cancellation mid-request leaves the JNI
call running to completion; only the post-completion body read aborts.

Fix shape: plumb OkHttp's `Call.cancel()` over JNI so a token
registration can abort the in-flight call. Needs (a) a Java-side
method on the AOA client that holds a reference to the active `Call`
keyed by request id, and (b) a JNI bridge to invoke `cancel()` on it
from the C# cancellation callback.

Independent correctness gap. Not on any feature critical path; most
current flows don't cancel mid-request. Latent real bug.

## Follow-up 3: Lower OkHttp `readTimeout` on AOA client

`AoaAccessoryClient.java` inherits OkHttp's default 60s `readTimeout`.
The original 60s cold-start hang symptom (Bug A) was the pooled h2c
session waiting out exactly this timeout before dead-connection
eviction. The real fix — the tear-down reset in `_run_once`'s `finally`
— makes the timeout moot in practice today.

Defense-in-depth: lower `readTimeout` to 3-5s so that any future
regression where the bridge fails to issue a clean reset gets bounded
by the timeout instead of pegging a thread for a full minute. 60s is
far longer than any legitimate AOA request should take; the
protective value of catching anomalies fast outweighs lost headroom
for slow-but-legitimate requests.

One config-line change in `AoaAccessoryClient.java`.

## Follow-up 4: LogDrain cursor persistence across process restarts

In `apps/AndroidMobile/Assets/Scripts/Capture/LogDrainController.cs`,
the drain cursor (`logDrainCursorNs`) is held in memory only and pegs
to NOW on `Initialize()`. Any process restart between an AOA failure
and recovery loses every log line from the failure window prior to
the restart: APK reinstall, process kill, OS-side crash.

Observable symptom matches the earlier cursor-resets-on-flap bug
(drain restarts at NOW, prior failure-window logs unreachable), but
the mechanism is different (process boundary, not reconnection).

Fix shape: persist `logDrainCursorNs` via `PlayerPrefs` on every
successful drain tick, restore it on `Initialize()` instead of
pegging to NOW, and still apply the existing
`NOW - logDrainMaxLookback` cap on the restored value so a long-offline
process doesn't try to drain weeks of logs on resume.

## Key files

- `docker/zed-capture/compose.rig.yml` — `GODEBUG` env to remove.
- `docker/aoa-gateway/Caddyfile` — log level to lower.
- `apps/AndroidMobile/Assets/Scripts/LogcatRelay.cs` — OkHttp h2
  verbose whitelist entry to remove.
- `apps/AndroidMobile/.../AndroidAoaHttpHandler.cs` (call site of
  `ExecuteOverAoa`) — cancellation plumbing.
- The Java AOA client + the `AoaJni` bridge — `Call.cancel()` plumbing.
- `apps/AndroidMobile/.../AoaAccessoryClient.java` — `readTimeout`
  config line.
- `apps/AndroidMobile/Assets/Scripts/Capture/LogDrainController.cs` —
  cursor persistence via `PlayerPrefs`.

## Pending threads

1. Debug-logging cleanup (three single-line reverts across three files).
2. JNI cancellation: Java-side `Call` registry + JNI `cancel()` bridge
   + C# token-registration call.
3. Lower OkHttp `readTimeout` to 3-5s in `AoaAccessoryClient.java`.
4. `PlayerPrefs`-backed `LogDrain` cursor with `Initialize()` restore
   and `logDrainMaxLookback` cap.
