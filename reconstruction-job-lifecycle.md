---
updated: 2026-11-23
---

# Reconstruction job lifecycle ADR

This ADR replaces PR #172 (`port/devhh-cancellation`), which will be closed with a pointer to this branch. It also owns the checkpoint/resume dependency (S11) that the demand-driven GPU orchestration ADR handed off when GPU orchestration landed. That ADR and its plan are no longer in the repo. Nothing from PR #172 or from the external contributor's self-hosted branch is ported. Both are evidence, not code to take. Every mechanism here is worked out from first principles. Where a mechanism ends up matching one of theirs, the overlap is credited.

## Status and session protocol

This document is the entry point for a fixed sequence of sessions. A session that opens by reading this doc must check this section first.

1. **Brainstorming session (complete, 2026-11-23).** Frame identified, settled decisions recorded, open questions enumerated under a strict bar. A question is open only if the desired behavior or the architecturally correct design is genuinely ambiguous. Implementation effort and blast radius are never reasons to keep a question open.
2. **Design sessions (complete, 2026-11-23).** Checkpoint granularity, the verification mechanism, and the artifact write path were worked to settlement. See settled designs 8 through 12.
3. **Interview session (complete, 2026-11-23).** The operator closed every remaining question. The transient-failure question dissolved into a simpler routing rule, settled design 8. Cancellation became deletion and pause/resume entered the design, settled design 9. No questions were open at its close.
4. **Second interview round (complete, 2026-11-23).** The first planning pass stopped before producing a plan, because grounding the design in the code raised questions the first round had not reached. The operator ruled on each, one at a time. Six became settled designs 14 through 17, 19, and 21. Three dissolved into existing designs. One was withdrawn as not a design question.
5. **Planning session (complete, 2026-11-23).** The plan is `reconstruction-job-lifecycle-plan.md` at the repo root: ten linear phases, one per execution session, with progress recorded in the plan's status table.
6. **Execution sessions.** Land the plan on this branch and fold the hardened truth into the co-located `AGENTS.md` files, after which those files are the authority. The fate of this ADR and of the plan is the operator's decision and is not plan work.

## Problem

Preemption, crash recovery, resume, and operator control are not four features. They are transitions of one thing: ownership and intent for a reconstruction job. The Postgres row is the authority. Workers are untrusted reporters that can vanish, go silent while healthy, or arrive late after being declared dead. Three live defects on `dev` make that concrete today:

1. **Silent stages reap live workers.** The publisher flushes once at phase entry, then only on per-image ticks. Pre-extraction setup, bundle adjustment, OPQ/PQ training, and geometric verification emit nothing. A stage that outlasts the 30-minute lease timeout gets the job requeued while the worker is still working on it.
2. **No-op progress writes refresh nothing.** `updated_at` moves via a `BEFORE UPDATE` trigger, and SQLAlchemy executes no UPDATE when no column value changed. A worker that diligently re-sends the same phase keeps the lease stale. The stale-filter comment in `request_lease` asserts the opposite, so the wrong belief is documented in the code.
3. **Preemption consumes the failure budget.** The requeue path increments `requeue_count` for both timeout reaps and explicit SIGTERM requeues, and five requeues fail the job permanently. The gpu-orchestrator preempts a healthy reconstruction whenever localization demand arrives under contention. A contended GPU with recurring localization demand can fail a good job through healthy preemptions alone.

When a wrongful reap fires, nothing is safe about it. `succeed` and `fail` carry no lease identity, so the reaped-but-alive worker's late finalize overwrites whatever the replacement attempt has done. The external contributor's fleet watched this happen. Cancellation has no home in a lifecycle that cannot even tell its live owner from a zombie.

The correct design is one lifecycle state machine:

```
QUEUED ──grant(attempt N)──▶ WORKING ──succeed──▶ SUCCEEDED (terminal)
  ▲                            │
  │                            ├──completed, unsuccessful──▶ FAILED (terminal)
  ├──resume(operator)──────────┤              WORKING = any phase status,
   ├──error / reap─────────────┤              owned by exactly one attempt
   └──preempt(worker)──────────┘

pause(operator) ──▶ PAUSED ──resume(operator)──▶ QUEUED
delete(operator) ──▶ row and artifact prefix gone
resume(operator) ──▶ FAILED ──▶ QUEUED
```

Statuses: QUEUED, PAUSED, WORKING (the phase-status family), SUCCEEDED, FAILED. Pause is operator intent. System-initiated pauses are just QUEUED again. Cancellation is deletion.

## Sources and subsumption ledger

| Source | Disposition |
|---|---|
| PR #172 `port/devhh-cancellation` (Howard Huang's dev_hh work) | Closed with a pointer to this branch. The refused-write-as-signal mechanism is worked out again below and credited where it matches. His tests are rewritten, not ported. |
| Johnny Lee's `self-hosted` branch (private deployment mirror) | Not ported. His observed failure cases are the requirements record: the silent-stage reap, the no-op write, the double-build, the fleet that needs short timeouts. His checkpoint work, two monolithic stage-end npz objects behind an opt-in flag with no validation, is replaced by settled design 10. His measurement that descriptor storage at float16 leaves matching quality unchanged is adopted there. |
| `demand-driven-orchestration.md` S11 | Fulfilled. A preempted job presents as claimable resumable work counting in `queued`. The flush fits inside the orchestrator's negotiated ~60 s stop budget, and with shard-as-you-go upload the flush is nearly empty. Preemption costs a checkpoint cycle, not the whole build. The localizer has zero changes. |
| The other four dev_hh port PRs | Untouched. Sequencing note: #169 also edits `run_reconstruction.py`, so it should land first or be absorbed by rebase. |

## Settled design

Each entry was held against the strict bar and closed by principle or by operator ruling. The rationale is recorded so later sessions do not work it out again.

### 1. Lease identity

**Decision: a monotonic attempt integer column on the reconstruction row, incremented on every grant. The lease response carries it and every worker write echoes it.**

Two alternatives were rejected. Reusing the error counter mixes identity with budget. A random token per grant is stronger than one Postgres needs, because the row with row-level locking is already the serialization point. A dedicated column names exactly the concept: which grant is this.

### 2. Fencing

**Decision: `progress`, `succeed`, `fail`, `error`, and `preempt` all reject writes whose echoed attempt is stale, with 409.**

`error` and `preempt` must be fenced like the rest. A zombie's call to either would send the new owner's in-flight job back to the queue, which is a stomp by another door. Fencing is by attempt and by state together. A write lands only on a WORKING row, because a QUEUED row is owned by nobody until the next grant, so a matching attempt on a QUEUED row is refused like a stale one. The wire field is a new `lease_attempt`, distinct from the existing `progress_attempt`, which reports within-stage retry behavior and must not be overloaded.

### 3. The refusal channel

**Decision: one 409 body with a reason enum, `superseded`, `paused`, `not-found`, documented in the OpenAPI schema. The worker has one refusal handler: abandon the job and leave the stage artifacts untouched. `not-found` arrives as a 404, because the row is gone.**

The refusal is not an error. It is the only channel a worker has for learning that the world changed. `superseded` and `paused` both require the artifacts left alone, for a new owner or for the same job resuming later. `not-found` means deletion is sweeping the prefix, so the worker just stops. A zombie may upload shard objects for up to one heartbeat cadence after the sweep. Those are orphaned objects under a random UUID prefix, storage noise rather than corruption, and are accepted without mitigation.

### 4. Terminal integrity

**Decision: worker writes never flip a terminal state. An explicit operator resume is the one allowed transition out of a terminal state.**

A late `succeed` on a FAILED row is refused, and nothing resurrects SUCCEEDED or FAILED on its own. Resume, settled design 9, is the row's own authority acting deliberately on operator instruction. That is a different thing from a racy worker write, and it is honestly labeled.

### 5. Heartbeat

**Decision: the publisher re-sends its last state on a floor cadence of 60 seconds over the same progress endpoint, and the lease-server persists an accepted heartbeat even when nothing changed.**

A dedicated heartbeat endpoint would fragment the one channel that teaches the worker it lost ownership. Liveness is a protocol concept and gets a dedicated `lease_heartbeat_at` column that the reaper reads. `updated_at` reverts to a pure audit field. A boot-time invariant ties timeout to cadence, timeout at least 3x cadence, so a misconfigured pair fails loudly at startup.

### 6. Timeout and budget

**Decision: the lease timeout becomes a lease-server setting exposed through the score-tier config valve in both renderings. Default stays 30 minutes.**

Deployments genuinely differ. A spot fleet wants minutes and a home stack wants conservatism. With heartbeats fixed, the timeout needs to exceed missed heartbeats, not the longest silent stage.

**Decision: the error counter counts `error` calls and reaps only. `preempt` is uncounted. The existing cap of 5 fails the job. No backoff and no earn-back accounting.**

The cap exists to stop a deterministic poison job from wedging the queue forever. On a single-worker stack, an always-retry policy with no cap hands the same job back on every poll and starves everything behind it. The cap is the existing ten lines of code, not new machinery. Preemption is a scheduling decision, not a job property, so it consumes nothing. This closes live defect 3. Earn-back on stage progress is deliberately deferred. It exists to protect fleet jobs killed by SIGKILL-only preemption from exhausting the cap while making progress, and no such fleet is ours yet.

### 7. Preemption authority

**Decision: the worker is the only caller of `preempt`. Every stop reaches the worker as SIGTERM, whether it is a spot eviction notice, `docker stop`, a k8s drain, or the gpu-orchestrator swapping the GPU to the localizer. The worker flushes the upload queue, calls `preempt` for its own job, and exits. A worker that cannot answer is recovered by the reaper. The gpu-orchestrator stops containers and never writes to the lifecycle.**

One event, one path. The orchestrator calling the lease-server before it stops the container was rejected. It would be a second recovery mechanism for a worker that stopped responding, which is the reaper's one job. It would also make the orchestrator a lifecycle writer with neither a job id nor an attempt to write with, and the lease-server could not tell it from a stale worker.

Relying on the reaper costs at most the lease timeout, and usually less. The reaper runs only when a reconstructor polls, and after a preempt none runs until the orchestrator swaps back, which waits out the 600 second localization idle window. At a lease timeout of 10 minutes or less the job is already stale when the reconstructor returns, and its first poll recovers it. A short timeout is safe only while no call holds the GIL long enough to starve the heartbeat, because the call that blocks SIGTERM blocks the heartbeat too. Settled design 11 chunks the one call known to do it, geometric verification.

Fencing keeps a late `preempt` harmless. If the reaper already recovered the job and a new worker holds it, the call is refused as superseded and the exit proceeds.

### 8. Failure routing

**Decision: a completed-but-unsuccessful pipeline run fails the job. A raised exception is reported on `error` and retried under the cap. That is the whole policy.**

"The reconstruction itself failed" is not an exception. It is a result. The pipeline completes, reports no model or unsuccessful with its metrics, and the worker calls `fail`. That is FAILED, the honest terminal state for content failure. Any raised exception is reported on `error`, which carries the error string for visibility and increments the error counter. Exhausting the cap fails the job as FAILED-by-exhaustion with the last error on the row. There is no error-class taxonomy on the wire, no server policy branch, and no worker-side allowlist. The error string is for reading, not for routing. Routing is structural: exception versus completed result.

Underneath, short infrastructure blips never reach the lifecycle. Artifact uploads and downloads retry in place with backoff, since PUTs are idempotent, with a minutes-level tolerance per object. Heartbeat writes are fire-and-forget. A sustained outage escalates through the exception path and retries over and over until it heals or the cap trips. In the current world that hammering is preferred to backoff machinery, and the cap is the safety rail that stops the infinite loop. The cap also doubles as the discriminator between transient and permanent. A content-flavored exception reported on `error` costs a few cheap cycles, because shard resume makes retries cheap, and then lands FAILED via exhaustion. Self-correcting. Operator resume is the explicit override when the verdict is wrong.

### 9. Pause, resume, and cancellation

**Decision: there is no CANCELLED state. Cancellation is deletion. There is a PAUSED state with pause and resume endpoints. Resume makes both PAUSED and FAILED jobs claimable again.**

The verb space closes cleanly. Claimable and wanted is QUEUED. Not claimable and unwanted is DELETE, the existing route, which cascades the artifact prefix. For a half-built job that is exactly the right cleanup. Not claimable, wanted, and incomplete was the empty cell, and PAUSED fills it. A consumer watching a job cycle on broken infra, or wanting a build to wait until tonight, previously had no honest verb. QUEUED keeps hammering. DELETE destroys hours of checkpointed work, and a recreated row gets a new id and prefix, so the old work is unreachable anyway.

One loss is accepted and stated openly: a deleted job leaves no record that a cancel ever happened. That is consistent with the row being unwanted, and the repo history and the API's own logs remain.

- `POST /reconstructions/{id}/pause` moves any non-terminal state to PAUSED. It is an idempotent no-op when already paused and a 409 on terminal states. A working worker learns through the refusal channel with reason `paused`, abandons, and leaves artifacts alone, bounded by heartbeat cadence.
- `POST /reconstructions/{id}/resume` moves PAUSED or FAILED to QUEUED. It is an idempotent no-op when already QUEUED and a 409 on SUCCEEDED, because a finished job is not resumed. Build a new row instead. Resume resets `error_count`, per settled design 16. Resume-on-FAILED is the recovery verb for exhaustion calls the operator disagrees with, and it is the one allowed terminal exit of settled design 4.
- The grant query claims only QUEUED, so PAUSED is naturally inert. **The stale-lease reaper must exclude PAUSED**, or it would reap a deliberately held row. That is the one genuine trap in this design. `queue-state` counts PAUSED in neither bucket. Pause never touches the error counter.
- The schema drops the `cancelled` enum value. There is no migration path, per settled design 14.

### 10. Checkpoints are incremental artifact upload

**Decision: stage outputs upload to their final layout under `reconstructions/<id>/` as each shard completes, marked by a per-shard completion marker carrying the options hash, the pipeline version, and per-file checksums. There is no separate checkpoint namespace, no second format, and no flag. It is always on.**

The current code computes everything and then uploads everything at the end. Moving the upload to shard boundaries makes checkpointing a timing change rather than a new artifact class. The bytes upload exactly once, to their final names. Resume becomes a prefix check against markers. The alternative, a checkpoint namespace beside the final artifacts, stores every byte twice and answers no question this design leaves open.

**Granularity.** The three per-item stages shard inside the stage. The training stages carry one marker each. SfM runs whole.

| Stage | After |
|---|---|
| Feature extraction | many shards: keypoints, descriptors, global descriptors, sizes, uploaded as each batch completes |
| Pair generation | unchanged, one file. Cheap deterministic recompute |
| OPQ / PQ training | unchanged, one file each, plus a stage marker |
| Encode / `features.h5` | unchanged, one file |
| Matching | many shards of match indices, uploaded as each batch completes |
| Verification | many shards of two-view geometries, per settled design 11 |
| SfM | whole. pycolmap exposes no mid-run state serialization, and its outputs are the final artifacts they already are |

Marker absence is the crash detector, since a half-written prefix has no marker. On resume the options hash and pipeline version in the marker must match the lease. A mismatch means ignore and overwrite, because a re-run with different options must not reuse stale stage outputs.

**Resume semantics.** Nothing resumes inside the database. The local COLMAP database is disposable scratch, rebuilt on every run, and the artifact prefix is the only durable truth. A resumed worker downloads the capture tar, always, then loads feature shards for the features stage while re-canonicalizing all images to disk because SfM needs the processed files, recomputes pairs in memory in seconds, and enters the shard loops at the first unmarked shard. This is sound because every checkpointed stage is a deterministic function of its inputs. SfM is the exception and the one whole-stage redo.

**Descriptor shards.** The one genuinely new durable datum is raw descriptors. Today they never leave worker RAM. They are stored at float16, since matching quality is insensitive and the observation is the external contributor's, and cast to the pipeline's working precision on load. Four stages read them: OPQ training, PQ training, encode, and matching. At venue scale they are the largest intermediate there is. They are deleted with every other shard when the job succeeds, per settled design 19. Keypoints and PQ codes remain the permanent record. The GC rule is part of the core design, not an optimization to add later.

### 11. Verification: drive the stock kernel per shard

**Decision: one main COLMAP database. The shard loop drives stock `geometric_verification` per shard by controlling the matches table. Write the shard's matches, run the stock kernel, harvest the resulting two-view geometries into a verification shard artifact, delete the shard's match rows, and move on. A final pass rewrites all matches so the uploaded `database.db` artifact keeps today's shape.**

History: a bespoke per-pair thread-pool verifier existed until `f36116ad` (2026-06) replaced it with stock `geometric_verification(rig_verification=True)` to gain rig verification. The price was a callback-less black box whose progress is today a child subprocess polling the sqlite database, `_VerificationProgressPoller`, and this design deletes it. A probe of the pinned pycolmap 4.0.4 confirmed that the stock verifier does **not** skip pairs that already have two-view geometries. Rerunning it re-verifies every match present, so there is no free fast-forward and some driving machinery is unavoidable. What is avoided is reimplementing the kernel. Rig verification, `EstimateRigTwoViewGeometries`, is nontrivial rig-constrained estimation reachable only through the stock entry point, and replicating it in Python is a fidelity risk on the step that guards geometry quality. The rule is: unroll the driver, keep the kernel. SfM already follows the same principle.

Constraints and consequences:

- **Shards group by frame pair**, so the rig pass inside each invocation aggregates across the complete set of camera pairs for a frame pair. An arbitrary pair-count split can silently break rig verification.
- The matches table is not where matches live. The match shards are the record. The table only hands one shard at a time to the kernel. SfM, the VIO essential-matrix check, and the metrics builder all read two-view geometries. Only the archived database consumes raw matches, and the final parity rewrite restores them.
- On resume, completed verification shards are replayed into the rebuilt database as direct two-view-geometry writes, and the loop starts at the first unmarked shard.
- The whole stage runs under `VERIFYING_GEOMETRY` with progress counted in shards, per settled design 21. Each call runs the pair pass and the rig pass back to back, so no shard boundary falls between the passes.
- Per-invocation overhead is the stock kernel's database open and pair scan, bounded by shard sizing.
- `workloads/reconstructor/AGENTS.md` currently describes the pre-June thread-pool verifier as shipped behavior. Correcting it rides this branch.

### 12. The artifact write path

**Decision: artifact and shard writes go through a bounded asynchronous queue drained by a background uploader. The marker is the commit point and is written last, by the uploader, after that shard's data objects are durably stored. Backpressure blocks the producer rather than dropping.**

These are artifacts and none may be lost, so a full queue blocks compute. The design degrades honestly to synchronous behavior under bandwidth starvation, which is the correct degradation. Marker-last ordering puts the atomicity story in one thread. The SIGTERM path becomes "flush the queue, drop the in-flight partial shard," which is why the orchestrator's 60-second stop budget stays mostly unspent. PUTs retry in place with backoff, and that is the blip-absorption layer of settled design 8. Progress and heartbeat writes are the separate, tiny, fire-and-forget HTTP channel the flusher already owns.

### 13. Docs, tests, wire

The lifecycle law moves into the lease-server's agent doc. The refusal channel, shard layout, GC rule, and verification choreography move into the reconstructor's. The orchestrator's S11 paragraph flips from reservation to description. The data-flow section of `workloads/AGENTS.md` updates.

Wire changes on the lease-server spec: `lease_attempt` on the grant, `requeue` replaced by `error`, which carries the error string, the `preempt` endpoint, and documented 409 bodies on `progress`, `succeed`, `fail`, `error`, and `preempt`. Wire changes on the api spec: `pause` and `resume`, the removal of `retry`, plus delete-during-flight semantics. There is no cancel route. The schema change adds the attempt column and `lease_heartbeat_at`, adds the PAUSED enum value, removes `cancelled` and `verifying_rig_geometry`, and renames `requeue_count` to `error_count`. Regen commits keep their canonical messages.

Tests cover, at minimum: fencing rejection on all five writes, heartbeat persistence across no-op writes, the budget's counting rules, pause/resume/delete transitions including the late-succeed-on-FAILED race, marker validation and resume-skip, the matches-table choreography including frame-pair grouping, and the SIGTERM queue flush.

### 14. No migration path

**Decision: the schema changes in this ADR ship without a migration. A database that predates them is rebuilt from the schema directory.**

No production databases exist, so nothing has to be carried forward and `cancelled` simply leaves the enum. Rebuilding is also the only option the tooling leaves. Postgres cannot drop an enum value, and pg-schema-diff plans a removed value as `DROP TYPE` plus `CREATE TYPE`, which fails while a table still uses the type. A dev machine that already holds a database volume recreates it once when it picks up the change. The plan records the tool limit in `database/AGENTS.md`.

### 15. Resume replaces retry

**Decision: `PUT /reconstructions/{id}/retry` is removed. `POST /reconstructions/{id}/resume` is the only verb that makes a PAUSED or FAILED job claimable again.**

`retry` already made the FAILED-to-QUEUED move and accepted CANCELLED, a state that no longer exists. Two routes for one transition would make every client learn a split that has no reason behind it. Keeping `retry` as an alias was rejected because a second name outlives its cause and shows up in every generated client. Teaching `retry` to un-pause instead of adding `resume` was rejected because the name is wrong for lifting a hold and because `pause` loses its natural counterpart. The capture-tool app is the one caller and picks up the renamed call in the companion change the enum change already forces on it.

### 16. Resume resets the error counter

**Decision: `resume` sets `error_count` back to 0, whether the row comes from PAUSED or from FAILED.**

The cap protects the queue from a job that loops with nobody watching, and resume is an operator watching. A resumed job therefore gets the full budget of five again. Leaving the counter alone was rejected because a job resumed from exhaustion would still sit at the cap and fail on its next exception or reap, so the recovery verb of settled design 9 would buy one attempt with no tolerance for failure. Resetting only on the FAILED path was rejected because one verb with two behaviors is the split settled design 15 removed. The refill that pause and resume gives a job that never failed is accepted, since it takes an operator action to trigger.

### 17. Three causes and four routes

**Decision: a job that stops before succeeding stops for one of three causes, and each cause has its own route. The user paused it, infra took the machine away, or the attempt failed. `requeue` leaves the wire. Errors are reported on `error`. Infra stops are reported on `preempt`. `fail` never retries.**

| Cause | Who reports it | Route | Row goes to | Counts toward the cap |
|---|---|---|---|---|
| Told to stop, by the user | the api, when the operator pauses | `POST /reconstructions/{id}/pause` | PAUSED | no |
| Told to stop, by infra | the worker on SIGTERM | `preempt` on the lease-server | QUEUED | no |
| Finished, bad result | the worker | `fail` | FAILED | no |
| Threw, or wedged and reaped | the worker, or the reaper | `error` on the lease-server | QUEUED, or FAILED once the cap is spent | yes |

A route is named for what the caller reports, never for what the server then does. The row is the authority and callers only report. `requeue` broke that twice. It carried two causes with two counting rules, so the server could not tell an infra stop from an error. And it kept the name when an error at the cap produced FAILED instead of a queue entry, while answering exactly as a successful call does. `error` answering the same way in both cases reads true, because the caller only reported the error. `preempt` puts a working job back in the queue, never counts, and never fails it, so its name is true in every case.

The first cause has two routes because its callers want different outcomes. A user pause holds the job until someone resumes it. An infra stop goes straight back to the queue, because nobody is coming to resume it. The worker calls nothing when a user pauses. It learns through the refusal channel and stops.

The reaper is not a call. It applies the `error` rule in bulk to a job whose worker went silent, and it counts the same way. The worker's `preempt` call echoes its attempt like every write, so a call that arrives after the reaper already recovered the job is refused as superseded and changes nothing. The counter only ever counts errors, so the column is `error_count`.

### 19. Shards go at success

**Decision: every object written only for resumption stays for the whole job and is deleted when the job succeeds. That covers feature shards, descriptor shards, match shards, verification shards, and every marker. Nothing is deleted at a stage boundary.**

A resumed job may need any shard, so deleting before success is a bet that no earlier stage ever has to run again. Deleting descriptor shards once the training markers exist was rejected. Training runs before matching, so that would strand a resumed matching stage with nothing to match. Matching needs the descriptors anyway, so the peak footprint is the same under any rule. Waiting for success only keeps them through verification and SfM, and descriptors are the one large intermediate.

The worker deletes after `succeed` is accepted and never before, because a refused `succeed` means the job is no longer its own. A FAILED job keeps everything, since resume may need any shard, and the storage returns when the job is deleted. A worker that dies between the accepted `succeed` and the deletion leaves that job's shards behind. That is rare and small.

What remains is the final artifacts, so a finished job's prefix looks as it does today: `global_descriptors.h5`, `features.h5`, `opq_matrix.tf`, `pq_quantizer.pq`, `sfm_model/`, `database.db`, `pairs.txt`, and `pairs_with_source.csv`.

The tar export carries final artifacts only. It skips the shard prefixes and every marker, beside its existing `database.db` exclusion, so a tar never depends on whether a job's cleanup finished. Export refuses any job that has not succeeded, so in a normal job there is nothing to skip.

### 21. One status for verification

**Decision: verification runs under `VERIFYING_GEOMETRY` for its whole length, with progress counted in shards. `verifying_rig_geometry` leaves the status enum.**

One `geometric_verification(rig_verification=True)` call runs the pair pass and then the rig pass over the matches it is given, holding the GIL throughout. The worker can act only between calls, and every shard runs both passes inside its own call, so no shard boundary falls between the passes. Running the pair pass as its own sweep to give it its own status was rejected. The stock kernel cannot run the rig pass alone and does not skip pairs that already have a result, so the second sweep would compute the pair pass twice, and more wall-clock is not acceptable here. Guessing the pass by watching the database from a child process was rejected, because the status would flip on every shard and the poller that settled design 11 deletes would stay. Changing the kernel to report its pass was rejected, because it means building our own pycolmap. The second label was a nicety. The worker reporting real progress, answering a stop signal between shards, and skipping finished shards on resume are what the shard loop is for, and all three hold with one status.

## Open questions (second interview round)

None. The round closed every question. Planning can start.

## Closed questions (interview record)

- **Transient failures** (was Q1): dissolved by settled design 8. Completed-unsuccessful fails, exceptions go to `error` and retry under the cap, and blips absorb in the IO layer. No classification machinery anywhere.
- **Cancellation**: no CANCELLED state. Deletion is the verb, per settled design 9.
- **Pause and resume**: PAUSED added, and resume covers PAUSED and FAILED by operator ruling. It is the recovery verb for wrong exhaustion calls.
- **Preempt route shape** (was question 18): dissolved. The orchestrator does not call the lease-server, per settled design 7, so `preempt` is a per-job write from the worker and needs no shape decision.
- **Shard retention after success** (was question 20): merged into settled design 19. One deletion rule covers every shard.
- **Shard objects in the tar export** (was question 22): dissolved into settled design 19. Export refuses unfinished jobs and success deletes the shards, so only the cleanup-leak edge remained, and the export filters it.
- **Retirement of this ADR and the plan** (was question 23): withdrawn as not a design question. When the plan is done the work is done, and the fate of these two prose documents is the operator's decision.

## Deliberately deferred (not open)

- **Earn-back accounting** on the error cap. Revisit when a real fleet of ours loses workers to SIGKILL-only preemption while jobs make progress.
- **Backoff or parking** on retry cadence. Revisit when hammering is provably costly in practice.
- **Orphan-shard cleanup** after delete-versus-zombie races. Revisit when the bucket noise is observed to matter.

## Consequences

- PR #172 is closed with a pointer here. The remaining four dev_hh port PRs proceed independently. #169 shares `run_reconstruction.py` with this branch and should land first or be absorbed by rebase.
- The capture-tool app needs a companion change when it bumps its api client pin: drop the `Cancelled` arms, handle `Paused` in its status mapping, label switch, and polling, and call `resume` where it called `retry`.
- The gpu-orchestrator's code is untouched. It stops containers and reads `queue-state` as it does today. Only its agent doc changes, per settled design 13.
- The localizer is untouched. Localizer capacity work, meaning request threading and replica orchestration, is out of scope and unaffected by anything here.
- Credit where mechanisms coincide. The refused-write-as-signal design rediscovers Howard Huang's cancellation channel. The heartbeat and budget semantics answer Johnny Lee's observed failure cases. Float16 descriptor storage adopts his measured observation. The implementations are new.
