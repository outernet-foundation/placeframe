using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
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
    // In-memory Loki sink. Emit serializes the event to an indented JSON
    // line and appends it to a queue; the drainer (started by Enable once
    // auth lands) snapshots the queue, POSTs to Loki, and dequeues the
    // snapshot prefix on success. The queue accumulates events emitted
    // before Enable so pre-auth logs are flushed on the first successful
    // drain. A per-attempt HTTP timeout prevents a hung send from wedging
    // the loop, and exponential backoff paces retries on transient
    // transport faults. Drain failures route through Serilog's SelfLog so
    // a failing drain doesn't recursively re-enqueue its own diagnostics.
    internal sealed class LokiSink : ILogEventSink, IDisposable
    {
        private static readonly long UnixEpochTicks = new DateTime(1970, 1, 1, 0, 0, 0, DateTimeKind.Utc).Ticks;

        private static readonly TimeSpan IdleSleep = TimeSpan.FromSeconds(2);
        private static readonly TimeSpan InitialBackoff = TimeSpan.FromSeconds(1);
        private static readonly TimeSpan MaxBackoff = TimeSpan.FromSeconds(60);
        private static readonly TimeSpan PerAttemptTimeout = TimeSpan.FromSeconds(15);

        private readonly Dictionary<string, string> _labels;
        private readonly object _queueLock = new();
        private readonly LinkedList<(string ts, string line)> _pending = new();
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

        public void Enable(string domain, Func<UniTask<string>> tokenProvider, HttpMessageHandler handler)
        {
            if (_disposed)
                throw new ObjectDisposedException(nameof(LokiSink));
            if (_httpClient != null)
                throw new InvalidOperationException("Enable has already been called");

            _httpClient = new HttpClient(handler ?? new HttpClientHandler());
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
                // Inject Grafana-style level (Fatal→"critical" because Grafana has
                // no native "fatal"). Filter any caller-supplied "level" property
                // first so the canonical level wins and ToDictionary doesn't throw
                // on a duplicate key. Compact JSON because LogQL line filters
                // (`|=`, `|~`) operate per line and won't match across embedded
                // newlines.
                lock (_queueLock)
                {
                    _pending.AddLast(
                        (
                            ((logEvent.Timestamp.UtcDateTime.Ticks - UnixEpochTicks) * 100).ToString(CultureInfo.InvariantCulture),
                            JsonConvert.SerializeObject(
                                logEvent
                                    .Properties.Where(property => property.Key != "level")
                                    .Append(
                                        new KeyValuePair<string, LogEventPropertyValue>(
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
                                        )
                                    )
                                    .OrderBy(property =>
                                        property.Key switch
                                        {
                                            "level" => 1,
                                            "logGroup" => 2,
                                            "messageTemplate" => 3,
                                            "message" => 4,
                                            "stackTrace" => 6,
                                            "exception" => 7,
                                            _ => 5,
                                        }
                                    )
                                    .ToDictionary(property => property.Key, property => Json.FromSerilogProperty(property.Key, property.Value, false)),
                                Formatting.None
                            )
                        )
                    );
                }
            }
            catch (Exception exception)
            {
                Serilog.Debugging.SelfLog.WriteLine($"LokiSink emit failed: {exception}");
            }
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

                    (string ts, string line)[] batch;
                    lock (_queueLock)
                    {
                        if (_pending.Count == 0)
                        {
                            schedule.OnIdle();
                            continue;
                        }
                        batch = _pending.ToArray();
                    }

                    // Per-attempt timeout so a hung token fetch or HTTP send can't
                    // wedge the drain.
                    using var timeout = new CancellationTokenSource(PerAttemptTimeout);
                    var token = await _tokenProvider().AttachExternalCancellation(timeout.Token);

                    using var request = new HttpRequestMessage(HttpMethod.Post, _pushUrl);
                    request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
                    request.Content = new StringContent(
                        JsonConvert.SerializeObject(
                            new { streams = new[] { new { stream = _labels, values = batch.Select(entry => new[] { entry.ts, entry.line }) } } }
                        ),
                        Encoding.UTF8,
                        "application/json"
                    );

                    using var response = await _httpClient.SendAsync(request, timeout.Token);
                    if (!response.IsSuccessStatusCode)
                    {
                        Serilog.Debugging.SelfLog.WriteLine($"LokiSink POST returned {(int)response.StatusCode} {response.ReasonPhrase}");
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
    }
}
