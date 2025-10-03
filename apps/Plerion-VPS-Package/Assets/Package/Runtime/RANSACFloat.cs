using System;
using System.Collections.Generic;
using System.Linq;
using Unity.Mathematics;
using UnityEngine;

using static Plerion.VisualPositioningSystem;

namespace Plerion
{
    static public class RANSACFloat
    {
        const double inlierThresholdPosition = 0.05;
        const int iterations = 100;
        const int sampleSize = 3;

        static public double Score { get; private set; } = 0;

        static private float[] bestModelEstimates = null;

        static public float? Compute(
            IEnumerable<(
                float estimate,
                float normalizedConfidence
            )> estimates)
        {
            estimates = estimates.Reverse().Take(RansacHistorySize);

            if (estimates.Count() < sampleSize) return null;

            var estimatesList = estimates.ToList();

            double bestScore = 0;
            float bestModel = 0;

            // Start from the previous best model if it exists
            if (bestModelEstimates != null)
            {
                bestModel = bestModelEstimates.Average();

                bestScore = ComputeModelScore(bestModel, estimates);
            }

            System.Random rand = new System.Random();

            for (int iteration = 0; iteration < iterations; iteration++)
            {
                var sample = Enumerable
                    .Range(0, estimatesList.Count)
                    .OrderBy(x => rand.Next())
                    .Take(sampleSize)
                    .Select(index => estimatesList[index]);

                var model = sample.Select(pair => pair.estimate).Average();

                double score = ComputeModelScore(bestModel, estimates);

                if (score <= bestScore) continue;

                bestScore = score;
                bestModel = model;
                bestModelEstimates = sample.Select(pair => pair.estimate).ToArray();
            }

            Score = bestScore;

            return bestModel;
        }

        static private double ComputeModelScore(
            float model,
            IEnumerable<(float estimate, float normalizedConfidence)> estimates)
        {
            double score = 0;

            foreach (var estimate in estimates)
            {
                score += Mathf.Pow(estimate.normalizedConfidence, RansacConfidenceFactor) * math.exp(-math.abs(estimate.estimate - model) / inlierThresholdPosition);
            }

            return score / estimates.Count();
        }
    }
}