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

        // One batch per query: associate every measurement, then decay/prune/promote exactly once, so
        // decay tracks query cadence rather than how many clusters a frame happened to produce.
        public MeasurementOutcome ApplyMeasurements(IReadOnlyList<MapLocalization> measurements, CameraFrame frame, float nowSeconds)
        {
            var supported = new HashSet<Hypothesis>();
            var bootstrapped = false;
            var startId = _nextId;
            var redundantCount = 0;

            foreach (var measurement in measurements)
            {
                var wasLeaderless = _leader == null;
                var touched = AssociateMeasurement(measurement, frame, nowSeconds, supported, out var redundant);
                if (redundant)
                    redundantCount++;

                if (touched == null)
                    continue;

                supported.Add(touched);
                bootstrapped |= wasLeaderless;
            }

            // supported holds only matched and spawned hypotheses (redundant duplicates and quality rejects
            // return null and never enter it), each distinct and each spawn having bumped _nextId once, so the
            // set splits cleanly into matched + spawned.
            var spawnedCount = _nextId - startId;
            var matchedCount = supported.Count - spawnedCount;
            var rejectedCount = measurements.Count - supported.Count - redundantCount;

            if (supported.Count == 0)
            {
                LogBatch(measurements.Count, matchedCount, spawnedCount, redundantCount, rejectedCount, MeasurementOutcome.Rejected);
                return MeasurementOutcome.Rejected;
            }

            // Decay the unsupported hypotheses; prune below the floor, never the leader; drop a pruned challenger.
            foreach (var hypothesis in _hypotheses)
            {
                if (!supported.Contains(hypothesis))
                    hypothesis.Score *= RelocalizationConfig.ScoreDecayPerMeasurement;
            }

            var pruned = _hypotheses
                .Where(hypothesis => hypothesis != _leader && hypothesis.Score < RelocalizationConfig.ScoreFloor)
                .ToList();
            foreach (var hypothesis in pruned)
                VisualPositioningSystem.LogDebug($"step=reloc.prune reason=belowFloor id={hypothesis.Id} score={hypothesis.Score:F3}");

            _hypotheses.RemoveAll(pruned.Contains);
            if (_challenger != null && !_hypotheses.Contains(_challenger))
                _challenger = null;

            UpdateLeader(nowSeconds);

            var outcome = bootstrapped ? MeasurementOutcome.Bootstrapped : MeasurementOutcome.Accepted;
            LogBatch(measurements.Count, matchedCount, spawnedCount, redundantCount, rejectedCount, outcome);
            return outcome;
        }

        // One line per query: outcome, the matched/spawned/rejected split, the published leader and standing
        // challenger, and the full post-batch score roster — the only marker delimiting one query's batch from
        // the next, and the readout for watching an alias hypothesis accrue score across queries.
        private void LogBatch(int measurements, int matched, int spawned, int redundant, int rejected, MeasurementOutcome outcome)
        {
            var roster = string.Join(",", _hypotheses.Select(hypothesis => $"{hypothesis.Id}:{hypothesis.Score:F2}"));
            VisualPositioningSystem.LogDebug(
                $"step=reloc.batch outcome={outcome} measurements={measurements} matched={matched} spawned={spawned}"
                    + $" redundant={redundant} rejected={rejected} leader={(_leader?.Id ?? -1)} challenger={(_challenger?.Id ?? -1)} roster=[{roster}]"
            );
        }

        public MeasurementOutcome ApplyMeasurement(MapLocalization localizationResult, CameraFrame frame, float nowSeconds) =>
            ApplyMeasurements(new[] { localizationResult }, frame, nowSeconds);

        // Associate one measurement to a hypothesis (or spawn one), without decaying or promoting — the
        // batch owns those. Returns the matched/spawned hypothesis, or null on a quality-gate reject or a
        // redundant measurement (one whose best in-gate hypothesis was already matched this batch, e.g. a
        // second retrieval cluster solving to the same pose). redundant is set only in that latter case.
        private Hypothesis AssociateMeasurement(MapLocalization localizationResult, CameraFrame frame, float nowSeconds, HashSet<Hypothesis> alreadyMatched, out bool redundant)
        {
            redundant = false;
            var metrics = localizationResult.Metrics;
            if (metrics.InlierRatio < RelocalizationConfig.MinInlierRatio || metrics.NumInliers < RelocalizationConfig.MinInliers)
            {
                VisualPositioningSystem.LogDebug($"step=reloc.measure action=reject reason=qualityGate {QualityFields(metrics)}");
                return null;
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
                var seed = Spawn(measurementMatrix, vioPosition, nowSeconds);
                _leader = seed;
                VisualPositioningSystem.LogDebug(
                    $"step=reloc.measure action=spawn chosen={seed.Id} score={seed.Score:F3}"
                        + $" {MeasurementFields(measurementMatrix.Position())} {QualityFields(metrics)}"
                );
                return seed;
            }

            // Associate to the hypothesis with the smallest SE(3) residual inside the gate — a translation
            // bound that widens with distance walked, plus a fixed rotation bound. If that hypothesis was
            // already matched this batch the measurement is a redundant duplicate (a second cluster solving
            // to the same pose); a measurement matching no hypothesis at all spawns a new one.
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

            if (best != null && alreadyMatched.Contains(best.Hypothesis))
            {
                redundant = true;
                VisualPositioningSystem.LogDebug(
                    $"step=reloc.measure action=redundant chosen={best.Hypothesis.Id} residM={best.ResidualMeters:F3} {QualityFields(metrics)}"
                );
                return null;
            }

            if (best != null)
            {
                var matched = best.Hypothesis;
                matched.Estimate = measurementMatrix;
                matched.Score = math.min(
                    matched.Score
                        + RelocalizationConfig.SupportRewardBase
                        + (RelocalizationConfig.SupportRewardGainPerMeter * math.min(best.VioDelta, RelocalizationConfig.SupportRewardCapMeters)),
                    RelocalizationConfig.ScoreCap
                );
                matched.LastSupportVioPosition = vioPosition;
                matched.LastSupportTime = nowSeconds;

                VisualPositioningSystem.LogDebug(
                    $"step=reloc.measure action=match chosen={matched.Id} score={matched.Score:F3}"
                        + $" residM={best.ResidualMeters:F3} residRad={best.ResidualRadians:F4}"
                        + $" gateThresh={best.Threshold:F3} vioDelta={best.VioDelta:F3}"
                        + $" {MeasurementFields(measurementMatrix.Position())} {QualityFields(metrics)}"
                );
                return matched;
            }

            if (_hypotheses.Count >= RelocalizationConfig.MaxHypotheses)
                PruneStalestNonLeader();

            var spawned = Spawn(measurementMatrix, vioPosition, nowSeconds);
            VisualPositioningSystem.LogDebug(
                $"step=reloc.measure action=spawn chosen={spawned.Id} score={spawned.Score:F3}"
                    + $" {MeasurementFields(measurementMatrix.Position())} {QualityFields(metrics)}"
            );
            return spawned;
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
                if (_challenger != null)
                    VisualPositioningSystem.LogDebug($"step=reloc.challenger action=reset from={_challenger.Id}");

                _challenger = null;
                return;
            }

            if (_challenger != top)
            {
                _challenger = top;
                _challengerSince = nowSeconds;
                VisualPositioningSystem.LogDebug(
                    $"step=reloc.challenger action=establish id={top.Id} gap={top.Score - _leader.Score:F3}"
                );
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

        // Evict the stalest non-leader (oldest since last support, ties broken by score), never the lowest
        // score outright: a freshly-spawned candidate carries the seed score and would always be the lowest,
        // so a weakest-score policy would evict it via the spawn that immediately follows it, before it could
        // earn a second match. Staleness protects what was just supported and removes the genuinely abandoned.
        private void PruneStalestNonLeader()
        {
            var stalest = _hypotheses
                .Where(hypothesis => hypothesis != _leader)
                .OrderBy(hypothesis => hypothesis.LastSupportTime)
                .ThenBy(hypothesis => hypothesis.Score)
                .FirstOrDefault();
            if (stalest == null)
                return;

            VisualPositioningSystem.LogDebug(
                $"step=reloc.prune reason=capacity id={stalest.Id} score={stalest.Score:F3} lastSupport={stalest.LastSupportTime:F3}"
            );
            _hypotheses.Remove(stalest);
            if (_challenger == stalest)
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
