using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading;
using Cysharp.Threading.Tasks;
using Placeframe.Client;
using Placeframe.Core;
using PlaceframeApiClient.Model;
using LogBatchModel = PlaceframeZedCaptureClient.Model.LogBatch;
using ZedStatusModel = PlaceframeZedCaptureClient.Model.ZedStatus;

#if !UNITY_EDITOR && UNITY_ANDROID
using System.Net.Http;
using FofX;
using FofX.Stateful;
using ObserveThing;
using Placeframe.Client;
using Placeframe.Core;
using PlaceframeApiClient.Model;
using PlaceframeZedCaptureClient.Api;
using PlaceframeZedCaptureClient.Client;
using DeviceType = PlaceframeApiClient.Model.DeviceType;
#endif

public static class ZedCaptureController
{
#if UNITY_EDITOR || !UNITY_ANDROID

    private const string unsupportedMessage = "ZedCaptureController is only supported on non-Editor Android builds";
    private static bool initialized;

    public static void Initialize()
    {
        if (initialized)
            throw new InvalidOperationException("ZedCaptureController.Initialize already called");
        initialized = true;
    }

    public static void Shutdown()
    {
        initialized = false;
    }

    public static UniTask StartCapture(float captureInterval, CancellationToken cancellationToken = default) =>
        throw new PlatformNotSupportedException(unsupportedMessage);

    public static UniTask StopCapture(CancellationToken cancellationToken = default) =>
        throw new PlatformNotSupportedException(unsupportedMessage);

    public static UniTask<IEnumerable<LocalCapture>> EnumerateCaptures() =>
        UniTask.FromResult(Enumerable.Empty<LocalCapture>());

    public static UniTask<Stream> GetCapture(Guid captureId, CancellationToken cancellationToken = default) =>
        throw new PlatformNotSupportedException(unsupportedMessage);

    public static UniTask DeleteCapture(Guid captureId, CancellationToken cancellationToken = default) =>
        throw new PlatformNotSupportedException(unsupportedMessage);

    public static UniTask<ZedStatusModel> GetStatus(CancellationToken cancellationToken = default) =>
        throw new PlatformNotSupportedException(unsupportedMessage);

    public static UniTask<LogBatchModel> GetLogs(string since, int limit, CancellationToken cancellationToken = default) =>
        throw new PlatformNotSupportedException(unsupportedMessage);

#else

    // The ZED is the USB host; the phone is a USB accessory speaking the
    // Android Open Accessory (AOA) protocol. The ZED-side aoa_bridge daemon
    // performs the AOA handshake and forwards the accessory's bulk endpoints
    // to localhost:9000 (the box-side aoa-gateway Caddy sidecar) as a
    // transparent byte pipe — so this client speaks HTTP/2 cleartext
    // (h2c, prior-knowledge) directly to the accessory FD with no TCP,
    // no IP, no Android ConnectivityService involvement. The hostname in
    // baseUrl is a placeholder for the Host header only; the request never
    // resolves anywhere. The Caddy sidecar terminates h2c and reverse-proxies
    // HTTP/1.1 to uvicorn on 127.0.0.1:9001 on the box.
    private const string baseUrl = "http://zed-box";
    private static readonly TimeSpan requestTimeout = TimeSpan.FromSeconds(600);

    private static DefaultApi capturesApi;
    private static IDisposable subscriptions;

    private const float healthPollIntervalSeconds = 0.5f;
    private const float healthRequestTimeoutSeconds = 2f;
    private const int healthUnreachableThreshold = 2;
    private const long healthDiskLowBytes = 1L * 1024L * 1024L * 1024L;
    private static TaskHandle healthPollTask = TaskHandle.Complete;

    private const int logDrainBatchLimit = 500;
    private const float logDrainIdlePollIntervalSeconds = 5f;
    private static string logDrainPendingAck = "";
    private static TaskHandle logDrainTask = TaskHandle.Complete;

    public static void Initialize()
    {
        if (capturesApi != null)
            throw new InvalidOperationException("ZedCaptureController.Initialize already called");

        capturesApi = new DefaultApi(
            new HttpClient(new ProgressTrackingHandler { InnerHandler = new AndroidAoaHttpHandler() })
            {
                BaseAddress = new Uri(baseUrl),
                Timeout = requestTimeout,
            },
            new Configuration { BasePath = baseUrl, Timeout = requestTimeout }
        );

        // TODO(ObserveThing): explicit lambda parameter types are a workaround for
        // an overload-resolution gap. StateValue<T> implements both IValueObservable<T>
        // and IObservable<IStateOperation> (via IStateNode), so Observables.Subscribe
        // matches two extension overloads. When the lambda body doesn't constrain the
        // parameter type (here it's discarded with `_`), the call is ambiguous (CS0121).
        // The fix belongs upstream in ObserveThing — either by collapsing the dual
        // interface or by adding a Subscribe overload on IStateNode that wins resolution.
        subscriptions = new ComposedDisposable(
            App.state.loggedIn.Subscribe((bool _) => EvaluateHealthPollState()),
            App.state.zedStatus.Subscribe((ZedStatusKind _) => EvaluateLogDrainState()),
            App.state.loggedIn.Subscribe((bool _) => EvaluateLogDrainState())
        );
    }

    public static void Shutdown()
    {
        healthPollTask.Cancel();
        logDrainTask.Cancel();
        subscriptions?.Dispose();
        subscriptions = null;
        capturesApi = null;
    }

    public static async UniTask StartCapture(float captureInterval, CancellationToken cancellationToken = default)
    {
        await capturesApi.StartCaptureAsync(captureInterval, cancellationToken);
        App.state.zedStatus.value = ZedStatusKind.Recording;
    }

    public static async UniTask StopCapture(CancellationToken cancellationToken = default)
    {
        await capturesApi.StopCaptureAsync(cancellationToken);
        App.state.zedStatus.value = ZedStatusKind.Ready;
    }

    // Bound enumerate so refreshes don't stall on a long socket timeout when the
    // ZED box is unreachable. An absent box is indistinguishable from an empty one.
    private static readonly TimeSpan enumerateTimeout = TimeSpan.FromSeconds(1);

    public static async UniTask<IEnumerable<LocalCapture>> EnumerateCaptures()
    {
        try
        {
            using var cts = new CancellationTokenSource(enumerateTimeout);
            var captures = await capturesApi.GetCapturesAsync(cts.Token);
            return captures.Select(c => new LocalCapture(c.Id, c.RecordedAt, DeviceType.Zed));
        }
        catch
        {
            return Enumerable.Empty<LocalCapture>();
        }
    }

    public static async UniTask<Stream> GetCapture(Guid captureId, CancellationToken cancellationToken = default) =>
        (await capturesApi.DownloadCaptureTarAsync(captureId, cancellationToken: cancellationToken)).Content;

    public static async UniTask DeleteCapture(Guid captureId, CancellationToken cancellationToken = default) =>
        await capturesApi.DeleteCaptureAsync(captureId, cancellationToken);

    public static async UniTask<ZedStatusModel> GetStatus(CancellationToken cancellationToken = default) =>
        await capturesApi.GetStatusAsync(cancellationToken);

    public static async UniTask<LogBatchModel> GetLogs(
        string since,
        int limit,
        CancellationToken cancellationToken = default
    ) => await capturesApi.GetLogsAsync(since, limit, cancellationToken);

    private static void EvaluateHealthPollState()
    {
        healthPollTask.Cancel();

        if (!App.state.loggedIn.value)
        {
            App.state.zedStatus.value = ZedStatusKind.Unknown;
            return;
        }

        App.state.zedStatus.value = ZedStatusKind.Connecting;
        healthPollTask = TaskHandle.Execute(HealthPollLoop);
    }

    private static async UniTask HealthPollLoop(CancellationToken cancellationToken)
    {
        int consecutiveFailures = 0;

        try
        {
            while (!cancellationToken.IsCancellationRequested)
            {
                ZedStatusModel response = null;

                using var requestCts = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
                requestCts.CancelAfter(TimeSpan.FromSeconds(healthRequestTimeoutSeconds));

                try
                {
                    response = await GetStatus(requestCts.Token);
                }
                catch (Exception exception) when (!cancellationToken.IsCancellationRequested)
                {
                    Log.Info(LogGroup.Zed, exception, "health poll request failed");
                }

                consecutiveFailures = response == null ? consecutiveFailures + 1 : 0;

                UpdateStatus(response, consecutiveFailures);

                await UniTask.WaitForSeconds(healthPollIntervalSeconds, cancellationToken: cancellationToken);
            }
        }
        catch (OperationCanceledException) when (cancellationToken.IsCancellationRequested) { }
    }

    private static void UpdateStatus(ZedStatusModel response, int consecutiveFailures)
    {
        if (consecutiveFailures >= healthUnreachableThreshold)
        {
            App.state.zedStatus.value = (App.state.zedStatus.value == ZedStatusKind.Recording || App.state.zedStatus.value == ZedStatusKind.LostMidCapture 
                ? ZedStatusKind.LostMidCapture 
                : ZedStatusKind.Unreachable);
        }

        if (consecutiveFailures > 0)
            return;

        if (response.CurrentCaptureId.HasValue)
        {
            App.state.zedStatus.value = ZedStatusKind.Recording;
            return;
        }

        if (!string.IsNullOrEmpty(response.LastException))
        {
            App.state.zedStatus.value = ZedStatusKind.DegradedError;
            return;
        }

        if (response.DiskFreeBytes < healthDiskLowBytes)
        {
            App.state.zedStatus.value = ZedStatusKind.DegradedDiskLow;
            return;
        }

        App.state.zedStatus.value = ZedStatusKind.Ready;
    }

    private static void EvaluateLogDrainState()
    {
        logDrainTask.Cancel();
        if (App.state.loggedIn.value && App.state.zedReachable.value)
        {
            logDrainTask = TaskHandle.Execute(LogDrainLoop);
        }
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
                catch (Exception e) when (!cancellationToken.IsCancellationRequested)
                {
                    Log.Info(LogGroup.Zed, e, "log drain tick failed");
                }

                if (!hasMore)
                {
                    await UniTask.WaitForSeconds(logDrainIdlePollIntervalSeconds, cancellationToken: cancellationToken);
                }
            }
        }
        catch (OperationCanceledException) when (cancellationToken.IsCancellationRequested) { }
    }

    private static async UniTask<bool> LogDrainOnce(CancellationToken cancellationToken)
    {
        var batch = await GetLogs(logDrainPendingAck, logDrainBatchLimit, cancellationToken);

        if (batch.DroppedBefore)
            Log.Info(LogGroup.Zed, "prior box logs rotated off before ack {Ack}", logDrainPendingAck);

        // Defensive null check despite Entries being marked required in the
        // schema. Codegen gap: the C# httpclient template emits a protected
        // parameterless constructor with [JsonConstructorAttribute], so
        // Newtonsoft deserializes via property setters and ignores the
        // [DataMember(IsRequired = true)] annotation — a malformed server
        // response with no "entries" field leaves Entries null. Fix belongs
        // in build/openapi-generator/templates-patches/csharp/ as a new
        // patch that adds [JsonProperty(Required = Required.Always)] to
        // required ref-type fields; once that lands this guard can go.
        if (batch.Entries != null && batch.Entries.Count > 0)
        {
            await VisualPositioningSystem.Api
                .PushZedBoxLogsAsync(new LogRelayBatch(batch.Entries), cancellationToken);
        }

        // Update logDrainPendingAck only after a successful round trip (fetch + forward).
        // Any throw above leaves it unchanged so the box re-serves on retry.
        logDrainPendingAck = batch.NextCursor;
        return batch.HasMore;
    }
#endif
}
