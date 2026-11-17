using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text;
using System.Threading;
using Cysharp.Threading.Tasks;
using Newtonsoft.Json;
using Serilog.Core;
using Serilog.Events;

namespace Outernet.Logging
{
    // In-memory Loki sink. Emit serializes the event to a JSON line and
    // appends to the queue tail, keyed by fingerprint (level, template,
    // exception type, stack-trace head) — when an incoming event's
    // fingerprint matches any entry still in the queue, that entry is
    // collapsed in place with repeated/firstAt/lastAt fields, so duplicate
    // spam (e.g. a per-tick failure loop) ships as one entry with a count
    // no matter what else interleaves between occurrences. The drainer
    // takes a bounded head slice (MaxBatchEvents / MaxBatchBytes), gzips
    // it, and POSTs to Loki with Content-Encoding: gzip; entries dequeue
    // only on success. Pre-Enable events accumulate for first-drain flush.
    // Per-attempt HTTP timeout. 429 honors Retry-After; other faults use
    // exponential backoff.
    //
    // Drain faults report through the injected SinkFaultReporter at a level
    // that tracks cause: transport faults and 429 are Info per occurrence,
    // one Warn once failures run SustainedFailureThreshold consecutive,
    // one Info on recovery after a sustained run; 5xx and other non-success
    // responses are Error (our service broken or our request malformed);
    // unexpected exceptions are Error. The reporter routes into the Serilog
    // pipeline, so fault records queue and ship once the drain recovers —
    // fingerprint dedup bounds that self-referential queue growth to one
    // entry. Emit failures stay on SelfLog: reporting them through the
    // pipeline recurses (Emit → report → Emit), and they are serialization
    // bugs, which the SelfLog → console LogType.Error wiring reports at
    // the right level.
    //
    // Bespoke rather than the upstream Serilog.Sinks.Grafana.Loki NuGet for
    // three reasons: events emitted before Enable queue rather than drop, so
    // boot-time and pre-login errors survive a failed login; the per-attempt
    // timeout wraps the whole send, so a hung auth handler (token mint/refresh
    // runs inside SendAsync on the injected HttpMessageHandler) can't wedge the
    // drain; and it removes one HTTP/handler abstraction from crossing Unity's
    // IL2CPP boundary. Auth is entirely the injected handler's job — this sink
    // never sees a token.
    //
    // Payload is JSON, not Protobuf (Loki accepts both): JSON keeps the sink
    // grep-able and avoids dragging a Protobuf dependency across IL2CPP.
    //
    // SerializeLine orders keys level, logGroup, messageTemplate, message, then
    // everything else, then stackTrace and exception last. Pure UX — these are
    // the visible columns of a Grafana log row. Fatal maps to "critical"
    // because Grafana has no native "fatal" level.
    internal delegate void SinkFaultReporter(LogLevel level, Exception exception, string messageTemplate, params object[] propertyValues);

    internal sealed class LokiSink : ILogEventSink, IDisposable
    {
        private static readonly long UnixEpochTicks = new DateTime(1970, 1, 1, 0, 0, 0, DateTimeKind.Utc).Ticks;

        private static readonly TimeSpan IdleSleep = TimeSpan.FromSeconds(2);
        private static readonly TimeSpan InitialBackoff = TimeSpan.FromSeconds(1);
        private static readonly TimeSpan MaxBackoff = TimeSpan.FromSeconds(60);
        private static readonly TimeSpan PerAttemptTimeout = TimeSpan.FromSeconds(15);

        // Sized to stay well under Loki's default per-tenant 6 MB ingestion
        // burst. The byte cap bounds the uncompressed slice; gzip typically
        // shrinks it ~10x on the wire, keeping pushes small enough that a
        // slow uplink finishes them well inside PerAttemptTimeout.
        private const int MaxBatchEvents = 500;
        private const int MaxBatchBytes = 128 * 1024;
        private const int SustainedFailureThreshold = 4;

        private readonly Dictionary<string, string> _labels;
        private readonly SinkFaultReporter _reportFault;
        private readonly object _queueLock = new();
        private readonly LinkedList<PendingEntry> _pending = new();
        private readonly Dictionary<string, LinkedListNode<PendingEntry>> _pendingByFingerprint = new();
        private int _consecutiveFailures;
        private bool _sustainedReported;
        private volatile bool _disposed;

        private HttpClient _httpClient;
        private string _pushUrl;

        public LokiSink(IEnumerable<(string key, string value)> labels, SinkFaultReporter reportFault)
        {
            _labels = labels.ToDictionary(label => label.key, label => label.value);
            _reportFault = reportFault;
        }

        public void Dispose()
        {
            _disposed = true;
            _httpClient?.Dispose();
        }

        public void Enable(string apiUrl, HttpMessageHandler authHandler)
        {
            if (_disposed)
                throw new ObjectDisposedException(nameof(LokiSink));
            if (_httpClient != null)
                throw new InvalidOperationException("Enable has already been called");
            if (!Uri.TryCreate(apiUrl, UriKind.Absolute, out var baseUri))
                throw new ArgumentException($"apiUrl must be an absolute URI, got: '{apiUrl ?? "<null>"}'", nameof(apiUrl));

            _httpClient = new HttpClient(authHandler ?? new HttpClientHandler());
            _pushUrl = new Uri(baseUri, "/loki/api/v1/push").AbsoluteUri;

            UniTask.RunOnThreadPool(DrainLoop).Forget();
        }

        public void Emit(LogEvent logEvent)
        {
            if (_disposed)
                return;
            try
            {
                // .NET ticks are 100 ns; Loki wants a nanosecond integer, hence *100.
                var ts = ((logEvent.Timestamp.UtcDateTime.Ticks - UnixEpochTicks) * 100).ToString(CultureInfo.InvariantCulture);
                var fingerprint = ComputeFingerprint(logEvent);

                lock (_queueLock)
                {
                    if (_pendingByFingerprint.TryGetValue(fingerprint, out var node))
                    {
                        var tail = node.Value;
                        tail.RepeatCount += 1;
                        tail.LastTs = ts;
                        tail.Line = SerializeLine(logEvent, tail.RepeatCount, tail.FirstTs, tail.LastTs);
                    }
                    else
                    {
                        var entry = new PendingEntry
                        {
                            FirstTs = ts,
                            LastTs = ts,
                            Fingerprint = fingerprint,
                            RepeatCount = 1,
                            Line = SerializeLine(logEvent, 1, ts, ts),
                        };
                        _pendingByFingerprint[fingerprint] = _pending.AddLast(entry);
                    }
                }
            }
            catch (Exception exception)
            {
                Serilog.Debugging.SelfLog.WriteLine($"LokiSink emit failed: {exception}");
            }
        }

        // Stack-trace head distinguishes call sites that share a template.
        private static string ComputeFingerprint(LogEvent logEvent)
        {
            var exceptionType = logEvent.Exception?.GetType().FullName ?? "";
            var stackHead = "";
            if (logEvent.Exception?.StackTrace is string stack)
            {
                var newline = stack.IndexOf('\n');
                stackHead = newline >= 0 ? stack.Substring(0, newline) : stack;
            }
            return $"{(int)logEvent.Level}|{logEvent.MessageTemplate.Text}|{exceptionType}|{stackHead}";
        }

        // Inject Grafana-style level (Fatal→"critical" because Grafana has
        // no native "fatal"). Filter caller-supplied "level" so the canonical
        // level wins ToDictionary. Compact JSON because LogQL line filters
        // operate per line.
        private static string SerializeLine(LogEvent logEvent, int repeatCount, string firstTs, string lastTs)
        {
            var properties = logEvent.Properties
                .Where(property => property.Key != "level")
                .Append(new KeyValuePair<string, LogEventPropertyValue>(
                    "level",
                    new ScalarValue(
                        logEvent.Level switch
                        {
                            LogEventLevel.Verbose => "trace",
                            LogEventLevel.Debug => "debug",
                            LogEventLevel.Information => "info",
                            LogEventLevel.Warning => "warning",
                            LogEventLevel.Error => "error",
                            LogEventLevel.Fatal => "critical",
                            _ => "unknown",
                        }
                    )
                ));

            if (repeatCount > 1)
            {
                properties = properties
                    .Append(new KeyValuePair<string, LogEventPropertyValue>("repeated", new ScalarValue(repeatCount)))
                    .Append(new KeyValuePair<string, LogEventPropertyValue>("firstAt", new ScalarValue(firstTs)))
                    .Append(new KeyValuePair<string, LogEventPropertyValue>("lastAt", new ScalarValue(lastTs)));
            }

            return JsonConvert.SerializeObject(
                properties
                    .OrderBy(property =>
                        property.Key switch
                        {
                            "level" => 1,
                            "logGroup" => 2,
                            "messageTemplate" => 3,
                            "message" => 4,
                            "repeated" => 5,
                            "firstAt" => 6,
                            "lastAt" => 7,
                            "stackTrace" => 9,
                            "exception" => 10,
                            _ => 8,
                        }
                    )
                    .ToDictionary(property => property.Key, property => Json.FromSerilogProperty(property.Key, property.Value, false)),
                Formatting.None
            );
        }

        private async UniTask DrainLoop()
        {
            var schedule = new ExponentialBackoff(InitialBackoff, IdleSleep, MaxBackoff);

            while (!_disposed)
            {
                try
                {
                    if (schedule.SleepDuration > TimeSpan.Zero)
                        await UniTask.Delay(schedule.SleepDuration);

                    PendingEntry[] batch;
                    lock (_queueLock)
                    {
                        if (_pending.Count == 0)
                        {
                            schedule.OnIdle();
                            continue;
                        }
                        batch = TakeHeadSlice();
                    }

                    // Per-attempt timeout so a hung HTTP send — including the auth handler's
                    // token mint/refresh — can't wedge the drain.
                    using var timeout = new CancellationTokenSource(PerAttemptTimeout);

                    using var request = new HttpRequestMessage(HttpMethod.Post, _pushUrl);
                    request.Content = CompressContent(
                        JsonConvert.SerializeObject(
                            new { streams = new[] { new { stream = _labels, values = batch.Select(entry => new[] { entry.LastTs, entry.Line }) } } }
                        )
                    );

                    using var response = await _httpClient.SendAsync(request, timeout.Token);
                    if (!response.IsSuccessStatusCode)
                    {
                        var statusCode = (int)response.StatusCode;
                        var reasonPhrase = response.ReasonPhrase;
                        if (response.StatusCode == HttpStatusCode.TooManyRequests)
                        {
                            ReportExogenousFault(null, "Loki push rejected with {StatusCode} {ReasonPhrase}", statusCode, reasonPhrase);
                            if (TryGetRetryAfter(response.Headers.RetryAfter, out var retryAfter))
                                schedule.OnRetryAfter(retryAfter);
                            else
                                schedule.OnFailure();
                        }
                        else
                        {
                            _reportFault(LogLevel.Error, null, "Loki push rejected with {StatusCode} {ReasonPhrase}", statusCode, reasonPhrase);
                            schedule.OnFailure();
                        }
                        continue;
                    }

                    lock (_queueLock)
                    {
                        for (int index = 0; index < batch.Length; index++)
                        {
                            _pendingByFingerprint.Remove(batch[index].Fingerprint);
                            _pending.RemoveFirst();
                        }
                    }
                    schedule.OnSuccess();
                    if (_sustainedReported)
                        _reportFault(LogLevel.Info, null, "Loki push recovered after {FailureCount} consecutive failures", _consecutiveFailures);
                    _consecutiveFailures = 0;
                    _sustainedReported = false;
                }
                catch (Exception exception)
                {
                    // A mid-flight SendAsync can throw ObjectDisposedException when
                    // Dispose() runs concurrently. That's an expected shutdown path,
                    // not an iteration fault — exit silently.
                    if (_disposed)
                        break;
                    if (IsTransportFault(exception))
                        ReportExogenousFault(exception, "Loki push failed");
                    else
                        _reportFault(LogLevel.Error, exception, "LokiSink drain loop faulted");
                    schedule.OnFailure();
                }
            }
        }

        private void ReportExogenousFault(Exception exception, string messageTemplate, params object[] propertyValues)
        {
            _consecutiveFailures += 1;
            if (_consecutiveFailures == SustainedFailureThreshold)
                _reportFault(LogLevel.Warn, exception, "Loki push fault sustained: {FailureCount} consecutive failures", _consecutiveFailures);
            else
                _reportFault(LogLevel.Info, exception, messageTemplate, propertyValues);
        }

        private static bool IsTransportFault(Exception exception)
        {
            return exception is HttpRequestException
                || exception is WebException
                || exception is OperationCanceledException;
        }

        private static bool TryGetRetryAfter(RetryConditionHeaderValue header, out TimeSpan delay)
        {
            if (header == null)
            {
                delay = default;
                return false;
            }
            if (header.Delta.HasValue)
            {
                delay = header.Delta.Value;
                return true;
            }
            if (header.Date.HasValue)
            {
                var diff = header.Date.Value - DateTimeOffset.UtcNow;
                delay = diff > TimeSpan.Zero ? diff : TimeSpan.Zero;
                return true;
            }
            delay = default;
            return false;
        }

    private static ByteArrayContent CompressContent(string json)
    {
        byte[] jsonBytes = Encoding.UTF8.GetBytes(json);
        byte[] compressedBytes;
        using (var outputStream = new MemoryStream())
        {
            using (var gzipStream = new GZipStream(outputStream, CompressionLevel.Fastest))
                gzipStream.Write(jsonBytes, 0, jsonBytes.Length);
            compressedBytes = outputStream.ToArray();
        }

        var content = new ByteArrayContent(compressedBytes);
        content.Headers.ContentType = new MediaTypeHeaderValue("application/json");
        content.Headers.ContentEncoding.Add("gzip");
        return content;
    }

    // Caller holds _queueLock. Always returns at least one entry so a
    // single oversized event can't wedge the drain.
    private PendingEntry[] TakeHeadSlice()
        {
            var slice = new List<PendingEntry>(Math.Min(_pending.Count, MaxBatchEvents));
            var totalBytes = 0;
            foreach (var entry in _pending)
            {
                var entryBytes = Encoding.UTF8.GetByteCount(entry.Line);
                if (slice.Count > 0 && (slice.Count >= MaxBatchEvents || totalBytes + entryBytes > MaxBatchBytes))
                    break;
                slice.Add(entry);
                totalBytes += entryBytes;
            }
            return slice.ToArray();
        }

        private sealed class PendingEntry
        {
            public string FirstTs;
            public string LastTs;
            public string Fingerprint;
            public int RepeatCount;
            public string Line;
        }
    }
}
