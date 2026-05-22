---
updated: 2026-05-22
---

# LogDrain cursor resets to NOW on every reachable-flip, losing the exact log window we need to diagnose AOA cold-start

## Goal

The Capture Tool drains box-Loki to host-Loki by polling Caddy at `/loki/api/v1/query_range` and POSTing batches to `/loki/api/v1/push`. The drain repeatedly **silently discards** the most diagnostically-valuable log window: the AOA cold-start failure window, when bridge / Caddy / zed-capture logs explain *why* the pipe RST'd and recovered.

Proximate symptom observed during the 2026-05-22 22:38 UTC AOA cold-start repro: host-Loki had ZERO box-side entries for the 22:37:44 – 22:38:15 window (entire cold-start drama). Bridge and Caddy hex dumps + GOAWAY frames sat in box-Loki on the ZED box. The Capture Tool's LogDrain task started up fresh after the pipe healed and pinned its cursor to "now," so the buffered failure-window logs were unreachable. They will be evicted by box-Loki's 72 h retention without ever reaching host-Loki.

This is the root cause of the recurring "bridge looks silent in host-Loki" observation called out as a side-thread in `aoa-cold-start-rst-diagnosis.md` (item 5 under Pending threads). It is also the reason every cold-start diagnostic cycle has required SSHing to the box to read raw `docker logs` — the data exists, the relay was just designed to throw it away.

## State

### What's confirmed (smoking gun captured in host-Loki on 2026-05-22)

After the cold-start recovery at 22:38:15, host-Loki shows the LogDrain ran exactly one query against box-Loki:

```
start = 1779489495217726000
end   = 1779489495218411000
diff  = 685 µs
```

A 0.685 ms window. It found nothing and the cursor advanced from there. Every byte of bridge + Caddy + zed-capture output from 22:37:44 – 22:38:15 (the failure + recovery period) has timestamps **before** that cursor, so it is permanently invisible to host-Loki by this design.

### Sequence that produces the loss

1. AOA accessory detaches → `OnAccessoryDetached` → `zedStatus = Unreachable` → `zedReachable = false`.
2. The `zedStatus.Subscribe(...)` callback at `ZedCaptureController.cs:159` fires → `EvaluateLogDrainState()` → `logDrainTask.Cancel()`. **Existing drain loop is killed mid-tick.**
3. Health polls fail (`EBADF / EIO / accessory not ready`) for ~5 s while the bridge `resetDevice()`s and the user accepts a second AOA permission dialog. The bridge writes interesting hex-dump and Caddy writes the `FRAME_SIZE_ERROR` GOAWAY during this window — into box-Loki.
4. Pipe heals → health poll succeeds → `zedStatus = Ready` → `zedReachable = true` → `EvaluateLogDrainState()` fires again.
5. `ZedCaptureController.cs:339`: `logDrainCursorNs = ToUnixNanos(DateTime.UtcNow);` — cursor pegged to *this moment*.
6. New loop's first query has `start ≈ end`. Zero entries. From here forward only `>=NOW` is ever queried.

The failure window's logs are now stranded in box-Loki for 72 h (its retention) and then evicted.

### Three problems with the current `EvaluateLogDrainState` (`ZedCaptureController.cs:330-341`)

1. **Cursor reset on every reachable-flip wipes recovery-period logs.** Proximate cause of the 25-minute Loki gap. The cold-start RST is *precisely* the case where `zedReachable` does a true→false→true flip, so the period we most need to capture is the one whose cursor reset throws it away.
2. **Gating on `zedReachable` couples drain liveness to AOA pipe health.** When the AOA pipe is broken, drain doesn't run; when the pipe heals, drain restarts forgetting the broken window. The natural failure mode is exactly the one that hides the bug we need to debug.
3. **Even pre-cold-start, line 339 always resets cursor on start.** First-time login resets to NOW (correct — no replay desired). But every subsequent unrelated state evaluation that ends with the predicate true also re-pegs cursor to NOW, potentially skipping legitimate buffered logs the previous run hadn't gotten to.

### Why "wait for box-Loki polling to catch up" doesn't help

The drain task is *cancelled* on the false flip, not paused. There is no in-memory buffer; `logDrainCursorNs` is just a `long` that gets re-initialized on every restart. There is no on-disk persistence. Nothing in the existing code path preserves the pre-failure cursor across the gating flip.

### What's NOT broken

- **Box-Loki transport itself** — Alloy → box-Loki on the box is fine; entries are present in box-Loki, they just never get pulled.
- **LogDrain steady-state polling** — when the pipe is healthy and `zedReachable=true` continuously, the drain works as designed.
- **Caddy `/loki/*` reverse-proxy** — confirmed serving query_range/push at 22:38:15 onwards.

This is purely a state-machine bug in `EvaluateLogDrainState` / `LogDrainLoop` lifetime management.

## Decisions

### Investigate-only this turn; yielded after diagnosis

User's original `/memorize` came after a deliberate investigation pass. No code changes were made. The fix is described as a sketch below but not implemented.

### The fix is a three-line state-machine change, not a redesign

The transport (Alloy → box-Loki → Caddy → drain → host-Loki) is correct. Don't redesign it. The only thing wrong is *when* the cursor resets and *what* gates the drain task lifetime.

## Fix sketch (recommended path)

Smallest change that recovers the missing data:

1. **Gate only on `loggedIn`, not on `zedReachable`.** Let LogDrain queries fail during AOA downtime — the existing `try/catch` at `ZedCaptureController.cs:354` already handles that (`Log.Info("log drain tick failed")`) and the loop retries every `logDrainIdlePollIntervalSeconds` (5 s).
2. **Set cursor to NOW only on the first transition into a running state per app session.** On cancellation due to a transient gating flip (which under fix #1 only happens when `loggedIn` flips, i.e. logout/login — not on AOA hiccups), preserve the existing cursor so the next run picks up where the prior one left off.
3. **Cap maximum lookback** (e.g. cursor never older than `NOW - 1h`) so a long-offline app doesn't try to replay days of history when it reconnects. Defense against the case where a user backgrounds the app for a long time then returns.

Three lines of state-machine logic on top of the existing structure. The drain loop body (`LogDrainOnce`) does not need to change.

Concrete locations:

- `ZedCaptureController.cs:159-160` — drop the `zedStatus.Subscribe` line; keep only `loggedIn.Subscribe`.
- `ZedCaptureController.cs:330-341` — `EvaluateLogDrainState`: change predicate to `if (!App.state.loggedIn.value) return;`. Track `logDrainStartedThisSession` (or check whether the task is `Complete` vs. just-cancelled-and-replaced) to decide whether to overwrite `logDrainCursorNs` or leave it alone.
- Optional cap: `logDrainCursorNs = Math.Max(logDrainCursorNs, ToUnixNanos(DateTime.UtcNow - TimeSpan.FromHours(1)));` immediately before the loop body queries.

## Open questions

- **Should the LogDrain cursor persist across app process restarts** (e.g. via `PlayerPrefs`)? The current scope is "within a single app session." The cross-restart case is the same scenario that produced the in-memory-only gotcha noted in `aoa-cold-start-rst-diagnosis.md` — if the user kills/relaunches the app between failure and recovery, even the proposed fix doesn't help. Out of scope for the immediate fix but worth raising as a follow-up if it bites in practice.
- **Is the 1-hour lookback cap the right value?** Too short = miss legitimate backlog after a brief network blip. Too long = pull megabytes of irrelevant history on every cold start. 1 h is a guess; could be 15 min or could be 24 h. Worth checking against box-Loki ingestion rate (`uv run loki-query --raw` against a healthy session and time-bucket the count).
- **Should the predicate cover `App.state.zedReachable` at all?** Argument for keeping it: there's no point hammering Caddy with queries when the AOA pipe is known-down. Counter-argument: queries cost ~1 round-trip every 5 s, the failures are cheap, and the proposed fix makes them harmless. Recommendation: drop the gating; let the loop's idle backoff handle the no-data case naturally.

## Key files

- `apps/AndroidMobile/Assets/Scripts/Capture/ZedCaptureController.cs` — LogDrain implementation. Lines of interest:
  - `92-105` — drain constants and statics (`logDrainCursorNs`, `logDrainTask`, `logDrainIdlePollIntervalSeconds = 5f`, `logDrainBatchLimit = 500`).
  - `159-160` — subscriptions that invoke `EvaluateLogDrainState`. The `zedStatus.Subscribe` line is the proximate cause of the spurious cancel-on-pipe-flip behavior.
  - `330-341` — `EvaluateLogDrainState`. Line 339 is the cursor reset.
  - `343-...` — `LogDrainLoop`. The `try/catch` at the loop body already tolerates query failures gracefully.
- `apps/AndroidMobile/Assets/Scripts/Capture/AppState.cs:87-99` — `zedReachable` derived from `zedStatus` via `IsZedReachable`. Flips to false on `Unreachable`, `LostMidCapture`, etc.
- `.pulsar/memories/aoa-cold-start-rst-diagnosis.md` — parent diagnostic memo. Pending thread #5 there is *this* bug. Update that memo's pending-threads list to point here once a fix lands.
- `docker/aoa-gateway/Caddyfile` — `handle /loki/*` reverse-proxy to box-Loki at `127.0.0.1:3100`. Drain queries hit this path.
- `docker/aoa-loki/config.yaml` — box-Loki, 72 h retention. After 72 h the missed window is gone permanently regardless of drain fixes.
- `docker/aoa-alloy/config.alloy` — box-side log shipper into box-Loki. Working as intended.

## Pending threads

1. **Implement the fix sketch.** Three locations in `ZedCaptureController.cs`; spec is above. Yielded after diagnosis at user's prior `/memorize`. Note: per CLAUDE.md, prose and code commit separately — this memo update is its own commit; the C# change is a separate commit.

2. **Cross-restart cursor persistence (`PlayerPrefs`).** Optional follow-up. Not required to close the immediate gap but the only way to also capture failures that happen before the user notices and reopens the app.

3. **Audit other `Evaluate*State` callbacks for the same anti-pattern.** `EvaluateHealthPollState` at `ZedCaptureController.cs:251-...` is gated on `loggedIn` only (good), but if any other long-running task in the codebase resets its progress on every gating flip, it has the same latent bug. Quick grep: anything matching `Cancel()` immediately followed by re-initialization of a cursor / offset / sequence number.

4. **Re-test the cold-start RST repro under the fix.** Once the fix lands and the box is cycled, repro the cold-start dance: cable, dialog #1, captures-tab tap, dialog #2, captures load. Expect host-Loki to show the full bridge hex dump (`on_in_complete` 512 B first-bytes log) and Caddy `wrote GOAWAY ErrCode=FRAME_SIZE_ERROR` *in the same Loki query* without SSHing to the box. That's the verifier.

## Operational notes for the next session

- Reproducing the bug requires producing an AOA pipe flap with bridge/Caddy logs flowing during the down window. Cleanest repro: `uv run install-zed --build` on the host (cycles ZED), let the phone reconnect, then unplug + replug the AOA cable. Watch host-Loki for the gap.
- `uv run loki-query '{service_name=~".+"}'` (or `{service=~".+"}`) against host-Loki tells you whether box entries are arriving. With the drain working, expect entries labeled `service=aoa-bridge`, `service=aoa-gateway`, `service=zed-capture`. Without the fix during a cold-start cycle, you'll see a multi-second gap straddling the recovery.
- Avoid SSHing to the box as the workaround if at all possible — every SSH workaround papers over this exact bug and obscures whether the fix is working.
- Codegen commits must be exactly `Run generate-clients` etc; prose and code commit separately. This memo update is a prose-only change in `.pulsar/memories/`.
