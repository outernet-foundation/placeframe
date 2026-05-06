using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading;
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

        // The phone may not have an active USB-ethernet link to the ZED box. Bound the
        // enumerate call so a list refresh doesn't block on a long socket timeout when
        // the box is simply absent; reachability is owned by ZedCaptureController's
        // health poll, not by this method.
        private static readonly TimeSpan ZedEnumerateTimeout = TimeSpan.FromSeconds(1);

        private CancellationTokenSource currentCaptureCts;
        private bool capturesLoaded;
        private string localCaptureNamePath;
        private readonly Dictionary<Guid, CancellationTokenSource> awaitReconstructionCts = new Dictionary<Guid, CancellationTokenSource>();
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
                    capture
                        .status
                        .Subscribe(x =>
                        {
                            if (
                                x != CaptureUploadStatus.Initializing
                                && x != CaptureUploadStatus.Uploading
                                && x != CaptureUploadStatus.Reconstructing
                                && awaitReconstructionCts.TryGetValue(capture.id, out var existingCts)
                            )
                            {
                                existingCts.Cancel();
                                existingCts.Dispose();
                                awaitReconstructionCts.Remove(capture.id);
                            }

                            if (x == CaptureUploadStatus.Reconstructing
                                && !awaitReconstructionCts.ContainsKey(capture.id))
                            {
                                var cts = new CancellationTokenSource();
                                awaitReconstructionCts.Add(capture.id, cts);
                                UniTask.Create(() => AwaitReconstructionComplete(capture.id, cts.Token)).Forget();
                            }
                        })
                );
        }

        void OnDestroy()
        {
            currentCaptureCts?.Cancel();
            currentCaptureCts?.Dispose();
            captureStatusStream?.Dispose();
            foreach (var cts in awaitReconstructionCts.Values)
            {
                cts.Cancel();
                cts.Dispose();
            }
            awaitReconstructionCts.Clear();
        }

        public static void Upload(CaptureState capture, ReconstructionOptions reconstructionOptions) =>
            UniTask.Create(async () =>
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
            }).Forget();

        public static void Reconstruct(CaptureState capture, ReconstructionOptions reconstructionOptions) =>
            UniTask.Create(async () =>
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
            }).Forget();

        public static void Retry(CaptureState capture) =>
            UniTask.Create(async () =>
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
            }).Forget();

        public static void CreateMap(CaptureState capture) =>
            UniTask.Create(async () =>
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
            }).Forget();

        public static UniTask DeleteCapture(Guid id, DeviceType type) => type switch
        {
            DeviceType.ARFoundation => Sync(() => CaptureManager.DeleteCapture(id)),
            DeviceType.Zed => ZedCaptureController.DeleteCapture(id),
            _ => throw new ArgumentException($"Unknown DeviceType {type}"),
        };

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
                    currentCaptureCts?.Cancel();
                    currentCaptureCts?.Dispose();
                    currentCaptureCts = new CancellationTokenSource();
                    var startToken = currentCaptureCts.Token;
                    UniTask.Create(async () =>
                    {
                        await StartCapture(App.state.captureMode.value, startToken);
                        App.ExecuteTransaction(new SetCaptureStatusAction(CaptureStatus.Capturing));
                    }).Forget();
                    break;

                case CaptureStatus.Stopping:
                    currentCaptureCts?.Cancel();
                    currentCaptureCts?.Dispose();
                    currentCaptureCts = new CancellationTokenSource();
                    var stopToken = currentCaptureCts.Token;
                    UniTask.Create(async () =>
                    {
                        await StopCapture(App.state.captureMode.value, stopToken);
                        App.ExecuteTransaction(new SetCaptureStatusAction(CaptureStatus.Idle));
                    }).Forget();
                    break;
            }
        }

        private void HandleCapturesChanged(IReadOnlyList<IStateOperation> ops)
        {
            if (!capturesLoaded)
                return;

            var json = new SimpleJSON.JSONObject();

            foreach (var kvp in App.state.captures.Where(x => x.value.status.value == CaptureUploadStatus.NotUploaded))
                json[kvp.key.ToString()] = kvp.value.name.value;

            File.WriteAllText(localCaptureNamePath, json.ToString());
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

        private async UniTask AwaitReconstructionComplete(Guid captureSessionId, CancellationToken cancellationToken)
        {
            var reconstructionId = App.state.captures[captureSessionId].reconstructionId.value;

            while (true)
            {
                cancellationToken.ThrowIfCancellationRequested();

                try
                {
                    var reconstruction = await VisualPositioningSystem.Api.GetReconstructionAsync(reconstructionId);
                    App.state.captures[captureSessionId].reconstruction.value = reconstruction;

                    if (reconstruction.Status == ReconstructionStatus.Succeeded
                        || reconstruction.Status == ReconstructionStatus.Failed
                        || reconstruction.Status == ReconstructionStatus.Cancelled)
                    {
                        break;
                    }
                }
                catch
                {
                    // Transient — retry on the next tick. HTTP-layer logging surfaces the underlying cause.
                }

                await UniTask.WaitForSeconds(0.5f, cancellationToken: cancellationToken);
            }

            await UpdateCaptureList();
        }

        private UniTask StartCapture(DeviceType deviceType, CancellationToken cancellationToken = default) => deviceType switch
        {
            DeviceType.ARFoundation => Sync(() => CaptureManager.StartCapture(captureIntervalSeconds)),
            DeviceType.Zed => ZedCaptureController.StartCapture(captureIntervalSeconds, cancellationToken),
            _ => throw new ArgumentException($"Unknown DeviceType {deviceType}"),
        };

        private UniTask StopCapture(DeviceType deviceType, CancellationToken cancellationToken = default) => deviceType switch
        {
            DeviceType.ARFoundation => Sync(CaptureManager.StopCapture),
            DeviceType.Zed => ZedCaptureController.StopCapture(cancellationToken),
            _ => throw new ArgumentException($"Unknown DeviceType {deviceType}"),
        };

        private static UniTask Sync(Action action)
        {
            action();
            return UniTask.CompletedTask;
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

        private static async UniTask<IReadOnlyList<LocalCapture>> GetAllLocalCaptures()
        {
            var arFoundation = CaptureManager.GetCaptures()
                .Select(id => new LocalCapture(id, CaptureManager.GetCaptureRecordedAtUtc(id), DeviceType.ARFoundation));

            IEnumerable<LocalCapture> zed;
            try
            {
                using var cts = new CancellationTokenSource(ZedEnumerateTimeout);
                var zedCaptures = await ZedCaptureController.GetCaptures(cts.Token);
                zed = zedCaptures.Select(c => new LocalCapture(c.Id, c.RecordedAt, DeviceType.Zed));
            }
            catch
            {
                zed = Array.Empty<LocalCapture>();
            }

            return arFoundation.Concat(zed).ToArray();
        }
    }
}
