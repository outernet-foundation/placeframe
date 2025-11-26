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
using PinholeCamera = PlerionApiClient.Model.PinholeCamera;
using LocalizationSession = PlerionApiClient.Model.LocalizationSessionRead;
using LocalizationMetrics = PlerionApiClient.Model.LocalizationMetrics;

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

        public static double4x4 EcefToUnityWorldTransform => ecefToUnityTransform;
        public static double4x4 UnityWorldToEcefTransform => unityToEcefTransform;

        public static event Action OnEcefToUnityWorldTransformUpdated;

        private static DefaultApi api;
        private static CancellationTokenSource startSessionTokenSource = new CancellationTokenSource();
        private static Task startSessionTask;
        public static Guid localizationSessionId = Guid.Empty;

        private static double4x4 ecefToUnityTransform = new float4x4(quaternion.identity, new float3());
        private static double4x4 unityToEcefTransform = math.inverse(ecefToUnityTransform);

        private static readonly float3x3 basisUnity = float3x3.identity;

        private static readonly float3x3 basisOpenCV = new float3x3(
            1f, 0f, 0f,
            0f, -1f, 0f,
            0f, 0f, 1f
        );

        private static readonly float3x3 basisEcef = new float3x3(
            1f, 0f, 0f,
            0f, -1f, 0f,
            0f, 0f, 1f
        );

        private static readonly float3x3 basisChangeUnityFromOpenCV = math.mul(math.transpose(basisUnity), basisOpenCV);
        private static readonly float3x3 basisChangeOpenCVFromUnity = math.transpose(basisChangeUnityFromOpenCV);

        private static readonly double3x3 basisChangeUnityFromEcef = math.mul(math.transpose(basisUnity), basisEcef);
        private static readonly double3x3 basisChangeEcefFromUnity = math.transpose(basisChangeUnityFromEcef);

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
            startSessionTask = StartSessionInternal(new CameraModel(new PinholeCamera(
                model: PinholeCamera.ModelEnum.PINHOLE,
                width: intrinsics.resolution.x,
                height: intrinsics.resolution.y,
                mirroring: PinholeCamera.MirroringEnum.None,
                rotation: PinholeCamera.RotationEnum._90CCW,
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

            var unityWorldFromColmap = BuildUnityWorldFromColmapWorldTransform(
                colmapRotationCameraFromWorld: localizationResult.Transform.Rotation.ToMathematicsQuaternion(),
                colmapTranslationCameraFromWorld: localizationResult.Transform.Position.ToFloat3(),
                unityRotationWorldFromCamera: cameraRotationUnityWorldFromCamera,
                unityTranslationWorldFromCamera: cameraTranslationUnityWorldFromCamera.ToFloat3()
            );

            var (mapRotation, mapPosition) = ChangeBasisEcefToUnity(
                new float3x3(localizationResult.MapTransform.Rotation.ToMathematicsQuaternion()),
                localizationResult.MapTransform.Position.ToFloat3()
            );

            var ecefFromColmapWorldMatrix = Double4x4.FromTranslationRotation(mapPosition, new quaternion(new float3x3(mapRotation)));
            var colmapWorldFromEcefMatrix = math.inverse(ecefFromColmapWorldMatrix);
            var unityWorldFromEcefMatrix = math.mul(unityWorldFromColmap, colmapWorldFromEcefMatrix);

            ecefToUnityTransform = unityWorldFromEcefMatrix;
            unityToEcefTransform = math.inverse(ecefToUnityTransform);

            OnEcefToUnityWorldTransformUpdated?.Invoke();
        }

        public static void SetUnityWorldToEcefTransform(double4x4 transform)
        {
            unityToEcefTransform = transform;
            ecefToUnityTransform = math.inverse(transform);

            OnEcefToUnityWorldTransformUpdated?.Invoke();
        }

        public static void SetEcefToUnityWorldTransform(double4x4 transform)
        {
            ecefToUnityTransform = transform;
            unityToEcefTransform = math.inverse(transform);

            OnEcefToUnityWorldTransformUpdated?.Invoke();
        }

        private static float4x4 BuildUnityWorldFromColmapWorldTransform(
            quaternion colmapRotationCameraFromWorld,
            float3 colmapTranslationCameraFromWorld,
            quaternion unityRotationWorldFromCamera,
            float3 unityTranslationWorldFromCamera)
        {
            // Adjust unity rotation to account for phone orientation (portrait vs landscape)
            var unityRotationWorldFromCameraMatrix = math.mul(
                new float3x3(unityRotationWorldFromCamera),
                new float3x3(quaternion.AxisAngle(new float3(0f, 0f, 1f), math.radians(0f))));

            // Change basis from OpenCV to Unity
            var colmapRotationCameraFromWorldMatrix = new float3x3(colmapRotationCameraFromWorld);
            (colmapRotationCameraFromWorldMatrix, colmapTranslationCameraFromWorld) =
                ChangeBasisOpenCVToUnity(colmapRotationCameraFromWorldMatrix, colmapTranslationCameraFromWorld);

            // Compute similarity transform
            return new float4x4(
                math.mul(unityRotationWorldFromCameraMatrix, colmapRotationCameraFromWorldMatrix),
                math.mul(unityRotationWorldFromCameraMatrix, colmapTranslationCameraFromWorld) + unityTranslationWorldFromCamera
            );
        }

        private static (float3x3, float3) ChangeBasisOpenCVToUnity(float3x3 rotation, float3 translation)
            => (math.mul(basisChangeUnityFromOpenCV, math.mul(rotation, basisChangeOpenCVFromUnity)), math.mul(basisChangeUnityFromOpenCV, translation));

        // private static (float3x3, float3) OpenCVFromUnity(float3x3 rotation, float3 translation)
        //     => (math.mul(basisChangeOpenCVFromUnity, math.mul(rotation, basisChangeUnityFromOpenCV)), math.mul(basisChangeOpenCVFromUnity, translation));

        private static (double3x3, double3) ChangeBasisEcefToUnity(double3x3 rotation, double3 translation)
            => (math.mul(basisChangeUnityFromEcef, math.mul(rotation, basisChangeEcefFromUnity)), math.mul(basisChangeUnityFromEcef, translation));

        private static (double3x3, double3) ChangeBasisUnityToEcef(double3x3 rotation, double3 translation)
            => (math.mul(basisChangeEcefFromUnity, math.mul(rotation, basisChangeUnityFromEcef)), math.mul(basisChangeEcefFromUnity, translation));

        public static (Vector3 position, Quaternion rotation) EcefToUnityWorld(double3 ecefPosition, quaternion ecefRotation)
        {
            var (rot, pos) = ChangeBasisEcefToUnity(new float3x3(ecefRotation), ecefPosition);
            var ecefTransform = Double4x4.FromTranslationRotation(pos, new quaternion(new float3x3(rot)));
            var unityTransform = math.mul(ecefToUnityTransform, ecefTransform);
            return (unityTransform.Position().ToFloats(), unityTransform.Rotation());
        }

        public static (double3 position, quaternion rotation) UnityWorldToEcef(Vector3 position, Quaternion rotation)
        {
            var unityTransform = Double4x4.FromTranslationRotation(position, rotation);
            var ecefTransform = math.mul(unityToEcefTransform, unityTransform);
            var (rot, pos) = ChangeBasisUnityToEcef(new float3x3(ecefTransform.Rotation()), ecefTransform.Position());
            return (pos, new quaternion(new float3x3(rot)));
        }

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
                var pcw = x.Position.ToFloat3();
                var p_ucam = ChangeBasisOpenCVToUnity(new float3x3(quaternion.identity), pcw).Item2;
                return new Point
                {
                    position = p_ucam,
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