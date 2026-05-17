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
    // In-memory Loki sink. Emit serializes the event to a JSON line and
    // appends to the queue tail, except when the new event's fingerprint
    // (level, template, exception type, stack-trace head) matches the tail —
    // then the tail entry is collapsed in place with repeated/firstAt/lastAt
    // fields, so duplicate spam (e.g. a 60 Hz exception loop) caps at one
    // entry per run. The drainer takes a bounded head slice (MaxBatchEvents
    // / MaxBatchBytes), POSTs to Loki, dequeues on success. Pre-Enable
    // events accumulate for first-drain flush. Per-attempt HTTP timeout.
    // 429 honors Retry-After; other faults use exponential backoff. Drain
    // failures route through SelfLog to avoid recursive re-enqueue.
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

        private readonly Dictionary<string, string> _labels;
        private readonly object _queueLock = new();
        private readonly LinkedList<PendingEntry> _pending = new();
        private volatile bool _disposed;

        private HttpClient _httpClient;
        private string _pushUrl;
        private Func<UniTask<string>> _tokenProvider;

        public LokiSink(IEnumerable<(string key, string value)> labels)
        {
            _labels = labels.ToDictionary(label => label.key, label => label.value);
        }

        public void Dispose()
        {
            _disposed = true;
            _httpClient?.Dispose();
        }

        public void Enable(string domain, Func<UniTask<string>> tokenProvider)
        {
            if (_disposed)
                throw new ObjectDisposedException(nameof(LokiSink));
            if (_httpClient != null)
                throw new InvalidOperationException("Enable has already been called");

            _httpClient = new HttpClient(new HttpClientHandler());
            _pushUrl = $"https://{domain}/loki/api/v1/push";
            _tokenProvider = tokenProvider;

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
                        tail.Line = SerializeLine(logEvent, tail.RepeatCount, tail.FirstTs, tail.LastTs);
                    }
                    else
                    {
                        _pending.AddLast(new PendingEntry
                        {
                            FirstTs = ts,
                            LastTs = ts,
                            Fingerprint = fingerprint,
                            RepeatCount = 1,
                            Line = SerializeLine(logEvent, 1, ts, ts),
                        });
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

                    // Per-attempt timeout so a hung token fetch or HTTP send can't
                    // wedge the drain.
                    using var timeout = new CancellationTokenSource(PerAttemptTimeout);
                    var token = await _tokenProvider().AttachExternalCancellation(timeout.Token);

                    using var request = new HttpRequestMessage(HttpMethod.Post, _pushUrl);
                    request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
                    request.Content = new StringContent(
                        JsonConvert.SerializeObject(
                            new { streams = new[] { new { stream = _labels, values = batch.Select(entry => new[] { entry.LastTs, entry.Line }) } } }
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
