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

using Color = UnityEngine.Color;

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

        private IDisposable awaitReconstructionTasksStream;
        private Dictionary<Guid, TaskHandle> awaitReconstructionTasks = new Dictionary<Guid, TaskHandle>();

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

            awaitReconstructionTasksStream = App.state.captures
                .AsObservable()
                .WhereDynamic(x => x.Value.status
                    .AsObservable()
                    .SelectDynamic(x =>
                        x == CaptureUploadStatus.Initializing ||
                        x == CaptureUploadStatus.Uploading ||
                        x == CaptureUploadStatus.Reconstructing
                    )
                )
                .Subscribe(
                    observer: x =>
                    {
                        if (x.operationType == OpType.Add)
                        {
                            var progress = Progress.Create<CaptureUploadStatus>(progress => x.element.Value.status.ScheduleSet(progress));

                            awaitReconstructionTasks.Add(
                                x.element.Key,
                                TaskHandle.Execute(token => AwaitReconstructionComplete(x.element.Key, progress, token))
                            );
                        }
                        else if (awaitReconstructionTasks.TryGetValue(x.element.Key, out var taskHandle))
                        {
                            taskHandle.Cancel();
                            awaitReconstructionTasks.Remove(x.element.Key);
                        }
                    },
                    onDispose: () =>
                    {
                        foreach (var taskHandle in awaitReconstructionTasks.Values)
                            taskHandle.Cancel();

                        awaitReconstructionTasks.Clear();
                    }
                );
        }

        void OnDestroy()
        {
            ui.Dispose();
            currentCaptureTask.Cancel();
            awaitReconstructionTasksStream.Dispose();
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
            var remoteCaptureList = await capturesApi.GetCaptureSessionsAsync();
            var remoteCaptureReconstructions = await GetReconstructionsForCaptures(remoteCaptureList.Select(x => x.Id).ToList());
            var remoteCaptureLocalizationMaps = await capturesApi.GetLocalizationMapsAsync(reconstructionIds: remoteCaptureReconstructions.Select(x => x.Id).ToList());

            var captureData = remoteCaptureList.ToDictionary(
                x => x.Id,
                x =>
                {
                    var reconstruction = remoteCaptureReconstructions.FirstOrDefault(y => y.CaptureSessionId == x.Id);
                    var localizationMap = reconstruction == null ? default : remoteCaptureLocalizationMaps.FirstOrDefault(y => y.ReconstructionId == reconstruction.Id);

                    return (name: x.Name, capture: x, reconstruction, localizationMap);
                }
            );

            foreach (var localCapture in localCaptures)
            {
                if (captureData.ContainsKey(localCapture))
                    continue;

                captureData.Add(localCapture, new(captureNames.TryGetValue(localCapture, out var name) ? name : null, null, null, null));
            }

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
                (captureData, state) =>
                {
                    state.SetFrom(
                        captureData,
                        refreshOldEntries: true,
                        copy: (key, entry, state) =>
                        {
                            state.name.value = entry.name;
                            state.type.value = CaptureType.Local;

                            if (entry.capture == null) //capture is local only
                            {
                                state.status.value = CaptureUploadStatus.NotUploaded;
                                return;
                            }

                            if (entry.reconstruction == null)
                            {
                                state.status.value = CaptureUploadStatus.ReconstructionNotStarted;
                                return;
                            }

                            state.reconstructionId.value = entry.reconstruction.Id;

                            switch (entry.reconstruction.Status)
                            {
                                case ReconstructionStatus.Pending:
                                case ReconstructionStatus.Queued:
                                case ReconstructionStatus.Running:
                                    state.status.value = CaptureUploadStatus.Reconstructing;
                                    break;
                                case ReconstructionStatus.Succeeded:
                                    state.status.value = CaptureUploadStatus.Uploaded;
                                    break;
                                case ReconstructionStatus.Cancelled:
                                case ReconstructionStatus.Failed:
                                    state.status.value = CaptureUploadStatus.Failed;
                                    break;
                            }

                            if (entry.localizationMap != null)
                                state.localizationMapId.value = entry.localizationMap.Id;
                        }
                    );
                }
            );
        }

        private async UniTask<List<ReconstructionRead>> GetReconstructionsForCaptures(List<Guid> captures)
        {
            var result = new List<ReconstructionRead>();

            await UniTask.WhenAll(captures.Select(x => capturesApi
                    .GetReconstructionsAsync(captureSessionId: x).AsUniTask()
                    .ContinueWith(x => result.AddRange(x))
            ));

            return result;
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

            await capturesApi.CreateReconstructionAsync(new ReconstructionCreate(captureSession.Id), cancellationToken);
        }

        private async UniTask<Guid> AwaitReconstructionID(Guid captureSessionId, CancellationToken cancellationToken = default)
        {
            while (true)
            {
                try
                {
                    var reconstructions = await capturesApi.GetCaptureSessionReconstructionsAsync(captureSessionId);
                    return reconstructions[0];
                }
                catch (Exception exc)
                {
                    Log.Error(LogGroup.Default, exc, $"Encountered an error getting reconstruction for capture session {captureSessionId}");
                }

                await UniTask.WaitForSeconds(10, cancellationToken: cancellationToken);
            }
        }

        private async UniTask AwaitReconstructionComplete(Guid captureSessionId, IProgress<CaptureUploadStatus> progress = default, CancellationToken cancellationToken = default)
        {
            var reconstructionId = await AwaitReconstructionID(captureSessionId, cancellationToken);

            //HACK: Pushing directly to state for convenience
            App.state.captures[captureSessionId].reconstructionId.ScheduleSet(reconstructionId);

            progress?.Report(CaptureUploadStatus.Reconstructing);

            while (true)
            {
                var status = await capturesApi.GetReconstructionStatusAsync(reconstructionId, cancellationToken);

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
            return new Control("root", canvas.gameObject).Setup(root => root.Children(
                Image("background").Setup(background =>
                {
                    background.FillParent();
                    background.props.color.From(new Color(0.2196079f, 0.2196079f, 0.2196079f, 1f));
                }),
                SafeArea().Setup(safeArea => safeArea.Children(TightRowsWideColumns("content").Setup(content =>
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
                })))
            ));
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
                    button.props.interactable.From(Observables.Combine(
                        capture.status.AsObservable(),
                        capture.localizationMapId.AsObservable(),
                        (uploadStatus, localizationMapId) =>
                        {
                            if (localizationMapId != Guid.Empty)
                                return false;

                            return uploadStatus == CaptureUploadStatus.NotUploaded ||
                                uploadStatus == CaptureUploadStatus.ReconstructionNotStarted ||
                                uploadStatus == CaptureUploadStatus.Uploaded;
                        }
                    ));

                    button.LabelFrom(Observables.Combine(
                        capture.status.AsObservable(),
                        capture.localizationMapId.AsObservable(),
                        (uploadStatus, localizationMapId) =>
                        {
                            if (localizationMapId != Guid.Empty)
                                return "Map Created";

                            return uploadStatus switch
                            {
                                CaptureUploadStatus.NotUploaded => "Upload",
                                CaptureUploadStatus.ReconstructionNotStarted => "Reconstruct",
                                CaptureUploadStatus.Initializing => "Initializing",
                                CaptureUploadStatus.Uploading => "Uploading",
                                CaptureUploadStatus.Reconstructing => "Constructing",
                                CaptureUploadStatus.Uploaded => "Create Map",
                                CaptureUploadStatus.Failed => "Failed",
                                _ => throw new ArgumentOutOfRangeException(nameof(uploadStatus), uploadStatus, null)
                            };
                        }
                    ));

                    button.PreferredWidth(106);
                    button.props.onClick.From(() =>
                    {
                        if (capture.status.value == CaptureUploadStatus.NotUploaded)
                        {
                            UploadCapture(
                                capture.id,
                                capture.name.value ?? capture.id.ToString(),
                                capture.type.value,
                                Progress.Create<CaptureUploadStatus>(x => capture.status.ScheduleSet(x))
                            ).Forget();
                        }
                        else if (capture.status.value == CaptureUploadStatus.ReconstructionNotStarted)
                        {
                            capturesApi.CreateReconstructionAsync(new ReconstructionCreate(capture.id));
                            capture.status.ExecuteSetOrDelay(CaptureUploadStatus.Reconstructing);
                        }
                        else if (capture.status.value == CaptureUploadStatus.Uploaded)
                        {
                            CreateLocalizationMapAndAssignId(capture).Forget();
                        }
                    });
                })
            ));
        }

        private async UniTask CreateLocalizationMapAndAssignId(CaptureState capture)
        {
            var localizationMap = await capturesApi.CreateLocalizationMapAsync(new LocalizationMapCreate(
                capture.reconstructionId.value,
                positionX: 0,
                positionY: 0,
                positionZ: 0,
                rotationX: 0,
                rotationY: 0,
                rotationZ: 0,
                rotationW: 1,
                color: 0
            ));

            await UniTask.SwitchToMainThread();

            capture.localizationMapId.ExecuteSetOrDelay(localizationMap.Id);
        }

        private string DefaultRowLabel(Guid id)
            => $"<i>Unnamed [{id}]";

        private bool IsDefaultRowLabel(string source, Guid id)
            => source == DefaultRowLabel(id);
    }
}