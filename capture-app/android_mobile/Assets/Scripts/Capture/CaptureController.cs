using System;
using System.Collections.Generic;
using System.IO;
using System.Threading;
using System.Linq;
using System.Net.Http;

using UnityEngine;

using Cysharp.Threading.Tasks;
using PlerionApiClient.Api;
using PlerionApiClient.Model;

using FofX;
using FofX.Stateful;

using Nessle;
using Nessle.StatefulExtensions;

using ObserveThing;
using ObserveThing.StatefulExtensions;

using PlerionApiClient.Client;
using static PlerionClient.Client.UIElements;
using DeviceType = PlerionApiClient.Model.DeviceType;
using Plerion.Core;

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
        float captureIntervalSeconds = 0.2f;

        private DefaultApi capturesApi;
        private IControl ui;
        private TaskHandle currentCaptureTask = TaskHandle.Complete;

        private string localCaptureNamePath;

        private Dictionary<Guid, TaskHandle> awaitReconstructionTasks = new Dictionary<Guid, TaskHandle>();
        private IDisposable captureStatusStream;

        void Awake()
        {
            localCaptureNamePath = $"{Application.persistentDataPath}/LocalCaptureNames.json";

            capturesApi = new DefaultApi(
                new HttpClient(new KeycloakHttpHandler() { InnerHandler = new HttpClientHandler() })
                {
                    BaseAddress = new Uri(App.state.plerionAPIBaseUrl.value),
                    Timeout = TimeSpan.FromSeconds(600)
                },
                new Configuration()
                {
                    BasePath = App.state.plerionAPIBaseUrl.value,
                    Timeout = TimeSpan.FromSeconds(600)
                }
            );


            ui = ConstructUI(canvas);

            App.RegisterObserver(HandleCaptureStatusChanged, App.state.loggedIn, App.state.captureStatus);
            App.RegisterObserver(HandleCapturesChanged, App.state.captures);

            captureStatusStream = App.state.captures.AsObservable()
                .SelectDynamic(x => x.Value)
                .SubscribeEach(capture => capture.status.AsObservable().Subscribe(
                    x =>
                    {
                        if (x.currentValue != CaptureUploadStatus.Initializing &&
                            x.currentValue != CaptureUploadStatus.Uploading &&
                            x.currentValue != CaptureUploadStatus.Reconstructing &&
                            awaitReconstructionTasks.TryGetValue(capture.id, out var taskHandle))
                        {
                            taskHandle.Cancel();
                            awaitReconstructionTasks.Remove(capture.id);
                        }

                        if (x.currentValue == CaptureUploadStatus.UploadRequested)
                        {
                            UploadCapture(
                                capture.id,
                                capture.name.value ?? capture.id.ToString(),
                                capture.type.value,
                                Progress.Create<(CaptureUploadStatus, float?)>(progress => capture.status.ScheduleSet(progress.Item1))
                            ).Forget();
                        }
                        else if (x.currentValue == CaptureUploadStatus.ReconstructRequested)
                        {
                            CreateReconstruction(capture.id).Forget();
                            capture.status.ExecuteSetOrDelay(CaptureUploadStatus.Reconstructing);
                        }
                        else if (x.currentValue == CaptureUploadStatus.CreateMapRequested)
                        {
                            capturesApi.CreateLocalizationMapAsync(new LocalizationMapCreate(capture.reconstructionId.value, 0, 0, 0, 0, 0, 0, 1, 0) { Name = capture.name.value })
                                .ContinueWith(x =>
                                {
                                    capture.localizationMapId.ScheduleSet(x.Result.Id);
                                    capture.status.ScheduleSet(CaptureUploadStatus.MapCreated);
                                });
                        }
                        else if (x.currentValue == CaptureUploadStatus.Initializing ||
                            x.currentValue == CaptureUploadStatus.Uploading ||
                            x.currentValue == CaptureUploadStatus.Reconstructing)
                        {
                            if (!awaitReconstructionTasks.ContainsKey(capture.id))
                            {
                                var progress = Progress.Create<CaptureUploadStatus>(progress => capture.status.ScheduleSet(progress));

                                awaitReconstructionTasks.Add(
                                    capture.id,
                                    TaskHandle.Execute(token => AwaitReconstructionComplete(capture.id, progress, token))
                                );
                            }
                        }
                    }
                ));
        }

        void OnDestroy()
        {
            ui?.Dispose();
            currentCaptureTask?.Cancel();
            captureStatusStream?.Dispose();
        }

        private void HandleCaptureStatusChanged(NodeChangeEventArgs args)
        {
            if (!App.state.loggedIn.value)
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

        private async UniTask StopCapture(DeviceType deviceType, CancellationToken cancellationToken = default)
        {
            switch (deviceType)
            {
                case DeviceType.ARFoundation:
                    LocalCaptureController.StopCapture();
                    break;
                case DeviceType.Zed:
                    await ZedCaptureController.StopCapture(cancellationToken);
                    break;
                default:
                    throw new Exception($"Unhandled capture type {deviceType}");
            }
        }

        private async UniTask StartCapture(DeviceType deviceType, CancellationToken cancellationToken = default)
        {
            switch (deviceType)
            {
                case DeviceType.ARFoundation:
                    await LocalCaptureController.StartCapture(cancellationToken, captureIntervalSeconds);
                    break;
                case DeviceType.Zed:
                    await ZedCaptureController.StartCapture(captureIntervalSeconds, cancellationToken);
                    break;
                default:
                    throw new Exception($"Unhandled capture type {deviceType}");
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

            var remoteCaptureList = await capturesApi.GetCaptureSessionsAsync();
            var remoteCaptureReconstructions = await GetReconstructionsForCaptures(remoteCaptureList.Select(x => x.Id).ToList());
            var remoteCaptureLocalizationMaps = await capturesApi.GetLocalizationMapsAsync(reconstructionIds: remoteCaptureReconstructions.Select(x => x.Id).ToList());

            List<Guid> zedCaptures = new List<Guid>();

            try
            {
                using var cancellationTokenSource = new CancellationTokenSource(TimeSpan.FromSeconds(1));
                var captures = await ZedCaptureController.GetCaptures(cancellationTokenSource.Token);
                zedCaptures.AddRange(captures);
            }
            catch
            {
                // Handle the exception if ZedCaptureController.GetCaptures() fails
            }

            List<Guid> arFoundationCaptures = LocalCaptureController.GetCaptures().ToList();

            var captureData = remoteCaptureList.ToDictionary(
                x => x.Id,
                x =>
                {
                    var reconstruction = remoteCaptureReconstructions.FirstOrDefault(y => y.CaptureSessionId == x.Id);
                    var localizationMap = reconstruction == null ?
                        default : remoteCaptureLocalizationMaps.FirstOrDefault(y => y.ReconstructionId == reconstruction.Id);

                    return (
                        name: x.Name,
                        capture: x,
                        deviceType: x.DeviceType,
                        reconstruction,
                        localizationMap,
                        hasLocalFiles: zedCaptures.Contains(x.Id) || arFoundationCaptures.Contains(x.Id)
                    );
                }
            );

            foreach (var zedCapture in zedCaptures)
            {
                if (captureData.ContainsKey(zedCapture))
                    continue;

                captureData.Add(zedCapture, (
                    name: captureNames.TryGetValue(zedCapture, out var name) ? name : null,
                    capture: null,
                    deviceType: DeviceType.Zed,
                    reconstruction: null,
                    localizationMap: null,
                    hasLocalFiles: true
                ));
            }

            foreach (var arFoundationCapture in arFoundationCaptures)
            {
                if (captureData.ContainsKey(arFoundationCapture))
                    continue;

                captureData.Add(arFoundationCapture, (
                    name: captureNames.TryGetValue(arFoundationCapture, out var name) ? name : null,
                    capture: null,
                    deviceType: DeviceType.ARFoundation,
                    reconstruction: null,
                    localizationMap: null,
                    hasLocalFiles: true
                ));
            }

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
                            state.hasLocalFiles.value = entry.hasLocalFiles;

                            if (entry.capture == null) //capture is local only
                            {
                                state.type.value = entry.deviceType;
                                state.status.value = CaptureUploadStatus.NotUploaded;
                                return;
                            }
                            else
                            {
                                state.type.value = entry.deviceType;
                            }

                            if (entry.reconstruction == null)
                            {
                                state.status.value = CaptureUploadStatus.ReconstructionNotStarted;
                                return;
                            }

                            state.reconstructionId.value = entry.reconstruction.Id;

                            switch (entry.reconstruction.OrchestrationStatus)
                            {
                                case OrchestrationStatus.Pending:
                                case OrchestrationStatus.Queued:
                                case OrchestrationStatus.Running:
                                    state.status.value = CaptureUploadStatus.Reconstructing;
                                    break;
                                case OrchestrationStatus.Succeeded:
                                    state.status.value = CaptureUploadStatus.Uploaded;
                                    break;
                                case OrchestrationStatus.Cancelled:
                                case OrchestrationStatus.Failed:
                                    state.status.value = CaptureUploadStatus.Failed;
                                    break;
                            }

                            if (entry.localizationMap != null)
                            {
                                state.status.value = CaptureUploadStatus.MapCreated;
                                state.localizationMapId.value = entry.localizationMap.Id;
                            }
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


        private async UniTask UploadCapture(Guid id, string name, DeviceType type, IProgress<(CaptureUploadStatus, float?)> progress = default, CancellationToken cancellationToken = default)
        {
            progress?.Report((CaptureUploadStatus.Initializing, null));

            CaptureSessionRead captureSession = default;
            Stream captureData = default;

            if (type == DeviceType.Zed)
            {
                captureData = await ZedCaptureController.GetCapture(id, cancellationToken);
                captureSession = await capturesApi.CreateCaptureSessionAsync(new CaptureSessionCreate(DeviceType.Zed, name) { Id = id }).AsUniTask();
            }
            else if (type == DeviceType.ARFoundation)
            {
                try

                {
                    captureData = await LocalCaptureController.GetCapture(id);
                }
                catch (Exception e)
                {
                    Debug.LogError($"Failed to get local capture data for capture {id}: {e}");
                    throw;
                }

                try
                {
                    await UniTask.SwitchToMainThread();
                    captureSession = await capturesApi.CreateCaptureSessionAsync(new CaptureSessionCreate(DeviceType.ARFoundation, name) { Id = id }).AsUniTask();
                }
                catch (Exception e)
                {
                    Debug.LogError($"Failed to create capture session for capture {id}: {e}");
                    throw;
                }
            }

            progress?.Report((CaptureUploadStatus.Uploading, null));

            try
            {
                await capturesApi.UploadCaptureSessionTarAsync(captureSession.Id, captureData, cancellationToken: cancellationToken).AsUniTask();
                // var presignedUrl = await capturesApi.GetUploadCaptureSessionTarPresignedUrlAsync(captureSession.Id, cancellationToken);
                // var progress2 = Progress.Create<float>(p => progress?.Report((CaptureUploadStatus.Uploading, p)));
                // using (captureData)
                // {
                //     var httpClient = new HttpClient(new ProgressReportingHttpClientHandler(progress2))
                //     {
                //         Timeout = TimeSpan.FromMinutes(30)
                //     };

                //     var content = new StreamContent(captureData);
                //     content.Headers.Add("Content-Type", "application/x-tar");

                //     var response = await httpClient.PutAsync(presignedUrl, content, cancellationToken);
                //     response.EnsureSuccessStatusCode();
                // }
            }
            catch (Exception exception)
            {
                Debug.LogError($"Upload failed: {exception}");
                throw;
            }

            progress?.Report((CaptureUploadStatus.Reconstructing, null));

            await CreateReconstruction(captureSession.Id);
        }

        private async UniTask<Guid> AwaitReconstructionID(Guid captureSessionId, CancellationToken cancellationToken = default)
        {
            while (true)
            {
                var reconstructions = await capturesApi.GetCaptureSessionReconstructionsAsync(captureSessionId);
                if (reconstructions.Count > 0)
                {
                    return reconstructions[0];
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
            return new Control("root", canvas.gameObject).Setup(root => root.SingleChild(
                App.state.loggedIn.AsObservable()
                    .SelectDynamic(loggedIn =>
                    {
                        IControl screen = default;

                        if (loggedIn)
                        {
                            screen = MainAppUI().Setup(mainUI => mainUI.BindValue(x => x.mode, App.state.mode));
                        }
                        else
                        {
                            screen = LoginUI();
                        }

                        screen?.FillParent();
                        return screen;
                    })
            ));
        }

        private async UniTask CreateReconstruction(Guid captureId)
        {
            await capturesApi.CreateReconstructionAsync(new ReconstructionCreateWithOptions(new ReconstructionCreate(captureId))
            {
                Options = new ReconstructionOptions()
                {
                    NeighborsCount = 12,
                    MaxKeypointsPerImage = 2500,
                    RansacMaxError = 2.0,
                    RansacMinInlierRatio = 0.15,
                    TriangulationMinimumAngle = 3.0,
                    TriangulationCompleteMaxReprojectionError = 2.0,
                    TriangulationMergeMaxReprojectionError = 4.0,
                    MapperFilterMaxReprojectionError = 2.0,
                    UsePriorPosition = true,
                    RigVerification = true
                }
            }).AsUniTask();
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