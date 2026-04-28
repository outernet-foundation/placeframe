using System;
using System.Collections.Generic;
using System.IO;
using System.Net.Http;
using System.Threading;
using Cysharp.Threading.Tasks;
using FofX;
using FofX.Stateful;
using ObserveThing;
using ObserveThing.StatefulExtensions;
using Placeframe.Client;
using Placeframe.Core;
using PlaceframeApiClient.Model;
using PlaceframeZedCaptureClient.Api;
using PlaceframeZedCaptureClient.Client;
using DeviceType = PlaceframeApiClient.Model.DeviceType;
using LogBatchModel = PlaceframeZedCaptureClient.Model.LogBatch;
using ZedStatusModel = PlaceframeZedCaptureClient.Model.ZedStatus;

public static class ZedCaptureController
{
#if !UNITY_EDITOR && UNITY_ANDROID
    private const int transportEthernet = 3;

    // The ZED box reaches the phone over a USB-ethernet gadget interface: the
    // phone's USB-C cable to the ZED's OTG port, with the ZED running in USB
    // gadget mode presenting as a USB-ethernet (RNDIS/ECM) peripheral. Android
    // enumerates this as TRANSPORT_ETHERNET. No physical ethernet or dongle is
    // involved — the USB cable *is* the ethernet link. 192.168.55.1 is the
    // box's address on that interface; 9000 is the zed-capture HTTP server.
    private const string baseUrl = "http://192.168.55.1:9000";
    private static readonly TimeSpan requestTimeout = TimeSpan.FromSeconds(600);

    private static DefaultApi capturesApi;

    private const float healthPollIntervalSeconds = 0.5f;
    private const float healthRequestTimeoutSeconds = 2f;
    private const int healthUnreachableThreshold = 2;
    private const long healthDiskLowBytes = 1L * 1024L * 1024L * 1024L;
    private static TaskHandle healthPollTask = TaskHandle.Complete;

    private const int logDrainBatchLimit = 500;
    private const float logDrainIdlePollIntervalSeconds = 5f;
    // The box owns the cursor. We only carry the previous response's token so we
    // can ack it on the next fetch, and only after the relay forward succeeds —
    // a transient forward failure keeps the same token, the box keeps re-serving
    // the same chunk, and we deliver at-least-once.
    private static string logDrainPendingAck = "";
    private static TaskHandle logDrainTask = TaskHandle.Complete;

    public static void Initialize()
    {
        if (capturesApi != null)
            throw new InvalidOperationException("ZedCaptureController.Initialize already called");

        var handler = new Placeframe.Client.AndroidBoundHttpHandler(new[] { transportEthernet });
        capturesApi = new DefaultApi(
            new HttpClient(handler)
            {
                BaseAddress = new Uri(baseUrl),
                Timeout = requestTimeout,
            },
            new Configuration { BasePath = baseUrl, Timeout = requestTimeout }
        );

        App.state.captureMode.ToObservable().Subscribe(OnCaptureModeChanged);
        App.state.loggedIn.ToObservable().Subscribe(_ => EvaluateLogDrainState());
    }

    public static async UniTask StartCapture(float captureInterval, CancellationToken cancellationToken = default) =>
        await capturesApi.StartCaptureAsync(captureInterval, cancellationToken);

    public static async UniTask StopCapture(CancellationToken cancellationToken = default) =>
        await capturesApi.StopCaptureAsync(cancellationToken);

    public static async UniTask<IEnumerable<Guid>> GetCaptures(CancellationToken cancellationToken = default) =>
        await capturesApi.GetCapturesAsync(cancellationToken);

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

    private static void OnCaptureModeChanged(DeviceType mode)
    {
        OnHealthCaptureModeChanged(mode);
        EvaluateLogDrainState();
    }

    private static void OnHealthCaptureModeChanged(DeviceType mode)
    {
        healthPollTask.Cancel();

        if (mode != DeviceType.Zed)
        {
            App.state.zedStatus.ExecuteSetOrDelay(ZedStatusKind.Unknown);
            return;
        }

        App.state.zedStatus.ExecuteSetOrDelay(ZedStatusKind.Connecting);
        healthPollTask = TaskHandle.Execute(HealthPollLoop);
    }

    private static async UniTask HealthPollLoop(CancellationToken cancellationToken)
    {
        int consecutiveFailures = 0;

        while (!cancellationToken.IsCancellationRequested)
        {
            ZedStatusModel response = null;

            using var requestCts = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
            requestCts.CancelAfter(TimeSpan.FromSeconds(healthRequestTimeoutSeconds));

            try
            {
                response = await GetStatus(requestCts.Token);
            }
            catch (OperationCanceledException) when (cancellationToken.IsCancellationRequested)
            {
                return;
            }
            catch (Exception)
            {
                // Network failure, per-request timeout, deserialization error — treated as unreachable.
            }

            if (response != null)
            {
                consecutiveFailures = 0;
                ZedStatusKind kind;
                if (response.CurrentCaptureId.HasValue)
                    kind = ZedStatusKind.Recording;
                else if (!string.IsNullOrEmpty(response.LastException))
                    kind = ZedStatusKind.DegradedError;
                else if (response.DiskFreeBytes < healthDiskLowBytes)
                    kind = ZedStatusKind.DegradedDiskLow;
                else
                    kind = ZedStatusKind.Ready;
                App.state.zedStatus.ExecuteSetOrDelay(kind);
            }
            else
            {
                consecutiveFailures++;
                if (consecutiveFailures >= healthUnreachableThreshold)
                {
                    var previous = App.state.zedStatus.value;
                    var wasRecording = previous == ZedStatusKind.Recording
                        || previous == ZedStatusKind.LostMidCapture;
                    var nextKind = wasRecording ? ZedStatusKind.LostMidCapture : ZedStatusKind.Unreachable;
                    App.state.zedStatus.ExecuteSetOrDelay(nextKind);
                }
            }

            await UniTask.WaitForSeconds(healthPollIntervalSeconds, cancellationToken: cancellationToken);
        }
    }

    // Drain depends on both signals: capture mode is ZED (so the box is the
    // log source) AND loggedIn (so the relay forward to the backend can
    // authenticate). Re-evaluated whenever either input changes.
    private static void EvaluateLogDrainState()
    {
        var shouldDrain = App.state.captureMode.value == DeviceType.Zed
                          && App.state.loggedIn.value;

        logDrainTask.Cancel();
        if (shouldDrain)
        {
            logDrainPendingAck = "";
            logDrainTask = TaskHandle.Execute(LogDrainLoop);
        }
    }

    private static async UniTask LogDrainLoop(CancellationToken cancellationToken)
    {
        while (!cancellationToken.IsCancellationRequested)
        {
            bool hasMore = false;
            try
            {
                hasMore = await LogDrainOnce(cancellationToken);
            }
            catch (OperationCanceledException) when (cancellationToken.IsCancellationRequested)
            {
                return;
            }
            catch (Exception e)
            {
                Log.Warn(LogGroup.Zed, $"log drain tick failed: {e.Message}");
            }

            if (!hasMore)
            {
                await UniTask.WaitForSeconds(logDrainIdlePollIntervalSeconds, cancellationToken: cancellationToken);
            }
        }
    }

    private static async UniTask<bool> LogDrainOnce(CancellationToken cancellationToken)
    {
        var batch = await GetLogs(logDrainPendingAck, logDrainBatchLimit, cancellationToken);

        if (batch.DroppedBefore)
            Log.Warn(LogGroup.Zed, $"prior box logs rotated off before ack '{logDrainPendingAck}'.");

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
                .PushZedBoxLogsAsync(new LogRelayBatch(batch.Entries), cancellationToken)
                .AsUniTask();
        }

        // Update logDrainPendingAck only after a successful round trip (fetch + forward).
        // Any throw above leaves it unchanged so the box re-serves on retry.
        logDrainPendingAck = batch.NextCursor;
        return batch.HasMore;
    }
#else
    private const string unsupportedMessage = "ZedCaptureController is only supported on non-Editor Android builds";
    private static bool initialized;

    public static void Initialize()
    {
        if (initialized)
            throw new InvalidOperationException("ZedCaptureController.Initialize already called");
        initialized = true;
    }

    public static UniTask StartCapture(float captureInterval, CancellationToken cancellationToken = default) =>
        throw new PlatformNotSupportedException(unsupportedMessage);

    public static UniTask StopCapture(CancellationToken cancellationToken = default) =>
        throw new PlatformNotSupportedException(unsupportedMessage);

    public static UniTask<IEnumerable<Guid>> GetCaptures(CancellationToken cancellationToken = default) =>
        throw new PlatformNotSupportedException(unsupportedMessage);

    public static UniTask<Stream> GetCapture(Guid captureId, CancellationToken cancellationToken = default) =>
        throw new PlatformNotSupportedException(unsupportedMessage);

    public static UniTask DeleteCapture(Guid captureId, CancellationToken cancellationToken = default) =>
        throw new PlatformNotSupportedException(unsupportedMessage);

    public static UniTask<ZedStatusModel> GetStatus(CancellationToken cancellationToken = default) =>
        throw new PlatformNotSupportedException(unsupportedMessage);

    public static UniTask<LogBatchModel> GetLogs(string since, int limit, CancellationToken cancellationToken = default) =>
        throw new PlatformNotSupportedException(unsupportedMessage);
#endif
}
