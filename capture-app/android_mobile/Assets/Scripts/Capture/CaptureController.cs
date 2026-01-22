using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Threading;
using Cysharp.Threading.Tasks;
using FofX;
using FofX.Stateful;
using Nessle;
using ObserveThing;
using ObserveThing.StatefulExtensions;
using Plerion.Core;
using PlerionApiClient.Api;
using PlerionApiClient.Client;
using PlerionApiClient.Model;
using UnityEngine;
using static PlerionClient.Client.UIElements;
using DeviceType = PlerionApiClient.Model.DeviceType;

namespace PlerionClient.Client
{
    public class CaptureController : MonoBehaviour
    {
        private float captureIntervalSeconds = 0.2f;

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
                new HttpClient(new AuthHttpHandler() { InnerHandler = new HttpClientHandler() })
                {
                    BaseAddress = new Uri(App.state.plerionApiUrl.value),
                    Timeout = TimeSpan.FromSeconds(600),
                },
                new Configuration() { BasePath = App.state.plerionApiUrl.value, Timeout = TimeSpan.FromSeconds(600) }
            );

            ui = OrderedCanvas(
                new()
                {
                    children = Props.List(
                        App.state.loggedIn.AsObservable()
                            .CreateDynamic(loggedIn =>
                            {
                                IControl screen = default;
                                if (loggedIn)
                                {
                                    screen = MainAppUI(
                                        new MainAppUIProps()
                                        {
                                            mode = App.state.mode.AsObservable(),
                                            onModeChanged = x => App.state.mode.ExecuteSetOrDelay(x),
                                        }
                                    );
                                }
                                else
                                {
                                    screen = LoginUI();
                                }

                                return screen;
                            })
                    ),
                }
            );

            App.RegisterObserver(HandleCaptureStatusChanged, App.state.loggedIn, App.state.captureStatus);
            App.RegisterObserver(HandleCapturesChanged, App.state.captures);

            captureStatusStream = App
                .state.captures.AsObservable()
                .SelectDynamic(x => x.Value)
                .SubscribeEach(capture =>
                    capture
                        .status.AsObservable()
                        .Subscribe(x =>
                        {
                            if (
                                x.currentValue != CaptureUploadStatus.Initializing
                                && x.currentValue != CaptureUploadStatus.Uploading
                                && x.currentValue != CaptureUploadStatus.Reconstructing
                                && awaitReconstructionTasks.TryGetValue(capture.id, out var taskHandle)
                            )
                            {
                                taskHandle.Cancel();
                                awaitReconstructionTasks.Remove(capture.id);
                            }

                            if (x.currentValue == CaptureUploadStatus.UploadRequested)
                            {
                                ReconstructionOptionsDialog(
                                    new ReconstructionOptionsDialogProps()
                                    {
                                        capture = capture,
                                        options = LoadOrCreateReconstructionOptions(),
                                        onDialogComplete = reconstructionOptions =>
                                        {
                                            SaveReconstructionOptions(reconstructionOptions);
                                            UploadCapture(
                                                    capture,
                                                    reconstructionOptions,
                                                    Progress.Create<(CaptureUploadStatus, float?)>(progress =>
                                                        capture.status.ScheduleSet(progress.Item1)
                                                    )
                                                )
                                                .Forget();
                                        },
                                        onDialogCancelled = () =>
                                            capture.status.ExecuteSetOrDelay(CaptureUploadStatus.NotUploaded),
                                    }
                                );

                                return;
                            }
                            else if (x.currentValue == CaptureUploadStatus.ReconstructRequested)
                            {
                                ReconstructionOptionsDialog(
                                    new ReconstructionOptionsDialogProps()
                                    {
                                        capture = capture,
                                        onDialogComplete = reconstructionOptions =>
                                        {
                                            CreateReconstruction(capture.id, reconstructionOptions).Forget();

                                            capture.status.ExecuteSetOrDelay(CaptureUploadStatus.Reconstructing);
                                        },
                                        onDialogCancelled = () =>
                                            capture.status.ExecuteSetOrDelay(
                                                CaptureUploadStatus.ReconstructionNotStarted
                                            ),
                                    }
                                );

                                return;
                            }
                            else if (x.currentValue == CaptureUploadStatus.CreateMapRequested)
                            {
                                capturesApi
                                    .CreateLocalizationMapAsync(
                                        new LocalizationMapCreate(
                                            capture.reconstructionId.value,
                                            0,
                                            0,
                                            0,
                                            0,
                                            0,
                                            0,
                                            1,
                                            0
                                        )
                                        {
                                            Name = capture.name.value,
                                        }
                                    )
                                    .ContinueWith(x =>
                                    {
                                        capture.localizationMapId.ScheduleSet(x.Result.Id);
                                        capture.status.ScheduleSet(CaptureUploadStatus.MapCreated);
                                    });
                            }
                            else if (x.currentValue == CaptureUploadStatus.Reconstructing)
                            {
                                if (!awaitReconstructionTasks.ContainsKey(capture.id))
                                {
                                    var progress = Progress.Create<CaptureUploadStatus>(progress =>
                                        capture.status.ScheduleSet(progress)
                                    );

                                    awaitReconstructionTasks.Add(
                                        capture.id,
                                        TaskHandle.Execute(token =>
                                            AwaitReconstructionComplete(capture.id, progress, token)
                                        )
                                    );
                                }
                            }
                        })
                );
        }

        private void SaveReconstructionOptions(ReconstructionOptions reconstructionOptions)
        {
            File.WriteAllText(
                Path.Join(Application.persistentDataPath, "reconstructionOptions.json"),
                reconstructionOptions.ToJson()
            );
        }

        private ReconstructionOptions LoadOrCreateReconstructionOptions()
        {
            var path = Path.Join(Application.persistentDataPath, "reconstructionOptions.json");

            if (!File.Exists(path))
            {
                return new ReconstructionOptions()
                {
                    NeighborsCount = 12,
                    RansacMaxError = 2.0,
                    RansacMinInlierRatio = 0.15,
                    TriangulationMinimumAngle = 3.0,
                    TriangulationCompleteMaxReprojectionError = 2.0,
                    TriangulationMergeMaxReprojectionError = 4.0,
                    MapperFilterMaxReprojectionError = 2.0,
                    UsePriorPosition = true,
                    RigVerification = true,
                };
            }

            var json = File.ReadAllText(path);
            return Newtonsoft.Json.JsonConvert.DeserializeObject<ReconstructionOptions>(json);
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
                    await LocalCaptureController.StopCapture();
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
                    await LocalCaptureController.StartCapture(captureIntervalSeconds, cancellationToken);
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
            var remoteCaptureReconstructions = await GetReconstructionsForCaptures(
                remoteCaptureList.Select(x => x.Id).ToList()
            );

            List<ReconstructionManifest> remoteCaptureReconstructionManifests = default;
            List<LocalizationMapRead> remoteCaptureLocalizationMaps = default;

            await UniTask.WhenAll(
                GetReconstructionManifests(remoteCaptureReconstructions.Select(x => x.Id).ToList())
                    .ContinueWith(x => remoteCaptureReconstructionManifests = x),
                capturesApi
                    .GetLocalizationMapsAsync(
                        reconstructionIds: remoteCaptureReconstructions
                            .Where(x => x.OrchestrationStatus == OrchestrationStatus.Succeeded)
                            .Select(x => x.Id)
                            .ToList()
                    )
                    .AsUniTask()
                    .ContinueWith(x => remoteCaptureLocalizationMaps = x)
            );

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
                    var reconstructionManifest = remoteCaptureReconstructionManifests.FirstOrDefault(y =>
                        y.CaptureId == x.Id.ToString()
                    );
                    var localizationMap =
                        reconstruction == null
                            ? default
                            : remoteCaptureLocalizationMaps.FirstOrDefault(y =>
                                y.ReconstructionId == reconstruction.Id
                            );

                    return (
                        name: x.Name,
                        capture: x,
                        deviceType: x.DeviceType,
                        reconstruction,
                        localizationMap,
                        hasLocalFiles: zedCaptures.Contains(x.Id) || arFoundationCaptures.Contains(x.Id),
                        reconstructionManifest: reconstructionManifest
                    );
                }
            );

            foreach (var zedCapture in zedCaptures)
            {
                if (captureData.ContainsKey(zedCapture))
                    continue;

                captureData.Add(
                    zedCapture,
                    (
                        name: captureNames.TryGetValue(zedCapture, out var name) ? name : null,
                        capture: null,
                        deviceType: DeviceType.Zed,
                        reconstruction: null,
                        localizationMap: null,
                        hasLocalFiles: true,
                        reconstructionManifest: null
                    )
                );
            }

            foreach (var arFoundationCapture in arFoundationCaptures)
            {
                if (captureData.ContainsKey(arFoundationCapture))
                    continue;

                captureData.Add(
                    arFoundationCapture,
                    (
                        name: captureNames.TryGetValue(arFoundationCapture, out var name) ? name : null,
                        capture: null,
                        deviceType: DeviceType.ARFoundation,
                        reconstruction: null,
                        localizationMap: null,
                        hasLocalFiles: true,
                        reconstructionManifest: null
                    )
                );
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
                            state.manifest.value = entry.reconstructionManifest;

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

            await UniTask.WhenAll(
                captures.Select(x =>
                    capturesApi
                        .GetReconstructionsAsync(captureSessionId: x)
                        .AsUniTask()
                        .ContinueWith(x => result.AddRange(x))
                )
            );

            return result;
        }

        private async UniTask<List<ReconstructionManifest>> GetReconstructionManifests(List<Guid> reconstructions)
        {
            var result = new List<ReconstructionManifest>();

            await UniTask.WhenAll(
                reconstructions.Select(x =>
                    capturesApi
                        .GetReconstructionManifestAsync(x)
                        .AsUniTask()
                        .ContinueWith(manifest => result.Add(manifest))
                )
            );

            return result;
        }

        private async UniTask UploadCapture(
            CaptureState capture,
            ReconstructionOptions reconstructionOptions,
            IProgress<(CaptureUploadStatus, float?)> progress = default,
            CancellationToken cancellationToken = default
        )
        {
            var id = capture.id;
            var name = capture.name.value ?? capture.id.ToString();
            var type = capture.type.value;

            progress?.Report((CaptureUploadStatus.Initializing, null));

            CaptureSessionRead captureSession = default;
            Stream captureData = default;

            if (type == DeviceType.Zed)
            {
                captureData = await ZedCaptureController.GetCapture(id, cancellationToken);
                captureSession = await capturesApi
                    .CreateCaptureSessionAsync(new CaptureSessionCreate(DeviceType.Zed, name) { Id = id })
                    .AsUniTask();
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
                    captureSession = await capturesApi
                        .CreateCaptureSessionAsync(new CaptureSessionCreate(DeviceType.ARFoundation, name) { Id = id })
                        .AsUniTask();
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
                await capturesApi
                    .UploadCaptureSessionTarAsync(captureSession.Id, captureData, cancellationToken: cancellationToken)
                    .AsUniTask();
            }
            catch (Exception exception)
            {
                Debug.LogError($"Upload failed: {exception}");
                throw;
            }

            progress?.Report((CaptureUploadStatus.Reconstructing, null));

            capture.status.ExecuteSetOrDelay(CaptureUploadStatus.Reconstructing);

            await CreateReconstruction(captureSession.Id, reconstructionOptions);
        }

        private async UniTask<Guid> AwaitReconstructionID(
            Guid captureSessionId,
            CancellationToken cancellationToken = default
        )
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

        private async UniTask AwaitReconstructionComplete(
            Guid captureSessionId,
            IProgress<CaptureUploadStatus> progress = default,
            CancellationToken cancellationToken = default
        )
        {
            var reconstructionId = await AwaitReconstructionID(captureSessionId, cancellationToken);

            //HACK: Pushing directly to state for convenience
            App.state.captures[captureSessionId].reconstructionId.ScheduleSet(reconstructionId);

            progress?.Report(CaptureUploadStatus.Reconstructing);

            while (true)
            {
                var status = await capturesApi.GetReconstructionStatusAsync(reconstructionId, cancellationToken);

                if (status == OrchestrationStatus.Succeeded)
                    break;

                if (status == OrchestrationStatus.Failed || status == OrchestrationStatus.Cancelled)
                {
                    progress?.Report(CaptureUploadStatus.Failed);
                    throw new Exception("Capture reconstruction failed.");
                }

                await UniTask.WaitForSeconds(10, cancellationToken: cancellationToken);
            }

            progress?.Report(CaptureUploadStatus.Uploaded);

            await UpdateCaptureList();
        }

        private async UniTask CreateReconstruction(Guid captureId, ReconstructionOptions reconstructionOptions)
        {
            await capturesApi
                .CreateReconstructionAsync(
                    new ReconstructionCreateWithOptions(new ReconstructionCreate(captureId))
                    {
                        Options = reconstructionOptions,
                    }
                )
                .AsUniTask();
        }
    }
}
