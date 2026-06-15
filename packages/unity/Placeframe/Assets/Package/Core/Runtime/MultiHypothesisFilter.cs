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
        public double3 LastSupportMapPosition;
        public float LastSupportTime;
        public double LastInlierRatio;
        public int LastNumInliers;
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
        private double? _lastValidScaleRatio;

        public bool HasLeader => _leader != null;
        public double4x4 BestEstimate => _leader?.Estimate ?? double4x4.identity;
        public int HypothesisCount => _hypotheses.Count;
        public int PublishedHypothesisId => _leader?.Id ?? -1;

        // The most recent per-segment device-vs-map scale ratio (vioDelta / mapDelta) from a matched
        // measurement with real motion, or null when the latest batch had no such segment (standstill,
        // spawn-only, or reject). The consumer reads this once after ApplyMeasurements to drive online
        // scale compensation; it is the EMA input, not a published value.
        public double? LastValidScaleRatio => _lastValidScaleRatio;

        // One batch per query: associate every measurement, then decay/prune/promote exactly once, so
        // decay tracks query cadence rather than how many clusters a frame happened to produce.
        public MeasurementOutcome ApplyMeasurements(IReadOnlyList<MapLocalization> measurements, CameraFrame frame, float nowSeconds)
        {
            var supported = new HashSet<Hypothesis>();
            var bootstrapped = false;
            var startId = _nextId;
            var redundantCount = 0;
            _lastValidScaleRatio = null;

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
            var cameraFields = CameraGeodeticFields(translationEcefFromCamera);

            if (_leader == null)
            {
                var seed = Spawn(measurementMatrix, vioPosition, translationMapFromCamera, metrics, nowSeconds);
                _leader = seed;
                VisualPositioningSystem.LogDebug(
                    $"step=reloc.measure action=spawn chosen={seed.Id} score={seed.Score:F3}"
                        + $" {MeasurementFields(measurementMatrix.Position())} {MapPositionFields(translationMapFromCamera)} {cameraFields} {QualityFields(metrics)}"
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
                    $"step=reloc.measure action=redundant chosen={best.Hypothesis.Id} residM={best.ResidualMeters:F3}"
                        + $" {cameraFields} {QualityFields(metrics)}"
                );
                return null;
            }

            if (best != null)
            {
                var matched = best.Hypothesis;

                // Scale-warp discriminator: map-frame motion of the camera since this hypothesis was
                // last supported, paired with the VIO motion over the same interval. scaleRatio is the
                // device-vs-map metric scale on that segment. A ratio that holds constant across map
                // regions is a uniform device/VIO scale offset; one that varies with map position is
                // local map warp. mapDelta near zero (standstill) makes the ratio meaningless.
                var mapDelta = math.length(translationMapFromCamera - matched.LastSupportMapPosition);
                var scaleRatio = mapDelta > 1e-3 ? best.VioDelta / mapDelta : 0.0;

                if (mapDelta > 1e-3)
                    _lastValidScaleRatio = scaleRatio;

                matched.Estimate = measurementMatrix;
                matched.Score = math.min(
                    matched.Score
                        + RelocalizationConfig.SupportRewardBase
                        + (RelocalizationConfig.SupportRewardGainPerMeter * math.min(best.VioDelta, RelocalizationConfig.SupportRewardCapMeters)),
                    RelocalizationConfig.ScoreCap
                );
                matched.LastSupportVioPosition = vioPosition;
                matched.LastSupportMapPosition = translationMapFromCamera;
                matched.LastSupportTime = nowSeconds;
                matched.LastInlierRatio = metrics.InlierRatio;
                matched.LastNumInliers = metrics.NumInliers;

                VisualPositioningSystem.LogDebug(
                    $"step=reloc.measure action=match chosen={matched.Id} score={matched.Score:F3}"
                        + $" residM={best.ResidualMeters:F3} residRad={best.ResidualRadians:F4}"
                        + $" gateThresh={best.Threshold:F3} vioDelta={best.VioDelta:F3}"
                        + $" mapDelta={mapDelta:F3} scaleRatio={scaleRatio:F3}"
                        + $" {MeasurementFields(measurementMatrix.Position())} {MapPositionFields(translationMapFromCamera)} {cameraFields} {QualityFields(metrics)}"
                );
                return matched;
            }

            if (_hypotheses.Count >= RelocalizationConfig.MaxHypotheses)
                PruneStalestNonLeader();

            var spawned = Spawn(measurementMatrix, vioPosition, translationMapFromCamera, metrics, nowSeconds);
            VisualPositioningSystem.LogDebug(
                $"step=reloc.measure action=spawn chosen={spawned.Id} score={spawned.Score:F3}"
                    + $" {MeasurementFields(measurementMatrix.Position())} {MapPositionFields(translationMapFromCamera)} {cameraFields} {QualityFields(metrics)}"
            );
            return spawned;
        }

        public void Reset()
        {
            _hypotheses.Clear();
            _leader = null;
            _challenger = null;
            _lastValidScaleRatio = null;
        }

        // Referee: the leader hands off to the top-scoring challenger only once it qualifies AND holds the
        // lead for the dwell. Two qualifying paths: the motion-margin path (leads by PromotionMargin) is
        // the anti-aliasing core that adjudicates between comparable-quality hypotheses; the
        // quality-dominance path lets a much-stronger lock unseat a much-weaker incumbent without the full
        // margin (still requiring real motion, so a single-viewpoint alias never qualifies). Evaluated on
        // each accepted measurement, not a clock, so a stalled stream never promotes on stale evidence.
        private void UpdateLeader(float nowSeconds)
        {
            var top = HighestScoring();
            var marginCleared = top != null && top != _leader && top.Score > _leader.Score + RelocalizationConfig.PromotionMargin;
            var qualityCleared = top != null && top != _leader && QualityDominates(top, _leader);

            if (!marginCleared && !qualityCleared)
            {
                ClearChallenger();
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
                    $"step=reloc.promote from={_leader.Id} to={top.Id} reason={(marginCleared ? "margin" : "qualityDominance")}"
                        + $" gap={top.Score - _leader.Score:F3} leaderInliers={_leader.LastNumInliers} topInliers={top.LastNumInliers}"
                        + $" leaderRatio={_leader.LastInlierRatio:F3} topRatio={top.LastInlierRatio:F3}"
                );
                _leader = top;
                _challenger = null;
            }
        }

        private void ClearChallenger()
        {
            if (_challenger != null)
                VisualPositioningSystem.LogDebug($"step=reloc.challenger action=reset from={_challenger.Id}");

            _challenger = null;
        }

        // True when the challenger overwhelmingly out-evidences the leader (inlier count and ratio) and has
        // earned real motion credit. The motion floor is the largest possible seed plus the minimum motion
        // reward, so a freshly-spawned strong lock — seeded high but unwalked — never qualifies; only one
        // confirmed across a walk does. This is the weak-partial-vs-strong case, not two comparable aliases.
        private static bool QualityDominates(Hypothesis challenger, Hypothesis leader)
        {
            var inlierDominance = challenger.LastNumInliers >= RelocalizationConfig.PromotionQualityDominanceFactor * leader.LastNumInliers;
            var ratioDominance = challenger.LastInlierRatio >= leader.LastInlierRatio + RelocalizationConfig.PromotionInlierRatioMargin;
            var motionFloor =
                RelocalizationConfig.SpawnSeedScore
                + RelocalizationConfig.SpawnQualityBonusMax
                + RelocalizationConfig.PromotionQualityMotionMinScore;
            var hasMotion = challenger.Score >= motionFloor;
            return inlierDominance && ratioDominance && hasMotion;
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

        // Seed scales with how far the measurement clears the quality gate so a much-stronger lock survives
        // the decay window long enough for motion to adjudicate it, instead of being pruned at the flat
        // seed before it can earn a second confirmation. The bonus stays below PromotionMargin, so a fresh
        // spawn still cannot promote on quality alone.
        private Hypothesis Spawn(double4x4 measurementMatrix, double3 vioPosition, double3 mapPosition, LocalizationMetrics metrics, float nowSeconds)
        {
            var hypothesis = new Hypothesis
            {
                Id = _nextId++,
                Estimate = measurementMatrix,
                Score = RelocalizationConfig.SpawnSeedScore + (RelocalizationConfig.SpawnQualityBonusMax * QualityFraction(metrics)),
                LastSupportVioPosition = vioPosition,
                LastSupportMapPosition = mapPosition,
                LastSupportTime = nowSeconds,
                LastInlierRatio = metrics.InlierRatio,
                LastNumInliers = metrics.NumInliers,
            };
            _hypotheses.Add(hypothesis);
            return hypothesis;
        }

        // Relative quality in [0,1]: inlier count above the gate floor, saturating at
        // QualityBonusSaturationInliers. A calibration-free ordering between locks from the same localizer.
        private static double QualityFraction(LocalizationMetrics metrics) =>
            math.saturate((double)metrics.NumInliers / RelocalizationConfig.QualityBonusSaturationInliers);

        private Hypothesis HighestScoring() =>
            _hypotheses.OrderByDescending(hypothesis => hypothesis.Score).FirstOrDefault();

        private static string QualityFields(LocalizationMetrics metrics) =>
            $"inlierRatio={metrics.InlierRatio:F3} numInliers={metrics.NumInliers} confTight={metrics.ConfidenceTight:F3}";

        private static string MeasurementFields(double3 translation) =>
            $"measTx={translation.x:F3} measTy={translation.y:F3} measTz={translation.z:F3}";

        // Camera position in the reconstruction's own (map) frame — the region coordinate that
        // scaleRatio is binned against to separate a uniform device/VIO scale offset from local warp.
        private static string MapPositionFields(double3 mapPosition) =>
            $"mapX={mapPosition.x:F3} mapY={mapPosition.y:F3} mapZ={mapPosition.z:F3}";

        // translationEcefFromCamera is in Unity basis; undo the basis change to get true ECEF so WGS84
        // returns the camera's real-world geodetic position — "under the ground" is a height question.
        private static string CameraGeodeticFields(double3 translationEcefFromCameraUnityBasis)
        {
            var (translationEcefFromCamera, _) = LocationUtilities.ChangeBasisEcefFromUnity(translationEcefFromCameraUnityBasis, double3x3.identity);
            var geodetic = WGS84.EcefToCartographic(translationEcefFromCamera);
            return $"camLat={geodetic.Latitude:F7} camLon={geodetic.Longitude:F7} camAlt={geodetic.Height:F2}";
        }
    }
}
