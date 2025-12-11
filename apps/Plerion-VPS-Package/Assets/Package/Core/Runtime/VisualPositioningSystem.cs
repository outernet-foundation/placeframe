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
using Camera = PlerionApiClient.Model.Camera;

namespace Plerion.Core
{
    public static class VisualPositioningSystem
    {
        class MapData
        {
            public bool loaded;
            public LocalizationMapRead map;
            public ReconstructionVisualizer reconstructionVisualizer;
        }

        private static Dictionary<Guid, MapData> _maps = new Dictionary<Guid, MapData>();
        private static DefaultApi api;
        private static SystemState _localizationSessionState = SystemState.Idle;
        private static SystemState _localizingState = SystemState.Idle;
        private static Guid localizationSessionId = Guid.Empty;
        private static double4x4 unityFromEcefTransform = double4x4.identity;
        private static double4x4 ecefFromUnityTransform = math.inverse(unityFromEcefTransform);
        private static Action<string> _logCallback;
        private static Action<string> _warnCallback;
        private static Action<string> _errorCallback;
        private static Action<string, Exception> _logExceptionCallback;

        public static ICameraProvider CameraProvider { get; private set; }
        public static Prefabs Prefabs { get; private set; }
        public static bool LocalizationSessionActive => localizationSessionId != Guid.Empty;
        public static LocalizationMetrics MostRecentMetrics { get; private set; }
        public static double4x4 EcefToUnityWorldTransform => unityFromEcefTransform;
        public static double4x4 UnityWorldToEcefTransform => ecefFromUnityTransform;
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

            CameraProvider = cameraProvider;
            _logCallback = logCallback;
            _warnCallback = warnCallback;
            _errorCallback = errorCallback;
            _logExceptionCallback = logException;

            Prefabs = Resources.Load<Prefabs>("PrefabReferences");

            Auth.Initialize(authTokenUrl, authAudience, logCallback, warnCallback, errorCallback);

            api = new DefaultApi(
                new HttpClient(new AuthHttpHandler() { InnerHandler = new HttpClientHandler() })
                {
                    BaseAddress = new Uri(apiUrl),
                },
                apiUrl
            );
        }

        public static async UniTask Login(string username, string password) => await Auth.Login(username, password);

        public static async UniTask StartLocalizationSession()
        {
            if (_localizationSessionState != SystemState.Idle)
                throw new InvalidOperationException("Localization session is not idle");

            _localizationSessionState = SystemState.Starting;

            LocalizationSessionRead session = default;

            try
            {
                session = await api.CreateLocalizationSessionAsync();

                while (true)
                {
                    var status = await api.GetLocalizationSessionStatusAsync(session.Id);

                    if (status == "\"failed\"" || status == "\"exited\"")
                        throw new Exception("Session failed to start.");

                    if (status == "\"ready\"")
                        break;

                    await UniTask.WaitForSeconds(1);
                }

                await UniTask.SwitchToMainThread();
            }
            catch (Exception)
            {
                if (session != null)
                    api.DeleteLocalizationSessionAsync(session.Id).AsUniTask().Forget();

                throw;
            }

            localizationSessionId = session.Id;

            _localizationSessionState = SystemState.Running;
        }

        public static async UniTask StopLocalizationSession()
        {
            if (_localizationSessionState != SystemState.Running)
                throw new InvalidOperationException("Localization session is not running");

            _localizationSessionState = SystemState.Stopping;

            if (localizationSessionId != Guid.Empty)
            {
                await api.DeleteLocalizationSessionAsync(localizationSessionId).AsUniTask();
                localizationSessionId = Guid.Empty;
            }

            _localizationSessionState = SystemState.Idle;
        }

        public static UniTask AddLocalizationMaps(IEnumerable<Guid> maps) => AddLocalizationMaps(maps.ToList());

        public static UniTask AddLocalizationMaps(params Guid[] maps) => AddLocalizationMaps(maps.ToList());

        public static async UniTask AddLocalizationMaps(List<Guid> maps)
        {
            var tasks = new List<UniTask>();

            foreach (var mapId in maps)
            {
                if (_maps.ContainsKey(mapId))
                    throw new Exception($"Map {mapId} is already added");
            }

            // Create task to load all maps into localization session
            tasks.Add(api.LoadLocalizationMapsAsync(localizationSessionId, maps).AsUniTask());

            foreach (var mapId in maps)
            {
                _maps[mapId] = new MapData()
                {
                    reconstructionVisualizer = GameObject.Instantiate(
                        Prefabs.mapRendererPrefab,
                        Vector3.zero,
                        Quaternion.identity
                    ),
                };

                // Create task to fetch metadata
                tasks.Add(
                    api.GetLocalizationMapAsync(mapId)
                        .AsUniTask()
                        .ContinueWith(async map =>
                        {
                            _maps[mapId].loaded = false;
                            _maps[mapId].map = map;
                            _maps[mapId]
                                .reconstructionVisualizer.GetComponent<Anchor>()
                                .SetEcefTransform(
                                    new double3(map.PositionX, map.PositionY, map.PositionZ),
                                    new quaternion(
                                        (float)map.RotationX,
                                        (float)map.RotationY,
                                        (float)map.RotationZ,
                                        (float)map.RotationW
                                    )
                                );

                            await _maps[mapId].reconstructionVisualizer.Load(api, _maps[mapId].map.ReconstructionId);
                        })
                );
            }

            // Run all tasks in parallel and wait for them to complete
            await UniTask.WhenAll(tasks);

            // Mark maps as loaded
            foreach (var mapId in maps)
            {
                _maps[mapId].loaded = true;
            }
        }

        public static async UniTask RemoveLocalizationMap(Guid map)
        {
            if (!_maps.ContainsKey(map))
                throw new Exception($"Map {map} has not been added");
            if (!_maps[map].loaded)
                throw new Exception($"Map {map} has not finished loading");

            var mapData = _maps[map];
            GameObject.Destroy(mapData.reconstructionVisualizer.gameObject);
            _maps.Remove(map);

            await api.UnloadMapAsync(localizationSessionId, map);
        }

        public static async UniTask StartLocalizing()
        {
            if (_localizingState != SystemState.Idle)
                throw new InvalidOperationException("Localizing is already started");

            if (CameraProvider == null)
                throw new Exception("Camera provider must be set before calling Start.");

            var cameraConfig = await CameraProvider.Start(
                intervalSeconds: 0,
                cameraPoseProvider: () =>
                {
                    var cameraTransform = UnityEngine.Camera.main.transform;
                    return (cameraTransform.position, cameraTransform.rotation);
                },
                onFrameReceived: async (
                    image,
                    cameraTranslationUnityWorldFromCamera,
                    cameraRotationUnityWorldFromCamera
                ) =>
                {
                    if (image == null)
                        return;

                    using var memoryStream = new MemoryStream(image);
                    var localizationResults = await api.LocalizeImageAsync(
                        localizationSessionId,
                        AxisConvention.UNITY,
                        new FileParameter(memoryStream)
                    );

                    if (localizationResults.Count == 0)
                    {
                        LogDebug("Localization failed");
                        return;
                    }

                    var localizationResult = localizationResults.FirstOrDefault(); //for now, just use the first one
                    MostRecentMetrics = localizationResult.Metrics;

                    // Updating transforms should be done on the main thread
                    await UniTask.SwitchToMainThread();

                    unityFromEcefTransform = LocationUtilities.ComputeUnityFromEcefTransform(
                        localizationResult.CameraFromMapTransform.Translation.ToDouble3(),
                        localizationResult.CameraFromMapTransform.Rotation.ToMathematicsQuaternion().ToDouble3x3(),
                        localizationResult.MapTransform.Translation.ToDouble3(),
                        localizationResult.MapTransform.Rotation.ToMathematicsQuaternion().ToDouble3x3(),
                        cameraTranslationUnityWorldFromCamera,
                        // TODO: Adjust unity rotation to account for phone orientation (portrait vs landscape)
                        math.mul(
                            ((quaternion)cameraRotationUnityWorldFromCamera).ToDouble3x3(),
                            quaternion.AxisAngle(new float3(0f, 0f, 1f), math.radians(0f)).ToDouble3x3()
                        )
                    );
                    ecefFromUnityTransform = math.inverse(unityFromEcefTransform);

                    OnEcefToUnityWorldTransformUpdated?.Invoke();
                }
            );

            await api.SetLocalizationSessionCameraIntrinsicsAsync(localizationSessionId, new Camera(cameraConfig));

            _localizingState = SystemState.Running;
        }

        public static async UniTask StopLocalizing()
        {
            if (_localizingState != SystemState.Running)
                throw new InvalidOperationException("Localizing is not started");

            _localizingState = SystemState.Stopping;

            await CameraProvider.Stop();

            _localizingState = SystemState.Idle;
        }

        public static (Vector3 position, Quaternion rotation) EcefToUnityWorld(
            double3 ecefPosition,
            quaternion ecefRotation
        )
        {
            var (position, rotation) = LocationUtilities.UnityFromEcef(
                unityFromEcefTransform,
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
                ecefFromUnityTransform,
                new double3(position.x, position.y, position.z),
                rotation
            );
    }
}
