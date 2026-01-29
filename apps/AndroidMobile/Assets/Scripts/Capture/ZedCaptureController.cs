using System;
using System.Collections.Generic;
using System.IO;
using System.Net.Http;
using System.Threading;
using Cysharp.Threading.Tasks;
using PlaceframeZedClient.Api;
using PlaceframeZedClient.Client;

public static class ZedCaptureController
{
    private static DefaultApi capturesApi;
    private static readonly string host = "http://192.168.55.1";
    private static readonly int port = 9000;

    [Serializable]
    struct StartCaptureRequest
    {
        public string capture_name;
        public float capture_interval;
    }

    public static void Initialize()
    {
#if !UNITY_EDITOR && UNITY_ANDROID
        AndroidMobileEthernetNetworkBinder.Initialize();
#endif
        capturesApi = new DefaultApi(
            new HttpClient(new HttpClientHandler())
            {
                BaseAddress = new Uri($"{host}:{port}"),
                Timeout = TimeSpan.FromSeconds(600),
            },
            new Configuration { BasePath = $"{host}:{port}", Timeout = TimeSpan.FromSeconds(600) }
        );
    }

    public static async UniTask<T> WithEthernetIfAndroidMobile<T>(
        Func<UniTask<T>> action,
        CancellationToken cancellationToken = default
    )
    {
#if !UNITY_EDITOR && UNITY_ANDROID
        await AndroidMobileEthernetNetworkBinder.Enter();
#endif
        var result = await action();
#if !UNITY_EDITOR && UNITY_ANDROID
        AndroidMobileEthernetNetworkBinder.Exit();
#endif
        return result;
    }

    public static async UniTask StartCapture(float captureInterval, CancellationToken cancellationToken = default) =>
        await WithEthernetIfAndroidMobile(async () =>
            await capturesApi.StartCaptureAsync(captureInterval, cancellationToken)
        );

    public static async UniTask StopCapture(CancellationToken cancellationToken = default) =>
        await WithEthernetIfAndroidMobile(async () => await capturesApi.StopCaptureAsync(cancellationToken));

    public static async UniTask<IEnumerable<Guid>> GetCaptures(CancellationToken cancellationToken = default) =>
        await WithEthernetIfAndroidMobile<IEnumerable<Guid>>(async () =>
            await capturesApi.GetCapturesAsync(cancellationToken)
        );

    public static async UniTask<Stream> GetCapture(Guid captureId, CancellationToken cancellationToken = default) =>
        await WithEthernetIfAndroidMobile(async () =>
            (await capturesApi.DownloadCaptureTarAsync(captureId, cancellationToken)).Content
        );

    public static async UniTask DeleteCapture(Guid captureId, CancellationToken cancellationToken = default) =>
        await WithEthernetIfAndroidMobile(async () =>
            await capturesApi.DeleteCaptureAsync(captureId, cancellationToken)
        );
}
