using System;
using System.IO;
using System.Threading;
using System.Linq;

using UnityEngine;
using UnityEngine.UI;

using Cysharp.Threading.Tasks;
using TMPro;
using PlerionClient.Api;

using FofX;
using FofX.Stateful;
using Nessle;
using ObserveThing;
using static Nessle.UIBuilder;
using static PlerionClient.Client.UIPresets;

namespace PlerionClient.Client
{
    public class CaptureController : MonoBehaviour
    {
        public Canvas canvas;
        [SerializeField][Range(0, 5)] float captureIntervalSeconds = 0.5f;

        private CapturesApi capturesApi;
        private UnityComponentControl<Canvas> ui;
        private TaskHandle currentCaptureTask = TaskHandle.Complete;

        void Awake()
        {
            capturesApi = new CapturesApi(new Configuration { BasePath = App.state.plerionAPIBaseUrl.value });

            DefaultButtonStyle = StylePillButton;
            DefaultScrollbarStyle = StyleRoundedScrollBar;
            DefaultInputFieldStyle = StylePillInputField;
            DefaultLabelStyle = StyleStandardText;
            DefaultScrollRectStyle = StyleStandardScrollRect;
            DefaultDropdownStyle = StyleStandardDropdown;

            ui = ConstructUI(canvas);

            App.RegisterObserver(HandleCaptureStatusChanged, App.state.captureStatus);
        }

        private void HandleCaptureStatusChanged(NodeChangeEventArgs args)
        {
            if (args.initialize)
                return;

            switch (App.state.captureStatus.value)
            {
                case CaptureStatus.Idle:
                    UpdateCaptureList().Forget();
                    break;

                case CaptureStatus.Starting:
                    currentCaptureTask = TaskHandle.Execute(async token =>
                    {
                        await StartCapture(App.state.captureMode.value, token);
                        App.state.ExecuteAction(new SetCaptureStatusAction(CaptureStatus.Capturing));
                    });
                    break;

                case CaptureStatus.Stopping:
                    currentCaptureTask = TaskHandle.Execute(async token =>
                    {
                        await StopCapture(App.state.captureMode.value, token);
                        App.state.ExecuteAction(new SetCaptureStatusAction(CaptureStatus.Idle));
                    });
                    break;
            }
        }

        private async UniTask StartCapture(CaptureType captureType, CancellationToken cancellationToken = default)
        {
            switch (captureType)
            {
                case CaptureType.Local:
                    LocalCaptureController.StopCapture();
                    break;
                case CaptureType.Zed:
                    await ZedCaptureController.StopCapture(cancellationToken);
                    break;
                default:
                    throw new Exception($"Unhandled capture type {captureType}");
            }
        }

        private async UniTask StopCapture(CaptureType captureType, CancellationToken cancellationToken = default)
        {
            switch (captureType)
            {
                case CaptureType.Local:
                    await LocalCaptureController.StartCapture(cancellationToken, captureIntervalSeconds);
                    break;
                case CaptureType.Zed:
                    await ZedCaptureController.StartCapture(cancellationToken, captureIntervalSeconds);
                    break;
                default:
                    throw new Exception($"Unhandled capture type {captureType}");
            }
        }

        void OnDestroy()
        {
            ui.Dispose();
            currentCaptureTask.Cancel();
        }

        private async UniTask UpdateCaptureList()
        {
            var localCaptures = LocalCaptureController.GetCaptures().ToList();

            var remoteCaptures = await capturesApi.GetCapturesAsync(
                localCaptures.ToList());

            App.state.captures.ExecuteActionOrDelay(
                (localCaptures, remoteCaptures),
                (data, state) =>
                {
                    state.Clear();
                    foreach (var capture in data.localCaptures)
                    {
                        var newCapture = state.Add();
                        newCapture.name.value = capture;
                        newCapture.type.value = CaptureType.Local;
                        newCapture.uploaded.value = remoteCaptures.Select(capture => capture.Filename).Contains(capture);
                    }
                }
            );
        }

        private async UniTask UploadCapture(string name, CaptureType type, CancellationToken cancellationToken)
        {
            var response = await capturesApi.CreateCaptureAsync(new PlerionClient.Model.BodyCreateCapture(name));

            if (type == CaptureType.Zed)
            {
                var captureData = await ZedCaptureController.GetCapture(name);
                await capturesApi.UploadCaptureFileAsync(response.Id.ToString(), new MemoryStream(captureData), cancellationToken);
            }
            else if (type == CaptureType.Local)
            {
                var captureData = await LocalCaptureController.GetCapture(name);
                await capturesApi.UploadCaptureFileAsync(response.Id.ToString(), new MemoryStream(captureData), cancellationToken);
            }

            await UpdateCaptureList();
        }

        private UnityComponentControl<Canvas> ConstructUI(Canvas canvas)
        {
            return new UnityComponentControl<Canvas>(canvas).Children(SafeArea().FillParent().Children(
                Image().FillParent().Color(UIResources.PanelColor),
                VerticalLayout()
                    .FillParent()
                    .ControlChildSize(true)
                    .ChildForceExpandWidth(true)
                    .Spacing(10)
                    .Padding(new RectOffset(10, 10, 10, 10))
                    .Children(
                        VerticalScrollRect().FlexibleHeight(true).Content(
                            VerticalLayout().ChildForceExpandWidth(true).ControlChildSize(true).Spacing(10).Children(
                                App.state.captures
                                    .SelectDynamic(x => ConstructCaptureRow(x).WithMetadata(x.name))
                                    .OrderByDynamic(x => x.metadata.AsObservable())
                            )
                        ),
                        Row().Children(
                            Button()
                                .Interactable(App.state.captureStatus.SelectDynamic(x => x == CaptureStatus.Idle || x == CaptureStatus.Capturing))
                                .Content(Label().Text(App.state.captureStatus.SelectDynamic(x =>
                                    x switch
                                    {
                                        CaptureStatus.Idle => "Start Capture",
                                        CaptureStatus.Starting => "Starting...",
                                        CaptureStatus.Capturing => "Stop Capture",
                                        CaptureStatus.Stopping => "Stopping...",
                                        _ => throw new ArgumentOutOfRangeException(nameof(x), x, null)
                                    }
                                )))
                                .OnClick(() =>
                                {
                                    if (App.state.captureStatus.value == CaptureStatus.Idle)
                                        App.state.ExecuteAction(new SetCaptureStatusAction(CaptureStatus.Starting));
                                    else if (App.state.captureStatus.value == CaptureStatus.Capturing)
                                        App.state.ExecuteAction(new SetCaptureStatusAction(CaptureStatus.Stopping));
                                }),
                            ScrollingDropdown()
                                .Style(x => x.template.SizeDelta(new Vector2(0, 60)))
                                .PreferredWidth(100)
                                .PreferredHeight(25.65f)
                                .Options(Enum.GetNames(typeof(CaptureType)))
                                .Interactable(App.state.captureStatus.SelectDynamic(x => x == CaptureStatus.Idle))
                                .BindValue(App.state.captureMode, x => (CaptureType)x, x => (int)x)
                        )
                    )
            ));
        }

        private IUnityComponentControl<HorizontalLayoutGroup> ConstructCaptureRow(CaptureState capture)
        {
            return Row().Children(
                Label()
                    .Text(capture.name.AsObservable())
                    .MinHeight(25)
                    .FlexibleWidth(true),
                Label()
                    .Text(capture.type.AsObservable())
                    .MinHeight(25)
                    .PreferredWidth(100),
                Button()
                    .Interactable(capture.uploaded.AsObservable().SelectDynamic(x => !x))
                    .PreferredWidth(100)
                    .Content(Label().Text(capture.uploaded.SelectDynamic(x => x ? "Uploaded" : "Upload")).Alignment(TextAlignmentOptions.CaplineGeoAligned))
                    .OnClick(() => UploadCapture(capture.name.value, capture.type.value, default).Forget())
            );
        }
    }
}