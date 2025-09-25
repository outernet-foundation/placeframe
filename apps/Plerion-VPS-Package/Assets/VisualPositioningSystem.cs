using System;
using System.Collections.Generic;
using System.Linq;

using Unity.Mathematics;
using Unity.XR.CoreUtils;

using UnityEngine;

using Cysharp.Threading.Tasks;

namespace Plerion
{
    public enum Lighting
    {
        Day,
        Dusk,
        Night
    }

    public static class VisualPositioningSystem
    {
        const int estimateHistorySize = 128;

        // The height above the ground of the blk2go camera array at during scan initialization
        const float scanneraOriginHeightOffset = 0.15f;

        public static bool FallbackToMostRecentEstimate = false;
        public static bool DiscardBelowAverageConfidenceEstimates = false;
        public static float MinimumPositionThreshold = 0.05f;
        public static float MinimumRotationThreshold = 2f;
        public static float? FloorHeight = null;

        public static float RansacPositionInlierThreshold = 0.05f;
        public static float RansacRotationInlierThreshold = 0.05f;
        public static float RansacConfidenceFactor = 1.0f;
        public static int RansacHistorySize = 128;

        private static double4x4 unityWorldToEcefTransform = double4x4.identity;
        private static double4x4 ecefToUnityWorldTransform = math.inverse(double4x4.identity);
        private static Queue<CameraPoseEstimate> estimateHistory = new Queue<CameraPoseEstimate>();

        public static event Action onReferenceFrameUpdated;

        public static void Initialize()
        {
            ImmersalNative.Initialize();
            ImmersalNative.SetInteger("LocalizationMaxPixels", 960 * 720);
            ImmersalNative.SetInteger("NumThreads", 1);
        }

        public static void ClearEstimateHistory()
        {
            estimateHistory.Clear();
        }

        public static void ApplyEstimate(CameraPoseEstimate estimate)
        {
            estimateHistory.Enqueue(estimate);

            if (estimateHistory.Count > estimateHistorySize)
                estimateHistory.Dequeue();

            var orderedEstimates = estimateHistory
                .OrderByDescending(estimate => estimate.confidence)
                .ToList();

            float range = orderedEstimates.First().confidence - orderedEstimates.Last().confidence;

            try
            {
                var filteredEstimateHistory = estimateHistory.Select(estimate => estimate);

                if (DiscardBelowAverageConfidenceEstimates)
                {
                    // Discard estimates below the average confidence
                    var averageConfidence =
                        filteredEstimateHistory.Select(estimate => estimate.confidence).Average();
                    filteredEstimateHistory =
                        filteredEstimateHistory.Where(estimate => estimate.confidence >= averageConfidence);
                }

                var estimates = filteredEstimateHistory.Select(estimate => (
                    estimate,
                    normalizedConfidence:
                        (estimate.confidence - orderedEstimates.Last().confidence) / range,
                    // Compute the local to ecef transform for each estimate (needs to be be
                    // recomputed when floor plane height changes, so for simplicity just always
                    // recompute)
                    transform: ComputeUnityWorldToEcefTransform(estimate)
                ));

                double4x4? newLocalToEcefTransform = null;

                // if (Settings.localizationReducer == Shared.LocalizationReducer.FAV)
                // {
                //     newTargetLocalToEcefTransform = FAV.Compute(estimates);
                // }
                // else if (Settings.localizationReducer == Shared.LocalizationReducer.RANSAC)
                {
                    newLocalToEcefTransform = RANSAC.Compute(estimates);
                }

                if (!newLocalToEcefTransform.HasValue)
                {
                    if (FallbackToMostRecentEstimate)
                    {
                        newLocalToEcefTransform = estimates.Last().transform;
                    }
                    else
                    {
                        newLocalToEcefTransform = estimates
                            .OrderByDescending(estimate => estimate.estimate.confidence)
                            .First().transform;
                    }
                }

                SetUnityWorldToEcefTransform(newLocalToEcefTransform.Value);
            }
            catch (Exception exception)
            {
                Log.Error(LogGroup.Localizer, "Failed to apply estimate", exception);
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
            var newPosition = unityWorldToEcefTransform.Position();
            var newRotation = unityWorldToEcefTransform.Rotation();

            var currentPosition = VisualPositioningSystem.unityWorldToEcefTransform.Position();
            var currentRotation = VisualPositioningSystem.unityWorldToEcefTransform.Rotation();

            var distance = math.distance(currentPosition, newPosition);
            var angle = Quaternion.Angle(currentRotation, newRotation);

            if (distance < MinimumPositionThreshold && angle < MinimumRotationThreshold)
                return;

            if (distance > MinimumPositionThreshold)
                Log.Info(LogGroup.Localizer, $"Distance threshold exceeded: {distance}");

            if (angle > MinimumRotationThreshold)
                Log.Info(LogGroup.Localizer, $"Angle threshold exceeded: {angle}");

            VisualPositioningSystem.unityWorldToEcefTransform = unityWorldToEcefTransform;
            ecefToUnityWorldTransform = math.inverse(unityWorldToEcefTransform);
            onReferenceFrameUpdated?.Invoke();
        }

        public static (Vector3 position, Quaternion rotation) EcefToUnityWorld(double3 position, quaternion rotation)
        {
            var ecefTransformMatrix = Double4x4.FromTranslationRotation(position, rotation);
            var localTransformMatrix = math.mul(ecefToUnityWorldTransform, ecefTransformMatrix);
            return (
                // Also see Localizer.cs 
                //
                // I never worked out why this position inversion (and the one in
                // SetEcefTransformFromLocalTransform, and the two other ones in Localizer.cs) are
                // required. I just brute-force guess-and-checked until I found something that worked.
                // The ecef rotations for localization maps comes from Cesium, and I searched
                // CesiumForUnity and Cesium-Native for answers, but there are many layers of
                // indirection, and at time of of writing, all origin modes go through a EUN (East-Up-North)
                // coordinate system that I believe gets "undone" by the local Unity transform of the
                // CesiumGeoreference itself. When I realized that, I gave up. But the ultimate
                // result, apparently, is that the required transform to go from ecef space to unity
                // space happens to be a position inversion. ¯\_(ツ)_/¯ 
                //
                // Apologies to the poor soul (probably me) who has to maintain this code in the future.
                -localTransformMatrix.Position().ToFloats(),
                localTransformMatrix.Rotation()
            );
        }

        public static (double3 position, quaternion rotation) UnityWorldToEcef(Vector3 position, Quaternion rotation)
        {
            var localTransformMatrix = Double4x4.FromTranslationRotation(
                // See above
                -position.ToDoubles(),
                rotation
            );

            var ecefTransformMatrix = math.mul(unityWorldToEcefTransform, localTransformMatrix);
            return (ecefTransformMatrix.Position(), ecefTransformMatrix.Rotation());
        }

        public static async UniTask LocalizeFromCameraImage(CameraImage cameraImage, Vector3 cameraPosition, Quaternion cameraRotation)
        {
            if (cameraImage.pixelBuffer == null)
                return;

            cameraRotation *= cameraImage.cameraOrientation;
            cameraRotation.SwitchHandedness();

            var localizeResult = await PlerionAPI.Localize(
                cameraImage.imageWidth,
                cameraImage.imageHeight,
                new Vector4(
                    cameraImage.focalLength.x,
                    cameraImage.focalLength.y,
                    cameraImage.principalPoint.x,
                    cameraImage.principalPoint.y
                ),
                cameraRotation,
                cameraImage.pixelBuffer
            );

            if (localizeResult.mapID == Guid.Empty)
                return;

            ApplyEstimate(new CameraPoseEstimate
            {
                unityWorldCameraPosition = cameraPosition,
                unityWorldCameraRotation = cameraRotation,
                ecefCameraPosition = localizeResult.ecefPosition,
                ecefCameraRotation = localizeResult.ecefRotation,
                confidence = localizeResult.confidence,
                map = localizeResult.mapID
            });
        }

        public static double4x4 ComputeUnityWorldToEcefTransform(CameraPoseEstimate estimate)
        {
            var unityWorldCameraPosition = estimate.unityWorldCameraPosition;
            var unityWorldCameraRotation = estimate.unityWorldCameraRotation;
            var ecefCameraPosition = estimate.ecefCameraPosition;
            var ecefCameraRotation = estimate.ecefCameraRotation;

            // Up is always up
            unityWorldCameraRotation = Quaternion.LookRotation(Vector3.Cross(unityWorldCameraRotation * Vector3.right, Vector3.up), Vector3.up);
            ecefCameraRotation = Quaternion.LookRotation(Vector3.Cross((Quaternion)ecefCameraRotation * Vector3.right, Vector3.up), Vector3.up);

            // The ground is always the ground
            if (FloorHeight != null)
                ecefCameraPosition.y = -FloorHeight.Value + unityWorldCameraPosition.y - scanneraOriginHeightOffset;

            var cameraTransformLocalSpace = Double4x4.FromTranslationRotation(
                -unityWorldCameraPosition, // See note in EcefTransform.cs
                unityWorldCameraRotation
            );

            var cameraTransformEcefSpace = Double4x4.FromTranslationRotation(
                -ecefCameraPosition, // See note in EcefTransform.cs
                ecefCameraRotation
            );

            return math.mul(cameraTransformEcefSpace, math.inverse(cameraTransformLocalSpace));
        }
    }
}