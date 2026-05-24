using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading;
using Cysharp.Threading.Tasks;
using Placeframe.Client;
using Placeframe.Core;
using PlaceframeApiClient.Model;
using FileParameter = PlaceframeApiClient.Client.FileParameter;
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
using UnityEngine;
using DeviceType = PlaceframeApiClient.Model.DeviceType;
#endif

// Defense-in-depth pair to AoaSocketFactory's socketIssued guard: the Java
// guard stops a concurrent socket from corrupting the wire, this guard stops
// a concurrent request from being initiated at all. A typed handle ("ZedSession"
// passed to call sites) would enforce the same invariant in the type system,
// but every AOA call already funnels through this static controller — gating
// at the chokepoint achieves the same structural guarantee without call-site
// churn.
public sealed class ZedNotReachableException : Exception
{
    public ZedNotReachableException()
        : base("Zed box is not reachable; refused to dispatch the call to the AOA pipe") {}
}

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

    public static UniTask<FileParameter> GetCapture(Guid captureId, CancellationToken cancellationToken = default) =>
        throw new PlatformNotSupportedException(unsupportedMessage);

    public static UniTask DeleteCapture(Guid captureId, CancellationToken cancellationToken = default) =>
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
    private static AccessoryEventBridge accessoryEvents;

    private const float healthPollIntervalSeconds = 0.5f;
    private const float healthRequestTimeoutSeconds = 2f;
    private const int healthUnreachableThreshold = 2;
    private const long healthDiskLowBytes = 1L * 1024L * 1024L * 1024L;
    private static TaskHandle healthPollTask = TaskHandle.Complete;

    private static HttpClient capturesHttpClient;

    public static HttpClient AoaHttpClient => capturesHttpClient;

    public static void Initialize()
    {
        if (capturesApi != null)
            throw new InvalidOperationException("ZedCaptureController.Initialize already called");

        capturesHttpClient = new HttpClient(new ProgressTrackingHandler { InnerHandler = new AndroidAoaHttpHandler() })
        {
            BaseAddress = new Uri(baseUrl),
            Timeout = requestTimeout,
        };
        capturesApi = new DefaultApi(
            capturesHttpClient,
            new Configuration { BasePath = baseUrl, Timeout = requestTimeout }
        );

        accessoryEvents = new AccessoryEventBridge(
            onAttached: OnAccessoryAttached,
            onDetached: OnAccessoryDetached,
            onPermissionResult: OnAccessoryPermissionResult
        );
        using (var activity = new AndroidJavaClass("com.unity3d.player.UnityPlayer")
            .GetStatic<AndroidJavaObject>("currentActivity"))
        {
            AoaJni.RegisterEventListener(activity, accessoryEvents);
        }

        // TODO(ObserveThing): explicit lambda parameter type is a workaround for an
        // overload-resolution gap. StateValue<T> implements both IValueObservable<T>
        // and IObservable<IStateOperation> (via IStateNode), so Observables.Subscribe
        // matches two extension overloads. When the lambda body discards the value
        // with `_`, the call is ambiguous (CS0121). The fix belongs upstream in
        // ObserveThing — either by collapsing the dual interface or by adding a
        // Subscribe overload on IStateNode that wins resolution.
        subscriptions = App.state.loggedIn.Subscribe((bool _) => EvaluateHealthPollState());
    }

    public static void Shutdown()
    {
        healthPollTask.Cancel();
        subscriptions?.Dispose();
        subscriptions = null;
        capturesApi = null;
        capturesHttpClient?.Dispose();
        capturesHttpClient = null;
    }

    public static async UniTask StartCapture(float captureInterval, CancellationToken cancellationToken = default)
    {
        EnsureReachable();
        await capturesApi.StartCaptureAsync(captureInterval, cancellationToken);
        App.state.zedStatus.value = ZedStatusKind.Recording;
    }

    public static async UniTask StopCapture(CancellationToken cancellationToken = default)
    {
        EnsureReachable();
        await capturesApi.StopCaptureAsync(cancellationToken);
        App.state.zedStatus.value = ZedStatusKind.Ready;
    }

    // Bound enumerate so refreshes don't stall on a long socket timeout when the
    // ZED box is unreachable. An absent box is indistinguishable from an empty one.
    private static readonly TimeSpan enumerateTimeout = TimeSpan.FromSeconds(1);

    public static async UniTask<IEnumerable<LocalCapture>> EnumerateCaptures()
    {
        EnsureReachable();
        var stopwatch = System.Diagnostics.Stopwatch.StartNew();
        try
        {
            using var cts = new CancellationTokenSource(enumerateTimeout);
            var captures = await capturesApi.GetCapturesAsync(cts.Token);
            var result = captures
                .Select(c => new LocalCapture(c.Id, c.RecordedAt, DeviceType.Zed, c.SizeBytes))
                .ToList();
            Log.Info(LogGroup.Zed, "EnumerateCaptures success count={Count} durationMs={DurationMs}",
                result.Count, stopwatch.ElapsedMilliseconds);
            return result;
        }
        catch (Exception exception)
        {
            Log.Info(LogGroup.Zed, exception,
                "EnumerateCaptures failed durationMs={DurationMs} timeoutMs={TimeoutMs}",
                stopwatch.ElapsedMilliseconds, (int)enumerateTimeout.TotalMilliseconds);
            return Enumerable.Empty<LocalCapture>();
        }
    }

    public static async UniTask<FileParameter> GetCapture(Guid captureId, CancellationToken cancellationToken = default)
    {
        EnsureReachable();
        var response = await capturesApi.DownloadCaptureTarWithHttpInfoAsync(captureId, cancellationToken: cancellationToken);
        return new FileParameter(
            $"{captureId}.tar",
            "application/x-tar",
            new LengthOnlyStream(response.Data.Content, long.Parse(response.Headers["Content-Length"][0])));
    }

    public static async UniTask DeleteCapture(Guid captureId, CancellationToken cancellationToken = default)
    {
        EnsureReachable();
        await capturesApi.DeleteCaptureAsync(captureId, cancellationToken);
    }

    private static void EnsureReachable()
    {
        if (!App.state.zedReachable.value)
            throw new ZedNotReachableException();
    }

    private static void OnAccessoryAttached()
    {
        Log.Info(LogGroup.Zed, "AOA accessory attached");
        if (App.state.loggedIn.value)
            App.state.zedStatus.value = ZedStatusKind.Connecting;
    }

    private static void OnAccessoryDetached()
    {
        Log.Info(LogGroup.Zed, "AOA accessory detached");
        ZedStatusKind previous = App.state.zedStatus.value;
        App.state.zedStatus.value =
            previous == ZedStatusKind.Recording || previous == ZedStatusKind.LostMidCapture
                ? ZedStatusKind.LostMidCapture
                : ZedStatusKind.Unreachable;
    }

    private static void OnAccessoryPermissionResult(bool granted) =>
        Log.Info(LogGroup.Zed, "AOA accessory permission result granted={Granted}", granted);

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
                    response = await capturesApi.GetStatusAsync(requestCts.Token);
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
#endif
}
