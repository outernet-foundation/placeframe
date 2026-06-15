using System;
using System.Buffers;
using System.Buffers.Binary;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Runtime.InteropServices;
using System.Threading;
using Cysharp.Threading.Tasks;
using PlaceframeApiClient.Api;
using PlaceframeApiClient.Client;
using PlaceframeApiClient.Model;
using R3;
using Unity.Mathematics;
using UnityEngine;
using Quaternion = UnityEngine.Quaternion;
using Vector3 = UnityEngine.Vector3;

namespace Placeframe.Core
{
    public struct FilterHealth
    {
        public bool LocalizationLost;
        public float SecondsSinceLastAccept;

        public static FilterHealth Snapshot() =>
            new FilterHealth
            {
                LocalizationLost = VisualPositioningSystem.IsLocalizationLost,
                SecondsSinceLastAccept = VisualPositioningSystem.SecondsSinceLastAccept,
            };
    }

    public static class VisualPositioningSystem
    {
        private static Action<string> _logCallback;
        private static Action<string> _warnCallback;
        private static Action<string> _errorCallback;
        private static Func<HttpMessageHandler> _httpHandlerFactory;
        private static IDisposable _localizationSubscription;
        private static IDisposable _driftCorrectionSubscription;
        private static HashSet<Guid> _maps = new HashSet<Guid>();
        private static LocalizationMapManager _localizationMapManager;
        private static bool _visualizationsVisible = true;
        private static ICameraProvider _cameraProvider;

        private static readonly MultiHypothesisFilter _filter = new MultiHypothesisFilter();
        private static readonly DriftCorrectionController _controller = new DriftCorrectionController();

        // Discovery is a single quick GET; unlike the long-lived API client (whose timeout is
        // infinite so uploads/reconstructions aren't cut off), it needs a finite bound so an
        // unreachable host surfaces as a connect error instead of hanging the Connect button.
        private static readonly TimeSpan DiscoveryTimeout = TimeSpan.FromSeconds(15);

        private static float _lastAcceptedTime = -1f;
        private static double3 _lastVioPosition;
        private static float _lastVioLogTime;
        private static bool _hasLastVio;

        public static DefaultApi Api { get; private set; }
        public static bool Localizing => _localizationSubscription != null;
        public static int LoadedMapCount => _maps.Count;
        public static double4x4 EcefToUnityWorldTransform => _controller.Current;
        public static double4x4 UnityWorldToEcefTransform => _controller.CurrentInverse;
        public static event Action OnEcefToUnityWorldTransformUpdated;

        public static float SecondsSinceLastAccept => _lastAcceptedTime < 0f ? float.PositiveInfinity : Time.realtimeSinceStartup - _lastAcceptedTime;
        public static bool IsLocalizationLost => Localizing && SecondsSinceLastAccept > RelocalizationConfig.LocalizationLostSeconds;

        public static void SetMapVisualizationsVisible(bool visible)
        {
            _visualizationsVisible = visible;
            _localizationMapManager?.SetVisible(visible);
        }

        public static void LogDebug(string message) => _logCallback?.Invoke(message);

        public static void LogWarn(string message) => _warnCallback?.Invoke(message);

        public static void LogError(string message) => _errorCallback?.Invoke(message);

        public static void Initialize(
            ICameraProvider cameraProvider,
            Action<string> logCallback,
            Action<string> warnCallback,
            Action<string> errorCallback,
            Func<HttpMessageHandler> httpHandlerFactory = null
        )
        {
            if (_cameraProvider != null)
                throw new InvalidOperationException("VisualPositioningSystem is already initialized");

            _logCallback = logCallback;
            _warnCallback = warnCallback;
            _errorCallback = errorCallback;
            _httpHandlerFactory = httpHandlerFactory;

            Auth.Initialize(logCallback, warnCallback, errorCallback, httpHandlerFactory);

            _cameraProvider = cameraProvider;
            _driftCorrectionSubscription = Observable
                .EveryUpdate(UnityFrameProvider.Update)
                .Subscribe(_ => PublishIfChanged(_controller.Advance(Time.deltaTime)));
        }

        // Caller passes the full apiUrl (e.g. https://x.ngrok-free.app or http://192.168.1.100:58080).
        // Discover hits the unauthenticated /server-info before any authenticated client exists, so
        // the auth mode and (under keycloak) the OIDC token endpoint and client id come from the
        // server rather than being guessed or hardcoded.
        public static async UniTask<ServerInfo> Discover(string apiUrl, CancellationToken cancellationToken = default)
        {
            var api = new DefaultApi(
                new HttpClient(_httpHandlerFactory?.Invoke() ?? new HttpClientHandler())
                {
                    BaseAddress = new Uri(apiUrl),
                    Timeout = DiscoveryTimeout,
                },
                new Configuration { BasePath = apiUrl, Timeout = DiscoveryTimeout }
            );

            return await api.GetServerInfoAsync(cancellationToken);
        }

        // serverInfo comes from a prior Discover call. Under keycloak the password grant must run
        // before any authenticated client is built, so the bearer handler has a token to mint;
        // disabled mode needs no such exchange.
        public static async UniTask Login(string apiUrl, ServerInfo serverInfo, string username, string password)
        {
            if (serverInfo.AuthMode == ServerInfo.AuthModeEnum.Keycloak)
                await Auth.Login(serverInfo.TokenUrl, serverInfo.Audience, username, password);

            // The generated client also enforces Configuration.Timeout via its own
            // CancellationTokenSource, so both timeouts must be infinite to disable it.
            Api = new DefaultApi(
                new HttpClient(CreateBackendAuthHandler(serverInfo))
                {
                    BaseAddress = new Uri(apiUrl),
                    Timeout = Timeout.InfiniteTimeSpan,
                },
                new Configuration { BasePath = apiUrl, Timeout = Timeout.InfiniteTimeSpan }
            );
        }

        // Single source of the backend's outbound auth policy: every backend-bound HttpClient (API
        // client, Loki sink, log drainer) wraps the handler this returns. Keycloak gets a bearer
        // token (minted by a prior Auth.Login, so login must precede any request); disabled mode
        // gets the device id as X-Anonymous-Identity, kept for attribution.
        public static DelegatingHandler CreateBackendAuthHandler(ServerInfo serverInfo)
        {
            DelegatingHandler authHandler = serverInfo.AuthMode == ServerInfo.AuthModeEnum.Keycloak
                ? new AuthHttpHandler()
                : new AnonymousIdentityHttpHandler(SystemInfo.deviceUniqueIdentifier);
            authHandler.InnerHandler = _httpHandlerFactory?.Invoke() ?? new HttpClientHandler();
            return authHandler;
        }

        public static void SetLocalizationMapManager(LocalizationMapManager localizationMapManager)
        {
            _localizationMapManager = localizationMapManager;

            foreach (var map in _maps)
                _localizationMapManager.AddMap(map, _visualizationsVisible);
        }

        public static async UniTask SetLocalizationMaps(double3 ecefPosition, double radius, CancellationToken cancellationToken = default)
        {
            var maps = await GetLocalizationMaps(
                positionX: ecefPosition.x,
                positionY: ecefPosition.y,
                positionZ: ecefPosition.z,
                radius: radius,
                cancellationToken: cancellationToken
            );

            cancellationToken.ThrowIfCancellationRequested();

            SetLocalizationMaps(maps.Select(x => x.Id).ToArray());
        }

        public static void SetLocalizationMaps(Guid[] maps)
        {
            var currentMaps = _maps.ToArray();

            foreach (var toUnload in currentMaps.Except(maps))
                RemoveLocalizationMap(toUnload);

            foreach (var toLoad in maps.Except(currentMaps))
                AddLocalizationMap(toLoad);
        }

        public static void AddLocalizationMap(Guid mapId)
        {
            if (!_maps.Add(mapId))
                throw new InvalidOperationException($"Map {mapId} is already added");

            _localizationMapManager?.AddMap(mapId, _visualizationsVisible);
        }

        public static void RemoveLocalizationMap(Guid mapId)
        {
            if (!_maps.Remove(mapId))
                throw new InvalidOperationException($"Map {mapId} is not added or loading");

            _localizationMapManager?.RemoveMap(mapId);
        }

        public static void StartLocalizing(float intervalSeconds)
        {
            if (_localizationSubscription != null)
                throw new InvalidOperationException("VisualPositioningSystem is already localizing");
            if (_maps.Count == 0)
                throw new InvalidOperationException("VisualPositioningSystem has no maps loaded; call SetLocalizationMaps or AddLocalizationMap first");

            // Re-bootstrap so a Stop→Start cycle is a real recovery: drop every hypothesis and let the
            // next measurement bootstrap a fresh one. The rendered frame holds where it is until then.
            _filter.Reset();
            PublishIfChanged(true);
            _lastAcceptedTime = -1f;
            _hasLastVio = false;

            _localizationSubscription = _cameraProvider
                // Get camera configuration asynchronously
                .CameraConfig()
                // Observe CameraFrames and emit a (PinholeCameraConfig, CameraFrame) tuple for each new CameraFrame
                .SelectMany(cameraConfig => _cameraProvider.Frames(intervalSeconds).Select(frame => (cameraConfig, frame)))
                // Localize this client using each new CameraFrame
                .SubscribeAwait(
                    async (data, cancellationToken) => await Localize(data.cameraConfig, data.frame, cancellationToken),
                    // Localize throws for empty server responses and for the in-flight race where the last map is
                    // removed mid-frame; a measurement that fails the quality gate is not an exception — it comes
                    // back as a Reject result that the structured log line records on the normal path.
                    onErrorResume: exception => LogDebug(exception.Message),
                    onCompleted: _ => { },
                    // Skip frames if they pile up
                    awaitOperation: AwaitOperation.Drop
                );
        }

        public static void StopLocalizing()
        {
            if (_localizationSubscription == null)
                throw new InvalidOperationException("VisualPositioningSystem is not localizing");

            _localizationSubscription.Dispose();
            _localizationSubscription = null;
        }

        public static (Vector3 position, Quaternion rotation) EcefToUnityWorld(double3 ecefPosition, quaternion ecefRotation)
        {
            var (position, rotation) = LocationUtilities.UnityFromEcef(EcefToUnityWorldTransform, ecefPosition, ecefRotation);
            return (
                new Vector3((float)position.x, (float)position.y, (float)position.z),
                new Quaternion(rotation.value.x, rotation.value.y, rotation.value.z, rotation.value.w)
            );
        }

        public static (double3 position, quaternion rotation) UnityWorldToEcef(Vector3 position, Quaternion rotation) =>
            LocationUtilities.EcefFromUnity(UnityWorldToEcefTransform, new double3(position.x, position.y, position.z), rotation);

        private static async UniTask<Unit> Localize(PinholeCameraConfig cameraConfig, CameraFrame frame, CancellationToken cancellationToken)
        {
            // Switch to main thread to read _maps
            await UniTask.SwitchToMainThread();

            if (_maps.Count == 0)
                throw new InvalidOperationException("No localization maps loaded");

            using var memoryStream = new MemoryStream(frame.ImageBytes);

            // Localize
            var localizationResults = await Api.LocalizeImageAsync(
                _maps.ToList(),
                cameraConfig,
                AxisConvention.UNITY,
                new FileParameter(memoryStream),
                cancellationToken: cancellationToken
            );

            if (localizationResults.Count == 0)
                throw new InvalidOperationException("Localization failed");

            await UniTask.SwitchToMainThread();

            var now = Time.realtimeSinceStartup;
            var vioPosition = (double3)(float3)frame.CameraTranslationUnityWorldFromCamera;

            // Per-query VIO snapshot — a large vioDelta between successive Localize calls when the user
            // did not walk separates a VIO jump or session degradation from a stationary PnP sweep.
            var vioDelta = _hasLastVio ? math.length(vioPosition - _lastVioPosition) : 0.0;
            var vioElapsed = _hasLastVio ? now - _lastVioLogTime : 0f;
            LogDebug(
                $"step=reloc.vio trackingState={frame.TrackingState} vioDelta={vioDelta:F3} vioElapsed={vioElapsed:F3}"
                    + $" vioTx={vioPosition.x:F3} vioTy={vioPosition.y:F3} vioTz={vioPosition.z:F3}"
            );
            _lastVioPosition = vioPosition;
            _lastVioLogTime = now;
            _hasLastVio = true;

            var outcome = _filter.ApplyMeasurements(localizationResults, frame, now);

            if (outcome != MeasurementOutcome.Rejected)
                _lastAcceptedTime = now;

            // Only a Tracking-state segment carries a trustworthy scale ratio; under Limited/Lost the
            // estimate is frozen (null) rather than poisoned by a degraded VIO reading.
            var scaleRatio = frame.TrackingState == CameraTrackingState.Tracking ? _filter.LastValidScaleRatio : null;

            // Bootstrap sets the rendered frame outright; thereafter the controller decides — against its
            // motion-decaying deadband — whether the new belief has drifted far enough to ease toward. A
            // quality-gate rejection touches neither.
            if (outcome == MeasurementOutcome.Bootstrapped)
            {
                _controller.Set(_filter.BestEstimate, vioPosition, now);
                PublishIfChanged(true);
            }
            else if (outcome == MeasurementOutcome.Accepted)
            {
                var vioRotation = (quaternion)frame.CameraRotationUnityWorldFromCamera;
                _controller.Observe(_filter.BestEstimate, vioPosition, vioRotation, scaleRatio, now);
            }

            return Unit.Default;
        }

        public static void SetEcefToUnityTransform(double4x4 ecefToUnityTransform)
        {
            _filter.Reset();
            var vioPosition = _hasLastVio ? _lastVioPosition : double3.zero;
            _controller.Set(ecefToUnityTransform, vioPosition, Time.realtimeSinceStartup);
            PublishIfChanged(true);
        }

        public static UniTask<List<LocalizationMapRead>> GetLocalizationMaps(
            List<Guid> ids = default,
            List<Guid> reconstructionIds = default,
            double? positionX = default,
            double? positionY = default,
            double? positionZ = default,
            double? radius = default,
            CancellationToken cancellationToken = default
        ) => Api.GetLocalizationMapsAsync(ids, reconstructionIds, positionX, positionY, positionZ, radius, cancellationToken);

        public static UniTask<LocalizationMapRead> GetMapData(Guid mapID)
        {
            return Api.GetLocalizationMapAsync(mapID);
        }

        public static async UniTask<ReconstructionPoint[]> GetReconstructionPoints(Guid reconstructionID, CancellationToken cancellationToken = default)
        {
            var pointPayload = await FetchPayloadAsync(
                Api.GetReconstructionPointsAsync(reconstructionID, AxisConvention.UNITY),
                bytesPerElement: (3 * sizeof(float)) + 3,
                cancellationToken
            );

            return ParseReconstructionPointPayload(pointPayload);
        }

        private static ReconstructionPoint[] ParseReconstructionPointPayload(byte[] pointPayload)
        {
            var pointCount = (int)BinaryPrimitives.ReadUInt32LittleEndian(pointPayload.AsSpan(0, 4));
            var positionsByteCount = pointCount * 3 * sizeof(float);
            var positions = MemoryMarshal.Cast<byte, float>(pointPayload.AsSpan(4, positionsByteCount));
            var colors = pointPayload.AsSpan(4 + positionsByteCount, pointCount * 3);
            var points = new ReconstructionPoint[pointCount];

            for (var i = 0; i < points.Length; i++)
            {
                var index = i * 3;
                points[i] = new()
                {
                    position = new Vector3(positions[index + 0], positions[index + 1], positions[index + 2]),
                    color = new Color32(colors[index + 0], colors[index + 1], colors[index + 2], 255),
                };
            }

            return points;
        }

        public static async UniTask<Vector3[]> GetReconstructionFramePoses(Guid reconstructionID, CancellationToken cancellationToken = default)
        {
            var framePayload = await FetchPayloadAsync(
                Api.GetReconstructionFramePosesAsync(reconstructionID, AxisConvention.UNITY),
                bytesPerElement: (3 * sizeof(float)) + (4 * sizeof(float)),
                cancellationToken
            );

            return ParseReconsructionFramePosesPayload(framePayload);
        }

        private static Vector3[] ParseReconsructionFramePosesPayload(byte[] framePayload)
        {
            var frameCount = (int)BinaryPrimitives.ReadUInt32LittleEndian(framePayload.AsSpan(0, 4));
            var positionsByteCount = frameCount * 3 * sizeof(float);
            var positions = MemoryMarshal.Cast<byte, float>(framePayload.AsSpan(4, positionsByteCount));
            var framePositions = new Vector3[frameCount];

            for (var i = 0; i < framePositions.Length; i++)
            {
                var index = i * 3;
                framePositions[i] = new Vector3(positions[index + 0], positions[index + 1], positions[index + 2]);
            }

            return framePositions;
        }

        public struct ReconstructionPoint
        {
            public Vector3 position;
            public Color32 color;
        }

        private static void PublishIfChanged(bool transformChanged)
        {
            if (transformChanged)
                OnEcefToUnityWorldTransformUpdated?.Invoke();
        }

        private static async UniTask<byte[]> FetchPayloadAsync(UniTask<FileParameter> responseTask, int bytesPerElement, CancellationToken cancellationToken)
        {
            var response = await responseTask;
            var stream = response.Content;
            try
            {
                var header = new byte[4];
                await stream.ReadExactlyAsync(header, 0, 4, cancellationToken);

                var count = (int)BinaryPrimitives.ReadUInt32LittleEndian(header);
                var payloadByteCount = 4 + (count * bytesPerElement);

                var payload = ArrayPool<byte>.Shared.Rent(payloadByteCount);
                Buffer.BlockCopy(header, 0, payload, 0, 4);
                await stream.ReadExactlyAsync(payload, 4, payloadByteCount - 4, cancellationToken);

                return payload;
            }
            finally
            {
                stream.Dispose();
            }
        }
    }

    internal static class StreamExtensions
    {
        public static async UniTask ReadExactlyAsync(this Stream stream, byte[] buffer, int offset, int count, CancellationToken cancellationToken)
        {
            while (count > 0)
            {
                var read = await stream.ReadAsync(buffer, offset, count, cancellationToken);
                if (read == 0)
                    throw new EndOfStreamException();
                offset += read;
                count -= read;
            }
        }
    }
}
