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
    public readonly struct LocalCapture
    {
        public readonly Guid Id;
        public readonly DateTime RecordedAt;
        public readonly DeviceType Type;

        public LocalCapture(Guid id, DateTime recordedAt, DeviceType type)
        {
            Id = id;
            RecordedAt = recordedAt;
            Type = type;
        }
    }

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
        private bool wasZedReachable;

        private IDisposable _subscription;

        public static UniTask DeleteCapture(Guid id, DeviceType type) => type switch
        {
            DeviceType.ARFoundation => Sync(() => CaptureManager.DeleteCapture(id)),
            DeviceType.Zed => ZedCaptureController.DeleteCapture(id),
            _ => throw new ArgumentException($"Unknown DeviceType {type}"),
        };

        private static UniTask Sync(Action action)
        {
            action();
            return UniTask.CompletedTask;
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
                        UploadCapture(capture, reconstructionOptions).Forget(e => OnPipelineFailed(capture, "Upload", e));
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
                        DoReconstruct(capture, reconstructionOptions).Forget(e => OnPipelineFailed(capture, "Reconstruct", e)),
                }
            );
        }

        private static async UniTask DoReconstruct(CaptureState capture, ReconstructionOptions reconstructionOptions)
        {
            var reconstruction = await CreateReconstruction(capture.id, reconstructionOptions);
            capture.reconstructionId.value = reconstruction.Id;
            capture.reconstruction.value = reconstruction;
            capture.clientPhase.value = CaptureClientPhase.Idle;
        }

        public static void RequestRetry(CaptureState capture)
        {
            RetryReconstruction(capture).Forget(e => OnPipelineFailed(capture, "Retry", e));
        }

        private static async UniTask RetryReconstruction(CaptureState capture)
        {
            var reconstruction = await VisualPositioningSystem.Api
                .RetryReconstructionAsync(capture.reconstructionId.value)
                .AsUniTask();
            capture.reconstruction.value = reconstruction;
            capture.clientPhase.value = CaptureClientPhase.Idle;
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
                .ContinueWith(x => capture.localizationMapId.value = x.Result.Id);
        }

        private static void OnPipelineFailed(CaptureState capture, string stage, Exception exception)
        {
            Log.Error(LogGroup.Capture, $"{stage} failed for capture {capture.id}: {exception}");
            capture.clientPhase.value = CaptureClientPhase.Failed;
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

            wasZedReachable = ZedCaptureController.IsZedReachable(App.state.zedStatus.value);

            _subscription = new ComposedDisposable(
                StateObservables.SubscribeOperations(HandleCaptureStatusChanged, App.state.loggedIn, App.state.captureStatus),
                App.state.captures.SubscribeOperations(HandleCapturesChanged),
                StateObservables.SubscribeOperations(HandleZedReachabilityChanged, App.state.zedStatus)
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
                                awaitReconstructionTasks.Add(
                                    capture.id,
                                    TaskHandle.Execute(token =>
                                        AwaitReconstructionComplete(capture.id, token)
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

        private void HandleZedReachabilityChanged(IReadOnlyList<IStateOperation> ops)
        {
            var nowReachable = ZedCaptureController.IsZedReachable(App.state.zedStatus.value);
            var becameReachable = nowReachable && !wasZedReachable;
            wasZedReachable = nowReachable;

            if (becameReachable
                && App.state.loggedIn.value
                && App.state.captureStatus.value == CaptureStatus.Idle)
            {
                UpdateCaptureList().Forget();
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

        private UniTask StopCapture(DeviceType deviceType, CancellationToken cancellationToken = default) => deviceType switch
        {
            DeviceType.ARFoundation => Sync(CaptureManager.StopCapture),
            DeviceType.Zed => ZedCaptureController.StopCapture(cancellationToken),
            _ => throw new ArgumentException($"Unknown DeviceType {deviceType}"),
        };

        private UniTask StartCapture(DeviceType deviceType, CancellationToken cancellationToken = default) => deviceType switch
        {
            DeviceType.ARFoundation => Sync(() => CaptureManager.StartCapture(captureIntervalSeconds)),
            DeviceType.Zed => ZedCaptureController.StartCapture(captureIntervalSeconds, cancellationToken),
            _ => throw new ArgumentException($"Unknown DeviceType {deviceType}"),
        };

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

            List<LocalizationMapRead> remoteCaptureLocalizationMaps = await VisualPositioningSystem.Api
                .GetLocalizationMapsAsync(
                    reconstructionIds: remoteCaptureReconstructions
                        .Where(x => x.Status == ReconstructionStatus.Succeeded)
                        .Select(x => x.Id)
                        .ToList()
                )
                .AsUniTask();

            var localCaptures = (await GetAllLocalCaptures()).ToDictionary(x => x.Id);

            var captureData = remoteCaptureList.ToDictionary(
                x => x.Id,
                x =>
                {
                    var reconstruction = remoteCaptureReconstructions.FirstOrDefault(y => y.CaptureSessionId == x.Id);
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
                        hasLocalFiles: localCaptures.ContainsKey(x.Id),
                        recordedAt: x.RecordedAt
                    );
                }
            );

            foreach (var (id, local) in localCaptures)
            {
                if (captureData.ContainsKey(id))
                    continue;

                captureData.Add(
                    id,
                    (
                        name: captureNames.TryGetValue(id, out var name) ? name : null,
                        capture: null,
                        deviceType: local.Type,
                        reconstruction: null,
                        localizationMap: null,
                        hasLocalFiles: true,
                        recordedAt: local.RecordedAt
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
                        state.recordedAt.value = entry.recordedAt;
                        state.type.value = entry.deviceType;
                        state.serverCaptureExists.value = entry.capture != null;
                        state.reconstruction.value = entry.reconstruction;
                        state.reconstructionId.value = entry.reconstruction?.Id ?? Guid.Empty;
                        state.localizationMapId.value = entry.localizationMap?.Id ?? Guid.Empty;
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

        // The phone may not have an active USB-ethernet link to the ZED box. Bound the
        // enumerate call so a list refresh doesn't block on a long socket timeout when
        // the box is simply absent; reachability is owned by ZedCaptureController's
        // health poll, not by this method.
        private static readonly TimeSpan ZedEnumerateTimeout = TimeSpan.FromSeconds(1);

        private static async UniTask<IReadOnlyList<LocalCapture>> GetAllLocalCaptures(CancellationToken cancellationToken = default)
        {
            var arFoundation = CaptureManager.GetCaptures()
                .Select(id => new LocalCapture(id, CaptureManager.GetCaptureRecordedAtUtc(id), DeviceType.ARFoundation));

            IEnumerable<LocalCapture> zed;
            try
            {
                using var cts = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
                cts.CancelAfter(ZedEnumerateTimeout);
                var zedCaptures = await ZedCaptureController.GetCaptures(cts.Token);
                zed = zedCaptures.Select(c => new LocalCapture(c.Id, c.RecordedAt, DeviceType.Zed));
            }
            catch (OperationCanceledException) when (!cancellationToken.IsCancellationRequested)
            {
                zed = Array.Empty<LocalCapture>();
            }
            catch (Exception exception)
            {
                Log.Warn(LogGroup.Capture, $"Failed to enumerate ZED captures: {exception.Message}");
                zed = Array.Empty<LocalCapture>();
            }

            return arFoundation.Concat(zed).ToArray();
        }

        private static async UniTask UploadCapture(
            CaptureState capture,
            ReconstructionOptions reconstructionOptions,
            CancellationToken cancellationToken = default
        )
        {
            var id = capture.id;
            var type = capture.type.value;

            capture.clientPhase.value = CaptureClientPhase.Initializing;

            var captureData = type switch
            {
                DeviceType.Zed => await ZedCaptureController.GetCapture(id, cancellationToken),
                DeviceType.ARFoundation => await CaptureManager.GetCaptureTar(id),
                _ => throw new ArgumentException($"Unknown DeviceType {type}"),
            };

            await UniTask.SwitchToMainThread();
            var captureSession = await VisualPositioningSystem.Api
                .CreateCaptureSessionAsync(new CaptureSessionCreate(type) { Id = id, Name = capture.name.value, RecordedAt = capture.recordedAt.value })
                .AsUniTask();

            capture.clientPhase.value = CaptureClientPhase.Uploading;

            await VisualPositioningSystem.Api
                .UploadCaptureSessionTarAsync(captureSession.Id, captureData, cancellationToken: cancellationToken)
                .AsUniTask();

            capture.serverCaptureExists.value = true;

            var reconstruction = await CreateReconstruction(captureSession.Id, reconstructionOptions);
            capture.reconstructionId.value = reconstruction.Id;
            capture.reconstruction.value = reconstruction;
            capture.clientPhase.value = CaptureClientPhase.Idle;
        }

        private async UniTask AwaitReconstructionComplete(Guid captureSessionId, CancellationToken cancellationToken)
        {
            var reconstructionId = App.state.captures[captureSessionId].reconstructionId.value;

            while (true)
            {
                try
                {
                    var reconstruction = await VisualPositioningSystem.Api.GetReconstructionAsync(reconstructionId, cancellationToken);
                    App.state.captures[captureSessionId].reconstruction.value = reconstruction;

                    if (reconstruction.Status == ReconstructionStatus.Succeeded
                        || reconstruction.Status == ReconstructionStatus.Failed
                        || reconstruction.Status == ReconstructionStatus.Cancelled)
                    {
                        break;
                    }
                }
                catch (OperationCanceledException)
                {
                    throw;
                }
                catch (Exception exception)
                {
                    Log.Warn(LogGroup.Capture, $"Reconstruction poll failed for {reconstructionId}: {exception.Message}");
                }

                await UniTask.WaitForSeconds(0.5f, cancellationToken: cancellationToken);
            }

            await UpdateCaptureList();
        }

        private static UniTask<ReconstructionRead> CreateReconstruction(Guid captureId, ReconstructionOptions reconstructionOptions) =>
            VisualPositioningSystem.Api
                .CreateReconstructionAsync(
                    new ReconstructionCreateWithOptions(new ReconstructionCreate(captureId))
                    {
                        Options = reconstructionOptions,
                    }
                )
                .AsUniTask();
    }
}
