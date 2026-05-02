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

        public static DefaultApi Api { get; private set; }
        public static LocalizationMetrics MostRecentMetrics => _state.MostRecentMetrics;
        public static LocalizationMetrics LastReceivedMetrics { get; private set; }
        public static double4x4 EcefToUnityWorldTransform => _state.AlignmentCurrent;
        public static double4x4 UnityWorldToEcefTransform => _state.AlignmentCurrentInverse;
        public static event Action OnEcefToUnityWorldTransformUpdated;
        public static event Action OnMetricsReceived;
        public static AlignmentUncertainty CurrentUncertainty =>
            RelocalizationFilter.SummariseCovariance(_state.AlignmentCovariance);

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
                .Subscribe(_ =>
                    ApplyStepResult(RelocalizationFilter.TickSlew(_state, Time.deltaTime))
                );
        }

        public static async UniTask Login(string domain, string username, string password)
        {
            var apiUrl = $"https://{domain}";
            var authTokenUrl = $"{apiUrl}/auth/realms/placeframe-dev/protocol/openid-connect/token";

            await Auth.Login(authTokenUrl, username, password);

            Api = new DefaultApi(
                new HttpClient(
                    new AuthHttpHandler() { InnerHandler = _httpHandlerFactory?.Invoke() ?? new HttpClientHandler() }
                )
                {
                    BaseAddress = new Uri(apiUrl),
                },
                apiUrl
            );
        }

        public static void SetLocalizationMapManager(LocalizationMapManager localizationMapManager)
        {
            _localizationMapManager = localizationMapManager;

            foreach (var map in _maps)
                _localizationMapManager.AddMap(map, _visualizationsVisible);
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

            _localizationSubscription = _cameraProvider
                // Get camera configuration asynchronously
                .CameraConfig()
                // Observe CameraFrames and emit a (PinholeCameraConfig, CameraFrame) tuple for each new CameraFrame
                .SelectMany(cameraConfig =>
                    _cameraProvider.Frames(intervalSeconds).Select(frame => (cameraConfig, frame))
                )
                // Localize this client using each new CameraFrame
                .SubscribeAwait(
                    async (data, cancellationToken) => await Localize(data.cameraConfig, data.frame, cancellationToken),
                    // Localize throws for setup failures (no maps loaded) or empty server responses; per-measurement
                    // filter rejections (confidence floor, innovation gate) are silent log-and-skip inside ApplyMeasurement.
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

        public static (Vector3 position, Quaternion rotation) EcefToUnityWorld(
            double3 ecefPosition,
            quaternion ecefRotation
        )
        {
            var (position, rotation) = LocationUtilities.UnityFromEcef(
                _state.AlignmentCurrent,
                ecefPosition,
                ecefRotation
            );
            return (
                new Vector3((float)position.x, (float)position.y, (float)position.z),
                new Quaternion(rotation.value.x, rotation.value.y, rotation.value.z, rotation.value.w)
            );
        }

        public static (double3 position, quaternion rotation) UnityWorldToEcef(Vector3 position, Quaternion rotation) =>
            LocationUtilities.EcefFromUnity(
                _state.AlignmentCurrentInverse,
                new double3(position.x, position.y, position.z),
                rotation
            );

        private static async UniTask<Unit> Localize(
            PinholeCameraConfig cameraConfig,
            CameraFrame frame,
            CancellationToken cancellationToken
        )
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
                12,
                12.0,
                new FileParameter(memoryStream),
                cancellationToken
            );

            if (localizationResults.Count == 0)
                throw new InvalidOperationException("Localization failed");

            // TODO: Handle multiple results.
            var localizationResult = localizationResults.FirstOrDefault();

            await UniTask.SwitchToMainThread();

            LastReceivedMetrics = localizationResult.Metrics;
            OnMetricsReceived?.Invoke();

            var result = RelocalizationFilter.ApplyMeasurement(_state, localizationResult, frame);

            switch (result.Rejection)
            {
                case MeasurementRejection.ConfidenceFloor:
                    LogDebug(
                        $"Localization rejected: confidence.loose {localizationResult.Metrics.Confidence.Loose:0.00} < {RelocalizationFilter.LooseLowerBound:0.00}"
                    );
                    break;
                case MeasurementRejection.InnovationGate:
                    LogDebug(
                        $"Localization rejected: innovation gate (m² = {result.InnovationMahalanobisSquared:0.00})"
                    );
                    break;
            }

            ApplyStepResult(result);

            return Unit.Default;
        }

        public static void SetEcefToUnityTransform(double4x4 ecefToUnityTransform)
        {
            ApplyStepResult(RelocalizationFilter.Reset(_state, ecefToUnityTransform));
        }

        public static UniTask<LocalizationMapRead> GetMapData(Guid mapID)
        {
            return Api.GetLocalizationMapAsync(mapID).AsUniTask();
        }

        public static async UniTask<ReconstructionPoint[]> GetReconstructionPoints(
            Guid reconstructionID,
            CancellationToken cancellationToken = default
        )
        {
            var pointPayload = await FetchPayloadAsync(
                Api.GetReconstructionPointsAsync(reconstructionID, AxisConvention.UNITY).AsUniTask(),
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

        public static async UniTask<Vector3[]> GetReconstructionFramePoses(
            Guid reconstructionID,
            CancellationToken cancellationToken = default
        )
        {
            var framePayload = await FetchPayloadAsync(
                Api.GetReconstructionFramePosesAsync(reconstructionID, AxisConvention.UNITY).AsUniTask(),
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

        private static async UniTask<byte[]> FetchPayloadAsync(
            UniTask<FileParameter> responseTask,
            int bytesPerElement,
            CancellationToken cancellationToken
        )
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
        public static async UniTask ReadExactlyAsync(
            this Stream stream,
            byte[] buffer,
            int offset,
            int count,
            CancellationToken cancellationToken
        )
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
