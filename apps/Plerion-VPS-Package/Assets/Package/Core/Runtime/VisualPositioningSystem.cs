using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;

using Unity.Mathematics;

using UnityEngine;

using Cysharp.Threading.Tasks;
using PlerionApiClient.Client;
using System.IO;
using PlerionApiClient.Api;
using System.Threading.Tasks;
using System.Net.Http;

using CameraModel = PlerionApiClient.Model.Camera;
using PinholeCameraConfig = PlerionApiClient.Model.PinholeCameraConfig;
using LocalizationSession = PlerionApiClient.Model.LocalizationSessionRead;
using LocalizationMetrics = PlerionApiClient.Model.LocalizationMetrics;
using Plerion.Core;

namespace Plerion.VPS
{
    public static class VisualPositioningSystem
    {

        private class KeycloakHttpHandler : DelegatingHandler
        {
            protected override async System.Threading.Tasks.Task<HttpResponseMessage> SendAsync(
                HttpRequestMessage request, CancellationToken cancellationToken)
            {
                var token = await Auth.GetOrRefreshToken();
                request.Headers.Authorization = new System.Net.Http.Headers.AuthenticationHeaderValue("Bearer", token);
                return await base.SendAsync(request, cancellationToken);
            }
        }

        public static bool FallbackToMostRecentEstimate = false;
        public static bool DiscardBelowAverageConfidenceEstimates = false;
        public static float MinimumPositionThreshold = 0.05f;
        public static float MinimumRotationThreshold = 2f;
        public static float? DetectedFloorHeight = null;
        public static float? EstimatedFloorHeight { get; private set; } = null;
        public static float? FloorHeight => EstimatedFloorHeight ?? DetectedFloorHeight;
        public static bool LocalizationSessionActive => localizationSessionId != Guid.Empty;

        public static double4x4 EcefToUnityWorldTransform => unityFromEcefTransform;
        public static double4x4 UnityWorldToEcefTransform => ecefFromUnityTransform;

        public static event Action OnEcefToUnityWorldTransformUpdated;

        private static DefaultApi api;
        private static CancellationTokenSource startSessionTokenSource = new CancellationTokenSource();
        private static Task startSessionTask;
        public static Guid localizationSessionId = Guid.Empty;

        private static double4x4 unityFromEcefTransform = double4x4.identity;
        private static double4x4 ecefFromUnityTransform = math.inverse(unityFromEcefTransform);

        private static async Task StartSessionInternal(CameraModel cameraIntrinsics, CancellationToken cancellationToken = default)
        {
            LocalizationSession session = default;

            try
            {
                session = await api.CreateLocalizationSessionAsync(cancellationToken);

                while (true)
                {
                    var status = await api.GetLocalizationSessionStatusAsync(session.Id, cancellationToken);

                    if (status == "\"failed\"" || status == "\"exited\"")
                        throw new Exception("Session failed to start.");

                    if (status == "\"ready\"")
                        break;

                    await UniTask.WaitForSeconds(1, cancellationToken: cancellationToken);
                }

                await api.SetLocalizationSessionCameraIntrinsicsAsync(session.Id, cameraIntrinsics, cancellationToken);

                await UniTask.SwitchToMainThread(cancellationToken: cancellationToken);
            }
            catch (Exception exc)
            {
                if (session != null)
                    api.DeleteLocalizationSessionAsync(session.Id).AsUniTask().Forget();

                throw exc;
            }

            localizationSessionId = session.Id;
        }

        public static async UniTask Initialize(string apiUrl, string authUrl, string username, string password)
        {
            Auth.url = authUrl;
            Auth.username = username;
            Auth.password = password;
            Auth.LogInfo = message => Debug.Log(message);
            Auth.LogWarning = message => Debug.LogWarning(message);
            Auth.LogError = message => Debug.LogError(message);

            api = new DefaultApi(
                new HttpClient(new KeycloakHttpHandler() { InnerHandler = new HttpClientHandler() })
                {
                    BaseAddress = new Uri(apiUrl)
                },
                apiUrl
            );

            await Auth.Login();
        }

        public static UniTask StartLocalizationSession(CameraIntrinsics intrinsics)
        {
            if (localizationSessionId != Guid.Empty)
                return UniTask.CompletedTask;

            if (startSessionTask != null && !startSessionTask.IsCompleted)
                return startSessionTask.AsUniTask();

            startSessionTokenSource?.Dispose();
            startSessionTokenSource = new CancellationTokenSource();
            startSessionTask = StartSessionInternal(new CameraModel(new PinholeCameraConfig(
                model: PinholeCameraConfig.ModelEnum.PINHOLE,
                width: intrinsics.resolution.x,
                height: intrinsics.resolution.y,
                mirroring: PinholeCameraConfig.MirroringEnum.None,
                rotation: PinholeCameraConfig.RotationEnum._90CCW,
                fx: intrinsics.focalLength.x,
                fy: intrinsics.focalLength.y,
                cx: intrinsics.resolution.x - 1 - intrinsics.principlePoint.x,
                cy: intrinsics.principlePoint.y
            )), startSessionTokenSource.Token);

            return startSessionTask.AsUniTask();
        }

        public static UniTask LoadLocalizationMaps(IEnumerable<Guid> maps)
            => LoadLocalizationMaps(maps.ToList());

        public static UniTask LoadLocalizationMaps(params Guid[] maps)
            => LoadLocalizationMaps(maps.ToList());

        public static async UniTask LoadLocalizationMaps(List<Guid> maps)
        {
            await api.LoadLocalizationMapsAsync(localizationSessionId, maps);
        }

        public static async UniTask UnloadLocalizationMap(Guid map)
        {
            await api.UnloadMapAsync(localizationSessionId, map);
        }

        public static void StopLocalizationSession()
        {
            startSessionTokenSource?.Cancel();
            startSessionTokenSource?.Dispose();
            startSessionTokenSource = null;

            if (localizationSessionId != Guid.Empty)
            {
                api.DeleteLocalizationSessionAsync(localizationSessionId).AsUniTask().Forget();
                localizationSessionId = Guid.Empty;
            }
        }

        public static async UniTask LocalizeFromCameraImage(byte[] image, Vector3 cameraTranslationUnityWorldFromCamera, Quaternion cameraRotationUnityWorldFromCamera)
        {
            if (image == null)
                return;

            var localizationResults = await api.LocalizeImageAsync(
                localizationSessionId,
                new FileParameter(new MemoryStream(image))
            );

            if (localizationResults.Count == 0)
            {
                Debug.Log("EP: LOCALIZATION FAILED");
                return; //localization failed
            }

            var localizationResult = localizationResults.FirstOrDefault(); //for now, just use the first one

            unityFromEcefTransform = LocationUtilities.ComputeUnityFromEcefTransform(
                localizationResult.Transform.Position.ToDouble3(),
                localizationResult.Transform.Rotation.ToMathematicsQuaternion().ToDouble3x3(),
                localizationResult.MapTransform.Position.ToDouble3(),
                localizationResult.MapTransform.Rotation.ToMathematicsQuaternion().ToDouble3x3(),
                cameraTranslationUnityWorldFromCamera.ToFloat3(),
                // TODO: Adjust unity rotation to account for phone orientation (portrait vs landscape)
                math.mul(
                    ((quaternion)cameraRotationUnityWorldFromCamera).ToDouble3x3(),
                    quaternion.AxisAngle(new float3(0f, 0f, 1f), math.radians(0f)).ToDouble3x3())
            );
            ecefFromUnityTransform = math.inverse(unityFromEcefTransform);

            OnEcefToUnityWorldTransformUpdated?.Invoke();
        }

        public static void SetUnityWorldToEcefTransform(double4x4 transform)
        {
            ecefFromUnityTransform = transform;
            unityFromEcefTransform = math.inverse(transform);

            OnEcefToUnityWorldTransformUpdated?.Invoke();
        }

        public static void SetEcefToUnityWorldTransform(double4x4 transform)
        {
            unityFromEcefTransform = transform;
            ecefFromUnityTransform = math.inverse(transform);

            OnEcefToUnityWorldTransformUpdated?.Invoke();
        }

        public static (Vector3 position, Quaternion rotation) EcefToUnityWorld(double3 ecefPosition, quaternion ecefRotation)
        {
            var (position, rotation) = LocationUtilities.EcefToUnityWorld(unityFromEcefTransform, ecefPosition, ecefRotation);
            return (new Vector3((float)position.x, (float)position.y, (float)position.z), new Quaternion((float)rotation.value.x, (float)rotation.value.y, (float)rotation.value.z, (float)rotation.value.w));
        }

        public static (double3 position, quaternion rotation) UnityWorldToEcef(Vector3 position, Quaternion rotation)
            => LocationUtilities.UnityWorldToEcef(ecefFromUnityTransform, position.ToFloat3(), rotation);

        public static async UniTask<MapData[]> GetLoadedLocalizationMapsAsync(bool includePoints = false, CancellationToken cancellationToken = default)
        {
            var maps = await api.GetLocalizationMapsAsync(cancellationToken: cancellationToken);

            if (maps == null || maps.Count == 0)
                return new MapData[0];

            var loadedMaps = new List<PlerionApiClient.Model.LocalizationMapRead>();

            await UniTask.WhenAll(maps.Select(map => api
                .GetMapLoadStatusAsync(localizationSessionId, map.Id, cancellationToken)
                .AsUniTask()
                .ContinueWith(x =>
                {
                    if (x.Status == PlerionApiClient.Model.LoadState.Ready)
                        loadedMaps.Add(map);
                })
            ));

            if (loadedMaps.Count == 0)
                return new MapData[0];

            if (!includePoints)
                return loadedMaps.Select(ToMapData).ToArray();

            var mapsByID = loadedMaps.ToDictionary(x => x.Id, x => ToMapData(x));

            await UniTask.WhenAll(loadedMaps.Select(map => GetLocalizationMapPointsAsync(map.Id, cancellationToken: cancellationToken)));

            return mapsByID.Values.ToArray();
        }

        public static async UniTask<MapData[]> GetLocalizationMapsAsync(bool includePoints = false, CancellationToken cancellationToken = default)
        {
            var maps = await api.GetLocalizationMapsAsync(cancellationToken: cancellationToken);

            if (!includePoints)
                return maps.Select(ToMapData).ToArray();

            var mapsByID = maps.ToDictionary(x => x.Id, x => ToMapData(x));

            await UniTask.WhenAll(maps.Select(map => GetLocalizationMapPointsAsync(map.Id, cancellationToken: cancellationToken)));

            return mapsByID.Values.ToArray();
        }

        public static async UniTask<Point[]> GetLocalizationMapPointsAsync(Guid mapID, CancellationToken cancellationToken = default)
        {
            var points = await api.GetLocalizationMapPointsAsync(mapID, cancellationToken);

            return points.Select(x =>
            {
                var pcw = x.Position.ToDouble3();
                var (p_ucam, _) = LocationUtilities.ChangeBasisOpenCVToUnity(pcw, quaternion.identity.ToDouble3x3());
                return new Point
                {
                    position = new float3((float)p_ucam.x, (float)p_ucam.y, (float)p_ucam.z),
                    color = x.Color.ToUnityColor()
                };
            }).ToArray();
        }

        private static MapData ToMapData(PlerionApiClient.Model.LocalizationMapRead map)
        {
            return new MapData()
            {
                id = map.Id,
                active = map.Active,
                name = map.Name,
                ecefPosition = new double3(map.PositionX, map.PositionY, map.PositionZ),
                ecefRotation = new quaternion((float)map.RotationX, (float)map.RotationY, (float)map.RotationZ, (float)map.RotationW)
            };
        }
    }

    public class MapData
    {
        public Guid id;
        public bool active;
        public string name;
        public double3 ecefPosition;
        public quaternion ecefRotation;
        public Point[] points;
    }

    public struct Point
    {
        public Color color;
        public Vector3 position;
    }

    public struct CameraIntrinsics
    {
        public Vector2Int resolution;
        public Vector2 focalLength;
        public Vector2 principlePoint;
    }
}