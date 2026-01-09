using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net.Http;
using Cysharp.Threading.Tasks;
using PlerionApiClient.Api;
using PlerionApiClient.Client;
using PlerionApiClient.Model;
using Unity.Mathematics;
using UnityEngine;

namespace Plerion.Core
{
    public static class VisualPositioningSystem
    {
        private static Action<string> _logCallback;
        private static Action<string> _warnCallback;
        private static Action<string> _errorCallback;
        private static Action<string, Exception> _logExceptionCallback;
        private static readonly AsyncLifecycleGuard _serviceGuard = new AsyncLifecycleGuard();
        private static Dictionary<Guid, LocalizationMap> _maps = new Dictionary<Guid, LocalizationMap>();
        private static double4x4 _unityFromEcefTransform = double4x4.identity;
        private static double4x4 _ecefFromUnityTransform = math.inverse(_unityFromEcefTransform);

        public static DefaultApi Api { get; private set; }
        public static Prefabs Prefabs { get; private set; }
        public static ICameraProvider CameraProvider { get; private set; }
        public static LocalizationMetrics MostRecentMetrics { get; private set; }
        public static double4x4 EcefToUnityWorldTransform => _unityFromEcefTransform;
        public static double4x4 UnityWorldToEcefTransform => _ecefFromUnityTransform;
        public static event Action OnEcefToUnityWorldTransformUpdated;

        internal static void LogDebug(string message) => _logCallback?.Invoke(message);

        internal static void LogWarn(string message) => _warnCallback?.Invoke(message);

        internal static void LogError(string message) => _errorCallback?.Invoke(message);

        internal static void LogException(string message, Exception exception = null) =>
            _logExceptionCallback?.Invoke(message, exception);

        public static void Initialize(
            ICameraProvider cameraProvider,
            string apiUrl,
            string authTokenUrl,
            string authAudience,
            Action<string> logCallback,
            Action<string> warnCallback,
            Action<string> errorCallback,
            Action<string, Exception> logException
        )
        {
            if (CameraProvider != null)
                throw new InvalidOperationException("VisualPositioningSystem is already initialized");

            _logCallback = logCallback;
            _warnCallback = warnCallback;
            _errorCallback = errorCallback;
            _logExceptionCallback = logException;

            Auth.Initialize(authTokenUrl, authAudience, logCallback, warnCallback, errorCallback);

            CameraProvider = cameraProvider;
            Prefabs = Resources.Load<Prefabs>("PrefabReferences");
            Api = new DefaultApi(
                new HttpClient(new AuthHttpHandler() { InnerHandler = new HttpClientHandler() })
                {
                    BaseAddress = new Uri(apiUrl),
                },
                apiUrl
            );
        }

        public static async UniTask Login(string username, string password) => await Auth.Login(username, password);

        public static void AddLocalizationMap(Guid mapId)
        {
            if (_maps.ContainsKey(mapId))
                throw new InvalidOperationException($"Map {mapId} is already added");

            _maps[mapId] = GameObject.Instantiate(Prefabs.localizationMapPrefab, Vector3.zero, Quaternion.identity);
            _maps[mapId]
                .gameObject.SetActive(
                    _serviceGuard.State == AsyncLifecycleGuard.LifecycleState.Starting
                        || _serviceGuard.State == AsyncLifecycleGuard.LifecycleState.Running
                );

            _maps[mapId].Initialize(mapId);
        }

        public static void RemoveLocalizationMap(Guid mapId)
        {
            if (_maps.TryGetValue(mapId, out var visualizer))
            {
                if (visualizer != null)
                    GameObject.Destroy(visualizer.gameObject);
                _maps.Remove(mapId);
                return;
            }

            throw new InvalidOperationException($"Map {mapId} is not added");
        }

        public static void StartLocalizing() => StartLocalizingInternal().Forget();

        public static void StopLocalizing() => StopLocalizingInternal().Forget();

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

        private static async UniTask StartLocalizingInternal()
        {
            try
            {
                foreach (var map in _maps.Values)
                {
                    map.gameObject.SetActive(true);
                }

                await _serviceGuard.StartAsync(
                    (token) =>
                        CameraProvider.Start(
                            intervalSeconds: 0,
                            cameraPoseProvider: GetCameraPose,
                            onFrameReceived: OnFrameReceived,
                            cancellationToken: token
                        )
                );
            }
            catch (OperationCanceledException)
            {
                // Ignored (Stop was called)
            }
            catch (Exception exception)
            {
                LogException("Failed to start localizing", exception);
                StopLocalizing();
            }
        }

        private static async UniTask StopLocalizingInternal()
        {
            foreach (var map in _maps.Values)
            {
                map.gameObject.SetActive(false);
            }

            await _serviceGuard.StopAsync(CameraProvider.Stop);
        }

        private static (Vector3 position, Quaternion rotation)? GetCameraPose()
        {
            if (UnityEngine.Camera.main == null)
                return null;
            var cameraTransform = UnityEngine.Camera.main.transform;
            return (cameraTransform.position, cameraTransform.rotation);
        }

        private static async UniTask OnFrameReceived(
            byte[] image,
            PinholeCameraConfig cameraConfig,
            Vector3 cameraTranslationUnityWorldFromCamera,
            Quaternion cameraRotationUnityWorldFromCamera
        )
        {
            // If we received a frame but the service is not running, the service
            // is stopping but hasn't deregistered the event yet, so ignore the frame
            if (_serviceGuard.State != AsyncLifecycleGuard.LifecycleState.Running)
                return;

            try
            {
                using var memoryStream = new MemoryStream(image);

                var mapIds = _maps.Keys.ToList();
                if (mapIds.Count == 0)
                {
                    LogWarn("No localization maps loaded, skipping localization");
                    return;
                }

                var localizationResults = await Api.LocalizeImageAsync(
                    mapIds,
                    cameraConfig,
                    AxisConvention.UNITY,
                    new FileParameter(memoryStream)
                );

                if (localizationResults.Count == 0)
                {
                    LogDebug("Localization failed");
                    return;
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
                var rotationEcefFromMap = localizationResult
                    .MapTransform.Rotation.ToMathematicsQuaternion()
                    .ToDouble3x3();

                // Change the basis of the map's pose to Unity's conventions
                (translationEcefFromMap, rotationEcefFromMap) = LocationUtilities.ChangeBasisUnityFromEcef(
                    translationEcefFromMap,
                    rotationEcefFromMap
                );

                // Get the transform from the camera to Unity world (the camera's pose in the Unity world)
                var translationUnityWorldFromCamera = (float3)cameraTranslationUnityWorldFromCamera;
                // TODO: Adjust unity rotation to account for phone orientation (portrait vs landscape)
                var rotationUnityWorldFromCamera = math.mul(
                    ((quaternion)cameraRotationUnityWorldFromCamera).ToDouble3x3(),
                    quaternion.AxisAngle(new float3(0f, 0f, 1f), math.radians(0f)).ToDouble3x3()
                );

                // Constrain both camera rotations to be gravity-aligned
                // rotationCameraFromMap = rotationCameraFromMap.RemovePitchAndRoll();
                // rotationUnityWorldFromCamera = rotationUnityWorldFromCamera.RemovePitchAndRoll();

                // Compute the transform from the map to the Unity world
                var rotationUnityFromMap = math.mul(rotationUnityWorldFromCamera, rotationCameraFromMap);
                var translationUnityFromMap =
                    math.mul(rotationUnityWorldFromCamera, translationCameraFromMap) + translationUnityWorldFromCamera;
                var transformUnityFromMap = Double4x4.FromTranslationRotation(
                    translationUnityFromMap,
                    rotationUnityFromMap
                );

                // Switch to the main thread before updating transforms and metrics, to avoid race conditions
                await UniTask.SwitchToMainThread();

                // Compute the transform from ECEF to Unity world
                _unityFromEcefTransform = math.mul(
                    transformUnityFromMap,
                    math.inverse(Double4x4.FromTranslationRotation(translationEcefFromMap, rotationEcefFromMap))
                );

                // Compute the transform from Unity world to ECEF
                _ecefFromUnityTransform = math.inverse(_unityFromEcefTransform);

                // Update metrics
                MostRecentMetrics = localizationResult.Metrics;

                // Notify listeners about the updated transform
                OnEcefToUnityWorldTransformUpdated?.Invoke();
            }
            catch (Exception ex)
            {
                LogException("Error during frame localization", ex);
            }
        }

        // public static double3x3 RemovePitchAndRoll(this double3x3 rotation)
        // {
        //     float3 up = new float3(0f, 1f, 0f);
        //     float3 right = math.mul(rotation.ToQuaternion(), new float3(1f, 0f, 0f));
        //     float3 forward = math.normalize(math.cross(right, up));
        //     return quaternion.LookRotationSafe(forward, up).ToDouble3x3();
        // }
    }
}
