using System;
using System.Threading;
using Cysharp.Threading.Tasks;

#if !UNITY_EDITOR && UNITY_ANDROID
using System.Collections.Generic;
using System.Globalization;
using System.Net.Http;
using System.Text;
using FofX;
using Newtonsoft.Json;
using ObserveThing;
using Placeframe.Client;
using Placeframe.Core;
#endif

// Lives outside ZedCaptureController to keep zedStatus out of scope.
// Conditioning the drain on AOA reachability would cancel the loop on cable
// flaps and reset the cursor on recovery, discarding exactly the failure-window
// logs needed to debug AOA cold-starts.
public static class LogDrainController
{
#if UNITY_EDITOR || !UNITY_ANDROID

    private static bool initialized;

    public static void Initialize()
    {
        if (initialized)
            throw new InvalidOperationException("LogDrainController.Initialize already called");
        initialized = true;
    }

    public static void Shutdown()
    {
        initialized = false;
    }

#else

    private const int logDrainBatchLimit = 500;
    private const float logDrainIdlePollIntervalSeconds = 5f;
    private static readonly TimeSpan logDrainMaxLookback = TimeSpan.FromHours(1);

    // LogQL matcher selecting every stream box-Alloy writes to box-Loki. The
    // OTLP pipeline maps each container's `service.name` resource attribute to
    // the `service_name` label, so this matches all box containers without an
    // explicit allowlist.
    private const string boxLokiQuery = "{service_name=~\".+\"}";
    private const string boxLokiQueryPath = "/loki/api/v1/query_range";
    private const string boxLokiBuildInfoPath = "/loki/api/v1/status/buildinfo";
    private const string hostLokiPushPath = "/loki/api/v1/push";

    private static HttpClient boxHttpClient;
    private static HttpClient hostLokiHttpClient;
    private static long logDrainCursorNs;
    private static bool logDrainCursorInitialized;
    private static TaskHandle logDrainTask = TaskHandle.Complete;
    private static IDisposable subscription;

    private sealed class LokiQueryResponse
    {
        [JsonProperty("data")] public LokiQueryData Data { get; set; }
    }

    private sealed class LokiQueryData
    {
        [JsonProperty("result")] public List<LokiStream> Result { get; set; }
    }

    private sealed class LokiStream
    {
        [JsonProperty("stream")] public Dictionary<string, string> Stream { get; set; }
        [JsonProperty("values")] public List<List<string>> Values { get; set; }
    }

    public static void Initialize()
    {
        if (boxHttpClient != null)
            throw new InvalidOperationException("LogDrainController.Initialize already called");

        boxHttpClient = ZedCaptureController.AoaHttpClient;

        // TODO(ObserveThing): explicit lambda parameter type is a workaround for an
        // overload-resolution gap. StateValue<T> implements both IValueObservable<T>
        // and IObservable<IStateOperation> (via IStateNode), so Observables.Subscribe
        // matches two extension overloads. When the lambda body discards the value
        // with `_`, the call is ambiguous (CS0121). The fix belongs upstream in
        // ObserveThing — either by collapsing the dual interface or by adding a
        // Subscribe overload on IStateNode that wins resolution.
        subscription = App.state.loggedIn.Subscribe((bool _) => EvaluateState());
    }

    public static void Shutdown()
    {
        logDrainTask.Cancel();
        subscription?.Dispose();
        subscription = null;
        boxHttpClient = null;
        hostLokiHttpClient?.Dispose();
        hostLokiHttpClient = null;
        logDrainCursorInitialized = false;
    }

    private static void EvaluateState()
    {
        logDrainTask.Cancel();

        if (!App.state.loggedIn.value)
            return;

        // Built here, not in Initialize, because the backend auth handler reads the AuthMode and
        // (under keycloak) the token minted by login — neither exists until we are logged in.
        hostLokiHttpClient?.Dispose();
        hostLokiHttpClient = new HttpClient(VisualPositioningSystem.CreateBackendAuthHandler(App.state.serverInfo.value));

        logDrainTask = TaskHandle.Execute(LogDrainLoop);
    }

    private static async UniTask LogDrainLoop(CancellationToken cancellationToken)
    {
        try
        {
            while (!cancellationToken.IsCancellationRequested)
            {
                bool hasMore = false;
                try
                {
                    hasMore = await LogDrainOnce(cancellationToken);
                }
                catch (Exception exception) when (!cancellationToken.IsCancellationRequested)
                {
                    Log.Info(LogGroup.Zed, exception, "log drain tick failed");
                }

                if (!hasMore)
                    await UniTask.WaitForSeconds(logDrainIdlePollIntervalSeconds, cancellationToken: cancellationToken);
            }
        }
        catch (OperationCanceledException) when (cancellationToken.IsCancellationRequested) { }
    }

    private static async UniTask<bool> LogDrainOnce(CancellationToken cancellationToken)
    {
        // box-Loki stamps entries with the box clock (boots at 1970, no RTC), so the window
        // below is box time, not phone time. Read the box clock from buildinfo's Date header —
        // it takes no time params, so it is safe at any clock (a windowed query misparses a 1970
        // clock into a 30d-limit rejection). Entries are converted back to phone time only at push.
        long boxNowNs;
        string clockUrl = new Uri(boxHttpClient.BaseAddress, boxLokiBuildInfoPath).ToString();
        using (var clockRequest = new HttpRequestMessage(HttpMethod.Get, clockUrl))
        using (var clockResponse = await boxHttpClient.SendAsync(clockRequest, cancellationToken))
        {
            clockResponse.EnsureSuccessStatusCode();
            DateTimeOffset boxNow =
                clockResponse.Headers.Date
                ?? throw new InvalidOperationException("box response missing Date header; cannot anchor drain to box clock");
            boxNowNs = ToUnixNanos(boxNow.UtcDateTime);
        }

        long restampOffsetNs = ToUnixNanos(DateTime.UtcNow) - boxNowNs;

        if (!logDrainCursorInitialized)
        {
            logDrainCursorNs = boxNowNs;
            logDrainCursorInitialized = true;
        }
        else
        {
            long maxLookbackNs = boxNowNs - logDrainMaxLookback.Ticks * 100;
            if (logDrainCursorNs < maxLookbackNs)
                logDrainCursorNs = maxLookbackNs;
        }

        long startNs = logDrainCursorNs;
        long endNs = boxNowNs;
        if (endNs <= startNs)
            return false;

        // Query box-Loki via box-Caddy over the AOA pipe, in box time. start/end go as RFC3339Nano,
        // not integer nanoseconds: Loki reads a small integer (a near-epoch 1970 boot clock) as
        // seconds, inflating the window past its 30-day max and rejecting the query with 400.
        string queryUrl = new Uri(boxHttpClient.BaseAddress, boxLokiQueryPath)
            + $"?query={Uri.EscapeDataString(boxLokiQuery)}"
            + $"&start={Uri.EscapeDataString(ToRfc3339Nano(startNs))}"
            + $"&end={Uri.EscapeDataString(ToRfc3339Nano(endNs))}"
            + $"&limit={logDrainBatchLimit}&direction=forward";

        LokiQueryResponse parsed;
        using (var queryRequest = new HttpRequestMessage(HttpMethod.Get, queryUrl))
        using (var queryResponse = await boxHttpClient.SendAsync(queryRequest, cancellationToken))
        {
            queryResponse.EnsureSuccessStatusCode();
            string queryBody = await queryResponse.Content.ReadAsStringAsync();
            parsed = JsonConvert.DeserializeObject<LokiQueryResponse>(queryBody);
        }

        var streams = parsed?.Data?.Result;
        if (streams == null || streams.Count == 0)
            return false;

        long maxNs = startNs;
        int entryCount = 0;
        foreach (var stream in streams)
        {
            if (stream.Values == null)
                continue;
            foreach (var pair in stream.Values)
            {
                if (pair.Count < 2)
                    continue;
                if (long.TryParse(pair[0], out long timestampNs))
                {
                    // Cursor stays in box time (it queries box-Loki); only the pushed copy is restamped.
                    if (timestampNs > maxNs)
                        maxNs = timestampNs;
                    pair[0] = (timestampNs + restampOffsetNs).ToString(CultureInfo.InvariantCulture);
                }

                entryCount++;
            }
        }

        if (entryCount == 0)
            return false;

        // Push to host-Loki through host-Caddy. Timestamps are restamped to phone time above;
        // labels are untouched. hostLokiHttpClient carries the backend auth policy in its handler.
        string apiUrl = App.state.settings.apiUrl.value;
        string pushUrl = $"{apiUrl}{hostLokiPushPath}";
        string pushBody = JsonConvert.SerializeObject(new { streams });

        using (var pushRequest = new HttpRequestMessage(HttpMethod.Post, pushUrl))
        {
            pushRequest.Content = new StringContent(pushBody, Encoding.UTF8, "application/json");
            using var pushResponse = await hostLokiHttpClient.SendAsync(pushRequest, cancellationToken);
            pushResponse.EnsureSuccessStatusCode();
        }

        // +1 so the next query starts strictly after the latest entry we saw.
        logDrainCursorNs = maxNs + 1;
        return entryCount >= logDrainBatchLimit;
    }

    private static readonly long unixEpochTicks = new DateTime(1970, 1, 1, 0, 0, 0, DateTimeKind.Utc).Ticks;

    private static long ToUnixNanos(DateTime utc) => (utc.Ticks - unixEpochTicks) * 100;

    private static string ToRfc3339Nano(long unixNanos)
    {
        long seconds = unixNanos / 1_000_000_000L;
        long nanos = unixNanos % 1_000_000_000L;
        DateTime utc = DateTimeOffset.FromUnixTimeSeconds(seconds).UtcDateTime;
        return utc.ToString("yyyy-MM-ddTHH:mm:ss", CultureInfo.InvariantCulture)
            + "."
            + nanos.ToString("D9", CultureInfo.InvariantCulture)
            + "Z";
    }
#endif
}
