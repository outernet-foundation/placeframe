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
        public int ConsecutiveRejections;
        public float SecondsSinceLastAccept;
        public MeasurementRejection LastRejectionReason;
        public double LastInnovationMahalanobisSquared;

        public static FilterHealth Snapshot() =>
            new FilterHealth
            {
                LocalizationLost = VisualPositioningSystem.IsLocalizationLost,
                ConsecutiveRejections = VisualPositioningSystem.ConsecutiveRejections,
                SecondsSinceLastAccept = VisualPositioningSystem.SecondsSinceLastAccept,
                LastRejectionReason = VisualPositioningSystem.LastRejectionReason,
                LastInnovationMahalanobisSquared = VisualPositioningSystem.LastInnovationMahalanobisSquared,
            };
    }

    public static class VisualPositioningSystem
    {
        private static Action<string> _logCallback;
        private static Action<string> _warnCallback;
        private static Action<string> _errorCallback;
        private static Func<HttpMessageHandler> _httpHandlerFactory;
        private static IDisposable _localizationSubscription;
        private static IDisposable _slewSubscription;
        private static HashSet<Guid> _maps = new HashSet<Guid>();
        private static LocalizationMapManager _localizationMapManager;
        private static bool _visualizationsVisible = true;
        private static ICameraProvider _cameraProvider;

        private static FilterState _state = RelocalizationFilter.InitialState();

        private const int LockupRejectionThreshold = 5;
        private const float LockupSecondsThreshold = 5f;

        private static float _lastAcceptedTime = -1f;

        // Diagnostic bypass switches surfaced as toggles in the metrics dialog. Flipped at
        // runtime to A/B individual pipeline stages against the same camera feed without a
        // rebuild. Neither gates the early-out behavior of StartLocalizing — both only affect
        // per-measurement processing in Localize/ApplyMeasurement.
        public static bool BypassInnovationGate;
        public static bool BypassKalman;

        public static DefaultApi Api { get; private set; }
        public static bool UseKeycloak { get; private set; }
        public static LocalizationMetrics MostRecentMetrics => _state.MostRecentMetrics;
        public static LocalizationMetrics LastReceivedMetrics { get; private set; }
        public static bool Localizing => _localizationSubscription != null;
        public static int LoadedMapCount => _maps.Count;
        public static double4x4 EcefToUnityWorldTransform => _state.AlignmentCurrent;
        public static double4x4 UnityWorldToEcefTransform => _state.AlignmentCurrentInverse;
        public static event Action OnEcefToUnityWorldTransformUpdated;
        public static event Action OnMetricsReceived;
        public static AlignmentUncertainty CurrentUncertainty => RelocalizationFilter.SummariseCovariance(_state.AlignmentCovariance);

        public static int ConsecutiveRejections => _state.ConsecutiveRejections;
        public static MeasurementRejection LastRejectionReason { get; private set; }
        public static double LastInnovationMahalanobisSquared { get; private set; }
        public static float SecondsSinceLastAccept => _lastAcceptedTime < 0f ? float.PositiveInfinity : Time.realtimeSinceStartup - _lastAcceptedTime;
        public static bool IsLocalizationLost =>
            Localizing && (ConsecutiveRejections > LockupRejectionThreshold || SecondsSinceLastAccept > LockupSecondsThreshold);

        public static void SetMapVisualizationsVisible(bool visible)
        {
            _visualizationsVisible = visible;
            _localizationMapManager?.SetVisible(visible);
        }

        internal static void LogDebug(string message) => _logCallback?.Invoke(message);

        internal static void LogWarn(string message) => _warnCallback?.Invoke(message);

        internal static void LogError(string message) => _errorCallback?.Invoke(message);

        public static void Initialize(
            ICameraProvider cameraProvider,
            string authAudience,
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

            Auth.Initialize(authAudience, logCallback, warnCallback, errorCallback, httpHandlerFactory);

            _cameraProvider = cameraProvider;
            _slewSubscription = Observable
                .EveryUpdate(UnityFrameProvider.Update)
                .Subscribe(_ => ApplyStepResult(RelocalizationFilter.TickSlew(_state, Time.deltaTime)));
        }

        // Caller passes the full apiUrl (e.g. https://x.ngrok-free.app or http://192.168.1.100:58080)
        // and whether to use Keycloak auth. A client/server auth-mode mismatch surfaces as a
        // 401/403 from the first /api/* call rather than a probe roundtrip at login time.
        public static async UniTask Login(string apiUrl, bool useKeycloak, string username, string password)
        {
            UseKeycloak = useKeycloak;

            // The generated client also enforces Configuration.Timeout via its own
            // CancellationTokenSource, so both timeouts must be infinite to disable it.
            DelegatingHandler authHandler;
            if (useKeycloak)
            {
                var authTokenUrl = $"{apiUrl}/auth/realms/placeframe-dev/protocol/openid-connect/token";
                await Auth.Login(authTokenUrl, username, password);
                authHandler = new AuthHttpHandler();
            }
            else
            {
                authHandler = new AnonymousIdentityHttpHandler(SystemInfo.deviceUniqueIdentifier);
            }

            authHandler.InnerHandler = _httpHandlerFactory?.Invoke() ?? new HttpClientHandler();

            Api = new DefaultApi(
                new HttpClient(authHandler)
                {
                    BaseAddress = new Uri(apiUrl),
                    Timeout = Timeout.InfiniteTimeSpan,
                },
                new Configuration { BasePath = apiUrl, Timeout = Timeout.InfiniteTimeSpan }
            );
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

            // Re-bootstrap filter history so a Stop→Start cycle is a real recovery, not a no-op against a locked posterior.
            ApplyStepResult(RelocalizationFilter.Reset(_state, _state.AlignmentCurrent));
            _lastAcceptedTime = -1f;
            LastRejectionReason = MeasurementRejection.None;
            LastInnovationMahalanobisSquared = 0.0;

            _localizationSubscription = _cameraProvider
                // Get camera configuration asynchronously
                .CameraConfig()
                // Observe CameraFrames and emit a (PinholeCameraConfig, CameraFrame) tuple for each new CameraFrame
                .SelectMany(cameraConfig => _cameraProvider.Frames(intervalSeconds).Select(frame => (cameraConfig, frame)))
                // Localize this client using each new CameraFrame
                .SubscribeAwait(
                    async (data, cancellationToken) => await Localize(data.cameraConfig, data.frame, cancellationToken),
                    // Localize throws for empty server responses and for the in-flight race where the last map is
                    // removed mid-frame; per-measurement filter rejections (confidence floor, innovation gate) are
                    // silent log-and-skip inside ApplyMeasurement.
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

            // TODO: Handle multiple results.
            var localizationResult = localizationResults.FirstOrDefault();

            await UniTask.SwitchToMainThread();

            LastReceivedMetrics = localizationResult.Metrics;
            OnMetricsReceived?.Invoke();

            var priorTranslation = _state.AlignmentMean.Position();
            var options = new ApplyMeasurementOptions { BypassInnovationGate = BypassInnovationGate, BypassKalman = BypassKalman };

            var result = RelocalizationFilter.ApplyMeasurement(_state, localizationResult, frame, options);

            LastRejectionReason = result.Rejection;
            LastInnovationMahalanobisSquared = result.InnovationMahalanobisSquared;
            if (result.Rejection == MeasurementRejection.None)
                _lastAcceptedTime = Time.realtimeSinceStartup;

            var measurement = result.Measurement;
            var residual = result.InnovationResidual;
            var sigma = result.SigmaPredicted;
            var posteriorTranslation = result.NewState.AlignmentMean.Position();
            var bypassTag = BypassFlagsTag();
            var stepResult = result.Rejection == MeasurementRejection.None ? "accept" : "reject";
            var reason = result.Rejection switch
            {
                MeasurementRejection.None => "ok",
                MeasurementRejection.InnovationGate => "innovationGate",
                _ => "unknown",
            };
            LogDebug(
                $"step=loc.measure result={stepResult} reason={reason}"
                    + $" hadAccept={result.HadAcceptedMeasurementBeforeStep}"
                    + $" snapped={result.Snapped} bypass={bypassTag}"
                    + $" mahalanobisSq={result.InnovationMahalanobisSquared:F4}"
                    + $" gateThresh={RelocalizationFilter.Chi2_99_6dof:F2}"
                    + $" tilt={measurement.TiltRadians:F4}"
                    + $" measTx={measurement.Translation.x:F3}"
                    + $" measTy={measurement.Translation.y:F3}"
                    + $" measTz={measurement.Translation.z:F3}"
                    + $" priorTx={priorTranslation.x:F3}"
                    + $" priorTy={priorTranslation.y:F3}"
                    + $" priorTz={priorTranslation.z:F3}"
                    + $" postTx={posteriorTranslation.x:F3}"
                    + $" postTy={posteriorTranslation.y:F3}"
                    + $" postTz={posteriorTranslation.z:F3}"
                    + $" resRx={residual[0]:F4}"
                    + $" resRy={residual[1]:F4}"
                    + $" resRz={residual[2]:F4}"
                    + $" resTx={residual[3]:F3}"
                    + $" resTy={residual[4]:F3}"
                    + $" resTz={residual[5]:F3}"
                    + $" sigRx={sigma[0, 0]:E2}"
                    + $" sigRy={sigma[1, 1]:E2}"
                    + $" sigRz={sigma[2, 2]:E2}"
                    + $" sigTx={sigma[3, 3]:E2}"
                    + $" sigTy={sigma[4, 4]:E2}"
                    + $" sigTz={sigma[5, 5]:E2}"
            );

            ApplyStepResult(result);

            return Unit.Default;
        }

        private static string BypassFlagsTag()
        {
            if (!BypassInnovationGate && !BypassKalman)
                return "none";
            var parts = new List<string>();
            if (BypassInnovationGate)
                parts.Add("gate");
            if (BypassKalman)
                parts.Add("kalman");
            return string.Join("+", parts);
        }

        public static void SetEcefToUnityTransform(double4x4 ecefToUnityTransform)
        {
            ApplyStepResult(RelocalizationFilter.Reset(_state, ecefToUnityTransform));
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

        private static void ApplyStepResult(StepResult result)
        {
            _state = result.NewState;
            if (result.TransformChanged)
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
