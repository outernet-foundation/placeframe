using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Cysharp.Threading.Tasks;
using FofX.Stateful;
using ObserveThing;
using static ObserveThing.Observables;
using Placeframe.Core;
using PlaceframeApiClient.Api;
using PlaceframeApiClient.Model;
using R3;
using UnityEngine;
using DeviceType = PlaceframeApiClient.Model.DeviceType;

namespace Placeframe.Client
{
    public static class CaptureController
    {
        private static float captureIntervalSeconds = 0.5f;
        private static readonly TimeSpan idleRefreshInterval = TimeSpan.FromSeconds(5);

        private static string localCaptureNamePath;
        private static Dictionary<Guid, string> _localCaptureNames = new();
        private static Dictionary<uint, IDisposable> _nameSubscriptions = new();
        private static IDisposable _subscription;
        private static IDisposable _idleRefreshTimerSubscription;
        private static CompositeDisposable _pollSubscriptions = new();

        private static readonly SemaphoreSlim _uploadSemaphore = new SemaphoreSlim(1, 1);
        private static readonly List<Guid> _uploadOrder = new();

        public static void Initialize()
        {
            ZedCaptureController.Initialize();
            LogDrainController.Initialize();

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
                        if (isIdleAndLoggedIn)
                        {
                            Log.Info(LogGroup.Capture, "UpdateCaptureList trigger=one-shot");
                            UpdateCaptureList().Forget();
                        }
                    }),
                App.state.zedReachable.Subscribe((bool _) =>
                {
                    if (App.state.loggedIn.value && App.state.captureStatus.value == CaptureStatus.Idle)
                    {
                        Log.Info(LogGroup.Capture, "UpdateCaptureList trigger=zedReachable-changed");
                        UpdateCaptureList().Forget();
                    }
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
                        if (isStoppingAndLoggedIn) StopCaptureForCurrentDevice(App.state.pendingCaptureName.value).Forget();
                    }),
                ObservableCombineValues(
                    App.state.loggedIn,
                    App.state.captureStatus,
                    (loggedIn, captureStatus) =>
                        loggedIn && captureStatus == CaptureStatus.Idle)
                    .Subscribe(shouldRefresh =>
                    {
                        if (shouldRefresh && _idleRefreshTimerSubscription == null)
                        {
                            Log.Info(LogGroup.Capture,
                                "captures polling timer started intervalSeconds={IntervalSeconds}",
                                idleRefreshInterval.TotalSeconds);
                            _idleRefreshTimerSubscription = Observable
                                .Timer(TimeSpan.Zero, idleRefreshInterval)
                                .Subscribe(_ => UpdateCaptureList().Forget());
                        }
                        else if (!shouldRefresh && _idleRefreshTimerSubscription != null)
                        {
                            Log.Info(LogGroup.Capture, "captures polling timer stopped");
                            _idleRefreshTimerSubscription.Dispose();
                            _idleRefreshTimerSubscription = null;
                        }
                    }),
                App.state.captures
                    .ObservableSelect(entry => entry.Value)
                    .SubscribeWithId(
                        onAdd: (subscriptionId, capture) =>
                            _nameSubscriptions[subscriptionId] = capture.name.Subscribe(
                                name => OnCaptureNameChanged(capture, name)),
                        onRemove: (subscriptionId, capture) =>
                        {
                            if (_nameSubscriptions.TryGetValue(subscriptionId, out var sub))
                            {
                                sub.Dispose();
                                _nameSubscriptions.Remove(subscriptionId);
                            }
                            if (_localCaptureNames.Remove(capture.id))
                                SaveLocalCaptureNames();
                        },
                        onDispose: () =>
                        {
                            foreach (var sub in _nameSubscriptions.Values)
                                sub.Dispose();
                            _nameSubscriptions.Clear();
                        }
                    ),
                App.state.captures
                    .ObservableSelect(entry => entry.Value)
                    .ObservableWhere(capture => capture.status
                        .ObservableSelect(status => status == CaptureUploadStatus.Reconstructing))
                    .Subscribe(onAdd: capture =>
                        Observable.Timer(TimeSpan.Zero, TimeSpan.FromSeconds(0.5))
                            .SelectAwait(async (_, cancellationToken) => await PollReconstruction(capture.id, cancellationToken))
                            .Where(reconstruction => reconstruction != null)
                            .TakeUntil(reconstruction => reconstruction.Status is ReconstructionStatus.Succeeded or ReconstructionStatus.Failed or ReconstructionStatus.Cancelled)
                            .Subscribe(
                                onNext: reconstruction => App.state.captures[capture.id].reconstruction.value = reconstruction,
                                onCompleted: _ => UpdateCaptureList().Forget())
                            .AddTo(_pollSubscriptions))
            );
        }

        private static async UniTask<ReconstructionReadWithQueue> PollReconstruction(Guid captureId, CancellationToken cancellationToken)
        {
            try
            {
                return await VisualPositioningSystem.Api.GetReconstructionAsync(
                    App.state.captures[captureId].reconstruction.value.Id,
                    cancellationToken: cancellationToken
                );
            }
            catch (HttpRequestException exception)
            {
                Log.Info(LogGroup.Capture, exception, "Reconstruction poll transient error for capture {CaptureId}", captureId);
                return null;
            }
        }

        public static void Shutdown()
        {
            _subscription?.Dispose();
            _subscription = null;
            _idleRefreshTimerSubscription?.Dispose();
            _idleRefreshTimerSubscription = null;
            _pollSubscriptions.Dispose();
            LogDrainController.Shutdown();
            ZedCaptureController.Shutdown();
        }

        public static async UniTask EnqueueUpload(CaptureState capture)
        {
            EnterUploadQueue(capture);
            try
            {
                await _uploadSemaphore.WaitAsync().AsUniTask();
            }
            finally
            {
                LeaveUploadQueue(capture);
            }

            try
            {
                await UIElements.Upload(capture);
            }
            finally
            {
                _uploadSemaphore.Release();
            }
        }

        private static void EnterUploadQueue(CaptureState capture)
        {
            _uploadOrder.Add(capture.id);
            RefreshUploadQueuePositions();
            capture.clientPhase.value = CaptureClientPhase.Queued;
        }

        private static void LeaveUploadQueue(CaptureState capture)
        {
            _uploadOrder.Remove(capture.id);
            capture.uploadQueuePosition.value = null;
            capture.uploadQueueDepth.value = null;
            RefreshUploadQueuePositions();
        }

        private static void RefreshUploadQueuePositions()
        {
            var depth = _uploadOrder.Count;
            for (var index = 0; index < _uploadOrder.Count; index++)
            {
                if (!App.state.captures.TryGetValue(_uploadOrder[index], out var queued))
                    continue;
                queued.uploadQueuePosition.value = index + 1;
                queued.uploadQueueDepth.value = depth;
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

        private static async UniTask StartCaptureForCurrentDevice()
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

        private static async UniTask StopCaptureForCurrentDevice(string name)
        {
            var deviceType = App.state.captureMode.value;
            switch (deviceType)
            {
                case DeviceType.ARFoundation:
                    var arId = CaptureManager.StopCapture();
                    _localCaptureNames[arId] = name;
                    SaveLocalCaptureNames();
                    break;
                case DeviceType.Zed:
                    await ZedCaptureController.StopCapture(name);
                    break;
                default:
                    throw new ArgumentException($"Unknown DeviceType {deviceType}");
            }
            App.state.captureStatus.value = CaptureStatus.Idle;
        }

        private static void OnCaptureNameChanged(CaptureState capture, string name)
        {
            if (string.IsNullOrWhiteSpace(name))
                return;
            var trimmed = name.Trim();
            var captureId = capture.id;

            if (capture.type.value == DeviceType.ARFoundation)
            {
                if (!_localCaptureNames.TryGetValue(captureId, out var existing) || existing != trimmed)
                {
                    _localCaptureNames[captureId] = trimmed;
                    SaveLocalCaptureNames();
                }
            }
            else
            {
                if (capture.hasLocalFiles.value)
                    PatchBoxName(captureId, trimmed).Forget();
            }

            if (capture.serverCaptureExists.value)
                PatchApiName(captureId, trimmed).Forget();
        }

        private static async UniTask PatchApiName(Guid captureId, string name)
        {
            try
            {
                await VisualPositioningSystem.Api.UpdateCaptureSessionAsync(
                    captureId, new CaptureSessionUpdate { Name = name });
            }
            catch (Exception exception)
            {
                Log.Info(LogGroup.Capture, exception, "Rename PATCH to API failed for {CaptureId}", captureId);
            }
        }

        private static async UniTask PatchBoxName(Guid captureId, string name)
        {
            try
            {
                await ZedCaptureController.UpdateCaptureSessionName(captureId, name);
            }
            catch (Exception exception)
            {
                Log.Info(LogGroup.Capture, exception, "Rename PATCH to box failed for {CaptureId}", captureId);
            }
        }

        private static void SaveLocalCaptureNames()
        {
            var json = new SimpleJSON.JSONObject();
            foreach (var kvp in _localCaptureNames)
                json[kvp.Key.ToString()] = kvp.Value;
            File.WriteAllText(localCaptureNamePath, json.ToString());
        }

        private static async UniTask UpdateCaptureList()
        {
            var stopwatch = System.Diagnostics.Stopwatch.StartNew();
            Log.Info(LogGroup.Capture, "UpdateCaptureList start");

            List<LocalCapture> zedCaptures;
            try
            {
                zedCaptures = (await ZedCaptureController.EnumerateCaptures()).ToList();
            }
            catch (ZedNotReachableException)
            {
                zedCaptures = new List<LocalCapture>();
            }
            var arCaptures = CaptureManager.GetCaptures().ToList();
            var locals = arCaptures.Concat(zedCaptures).ToDictionary(c => c.Id);
            var localsDurationMs = stopwatch.ElapsedMilliseconds;

            var serverStartMs = stopwatch.ElapsedMilliseconds;
            Dictionary<Guid, ExpandedCaptureSession> remotes;
            try
            {
                remotes = (await VisualPositioningSystem.Api.GetCaptureSessionsExpandedAsync())
                    .CaptureSessions.ToDictionary(c => c.CaptureSession.Id);
            }
            catch (Exception exception)
            {
                Log.Info(LogGroup.Capture, exception,
                    "UpdateCaptureList GetCaptureSessionsExpanded failed durationMs={DurationMs}",
                    stopwatch.ElapsedMilliseconds - serverStartMs);
                throw;
            }
            var serverDurationMs = stopwatch.ElapsedMilliseconds - serverStartMs;

            Log.Info(LogGroup.Capture,
                "UpdateCaptureList counts zedCount={ZedCount} arCount={ArCount} remoteCount={RemoteCount} localsDurationMs={LocalsDurationMs} serverDurationMs={ServerDurationMs}",
                zedCaptures.Count, arCaptures.Count, remotes.Count, localsDurationMs, serverDurationMs);

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
                        state.name.value = remote?.CaptureSession.Name
                            ?? local.Name
                            ?? _localCaptureNames.GetValueOrDefault(id)
                            ?? id.ToString();
                        state.hasLocalFiles.value = hasLocal;
                        state.recordedAt.value = remote?.CaptureSession.RecordedAt ?? local.RecordedAt;
                        state.type.value = remote?.CaptureSession.DeviceType ?? local.Type;
                        state.sessionSizeBytes.value = hasLocal
                            ? local.SizeBytes
                            : (long?)remote?.CaptureSession.SizeBytes;
                        state.serverCaptureExists.value = remote != null;
                        state.reconstruction.value = primary?.Reconstruction;
                        state.localizationMapId.value = primary?.LocalizationMapId ?? Guid.Empty;
                    });
            });

            Log.Info(LogGroup.Capture,
                "UpdateCaptureList done durationMs={DurationMs} resultCount={ResultCount}",
                stopwatch.ElapsedMilliseconds, App.state.captures.Count);
        }
    }
}
