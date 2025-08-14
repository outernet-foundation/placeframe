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
using System.Net.Http;

using System.IO;

using System.Net.Http.Headers;
using Nessle;
using ObserveThing;

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
    public bool Uploaded { get; set; }
}

public partial class CaptureController : MonoBehaviour
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

    // public Button startStopButton;
    // public TMP_Text startStopButtonText;
    // public TMP_Dropdown captureMode;
    // public RectTransform capturesTable;
    // public RectTransform captureRowPrefab;

    public Canvas canvas;

    [SerializeField][Range(0, 5)] float captureIntervalSeconds = 0.5f;

    static private QueueSynchronizationContext context = new QueueSynchronizationContext();
    private ObservableProperty<CaptureState> captureStatus = new ObservableProperty<CaptureState>(context, CaptureState.Idle);
    private CollectionObservable<Capture> captures = new CollectionObservable<Capture>();
    private IDisposable disposables;
    private CapturesApi capturesApi;

    public Color color;

    private UnityComponentControl<Canvas> canvasControl;

    void Awake()
    {
        var plerionAPIBaseUrl = "https://api.outernetfoundation.org";

#if UNITY_EDITOR
        var editorSettings = EditorSettings.GetOrCreateInstance();
        if (editorSettings.overrideEnvironment)
            plerionAPIBaseUrl = editorSettings.overrideEnvironmentURL;
#endif

        capturesApi = new CapturesApi(new Configuration
        {
            BasePath = plerionAPIBaseUrl
        });

        ZedCaptureController.Initialize();
        UpdateCaptureList();

        UIBuilder.DefaultButtonStyle = UIPresets.StylePillButton;
        UIBuilder.DefaultScrollbarStyle = UIPresets.StyleRoundedScrollBar;
        UIBuilder.DefaultInputFieldStyle = UIPresets.StylePillInputField;
        UIBuilder.DefaultLabelStyle = UIPresets.StyleStandardText;
        UIBuilder.DefaultScrollRectStyle = UIPresets.StyleStandardScrollRect;
        UIBuilder.DefaultDropdownStyle = UIPresets.StyleStandardDropdown;

        IUnityComponentControl<Button> startStopButton;
        IUnityComponentControl<TextMeshProUGUI> startStopButtonText;
        IUnityComponentControl<TMP_Dropdown> captureMode;

        canvasControl = new UnityComponentControl<Canvas>(canvas).Children(UIPresets.SafeArea().FillParent().Children(
            UIBuilder.Image().FillParent().Color(UIResources.PanelColor),
            UIBuilder.VerticalLayout().FillParent().ControlChildSize(true).ChildForceExpandWidth(true).Spacing(10).Padding(new RectOffset(10, 10, 10, 10)).Children(
                UIPresets.VerticalScrollRect().FlexibleHeight(true).Content(
                    UIBuilder.VerticalLayout().ChildForceExpandWidth(true).ControlChildSize(true).Spacing(10).Children(
                        captures.SelectDynamic(x => ConstructCaptureRow(x).WithMetadata(x.Name)).OrderByDynamic(x => x.metadata)
                    )
                ),
                UIPresets.Row().Children(
                    startStopButton = UIBuilder.Button().Content(startStopButtonText = UIBuilder.Label().Text("Start Capture")),
                    captureMode = UIBuilder.ScrollingDropdown().Style(x => x.template.SizeDelta(new Vector2(0, 60))).PreferredWidth(100).PreferredHeight(25.65f).Options(Enum.GetNames(typeof(Capture.Mode)))
                )
            )
        ));

        var captureModeEventStream = captureMode.component
            .OnValueChangedAsObservable()
            .Select(index => (Capture.Mode)index)
            .DistinctUntilChanged();

        var captureControlEventStream = startStopButton.component
            .OnClickAsObservable()
            .WithLatestFrom(captureModeEventStream, (_, captureMode) => captureMode)
            .WithLatestFrom(captureStatus, (captureMode, captureState) => (captureMode, captureState));

        disposables = Disposable.Combine(

            captureStatus
                .Subscribe(state => startStopButtonText.component.text = state switch
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
                    .Subscribe(isIdleOrCapturing => startStopButton.component.interactable = isIdleOrCapturing),

                captureStatus
                    .Select(state =>
                        state == CaptureState.Idle)
                    .Subscribe(isIdle => captureMode.component.interactable = isIdle),

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

    private IControl ConstructCaptureRow(Capture capture)
    {
        return UIPresets.Row().Children(
            UIBuilder.Label()
                .Text(capture.Name)
                .MinHeight(25)
                .FlexibleWidth(true),
            UIBuilder.Label()
                .Text(capture.Type)
                .MinHeight(25)
                .PreferredWidth(100),
            UIBuilder.Button()
                .Interactable(!capture.Uploaded)
                .PreferredWidth(100)
                .Content(UIBuilder.Label().Text(capture.Uploaded ? "Uploaded" : "Upload").Alignment(TextAlignmentOptions.CaplineGeoAligned))
                .OnClick(() => UploadCapture(capture.Name, capture.Type, default).Forget())
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

    async void UpdateCaptureList()
    {
        var localCaptures = LocalCaptureController.GetCaptures();

        var remoteCaptures = await capturesApi.GetCapturesAsync(
            localCaptures.ToList());

        captures.Clear();

        foreach (var capture in localCaptures)
        {
            captures.Add(new Capture()
            {
                Name = capture,
                Type = Capture.Mode.Local,
                Uploaded = remoteCaptures.Select(capture => capture.Filename).Contains(capture)
            });
        }
    }

    private async UniTask UploadCapture(string name, Capture.Mode mode, CancellationToken cancellationToken)
    {
        var response = await capturesApi.CreateCaptureAsync(new PlerionClient.Model.BodyCreateCapture(name));

        if (mode == Capture.Mode.Zed)
        {
            var captureData = await ZedCaptureController.GetCapture(name);
            await capturesApi.UploadCaptureFileAsync(response.Id.ToString(), new MemoryStream(captureData), cancellationToken);
        }
        else if (mode == Capture.Mode.Local)
        {
            var captureData = await LocalCaptureController.GetCapture(name);
            await capturesApi.UploadCaptureFileAsync(response.Id.ToString(), new MemoryStream(captureData), cancellationToken);
        }

        UpdateCaptureList();
    }
}
