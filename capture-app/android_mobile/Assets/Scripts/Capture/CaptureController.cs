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
using Polly;

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
            Environment.Local => Resources.Load<TextAsset>("ngrok").text,
            Environment.Remote => "",
            _ => throw new ArgumentOutOfRangeException(nameof(environment), environment, null)
        };

        capturesApi = new CapturesApi(new Configuration { BasePath = plerionAPIBaseUrl });

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
                    if (capture.Type == Capture.Mode.Zed)
                    {
                        var captureData = await ZedCaptureController.GetCapture(capture.Name);
                        await capturesApi.UploadCaptureFileAsync(capture.Name, new MemoryStream(captureData), cancellationToken);
                    }
                    else if (capture.Type == Capture.Mode.Local)
                    {
                        var captureData = await LocalCaptureController.GetCapture(capture.Name);
                        await capturesApi.UploadCaptureFileAsync(capture.Name, new MemoryStream(captureData), cancellationToken);
                    }
                }

                capture.disposables = capture.Row.uploadButton.onClick
                    .AsObservable()
                    .SubscribeAwait(UploadCapture);
            }
        }
    }
}
