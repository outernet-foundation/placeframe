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
using GenericParamsIntrinsics = PlerionClient.Model.GenericParamsIntrinsics;
using PinholeIntrinsics = PlerionClient.Model.PinholeIntrinsics;
using OpenCVRadTanIntrinsics = PlerionClient.Model.OpenCVRadTanIntrinsics;
using LocalizationSession = PlerionClient.Model.LocalizationSessionRead;
using Unity.Profiling;

namespace Plerion.VPS
{
    public static class VisualPositioningSystem
    {
        static class Handedness
        {
            // Flip Z to go between right-handed (COLMAP/ECEF) and Unity left-handed.
            public static readonly double4x4 zFlip = new double4x4(
                1, 0, 0, 0,
                0, 1, 0, 0,
                0, 0, -1, 0,
                0, 0, 0, 1
            );

            // Conjugate a 4x4 by the Z flip: LH = F * RH * F  (and vice-versa; same op).
            public static double4x4 ToUnityLeftHanded(double4x4 rightHandedMatrix)
                => math.mul(zFlip, math.mul(rightHandedMatrix, zFlip));
        }

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

        // const int estimateHistorySize = 128;

        // The height above the ground of the blk2go camera array at during scan initialization
        // const float scanneraOriginHeightOffset = 0.15f;

        public static bool FallbackToMostRecentEstimate = false;
        public static bool DiscardBelowAverageConfidenceEstimates = false;
        public static float MinimumPositionThreshold = 0.05f;
        public static float MinimumRotationThreshold = 2f;
        public static float? DetectedFloorHeight = null;
        public static float? EstimatedFloorHeight { get; private set; } = null;
        public static float? FloorHeight => EstimatedFloorHeight ?? DetectedFloorHeight;
        public static bool LocalizationSessionActive => localizationSessionId != Guid.Empty;

        // Do we need these if we're not doing estimate history?
        // public static float RansacPositionInlierThreshold = 0.05f;
        // public static float RansacRotationInlierThreshold = 0.05f;
        // public static float RansacConfidenceFactor = 1.0f;
        // public static int RansacHistorySize = 128;

        // public static double4x4 UnityWorldToEcefTransform => unityWorldToEcefTransform;
        // public static double4x4 EcefToUnityWorldTransform => ecefToUnityWorldTransform;

        public static double4x4 UnityFromEcefTransformLeftHanded => unity_from_ecef_transform_left_handed;
        public static double4x4 EcefFromUnityTransformLeftHanded => ecef_from_unity_transform_left_handed;

        public static event Action OnEcefToUnityWorldTransformUpdated;

        private static DefaultApi api;
        private static CancellationTokenSource startSessionTokenSource = new CancellationTokenSource();
        private static Task startSessionTask;
        public static Guid localizationSessionId = Guid.Empty;

        // private static double4x4 unityWorldToEcefTransform = double4x4.identity;
        // private static double4x4 ecefToUnityWorldTransform = math.inverse(double4x4.identity);

        private static double4x4 unity_from_ecef_transform_left_handed = double4x4.identity;
        private static double4x4 ecef_from_unity_transform_left_handed = math.inverse(double4x4.identity);

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

        public static void Initialize(string username, string password)
            => Initialize("https://desktop-otd3rch-api.outernetfoundation.org", username, password); // TODO EP: Replace with actual url

        public static void Initialize(string baseURL, string username, string password)
        {
            Auth.username = username;
            Auth.password = password;
            api = new DefaultApi(
                new HttpClient(new KeycloakHttpHandler() { InnerHandler = new HttpClientHandler() })
                {
                    BaseAddress = new Uri(baseURL)
                },
                baseURL
            );
        }

        // public static UniTask StartGenericLocalizationSession(int width, int height, List<double> varParams)
        //     => StartLocalizationSessionWithCamera(new CameraModel(
        //         new GenericParamsIntrinsics(GenericParamsIntrinsics.ModelEnum.GENERIC, width, height, varParams)
        //     ));

        // public static UniTask StartOpenCVLocalizationSession(int width, int height, double fx, double fy, double cx, double cy, double k1, double k2, double p1, double p2, double? k3)
        //     => StartLocalizationSessionWithCamera(new CameraModel(new OpenCVRadTanIntrinsics(
        //         OpenCVRadTanIntrinsics.ModelEnum.OPENCV,
        //         width, height, fx, fy, cx, cy,
        //         k1, k2, p1, p2, k3
        //     )));

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
                cx: intrinsics.principlePoint.x,
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

        public static void SetEcefToUnityWorldTransform(double3 position, quaternion rotation)
            => SetUnityWorldToEcefTransform(math.inverse(Double4x4.FromTranslationRotation(position, rotation)));

        public static void SetEcefToUnityWorldTransform(double4x4 ecefToLocalTransform)
            => SetUnityWorldToEcefTransform(math.inverse(ecefToLocalTransform));

        public static void SetUnityWorldToEcefTransform(double3 position, quaternion rotation)
            => SetUnityWorldToEcefTransform(Double4x4.FromTranslationRotation(position, rotation));

        public static void SetUnityWorldToEcefTransform(double4x4 unityWorldToEcefTransform)
        {
            VisualPositioningSystem.unity_from_ecef_transform_left_handed = Handedness.ToUnityLeftHanded(unityWorldToEcefTransform);
            VisualPositioningSystem.ecef_from_unity_transform_left_handed = math.inverse(VisualPositioningSystem.unity_from_ecef_transform_left_handed);
            // var newPosition = unityWorldToEcefTransform.Position();
            // var newRotation = unityWorldToEcefTransform.Rotation();

            // var currentPosition = VisualPositioningSystem.unityWorldToEcefTransform.Position();
            // var currentRotation = VisualPositioningSystem.unityWorldToEcefTransform.Rotation();

            // var distance = math.distance(currentPosition, newPosition);
            // var angle = Quaternion.Angle(currentRotation, newRotation);

            // if (Application.isPlaying)
            // {
            //     if (distance < MinimumPositionThreshold && angle < MinimumRotationThreshold)
            //         return;

            //     if (distance > MinimumPositionThreshold)
            //         Log.Info(LogGroup.VisualPositioningSystem, $"Distance threshold exceeded: {distance}");

            //     if (angle > MinimumRotationThreshold)
            //         Log.Info(LogGroup.VisualPositioningSystem, $"Angle threshold exceeded: {angle}");
            // }

            // VisualPositioningSystem.unityWorldToEcefTransform = unityWorldToEcefTransform;
            // ecefToUnityWorldTransform = math.inverse(unityWorldToEcefTransform);
            // OnEcefToUnityWorldTransformUpdated?.Invoke();
        }


        public static async UniTask LocalizeFromCameraImage(byte[] image, Vector3 cameraPosition, Quaternion cameraRotation)
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

            Debug.Log($"EP: GOT LOCALIZATION {localizationResult.Transform.Position} {localizationResult.Transform.Rotation}");

            (unity_from_ecef_transform_left_handed, ecef_from_unity_transform_left_handed) =
                BuildUnityFromEcefMapping_Once(
                    Double4x4.FromTranslationRotation(localizationResult.MapTransform.Position, localizationResult.MapTransform.Rotation),
                    Double4x4.FromTranslationRotation(localizationResult.Transform.Position, localizationResult.Transform.Rotation),
                    Double4x4.FromTranslationRotation(cameraPosition, cameraRotation)
                );
        }

        public static (double4x4 unity_from_ecef_transform_left_handed,
                       double4x4 ecef_from_unity_transform_left_handed)
        BuildUnityFromEcefMapping_Once(
            double4x4 ecef_from_map_transform_right_handed,    // E <- L (RH)
            double4x4 map_from_camera_transform_right_handed,  // L <- C (RH, world_from_camera)
            double4x4 unity_from_camera_transform_left_handed  // U <- C (LH)
        )
        {
            // 1) Convert the COLMAP/ECEF pieces to Unity's left-handed space ONCE.
            var ecef_from_map_transform_left_handed = Handedness.ToUnityLeftHanded(ecef_from_map_transform_right_handed);
            var map_from_camera_transform_left_handed = Handedness.ToUnityLeftHanded(map_from_camera_transform_right_handed);

            // 2) Compose the camera pose in ECEF, all in LEFT-HANDED now:
            //    E <- C = (E <- L) * (L <- C)
            var ecef_from_camera_transform_left_handed =
                math.mul(ecef_from_map_transform_left_handed, map_from_camera_transform_left_handed);

            // 3) Solve for the global mapping in LEFT-HANDED:
            //    U <- E = (U <- C) * inverse(E <- C)
            var unity_from_ecef_transform_left_handed =
                math.mul(unity_from_camera_transform_left_handed,
                         math.inverse(ecef_from_camera_transform_left_handed));

            // 4) Keep the inverse too (saves recomputing later).
            var ecef_from_unity_transform_left_handed = math.inverse(unity_from_ecef_transform_left_handed);

            return (unity_from_ecef_transform_left_handed, ecef_from_unity_transform_left_handed);
        }

        public static (Vector3 position, Quaternion rotation) EcefToUnityWorld(double3 position, quaternion rotation)
        {
            var ecefTransform = Double4x4.FromTranslationRotation(position, rotation);
            // U <- X = (U <- E) * (E <- X)
            var unityTransform = math.mul(unity_from_ecef_transform_left_handed, ecefTransform);
            return (unityTransform.Position().ToFloats(), unityTransform.Rotation());
        }


        public static (double3 position, quaternion rotation) UnityWorldToEcef(Vector3 position, Quaternion rotation)
        {
            var unityTransform = Double4x4.FromTranslationRotation(position, rotation);
            // E <- X = (E <- U) * (U <- X)
            var ecefTransform = math.mul(ecef_from_unity_transform_left_handed, unityTransform);
            return (ecefTransform.Position(), ecefTransform.Rotation());
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
            return points.Select(x => new Point()
            {
                position = x.Position.ToUnityVector3(),
                color = x.Color.ToUnityColor(),
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