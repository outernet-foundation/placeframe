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
using PlerionApiClient.Api;
using PlerionApiClient.Client;
using PlerionApiClient.Model;
using R3;
using Unity.Mathematics;
using UnityEngine;
using Quaternion = UnityEngine.Quaternion;
using Vector3 = UnityEngine.Vector3;

namespace Plerion.Core
{
    public static class VisualPositioningSystem
    {
        private static Action<string> _logCallback;
        private static Action<string> _warnCallback;
        private static Action<string> _errorCallback;
        private static IDisposable _localizationSubscription;
        private static DefaultApi _api;
        private static HashSet<Guid> _maps = new HashSet<Guid>();
        private static LocalizationMapManager _localizationMapManager;
        private static ICameraProvider _cameraProvider;
        private static double4x4 _unityFromEcefTransform = double4x4.identity;
        private static double4x4 _ecefFromUnityTransform = math.inverse(_unityFromEcefTransform);

        public static LocalizationMetrics MostRecentMetrics { get; private set; }
        public static double4x4 EcefToUnityWorldTransform => _unityFromEcefTransform;
        public static double4x4 UnityWorldToEcefTransform => _ecefFromUnityTransform;
        public static event Action OnEcefToUnityWorldTransformUpdated;

        internal static void LogDebug(string message) => _logCallback?.Invoke(message);

        internal static void LogWarn(string message) => _warnCallback?.Invoke(message);

        internal static void LogError(string message) => _errorCallback?.Invoke(message);

        public static void Initialize(
            ICameraProvider cameraProvider,
            string apiUrl,
            string authTokenUrl,
            string authAudience,
            Action<string> logCallback,
            Action<string> warnCallback,
            Action<string> errorCallback
        )
        {
            if (_cameraProvider != null)
                throw new InvalidOperationException("VisualPositioningSystem is already initialized");

            _logCallback = logCallback;
            _warnCallback = warnCallback;
            _errorCallback = errorCallback;

            Auth.Initialize(authTokenUrl, authAudience, logCallback, warnCallback, errorCallback);

            _cameraProvider = cameraProvider;
            _api = new DefaultApi(
                new HttpClient(new AuthHttpHandler() { InnerHandler = new HttpClientHandler() })
                {
                    BaseAddress = new Uri(apiUrl),
                },
                apiUrl
            );
        }

        public static async UniTask Login(string username, string password) => await Auth.Login(username, password);

        public static void SetLocalizationMapManager(LocalizationMapManager localizationMapManager)
        {
            _localizationMapManager = localizationMapManager;

            foreach (var map in _maps)
                _localizationMapManager.AddMap(map, _localizationSubscription != null);
        }

        public static void AddLocalizationMap(Guid mapId)
        {
            if (!_maps.Add(mapId))
                throw new InvalidOperationException($"Map {mapId} is already added");

            _localizationMapManager?.AddMap(mapId, _localizationSubscription != null);
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

            _localizationMapManager.SetVisible(true);

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
                    // Skip frames if they pile up
                    AwaitOperation.Drop
                );
        }

        public static void StopLocalizing()
        {
            if (_localizationSubscription == null)
                throw new InvalidOperationException("VisualPositioningSystem is not localizing");

            _localizationMapManager.SetVisible(false);

            _localizationSubscription.Dispose();
            _localizationSubscription = null;
        }

        public static (Vector3 position, Quaternion rotation) EcefToUnityWorld(
            double3 ecefPosition,
            quaternion ecefRotation
        )
        {
            var (position, rotation) = LocationUtilities.UnityFromEcef(
                _unityFromEcefTransform,
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
                _ecefFromUnityTransform,
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
            {
                throw new InvalidOperationException("No localization maps loaded");
            }

            using var memoryStream = new MemoryStream(frame.ImageBytes);

            // Localize
            var localizationResults = await _api.LocalizeImageAsync(
                _maps.ToList(),
                cameraConfig,
                AxisConvention.UNITY,
                12,
                12.0,
                new FileParameter(memoryStream),
                cancellationToken
            );

            if (localizationResults.Count == 0)
            {
                throw new InvalidOperationException("Localization failed");
            }

            // TODO: Handle multiple results
            var localizationResult = localizationResults.FirstOrDefault();

            // Get the transform from the map to the camera (The inverse of the camera's pose in the map)
            var translationCameraFromMap = localizationResult.CameraFromMapTransform.Translation.ToDouble3();
            var rotationCameraFromMap = localizationResult
                .CameraFromMapTransform.Rotation.ToMathematicsQuaternion()
                .ToDouble3x3();

            // Get the transform from the map to the ECEF reference frame (the map's ECEF pose)
            var translationEcefFromMap = localizationResult.MapTransform.Translation.ToDouble3();
            var rotationEcefFromMap = localizationResult.MapTransform.Rotation.ToMathematicsQuaternion().ToDouble3x3();

            // Change the basis of the map's pose to Unity's conventions
            (translationEcefFromMap, rotationEcefFromMap) = LocationUtilities.ChangeBasisUnityFromEcef(
                translationEcefFromMap,
                rotationEcefFromMap
            );

            // Get the transform from the camera to Unity world (the camera's pose in the Unity world)
            var translationUnityWorldFromCamera = (float3)frame.CameraTranslationUnityWorldFromCamera;
            // TODO: Adjust unity rotation to account for phone orientation (portrait vs landscape)
            var rotationUnityWorldFromCamera = math.mul(
                ((quaternion)frame.CameraRotationUnityWorldFromCamera).ToDouble3x3(),
                quaternion.AxisAngle(new float3(0f, 0f, 1f), math.radians(0f)).ToDouble3x3()
            );

            // Constrain both camera rotations to be gravity-aligned
            // rotationCameraFromMap = rotationCameraFromMap.RemovePitchAndRoll();
            // rotationUnityWorldFromCamera = rotationUnityWorldFromCamera.RemovePitchAndRoll();

            // Compute the transform from the map to Unity world
            var rotationUnityFromMap = math.mul(rotationUnityWorldFromCamera, rotationCameraFromMap);
            var translationUnityFromMap =
                math.mul(rotationUnityWorldFromCamera, translationCameraFromMap) + translationUnityWorldFromCamera;
            var transformUnityFromMap = Double4x4.FromTranslationRotation(
                translationUnityFromMap,
                rotationUnityFromMap
            );

            await UniTask.SwitchToMainThread();

            _unityFromEcefTransform = math.mul(
                transformUnityFromMap,
                math.inverse(Double4x4.FromTranslationRotation(translationEcefFromMap, rotationEcefFromMap))
            );
            _ecefFromUnityTransform = math.inverse(_unityFromEcefTransform);

            MostRecentMetrics = localizationResult.Metrics;

            OnEcefToUnityWorldTransformUpdated?.Invoke();

            return Unit.Default;
        }

        // public static double3x3 RemovePitchAndRoll(this double3x3 rotation)
        // {
        //     float3 up = new float3(0f, 1f, 0f);
        //     float3 right = math.mul(rotation.ToQuaternion(), new float3(1f, 0f, 0f));
        //     float3 forward = math.normalize(math.cross(right, up));
        //     return quaternion.LookRotationSafe(forward, up).ToDouble3x3();
        // }

        public static UniTask<LocalizationMapRead> GetMapData(Guid mapID)
        {
            return _api.GetLocalizationMapAsync(mapID).AsUniTask();
        }

        public static async UniTask<ReconstructionPoint[]> GetReconstructionPoints(
            Guid reconstructionID,
            CancellationToken cancellationToken = default
        )
        {
            var pointPayload = await FetchPayloadAsync(
                _api.GetReconstructionPointsAsync(reconstructionID, AxisConvention.UNITY).AsUniTask(),
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
                _api.GetReconstructionFramePosesAsync(reconstructionID, AxisConvention.UNITY).AsUniTask(),
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
