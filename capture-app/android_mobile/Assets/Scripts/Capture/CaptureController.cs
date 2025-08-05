using System;
using UnityEngine;
using UnityEngine.UI;
using R3;
using Cysharp.Threading.Tasks;
using System.Threading;
using TMPro;
using System.Collections.Generic;
using System.Linq;
using Unity.VisualScripting;
using PlerionClient.Client;
using PlerionClient.Api;
using System.IO;
using System.Net.Http;

using System.Net.Http.Headers;

namespace PlerionClient.Client
{
    public partial class ApiClient
    {
        public void InterceptRequest(HttpRequestMessage req)
        {
            // Only for the redirecting upload endpoint
            if (req.Method == HttpMethod.Put &&
                req.RequestUri != null &&
                req.RequestUri.AbsolutePath.EndsWith("/file"))
            {
                // 1) Header-only probe: make server send 307 before we stream the body
                req.Headers.ExpectContinue = true;

                // 2) Match the Content-Type used in the presign (important for signature)
                if (req.Content != null && req.Content.Headers.ContentType == null)
                {
                    req.Content.Headers.ContentType =
                        new MediaTypeHeaderValue("application/octet-stream"); // or whatever you signed
                }

                // (Optional) If you *know* the content length (seekable stream), set it here.
                // Many S3-compatible endpoints prefer Content-Length over chunked.
                // Unfortunately StreamContent doesn't expose the stream; prefer to set this
                // when you construct the StreamContent at the call site.
            }
        }

        public void InterceptResponse(HttpRequestMessage req, HttpResponseMessage resp)
        {
            // Normally you won't see 307 here because AllowAutoRedirect is true.
            // If you *do*, log it (or throw) to catch handler config issues.
            var code = (int)resp.StatusCode;
            if (code == 307 || code == 308)
            {
                UnityEngine.Debug.LogWarning(
                    $"Redirect not auto-followed for {req.Method} {req.RequestUri} → {resp.Headers.Location}");
            }
        }
    }
}


public class Capture
{
    public enum Mode
    {
        Local,
        Zed
    }

    public string Name { get; set; }
    public Mode Type { get; set; }
    public CaptureRow Row { get; set; }
    public IDisposable disposables { get; set; }
}

public class CaptureController : MonoBehaviour
{
    private enum Environment
    {
        Local,
        Remote
    }

    enum CaptureState
    {
        Idle,
        Starting,
        Capturing,
        Stopping
    }

    enum UploadState
    {
        NotUploaded,
        Uploading,
        Uploaded,
        Errored
    }

    public Button startStopButton;
    public TMP_Text startStopButtonText;
    public TMP_Dropdown captureMode;
    public RectTransform capturesTable;
    public RectTransform captureRowPrefab;

    [SerializeField][Range(0, 5)] float captureIntervalSeconds = 0.5f;

    private static Environment environment = Environment.Local;

    static private QueueSynchronizationContext context = new QueueSynchronizationContext();
    private ObservableProperty<CaptureState> captureStatus = new ObservableProperty<CaptureState>(context, CaptureState.Idle);
    private List<Capture> captures;
    private IDisposable disposables;
    private CapturesApi capturesApi;

    void Awake()
    {
        var temp = Application.streamingAssetsPath;

        var plerionAPIBaseUrl = environment switch
        {
            Environment.Local => "https://desktop-otd3rch-api.outernetfoundation.org",
            Environment.Remote => "https://api.outernetfoundation.org",
            _ => throw new ArgumentOutOfRangeException(nameof(environment), environment, null)
        };

        capturesApi = new CapturesApi(new Configuration
        {
            BasePath = plerionAPIBaseUrl
        });

        ZedCaptureController.Initialize();
        UpdateCaptureList();

        captureMode.options.Clear();
        foreach (var mode in Enum.GetValues(typeof(Capture.Mode)))
        {
            captureMode.options.Add(new TMP_Dropdown.OptionData(mode.ToString()));
        }

        var captureModeEventStream = captureMode
            .OnValueChangedAsObservable()
            .Select(index => (Capture.Mode)index)
            .DistinctUntilChanged();

        var captureControlEventStream = startStopButton
            .OnClickAsObservable()
            .WithLatestFrom(captureModeEventStream, (_, captureMode) => captureMode)
            .WithLatestFrom(captureStatus, (captureMode, captureState) => (captureMode, captureState));

        disposables = Disposable.Combine(

            captureStatus
                .Subscribe(state => startStopButtonText.text = state switch
                {
                    CaptureState.Idle => "Start Capture",
                    CaptureState.Starting => "Starting...",
                    CaptureState.Capturing => "Stop Capture",
                    CaptureState.Stopping => "Stopping...",
                    _ => throw new ArgumentOutOfRangeException(nameof(state), state, null)
                }),

            captureStatus
                .Select(state =>
                    state == CaptureState.Idle || state == CaptureState.Capturing)
                .Subscribe(isIdleOrCapturing => startStopButton.interactable = isIdleOrCapturing),

            captureStatus
                .Select(state =>
                    state == CaptureState.Idle)
                .Subscribe(isIdle => captureMode.interactable = isIdle),

            captureStatus
                .Where(state =>
                    state is CaptureState.Idle)
                .Skip(1) // Skip the initial state
                .Subscribe(UpdateCaptureList),

            captureControlEventStream
                .Where(@event =>
                    @event is (_, CaptureState.Starting or CaptureState.Stopping))
                .Subscribe(_ => Debug.LogError("Impossible!")),

            captureModeEventStream
                .WithLatestFrom(captureStatus, (mode, state) => (mode, state))
                .Where(@event =>
                    @event is (_, CaptureState.Starting or CaptureState.Stopping))
                .Subscribe(_ => Debug.LogError("Impossible!")),

            captureControlEventStream
                .Where(@event =>
                    @event is (Capture.Mode.Local, CaptureState.Idle))
                .SubscribeAwait(StartLocalCapture),

            captureControlEventStream
                .Where(@event =>
                    @event is (Capture.Mode.Local, CaptureState.Capturing))
                .Subscribe(StopLocalCapture),

            captureControlEventStream
                .Where(@event =>
                    @event is (Capture.Mode.Zed, CaptureState.Idle))
                .SubscribeAwait(StartZedCapture),

            captureControlEventStream
                .Where(@event =>
                    @event is (Capture.Mode.Zed, CaptureState.Capturing))
                .SubscribeAwait(StopZedCapture)
        );
    }

    void OnDestroy()
    {
        disposables?.Dispose();
        disposables = null;
    }

    private async UniTask StartLocalCapture(CancellationToken cancellationToken)
    {
        captureStatus.EnqueueSet(CaptureState.Starting);
        await LocalCaptureController.StartCapture(cancellationToken, captureIntervalSeconds);
        captureStatus.EnqueueSet(CaptureState.Capturing);
    }

    private void StopLocalCapture()
    {
        captureStatus.EnqueueSet(CaptureState.Stopping);
        LocalCaptureController.StopCapture();
        captureStatus.EnqueueSet(CaptureState.Idle);
    }

    private async UniTask StartZedCapture(CancellationToken cancellationToken)
    {
        captureStatus.EnqueueSet(CaptureState.Starting);
        await ZedCaptureController.StartCapture(cancellationToken, captureIntervalSeconds);
        captureStatus.EnqueueSet(CaptureState.Capturing);
    }

    private async UniTask StopZedCapture(CancellationToken cancellationToken)
    {
        captureStatus.EnqueueSet(CaptureState.Stopping);
        await ZedCaptureController.StopCapture(cancellationToken);
        captureStatus.EnqueueSet(CaptureState.Idle);
    }

    [Serializable]
    class CaptureUploadRequest
    {
        public string filename { get; set; }
    }

    async void UpdateCaptureList()
    {
        // Clear captures table
        if (captures != null)
        {
            foreach (var capture in captures)
            {
                capture.disposables.Dispose();
                Destroy(capture.Row.gameObject);
            }
        }

        var localCaptures = LocalCaptureController
            .GetCaptures()
            .Select(name => new Capture
            {
                Name = name,
                Type = Capture.Mode.Local
            });

        captures = localCaptures.ToList();

        var capturesFromServer = await capturesApi.GetCapturesAsync(
            captures.Select(c => c.Name).ToList());

        var databaseCaptures = capturesFromServer
            .ToList();

        foreach (var capture in captures)
        {
            var gameObject = Instantiate(captureRowPrefab, capturesTable);
            capture.Row = gameObject.GetComponent<CaptureRow>();
            capture.Row.captureName.text = capture.Name;
            capture.Row.captureType.text = capture.Type.ToString();

            if (databaseCaptures.Select(capture => capture.Filename).Contains(capture.Name))
            {
                capture.Row.uploadButton.interactable = false;
                capture.Row.uploadButtonText.text = "Uploaded";
                capture.disposables = Disposable.Empty;
            }
            else
            {
                capture.Row.uploadButton.interactable = true;
                capture.Row.uploadButtonText.text = "Upload";

                async UniTask UploadCapture(CancellationToken cancellationToken)
                {
                    var response = await capturesApi.CreateCaptureAsync(new PlerionClient.Model.BodyCreateCapture(capture.Name));

                    if (capture.Type == Capture.Mode.Zed)
                    {
                        var captureData = await ZedCaptureController.GetCapture(capture.Name);
                        await capturesApi.UploadCaptureFileAsync(response.Id.ToString(), new MemoryStream(captureData), cancellationToken);
                    }
                    else if (capture.Type == Capture.Mode.Local)
                    {
                        var captureData = await LocalCaptureController.GetCapture(capture.Name);
                        await capturesApi.UploadCaptureFileAsync(response.Id.ToString(), new MemoryStream(captureData), cancellationToken);
                    }

                    UpdateCaptureList();
                }

                capture.disposables = capture.Row.uploadButton.onClick
                    .AsObservable()
                    .SubscribeAwait(UploadCapture);
            }
        }
    }
}
