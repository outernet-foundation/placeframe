using System.Collections.Generic;
using System.Linq;
using PlaceframeApiClient.Model;
using Unity.Mathematics;

namespace Placeframe.Core
{
    public sealed class Hypothesis
    {
        public int Id;
        public double4x4 Estimate;
        public double Score;
        public double3 LastSupportVioPosition;
        public float LastSupportTime;
    }

    public enum MeasurementOutcome
    {
        Rejected,
        Bootstrapped,
        Accepted,
    }

    // A small set of competing alignment hypotheses, maintained as the system's belief about the
    // ECEF-to-Unity transform. Each measurement confirms an existing hypothesis (raising its score by
    // distance-weighted credit) or spawns a new one; a challenger takes the lead only after clearing a
    // margin and holding it for a dwell. The filter only decides what it believes; rendering that belief
    // into a published transform is the consumer's job.
    public sealed class MultiHypothesisFilter
    {
        private readonly List<Hypothesis> _hypotheses = new List<Hypothesis>();
        private Hypothesis _leader;
        private Hypothesis _challenger;
        private float _challengerSince;
        private int _nextId;

        public bool HasLeader => _leader != null;
        public double4x4 BestEstimate => _leader?.Estimate ?? double4x4.identity;
        public int HypothesisCount => _hypotheses.Count;
        public int PublishedHypothesisId => _leader?.Id ?? -1;

        public MeasurementOutcome ApplyMeasurement(MapLocalization localizationResult, CameraFrame frame, float nowSeconds)
        {
            var metrics = localizationResult.Metrics;
            if (metrics.InlierRatio < RelocalizationConfig.MinInlierRatio || metrics.NumInliers < RelocalizationConfig.MinInliers)
            {
                VisualPositioningSystem.LogDebug($"step=reloc.measure action=reject reason=qualityGate {QualityFields(metrics)}");
                return MeasurementOutcome.Rejected;
            }

            // Get the transform from the map to the camera (the inverse of the camera's pose in the map)
            var translationCameraFromMap = localizationResult.CameraFromMapTransform.Translation.ToDouble3();
            var rotationCameraFromMap = localizationResult.CameraFromMapTransform.Rotation.ToMathematicsQuaternion().ToDouble3x3();

            // Get the transform from the map to the ECEF reference frame (the map's ECEF pose)
            var translationEcefFromMap = localizationResult.MapTransform.Translation.ToDouble3();
            var rotationEcefFromMap = localizationResult.MapTransform.Rotation.ToMathematicsQuaternion().ToDouble3x3();

            // Change the basis of the map's pose to Unity's conventions
            (translationEcefFromMap, rotationEcefFromMap) = LocationUtilities.ChangeBasisUnityFromEcef(translationEcefFromMap, rotationEcefFromMap);

            // Get the transform from the camera to Unity world (the camera's pose in the Unity world)
            var vioPosition = (double3)(float3)frame.CameraTranslationUnityWorldFromCamera;
            var rotationUnityWorldFromCamera = ((quaternion)frame.CameraRotationUnityWorldFromCamera).ToDouble3x3();

            // Camera position in ECEF (Unity basis), via the map.
            var rotationMapFromCamera = math.transpose(rotationCameraFromMap);
            var translationMapFromCamera = math.mul(-rotationMapFromCamera, translationCameraFromMap);
            var translationEcefFromCamera = math.mul(rotationEcefFromMap, translationMapFromCamera) + translationEcefFromMap;

            // Composed rotation Unity ← ECEF. MapTransform carries R_ecefFromMap, so composition
            // into R_unityFromEcef needs R_mapFromEcef = transpose(R_ecefFromMap).
            var rotationUnityFromMap = math.mul(rotationUnityWorldFromCamera, rotationCameraFromMap);
            var rotationUnityFromEcef = math.mul(rotationUnityFromMap, math.transpose(rotationEcefFromMap));

            // Translation anchored on the camera: the published alignment places the camera at its
            // VIO-reported Unity-world position regardless of rotation noise, so rotation errors
            // cannot lever-arm the rendered camera away from its true position.
            var translation = vioPosition - math.mul(rotationUnityFromEcef, translationEcefFromCamera);

            var measurementMatrix = Double4x4.FromTranslationRotation(translation, rotationUnityFromEcef);

            if (_leader == null)
            {
                var bootstrapped = Spawn(measurementMatrix, vioPosition, nowSeconds);
                _leader = bootstrapped;
                VisualPositioningSystem.LogDebug(
                    $"step=reloc.measure action=spawn chosen={bootstrapped.Id} score={bootstrapped.Score:F3}"
                        + $" {MeasurementFields(measurementMatrix.Position())} {QualityFields(metrics)}"
                );
                return MeasurementOutcome.Bootstrapped;
            }

            // Associate to the hypothesis with the smallest SE(3) residual inside the gate — a translation
            // bound that widens with distance walked, plus a fixed rotation bound. A measurement matching
            // none spawns a new hypothesis.
            var best = _hypotheses
                .Select(hypothesis =>
                {
                    var candidateVioDelta = math.length(vioPosition - hypothesis.LastSupportVioPosition);
                    var residual = Se3.Log(math.mul(math.inverse(hypothesis.Estimate), measurementMatrix));
                    return new
                    {
                        Hypothesis = hypothesis,
                        VioDelta = candidateVioDelta,
                        ResidualRadians = math.length(new double3(residual[0], residual[1], residual[2])),
                        ResidualMeters = math.length(new double3(residual[3], residual[4], residual[5])),
                        Threshold = RelocalizationConfig.GateTranslationBaseMeters + (RelocalizationConfig.GateTranslationRatePerMeter * candidateVioDelta),
                    };
                })
                .Where(candidate => candidate.ResidualMeters <= candidate.Threshold && candidate.ResidualRadians <= RelocalizationConfig.GateRotationRadians)
                .OrderBy(candidate => candidate.ResidualMeters)
                .FirstOrDefault();

            Hypothesis matched;
            if (best != null)
            {
                matched = best.Hypothesis;

                matched.Estimate = measurementMatrix;
                matched.Score +=
                    RelocalizationConfig.SupportRewardBase
                    + (RelocalizationConfig.SupportRewardGainPerMeter * math.min(best.VioDelta, RelocalizationConfig.SupportRewardCapMeters));
                matched.LastSupportVioPosition = vioPosition;
                matched.LastSupportTime = nowSeconds;

                VisualPositioningSystem.LogDebug(
                    $"step=reloc.measure action=match chosen={matched.Id} score={matched.Score:F3}"
                        + $" residM={best.ResidualMeters:F3} residRad={best.ResidualRadians:F4}"
                        + $" gateThresh={best.Threshold:F3} vioDelta={best.VioDelta:F3}"
                        + $" {MeasurementFields(measurementMatrix.Position())} {QualityFields(metrics)}"
                );
            }
            else
            {
                if (_hypotheses.Count >= RelocalizationConfig.MaxHypotheses)
                    PruneWeakestNonLeader();

                matched = Spawn(measurementMatrix, vioPosition, nowSeconds);
                VisualPositioningSystem.LogDebug(
                    $"step=reloc.measure action=spawn chosen={matched.Id} score={matched.Score:F3}"
                        + $" {MeasurementFields(measurementMatrix.Position())} {QualityFields(metrics)}"
                );
            }

            // Decay the unsupported hypotheses; prune below the floor, never the leader; drop a pruned challenger.
            foreach (var hypothesis in _hypotheses)
            {
                if (hypothesis != matched)
                    hypothesis.Score *= RelocalizationConfig.ScoreDecayPerMeasurement;
            }

            _hypotheses.RemoveAll(hypothesis => hypothesis != _leader && hypothesis.Score < RelocalizationConfig.ScoreFloor);
            if (_challenger != null && !_hypotheses.Contains(_challenger))
                _challenger = null;

            UpdateLeader(nowSeconds);

            return MeasurementOutcome.Accepted;
        }

        public void Reset()
        {
            _hypotheses.Clear();
            _leader = null;
            _challenger = null;
        }

        // Referee: the leader hands off to the top-scoring challenger only once that challenger leads by
        // the margin AND holds the lead for the dwell. Evaluated on each accepted measurement, not on a
        // clock, so a stalled measurement stream never promotes a challenger on stale evidence.
        private void UpdateLeader(float nowSeconds)
        {
            var top = HighestScoring();
            if (top == null || top == _leader || top.Score <= _leader.Score + RelocalizationConfig.PromotionMargin)
            {
                _challenger = null;
                return;
            }

            if (_challenger != top)
            {
                _challenger = top;
                _challengerSince = nowSeconds;
                return;
            }

            if (nowSeconds - _challengerSince >= RelocalizationConfig.PromotionDwellSeconds)
            {
                VisualPositioningSystem.LogDebug(
                    $"step=reloc.promote from={_leader.Id} to={top.Id} gap={top.Score - _leader.Score:F3}"
                );
                _leader = top;
                _challenger = null;
            }
        }

        private void PruneWeakestNonLeader()
        {
            var weakest = _hypotheses
                .Where(hypothesis => hypothesis != _leader)
                .OrderBy(hypothesis => hypothesis.Score)
                .FirstOrDefault();
            if (weakest == null)
                return;

            _hypotheses.Remove(weakest);
            if (_challenger == weakest)
                _challenger = null;
        }

        private Hypothesis Spawn(double4x4 measurementMatrix, double3 vioPosition, float nowSeconds)
        {
            var hypothesis = new Hypothesis
            {
                Id = _nextId++,
                Estimate = measurementMatrix,
                Score = RelocalizationConfig.SpawnSeedScore,
                LastSupportVioPosition = vioPosition,
                LastSupportTime = nowSeconds,
            };
            _hypotheses.Add(hypothesis);
            return hypothesis;
        }

        private Hypothesis HighestScoring() =>
            _hypotheses.OrderByDescending(hypothesis => hypothesis.Score).FirstOrDefault();

        private static string QualityFields(LocalizationMetrics metrics) =>
            $"inlierRatio={metrics.InlierRatio:F3} numInliers={metrics.NumInliers} confTight={metrics.ConfidenceTight:F3}";

        private static string MeasurementFields(double3 translation) =>
            $"measTx={translation.x:F3} measTy={translation.y:F3} measTz={translation.z:F3}";
    }
}
