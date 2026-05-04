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
using Placeframe.Core;
using PlaceframeApiClient.Api;
using PlaceframeApiClient.Client;
using PlaceframeApiClient.Model;
using Unity.VisualScripting;
using UnityEngine;
using UnityEngine.XR;
using static Placeframe.Client.UIElements;
using DeviceType = PlaceframeApiClient.Model.DeviceType;

namespace Placeframe.Client
{
    public class CaptureController : MonoBehaviour
    {
        private float captureIntervalSeconds = 0.2f;

        // private DefaultApi capturesApi;
        private IControl ui;
        private TaskHandle currentCaptureTask = TaskHandle.Complete;
        private bool capturesLoaded;

        private string localCaptureNamePath;

        private Dictionary<Guid, TaskHandle> awaitReconstructionTasks = new Dictionary<Guid, TaskHandle>();
        private IDisposable captureStatusStream;

        private IDisposable _subscription;

        public static UniTask DeleteCapture(Guid id, DeviceType type)
        {
            if (type == DeviceType.ARFoundation)
            {
                CaptureManager.DeleteCapture(id);
                return UniTask.CompletedTask;
            }
            return ZedCaptureController.DeleteCapture(id);
        }

        public static void RequestUpload(CaptureState capture)
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
                                    capture.status.value = progress.Item1
                                )
                            )
                            .Forget(exception => capture.status.value = CaptureUploadStatus.Failed);
                    },
                }
            );
        }

        public static void RequestReconstruct(CaptureState capture)
        {
            ReconstructionOptionsDialog(
                new ReconstructionOptionsDialogProps()
                {
                    capture = capture,
                    onDialogComplete = reconstructionOptions =>
                    {
                        CreateReconstruction(capture.id, reconstructionOptions).Forget();
                        capture.status.value = CaptureUploadStatus.Reconstructing;
                    },
                }
            );
        }

        public static void RequestCreateMap(CaptureState capture)
        {
            VisualPositioningSystem.Api
                .CreateLocalizationMapAsync(
                    new LocalizationMapCreate(
                        capture.reconstructionId.value, 0, 0, 0, 0, 0, 0, 1, 0
                    )
                    {
                        Name = capture.name.value,
                    }
                )
                .ContinueWith(x =>
                {
                    capture.localizationMapId.value = x.Result.Id;
                    capture.status.value = CaptureUploadStatus.MapCreated;
                });
        }

        void Awake()
        {
            ZedCaptureController.Initialize();

            localCaptureNamePath = $"{Application.persistentDataPath}/LocalCaptureNames.json";

            // var placeframeApiUrl = $"https://{App.state.domain.value}";
            // capturesApi = new DefaultApi(
            //     new HttpClient(new AuthHttpHandler() { InnerHandler = new HttpClientHandler() })
            //     {
            //         BaseAddress = new Uri(placeframeApiUrl),
            //         Timeout = TimeSpan.FromSeconds(600),
            //     },
            //     new Configuration() { BasePath = placeframeApiUrl, Timeout = TimeSpan.FromSeconds(600) }
            // );

            ui = OrderedCanvas(
                new()
                {
                    children = Props.List(
                        App.state.loggedIn
                            .ObservableCreate(loggedIn =>
                            {
                                IControl screen = default;
                                if (loggedIn)
                                {
                                    screen = MainAppUI(
                                        new MainAppUIProps()
                                        {
                                            mode = App.state.mode,
                                            onModeChanged = x => App.state.mode.value = x,
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

            _subscription = new ComposedDisposable(
                StateObservables.SubscribeOperations(HandleCaptureStatusChanged, App.state.loggedIn, App.state.captureStatus),
                App.state.captures.SubscribeOperations(HandleCapturesChanged)
            );

            captureStatusStream = App
                .state.captures
                .ObservableSelect(x => x.Value)
                .SubscribeEach(capture =>
                    capture
                        .status
                        .Subscribe(x =>
                        {
                            if (
                                x != CaptureUploadStatus.Initializing
                                && x != CaptureUploadStatus.Uploading
                                && x != CaptureUploadStatus.Reconstructing
                                && awaitReconstructionTasks.TryGetValue(capture.id, out var taskHandle)
                            )
                            {
                                taskHandle.Cancel();
                                awaitReconstructionTasks.Remove(capture.id);
                            }

                            if (x == CaptureUploadStatus.Reconstructing
                                && !awaitReconstructionTasks.ContainsKey(capture.id))
                            {
                                var progress = Progress.Create<CaptureUploadStatus>(progress =>
                                    capture.status.value = progress
                                );

                                awaitReconstructionTasks.Add(
                                    capture.id,
                                    TaskHandle.Execute(token =>
                                        AwaitReconstructionComplete(capture.id, progress, token)
                                    )
                                );
                            }
                        })
                );
        }

        private static void SaveReconstructionOptions(ReconstructionOptions reconstructionOptions)
        {
            File.WriteAllText(
                Path.Join(Application.persistentDataPath, "reconstructionOptions.json"),
                reconstructionOptions.ToJson()
            );
        }

        private static ReconstructionOptions LoadOrCreateReconstructionOptions()
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

        private void HandleCaptureStatusChanged(IReadOnlyList<IStateOperation> ops)
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
                        App.ExecuteTransaction(new SetCaptureStatusAction(CaptureStatus.Capturing));
                    });
                    break;

                case CaptureStatus.Stopping:
                    currentCaptureTask = TaskHandle.Execute(async token =>
                    {
                        await StopCapture(App.state.captureMode.value, token);
                        App.ExecuteTransaction(new SetCaptureStatusAction(CaptureStatus.Idle));
                    });
                    break;
            }
        }

        private void HandleCapturesChanged(IReadOnlyList<IStateOperation> ops)
        {
            if (!capturesLoaded)
                return;

            var json = new SimpleJSON.JSONObject();

            foreach (var kvp in App.state.captures.Where(x => x.Value.status.value == CaptureUploadStatus.NotUploaded))
                json[kvp.Key.ToString()] = kvp.Value.name.value;

            File.WriteAllText(localCaptureNamePath, json.ToString());
        }

        private async UniTask StopCapture(DeviceType deviceType, CancellationToken cancellationToken = default)
        {
            switch (deviceType)
            {
                case DeviceType.ARFoundation:
                    CaptureManager.StopCapture();
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
                    CaptureManager.StartCapture(captureIntervalSeconds);
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

            var remoteCaptureList = await VisualPositioningSystem.Api.GetCaptureSessionsAsync();
            var remoteCaptureReconstructions = await GetReconstructionsForCaptures(
                remoteCaptureList.Select(x => x.Id).ToList()
            );

            List<ReconstructionManifest> remoteCaptureReconstructionManifests = default;
            List<LocalizationMapRead> remoteCaptureLocalizationMaps = default;

            await UniTask.WhenAll(
                GetReconstructionManifests(remoteCaptureReconstructions.Select(x => x.Id).ToList())
                    .ContinueWith(x => remoteCaptureReconstructionManifests = x),
                VisualPositioningSystem.Api
                    .GetLocalizationMapsAsync(
                        reconstructionIds: remoteCaptureReconstructions
                            .Where(x => x.OrchestrationStatus == OrchestrationStatus.Succeeded)
                            .Select(x => x.Id)
                            .ToList()
                    )
                    .AsUniTask()
                    .ContinueWith(x => remoteCaptureLocalizationMaps = x)
            );

            Dictionary<Guid, DateTime> zedCaptures = new Dictionary<Guid, DateTime>();

            try
            {
                using var cancellationTokenSource = new CancellationTokenSource(TimeSpan.FromSeconds(1));
                var captures = await ZedCaptureController.GetCaptures(cancellationTokenSource.Token);
                foreach (var capture in captures)
                    zedCaptures[capture.Id] = capture.RecordedAt;
            }
            catch
            {
                // Handle the exception if ZedCaptureController.GetCaptures() fails
            }

            List<Guid> arFoundationCaptures = CaptureManager.GetCaptures().ToList();

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
                        hasLocalFiles: zedCaptures.ContainsKey(x.Id) || arFoundationCaptures.Contains(x.Id),
                        reconstructionManifest: reconstructionManifest,
                        recordedAt: x.RecordedAt
                    );
                }
            );

            foreach (var (zedCaptureId, zedCaptureRecordedAt) in zedCaptures)
            {
                if (captureData.ContainsKey(zedCaptureId))
                    continue;

                captureData.Add(
                    zedCaptureId,
                    (
                        name: captureNames.TryGetValue(zedCaptureId, out var name) ? name : null,
                        capture: null,
                        deviceType: DeviceType.Zed,
                        reconstruction: null,
                        localizationMap: null,
                        hasLocalFiles: true,
                        reconstructionManifest: null,
                        recordedAt: zedCaptureRecordedAt
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
                        reconstructionManifest: null,
                        recordedAt: CaptureManager.GetCaptureRecordedAtUtc(arFoundationCapture)
                    )
                );
            }

            await UniTask.SwitchToMainThread();

            App.ExecuteTransaction(appState =>
            {
                var state = appState.captures;
                state.SetFrom(
                    captureData,
                    refreshOldEntries: true,
                    copy: (key, entry, state) =>
                    {
                        state.name.value = entry.name;
                        state.hasLocalFiles.value = entry.hasLocalFiles;
                        state.manifest.value = entry.reconstructionManifest;
                        state.recordedAt.value = entry.recordedAt;
                        state.type.value = entry.deviceType;

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
            });

            capturesLoaded = true;
        }

        private async UniTask<List<ReconstructionRead>> GetReconstructionsForCaptures(List<Guid> captures)
        {
            var result = new List<ReconstructionRead>();

            await UniTask.WhenAll(
                captures.Select(x =>
                    VisualPositioningSystem.Api
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
                    VisualPositioningSystem.Api
                        .GetReconstructionManifestAsync(x)
                        .AsUniTask()
                        .ContinueWith(manifest => result.Add(manifest))
                )
            );

            return result;
        }

        private static async UniTask UploadCapture(
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
                captureSession = await VisualPositioningSystem.Api
                    .CreateCaptureSessionAsync(new CaptureSessionCreate(DeviceType.Zed, name) { Id = id, RecordedAt = capture.recordedAt.value })
                    .AsUniTask();
            }
            else if (type == DeviceType.ARFoundation)
            {
                try
                {
                    captureData = await CaptureManager.GetCaptureTar(id);
                }
                catch (Exception e)
                {
                    Log.Error(LogGroup.Capture, $"Failed to get local capture data for capture {id}: {e}");
                    throw;
                }

                try
                {
                    await UniTask.SwitchToMainThread();
                    captureSession = await VisualPositioningSystem.Api
                        .CreateCaptureSessionAsync(new CaptureSessionCreate(DeviceType.ARFoundation, name) { Id = id, RecordedAt = capture.recordedAt.value })
                        .AsUniTask();
                }
                catch (Exception e)
                {
                    Log.Error(LogGroup.Capture, $"Failed to create capture session for capture {id}: {e}");
                    throw;
                }
            }

            progress?.Report((CaptureUploadStatus.Uploading, null));

            try
            {
                await VisualPositioningSystem.Api
                    .UploadCaptureSessionTarAsync(captureSession.Id, captureData, cancellationToken: cancellationToken)
                    .AsUniTask();
            }
            catch (Exception exception)
            {
                Log.Error(LogGroup.Capture, $"Upload failed: {exception}");
                throw;
            }

            progress?.Report((CaptureUploadStatus.Reconstructing, null));

            capture.status.value = CaptureUploadStatus.Reconstructing;

            await CreateReconstruction(captureSession.Id, reconstructionOptions);
        }

        private async UniTask<Guid> AwaitReconstructionID(
            Guid captureSessionId,
            CancellationToken cancellationToken = default
        )
        {
            while (true)
            {
                var reconstructions = await VisualPositioningSystem.Api.GetCaptureSessionReconstructionsAsync(captureSessionId);
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
            App.state.captures[captureSessionId].reconstructionId.value = reconstructionId;

            progress?.Report(CaptureUploadStatus.Reconstructing);

            while (true)
            {
                var status = await VisualPositioningSystem.Api.GetReconstructionStatusAsync(reconstructionId, cancellationToken);

                if (status == OrchestrationStatus.Succeeded)
                    break;

                if (status == OrchestrationStatus.Failed || status == OrchestrationStatus.Cancelled)
                {
                    progress?.Report(CaptureUploadStatus.Failed);
                    throw new Exception("Capture reconstruction failed.");
                }

                try
                {
                    var manifest = await VisualPositioningSystem.Api.GetReconstructionManifestAsync(reconstructionId, cancellationToken);
                    App.state.captures[captureSessionId].manifest.value = manifest;
                }
                catch (Exception exception)
                {
                    Log.Warn(LogGroup.Capture, $"Manifest poll failed for reconstruction {reconstructionId}: {exception.Message}");
                }

                await UniTask.WaitForSeconds(3, cancellationToken: cancellationToken);
            }

            progress?.Report(CaptureUploadStatus.Uploaded);

            await UpdateCaptureList();
        }

        private static async UniTask CreateReconstruction(Guid captureId, ReconstructionOptions reconstructionOptions)
        {
            await VisualPositioningSystem.Api
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
