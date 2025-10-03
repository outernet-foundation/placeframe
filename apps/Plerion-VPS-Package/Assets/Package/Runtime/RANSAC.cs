using System.Collections.Generic;
using System.Linq;
using Unity.Mathematics;
using UnityEngine;
using static Plerion.VisualPositioningSystem;

namespace Plerion
{
    static public class RANSAC
    {
        // const double inlierThresholdPosition = 0.05;
        // const double inlierThresholdRotationDegrees = 2.0;
        const int iterations = 100;
        const int sampleSize = 3;

        static public double Score { get; private set; } = 0;

        static private CameraPoseEstimate[] bestModelEstimates = null;

        static public double4x4? Compute(
            IEnumerable<(
                CameraPoseEstimate estimate,
                float normalizedConfidence,
                double4x4 transform
            )> estimates)
        {
            if (estimates.Count() < sampleSize) return null;

            estimates = estimates.Reverse().Take(RansacHistorySize);

            var estimatesList = estimates.ToList();

            double bestScore = 0;
            double4x4 bestModel = double4x4.identity;

            // Start from the previous best model if it exists
            if (bestModelEstimates != null)
            {
                var (position, rotation) = ComputeModel(bestModelEstimates
                    // Compute the local to ecef transform for each estimate (needs to be be
                    // recomputed when floor plane height changes, so for simplicity just always
                    // recompute)
                    .Select(estimate => ComputeUnityWorldToEcefTransform(estimate))
                    .ToList());

                bestScore = ComputeModelScore(
                    position,
                    rotation,
                    estimatesList.Select(pair => (pair.transform, pair.normalizedConfidence)));
                bestModel = Double4x4.FromTranslationRotation(position, rotation);
            }

            System.Random rand = new System.Random();

            for (int iteration = 0; iteration < iterations; iteration++)
            {
                var sample = Enumerable
                    .Range(0, estimatesList.Count)
                    .OrderBy(x => rand.Next())
                    .Take(sampleSize)
                    .Select(index => estimatesList[index]);

                var (position, rotation) = ComputeModel(
                    sample.Select(pair => pair.transform).ToList());

                double score = ComputeModelScore(
                    position,
                    rotation,
                    estimatesList.Select(pair => (pair.transform, pair.normalizedConfidence)));

                if (score <= bestScore) continue;

                bestScore = score;
                bestModel = Double4x4.FromTranslationRotation(position, rotation);
                bestModelEstimates = sample.Select(pair => pair.estimate).ToArray();
            }

            Score = bestScore;

            return bestModel;
        }

        static private (double3 position, Quaternion rotation) ComputeModel(List<double4x4> sample)
        {
            double3 averagePosition = double3.zero;
            Quaternion averageRotation = sample.First().Rotation();

            for (int i = 0; i < sampleSize; i++)
            {
                averagePosition += sample[i].Position();
                if (i == 0) continue;
                averageRotation = math.slerp(averageRotation, sample[i].Rotation(), 1.0f / (i + 1));
            }
            averagePosition /= sampleSize;

            return (averagePosition, averageRotation);
        }

        static private double ComputeModelScore(
            double3 position,
            Quaternion rotation,
            IEnumerable<(double4x4 transform, float normalizedConfidence)> estimates)
        {
            double score = 0;

            foreach (var estimate in estimates)
            {
                var positionScore = math.exp(
                    -math.length(estimate.transform.Position() - position) /
                    VisualPositioningSystem.RansacPositionInlierThreshold);

                var rotationScore = math.exp(
                    -math.abs(Quaternion.Angle(estimate.transform.Rotation(), rotation)) /
                    VisualPositioningSystem.RansacRotationInlierThreshold);

                score += Mathf.Pow(estimate.normalizedConfidence, VisualPositioningSystem.RansacConfidenceFactor) * (positionScore + rotationScore);
            }

            return score / estimates.Count();
        }
    }
}