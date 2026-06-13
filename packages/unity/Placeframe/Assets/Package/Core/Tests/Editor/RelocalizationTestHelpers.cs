using System;
using System.Collections.Generic;
using NUnit.Framework;
using PlaceframeApiClient.Model;
using Unity.Mathematics;

namespace Placeframe.Core.Tests
{
    public static class RelocalizationTestHelpers
    {
        public static LocalizationMetrics MakeMetrics(double inlierRatio = 0.9, int numInliers = 100)
        {
            var identityCovariance = new List<List<double>>();
            for (var row = 0; row < 6; row++)
            {
                var values = new List<double>();
                for (var column = 0; column < 6; column++)
                {
                    values.Add(row == column ? 1.0 : 0.0);
                }

                identityCovariance.Add(values);
            }

            return new LocalizationMetrics(
                inlierRatio: inlierRatio,
                reprojectionErrorMedian: 0.5,
                numInliers: numInliers,
                numCorrespondences: 110,
                numMatches: 120,
                inlierCoverage: 0.8,
                confidenceTight: 0.99,
                confidenceLoose: 0.99,
                confidenceIsCalibrated: true,
                measurementCovariance: identityCovariance,
                pnpCovariance: identityCovariance,
                pipelineVersion: "test"
            );
        }

        public static CameraFrame MakeFrame(float3 cameraPosition) =>
            new CameraFrame
            {
                CameraTranslationUnityWorldFromCamera = cameraPosition,
                CameraRotationUnityWorldFromCamera = quaternion.identity,
            };

        public static MapLocalization MakeLocalization(double inlierRatio = 0.9, int numInliers = 100, float3 mapTranslation = default)
        {
            var metrics = MakeMetrics(inlierRatio: inlierRatio, numInliers: numInliers);
            var cameraFromMap = new Transform(translation: new Float3(0, 0, 0), rotation: new Float4(0, 0, 0, 1));
            var mapTransform = new Transform(
                translation: new Float3(mapTranslation.x, mapTranslation.y, mapTranslation.z),
                rotation: new Float4(0, 0, 0, 1)
            );
            return new MapLocalization(id: Guid.NewGuid(), cameraFromMapTransform: cameraFromMap, mapTransform: mapTransform, metrics: metrics);
        }

        // Feeds the filter a measurement whose published alignment places the world origin at alignmentX
        // while the device (VIO) sits at cameraX. With identity rotations the camera-anchored translation
        // is cameraX - mapTranslation, so choosing mapTranslation = cameraX - alignmentX yields exactly
        // alignmentX — letting a test name the two quantities it actually cares about.
        public static MeasurementOutcome Apply(
            MultiHypothesisFilter filter,
            double alignmentX,
            double cameraX,
            float nowSeconds,
            double inlierRatio = 0.9,
            int numInliers = 100
        )
        {
            var camera = new float3((float)cameraX, 0f, 0f);
            var mapTranslation = new float3((float)(cameraX - alignmentX), 0f, 0f);
            return filter.ApplyMeasurement(MakeLocalization(inlierRatio, numInliers, mapTranslation), MakeFrame(camera), nowSeconds);
        }

        public static void AssertMatricesEqual(double4x4 actual, double4x4 expected, double tolerance = 1e-6)
        {
            for (var column = 0; column < 4; column++)
            {
                for (var row = 0; row < 4; row++)
                {
                    Assert.That(actual[column][row], Is.EqualTo(expected[column][row]).Within(tolerance), $"m[{column}][{row}]");
                }
            }
        }

        public static void AssertNearIdentity(double4x4 matrix) => AssertMatricesEqual(matrix, double4x4.identity);
    }
}
