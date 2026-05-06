using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Cysharp.Threading.Tasks;
using FofX.Stateful;
using ObserveThing;
using Placeframe.Core;
using PlaceframeApiClient.Api;
using PlaceframeApiClient.Client;
using PlaceframeApiClient.Model;
using UnityEngine;
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

        private bool capturesLoaded;
        private string localCaptureNamePath;
        private readonly HashSet<Guid> activeReconstructionPolls = new HashSet<Guid>();
        private IDisposable captureStatusStream;
        private IDisposable _subscription;
        private bool wasZedReachable;

        void Awake()
        {
            ZedCaptureController.Initialize();

            localCaptureNamePath = $"{Application.persistentDataPath}/LocalCaptureNames.json";

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
                    capture.status.Subscribe(status => HandleCaptureUploadStatusChanged(capture, status))
                );
        }

        void OnDestroy()
        {
            captureStatusStream?.Dispose();
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
                var captureSession = await VisualPositioningSystem.Api
                    .CreateCaptureSessionAsync(new CaptureSessionCreate(type) { Id = id, Name = capture.name.value, RecordedAt = capture.recordedAt.value })
                    .AsUniTask();

                capture.clientPhase.value = CaptureClientPhase.Uploading;

                await VisualPositioningSystem.Api
                    .UploadCaptureSessionTarAsync(captureSession.Id, captureData)
                    .AsUniTask();

                capture.serverCaptureExists.value = true;

                var reconstruction = await CreateReconstruction(captureSession.Id, reconstructionOptions);
                capture.reconstructionId.value = reconstruction.Id;
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
                capture.reconstructionId.value = reconstruction.Id;
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
                    .RetryReconstructionAsync(capture.reconstructionId.value)
                    .AsUniTask();
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
                        new LocalizationMapCreate(capture.reconstructionId.value, 0, 0, 0, 0, 0, 0, 1, 0)
                        {
                            Name = capture.name.value,
                        }
                    )
                    .AsUniTask();
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
                    }
                )
                .AsUniTask();

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
                    StartCaptureForCurrentDevice().Forget();
                    break;

                case CaptureStatus.Stopping:
                    StopCaptureForCurrentDevice().Forget();
                    break;
            }
        }

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

            var json = new SimpleJSON.JSONObject();

            foreach (var kvp in App.state.captures.Where(x => x.Value.status.value == CaptureUploadStatus.NotUploaded))
                json[kvp.Key.ToString()] = kvp.Value.name.value;

            File.WriteAllText(localCaptureNamePath, json.ToString());
        }

        private void HandleZedReachabilityChanged(IReadOnlyList<IStateOperation> ops)
        {
            var nowReachable = ZedCaptureController.IsZedReachable(App.state.zedStatus.value);

            if (nowReachable
                && !wasZedReachable
                && App.state.loggedIn.value
                && App.state.captureStatus.value == CaptureStatus.Idle)
            {
                UpdateCaptureList().Forget();
            }

            wasZedReachable = nowReachable;
        }

        private void HandleCaptureUploadStatusChanged(CaptureState capture, CaptureUploadStatus status)
        {
            if (status != CaptureUploadStatus.Reconstructing
                || activeReconstructionPolls.Contains(capture.id))
            {
                return;
            }

            activeReconstructionPolls.Add(capture.id);
            PollReconstructionUntilTerminal(capture).Forget();
        }

        private async UniTask PollReconstructionUntilTerminal(CaptureState capture)
        {
            try
            {
                while (this != null && capture.status.value == CaptureUploadStatus.Reconstructing)
                {
                    try
                    {
                        var reconstruction = await VisualPositioningSystem.Api
                            .GetReconstructionAsync(App.state.captures[capture.id].reconstructionId.value);

                        if (this == null || capture.status.value != CaptureUploadStatus.Reconstructing)
                            return;

                        App.state.captures[capture.id].reconstruction.value = reconstruction;

                        if (reconstruction.Status == ReconstructionStatus.Succeeded
                            || reconstruction.Status == ReconstructionStatus.Failed
                            || reconstruction.Status == ReconstructionStatus.Cancelled)
                        {
                            await UpdateCaptureList();
                            return;
                        }
                    }
                    catch
                    {
                        // Transient — retry on the next tick. HTTP-layer logging surfaces the underlying cause.
                    }

                    await UniTask.WaitForSeconds(0.5f);
                }
            }
            finally
            {
                activeReconstructionPolls.Remove(capture.id);
            }
        }

        private async UniTask UpdateCaptureList()
        {
            Dictionary<Guid, string> captureNames = new Dictionary<Guid, string>();

            if (File.Exists(localCaptureNamePath))
            {
                foreach (var kvp in SimpleJSON.JSONNode.Parse(File.ReadAllText(localCaptureNamePath)))
                    captureNames.Add(Guid.Parse(kvp.Key), kvp.Value);
            }

            var remoteCaptureList = await VisualPositioningSystem.Api.GetCaptureSessionsAsync();

            var remoteCaptureReconstructions = new List<ReconstructionRead>();
            await UniTask.WhenAll(
                remoteCaptureList.Select(c =>
                    VisualPositioningSystem.Api
                        .GetReconstructionsAsync(captureSessionId: c.Id)
                        .AsUniTask()
                        .ContinueWith(x => remoteCaptureReconstructions.AddRange(x))
                )
            );

            List<LocalizationMapRead> remoteCaptureLocalizationMaps = await VisualPositioningSystem.Api
                .GetLocalizationMapsAsync(
                    reconstructionIds: remoteCaptureReconstructions
                        .Where(x => x.Status == ReconstructionStatus.Succeeded)
                        .Select(x => x.Id)
                        .ToList()
                )
                .AsUniTask();

            var zedCaptures = await ZedCaptureController.EnumerateCaptures();
            var zed = zedCaptures.Select(c => new LocalCapture(c.Id, c.RecordedAt, DeviceType.Zed));

            var localCaptures = CaptureManager.GetCaptures()
                .Select(id => new LocalCapture(id, CaptureManager.GetCaptureRecordedAtUtc(id), DeviceType.ARFoundation))
                .Concat(zed)
                .ToDictionary(x => x.Id);

            var captureData = remoteCaptureList.ToDictionary(
                x => x.Id,
                x =>
                {
                    var reconstruction = remoteCaptureReconstructions.FirstOrDefault(y => y.CaptureSessionId == x.Id);
                    return (
                        name: x.Name,
                        capture: x,
                        deviceType: x.DeviceType,
                        reconstruction,
                        localizationMap: reconstruction == null
                            ? default
                            : remoteCaptureLocalizationMaps.FirstOrDefault(y => y.ReconstructionId == reconstruction.Id),
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
                appState.captures.SetFrom(
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
    }
}
