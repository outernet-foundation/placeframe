using System;
using System.Collections.Generic;
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
using ObserveThing.StatefulExtensions;
using static Nessle.UIBuilder;
using static PlerionClient.Client.UIPresets;

namespace PlerionClient.Client
{
    public class CaptureController : MonoBehaviour
    {
        public Canvas canvas;
        [SerializeField][Range(0, 5)] float captureIntervalSeconds = 0.5f;

        private DefaultApi capturesApi;
        private IControl ui;
        private TaskHandle currentCaptureTask = TaskHandle.Complete;

        private string localCaptureNamePath => $"{Application.persistentDataPath}/LocalCaptureNames.json";

        void Awake()
        {
            capturesApi = new DefaultApi(new Configuration { BasePath = App.state.plerionAPIBaseUrl.value });

            ui = ConstructUI(canvas);

            App.RegisterObserver(HandleCaptureStatusChanged, App.state.captureStatus);
            App.RegisterObserver(HandleCapturesChanged, App.state.captures);
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

        private void HandleCapturesChanged(NodeChangeEventArgs args)
        {
            var json = new SimpleJSON.JSONObject();

            foreach (var kvp in App.state.captures.Where(x => !x.value.uploaded.value))
                json[kvp.key.ToString()] = kvp.value.name.value;

            File.WriteAllText(localCaptureNamePath, json.ToString());
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
            Dictionary<Guid, string> captureNames = new Dictionary<Guid, string>();

            if (File.Exists(localCaptureNamePath))
            {
                var data = File.ReadAllText(localCaptureNamePath);
                var json = SimpleJSON.JSONNode.Parse(data);

                foreach (var kvp in json)
                    captureNames.Add(Guid.Parse(kvp.Key), kvp.Value);
            }

            var localCaptures = LocalCaptureController.GetCaptures().ToList();
            // var remoteCaptureList = await capturesApi.GetCapturesAsync(localCaptures);

            // var captureData = localCaptures.ToDictionary(x => x, x => remoteCaptureList.FirstOrDefault(y => y.Id == x));

            var captureData = new Dictionary<Guid, Model.CaptureModel>();

            for (int i = 0; i < 20; i++)
            {
                var capture = new Model.CaptureModel(Guid.NewGuid(), i.ToString());
                captureData.Add(capture.Id, capture);
            }

            await UniTask.SwitchToMainThread();

            App.state.captures.ExecuteActionOrDelay(
                captureData,
                (captures, state) =>
                {
                    state.SetFrom(
                        captures,
                        refreshOldEntries: true,
                        copy: (key, remote, local) =>
                        {
                            if (remote == null) //capture is local only
                            {
                                local.name.value = captureNames.TryGetValue(key, out var name) ? name : null;
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

        private async UniTask UploadCapture(Guid id, string name, CaptureType type, CancellationToken cancellationToken)
        {
            var response = await capturesApi.CreateCaptureAsync(new Model.BodyCreateCapture(id: id, filename: name));

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
            return new Control("root", canvas.gameObject).Setup(root => root.Children(SafeArea().Setup(safeArea =>
            {
                safeArea.FillParent();
                safeArea.Children(
                    Image("background").Setup(background =>
                    {
                        background.FillParent();
                        background.props.color.From(new Color(0.2196079f, 0.2196079f, 0.2196079f, 1f));
                    }),
                    TightRowsWideColumns("content").Setup(content =>
                    {
                        content.props.padding.From(new RectOffset(10, 10, 10, 10));
                        content.FillParent();
                        content.Children(
                            ScrollRect("captureList").Setup(captureList =>
                            {
                                captureList.FlexibleHeight(true);
                                captureList.props.horizontal.From(false);
                                captureList.props.content.From(TightRowsWideColumns("content").Setup(content =>
                                {
                                    content.FillParentWidth();
                                    content.FitContentVertical(ContentSizeFitter.FitMode.PreferredSize);
                                    content.Children(
                                        App.state.captures
                                            .AsObservable()
                                            .CreateDynamic(x => ConstructCaptureRow(x.Value).WithMetadata(x.Value.name))
                                            .OrderByDynamic(x => x.metadata.AsObservable())
                                    );
                                }));
                            }),
                            Row("bottomBar").Setup(row => row.Children(
                                Button().Setup(button =>
                                {
                                    button.props.interactable.From(App.state.captureStatus.AsObservable().SelectDynamic(x => x == CaptureStatus.Idle || x == CaptureStatus.Capturing));

                                    button.PreferredWidth(110);
                                    button.LabelFrom(App.state.captureStatus.AsObservable().SelectDynamic(x =>
                                        x switch
                                        {
                                            CaptureStatus.Idle => "Start Capture",
                                            CaptureStatus.Starting => "Starting...",
                                            CaptureStatus.Capturing => "Stop Capture",
                                            CaptureStatus.Stopping => "Stopping...",
                                            _ => throw new ArgumentOutOfRangeException(nameof(x), x, null)
                                        }
                                    ));

                                    button.props.onClick.From(() =>
                                    {
                                        if (App.state.captureStatus.value == CaptureStatus.Idle)
                                            App.state.ExecuteAction(new SetCaptureStatusAction(CaptureStatus.Starting));
                                        else if (App.state.captureStatus.value == CaptureStatus.Capturing)
                                            App.state.ExecuteAction(new SetCaptureStatusAction(CaptureStatus.Stopping));
                                    });
                                }),
                                Dropdown().Setup(dropdown =>
                                {
                                    dropdown.PreferredWidth(100);
                                    dropdown.props.options.From(Enum.GetNames(typeof(CaptureType)));
                                    dropdown.props.interactable.From(App.state.captureStatus.AsObservable().SelectDynamic(x => x == CaptureStatus.Idle));
                                    dropdown.BindValue(App.state.captureMode, x => (CaptureType)x, x => (int)x);
                                })
                            ))
                        );
                    })
                );
            })));
        }

        private IControl<LayoutProps> ConstructCaptureRow(CaptureState capture)
        {
            return Row().Setup(row => row.Children(
                EditableLabel().Setup(editableLabel =>
                {
                    editableLabel.MinHeight(28);
                    editableLabel.FlexibleWidth(true);
                    editableLabel.BindValue(
                        capture.name,
                        x => IsDefaultRowLabel(x, capture.id) ? null : x,
                        x => string.IsNullOrEmpty(x) ? DefaultRowLabel(capture.id) : x
                    );
                }),
                Text().Setup(text =>
                {
                    text.props.text.From(capture.type.AsObservable());
                    text.MinHeight(25);
                    text.PreferredWidth(100);
                }),
                Button().Setup(button =>
                {
                    button.props.interactable.From(capture.uploaded.AsObservable().SelectDynamic(x => !x));

                    button.LabelFrom(capture.uploaded.AsObservable().SelectDynamic(x => x ? "Uploaded" : "Upload"));
                    button.PreferredWidth(100);
                    button.props.onClick.From(() =>
                        UploadCapture(capture.id, capture.name.value ?? capture.id.ToString(), capture.type.value, default).Forget()
                    );
                })
            ));
        }

        private string DefaultRowLabel(Guid id)
            => $"<i>Unnamed [{id}]";

        private bool IsDefaultRowLabel(string source, Guid id)
            => source == DefaultRowLabel(id);
    }
}