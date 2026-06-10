using System;
using System.Collections.Generic;
using System.Globalization;
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
    // In-memory Loki sink. Emit renders each event to a body line plus a flat
    // structured-metadata map (the canonical OTLP shape: body is the message,
    // everything else is structured metadata) and appends to the queue tail,
    // except when the new event's fingerprint (level, template, exception type,
    // stack-trace head) matches the tail — then the tail entry is collapsed in
    // place with repeated/firstAt/lastAt metadata, so duplicate spam (e.g. a
    // 60 Hz exception loop) caps at one entry per run. The drainer takes a
    // bounded head slice (MaxBatchEvents / MaxBatchBytes), POSTs to Loki's push
    // API as [ts, body, metadata] values, dequeues on success. Pre-Enable events
    // accumulate for first-drain flush. Per-attempt HTTP timeout. 429 honors
    // Retry-After; other faults use exponential backoff. Drain failures route
    // through SelfLog to avoid recursive re-enqueue.
    internal sealed class LokiSink : ILogEventSink, IDisposable
    {
        private static readonly long UnixEpochTicks = new DateTime(1970, 1, 1, 0, 0, 0, DateTimeKind.Utc).Ticks;

        private static readonly TimeSpan IdleSleep = TimeSpan.FromSeconds(2);
        private static readonly TimeSpan InitialBackoff = TimeSpan.FromSeconds(1);
        private static readonly TimeSpan MaxBackoff = TimeSpan.FromSeconds(60);
        private static readonly TimeSpan PerAttemptTimeout = TimeSpan.FromSeconds(15);

        // Sized to stay well under Loki's default per-tenant 6 MB ingestion burst.
        private const int MaxBatchEvents = 500;
        private const int MaxBatchBytes = 512 * 1024;

        // Only these incoming labels stay Loki stream labels; the rest (e.g. platform)
        // ride as structured metadata, matching the backend's low-cardinality label set.
        private static readonly HashSet<string> StreamLabelKeys = new() { "service_name", "deployment_environment_name" };

        private readonly Dictionary<string, string> _labels;
        private readonly Dictionary<string, string> _seedMetadata;
        private readonly object _queueLock = new();
        private readonly LinkedList<PendingEntry> _pending = new();
        private volatile bool _disposed;

        private HttpClient _httpClient;
        private string _pushUrl;

        public LokiSink(IEnumerable<(string key, string value)> labels)
        {
            _labels = new Dictionary<string, string>();
            _seedMetadata = new Dictionary<string, string>();
            foreach (var (key, value) in labels)
            {
                if (StreamLabelKeys.Contains(key))
                    _labels[key] = value;
                else
                    _seedMetadata[key] = value;
            }
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
                var ts = ((logEvent.Timestamp.UtcDateTime.Ticks - UnixEpochTicks) * 100).ToString(CultureInfo.InvariantCulture);
                var fingerprint = ComputeFingerprint(logEvent);

                lock (_queueLock)
                {
                    var tail = _pending.Last?.Value;
                    if (tail != null && tail.Fingerprint == fingerprint)
                    {
                        tail.RepeatCount += 1;
                        tail.LastTs = ts;
                        FillContent(tail, logEvent);
                    }
                    else
                    {
                        var entry = new PendingEntry
                        {
                            FirstTs = ts,
                            LastTs = ts,
                            Fingerprint = fingerprint,
                            RepeatCount = 1,
                        };
                        FillContent(entry, logEvent);
                        _pending.AddLast(entry);
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

        private void FillContent(PendingEntry entry, LogEvent logEvent)
        {
            var (body, metadata) = SerializeEvent(logEvent, entry.RepeatCount, entry.FirstTs, entry.LastTs);
            entry.Body = body;
            entry.Metadata = metadata;

            var size = Encoding.UTF8.GetByteCount(body);
            foreach (var pair in metadata)
                size += Encoding.UTF8.GetByteCount(pair.Key) + Encoding.UTF8.GetByteCount(pair.Value);
            entry.ByteSize = size;
        }

        // Build the canonical (body, structured-metadata) pair. body is the rendered
        // message; metadata is every other property flattened to string->string, seeded
        // with the non-label sink labels (e.g. platform). severity_text drives Loki's
        // detected_level (Fatal→"critical" since there is no native "fatal"). A collapsed
        // duplicate run is marked with repeated/firstAt/lastAt.
        private (string body, Dictionary<string, string> metadata) SerializeEvent(LogEvent logEvent, int repeatCount, string firstTs, string lastTs)
        {
            var metadata = new Dictionary<string, string>(_seedMetadata)
            {
                ["severity_text"] = logEvent.Level switch
                {
                    LogEventLevel.Verbose => "trace",
                    LogEventLevel.Debug => "debug",
                    LogEventLevel.Information => "info",
                    LogEventLevel.Warning => "warning",
                    LogEventLevel.Error => "error",
                    LogEventLevel.Fatal => "critical",
                    _ => "unknown",
                },
            };

            string body = null;
            foreach (var property in logEvent.Properties)
            {
                if (property.Key == "message")
                {
                    body = (property.Value as ScalarValue)?.Value as string;
                    continue;
                }

                if (property.Key == "level")
                    continue;

                Json.FlattenSerilogProperty(property.Key, property.Value, metadata);
            }

            if (string.IsNullOrEmpty(body))
                body = logEvent.MessageTemplate.Text;
            if (string.IsNullOrEmpty(body))
                body = "(empty)";

            if (repeatCount > 1)
            {
                metadata["repeated"] = repeatCount.ToString(CultureInfo.InvariantCulture);
                metadata["firstAt"] = firstTs;
                metadata["lastAt"] = lastTs;
            }

            return (body, metadata);
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
                    request.Content = new StringContent(
                        JsonConvert.SerializeObject(
                            new
                            {
                                streams = new[]
                                {
                                    new { stream = _labels, values = batch.Select(entry => new object[] { entry.LastTs, entry.Body, entry.Metadata }) },
                                },
                            }
                        ),
                        Encoding.UTF8,
                        "application/json"
                    );

                    using var response = await _httpClient.SendAsync(request, timeout.Token);
                    if (!response.IsSuccessStatusCode)
                    {
                        Serilog.Debugging.SelfLog.WriteLine($"LokiSink POST returned {(int)response.StatusCode} {response.ReasonPhrase}");
                        if (response.StatusCode == HttpStatusCode.TooManyRequests && TryGetRetryAfter(response.Headers.RetryAfter, out var retryAfter))
                            schedule.OnRetryAfter(retryAfter);
                        else
                            schedule.OnFailure();
                        continue;
                    }

                    lock (_queueLock)
                    {
                        for (int index = 0; index < batch.Length; index++)
                            _pending.RemoveFirst();
                    }
                    schedule.OnSuccess();
                }
                catch (Exception exception)
                {
                    // A mid-flight SendAsync can throw ObjectDisposedException when
                    // Dispose() runs concurrently. That's an expected shutdown path,
                    // not an iteration fault — exit silently.
                    if (_disposed)
                        break;
                    Serilog.Debugging.SelfLog.WriteLine($"LokiSink iteration faulted: {exception}");
                    schedule.OnFailure();
                }
            }
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

        // Caller holds _queueLock. Always returns at least one entry so a
        // single oversized event can't wedge the drain.
        private PendingEntry[] TakeHeadSlice()
        {
            var slice = new List<PendingEntry>(Math.Min(_pending.Count, MaxBatchEvents));
            var totalBytes = 0;
            foreach (var entry in _pending)
            {
                var entryBytes = entry.ByteSize;
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
            public string Body;
            public Dictionary<string, string> Metadata;
            public int ByteSize;
        }
    }
}
