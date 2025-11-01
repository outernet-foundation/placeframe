using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;

using Unity.Mathematics;

using UnityEngine;

using Cysharp.Threading.Tasks;
using PlerionClient.Client;
using System.IO;
using PlerionClient.Api;
using System.Threading.Tasks;
using System.Net.Http;

using CameraModel = PlerionClient.Model.Camera;
using PinholeIntrinsics = PlerionClient.Model.PinholeIntrinsics;
using LocalizationSession = PlerionClient.Model.LocalizationSessionRead;

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

        public static event Action OnEcefToUnityWorldTransformUpdated;

        private static DefaultApi api;
        private static CancellationTokenSource startSessionTokenSource = new CancellationTokenSource();
        private static Task startSessionTask;
        public static Guid localizationSessionId = Guid.Empty;

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

        //TODO EP: Replace with proper URLs when deploying
        public static void Initialize(string username, string password)
        {
            Auth.url = "https://desktop-otd3rch-keycloak.outernetfoundation.org/realms/plerion-dev/protocol/openid-connect/token";
            Auth.username = username;
            Auth.password = password;

            api = new DefaultApi(
                new HttpClient(new KeycloakHttpHandler() { InnerHandler = new HttpClientHandler() })
                {
                    BaseAddress = new Uri("https://desktop-otd3rch-api.outernetfoundation.org")
                },
                "https://desktop-otd3rch-api.outernetfoundation.org"
            );
        }

        public static UniTask StartLocalizationSession(CameraIntrinsics intrinsics)
        {
            if (localizationSessionId != Guid.Empty)
                return UniTask.CompletedTask;

            if (startSessionTask != null && !startSessionTask.IsCompleted)
                return startSessionTask.AsUniTask();

            startSessionTokenSource?.Dispose();
            startSessionTokenSource = new CancellationTokenSource();
            startSessionTask = StartSessionInternal(new CameraModel(new PinholeIntrinsics(
                model: PinholeIntrinsics.ModelEnum.PINHOLE,
                width: intrinsics.resolution.x,
                height: intrinsics.resolution.y,
                fx: intrinsics.focalLength.x,
                fy: intrinsics.focalLength.y,
                // cx: intrinsics.principlePoint.x,
                cx: (intrinsics.resolution.x - 1) - intrinsics.principlePoint.x,
                cy: intrinsics.principlePoint.y
            )), startSessionTokenSource.Token);

            return startSessionTask.AsUniTask();
        }

        public static UniTask LoadLocalizationMaps(params Guid[] maps)
            => LoadLocalizationMaps(maps.ToList());

        public static async UniTask LoadLocalizationMaps(List<Guid> maps)
        {
            await api.LoadLocalizationMapsAsync(localizationSessionId, maps);
        }

        public static void StopLocalizationSession()
        {
            startSessionTokenSource?.Cancel();
            startSessionTokenSource?.Dispose();
            startSessionTokenSource = null;

            if (localizationSessionId != Guid.Empty)
            {
                api.DeleteLocalizationSessionAsync(localizationSessionId);
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

            unityWorldFromColmapWorld = BuildUnityWorldFromColmapWorldTransform(
                colmapRotationCameraFromWorld: new quaternion(
                    (float)localizationResult.Transform.Rotation.X,
                    (float)localizationResult.Transform.Rotation.Y,
                    (float)localizationResult.Transform.Rotation.Z,
                    (float)localizationResult.Transform.Rotation.W
                ),
                colmapTranslationCameraFromWorld: new float3(
                    (float)localizationResult.Transform.Position.X,
                    (float)localizationResult.Transform.Position.Y,
                    (float)localizationResult.Transform.Position.Z
                ),
                unityRotationWorldFromCamera: new quaternion(
                    cameraRotationUnityWorldFromCamera.x,
                    cameraRotationUnityWorldFromCamera.y,
                    cameraRotationUnityWorldFromCamera.z,
                    cameraRotationUnityWorldFromCamera.w
                ),
                unityTranslationWorldFromCamera: new float3(
                    cameraTranslationUnityWorldFromCamera.x,
                    cameraTranslationUnityWorldFromCamera.y,
                    cameraTranslationUnityWorldFromCamera.z
                )
            );

            OnEcefToUnityWorldTransformUpdated?.Invoke();
        }

        static float4x4 unityWorldFromColmapWorld = float4x4.identity;

        static float3x3 basisOpenCV = new float3x3(
            new float3(1f, 0f, 0f),
            new float3(0f, -1f, 0f),
            new float3(0f, 0f, 1f)
        );
        static float3x3 basisUnity = float3x3.identity;
        static float3x3 basisChangeUnityFromOpenCV = math.mul(math.transpose(basisUnity), basisOpenCV);
        static float3x3 basisChangeOpenCVFromUnity = math.transpose(basisChangeUnityFromOpenCV);
        public static (float3x3, float3) UnityFromOpenCV(float3x3 rotation, float3 translation)
            => (math.mul(basisChangeUnityFromOpenCV, math.mul(rotation, basisChangeOpenCVFromUnity)), math.mul(basisChangeUnityFromOpenCV, translation));
        public static (float3x3, float3) OpenCVFromUnity(float3x3 rotation, float3 translation)
            => (math.mul(basisChangeOpenCVFromUnity, math.mul(rotation, basisChangeUnityFromOpenCV)), math.mul(basisChangeOpenCVFromUnity, translation));

        public static float4x4 BuildUnityWorldFromColmapWorldTransform(
            quaternion colmapRotationCameraFromWorld,
            float3 colmapTranslationCameraFromWorld,
            quaternion unityRotationWorldFromCamera,
            float3 unityTranslationWorldFromCamera)
        {
            // Adjust unity rotation to account for phone orientation (portrait vs landscape)
            var unityRotationWorldFromCameraMatrix = math.mul(
                new float3x3(unityRotationWorldFromCamera),
                new float3x3(quaternion.AxisAngle(new float3(0f, 0f, 1f), math.radians(-90f))));

            // Change basis from OpenCV to Unity
            var colmapRotationCameraFromWorldMatrix = new float3x3(colmapRotationCameraFromWorld);
            (colmapRotationCameraFromWorldMatrix, colmapTranslationCameraFromWorld) =
                UnityFromOpenCV(colmapRotationCameraFromWorldMatrix, colmapTranslationCameraFromWorld);

            // Compute similarity transform
            return new float4x4(
                math.mul(unityRotationWorldFromCameraMatrix, colmapRotationCameraFromWorldMatrix),
                math.mul(unityRotationWorldFromCameraMatrix, colmapTranslationCameraFromWorld) + unityTranslationWorldFromCamera
            );
        }

        public static (Vector3 position, Quaternion rotation) UnityWorldFromColmapWorld(float3 position, quaternion rotation)
        {
            // Change basis from OpenCV to Unity
            var rotationMatrix = new float3x3(rotation);
            var (rotationMatrix_unityBasis, position_unityBasis) = UnityFromOpenCV(rotationMatrix, position);

            // Apply similarity transform to get unity world transform
            float4x4 unityTransform = math.mul(unityWorldFromColmapWorld, new float4x4(rotationMatrix_unityBasis, position_unityBasis));

            // Extract the rotation
            var unityRotation = new quaternion(new float3x3(unityTransform.c0.xyz, unityTransform.c1.xyz, unityTransform.c2.xyz));

            return (
                new Vector3(unityTransform.c3.x, unityTransform.c3.y, unityTransform.c3.z),
                new Quaternion(unityRotation.value.x, unityRotation.value.y, unityRotation.value.z, unityRotation.value.w)
            );
        }

        public static (float3 position, quaternion rotation) ColmapWorldFromUnityWorld(Vector3 position, Quaternion rotation)
        {
            return (float3.zero, new quaternion());
        }

        public static async UniTask<MapData[]> GetLoadedLocalizationMapsAsync(bool includePoints = false, CancellationToken cancellationToken = default)
        {
            var maps = await api.GetLocalizationMapsAsync(cancellationToken: cancellationToken);

            if (maps == null || maps.Count == 0)
                return new MapData[0];

            var loadedMaps = new List<PlerionClient.Model.LocalizationMapRead>();

            await UniTask.WhenAll(maps.Select(map => api
                .GetMapLoadStatusAsync(localizationSessionId, map.Id, cancellationToken)
                .AsUniTask()
                .ContinueWith(x =>
                {
                    if (x == "\"ready\"")
                        loadedMaps.Add(map);
                })
            ));

            if (loadedMaps.Count == 0)
                return new MapData[0];

            if (!includePoints)
            {
                return loadedMaps.Select(x => new MapData()
                {
                    id = x.Id,
                    name = x.Name,
                    ecefPosition = new double3(x.PositionX, x.PositionY, x.PositionZ),
                    ecefRotation = new quaternion((float)x.RotationX, (float)x.RotationY, (float)x.RotationZ, (float)x.RotationW)
                }).ToArray();
            }

            var mapsByID = loadedMaps.ToDictionary(x => x.Id, x => new MapData()
            {
                id = x.Id,
                name = x.Name,
                ecefPosition = new double3(x.PositionX, x.PositionY, x.PositionZ),
                ecefRotation = new quaternion((float)x.RotationX, (float)x.RotationY, (float)x.RotationZ, (float)x.RotationW)
            });

            await UniTask.WhenAll(loadedMaps.Select(map => GetLocalizationMapPointsAsync(map.Id, cancellationToken: cancellationToken)));

            return mapsByID.Values.ToArray();
        }

        public static async UniTask<MapData[]> GetLocalizationMapsAsync(bool includePoints = false, CancellationToken cancellationToken = default)
        {
            var maps = await api.GetLocalizationMapsAsync(cancellationToken: cancellationToken);

            if (!includePoints)
            {
                return maps.Select(x => new MapData()
                {
                    id = x.Id,
                    name = x.Name,
                    ecefPosition = new double3(x.PositionX, x.PositionY, x.PositionZ),
                    ecefRotation = new quaternion((float)x.RotationX, (float)x.RotationY, (float)x.RotationZ, (float)x.RotationW)
                }).ToArray();
            }

            var mapsByID = maps.ToDictionary(x => x.Id, x => new MapData()
            {
                id = x.Id,
                name = x.Name,
                ecefPosition = new double3(x.PositionX, x.PositionY, x.PositionZ),
                ecefRotation = new quaternion((float)x.RotationX, (float)x.RotationY, (float)x.RotationZ, (float)x.RotationW)
            });

            await UniTask.WhenAll(maps.Select(map => GetLocalizationMapPointsAsync(map.Id, cancellationToken: cancellationToken)));

            return mapsByID.Values.ToArray();
        }

        public static async UniTask<Point[]> GetLocalizationMapPointsAsync(Guid mapID, CancellationToken cancellationToken = default)
        {
            var points = await api.GetLocalizationMapPointsAsync(mapID, cancellationToken);

            return points.Select(x =>
            {
                var pcw = new float3((float)x.Position.X, (float)x.Position.Y, (float)x.Position.Z);
                var p_ucam = math.mul(basisChangeUnityFromOpenCV, pcw);
                return new Point
                {
                    position = new Vector3(p_ucam.x, p_ucam.y, p_ucam.z),
                    color = x.Color.ToUnityColor()
                };
            }).ToArray();
        }
    }

    public class MapData
    {
        public Guid id;
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