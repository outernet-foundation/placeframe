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
using PlerionClient.Model;

using FofX;
using FofX.Stateful;

using Nessle;
using Nessle.StatefulExtensions;

using ObserveThing;
using ObserveThing.StatefulExtensions;

using static Nessle.UIBuilder;
using static PlerionClient.Client.UIPresets;
using System.Net.Http;
using UnityEngine.SocialPlatforms;

namespace PlerionClient.Client
{
    public class KeycloakHttpHandler : DelegatingHandler
    {
        protected override async System.Threading.Tasks.Task<HttpResponseMessage> SendAsync(
            HttpRequestMessage request, CancellationToken cancellationToken)
        {
            var token = await Auth.GetOrRefreshToken();
            request.Headers.Authorization = new System.Net.Http.Headers.AuthenticationHeaderValue("Bearer", token);
            return await base.SendAsync(request, cancellationToken);
        }
    }

    public class CaptureController : MonoBehaviour
    {
        public Canvas canvas;
        [SerializeField][Range(0, 5)] float captureIntervalSeconds = 0.2f;

        private DefaultApi capturesApi;
        private IControl ui;
        private TaskHandle currentCaptureTask = TaskHandle.Complete;

        private string localCaptureNamePath;

        void Awake()
        {
            localCaptureNamePath = $"{Application.persistentDataPath}/LocalCaptureNames.json";

            capturesApi = new DefaultApi(
                new HttpClient(new KeycloakHttpHandler() { InnerHandler = new HttpClientHandler() })
                {
                    BaseAddress = new Uri(App.state.plerionAPIBaseUrl.value)
                },
                App.state.plerionAPIBaseUrl.value
            );

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

            foreach (var kvp in App.state.captures.Where(x => x.value.status.value == CaptureUploadStatus.NotUploaded))
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
            var remoteCaptureList = await capturesApi.GetCaptureSessionsAsync(localCaptures);

            var captureData = localCaptures.ToDictionary(x => x, x => remoteCaptureList.FirstOrDefault(y => y.Id == x));

            // var captureData = new Dictionary<Guid, CaptureSessionCreate>();

            // for (int i = 0; i < 20; i++)
            // {
            //     var id = Guid.NewGuid();
            //     var capture = new CaptureSessionCreate(Model.DeviceType.ARFoundation, i.ToString()) { Id = id };
            //     captureData.Add(id, capture);
            // }

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
                                local.status.value = CaptureUploadStatus.NotUploaded;
                                return;
                            }

                            local.name.value = remote.Name;
                            local.type.value = CaptureType.Local;
                            local.status.value = CaptureUploadStatus.Uploaded;
                        }
                    );
                }
            );
        }

        private async UniTask UploadCapture(Guid id, string name, CaptureType type, IProgress<CaptureUploadStatus> progress = default, CancellationToken cancellationToken = default)
        {
            progress?.Report(CaptureUploadStatus.Initializing);

            CaptureSessionRead captureSession = default;
            Stream captureData = default;

            if (type == CaptureType.Zed)
            {
                await UniTask.WhenAll(
                    capturesApi.CreateCaptureSessionAsync(new CaptureSessionCreate(Model.DeviceType.Zed, name) { Id = id }).AsUniTask().ContinueWith(x => captureSession = x),
                    ZedCaptureController.GetCapture(id, cancellationToken).ContinueWith(x => captureData = x)
                );
            }
            else if (type == CaptureType.Local)
            {
                await UniTask.WhenAll(
                    capturesApi.CreateCaptureSessionAsync(new CaptureSessionCreate(Model.DeviceType.ARFoundation, name) { Id = id }).AsUniTask().ContinueWith(x => captureSession = x),
                    LocalCaptureController.GetCapture(id).ContinueWith(x => captureData = x)
                );
            }

            progress?.Report(CaptureUploadStatus.Uploading);

            await capturesApi.UploadCaptureSessionTarAsync(captureSession.Id, captureData, cancellationToken);

            progress?.Report(CaptureUploadStatus.Reconstructing);

            var reconstruction = await capturesApi.CreateReconstructionAsync(new ReconstructionCreate(captureSession.Id), cancellationToken);

            while (true)
            {
                var status = await capturesApi.GetReconstructionStatusAsync(reconstruction.Id, cancellationToken);

                if (status == "\"succeeded\"")
                    break;

                if (status == "\"failed\"" || status == "\"exited\"")
                {
                    progress?.Report(CaptureUploadStatus.Failed);
                    throw new Exception("Capture reconstruction failed.");
                }

                await UniTask.WaitForSeconds(10, cancellationToken: cancellationToken);
            }

            progress?.Report(CaptureUploadStatus.Uploaded);

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
                        background.props.color.From(new UnityEngine.Color(0.2196079f, 0.2196079f, 0.2196079f, 1f));
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

                    editableLabel.props.label.style.verticalAlignment.From(VerticalAlignmentOptions.Capline);
                    editableLabel.props.inputField.placeholderText.text.From(DefaultRowLabel(capture.id));
                    editableLabel.props.inputField.onEndEdit.From(x => capture.name.ExecuteSetOrDelay(x));
                    editableLabel.AddBinding(capture.name.AsObservable().Subscribe(x => editableLabel.props.inputField.inputText.text.From(x.currentValue)));
                }),
                Text().Setup(text =>
                {
                    text.props.text.From(capture.type.AsObservable());
                    text.props.style.verticalAlignment.From(VerticalAlignmentOptions.Capline);
                    text.MinHeight(25);
                    text.PreferredWidth(100);
                }),
                Button().Setup(button =>
                {
                    button.props.interactable.From(capture.status.AsObservable().SelectDynamic(x => x == CaptureUploadStatus.NotUploaded));
                    button.LabelFrom(capture.status.AsObservable().SelectDynamic(x =>
                        x switch
                        {
                            CaptureUploadStatus.NotUploaded => "Upload",
                            CaptureUploadStatus.Initializing => "Initializing",
                            CaptureUploadStatus.Uploading => "Uploading",
                            CaptureUploadStatus.Reconstructing => "Constructing",
                            CaptureUploadStatus.Uploaded => "Uploaded",
                            CaptureUploadStatus.Failed => "Failed",
                            _ => throw new ArgumentOutOfRangeException(nameof(x), x, null)
                        }
                    ));
                    button.PreferredWidth(105);
                    button.props.onClick.From(() =>
                        UploadCapture(
                            capture.id,
                            capture.name.value ?? capture.id.ToString(),
                            capture.type.value,
                            Progress.Create<CaptureUploadStatus>(x => capture.status.ScheduleSet(x))
                        ).Forget()
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