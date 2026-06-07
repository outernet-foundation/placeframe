# packages/unity/Logging/SPEC.md

## What this is

`Outernet.Logging` is a Unity package that wires Serilog into a Unity app and ships log events to the Placeframe server's Loki over HTTPS via the public gateway, authenticated with a Keycloak Bearer token supplied by the consumer. It also intercepts `UnityEngine.Debug` so anything that goes through Unity's log handler (including native plugins, async unobserved exceptions, and R3 subscription faults) flows through the same Serilog pipeline. The in-repo consumer is `apps/CaptureTool/` (`app=capture-tool`). The package is referenced as a file-pathed UPM dep (`org.outernet.logging` at `file:../../../packages/unity/Logging/Assets/Package`).

## Shape

The package is one asmdef (`Outernet.Logging`) with nine runtime source files; no editor code, no tests.

```
packages/unity/Logging/Assets/Package/
|-- package.json
`-- Runtime/
    |-- Outernet.Logging.asmdef                  refs UniTask, R3.Unity
    |-- Logger.cs                                lifecycle + Unity-log interception + Serilog factory
    |-- Log.cs                                   static call surface + Microsoft.Extensions.Logging adapter
    |-- LokiSink.cs                              in-memory queue + thread-pool drain to Loki
    |-- UnityLoggerConfiguration.cs              ILogEventSink piping to UnityEngine.Debug (colored console)
    |-- Enricher.cs                              message/messageTemplate/stackTrace/exception capture
    |-- JTokenFromSerilogProperty.cs             Newtonsoft conversion for the Loki line payload
    |-- ExponentialBackoff.cs                    1s -> 60s schedule for the drain loop
    |-- LogLevel.cs                              Trace/Debug/Info/Warn/Error/Fatal/None
    |-- LogGroupColorAttribute.cs                marker placed on consumer enum members
    `-- InnerFramesHiddenFromStackTraceAttribute.cs   marker for stack-trace trimming
```

### Public surface

- `Logger<TLogGroup>.Initialize(labels, suppressErrors = null)` -- set up Serilog, install Unity-log interception. `labels` (e.g. `[("app","capture-tool"),("platform","android-mobile")]`) bake into the Loki stream selector for every push. `suppressErrors` is a list of substrings: a message containing any of them is downgraded from `Error`/`Exception` to `Log` before forwarding (used for known-benign native spam like ARCore `GL_INVALID_ENUM`).
- `Logger<TLogGroup>.EnableLoki(apiUrl, tokenProvider)` -- turn on the Loki drain. Until this is called, emitted events queue in memory. `apiUrl` is the full public URL of the placeframe gateway (e.g. `https://x.ngrok-free.app` or `http://192.168.1.100:58080`); the sink appends `/loki/api/v1/push`. `tokenProvider` is a `Func<UniTask<string>>` returning a Bearer token (Placeframe consumers pass `() => Auth.GetOrRefreshToken()`) -- or `null` for unauthenticated push, used when the server runs in `AUTH_MODE=disabled` and the gateway has dropped its `/loki/*` `forward_auth` directive (see `docker/gateway/entrypoint.sh`). The sink builds its own `HttpClient` over the default `HttpClientHandler`.
- `Logger<TLogGroup>.Terminate()` -- dispose the sink and unhook R3/Task subscriptions. Not used by any current consumer.
- `Log<TLogGroup>.{Trace,Debug,Info,Warn,Error,Fatal}(...)` -- ~40 overloads covering combinations of `(TLogGroup, Exception, string template, object[] values)`.
- `Log<TLogGroup>.{logLevel, stackTraceLevel, enabledLogGroups}` -- mutable static gates. Defaults: `Info`, `Warn`, all-bits-set. Consumers reconfigure at boot; external consumers may rebind them at runtime against remote config.
- `Log<TLogGroup>.LoggerFactory : ILoggerFactory` -- adapter so libraries that take `Microsoft.Extensions.Logging.ILogger` flow through the same pipeline.
- `LogGroupColorAttribute(hexColor)` -- placed on each consumer enum member; the Unity console sink reads it via reflection to color `[group]` preludes.
- `InnerFramesHiddenFromStackTraceAttribute` -- placed on `Log<>.*` overloads and the internal Unity-log shim; the Enricher trims everything up to and including the last attribute-marked frame so the captured stack starts at the actual caller.

### Pipeline at runtime

`Logger<TLogGroup>.Initialize` builds one Serilog logger per app (per closed generic type):

    LoggerConfiguration()
        .MinimumLevel.Verbose()
        .Enrich.With<Enricher<TLogGroup>>()
        .WriteTo.Unity<TLogGroup>()       <-- UnityDebugSink: colored Unity-console output
        .WriteTo.Sink(_lokiSink)          <-- LokiSink: queue -> drain loop -> Loki HTTP push
        .CreateLogger();

Then the reverse direction is hooked so *anything* logging reaches Serilog:

- `Debug.unityLogger.logHandler` is replaced with a `SerilogLogHandler` (captures `Debug.Log/Warning/Error` and native plugin emissions that go through `ILogHandler`).
- `Application.logMessageReceived` is subscribed via R3 (catches emissions that skip `logHandler`, e.g. native crash text).
- `UniTaskScheduler.UnobservedTaskException`, `TaskScheduler.UnobservedTaskException`, and `R3.ObservableSystem.RegisterUnhandledExceptionHandler` all route into `Log<TLogGroup>.Error`.
- `Application.SetStackTraceLogType(..., None)` is called for every Unity log type -- Unity's built-in stack-trace capture is disabled because the Serilog Enricher captures a richer one.

The Unity sink and the reverse hook would naively form a loop (Serilog -> UnityDebugSink -> `Debug.logHandler` -> `SerilogLogHandler` -> Serilog). `[ThreadStatic] internal static bool emittingToUnity` is set by the UnityDebugSink immediately before calling the saved-off `defaultUnityLogHandler`, and the reverse hook early-returns when it's true (`Runtime/Logger.cs:81-88, 141`).

### LokiSink

The Loki sink is the only non-mechanical piece. `Emit` is callable from the moment `Initialize` returns; it serializes the event to a one-line JSON document and appends it to a `LinkedList<(ts, line)>` guarded by `_queueLock`. Events that arrive before `EnableLoki` accumulate so a successful first drain ships everything captured during boot and pre-login.

When `EnableLoki(apiUrl, tokenProvider, handler)` fires, the sink:

1. Constructs an `HttpClient` over the caller-supplied handler (or `new HttpClientHandler()`).
2. Sets `_pushUrl = {apiUrl}/loki/api/v1/push`.
3. Starts one `UniTask.RunOnThreadPool(DrainLoop)`.

The drain loop, each iteration:

1. Sleeps `SleepDuration` from the `ExponentialBackoff` schedule (initially `Zero`, so the first iteration runs immediately).
2. Snapshots `_pending` under the lock. If empty, `OnIdle` -> 2s sleep -> continue.
3. If `_tokenProvider` is non-null, awaits it under a 15s `CancellationTokenSource` so a hung token fetch can't wedge the loop, and attaches the returned string as `Authorization: Bearer …`. A null provider skips both the await and the header -- the POST goes out unauthenticated, relying on the gateway to drop its forward_auth in `AUTH_MODE=disabled`.
4. POSTs `{streams: [{stream: <labels>, values: [[ts, line], ...]}]}` under the same cancellation token.
5. On 2xx: pops `batch.Length` entries from the head -- events that arrived during the in-flight POST stay at the tail and ship next drain. `OnSuccess` resets backoff.
6. On non-2xx: SelfLog + `OnFailure` (sleeps current backoff, doubles up to 60s).
7. On exception: if `_disposed`, exit silently -- that's the shutdown path. Else SelfLog + `OnFailure`.

Sink-internal failures route through `Serilog.Debugging.SelfLog.WriteLine` (which the Logger wires to write through the saved-off `defaultUnityLogHandler`), so a failing drain does not recursively re-enqueue its own diagnostics.

Timestamp encoding: `(logEvent.Timestamp.UtcDateTime.Ticks - UnixEpochTicks) * 100` -- .NET ticks are 100ns, Loki wants a nanosecond integer string. JSON formatting is `Formatting.None` because LogQL `|=` / `|~` line filters operate per line and won't match across embedded newlines.

Property serialization in `Emit`: it filters any caller-supplied `"level"` so the canonical Grafana-flavored level (`trace/debug/info/warning/error/critical`) wins, then orders keys with a hand-picked weighting (`level`, `logGroup`, `messageTemplate`, `message`, then everything else, then `stackTrace`, `exception` last). The order is pure UX for the Grafana viewer -- these become the visible "columns" in a log row. Fatal becomes `critical` because Grafana has no native `fatal`.

### Enricher

`Enricher<TLogGroup>.Enrich` adds, on every event:

- `exception` (`DictionaryValue`) -- structured exception with `type`, `message`, `stackTrace`, `innerException` / `innerExceptions`. Special-case `UnityEngine.AndroidJavaException`: reflects the private `mJavaStackTrace` field and adds it as `javaStackTrace` (`Runtime/Enricher.cs:78-84`). JNI exceptions surface their Java frames alongside .NET ones -- `new StackTrace(true)` only sees the .NET side.
- `messageTemplate` -- the unrendered Serilog template.
- `message` -- the rendered string.
- `deviceName` -- `SystemInfo.deviceName` captured at `Initialize` time.
- `stackTrace` (`SequenceValue`) -- structured frames, only if event level >= `Log<>.stackTraceLevel`. Frames marked `[InnerFramesHiddenFromStackTrace]` are skipped -- the captured stack starts at the actual caller. File paths under `Application.dataPath` are made project-relative. `BuildMethodName` reverse-engineers anonymous-lambda (`<EnclosingMethod>b__N_M`) and async-state-machine (`<Method>d__N`) names into readable `Type.Method+[Anonymous_M]` / `Type.Method+[AsyncStateMachine].MoveNext` strings.
- `properties` (`SequenceValue`) -- only for template tokens with a format specifier (e.g. `{Timestamp:O}`): captures the rendered formatted strings as a pre-rendered list.

### Consumer integration

The in-repo consumer boots at `[RuntimeInitializeOnLoadMethod(BeforeSceneLoad)]` with static labels (`apps/CaptureTool/Assets/Scripts/Capture/App.cs:32`), then calls `EnableLoki` after its Keycloak login completes (`apps/CaptureTool/Assets/AuthManager.cs:53`). Loki labels are static -- every event from one app collapses into one Loki stream. High-cardinality fields (device name, log group, exception) live inside the JSON line, not in the label set.

The gateway (`docker/SPEC.md` "Authentication") fronts `/loki/` and, in `AUTH_MODE=keycloak`, forwards to Loki using the client's existing Keycloak token -- there is no separate Loki ingress and no Loki-specific credential. In `AUTH_MODE=disabled`, the gateway drops the forward_auth directive and the client is expected to pass `tokenProvider: null` so the push goes out without an `Authorization` header. The Loki `service_name` label is auto-derived from the `app` label, so a query like `{service_name="capture-tool"}` works in either mode.

## Constraints

The non-obvious pieces of this package fall out of three constraints: (a) Unity is a single-process world where third-party plugins, native code, and async exceptions all need to land in the same log pipeline, (b) Loki labels are a hard cardinality budget, (c) the consumer can't authenticate Loki pushes until *after* it has done its own login dance.

**One Serilog logger per closed generic type, gated externally.** `Log<TLogGroup>.LogEnabled` does the level + flag-group gate *before* the event reaches Serilog; the Serilog config itself is `MinimumLevel.Verbose`. The package owns gating because the bitflag-group check needs the consumer's enum type, which Serilog doesn't know about. A side effect: every captured event always pays the enricher cost (stack-trace capture on `Warn+`, exception structure capture always). Cheap relative to a Loki POST; visible relative to a `Debug.Log`.

**Reverse-hook everything.** Unity's `Debug.unityLogger.logHandler`, `Application.logMessageReceived`, `UniTaskScheduler.UnobservedTaskException`, `TaskScheduler.UnobservedTaskException`, and `R3.ObservableSystem.RegisterUnhandledExceptionHandler` are all hooked at init. Five hook points because there are five distinct paths by which a third-party crash, async fault, or subscription bug can emit a log message that isn't a direct `Log<>.X` call. Without all five hooks, a class of crashes never reaches Loki. The `[ThreadStatic] emittingToUnity` guard exists *only* to break the cycle the Unity sink creates when the reverse hook is installed.

**In-memory queue + thread-pool drain instead of the upstream `Serilog.Sinks.Grafana.Loki` NuGet.** The replacement (commit `36db199d`) buys three things: (1) events emitted before `EnableLoki` queue rather than drop, so boot-time errors aren't lost when login fails; (2) a per-attempt 15s timeout that wraps both the token fetch and the HTTP send, so a hung token provider can't wedge the drain; (3) one less HTTP/handler abstraction crossing Unity's IL2CPP boundary. The cost is a bespoke implementation with no tests.

**`tokenProvider` is called every drain cycle, not just on 401.** The package takes on faith that the consumer's auth helper caches and only refreshes when the cached token is near-expiry. Placeframe's `Auth.GetOrRefreshToken` does. A consumer with a naive provider that round-trips to Keycloak per call would cap the Loki drain rate at one POST per token roundtrip. A `null` provider short-circuits the per-cycle await entirely -- the unauthenticated-push path is cheaper, not more expensive.

**JSON over Protobuf.** Loki accepts both. JSON keeps the implementation grep-able and avoids dragging a Protobuf dep across the IL2CPP boundary. The drain loop POSTs one stream per batch with `Content-Type: application/json` to `/loki/api/v1/push`.

**Sort order in the JSON line.** `level`, `logGroup`, `messageTemplate`, `message`, then everything else, then `stackTrace`, `exception` last. Pure UX for the Grafana viewer -- these become the visible columns of a log row. Fatal becomes `critical` because Grafana has no native `fatal`.

**`new StackTrace(true)` + `InnerFramesHiddenFromStackTrace` trimming over Unity's `StackTraceLogType.ScriptOnly`.** Unity's built-in capture is per-LogType and produces unstructured text; the Enricher's structured frame list survives JSON serialization, supports `[InnerFramesHiddenFromStackTrace]` to trim the logging shim itself out of every captured stack, and reads `mJavaStackTrace` out of `AndroidJavaException` so JNI exceptions surface their Java side. `Application.SetStackTraceLogType(..., None)` is set for every Unity LogType to suppress the duplicate built-in capture.

## See also

- `docker/SPEC.md` -- the gateway's `/loki/` passthrough and the `service_name` label conventions for Loki queries; this package is the client side of that contract.
