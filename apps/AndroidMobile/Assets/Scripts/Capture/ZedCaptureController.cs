using System;
using System.Collections.Generic;
using System.IO;
using System.Threading;
using Cysharp.Threading.Tasks;
using LogBatchModel = PlaceframeZedCaptureClient.Model.LogBatch;
using ZedStatusModel = PlaceframeZedCaptureClient.Model.ZedStatus;

#if !UNITY_EDITOR && UNITY_ANDROID
using System.Net.Http;
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

#else

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
    private static string logDrainPendingAck = "";
    private static TaskHandle logDrainTask = TaskHandle.Complete;

    public static void Initialize()
    {
        if (capturesApi != null)
            throw new InvalidOperationException("ZedCaptureController.Initialize already called");

        capturesApi = new DefaultApi(
            new HttpClient(new AndroidBoundHttpHandler(forZedBox: true))
            {
                BaseAddress = new Uri(baseUrl),
                Timeout = requestTimeout,
            },
            new Configuration { BasePath = baseUrl, Timeout = requestTimeout }
        );

        App.state.captureMode.ToObservable().Subscribe(OnCaptureModeChanged);
        App.state.loggedIn.ToObservable().Subscribe(_ => EvaluateLogDrainState());
    }

    public static async UniTask StartCapture(float captureInterval, CancellationToken cancellationToken = default)
    {
        await capturesApi.StartCaptureAsync(captureInterval, cancellationToken);
        App.state.zedStatus.ExecuteSetOrDelay(ZedStatusKind.Recording);
    }

    public static async UniTask StopCapture(CancellationToken cancellationToken = default)
    {
        await capturesApi.StopCaptureAsync(cancellationToken);
        App.state.zedStatus.ExecuteSetOrDelay(ZedStatusKind.Ready);
    }

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
                catch (Exception) when (!cancellationToken.IsCancellationRequested)
                {
                    // Network failure, per-request timeout, deserialization error — treated as unreachable.
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
            App.state.zedStatus.ExecuteSetOrDelay(
                App.state.zedStatus.value == ZedStatusKind.Recording || App.state.zedStatus.value == ZedStatusKind.LostMidCapture 
                ? ZedStatusKind.LostMidCapture 
                : ZedStatusKind.Unreachable);
        }

        if (consecutiveFailures > 0)
            return;

        if (response.CurrentCaptureId.HasValue)
        {
            App.state.zedStatus.ExecuteSetOrDelay(ZedStatusKind.Recording);
            return;
        }

        if (!string.IsNullOrEmpty(response.LastException))
        {
            App.state.zedStatus.ExecuteSetOrDelay(ZedStatusKind.DegradedError);
            return;
        }

        if (response.DiskFreeBytes < healthDiskLowBytes)
        {
            App.state.zedStatus.ExecuteSetOrDelay(ZedStatusKind.DegradedDiskLow);
            return;
        }

        App.state.zedStatus.ExecuteSetOrDelay(ZedStatusKind.Ready);
    }

    // Drain depends on both signals: capture mode is ZED (so the box is the
    // log source) AND loggedIn (so the relay forward to the backend can
    // authenticate). Re-evaluated whenever either input changes.
    private static void EvaluateLogDrainState()
    {
        logDrainTask.Cancel();
        if (App.state.captureMode.value == DeviceType.Zed
            && App.state.loggedIn.value)
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
                    Log.Warn(LogGroup.Zed, $"log drain tick failed: {e.Message}");
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
#endif
}
