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

        private static bool capturesLoaded;
        private static string localCaptureNamePath;
        private static Dictionary<Guid, string> _localCaptureNames = new();
        private static IDisposable _subscription;
        private static IDisposable _idleRefreshTimerSubscription;
        private static CompositeDisposable _pollSubscriptions = new();

        public static void Initialize()
        {
            ZedCaptureController.Initialize();

            localCaptureNamePath = $"{Application.persistentDataPath}/LocalCaptureNames.json";

            if (File.Exists(localCaptureNamePath))
                foreach (var kvp in SimpleJSON.JSONNode.Parse(File.ReadAllText(localCaptureNamePath)))
                    _localCaptureNames[Guid.Parse(kvp.Key)] = kvp.Value;

            _subscription = new ComposedDisposable(
                App.state.loggedIn.Subscribe((bool value) =>
                    Log.Info(LogGroup.Capture, "state loggedIn={LoggedIn}", value)),
                App.state.captureStatus.Subscribe((CaptureStatus value) =>
                    Log.Info(LogGroup.Capture, "state captureStatus={CaptureStatus}", value)),
                App.state.zedReachable.Subscribe((bool value) =>
                    Log.Info(LogGroup.Capture, "state zedReachable={ZedReachable} zedStatus={ZedStatus}",
                        value, App.state.zedStatus.value)),
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
                ObservableCombineValues(
                    App.state.loggedIn,
                    App.state.captureStatus,
                    App.state.zedReachable,
                    (loggedIn, captureStatus, zedReachable) =>
                        loggedIn && captureStatus == CaptureStatus.Idle && zedReachable)
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
                                    {
                                        Log.Error(
                                            LogGroup.Capture,
                                            result.Exception,
                                            "Reconstruction poll failed for capture {CaptureId}",
                                            capture.id
                                        );
                                        App.state.captures[capture.id].clientPhase.value = CaptureClientPhase.Failed;
                                    }
                                    else
                                        UpdateCaptureList().Forget();
                                })
                            .AddTo(_pollSubscriptions))
            );
        }

        public static void Shutdown()
        {
            _subscription?.Dispose();
            _subscription = null;
            _idleRefreshTimerSubscription?.Dispose();
            _idleRefreshTimerSubscription = null;
            _pollSubscriptions.Dispose();
            ZedCaptureController.Shutdown();
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

        private static async UniTask StopCaptureForCurrentDevice()
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

        private static void HandleCapturesChanged(IReadOnlyList<IStateOperation> ops)
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

        private static async UniTask UpdateCaptureList()
        {
            var stopwatch = System.Diagnostics.Stopwatch.StartNew();
            Log.Info(LogGroup.Capture, "UpdateCaptureList start");

            var zedCaptures = (await ZedCaptureController.EnumerateCaptures()).ToList();
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
                        state.name.value = remote?.CaptureSession.Name ?? _localCaptureNames.GetValueOrDefault(id);
                        state.hasLocalFiles.value = hasLocal;
                        state.recordedAt.value = remote?.CaptureSession.RecordedAt ?? local.RecordedAt;
                        state.type.value = remote?.CaptureSession.DeviceType ?? local.Type;
                        state.sessionSizeBytes.value = hasLocal ? local.SizeBytes : null;
                        state.serverCaptureExists.value = remote != null;
                        state.reconstruction.value = primary?.Reconstruction;
                        state.localizationMapId.value = primary?.LocalizationMapId ?? Guid.Empty;
                    });
            });

            capturesLoaded = true;
            Log.Info(LogGroup.Capture,
                "UpdateCaptureList done durationMs={DurationMs} resultCount={ResultCount}",
                stopwatch.ElapsedMilliseconds, App.state.captures.Count);
        }
    }
}
