using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Cysharp.Threading.Tasks;
using FofX.Stateful;
using ObserveThing;
using static ObserveThing.Observables;
using Placeframe.Core;
using PlaceframeApiClient.Api;
using PlaceframeApiClient.Client;
using PlaceframeApiClient.Model;
using R3;
using UnityEngine;
using DeviceType = PlaceframeApiClient.Model.DeviceType;

namespace Placeframe.Client
{
    public class CaptureController : MonoBehaviour
    {
        private float captureIntervalSeconds = 0.2f;

        private bool capturesLoaded;
        private string localCaptureNamePath;
        private Dictionary<Guid, string> _localCaptureNames = new();
        private IDisposable _subscription;
        private CompositeDisposable _pollSubscriptions = new();

        void Awake()
        {
            ZedCaptureController.Initialize();

            localCaptureNamePath = $"{Application.persistentDataPath}/LocalCaptureNames.json";

            if (File.Exists(localCaptureNamePath))
                foreach (var kvp in SimpleJSON.JSONNode.Parse(File.ReadAllText(localCaptureNamePath)))
                    _localCaptureNames[Guid.Parse(kvp.Key)] = kvp.Value;

            _subscription = new ComposedDisposable(
                ObservableCombineValues(
                    App.state.loggedIn,
                    App.state.captureStatus,
                    (loggedIn, captureStatus) => loggedIn && captureStatus == CaptureStatus.Idle)
                    .Subscribe(isIdleAndLoggedIn =>
                    {
                        if (isIdleAndLoggedIn) UpdateCaptureList().Forget();
                    }),
                ObservableCombineValues(
                    App.state.loggedIn,
                    App.state.captureStatus,
                    (loggedIn, captureStatus) => loggedIn && captureStatus == CaptureStatus.Starting)
                    .Subscribe(isStartingAndLoggedIn =>
                    {
                        if (isStartingAndLoggedIn) StartCaptureForCurrentDevice().Forget();
                    }),
                ObservableCombineValues(
                    App.state.loggedIn,
                    App.state.captureStatus,
                    (loggedIn, captureStatus) => loggedIn && captureStatus == CaptureStatus.Stopping)
                    .Subscribe(isStoppingAndLoggedIn =>
                    {
                        if (isStoppingAndLoggedIn) StopCaptureForCurrentDevice().Forget();
                    }),
                App.state.zedReachable.Subscribe(isReachable =>
                {
                    if (isReachable
                        && App.state.loggedIn.value
                        && App.state.captureStatus.value == CaptureStatus.Idle)
                        UpdateCaptureList().Forget();
                }),
                App.state.captures.SubscribeOperations(HandleCapturesChanged),
                App.state.captures
                    .ObservableSelect(entry => entry.Value)
                    .ObservableWhere(capture => capture.status
                        .ObservableSelect(status => status == CaptureUploadStatus.Reconstructing))
                    .Subscribe(onAdd: capture =>
                        Observable.Timer(TimeSpan.Zero, TimeSpan.FromSeconds(0.5))
                            .SelectAwait(async (_, cancellationToken) => await VisualPositioningSystem.Api.GetReconstructionAsync(App.state.captures[capture.id].reconstruction.value.Id, cancellationToken: cancellationToken))
                            .OnErrorResumeAsFailure()
                            .TakeUntil(reconstruction => reconstruction.Status is ReconstructionStatus.Succeeded or ReconstructionStatus.Failed or ReconstructionStatus.Cancelled)
                            .Subscribe(
                                onNext: reconstruction => App.state.captures[capture.id].reconstruction.value = reconstruction,
                                onCompleted: result =>
                                {
                                    if (result.IsFailure)
                                        App.state.captures[capture.id].clientPhase.value = CaptureClientPhase.Failed;
                                    else
                                        UpdateCaptureList().Forget();
                                })
                            .AddTo(_pollSubscriptions))
            );
        }

        void OnDestroy()
        {
            _subscription?.Dispose();
            _pollSubscriptions.Dispose();
        }

        public static async UniTask Upload(CaptureState capture, ReconstructionOptions reconstructionOptions)
        {
            try
            {
                var id = capture.id;
                var type = capture.type.value;

                capture.clientPhase.value = CaptureClientPhase.Initializing;

                var captureData = type switch
                {
                    DeviceType.Zed => await ZedCaptureController.GetCapture(id),
                    DeviceType.ARFoundation => await CaptureManager.GetCaptureTar(id),
                    _ => throw new ArgumentException($"Unknown DeviceType {type}"),
                };

                await UniTask.SwitchToMainThread();
                capture.clientPhase.value = CaptureClientPhase.Uploading;

                var captureSession = await VisualPositioningSystem.Api
                    .CreateCaptureSessionAsync(
                        type,
                        new FileParameter(captureData),
                        id: id,
                        name: capture.name.value,
                        recordedAt: capture.recordedAt.value);

                capture.serverCaptureExists.value = true;

                var reconstruction = await CreateReconstruction(captureSession.Id, reconstructionOptions);
                capture.reconstruction.value = reconstruction;
                capture.clientPhase.value = CaptureClientPhase.Idle;
            }
            catch
            {
                capture.clientPhase.value = CaptureClientPhase.Failed;
                throw;
            }
        }

        public static async UniTask Reconstruct(CaptureState capture, ReconstructionOptions reconstructionOptions)
        {
            try
            {
                var reconstruction = await CreateReconstruction(capture.id, reconstructionOptions);
                capture.reconstruction.value = reconstruction;
                capture.clientPhase.value = CaptureClientPhase.Idle;
            }
            catch
            {
                capture.clientPhase.value = CaptureClientPhase.Failed;
                throw;
            }
        }

        public static async UniTask Retry(CaptureState capture)
        {
            try
            {
                var reconstruction = await VisualPositioningSystem.Api
                    .RetryReconstructionAsync(capture.reconstruction.value.Id);
                capture.reconstruction.value = reconstruction;
                capture.clientPhase.value = CaptureClientPhase.Idle;
            }
            catch
            {
                capture.clientPhase.value = CaptureClientPhase.Failed;
                throw;
            }
        }

        public static async UniTask CreateMap(CaptureState capture)
        {
            try
            {
                var map = await VisualPositioningSystem.Api
                    .CreateLocalizationMapAsync(
                        new LocalizationMapCreate(capture.reconstruction.value.Id, 0, 0, 0, 0, 0, 0, 1, 0)
                        {
                            Name = capture.name.value,
                        });
                capture.localizationMapId.value = map.Id;
            }
            catch
            {
                capture.clientPhase.value = CaptureClientPhase.Failed;
                throw;
            }
        }

        public static UniTask DeleteCapture(Guid id, DeviceType type)
        {
            switch (type)
            {
                case DeviceType.ARFoundation:
                    CaptureManager.DeleteCapture(id);
                    return UniTask.CompletedTask;
                case DeviceType.Zed:
                    return ZedCaptureController.DeleteCapture(id);
                default:
                    throw new ArgumentException($"Unknown DeviceType {type}");
            }
        }

        private static UniTask<ReconstructionRead> CreateReconstruction(Guid captureId, ReconstructionOptions reconstructionOptions) =>
            VisualPositioningSystem.Api
                .CreateReconstructionAsync(
                    new ReconstructionCreateWithOptions(new ReconstructionCreate(captureId))
                    {
                        Options = reconstructionOptions,
                    });

        private async UniTask StartCaptureForCurrentDevice()
        {
            var deviceType = App.state.captureMode.value;
            switch (deviceType)
            {
                case DeviceType.ARFoundation:
                    CaptureManager.StartCapture(captureIntervalSeconds);
                    break;
                case DeviceType.Zed:
                    await ZedCaptureController.StartCapture(captureIntervalSeconds);
                    break;
                default:
                    throw new ArgumentException($"Unknown DeviceType {deviceType}");
            }
            App.state.captureStatus.value = CaptureStatus.Capturing;
        }

        private async UniTask StopCaptureForCurrentDevice()
        {
            var deviceType = App.state.captureMode.value;
            switch (deviceType)
            {
                case DeviceType.ARFoundation:
                    CaptureManager.StopCapture();
                    break;
                case DeviceType.Zed:
                    await ZedCaptureController.StopCapture();
                    break;
                default:
                    throw new ArgumentException($"Unknown DeviceType {deviceType}");
            }
            App.state.captureStatus.value = CaptureStatus.Idle;
        }

        private void HandleCapturesChanged(IReadOnlyList<IStateOperation> ops)
        {
            if (!capturesLoaded)
                return;

            _localCaptureNames.Clear();
            var json = new SimpleJSON.JSONObject();
            foreach (var kvp in App.state.captures.Where(x => x.Value.status.value == CaptureUploadStatus.NotUploaded))
            {
                var name = kvp.Value.name.value;
                _localCaptureNames[kvp.Key] = name;
                json[kvp.Key.ToString()] = name;
            }

            File.WriteAllText(localCaptureNamePath, json.ToString());
        }

        private async UniTask UpdateCaptureList()
        {
            var zedCaptures = await ZedCaptureController.EnumerateCaptures();
            var locals = CaptureManager.GetCaptures().Concat(zedCaptures).ToDictionary(c => c.Id);
            var remotes = (await VisualPositioningSystem.Api.GetCaptureSessionsExpandedAsync())
                .CaptureSessions.ToDictionary(c => c.CaptureSession.Id);

            await UniTask.SwitchToMainThread();

            App.ExecuteTransaction(appState =>
            {
                appState.captures.SetFrom(
                    locals.Keys.Union(remotes.Keys).ToDictionary(id => id, id => id),
                    refreshOldEntries: true,
                    copy: (id, _, state) =>
                    {
                        var remote = remotes.GetValueOrDefault(id);
                        var primary = remote?.Reconstructions.FirstOrDefault();
                        var hasLocal = locals.TryGetValue(id, out var local);
                        state.name.value = remote?.CaptureSession.Name ?? _localCaptureNames.GetValueOrDefault(id);
                        state.hasLocalFiles.value = hasLocal;
                        state.recordedAt.value = remote?.CaptureSession.RecordedAt ?? local.RecordedAt;
                        state.type.value = remote?.CaptureSession.DeviceType ?? local.Type;
                        state.serverCaptureExists.value = remote != null;
                        state.reconstruction.value = primary?.Reconstruction;
                        state.localizationMapId.value = primary?.LocalizationMapId ?? Guid.Empty;
                    });
            });

            capturesLoaded = true;
        }
    }
}
