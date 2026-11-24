# lease-server/

## What this is

The control-plane work queue for reconstruction jobs. The `reconstructions` row is the single authority for job ownership, intent, and progress; workers are untrusted reporters that can vanish, go silent while healthy, or arrive late after being declared dead. The reconstructor is the only writer (poll and report); the gpu-orchestrator reads `GET /queue-state` as a demand signal. No auth and no gateway route — the compose-internal network is the boundary (`workloads/AGENTS.md`).

## The lifecycle law

States: `QUEUED`, `PAUSED`, WORKING (the phase-status family the pipeline reports: `extracting_features` through `reconstructing`), `SUCCEEDED`, `FAILED`.

```
QUEUED ──grant──▶ WORKING ──succeed──▶ SUCCEEDED (terminal)
  ▲                 ├──completed, unsuccessful──▶ FAILED (terminal)
  │                 ├──error / lease-timeout reap──▶ QUEUED, or FAILED at the cap
  │                 └──preempt (worker SIGTERM)──▶ QUEUED
  ├──pause (operator, via api)──▶ PAUSED ──resume (operator)──▶ QUEUED
  └──resume (operator, via api)──▶ QUEUED (from FAILED; resets the error budget)
```

The law, enforced in `src/routers/leases.py`:

- **Lease identity is `lease_attempt`**: monotonic, incremented on every grant, echoed by every worker write. `progress_attempt` is a different concept (within-stage retry reporting) and must not be overloaded into fencing.
- **All five worker writes are fenced** — `progress`, `succeed`, `fail`, `error`, `preempt` (`_fenced_row`). A write lands only on a WORKING row whose `lease_attempt` matches the echo. A QUEUED row is owned by nobody until the next grant, so even a matching attempt refuses as `superseded`; terminal rows refuse (`superseded`) because an operator resume is the one allowed exit from terminal; PAUSED refuses (`paused`).
- **The refusal channel is one 409 body**, `{"reason": "superseded" | "paused"}`; a missing row is a 404 (deletion in flight). A refusal is information, not an error — the worker abandons the job and leaves artifacts untouched. The rendered body and the OpenAPI `REFUSAL_RESPONSE` description must stay in agreement; the generated client is the contract test.
- **Liveness is `lease_heartbeat_at`, not `updated_at`** — `updated_at` is pure audit. The heartbeat column is stamped on grant and on every accepted progress write; the progress route issues a core `UPDATE` rather than ORM attribute mutation precisely because SQLAlchemy skips no-op updates, and a diligently re-sent identical progress must still refresh the heartbeat. Boot invariant `lease_timeout_s >= 3 * lease_heartbeat_cadence_s` (a settings validator, so a misconfigured pair crashes the server at startup, not at first reap).
- **The error budget counts `error` calls and lease-timeout reaps only**, toward `MAX_ERROR_ATTEMPTS` (5). `preempt` is a scheduling decision and `fail` a content verdict; neither counts. At the cap, `error` flips the row to FAILED, leaves `error_count` unchanged, and answers 200 exactly as the below-cap branch does — a route is named for what its caller reports, never for what the server then does with the row.
- **The reaper runs inside `request_lease`** in its own transaction (recovery piggybacks on the worker poll; there is no timer service), reaping WORKING rows whose heartbeat lapsed the timeout. **PAUSED is excluded from every "holds no lease" set** — the reaper's stale filter, the fenced-write predicate, `queue-state`'s `in_flight` — because a deliberately held row must never be reaped. The grant query needs no PAUSED case of its own because it selects `QUEUED` only; any new status filter must carry PAUSED through all of these.
- **`queue-state` buckets**: `queued` counts only `QUEUED`; `in_flight` counts the WORKING family; PAUSED lands in neither, so a paused job exerts no batch demand on the gpu-orchestrator.

The wire contract detail (field names, request/response shapes) lives in the OpenAPI schema and the generated client under `packages/generated/python/lease-server-client/`.

## Schema coupling

The `reconstruction_status` enum cannot lose values without rebuilding the database from `database/`: Postgres cannot drop an enum value, and pg-schema-diff plans a removal as `DROP TYPE` + `CREATE TYPE`, which fails while a table still uses the type (`database/AGENTS.md`).
