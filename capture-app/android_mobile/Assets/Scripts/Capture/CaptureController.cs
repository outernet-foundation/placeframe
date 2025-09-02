using System;
using System.Collections.Generic;
using System.IO;
using System.Threading;

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
        private IControl ui;
        private TaskHandle currentCaptureTask = TaskHandle.Complete;

        void Awake()
        {
            capturesApi = new CapturesApi(new Configuration { BasePath = App.state.plerionAPIBaseUrl.value });

            DefaultButtonStyle = StyleButton;
            DefaultScrollbarStyle = StyleScrollBar;
            DefaultInputFieldStyle = StyleInputField;
            DefaultTextStyle = StyleText;
            DefaultScrollRectStyle = StyleScrollRect;
            DefaultDropdownStyle = StyleDropdown;
            DefaultSliderStyle = StyleSlider;

            ui = ConstructUI(canvas);

            App.RegisterObserver(HandleCaptureStatusChanged, App.state.captureStatus);
        }

        void OnDestroy()
        {
            ui.Dispose();
            currentCaptureTask.Cancel();
        }

        private void HandleCaptureStatusChanged(NodeChangeEventArgs args)
        {
            switch (App.state.captureStatus.value)
            {
                case CaptureStatus.Idle:
                    UpdateCaptureList().Forget();
                    break;

                case CaptureStatus.Starting:
                    currentCaptureTask = TaskHandle.Execute(async token =>
                    {
                        await StartCapture(App.state.captureMode.value, token);
                        App.state.ExecuteActionOrDelay(new SetCaptureStatusAction(CaptureStatus.Capturing));
                    });
                    break;

                case CaptureStatus.Stopping:
                    currentCaptureTask = TaskHandle.Execute(async token =>
                    {
                        await StopCapture(App.state.captureMode.value, token);
                        App.state.ExecuteActionOrDelay(new SetCaptureStatusAction(CaptureStatus.Idle));
                    });
                    break;
            }
        }

        private async UniTask StopCapture(CaptureType captureType, CancellationToken cancellationToken = default)
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

        private async UniTask StartCapture(CaptureType captureType, CancellationToken cancellationToken = default)
        {
            switch (captureType)
            {
                case CaptureType.Local:
                    await LocalCaptureController.StartCapture(cancellationToken, captureIntervalSeconds);
                    break;
                case CaptureType.Zed:
                    await ZedCaptureController.StartCapture(captureIntervalSeconds, cancellationToken);
                    break;
                default:
                    throw new Exception($"Unhandled capture type {captureType}");
            }
        }

        private async UniTask UpdateCaptureList()
        {
            // var localCaptures = LocalCaptureController.GetCaptures().ToList();
            // var remoteCaptureList = await capturesApi.GetCapturesAsync(localCaptures);

            // var captureData = localCaptures.ToDictionary(x => x, x => remoteCaptureList.FirstOrDefault(y => y.Id == x));

            var captureData = new Dictionary<Guid, Model.CaptureModel>();

            for (int i = 0; i < 20; i++)
            {
                var capture = new Model.CaptureModel(Guid.NewGuid(), i.ToString());
                captureData.Add(capture.Id, capture);
            }

            App.state.captures.ExecuteActionOrDelay(
                captureData,
                (captures, state) =>
                {
                    state.SetFrom(
                        captures,
                        copy: (key, remote, local) =>
                        {
                            if (remote == null) //capture is local only
                            {
                                // local.name.value = capture;
                                local.type.value = CaptureType.Local;
                                local.uploaded.value = false;
                                return;
                            }

                            local.name.value = remote.Filename;
                            local.type.value = CaptureType.Local;
                            local.uploaded.value = true;
                        }
                    );
                }
            );
        }

        private async UniTask UploadCapture(Guid id, CaptureType type, CancellationToken cancellationToken)
        {
            var response = await capturesApi.CreateCaptureAsync(new Model.BodyCreateCapture(id: id));

            if (type == CaptureType.Zed)
            {
                var captureData = await ZedCaptureController.GetCapture(id, cancellationToken);
                await capturesApi.UploadCaptureTarAsync(response.Id, captureData, cancellationToken);
            }
            else if (type == CaptureType.Local)
            {
                var captureData = await LocalCaptureController.GetCapture(id);
                await capturesApi.UploadCaptureTarAsync(response.Id, captureData, cancellationToken);
            }

            await UpdateCaptureList();
        }

        private IControl ConstructUI(Canvas canvas)
        {
            return new Control(canvas.gameObject).Children(SafeArea().FillParent().Children(
                Image().FillParent().Color(UIResources.PanelColor),
                VerticalLayout()
                    .Style(x =>
                    {
                        x.childControlWidth.value = true;
                        x.childControlHeight.value = true;
                        x.childForceExpandWidth.value = true;
                        x.spacing.value = 10;
                        x.padding.value = new RectOffset(10, 10, 10, 10);
                    })
                    .FillParent()
                    .Children(
                        ScrollRect().Style(x => x.horizontal.value = false).FlexibleHeight(true).Children(
                            VerticalLayout().Style(x =>
                            {
                                x.childForceExpandWidth.value = true;
                                x.childControlWidth.value = true;
                                x.childControlHeight.value = true;
                                x.spacing.value = 10;
                            }).Children(
                                App.state.captures
                                    .CreateDynamic(x => ConstructCaptureRow(x.Value).WithMetadata(x.Value.name))
                                    .OrderByDynamic(x => x.metadata.AsObservable())
                            )
                        ),
                        Row().Children(
                            Button()
                                .Interactable(App.state.captureStatus.SelectDynamic(x => x == CaptureStatus.Idle || x == CaptureStatus.Capturing))
                                .Children(Text().Value(App.state.captureStatus.SelectDynamic(x =>
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
                            Dropdown()
                                .PreferredWidth(100)
                                .PreferredHeight(29.65f)
                                .Options(Enum.GetNames(typeof(CaptureType)))
                                .Interactable(App.state.captureStatus.SelectDynamic(x => x == CaptureStatus.Idle))
                                .BindValue(App.state.captureMode, x => (CaptureType)x, x => (int)x)
                        )
                    )
            ));
        }

        private IControl<LayoutProps> ConstructCaptureRow(CaptureState capture)
        {
            return Row().Children(
                EditableLabel()
                    .MinHeight(25)
                    .FlexibleWidth(true)
                    .BindValue(
                        capture.name,
                        x => IsDefaultRowLabel(x, capture.id) ? null : x,
                        x => string.IsNullOrEmpty(x) ? DefaultRowLabel(capture.id) : x
                    ),
                Text()
                    .Value(capture.type)
                    .MinHeight(25)
                    .PreferredWidth(100),
                Button()
                    .Interactable(capture.uploaded.AsObservable().SelectDynamic(x => !x))
                    .PreferredWidth(100)
                    .Children(Text().Style(x => x.style.alignment.value = TextAlignmentOptions.CaplineGeoAligned).Value(capture.uploaded.SelectDynamic(x => x ? "Uploaded" : "Upload")))
                    .OnClick(() => UploadCapture(capture.id, capture.type.value, default).Forget())
            );
        }

        private string DefaultRowLabel(Guid id)
            => $"<i>Unnamed [{id}]";

        private bool IsDefaultRowLabel(string source, Guid id)
            => source == DefaultRowLabel(id);
    }
}