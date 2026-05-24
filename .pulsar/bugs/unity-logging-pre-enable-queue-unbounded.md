# Unity logging `LokiSink` queue is unbounded pre-`EnableLoki`

**Severity**: medium — slow-leak OOM in any session that emits logs before login and never logs in.

**Location**: `packages/unity/Logging/Assets/Package/Runtime/LokiSink.cs` (`_pending` LinkedList) and `packages/unity/Logging/Assets/Package/Runtime/Logger.cs` (`Initialize` constructs the sink; `EnableLoki` starts the drain).

**Symptom**: A process that calls `Initialize` but never reaches `EnableLoki` (user never logs in, login fails, demo scene) accumulates one `PendingEntry` per distinct log fingerprint forever. The drain loop is only spawned by `Enable`, so nothing dequeues. The duplicate-collapse logic in `Emit` caps repeats of the same line, but distinct lines grow without bound. There is no disk spill, no event-count cap, no byte-count cap on `_pending` itself (the `MaxBatchEvents` / `MaxBatchBytes` constants gate batch *send*, not queue *length*).

**Mechanism**: `Emit` appends to `_pending` unconditionally whenever `!_disposed`. `DrainLoop` is started only from `Enable`. Pre-Enable, the queue is write-only.

**Fix sketch**: Cap `_pending` at a hard ceiling (e.g. 10k entries or 10 MB), dropping or coalescing oldest entries when full. Surface drop counts via `Serilog.Debugging.SelfLog`. Alternative: have `Initialize` start the drain loop in a "buffer locally, don't POST" mode and let `Enable` flip the switch.

**Verification**: In a test scene, call `Initialize` without `EnableLoki`, emit 100k distinct log lines, assert process RSS stays bounded and a SelfLog "queue full, dropping" line is emitted.
